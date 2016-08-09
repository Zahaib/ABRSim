# ABRSim
## Introduction
ABRSim is a Discrete Event Simulator ([DES](https://en.wikipedia.org/wiki/Discrete_event_simulation)) of an online video player. It takes as input a throughput trace, a configuration of player such as maximum buffer length and the ABR algorithm. It currently allows to choose from three ABR algorithm: a pure throughput based ABR, a buffer based ABR and a hybrid ABR that uses both buffer and througput information to make bitrate decision.
`
## Usage 
  %core.py <inputfile> [OPTIONS]

Options
=======
 --version                          show program's version number and exit
 -h, --help                         show this help message and exit
 -d, --debug                        debugging output, prints state once every decision
 -v, --verbose                      verbose debugging output, prints state once every simulation step

Player config:
--------------
  -b INT, --max-buflen=INT          maximum playback buffer length in sec
  -l INT, --switch-lock=INT         duration of lock on switch up decision in sec
  -j FLOAT, --join-buffsize=FLOAT   bufferlength at jointime in sec

Stream config:
--------------
  -s INT, --chunksize=INT           size of chunk in sec
  -r INT, --init-bitrate=INT        initial bitrate

Simulation config:
------------------
  -I INT, --simstep=INT             simulation step size in msec
  -n INT, --init-stream-chunks=INT  duration of initial stream in number of chunks
  -x INT, --init-decision-freq=INT  duration of decision interval in initial stream in msec
  -y INT, --mid-decision-freq=INT   duration of decision interval in middle stream in msec
  -m, --use-chunk-map               enable simulation to use a chunkmap provided as a dictionary named "sizeDict"

ABR algo config:
----------------
  -A ABR, --abr=ABR                 choose ABR from 'utility', 'buffer' or 'rate', without quotes
  -B FLOAT, --bsm=FLOAT             bandwidth safety margin for utility ABR
  -W FLOAT, --bwsm=FLOAT            bandwidth safety margin for utility ABR
  -L INT, --lower-res=INT           lower reservoir for buffer based ABR
  -U FLOAT, --upper-res=FLOAT       upper reservoir for buffer based ABR as percentage of max_buflen
`
For bugs and suggestions, email: zakhtar@usc.edu
