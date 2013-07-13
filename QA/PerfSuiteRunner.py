#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Andreas Pfeiffer on 2010-01-17.
Copyright (c) 2010 CERN. All rights reserved.
"""

import os, sys, time, re
import getopt
import PerfSuiteRawRef

# ================================================================================

from threading import Thread

class PerfRunner(Thread):
    def __init__(self, stepsIn, cpuIn, cmdIn, harvestPreIn, dryRunIn):
        Thread.__init__(self)
        self.steps = stepsIn
        self.cpu   = cpuIn
        self.cmd   = cmdIn
        self.harvestPre = harvestPreIn
        self.dryRun = dryRunIn

        self.id = self.steps+'_'+self.cpu
        self.startTime = -1
        self.stopTime  = -1
        self.status = None
        return
    
    def run(self):
        
        self.startTime = time.time()
        
        import socket
        try:
            cmd = '#!/usr/bin/env bash;\n'
            cmd += 'cd '+os.path.join(self.steps, self.cpu)+';'
            cmd += 'pwd;'
            cmd += 'export HOST='+socket.gethostname()+';'
            if not os.environ.has_key('STAGE_HOST'):
                stageHost = 'castorcms'
                cmd += 'echo "STAGE_HOST not set, setting it to '+stageHost+'";'
                cmd += 'export STAGE_HOST='+stageHost+';'
            cmd += 'eval `scramv1 run -sh` ;unset DISPLAY;'
            cmd += 'export LOCALRT=$LOCALRT_SCRAMRT;' # temporary hack for scram 2.0.1
            cmd += 'export QUIET_ASSERT="sa";'      # Abort on stack trace in SEAL PluginManager:
            # cmd += 'export CMS_PATH='+self.cmsPath+';'
            cmd += 'ulimit -v 40960000;' # set memory limit for processes. should this be lower ???
            cmd += self.cmd+';'
            cmd += 'RET=$?;'
            cmd += 'mkdir results;'
            cmd += 'cmsPerfPublish.py results;'
            if self.cpu in ['cpu0', 'cpu1', 'cpu2', 'cpu3', 'cpu4']:
                cmd += self.harvestPre+';cmsPerfSuiteHarvest.py;'
            cmd += 'if [ -e PerfSuiteDBData -a -d PerfSuiteDBData ]; then ;'
            cmd += '   scp PerfSuiteDBData/*.xml  cmsperfvmdev.cern.ch://data/projects/conf/PerfSuiteDB/xml_dropbox/.;'
            cmd += '   scp PerfSuiteDBData/*.xml  cmsperfvm5.cern.ch://data/projects/conf/PerfSuiteDB/xml_dropbox/.;'
            cmd += 'fi;'
            cmd += 'exit $RET   # return the exitcode from the actual perfsuite ... ;' 
            
            cmdFileName = 'cmd-'+self.steps+'-'+self.cpu+'.sh'
            cmdFile = open(cmdFileName,'w')
            cmdFile.write( cmd.replace(';','\n') )
            cmdFile.close()

            cmd = 'chmod +x '+cmdFileName+';'
            cmd += './'+cmdFileName+' > '+cmdFileName.replace('.sh','.log')+' 2>&1 '
            print time.asctime()+'==++> '+self.id+' in '+os.getcwd()+', going to run: "'+cmd+'"'

            if self.dryRun:
                print "dryRun for "+self.id+": "+cmd.replace(';','\n')
                time.sleep(2) # fake some work ...
                ret = 0
            else:
                ret = os.system(cmd)

            print time.asctime()+'==++> '+self.id+' in '+os.getcwd()+', done running: "'+cmd+'"'
            
            self.status = ret
            if ret != 0:
                print "ERROR when running perfsuite cmd: cmd returned " + str(ret)
        except Exception, e :
            print "ERROR in PerfRunner "+self.steps+"/"+self.cpu+" : caught exception: " + str(e)
            pass
        
        self.stopTime = time.time()

        cmdDir = os.path.join(self.steps, self.cpu)
        cmdFileName = 'cmd-'+self.steps+'-'+self.cpu+'.sh'
        cmd = 'cp '+cmdFileName+ '  ' +cmdDir+';'
        if self.dryRun:
            ret = 0
            print 'dryRun for '+cmd
        else:
            ret = os.system(cmd)
        if ret != 0:
            print "ERROR copying cmd file to "+cmdDir
            print "      using  ",cmd
        
        return

# ================================================================================

class PerfSuiteRunner(object):
    """docstring for PerfSuiteRunner"""
    def __init__(self, crossCheck=False, maxThreadsIn=4, show=False, part='all'):
        super(PerfSuiteRunner, self).__init__()
        self.cmdMap = {}
        import socket
        self.host = socket.gethostname()

        self.part = part

        # enable the following to cross-check the "manual" entries in the files.
        # to check, go to the dir where the action is ( ~/public/IBTests/ ), then do:
        # grep cmsPerfSuite newPerfMatrix-part*.sh | grep -v Harvest | cut -d':' -f2-  | sort >foo
        # python PerfSuiteRunner.py | cut -d':' -f 2- | sort >foo1
        # then tkdiff the two files. At present only the cpu X numbers change for some runs and there
        # are two who have duplicate step options
        self.crossCheck = crossCheck
        
        self.harvestPreamble  = 'export PERF_CASTOR_URL=/castor/cern.ch/cms/store/relval/performance/;'
        self.harvestPreamble += 'export PERFDB_cmssw_version=$CMSSW_VERSION;'
        self.harvestPreamble += 'export PERFDB_TARFILE=UNAVAILABLE_IBTEST;'
        self.harvestPreamble += 'export PERFDB_CASTOR_FILE_URL=${PERF_CASTOR_URL}${PERFDB_TARFILE};'

        self.rawRefDir = PerfSuiteRawRef.rawRefDir
        self.referenceFiles = PerfSuiteRawRef.referenceFiles

        self.setupCmdMap()

        self.threadList = []
        self.maxThreads = int(maxThreadsIn)
        self.threadStatus = {}
        self.threadTiming = {}
        
    def __delete__(self):
        
        # wait for threads to finish ...
        for task in self.threadList:
            task.join()
    
    def dumpInfo(self):

        from pickle import Pickler
        psrPklFileName = 'PerfSuiteRunner-'+self.part+'.pkl'
        summFile = open(psrPklFileName,'w')
        pklr = Pickler(summFile)
        pklr.dump(self.host)
        pklr.dump(self.part)
        pklr.dump(self.referenceFiles)
        pklr.dump(self.cmdMap)
        summFile.close()

    
    def activeThreads(self):
    
        nActive = 0
        for t in self.threadList:
            if t.isAlive() : 
                nActive += 1
            else:
                if t.id not in self.threadStatus.keys(): 
                    self.threadStatus[t.id] = t.status
                    self.threadTiming[t.id] = [t.startTime, t.stopTime]
    
        return nActive
            
    # --------------------------------------------------------------------------------

    def prepareRawRefs(self, dryRun):
        """docstring for prepareRawRefs"""
        
        for castorDir, refList in self.referenceFiles.items():
            for rem, ref in refList.items():
                if os.path.exists(self.rawRefDir+'/'+ref) :
                    print "Ignoring existing rawRefFile ", ref
                    continue
                if dryRun:
                    ret = 0
                    print 'dryRun for: rfcp '+castorDir+rem+' '+self.rawRefDir+ref
                else:
                    ret = os.system('mkdir -p '+self.rawRefDir+'; rfcp '+castorDir+rem+' '+self.rawRefDir+ref)
                if ret != 0:
                    print "ERROR copying rawRefFile ", castorDir+rem, ' to ', self.rawRefDir+ref
                    print "      rfcp returned: ", ret

    # --------------------------------------------------------------------------------

    def setupCmdMap(self):
        """docstring for setupCmdMap"""
        
        if self.crossCheck:
            perfSuiteOptions = '$PERFSUITE_OPTIONS ' # ' --mail gbenelli '
            condMC = 'FrontierConditions_GlobalTag,${COND_MC}::All'
            condSU = 'FrontierConditions_GlobalTag,${COND_SU}::All'
        else:
            perfSuiteOptions = ' --cmsScimark 0 --cmsScimarkLarge 0 '
            condMC = 'auto:mc'
            condSU = 'auto:startup'
        
        pileupInputFile = '/store/relval/CMSSW_3_5_1/RelValMinBias/GEN-SIM-DIGI-RAW-HLTDEBUG/MC_3XY_V21-v1/0000/9CF547DC-AB1C-DF11-8B8C-0030487C90C2.root'
        #pileupInputFile = '/store/relval/CMSSW_3_3_0_pre3/RelValMinBias/GEN-SIM-DIGI-RAW-HLTDEBUG/MC_31X_V8-v1/0015/EC95D731-779F-DE11-A1BA-000423D9939C.root'
        # pileupInputFile = '${PILEUP_INPUT_FILE} '
        
        #          cpuNr:   dir  ,        what , sample
        suiteMap = {  0 : ['cpu0', 'RunTimeSize'  , 'TTbar'],
                      1 : ['cpu1', 'RunTimeSizePU', 'TTbar'],
                      2 : ['cpu2', 'RunTimeSize'  , 'MinBias'],
                      3 : ['cpu3', 'RunIgProf'    , 'TTbar'],
                      4 : ['cpu4', 'RunIgProfPU'  , 'TTbar'],
                      5 : ['cpu5', 'RunMemcheck'  , 'TTbar'],
                      6 : ['cpu6', 'RunMemcheckPU', 'TTbar'],
                      7 : ['cpu7', 'RunMemcheck'  , 'Run2010A'],
                    }
        
        steps = ['GEN-DIGI2RAW', 'GEN-FASTSIM', 'RAW2DIGI-RECO', 'HLT']
        
        nevtsMB = { 'GEN-DIGI2RAW_RunTimeSize'   : ' -t 600 ',
                    'GEN-FASTSIM_RunTimeSize'    : ' -t 6000 ',
                    'RAW2DIGI-RECO_RunTimeSize'  : ' -t 6000 ',
                    'HLT_RunTimeSize'            : ' -t 6000 ',
                    }
        
        nevts = { 'GEN-DIGI2RAW_RunIgProf'     : ' -i 101 ',
                  'GEN-DIGI2RAW_RunIgProfPU'   : ' -i 101 ',
                  'GEN-DIGI2RAW_RunMemcheck'   : ' -m 2 ',
                  'GEN-DIGI2RAW_RunMemcheckPU' : ' -m 2 ',
                  'GEN-DIGI2RAW_RunTimeSize'   : ' -t 100 ',
                  'GEN-DIGI2RAW_RunTimeSizePU' : ' -t 100 ',
                  
                  'GEN-FASTSIM_RunIgProf'      : ' -i 1001 ',
                  'GEN-FASTSIM_RunIgProfPU'    : ' -i 1001 ',
                  'GEN-FASTSIM_RunMemcheck'    : ' -m 20 ',
                  'GEN-FASTSIM_RunMemcheckPU'  : ' -m 20 ',
                  'GEN-FASTSIM_RunTimeSize'    : ' -t 1000 ',
                  'GEN-FASTSIM_RunTimeSizePU'  : ' -t 1000 ',
                  
                  'RAW2DIGI-RECO_RunIgProf'    : ' -i 1001 ',
                  'RAW2DIGI-RECO_RunIgProfPU'  : ' -i 501 ',
                  'RAW2DIGI-RECO_RunMemcheck'  : ' -m 15 ',
                  'RAW2DIGI-RECO_RunMemcheckPU': ' -m 10 ',
                  'RAW2DIGI-RECO_RunTimeSize'  : ' -t 1000 ',
                  'RAW2DIGI-RECO_RunTimeSizePU': ' -t 500 ',
                  
                  'HLT_RunIgProf'              : ' -i 1001 ',
                  'HLT_RunIgProfPU'            : ' -i 1001 ',
                  'HLT_RunMemcheck'            : ' -m 40 ',
                  'HLT_RunMemcheckPU'          : ' -m 20 ',
                  'HLT_RunTimeSize'            : ' -t 1000 ',
                  'HLT_RunTimeSizePU'          : ' -t 1000 ',
                }
        
        inFile = { 'MinBias_mc'  : 'MinBias_RAW_320_IDEAL.root',
                   'MinBias_su'  : 'MinBias_RAW_320_STARTUP.root',
                   'TTbar_mc'    : 'TTbar_RAW_320_IDEAL.root',
                   'TTbar_su'    : 'TTbar_RAW_320_STARTUP.root',
                   'PU_su'       : 'TTbar_Tauola_PileUp_RAW_320_STARTUP.root',
                   'Run2010A_mc' : 'run2010A-minBias.root',
                   }
        
        for step in steps:
            for cpu in range(0,7):
                if cpu == 7 and step != 'RAW2DIGI-RECO' : continue
                dirCpu, what, sample = suiteMap[cpu]
                
                cond = condMC
                
                if cpu in [1, 4, 6]: # PileUp
                    puCmd = ' --PUInputFile='+pileupInputFile
                    puDriver = ' --pileup=LowLumiPileUp'
                    if step == 'HLT': cond = condSU
                    if step == 'RAW2DIGI-RECO': cond = condSU
                else:  # no PileUp
                    puDriver = ''
                    puCmd = ''
                    if step == 'HLT': cond = condSU
                
                psCmd  = 'cmsPerfSuite.py  ' + perfSuiteOptions
                if "MinBias" in sample:
                    psCmd += nevtsMB[step+'_'+what]  + '--' + what + ' '
                else:
                    psCmd += nevts[step+'_'+what]  + '--' + what + ' '
                psCmd += sample + ' --step '+ step+ ' '
                
                if step[:4] != 'GEN-' :
                    condition = 'su'
                    if 'MC' in cond.upper(): condition = 'mc'
                    if what[-2:] == 'PU':
                        psCmd += '--PUInputFile=' + self.rawRefDir + '/' + inFile['PU_'+condition] + ' '
                    else:
                        psCmd += '--filein=' + self.rawRefDir + '/' + inFile[sample+'_'+condition] + ' '
                
                cmsDriver = '--eventcontent RAWSIM '
                if 'RECO' in step: cmsDriver = '--eventcontent RECOSIM '
                
                cmsDriver += '--conditions '+cond
                if "FASTSIM" in step:
                    cmsDriver += puDriver
                    psCmd = psCmd.replace('PU ',' ')
                elif 'HLT' in step:
                    cmsDriver += ' --processName HLTFROMRAW'
                elif 'GEN' in step:
                    psCmd += puCmd
                
                psCmd += ' --cmsdriver="'+cmsDriver+'"'
                psCmd += ' --cores 0 --cpu '+str(cpu)+ ' '
                psCmd += '> cmsPerfSuite.log 2>&1 '
                
                self.cmdMap[(step,dirCpu)] = psCmd

        # add realdata
        # psCmd = 'cmsPerfSuite.py --cmsScimark 0 --cmsScimarkLarge 0 --mail gbenelli '
        # psCmd += ' -m 15 --RunMemcheck Run2010A --step RAW2DIGI-RECO '
        # psCmd += ' --filein=/build/RAWReference/run2010A-minBias.root  '
        # psCmd += ' --cmsdriver="--eventcontent RECO --conditions auto:com10 --scenario pp --data" '
        # psCmd += ' --cores 0 --cpu 7 > cmsPerfSuite.log 2>&1 '

        # for now just take the "raw" valgrind command ...
        psCmd = 'cmsDriver.py run2010A_step2 -n %d '
        psCmd += ' --step=RAW2DIGI,L1Reco,RECO,DQM '
        psCmd += ' --filein file:%s/run2010A-minBias.root '
        psCmd += ' --fileout=run2010A__RAW2DIGI,L1Reco,RECO.root '
        psCmd += ' --eventcontent RECO --datatier RECO --data --scenario pp '
        psCmd += ' --magField AutoFromDBCurrent '
        # psCmd += ' --process reRECO --customise Configuration/GlobalRuns/customise_Collision_37X.py '
        psCmd += ' --conditions auto:com10 '
        psCmd += ' --prefix "time valgrind --tool=memcheck `cmsvgsupp` '
        psCmd += ' --num-callers=20 --xml=yes '
        psCmd += ' --xml-file=run2010A__%s_memcheck_valgrind.xml " %s > run2010A__%s_memcheck_valgrind.log 2>&1 '

        nEvts = 100
        step = 'RAW2DIGI-RECO'
        self.cmdMap[(step,'cpu7')] = psCmd % (nEvts,self.rawRefDir,step,'',step.replace('-',','))
	step = 'RAW2DIGI-RECO-DQM'
        if self.isCmsDriverSupport('customise_commands'):
            from random import randrange
            skipEvt = randrange(nEvts, 20300, nEvts)
            step = 'RAW2DIGI-RECO-DQM'
            self.cmdMap[(step,'cpu7')] = psCmd % (nEvts,self.rawRefDir,step,"--customise_commands 'process.source.skipEvents=cms.untracked.uint32("+str(skipEvt)+")'",step.replace('-',','))
        else:
            self.cmdMap[(step,'cpu7')] = 'echo This test is not available for this release' 
    # --------------------------------------------------------------------------------

    def isCmsDriverSupport(self,option): 
        from commands import getstatusoutput
        err,res = getstatusoutput("cmsDriver.py --help | grep '\-\-%s\(=\| \)' | tr '=' ' ' | awk '{print $1}'" % option)
        if err or (not option in res):
            print 'Warning: cmsDriver.py does not support --'+option+' command-line option'
            return False
        return True

    # --------------------------------------------------------------------------------

    def showRaw(self, step=None, format=False):
        print "running on ", self.host
        from pprint import pprint
        pprint( self.cmdMap )

    # --------------------------------------------------------------------------------

    def show(self, step=None, format=False):
        """docstring for show"""
        
        print "running on ", self.host

        print "\nReference files:"
        for castorDir, refList in self.referenceFiles.items():
            for rem, ref in refList.items():
                print 'ref> remote: %s local: %s ' % (castorDir+rem, self.rawRefDir+ref)

        print '\nRunning part:', self.part

        print '\nCommands:'
        
        if self.part.lower() == 'all':
            rem, mod = 1,1
        else:
            rem, mod = [int(x) for x in self.part.split('of')]

        rem -= 1
        keys = self.cmdMap.keys()
	while (rem<len(keys)):
	    k = keys[rem]
	    rem += mod
            v= self.cmdMap[k]
            if step and step not in k[0] : continue
            line = " %20s/%4s : " % k
            for item in v.split(' --'):
                if 'cmsPerfSuite' in item:
                    line += item
                else:
                    if 'cpu7' in k and 'cmsDriver' in item:
                        line += item
                    else:
                        line += ' --'+item
                if format : line += "\n"+' '*30
            line = line.replace('\n'+' '*30+'--conditions', ' --conditions')
            print line

    # --------------------------------------------------------------------------------

    def runPart(self, dryRun):

        self.prepareRawRefs(dryRun)

        print time.asctime()+' PSR> going to run with ',self.maxThreads,'threads.'
        
        if self.part.lower() == 'all':
            rem, mod = 1,1
            print time.asctime()+' PSR> going to run all'
        else:
            rem, mod = [int(x) for x in self.part.split('of')]
            print time.asctime()+' PSR> going to run ', str(self.part), '('+str(rem)+'/'+str(mod)+')'

        rem -= 1
        keys = self.cmdMap.keys()
	while (rem<len(keys)):
	    k = keys[rem]
	    rem += mod
            
    	    # make sure we don't run more than the allowed number of threads:
            while ( self.activeThreads() >= self.maxThreads) :
                time.sleep(5)
                continue
                    
            cmd = self.cmdMap[k]
            step, cpu = k

            print time.asctime()+' PSR> preparing to run step, cpu, cmd',step, cpu, cmd
            
            subDir = os.path.join(step, cpu)
            if os.path.exists( subDir ): os.system('rm -rf '+subDir)
            if dryRun:
                print "DryRun for creating subdir ", subDir
            else:
                os.makedirs(subDir)
            
            runner = PerfRunner(step, cpu, cmd, self.harvestPreamble, dryRun)
            self.threadList.append(runner)
            runner.start()

        print time.asctime()+' PSR> waiting for threads to finish'

        # wait until all threads are finished
        while self.activeThreads() > 0:
    	    time.sleep(5)

        print time.asctime()+' PSR> all threads finished, harvesting next'

        resultInfo = {}
        for t in self.threadList: 
            self.threadStatus[t.id] = t.status
            self.threadTiming[t.id] = [t.startTime, t.stopTime]
            resultInfo[t.id] = [t.status, t.startTime, t.stopTime, t.cpu, t.steps, t.cmd, t.harvestPre]

        for id, status in self.threadStatus.items():
            dTime = time.gmtime(self.threadTiming[id][1]-self.threadTiming[id][0])
            dTimeAsc = time.strftime('%H:%M:%S', dTime)
            print 'PSR: result for %20s : %s, time to process: %s' % (id, str(status), dTimeAsc)


        try:
            from pickle import Pickler
            psrPklFileName = 'PerfSuiteRunner-results-'+self.part+'.pkl'
            summFile = open(psrPklFileName,'w')
            pklr = Pickler(summFile)
            pklr.dump(self.host)
            pklr.dump(self.part)
            pklr.dump(self.referenceFiles)
            pklr.dump(self.cmdMap)
            pklr.dump(resultInfo)
            summFile.close()
            print "Successfully wrote results file"
        except Exception, e:
            print "ERROR when writing results file:", str(e)
            
    # --------------------------------------------------------------------------------

    def showThreadInfo(self):
        total = len(self.cmdMap.keys())
        index  = 0
        for k in self.cmdMap:
            index += 1
            if re.search('\s+(\-\-RunMemcheck(PU|)|valgrind)\s+',self.cmdMap[k]): print "%dof%d:1.3" % (index,total)
            else: print "%dof%d:1" % (index,total)
# ================================================================================

class Usage(Exception):
    def __init__(self, msg):
        self.msg = str(msg)
        self.msg += """ <options>

