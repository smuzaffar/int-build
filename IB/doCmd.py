#!/usr/bin/env python

import os, sys, time


# ================================================================================

class ActionError(Exception):
    def __init__(self, msg):
        self.msg = msg
        return
    def __str__(self):
        return repr(self.msg)

#================================================================================

def doCmd(cmd, dryRun=False, inDir=None):
    if not inDir:
        print "--> "+time.asctime()+ " in ", os.getcwd() ," executing ", cmd
    else:
        print "--> "+time.asctime()+ " in " + inDir + " executing ", cmd
        cmd = "cd " + inDir + "; "+cmd
	
    sys.stdout.flush()
    sys.stderr.flush()
        
    start = time.time()
    ret = 0
    while cmd.endswith(";"): cmd=cmd[:-1]
    if dryRun:
        print "DryRun for: "+cmd
    else:
        from commands import getstatusoutput
        ret, outX = getstatusoutput(cmd)
        if outX: print outX
            
    # do the logging before raising an Error
    stop = time.time()
    print "--> "+time.asctime()+" cmd took", stop-start, "sec. ("+time.strftime("%H:%M:%S",time.gmtime(stop-start))+")"
    sys.stdout.flush()
    sys.stderr.flush()
    
    if ret != 0 :
        msg = "ERROR: cmd returned :" + str(ret)
        raise ActionError(msg)

    return ret

