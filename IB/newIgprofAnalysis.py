#!/usr/bin/env python
#Quick and dirty script to run on top of V01-09-01 the old igprof-analyse analysis by Giulio
#that populated the "production" igprof-navigator AFS area at:
#/afs/cern.ch/cms/sdt/web/qa/igprof/data/
#(The performance suite now publishes data directly to /afs/cern.ch/cms/sdt/web/qa/igprof-testbed/data/)

import os, sys, glob, re
from optparse import OptionParser
from os.path import join

def yieldIgProfArgs(*t):
    yield t
    opts, anType, anFile, destFile = t
    if anType == "MEM_TOTAL":
        memLiveFile = destFile.replace('MemTotal', 'MemLive')
        memMaxFile = destFile.replace('MemTotal', 'MemMax')
        yield (opts, "MEM_LIVE", anFile, memLiveFile)
        yield (opts, "MEM_MAX", anFile, memMaxFile)

def igprofAnalyseOptions(anFile):
    #This is different when running with Validation/Performance V01-08-01 vs. V01-09-01 and older...
    #V01-08-01:
    #Here the dir structure/naming convention was (from perfNew1[2]):
    #GEN-DIGI2RAW/cpu3/TTbar_IgProf_Mem/TTBAR__GEN,SIM,DIGI,L1,DIGI2RAW_IgProfMemTotal.1.gz
    OLD_deltaFilePerfRe = re.compile('.*?IgProfperf\.(\d+)\.gz$') #This was missing...
    OLD_deltaFileMemRe = re.compile('.*?IgProfMemTotal\.(\d+)\.gz$')
    OLD_deltaFileRe = re.compile('.*?\.(\d+)\.gz$')
    #V01-09-01 and newer:
    #The structure is now (from perfNew1[2]):
    #GEN-DIGI2RAW/cpu3/TTbar_IgProf_Mem/TTbar___GEN,SIM,DIGI,L1,DIGI2RAW___NOPILEUP___MC_31X_V9___RAWSIM___IgProfMem___1.gz
    deltaFilePerfRe = re.compile('.*?IgProfPerf\_\_\_(\d+)\.gz$') #This was missing...
    deltaFileMemRe = re.compile('.*?IgProfMem\_\_\_(\d+)\.gz$') #No more igProfMemTotal for all cases...
    deltaFileRe = re.compile('.*?\_\_\_(\d+)\.gz$')
    
    anType = 'MEM_TOTAL'
    anEventsNumber = "UNKNOWN_EVENT_NUMBER"
    if   'IgProfperf'    in anFile : anType = 'PERF_TICKS'
    elif 'IgProfMemLive' in anFile : anType = 'MEM_LIVE'
    if deltaFilePerfRe.match(anFile) or OLD_deltaFilePerfRe.match(anFile): 
        anType = 'PERF_TICKS'
        anEventsNumber = deltaFilePerfRe.match(anFile).group(1)
    if deltaFileMemRe.match(anFile) or OLD_deltaFileMemRe.match(anFile):
        anType = 'MEM_TOTAL'
        anEventsNumber = deltaFileMemRe.match(anFile).group(1)
        
    #Smart up the script to pick the highest available dump to do the diff
    #This return reports no options back, so the plain vanilla analyse command is run.
    if not anEventsNumber.endswith("1"):
        return

    #Now if the file ends with 1, we can do diffs and merging:

    #This file name is the node of the issue:
    #let's massage it to make sure it is compatible with the old igprof-navigator...
    #if V01-09-01:
    #MApping of Counter with old nomenclature:
    #This is needed since we want the destination files to be the same as the old ones for compatibility
    #with the old igprof-navigator.
    IgProfNaming={
        #Old perf files: TTBAR__GEN,SIM,DIGI,L1,DIGI2RAW_IgProfperf.1.gz
        #New:            TTbar___GEN,SIM,DIGI,L1,DIGI2RAW___NOPILEUP___MC_31X_V9___RAWSIM___IgProfPerf___1.gz 
        "IgProfPerf":"IgProfperf",
        #Old mem files:  TTBAR__GEN,SIM,DIGI,L1,DIGI2RAW_IgProfMemTotal.1.gz 
        #new:            TTbar___GEN,SIM,DIGI,L1,DIGI2RAW___NOPILEUP___MC_31X_V9___RAWSIM___IgProfMem___1.gz
        "IgProfMem":"IgProfMemTotal"
        }
    if "___" in anFile:
        #Need to recompose the file name following Giulio's old naming convention:
        #TTBAR__GEN,SIM,DIGI,L1,DIGI2RAW_IgProfperf.1.sql3
        #TTBAR__GEN,SIM,DIGI,L1,DIGI2RAW_IgProfMemTotal.1.sql3
        #Manipulate the new ones:
        #TTbar___GEN,SIM,DIGI,L1,DIGI2RAW___NOPILEUP___MC_31X_V9___RAWSIM___IgProfPerf___1.gz
        #TTbar___GEN,SIM,DIGI,L1,DIGI2RAW___NOPILEUP___MC_31X_V9___RAWSIM___IgProfMem___1.gz
        (Candle,Step,PUConditions,Conditions,EventContent,IgProfProfile,EventNumber)=anFile.split(".")[0].split("___")
        #Trying to address an original problem of the script: handling of PileUp profiles... they would overwrite regular ones...
        if not "NOPILEUP" in PUConditions:
            Candle=Candle+PUConditions
        destFile=Candle+"__"+Step+"_"+IgProfNaming[IgProfProfile]+"."+EventNumber+".sql3"
    else:
        destFile = anFile.replace('.gz','.sql3')
    for x in yieldIgProfArgs("", anType, anFile, destFile):
        yield x
    for x in yieldIgProfArgs("-ml -mr 's|.*/(.*)$|\\1|'", anType, anFile,
                             destFile.replace("."+anEventsNumber,  
                             "."+anEventsNumber+"_merged")):
        yield x
    #Instead of smarting up the script to pick the highest available dump to do the diff
    #Just diff any dump w.r.t. 1st event.
    if anEventsNumber != "1":
        baseLineFile = anFile.replace("_"+anEventsNumber+".", "_1.")
        print "####BASELINE file is %s"%baseLineFile
        for x in yieldIgProfArgs("--diff-mode -b %s" % baseLineFile, anType, 
                                 anFile,
                                 destFile.replace("_"+anEventsNumber+".", "_"+anEventsNumber+"_diff1.")):
            yield x


