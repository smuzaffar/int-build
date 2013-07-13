#!/usr/bin/env python

import os, sys, re

def checkCommonLog(fileName):

    log = open(fileName, 'r')
    lines = log.readlines()
    log.close()

    startRe = re.compile('^Preparing to run (.*)')
    errRe   = re.compile('^%MSG-e')

    pkg = None
    err = None
    line1 = None
    errMap = {}
    for line in lines:
        startMatch = startRe.match(line)
        errMatch = errRe.match(line)

        if startMatch :
            pkg = startMatch.group(1)
#            print "--> pkgMatch : ", pkg

        if errMatch:
            err = line
#            print "--> errMatch : ", err

        if line1 :
            if errMap.has_key(pkg) :
                errMap[pkg].append( [err, line1, line] )
            else:
                errMap[pkg] = [[err, line1, line]]
#            print "--> errMatch : ", err, line1, line
            err = None
            line1 = None

        if not errMatch and err:
            line1 = line


    print "a total of ", len(errMap.keys()), "pacakges had errors:"
    for p,e in errMap.items():
        print "pkg ", pkg, len(e), 'errors:'
        for line in e:
            print " -- ", line[0], ' -- ', line[1], ' -- ', line[2]

# --------------------------------------------------------------------------------

def checkLog(fileName):

    log = open(fileName, 'r')
    lines = log.readlines()
    log.close()

    errRe   = re.compile('^%MSG-[es]')
    endRe   = re.compile('^%MSG$')

    pkg = fileName[:fileName.find('.')]
    err = None
    errID = 0
    errMap = {}
    for line in lines:
        errMatch = errRe.match(line)
        endMatch = endRe.match(line)
        
        if errMatch:
            err = line
            errID += 1
#            print "--> errMatch : ", err

        if err :
            if errMap.has_key(errID) :
                errMap[errID].append( line )
            else:
                errMap[errID] = [err]
#            print "--> errMatch : ", err, line1, line

        if endMatch:
            err = None


    print '\n','-'*80,'\n'
    print "package ", pkg, " had errors: \n"
    for e,msg in errMap.items():
        print "".join(msg)


if __name__ == "__main__":

    for item in sys.argv[1:]:
        checkLog(item)
