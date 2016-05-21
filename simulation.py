# SIMULATION 1.0
import math
from config import *
from helpers import *
# TODO:
# 1. put the statistics logging inside a function
# 2. figure out non-conditional and conditional events
# 3. check whether a print at the end of the session is needed
# 4. check the bootstrap code and remove the assumptions

# def simulate(init, mid, singleSession): # input the pandas dataframe
# for i in range(500,1000,500):
hbconfig = [2000,5000,10000,15000,20000]
# for i in range(1000,20500,1000):
# for i in range(len(hbconfig)):
debugcount = 0
debugcountP = 0
debugcountN = 0
# singleSession[['timestampms', 'bandwidth']] = singleSession[['timestampms', 'bandwidth']].astype(int)
# sessionwise = singleSession.groupby(['clientid','clientsessionid'])
NUM_SESSIONS = 0
percentageErrorBitrate = []
percentageErrorRebuf = []
avgbitratePrecision = []
rebufPrecision = []
avgbitrateGroundTruth = []
rebufGroundTruth = []
avgbwSessions = []
stdbwSessions = []
completionTimeStamps = []

# for name1, group1 in sessionwise:
for gggg in range(0,1):
  if DEBUG:
    printHeader()

#     bwMap = dict()
  sizeDict = dict()
  usedBWArray = []
  bitratesPlayed = dict()
  BLEN, CHUNKS_DOWNLOADED, BUFFTIME, PLAYTIME, CANONICAL_TIME, INIT_HB, MID_HB, BR, BW, AVG_SESSION_BITRATE, SWITCH_LOCK, MAX_BUFFLEN, LOCK = initSysState()
  # group2 = group1.sort("timestampms")
  candidateBR, jointime, playtimems, sessiontimems, bitrate_groundtruth, bufftimems, BR, bwArray, CHUNKSIZE, TOTAL_CHUNKS = parseSessionStateFromTrace('filename')    
  
  if VALIDATION_MODE:
    bwArray = bwArray[0::2]
  if AVERAGE_BANDWIDTH_MODE:
    bwArray = validationBWMap(bwArray)
  
  avgbw, stdbw = getBWStdDev(bwArray)
  
  if not isSane(bwArray, BR, stdbw, avgbw, sizeDict):
    continue    

  BW = int(getInitBW(bwArray)) 
  if(jointime < bwArray[0][0]):
    bwArray = insertJoinTimeandInitBW(jointime, BW, bwArray)
  BLEN += CHUNKSIZE
  CHUNKS_DOWNLOADED += 1
  CANONICAL_TIME = jointime
  chunk_residue = 0 # partially downloded chunk
  AVG_SESSION_BITRATE += 1 * BR * CHUNKSIZE

  oldBR = BR
  if UTILITY_BITRATE_SELECTION:
    newBR = getUtilityBitrateDecision(BLEN, candidateBR, BW, CHUNKS_DOWNLOADED, CHUNKSIZE)
  else:
    newBR = getBitrateDecision(BLEN, candidateBR, BW)
  if newBR < BR:
    SWITCH_LOCK = LOCK
  BR = newBR

  buffering = False
  sessionFullyDownloaded = False

#   BW = getInitBW(BR, CANONICAL_TIME, CHUNKSIZE) # if want to calculate using the jointimems


  while CANONICAL_TIME - BLEN * 1000 < sessiontimems: # todo: check the termination condition bwArray[len(bwArray) - 1][0]
    # reset variables which are specific to a clock step
    playStalled_thisInterval = 0
    ch_d = 0
    blenAdded_thisInterval = 0

    if DEBUG:
      printStats(CANONICAL_TIME, BW, BLEN, BR, oldBR, CHUNKS_DOWNLOADED, BUFFTIME, PLAYTIME)
      
    if CHUNKS_DOWNLOADED * CHUNKSIZE * 1000 < 30000:
      interval = INIT_HB # 2 sec
    elif CHUNKS_DOWNLOADED * CHUNKSIZE * 1000 >= 30000:
      interval = MID_HB # 5 sec        

    CANONICAL_TIME += interval # incrementing the canonical_time which is the same as sessiontime. Todo: change variable name to session time      
    if SWITCH_LOCK > 0:
      SWITCH_LOCK -= interval/float(1000) # add float
    
    if BLEN > 0:
      buffering = False

    if buffering and not sessionFullyDownloaded:
      playStalled_thisInterval = min(timeToDownloadSingleChunk(CHUNKSIZE, BR, BW, chunk_residue, CHUNKS_DOWNLOADED), interval/float(1000)) # add float
      if playStalled_thisInterval < interval/float(1000): # chunk download so resume
        buffering = False

    if not sessionFullyDownloaded:
      # chunks downloaded during interval
