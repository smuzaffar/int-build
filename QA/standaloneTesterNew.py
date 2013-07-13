#!/usr/bin/env python

import os, sys, time, re, threading, random

scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

ibPath = scriptPath+'/../IB'
if ibPath not in sys.path:
    sys.path.append(ibPath)

from BuilderBase import BuilderBase
import helpers

# ================================================================================

from threading import Thread
        
class Tester(Thread):
    def __init__(self, startDirIn, cmdIn, thrWeight, rel, logDir, testType=None):
        Thread.__init__(self)
        self.startDir = startDirIn
        self.cmd = cmdIn
        self.threadWeight = thrWeight
        self.release = rel
        self.logDir = logDir
        self.testType = testType
        if not self.testType :
            self.testType = os.path.basename(startDirIn)
        
        return
    
    def doCmd(self, cmd):

        try:
            ret = os.system(cmd)            
            if ret != 0:
                print "ERROR when executing :", cmd
                print "      cmd returned   :", ret
        except Exception, e :
            print "ERROR during runtests : caught exception: " + str(e)
            pass

        return ret
    
    def run(self):

        qaDir = self.startDir+'/qaTests'
        self.doCmd("mkdir -p "+qaDir)
        logFileName = qaDir+'/'+self.testType+'-'+self.release+'.log'
        tmpFileName = qaDir+'/cmdFile.'+self.testType
        tmpFile = open(tmpFileName, 'w')
        tmpFile.write("\n")
        tmpFile.write("/usr/sue/bin/kinit -R;\n")
        tmpFile.write('cd '+qaDir+';\n')
        tmpFile.write('ulimit -v 40960000;\n')   # set memory limit for processes. should this be lower ???
        tmpFile.write(self.cmd.replace(';','\n') + ' > '+logFileName+' 2>&1 \n')
        tmpFile.write("/usr/sue/bin/kinit -R;\n")
        tmpFile.write("\n")
        tmpFile.close()
        cmd = 'chmod +x '+tmpFileName+'; mkdir -p '+self.logDir+'; '+tmpFileName
        self.doCmd(cmd)

        cmd = 'cp ' + logFileName +' '+self.logDir+'/'+self.testType+'.log'
        self.doCmd(cmd)

        tmpFile = open(tmpFileName+".done", 'w')
        tmpFile.close()

        return

# ================================================================================

