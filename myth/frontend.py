# importing required library.
from socket import socket
from time import strftime, sleep, mktime
import myth.protocol
import myth.util
import sys
import os
from threading import Thread

class Frontend:
	version = 31
	ps1 = "mythfrontend> "

	def __init__(self, server):
		self.sock = socket()
		self.sock.connect(server)
		print 'Connected to', server
		self.running = True

		self.sendCommand(myth.protocol.ProtocolVersion(self.version))
		self.sendCommand(myth.protocol.Announce('mythproto'))
		self.prompt()
	
	def prompt(self):
		while self.running:
			sys.stdout.write(self.ps1)
			sys.stdout.flush()

			line = sys.stdin.readline()
			line = line.split(' ')
			line[-1] = line[-1][:-1]
			cmd = line[0]

			if cmd == 'help' or cmd == '?':
				print """The following commands are available:
exit		Disconnect from the server and exit
ls		List recorded shows
stop		Stop recording a show
check		Check to see if a show is currently recording
pending		List shows pending deletion (AutoExpire)
expiring	List shows pending deletion (AutoExpire including LiveTV)
conflict	List all shows that are currently in conflict
status		Show status information about the backend
checkfile	Check for the existance of a file on the backend
guidedata	Show the date when guide data ends
transfer	Transfer a file from the backend"""

			if cmd == 'exit':
				self.running = False
				self.sendCommand(myth.protocol.Done())
				if self.player:
					self.player.stopPlaying()

			if cmd == 'ls':
				query = self.sendCommand(myth.protocol.QueryRecordings())
				recordings = query.getRecordings()
				self.index = []
				for i in range(len(recordings)):
					print i, '\t' + recordings[i].getTitle() + ': ' + recordings[i].getSubtitle()
					self.index.append(recordings[i])
			
			if cmd == 'cat' and len(line) > 1:
				if not self.index:
					print 'Run ls first'
				else:
					print self.index[int(line[1])]
			
			if cmd == 'comm' and len(line) > 1:
				if not self.index:
					print 'Please run the "ls" command first.'
				else:
					program = self.index[int(line[1])]
					cmd = myth.protocol.QueryCommBreak(program.getChannelID(), int(mktime(program.getStartTime())))
					cmd.setSock(self.sock)
					cmd.sr()
					self.commList = cmd.breakList()
					for i in cmd.breakList():
						print repr(i)

			if cmd == 'stoprec' and len(line) > 1:
				if not self.index:
					print 'Please run the "ls" command first to retreive a list of recordings.'
				else:
					requested = int(line[1])
					query = self.sendCommand(myth.protocol.StopRecording(self.index[requested]))
					print 'Deleted', self.index[requested].getTitle() + ': ' + self.index[requested].getSubtitle()

			if cmd == 'check' and len(line) > 1:
				if not self.index:
					print 'Please run the "ls" command first to retreive a list of recordings.'
				else:
					requested = int(line[1])
					query = self.sendCommand(myth.protocol.CheckRecording(self.index[requested]))
					if query.active():
						print self.index[requested].getTitle() + ': ' + self.index[requested].getSubtitle(), 'is currently recording.'
					else:
						print self.index[requested].getTitle() + ': ' + self.index[requested].getSubtitle(), 'is not recording.'

			if cmd == 'pending':
				query = self.sendCommand(myth.protocol.QueryGetAllPending())
				pending = query.getPending()
				for program in pending:
					print program.getTitle() + ': ' + program.getSubtitle()
				print len(pending), 'pending recordings'

			if cmd == 'expiring':
				query = self.sendCommand(myth.protocol.QueryGetAllScheduled())
				scheduled = query.getScheduled()
				for program in scheduled:
					print program.getTitle() + ': ' + program.getSubtitle()
				print '\t', len(scheduled), 'recordings scheduled to expire'

			if cmd == 'conflict':
				if not self.index:
					print 'Please run the "ls" command first to retreive a list of recordings.'
				else:
					for program in self.index:
						query = self.sendCommand(myth.protocol.QueryGetConflicting(program))
						if query.getConflicting():
							print program.getTitle() + ': ' + program.getSubtitle(), 'is in conflict'

			if cmd == 'status':
				query = self.sendCommand(myth.protocol.QueryFreeSpace())
				total, used, free = query.getSpace()
				print 'Disk usage:'
				print '\tTotal:\t', total / 1000000, 'GB'
				print '\tUsed:\t', used / 1000000, 'GB'
				print '\tFree:\t', free / 1000000, 'GB'
				query = self.sendCommand(myth.protocol.QueryMemStats())
				totalv, usedv, freev = query.getVirtual()
				totalp, usedp, freep = query.getPhysical()
				print 'Physical memory usage:'
				print '\tTotal:\t', totalp, 'MB'
				print '\tUsed:\t', usedp, 'MB'
				print '\tFree:\t', freep, 'MB'
				print 'Virtual memory usage:'
				print '\tTotal:\t', totalv, 'MB'
				print '\tUsed:\t', usedv, 'MB'
				print '\tFree:\t', freev, 'MB'
				
				query = self.sendCommand(myth.protocol.QueryLoad())
				print 'Load average:', repr(query.getLoads())
				query = self.sendCommand(myth.protocol.QueryUptime())
				days = (query.getUptime() / 60.0) / 24.0
				print 'Uptime:', days, 'days'

			if cmd == 'checkfile' and len(line) > 1:
				query = self.sendCommand(myth.protocol.QueryCheckFile(line[1]))
				if query.exists():
					print 'File exists!'
				else:
					print 'File not found.'

			if cmd == 'guidedata':
				query = self.sendCommand(myth.protocol.QueryGuideDataThrough())
				print 'Guide data available until:', strftime("%A, %B %d, %Y %H:%M:%S", query.getDate())

			if cmd == 'transfer' and len(line) > 1:
				if not self.index:
					print 'Please run the "ls" command first.'
				else:
					rec = self.index[int(line[1])]
					self.player = Player(self.sock, rec)
					self.player.start()

			if cmd == 'pause':
				self.player.pause()
					
			if cmd == 'seek' and len(line) > 1:
				self.player.seek(int(line[1]))

			if cmd == 'goto':
				self.player.goto(int(line[1]))

			if cmd == 'pos':
				print 'At position %s / %s' % (self.player.pos, self.player.filesize)
	
	def sendCommand(self, cmd):
		cmd.setSock(self.sock)
		cmd.sr()
		return cmd

