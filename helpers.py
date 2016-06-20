# LIST OF HELPER FUNCTIONS
import numpy as np
import random, sys
from config import *
from chunkMap import *
# function returns the most dominant bitrate played, if two are dominant it returns the bigger of two
def getDominant(dominantBitrate):
  ret = 0
  maxFreq = -sys.maxint
  for b in sorted(dominantBitrate.keys()):
    if maxFreq <= dominantBitrate[b]:
      ret = b
      maxFreq = dominantBitrate[b]
  #print dominantBitrate.items()
  return ret, maxFreq, sum(dominantBitrate.values())


# function return the initial bandwidth using the jointime of the session
def printPercentile(target):
  for i in range (0,101):
    print str(i/float(100)) + "\t" + str(np.percentile(target, i))
    
def getInitBWCalculated(init_br, jointime, chunksize):
  return int(init_br * chunksize / float(jointime) * 1000)

def getInitBW(bwArray):
  return bwArray[0][1]

# function prints a print header
def printHeader():
  print "\nSession joined..." #+ str(group2.irow(0)["clientid"]) + ", " + str(group2.irow(0)["clientsessionid"])
  print "TIME" + "\t" + "BW" + "\t" + "BLEN" + "\t" + "OBR" + "\t" + "BR" + "\t" + "CHKS" + "\t" + "BUFF" + "\t" + "PLAY"

# function prints current session status
def printStats(CANONICAL_TIME, BW, BLEN, BR, oldBR, CHUNKS_DOWNLOADED, BUFFTIME, PLAYTIME):
  print str(CANONICAL_TIME) + "\t" + str(BW) + "\t" + str(BLEN) + "\t" + str(oldBR) + "\t" + str(BR) + "\t" + str(CHUNKS_DOWNLOADED) + "\t" + str(BUFFTIME) + "\t" + str(PLAYTIME)

def initSysState():
  BLEN = 0
  CHUNKS_DOWNLOADED = 0
  BUFFTIME = 0
  PLAYTIME = 0
  CANONICAL_TIME = 0
  INIT_HB = 500
  MID_HB = 500
  BR = 0
  BW = 0
  AVG_SESSION_BITRATE = 0
  SWITCH_LOCK = 0
  return BLEN, CHUNKS_DOWNLOADED, BUFFTIME, PLAYTIME, CANONICAL_TIME, INIT_HB, MID_HB, BR, BW, AVG_SESSION_BITRATE, SWITCH_LOCK

def bootstrapSim(jointime, BW, BR, CHUNKSIZE):
  BLEN = 1.25
  CHUNKS_DOWNLOADED = 0
  CLOCK = jointime
  chunk_residue = BLEN / CHUNKSIZE 
  first_chunk = True
  return BLEN, CHUNKS_DOWNLOADED, CLOCK, chunk_residue, first_chunk  


def isSane(bwArray, BR, stdbw, avgbw, sizeDict):
  sanity = True
  if any(bw[1] < 0 for bw in bwArray):
    if DEBUG: print "Bad bandwidth value in bwArry, exiting..."
    sanity = False
  if any(ts[0] < 0 for ts in bwArray):
    if DEBUG: print "Bad timestamp value in bwArry, exiting..."
    sanity = False
  if any(bw[0] < 0 for bw in bwArray):
    if DEBUG: print "Bad bandwidth map, exiting..."
    sanity = False
  if BR == -1:
    if DEBUG: print "Bad init bitrate, exiting..."
    sanity = False
  # filter sessions which have avgbw less than 200kbps or greater than 250mbps
  # if avgbw < 200 or avgbw > 250000:
  #   if DEBUG: print "Bad bandwidth reported, exiting..."
  #   sanity = False
  # filter sessions for which not enough samples are available  
  if len(bwArray) < 3:
    if DEBUG: print "Not enough session information, exiting..."
    sanity = False
    # filter sessions which have too much bandwidth variation    
  if stdbw/float(avgbw) > 1: 
    if DEBUG: print "Bad bandwidth deviation, exiting..."
    sanity = False
  # if BR not in sizeDict.keys():
  #   if DEBUG: print "Bad BR reported, exiting..."
  #   sanity = False

  return sanity      

def generateStats(AVG_SESSION_BITRATE, BUFFTIME, PLAYTIME, bufftimems, playtimems):
  AVG_SESSION_BITRATE = (AVG_SESSION_BITRATE/float(PLAYTIME)) # add float
  REBUF_RATIO = round(BUFFTIME/float(BUFFTIME + PLAYTIME),3)
  rebuf_groundtruth = round(bufftimems/float(bufftimems + playtimems),3)
  
  return AVG_SESSION_BITRATE, REBUF_RATIO, rebuf_groundtruth