class StandaloneTester(BuilderBase):

    # --------------------------------------------------------------------------------

    def __init__(self, cyc, release, buildDir=None, only=None, dryRun=False):

        BuilderBase.__init__(self, verbose=0, release=release)

        self.release = release
        self.buildDir = buildDir
        self.cycle = cyc
        self.only  = only
        self.cpu = 0
        self.cmsenv = ''
        self.dryRun = dryRun
        self.threadList = []
        if not self.only: self.only = [ '1of1', 'perfMatrix']
        self.orderedJobs = [ '28of','5of','15of','12of','21of','perfMatrix3.0','10of','7of',
                             '26of','19of','17of','23of','16of','3of','8of','1of','9of',
                             '18of','perfMatrix2.0','22of','24of','13of','20of','2of',
                             '25of','27of','30of','4of','6of','14of','11of','29of','perfMatrix1.0']
        return

    # --------------------------------------------------------------------------------
    
    def prepare(self):
        global scriptPath
        cmd = 'cat /proc/cpuinfo'
        pipe = os.popen(cmd)
        res = pipe.readlines()
        pipe.close()
        for line in res:
            if re.match('^processor\s*:\s*\d+\s*$',line): self.cpu += 1
        if not self.cpu: self.cpu = 8
        self.doCmd("%s/stdKill.py --kill --cycle %s" % (scriptPath,self.cycle))        
        if os.environ.get('CMSSW_BASE',None): return
        cmd  = 'mkdir -p '+self.buildDir+'; cd '+self.buildDir+';scram project '+self.release+';'
        self.doCmd(cmd)
        self.buildDir = os.path.join(self.buildDir, self.release)
        self.cmsenv = 'cd '+self.buildDir+'; eval `scram run -sh`;'
        return

    # --------------------------------------------------------------------------------

    def activeThreads(self):

        nActive = 0
        for t in self.threadList:
            if t.isAlive() : nActive += 1

        return nActive

    # --------------------------------------------------------------------------------

    def continueIfHasEnoughPower(self, actWeight):
        currentLoadFactor = self.getCurrentLoadFactor()
        
        while True:
            avail = self.cpu - currentLoadFactor
            if avail >= actWeight: 
                break
            time.sleep(60)
            currentLoadFactor = self.getCurrentLoadFactor()
        return True

    # --------------------------------------------------------------------------------

    def getCurrentLoadFactor(self):
        loadFactor = 0
        for t in self.threadList:
            if t.isAlive() :
                loadFactor += t.threadWeight
        return loadFactor
    
    # --------------------------------------------------------------------------------
    
    def fixJobNames(self, jobs):
        cmd = self.cmsenv + scriptPath+"/PerfSuiteRunner.py --testCount | grep '^[0-9]*of[0-9]*:'"
        pipe = os.popen(cmd)
        res = pipe.readlines()
        pipe.close()

        tjobs = []
        mjob = 0
        for job in res:
            j,w = job.split(":",1)
            jobs[j]=float(w)
            if not mjob: mjob = int(j.split("of",1)[1])
        for item in self.only:
            if 'perfMatrix' == item:
                for j in ['3.0', '2.0', '1.0']:
                    jn = 'perfMatrix'+j
                    jobs[jn]=1.0
                    tjobs.append(jn)
            elif 'of' in item:
                s, e = item.split("of",1)
                e = int(e)
                s = int(s)
                if (s < 1) or (s > mjob): continue
                if e < 1: e = 1
                if e > mjob: e = mjob
                jx = int(mjob/e)
                if s == e:
                    e = mjob
                else:
                    e = s*jx
                s = (s-1)*jx
                for j in range (s+1,e+1):
                    jn = str(j)+"of"+str(mjob)
                    if jn in jobs: tjobs.append(jn)
            else:
                tjobs.append(item)
                if item not in jobs: jobs[item]=1.0

        orderJobs = []
        for oj in self.orderedJobs:
            for j in tjobs:
               if j.startswith(oj):
                   orderJobs.append(j)
                   break
        for j in tjobs:
            if not j in orderJobs: orderJobs.append(j)
        self.only = orderJobs
        return
    # --------------------------------------------------------------------------------

    def runTests(self):
        
        self.afsLogDir = os.path.join(self.installDir,self.plat,self.stamp[:3],self.cycle+'-'+self.stamp,self.release,'qaLogs')
        threadWeight = { 'relval+standard' : 8 ,
                         'relval+highstats': 8 ,
                         'autoBuild'       : 4 ,
                         'perfMatrix'      : 3 ,
                         '1of2'            : 8 ,
                         '2of2'            : 8 ,
                         }
        self.prepare()
        self.fixJobNames(threadWeight)
        for item in self.only:
            tWeight = 1
            try:
                tWeight = threadWeight[item]
            except:
                print "\n ==> found process with unknown threadWeight", item, '\n'
            
            print '\nitem=', item, '; tWeight=', tWeight
            
            self.continueIfHasEnoughPower(tWeight)

            cmd = self.cmsenv + scriptPath+'/runReleaseTests.py --afsLogDir '+self.afsLogDir+' --only '+item
            
            print '\nPreparing to run %s "%s"' % (self.buildDir, cmd)
            if self.dryRun: continue

            current = Tester(self.buildDir, cmd, tWeight, self.release, self.afsLogDir, item)
            self.threadList.append(current)
            current.start()
            time.sleep(random.randint(0,5)+5) # try to avoid race cond by sleeping random amount of time [5,10] sec 

    	# wait until all threads are finished
        activeThrd = self.activeThreads()
        while activeThrd > 0:
    	    time.sleep(10)
            aThrd = self.activeThreads()
            if aThrd != activeThrd:
                print "Waiting for "+str(aThrd)+" threads to finish"
                activeThrd = aThrd

    	if self.dryRun: return
        from publishQAResults import QAPublisher
        qap = QAPublisher(self.plat, self.release)
        qap.publishVGResults(self.afsLogDir)
        return
    
# ================================================================================

def usage():
    print "usage:", os.path.basename(sys.argv[0]), " [--release <releaseName>] [--buildDir <buildDir>] [--platform <arch>] [--dryRun] [--only perfMatrix|NofM]"
    return

# ================================================================================

def main():

    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'h', 
                                   ['help','buildDir=', 'dryRun', 'only=', 'platform=', 'release='])
    except getopt.GetoptError, msg:
        print msg
        usage()
        sys.exit(-2)

    buildDir = os.environ.get('CMSSW_BASE', os.getcwd())
    dryRun = False
    only = ['1of1','perfMatrix']
    plat = os.environ.get('SCRAM_ARCH', None)
    release = os.environ.get('CMSSW_VERSION', None)
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()

        if o in ('--buildDir',):
            buildDir = a

        if o in ('--dryRun',):
            dryRun = True

        if o in ('--only',):
            only = a.split(',')

        if o in ('--platform',):
            plat = a
            os.environ["SCRAM_ARCH"] = plat
            
        if o in ('--release',):
            release = a

    if not release:
        print "No release name specified!"
        usage()
        sys.exit(-1)

    cyc = release.split("_X_",1)[0].replace("CMSSW_","").replace("_",".")

    if not plat:
        print "ERROR: SCRAM_ARCH not set and no platform given on command line! Ignoring."
        sys.exit(-1)
    st = StandaloneTester(cyc, release, os.path.join(buildDir,plat), only, dryRun)
    return st.runTests()

# ================================================================================

if __name__ == "__main__":

    sys.exit( main() )

