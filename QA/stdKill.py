#!/usr/bin/env python
import os,sys,re, getpass

thisPath = os.path.abspath(sys.argv[0])
try:                  scriptPath = os.path.abspath(__file__)
except Exception, e : scriptPath = thisPath

class Process:
  def __init__(self):
    self.child = []
    self.cmd = ''
    self.arg = ''
    self.ppid = 0

  def data(self, ppid, cmd, arg):
    self.cmd = cmd
    self.arg = arg
    self.ppid = ppid

  def addChild(self, pid):
    self.child.append(pid)

class ProcessTree:
  def __init__(self, user=None, detail=False):
    self.allProcesses(user)
    self.detail = detail

  def allProcesses(self, user=None):
    if not user: user = getpass.getuser()
    cmd = 'ps -ao pid,ppid,comm,args -U %s -u %s' % (user,user)
    pipe = os.popen(cmd)
    res = pipe.readlines()
    pipe.close()
    self.all = {}
    pRE = re.compile('^\s*(\d+)\s+(\d+)\s+([^\s]+)\s*(.*)$')
    xpid = os.getpid()
    for pros in res:
      m = pRE.match(pros)
      if m:
         pid = m.group(1)
         ppid = m.group(2)
         if (int(pid) == xpid) or (int(ppid) == xpid): continue
         if not self.all.has_key(ppid): self.all[ppid]=Process()
         if not self.all.has_key(pid):  self.all[pid]=Process()
         self.all[pid].data(ppid, m.group(3), m.group(4))
         self.all[ppid].addChild(pid)
    return

  def updateSelected(self, command=None, args=None):
    if not command: command = '.+'
    if not args:    args    = '.*'
    self.selected = {}
    cRE = re.compile(command)
    aRE = re.compile('.*'+args+'.*')
    for pid in self.all:
      if cRE.match(self.all[pid].cmd) and aRE.match(self.all[pid].arg): self._addChildren(pid)
    self.dump = []
    for p in self.selected: self.dumpParentTree(p)
    self.dump = None
    self.all = None

  def dumpParentTree(self, pid):
    if pid in self.dump: return
    ppid = self.all[pid].ppid
    if ppid in self.selected: self.dumpParentTree(ppid)
    else: self.printInfo(pid)

  def printInfo(self, pid, tab=''):
     if not (pid in self.selected): return
     cmd = self.all[pid].cmd
     arg = self.all[pid].arg
     if not self.detail:
       cmd = cmd[0:25]
       arg = arg[0:120]  
     print tab+pid+'\t'+self.all[pid].ppid+'\t'+cmd+'\t'+arg
     self.dump.append(pid)
     for p in self.all[pid].child: self.printInfo(p, tab+'  ')

  def _addChildren(self, pid):
    self.selected[pid]=1
    for p in self.all[pid].child: self._addChildren(p)

  def killSelected(self, command, args):
    if (not command) or (not args): return
    self.updateSelected(command, args)
    if not self.selected: return
    cmd = 'kill -9 '
    for pid in self.selected: cmd += pid+' '
    print 'Running ',cmd
    pipe = os.popen(cmd)
    res = pipe.readlines()
    pipe.close()

# ================================================================================

def usage():
  print "usage:", os.path.basename(sys.argv[0]), " --cycle <releaseCycle> [--platfrom <SCRAM_ARCH>]"
  return

# ================================================================================

def checkRemoteStdTests(cycle, user, kill):
  precmd = "ps -ao args -U %s -u %s | grep '^ssh '" % (user, user)
  cmd = precmd + " | grep CMSSW_%s_X_20 | awk '{print $4}' | sed 's|.*/CMSSW_|CMSSW_|;s|/cmdFile.*||' | sort | uniq" %  (cycle)
  pipe = os.popen(cmd)
  rels = pipe.readlines()
  pipe.close()
  for rel in rels:
    rel = rel.strip('\n')
    print "Release "+rel
    cmd = precmd + " | grep %s | awk '{print $3}' | sort | uniq" % (rel)
    pipe = os.popen(cmd)
    machs = pipe.readlines()
    pipe.close()
    cscript = os.path.join(os.environ["HOME"], os.path.basename(scriptPath))
    for mach in machs:
      mach = mach.strip('\n')
      cmd = 'cp -u %s %s; ssh %s "%s --command tcsh --args /%s/cmdFile" %s'
      cmd = cmd % (scriptPath, cscript, mach, cscript, rel, kill)
      print "cmd> %s" % (cmd)
      pipe = os.popen(cmd)
      for line in pipe.readlines(): print line.strip('\n')
      pipe.close()
  return

def main():
  import getopt
  options = sys.argv[1:]
  try:
    opts, args = getopt.getopt(options, 'h',['help', 'kill', 'detail', 'cycle=', 'user=', 'command=', 'args='])
  except getopt.GetoptError, msg:
    print msg
    usage()
    sys.exit(-2)

  cyc     = None
  command = None
  args    = None
  user    = getpass.getuser()
  kill    = ''
  detail  = False
  for o, a in opts:
    if o in ('-h', '--help'):
      usage()
      sys.exit()
    elif o in ('--cycle',):
      cyc = a
    elif o in ('--user'):
      user = a
    elif o in ('--detail'):
      detail = True
    elif o in ('--command'):
      command = a
    elif o in ('--args'):
      args = a
    elif o in ('--kill', '-k'):
      kill = o
  if cyc:
    checkRemoteStdTests(cyc,user,kill)
  else:
    x = ProcessTree(user, detail)
    if kill: x.killSelected  (command, args)
    else:    x.updateSelected(command, args)
  return

# ================================================================================
if __name__ == "__main__": sys.exit(main())