Where <options> is one of:

 --help --crossCheck --step=<step> --format --run --part=<part> --maxThreads=<n> --show

""" 

# ================================================================================

def main(argv=None):
    if argv is None:
        argv = sys.argv
    
    crossCheck = False
    step       = None
    format     = False
    run        = False
    dryRun     = False
    show       = False
    part       = 'all'
    maxThreads = 8
    dump = False
    testCount = False

    try:
        try:
            opts, args = getopt.getopt(argv[1:], "ho:vj:sp:d", ["help", 'crossCheck', 'step=','format','run','part=','maxThreads=','show','dump','dryRun','testCount'])
        except getopt.error, msg:
            raise Usage(msg)
        
        # option processing
        for option, value in opts:
            if option == "-v":
                verbose = True
            if option in ("-h", "--help"):
                raise Usage('')
                return
            if option in ("--crossCheck",):
                crossCheck = True
            if option in ("--step",):
                step = value
            if option in ("--format",):
                format = True
            if option in ("--dryRun",):
                dryRun = True
            if option in ("--run",):
                run = True
            if option in ("--show",):
                show = True
            if option in ('-p', "--part",):
                part = value
            if option in ('-d', "--dump",):
                dump = True
            if option in ("--testCount",):
               testCount  = True
            if option in ('-j', "--maxThread",):
                maxThreads = value
        
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        return 2
    
    psr = PerfSuiteRunner(crossCheck, maxThreads, show, part)
    if testCount: psr.showThreadInfo()
    if show: psr.show(step, format)
    if run:  psr.runPart(dryRun)
    if dump: psr.dumpInfo()

# ================================================================================

if __name__ == "__main__":
    sys.exit(main())
