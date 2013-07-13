#!/usr/bin/env python
 
import os, sys, time
from commands import getstatusoutput
scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)


from BuilderBase import BuilderBase, ActionError

# ================================================================================

class ProjectInstaller(BuilderBase):
    
    # --------------------------------------------------------------------------------

    def __init__(self):
 
        BuilderBase.__init__(self)

	self.afsTopDir = None
        self.cand      = None
        self.release   = None
        self.relDir    = None
        
        self.setupDone = False

        return

    # --------------------------------------------------------------------------------

    def setupCand(self, candIn, relIn, day):

        self.afsTopDir = self.installDir
        self.cand = candIn
        self.release = relIn
        self.tgtDir = os.path.join(self.afsTopDir, self.plat, day, self.cand)
        self.relDir = os.path.join(self.tgtDir)

	print "self.install/afsTopDir is set to as .......... ", self.afsTopDir

        if not os.path.exists(self.relDir) :
            print "creating release dir at: ", self.relDir
            if not self.dryRun:
                os.makedirs(self.relDir)
        
        self.setupDone = True
        
        return

    # --------------------------------------------------------------------------------

    def install(self, buildDir=None):

        if not self.setupDone :
            raise "FATAL: install called before setup was done!"

	print "CWD just before copying the release is ....... ", 

        print "going to copy release to ", self.tgtDir
	if not buildDir:
	    buildDir = os.getcwd()
        cmd  = 'cd '+buildDir+'; tar --exclude=CMSDIST --exclude=PKGTOOLS --exclude=IB --exclude=www/ --exclude=CVS  -cf - * | (cd ' + self.tgtDir + ' ; tar xf - ) ; '
        cmd += 'cd '+self.cmsswBuildDir+'; tar --exclude=www/ --exclude=CVS --exclude=tmp/' + self.plat + '/src  -cf - '+self.release+' | (cd '+self.tgtDir+' ; tar xf - ) '
	self.doCmd(cmd,self.dryRun,buildDir)
        
        self.postInstall()

        return

    # --------------------------------------------------------------------------------
 
    def postInstall(self):

        releaseLocation = os.path.join(self.relDir,self.release)
        error, bldDir = getstatusoutput("cd "+releaseLocation+"; grep 'toolbox *dir=' config/boot.xml | sed 's|.*file:||;s|/cms/cmssw-tool-conf/.*||'")
        cmsDir = os.path.join(self.cmsPathMain,self.plat)
        print "renaming project"
        cmd  = self.cmsinit+"; scram b projectrename; SCRAM_TOOL_HOME="+cmsDir+"/lcg/SCRAMV1/`scram version`/src "
        cmd += " ./config/SCRAM/projectAreaRename.pl "+bldDir+" "+cmsDir+" "+self.plat+"; "
        cmd += " find config -name '*' -type f | xargs sed -i -e 's|"+bldDir+"/|"+cmsDir+"/|g'; "
        cmd += " rm -rf external; scram build -f ExternalLinks"
        self.doCmd(cmd,self.dryRun,releaseLocation)
        print "installing project"

	scramDB = self.installDir+"/"+self.plat+"/scramInfo"
	if not os.path.exists(scramDB):
	    os.makedirs(scramDB)
      
        scramDB = scramDB+"/project.lookup"
	if not os.path.exists(scramDB):
	    self.doCmd("touch "+scramDB,self.dryRun,releaseLocation)
	    
        os.environ["SCRAM_USERLOOKUPDB"]=scramDB
	cmd = self.cmsinit+"; cd "+releaseLocation+"; scram install -f"
        self.doCmd(cmd,self.dryRun,releaseLocation)

        print "Creating status file for QA tests "
        cmd = 'touch '+releaseLocation+'/installed.done'
        self.doCmd(cmd,self.dryRun,releaseLocation)

        return

# ================================================================================

def usage():
    print "usage:", os.path.basename(sys.argv[0]), " --rel <release> --cand <rc> --day <day> "
    print """
    Where:
    <release>   is the release (e.g. CMSSW_1_7_X_2007-07-24-1600)
    <rc>        is the candidate-build (e.g. 1.7-tue-15)
    <day>       is the day of week (e.g. tue)
    """
    return

# ================================================================================

def main():

    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'h', 
                                   ['help','release=', 'cand=', 'day=', 'dryRun'])
    except getopt.GetoptError:
        usage()
        sys.exit(-2)

    slot = None
    rel  = None
    cand = None
    day  = None
    dryRun = False
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()

        if o in ('--release',):
            rel = a

        if o in ('--cand',):
            cand = a

        if o in ('--day',):
            day = a

        if o in ('--dryRun',):
            dryRun = True

    if not cand or not rel or not day:
        usage()
        sys.exit()

    pi = ProjectInstaller()
    if dryRun: pi.setDryRun()

    try:
        pi.setupCand(cand, rel, day)
    except Exception, e:
        print "ERROR: Caught exception during setup : " + str(e)
        sys.exit(-1)
        
    try:
        pi.install()
    except Exception, e:
        print "ERROR: Caught exception during install : " + str(e)

    return

# ================================================================================

if __name__ == "__main__":

    main()
