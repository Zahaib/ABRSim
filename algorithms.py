#!/usr/bin/python

from helpers import *
from chunkMap import *
from config import *

# utility function:
  # pick the highest bitrate that will not introduce buffering
def getUtilityBitrateDecision(bufferlen, candidateBitrates, bandwidth, chunkid, CHUNKSIZE, BUFFER_SAFETY_MARGIN):
  if BUFFER_SAFETY_MARGIN == -1:
    BUFFER_SAFETY_MARGIN = 0.25
  BUFFERING_WEIGHT = -1000
  BITRATE_WEIGHT = 1
  BANDWIDTH_SAFETY_MARGIN = 1 # 0.90
  ret = -1;
  candidateBitrates = sorted(candidateBitrates)
  estBufferingTime = 0
  utility = -1000000
  actualbitrate = 0
  bandwidth = bandwidth * BANDWIDTH_SAFETY_MARGIN
  for br in candidateBitrates:
#     if bandwidth < br * BANDWIDTH_SAFETY_MARGIN:
#       continue
# the buffer len you will add: sum of buffer you will download plus current buffer. If current buffer is zero then the
# amount you will add is a function of bandwidth alone. If the bandwidth is zero, then the buffer you have is just the
# current value of the buffer.
    actualbitrate = br
    if CHUNK_AWARE_MODE and br in sizeDict and chunkid in sizeDict[br]: actualbitrate = getRealBitrate(br, chunkid, CHUNKSIZE) #sizeDict[br][chunkid]*8/float(CHUNKSIZE * 1000)
    bufferlengthMs = bufferlen - actualbitrate * CHUNKSIZE/float(bandwidth) + CHUNKSIZE
    estBufferingTime = 1000 * max(actualbitrate * CHUNKSIZE/float(bandwidth) - bufferlengthMs * BUFFER_SAFETY_MARGIN, 0) # all computation are in milli seconds
    if utility < estBufferingTime * BUFFERING_WEIGHT + br * BITRATE_WEIGHT:
      ret = br
      utility = estBufferingTime * BUFFERING_WEIGHT + br * BITRATE_WEIGHT
#     if max(actualbitrate * CHUNKSIZE/bandwidth - bufferlen * BUFFER_SAFETY_MARGIN, 0) == 0: ret = br
  # extremely bad bandwidth case
  if ret == -1:
    ret = candidateBitrates[0]
  return ret


# function returns the bitrate decision given the bufferlen and bandwidth at the heartbeat interval
def getUtilityBitrateDecisionBasic(bufferlen, bitrates, bandwidth, chunkid, CHUNKSIZE):
  WEIGHT = 0
  ret = -1;
  bitrates = sorted(bitrates)
  if bufferlen >= 0 and bufferlen <= 15:
    WEIGHT = 1.15 #1.25 #3 #5 #1.5
  elif bufferlen > 15 and bufferlen <= 35:
    WEIGHT = 0.75 #0.85 #2 #4 #1
  elif bufferlen > 35:
    WEIGHT = 0.5 #0.75 #1 #3 # 0.75

  for br in bitrates:
    if br * WEIGHT <= bandwidth:
      ret = br

  # special case: bandwidth is extremely bad such that no suitable bitrate could be assigned then just return the lowest available bitrate
  if ret == -1:
    ret = bitrates[0]
  return ret

# function returns the bitrate decision given the bufferlen using BBA0 in T.Y paper.
# conf is a dict storing any configuration related stuff, for this case, conf = {'maxbuflen':120, 'r': 45, 'maxRPct':0.9}
def getBitrateBBA0(bufferlen, candidateBitRate, conf):
  maxbuflen = conf['maxbuflen']
  reservoir = conf['r']
  maxRPct = conf['maxRPct']
#  print maxbuflen, reservoir, maxRPct, int(maxbuflen * maxRPct)
  assert (maxbuflen > 30), "too small max player buffer length"
  assert (reservoir < maxbuflen), "initial reservoir is not smaller than max player buffer length"
  assert (maxRPct < 1)
  assert (bufferlen < maxbuflen), "bufferlen greater than maxbufferlen"

  upperReservoir = int(maxbuflen * maxRPct)

  R_min = candidateBitRate[0]
  R_max = candidateBitRate[-1]

  #print "Rmin=%d, Rmax=%d, reservoir=%d, upperReservoir=%d " % (R_min, R_max, reservoir, upperReservoir)

  # if bufferlen is small, return R_min
  if (bufferlen <=reservoir):
    return R_min
  # if bufferlen is close to full, return R_max
  if (bufferlen >=upperReservoir):
    return R_max

  # linear interpolation of the bufferlen vs bit-rate
  RGap = R_max - R_min
  BGap = upperReservoir - reservoir

  assert (RGap > 100), "R_max and R_min need at least 100kbps gap"
  assert (BGap > 30), "upper reservoir and reservoir need at least 30s gap"

  # based on the slope calc. ideal bit-rate
  RIdeal = R_min + int((bufferlen - reservoir) * RGap * 1.0 / (BGap*1.0))

  #print "RGap = %d, BGap=%d, RIdeal=%d" % (RGap, BGap, RIdeal)

  # find the max rate that is lower than then ideal one.
  for idx in range(len(candidateBitRate)):
    if RIdeal < candidateBitRate[idx]:
      return candidateBitRate[idx-1]


# function returns the bitrate decision only on the basis of bandwidth
def getBitrateDecisionBandwidth(bufferlen, bitrates, bandwidth):
  BANDWIDTH_SAFETY_MARGIN = 1.2
  ret = -1;
  for br in bitrates:
    if br * BANDWIDTH_SAFETY_MARGIN <= bandwidth:
      ret = br

  # special case: bandwidth is extremely bad such that no suitable bitrate could be assigned then just return the lowest available bitrate
  if ret == -1:
    ret = bitrates[0]
  return ret


# function return the bitrate decision as a weighted average: a * BW + (1 - a)Avg(nSamples)
def getBitrateWeightedBandwidth(bitrates, BW, nSamples, weight):
  A = weight
  avg_nSamples = 0.0
  count = 0
  ret = -1
  weighted_BW = -1
  if nSamples.count(0) != 5:
    for s in nSamples:
      if s == 0:
        continue
      avg_nSamples += s
      count += 1
    avg_nSamples /= count
    weighted_BW = int(A * avg_nSamples + (1 - A) * BW)
  else:
    weighted_BW = BW

  # print BW, weighted_BW, avg_nSamples

  for br in bitrates:
    if br <= weighted_BW:
      ret = br

  if ret == -1:
    ret = bitrates[0]

  return ret

