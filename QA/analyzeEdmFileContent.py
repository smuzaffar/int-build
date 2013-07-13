#!/usr/bin/env python

import os, sys


class EdmFileContentAnalyzer(object):

    def __init__(self, force):

        self.plat = 'slc4_ia32_gcc432'
        self.pre1 = 'export SCRAM_ARCH='+self.plat+';'
        self.pre2 = self.pre1+ 'eval `scram run -sh`;'

        self.rel = os.popen(self.pre1+"scram l CMSSW | grep CMSSW_3_4_X | tail -2 | head -1 | awk '{print $2}'").readlines()[0].strip()
        
        self.setup(force)
        
    def setup(self, force):

        cmd = self.pre1

        if os.path.exists(self.rel):
            if force: os.system("rm -rf "+self.rel)
            else:
                print "ERROR: release directory already existing for ", self.rel
                print "       nothing done. If you want to remove it, use the --forceClean option.\n"
                sys.exit(-1)
            
        cmd += 'scram p CMSSW '+self.rel+'; cd '+self.rel+'/src;'
        cmd += 'eval `scram run -sh`;'
        cmd += 'mkdir act;'
        cmd += 'mkdir ref;cd ref;'
        cmd += 'tar zxf /afs/cern.ch/user/a/andreasp/public/refRaw-31X-20091111.tgz;'
        cmd += 'tar zxf /afs/cern.ch/user/a/andreasp/public/refRec-31X-20091111.tgz;'
        ret = os.system(cmd)
        if ret != 0:
            print "ERROR preparing devel area : ", ret

    def analyze(self, relDir, host=None):

        os.chdir(self.rel+'/src/act')
        print 'now in ', os.getcwd()

        path = relDir+'/src/Configuration/PyReleaseValidation/data/run/24.0_TTbar+RECO1+ALCATT1/'
        if 'CMSSW_3_2_' in path:
            path = path.replace('/24.0_', '/24_')
        cmd = 'cp '+path+'/r*.root .'
        if host:
            cmd = 'scp '+host+':'+path+'/r*.root .;'

        print "going to copy root files from ", host+':'+path
        ret = os.system( cmd )
        if ret != 0:
            print "ERROR copying root files from ", host+':'+path
            return

        print "going to analyze raw ..."
        cmd = self.pre2
        cmd += 'mkdir cmpRaw; cd cmpRaw;'
        cmd += 'runEdmFileComparison.py --describeOnly ../raw.root --verbose --private --single >../raw.log 2>&1;'
        ret = os.system(cmd)
        if ret != 0:
            print "ERROR analysing raw files: ", ret, 'from ', cmd

        print "going to analyze reco ..."
        cmd = self.pre2
        cmd += 'mkdir cmpRec; cd cmpRec;'
        cmd += 'runEdmFileComparison.py --describeOnly ../reco.root --verbose --private --single >../reco.log 2>&1;'
        ret = os.system(cmd)
        if ret != 0:
            print "ERROR analysing reco files: ", ret, 'from ', cmd

        print '\n'+"-"*80+'\n'
        print "Diff for raw (ref: 31X-2009-11-11):\n"
        cmd = 'diff --exclude logfiles --rec --brief ../ref/refRaw ./cmpRaw;'
        os.system(cmd)
        print '\n'+"-"*80+'\n'
        print "Diff for reco (ref: 31X-2009-11-11):\n"
        cmd = 'diff --exclude logfiles --rec --brief ../ref/refRec ./cmpRec;'
        os.system(cmd)
        print "\n"

# ================================================================================

def main():
    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'hnr:', 
                                   ['help','dryRun','relDir=','host=','forceClean'])
    except getopt.GetoptError:
        usage()
        sys.exit(-2)

    dryRun = False
    relDir = None
    host   = None
    force  = False
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
            
        if o in ('n', '--dryRun',):
            dryRun = True

        if o in ('n', '--forceClean',):
            force = True

        if o in ('r', '--relDir',):
            relDir = a
            
        if o in ('--host',):
            host = a

    if not relDir:
        usage()
        sys.exit(-1)

    ea = EdmFileContentAnalyzer(force)
    ea.analyze(relDir, host)


# ================================================================================

def usage():
    print "usage: ", os.path.basename(sys.argv[0])," "
    return

# ================================================================================


if __name__ == "__main__":
    main()
    
    
