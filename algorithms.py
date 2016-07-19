#!/usr/bin/python

from helpers import *
from chunkMap import *
from config import *
import math
# utility function:
# pick the highest bitrate that will not introduce buffering
def getUtilityBitrateDecision(bufferlen, candidateBitrates, bandwidth, chunkid, CHUNKSIZE, BUFFER_SAFETY_MARGIN, buffering_weight):
  if BUFFER_SAFETY_MARGIN == -1:
    BUFFER_SAFETY_MARGIN = 0.275
  BUFFERING_WEIGHT = buffering_weight
  BITRATE_WEIGHT = 1
  BANDWIDTH_SAFETY_MARGIN = 0.9 # 0.90
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
  # extremely bad bandwidth case
  if ret == -1:
    ret = candidateBitrates[0]
  return ret

def isWithinBandwidth(br, bw):
  exp = 4.17989 * math.pow(10, -22) * math.pow(br, 6) - 1.19444* math.pow(10,-17) * math.pow(br, 5) + 1.25648 * math.pow(10, -13) * math.pow(br, 4) - 6.28056 * math.pow(10, -10) * math.pow(br, 3) + 1.57631 * math.pow(10, -6) * math.pow(br, 2) - 0.00185333 * br + 1.73095  
  if math.pow(br, exp) < bw:
    return True
  return False

#http://www.wolframalpha.com/input/?i=interpolate+%5B(1000,+0.94),+(2000,+0.96),+(3000,+0.98),+(4000,+0.98),+(5000,+1.05),+(5500,1.13),+(6000,+1.16)

#iteration7
#  exp = 4.17989 * math.pow(10, -22) * math.pow(br, 6) - 1.19444* math.pow(10,-17) * math.pow(br, 5) + 1.25648 * math.pow(10, -13) * math.pow(br, 4) - 6.28056 * math.pow(10, -10) * math.pow(br, 3) + 1.57631 * math.pow(10, -6) * math.pow(br, 2) - 0.00185333 * br + 1.73095

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
  # print maxbuflen, reservoir, maxRPct, int(maxbuflen * maxRPct)
  assert (maxbuflen > 30), "too small max player buffer length"
  assert (reservoir < maxbuflen), "initial reservoir is not smaller than max player buffer length"
  assert (maxRPct < 1)
  assert (bufferlen <= maxbuflen), "bufferlen greater than maxbufferlen"

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


# function returns the bitrate decision given the bufferlen using BBA2 in T.Y paper.
def getBitrateBBA2(bufferlen, candidateBitRate, conf, chunkid, CHUNKSIZE, bitrate, bandwidth, blen_decrease):
  maxbuflen = conf['maxbuflen']
  reservoir = conf['r']
  maxRPct = conf['maxRPct']
  X = conf['xLookahead']
  assert (maxbuflen > 30), "too small max player buffer length"
  assert (reservoir < maxbuflen), "initial reservoir is not smaller than max player buffer length"
  assert (maxRPct < 1)
  assert (bufferlen <= maxbuflen), "bufferlen greater than maxbufferlen"

  # calculate the fallback buffer if the dynamic calculation fails
  upperReservoir = int(maxbuflen * maxRPct)

  R_min = candidateBitRate[0]
  R_max = candidateBitRate[-1]
  # get the dynamic value of the reservoir
  reservoir = dynamicReservoir(bandwidth, chunkid, X, reservoir, CHUNKSIZE, bitrate, candidateBitRate)
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
  interpolatedCandidate = 0
  # find the max rate that is lower than then ideal one.
  for idx in range(len(candidateBitRate)):
    if RIdeal < sizeDict[candidateBitRate[idx]][chunkid]:
      interpolatedCandidate = candidateBitRate[idx-1]
      break
  
  startupCandidate = -1
  threshold = 0.0
  if not blen_decrease:
    if bufferlen >= 0 and bufferlen < int(upperReservoir / 8):
      threshold = 8.0
    elif bufferlen >= int(upperReservoir / 8) and bufferlen < int(upperReservoir / 4):
      threshold = 4.0
    elif bufferlen >= int(upperReservoir / 4) and bufferlen < int(upperReservoir / 1):
      threshold = 2.0
    else:
      return interpolatedCandidate

  if chunkid < len(sizeDict[bitrate]) and CHUNKSIZE / (((sizeDict[bitrate][chunkid] / 1000) * CHUNKSIZE) / float(bandwidth)) > threshold:
    newIndex = candidateBitRate.index(bitrate) + 1
    if newIndex >= len(candidateBitRate):
      newIndex -= 1
    startupCandidate = candidateBitRate[newIndex]

  if startupCandidate > interpolatedCandidate:
    return startupCandidate

  return interpolatedCandidate
    

# function returns the bitrate decision given the bufferlen using BBA2 in T.Y paper.
def getBitrateBBA1(bufferlen, candidateBitRate, conf, chunkid, CHUNKSIZE, bitrate, bandwidth):
  maxbuflen = conf['maxbuflen']
  reservoir = conf['r']
  maxRPct = conf['maxRPct']
  X = conf['xLookahead']
  assert (maxbuflen > 30), "too small max player buffer length"
  assert (reservoir < maxbuflen), "initial reservoir is not smaller than max player buffer length"
  assert (maxRPct < 1)
  assert (bufferlen <= maxbuflen), "bufferlen greater than maxbufferlen"

  # calculate the fallback buffer if the dynamic calculation fails
  upperReservoir = int(maxbuflen * maxRPct)

  R_min = candidateBitRate[0]
  R_max = candidateBitRate[-1]
  # get the dynamic value of the reservoir
  reservoir = dynamicReservoir(bandwidth, chunkid, X, reservoir, CHUNKSIZE, bitrate, candidateBitRate)
  #print conf['r'], reservoir
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
    if RIdeal < sizeDict[candidateBitRate[idx]][chunkid]:
      return candidateBitRate[idx-1]


# function returns the dynamic value of the reservoir
def dynamicReservoir(bw, chunkid, X, reservoir, CHUNKSIZE, bitrate, candidateBitRate):
  #print chunkid
  if chunkid > len(sizeDict[candidateBitRate[0]]) - X / CHUNKSIZE:
    return reservoir
  bufAdded = 0
  timeAccumulated = 0.0
  while chunkid < len(sizeDict[bitrate]) and ((sizeDict[bitrate][chunkid] / 1000.0) * CHUNKSIZE) / float(bw) + timeAccumulated < X:
    timeAccumulated += ((sizeDict[bitrate][chunkid] / 1000.0) * CHUNKSIZE) / float(bw)
#    print timeAccumulated
    bufAdded += CHUNKSIZE
    chunkid += 1
  #print "bufAdded: " + str(bufAdded) + " X: " + str(X)
  ret = max(X - bufAdded, 2)
  #print "bufAdded: " + str(bufAdded) + " X: " + str(X) + " ret: " + str(ret)
  return ret

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


