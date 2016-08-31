#!/usr/bin/python
# import config
import helpers, algorithms
import math, sys
import numpy as np

class globalstate(object):

  def __init__(self, config, bwArray):
    self.clock = config.jointime
    self.simstep = config.simstep
    self.bufftime = 0
    self.playtime = 0
    self.avg_bitrate = 0
    self.traceSessiontime = bwArray[-1][0] + config.jointime
    self.tracePlaytime = bwArray[-1][0]
    
  def doNonConditional(self, config):
    if self.clock + self.simstep > self.traceSessiontime:
      self.simstep = self.traceSessiontime - self.clock
    self.clock += self.simstep

  def doConditional(self, config, bwArray, globalstate, chunkstate, bitratestate, bandwidthstate, bufferstate, isComplete):
    self.bufftime += bufferstate.playStalled_thisStep
    self.playtime += self.simstep/config.MSEC_IN_SEC - bufferstate.playStalled_thisStep

    bitrate_toUse = 0
    if bitratestate.didSwitch:
      bitrate_toUse = bitratestate.old_bitrate
    else:
      bitrate_toUse = bitratestate.bitrate

    if chunkstate.chunks_downloaded <= math.ceil((self.tracePlaytime)/float(config.chunksize * 1000)) and not isComplete: # check the equal to sign in less than equal to
      self.avg_bitrate += int(chunkstate.chd_thisStep) * bitrate_toUse * config.chunksize

  def updatePlaytime(self, val):
    self.playtime += val


class chunkstate(object):
  def __init__(self, config):
    self.first_chunk = True
    self.chd_thisStep = 0
    self.chunk_sched_time_delay = 0
    self.chunk_residue =  config.join_buffsize / config.chunksize
    self.chunks_downloaded = 0
    self.chunk_residue_step_start = 0
    self.chunks_downloaded_step_start = 0
    self.last_decision_bitrate = config.bitrate
    self.sessionHistory = dict()
    self.chunk_bitratesPlayed = dict()
    self.time_to_finish_chunk = 0

  def doNonConditional(self, globalstate, config):
    self.chd_thisStep = 0
    self.chunk_sched_time_delay = max(0, self.chunk_sched_time_delay - globalstate.simstep)
    self.chunk_residue_step_start = self.chunk_residue
    self.chunks_downloaded_step_start = self.chunks_downloaded


  def doConditional(self, config, bwArray, globalstate, chunkstate, bitratestate, bandwidthstate, bufferstate):
    self.chd_thisStep = 0

    if bitratestate.bitrate != self.last_decision_bitrate:
      self.chunk_residue = 0
      self.last_decision_bitrate = bitratestate.bitrate

    if self.chunk_sched_time_delay < globalstate.simstep:
      numChunks, completionTimeStamps, self.chunk_sched_time_delay = helpers.chunksDownloaded(globalstate.clock - globalstate.simstep, globalstate.clock, bitratestate.bitrate, \
      bandwidthstate.bandwidth, self.chunks_downloaded, config.chunksize, self.chunk_residue, bandwidthstate.usedBWArray, bwArray, self.chunk_sched_time_delay, bufferstate.blen)

      self.chd_thisStep = self.chunk_residue + numChunks

      # ToDo: this condition should move to the chunksDownloaded function instead of being here.
      # if a chunk was completed then need to add delay
      if int(self.chd_thisStep) >= 1 and self.chunk_sched_time_delay < globalstate.simstep:
        self.chunk_sched_time_delay = helpers.getRandomDelay(bitratestate.bitrate, self.chunks_downloaded, config.chunksize, bufferstate.blen)

    if bufferstate.blen + self.chd_thisStep * config.chunksize >= config.max_buflen: # can't download more than the MAX_BUFFLEN
      self.chd_thisStep = int(config.max_buflen - bufferstate.blen) / config.chunksize
      self.chunk_residue = 0
    elif self.chunks_downloaded + int(self.chd_thisStep) >=  math.ceil((globalstate.tracePlaytime)/float(config.chunksize * 1000)):
      self.chd_thisStep = math.ceil((globalstate.tracePlaytime)/float(config.chunksize * 1000)) - self.chunks_downloaded
      
    self.chunk_residue = self.chd_thisStep - int(self.chd_thisStep) 
      
    if self.chunks_downloaded >= 1:
      self.first_chunk = False  

    # can we finish the download of the chunk before buffer drains
    # self.time_to_finish_chunk = helpers.timeRemainingFinishChunk(self.chunk_residue, bitratestate.bitrate, bandwidthstate.bandwidth, self.chunks_downloaded, config.chunksize)
    # append the information to session history if a chunk just finished to downloaded
    # if int(self.chd_thisStep) == 1:
    #   self.sessionHistory = helpers.updateSessionHistory(bitratestate.bitrate, globalstate.clock, self.chunks_downloaded, config.chunksize, self.sessionHistory, self.first_chunk, self.chunk_sched_time_delay)

    # only append fully downloaded chunks                       
    self.chunks_downloaded += int(self.chd_thisStep)

    # update the dictionary with count of chunks downloaded for a particular bitrate
    if bitratestate.bitrate in self.chunk_bitratesPlayed:
      self.chunk_bitratesPlayed[bitratestate.bitrate] += int(self.chd_thisStep)
    else:
      self.chunk_bitratesPlayed[bitratestate.bitrate] = int(self.chd_thisStep)    


