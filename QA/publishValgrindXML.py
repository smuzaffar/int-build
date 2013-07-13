#!/usr/bin/env python

import os, sys, glob, re
scriptPath = os.path.dirname(os.path.abspath(__file__))

def publishValgrindXML(rel, part, pubDirTop, pubHost, dryRun=False, arch='slc5_amd64_gcc434'):

    xmlFiles = glob.glob('newPerf-'+part+'/*/*/*/*valgrind.xml')
    xmlFiles += glob.glob('newPerf-'+part+'/*/cpu7/*valgrind.xml')
    
    print "pvgx> publishing to :", pubHost, pubDirTop
    print "pvgx> found         :", xmlFiles
    errMap = {}
    
    for xmlFile in xmlFiles:
        newFileName = xmlFile.replace('valgrind.xml', 'vlgd.xml')
        cmd = 'xsltproc --output '+newFileName+' '+scriptPath+'/filterOutValgrindLeakErrors.xsl '+xmlFile
        
        if dryRun:
            print 'dryRun for:',cmd
        else:
            print cmd
            ret = os.system(cmd)
            if ret != 0:
                print "ERROR when compacting valgrind output for ",xmlFile, newFileName, ret
                continue
            
        remFile = newFileName.replace('newPerf-'+part+'/','')
        remotePath, remoteFile = os.path.split(pubDirTop+'/'+remFile)

        cmd = 'ssh '+pubHost+' mkdir -p '+remotePath+';'
        cmd += 'scp -q '+newFileName + ' ' +pubHost+':'+remotePath
        if dryRun:
            print 'dryRun for:',cmd
        else:
            print cmd
            ret = os.system(cmd)
            if ret != 0:
                print "ERROR when copying valgrind output to " +pubHost+':'+pubDirTop+'/'+newFileName
                print "      command returned", ret

        cmd = "grep '<error>' "+newFileName+ " | wc -l "    
        p = os.popen(cmd, 'r')
        nerr = int(p.readlines()[0])
        if nerr == 0 :
            cmd = "grep '<state>RUNNING</state>' "+newFileName+ " | wc -l "    
            p = os.popen(cmd, 'r')
            nFoundRun = int(p.readlines()[0])
            cmd = "grep '<state>FINISHED</state>' "+newFileName+ " | wc -l "    
            p = os.popen(cmd, 'r')
            nFoundFin = int(p.readlines()[0])
            if nFoundRun > 0 and nFoundFin == 0 :
                nerr = -1

        print "---> found ", nerr, 'errors in ', newFileName
        errMap[newFileName] = nerr

    if xmlFiles:
        from pickle import Pickler
        vgPklFileName = 'valgrindSummary-'+part+'.pkl'
        summFile = open(vgPklFileName,'w')
        pklr = Pickler(summFile)
        pklr.dump([rel, arch])
        pklr.dump(errMap)
        summFile.close()

        remDir = pubHost+":"+pubDirTop
        cmd = 'scp -q '+vgPklFileName+' ' +remDir
        if dryRun:
            print 'dryRun for:',cmd
        else:
            print cmd
            ret = os.system(cmd)
            if ret != 0:
                print "ERROR when copying valgrind output to " +remDir

    logFiles = glob.glob('newPerf-'+part+'/perfNew-'+part+'.log')
    logFiles += glob.glob('newPerf-'+part+'/*/*/*/*.log')
    logFiles += glob.glob('newPerf-'+part+'/*/cpu7/*.log')
    for lf in logFiles:
        newFileName = lf.replace('newPerf-'+part+'/','')
        remotePath, remoteFile = os.path.split(pubDirTop+'/'+newFileName)

        cmd = 'ssh '+pubHost+' mkdir -p '+remotePath+';'
        cmd += 'scp -q '+ lf + ' ' +pubHost+':'+ remotePath
        if dryRun:
            print 'dryRun for:',cmd
        else:
            print cmd
            ret = os.system(cmd)
            if ret != 0:
                print "ERROR when copying logFile "+lf+" to " +pubHost+':'+pubDirTop+'/'+newFileName
