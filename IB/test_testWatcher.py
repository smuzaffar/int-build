#!/usr/bin/env python

import os, sys, time, threading

scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

from testWatcher import *

def doTest():

    # start a thread with the watcher, then start a "test"
    isDone = threading.Event()
    killer = TestKiller("cmsbuild", "python", isDone)
    killer.start()

    for i in range(10):
        print "in main",i, isDone.isSet()
        time.sleep(1)
    isDone.set()
    print "evt now set"
    time.sleep(3)

doTest()
