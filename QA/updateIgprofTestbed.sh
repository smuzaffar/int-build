#!/usr/bin/env bash

source /afs/cern.ch/cms/slc5_amd64_gcc434/external/python/2.6.4-cms14/etc/profile.d/init.sh

TBDIR=/afs/cern.ch/cms/sdt/web/qa/igprof-testbed

ARCH=slc5_amd64_gcc434

cd $TBDIR

# update the testbed ... 
(cd data/$ARCH; rsync -au ../../../igprof/data/$ARCH/. . 2>&1 | \
    grep -v -e 'data/slc5_amd64_gcc434/CMSSW_4_2_3" failed: Operation not permitted (1)' | \
    grep -v -e 'rsync error: some files could not be transferred (code 23)' 
)

mv igprof-index.db igprof-index.db.bkp
mv summary.log summary.log.bkp
./igprof-navigator-summary -o igprof-index.db ./data/slc5_amd64_gcc434 >summary.log 2>&1

~/public/IBTests/igpAnaSumm.py > navigator-summary.txt

cp navigator-summary.txt ..

