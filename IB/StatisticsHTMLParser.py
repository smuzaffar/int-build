#!/usr/bin/env python

import re
from HTMLParser import HTMLParser


class StatisticsHTMLParser(HTMLParser):

    isFirst = True
    isData = False
    n_successes = 0
    n_nulls = 0
    n_fails = 0

    def __init__(self):
            HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == 'li' and self.isFirst:
            self.isData = True

    def handle_endtag(self, tag):
        if tag == 'ul':
            self.isFirst = False #search only in the first list
    
    def handle_data(self, data):
        if self.isData:
            dataStr = str(data)
            match = re.match(r"(\w+):\s*[0-9.%]+\s*\((\d+)\)", dataStr)
            if match:
                if 'Success' == match.group(1):
                    self.n_successes = match.group(2)
                elif 'Null' == match.group(1):
                    self.n_nulls = match.group(2)
                elif 'Fail' == match.group(1):
                    self.n_fails = match.group(2)
            self.isData = False