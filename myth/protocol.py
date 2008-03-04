from time import strptime
from myth.types import ProgramInfo
from myth.util import *

DEBUG = False
RECV_BUFFER = 4096

# Superclass for all commands in the mythtv protocol. Formats and sends data to
# the server. This class should not be used directly.
#	sock = A socket object representing an active connection to the server
class Command:
	cmd = ''
	args = []
	version = 0

	def __init__(self, sock):
		self.sock = sock
	
	def getPayload(self):
		payload = self.cmd
		argstr = ''
		for arg in self.args:
			argstr += '[]:[]' + arg
		payload += argstr
	
		size = str(len(payload))
		if len(size) < 8:
			size += ' ' * (8 - len(size))

		payload = size + payload
		return payload

	def setSock(self, sock):
		self.sock = sock
	
	def log(self, msg):
		if DEBUG:
			print msg
	
	def send(self):
		msg = self.getPayload()
		size = 0
		while size < len(msg):
			msg = msg[size:]
			self.log('--> ' + msg)
			size = self.sock.send(self.getPayload())
	
	# Do not call this method
	def recv(self):
		msg = self.sock.recv(RECV_BUFFER)

		if len(msg) > 7:
			size = int(msg[:8])
		else:
			size = 0

		if len(msg[8:]) > 0:
			response = msg[8:]
		else:
			response = ''

		while len(response) < size:
			response += self.sock.recv(RECV_BUFFER)

		self.response = response.split('[]:[]')
		self.log('<-- ' + repr(self.response))
		return self.response
	
	def sr(self):
		self.send()
		self.recv()
	
	# Subclasses should override this method if they want to act upon a server
	# response to the request.
	def response(self, response):
		pass

# Announce this host to the server. This command must be completed before most
# other commands.
#	hostname = This client's hostname
#	wantEvents = True if you want this client to receive events
#	preventShutdown = True if you want this client to prevent the server from
#					  shutting down while still connected
class Announce(Command):
	def __init__(self, hostname, wantEvents=True, preventShutdown=False):
		if wantEvents:
			events = '1'
		else:
			events = '0'

		if preventShutdown:
			mode = 'Playback '
		else:
			mode = 'Monitor '

		self.cmd = 'ANN ' + mode + events

# Announce this host to the server as a slave backend. Slaves do not block
# shutdowns.
# TODO: This command requires an encoder list. I'm not sure what format or what
# kind of data it needs. If you know, shoot me an email synack at csh.rit.edu
#	hostname = This host's hostname.
#	ip = The IP address of this slave, routable from the connected server. If
#		 this parameter isn't specified, we'll attempt to resolve it based on
#		 the supplied hostname. Will raise an exception if we can't resolve it.
#	encoderList = A list of this slave's encoders
class AnnounceSlave(Command):
	def __init__(self, hostname, ip=None, encoderList='test'):
		if not ip:
			ip = self.sock.getsockname()[0]
		self.cmd = 'ANN SlaveBackend ' + hostname + ' ' + ip + ' ' + encoderList

# Negotiate a protocol version with the server. If the server's version is the
# same, args[0] will equal '', otherwise it will be 'REJECT' with the server's
# protocol version in args[1]. The rejected() method returns the server's
# version if they don't match... If the backend version matches, it returns
# False.
#	version = This client's version number
class ProtocolVersion(Command):
	def __init__(self, version=31):
		self.cmd = 'MYTH_PROTO_VERSION ' + str(version)
	
	def rejected(self):
		if self.response[0] == 'REJECT':
			return int(self.response[1])
		else:
			return False

