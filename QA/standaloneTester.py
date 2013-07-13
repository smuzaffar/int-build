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
    def __init__(self, startDirIn, cmdIn, hostIn, thrWeight, rel, logDir, testType=None):
        Thread.__init__(self)
        self.startDir = startDirIn
        self.cmd = cmdIn
        self.host = hostIn
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

        logFileName = self.startDir+'/'+self.host+'-'+self.testType+'-'+self.release+'.log'
        tmpFileName = self.startDir+'/cmdFile.'+self.testType
        tmpFile = open(tmpFileName, 'w')
        tmpFile.write("\n")
        tmpFile.write('cd '+self.startDir+';\n')
        tmpFile.write('ulimit -v 40960000;\n')   # set memory limit for processes. should this be lower ???
        tmpFile.write(self.cmd.replace(';','\n') + ' > '+logFileName+' 2>&1 \n')
        tmpFile.write("\n")
        tmpFile.close()
        os.system('chmod +x '+tmpFileName)
        os.system('mkdir -p '+self.logDir)

        cmd = 'scp -pq ' + tmpFileName + ' ' + self.host + ':'+tmpFileName+' ' 
        self.doCmd(cmd)

        cmd = 'ssh -qTx ' + self.host + ' " ' + tmpFileName+' " ' 
        self.doCmd(cmd)

        cmd = 'scp -pq ' + self.host + ':' + logFileName +' '+self.logDir+'/'+self.testType+'.log'
        cmd += ' ; echo "HOST NAME: '+self.host+'" >> '+self.logDir+'/'+self.testType+'.log'
        self.doCmd(cmd)

        tmpFile = open(tmpFileName+".done", 'w')
        tmpFile.close()

        return

# ================================================================================

