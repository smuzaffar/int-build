#!/usr/bin/env python
 
import os, sys, time

scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

from BuilderBase import BuilderBase, ActionError
from glob import glob
from doCmd import doCmd

# ================================================================================

class AFSCleaner(BuilderBase) :
    def __init__(self, dayIn=None, plat=None):
        
        BuilderBase.__init__(self)

        self.afsTopDir = self.installDir

        self.plat = plat

        self.day = dayIn
        if not self.day:
            tomorrow = time.strftime( "%a", time.localtime(time.time()+86400) ) # get day of tomorrow
            self.day = tomorrow.lower()

        return
    
    # --------------------------------------------------------------------------------

    def cleanReleaseArea(self, dryRunIn=False):
        for d in glob(os.path.join(self.afsTopDir, self.plat)):
            try: self.checkAndRemove( os.path.join(d, self.day), dryRun=dryRunIn)
	    except Exception, e: print e 
            # clean out web area
            try: self.checkAndRemove( os.path.join(d, 'www', self.day) , dryRun=dryRunIn)
	    except Exception, e: print e
        return

    # --------------------------------------------------------------------------------

    def checkAndRemove(self, dirIn, dryRun=False):
        startDir = os.getcwd()
        if not os.path.isdir(dirIn): return
        os.chdir(dirIn)

        print '\n--------------------------------------------------------------------------------'
        print '\ncleaning out ', dirIn
        
        entries = os.listdir(".")
        for entry in entries:
            if not os.path.isdir(entry): continue # we're only interested in directories here
            # check if there is a dontTouch file, if so, remove only the file, but leave dir
            dontTouch = entry+'.dontTouch'
            if os.path.exists(dontTouch):
                cmd = 'rm -f '+dontTouch
                try: doCmd(cmd, dryRun)
                except: pass
                continue
            # no dontTouch file for entry, remove dir

            relDir = os.listdir(entry)
            rel = None
            for d in relDir:
                if d[:6] == 'CMSSW_':
                    rel = d
                    break

            if not rel:
                try: doCmd('rm -rf '+entry, dryRun)
                except: pass
                continue
            else:
                print "Going to clean out release", rel, entry
                
            cmd = 'rm -rf '+entry
            try:doCmd(cmd, dryRun)
	    except: pass

        print '\n'
        cmd = '/usr/bin/fs lq '+dirIn
        try: doCmd(cmd, False)
        except: pass

        print '\n'

        os.chdir(startDir)

        return

# ================================================================================

def usage():
    print "usage: ", os.path.basename(sys.argv[0])," [--day <day>] [--plat <arch>] [--dryRun]"
    return

if __name__ == "__main__" :
    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'h', 
                                   ['help','day=', 'plat=', 'dryRun'])
    except getopt.GetoptError:
        usage()
        sys.exit(-2)

    day    = None
    dryRun = False
    plat   = 'slc*'
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
            
        if o in ('--day',):
            day = a

        if o in ('--plat',):
            plat = a

        if o in ('--dryRun',):
            dryRun = True

    os.environ["SCRAM_ARCH"] = plat
    ac = AFSCleaner(day, plat)
    ac.cleanReleaseArea(dryRun)
