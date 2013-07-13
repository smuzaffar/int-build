#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Andreas Pfeiffer on 2008-08-05.
Copyright (c) 2008 CERN. All rights reserved.
"""

import sys, os, re, time
import getopt

# ================================================================================

class ErrorInfo(object):
	"""keeps track of information for errors"""
	def __init__(self, errType, msg):
		super(ErrorInfo, self).__init__()
		self.errType = errType
		self.errMsg  = msg

# ================================================================================

class PackageInfo(object):
	"""keeps track of information for each package"""
	def __init__(self, subsys, pkg):
		super(PackageInfo, self).__init__()

		self.subsys  = subsys
		self.pkg     = pkg
		self.errInfo = []
		self.errSummary = {}
		
	def addErrInfo(self, errInfo):
		"""docstring for addErr"""
		self.errInfo.append( errInfo )
		if errInfo.errType not in self.errSummary.keys():
			self.errSummary[errInfo.errType] = 1
		else:
			self.errSummary[errInfo.errType] += 1
			
	def name(self):
		"""docstring for name"""
		return self.subsys+'/'+self.pkg
		
# ================================================================================

class LogFileAnalyzer(object):
	"""docstring for LogFileAnalyzer"""
	def __init__(self, topDirIn='.', verbose = -1):
		super(LogFileAnalyzer, self).__init__()
		self.topDir = os.path.abspath( topDirIn )
		self.verbose = verbose
		
		self.nErrorInfo  = {}
		self.nFailedPkgs = []
		self.packageList = []
		self.pkgOK       = []
		self.pkgErr      = []
				
		self.errorKeys = ['dictError',
		                  'compError',
		                  'linkError',
						  'pythonError',
		                  'dwnlError',
		                  'miscError',
						 ]

		# get the lists separately for "priority" treatment ...
		self.errMap = {}
		for key in self.errorKeys:
			self.errMap[key] = []

	def  getDevelAdmins(self):
		"""
		get list of admins and developers from .admin/developers file in each package
		needed for sending out e-mails
		"""
		pass
		
	def analyze(self):
		"""loop over all packages and analyze the log files"""

		os.chdir(self.topDir)
		
		import glob
		start = time.time()
		packageList = glob.glob('*/*/build.log')

		if self.verbose > 0: print "going to analyze ", len(packageList), 'files.'

		for logFile in packageList:
			self.analyzeFile(logFile)

		pkgDone = []
		for pkg in self.packageList:
			if pkg.errInfo:
				self.pkgErr.append(pkg)
				for key in self.errorKeys:
					if key in pkg.errSummary.keys() and pkg not in pkgDone: 
						self.errMap[key].append(pkg)
						pkgDone.append(pkg)
			else:	
				self.pkgOK.append(pkg)

		stop = time.time()
		self.anaTime = stop-start
		pass

	def report(self):
		"""show collected info"""
		
		print 'analyzed ', len(self.packageList), 'log files in', str(self.anaTime), 'sec.'
		totErr = 0
		for key, val in self.nErrorInfo.items():
			totErr += int(val)
			
		print 'found ', totErr, ' errors in total, by type:'
		for key, val in self.nErrorInfo.items():
			print '\t', key, ' : ', val
		
		print 'found ', len(self.pkgOK),  'packages without errors.'
		print 'found ', len(self.pkgErr), 'packages with errors'
#		for pkg in pkgErr:
#			print '\t',pkg.name(), ' : ',
#			for key in ['dictError', 'compError', 'linkError']:
#				if key in pkg.errSummary.keys():
#					print key, pkg.errSummary[key],
#				else:
#					print key, ' N/A ',
#			print ''

## for debugging
#			for err in pkg.errInfo:
#				if err.errType == 'miscError':
#					print '\t\t', err.errMsg
		
		start = time.time()
		self.makeHTMLSummaryPage()
		for key in self.errorKeys:
			pkgList = self.errMap[key]
			pkgList.sort()
#			print 'Error type :', key
#			print [x.name() for x in pkgList]
			for pkg in pkgList:
				self.makeHTMLLogFile(pkg)
		stop = time.time()
		print "creating html pages took ", str(stop-start), 'sec.'
		
	def makeHTMLSummaryPage(self):

		keyList = self.errorKeys
		
		htmlDir = '../html/'
		if not os.path.exists(htmlDir):
			os.makedirs(htmlDir)

		htmlFileName = htmlDir + "index.html"
		htmlFile = open (htmlFileName, 'w')
		htmlFile.write("<html>\n")
		htmlFile.write("<head>\n")
		htmlFile.write("<title>Summary for builds</title>")
		htmlFile.write("</head>\n")
		htmlFile.write("<body>\n")
		htmlFile.write("<h2>Summary for builds</h2>")

		red     = '#ff0000'
		orange  = '#ff8100'
		green   = '#00930d'
		brown   = '#996632'
		magenta = '#ff28ff'
		black   = '#000000'
		white   = '#ffffff'

		bgcolor = {'dictError'   : red,
		 		   'compError'   : orange,
	 			   'linkError'   : brown,
 				   'pythonError' : magenta,
				   'dwnlError'   : white,
				   'miscError'   : white,	
		 }

		htmlFile.write('analyzed '+ str(len(self.packageList)) + ' log files in ' + str(self.anaTime) +' sec.\n')
		totErr = 0
		for key, val in self.nErrorInfo.items():
			totErr += int(val)
		
		htmlFile.write('<h3> found '+ str(totErr)+ ' errors in total, by type: </h3>\n')
		htmlFile.write('<table border="1" cellpadding="10">')
		for key in keyList:
			val = 0
			try:
				val = self.nErrorInfo[key]
			except KeyError:
				pass
			htmlFile.write('<tr bgcolor="'+bgcolor[key]+'"> <td>'+ key + ' </td><td> ' + str(val) + '</td></tr>\n')
		htmlFile.write('<table>')
		
		htmlFile.write('<table border="1">\n')
		htmlFile.write(" <tr>")
		htmlFile.write("<th>")
		htmlFile.write('subsystem/package')
		htmlFile.write("</th>")	
		for key in keyList:
			htmlFile.write("<th>")
			htmlFile.write(key)
			htmlFile.write("</th>")	
		htmlFile.write(" </tr> \n")
		
		topLogString = 'https://macms01.cern.ch/cgi-bin/ap/showLogFile.py/CMSSW_2_1_0/osx105_ia32_gcc401/html/'

		for key in keyList:
			pkgList = self.errMap[key]
			pkgList.sort()
            
			for pkg in pkgList:
				color = green
				for cKey in self.errorKeys :
					if color == green and cKey in pkg.errSummary.keys(): color = bgcolor[cKey]
				htmlFile.write(' <tr bgcolor="'+color+'">')
				htmlFile.write('<td>')
				link = ' <a href="'+topLogString+pkg.name()+'/log.html">'+pkg.name()+'</a> '
				htmlFile.write(link)
				htmlFile.write("</td>")	
				for pKey in keyList:
					htmlFile.write("<td>")
					if pKey in pkg.errSummary.keys():
						htmlFile.write( str(pkg.errSummary[pKey]) )
					else:
						htmlFile.write(' - ')
					htmlFile.write("</td>")	

				htmlFile.write("</tr>\n")	

		pkgList = self.pkgOK
		pkgList.sort()
        
		for pkg in pkgList:
			color = green
			htmlFile.write(' <tr bgcolor="'+color+'">')
			htmlFile.write('<td>')
			link = ' <a href="'+topLogString+pkg.name()+'/log.html">'+pkg.name()+'</a> '
			htmlFile.write(link)
			htmlFile.write("</td>")	
			for pKey in self.errorKeys:
				htmlFile.write("<td>")
				htmlFile.write(' - ')
				htmlFile.write("</td>")	
			htmlFile.write("</tr>\n")	


		htmlFile.write("</table>\n")	
		htmlFile.write("</body>\n")	
		htmlFile.write("</html>\n")		

		htmlFile.close()
		
	def makeHTMLLogFile(self, pkg):
		"""docstring for makeHTMLFile"""

		htmlDir = '../html/'+pkg.name()+'/'
		if not os.path.exists(htmlDir):
			os.makedirs(htmlDir)
		htmlFileName = htmlDir +'log.html'	

		logFileName = pkg.name()+'/build.log'
		logFile = open(logFileName, 'r')
		htmlFile = open (htmlFileName, 'w')
		htmlFile.write("<html>\n")
		htmlFile.write("<head>\n")
		htmlFile.write("<title>Log File for "+pkg.name()+"</title>")
		htmlFile.write("</head>\n")
		htmlFile.write("<body>\n")
		htmlFile.write("<h2>Log File for "+pkg.name()+"</h2>\n")
		htmlFile.write("<pre>\n")
		for line in logFile.readlines():
			htmlFile.write(line)
		htmlFile.write("</pre>\n")	
		htmlFile.write("</body>\n")	
		htmlFile.write("</html>\n")		
		htmlFile.close()
		
	def analyzeFile(self, fileNameIn):
		"""read in file and check for errors"""
		subsys, pkg, logFile = fileNameIn.split('/')
		
		if self.verbose > 5 : print "analyzing file : ", fileNameIn
		
		fileIn = open(fileNameIn, 'r')
		lines = fileIn.xreadlines()
		shLib = 'dylib'
		errorInf ={ 
			str('/usr/bin/ld: cannot find -l(.*?)$') : ['linkError', 'missing library "%s"'],
	        str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/src/'+subsys+pkg+'/classes_rflx\.cpp')  : ['dictError', 'for package dictionary'],
	        str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/src/'+subsys+pkg+'/.*?\.'+shLib)        : ['linkError', 'for package library'],
	        str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/src/'+subsys+pkg+'/.*?\.o')             : ['compError', 'for package library'],
	        str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/bin/(.*?)/.*?\.o')                      : ['compError', 'for executable %s'],
	        str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/bin/(.*?)/\1')                          : ['linkError', 'for executable %s'],
		    str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/bin/(.*?)/lib\1\.'+shLib)               : ['linkError', 'for shared library %s in bin'],
		    str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/test/stubs/lib(.*?)\.'+shLib)           : ['linkError', 'for shared library %s in test/stubs'],
		    str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/test/(.*?)/.*?\.'+shLib)                : ['linkError', 'for shared library %s in test'],
		    str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/test/stubs/.*?\.o')                     : ['compError', 'for library in test/stubs'],
		    str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/test/(.*?)/.*?\.o')                     : ['compError', 'for executable %s in test'],
		    str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/test/(.*?)\.'+shLib)                    : ['linkError', 'for shared library %s in test'],
		    str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/test/(.*?)\.o')                         : ['compError', 'for executable %s in test'],
		    str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/test/(.*?)/\1')                         : ['linkError', 'for executable %s in test'],
		    str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/plugins/(.*?)/.*?\.o')                  : ['compError', 'for plugin %s in plugins'],
		    str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/plugins/(.*?)/lib.*?\.'+shLib)          : ['linkError', 'for plugin library %s in plugins'],
			# somehow the \1 replacement seems to not be working ... :(
		    # str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/plugins/(.*?)/lib\1\.'+shLib)          : ['linkError', 'for plugin library %s in plugins'],
			str('^ImportError: .*')                                                                 : ['pythonError', 'importing another module'],
			str('^SyntaxError: .*')                                                                 : ['pythonError', 'syntax error in module'],
			str('^NameError: .*')                                                                   : ['pythonError', 'name error in module'],
		    str('^gmake: \*\*\* .*?/src/'+subsys+'/'+pkg+'/test/data/download\.url')               : ['dwnlError', 'for file in data/download.url in test'],
		}	

		miscErrRe = re.compile('^gmake: \*\*\* (.*)$')

		errors = {}
		for err, val in errorInf.items():
			# print "err = '"+err+"'"
			errors[re.compile(err)] = val
			
		pkgInfo = PackageInfo(subsys, pkg)
		errFound = False
		for line in lines:
			for errRe, info in errors.items():
				errMatch = errRe.match(line)
				if errMatch:
					errFound = True
					errTyp, msg = info
					if '%s' in msg :
						msg = info[1] % errMatch.groups(1)
					if errTyp in self.nErrorInfo.keys():
						self.nErrorInfo[errTyp] += 1
					else:
						self.nErrorInfo[errTyp] = 1	
					pkgInfo.addErrInfo( ErrorInfo(errTyp, msg) )
					break;
			if not errFound :
				miscErrMatch = miscErrRe.match(line)
				if miscErrMatch:
					errTyp = 'miscError'
					msg = 'Unknown error found: %s' % miscErrMatch.groups(1)
					if errTyp in self.nErrorInfo.keys():
						self.nErrorInfo[errTyp] += 1
					else:
						self.nErrorInfo[errTyp] = 1	
					pkgInfo.addErrInfo( ErrorInfo(errTyp, msg) )
				
		fileIn.close()

		self.packageList.append( pkgInfo )

		return
	
# ================================================================================

help_message = '''
The help message goes here.
'''

class Usage(Exception):
	def __init__(self, msg):
		self.msg = msg


def main(argv=None):
	logDir = '.'
	verbose = -1
	if argv is None:
		argv = sys.argv
	try:
		try:
			opts, args = getopt.getopt(argv[1:], "hv:l:", ["help", "verbose=", "logDir="])
		except getopt.error, msg:
			raise Usage(msg)
	
		# option processing
		for option, value in opts:
			if option in ("-v", '--verbose'):
				verbose = int(value)
			if option in ("-h", "--help"):
				raise Usage(help_message)
			if option in ("-l", "--logDir"):
				logDir = value
	
	except Usage, err:
		print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
		print >> sys.stderr, "\t for help use --help"
		return 2

	lfa = LogFileAnalyzer(logDir, verbose)
	lfa.analyze()
	lfa.report()
	
if __name__ == "__main__":
	sys.exit(main())
