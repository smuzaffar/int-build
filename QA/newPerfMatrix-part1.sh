
echo "USER : $USER "
echo "HOST : $HOST "

# set | grep CMSSW

eval `scramv1 run -sh`

echo "USER : $USER "
echo "HOST : $HOST "

# set | grep CMSSW

export HOST=`hostname`

export QUIET_ASSERT="sa"

# export PERFSUITE_OPTIONS=' --mail "" --no_tarball '
# export PERFSUITE_OPTIONS=''
export PERFSUITE_OPTIONS=' --mail gbenelli '


export COND_MC=MC_3XY_V21
export COND_SU=START3X_V21

# first part of the new perfsuite for IBs - to be run on one machine 

# export PILEUP_INPUT_FILE="/store/relval/CMSSW_3_2_0/RelValMinBias/GEN-SIM-DIGI-RAW-HLTDEBUG/MC_31X_V3-v1/0004/BA4BF096-FA74-DE11-8C04-001D09F25460.root"

export PILEUP_INPUT_FILE="/store/relval/CMSSW_3_3_0_pre3/RelValMinBias/GEN-SIM-DIGI-RAW-HLTDEBUG/MC_31X_V8-v1/0015/EC95D731-779F-DE11-A1BA-000423D9939C.root"

mkdir GEN-DIGI2RAW
cd GEN-DIGI2RAW
mkdir cpu0
mkdir cpu1
mkdir cpu2
mkdir cpu3
mkdir cpu4
mkdir cpu5
mkdir cpu6
mkdir cpu7
cd cpu0
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -t 100 --RunTimeSize TTbar --step GEN-DIGI2RAW --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 0 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu1
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -t 100 --RunTimeSizePU TTbar --step GEN-DIGI2RAW --PUInputFile ${PILEUP_INPUT_FILE} --step GEN-DIGI2RAW --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 1 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu2
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -t 600 --RunTimeSize MinBias --step GEN-DIGI2RAW --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 2 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu3
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -i 51 --RunIgProf TTbar --step GEN-DIGI2RAW --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 3 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu4
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -i 51 --RunIgProfPU TTbar --step GEN-DIGI2RAW --PUInputFile ${PILEUP_INPUT_FILE} --step GEN-DIGI2RAW --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 4 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu5
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -m 1 --RunMemcheck TTbar --step GEN-DIGI2RAW --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 5 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu6
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -m 1 --RunMemcheckPU TTbar --step GEN-DIGI2RAW --PUInputFile ${PILEUP_INPUT_FILE} --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 6 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../..

HERE=`pwd`
#Make local directory to store RAW reference root files:
mkdir /build/RAWReference
chmod 777 /build/RAWReference
cd /build/RAWReference
#Copy the wanted RAW reference root files from castor:
rfcp /castor/cern.ch/user/g/gbenelli/RAWReference/MinBias_RAW_320_IDEAL.root /build/RAWReference/.
rfcp /castor/cern.ch/user/g/gbenelli/RAWReference/MinBias_RAW_320_STARTUP.root /build/RAWReference/.
rfcp /castor/cern.ch/user/g/gbenelli/RAWReference/TTbar_RAW_320_IDEAL.root /build/RAWReference/.
rfcp /castor/cern.ch/user/g/gbenelli/RAWReference/TTbar_RAW_320_STARTUP.root /build/RAWReference/.
rfcp /castor/cern.ch/user/g/gbenelli/RAWReference/TTbar_RAW_320_STARTUP.root /build/RAWReference/.
rfcp /castor/cern.ch/user/g/gbenelli/RAWReference/TTbar_Tauola_PileUp_RAW_320_STARTUP.root /build/RAWReference/.
cd $HERE
mkdir RAW2DIGI-RECO
cd RAW2DIGI-RECO
mkdir cpu7 #Will submit the rest of RECO stuff on the next machine (142)
cd cpu7
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -t 1000 --RunTimeSize TTbar --step RAW2DIGI-RECO --filein /build/RAWReference/TTbar_RAW_320_IDEAL.root --cmsdriver "--eventcontent RECOSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 7 > cmsPerfSuite.log 2>&1 &
mkdir results
cd ../..

