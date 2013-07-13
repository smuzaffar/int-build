
from Configuration.GlobalRuns.promptCollisionReco_FirstCollisions_RAW2DIGI_L1Reco_RECO_DQM_ALCA import *

process.maxEvents.input = 100

process.options = cms.untracked.PSet( Rethrow = cms.untracked.vstring('ProductNotFound') )

process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring(
    # '/store/data/BeamCommissioning09/MinimumBias/RAW/v1/000/122/314/BED7A8E6-62D8-DE11-BEF1-001D09F25456.root'
    # '/store/data/BeamCommissioning09/MinimumBias/RAW/v1/000/122/314/C28DBE30-62D8-DE11-B5B0-003048D2BE08.root'
    # '/store/data/BeamCommissioning09/MinimumBias/RAW/v1/000/123/151/3CE3F1C6-FADD-DE11-8AEA-001D09F251D1.root'
    '/store/data/BeamCommissioning09/Cosmics/RAW/v1/000/120/015/8ED3F312-F0CB-DE11-8821-001D09F2AF1E.root'
    )
)

