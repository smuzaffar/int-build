#!/usr/bin/env python

import sys,os,time
from Lock import Lock
from threading import Thread
class GetRawRefFile(Thread):
    def __init__(self, castorFile, localFile):
        Thread.__init__(self)
        self.castorFile = castorFile
	self.localFile = localFile
        return
    
    def run(self):
	ret = 0
	try:
            ret = os.system('rfcp '+self.castorFile+' '+self.localFile)
	except:
	    ret = 1
        if ret != 0:
            print "ERROR copying rawRefFile ", self.castorFile, ' to ', self.localFile
            print "      rfcp returned: ", ret
	return
	                
def getRawRefs():
    import PerfSuiteRawRef
    threadList = []
    if not os.path.exists(PerfSuiteRawRef.rawRefDir):
        os.makedirs(PerfSuiteRawRef.rawRefDir)
    for castorDir, refList in PerfSuiteRawRef.referenceFiles.items():
        for rem, ref in refList.items():
            if os.path.exists(PerfSuiteRawRef.rawRefDir+'/'+ref) :
                print "Ignoring existing rawRefFile ", ref
                continue
            else:
	        t = GetRawRefFile(castorDir+rem,PerfSuiteRawRef.rawRefDir+ref)
		t.start()
		threadList.append(t)
    for t in threadList: t.join()

xLock = Lock('prefSuit.rawRef.lock')
xLock.getLock(10,1000)
getRawRefs()
