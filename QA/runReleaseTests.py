#!/usr/bin/env python
 
import os, sys, time, threading, re
import glob

scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

parentPath = os.path.join(scriptPath,'../IB')
if parentPath not in sys.path:
    sys.path.append( parentPath )

from BuilderBase import BuilderBase, ActionError
import helpers
# ================================================================================

class ReleaseTestRunner(BuilderBase):

    def __init__(self, dirIn=None, only=None, afsLogDir=None, rel=None):

        BuilderBase.__init__(self, verbose=1, release=rel)
    
        self.buildDir = dirIn
        self.release = rel
        self.relCycle = rel.split("_X_",1)[0].replace("CMSSW_","").replace("_",".")
        self.only = only
        self.afsLogDir=afsLogDir
        return
    
    # --------------------------------------------------------------------------------
    
    def runAutoBuildFile(self):
        baseDir = os.envirn.get('CMSSW_RELEASE_BASE','')
        if not baseDir: os.envirn['CMSSW_BASE']
        logName = 'auto-build-file.log'
        cmdBld = 'createBuildFile.pl --detail --xml --jobs 4 --dir '+baseDir
        cmdLog = 'tar cf - AutoBuildFile/newBuildFile '+logName+ ' | (cd '+self.afsLogDir+'/../tmp/; tar xf - ) '
        self.runGeneric('autoBF', cmdBld, cmdLog, logName)

        return

    # --------------------------------------------------------------------------------
    
    def runGeneric(self, subDir, cmdBld, cmdLog, logName):

        cmdpre = ''
        if subDir and subDir.strip() != '':
            cmdpre += 'mkdir %s; cd %s;' % (subDir, subDir)
        cmd = cmdpre + cmdBld +' > '+logName+' 2>&1 '
        try:
            self.doCmd( cmd )
        except Exception, e:
            print "ERROR when running command in "+subDir+" cmd:"+cmd
            pass

        cmd = cmdpre + cmdLog
        try:
            self.doCmd( cmd )
        except Exception, e:
            print "ERROR when copying logs in "+subDir+" :"+str(e)
            pass

        return True

    # --------------------------------------------------------------------------------
    
    def runPerfMatrix(self):

        part = self.only
        wf = ''
        m = re.match('^perfMatrix(\d+\.\d+|)$',part)
        if m:  wf = m.group(1)
        if wf: wf = '--list '+wf
        cmd = 'mkdir %s; cd %s;' % (part, part)
        cmd += scriptPath+'/runPerfMatrix.py %s > %s.log 2>&1 ' % (wf, part)
        self.doCmd( cmd )

        from publishQAResults import QAPublisher
        qap = QAPublisher(self.plat, self.release)
        qap.publishPerfMatrixResults(part)

        remDir = self.afsLogDir
        if not os.path.exists(remDir): os.makedirs(remDir)

        cmd = 'cp '+part+'/'+part+'.log '+remDir
        try:
            self.doCmd( cmd )
        except Exception, e:
            print "ERROR when copying perfMatrix logFile to ", remDir
            print "      exception ", str(e)
            print "      cmd = ", cmd

        return True

    # --------------------------------------------------------------------------------
    
    def runNewPerfMatrix(self):

	part = self.only
	cmd = scriptPath+'/prepareRawRefs.py'
        self.doCmd( cmd )

        cmd = 'mkdir newPerf-'+part+'; cd newPerf-'+part+'; '
        cmd += scriptPath+'/PerfSuiteRunner.py --run --part '+part+'  -j 4  > perfNew-'+part+'.log 2>&1 '
        print "==> going to run",cmd
        self.doCmd( cmd )

        # publish the locally produced navigator output 
        print "rrt> publishing to navigator ... "
        afsIgpDir = os.path.join('/afs/cern.ch/cms/sdt/web/qa/igprof/data/',self.plat)
        cmd = 'cd '+afsIgpDir+' ; mkdir -p '+self.relCycle+' ;'
        cmd += 'ln -fs '+self.relCycle+'/'+self.release+' '+self.release
        ret = os.system(cmd)
        print "setting symlink via", cmd
        if ret != 0:
            print "rrt> ERROR when setting symlink via:", cmd

        igpDirs = glob.glob('newPerf-'+part+'/*/cpu*/IgProfData')
        print "rrt> dirs found: ", igpDirs
        for igpdir in igpDirs:
            cmd = 'cd '+igpdir+'/'+self.plat+'; tar -cf - '+self.release+'| (cd '+afsIgpDir+'/'+self.relCycle+'; tar xf - )'
            try:
                self.doCmd( cmd )
            except Exception, e:
                print "rrt> ERROR when copying over the IgProfData from ", os.getcwd()
                print "     exception ", str(e)
                print "     cmd = ", cmd
        
        print "rrt> publish valgrind xml files and command list to AFS install area ... "
        remDir = self.afsLogDir
        if not os.path.exists(remDir): os.makedirs(remDir)
            
        cmd = 'cd newPerf-'+part+'; tar cf - `find . -name \*vlgd.xml` | (cd '+remDir+' ; tar xf - ) '
        try:
            self.doCmd( cmd )
        except Exception, e:
	    pass

        print "rrt> going to publish QA results "
        from publishQAResults import QAPublisher
        qap = QAPublisher(self.plat, self.release)
        qap.publishPerfSuiteResults(part)
        qap.publishValgrindXML(part)
        qap.publishVGResults(remDir)

        print 'rrt> publishing perfNew log file to ', remDir
        cmd = 'cp newPerf-'+part+'/perfNew-'+part+'.log '+remDir
        try:
            self.doCmd( cmd )
        except Exception, e:
            print "rrt> ERROR when copying perfNew logFile to ", remDir
            print "     exception ", str(e)
            print "     cmd = ", cmd
        
        print "rrt> check for valgrind errors, rebuild and re-run if needed ..."
        stepRevg = 'none'
        try:
            from redoValgrind import ValgrindAnalyzer
            a = ValgrindAnalyzer(part)
            errors = a.analyzeAll()
	    #FIXME: avoid re-running valgrid for now.
	    errors = 0
            if errors > 0:
                stepRevg = 'showErrLibs'
                a.showErrLibs()
                stepRevg = 'rebuildPkgs'
                a.rebuildPackages()
                stepRevg = 'rerunValgrind'
                a.rerunValgrind()
                stepRevg = 'updateResults'
                a.updateResults()
                stepRevg = 'allDone'
            else:
                print "rrt> No errors found in ", inFile
        except Exception, e:
            print "rrt> ERROR when re-running valgrind ("+part+") :"+str(e)
            print "     during step ", stepRevg
            pass
        cmd = 'cd newPerf-'+part+'; find . -mindepth 3 -name "*" -type f | egrep "*.gz|*.sql3|*.tgz|*.root|*.log" | xargs rm -f '
        try: self.doCmd( cmd )
        except: pass
        return True

    # --------------------------------------------------------------------------------
    
    def runTests(self):
        print '\n'+80*'='+' tests start '+self.only+'\n'

        cmd = 'mkdir -p '+self.buildDir+'/qaTests'
        self.doCmd( cmd )
        os.chdir(os.path.join(self.buildDir, 'qaTests'))

        if re.match("^\d+of\d+$", self.only):
            try:
                self.runNewPerfMatrix()
            except Exception, e:
                print "ERROR when running NewPerfMatrix:"+str(e)
        elif re.match("^perfMatrix(\d+\.\d+|)$", self.only):
            try:
                self.runPerfMatrix()
            except Exception, e:
                print "ERROR when running PerfMatrix:"+str(e)
        elif 'autoBuild' == self.only:
            try:
                self.runAutoBuildFile()
            except Exception, e:
                print "ERROR when running autoBuild:"+str(e)

        print '\n'+80*'='+' tests end '+self.only+'\n'

        return 0

# ================================================================================

def usage():
    print "usage:", os.path.basename(sys.argv[0]), " --afsLogDir <afsLogDir> [--only <selection>] [--help]"
    return

# ================================================================================

def main():

    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'h', 
                                   ['help', 'only=', 'afsLogDir='])
    except getopt.GetoptError, msg:
        print msg
        usage()
        sys.exit(-2)

    only = None
    afsLogDir = None
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
        elif o in ('--only',):
            only = a
        elif o in ('--afsLogDir',):
            afsLogDir = a

    if not afsLogDir:
        print "ERROR: Please pass afsLogDir."
        sys.exit(-1)

    rb = ReleaseTestRunner(os.environ['CMSSW_BASE'], only, afsLogDir, os.environ['CMSSW_VERSION'])
    try:
        rb.runTests()
    except Exception, e:
        print "ERROR: Caught exception during runTest : " + str(e)
    return

# ================================================================================

if __name__ == "__main__":

    main()
