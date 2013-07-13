import os,glob,re,sys,time
from Lock import Lock
from stat import *

from threading import Thread
class QAJob(Thread):
    def __init__(self,JobHost,JobType):
        Thread.__init__(self)
        self.JobHost = JobHost
        self.JobType = JobType
        self.ActiveTime = 0
        self.JobDone = False

    def run(self):
        return

##################################################

class QAJobManager(object):
    def __init__(self, JobDir, Hosts):
        self.JobDir = os.path.join(JobDir,"QAHosts")
        self.HostRegexp = re.compile("^.*/Host\.(.+)$")
        self.JobRegexp = re.compile("^.*/JOB\.(.+)$")
        self.Hosts = Hosts
        self.HostIndex = 0
        self.MaxJobWait = 60*15  #15 min
        self.QaJobs=[]
        self.refresh()

# -----------------------------------------------------

    def refresh(self):
        self.HostData = {}
        for host in self.Hosts: self.updateHost(host)
        return

# -----------------------------------------------------

    def updateHost(self,host):
        hostDir = os.path.join(self.JobDir, 'Host.'+host)
        if not os.path.exists(hostDir): os.makedirs(hostDir)
        doRead = False
        s = os.stat(hostDir)[ST_MTIME]
        if host not in self.HostData:
            doRead = True
            self.HostData[host]={}
            self.HostData[host]['total']=0
        elif self.HostData[host]['timestamp'] != s:
            doRead = True
        self.HostData[host]['timestamp']=s
        if doRead:
            self.HostData[host]['jobs']={}
            total = 0
            for job in glob.glob(os.path.join(hostDir, 'JOB.*')):
                s1 = os.stat(job)[ST_MTIME]
                if (time.time()-s1) > self.MaxJobWait:
                    try: os.unlink(job)
                    except: pass
                    continue
                m = re.search(self.JobRegexp, job)
                if not m: continue
                jobType = m.group(1)
                weight = 1
                try:
                    jFile = open(job)
                    wt = jFile.readline()
                    jFile.close()
                    if re.search('^\d+$',wt): weight = int(wt)
                except:
                    pass
                self.HostData[host]['jobs'][jobType] = weight
                total += weight
            self.HostData[host]['total']=total
	    print 'HOST UPDATED:%s=%d' % (host,total)
        return doRead

# -----------------------------------------------------                
        
    def addJob(self,jobType,jobWeight=1):
        host,xWeight = self.getNextHost(jobWeight)
        xLock = Lock(os.path.join(self.JobDir,"lock-"+host))
        xLock.getLock()
        try:
            hostDir = os.path.join(self.JobDir, 'Host.'+host)
            if not os.path.exists(hostDir):
                try:
                    os.mkdir(hostDir)
                except:
                    pass
            jFile = open(os.path.join(hostDir,'JOB.'+jobType),"w")
            jFile.write(str(jobWeight))
            jFile.close()
            self.updateHost(host)
            time.sleep(1)
        except:
            pass
	print 'ADDED JOB:',jobType,':',jobWeight,'===>',host
        return host,xWeight

# -----------------------------------------------------                
        
    def doneJob(self,qaJob):
        jobFile = os.path.join(self.JobDir, 'Host.'+qaJob.JobHost,'JOB.'+qaJob.JobType)
        try:
            os.unlink(jobFile)
            self.updateHost(qaJob.JobHost)
            time.sleep(1)
	    qaJob.JobDone = True
	    print 'JOB Done:',qaJob.JobType,'===>',qaJob.JobHost
        except Exception, e :
	    print 'ERROR DONE:',e,'(%s,%s)' % (qaJob.JobHost,qaJob.JobType)
            pass

# -----------------------------------------------------                
        
    def activeJob(self,qaJob):
        ctime = time.time()
        if  (ctime-qaJob.ActiveTime)<180: return
        qaJob.ActiveTime = ctime
        jobFile = os.path.join(self.JobDir, 'Host.'+qaJob.JobHost,'JOB.'+qaJob.JobType)
        try:
            if os.path.exists(jobFile):
                os.system("touch "+jobFile)
		print 'ACTIVE:',qaJob.JobHost,'.',qaJob.JobType
        except:
            pass

# -----------------------------------------------------                
        
    def getNextHost(self,actWeight=1):
	sIndex = self.HostIndex
	while True:
	    while True:
	        self.HostIndex += 1
		if self.HostIndex >= len(self.Hosts) : self.HostIndex = 0
	        host = self.Hosts[self.HostIndex]
                self.updateHost(host)
                cWeight = self.HostData[host]['total']
                if (cWeight+actWeight)<=8: return host,cWeight
		if (sIndex == self.HostIndex): break
	    stateChanged=False
	    while not stateChanged:
	        time.sleep(30)
		print 'WAITING for jobs to finish ....'
                for t in self.QaJobs:
                    if t.JobDone: continue
                    if t.isAlive(): self.activeJob(t)
		    else: self.doneJob(t)
                for host in self.Hosts:
	            if self.updateHost(host):
		        stateChanged=True
        
# ----------------------------------------------------- 

    def waitForThreads(self,maxActive=0):
        while True:
            active =0
            for t in self.QaJobs:
                if t.JobDone: continue
                if t.isAlive():
                    self.activeJob(t)
                    active+=1
                else:
                    self.doneJob(t)
            print 'ACTIVE:',active,'/',maxActive
            if active>maxActive: time.sleep(30)
            else: return active
  
        
# -----------------------------------------------------

    def addQAThread(self,thread):
        thread.start()
        self.QaJobs.append(thread)

