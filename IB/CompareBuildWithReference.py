#!/usr/bin/env python

from BuildReportComparatorCore import *
from optparse import OptionParser
from StatisticsHTMLParser import *
import errno, doCmd
import time
from threading import Thread

def main():
    
    parser = OptionParser()
    
    usage = "usage: %prog [option1] arg1 [option2] arg2 ... [optionN] argN"
    parser = OptionParser(usage=usage)
    parser.add_option("-b", "--buildDir",
                  dest="buildDir",
                  help="build directory")
    parser.add_option("-r", "--releaseDir",
                  dest="releaseDir",
                  help="release directory")
    parser.add_option("-d", "--dryRun",
                  action="store_true", dest="dryRun",
                  help="is a dry run?")
    parser.add_option("-p", "--platform",
                  dest="platform",
                  help="used architecture")
    parser.add_option("-c", "--relCycle",
                  dest="relCycle",
                  help="Release cycle")
    parser.add_option("-s", "--stamp",
                  dest="stamp",
                  help="Release stamp")
    parser.add_option("-t", "--relTag",
                  dest="relTag",
                  help="Release tag")
    parser.add_option("-u", "--custom_ib",
                  action="store_true",
                  dest="custom_ib",
                  help="Sets the specific configuration for running DQM comparison for Custom IBs.")
    parser.add_option("-e", "--report_path",
                  dest="report_path",
                  help="Path to report. Optional value")
    parser.add_option("-o", "--report_relative_path",
                  dest="report_relative_path",
                  help="Relative Path to report. The value is used for compiling report web page url. Optional value")
    
    (options, args) = parser.parse_args()
    
    dryRun = False
    
    if not options.dryRun == None:
        dryRun = options.dryRun
    
    custom_ib = False
    if not options.custom_ib == None:
        custom_ib = options.custom_ib
 
    if options.buildDir == None:
        print "The Integration Build directory is not specified"
        return errno.EINVAL
    
    buildDir = options.buildDir
    report_path = options.report_path
    report_relative_path = options.report_relative_path
    
    while buildDir.endswith('/'):
        buildDir = buildDir[:(len(buildDir)-1)]
    (head, stamp) = os.path.split(buildDir)
    head.strip() #hack, don't show never read warning
    
    if options.stamp == None: 
        stamp = str(stamp).strip()
    else:
        stamp = options.stamp
    
    if options.relTag == None:
        buildName = getBuildName(buildDir)
    else:
        buildName = options.relTag
    
    if options.platform == None:
        buildArchitecture = getBuildArchitecture(buildName, buildDir)
    else:
        buildArchitecture = options.platform
    
    if options.relCycle == None:
        rel = getRelVersion(buildName)
    else:
        rel = options.relCycle
    
    
    intBldFQNPath = os.path.dirname(os.path.dirname(buildDir))
    
    if not options.releaseDir == None:
        buildNameFQNPath = options.releaseDir
    else:
        buildNameFQNPath = os.path.join(buildDir, buildName)
    
    if not os.path.exists(buildNameFQNPath):
        print 'Build is not found in common path %s' % str(buildNameFQNPath)
        buildNameFQNPath = os.path.join(intBldFQNPath, 'cms', buildArchitecture, 'cms', 'cmssw', buildName)
        print 'Looking for the build in %s' % str(buildNameFQNPath)
        if not os.path.exists(buildNameFQNPath):
            print 'The build location cannot be found, terminating ...'
            return errno.ENOENT

    import config
    config.setDefaults(rel)
    relMonParameters = config.Configuration[rel]['RelMonParameters']
    if custom_ib:
        deployer_spec_file = os.path.join( buildNameFQNPath, 'tmp', 'tmpspec-cmssw-dqm-reference-deployer')
        referenceBuildName = config.getDQMReferenceBuild(deployer_spec_file)
    else:    
        referenceBuildName = config.getDQMReferenceBuild()
    if not referenceBuildName:
        print "Reference build doesn't exist in configuration, exiting comparison ..."
        return errno.ENOENT
    
    referenceBuildFQNPath = getReferenceBuildFQNPath(config, rel, referenceBuildName, buildArchitecture);
    if not os.path.exists(referenceBuildFQNPath):
        referenceBuildFQNPath2 = os.path.join(buildNameFQNPath, buildArchitecture, 'cms', 'cmssw-dqm-reference-deployer', referenceBuildName, 'data')
        print "Reference build path %s doesn't exist, will search in %s" % (referenceBuildFQNPath,referenceBuildFQNPath2,)
        referenceBuildFQNPath = referenceBuildFQNPath2
        
    (referenceBuildName, referenceBuildArchitecture) = searchReferenceBuildNameAndArchitectureInPath(referenceBuildFQNPath)
    
    threshold = getRelMonValue(relMonParameters,'threshold')
    statTest = getRelMonValue(relMonParameters,'statTest')
    doPngs = getRelMonValue(relMonParameters,'doPngs')
    doComparison = getRelMonValue(relMonParameters,'doComparison')
    doReport = getRelMonValue(relMonParameters,'doReport')
    no_successes = getRelMonValue(relMonParameters,'no_successes')
    black_list = getRelMonValue(relMonParameters,'black_list')
    success_percentage = getRelMonValue(relMonParameters, 'success_percentage')
    
    workflowFQNParentPath = os.path.join(buildNameFQNPath, workflowDataRelativePath)
    if not os.path.exists(workflowFQNParentPath):
        workflowFQNParentPath2 = os.path.join(buildNameFQNPath, workflowDataRelativePath_tests)
        print 'The workflow location %s cannot be found, will search in %s' % (workflowFQNParentPath, workflowFQNParentPath2,)
        workflowFQNParentPath = workflowFQNParentPath2
        if not os.path.exists(workflowFQNParentPath):
            print 'The workflow location %s cannot be found, terminating ...' % workflowFQNParentPath
            return errno.ENOENT
         
    
    dirs = os.listdir(workflowFQNParentPath)
    wThreads = {}
    for workflowDir in dirs:
        if 'HARVEST' in workflowDir:
            workflow = getWorkflowNumber(workflowDir)
            workflowDirFQN = os.path.join(workflowFQNParentPath, workflowDir)
            dqmHarvestedRootFile = getDQMHarvestedRootFile(workflowDirFQN)
            if dqmHarvestedRootFile is not None:
                rootfileBuildFQN = os.path.join(workflowDirFQN, dqmHarvestedRootFile)
                
                ## reference build root file
                referenceWorkflows = os.listdir(referenceBuildFQNPath)
                referenceBuildWorkflowFQNPath = None
                for referenceWorkflow in referenceWorkflows:
                    if referenceWorkflow.startswith(str(workflow)):
                        referenceBuildWorkflowFQNPath = os.path.join(referenceBuildFQNPath, referenceWorkflow)
                        break
                
                if referenceBuildWorkflowFQNPath == None:
                    print "Workflow ", str(workflow), " doesn't exist in the reference build folder ", str(referenceBuildFQNPath) 
                    continue #go to next workflow iw current one is missing
                    
                refRootfileBuild = getDQMHarvestedRootFile(referenceBuildWorkflowFQNPath)
                if refRootfileBuild is not None:
                    refRootfileBuildFQN = os.path.join(referenceBuildWorkflowFQNPath, refRootfileBuild)
                    print "comparing file ", rootfileBuildFQN, " with ", refRootfileBuildFQN
                    outputReportName = workflow
                    outputReportDir = os.path.join(buildNameFQNPath, outputReportBase, outputReportName)
                    increment = 0
                    while os.path.exists(outputReportDir):
                        increment = increment + 1
                        outputReportDir = outputReportDir + '-' + str(increment)
                    os.makedirs(outputReportDir)
                    waitThreads(wThreads,config.MachineCPUCount)
		    thrd = Thread(target=makeComparison, args=(buildNameFQNPath,
                                                               buildArchitecture, 
                                                               no_successes, 
                                                               rootfileBuildFQN, 
                                                               refRootfileBuildFQN, 
                                                               outputReportDir, 
                                                               threshold, 
                                                               statTest, 
                                                               doPngs, 
                                                               doComparison, 
                                                               doReport, 
                                                               workflowDir, 
                                                               workflowFQNParentPath,
                                                               black_list, 
                                                               success_percentage, 
                                                               stamp, 
                                                               rel, 
                                                               outputReportName, 
                                                               buildName,
                                                               workflow,
                                                               referenceBuildName,
                                                               report_path, 
                                                               report_relative_path,
                                                               dryRun))
                    wThreads[thrd]=1
		    thrd.start()
		    time.sleep(2)
                else:
                    print '%s folder doesn\'t contain the referencing DQM harvested root file.' % workflowDir
            else:
                print '%s folder doesn\'t contain the DQM harvested root file.' % workflowDir
    
    waitThreads(wThreads)
    #if os.path.exists(outputReportDir):
    #    print 'Deleting temporary build report dir output'
    #    doCmd.doCmd('rm -rf %s' % outputReportDir, dryRun)
    
    print "Done"
        
    return
    
