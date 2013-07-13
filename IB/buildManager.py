#!/usr/bin/env python

import os, sys, time, glob

scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

import doCmd
from BuilderBase import BuilderBase
import config

# ================================================================================

class BuildManager(BuilderBase) :

    def __init__(self, rel,ibdate=None, ibstamp=None):

        BuilderBase.__init__(self)
        if ibstamp and ibdate:
            self.stamp = ibstamp
            self.timeStamp = ibdate

        self.buildDir = os.path.join(self.topBuildDir, "rc", self.stamp, rel)
        self.relCycle = rel
        
        return

    # --------------------------------------------------------------------------------

    def cleanupOld(self):
        daysToKeep = 3
        dirsToCheck = [ self.topBuildDir+'/rc/*-*', self.cmsswBuildDir+'/CMSSW_*', self.topBuildDir+'/Install/*/www/*/*-*-*', self.topBuildDir+'/Install/*/*/*-*-*' ]
        delDirOlder = time.time() - (86400 * daysToKeep)
        print 'Cleanup> deleting releases older than ',daysToKeep,' days'
        for xdir in dirsToCheck:
            for sdir in glob.glob(xdir):
                if os.path.getctime(sdir)<=delDirOlder:
                    try:
                        self.doCmd('rm -rf '+sdir, self.dryRun)
                    except:
                        pass
        cmd = 'rm -rf '
        for d in [ 'tmp*' , 'SOURCES', 'SPEC', 'SRPMS' ]: cmd += self.cmsBuildDir+'/'+d+' '
        self.doCmd(cmd, self.dryRun)
        return

    # --------------------------------------------------------------------------------

    def checkout(self):
	if os.path.exists(self.buildDir):
	    cmd = "rm -rf " + self.buildDir
	    self.doCmd(cmd, True, self.topBuildDir)
        os.makedirs(self.buildDir)
        self.updateTimeStamp(self.buildDir)
        self.cleanupOld()
        cmd = 'cp -r '+scriptPath+' IB'
        self.doCmd(cmd, True, self.buildDir)
        return

    # --------------------------------------------------------------------------------

    def startBuild(self, buildDir=None):
        if buildDir: self.buildDir = buildDir
        os.environ['CMSINTBLD_RCDIR'] = self.buildDir

	self.updateTimeStamp(self.buildDir)

	os.environ["PATH"] = self.buildDir+"/cms/common:"+os.environ["PATH"]
        from logUpdater import LogUpdater
	logger = LogUpdater(self.buildDir)
	logger.setDryRun(self.dryRun)
	logger.setRelease("", self.relCycle, self.stamp)
	
	if not os.path.exists(self.cmsBuildDir):
            os.makedirs(self.cmsBuildDir)

        logDir = self.buildDir+'/'+self.relCycle+'/'+self.plat
	logFileName = logDir+"/fullLog"
	
	cmd = 'rm -rf '+self.relCycle+'; mkdir -p '+logDir+'; '
	cmd += scriptPath+"/buildNightly.py "
        cmd += " --releasecycle " + self.relCycle + ' '
        cmd += " --buildDir " + self.buildDir + ' '

	if self.dryRun : cmd += ' --dryRun '

        cmd += ' > '+logFileName+' 2>&1 '
        
        self.doCmd(cmd, True, self.buildDir)

        print "log file at " + self.buildDir + "/fullLog"

        webLogPath  = logger.webTargetDir
	if not os.path.exists(webLogPath):
            os.makedirs(webLogPath)
            
        cmd = 'cp '+logFileName+' '+webLogPath
        self.doCmd(cmd, True)

        if self.dryRun :
            sys.stdout.flush()
            sys.stderr.flush()
            os.system('cat '+logFileName)
        else:
            print "\n"
            print "web portal at:\n"
            print "http://cmssdt.cern.ch/SDT/cgi-bin/showIB.py?rc="+self.relCycle+"\n"
            print "http://cmssdt.cern.ch/SDT/cgi-bin/showIB.py\n"
            print "+"*80
            print "\n"

        sys.stdout.flush()
        sys.stderr.flush()
        
        return

# ================================================================================

def usage():
    print "usage:", os.path.basename(sys.argv[0]), " --releasecycle <rel> [--dryRun] [--buildDir <dir>] [--ibdate <IB-DateTime>]"
    print """
    where:
       <IB-DateTime> is of form YYYY-MM-DD-hhhh
       <rel>    is the release cycle to be build (e.g. 5.2
    """
    
    return

# ================================================================================

if __name__ == "__main__":

    import getopt
    options = sys.argv[1:]

    try:
        opts, args = getopt.getopt(options, 'hnb:r:s:d:', 
                                   ['help', 'dryRun', 'buildDir=', 'releasecycle=','ibdate='])
    except getopt.GetoptError, e:
        print e.msg
        usage()
        sys.exit(-2)

    dryRun  = False
    rel     = None
    buildDir = None
    ibdate = None
    ibstamp = None
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()

        if o in ('-n', '--dryRun',):
            dryRun = True

        if o in ('-r', '--releasecycle',):
            rel = a
            
        if o in ('-d', '--ibdate',):
            ibdate = a
            ibstamp = config.date2daystamp(ibdate)
            if not ibstamp:
                print 'ERROR: Can not convert date '+ibdate+' to a valid day stamp. Valid --ibdate should be of format YYYY-MM-DD-hhhh'
                sys.exit(1)
            
        if o in ('-b', '--buildDir',):
            buildDir = a

    plat = None
    try:
        plat = os.environ["SCRAM_ARCH"]
    except KeyError:
        plat = "slc5_ia32_gcc434" # assume this for now ...
        os.environ["SCRAM_ARCH"] = plat # make sure we have it for the others :)


    if not rel :
        usage()
        sys.exit(-1)

    bmgr = BuildManager(rel,ibdate,ibstamp)
    bmgr.setDryRun(dryRun)

    if not buildDir:
        from Lock import Lock
        lock = Lock(bmgr.topBuildDir+'/buildLock')
        if not lock:
            print 'WARNING: Another build is still running on '+config.getHostName()+' for release cycle '+rel
        else:
            bmgr.checkout()
            bmgr.startBuild(buildDir)
    else:
        bmgr.startBuild(buildDir)
   
    sys.exit(0)
    
