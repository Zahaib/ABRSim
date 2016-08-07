#!/usr/bin/python

from state import globalstate, bitratestate, bufferstate, chunkstate, bandwidthstate
import sys, os
import numpy as np
import helpers


class newsimulation(object):
  def __init__(self, config):
    self.sessionFullyDownloaded = False
    self.bwArray = helpers.parseTrace(config.tracefile)

    if(config.jointime < self.bwArray[0][0]):
      self.bwArray = helpers.insertJoinTimeandInitBW(config.jointime, self.bwArray[0][1], self.bwArray)

    self.globalstate = globalstate(config, self.bwArray)
    self.bitratestate = bitratestate(config)
    self.bufferstate = bufferstate(config)
    self.chunkstate = chunkstate(config)
    self.bandwidthstate = bandwidthstate(config, self.bwArray)

  def printHeader(self):
    print "\nSession joined..." #+ str(group2.irow(0)["clientid"]) + ", " + str(group2.irow(0)["clientsessionid"])
    print "TIME" + "\t" + "BW" + "\t" + "BLEN" + "\t" + "OBR" + "\t" + "BR" + "\t" + "CHKS" + "\t" + "RSDU" + "\t" + "BUFF" + "\t" + "PLAY"

  def printState(self, config, globalstate, chunkstate, bitratestate, bandwidthstate, bufferstate):
    print str(globalstate.clock/config.MSEC_IN_SEC) + "\t" + str(round(bandwidthstate.bandwidth,2)) + "\t" + str(round(bufferstate.blen,2)) + "\t" + str(bitratestate.old_bitrate) \
    + "\t" + str(bitratestate.bitrate) + "\t" + str(chunkstate.chunks_downloaded) + "\t" + str(round(chunkstate.chunk_residue,2)) + "\t" + str(round(globalstate.bufftime,2)) + "\t" \
    + str(round(globalstate.playtime,2))

  def printFinalStats(self, avg_bitrate, rebuf_ratio, num_switches):
    print"\nFinal output:"
    print "Avg. bitrate: " + str(avg_bitrate) 
    print "Rebuf_ratio: " + str(rebuf_ratio) 
    print "Number of switches: " + str(num_switches) 