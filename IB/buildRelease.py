#!/usr/bin/env python
 
import os, sys, time
from sys import platform
from os.path import join

scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

from BuilderBase import BuilderBase, ActionError
from commands import getstatusoutput
import config

# ================================================================================

class ReleaseBuilder(BuilderBase):

    def __init__(self, dirIn=None, cfg=None):

        BuilderBase.__init__(self)
	self.buildDir = dirIn
	self.updateTimeStamp(dirIn)
	self.configuration = cfg
        
        return
    # --------------------------------------------------------------------------------

    def doBuild(self, relIn, tcTagIn):

        self.release = relIn
        self.tcTag = tcTagIn
        if not self.tcTag:  # do this _after_ self.release has been checked and validated
            self.tcTag = relIn
        
        print '\n'+80*'-'+'\n'
        config.updateReleaseInfoFromTc(self.configuration,self.release)
        self.cmsswBuildDir += "/"+self.release
        self.checkout()
        print '\n'+80*'-'+'\n'
        print 'ReleaseBuilder: going to build ... '
        try:
            self.build()
        except:
            pass

        try:
            self.getBuildLogs()
	    pass
        except Exception, e:
            print "ERROR: Caught exception during generating log files : " + str(e)	    
	
        return

    # --------------------------------------------------------------------------------
    def getBuildLogs(self):
        buildLogFile = os.path.join(self.cmsswBuildLogDir,self.release,'log')
	if os.path.exists(buildLogFile):
	    preLog   = open ( os.path.join(self.buildDir,'prebuild.log'), 'w')
	    buildLog = open ( os.path.join(self.cmsswBuildDir,'logs', self.plat, 'release-build.log'), 'w')
	    inLog    = open ( os.path.join(buildLogFile), 'r')
	    preFlag = True
	    for line in inLog.readlines():
	        if preFlag:
		    preLog.write(line)
		    if line.startswith("Resetting caches"): preFlag = False
		else:
		    buildLog.write(line)
	    preLog.close()
	    buildLog.close()
	    inLog.close()
	else:
	    self.doCmd("touch prebuild.log",self.dryRun,self.buildDir)
	    self.doCmd("touch release-build.log",self.dryRun,os.path.join(self.cmsswBuildDir,'logs', self.plat))
	    
	if os.path.exists(self.cmsswBuildLogDir):
            if os.path.exists(self.cmsswBuildLogDir+"/"+self.release+"/logs"):
                self.doCmd("mkdir -p "+self.cmsswBuildDir+"/tmp/"+self.plat+"/cache")
                self.doCmd("mv "+self.cmsswBuildLogDir+"/"+self.release+"/logs "+self.cmsswBuildDir+"/tmp/"+self.plat+"/cache/log")
	    self.doCmd("rm -rf "+self.cmsswBuildLogDir,self.dryRun,self.buildDir)
        return

    # --------------------------------------------------------------------------------

    def checkout(self):
        cmd  = "cvs -Q co -r "+self.configuration['CMSDIST']+" CMSDIST; "
        cmd += "cvs -Q co -r "+self.configuration['PKGTOOLS']+" PKGTOOLS;"

        self.doCmd(cmd,True,self.buildDir)
        self.doCmd("cp CMSDIST/cmssw.spec CMSDIST/cmssw.spec.orig",True,self.buildDir)
	
        input = open(self.buildDir+"/CMSDIST/cmssw.spec","r")
        lines = input.readlines()
        input.close()

        import re
        output = open(self.buildDir+"/CMSDIST/cmssw.spec","w")
        output.write("### RPM cms cmssw "+self.release+"\n")
        for line in lines[1:]:
          line=re.sub("scram-project-build","scram-project-build-forIB",line)
          output.write(line)
        output.close()

        #We only want to build cmssw and exit after the build
        #FIXME: For new RPM 4.8 this should be removed
        self.doCmd("cp CMSDIST/scram-project-build.file CMSDIST/scram-project-build-forIB.file",True,self.buildDir)
        input = open(self.buildDir+"/CMSDIST/scram-project-build.file","r")
        lines = input.readlines()
        input.close()

        output = open(self.buildDir+"/CMSDIST/scram-project-build-forIB.file","w")
        for line in lines:
          if line.startswith("%install"):
            output.write("echo Force exit to avoid RPM dependency checking for now.\n")
            output.write("exit 1\n\n")
          output.write(line)
        output.close()

        if platform == "darwin":
          self.doCmd("sed -i -e 's|-o src/PackageList.cmssw|-j 2 -o src/PackageList.cmssw|' PKGTOOLS/cmsBuild",True,self.buildDir)
        return

    # --------------------------------------------------------------------------------

    def build(self):
        if "osx10" in self.plat and "6_1_X" in self.release:
            os.environ["COMPILER"] = "ccache"
            os.environ["CCACHE_NODIRECT"] = "1"
            os.environ["CCACHE_DIR"] = join(self.topBuildDir,"ccache-cache")

        cmsBuild = self.buildDir+"/PKGTOOLS/cmsBuild --debug --ignore-compile-errors --architecture="+self.plat+" --cmsdist="+self.buildDir+"/CMSDIST "
        opts = ""
	
        if "V00-16" in self.configuration['PKGTOOLS']:
            opts += " --compiling-processes "+str(self.configuration['compilingProcesses'])+" --cfg="+scriptPath+"/build.cfg "
        else:
            opts += " -j "+str(self.configuration['compilingProcesses'])+" build cmssw"
        print "Strating release build ..."
        try:
            try:
	       self.aptUpdate(cmsBuild)
	    except:
	        pass
            print "Initialized build area ...."
            self.doCmd(cmsBuild+opts,self.dryRun,self.cmsBuildDir)
        except:
            pass
        print "Release build done ..."
        if os.path.exists(os.path.join(self.cmsBuildDir,"tmp/BUILDROOT")):
            copyCmd  = "mkdir -p " + self.cmsswBuildDir + " ; rm -rf " + self.cmsswBuildDir
            copyCmd += " ; find tmp/BUILDROOT -name "+self.release+" -type d "
            copyCmd += " | xargs -I '{}' mv '{}' " + self.cmsswBuildDir
            copyCmd += " ; cd " + self.cmsswBuildDir + " ; scram build -f projectrename "
            copyCmd += " ; rm -rf " + os.path.join(self.cmsBuildDir,"tmp/BUILDROOT")
            self.doCmd(copyCmd,self.dryRun,self.cmsBuildDir)
 
        return

    # --------------------------------------------------------------------------------

    def aptUpdate(self, cmsBuild):
        cmd = ""
        aptDir = self.cmsBuildDir+"/"+self.plat+"/external/apt"
        if not os.path.exists(aptDir): self.packageBuild(cmsBuild,['SCRAMV1'])
        error, aptver = getstatusoutput ("ls "+aptDir+" | sort | tail -1")
        aptver.strip("\n")
        if aptver:
            cmd = "source " + os.path.join(aptDir,aptver,"etc/profile.d/init.sh") + " ; apt-get update; apt-get -y reinstall cms+cms-common+1.0 || true "
            for pk in self.configuration['defaultAptPackages']:
                cmd += "; apt-get -y install " + pk + " || true "
            try: self.doCmd(cmd,self.dryRun,self.cmsBuildDir)
            except: pass
        self.packageBuild(cmsBuild,self.configuration['defaultIBPackages'])

    # --------------------------------------------------------------------------------
                
    def packageBuild(self, cmsBuild, packs):
        pkgs = ""
        for pk in packs:
            if os.path.exists(self.buildDir+"/CMSDIST/"+pk+".spec"): pkgs += pk+" "
        if pkgs:
            cmd = ""
            if "V00-16" in self.configuration['PKGTOOLS']:
                cmd  = "cat "+scriptPath+"/build.cfg | sed -e 's|build  *cmssw|build "+pkgs+"|g' > "+scriptPath+"/packs.cfg ; "
		cmd += cmsBuild+" --cfg="+scriptPath+"/packs.cfg "
            else:
                cmd = cmsBuild+" build "+pkgs
            try: self.doCmd(cmd,self.dryRun,self.cmsBuildDir)
            except: pass
        if ("local-cern-siteconf" in pkgs) and (not os.path.exists(self.cmsBuildDir+"/SITECONF")):
          try:    self.doCmd ("cd %s; ln -sf `ls -d %s/cms/local-cern-siteconf/*/SITECONF | tail -1` ./SITECONF" % (self.cmsBuildDir,self.plat), self.dryRun, self.cmsBuildDir)
          except: pass

# ================================================================================

def usage():
    print "usage:", os.path.basename(sys.argv[0]), " --buildDir <buildDir> --rel <release> [--tag <TCtag>] [--dryRun]"
    return

# ================================================================================

def main():

    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'h', 
                                   ['help','buildDir=', 'release=', 'tag=', 'dryRun', 'cycle='])
    except getopt.GetoptError:
        usage()
        sys.exit(-2)

    buildDir = None
    rel = None
    tag = None
    dryRun = False
    cycle  = None
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()

        if o in ('--buildDir',):
            buildDir = a

        if o in ('--release',):
            rel = a

        if o in ('--tag',):
            tag = a

        if o in ('--dryRun',):
            dryRun = True

        if o in ('--cycle',):
            cycle = a

    config.setDefaults(cycle)
    cfg = config.Configuration[cycle]
    rb = ReleaseBuilder(buildDir, cfg)
    if dryRun: rb.setDryRun()

    try: rb.doBuild(rel, tag)
    except Exception, e: print "ERROR: Caught exception during doBuild : " + str(e)
    return

# ================================================================================

if __name__ == "__main__":

    main()
