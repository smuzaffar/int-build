#!/usr/bin/env python

import os, sys

scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

# make sure we find the modules from the IB
parentPath = os.path.join(scriptPath,'../IB')
if parentPath not in sys.path:
    sys.path.append( parentPath )


from doCmd import doCmd, ActionError
from helpers import newPrefPart

class QAPublisher(object):

    def __init__(self, arch, rel):
        self.plat = arch
        self.release = rel

        self.remoteMachine = 'vocms12'
        self.remoteTopDir  = '/data/intBld/incoming/'

    def doCmd(self, cmd):

        fullCmd  = ''  # 'project CMSSW;'
        fullCmd += cmd
    
        ret = doCmd(fullCmd)

        return ret

    def setRemote(self, mach, top):
        self.remoteMachine = mach
        self.remoteTopDir  = top
        print "    reset publishing parameters to:", self.remoteMachine, self.remoteTopDir
        
    def publishPerfMatrixResults(self, part):
        self.publishPerfMatrixResults_(part)

    def publishPerfSuiteResults(self, part):
        self.publishPerfSuiteResults_(part)

    def publishValgrindXML(self, part):
        self.publishValgrindXML_(part)

    def publishVGResults(self, remDir):
        self.publishVGResults_(remDir)

    # --------------------------------------------------------------------------------
    
    def publishPerfMatrixResults_(self, part):
        remDir = self.remoteTopDir+'perfMatrix/'+self.plat+'/'+self.release+'/perfMat'
        cmd = 'ssh '+self.remoteMachine+' mkdir -p '+remDir+';'
        cmd += 'scp -q -r '+part+'/* '+self.remoteMachine+':'+remDir
        try:
            self.doCmd( cmd )
        except Exception, e:
            print "ERROR when copying log for perfMatrix :"+str(e)
            pass
	
    def publishPerfSuiteResults_(self, part):

        xpart = 'newPerf-'+newPrefPart(part)
        remDir =  self.remoteTopDir+'/'+xpart+'/'+self.plat+'/'+self.release+'/'+xpart
        cmd = 'ssh '+self.remoteMachine+' mkdir -p '+remDir+';'
        cmd += 'cd newPerf-'+part+'; tar cf - --exclude=*_valgrind.xml [A-Z]*/cpu*/results  | ssh '+self.remoteMachine+' "cd '+remDir+'; tar xf - "'
        try:
            self.doCmd( cmd )
        except Exception, e:
            print "ERROR when copying log for "+part+" :"+str(e)
            pass
        
    def publishValgrindXML_(self, part):

        xpart = 'newPerf-'+newPrefPart(part)
        remDir = os.path.join(self.remoteTopDir, xpart, self.plat, self.release, xpart)
        import publishValgrindXML
        publishValgrindXML.publishValgrindXML(rel=self.release, part=part, pubDirTop=remDir, pubHost=self.remoteMachine, arch=self.plat)
        
    def publishVGResults_(self, remDir):

        cmd = 'ssh '+self.remoteMachine+' "'+self.remoteTopDir+'/../scripts/getVgCmds.py --rel '+self.release+' --plat '+self.plat+'"'
        try:
            self.doCmd( cmd )
        except Exception, e:
            print "ERROR when creating valgrind command file"
            print "      exception ", str(e)
            print "      cmd = ", cmd

        cmd = 'scp '+self.remoteMachine+':'+self.remoteTopDir+'vgCmds-'+self.release+'-'+self.plat+'.pkl '+remDir+'/vgCmds.pkl'
        try:
            self.doCmd( cmd )
        except Exception, e:
            print "ERROR when copying over valgrind command file"
            print "      exception ", str(e)
            print "      cmd = ", cmd
