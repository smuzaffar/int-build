
from Configuration.GlobalRuns.recoT0DQM_EvContent_38T_cfg import *
process.maxEvents.input = 100

process.options = cms.untracked.PSet( Rethrow = cms.untracked.vstring('ProductNotFound') )

# process.GlobalTag.connect = "frontier://FrontierProd/CMS_COND_21X_GLOBALTAG"
# process.GlobalTag.globaltag = 'CRZT210_V1::All'
