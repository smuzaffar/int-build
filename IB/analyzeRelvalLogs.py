#!/usr/bin/env python

import os, sys, re, time

class LogAnalyzer(object):
    def __init__(self, outFileIn=None):

        self.outFile=sys.stdout
        if outFileIn:
            print "Summary file:", outFileIn
            self.outFile=open(outFileIn, 'w')

        self.results = { 'PASS' : [],
                         'FAIL' : [] }
        self.errMap = {}
        
        return

    def __del__(self):
        self.outFile.close()
        return

    def analyzeRelValLog(self, logFile, verbose=False):

        self.outFile.write( '\n--------------------------------------------------------------------------------\n'+'\n')
        self.outFile.write( "going to check " + logFile + '\n' )

        lf = open(logFile, 'r')
        lines = lf.readlines()
        lf.close()

        errRe   = re.compile('^%MSG-[es]')
        endRe   = re.compile('^%MSG$')

        index = -1
        err = None
        errID = 0
        OK = True
        for line in lines:
            index += 1
            if line.find("cms::Exception") == 0:
                OK = False
                self.outFile.write( "--->\n" )
                for i in range(0,10):
                    if index+i < len(lines):
                        self.outFile.write( '  '+lines[index+i])
            errMatch = errRe.match(line)
            endMatch = endRe.match(line)
        
            if errMatch:
                err = line
                errID += 1
                OK = False
            if err :
                if self.errMap.has_key(errID) :
                    self.errMap[errID].append( line )
                else:
                    self.errMap[errID] = [err]
            if endMatch:
                err = None

        for e,msg in self.errMap.items():
            self.outFile.write( "".join(msg) )

        statMsg = '\nchecked: ' + logFile + ': '
        if OK :
            self.results['PASS'].append(logFile[:-4])
            statMsg += ' PASSED '
        else:
            self.results['FAIL'].append(logFile[:-4])
            statMsg += ' FAILED '
        self.outFile.write(statMsg + '\n')

        return

    def analyzeAll(self, verbose=False):

        # assumes we're running in the dir where the log files are

        startDir = os.getcwd()
        print "LogAnalyzer::analyzeAll> going to analyze files in ", startDir
        self.outFile.write( "\nLogAnalyzer::analyzeAll> going to analyze files in "+ startDir +'\n')
        
        dirList = os.listdir('.')
        for entry in dirList:
            if entry[-8:] != ".cfg.log" : continue
            self.analyzeRelValLog(entry, verbose)

        self.outFile.write('\n'+'-'*80+'\n')
        if len(self.errMap.keys()) > 0 :

            # try to "filter out" the date/time stamp ...
            #msgRe = re.compile('(.*)\s\d\d?-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d\d\d\d\s*\d\d?:\d\d:\d\d\s*CET\s(.*)')
            #msgMatch = msgRe.match(err)
            #errorID = msgMatch.group(0)+msgMatch.group(1)

            msgSeen = []
            self.outFile.write('Packages failed with the following errors: \n')
            for e,msg in self.errMap.items():
                fullMsg = "".join(msg)
                if fullMsg[fullMsg.find('Run: '):] in msgSeen : continue
                self.outFile.write( "".join(msg) )
                msgSeen.append(fullMsg[fullMsg.find('Run: '):] )


        for stat in ['FAIL', 'PASS'] :
            self.outFile.write( '\n'+str(len(self.results[stat])) + " packages "+stat+"ED :\n" )
            for pkg in self.results[stat]:
                self.outFile.write( stat + ' ' + pkg + '\n' )

        os.chdir(startDir)

        return


# ================================================================================

def usage():
    print "usage: ", os.path.basename(sys.argv[0])," [--logFile <logFileName> ] [--verbose] [--outFile <outFile>]"
    return

if __name__ == "__main__" :
    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'hl:o:v', 
                                   ['help','logFile=','outFile=','verbose'])
    except getopt.GetoptError:
        usage()
        sys.exit(-2)

    logFile  = None
    verb     = False
    of       = None
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
            
        if o in ('-l','--logFile',):
            logFile = a

        if o in ('-o','--outFile',):
            of = a

        if o in ('-v','--verbose',):
            verb = True


    print 'of ', of
    la = LogAnalyzer(of)
    if logFile:
        la.analyzeRelValLog(logFile, verb)
    else:
        la.analyzeAll(verbose=verb)
    
    
