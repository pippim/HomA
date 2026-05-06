#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Author: Pippim
License: GNU GPLv3. (c) 2026
Source: This repository
Description: HomA - Home Automation - PulseAudio sink-input change listener
"""

from __future__ import print_function  # Must be first import
from __future__ import with_statement  # Error handling for file opens

#==============================================================================
#
#       pa_listen.py - PulseAudio sink-input change listener
#
#       2026-05-03 - Initial design based on pa_meter.py
#
#==============================================================================

# Standard Python Library
import sys

# dist-packages
import time

# 3rd party modules
import pulsectl

# Pippim modules
import global_variables as g  # Needed for IPC filenames directory

appname = 'ytads'
if (len(sys.argv)) >= 3:  # [0]='pa_listen.py', [1]='option', [2]='ytads'
    appname = sys.argv[2]
g.init(appname=appname)  # Call g.init() because this is a spawned job
fn = g.TEMP_DIR + appname + "_pa_listen.txt"
print("fn:", fn)


def PulseListener():
    """ listen for PulseAudio sink-input changes """

    def event_handler(ev):
        """ When a new sink-input (or change) happens, write timestamp """
        if ev.facility == 'sink_input':
            with open(fn, "w") as f:
                f.write(str(time.time()))
        else:
            print("non-'sink_input' Event received: {}".format(ev))

    # Initial file contents for caller to open file
    with open(fn, "w") as pa_file:
        pa_file.write(str(time.time()))

    # Set masks for what to listen to
    pulse = pulsectl.Pulse('tk-listener')
    pulse.event_mask_set('sink_input')
    pulse.event_callback_set(event_handler)
    pulse.event_listen()


if __name__ == "__main__":
    PulseListener()


# End of pa_listen.py
