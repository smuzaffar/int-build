#!/usr/bin/env python
import sys,os,time
from Lock import Lock

def createDev(rel,packs):
    if not os.path.exists(rel+'/lib/'+os.environ['SCRAM_ARCH']):
	os.system("scram project CMSSW "+rel)
    cmd = 'cd '+rel+'; eval `scram runtim -sh`; '
    newPack=False
    for item in packs:
	pack = item
	tag =""
	try:
	    pack,tag = item.split(" ",2)
	except:
	  pack = item
	if not os.path.exists(rel+'/src/'+pack):
	    os.system(cmd+' addpkg -z '+item)
	    newPack=True
    if newPack: os.system('cd '+rel+'; scram build -j 4 -k')
    return

os.environ['SCRAM_ARCH']=sys.argv[1]
rel = sys.argv[2]

xLock = Lock(rel+'.lock')
xLock.getLock (10,1000)
try:    createDev(rel,sys.argv[3:])
except: pass
