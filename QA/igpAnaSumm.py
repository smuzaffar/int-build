#!/usr/bin/env python

import os, sys, re

class IgProfAnalyzeSummary(object):
    
    def __init__(self):
        
        self.summary = {}
        
        self.samples  = []
        self.steps    = []
        self.pileups  = []
        self.releases = []
		
        self.midEvt = { 'GEN,FASTSIM' : '101',
                        'GEN,SIM,DIGI,L1,DIGI2RAW' : '1',
                        'RAW2DIGI,RECO' : '101',
                        'HLT' : '101'
                        }
        self.lastEvt = { 'GEN,FASTSIM' : '201',
                         'GEN,SIM,DIGI,L1,DIGI2RAW' : '51',
                         'RAW2DIGI,RECO' : '201',
                         'HLT' : '201'
                         }
        
        self.columns = ['PERF_TICKS @ EoJ', 'MEM_TOTAL @ EoJ', 'MEM_LIVE @ mid', 'MEM_LIVE @ EoJ']
    
    def getSummary(self, pathIn=None):
        
        path = '/afs/cern.ch/cms/sdt/web/qa/igprof/'
        if pathIn: path = pathIn
        
        cmd = 'echo "select filename, cumCounts, cumCalls from reports;"'
        cmd += ' | sqlite3 -separator "|" ./igprof-index.db '
        results = os.popen(cmd).readlines()
        
        if 'SQL error ' in "".join(results):
            print results
            return
        
        sampleRe = re.compile('^(.*?)___(.*?)___(.*?)___(.*?)___(.*?)___(.*?)___(.*)$')
        
        for line in results:
            if line.strip() == '' : continue
            words = line.strip().split('|')
            dot, data, arch, cycle, rel, fileName = words[0].split('/')

            if 'CMSSW_3_4_' in rel: continue
            if 'CMSSW_3_5_' in rel: continue
            
            if 'sql3' in fileName :
                
                if '_2009-' in rel : continue
                if '_diff_' in fileName: continue
                if '_merged.sql3' in fileName : continue
                
                if rel not in self.releases:
    				self.releases.append(rel)

                sampleMatch = sampleRe.match(fileName)
                if not sampleMatch:
                    print "ignoring irregular file name", fileName
                    continue
                
                sample, step, pileup, cond, evtcontent, what, evtnum  = sampleMatch.groups()
                
                if "MEM_MAX" in what: continue
				
                if "MEM_TOTAL"  in what and '_EndOfJob.sql3' not in evtnum : continue
                if "PERF_TICKS" in what and '_EndOfJob.sql3' not in evtnum : continue
				
                # print arch, rel, fileName, words[1:]
                
                candle = "_".join([sample, step, pileup, what])
                
                if ( not(
                     (self.midEvt[step]+'.sql'  in evtnum) or
                     (self.lastEvt[step]+'_EndOfJob.sql' in evtnum) ) ) : continue

                if "MEM_LIVE" in what :
                    if self.lastEvt[step]+'_EndOfJob.sql3' == evtnum: what = what +' @ EoJ'
                    elif self.midEvt[step]+'.sql3' == evtnum:         what = what +' @ mid'
                else:
                    what = what +' @ EoJ'
                    
                if sample not in self.samples:
                    self.samples.append(sample)
                if step not in self.steps:
                    self.steps.append(step)
                if pileup not in self.pileups:
					self.pileups.append(pileup)
					
                info = [words[1], words[2], sample, step, pileup, cond, evtcontent, what, evtnum]
                id = sample+'_'+step+'_'+pileup
                
                if candle in self.summary.keys():
                    if rel in self.summary[candle].keys():
                        self.summary[candle][rel].append( info )
                    else:
                        self.summary[candle][rel] = [ info ]
                else:
                    self.summary[candle] = {}
                    self.summary[candle][rel] = [ info ]
    
    def showSummary(self):

        for sample in self.samples:
        	for step in self.steps:
        		for pileup in self.pileups:
        		    candleName = sample+'_'+step+'_'+pileup
        		    print "\ncandle : ", candleName, '  cumulative counts, cumulative calls'
        		    print ' '*29,
        		    for c in self.columns:
        		        print '   |   ', c,
        		    print
        		    for rel in self.releases:
        				print '   ',rel, 
        				for c in self.columns:
        					c1, c2 = c.split(' @ ')
        					try:
        					    infoList = self.summary[candleName+'_'+c1.strip()][rel]
        					    for items in infoList:
        						    cCounts, cCalls, sa, st, pu, cond, evtc, what, evtnum = items
        						    if what != c : continue
        						    print ' | ', cCounts, ',', cCalls,
        					except KeyError:
        					    print ' |        ? ,       ? ',  
        				print
        				
# 		for candle, v in self.summary.items():
# 			print "candle : ", candle
# 			for rel, infoList in v.items():
# 				print '   ', rel,
# 				for items in infoList:
# 					cCounts, cCalls, sample, step, pileup, cond, evtc, what, evtnum = items
# 					print cCounts, cCalls


    def showSummaryFOO(self):
        
        outTable = {}
        for c in self.columns:
            outTable[c] = {}
        
        for rel, v in self.summary.items():
            # print rel, len(v)
            for id, info in v.items():
                # print '  ', id, info[0][5]
                
                # for c in columns:
                #     print '      ', c,
                # print ''
                
                table = {}
                for items in info:
                    cCounts, cCalls, sample, step, pileup, cond, evtc, what, evtnum = items
                    where = "EoJ"
                    if evtnum in self.midEvt[step] : where = 'mid'
                    wnw = what+' @ '+where
                    table [wnw] = [cCounts, cCalls]
                    
                    # print '      ', evtnum, what, cCounts, cCalls
                    # print '      ', items
                
                row = ""
                for c in self.columns:
                    try:
                        row += ','.join(table[c]) + ' | '
                    except KeyError:
                        row += " not found  | "
                    
                    outTable[c][rel] = row
        
        print '-'*42
        for what, v in outTable.items():
            print " > ", what
            for rel, data in v.items():
                print '   ', rel, " : ", data

if __name__ == "__main__":
    
    ipas = IgProfAnalyzeSummary()
    path = '/afs/cern.ch/cms/sdt/web/qa/igprof-testbed/'
    ipas.getSummary(path)
    ipas.showSummary()
    
