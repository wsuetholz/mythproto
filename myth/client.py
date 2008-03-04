from myth.protocol import ProtocolVersion, Announce, QueryRecordings, AnnounceFileTransfer, FileTransfer
from socket import socket
from time import sleep
import sys

BLOCK_SIZE = 4096

class MythClient:
	def __init__(self, server, client_name='MythClient', port=6543, version=31):
		self.server = server
		self.port = port
		self.client_name = client_name

		self.sock = socket()
		self.sock.connect((server, port))

		self.send(ProtocolVersion(version))
		self.send(Announce(client_name))
		
	def send(self, cmd, sock=None):
		if not sock:
			sock = self.sock
		cmd.setSock(sock)
		cmd.sr()
		return cmd
	
	def getRecordings(self):
		return self.send(QueryRecordings()).getRecordings()
	
	def transfer(self, recording):
		transfer_sock = socket()
		transfer_sock.connect((self.server, self.port))
		transfer = self.send(AnnounceFileTransfer(self.client_name, recording.getFilename()), sock=transfer_sock)
		control = self.send(FileTransfer(transfer.getSocket()))

		self.bitrate = recording.getBitrate()
		self.paused = False
		datalen = BLOCK_SIZE
		filesize = transfer.getSize()
		self.position = 0
		while self.position < filesize:
			if self.paused:
				sleep(0.2)
			else:
				if datalen >= BLOCK_SIZE:
					# If we received the entire block in the last packet.
					control.requestBlock(BLOCK_SIZE)
					data = transfer_sock.recv(BLOCK_SIZE)
					datalen = len(data)
					self.position += datalen
				else:
					# If the packet was incomplete, finish the transfer.
					data = transfer_sock.recv(BLOCK_SIZE)
					datalen += len(data)
					self.position += len(data)
				yield data
	
	def transfer_stdout(self, recording):
		for block in self.transfer(recording):
			sys.stdout.write(block)
	
	def transfer_seek(self, seconds):
		if self.position:
			self.position += seconds * bitrate
			return self.position
		else:
			return False
	
	def transfer_pause(self):
		self.paused = not self.paused
