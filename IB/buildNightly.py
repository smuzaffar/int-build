#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import re
import urllib2

scriptPath = os.path.dirname(os.path.abspath(sys.argv[0]))
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

import doCmd
import config
from BuilderBase import BuilderBase
from manageWeb import WebManager


# ================================================================================

class NightlyBuilder(BuilderBase):

    def __init__(self, relCycle, buildDir):

        BuilderBase.__init__(self)
        print 'Entered in NightlyBuild constructor after invoking base class one!...'

        self.buildDir = buildDir
        self.updateTimeStamp(self.buildDir)

        self.relCycle = relCycle
        self.webMgr = WebManager(self.relCycle, self.stamp, self.dryRun)

        self.relTag = None
        self.tcTag = None

        self.logger = None
        self.webLog = None
        config.setDefaults(self.relCycle)

        return

    # --------------------------------------------------------------------------------

    def dumpInfo(self):

        import socket
        print ' host    : ', socket.gethostname()
        print ' buildDir: ', self.buildDir
        print ' dryRun  : ', self.dryRun
        print ' plat    : ', self.plat
        print ' relCycle: ', self.relCycle
        print ' stamp   : ', self.stamp
        print ' relTag  : ', self.relTag
        print ' tcTag   : ', self.tcTag

        return

    # --------------------------------------------------------------------------------

    def setDryRun(self, dryRun):
        self.dryRun = dryRun

        return

    # --------------------------------------------------------------------------------

    def readConfig(self):
        self.configuration = config.Configuration[self.relCycle]
        return

    # --------------------------------------------------------------------------------

    def doBuild(self):

        self.tcTag = self.configuration['tagCollTag']
        self.relTag = self.configuration['releaseTag'] + '_' \
            + self.timeStamp  # this is the release to use ...
        
        if self.domain != 'cern.ch':
            self.tcTag = self.relTag

        print 'Building of ', self.relTag, 'starting.'
        self.dumpInfo()

        self.cmsswBuildDir += '/' + self.relTag

        self.webMgr.setupJob('Integration build starting')
        self.webMgr.uploadPkgList(self.relTag)
        from buildRelease import ReleaseBuilder

        rb = ReleaseBuilder(self.buildDir, self.configuration)
        if self.dryRun:
            rb.setDryRun()

        try:
            rb.doBuild(self.relTag, self.tcTag)
        except Exception, e:
            print 'ERROR: Caught exception during doBuild : ' + str(e)

        self.doScramInstall()

        return

    # --------------------------------------------------------------------------------

    def doScramInstall(self):

        cmd = self.cmsinit + ';  scram install -f'
        try:
            self.doCmd(cmd, self.dryRun, self.cmsswBuildDir)
        except:
            pass

        return

    # --------------------------------------------------------------------------------

    def runTests(self):

        if '_CLANG_' in self.relTag: return
        cmd = self.cmsenv + '; unset DISPLAY; '
        cmd += 'export QUIET_ASSERT="sa";'  # Abort on stack trace in SEAL PluginManager:
        #cmd += 'ulimit -v 4096000;' #no needed anymore
        cmd += scriptPath + '/runTests.py --releaseDir ' \
            + self.cmsswBuildDir + ' --buildDir ' + self.buildDir

        if self.dryRun:
            cmd += ' --dryRun '
        try:
            self.doCmd(cmd, True, self.cmsswBuildDir)
        except:
            pass

        return

    # --------------------------------------------------------------------------------

    def checkBuildLog(self):

        # prepare new-style logs:
        bldLogDir = self.cmsBuildDir + '/WEB/build-logs/' + self.plat + '/' + self.relTag +'/logs/src'
        if os.path.exists(bldLogDir):
            try:
                cmd  = 'cd ' + self.cmsswBuildDir + '; mkdir -p tmp/'+self.plat+'/cache/log; '
                cmd += 'cp -r '+ bldLogDir + ' tmp/'+self.plat+'/cache/log/'
                self.doCmd(cmd, self.dryRun)
            except:
                pass

        print 'Going to create new-style log files ...'
        try:
            topURL = 'http://cern.ch/cms-sdt/rc/' + self.plat + '/www/' \
                + self.stamp[:3] + '/' + self.relCycle + '-' \
                + self.stamp + '/' + self.relTag + '/new/'
            cmd = 'cd ' + os.path.join(
                self.cmsswBuildDir,
                'tmp',
                self.plat,
                'cache',
                'log',
                'src',
                ) + ';'
            cmd += scriptPath + '/buildLogAnalyzer.py --topURL ' \
                + topURL
            self.doCmd(cmd, self.dryRun)
        except:
            pass

        self.webMgr.uploadLog('./build.log')

        return

    # --------------------------------------------------------------------------------

    def install(self):

        print 'in ', os.getcwd(), ' going to install'

        from installRelease import ProjectInstaller

        pi = ProjectInstaller()
        if dryRun or self.domain == 'testing':
            pi.setDryRun()

        try:
            pi.setupCand(self.relCycle + '-' + self.stamp, self.relTag,
                         self.stamp[:3])
        except Exception, e:
            print 'ERROR: Caught exception during installation setup : ' \
                + str(e)
            return

        try:
            pi.install()
        except Exception, e:
            print 'ERROR: Caught exception during install : ' + str(e)
            return

        return

    # --------------------------------------------------------------------------------

    def makeWebLog(self, doInstall=True):

        if not self.webLog:
            print '\n==> in ', os.getcwd()
            from makeWebLog import WebLogger
            try:
                print '\n==> Going to call weblogger with :', \
                    self.stamp[:3], self.relTag, self.relCycle + '-' \
                    + self.stamp, self.tcTag
                self.webLog = WebLogger(self.stamp[:3], self.relCycle,
                        self.dryRun, doInstall)
                self.webLog.prepare(self.relTag, self.relCycle + '-'
                                    + self.stamp, self.relTag)
            except Exception, e:
                print 'ERROR: Caught exception when creating weblog : ' \
                    + str(e)

        return

    # --------------------------------------------------------------------------------

    def setupLogger(self, doInstall=True):

        if not self.logger:
            self.makeWebLog(doInstall)
            from logUpdater import LogUpdater

            self.logger = LogUpdater(self.buildDir, doInstall)
            self.logger.setRelease(self.relTag, self.relCycle,
                                   self.stamp)
            if self.dryRun:
                self.logger.setDryRun()

        return

    # --------------------------------------------------------------------------------

    def buildRelease(self, doInstall=True):

        print 'Now entering buildRelease() under buildNightly....'
        self.readConfig()

        print '\n' + 80 * '=' + '\n'
        try:
            self.doBuild()
        except Exception, e:
            print 'Caught exception during build ', str(e)

        print '\n' + 80 * '=' + '\n'
        self.checkBuildLog()

        print '\n' + 80 * '=' + '\n'
        try:
            self.setupLogger(doInstall)
        except Exception, e:
            print 'Caught exception during making web logs', str(e)

        if doInstall:
            self.webMgr.sendMsg('Installing release ... ')
            print '\n' + 80 * '=' + '\n'
            try:
                self.install()
            except Exception, e:
                print 'Caught exception during installation', str(e)
        else:
            print 'noInstall requested, release not installed'

        print '\n' + 80 * '=' + '\n'
        self.webLog.createWebLog()

        try:
            import tagCollectorAPI
            tagCollectorAPI.createQARequest(self.relTag, self.plat)
        except Exception, e:
            print 'Caught exception during creating QA request', str(e)

        self.webMgr.sendMsg('Running tests ... ')
        print '\n' + 80 * '=' + '\n'
        try:
            self.runTests()
        except Exception, e:
            print 'Caught exception during testing', str(e)
            pass

        print 'buildNightly>> Release Build/test part is done'
        self.webMgr.tearDown('Integration build finished')

        return


