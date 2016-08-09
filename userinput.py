#!/usr/bin/python

import default
import sys, getopt
from optparse import OptionParser, OptionGroup, HelpFormatter

try:
    from gettext import gettext
except ImportError:
    def gettext(message):
        return message
_ = gettext


class parseinput(object):

  def __init__(self):

    parser = OptionParser(usage="%core.py <inputfile> [OPTIONS]", version="%prog 1.0", epilog="For bugs and suggestions, email: zakhtar@usc.edu", formatter=MyTitledHelpFormatter())
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
    group.add_option("-A", "--abr", action="store", dest="abr", type="choice", choices=['utility', 'buffer', 'rate'], help="choose ABR from 'utility', 'buffer' or 'rate', without quotes")
    group.add_option("-B", "--bsm", dest="bsm", type=float, metavar="FLOAT", help="bandwidth safety margin for utility ABR")
    group.add_option("-W", "--bwsm", dest="bwsm", type=float, metavar="FLOAT", help="bandwidth safety margin for utility ABR")
    group.add_option("-L", "--lower-res", dest="lower_res", type=int, metavar="INT", help="lower reservoir for buffer based ABR")
    group.add_option("-U", "--upper-res", dest="upper_res", type=float, metavar="FLOAT", help="upper reservoir for buffer based ABR as percentage of max_buflen")
    parser.add_option_group(group)
    (options, args) = parser.parse_args()

    if len(args) != 1:
      parser.error("input tracefile not provided, to get help please run: python abrsim.py -h")

    try:
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
        self.abr = self.getChoiceConfigVar({'utility' : default.UTILITY_ABR, 'buffer' : default.BUFFER_ABR, 'rate' : default.RATE_ABR}, options.abr, parser)
        self.bsm = self.getConfigVar(default.BUFFER_MARGIN, options.bsm)
        self.bwsm = self.getConfigVar(default.BANDWIDTH_MARGIN, options.bwsm)
        self.lower_res = self.getConfigVar(default.LOWER_RESERVOIR, options.lower_res)
        self.upper_res = self.getConfigVar(default.UPPER_RESERVOIR, options.upper_res)
        self.MSEC_IN_SEC = default.MSEC_IN_SEC
        self.tracefile = args[0]
        self.candidates = default.CANDIDATES
        self.jointime = default.JOINTIME
    except AttributeError, e:
        parser.error("missing default value for: " + str(e))


  def getConfigVar(self, default, user_opt):
    if user_opt is not None:
      return user_opt
    return default

  def getChoiceConfigVar(self, default_dict, user_opt, parser):
    if default_dict.values().count(True) > 1:
        parser.error("can not select more than one choices as default: " + str(default_dict))

    if user_opt is not None:
        return user_opt

    return default_dict.keys()[default_dict.values().index(True)]


class MyTitledHelpFormatter (HelpFormatter):
    """Format help with underlined section headers.
    """

    def __init__(self,
                 indent_increment=1,
                 max_help_position=48,
                 width=200,
                 short_first=1):
        HelpFormatter.__init__ (
            self, indent_increment, max_help_position, width, short_first)

    def format_usage(self, usage):
        return "%s  %s\n" % (self.format_heading(_("Usage")), usage)

    def format_heading(self, heading):
        return "%s\n%s\n" % (heading, "=-"[self.level] * len(heading))


