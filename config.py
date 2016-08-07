### debug configuration
DEBUG = True
VERBOSE_DEBUG = False

### simulation configuration
# MEDIAN_BITRATE_MODE = True
CHUNK_AWARE_MODE = True
PS_STYLE_BANDWIDTH = False
VALIDATION_MODE = False
TOTAL_CHUNKS  = 0
AVERAGE_BANDWIDTH_MODE = False
ESTIMATED_BANDWIDTH_MODE = True

### Operation mode ###
DATABRICKS_MODE = False
TRACE_MODE = True

### BB ABR configuration
conf = {'maxbuflen':120, 'r': 5, 'maxRPct':0.90, 'xLookahead':50}

### Player properties ###
MAX_BUFFLEN = 120
LOCK = 15


### ABR configuration ###
UTILITY_BITRATE_SELECTION = True 
BANDWIDTH_UTILITY = False
BUFFERLEN_UTILITY = False
BUFFERLEN_BBA1_UTILITY = False
BUFFERLEN_BBA2_UTILITY = False
WEIGHTED_BANDWIDTH = False

### DYNAMIC settings
DYNAMIC_BSM = False


### Simulation settings
SIMULATION_STEP = 50