class Player(Thread):
	blockSize = 4096
	pos = 0
	
	def __init__(self, sock, recording):
		Thread.__init__(self)
		self.sock = sock
		self.recording = recording
		self.execpath = "/Applications/VLC.app/Contents/MacOS/VLC"
		self.execpath += " --sout \"#transcode{vcodec=mp2v,vb=1500,venc=ffmpeg,scale=0.5,threads=2}:standard{access=udp,mux=ts,dst=10.1.1.196}\" - 2>&1 >>/tmp/mythproto.log"
		#self.execpath += " --sout \"#transcode{vcodec=mp4v,vb=128,venc=ffmpeg,scale=0.5,acodec=mp3,ab=64,threads=2,aenc=ffmpeg}:standard{access=udp,mux=ts,dst=192.168.10.100}\" - 2>&1 >>/tmp/mythproto.log"
		#self.execpath = "/Applications/VLC.app/Contents/MacOS/VLC - 2>/dev/null >/dev/null"

		self.paused = False
		#cbquery = myth.protocol.QueryCommBreak(self.recording.getChannelID(), int(mktime(self.recording.getStartTime())))
		#cbquery.setSock(self.sock)
		#cbquery.sr()
		#self.breakList = cbquery.breakList()
		self.breaks = []
		#bstart = 0
		#bend = 0
		#for cbreak in self.breakList:
		#	point = cbreak[1]
		#	if cbreak[0] == 0:
				# This is a commercial start point
		#		bstart = point
		#	else:
				# This is a commercial end point
		#		bend = point
		#		self.breaks.append((bstart, bend))
		#print repr(self.breaks)
		
		self.dataSocket = socket()
		self.dataSocket.connect(('10.1.1.6', 6543))
		
		cmd = myth.protocol.AnnounceFileTransfer('mythproto', self.recording.getFilename())
		cmd.setSock(self.dataSocket)
		cmd.sr()
		
		self.transfer = myth.protocol.FileTransfer(cmd.getSocket())
		self.transfer.setSock(self.sock)
		self.filesize = cmd.getSize()
		self.bitrate = (self.filesize / int(mktime(self.recording.endts) - mktime(self.recording.startts))) * 10
		
		self.stdin, self.stdout = os.popen2(self.execpath, "b")

	def run(self):
		try:
			#while self.pos < self.filesize:
			while True:
				while self.paused:	sleep(1)
				if len(self.breaks) > 0:
					bstart = self.breaks[0][0]
					bend = self.breaks[0][1]
					if (self.pos + self.blockSize) > bstart:
						print 'Skipping from %s to %s' % (self.pos, bend)
						self.transfer.seek(bend)
						del self.breaks[0]
				self.transfer.requestBlock(self.blockSize)
				msg = self.dataSocket.recv(self.blockSize)
				while len(msg) < self.blockSize:
					msg += self.dataSocket.recv(self.blockSize - len(msg))
				self.pos += len(msg)
				self.stdin.write(msg)
			cmd = myth.protocol.Done()
			cmd.setSock(self.dataSocket)
			cmd.sr()
			self.dataSocket.close()
		except IOError:
			print 'Error caught at position:', self.pos, '/', self.filesize
			print self.stdout.read()
		print 'Transfer of %s complete.' % self.recording
	
	def stopPlaying(self):
		self.stdin.close()
		self.stdout.close()
		cmd = myth.protocol.Done()
		cmd.setSock(self.sock)
		cmd.sr()
		cmd.setSock(self.dataSocket)
		cmd.sr()
		self.sock.close()
		self.dataSocket.close()
		self.join()
	
	def seek(self, distance):
		print 'Seeking', distance, 'seconds'
		distance = distance * (self.bitrate / 10)
		print 'Seeking\t', distance, 'bytes'
		targetBlock = self.pos + distance
		print 'Target\t', targetBlock
		
		if targetBlock < self.filesize and targetBlock > 0:
			self.transfer.seek(self.pos + distance)
			self.pos += distance
		else:
			print 'Seeking too far. Max seek distance:', self.filesize - self.pos
	
	def goto(self, pos):
		self.pos = pos
	
	def getNextBreak(self):
		if len(self.breakList) > 1:
			self.breakStart = self.breakList[0][1]
			self.breakEnd = self.breakList[1][1]
			self.breakList.remove(self.breakList[0])
			self.breakList.remove(self.breakList[1])
		else:
			self.breakStart = None
			self.breakEnd = None
	
	def pause(self):
		self.paused = not self.paused
