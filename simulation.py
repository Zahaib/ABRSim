# SIMULATION 1.0
import math, sys, collections
from config import *
from helpers import *
from chunkMap import *
from algorithms import *
import numpy as np
import collections
# TODO:
# 1. put the statistics logging inside a function
# 2. figure out non-conditional and conditional events
# 3. check whether a print at the end of the session is needed
# 4. check the bootstrap code and remove the assumptions (done)
# 5. subtract last chunk's unplayed part from AVG_BITRATE 
# 6. LOCK should be decremented by the PLAYTIME acquired in an interval rather than interval length
if TRACE_MODE:
  traceFile = sys.argv[1]
# def simulate(init, mid, singleSession): # input the pandas dataframe
# for i in range(500,1000,500):
hbconfig = [2000,5000,10000,15000,20000]
# for i in range(1000,20500,1000):
# for i in range(len(hbconfig)):
debugcount = 0
debugcountP = 0
debugcountN = 0
if DATABRICKS_MODE:
  singleSession[['timestampms', 'bandwidth']] = singleSession[['timestampms', 'bandwidth']].astype(int)
  sessionwise = singleSession.groupby(['clientid','clientsessionid'])

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
maxQoE = -sys.maxint
optimal_A = 0
optimal_bitrate = 0
optimal_rebuf = 0
optimal_domBR = 0
AVG_SESSION_BITRATE = 0
upr_end = 0
A_end = 0
allPerf = collections.OrderedDict()
if BUFFERLEN_UTILITY == False:
  upr_end = 0.271
else:
  upr_end = 1.0
if BUFFERLEN_BBA1_UTILITY == True or BUFFERLEN_BBA2_UTILITY == True:
  A_end = 0.02
else:
  A_end = 1.01
