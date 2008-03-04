def decodeLongLong(lst):
	high = int(lst[0]) << 32
	low = int(lst[1])
	if low < 0:
		low += 4294967296
	if high < 0:
		high += 4294967296
	return high + low

def encodeLongLong(i):
	high = int(i / 4294967296)
	low = i - high
	return high, low

def parseOk(str):
	if str == 'ok':
		return True
	else:
		return False

def printList(lst):
	#for i in range(len(lst)):
	#	print i, '\t', repr(lst[i])
	pass

# t is a nine item tuple returned by the time module. This method converts it to
# MythTV's standard representation used on filenames
def encodeTime(t):
	ret = ''
	for i in t[:-3]:
		si = str(i)
		if len(si) < 2:
			ret += si.zfill(2)
		else:
			ret += si
	return ret
