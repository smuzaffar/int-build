#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Andreas Pfeiffer on 2010-05-03.
Copyright (c) 2010 CERN. All rights reserved.
"""

import os, sys, glob, pickle

def getVgCmds(plat, build):
    """docstring for getVgCmds"""

    startDir = os.getcwd()

    # set up
    pmDirs = ['newPerf-1of2', 'newPerf-2of2']
    if '3_5_X' in build or '3_6_X' in build:
        pmDirs = ['perfNew-1', 'perfNew-2']

    baseDir = '/data/intBld/incoming'
    
    if ( not os.path.exists( os.path.join(baseDir, pmDirs[0], plat, build, pmDirs[0]) ) and
         not os.path.exists( os.path.join(baseDir, pmDirs[1], plat, build, pmDirs[1]) ) ) :
        print 'Error no info available for '+build+' on '+plat
        return

    # get the commands used 
    cmdMap = {}
    for pmDir in pmDirs:
        relPath = os.path.join(pmDir, plat, build, pmDir)
        try:
            os.chdir( os.path.join(baseDir, relPath) )
        except OSError:
            continue
    
        logFiles = glob.glob('*/cpu?/*/*.log') 
        for item in logFiles :
            pathName,fileName = os.path.split(item)
            vgCmd = "unknown"
            cmd = 'grep cmsDriver.py '+pathName+'/*log | cut -d" " -f3- '
            try:
                pipe = os.popen(cmd,'r')
                vgCmd = pipe.readlines()[0]
                pipe.close()
            except:
                pass
            # print 'checking '+cmd+ '<br />'
            # print '<b>vgCmd</b> = ' + str(vgCmd) + '<br /><br />'
            cmdMap[pathName] = vgCmd
    
    print 'in ', os.getcwd()
    vgCmdFile = open(baseDir+'/vgCmds-'+build+'-'+plat+'.pkl', 'w')
    pklr = pickle.Pickler(vgCmdFile)
    pklr.dump(cmdMap)
    vgCmdFile.close()
    
def main():

    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'h', 
                                   ['help','architecture=','platform=', 'release=', 'dryRun'])
    except getopt.GetoptError, msg:
        print msg
        usage()
        sys.exit(-2)

    plat = None
    rel = None
    dryRun = False
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()

        if o in ('--architecture','--platform'):
            plat = a

        if o in ('--release',):
            rel = a

        if o in ('--only',):
            only = a

    if not rel or not plat:
        print "No release or architecture specified !"
        sys.exit(0)

    getVgCmds(plat, rel)


if __name__ == '__main__':
	main()