#         print chunk_residue
      # print CANONICAL_TIME - interval, CANONICAL_TIME, BR, BW, CHUNKS_DOWNLOADED, CHUNKSIZE, chunk_residue
      chunks, completionTimeStamps = chunksDownloaded(CANONICAL_TIME - interval, CANONICAL_TIME, BR, BW, CHUNKS_DOWNLOADED, CHUNKSIZE, chunk_residue, usedBWArray,bwArray)
      ch_d = chunk_residue + chunks
#         print ch_d, CHUNKSIZE
  # calculate the size of the partially downloaded chunk
      chunk_residue = ch_d - int(ch_d) 
      if BLEN + ch_d * CHUNKSIZE >= MAX_BUFFLEN: # can't download more than the MAX_BUFFLEN
        ch_d = int(MAX_BUFFLEN - BLEN)/CHUNKSIZE
        chunk_residue = 0
    
    # can't download more chunks than the total playtime of the session.
    if CHUNKS_DOWNLOADED + int(ch_d) >=  math.ceil((playtimems)/float(CHUNKSIZE * 1000)):
      ch_d = math.ceil((playtimems)/float(CHUNKSIZE * 1000)) - CHUNKS_DOWNLOADED
      
    # only append fully downloaded chunks                       
    CHUNKS_DOWNLOADED += int(ch_d)
    blenAdded_thisInterval =  int(ch_d) * CHUNKSIZE

    # as long as the session has not finished downloading continue to update the average bitrate
    if CHUNKS_DOWNLOADED <= math.ceil((playtimems)/float(CHUNKSIZE * 1000)) and not sessionFullyDownloaded: # check the equal to sign in less than equal to
      AVG_SESSION_BITRATE += int(ch_d) * BR * CHUNKSIZE

    # if all the chunks in the sessions have been downloaded, mark the sessions complete
    if CHUNKS_DOWNLOADED >= TOTAL_CHUNKS or CHUNKS_DOWNLOADED >= math.floor((playtimems)/float(CHUNKSIZE * 1000)): 
      sessionFullyDownloaded = True

    # this condition checks if we can run into buffering during this session
    if not buffering and BLEN >= 0 and BLEN + blenAdded_thisInterval < interval/float(1000) and not sessionFullyDownloaded: 
      playStalled_thisInterval += (interval/float(1000) - BLEN - blenAdded_thisInterval) # add float
      buffering = True

    # update the buffering time and playtime accumulated during this interval
    # if not sessionFullyDownloaded:
    BUFFTIME += playStalled_thisInterval
    PLAYTIME += interval/float(1000) - playStalled_thisInterval # add float

    # print BUFFTIME, sessionFullyDownloaded
    # update the bufferlen at the end of this interval
#       BLEN = max(0, CHUNKS_DOWNLOADED * CHUNKSIZE - PLAYTIME) # this statement is same as above. Todo: check if this impacts correctness
    if buffering:
      BLEN = 0
    else:
      BLEN = max(0, CHUNKS_DOWNLOADED * CHUNKSIZE - PLAYTIME) # else update the bufferlen to take into account the current time step

    # get the bitrate decision for the next interval
    oldBR = BR
    if not sessionFullyDownloaded:
      if UTILITY_BITRATE_SELECTION:
        newBR = getUtilityBitrateDecision(BLEN, candidateBR, BW, CHUNKS_DOWNLOADED, CHUNKSIZE)
      elif BUFFERLEN_UTILITY:
        newBR = getBitrateBBA0(BLEN, candidateBR, conf)
      elif BANDWIDTH_UTILITY:
        newBR = getBitrateDecisionBandwidth(BLEN, candidateBR, BW)
      else:
        newBR = getBitrateDecision(BLEN, candidateBR, BW)

    # make the switch if switching up and no switch lock is active or switching down
    if (newBR > BR and SWITCH_LOCK <= 0) or newBR < BR:
      # activate switch lock if we have switched down      
      if newBR < BR:
        SWITCH_LOCK = LOCK
      BR = newBR
      # throw away the partially downloaded chunk if a switch is recommended
      chunk_residue = 0         
      
    if PS_STYLE_BANDWIDTH:
      BW = interpolateBWPrecisionServerStyle(CANONICAL_TIME, BLEN, usedBWArray)
    else:
      BW = max(interpolateBWInterval(CANONICAL_TIME, usedBWArray, bwArray),0.01) # interpolate bandwidth for the next heartbeat interval
    usedBWArray.append(BW) # save the bandwidth used in the session

  # if sessions has bad bandwidth info, just omit it
  if 0.01 in usedBWArray:
    continue

  NUM_SESSIONS += 1
  AVG_SESSION_BITRATE = (AVG_SESSION_BITRATE/float(playtimems/float(1000))) # add float
  REBUF_RATIO = round(BUFFTIME/float(BUFFTIME + PLAYTIME),3)
  rebuf_groundtruth = round(bufftimems/float(bufftimems + playtimems),3)

  avgbw, stdbw = getBWStdDev(bwArray)
  avgbwSessions.append(avgbw)
  stdbwSessions.append(stdbw)
  avgbitratePrecision.append(AVG_SESSION_BITRATE)
  rebufPrecision.append(REBUF_RATIO)
  avgbitrateGroundTruth.append(bitrate_groundtruth)
  rebufGroundTruth.append(rebuf_groundtruth)
