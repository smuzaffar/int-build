#!/usr/bin/env python
#Quick and dirty script to avoid running on top of V01-09-01 the old igprof-analyse analysis by Giulio
#that populated the "production" igprof-navigator AFS area at:
#/afs/cern.ch/cms/sdt/web/qa/igprof/data/
#(The performance suite now publishes data directly to /afs/cern.ch/cms/sdt/web/qa/igprof-testbed/data/)

#In lazy fashion this script assumes that the sql3 files already saved in the IgProf dirs are good
#(i.e. the perfsuite igprof-analyse commands executed with no mistakes/errors) and the issue is only the new naming convention.
#So basically it implements only a name-translation and copy over to the igprof/data area of the new sql3 profiles.

import os, sys, glob, re
from optparse import OptionParser
from os.path import join

class NewIgprofAnalyser(object):

    def __init__(self, topDirIn, debug):

        self.debug = debug
        self.topDir = topDirIn
        self.targetBase = ' /afs/cern.ch/cms/sdt/web/qa/igprof/data/' #' /afs/cern.ch/user/g/gbenelli/scratch0/igproftests/'  
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

        SQLFiles = glob.glob("*/*/*/*.sql3")

        SumRet=0
        for SQLFile in SQLFiles:
            print "Processing %s"%SQLFile
            #Passing all NEW SQL files to the GetDestFileName() function that returns the "translated" old naming convention name
            if "___" in SQLFile:
                cmd = "cp %s %s/%s;" % (SQLFile,self.targetDir,self.GetDestFileName(SQLFile))
                
                if self.debug:
                    print cmd
                else:
                    #I think it's good to have this logged in the output... One could be interested in the actual igprof-analyse command to reproduce it.
                    print "\n".join(cmd.split(";")) #to improve readability....
                    ret = os.system(cmd)
                    if ret != 0:
                        print "ERROR copying %s to %s"%(SQLFile,self.targetDir) 
                        #print cmd
                    SumRet=SumRet+ret
            else:
                print "File does not match the new naming convention... ignoring it"
                pass
        return SumRet

    def GetDestFileName(self,SQLFile):
        #MApping of Counter with old nomenclature:
        #This is needed since we want the destination files to be the same as the old ones for compatibility
        #with the old igprof-navigator.
        IgProfNaming={
            #Old perf files: TTbar__GEN,FASTSIM_IgProfperf.1.sql3
            #New:            TTbar___GEN,FASTSIM___NOPILEUP___MC_31X_V9___RAWSIM___PERF_TICKS___1.sql3
            "PERF_TICKS":"IgProfperf",
            #Old mem files:  TTbar__GEN,FASTSIM_IgProfMemLive.1.sql3
            #new:            TTbar___GEN,FASTSIM___NOPILEUP___MC_31X_V9___RAWSIM___MEM_LIVE___1.sql3
            "MEM_LIVE":"IgProfMemLive",
            "MEM_MAX":"IgProfMemMax",
            "MEM_TOTAL":"IgProfMemTotal"
            }
        
        #Need to recompose the file name following Giulio's old naming convention:
        #TTBAR__GEN,SIM,DIGI,L1,DIGI2RAW_IgProfperf.1.sql3
        #TTBAR__GEN,SIM,DIGI,L1,DIGI2RAW_IgProfMemTotal.1.sql3
        #Manipulate the new ones:
        #TTbar___RAW2DIGI,RECO___NOPILEUP___MC_31X_V9___RECOSIM___MEM_LIVE___1.sql3
        #TTbar___GEN,SIM,DIGI,L1,DIGI2RAW___NOPILEUP___MC_31X_V9___RAWSIM___MEM_LIVE___51_diff_1.sql3
        #DEBUG:
        print os.path.basename(SQLFile).split(".")[0]
        (Candle,Step,PUConditions,Conditions,EventContent,IgProfProfile,EventNumber)=os.path.basename(SQLFile).split(".")[0].split("___")
        #Trying to address an original problem of the script: handling of PileUp profiles... they would overwrite regular ones...
        if not "NOPILEUP" in PUConditions:
            Candle=Candle+PUConditions
        DestSQLFile=Candle+"__"+Step+"_"+IgProfNaming[IgProfProfile]+"."+EventNumber+".sql3"
            
        return DestSQLFile

        return ret1

def main():
    parser = OptionParser()
    parser.add_option("--debug", dest="debug", action="store_true")
    opts, args = parser.parse_args()
    
    na = NewIgprofAnalyser('.', opts.debug)
    na.doAnalysis()

if __name__ == "__main__":
    main()