# Request a file transfer from the server. It will return a socket id and a 64
# bit file size. Use the getSocket() and getSize() methods to parse the data
# after sending the request
#	hostname = This client's hostname
#	filename = The name of the file to request
class AnnounceFileTransfer(Command):
	def __init__(self, hostname, filename, readAhead=True, retries=1):
		self.cmd = 'ANN FileTransfer ' + hostname
		if readAhead:
			ahead = str(1)
		else:
			ahead = str(0)

		self.args = [filename, ahead, str(retries)]
	
	def getSocket(self):
		return int(self.response[1])
	
	def getSize(self):
		return decodeLongLong(self.response[2:])

# Get a list of recordings from the server. The getRecordings()  method splits
# the  list sent back from the server into separate field lists for each
# recording.
#	type = The type of query you wish to perform. At the moment, this field is
#		   required and may contain any value. However, if the type is set to
#		   "Delete", the query will be sorted in descending order and is not
#		   guaranteed to work with the getRecordings() method provided here.
#		   The default value of "Play" works just fine.
class QueryRecordings(Command):
	def __init__(self, type='Play'):
		version = 31
		self.cmd = "QUERY_RECORDINGS " + type
	
	def getRecordings(self):
		fieldCount = 42
		recordings = []
		for i in range(len(self.response) / fieldCount):
			start = fieldCount * i
			end = start + fieldCount
			#printList(self.response[start:end])
			recordings.append(ProgramInfo(self.response[start:end]))
		return recordings

# Get the free, used, and total disk space available on the server.
#	allHosts = Set to True if you want to get the available space on all
#			   backends, not just the connected one.
class QueryFreeSpace(Command):
	def __init__(self, allHosts=False):
		self.allHosts = allHosts
		if allHosts:
			self.cmd = "QUERY_FREE_SPACE_LIST"
		else:
			self.cmd = "QUERY_FREE_SPACE"

	# Returns the total, used, and free space of the host or hosts requested. If
	# allHosts was True in the constructor, it will return a dict of tuples,
	# with the key being the hostname and the value being a tuple of (total,
	# used, free)
	def getSpace(self):
		if self.allHosts:
			hosts = {}
			for i in range(len(self.response) / 5):
				x = i * 5
				hostname = self.response[x]
				totalH = int(self.response[x + 1])
				totalL = int(self.response[x + 2])
				total = (totalH * 4294967296) + totalL
				usedH = int(self.response[x + 3])
				usedL = int(self.response[x + 4])
				used = (usedH * 4294967296) + usedL
				free = total - used
				hosts[hostname] = (total, used, free)
			return hosts
		else:
			totalH = int(self.response[0])
			totalL = int(self.response[1])
			total = (totalH * 4294967296) + totalL
			usedH = int(self.response[2])
			usedL = int(self.response[3])
			used = (usedH * 4294967296) + usedL
			free = total - used
			return total, used, free

# Get the average system load for the last 1, 5, and 15 minutes from the server.
# Use the getLoads() accessor to get the loads returned as a tuple of floats
class QueryLoad(Command):
	def __init__(self):
		self.cmd = "QUERY_LOAD"
	
	def getLoads(self):
		one = float(self.response[0])
		five = float(self.response[1])
		ten = float(self.response[2])
		return one, five, ten

# Get the system uptime in seconds from the server. The getUptime() accessor
# returns the uptime as an integer (or long int, depending on how large the
# number is)
class QueryUptime(Command):
	def __init__(self):
		self.cmd = "QUERY_UPTIME"
	
	def getUptime(self):
		return int(self.response[0]) / 100

# Get the total, used, and free amounts of physical and virtual memory in units
# of MB from the server. The getPhysical() and getVirtual() accessors return
# three item tuples as (total, used, free)
class QueryMemStats(Command):
	def __init__(self):
		self.cmd = "QUERY_MEMSTATS"
	
	def getPhysical(self):
		total = int(self.response[0])
		free = int(self.response[1])
		used = total - free
		return total, used, free
		pass
	
	def getVirtual(self):
		total = int(self.response[2])
		free = int(self.response[3])
		used = total - free
		return total, used, free