wait

PREP="export PERF_CASTOR_URL=/castor/cern.ch/cms/store/relval/performance/;export PERFDB_cmssw_version=$CMSSW_VERSION;export PERFDB_TARFILE=UNAVAILABLE_IBTEST;export PERFDB_CASTOR_FILE_URL=${PERF_CASTOR_URL}${PERFDB_TARFILE};"

cd $HERE
cd GEN-DIGI2RAW
cd    cpu0 ; cmsPerfPublish.py results; ${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu1 ; cmsPerfPublish.py results; ${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu2 ; cmsPerfPublish.py results; ${PREP}; cmsPerfSuiteHarvest.py
###GB for now harvest only TimeSize tests (later will add IgProf)
cd ../cpu3 ; cmsPerfPublish.py results; ###${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu4 ; cmsPerfPublish.py results; ###${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu5 ; cmsPerfPublish.py results; ###${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu6 ; cmsPerfPublish.py results; ###${PREP}; cmsPerfSuiteHarvest.py
cd ..
scp cpu*/PerfSuiteDBData/*.xml  cmsperfvmdev.cern.ch://data/projects/conf/PerfSuiteDB/xml_dropbox/.

cd $HERE
cd RAW2DIGI-RECO/cpu7 ; cmsPerfPublish.py results; ${PREP}; cmsPerfSuiteHarvest.py
cd ..
scp cpu*/PerfSuiteDBData/*.xml  cmsperfvmdev.cern.ch://data/projects/conf/PerfSuiteDB/xml_dropbox/.


#FASTSIM:
cd $HERE

mkdir FASTSIM
cd    FASTSIM
mkdir cpu0
mkdir cpu1
mkdir cpu2
mkdir cpu3
mkdir cpu4
mkdir cpu5
mkdir cpu6
#cpu7 used by Filippo

cd cpu0
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -t 1000 --RunTimeSize TTbar --step GEN-FASTSIM --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 0 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu1
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -t 1000 --RunTimeSize TTbar --step GEN-FASTSIM  --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All --pileup=LowLumiPileUp" --cores 0 --cpu 1 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu2
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -t 6000 --RunTimeSize MinBias --step GEN-FASTSIM --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 2 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu3
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -i 201 --RunIgProf TTbar --step GEN-FASTSIM --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 3 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu4
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -i 201 --RunIgProf TTbar --step GEN-FASTSIM --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All --pileup=LowLumiPileUp" --cores 0 --cpu 4 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu5
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -m 20 --RunMemcheck TTbar --step GEN-FASTSIM --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 5 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu6
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -m 20 --RunMemcheck TTbar --step GEN-FASTSIM --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All --pileup=LowLumiPileUp" --cores 0 --cpu 6 > cmsPerfSuite.log 2>&1 &
mkdir results

wait 

PREP="export PERF_CASTOR_URL=/castor/cern.ch/cms/store/relval/performance/;export PERFDB_cmssw_version=$CMSSW_VERSION;export PERFDB_TARFILE=UNAVAILABLE_IBTEST;export PERFDB_CASTOR_FILE_URL=${PERF_CASTOR_URL}${PERFDB_TARFILE};"

cd ../cpu0 ; cmsPerfPublish.py results;  ${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu1 ; cmsPerfPublish.py results;  ${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu2 ; cmsPerfPublish.py results;  ${PREP}; cmsPerfSuiteHarvest.py
###GB for now harvest only TimeSize tests (later will add IgProf)
cd ../cpu3 ; cmsPerfPublish.py results; ### ${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu4 ; cmsPerfPublish.py results; ### ${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu5 ; cmsPerfPublish.py results; ### ${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu6 ; cmsPerfPublish.py results; ### ${PREP}; cmsPerfSuiteHarvest.py
cd ..
scp cpu*/PerfSuiteDBData/*.xml  cmsperfvmdev.cern.ch://data/projects/conf/PerfSuiteDB/xml_dropbox/.