# for name1, group1 in sessionwise:
# uncomment the line below if running for Hybrid ABR
for upr in range(-1000, -1100, -500):
# comment the line below if running for Hybrid ABR
#for upr in np.arange(0.27, upr_end, 0.05):
  #allPerf = collections.OrderedDict()
  # uncomment the line below if running for Hybrid ABR
  for A in np.arange(0.25,0.251,0.01):
  # comment the line below if running for Hybrid ABR
  #for A in np.arange(1,int(upr * conf['maxbuflen']) - 31,1):
    if DEBUG:
      printHeader()
    bwMap = dict()
    sizeDict = dict()
    usedBWArray = []
    bitratesPlayed = dict()
    nSamples = collections.deque(5*[0],5)
    hbCount = 0
    BSM = -1.0
    time_residue = 0.0
    blen_decrease = False
    BLEN, CHUNKS_DOWNLOADED, BUFFTIME, PLAYTIME, CLOCK, INIT_HB, MID_HB, BR, BW, AVG_SESSION_BITRATE, SWITCH_LOCK, SIMULATION_STEP = initSysState()
    if DATABRICKS_MODE:
      group2 = group1.sort("timestampms")
      candidateBR, jointime, playtimems, sessiontimems, bitrate_groundtruth, bufftimems, BR, bwArray, CHUNKSIZE, TOTAL_CHUNKS = parseSessionState(group2)
    elif TRACE_MODE:
      candidateBR, jointime, playtimems, sessiontimems, bitrate_groundtruth, bufftimems, BR, bwArray, CHUNKSIZE, TOTAL_CHUNKS = parseSessionStateFromTrace(traceFile)    
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

    BLEN, CHUNKS_DOWNLOADED, CLOCK, chunk_residue, first_chunk = bootstrapSim(jointime, BW, BR, CHUNKSIZE)
    oldBR = BR  
    buffering = False
    sessionFullyDownloaded = False
    numSwitches = 0
    dominantBitrate = dict()
    timeSinceLastDecision = 0
    # set the simulation interval to be the simulation step size, as defined in config.py
    interval = SIMULATION_STEP

  #   BW = getInitBW(BR, CLOCK, CHUNKSIZE) # if want to calculate using the jointimems

    # run the clock till the sessiontime
    while CLOCK < sessiontimems: 
      # reset variables which are specific to an interval
      playStalled_thisInterval = 0
      chd_thisInterval = 0
      blenAdded_thisInterval = 0

      if VERBOSE_DEBUG == True or DEBUG == True and timeSinceLastDecision == 0:
	printStats(CLOCK, BW, BLEN, BR, oldBR, CHUNKS_DOWNLOADED, BUFFTIME, PLAYTIME)
	
      if CHUNKS_DOWNLOADED * CHUNKSIZE * 1000 < 30000:
	decision_cycle = INIT_HB
      elif CHUNKS_DOWNLOADED * CHUNKSIZE * 1000 >= 30000:
	decision_cycle = MID_HB 

      # if this is the last interval we must not over-calculate it
      if CLOCK + interval > sessiontimems:
        interval = sessiontimems - CLOCK

      # increment the time since last decision by the simulation step size
      timeSinceLastDecision += interval
      #print timeSinceLastDecision, decision_cycle

      # incrementing the clock to jump to the next step
      CLOCK += interval       
      if SWITCH_LOCK > 0:
	SWITCH_LOCK -= interval/float(1000) # add float 

      if BLEN > 0:
	buffering = False

      # first take care of the non-conditional events ####################################################################################################
      if buffering and not sessionFullyDownloaded:
	playStalled_thisInterval = min(timeToDownloadSingleChunk(CHUNKSIZE, BR, BW, chunk_residue, CHUNKS_DOWNLOADED), interval/float(1000)) # add float
	if playStalled_thisInterval < interval/float(1000): # chunk download so resume
	  buffering = False

      if not sessionFullyDownloaded:
	numChunks, completionTimeStamps, time_residue = chunksDownloaded(CLOCK - interval, CLOCK, BR, BW, CHUNKS_DOWNLOADED, CHUNKSIZE, chunk_residue, usedBWArray,bwArray, time_residue)
	#print time_residue
        chd_thisInterval = chunk_residue + numChunks
        if playStalled_thisInterval == interval/float(1000) and chd_thisInterval >= 1.0:
          buffering = False

	chunk_residue = chd_thisInterval - int(chd_thisInterval)
	if BLEN + chd_thisInterval * CHUNKSIZE >= MAX_BUFFLEN: # can't download more than the MAX_BUFFLEN
	  chd_thisInterval = int(MAX_BUFFLEN - BLEN)/CHUNKSIZE
	  chunk_residue = 0
      
      # can't download more chunks than the total playtime of the session.
      if CHUNKS_DOWNLOADED + int(chd_thisInterval) >=  math.ceil((playtimems)/float(CHUNKSIZE * 1000)):
	chd_thisInterval = math.ceil((playtimems)/float(CHUNKSIZE * 1000)) - CHUNKS_DOWNLOADED
	
      # only append fully downloaded chunks                       
      CHUNKS_DOWNLOADED += int(chd_thisInterval)
      
      # updatet the dictionary with count of bitrates played 
      if BR in dominantBitrate:
	dominantBitrate[BR] += int(chd_thisInterval)
      else:
	dominantBitrate[BR] = int(chd_thisInterval)

      if first_chunk and CHUNKS_DOWNLOADED >= 1:
	first_chunk = False
      blenAdded_thisInterval =  int(chd_thisInterval) * CHUNKSIZE

      # as long as the session has not finished downloading continue to update the average bitrate
      if CHUNKS_DOWNLOADED <= math.ceil((playtimems)/float(CHUNKSIZE * 1000)) and not sessionFullyDownloaded: # check the equal to sign in less than equal to
	AVG_SESSION_BITRATE += int(chd_thisInterval) * BR * CHUNKSIZE

      # if all the chunks in the sessions have been downloaded, mark the session complete
      if CHUNKS_DOWNLOADED >= TOTAL_CHUNKS or CHUNKS_DOWNLOADED >= math.ceil((playtimems)/float(CHUNKSIZE * 1000)): 
	sessionFullyDownloaded = True

      # this condition checks if we got in buffering during this interval
      if not buffering and BLEN >= 0 and BLEN + blenAdded_thisInterval < interval/float(1000) and not sessionFullyDownloaded:
	playStalled_thisInterval += (interval/float(1000) - BLEN - blenAdded_thisInterval) # add float
	buffering = True

      # update the buffering time and playtime accumulated during this interval
      BUFFTIME += playStalled_thisInterval
      PLAYTIME += interval/float(1000) - playStalled_thisInterval # add float
      lastBlen = BLEN

      # update the bufferlen at the end of this interval
      if buffering:
	BLEN = 0
      elif not buffering and first_chunk and CHUNKS_DOWNLOADED == 0:
        BLEN = max(0, BLEN  - interval/float(1000))
      else:
	BLEN = max(0, CHUNKS_DOWNLOADED * CHUNKSIZE - PLAYTIME) # else update the bufferlen to take into account the current time step

      # check if the BLEN starts to decrease for the first time
      if lastBlen > BLEN and blen_decrease == False and CHUNKS_DOWNLOADED > 1:
        blen_decrease = True
      ####################################################################################################################################################

      # then take care of the conditional events #########################################################################################################
      
      BSM = A
      #conf['r'] = A
      #conf['maxRPct'] = upr
      # get Dynamic BSM
      if DYNAMIC_BSM:
	BSM = getDynamicBSM(nSamples, hbCount, BSM)
      # get the bitrate decision for the next interval
      oldBR = BR
      if not first_chunk and not sessionFullyDownloaded and timeSinceLastDecision == decision_cycle:
        #print "makeing decision at: " + str(CLOCK)
	if UTILITY_BITRATE_SELECTION:
          buffering_weight = upr
	  newBR = getUtilityBitrateDecision(BLEN, candidateBR, BW, CHUNKS_DOWNLOADED, CHUNKSIZE, BSM, buffering_weight)
	elif BUFFERLEN_UTILITY:
          conf['r'] = A
          conf['maxRPct'] = upr
	  newBR = getBitrateBBA0(BLEN, candidateBR, conf)
        elif BUFFERLEN_BBA1_UTILITY:
          newBR = getBitrateBBA1(BLEN, candidateBR, conf, CHUNKS_DOWNLOADED, CHUNKSIZE, BR, BW)
        elif BUFFERLEN_BBA2_UTILITY:
          newBR = getBitrateBBA2(BLEN, candidateBR, conf, CHUNKS_DOWNLOADED, CHUNKSIZE, BR, BW, blen_decrease)
	elif BANDWIDTH_UTILITY:
	  newBR = getBitrateDecisionBandwidth(BLEN, candidateBR, BW)
	elif WEIGHTED_BANDWIDTH:
	  newBR = getBitrateWeightedBandwidth(candidateBR, BW, nSamples, 0.35) # last parameter is the weight
	else:
	  newBR = getBitrateDecision(BLEN, candidateBR, BW)
      else:
	newBR = BR

      # reset timeSinceLastDecision
      if timeSinceLastDecision == decision_cycle:
        timeSinceLastDecision = 0
      # make the switch if switching up and no switch lock is active or switching down
      if (newBR > BR and SWITCH_LOCK <= 0) or newBR < BR:
	# activate switch lock if we have switched down      
	if newBR < BR:
	  SWITCH_LOCK = LOCK
	BR = newBR
	# throw away the partially downloaded chunk if a switch is recommended
	chunk_residue = 0         
	
      # count number of switches
      if not first_chunk and not sessionFullyDownloaded and oldBR != BR:
	numSwitches += 1

      nSamples.append(BW)
      if PS_STYLE_BANDWIDTH:
	BW = interpolateBWPrecisionServerStyle(CLOCK, BLEN, usedBWArray)
      else:
	BW = max(interpolateBWInterval(CLOCK, usedBWArray, bwArray),0.01) # interpolate bandwidth for the next heartbeat interval
      usedBWArray.append(BW) # save the bandwidth used in the session
      hbCount += 1

