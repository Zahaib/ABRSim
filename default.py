#!/usr/bin/python

### Debug settings
DEBUG = False
VERBOSE_DEBUG = False

### Player settings
MAX_BUFLEN = 120
SWITCH_LOCK = 15
JOIN_BUFFSIZE = 1.25

### Stream settings
CHUNKSIZE = 5
CANDIDATES = [1002, 1434, 2738, 3585, 4661, 5885]
INIT_BR = CANDIDATES[0]

### Simulation settings
SIMULATION_STEP = 50
INIT_STREAM = 6
INIT_HB = 200
MID_HB = 500
CHUNK_AWARE_MODE = False
JOINTIME = 0

### Bitrate selection settings
UTILITY_ABR = True
BUFFER_ABR = False
RATE_ABR = False

### ABR specific settings
BUFFER_MARGIN = 0.25
BANDWIDTH_MARGIN = 1.0
LOWER_RESERVOIR = 5
UPPER_RESERVOIR = 0.9

### Bandwidth settings
AVERAGE_BANDWIDTH_MODE = False
ESTIMATED_BANDWIDTH_MODE = False

### Constants
MSEC_IN_SEC = 1000.0