#     print AVG_SESSION_BITRATE
  if (AVG_SESSION_BITRATE - bitrate_groundtruth)/float(bitrate_groundtruth) * 100 > 20:
    debugcountP += 1
  if (AVG_SESSION_BITRATE - bitrate_groundtruth)/float(bitrate_groundtruth) * 100 < -20:
    debugcountN += 1
  if abs(AVG_SESSION_BITRATE - bitrate_groundtruth)/float(bitrate_groundtruth) * 100 > 0:
    debugcount += 1
#       print str(int(AVG_SESSION_BITRATE)) + "\t" + str(bitrate_groundtruth) + "\t" + str(round(abs(AVG_SESSION_BITRATE - bitrate_groundtruth)/float(bitrate_groundtruth) * 100,2)) + "\t" + str(REBUF_RATIO) + "\t" + str(rebuf_groundtruth) + "\t" + str(abs(REBUF_RATIO - rebuf_groundtruth) * 100) + "\t" + str(name1) + "\t" + str(debugcount) + "\t" + str(avgbw) + "\t" + str(stdbw)
  if round(abs((AVG_SESSION_BITRATE - bitrate_groundtruth)/float(bitrate_groundtruth) * 100),2) < 40 and bitrate_groundtruth/float(avgbw) < 0.9:
    percentageErrorBitrate.append(round((AVG_SESSION_BITRATE - bitrate_groundtruth)/float(bitrate_groundtruth) * 100,2))
    percentageErrorRebuf.append(round((REBUF_RATIO - rebuf_groundtruth) * 100,2))
  if NUM_SESSIONS == 500:
    break


  if DEBUG:
    print "\nSimulated session average bitrate = " + str(AVG_SESSION_BITRATE) + " ground truth session = " + str(bitrate_groundtruth)
    print "Simulated session rebuf = " + str(REBUF_RATIO) + " ground truth session = " + str(round(bufftimems/float(bufftimems + playtimems),2))
#   print "Total Session: " + str(NUM_SESSIONS)
#   print "Total debugP: " + str(debugcountP)
#   print "Total debugN: " + str(debugcountN)

#   printPercentile(avgbitratePrecision) 
#   print str(50) + "\t" + str(np.percentile(avgbitratePrecision, 50))+ "\t" + str(np.percentile(avgbitrateGroundTruth, 50)) + "\t" + str(95) + "\t" + str(np.percentile(avgbitratePrecision, 95))+ "\t" + str(np.percentile(avgbitrateGroundTruth, 95)) + "\t" + str(50) + "\t" + str(np.percentile(rebufPrecision, 50)) + "\t" + str(np.percentile(rebufGroundTruth, 50)) + "\t" + str(95) + "\t" + str(np.percentile(rebufPrecision, 95)) + "\t" + str(np.percentile(rebufGroundTruth, 95))
# print five number summaries
# print str(i)+ "\t" + str(i/500)+ "\t" + str(np.percentile(avgbitratePrecision, 5))+ "\t" + str(np.percentile(avgbitratePrecision, 25))+ "\t" + str(np.percentile(avgbitratePrecision, 50))+ "\t" + str(np.percentile(avgbitratePrecision, 75))+ "\t" + str(np.percentile(avgbitratePrecision, 95))+ "\t" + str(np.percentile(rebufPrecision, 5)) + "\t" + str(np.percentile(rebufPrecision, 25)) + "\t" + str(np.percentile(rebufPrecision, 50)) + "\t" + str(np.percentile(rebufPrecision, 75)) + "\t" + str(np.percentile(rebufPrecision, 95))+ "\t" + str(np.percentile(rebufPrecision, 99))

#   print str(i)+ "\t" + str(i/500)+ "\t" + str(np.percentile(avgbitratePrecision, 50))+ "\t" + str(np.percentile(avgbitrateGroundTruth, 50))+ "\t" + str(np.percentile(avgbitratePrecision, 50))+ "\t" + str(np.percentile(avgbitratePrecision, 95))+ "\t" + str(np.percentile(avgbitrateGroundTruth, 95))+ "\t" + str(np.percentile(rebufPrecision, 50)) + "\t" + str(np.percentile(rebufGroundTruth, 50)) + "\t" + str(np.percentile(rebufPrecision, 95)) + "\t" + str(np.percentile(rebufGroundTruth, 95)) + "\t" + str(np.percentile(rebufPrecision, 99))+ "\t" + str(np.percentile(rebufGroundTruth, 99))
