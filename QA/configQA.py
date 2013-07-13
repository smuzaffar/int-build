
# -------------------------------------------------------------------------------- # helper function(s) 
def getDomain():
    # check and set up the site-specific stuff ...
    import socket
    fqdn = socket.getfqdn().split('.') # fully qualified domain name as a field
    domain = fqdn[-2]+'.'+fqdn[-1]     # this should be something like 'cern.ch' or 'fnal.gov'
    return domain

# --------------------------------------------------------------------------------
#FORMAT: { 'site' : { 'testBoxes' : { 'cycle' : [ 'machine' | ('machine',<available CPU>), 'machine' | ('machine',<available CPU>)]}}}

siteInfoQA = { 'cern.ch'  : { 'testBoxes' :
                              { 
				#'4.4' : ['lxbuild164'], # 'lxbuild047'
				#'6.0' : ['lxbuild165'],
				#'5.3' : ['vocms108', ('lxbuild118' , 4.5)],
				#'5.2' : ['vocms113', ('vocms112', 4.5)],
				#'6.1' : ['lxbuild164'],
                              },
                            },
               'testing'  : { 'testBoxes' :
                              {
                                '3.6' : ['lxbuild144'],
                              },
                            }
             }