# Check to see if a file exists on the server. The exists() method will return
# a boolean.
#	filename = The file to check
class QueryCheckFile(Command):
	def __init__(self, filename):
		self.cmd = "QUERY_CHECKFILE " + filename
	
	def exists(self):
		if self.response[0] == '1':
			return True
		else:
			return False

# Check to see when the server's guide data ends. The getDate() accessor will
# return a python 9-item tuple that can be used with the time module
class QueryGuideDataThrough(Command):
	def __init__(self):
		self.cmd = "QUERY_GUIDEDATATHROUGH"
	
	def getDate(self):
		return strptime(self.response[0], "%Y-%m-%d %H:%M")

# Stop a recording on the backend. The ok() method will return a boolean of True
# if the stop was succesful.
#	recording = A myth.types.ProgramInfo object representing the recording you
#				wish to terminate.
class StopRecording(Command):
	def __init__(self, recording):
		self.cmd = "STOP_RECORDING"
		self.args = recording.stringList()
	
	def ok(self):
		if self.response[0] != '-1':
			return True
		else:
			return False

# Check to see if a given recording is active. The active() method will return
# a boolean of True if this recording is currently in progress
#	recording = A myth.types.ProgramInfo object representing the recording you
#				want the status of
class CheckRecording(Command):
	def __init__(self, recording):
		self.cmd = "CHECK_RECORDING"
		self.args = recording.stringList()
	
	def active(self):
		if self.response[0] == '0':
			return False
		else:
			return True

# Delete a recording from the backend or slave. The ok() method will return a
# boolean of True if the deletion was successful.
#	recording = A myth.types.ProgramInfo object representing the recording you
#				want to delete.
#	force = True if you want to force the deletion of this recording regardless
#			if the file's existance or state
class DeleteRecording(Command):
	def __init__(self, recording, force=False):
		if force:
			self.cmd = "FORCE_DELETE_RECORDING"
		else:
			self.cmd = "DELETE_RECORDING"
		self.args = recording.stringList()
	
	def ok(self):
		if self.response[0] != '-1':
			return True
		else:
			return False

# Reschedule a recording.
#	recordid = The recordid of the recording you wish to reschedule. It may be
#			   obtained via the ProgramInfo.getRecordID() method
class RescheduleRecordings(Command):
	def __init__(self, recordid):
		self.cmd = "RESCHEDULE_RECORDINGS " + str(recordid)
	
	def ok(self):
		if self.response[0] == '1':
			return True
		else:
			return False

# Forget the recording of a program so that it will be recorded again
#	recording = A myth.types.ProgramInfo object representing the recording you
#				want the backend to forget about.
class ForgetRecording(Command):
	def __init__(self, recording):
		self.cmd = "FORGET_RECORDING"
		self.args = recording.stringList()
		self.version = 31
	
	def ok(self):
		if self.response[0] == '1':
			return True
		else:
			return False

# This is an abstract class to be inherited by commands that need to parse a
# list of string lists into a list of ProgramInfo objects. It provides the
# utility getAll class that performs this function.
class GetAllCommand(Command):
	def getAll(self, offset=0):
		fieldCount = 42
		recordings = []
		for i in range(len(self.response) / fieldCount):
			start = fieldCount * i
			end = start + fieldCount
			recordings.append(ProgramInfo(self.response[start:end], offset))
		return recordings

# Query the backend for a list of all recordings pending deletion. The
# getPending method may be used to return a list of ProgramInfo objects
# representing the recordings.
# Note: The behavior of this command with table and recordid arguments is not
# 		completely implemented/understood. Use these arguments at your own risk.
#	table = Unknown
#	recordid = If specified, the recording associated with this recordid will be
#			   removed from the program table.
class QueryGetAllPending(GetAllCommand):
	def __init__(self, table=None, recordid=None):
		self.version = 31
		self.cmd = "QUERY_GETALLPENDING"
		if table:
			self.cmd += " " + table
		if recordid:
			self.cmd += " " + recordid
	
	def getPending(self):
		return self.getAll(offset=1)

