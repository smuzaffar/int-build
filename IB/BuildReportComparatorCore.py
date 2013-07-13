#!/usr/bin/env python

import os, sys, re
from BuilderBase import BuilderBase, ActionError

#============================GLOBAL=CONSTANTS===================================

intBuildRelativePath = "IntBuild/IB/"
workflowDataRelativePath = "DQMRef/data"
workflowDataRelativePath_tests = "src/tests"
buildReportsDirName = 'build_comparison_reports'
outputReportBase = buildReportsDirName
bbase = BuilderBase()
buildReportsAFSBaseFQNPath = bbase.installDir
dqmReportsAFSBaseFQNPath = '/data/sdt/SDT/html/dqm'
frontEndMachine = 'vocms12'
afsWWWLogsRelativePath = 'pyRelValMatrixLogs/run'
reportWWWDir = 'report'

# ================================================================================

class ActionError(Exception):
    def __init__(self, msg):
        self.msg = msg
        return
    def __str__(self):
        return repr(self.msg)

# ================================================================================

def getBuildArchitecture(buildName, build_machine_release_path):
    architectures = os.listdir(os.path.join(build_machine_release_path, buildName, "logs"))
    if len(architectures) != 1:
        msg = "The architecture cannot be defined, please make sure that a right build directory is used or update the getBuildArchitecture() method!";
        raise ActionError(msg)
    else:
        return architectures[0]
                
                
def getBuildName(build_machine_release_path):
    dirs = os.listdir(build_machine_release_path)
    for dir in dirs:
        if dir.startswith("CMSSW_") :
            return dir
    msg = "The name of the build cannot be defined, please make sure that a right build directory is used or update the getBuildName() method!";
    raise ActionError(msg)

def getWorkflowPath(workflow, buildName, build_machine_release_path, workflowDataRelativePath):
    workflowFQNParentPath = os.path.join(build_machine_release_path, buildName,workflowDataRelativePath)
    dirs = os.listdir(workflowFQNParentPath)
    for dir in dirs:
        if dir.startswith(str(workflow)) :
            return dir
    msg = "The directory for workflow " + workflowFQNParentPath + workflow + " cannot be found";
    raise ActionError(msg)

def getRelVersion(buildName):
    return '' + buildName[6] + '.' + buildName[8]
    
def searchReferenceBuildNameAndArchitectureInPath(path):
    if path == os.path.sep:
        print "Warning, no directory found starting with CMSSW_ in given path"
        return '', ''
    (head, tail) = os.path.split(path);
    if tail.startswith('CMSSW_'):
        build = tail #save buildName
        (head, tail) = os.path.split(head)#return the parent directory of build name
        return build, tail#return build name and architecture
    else:
        return searchReferenceBuildNameAndArchitectureInPath(head)
    
def getDQMHarvestedRootFile(workflowDirFQN):
    rex = re.compile('^DQM_V\d+_R\d+__\w+__CMSSW_[\w\d]_[\w\d]_[\w\d][_\w\d-]*.root$')
    if os.path.isdir(workflowDirFQN):
        files = os.listdir(workflowDirFQN)
        for file in files:
            isDQMFile = rex.match(file)
            if isDQMFile:
                return file
    return None

def getWorkflowNumber(workflowName):
    rex = re.compile('^([0-9\.]+)_')
    match =  rex.match(workflowName)
    return match.group(1)

def preparePythonPath(build_machine_release_path, buildFQNpath, buildArchitecture):
    scriptPath = os.path.join( build_machine_release_path, intBuildRelativePath )
    if scriptPath not in sys.path:
        sys.path.append(scriptPath)
    
    cmd = "cd " + str(buildFQNpath)+ "; SCRAM_ARCH=" + buildArchitecture + "; eval `scramv1 runtime -sh`; echo $PYTHONPATH"
    
    sysPathes = os.popen(cmd).read().strip().split(":")
    for sysPath in sysPathes:
        if sysPath not in sys.path:
                sys.path.append(sysPath)