# inserts the jointime and bandwidth as an additional timestamp and bandwidth  
def insertJoinTimeandInitBW(ts, bw, bwArray):
  t = []
  t.append(ts)
  b = []
  b.append(bw)
  row = zip(t,b)
  bwArray = row + bwArray
  return bwArray

# getStall Implementation
def getStall(ch_d, completionTimeStamps, bufferlen, intervalStart, interval, CHUNKSIZE):
  if ch_d != len(completionTimeStamps):
    return False,0
  if ch_d == 0 and bufferlen < interval :
    return True, interval - bufferlen
  if bufferlen > interval:
    return False, 0
  stall = 0
  ts_minus1 = intervalStart
  for i in range(ch_d):
#     if i < len(completionTimeStamps):
    if bufferlen < interval and (completionTimeStamps[i] - ts_minus1)/float(1000) > bufferlen:
      stall += (completionTimeStamps[i]  - ts_minus1)/float(1000) - bufferlen
      bufferlen = CHUNKSIZE + max(0, bufferlen - (completionTimeStamps[i] - ts_minus1)/float(1000))
    elif bufferlen < interval and (completionTimeStamps[i] - ts_minus1)/float(1000) < bufferlen:
      bufferlen = bufferlen - (completionTimeStamps[i] - ts_minus1)/float(1000) + CHUNKSIZE
    else:
      bufferlen = bufferlen - (completionTimeStamps[i] - ts_minus1)/float(1000) + CHUNKSIZE
    ts_minus1 = completionTimeStamps[i]
      
  if len(completionTimeStamps) > 0 and (completionTimeStamps[-1] - intervalStart)/float(1000) + bufferlen < interval:
    stall += interval - (completionTimeStamps[-1] - intervalStart)/float(1000) - bufferlen
    return True, round(stall,2)
  return False, round(stall,2)

# funtion returns the time it will take to download a single chunk whether downloading a new chunk or finishing up a partial chunk
def timeToDownloadSingleChunk(CHUNKSIZE, bitrate, BW, chunk_residue, chunkid):
  if BW == 0:
    return 1000000 # one thousand seconds, very large number
  if CHUNK_AWARE_MODE and bitrate in sizeDict and chunkid in sizeDict[bitrate]:
    bitrate = sizeDict[bitrate][chunkid] * 8/float(CHUNKSIZE * 1000)
  return round((bitrate * CHUNKSIZE - bitrate * CHUNKSIZE * chunk_residue)/float(BW),2)


# function returns the number of chunks downloaded during the heartbeat interval  
# def chunksDownloaded(time_prev, time_curr, bitrate, bandwidth, chunkid, CHUNKSIZE, chunk_residue):
#   if CHUNK_AWARE_MODE and bitrate in sizeDict and chunkid in sizeDict[bitrate]:
#     bitrate = sizeDict[bitrate][chunkid] * 8/(CHUNKSIZE * 1000)
#   return round(bandwidth/(float(bitrate) * CHUNKSIZE) * (time_curr - time_prev)/float(1000), 2)

# function returns the number of chunks downloaded during the heartbeat interval and uses delay
def chunksDownloaded(time_prev, time_curr, bitrate, bandwidth, chunkid, CHUNKSIZE, chunk_residue, usedBWArray, bwArray):
  chunkCount = 0.0
  completionTimeStamps = []
  bitrateAtIntervalStart = bitrate
  if CHUNK_AWARE_MODE:
    bitrate = getRealBitrate(bitrateAtIntervalStart, chunkid, CHUNKSIZE)

  time2FinishResidueChunk = (((1 - chunk_residue) * bitrate * CHUNKSIZE)/float(bandwidth)) * 1000
  time2DownloadFullChunk = (bitrate * CHUNKSIZE/float(bandwidth)) * 1000
  # if there is a residue chunk from the last interval, then handle it first
  if chunk_residue > 0 and time_prev + time2FinishResidueChunk < time_curr:
    chunkCount +=  1 - chunk_residue
    completionTimeStamps.append(time_prev + time2FinishResidueChunk)
    time_prev += time2FinishResidueChunk + getRandomDelay()
    # residue chunk is complete so now move to next chunkid and get the actual bitrate of the next chunk
    if CHUNK_AWARE_MODE:
      bitrate = getRealBitrate(bitrateAtIntervalStart, chunkid, CHUNKSIZE)
    bandwidth = max(interpolateBWInterval(time_prev, usedBWArray, bwArray),0.01)
    chunkid += 1
    time2DownloadFullChunk = (bitrate * CHUNKSIZE/float(bandwidth)) * 1000
    
  # loop untill chunks can be downloaded in the interval, after each download add random delay
  while time_prev + time2DownloadFullChunk < time_curr:
    chunkCount += 1
    completionTimeStamps.append(time_prev + time2DownloadFullChunk)
    time_prev += time2DownloadFullChunk + getRandomDelay()
    if CHUNK_AWARE_MODE:
      bitrate = getRealBitrate(bitrateAtIntervalStart, chunkid, CHUNKSIZE)
    # print time_prev, usedBWArray        
    bandwidth = max(interpolateBWInterval(time_prev, usedBWArray, bwArray),0.01)
    chunkid += 1
    time2DownloadFullChunk = (bitrate * CHUNKSIZE/float(bandwidth)) * 1000
  # if there is still some time left, download the partial chunk  
  if time_prev < time_curr:
    chunkCount += round(bandwidth/(float(bitrate) * CHUNKSIZE) * (time_curr - time_prev)/float(1000), 2)
  return chunkCount, completionTimeStamps


