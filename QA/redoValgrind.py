#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Andreas Pfeiffer on 2010-01-16.
Copyright (c) 2010 CERN. All rights reserved.
"""

import os, sys, time
import getopt, socket

from xml.dom import minidom 
from xml.dom import EMPTY_NAMESPACE

scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

# make sure we find the modules from the IB
parentPath = os.path.join(scriptPath,'../IB')
if parentPath not in sys.path:
    sys.path.append( parentPath )

from doCmd import doCmd, ActionError

from RelProdReader import RelProdReader

# ================================================================================

from threading import Thread

class ValgrindReRunner(Thread):
    def __init__(self, stepsIn, cpuIn, cmdIn, dryRunIn):
        Thread.__init__(self)
        self.steps = stepsIn
        self.cpu   = cpuIn
        self.cmd   = cmdIn
        self.dryRun  = dryRunIn

        self.id = self.steps+'_'+self.cpu+'-1'
        self.startTime = -1
        self.stopTime  = -1
        self.status = None
        return
    
    def run(self):

        dirMap = { 'cpu5' : 'TTbar_Memcheck',
                   'cpu6' : 'TTbar_PU_Memcheck',
                   }
        
        self.startTime = time.time()
        
        import socket
        try:
            cmd = '#!/usr/bin/env bash;\n'
            cmd += 'cd '+os.path.join(self.steps, self.cpu, dirMap[self.cpu])+';'
            cmd += 'pwd;'
            cmd += 'export HOST='+socket.gethostname()+';'
            cmd += 'eval `scramv1 run -sh` ;unset DISPLAY;'
            cmd += 'export LOCALRT=$LOCALRT_SCRAMRT;' # temporary hack for scram 2.0.1
            cmd += 'export QUIET_ASSERT="sa";'      # Abort on stack trace in SEAL PluginManager:
            # cmd += 'export CMS_PATH='+self.cmsPath+';'
            cmd += 'ulimit -v 40960000;' # set memory limit for processes. should this be lower ???
            cmd += self.cmd.replace('.log','-1.log')+';'
            cmd += self.cmd.replace('valgrind.xml','valgrind-1.xml')+';'
            cmd += 'RET=$?;'
            cmd += 'exit $RET   # return the exitcode from the actual command ... ;' 
            
            cmdFileName = 'cmd-'+self.steps+'-'+self.cpu+'-1.sh'
            cmdFile = open(cmdFileName,'w')
            cmdFile.write( cmd.replace(';','\n') )
            cmdFile.close()

            cmd = 'chmod +x '+cmdFileName+';'
            cmd += './'+cmdFileName+' > '+cmdFileName.replace('.sh','.log')+' 2>&1 '

            sys.stdout.flush()
            print time.asctime()+'==++> '+self.id+' in '+os.getcwd()+', going to run: "'+cmd+'"'
            sys.stdout.flush()
            
            if self.dryRun:
                print "dryRun for "+self.id+": "+cmd.replace(';','\n')
                time.sleep(10) # pretend to do some work ...
                ret = 0
            else:
                ret = os.system(cmd)

            sys.stdout.flush()
            print time.asctime()+'==++> '+self.id+' in '+os.getcwd()+', done running: "'+cmd+'"'
            sys.stdout.flush()
            
            self.status = ret
            if ret != 0:
                sys.stdout.flush()
                print "ERROR when running perfsuite cmd: cmd returned " + str(ret)
        except Exception, e :
            sys.stdout.flush()
            print "ERROR in PerfRunner "+self.steps+"/"+self.cpu+" : caught exception: " + str(e)
            pass
        
        self.stopTime = time.time()

        cmdDir = os.path.join(self.steps, self.cpu)
        cmd = 'cp '+cmdFileName+ '  ' +cmdDir+';'
        if self.dryRun:
            ret = 0
            sys.stdout.flush()
            print 'dryRun for '+cmd
            sys.stdout.flush()
        else:
            ret = os.system(cmd)
        if ret != 0:
            sys.stdout.flush()
            print "ERROR cpopying cmd file to "+cmdDir
            print "      using  ",cmd
            sys.stdout.flush()
            
        return

# ================================================================================

class ValgrindAnalyzer(object):
    """docstring for ValgrindAnalyzer"""

    def __init__(self, partIn, maxThreadsIn=8):
        super(ValgrindAnalyzer, self).__init__()
        self.release = None
        self.plat    = None
        self.part    = partIn
        self.ignoreLibs = ['libm-2.5.so','libpthread-2.5.so', 'cmsRun']
        self.libList = []

        prodFileName = os.environ['CMSSW_RELEASE_BASE']+'/src/ReleaseProducts.list'
        self.rpr = RelProdReader()
        self.rpr.readProducts(prodFileName)

        vgCmdFileName = os.environ['CMSSW_RELEASE_BASE']+'/qaLogs/vgCmds.pkl'
        from pickle import Unpickler
        vgCmdFile = open(vgCmdFileName, 'r')
        vgCmdPklr = Unpickler(vgCmdFile)
        self.vgCmds = vgCmdPklr.load()
        vgCmdFile.close()

        self.toDo = []

        self.threadList = []
        self.maxThreads = maxThreadsIn
        self.threadStatus = {}
        self.threadTiming = {}

    def activeThreads(self):
    
        nActive = 0
        for t in self.threadList:
            if t.isAlive() : 
                nActive += 1
    
        return nActive
            
    def findPkg(self, lib):
        """docstring for findPkg"""
        return self.rpr.findProduct(lib)

    def analyzeAll(self):
	import glob
	xmlFiles = glob.glob('*/cpu?/*/*_vlgd.xml')
        if not xmlFiles:
            xmlFiles = glob.glob('*/*/cpu?/*/*_vlgd.xml')
	allErrs = 0
        if not xmlFiles: print 'revg> ALERT: no xml files found !?!?!'
	for item in xmlFiles:
		print 'revg> processing ', item
		err = self.analyze(item)
		if err > 0:
			self.toDo.append(item)
		allErrs += err
	return allErrs

    def analyze(self, inFileName):
        """docstring for analyze"""

	doc = minidom.parse(open(inFileName))

	errorListDoc = doc.getElementsByTagName('error')
	for error in errorListDoc:
		obj = error.getElementsByTagName("obj")[0].childNodes[0].nodeValue
		if '/afs/cern.ch/cms/sw/ReleaseCandidates' in obj:
			self.release = obj.split('/')[9]
			self.plat    = obj.split('/')[6]
		stackFrame = error.getElementsByTagName("stack")[0].getElementsByTagName("frame")
		for frame in stackFrame:
			libName = frame.getElementsByTagName("obj")[0].childNodes[0].nodeValue.split('/')[-1]
			# fncName = frame.getElementsByTagName("fn")[0].childNodes[0].nodeValue
			if libName in self.ignoreLibs: continue
			if libName not in self.libList: self.libList.append(libName)

	return len(self.libList)

    def showErrLibs(self):
	"""docstring for showErrLibs"""
	pass
	print "revg> found ", len(self.libList), 'faulty libs:'
	for lib in self.libList:
		print lib

    def rebuildPackages(self, dryRun=False):
	"""docstring for rebuildPackages"""

	print "revg> rebuilding packages ... "

	self.startDir = os.getcwd()

	cmd = '' # 'cd ..;'
	cmd += 'eval `scram run -sh`;'
        cmd += 'export CVSROOT=:gserver:cmssw.cvs.cern.ch:/cvs/CMSSW;'
	for lib in self.libList:
		package = self.findPkg(lib)
		if not package: continue
		cmd += 'addpkg -z ' + package + ';'
	cmd += 'checkdeps -a ;'
	for lib in self.libList:
		package = self.findPkg(lib)
		if not package: continue
		cmd += '(cd ' + package + '&& scram b -v USER_CXXFLAGS="-g" -j 10 >vg-rebuild.log 2>&1 );'

	print 'revg> in: ', os.getcwd(), "going to execute:", cmd.replace(';','\n')

	ret = doCmd(cmd, dryRun)
	if ret != 0:
            print 'revg> ERROR executing cmd:"'+cmd+'"'
            print '      return code  :', ret
        else:
            print 'revg> Packages successfully rebuilt.'

    def rerunValgrind(self, dryRun=False):

        startDir = os.getcwd()
        os.chdir('newPerf-'+self.part)
        
        print 'revg> in ', os.getcwd(), ' going to re-run valgrind commands :'
        print 'revg> toDo'
        for item in self.toDo:
            print '      ', item
        # print 'revg> cmds'
        # for item in self.vgCmds:
        #     print '      ', item
            
        # print self.vgCmds
        for item in self.toDo:
            baseIn, xmlFile = os.path.split(item)
            base = baseIn.replace('newPerf-1of2/', '').replace('newPerf-2of2/', '')
            cmd = self.vgCmds[base]

            step, cpu, what = base.split('/')
            cmd = cmd.replace('valgrind --tool', 'valgrind --track-origins=yes --tool')

    	    # make sure we don't run more than the allowed number of threads:
            nAct = self.activeThreads()
            # print '\n===========> ', nAct, self.maxThreads
            while ( nAct >= self.maxThreads) :
                # print '\n waiting ... ', nAct, self.maxThreads
                # sys.stdout.flush()
                time.sleep(1)
                nAct = self.activeThreads()
                continue
                    
            runner = ValgrindReRunner(step, cpu, cmd, dryRun)
            self.threadList.append(runner)
            runner.start()

        print time.asctime()+'revg> waiting for threads to finish'

        # wait until all threads are finished
        while self.activeThreads() > 0:
    	    time.sleep(5)

        print time.asctime()+'revg> all threads finished, harvesting next'

        resultInfo = {}
        for t in self.threadList: 
            self.threadStatus[t.id] = t.status
            self.threadTiming[t.id] = [t.startTime, t.stopTime]
            resultInfo[t.id] = [t.status, t.startTime, t.stopTime, t.cpu, t.steps, t.cmd]

        for id, status in self.threadStatus.items():
            dTime = time.gmtime(self.threadTiming[id][1]-self.threadTiming[id][0])
            dTimeAsc = time.strftime('%H:%M:%S', dTime)
            print 'revg: result for %20s : %s, time to process: %s' % (id, str(status), dTimeAsc)


        psrPklFileName = 'ValgrindReRunner-results-'+self.part+'.pkl'
        try:
            from pickle import Pickler
            summFile = open(psrPklFileName,'w')
            pklr = Pickler(summFile)
            pklr.dump(socket.gethostname())
            pklr.dump(self.part)
            pklr.dump(self.toDo)
            pklr.dump(resultInfo)
            summFile.close()
            print "Successfully wrote results file", psrPklFileName
        except Exception, e:
            print "ERROR when writing results file:", psrPklFileName,str(e)

        os.chdir(startDir)
                    
    def updateResults(self, dryRun=False):
            
        startDir = os.getcwd()
        os.chdir('newPerf-'+self.part)
        
        print 'revg> in', os.getcwd(),' going to update results'
            
	for item in self.toDo: 
            baseIn, xmlFileIn = os.path.split(item)
            base = baseIn.replace('newPerf-1of2/', '').replace('newPerf-2of2/', '')
	    xmlFileFull = xmlFileIn.replace('_vlgd.xml', '_valgrind-1.xml')
            xmlFile     = xmlFileIn.replace('_vlgd.xml', '_vlgd-1.xml')

            print xmlFileFull
            if not os.path.exists( os.path.join(base,xmlFileFull) ) : continue # ignore files which did not get redone
            
	    # first convert the files to some manageable size
	    cmd = 'cd '+base+';'
	    cmd += 'xsltproc --output '+xmlFile
	    cmd += ' ' + scriptPath+'/filterOutValgrindLeakErrors.xsl ' + xmlFileFull
            try:
                doCmd(cmd, dryRun)
            except Exception, e:
                print "revg> Error when filtering XML file " + xmlFileFull + ' in ' + base
                print "      got ", str(e)
                
	    # then copy over the files to AFS:
	    from helpers import getStamp
            try:
                cyc, day, stamp = getStamp(self.release)
            except Exception, e:
                print "revg> ERROR when trying to get cyc,day,stamp from release for ", self.release
                print "      got :", str(e)
                cyc, day, stamp = ('none', 'none', 'none')
                
	    topDir = os.path.join('/afs/cern.ch/cms/sw/ReleaseCandidates/',os.environ['SCRAM_ARCH'], day, cyc+'-'+stamp, self.release, 'qaLogs')
	    # GEN-DIGI2RAW/cpu5/TTbar_Memcheck/TTBAR__GEN-SIM-DIGI-L1-DIGI2RAW_memcheck_vlgd.xml '
	    cmd = 'cp ' + os.path.join(base,xmlFile) + ' ' + os.path.join(topDir, base.replace('newPerf-1of2/', '').replace('newPerf-2of2/', ''), xmlFile)
            try:
                doCmd(cmd, dryRun)
            except Exception, e:
                print "revg> Error when copying file to AFS " + os.path.join(base, xmlFile)
                print "      cmd '"+cmd+"'"
                print "      returned ", str(e)

	    # ... and to the web (maybe this can be taken from AFS later):
	    topDir = os.path.join('/data/intBld/incoming/', 'newPerf-'+self.part, os.environ['SCRAM_ARCH'], self.release, 'newPerf-'+self.part)
	    #cmd = 'scp '+os.path.join(base, xmlFile) + ' vocms06:'+os.path.join(topDir, base.replace('newPerf-1of2/', '').replace('newPerf-2of2/', ''), xmlFile)
            #try:
             #   doCmd(cmd, dryRun)
            #except Exception, e:
             #   print "revg> Error when scp-ing file ", os.path.join(base, xmlFile)
              #  print "      cmd '"+cmd+"'"
               # print "      returned ", str(e)
            cmd = 'scp '+os.path.join(base, xmlFile) + ' vocms12:'+os.path.join(topDir, base.replace('newPerf-1of2/', '').replace('newPerf-2of2/', ''), xmlFile)
            try:
                doCmd(cmd, dryRun)
            except Exception, e:
                print "revg> Error when scp-ing file ", os.path.join(base, xmlFile)
                print "      cmd '"+cmd+"'"
                print "      returned ", str(e)

	    # then copy over the log files as well :
            # ... to AFS:
	    from helpers import getStamp
	    cyc, day, stamp = getStamp(self.release)
	    topDir = os.path.join('/afs/cern.ch/cms/sw/ReleaseCandidates/',os.environ['SCRAM_ARCH'], day, cyc+'-'+stamp, self.release, 'qaLogs')
	    # GEN-DIGI2RAW/cpu5/TTbar_Memcheck/TTBAR__GEN-SIM-DIGI-L1-DIGI2RAW_memcheck_vlgd.xml '
            logFileName = xmlFile.replace('_vlgd-1.xml','_valgrind.log').replace('-',',')
	    cmd = 'cp ' + os.path.join(base,logFileName) + ' ' + os.path.join(topDir, base.replace('newPerf-1of2/', '').replace('newPerf-2of2/', ''), logFileName.replace('_valgrind.log','_valgrind-1.log'))
            try:
                doCmd(cmd, dryRun)
            except Exception, e:
                print "revg> Error when copying log file to AFS ", os.path.join(base, logFileName)
                print "      got ", str(e)

	    # ... and to the web (maybe this can be taken from AFS later):
	    topDir = os.path.join('/data/intBld/incoming/', 'newPerf-'+self.part, os.environ['SCRAM_ARCH'], self.release, 'newPerf-'+self.part)
            logFileName = xmlFile.replace('_vlgd-1.xml','_valgrind.log').replace('-',',')
	   # cmd = 'scp '+ os.path.join(base, logFileName) + ' vocms06:'+os.path.join(topDir, base.replace('newPerf-1of2/', '').replace('newPerf-2of2/', ''), logFileName.replace('_valgrind.log','_valgrind-1.log'))
            #try:
             #   doCmd(cmd, dryRun)
            #except Exception, e:
             #   print "revg> Error when scp-ing log file ", os.path.join(base, logFileName)
              #  print "      got ", str(e)
            cmd = 'scp '+ os.path.join(base, logFileName) + ' vocms12:'+os.path.join(topDir, base.replace('newPerf-1of2/', '').replace('newPerf-2of2/', ''), logFileName.replace('_valgrind.log','_valgrind-1.log'))
            try:
                doCmd(cmd, dryRun)
            except Exception, e:
                print "revg> Error when scp-ing log file ", os.path.join(base, logFileName)
                print "      got ", str(e)

        os.chdir(startDir)

        return
    
# =============================================================================

class Usage(Exception):
	def __init__(self, msg):
		self.msg = msg

# =============================================================================

help_message = '''
The help message goes here.
'''

def main(argv=None):
	if argv is None:
		argv = sys.argv

	try:
            try:
                opts, args = getopt.getopt(argv[1:], "hi:v", ["help", "inFile=",'part=','dryRun'])
            except getopt.error, msg:
                raise Usage(msg)

            # option processing
            part = None
            inFile = None
            dryRun = False
            for option, value in opts:
                if option == "-v":
                    verbose = True
                if option in ("-h", "--help"):
                    raise Usage(help_message)
                if option in ("-i", "--inFile"):
                    inFile = value
                if option in ('--part',):
                    part = value
                if option in ('--dryRun',):
                    dryRun = True

            if not part:
                raise Usage("no part specified ...")

            a = ValgrindAnalyzer(part)
            if inFile:
                errors = a.analyze(inFile)
            else:
                errors = a.analyzeAll()

            if dryRun: print "DryRun requested ..."

            if errors > 0:
                a.showErrLibs()
                a.rebuildPackages(dryRun)
                a.rerunValgrind(dryRun)
                a.updateResults(dryRun)
            else:
                if inFile:
                    print "revg> No errors found in ", inFile
                else:
                    print "revg> No errors found."
            
        except Usage, err:
            print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
            print >> sys.stderr, "\t for help use --help"
            return 2


if __name__ == "__main__":
	sys.exit(main())