class bufferstate(object):

  def __init__(self, config):
    self.buffering = False
    self.buffer_full = False
    self.blenAdded_thisStep = 0.0
    self.playStalled_thisStep = 0.0
    self.blen = config.join_buffsize

  def doNonConditional(self, config, globalstate, isComplete):
    if self.blen > 0:
      self.buffering = False

    if isComplete:
      self.blen = max(self.blen - globalstate.simstep / config.MSEC_IN_SEC, 0)

  def doConditional(self, config, bwArray, globalstate, chunkstate, bitratestate, bandwidthstate, bufferstate):
    self.blenAdded_thisStep = 0
    self.playStalled_thisStep = 0
    if self.buffering:
      self.playStalled_thisStep = min(helpers.timeToDownloadSingleChunk(config.chunksize, bitratestate.bitrate, bandwidthstate.bandwidth, \
      chunkstate.chunk_residue_step_start, chunkstate.chunks_downloaded_step_start), globalstate.simstep/config.MSEC_IN_SEC)
      if self.playStalled_thisStep < (globalstate.simstep / config.MSEC_IN_SEC):
        self.buffering = False

    # if self.playStalled_thisStep == globalstate.simstep/config.MSEC_IN_SEC and chunkstate.chd_thisStep >= 1.0:
    #   buffering = False

    self.blenAdded_thisStep =  int(chunkstate.chd_thisStep) * config.chunksize

    if chunkstate.chd_thisStep >= 1.0:
      self.buffering = False 

    # this condition checks if we got in buffering during this interval
    if not self.buffering and self.blen >= 0 and self.blen + self.blenAdded_thisStep < globalstate.simstep/config.MSEC_IN_SEC:
      self.playStalled_thisStep += (globalstate.simstep/config.MSEC_IN_SEC - self.blen - self.blenAdded_thisStep)
      self.buffering = True

    # update the bufferlen at the end of this interval
    if self.buffering:
      self.blen = 0
    elif not self.buffering and chunkstate.first_chunk and chunkstate.chunks_downloaded == 0:
      self.blen = max(0, self.blen  - globalstate.simstep/config.MSEC_IN_SEC)
    else:
      self.blen = max(0, chunkstate.chunks_downloaded * config.chunksize - (globalstate.playtime + globalstate.simstep/config.MSEC_IN_SEC - self.playStalled_thisStep))


class bitratestate(object):

  def __init__(self, config):
    self.decision_cycle = config.init_hb
    self.timeSinceLastDecision = 0
    self.switch_lock = 0
    self.bitrate = config.bitrate
    self.old_bitrate = config.old_bitrate
    self.num_switches = 0
    self.didSwitch = False

  def doNonConditional(self, config, globalstate, chunkstate):
    self.didSwitch = False
    if self.switch_lock > 0:
      self.switch_lock -= globalstate.simstep / config.MSEC_IN_SEC

    if chunkstate.chunks_downloaded < config.init_stream:
      self.decision_cycle = config.init_hb
    else:
      self.decision_cycle = config.mid_hb

    self.timeSinceLastDecision += globalstate.simstep
    self.timeSinceLastDecision = self.timeSinceLastDecision % self.decision_cycle


  def doConditional(self, config, bwArray, globalstate, chunkstate, bitratestate, bandwidthstate, bufferstate):
    newBR = 0
    if not chunkstate.first_chunk and self.timeSinceLastDecision == 0: #self.decision_cycle:
      if config.abr == 'utility':
        buffering_weight = -1000.0
        BSM = config.bsm
        newBR = algorithms.getUtilityBitrateDecision(bufferstate.blen, config.candidates, bandwidthstate.bandwidth, chunkstate.chunks_downloaded, \
        config.chunksize, BSM, buffering_weight, chunkstate.sessionHistory, chunkstate.chunk_residue, bitratestate.bitrate)
    elif config.abr == 'buffer':
      conf = {'maxbuflen':120, 'r': config.lower_res, 'maxRPct':config.upper_res, 'xLookahead':50}
      newBR = algorithms.getBitrateBBA0(bufferstate.blen, config.candidates, conf)
    elif config.abr == 'rate':
      newBR = algorithms.getBitrateDecisionBandwidth(bufferstate.blen, config.candidates, bandwidthstate.bandwidth)
    else:
      newBR = self.bitrate

    #TODO: instead of newBR and self.bitrate use only self.old_bitrate and self.bitrate 

    # make the switch if switching up and no switch lock is active or switching down
    # if not chunkstate.first_chunk and (newBR > self.bitrate and self.switch_lock <= 0 and chunkstate.chunks_downloaded >= 2 and \
    #   chunkstate.time_to_finish_chunk < bufferstate.blen * 1000.0) or (newBR < self.bitrate and chunkstate.time_to_finish_chunk > bufferstate.blen * 0.05 * 1000.0):
    if (newBR > self.bitrate and self.switch_lock <= 0) or newBR < self.bitrate:
      self.didSwitch = True
      # activate switch lock if we are switching down      
      if newBR < self.bitrate and self.switch_lock <= 0:
        self.switch_lock = config.switch_lock
      
      # update the bitrate, old_bitrate and increase count of number of switches
      self.old_bitrate = self.bitrate
      self.bitrate = newBR
      self.num_switches += 1



class bandwidthstate(object):
  def __init__(self, config, bwArray):
    self.bandwidth = -1 #bwArray[0][1]
    self.usedBWArray = []
    self.avgbw, self.stdbw = helpers.getBWStdDev(bwArray)

  def doNonConditional(self, config, bwArray, globalstate):
    # ToDo: remove this minimum bandwidth condition
    # interpolate bandwidth for the next heartbeat interval
    if globalstate.clock == config.jointime:
      self.bandwidth = int(bwArray[0][1])
    else:
      self.bandwidth = max(helpers.interpolateBWInterval(globalstate.clock, self.usedBWArray, bwArray),0.01)
    self.usedBWArray.append(self.bandwidth)





  