####################################################################################################################################################

    # print status after finishing
    if DEBUG:
      printStats(CLOCK, BW, BLEN, BR, oldBR, CHUNKS_DOWNLOADED, BUFFTIME, PLAYTIME)

    if BLEN > 0:
      PLAYTIME += BLEN
    # if sessions has bad bandwidth info, just omit it
    #if 0.01 in usedBWArray:
    #  continue

    # generate the statistics for the session ########################################################################################################
    NUM_SESSIONS += 1
    AVG_SESSION_BITRATE, REBUF_RATIO, rebuf_groundtruth = generateStats(AVG_SESSION_BITRATE, BUFFTIME, PLAYTIME, bufftimems, playtimems)
    avgbw, stdbw = getBWStdDev(bwArray)
    avgbwSessions.append(avgbw)
    stdbwSessions.append(stdbw)
    avgbitratePrecision.append(AVG_SESSION_BITRATE)
    rebufPrecision.append(REBUF_RATIO)
    avgbitrateGroundTruth.append(bitrate_groundtruth)
    rebufGroundTruth.append(rebuf_groundtruth)
    # QoE calculation done as a weighted average of Avg. bitrate, Rebuf. ratio and Num. Switches
    QoE = AVG_SESSION_BITRATE - 3000 * BUFFTIME / (BUFFTIME + PLAYTIME) #- 10 * numSwitches

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
      print "Number of switches in the session = " + str(numSwitches)
      print "Value of A = " + str(A) + " QoE of sessions is: " + str(QoE)

    allPerf[str(upr) + " " + str(A)] = str(AVG_SESSION_BITRATE) + " " + str(REBUF_RATIO)
    # if new QoE is 10% greater than the previous max, then update it
    #if maxQoE + abs(0.1 * maxQoE) < QoE:
    if maxQoE < QoE:
      maxQoE = QoE
      optimal_A = A
      optimal_bitrate = AVG_SESSION_BITRATE
      optimal_rebuf = REBUF_RATIO
      #optimal_domBR = domBR
      #optimal_freq = freq

