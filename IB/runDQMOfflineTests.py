#!/usr/bin/env python

import doCmd, os, time, glob
from optparse import OptionParser

profDataRootDir = '/afs/cern.ch/cms/sdt/web/qa/dqm/data/'
daysToKeepIgProfData = 2


def renameAndCopyToIgProf(dryRun, platform, relTag, os, cmd, doCmd, test, fqnTestDirName, testOutputFile):
    fqnTestOutputFile = os.path.join(fqnTestDirName, testOutputFile)
    testOutputFileParts = testOutputFile.rsplit('_')
    sql3filePartsSeparator = '___'
    candle = 'MultiJet'
    tiers = 'ALL-PROMPTRECO'
    pileup = 'RealData'
    global_tag = 'AUTOCOM_' + test
    process = 'PROMPT-RECO'
    counter = 'MEM_LIVE'
    number_of_events = '500'
    i = 0
    for testOutputFilePart in testOutputFileParts:
        if testOutputFilePart.isdigit():
            number_of_events = str(testOutputFilePart)
        elif testOutputFilePart == 'MEM':
            next_part = testOutputFileParts[i + 1].rsplit('.')[0]
            if next_part == 'TOT':
                next_part = 'TOTAL'
            counter = "MEM_" + next_part
        i += 1
    
    testOutputSQL3FileName = candle + sql3filePartsSeparator + tiers + sql3filePartsSeparator + pileup + sql3filePartsSeparator + global_tag + sql3filePartsSeparator + process + sql3filePartsSeparator + counter + sql3filePartsSeparator + number_of_events + '.sql3'
    igProfOutputDirRoot = profDataRootDir + platform
    igProfOutputDir = igProfOutputDirRoot + "/" + relTag
    print 'igProfOutputDir=', igProfOutputDir
    
    if not os.path.exists(igProfOutputDir):
        os.makedirs(igProfOutputDir)
    cmd = 'cp ' + fqnTestOutputFile + " " + os.path.join(igProfOutputDir, testOutputSQL3FileName)
    doCmd.doCmd(cmd, dryRun)

def cleanupOld(igProfOutputDirRoot, dryRun):
    igProfOutputDirRoot = igProfOutputDirRoot.strip()
    if igProfOutputDirRoot != '' and igProfOutputDirRoot != '/' and not igProfOutputDirRoot.startswith('//'):  #to prevent deleting /* folder
        dirs = igProfOutputDirRoot+'/*'
        dirsToCheck = [ igProfOutputDirRoot+'/*' ]
        print 'dirsToCheck=',dirsToCheck
        delDirOlder = time.time() - (60 * 60 * 24 * daysToKeepIgProfData)
        print 'Cleanup> deleting data older than ',daysToKeepIgProfData,' days from ', igProfOutputDirRoot
        for xdir in dirsToCheck:
            for sdir in glob.glob(xdir):
                if os.path.getctime(sdir)<=delDirOlder:
                    try:
                        doCmd.doCmd('rm -rf '+sdir, dryRun)
                    except:
                        pass
    else:
        print "ignoring " + igProfOutputDirRoot + " folder as it may delete important files"
    return

def main():
    
    parser = OptionParser()
    
    usage = "usage: %prog [option] arg"
    parser = OptionParser(usage=usage)
    parser.add_option("-r", "--releaseDir",
                  dest="releaseDir",
                  help="release directory")
    parser.add_option("-p", "--platform",
                  dest="platform",
                  help="release architecture")
    parser.add_option("-d", "--dryRun",
                  action="store_true", dest="dryRun",
                  help="is a dry run?")
    
    (options, args) = parser.parse_args()
    
    dryRun = False
    platform = None
    releaseDir = None
    relTag = None
    
    if not options.dryRun == None:
        dryRun = options.dryRun
    
    if options.releaseDir == None:
        print "Release directory is not specified!"
        parser.print_help()
        return errno.EINVAL
    if options.platform == None:
        print "Release architecture is not specified!"
        parser.print_help()
        return errno.EINVAL
    
    platform = options.platform
    releaseDir = options.releaseDir
    head, relTag = os.path.split(releaseDir)
    if relTag == None or relTag == "":
        relTag = os.path.basename(head)
    tests = '11,15'
    testsArr = tests.rsplit(',')
    testDir = "DQMServices/Components/test"
    
    igProfOutputDirRoot = profDataRootDir + platform
    cleanupOld(igProfOutputDirRoot, dryRun)
        
    cmd = "cd " + releaseDir + "/src/"+testDir+"; python whiteRabbit.py -j 2 -n " + tests
    doCmd.doCmd(cmd, dryRun)

    for test in testsArr:
        test = test.strip()
        fqnDQMToolsTestsDirName = os.path.join(options.releaseDir, "src", testDir)
        dirs = os.listdir(fqnDQMToolsTestsDirName)
        for dir in dirs:
            fqnDir = os.path.join(fqnDQMToolsTestsDirName, dir)
            if os.path.isdir(fqnDir):
                if dir.isdigit():
                   fqnTestDirName = os.path.join(fqnDQMToolsTestsDirName, dir, test)
                   testOutputFiles = os.listdir(fqnTestDirName)
                   for testOutputFile in testOutputFiles:
                       if testOutputFile.endswith('.sql'):
                           fqnTestOutputFile = os.path.join(fqnTestDirName, testOutputFile)
                           testOutputSQL3FileName = "OutPutSqliteFileInIgprofFormat.sql3"
                           fqnTestOutputSQL3File = os.path.join(fqnTestDirName, testOutputSQL3FileName)
                           cmd = "sqlite3 < " + fqnTestOutputFile + " " + fqnTestOutputSQL3File
                           doCmd.doCmd(cmd, dryRun)
                           renameAndCopyToIgProf(dryRun, platform, relTag, os, cmd, doCmd, test, fqnTestDirName, testOutputSQL3FileName)
                       elif testOutputFile.endswith('.sql3'):
                           renameAndCopyToIgProf(dryRun, platform, relTag, os, cmd, doCmd, test, fqnTestDirName, testOutputFile)
                break
    

#=====================================================================================

if __name__ == "__main__":

    main()
