

echo "USER : $USER "
echo "HOST : $HOST "

# set | grep CMSSW

eval `scramv1 run -sh`

echo "USER : $USER "
echo "HOST : $HOST "

# set | grep CMSSW

export HOST=`hostname`

#Avoid dumping TB of logfiles when igprof prompts for Abort:
export QUIET_ASSERT="sa"


# export PERFSUITE_OPTIONS=' --mail "" --no_tarball '
# export PERFSUITE_OPTIONS=''
export PERFSUITE_OPTIONS=' --mail gbenelli '

export COND_MC=MC_3XY_V21
export COND_SU=START3X_V21

# second part of the new perfsuite for IBs - to be run on another machine 

# export PILEUP_INPUT_FILE="/store/relval/CMSSW_3_2_0/RelValMinBias/GEN-SIM-DIGI-RAW-HLTDEBUG/MC_31X_V3-v1/0004/BA4BF096-FA74-DE11-8C04-001D09F25460.root"

export PILEUP_INPUT_FILE="/store/relval/CMSSW_3_3_0_pre3/RelValMinBias/GEN-SIM-DIGI-RAW-HLTDEBUG/MC_31X_V8-v1/0015/EC95D731-779F-DE11-A1BA-000423D9939C.root"

# Move on lxbuild142 in /build/gbenelli/CMSSW_3_1_0_pre6_PerfSuiteTests/work/V01-05-02-Test/:
HERE=`pwd`
#Make local directory to store RAW reference root files:
mkdir /build/RAWReference
#Make local directory writeable by all...
chmod 777 /build/RAWReference
#Copy the wanted RAW reference root files from castor:
rfcp /castor/cern.ch/user/g/gbenelli/RAWReference/MinBias_RAW_320_IDEAL.root /build/RAWReference/.
rfcp /castor/cern.ch/user/g/gbenelli/RAWReference/MinBias_RAW_320_STARTUP.root /build/RAWReference/.
rfcp /castor/cern.ch/user/g/gbenelli/RAWReference/TTbar_RAW_320_IDEAL.root /build/RAWReference/.
rfcp /castor/cern.ch/user/g/gbenelli/RAWReference/TTbar_RAW_320_STARTUP.root /build/RAWReference/.
rfcp /castor/cern.ch/user/g/gbenelli/RAWReference/TTbar_Tauola_PileUp_RAW_320_STARTUP.root /build/RAWReference/.
cd $HERE
mkdir RAW2DIGI-RECO
cd RAW2DIGI-RECO
mkdir cpu0
mkdir cpu1
mkdir cpu2
mkdir cpu3
mkdir cpu4
mkdir cpu5
mkdir cpu6
#cpu7 used by Filippo
cd cpu0
#For pileup tests we will use a PILEUP input RAW file!
#Decrease PU events by factor of 2 since they take longer
#Note we need to use STARTUP conditions in PU since the RelVal sample is only run in STARTUP conditions
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -t 500 --RunTimeSizePU TTbar --step RAW2DIGI-RECO --PUInputFile /build/RAWReference/TTbar_Tauola_PileUp_RAW_320_STARTUP.root  --cmsdriver "--eventcontent RECOSIM --conditions FrontierConditions_GlobalTag,${COND_SU}::All" --cores 0 --cpu 0 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu1
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -t 6000 --RunTimeSize MinBias --step RAW2DIGI-RECO --filein /build/RAWReference/MinBias_RAW_320_IDEAL.root --cmsdriver "--eventcontent RECOSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 1 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu2
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -i 201 --RunIgProf TTbar --step RAW2DIGI-RECO --filein /build/RAWReference/TTbar_RAW_320_IDEAL.root --cmsdriver "--eventcontent RECOSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 2 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu3
#For pileup tests we will use a PILEUP input RAW file!
#Decrease PU events by factor of 2 since they take longer
#Note we need to use STARTUP conditions in PU since the RelVal sample is only run in STARTUP conditions
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -i 201 --RunIgProfPU TTbar --step RAW2DIGI-RECO --PUInputFile /build/RAWReference/TTbar_Tauola_PileUp_RAW_320_STARTUP.root   --cmsdriver "--eventcontent RECOSIM --conditions FrontierConditions_GlobalTag,${COND_SU}::All" --cores 0 --cpu 3 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu4
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -m 10 --RunMemcheck TTbar --step RAW2DIGI-RECO --filein /build/RAWReference/TTbar_RAW_320_IDEAL.root --cmsdriver "--eventcontent RECOSIM --conditions FrontierConditions_GlobalTag,${COND_MC}::All" --cores 0 --cpu 4 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu5
#For pileup tests we will use a PILEUP input RAW file!
#Decrease PU events by factor of 2 since they take longer
#Note we need to use STARTUP conditions in PU since the RelVal sample is only run in STARTUP conditions
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -m 5 --RunMemcheckPU TTbar --step RAW2DIGI-RECO --PUInputFile /build/RAWReference/TTbar_Tauola_PileUp_RAW_320_STARTUP.root  --cmsdriver "--eventcontent RECOSIM --conditions FrontierConditions_GlobalTag,${COND_SU}::All" --cores 0 --cpu 5 > cmsPerfSuite.log 2>&1 &
mkdir results