# Query the backend for a list of all recordings scheduled to be deleted. The
# getScheduled method may be used to return a list of ProgramInfo objects
# representing the recordings.
class QueryGetAllScheduled(GetAllCommand):
	def __init__(self):
		self.version = 31
		self.cmd = "QUERY_GETALLSCHEDULED"
	
	def getScheduled(self):
		return self.getAll()

# Query the backend for a list of all recordings scheduled to AutoExpire. The
# getExpiring method may be used to return a list of ProgramInfo objects
# representing the recordings.
class QueryGetAllExpiring(GetAllCommand):
	def __init__(self):
		self.version = 31
		self.cmd = "QUERY_GETEXPIRING"
	
	def getExpiring(self):
		return self.getAll()

# Ask the backend if the given recording is conflicting with another recording
# or not. The getConflicting method will return a boolean representation of the
# conflict status.
#	recording = A ProgramInfo object representing the recording you want to
#				query the status of.
class QueryGetConflicting(Command):
	def __init__(self, recording):
		self.version = 31
		self.cmd = "QUERY_GETCONFLICTING"
		self.args = recording.stringList()
	
	def getConflicting(self):
		if self.response[0] == '0':
			return False
		else:
			return True

# Get the id, ip address, and port of a free recorder.
class GetFreeRecorder(Command):
	def __init__(self):
		self.version = 31
		self.cmd = "GET_FREE_RECORDER"

# Get the number of available recorders. The getCount method exposes the
# response as an integer
class GetFreeRecorderCount(Command):
	def __init__(self):
		self.version = 31
		self.cmd = "GET_FREE_RECORDER_COUNT"
	
	def getCount(self):
		return int(self.response[0])

# Get a list of available recorders. The response is a list of recorder int ids
# represented as strings.
class GetFreeRecorderList(Command):
	def __init__(self):
		self.version = 31
		self.cmd = "GET_FREE_RECORDER_LIST"

# Get a list of commercial breaks. The getBreaks() method can be used to parse
# the server's response. It returns a list of two item tuples. The first item
# is either COMM_START or COMM_END as defined in myth.protocol.types. The
# second item in the tuple is the byte position of the break in the file.
#	chanid = Channel ID that the recording was performed on
#	starttime = The start time in unix seconds of the recording
class QueryCommBreak(Command):
	def __init__(self, chanid, starttime):
		self.version = 31
		self.cmd = "QUERY_COMMBREAK " + str(chanid) + " " + str(starttime)
	
	def breakList(self):
		breakList = []
		count = int(self.response[0])
		for i in range(1, (count / 3) + 1):
			breakType = int(self.response[i])
			breakPos = decodeLongLong((self.response[i + 1], self.response[i + 2]))
			breakList.append((breakType, breakPos))
		return breakList