# ================================================================================

def usage():
    print 'usage:', os.path.basename(sys.argv[0]), \
        ' --releasecycle <rel> --buildDir <buildDir> [--dryRun]'
    print """
    where:
       <rel>    is the release cycle to be build (e.g. 1.6)
       <buildDir>  is the directory where to start the build
    """

    return


# ================================================================================

if __name__ == '__main__':

    import getopt
    options = sys.argv[1:]
    try:
        (opts, args) = getopt.getopt(options, 'hnb:r:', ['help',
                'dryRun', 'releasecycle=', 'buildDir=', 'noinstall'])
    except getopt.GetoptError, e:
        print e.msg
        usage()
        sys.exit(-2)

    dryRun = False
    rel = None
    builDir = None
    install = True

    for (o, a) in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()

        if o in ('-n', '--dryRun'):
            dryRun = True

        if o in ('-r', '--releasecycle'):
            rel = a

        if o in ('-b', '--buildDir'):
            buildDir = a

        if o in ('--noinstall', ):
            install = False

    plat = os.environ['SCRAM_ARCH']

    spiScriptDir = os.path.abspath(os.path.dirname(sys.argv[0]))

    if not rel or not buildDir:
        usage()
        sys.exit(-1)

    print 'Release : ', rel
    print 'BuidlDir : ', buildDir
    nb = NightlyBuilder(rel, buildDir)
    if dryRun:
        nb.setDryRun(dryRun)
    nb.buildRelease(install)

