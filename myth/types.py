from time import localtime, mktime, strftime

# This class mimics the ProgramInfo class in the mythtv tree. Essentially, it exists
# to keep data structures tidy.
class ProgramInfo:
	title = ''
	subtitle = ''
	description = ''
	category = ''
	chanid = ''
	chanstr = ''
	chansign = ''
	channame = ''
	pathname = ''
	filesize = 0
	startts = localtime()
	endts = localtime()
	duplicate = 0
	shareable = True
	findid = 0
	hostname = ''
	sourceid = 0
	cardid = 0
	inputid = 0
	recpriority = 0
	recstatus = ''
	recordid = 0
	rectype = ''
	dupin = ''
	dupmethod = ''
	recstartts = localtime()
	recendts = localtime()
	repeat = False
	programflags = 0
	recgroup = ''
	chancommfree = False
	chanOutputFilters = ''
	seriesid = ''
	programid = ''
	lastmodified = localtime()
	stars = 0.0
	originalAirDate = localtime()
	hasAirDate = False
	playgroup = ''
	recpriority2 = ''
	parentid = 0

	def getBitrate(self):
		return (self.filesize / int(mktime(self.endts) - mktime(self.startts)))

	def getTitle(self):
		return self.title
	
	def getSubtitle(self):
		return self.subtitle
	
	def getRecordID(self):
		return self.recordid
	
	def getChannelID(self):
		return self.chanid
	
	def getFilename(self):
		return self.pathname
	
	def getStartTime(self):
		return self.startts
	
	def __init__(self, lst, offset=0):
		self.title =		lst[offset + 1]
		self.subtitle =		lst[offset + 2]
		self.description =	lst[offset + 3]
		self.category =		lst[offset + 4]
		self.chanid =		lst[offset + 5]
		self.chanstr =		lst[offset + 6]
		self.chansign =		lst[offset + 7]
		self.channame =		lst[offset + 8]
		self.pathname =		lst[offset + 9]
		if lst[offset + 10] != '':
			self.filesize =	(int(lst[offset + 10]) * 4294967296) + int(lst[offset + 11])
		else:
			self.filesize = int(lst[offset + 11])
		self.startts =		localtime(int(lst[offset + 12]))
		self.endts =		localtime(int(lst[offset + 13]))
		self.duplicate =	int(lst[offset + 14])
		self.shareable =	bool(int(lst[offset + 15]))
		self.findid =		int(lst[offset + 16])
		self.hostname =		lst[offset + 17]
		if lst[offset + 18] != '':
			self.sourceid =		int(lst[offset + 21])
		self.cardid =		int(lst[offset + 19])
		self.inputid =		int(lst[offset + 20])
		self.recpriority =	int(lst[offset + 21])
		self.recstatus =	lst[offset + 22]
		self.recordid =		int(lst[offset + 23])
		self.rectype =		lst[offset + 24]
		self.dupin =		lst[offset + 25]
		self.dupmethod =	lst[offset + 26]
		self.recstartts =	localtime(int(lst[offset + 27]))
		self.recendts =		localtime(int(lst[offset + 28]))
		self.repeat =		bool(int(lst[offset + 29]))
		self.programflags =	int(lst[offset + 30])
		self.recgroup = 	lst[offset + 31]
		self.chancommfree = bool(int(lst[offset + 32]))
		self.chanOutputFilters = lst[offset + 33]
		self.seriesid =		lst[offset + 34]
		self.programid =	lst[offset + 35]
		self.lastmodified =	localtime(int(lst[offset + 36]))
		self.stars =		float(lst[offset + 37])
		self.originalAirDate = localtime(int(lst[offset + 38]))
		self.hasAirDate =	bool(int(lst[offset + 39]))
		self.playgroup =	lst[offset + 40]
		#self.recpriority2 =	lst[offset + 41]
	
	def stringList(self):
		ret = []
		for i in self.objList():
			ret.append(str(i))
		return ret
	
	def __str__(self):
		ret = ''
		lst = self.objList()
		for i in range(len(lst)):
			ret += str(i) + '\t' + str(lst[i]) + '\n'
		return ret

	def objList(self):
		tmp = [
			0,
			self.title,
			self.subtitle,
			self.description,
			self.category,
			self.chanid,
			self.chanstr,
			self.channame,
			self.pathname,
			self.filesize,
			int(mktime(self.startts)),
			int(mktime(self.endts)),
			0,
			int(self.shareable),
			self.findid,
			self.hostname,
			self.sourceid,
			self.cardid,
			self.inputid,
			self.recpriority,
			self.recstatus,
			self.recordid,
			self.rectype,
			self.dupin,
			self.dupmethod,
			int(mktime(self.recstartts)),
			int(mktime(self.recendts)),
			int(self.repeat),
			self.programflags,
			self.recgroup,
			int(self.chancommfree),
			self.chanOutputFilters,
			self.seriesid,
			self.programid,
			int(mktime(self.lastmodified)),
			self.stars,
			int(mktime(self.originalAirDate)),
			int(self.hasAirDate),
			self.playgroup,
			self.recpriority2,
			self.parentid,
			0]
		return tmp

PictureAdjustType = {
	'None':		'0',
	'Playback':	'1',
	'Channel':	'2',
	'Recording':'3'
}

Direction = {
	'Up':		'0',
	'Down':		'1',
	'Favorite':	'2',
	'Left':		'3',
	'Right':	'4'
}

COMM_START = 4
COMM_END = 5