# function returns a random delay value to mimic the delay between start and end chunks
def getRandomDelay():
#   return 0
  return random.randint(150, 250)

# function returns the actual bitrate of the label bitrate and the specific chunk
def getRealBitrate(bitrate, chunkid, CHUNKSIZE):
  ret = bitrate
  if CHUNK_AWARE_MODE and bitrate in sizeDict and chunkid in sizeDict[bitrate]:
    ret = sizeDict[bitrate][chunkid] * 8/float(CHUNKSIZE * 1000)
  return ret
  
# return the average and standard deviation of the session bandwidth
def getBWStdDev(bwArray):
  bwMat = np.array(bwArray)
  return np.around(np.average(bwMat[:,1]),2), np.around(np.std(bwMat[:,1]),2)
        
# function intializes session state
def parseSessionState(group):
  ret = []
  ts = []
  bw = []
  for i in group.irow(0)["candidatebitrates"].split(","):
    ret.append(int(i))
  for j in range(0, group.shape[0]):
    ts.append(group.irow(j)["timestampms"])
    bw.append(group.irow(j)["bandwidth"])
  return ret, int(group.irow(0)["jointimems"]), int(group.irow(0)["playtimems"]), int(group.irow(0)["sessiontimems"]), int(group.irow(0)["lifeaveragebitratekbps"]), int(group.irow(0)["bufftimems"]), int(group.irow(0)["init_br"]), zip(ts,bw), int(group.irow(0)["chunkDuration"]), len(sizeDict[ret[0]]) #10 , 75 # 

# function intializes session state
def parseSessionStateFromTrace(filename):
  ts, bw = [], []
  ls = open(filename).readlines()
  for l in ls:
    if l in ['\n', '\r\n']:
      continue
    ts.append(float(l.split(" ")[0]))
    bw.append(float(l.split(" ")[1]))
  
  bitrates = [1002, 1434, 2738, 3585, 4661, 5885] # candidate bitrates are in kbps, you can change these to suite your values
  #bitrates  = range(150,2150,400)
  #ts = []
  #bw = []

  # now write the code to read the trace file

  # for j in range(0, group.shape[0]):
  #   ts.append(group.irow(j)["timestampms"])
  #   bw.append(group.irow(j)["bandwidth"])

  #ts = [0, 1000, 2000, 3000, 4000, 5000, 6000]
  #bw = [179981.99099548874, 203036.0, 209348.0, 198828.0000000001, 209348.0, 203036.0, 209348.0]    
  totalTraceTime = ts[-1] # read this value as the last time stamp in the file
  chunkDuration = 5
  jointimems = 500

  return bitrates, jointimems, totalTraceTime, totalTraceTime + jointimems, 1, 1, bitrates[0], zip(ts,bw), chunkDuration, sys.maxint #10 , 75 # 


# function returns interpolated bandwidth at the time of the heartbeat
def interpolateBWInterval(time_heartbeat, usedBWArray, bwArray):
  # print time_heartbeat, usedBWArray
  time_prev, time_next, bw_prev, bw_next = findNearestTimeStampsAndBandwidths(time_heartbeat, usedBWArray, bwArray) # time_prev < time_heartbeat < time_next
  # print time_prev, time_next, bw_prev, bw_next
  # print bwArray
  intervalLength = time_next - time_prev  
#   if time_heartbeat > time_next:
#     return (bw_prev + bw_next)/2
  # print time_prev, time_next, bw_prev, bw_next
  return int((intervalLength - (time_heartbeat - time_prev))/float(intervalLength) * bw_prev + (intervalLength - (time_next - time_heartbeat))/float(intervalLength) * bw_next)

