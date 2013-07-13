#!/usr/bin/env python

import os, sys

scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

from BuilderBase import BuilderBase

# ================================================================================

class WebManager(BuilderBase):

    def __init__(self, cycIn, candIn, dryRun=False):

        BuilderBase.__init__(self)
        
        self.clientDir = os.path.join(self.topBuildDir, 'clientkit','buildkit')
        self.serverBaseURL = 'http://vocms12/'
        self.dryRun = dryRun
        self.cycle = cycIn
        self.cand  = candIn
        
        return

# --------------------------------------------------------------------------------

    def doCmd(self, cmdIn):

		# no-op : there is no server for this any more.
		# so remove the action as a first step, later remove the file
		# once there are no more references to it ...

        return

# --------------------------------------------------------------------------------

    def srvStatus(self):

        lines = []
        try:
            statPg = open('status.html', 'r')
            lines = statPg.readlines()
            statPg.close()
        except IOError:
            # print "ERROR: no status report from server found, continuing nevertheless ... "
            return True
        
        if "".join(lines).find("STATUS=0") != -1:
            return True

        for line in lines:
            if line.find("ERROR:") != -1:
                print line

        return False

# --------------------------------------------------------------------------------

    def setupJob(self, desc):

        cmd = self.clientDir
        cmd += '/job-script.pl --mode setup '
        cmd += ' --statmsg "Build Started"'
        cmd += ' --description "'+desc+'"'

        self.doCmd(cmd)
        
        return

# --------------------------------------------------------------------------------

    def uploadPkgList(self, tcTag):
        cmd = self.clientDir
        cmd += '/file-uploader.pl --type PackList ' # '/upload-packagelist.pl '
        cmd += ' --tctag '+tcTag

        self.doCmd(cmd)
        return

# --------------------------------------------------------------------------------

    def uploadLog(self, logFileName=None):
        cmd = self.clientDir
        cmd += '/file-uploader.pl --type Log ' # '/upload-logfile.pl '
        cmd += ' --file '+logFileName  # '--log '
        self.doCmd(cmd)
        return

# --------------------------------------------------------------------------------

    def tearDown(self, msg):
        cmd = self.clientDir
        cmd += '/job-script.pl --mode teardown '
        cmd += ' --statmsg "Build Finished"'

        self.doCmd(cmd)
        return

# --------------------------------------------------------------------------------

    def sendMsg(self, msg):
        cmd = self.clientDir
        cmd += '/update-status-msg.pl --msg "'+msg+'" '

        self.doCmd(cmd)
        return

# ================================================================================

def usage():
    print "usage: ", os.path.basename(sys.argv[0])," --cycle <cycle> --candidate <cand> --log <log> "
    return

# ================================================================================

if __name__ == "__main__" :
    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'hn',
                                   ['help','dryRun','cycle=','candidate=','logFile=','phase=','tcTag=','msg='])
    except getopt.GetoptError:
        usage()
        sys.exit(-2)

    dryRun = False
    cycle  = None
    cand   = None
    log    = None
    phase  = None
    tcTag  = None
    msg    = "Dummy message"
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
            
        if o in ('n', '--dryRun',):
            dryRun = True

        if o in ('--cycle',):
            cycle = a

        if o in ('--candidate',):
            cand = a

        if o in ('--logFile',):
            log = a

        if o in ('--phase',):
            phase = a

        if o in ('--tcTag',):
            tcTag = a

        if o in ('--msg',):
            msg = a

    if not cycle or not cand or not log:
        print "none of cycle, candidate or logfile given!"
        usage()
        sys.exit(-1)

    if not tcTag:
        tcTag = cycle+"_"+cand
    
    wm = WebManager(cycle, cand, dryRun)

    desc = "Fake for testing"
    if not phase or phase=="start":
        wm.setupJob(desc)

    if not phase or phase=="ulPkg":
        wm.uploadPkgList(tcTag)

    if not phase or phase=="ulLog":
        wm.uploadLog(log)

    if not phase or phase=="msg":
        print "going to send ", msg
        wm.sendMsg(msg)

    msg = "Dummy teardown msg"
    if not phase or phase=="stop":
        wm.tearDown(msg)

        
