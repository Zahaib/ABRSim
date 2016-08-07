#!/usr/bin/python

import sys, os, math
import numpy as np
from userinput import parseinput
from sim import newsimulation
# from state import globalstate, chunkstate, bitratestate, bandwidthstate, bufferstate
import algorithms, helpers

# parse user input and defaults to get the config for this simulation
config = parseinput()

# create a new simulation based on the config
simulation = newsimulation(config)

if config.debug or config.verbose:
  simulation.printHeader()

while simulation.globalstate.clock < simulation.globalstate.traceSessiontime:
  simulation.bandwidthstate.doNonConditional(config, simulation.bwArray, simulation.globalstate)  

  if config.debug and simulation.bitratestate.timeSinceLastDecision == 0 or config.verbose:
    simulation.printState(config, simulation.globalstate, simulation.chunkstate, simulation.bitratestate, simulation.bandwidthstate, simulation.bufferstate)

  # bring all data structures up to date to the current step
  simulation.globalstate.doNonConditional(config)
  simulation.chunkstate.doNonConditional(config)
  simulation.bufferstate.doNonConditional(config, simulation.sessionFullyDownloaded)
  simulation.bitratestate.doNonConditional(config, simulation.chunkstate)

  # handle the conditional events for relevant state data structures
  if not simulation.sessionFullyDownloaded:
  	simulation.chunkstate.doConditional(config, simulation.bwArray, simulation.globalstate, simulation.chunkstate, simulation.bitratestate, simulation.bandwidthstate, simulation.bufferstate)
  	simulation.bufferstate.doConditional(config, simulation.bwArray, simulation.globalstate, simulation.chunkstate, simulation.bitratestate, simulation.bandwidthstate, simulation.bufferstate)
  	simulation.bitratestate.doConditional(config, simulation.bwArray, simulation.globalstate, simulation.chunkstate, simulation.bitratestate, simulation.bandwidthstate, simulation.bufferstate)

  simulation.globalstate.doConditional(config, simulation.bwArray, simulation.globalstate, simulation.chunkstate, simulation.bitratestate, simulation.bandwidthstate, simulation.bufferstate, simulation.sessionFullyDownloaded)

  # if all the chunks in the sessions have been downloaded, mark the session complete
  if simulation.chunkstate.chunks_downloaded >= math.ceil((simulation.globalstate.tracePlaytime)/float(config.chunksize * 1000)): 
    simulation.sessionFullyDownloaded = True


if config.debug or config.verbose:
  simulation.printState(config, simulation.globalstate, simulation.chunkstate, simulation.bitratestate, simulation.bandwidthstate, simulation.bufferstate)

if simulation.bufferstate.blen > 0:
  simulation.globalstate.updatePlaytime(simulation.bufferstate.blen)

# generate final statistics
avg_bitrate, rebuf_ratio, _ = helpers.generateStats(simulation.globalstate.avg_bitrate, simulation.globalstate.bufftime, \
	simulation.globalstate.playtime, 1.0, simulation.globalstate.tracePlaytime)

simulation.printFinalStats(avg_bitrate, rebuf_ratio, simulation.bitratestate.num_switches)