class StandaloneTester(BuilderBase):

    # --------------------------------------------------------------------------------

    def __init__(self, cyc, buildDir=None, only=None):

        BuilderBase.__init__(self, verbose=0)

        self.release = None
        self.releasePath = None
        self.buildDir = buildDir
        self.cycle = cyc
        self.only  = only
        if not self.only: self.only = [ '1of1', 'perfMatrix',]
        
        self.orderedJobs = [ '28of','5of','15of','12of','21of','perfMatrix3.0','10of','7of',
                             '26of','19of','17of','23of','16of','3of','8of','1of','9of',
                             '18of','perfMatrix2.0','22of','24of','13of','20of','2of',
                             '25of','27of','30of','4of','6of','14of','11of','29of','perfMatrix1.0']

        self.dryRun = False

        import configQA
        
        self.threadList = []
        self.boxCpu = []
        self.testBoxes = []
        for box in configQA.siteInfoQA[configQA.getDomain()]['testBoxes'][self.cycle]:
            mach = box ; cpu = 0
            if not isinstance(box, basestring):
                mach = box[0]
                cpu  = box[1]
            self.testBoxes.append(mach)
            self.boxCpu.append(cpu)
        self.actHostIndex = 0
        
        self.afsLogDir = os.path.join(self.installDir,self.plat,self.stamp[:3],self.cycle+'-'+self.stamp)

        return

    # --------------------------------------------------------------------------------
    
    def prepare(self):
        global scriptPath
        if not os.path.exists(self.buildDir): os.makedirs(self.buildDir)
        cmd  = 'cd '+self.buildDir+';'+scriptPath+'/createCMSSWDevArea.py '+os.environ['SCRAM_ARCH']+' '+self.release+';'
        cmd += 'touch '+self.releasePath+'/qaLogs.done'
        self.doCmd(cmd)
        hostIndex = -1
        for host in self.testBoxes:
            cmd  = 'ssh -qTx ' + host + ' rm -rf " ' + self.buildDir +' " ;' 
            cmd += 'ssh -qTx ' + host + ' mkdir -p " ' + self.buildDir +' " ;'
            cmd += 'scp -rq ' + scriptPath + '/../QA ' + host + ':' + self.buildDir + ';'
            cmd += 'scp -rq ' + scriptPath + '/../IB ' + host + ':' + self.buildDir
            self.doCmd(cmd)
            hostIndex += 1
            if self.boxCpu[hostIndex]>0: continue
            cmd = 'ssh -qTx ' + host + ' cat /proc/cpuinfo'
            pipe = os.popen(cmd)
            res = pipe.readlines()
            pipe.close()
            cpu = 0
            for line in res:
                if re.match('^processor\s*:\s*\d+\s*$',line): cpu += 1
            if not cpu: cpu = 8
            self.boxCpu[hostIndex]=cpu
        self.doCmd("%s/stdKill.py --kill --cycle %s" % (scriptPath,self.cycle))
        return

    # --------------------------------------------------------------------------------

    def activeThreads(self):

        nActive = 0
        for t in self.threadList:
            if t.isAlive() : nActive += 1

        return nActive

    # --------------------------------------------------------------------------------

    def getNextHost(self, actWeight):
        host = None
        startIndex = self.actHostIndex
        usedHosts = self.getUsedHosts()
        while True:
            self.actHostIndex += 1
            if self.actHostIndex >= len(self.testBoxes) : self.actHostIndex = 0
            host =self.testBoxes[self.actHostIndex]
            if host in usedHosts.keys():
                avail = self.boxCpu[self.actHostIndex] - usedHosts[ host ]
                if avail >= actWeight: break
            else: break
            if self.actHostIndex == startIndex:
                time.sleep(10)
                usedHosts = self.getUsedHosts()
        return (host, usedHosts)

    # --------------------------------------------------------------------------------

    def getUsedHosts(self):

        activeHosts = {}
        for t in self.threadList:
            if t.isAlive() :
                if t.host in activeHosts.keys():
                    activeHosts[t.host] += t.threadWeight
                else:
                    activeHosts[t.host] = t.threadWeight

        return activeHosts

    # --------------------------------------------------------------------------------
    
    def fixJobNames(self, jobs):
        add = False
        if 'perfMatrix' in self.only:
            self.only.remove('perfMatrix')
            add = True
        for j in [3.0, 2.0, 1.0]:
            j = 'perfMatrix'+str(j)
            jobs[j]=1.0
            if add: self.only.append(j)
        add = False
        if '1of1' in self.only:
            self.only.remove('1of1')
            add =True
        cmd = 'cd '+self.buildDir+'/'+self.release+'; eval `scram run -sh`;'+scriptPath+"/PerfSuiteRunner.py --testCount | grep '^[0-9]*of[0-9]*:'"
        pipe = os.popen(cmd)
        res = pipe.readlines()
        pipe.close()
        for job in res:
            j,w = job.split(":",1)
            jobs[j]=float(w)
            if add: self.only.append(j)
        orderJobs = []
        for oj in self.orderedJobs:
            for j in self.only: 
               if j.startswith(oj):
                   orderJobs.append(j)
                   break
        for j in self.only:
            if not j in orderJobs: orderJobs.append(j)
        self.only = orderJobs
    # --------------------------------------------------------------------------------

    def runTests(self):

        self.release = helpers.getRelease(self.cycle)
        if not self.release:
            print "no release (yet) found for ", self.cycle
            return -2
        
        self.releasePath = helpers.getReleasePath(self.release)

        if not os.path.exists(os.path.join(self.releasePath,'.SCRAM',self.plat)): return
        if not os.path.exists(os.path.join(self.releasePath,'installed.done')): return
        if os.path.exists(os.path.join(self.releasePath,'qaLogs.done')): return

        self.afsLogDir = os.path.join(self.releasePath, 'qaLogs')
        cycx, xday, self.stamp = helpers.getStamp(self.release)

        report=''    	
    	print 'Running on %s machine(s)' % len(self.testBoxes)
        
        cmd0 = 'unset DISPLAY;export CMSINTBLD_CMS_PATH=%s;export SCRAM_ARCH=%s;' % (self.cmsPath,self.plat)
        self.buildDir = os.path.join(self.buildDir, self.release)
        usedHost = {}
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

            tWeight = 1 # default: item has only one process 
            try:
                tWeight = threadWeight[item]
            except:
                print "\n ==> found process with unknown threadWeight", item, '\n'
    	    actHost, usedHosts =  self.getNextHost(tWeight)
            
            print '\nitem', item, 'acthost', actHost, 'used hosts = ', usedHosts, 'tWeight = ', tWeight

            cmd = cmd0 + self.buildDir+'/QA/runReleaseTests.py '
            cmd += '--cycle ' + self.cycle  + ' '
            cmd += '--rel   ' + self.release  + ' '
            cmd += '--build ' + self.buildDir + ' '
            cmd += '--only  ' + item + ' '
            
            print '\nPreparing to run %s "%s" %s' % (self.buildDir, cmd, actHost)

            current = Tester(self.buildDir, cmd, actHost, tWeight, self.release, self.afsLogDir, item)
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
    	    
        from publishQAResults import QAPublisher
        qap = QAPublisher(self.plat, self.release)
        qap.publishVGResults(self.afsLogDir)
        return
    
    # --------------------------------------------------------------------------------

    def setDryRun(self):
        self.dryRun = True
        return

# ================================================================================

def usage():
    print "usage:", os.path.basename(sys.argv[0]), " --cycle <releaseCycle> [--buildDir <buildDir>] [--dryRun] [--only <testsToRun>]"
    return

# ================================================================================

def main():

    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'h', 
                                   ['help','buildDir=', 'cycle=', 'dryRun','only=','platform='])
    except getopt.GetoptError, msg:
        print msg
        usage()
        sys.exit(-2)

    buildDir = None
    cyc = None
    dryRun = False
    only = None
    plat = None
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()

        if o in ('--buildDir',):
            buildDir = a

        if o in ('--cycle',):
            cyc = a

        if o in ('--dryRun',):
            dryRun = True

        if o in ('--only',):
            only = a.split(',')

        if o in ('--platform',):
            plat = a

    if not cyc:
        print "No release cycle specified !"
        usage()
        sys.exit(0)


    if not plat:
        try:
            plat = os.environ["SCRAM_ARCH"]
        except KeyError:
            print "ERROR: SCRAM_ARCH not set and no platform given on command line! Ignoring."
            sys.exit(-1)

    os.environ["SCRAM_ARCH"] = plat # make sure we have it for the others :)
    st = StandaloneTester(cyc, os.path.join(buildDir,plat), only)
    return st.runTests()

# ================================================================================

if __name__ == "__main__":

    sys.exit( main() )

