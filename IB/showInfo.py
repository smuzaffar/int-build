#!/usr/bin/env python

import os, sys, time, socket

scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

from checkTestLog import TestLogChecker

def findRel(dir):
    startDir = os.getcwd()
    os.chdir(dir)
    entries = os.listdir(".")
    for entry in entries:
        if entry[:6] == "CMSSW_" : return entry
    return "Unknown"

def runPipe(cmd):
    pipe = os.popen(cmd)
    result = pipe.readlines()
    pipe.close()
    return result[0].strip()

def getInfo(dirIn):

    os.chdir(dirIn)

    rel = findRel(dirIn)
    print '\n\nrunning on ', socket.gethostname(), 'checking for', rel
    print "\n"
    print runPipe("w | head -1")
    print "\n--------------------------------------------------------------------------------\n"

    checkedOut = runPipe("grep -e 'Package ' ./prebuild.log 2>/dev/null | wc -l")
    logFile = rel+'/tmp/slc4_ia32_gcc345/cache/log/src/*/*/build.log'
    buildsDone  = runPipe('grep -c -e "^>> Package .* built" '+logFile+'  2>/dev/null | grep -v ":0" | wc -l ')
    buildErrors = runPipe('grep "gmake: *** " '+logFile+'  2>/dev/null | wc -l ')
    prc = int(100*float(buildsDone)/float(checkedOut))
    print "==> build ", buildsDone, ' of ', checkedOut, '('+str(prc)+'% with ', buildErrors,'errors)'

    print "\n--------------------------------------------------------------------------------\n"
    
    testLogs = rel+'/runTests.log'
    if os.path.exists(testLogs) :
        tlc = TestLogChecker()
        tlc.check(testLogs)
    else:
        print "no test logs available"

    print "\n--------------------------------------------------------------------------------\n"

    runLog = rel+"/src/Configuration/PyReleaseValidation/data/runall.log"
    chkRelVals(runLog, "PyRelVal")    

    print "\n--------------------------------------------------------------------------------\n"
    
    runLog = rel+"/src/Configuration/ReleaseValidation/data/runall.log"
    chkRelVals(runLog, "RelVal")
    
    print "\n--------------------------------------------------------------------------------\n"

    return

def chkRelVals(runLog, hdr):

    relValPass = runPipe("grep -e '^Done with ' "+runLog+" 2>/dev/null | grep -v ' cmsRun ' | grep PASS | wc -l ")
    relValFail = runPipe("grep -e '^Done with ' "+runLog+" 2>/dev/null | grep -v ' cmsRun ' | grep FAIL | wc -l ")
    relValAbrt = runPipe("grep -e '^Done with ' "+runLog+" 2>/dev/null | grep -v ' cmsRun ' | grep ABORTED | wc -l ")

    prcP = 0
    prcF = 0
    prcA = 0
    sum = float(relValAbrt)+float(relValFail)+float(relValPass)
    if sum > 0.:
        prcP = int(100.*float(relValPass)/sum)
        prcF = int(100.*float(relValFail)/sum)
        prcA = int(100.*float(relValAbrt)/sum)

    print "\n==> "+hdr+": ",
    print " PASS ",  relValPass, '('+str(prcP)+' %) ',
    print " FAIL ",  relValFail, '('+str(prcF)+' %) ',
    print " ABORTED",relValAbrt, '('+str(prcA)+' %)'

    return

# ================================================================================

def usage():
    print "usage: ", os.path.basename(sys.argv[0])," --topDir <dir>"
    return

# ================================================================================

if __name__ == "__main__" :
    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'h', 
                                   ['help','topDir='])
    except getopt.GetoptError:
        usage()
        sys.exit(-2)

    topDir = None
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
            
        if o in ('--topDir',):
            topDir = a

    getInfo(topDir)