# wait until all jobs from above have finished, then publish the results
wait

PREP="export PERF_CASTOR_URL=/castor/cern.ch/cms/store/relval/performance/;export PERFDB_cmssw_version=$CMSSW_VERSION;export PERFDB_TARFILE=UNAVAILABLE_IBTEST;export PERFDB_CASTOR_FILE_URL=${PERF_CASTOR_URL}${PERFDB_TARFILE};"

cd ../cpu0 ; cmsPerfPublish.py results;  ${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu1 ; cmsPerfPublish.py results;  ${PREP}; cmsPerfSuiteHarvest.py
###GB for now harvest only TimeSize tests (later will add igprof):
cd ../cpu2 ; cmsPerfPublish.py results;  ###${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu3 ; cmsPerfPublish.py results;  ###${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu4 ; cmsPerfPublish.py results;  ###${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu5 ; cmsPerfPublish.py results;  ###${PREP}; cmsPerfSuiteHarvest.py
cd ..
scp cpu*/PerfSuiteDBData/*.xml  cmsperfvmdev.cern.ch://data/projects/conf/PerfSuiteDB/xml_dropbox/.

cd $HERE
#HLT:
mkdir HLT
cd HLT
mkdir cpu0
mkdir cpu1
mkdir cpu2
mkdir cpu3
mkdir cpu4
mkdir cpu5
mkdir cpu6
#cpu7 used by Filippo
#For now running HLT with STARTUP CONDITIONS
cd cpu0
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -t 1000 --RunTimeSize TTbar --step HLT  --filein /build/RAWReference/TTbar_RAW_320_STARTUP.root --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_SU}::All --processName HLTFROMRAW" --cores 0 --cpu 0 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu1
#For pileup we will use a PILEUP input RAW file!
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -t 1000 --RunTimeSizePU TTbar --step HLT --PUInputFile /build/RAWReference/TTbar_Tauola_PileUp_RAW_320_STARTUP.root --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_SU}::All --processName HLTFROMRAW" --cores 0 --cpu 1 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu2
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -t 6000 --RunTimeSize MinBias --step HLT --filein /build/RAWReference/MinBias_RAW_320_STARTUP.root --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_SU}::All --processName HLTFROMRAW" --cores 0 --cpu 2 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu3
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -i 201 --RunIgProf TTbar --step HLT --filein /build/RAWReference/TTbar_RAW_320_STARTUP.root --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_SU}::All --processName HLTFROMRAW" --cores 0 --cpu 3 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu4
#For pileup tests we will use a PILEUP input RAW file!
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -i 201 --RunIgProfPU TTbar --step HLT --PUInputFile /build/RAWReference/TTbar_Tauola_PileUp_RAW_320_STARTUP.root  --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_SU}::All --processName HLTFROMRAW" --cores 0 --cpu 4 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu5
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -m 20 --RunMemcheck TTbar --step HLT --filein /build/RAWReference/TTbar_RAW_320_STARTUP.root --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_SU}::All --processName HLTFROMRAW" --cores 0 --cpu 5 > cmsPerfSuite.log 2>&1 &
mkdir results

cd ../cpu6
#For pileup tests we will use a PILEUP input RAW file!
cmsPerfSuite.py  $PERFSUITE_OPTIONS  -m 20 --RunMemcheckPU TTbar --step HLT --PUInputFile /build/RAWReference/TTbar_Tauola_PileUp_RAW_320_STARTUP.root  --cmsdriver "--eventcontent RAWSIM --conditions FrontierConditions_GlobalTag,${COND_SU}::All --processName HLTFROMRAW" --cores 0 --cpu 6 > cmsPerfSuite.log 2>&1 &
mkdir results

# wait until all jobs from above have finished, then publish
wait

PREP="export PERF_CASTOR_URL=/castor/cern.ch/cms/store/relval/performance/;export PERFDB_cmssw_version=$CMSSW_VERSION;export PERFDB_TARFILE=UNAVAILABLE_IBTEST;export PERFDB_CASTOR_FILE_URL=${PERF_CASTOR_URL}${PERFDB_TARFILE};"

cd ../cpu0 ; cmsPerfPublish.py results; ${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu1 ; cmsPerfPublish.py results; ${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu2 ; cmsPerfPublish.py results; ${PREP}; cmsPerfSuiteHarvest.py
###GB for now harvest only TimeSize tests (later will add igprof): 
cd ../cpu3 ; cmsPerfPublish.py results; ###${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu4 ; cmsPerfPublish.py results; ###${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu5 ; cmsPerfPublish.py results; ###${PREP}; cmsPerfSuiteHarvest.py
cd ../cpu6 ; cmsPerfPublish.py results; ###${PREP}; cmsPerfSuiteHarvest.py
cd ..
scp cpu*/PerfSuiteDBData/*.xml  cmsperfvmdev.cern.ch://data/projects/conf/PerfSuiteDB/xml_dropbox/.


