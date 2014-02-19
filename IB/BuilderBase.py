#!/usr/bin/env python

import os, sys, time, re
from os.path import dirname
from datetime import datetime

try:
  scriptPath = os.path.dirname(os.path.abspath(__file__))
except:
  scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

import doCmd
from doCmd import ActionError

# ================================================================================

class BuilderBase(object):
    def __init__(self, verbose=1, release=None):

        # set up site specific config settings
        import config

        self._readTimeStamp = False
        if os.environ.has_key("CMSSW_VERSION") and os.environ.has_key("VO_CMS_SW_DIR"):
            self.rel2Stamp(os.environ["CMSSW_VERSION"])
            self.topBuildDir = dirname(os.environ["VO_CMS_SW_DIR"])
        elif os.environ.has_key('CMSINTBLD_RCDIR'):
            self.updateTimeStamp (os.environ['CMSINTBLD_RCDIR'], False)
        else:
            self.topBuildDir = os.getcwd()
            if release:
                self.rel2Stamp(release)
            else:
                self.stamp = time.strftime("%a").lower()+'-'+time.strftime("%H")
                self.timeStamp = time.strftime("%Y-%m-%d-%H00")
  
        self.plat  = os.environ["SCRAM_ARCH"]
        self.domain = config.getDomain()
        self.installDir  = config.siteInfo[self.domain]['installDir']
        self.cmsPathMain = config.siteInfo[self.domain]['cmsPath']
	
        if not self.installDir:  self.installDir  = self.topBuildDir+'/Install'
        if not self.cmsPathMain: self.cmsPathMain = self.topBuildDir+'/cms'

        self.cmsBuildDir = os.path.join(self.topBuildDir, "cms")
        self.cmsswBuildDir = os.path.join(self.cmsBuildDir, self.plat, "cms", "cmssw")
        self.cmsswBuildLogDir = os.path.join(self.cmsBuildDir, "BUILD", self.plat, "cms", "cmssw")
        self.cmsinit = "source "+os.path.join(self.cmsBuildDir, "cmsset_default.sh")
        self.cmsenv = self.cmsinit+"; eval `scram run -sh`"

        self.cmsPath = self.cmsBuildDir
        if os.environ.has_key('CMSINTBLD_CMS_PATH') and os.path.exists(os.environ['CMSINTBLD_CMS_PATH']):
            self.cmsPath = os.environ['CMSINTBLD_CMS_PATH']
        os.environ['CMS_PATH'] = self.cmsPath
        os.environ['PATH'] = os.path.join(self.cmsPath,'common') + ':' + os.path.join(self.cmsPath,'bin') + ':' + os.environ['PATH']

        self.release  = None
        self.logFileName = None
        self.errFileName = None
        self.tcTag = None
        self.dryRun = False

        # define the repository for the release code ... 
        self.cvsroot = ':pserver:anonymous@cmscvs.cern.ch:2401/local/reps/CMSSW'
        os.environ['CVSROOT'] = self.cvsroot
        os.environ['CVS_PASSFILE'] = scriptPath + '/cvspass'
        self.svnroot  = 'http://svn.cern.ch/guest/CMSIntBld/'
        return

    def rel2Stamp(self, rel):
        date = rel.split("_X_", 1)[1]
        self.timeStamp = date
	date = re.sub(".*_","",date)
        self.stamp = datetime.fromtimestamp(time.mktime(time.strptime(date, "%Y-%m-%d-%H00"))).strftime("%a-%H").lower()
        return
    # --------------------------------------------------------------------------------

    def doCmd(self,cmd, forceRun=False, inDir=None):
        ret = 0
	if forceRun:
            ret = doCmd.doCmd(cmd, False, inDir)
        else:
            ret = doCmd.doCmd(cmd, self.dryRun, inDir)
            
        return ret

    # --------------------------------------------------------------------------------

    def setDryRun(self, dryRun=True):
        self.dryRun = dryRun
        return

    # --------------------------------------------------------------------------------

    def updateTimeStamp(self, inDir, create=True):        
        if self._readTimeStamp: return
        if os.path.exists(inDir):
            timefile = os.path.join(inDir,"timestamp.txt")
            if os.path.exists(timefile):
                input = open(timefile,"r")
                lines = input.readlines()
                input.close()
                if len(lines) == 3:
                    self.stamp = lines[0].strip()
                    self.timeStamp = lines[1].strip()
                    self.topBuildDir = lines[2].strip()
                    self._readTimeStamp = True
            elif create:
                output = open(timefile,"w")
                output.write(self.stamp+"\n")
                output.write(self.timeStamp+"\n")
                output.write(self.topBuildDir+"\n")
                output.close()
                os.environ['CMSINTBLD_RCDIR'] = inDir
                self._readTimeStamp = True
        return

