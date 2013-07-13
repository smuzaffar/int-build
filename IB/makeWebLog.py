#!/usr/bin/env python

import os, sys, time

scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

from BuilderBase import BuilderBase
from doCmd import doCmd, ActionError
import config
# ================================================================================

class WebLogger(BuilderBase):

    def __init__(self, dayIn=None, relCycIn=None, dryRunIn=False,doInstall=True) :

        BuilderBase.__init__(self)

        self.day = dayIn
        if not self.day :
            self.day = time.strftime("%a").lower()

        self.dryRun = dryRunIn
        self.topDir = os.path.join(self.installDir, self.plat)
        self.relCycle = relCycIn
	self.doInstall = doInstall
        self.cand = None
        config.setDefaults (relCycIn)

        return

    # --------------------------------------------------------------------------------

    def makeWebLog(self, rel, candIn, tcTag=None):

        self.prepare(rel, candIn, tcTag)

        self.createWebLog()
        
        return

    # --------------------------------------------------------------------------------

    def prepare(self, rel, candIn, tcTag=None):
        
	if tcTag == None :
            tcTag = rel

        self.cand = candIn
        self.release = rel
        
        self.relDir = os.path.join( self.topDir, self.day, candIn, rel)
        self.webDir = os.path.join(self.topDir, 'www', self.day, candIn, rel)
        self.tcTag = tcTag
        if not self.doInstall: return
        if not os.path.exists(self.webDir) and not self.dryRun:
            print "Preparing web log for rel ",rel, 'candIn', candIn, 'tctag', tcTag
            print '          in ', self.topDir, 'day', self.day
            os.makedirs(self.webDir)

        return
    
    # --------------------------------------------------------------------------------

    def createWebLog(self):

        if not self.doInstall: return
        try:
            cmd = 'cd '+self.webDir + ';'
            cmd += 'ln -s '+ os.path.join(self.relDir, 'tmp', self.plat,'cache','log','html') + ' new ;'
            doCmd(cmd, self.dryRun)
        except: # ignore failures ...
            pass

        try:
	    cmd = 'cd '+self.webDir + ';'
            cmd += 'ln -s '+ os.path.join(self.relDir+"/..", 'prebuild.log') + ' . ;'
            doCmd(cmd, self.dryRun)
        except: # ignore failures ...
            pass

        try:
            startFlag = False
	    inFile = open( os.path.join(self.relDir,"logs",self.plat, 'release-build.log'), 'r')
	    outFile = open ( os.path.join(self.webDir, 'scramInfo.log'), 'w')	    
            for line in inFile.readlines():
		if not startFlag:
		    if line.startswith("Resetting caches"): startFlag = True
		else:
		    if line.startswith(">> Local Products Rules"): break
		    outFile.write(line)
	    inFile.close()
	    outFile.close()
            print "scramInfo log file created at", os.path.join(self.webDir, 'scramInfo.log')
        except: # ignore failures ...
            pass

        try:
            cmd = 'cd '+self.webDir + ';'
            cmd += 'ln -s '+ os.path.join(self.relDir,"logs",self.plat, 'release-build.log') + ' . ;'
            doCmd(cmd, self.dryRun)
        except: # ignore failures ...
            pass
        
        try:
            cmd = 'cd '+self.relDir + '/src ;'
            cmd += 'for D in `ls -d */*/data`; do echo $D " : " `ls $D/*.cf[ifg] 2>/dev/null | wc -l` ; done '
            cmd += '> '+ os.path.join(self.webDir, 'cfgInfo.log') + ' 2>/dev/null;'
            doCmd(cmd, self.dryRun)
        except: # ignore failures ...
            pass
            
        return
    
    # --------------------------------------------------------------------------------

    def sendMailAlerts(self, scriptDir):

        # get config to see if we should send mails:
        sendMails = False
        try:
            sendMails = config.Configuration[self.relCycle]['sendDevMail']
        except Exception, e:
            print "ERROR when trying to see if we should send mails, nothing send."
            print str(e)
            return
        
        #-ap: temporarily disable mails for non-standard platforms (as we
        # now switched the build of those from 1.9 to 2.0 ...
        if self.plat != 'slc4_ia32_gcc345':
            print "Will not send mails on non-standard platform"
            return

        if not sendMails:
            print "Config requested to NOT send mails to developers."
            return

        # send mails only for "official builds"
        hour = self.tcTag[-4:]
        if ( hour != '0200' and
             hour != '1600' ) :
            print "Ignoring non-official release", self.tcTag, hour
            return
        
        cmd = scriptDir+"/send_mail_alerts.pl "
        cmd += self.webDir + '/nightly-alerts '

        print "in: ", os.getcwd(), "going to execute:"
        print cmd
        doCmd(cmd, self.dryRun)
            
        return

    # --------------------------------------------------------------------------------
    
    def getWebLogDir(self):
        return self.webDir



# ================================================================================

def usage():
    print "usage:", sys.argv[0]," --cand <cand> --rel <release> --tctag <TCtag> --day <day>"
    return

# ================================================================================

if __name__ == '__main__' :

    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'h', 
                                   ['help','cand=', 'rel=', 'tctag=','dryRun', 'day='])
    except getopt.GetoptError:
        print "Unknown option"
        usage()
        sys.exit(-2)

    rc = None
    rel = None
    tcTag = None
    day = None
    dryRun = False
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
            
        if o in ('--cand',):
            rc = a
        if o in ('--rel',):
            rel = a
        if o in ('--tctag',):
            tcTag = a
        if o in ('--day',):
            day = a
        if o in ('--dryRun',):
            dryRun = True

    if not rc or not rel or not day:
        usage()
        sys.exit()

    wl = WebLogger(day, dryRun)
    wl.makeWebLog(rel, rc, tcTag=None)
