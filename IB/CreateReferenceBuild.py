#!/usr/bin/env python

import sys, errno, doCmd
from BuildReportComparatorCore import *
from optparse import OptionParser


scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

def main():
    
    parser = OptionParser()
    
    usage = "usage: %prog [option1] arg1"
    parser = OptionParser(usage=usage)
    parser.add_option("-r", "--releaseDir",
                  dest="releaseDir",
                  help="release directory")
    parser.add_option("-d", "--dryRun",
                  action="store_true", dest="dryRun",
                  help="is a dry run?")
    parser.add_option("-p", "--platform",
                  dest="platform",
                  help="used architecture")
    
    (options, args) = parser.parse_args()
    
    dryRun = False
    
    if not options.dryRun == None:
        dryRun = options.dryRun
 
    if options.releaseDir == None:
        print "The Release directory is not specified"
        return errno.EINVAL
    
    buildNameFQNPath = options.releaseDir
    
    (buildDir, buildName) = os.path.split(options.releaseDir)

    if buildName == '': #if releaseDir is ending with a separator
        (buildDir, buildName) = os.path.split(buildDir)
    
    if options.platform == None:
        buildArchitecture = getBuildArchitecture(buildName, buildDir)
    else:
        buildArchitecture = options.platform

    preparePythonPath(buildDir, buildName, buildArchitecture)
    
    buildReferenceBuildArchitectureFQNPath = os.path.join(reference_build_path, buildArchitecture)
    if not os.path.exists(buildReferenceBuildArchitectureFQNPath):
        print "Creating architecture folderfolder ", buildReferenceBuildArchitectureFQNPath
        os.makedirs(buildReferenceBuildArchitectureFQNPath)
    else:
        print "Using existing architecture folder ", buildReferenceBuildArchitectureFQNPath 


    buildReferenceBuildFQNPath = os.path.join(buildReferenceBuildArchitectureFQNPath, buildName)
    if not os.path.exists(buildReferenceBuildFQNPath):
        print "Creating build folder ", buildReferenceBuildFQNPath
        os.makedirs(buildReferenceBuildFQNPath)
    else:
        print "Warning! Using existing build folder ", buildReferenceBuildFQNPath , ". The folder should not exist normally!"
    
    workflowFQNParentPath = os.path.join(buildNameFQNPath, workflowDataRelativePath)
    if not os.path.exists(workflowFQNParentPath):
        print 'The path with workflows is not found: ' + str(buildNameFQNPath)
        workflowFQNParentPath = os.path.join(buildNameFQNPath, 'pyRelval')
        print 'looking for the worklfows in ' + workflowFQNParentPath
        if not os.path.exists(workflowFQNParentPath):
            print 'The workflow location cannot be found, terminating ...'
            return errno.ENOENT
    
    dirs = os.listdir(workflowFQNParentPath)
    for workflowDir in dirs:
        if 'HARVEST' in workflowDir:
            workflowDirFQN = os.path.join(workflowFQNParentPath, workflowDir)
            dqmHarvestedRootFile = getDQMHarvestedRootFile(workflowDirFQN)
            if dqmHarvestedRootFile is not None:
                dqmHarvestedRootFileFQN = os.path.join(workflowDirFQN, dqmHarvestedRootFile)
                buildReferenceWorkflowFQNPath = os.path.join(buildReferenceBuildFQNPath, workflowDir)
                if not os.path.exists(buildReferenceWorkflowFQNPath):
                    print "Creating build folder ", buildReferenceWorkflowFQNPath
                    os.makedirs(buildReferenceWorkflowFQNPath)
                else:
                    print "Warning! Using existing build folder ", buildReferenceWorkflowFQNPath , ". The folder should not exist normally!"
                
                buildReferenceWorkflowDQMRootFQNFileName = os.path.join(buildReferenceWorkflowFQNPath, dqmHarvestedRootFile)
                doCmd.doCmd('cp ' + dqmHarvestedRootFileFQN + " " + buildReferenceWorkflowDQMRootFQNFileName, dryRun)
            else:
                print workflowDir +' folder doesn\'t contain the DQM harvested root file.'
    
    
    print "Done"  
    return

if __name__ == "__main__":

    main()