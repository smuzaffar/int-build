#!/usr/bin/env python

# this needs python 2.4 !

import os, sys, time, re, urllib, getpass

def getPkgListFromTC(rel) :

    if not os.environ.has_key("CVSROOT") :
        print "CVSROOT not set, aborting !!!"
        sys.exit(-1)

    #  use .netrc for info on user/pwd
    url = 'https://cmstags.cern.ch/tc/CreateTagList?release='+rel

    print "going to get info from TC for release ", rel
    print "using url: '"+url+"'"

    lines = []
    page = os.popen('wget --no-check-certificate -nv -o /dev/null -O- '+url )
    lines = page.readlines()
    page.close()

    pkgRe = re.compile('<tr>\s*<td>\s*([A-Z].*)\s*</td>\s*<td>\s*(V.*)\s*</td>.*')

    ignoreList = ["config", "SCRAMToolbox"]
    pkgMap = {}
    for line in lines:
        pkgMatch = pkgRe.match(line)
        if pkgMatch :
            pkg = pkgMatch.group(1)
            ver = pkgMatch.group(2)
            if pkg in ignoreList : continue
            pkgMap[pkg] = ver
            #print pkg, ver

    return pkgMap

from threading import *
class Runner(Thread):
    def __init__(self, pkg, ver):
        Thread.__init__(self)
        self.pkg = pkg
        self.ver = ver
    def run(self):
        cmd = "cvs -Q co -r " + self.ver + " " + self.pkg
        tries = 10
        while tries>0:
            tries-=1
            ret = os.system(cmd)
            if ret == 0:
                print "Package ", self.pkg, " version", self.ver, "checkout SUCCESSFUL"
                return
            elif tries>0:
                print "Package ", self.pkg, " version", self.ver, "checkout returned ", ret, ' retrying ... '
                time.sleep(5)
        print " ... Package ", self.pkg, " version", self.ver, "checkout FAILED"
        return

def activeThreads(threadList):
    n = 0
    for t in threadList:
        if t.isAlive() :
            n += 1
    return n

def doCheckout(pkgMap):

    keyList = pkgMap.keys()

    print "going to check out ", len(keyList), "packages."

    # 25->10 as we got errors as we had errors last night 
    nPar = 5   # don't use more, this one gives spurious locks already :-(
    threadList = []
    for pkg,ver in pkgMap.items():
        co = Runner(pkg, ver)
        threadList.append(co)
        co.start()

        n = activeThreads(threadList)
        while  n > nPar:
            time.sleep(1)
            n = activeThreads(threadList)
            
    return

def checkoutRelease(rel):
    pkgMap = getPkgListFromTC(rel)
    doCheckout(pkgMap)
    return

def usage():
    print 'usage',sys.arvg[0],'--release <rel>'
    print ""
    print "example:"
    print '   ',sys.arvg[0],'--release CMSSW_1_3_4'
    return

if __name__ == "__main__" :
    
    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'h', 
                                   ['help','release='])
    except getopt.GetoptError:
        usage()
        sys.exit(-2)

    rel = None
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
            
        if o in ('--release',):
            rel = a


    if not rel:
        usage()
        sys.exit(-1)

    checkoutRelease(rel)

