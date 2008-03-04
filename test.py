import myth.frontend
import socket

frontend = myth.frontend.Frontend(('10.1.1.6', 6543))

#sock = socket.socket()
#sock.connect(('10.1.1.6', 6543))

#version = myth.protocol.ProtocolVersion(sock, 31)
#version.send()
#version.recv()

#ann = myth.protocol.Announce(sock, 'chipotle')
#ann.send()
#ann.recv()

#filetrans = myth.protocol.AnnounceFileTransfer(sock, 'chipotle', '/2131_20061108060653.mpg')
#filetrans.send()
#filetrans.recv()
#print 'Socket: ', filetrans.getSocket()
#print 'Size: ', filetrans.getSize()

#slave = myth.protocol.AnnounceSlave(sock, 'chipotle.csh.rit.edu')
#slave.send()
#slave.recv()

#recordings = myth.protocol.QueryRecordings(sock)
#recordings.send()
#recordings.recv()
#rec = recordings.getRecordings()

#freespace = myth.protocol.QueryFreeSpace(sock)
#freespace.send()
#freespace.recv()
#print repr(freespace.getSpace())

#load = myth.protocol.QueryLoad(sock)
#load.send()
#load.recv()
#print repr(load.getLoads())

#uptime = myth.protocol.QueryUptime(sock)
#uptime.send()
#uptime.recv()
#print uptime.getUptime()

#mem = myth.protocol.QueryMemStats(sock)
#mem.send()
#mem.recv()
#print 'Virtual: ', repr(mem.getVirtual())
#print 'Physical:', repr(mem.getPhysical())

#checkfile = myth.protocol.QueryCheckFile(sock, '2131_20061108060653.mpg')
#checkfile.send()
#checkfile.recv()
#print 'File exists: ', repr(checkfile.exists())

#guidedata = myth.protocol.QueryGuideDataThrough(sock)
#guidedata.send()
#guidedata.recv()
#print "Guide data available until: ", repr(guidedata.getDate())

#stoprecord = myth.protocol.StopRecording(sock, rec[0])
#stoprecord.send()
#stoprecord.recv()

#checkrecord = myth.protocol.CheckRecording(sock, rec[12])
#checkrecord.send()
#checkrecord.recv()
#print rec[12]
#print 'Starttime: ', rec[12].getStartTime()

#for i in range(len(rec)):
#	print i, '\t', rec[i].getTitle()

#deleterec = myth.protocol.DeleteRecording(sock, rec[12])
#deleterec.send()
#deleterec.recv()

#resched = myth.protocol.RescheduleRecordings(sock, rec[12].getRecordID())
#resched.send()
#resched.recv()

#forget = myth.protocol.ForgetRecording(sock, rec[12])
#forget.send()
#forget.recv()

#pending = myth.protocol.QueryGetAllPending(sock)
#pending.send()
#pending.recv()
#rec = pending.getPending()

#for i in range(len(rec)):
#	print rec[i].getTitle()
#print len(rec), 'pending recordings'

#scheduled = myth.protocol.QueryGetAllPending(sock, scheduled=True)
#scheduled.send()
#scheduled.recv()
#sch = scheduled.getPending()
#for i in sch:
#	print i.getTitle()
#print len(sch), 'scheduled recordings'

#conflict = myth.protocol.QueryGetConflicting(sock, rec[0])
#conflict.send()
#conflict.recv()

#expire = myth.protocol.QueryGetAllExpiring(sock)
#expire.send()
#expire.recv()

#for i in expire.getExpiring():
#	print i.getTitle()

#freeRec = myth.protocol.GetFreeRecorder(sock)
#freeRec.send()
#freeRec.recv()

#freeCount = myth.protocol.GetFreeRecorderCount(sock)
#freeCount.send()
#freeCount.recv()

#freeList = myth.protocol.GetFreeRecorderList(sock)
#freeList.send()
#freeList.recv()

#rec = myth.protocol.QueryRecorder(sock, 1)
#rec.send()
#rec.recv()

#isrec = myth.protocol.RecorderIsRecording(sock, 2)
#isrec.send()
#isrec.recv()
#print repr(isrec.getRecording())

#done = myth.protocol.Done(sock)
#done.send()
#done.recv()

#sock.close()