def interpolateBWPrecisionServerStyle(time_heartbeat, BLEN, usedBWArray):
  time_prev, time_next, bw_prev, _ = findNearestTimeStampsAndBandwidths(time_heartbeat, usedBWArray, bwArray) # time_prev < time_heartbeat < time_next
  time_prev_prev, time_next_next, bw_prev_prev, _ = findNearestTimeStampsAndBandwidths(time_prev, usedBWArray, bwArray) # time_prev < time_heartbeat < time_next
  if time_prev_prev == 0:
#     print "not found " + "\t" + str(bw_prev) + "\t" + str(bw_prev_prev) + "\t" + str(interpolateBWInterval(time_heartbeat, usedBWArray))
    return interpolateBWInterval(time_heartbeat, usedBWArray) 
  if BLEN < 10:
    return min(bw_prev, bw_prev_prev)
  
  return (bw_prev + bw_prev_prev)/2

# function returns the nearest timestamps and bandwidths to the heartbeat timestamp
def findNearestTimeStampsAndBandwidths(time_heartbeat, usedBWArray, bwArray):
  time_prev, time_next, bw_prev, bw_next = 0, 0, 0, 0
  if len(usedBWArray) > 1 and time_heartbeat > bwArray[len(bwArray) - 1][0]:
    bw_next = pickRandomFromUsedBW(usedBWArray)
    time_next = time_heartbeat
  for i in range(0, len(bwArray)):
    if bwArray[i][0] < time_heartbeat:
      time_prev = bwArray[i][0]
      bw_prev = bwArray[i][1]
  for i in range(len(bwArray) - 1, -1, -1):
    if bwArray[i][0] > time_heartbeat:
      time_next = bwArray[i][0]
      bw_next = bwArray[i][1]
  return time_prev, time_next, bw_prev, bw_next

# function just returns a bandwidth randomly form the second half of the session
def pickRandomFromUsedBW(usedBWArray):
#   if len(usedBWArray) < 4:
#     return -1
  return usedBWArray[random.randint(len(usedBWArray)/2 ,len(usedBWArray) - 1)]
  
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

# function to get the best value of the Buffer Safety Margin
def getDynamicBSM(nSamples, hbCount, BSM): 
  if hbCount < 5:
    return 0.25
  stdbw = []
  if nSamples.count(0) != 5:
    for s in nSamples:
      if s == 0:
        continue
      stdbw.append(s)
  CV = np.std(stdbw) / np.mean(stdbw)
  BUFFER_SAFETY_MARGIN = 0.0
  if hbCount % 5 != 0:
    return BSM
  if hbCount != 0 and hbCount % 5 == 0:
    if CV >= 0 and CV < 0.1:
      BUFFER_SAFETY_MARGIN = 0.85
    elif CV >= 0.1 and CV < 0.2:
      BUFFER_SAFETY_MARGIN = 0.65
    elif CV >= 0.2 and CV < 0.3:
      BUFFER_SAFETY_MARGIN = 0.45
    elif CV >= 0.3 and CV < 0.4:
      BUFFER_SAFETY_MARGIN = 0.35
    else:
      BUFFER_SAFETY_MARGIN = 0.20
  return BUFFER_SAFETY_MARGIN

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

# returns a bwArray of average of bandwidth at every 10 second interval
def validationBWMap(bwArray):
  ts = []
  bw = []
#   print bwArray
  avg, count, index, i = 0, 0, 0, 0
  last = bwArray[len(bwArray) - 1][0] % 10000
  while bwArray[i][0] <= bwArray[len(bwArray) - 1][0] - last:
    while bwArray[i][0] > index * 10000 and bwArray[i][0] <= index * 10000 + 10000:
#       avg += (10000 - (index * 10000 + 10000 - bwArray[i][0]))/10000 * bwArray[i][1] # time weighted average
      avg += bwArray[i][1] # simple average
      i += 1
      count += 1
#       print avg

    index += 1
    if count > 0:
      ts.append(index * 10000)
      bw.append(round(avg/int(count),2))
      avg = 0
      count = 0
  
  if i < len(bwArray) - 1:
    j = len(bwArray) - 1
    while bwArray[len(bwArray) - 1][0] - bwArray[j][0] < 10000:
      avg += bwArray[j][1]
      count += 1
      j -= 1
    ts.append(bwArray[len(bwArray) - 1][0])
    bw.append(round(avg/int(count),2))
  
#   print zip(ts,bw)
  return zip(ts,bw)

