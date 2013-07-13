#!/usr/bin/env python
 
import os, sys, re
from doCmd import doCmd, ActionError

scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

class ProductionRelVal(object):

    def __init__(self,cycle=None):
        self.cycle = cycle
        self.WorkFlows = {
                           'standard' : 'Configuration/PyReleaseValidation/data/cmsDriver_standard_hlt.txt',
        		   'PileUp'   : 'Configuration/PyReleaseValidation/data/cmsDriver_PileUp_hlt.txt',
                         }
        self.CVSCheckOut={
                           'PRODAGENT'             : 'PRODAGENT_0_12_18_patch1',
                           'PRODCOMMON/src/python' : 'PRODCOMMON_0_12_18_patch1',
                           'DLS/Client/LFCClient'  : 'DLS_1_1_2',
                         }
        self.PAEnvPath=  {
                           'PRODAGENT_CONFIG'      : 'PRODAGENT/etc/ProdAgentConfig.xml',
                         }
        self.PythonEnv=  [
                           'PRODCOMMON/src/python',
                           'PRODAGENT/src/python',
                           'DLS/Client/LFCClient',
                         ]
        self.ExtraCVSChecouts=[
                                '-r 1.53 PRODAGENT/ops/workflowcreation/prepareRelValWorkflows.py',
                              ]
        return

    def getCMSSWFile(self,rFile):
        for bdir in self.cmsswBase,self.cmsswReleaseBase:
            aFile = bdir+'/src/'+rFile
            if os.path.exists(aFile): return aFile
        
        return None
        
    def initWorkFlowTxtFiles(self):
        cmd = 'runTheMatrix.py --show --raw all'
        try: doCmd(cmd)
        except: pass
        for wf,wfFile in self.WorkFlows.iteritems():
            xFile = os.getcwd()+'/'+'cmsDriver_'+wf.lower()+'_hlt.txt'
            if not os.path.exists(xFile):
                aFile = self.getCMSSWFile(wfFile)
                if aFile and os.path.exists(aFile): doCmd('cp '+aFile+' '+xFile)
        return
        
    def getWorkFlowTxtFile(self,workFlow):
        aFile = None
        xFile = os.getcwd()+'/'+'cmsDriver_'+workFlow.lower()+'_hlt.txt'
        if os.path.exists(xFile): aFile = xFile
        return aFile

    def doInit(self):
        print 'prodRelVal> staring test .....'
        try:
            self.cmsswBase = os.environ['CMSSW_BASE']
            print 'prodRelVal> Running for: '+self.cmsswBase
            print 'prodRelVal> DBS_CLIENT_CONFIG => '+os.environ['DBS_CLIENT_CONFIG']
        except:
            print "prodRelVal> ERROR: Caught exception: " + str(e)
            print "prodRelVal> ERROR: CMSSW_BASE environment is not set. Make sure you run this script with CMSSW environment set."

        self.testDir = self.cmsswBase+'/prodRelVal'
        try:
            self.cmsswReleaseBase = os.environ['CMSSW_RELEASE_BASE']
            if self.cmsswReleaseBase == "": self.cmsswReleaseBase = self.cmsswBase
        except:
            self.cmsswReleaseBase = self.cmsswBase
            pass
        self.initWorkFlowTxtFiles()
        for wf,wfFile in self.WorkFlows.iteritems():
            relFile = self.getWorkFlowTxtFile(wf)
            if not relFile:
                print 'prodRelVal> ERROR: Can not find/generate ',wfFile,' in CMSSW release.'
        	sys.exit(1)
            self.WorkFlows[wf] = relFile
            print 'prodRelVal> '+wf+' txt file: '+relFile

        cmd = 'rm -rf '+self.testDir+'; mkdir -p '+self.testDir+'/wf '
        for wf in self.WorkFlows: cmd += self.testDir+'/wf/'+wf+' '
        doCmd(cmd)
        os.chdir(self.testDir)

        for module,tag in self.CVSCheckOut.iteritems():
           cmd = 'cvs -Q checkout -r '+tag+' '+module
           doCmd(cmd)

        for sdir in self.PythonEnv:
            os.environ['PYTHONPATH']=self.testDir+'/'+sdir+':'+os.environ['PYTHONPATH']

        for env,value in self.PAEnvPath.iteritems():
            os.environ[env] = self.testDir+'/'+value

        for cvsfile in self.ExtraCVSChecouts:
            cmd = 'cvs checkout '+cvsfile
            doCmd(cmd)

        return

    def doTest(self):
        self.doInit()
        script = self.testDir+'/PRODAGENT/ops/workflowcreation/prepareRelValWorkflows.py'
        try:
            from  Configuration.AlCa.autoCond import autoCond
        except:
            from  Configuration.PyReleaseValidation.autoCond import autoCond
        mcTag = re.sub('::.*','',autoCond['mc'])
        for wf,wfFile in self.WorkFlows.iteritems():
            processing_version = 'v1'
            cmssw_version = re.sub("_X_20.*","_X",os.environ['CMSSW_VERSION'])
            exopt = ''
            if wf == 'PileUp':
        	exopt =  ' --lumi 666666 --pileup /RelValMinBias/'+cmssw_version+'-'+mcTag+'-'+processing_version+'/GEN-SIM-DIGI-RAW-HLTDEBUG '
        	cmssw_version = 'CMSSW_3_11_0'
	
            cmd  = 'cd '+self.testDir+'/wf/'+wf+'; cp '+wfFile+' workflows.txt; '
            cmd += ' CMSSW_VERSION='+cmssw_version+' '+script
            cmd += ' --scripts-dir '+self.testDir+'/PRODAGENT/util '
            cmd += ' --samples '+wfFile
            cmd += ' --version '+processing_version
            cmd += ' --DBSURL http://cmsdbsprod.cern.ch/cms_dbs_prod_local_01/servlet/DBSServlet '
            cmd += ' --only-sites srm-cms.cern.ch '
            #cmd += ' --DBSURL http://cmssrv46.fnal.gov:8080/DBS209/servlet/DBSServlet '
            #cmd += ' --only-sites cmssrm.fnal.gov '
            cmd += ' --store-fail --debug --workflow-label '+wf
            cmd += exopt
            try:
                doCmd(cmd)
                pass
            except Exception, e:
                pass

        return
  
    def parseResults(self, ProdRelValDir):
        if not os.path.exists(ProdRelValDir): return
        timeFile = ProdRelValDir+'/timingInfo.txt'
        if not os.path.exists(timeFile): return 
        inFile=open(timeFile)
        lines = inFile.readlines()
        inFile.close()

        flag=False
        data = {}
        summry = ""
        for line in lines:
            line = re.sub('\s+s$','',line.strip())
            if not flag:
                if re.match('.*Details of time per workflow:$',line): flag = True
                else: summry += line + '\n'
            else:
                try:
                    xml,time = line.split(':',2)
                    xml = xml.strip()
                    time = time.strip()
                    xFile = ProdRelValDir+'/'+xml
                    size = 0
                    if os.path.exists(xFile): size = os.path.getsize(xFile)
                    data[xml]=[time, size]
                except Exception, e:
                    pass
        
        return

# ================================================================================

def usage():
    print "Usage:", os.path.basename(sys.argv[0]), " [--cycle=<cycle>] [--help]"
    return

# ================================================================================

def main():

    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'h', 
                                   ['help','useLocal','cycle='])
    except getopt.GetoptError, msg:
        print msg
        usage()
        sys.exit(-2)

    cyc      = None
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
        if o in ('--cycle',):
            cyc = a

    try:
        rb = ProductionRelVal(cycle=cyc)
        rb.doTest()
    except Exception, e:
        print "prodRelVal> ERROR: Caught exception: " + str(e)

    return

# ================================================================================

if __name__ == "__main__":

    main()
