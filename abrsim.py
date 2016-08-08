#!/usr/bin/python

import sys, os, math
import numpy as np
from userinput import parseinput
from sim import newsimulation
import algorithms, helpers

# parse user input and defaults to get the config for this sim
config = parseinput()

# create a new sim based on the config
sim = newsimulation(config)

if config.debug or config.verbose:
  sim.printHeader()

while sim.globalstate.clock < sim.globalstate.traceSessiontime:
  sim.bandwidthstate.doNonConditional(config, sim.bwArray, sim.globalstate)  

  if config.debug and sim.bitratestate.timeSinceLastDecision == 0 or config.verbose:
    sim.printState(config, sim.globalstate, sim.chunkstate, sim.bitratestate, sim.bandwidthstate, sim.bufferstate)

  # bring all data structures up to date to the current step
  sim.globalstate.doNonConditional(config)
  sim.chunkstate.doNonConditional(config)
  sim.bufferstate.doNonConditional(config, sim.sessionFullyDownloaded)
  sim.bitratestate.doNonConditional(config, sim.chunkstate)

  # handle the conditional events for relevant state data structures
  if not sim.sessionFullyDownloaded:
  	sim.chunkstate.doConditional(config, sim.bwArray, sim.globalstate, sim.chunkstate, sim.bitratestate, sim.bandwidthstate, sim.bufferstate)
  	sim.bufferstate.doConditional(config, sim.bwArray, sim.globalstate, sim.chunkstate, sim.bitratestate, sim.bandwidthstate, sim.bufferstate)
  	sim.bitratestate.doConditional(config, sim.bwArray, sim.globalstate, sim.chunkstate, sim.bitratestate, sim.bandwidthstate, sim.bufferstate)

  sim.globalstate.doConditional(config, sim.bwArray, sim.globalstate, sim.chunkstate, sim.bitratestate, sim.bandwidthstate, sim.bufferstate, sim.sessionFullyDownloaded)

  # if all the chunks in the sessions have been downloaded, mark the session complete
  if sim.chunkstate.chunks_downloaded >= math.ceil((sim.globalstate.tracePlaytime)/float(config.chunksize * config.MSEC_IN_SEC)): 
    sim.sessionFullyDownloaded = True


if config.debug or config.verbose:
  sim.printState(config, sim.globalstate, sim.chunkstate, sim.bitratestate, sim.bandwidthstate, sim.bufferstate)

if sim.bufferstate.blen > 0:
  sim.globalstate.updatePlaytime(sim.bufferstate.blen)

# generate final statistics
avg_bitrate, rebuf_ratio, _ = helpers.generateStats(sim.globalstate.avg_bitrate, sim.globalstate.bufftime, \
	sim.globalstate.playtime, 1.0, sim.globalstate.tracePlaytime)

sim.printFinalStats(avg_bitrate, rebuf_ratio, sim.bitratestate.num_switches)
