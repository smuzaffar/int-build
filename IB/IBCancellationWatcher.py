#!/usr/bin/env python

import os, sys, re, time, tagCollectorAPI
from procTree import ProcessTree
# ================================================================================

def startIBCancellationWatcher(pid, request_id):
    print "IBCancellationWatcher started with pid %s and request_id %s" % (str(pid), str(request_id))
    procs = ProcessTree(user=None, detail=True, xinfo=None, show=False)
    while True:
        time.sleep(60)
        try:
            procs.updateSelected(None, None, pid)
            if (len(procs.selectedTree)==0):
                print "PID %s doesnt's exist anymore, exiting..." % str(pid) 
                break
            data = None
            try:
                data = tagCollectorAPI.getRequestData(request_id)
            except:
	    	pass
            if data['state'] == "Cancelled" or data['state'] == "Failed":
                print "Found status Cancelled or Failed for request %s" % str(request_id)
                proc2kill = ProcessTree(user=None, detail=True, xinfo=None, show=True)
                proc2kill.killSelected(None, None, pid)
                break
            procs.allProcesses(None)
        except:
            print "Error: An exception occured while checking cancelled status"
    return

# ================================================================================

def usage(code=0):
    print "usage: ", sys.argv[0], '--request <processid> [--user <login>] [--dryRun] [-h|--help]'
    sys.exit(code)

# ================================================================================

if __name__ == "__main__":
    import getopt
    options = sys.argv[1:]
    try: opts, args = getopt.getopt(options, 'h', ['help','dryRun','pid=', 'request_id='])
    except getopt.GetoptError: usage(-2)
    dryRun  = False
    pid = None
    request_id = None
    for o, a in opts:
        if o in ('-h', '--help'): usage(0)
        elif o == '--dryRun': dryRun = True
        elif o == '--pid' :   pid = a
        elif o == '--request_id' : request_id = a
    if not pid: usage(-2)
    startIBCancellationWatcher(pid,request_id)