class NewIgprofAnalyser(object):

    def __init__(self, topDirIn, debug):

        self.debug = debug
        self.topDir = topDirIn
        self.targetBase = ' /afs/cern.ch/cms/sdt/web/qa/igprof/data/'
        return

    def doAnalysis(self):

        here = os.getcwd()
        ib = here.split('/')[-3]
        plat = os.environ['SCRAM_ARCH']
        self.targetDir = os.path.join(self.targetBase, plat, ib)
        try:
            os.system('mkdir -p '+self.targetDir)
        except Exception, e:
            print "error creating target dir :", self.targetDir, str(e)

        gzFiles = glob.glob("*/*/*/*.gz")

        for gzFile in gzFiles:
            #Passing all gzFiles to the analyse function that really will handle only the numbered ones (in the new PerfSuite all are handled)
            
            ret = self.analyse(gzFile)
            if ret != 0:
                print "ERROR analysing ", gzFile

        return

    def analyse(self, gzFilePath):

        path, anFile = os.path.split(gzFilePath)
        print "going to analyse ", anFile
        
        cmd = "cd "+path+';'
        cmd += 'eval `scram run -sh`;'
        cmd += 'export QUIET_ASSERT="sa";'      # Abort on stack trace in SEAL PluginManager:
        for options in igprofAnalyseOptions(anFile):
            cmd += 'igprof-analyse --sqlite -d -v -g %s -r %s %s  | sqlite3 %s;' % options
        
        if self.debug:
            print cmd
            ret1 = 0
        else:
            #I think it's good to have this logged in the output... One could be interested in the actual igprof-analyse command to reproduce it.
            print "\n".join(cmd.split(";")) #to improve readability....
            ret1 = os.system(cmd)

        cmd = ""
        for options in igprofAnalyseOptions(anFile):
            opts, anType, anFile, destFile = options
            cmd += "cp %s %s/.;" % (join(path, destFile), self.targetDir)

        if self.debug:
            print cmd
        else:
            #I think it's good to have this logged in the output... One could be interested in the actual igprof-analyse command to reproduce it.
            print "\n".join(cmd.split(";")) #to improve readability....
            ret2 = os.system(cmd)
            if ret2 != 0:
                print "ERROR copying results to ", self.targetDir 
                print cmd
        return ret1

def main():
    parser = OptionParser()
    parser.add_option("--debug", dest="debug", action="store_true")
    opts, args = parser.parse_args()
    
    na = NewIgprofAnalyser('.', opts.debug)
    na.doAnalysis()

if __name__ == "__main__":
    main()
