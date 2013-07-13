#! /usr/bin/env python
import os, sys, glob, re

class PyRelVals(object):
    def __init__(self, jobs):
        self.StepsPerJob=4
	self.jobs=jobs

    def parseLog(self):
        logData = {}
        logRE = re.compile('^([1-9][0-9]*\.[0-9]+)[^/]+/step([1-9])_.*\.log$')
        for logFile in glob.glob('[1-9]*/step[0-9]*.log'):
            m = logRE.match(logFile)
            if not m: continue
            wf = m.group(1)
            step = int(m.group(2))-1
            if step>=self.StepsPerJob: continue
            if not logData.has_key(wf):
                logData[wf] = {'events' : [], 'failed' : [], 'warning' : []}
                for s in range(0,self.StepsPerJob):
                    for k in logData[wf].keys(): logData[wf][k].append(-1)
            warn=0
            err=0
            rd=0
            inFile = open(logFile)
            for line in inFile:
                if '%MSG-w' in line: warn+=1
                if '%MSG-e' in line: err+=1
                if 'Begin processing the ' in line: rd+=1
            inFile.close()
            logData[wf]['events'][step]=rd
            logData[wf]['failed'][step]=err
            logData[wf]['warning'][step]=warn

        from pickle import Pickler
        outFile = open('runTheMatrixMsgs.pkl', 'w')
        pklFile = Pickler(outFile)
        pklFile.dump(logData)
        outFile.close()
        return

    def run(self,args=''):
        cmd = 'runTheMatrix.py --nproc '+str(self.jobs)+' '+args
        try:
            from commands import getstatusoutput
            ret, outX = getstatusoutput(cmd)
            if outX: print outX
        except Exception,e:
            print "runPyRelVal> ERROR during test PyReleaseValidation : caught exception: " + str(e)

        self.parseLog()
        return
                
def main(argv) :
    import getopt
    try:
        opts, args = getopt.getopt(argv, "", ["nproc=","args="])
    except getopt.GetoptError, e:
        print "unknown option", str(e)
        sys.exit(2)
    np=8
    xargs = ''
    for opt, arg in opts :
        if opt == "--nproc" :
            np=arg
        elif opt == "--args" :
            xargs=arg
    pyRel = PyRelVals(np)
    pyRel.run(xargs)
    return

if __name__ == '__main__' :
    main(sys.argv[1:])