#print "Max overall QoE = " + str(maxQoE) + " for A = " + str(optimal_A)
if maxQoE == -sys.maxint:
  print "#"
else:
  domBR, freq, totalFreq = getDominant(dominantBitrate)
  print traceFile + " QoE: " + str(maxQoE) + " avg. bitrate: " + str(optimal_bitrate) +  " buf. ratio: " + str(optimal_rebuf) + " optimal A: " + str(optimal_A) + " mapping: " + str(allPerf) + " dominant bitrate: " + str(dominantBitrate) 
#+ " numSwitches: " + str(numSwitches) + " dominant BR: " + str(domBR) + " played " + str(freq) + " out of " + str(totalFreq) + " optimal A: " + str(optimal_A) + " PLAYTIME: " + str(PLAYTIME) + " BUFFTIME: " + str(BUFFTIME) +  " CHUNKS: " + str(CHUNKS_DOWNLOADED)
#  print allPerf 
#   print "Total Session: " + str(NUM_SESSIONS)
#   print "Total debugP: " + str(debugcountP)
#   print "Total debugN: " + str(debugcountN)

#   printPercentile(avgbitratePrecision) 
#   print str(50) + "\t" + str(np.percentile(avgbitratePrecision, 50))+ "\t" + str(np.percentile(avgbitrateGroundTruth, 50)) + "\t" + str(95) + "\t" + str(np.percentile(avgbitratePrecision, 95))+ "\t" + str(np.percentile(avgbitrateGroundTruth, 95)) + "\t" + str(50) + "\t" + str(np.percentile(rebufPrecision, 50)) + "\t" + str(np.percentile(rebufGroundTruth, 50)) + "\t" + str(95) + "\t" + str(np.percentile(rebufPrecision, 95)) + "\t" + str(np.percentile(rebufGroundTruth, 95))
# print five number summaries
# print str(i)+ "\t" + str(i/500)+ "\t" + str(np.percentile(avgbitratePrecision, 5))+ "\t" + str(np.percentile(avgbitratePrecision, 25))+ "\t" + str(np.percentile(avgbitratePrecision, 50))+ "\t" + str(np.percentile(avgbitratePrecision, 75))+ "\t" + str(np.percentile(avgbitratePrecision, 95))+ "\t" + str(np.percentile(rebufPrecision, 5)) + "\t" + str(np.percentile(rebufPrecision, 25)) + "\t" + str(np.percentile(rebufPrecision, 50)) + "\t" + str(np.percentile(rebufPrecision, 75)) + "\t" + str(np.percentile(rebufPrecision, 95))+ "\t" + str(np.percentile(rebufPrecision, 99))

#   print str(i)+ "\t" + str(i/500)+ "\t" + str(np.percentile(avgbitratePrecision, 50))+ "\t" + str(np.percentile(avgbitrateGroundTruth, 50))+ "\t" + str(np.percentile(avgbitratePrecision, 50))+ "\t" + str(np.percentile(avgbitratePrecision, 95))+ "\t" + str(np.percentile(avgbitrateGroundTruth, 95))+ "\t" + str(np.percentile(rebufPrecision, 50)) + "\t" + str(np.percentile(rebufGroundTruth, 50)) + "\t" + str(np.percentile(rebufPrecision, 95)) + "\t" + str(np.percentile(rebufGroundTruth, 95)) + "\t" + str(np.percentile(rebufPrecision, 99))+ "\t" + str(np.percentile(rebufGroundTruth, 99))