#=====================================================================================

def waitThreads(wThreads, maxThreads=0):
  if maxThreads<=0: maxThreads=1
  while True:
    for t in wThreads.keys():
      if not t.isAlive():
        del wThreads[t]
    if len(wThreads) < maxThreads: break
    time.sleep(10)
  return
  
def getReferenceBuildFQNPath(config, rel, referenceBuildName, buildArchitecture):
    cms_path = os.path.expandvars("$CMS_PATH")
    return os.path.join(cms_path, buildArchitecture, "cms", "cmssw-dqm-reference-deployer", referenceBuildName , "data")
    

def getRelMonValue(relMonParameters, value):
    for paramKey, paramValue in relMonParameters.iteritems():
        if cmp(paramKey, value) == 0:
            return paramValue
    raise ActionError('no such paramater %s' % value )

    
def makeComparison(buildNameFQNPath, buildArchitecture, no_successes, rootfileBuild, rootFileBuildRef, outputReportDir, threshold, statTest, doPngs, doCompare, doReport, sample, workflowFQNParentPath, black_list, success_percentage, stamp, rel, outputReportName, buildName, workflow, referenceBuildName, report_path, report_relative_path, dryRun):
    preCmd = "SCRAM_ARCH=%s; cd %s; eval `scramv1 runtime -sh`;" % (buildArchitecture, buildNameFQNPath)
    cmd = "compare_using_files.py"
    if no_successes != 0:
        cmd += " --no_successes"
    
    cmd += " %s" % rootfileBuild
    cmd += " %s" % rootFileBuildRef
    cmd += ' --sample Global --metas "%s@@@%s"' % (buildName, referenceBuildName)
    cmd = preCmd + cmd
    
    if len(black_list)>0:
        cmd += " -B"
        for element in black_list:
            cmd += (" %s" % element)
    
    if cmp(outputReportDir, "") != 0:
        cmd += " -o %s" % outputReportDir
    
    if cmp(threshold, "") != 0:
        cmd += " -t %s" % threshold
        
    if cmp(statTest, "") != 0:
        cmd += " -s %s" % statTest
        
    if doPngs:
        cmd += " -p"
    
    if doCompare:
        cmd += " -C"
    
    if doReport:
        cmd += " -R"

    logFileFQNPath = '%s.log' % outputReportDir
    
    cmd += ' > %s 2>&1' % logFileFQNPath
    fQNPathToLogFile, logFileName = os.path.split(logFileFQNPath)
    fQNPathToLogFile = fQNPathToLogFile.strip()
    print cmd
    
    comparisonState = 'NOTRUN' ## in case of not running the comparison or raised exceptions
    ret = -1
    try:
        ret = doCmd.doCmd(cmd, dryRun)
        print "Comparison finished with exit code: %s" % str(ret)
        if ret == 0:
            relMonSummaryFQNPath = os.path.join(outputReportDir, 'RelMonSummary.html')
            statisticsParser = StatisticsHTMLParser()  # create new parser object
            f = open(relMonSummaryFQNPath, 'r')
            statisticsParser.feed(f.read())
            statisticsParser.close()
            n_successes = float(statisticsParser.n_successes)
            n_fails = float(statisticsParser.n_fails)
            n_nulls = float(statisticsParser.n_nulls)
            n_total = n_successes + n_fails + n_nulls
            
            if n_total != 0: 
                fail_percentage = (n_fails + n_nulls) * 100.00 / n_total
                success_percentage = float(success_percentage)
                if fail_percentage > success_percentage:
                    comparisonState = 'FAILED'
                else:
                    comparisonState = 'PASSED'
            
            cmd = '%s dir2webdir.py %s' % (preCmd, outputReportDir)
            doCmd.doCmd(cmd, dryRun)                   
                         
    except Exception, e:
        print "ERROR: Caught exception during making comparison report: %s" % str(e)
    #end = (datetime.datetime.now())
    if report_relative_path:
        buildReportRelativePath = report_relative_path
    else:
        buildReportRelativePath = os.path.join(buildArchitecture, buildName)
        
    if report_path:
        pathToWWW = report_path #i.e. '/afs/cern.ch/cms/sdt/internal/requests/customIB/slc5_amd64_gcc470/yana/1520'
    else:
        pathToWWW =  str(os.path.join(buildReportsAFSBaseFQNPath, buildArchitecture, 'www', stamp[:3], rel+'-'+stamp))
        pathToDQMComp = str(os.path.join(dqmReportsAFSBaseFQNPath, buildReportRelativePath))
    report = ""
    if ret == 0:
        report = os.path.join(buildReportRelativePath, reportWWWDir, workflow)
        reportFQNPath = os.path.join(pathToDQMComp, reportWWWDir)
        try:
            doCmd.doCmd('ssh %s "mkdir -p %s"' % (frontEndMachine, reportFQNPath) , dryRun)
            doCmd.doCmd('scp -r %s %s:%s' % (outputReportDir, frontEndMachine, reportFQNPath) , dryRun)
        except:
            print "Error: an Error occured while copying reports into build machine"
    else:
        report = os.path.join(buildReportRelativePath, reportWWWDir, workflow, logFileName)
        reportFQNPath = os.path.join(pathToDQMComp, reportWWWDir, workflow)
        try:
            doCmd.doCmd('ssh %s "mkdir -p %s"' % (frontEndMachine, reportFQNPath) , dryRun)
            doCmd.doCmd('scp %s %s:%s' % (logFileFQNPath, frontEndMachine, reportFQNPath), dryRun)
        except:
            print "Error: an Exception occured while copying reports into build machine"
    line = '%s Comparison-%s report: %s\r\n' % (sample, comparisonState, report)
    sumlog=os.path.join(os.path.dirname(os.path.abspath(outputReportDir)), 'runall-comparison.log')
    f = open(sumlog, 'a')
    f.write(line)
    f.close()
    try:
        if report_path:
            doCmd.doCmd('cp %s %s' % (sumlog, os.path.join(report_path, 'runall-comparison.log')), dryRun)
        else:
            doCmd.doCmd('cp %s %s' % (sumlog, os.path.join(pathToWWW, buildName, afsWWWLogsRelativePath, 'runall-comparison.log')), dryRun)
    except:
        print "Error: an Error occured while copying runall-comparison.log file into afs location"
    return
   

#=====================================================================================

if __name__ == "__main__":

    main()
