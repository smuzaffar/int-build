#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Andreas Pfeiffer on 2010-02-08.
Copyright (c) 2010 CERN. All rights reserved.
"""

import sys
import getopt


help_message = '''
The help message goes here.
'''

class RelProdReader(object):
	"""docstring for RelProdReader"""
	def __init__(self):
		super(RelProdReader, self).__init__()

		self.pkgMap  = {}

		self.libMap = {}
		self.binMap = {}
		self.tstMap = {}
		self.scrMap = {}
	
	def readProducts(self, fileName):
		"""docstring for readProducts"""
		
		rpFile = open(fileName, 'r')
		lines = rpFile.readlines()
		rpFile.close
		
		import re
		lineRe = re.compile('(?P<pkg>.*?):(?P<libs>[lp].*?)?\|(?P<bins>.*?)\|(?P<tests>.*?)\|(?P<scripts>.*?)$')
		
		for line in lines:

			lineMatch = lineRe.match(line)
			if not lineMatch: continue
						
			pkg = lineMatch.group('pkg')
			libs = lineMatch.group('libs')
			bins = lineMatch.group('bins')
			tsts = lineMatch.group('tests')
			scripts = lineMatch.group('scripts')

			if pkg in self.pkgMap.keys():
				print "ERROR: duplicate pkg found", pkg
			self.pkgMap[pkg] = (str(libs)+'|'+str(bins)+'|'+str(tsts)+'|'+str(scripts)).replace('None', '')
			
			if libs: 
				for x in libs.split(','): 
					self.libMap[x] = pkg
			if bins: 
				for x in bins.split(','): 
					self.binMap[x] = pkg
			if tsts: 
				for x in tsts.split(','): 
					self.tstMap[x] = pkg

			if scripts: 
				for x in scripts.split(','): 
					self.scrMap[x] = pkg
		
		print "found ", len(self.pkgMap.keys()), 'packages.'
		print "found ", len(self.libMap.keys()), 'libs and plugins, '
		print "found ", len(self.binMap.keys()), 'binary products, '
		print "found ", len(self.tstMap.keys()), 'tests, '
		print "found ", len(self.scrMap.keys()), 'scripts. '

	def showLib(self, lib):
		"""docstring for showLib"""
		print "lib ", lib, 'is from', self.libMap[lib]

	def showBin(self, bin):
		"""docstring for showLib"""
		print "bin ", bin, 'is from', self.binMap[bin]
        
	def showTest(self, tst):
		"""docstring for showLib"""
		print "test ", tst, 'is from', self.tstMap[tst]

	def showScript(self, tst):
		"""docstring for showLib"""
		print "script ", tst, 'is from', self.scrMap[tst]

	def findProduct(self, item):
		"""docstring for findProduct"""
		if item in self.libMap.keys() :
			return self.libMap[item]
		if item in self.binMap.keys() :
			return self.binMap[item]
		if item in self.tstMap.keys() :
			return self.tstMap[item]
		if item in self.scrMap.keys() :
			return self.scrMap[item]
		return None
		
class Usage(Exception):
	def __init__(self, msg):
		self.msg = msg


def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		try:
			opts, args = getopt.getopt(argv[1:], "hf:v", ["help", "relProdFile="])
		except getopt.error, msg:
			raise Usage(msg)
	
		# option processing
		rpFile = None
		for option, value in opts:
			if option == "-v":
				verbose = True
			if option in ("-h", "--help"):
				raise Usage(help_message)
			if option in ("-f", "--relProdFile"):
				rpFile = value
	
		rpr = RelProdReader()
		rpr.readProducts(rpFile)
		rpr.showTest('test_StorageFactory_t0Repack')
		
	except Usage, err:
		print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
		print >> sys.stderr, "\t for help use --help"
		return 2


if __name__ == "__main__":
	sys.exit(main())
