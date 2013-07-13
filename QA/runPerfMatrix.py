#!/usr/bin/env python

import os, sys, re, time

import random
from threading import Thread

# ================================================================================
class MatrixOpts:
  def __init__(self):
    self.what = 'all'
    self.wmcontrol = None
    self.command = None
    self.workflow = None
    self.overWrite = None
    self.testList= None
    self.dryRun=False
    self.cafVeto=True


def updateCmd (cmd):
  return re.sub('\s+-n\s+\d+',' -n 100 ',cmd) + ' --customise=Validation/Performance/TimeMemoryInfo.py '

def updateOldWF (wf):
  wf.cmdStep1 = updateCmd(wf.cmdStep1)
  wf.cmdStep2 = updateCmd(wf.cmdStep2)
  if wf.cmdStep3 : wf.cmdStep3 = None
  if wf.cmdStep4 : wf.cmdStep4 = None

def updateNewWF(wf):
  wf.cmds = wf.cmds[0:2]
  for step in range(0,2):
    wf.cmds[step] = updateCmd (wf.cmds[step])

def runSelected(testList=[], nThreads=4, show=False) :
  if not testList: testList=['1.0','2.0','3.0']  
  try:
    from Configuration.PyReleaseValidation.MatrixReader import MatrixReader
    from Configuration.PyReleaseValidation.MatrixRunner import MatrixRunner
  except Exception, e:
    bdir=os.getenv('CMSSW_RELEASE_BASE', None)
    if bdir != None:
      sys.path.insert(0,bdir+'/src/Configuration/PyReleaseValidation/scripts')
    bdir=os.getenv('CMSSW_BASE', None)
    if bdir != None:
      sys.path.insert(0,bdir+'/src/Configuration/PyReleaseValidation/scripts')
    from runTheMatrix import MatrixReader
    from runTheMatrix import MatrixRunner

  newWorkFlows = False
  opts = MatrixOpts()
  try:
    mrd = MatrixReader()
  except:
    mrd = MatrixReader(opts)
    newWorkFlows = True
  mrd.prepare()

  for wf in mrd.workFlows:
    if str(wf.numId) not in testList: continue
    print "processing ", wf.numId

    if newWorkFlows: updateNewWF(wf)
    else: updateOldWF(wf)

  ret = 0
  if show:
    if not newWorkFlows:
      for i in range(0,len(testList)): testList[i] = float(testList[i])
    mrd.show(testList)
    print 'selected items:', testList
  else:
    print 'going to run', testList
    mRunner = MatrixRunner(mrd.workFlows, nThreads)
    try:
      ret = mRunner.runTests(testList)
    except:
      opts.testList = testList
      ret = mRunner.runTests(opts)    

  return ret

# --------------------------------------------------------------------------------



# ================================================================================

if __name__ == '__main__':

  import getopt
    
  try:
    opts, args = getopt.getopt(sys.argv[1:], "j:sl:nqo:", ["nproc=",'selected','list=','showMatrix'])
  except getopt.GetoptError, e:
    print "unknown option", str(e)
    sys.exit(2)
        
# check command line parameter

  np=4 
  sel = []
  show = False

  for opt, arg in opts :
    if opt in ('-j', "--nproc" ):
      np=int(arg)
    elif opt in ('-n','-q','--showMatrix', ):
      show = True
    elif opt in ('-s','--selected',) :
      sel = []
    elif opt in ('-l','--list',) :
      sel = arg.split(',')

  ret = runSelected(testList=sel, show=show)
  sys.exit(ret)
