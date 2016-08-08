#!/usr/bin/python

import default
import sys, getopt
from optparse import OptionParser, OptionGroup,  TitledHelpFormatter

class parseinput(object):

  def __init__(self):

    parser = OptionParser(usage="%core.py <inputfile> [OPTIONS]", version="%prog 1.0", epilog="For bugs and suggestions, email: zakhtar@usc.edu", formatter=TitledHelpFormatter())
    parser.add_option("-d", "--debug", action="store_true", dest="debug", help="debugging output, prints state once every decision")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="verbose debugging output, prints state once every simulation step")
    group = OptionGroup(parser, "Player config:")
    group.add_option("-b", "--max-buflen", type=int, dest="max_buflen", metavar="INT", help="maximum playback buffer length in sec")
    group.add_option("-l", "--switch-lock", type=int, dest="switch_lock", metavar="INT", help="duration of lock on switch up decision in sec")
    group.add_option("-j", "--join-buffsize", type=float, dest="join_buffsize", metavar="FLOAT", help="bufferlength at jointime in sec")    
    parser.add_option_group(group)
    group = OptionGroup(parser, "Stream config:")
    group.add_option("-s", "--chunksize", type=int, dest="chunksize", metavar="INT", help="size of chunk in sec")
    group.add_option("-r", "--init-bitrate", type=int, dest="init_bitrate", metavar="INT", help="initial bitrate")
    parser.add_option_group(group)
    group = OptionGroup(parser, "Simulation config:")
    group.add_option("-I", "--simstep", type=int, dest="simstep", metavar="INT", help="simulation step size in msec")
    group.add_option("-n", "--init-stream-chunks", type=int, dest="init_stream_chunks", metavar="INT", help="duration of initial stream in number of chunks")
    group.add_option("-x", "--init-decision-freq", type=int, dest="init_hb", metavar="INT", help="duration of decision interval in initial stream in msec")
    group.add_option("-y", "--mid-decision-freq", type=int, dest="mid_hb", metavar="INT", help="duration of decision interval in middle stream in msec")
    group.add_option("-m", "--use-chunk-map", action="store_true", dest="use_chunk_map", help="enable simulation to use a chunkmap provided as a dictionary named \"sizeDict\"")
    parser.add_option_group(group)
    group = OptionGroup(parser, "ABR algo config:")
    group.add_option("-U", "--utility-abr", action="store_true", dest="utility", help="use utility based ABR to make bitrate decisions")
    group.add_option("-B", "--buffer-abr", action="store_true", dest="buffer", help="use buffer based ABR to make bitrate decisions")
    group.add_option("-R", "--xput-abr", action="store_true", dest="rate", help="use rate based ABR to make bitrate decisions")    
    parser.add_option_group(group)
    (options, args) = parser.parse_args()

    if len(args) != 1:
      parser.error("input tracefile not provided, to get help please run: python abrsim.py -h")

    self.debug = self.getConfigVar(default.DEBUG, options.debug)
    self.verbose = self.getConfigVar(default.VERBOSE_DEBUG, options.verbose)
    self.max_buflen = self.getConfigVar(default.MAX_BUFLEN, options.max_buflen)
    self.switch_lock = self.getConfigVar(default.SWITCH_LOCK, options.switch_lock)
    self.chunksize = self.getConfigVar(default.CHUNKSIZE, options.chunksize)
    self.bitrate = self.getConfigVar(default.INIT_BR, options.init_bitrate)
    self.old_bitrate = self.bitrate
    self.simstep = self.getConfigVar(default.SIMULATION_STEP, options.simstep)
    self.init_stream = self.getConfigVar(default.INIT_STREAM, options.init_stream_chunks)
    self.init_hb = self.getConfigVar(default.INIT_HB, options.init_hb)
    self.mid_hb = self.getConfigVar(default.MID_HB, options.mid_hb)
    self.use_chunk_map = self.getConfigVar(default.CHUNK_AWARE_MODE, options.use_chunk_map)
    self.join_buffsize = self.getConfigVar(default.JOIN_BUFFSIZE, options.join_buffsize)
    self.abr = self.getCaseBasedConfigVar({'utility' : default.UTILITY_ABR, 'buffer' : default.BUFFER_ABR, 'rate' : default.RATE_ABR}, \
        {'utility' : options.utility, 'buffer' : options.buffer, 'rate' : options.rate})
    self.MSEC_IN_SEC = default.MSEC_IN_SEC
    self.tracefile = args[0]
    self.candidates = default.CANDIDATES
    self.jointime = default.JOINTIME
    # self.utility_abr = default.UTILITY_ABR


  def getConfigVar(self, default, user_opt):
    if user_opt is not None:
      return user_opt
    return default

  def getCaseBasedConfigVar(self, default_dict, user_opt_dict):
    if default_dict.values().count(True) > 1 or user_opt_dict.values().count(True) > 1:
        parse.error("can not select more than one ABR algorithm...")

    if user_opt_dict.values().count(True) == 0:
        return default_dict.keys()[default_dict.values().index(True)]

    return user_opt_dict.keys()[user_opt_dict.values().index(True)]