# The recorder class is an abstraction of a recorder on the backend. Instead of
# the usual interface for interacting with the backend, each of the accessor
# methods run a new command against the backend. This is the model that this
# library will be moving toward in the future.
#	isRecording()	Returns a boolean stating if the recorder is currently
#					recording a program
class Recorder(Command):
	def __init__(self, recnum):
		self.version = 31
		self.cmd = "QUERY_RECORDER " + str(recnum)
	
	# If the recorder is recording something, return true
	def isRecording(self):
		self.args = ["IS_RECORDING"]
		self.sr()
		if self.response[0] == '1':
			return True
		else:
			return False
	
	# Returns the framerate of the recorder
	def getFramerate(self):
		self.args = ["GET_FRAMERATE"]
		return float(self.response[0])
	
	# Gets the total number of frames written
	def getFramesWritten(self):
		self.args = ["GET_FRAMES_WRITTEN"]
		self.sr()
		return decodeLongLong(self.response)
	
	# Returns the current position in the file
	def getFilePosition(self):
		self.args = ["GET_FILE_POSITION"]
		self.sr()
		return decodeLongLong(self.response)
	
	# Returns the maximum possible bitrate this recorder can produce
	def getMaxBitrate(self):
		self.args = ["GET_MAX_BITRATE"]
		self.sr()
		return decodeLongLong(self.response)
	
	# Returns a ProgramInfo object representing the current recording. The
	# GET_RECORDING command achieves the same effect with the only difference
	# being that GET_RECORDING will return a dummy ProgramInfo structure if the
	# recorder doesn't know. We're just going to implement the one that gives us
	# a local error to deal with.
	def getCurrentRecording(self):
		self.args = ["GET_CURRENT_RECORDING"]
		self.sr()
		return ProgramInfo(self.response)
	
	# Returns the keyframe number for the given position
	def getKeyframePosition(self, frame):
		self.args = ["GET_KEYFRAME_POS", str(frame)]
		self.sr()
		return decodeLongLong(self.response)
	
	# Fill the position map from the start frame to the end frame. Returns a
	# boolean indicating success
	def fillPositionMap(self, start, end):
		self.args = ["FILL_POSITION_MAP", str(start), str(end)]
		self.sr()
		return parseOk(self.response[0])
	
	# Tell the recorder that this frontend is ready... For something.
	def frontendReady(self):
		self.args = ["FRONTEND_READY"]
		self.sr()
		return parseOk(self.response[0])
	
	# Cancels the next recording scheduled on this recorder. Set cancel to False
	# if you want to invert the effect of this command (un-cancel a recording)
	def cancelNextRecording(self, cancel=True):
		if cancel:
			cancel = '1'
		else:
			cancel = '0'
		self.args = ["CANCEL_NEXT_RECORDING", cancel]
		self.sr()
		return parseOk(self.response[0])
	
	# Spawn a new Live TV session. Set pip to True if this is a
	# picture-in-picture session. This command will always return OK from the
	# backend, regardless of it's status.
	def spawnLiveTV(self, chanid, pip=False):
		if pip:
			pip = '1'
		else:
			pip = '0'
		self.args = ["SPAWN_LIVETV", str(chanid), pip]
		self.sr()
		return parseOk(self.response[0])
	
	# Stop the Live TV session started by this host. This command will always
	# return OK from the backend, regardless of it's status.
	def stopLiveTV(self):
		self.args = ["STOP_LIVETV"]
		self.sr()
		return parseOk(self.response[0])
	
	# Pause this recorder. Always returns OK.
	def pause(self):
		self.args = ["PAUSE"]
		self.sr()
		return parseOk(self.response[0])
	
	# Finish recording the program and close the file. If the recorder isn't
	# recording anything, this method does nothing. Always returns OK.
	def finishRecording(self):
		self.args = ["FINISH_RECORDING"]
		self.sr()
		return parseOk(self.response[0])
	
	# Tell the schedule about changes to the recording status of the LiveTV
	# recording. Currently the 'recording' parameter is ignored and decisions 
	# are based on the recording group alone. Set recording to 1 to mark as
	# recording, 0 to mark as cancelled, and -1 to base the decision on the
	# recording group. (quoted from tv_rec.cpp) Always returns OK.
	def setLiveRecording(self, recording=0):
		self.args = ["SET_LIVE_RECORDING", str(recording)]
		self.sr()
		return parseOk(self.response[0])
	
	# Returns the recorder's connected inputs.
	def getConnectedInputs(self):
		self.args = ["GET_CONNECTED_INPUTS"]
		self.sr()
		return self.response
	
	# Returns the recorder's current input.
	def getInput(self):
		self.args = ["GET_INPUT"]
		self.sr()
		return self.response
	
	# Set the recorder's current input to 'input'. Returns True if the input
	# was changed successfully, if the specified input is unknown or
	# unavailable, return False
	def setInput(self, input):
		self.args = ["SET_INPUT", input]
		self.sr()
		if self.response[0] == input:
			return True
		else:
			return False
	
	# Toggle the currently tuned channel as a favorite. Always returns OK.
	def toggleChannelFavorite(self):
		self.args = ["TOGGLE_CHANNEL_FAVORITE"]
		self.sr()
		return parseOk(self.response[0])
	
	# Move up or down one channel. If direction = 1, the next channel will be
	# selected, if direction = 2, the previous channel is selected. Always
	# returns OK.
	def changeChannel(self, direction):
		self.args = ["CHANGE_CHANNEL", str(direction)]
		self.sr()
		return parseOk(self.response[0])
	
	# Set the current channel to a new channel, identified by it's channame
	# property.
	def setChannel(self, name):
		self.args = ["SET_CHANNEL", name]
		self.sr()
		return parseOk(self.response[0])
	
	# Set the rate at which to monitor the signal on this encoder. Rate is the
	# number of milliseconds to wait between each signal check. If rate = 0,
	# the check will be disabled. If rate = -1, the old value will be preserved.
	# If notifyFrontend is True, SIGNAL messages are sent to the frontend, if
	# notifyFrontend is False, SIGNAL messages won't be sent.
	def setSignalMonitoringRate(self, rate, notifyFrontend=False):
		self.args = ["SET_SIGNAL_MONITORING_RATE", rate, notifyFrontend]
		self.sr()
		return int(self.response[0])
	
	# The following four methods return an integer representing the value the
	# requested picture attribute on the recorder. They'll probably throw a
	# ValueError if the server doesn't send back a value.
	def getColour(self):
		self.args = ["GET_COLOUR"]
		self.sr()
		return int(self.response[0])
	
	def getContrast(self):
		self.args = ["GET_CONTRAST"]
		self.sr()
		return int(self.response[0])

	def getBrightness(self):
		self.args = ["GET_BRIGHTNESS"]
		self.sr()
		return int(self.response[0])
	
	def getHue(self):
		self.args = ["GET_HUE"]
		self.sr()
		return int(self.response[0])
	
	# The following four methods use the following arguments and return the
	# current value of the attribute if successful, -1 on failure.
	#	pictureType = A value from the myth.types.PictureAdjustType dict stating
	#				  what picture type you want to set the value of.
	#	direction = A boolean stating whether you want the value to go up (True)
	#				or down (False)
	def changeColour(self, pictureType, direction):
		self.args = ["CHANGE_COLOUR", pictureType, int(direction)]
		self.sr()
		return int(self.response[0])
	
	def changeContrast(self, pictureType, direction):
		self.args = ["CHANGE_CONTRAST", pictureType, int(direction)]
		self.sr()
		return int(self.response[0])
	
	def changeBrightness(self, pictureType, direction):
		self.args = ["CHANGE_BRIGHTNESS", pictureType, int(direction)]
		self.sr()
		return int(self.response[0])
	
	def changeHue(self, pictureType, direction):
		self.args = ["CHANGE_HUE", pictureType, int(direction)]
		self.sr()
		return int(self.response[0])
	
	# Check if a channel exists on the current tuner.
	#	channame = The name of the channel you want to check for.
	def checkChannel(self, channame):
		self.args = ["CHECK_CHANNEL", channame]
		self.sr()
		return int(self.response[0])
	
	# Check to see if this tuner has the specified channel or if it's on another
	# tuner. Returns True if this tuner has the channel, False if it's elsewhere
	def hasChannel(self, chanid):
		self.args = ["SHOULD_SWITCH_CARD", str(chanid)]
		self.sr()
		return bool(int(self.response[0]))
	
	# This command checks to see if there are any channels that match the given
	# prefix. It returns a four item tuple (match, complete, extraUseful,
	# neededSpacer). Where match is an integer representing the number of
	# channels that match this prefix, complete is a boolean where True means
	# that this prefix is the complete name of a channel existing on this
	# recorder, extraUseful is a boolean meaning that adding an extra character
	# to the prefix would yield fewer results, and neededSpacer means that a
	# spacer like '.' or '_' was added to the prefix to yield more results.
	# Developer's rant: I have no idea why anybody would want a method like this
	# 					it appears to be extremely specialized with no real
	#					purpose. What's worse, is that it adds quite a bit of
	#					code to the backend that will rarely, if ever, get used.
	#	prefix = The prefix of the channel to check for
	def checkChannelPrefix(self, prefix):
		self.args = ["CHECK_CHANNEL_PREFIX", str(prefix)]
		self.sr()
		return (int(self.response[0]), bool(int(self.response[1])),
				bool(int(self.response[2])), bool(int(self.response[3])))
	
	# Get a subset of ProgramInfo for the next program in the given direction.
	#	chanid = The chanid of the channel to seek from. Optional.
	#	channum = The number of the channel to seek from. This value is used
	#			  if chanid=''
	#	direction = The direction to seek from this channel. Set to any value in
	#				the myth.types.Direction dict.
	#	starttime = The time to retreive a listing for
	def getNextProgramInfo(self, chanid='', channum='', direction=0, starttime=0):
		self.args = ["GET_NEXT_PROGRAM_INFO", channelname, chanid, str(int(direction)), starttime]
		self.sr()
		pginfo = ProgramInfo()
		pginfo.setTitle(self.response[0])
		pginfo.setSubtitle(self.response[1])
		pginfo.setDescription(self.response[2])
		pginfo.setCategory(self.response[3])
		pginfo.setStartTime(self.response[4])
		pginfo.setEndTime(self.response[5])
		pginfo.setCallsign(self.response[6])
		pginfo.setIconPath(self.response[7])
		pginfo.setChannelName(self.response[8])
		pginfo.setChannelID(self.response[9])
		pginfo.setSeriesID(self.response[10])
		pginfo.setProgramID(self.response[11])
		return pginfo
	
	def getChannelInfo(self, chanid):
		self.args = ["GET_CHANNEL_INFO", chanid]
		#### TODO: Implement a Channel class ####
		self.sr()

