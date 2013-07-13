#!/usr/bin/env python

import os, sys, re, time
from procTree import ProcessTree
# ================================================================================

def WatchAndKill(pid, user=None, listOnly=False):
  print "WatchAndKill started with pid " + str(pid)
  procChk = {}
  procChk['^cmsRun ']=[60*60*4,False]
  procChk['/testing\.log;\s*fi\s*$'] = [60*30,False]
  procChk['python\s+whiteRabbit.py\s+'] = [60*60*2,False]
  procChk['/runTheMatrix.py\s+']=[60*60*8,True]    #Kill child only
  procChk['/IB/runTests.py\s+']=[60*60*12,True]    #Kill child only
  procs = ProcessTree(user, detail=True, xinfo=None, show=False)
  startTime = -1
  while True:
    procs.updateSelected(None, None, pid)
    if (len(procs.selectedTree)==0) or (procs.all[pid].stime <= startTime): break
    startTime = procs.all[pid].stime
    for p in procs.selectedTree:
      proc = procs.all[p]
      maxRunAge=0
      for cmd in procChk:
        if re.search(cmd,proc.arg) and (proc.stime > procChk[cmd][0]):
          print "Job reached max allocated time: ",proc.arg, ' ===> ', proc.stime,'/',procChk[cmd][0]
          proc2kill = ProcessTree(user, detail=True, xinfo=None, show=True)
          if listOnly: proc2kill.updateSelected(None, None, p)
          elif procChk[cmd][1]:
            for cp in proc.child: proc2kill.killSelected(None, None, cp)
          else: proc2kill.killSelected(None, None, p)
    time.sleep(10)
    procs.allProcesses(user)
  return

# ================================================================================

def usage(code=0):
  print "usage: ", sys.argv[0], '--pid <processid> [--user <login>] [--dryRun] [-h|--help]'
  sys.exit(code)

# ================================================================================

if __name__ == "__main__":
  import getopt
  options = sys.argv[1:]
  try: opts, args = getopt.getopt(options, 'h', ['help','dryRun','pid=', 'user='])
  except getopt.GetoptError: usage(-2)
  dryRun  = False
  pid = None
  user = None
  for o, a in opts:
    if o in ('-h', '--help'): usage(0)
    elif o == '--dryRun': dryRun = True
    elif o == '--pid' :   pid = a
    elif o == '--user' :  user = a
  if not pid: usage(-2)
  WatchAndKill(pid,user,dryRun)
