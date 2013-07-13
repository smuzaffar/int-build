#!/usr/bin/env python

import os, sys

scriptPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
if scriptPath not in sys.path:
    sys.path.append(scriptPath)

from doCmd import doCmd

def prepare(dirIn=None, platIn=None, relIn=None):

    swDir = dirIn
    if not swDir:
        swDir = os.getcwd()

    plat = platIn
    if not platIn:
        plat = os.environ['SCRAM_ARCH']

    if not os.path.exists(plat):
        os.makedirs(plat)

    lnx32 = ""
    if ( ( plat[:9] == 'slc4_ia32' ) and
         ( os.uname()[-1] == 'x86_64') ):
        lnx32 = "linux32 "

#   following the wiki page at: https://twiki.cern.ch/twiki/bin/view/CMS/CMSSW_bootstrap

    cmd = "export VO_CMS_SW_DIR="+swDir+" "
    cmd += "; wget -O $VO_CMS_SW_DIR/bootstrap.sh http://cmsrep.cern.ch/cmssw/bootstrap-"+plat+".sh "
    cmd += "; chmod +x $VO_CMS_SW_DIR/bootstrap.sh"
    cmd += '; '+lnx32+' $VO_CMS_SW_DIR/bootstrap.sh setup -repository cms.eulisse -path $VO_CMS_SW_DIR '
    doCmd(cmd)

    shellUsed = os.environ['SHELL']
    shell = '-sh'
    if shellUsed in ['csh', 'tcsh']:
        shell = '-csh'

    aptDir = os.path.join( swDir ,plat,'external','apt' )
    aptVers = os.listdir(aptDir)[0]

    # for the time being ... 
    cmd = 'sed -i -e "s/cms.eulisse/cms/g" '+os.path.join(aptDir, aptVers, 'etc', 'sources.list')
    doCmd(cmd)
    
    print "found apt version:", aptVers
    
    if not relIn:
        print 'now please do:'
        print ' source '+ os.path.join(aptDir, aptVers, 'etc', 'profile.d','init.sh')
        print ' apt-get update'
        print ' apt-get install cms+cmssw+<release>'
    else:
        cmd = ' source '+ os.path.join(aptDir, aptVers, 'etc', 'profile.d','init.sh')
        cmd += '; apt-get update'
        cmd += '; apt-get install cms+cmssw+'+relIn
        doCmd(cmd)

    return


def usage():
    print "usage: ", os.path.basename(sys.argv[0])," [--swDir <swDir>] [--release <rel>]"
    return

if __name__ == "__main__" :
    import getopt
    options = sys.argv[1:]
    try:
        opts, args = getopt.getopt(options, 'h', 
                                   ['help','swDir=', 'platform', 'release='])
    except getopt.GetoptError:
        usage()
        sys.exit(-2)

    swDir = None
    rel   = None
    plat  = None
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit()
            
        if o in ('--swDir',):
            swDir = a

        if o in ('--platform',):
            plat = a

        if o in ('--release',):
            rel = a

    prepare(swDir, plat, rel)