class FileTransfer(Command):
	def __init__(self, recnum):
		self.cmd = "QUERY_FILETRANSFER " + str(recnum)
	
	# Check to see if the file transfer socket is open
	def isOpen(self):
		self.args = ["IS_OPEN"]
		self.sr()
		return bool(int(self.response[0]))
	
	# Stop the file transfer. Always returns OK
	def done(self):
		self.args = ["DONE"]
		self.sr()
		return parseOk(self.response[0])
	
	# Request that a block be sent, returns the size of the block sent.
	def requestBlock(self, block):
		self.args = ["REQUEST_BLOCK", str(block)]
		self.sr()
		return int(self.response[0])
	
	# Seek to the specified position in the file.
	#	current = Current location in the file to seek from
	# 	offset = Offset from the current position to seek (bytes)
	#	whence = corresponds to the arguments of lseek().
	#			SEEK_SET = 0 (location = offset)
	#			SEEK_CUR = 1 (location = current + offset)
	#	Note: The backend appears to only support SEEK_CUR and SEEK_SET
	def seek(self, offset, current=0, whence=0):
		offhigh, offlow = encodeLongLong(offset)
		curhigh, curlow = encodeLongLong(current)
		self.args = ["SEEK", str(offhigh), str(offlow), str(whence), str(curhigh), str(curlow)]
		self.sr()
		#return decodeLongLong(self.response)
	
	def setTimeout(self, timeout):
		self.args = ["SET_TIMEOUT", str(timeout)]
		self.sr()
		return parseOk(self.response[0])

# Tells the server that we're done with this connection.
class Done(Command):
	def __init__(self):
		self.cmd = 'DONE'
