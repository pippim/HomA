#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Author: Pippim
License: GNU GPLv3
Source: This repository
Description: mserve - Music Server - VU Meter processor spawned by mserve.py
WARNING: Do not shorten or lengthen description! It is used in Python Dashboard
         and will break mserve_config.py that feeds /website/programs/mserve.md
"""

from __future__ import print_function  # Must be first import
from __future__ import with_statement  # Error handling for file opens

#==============================================================================
#
#       vu_meter.py - Listen to microphone left/right and generate vu levels
#
#       July 02 2023 - Temporary filenames suitable for Windows and Mac.
#       July 12 2023 - Modify import order for mserve_config.py
#       June 14 2025 - Support HomA appname. Create BASELINE_RESET untested 100
#
#==============================================================================
# noinspection SpellCheckingInspection
"""

IMPORTANT: Use pavucontrol to create loopback from sound output to microphone:
           https://wiki.ubuntu.com/record_system_sound


CREDIT for VU Meter coding: https://github.com/kmein/vu-meter  The GitHub
modules in "kmein/vu-meter", listed below, were combined into `vu-meter.py`:

.gitignore          NOT INSTALLED
LICENSE             NOT INSTALLED
README.md           NOT INSTALLED
amplitude.py                        THIS MODULE
record.py           NOT INSTALLED
vu_constants.py                     THIS MODULE
vu_meter.py                         THIS MODULE

ENHANCEMENTS:

    1) Support Python environment variable for automatic python 2 / 3 selection
    2) Add UTF-8 to support Python 2 (not necessary in this program though)
    3) Reset maximal between songs (gap when 10 samples of zero strength)
    4) Remove console output and write values to ramdisk (/run/user/1000)
    5) Optional 'stereo' parameter to measure left & right channels
    6) Utilize numpy which is auto-installed on most Linux distros
    7) Include separate amplitude.py & vu_constants.py in vu_meter.py
    8) Remove unused functions from Amplitude class

"""

# Standard Python Library
import sys
import math
import struct

# dist-packages
import pyaudio
import numpy as np  # January 24, 2021 support Left & Right channels

appname = 'mserve'
if (len(sys.argv)) >= 3:  # 2025-06-14 Can be 2 parameters now
    appname = sys.argv[2]  # Null = 'mserve'. Alternatively 'homa'.

# Pippim modules
import global_variables as g  # Needed for IPC filenames directory
g.init(appname=appname)  # Always have to run because this is a spawned job

RATE = 44100
INPUT_BLOCK_TIME = 0.05
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
SHORT_NORMALIZE = 1.0 / 32768.0
BASELINE_RESET = 10  # How much silence to reset peek
# 2025-06-21 BASELINE_RESET was 10 set 100. Have no idea if this if 5 seconds or not?
# 2025-06-22 Change BASELINE_RESET back to 10 for now...

''' Volume Meter IPC filenames. Repeat changes in mserve.py, homa.py & toolkit.py '''
# Mono output
AMPLITUDE_MONO_FNAME = g.TEMP_DIR + appname + "_vu-meter-mono.txt"
# Stereo output (Left and Right)
AMPLITUDE_LEFT_FNAME = g.TEMP_DIR + appname + "_vu-meter-left.txt"
AMPLITUDE_RIGHT_FNAME = g.TEMP_DIR + appname + "_vu-meter-right.txt"


class Amplitude(object):
    """ an abstraction for Amplitudes (with an underlying float value)
    that packages a display function and many more
    
    January 25, 2021 - Remove unused add, sub, gt, eq, int & str functions
    """

    def __init__(self, value=0):
        self.value = value

    def __lt__(self, other):
        return self.value < other.value

    def to_int(self, scale=1):
        """ convert an amplitude to an integer given a scale such that one can
        choose the precision of the resulting integer """
        return int(self.value * scale)

    @staticmethod
    def from_data(block):
        """ generate an Amplitude object based on a block of audio input data """
        count = len(block) / 2
        shorts = struct.unpack("%dh" % count, block)
        sum_squares = sum(s**2 * SHORT_NORMALIZE**2 for s in shorts)
        # Expected int, got float error
        # noinspection PyTypeChecker
        return Amplitude(math.sqrt(sum_squares / count))

    def display(self, mark, scale=50, fn=AMPLITUDE_MONO_FNAME):
        """ display an amplitude and another (marked) maximal Amplitude
        graphically """
        int_val = self.to_int(scale)
        mark_val = mark.to_int(scale)
        # delta = abs(int_val - mark_val)
        # print(int_val * '*', (delta-1) * ' ', '|',mark_val,int_val,delta)
        # January 23, 2021: Write values to ramdisk instead of displaying
        with open(fn, "w") as vu_file:
            vu_file.write(str(mark_val) + " " + str(int_val))


def parse_data(data, channel_ndx, channel_cnt, maximal):
    """
        Process data from one channel
    """
    data = np.fromstring(data, dtype=np.int16)[channel_ndx::channel_cnt]
    data = data.tostring()
    amp = Amplitude.from_data(data)
    gap = amp.value      # For signal test below.
    if amp > maximal:
        maximal = amp
    return amp, maximal, gap


def main():
    """ mainline """

    # January 24, 2021 separate left and right channels
    parameter = 'mono'
    if (len(sys.argv)) >= 2:  # 2025-06-14 Can be 2 parameters now
        parameter = sys.argv[1]     # Null = 'mono', 'stereo' = Left & Right

    audio = pyaudio.PyAudio()
    reset_baseline_count = 0
    stream = None

    try:
        stream = audio.open(format=pyaudio.paInt16,
                            channels=2,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=INPUT_FRAMES_PER_BLOCK)

        maximal = Amplitude()
        maximal_l = maximal_r = maximal

        while True:
            data = stream.read(INPUT_FRAMES_PER_BLOCK)

            # January 24, 2021 separate left and right channels
            if parameter == 'stereo':
                amp = None
                amp_l, maximal_l, gap = parse_data(data, 0, 2, maximal_l)
                amp_r, maximal_r, gap = parse_data(data, 1, 2, maximal_r)
                if maximal_r < maximal_l:
                    # A momentary spike to left channel inherited by right
                    maximal_r = maximal_l
                if maximal_l < maximal_r:
                    # A momentary spike to right channel inherited by left
                    maximal_l = maximal_r
                # 2025-06-20 - gap isn't set for stereo?
            else:
                # Mono - processing all data
                amp_l = None
                amp_r = None
                amp = Amplitude.from_data(data)
                gap = amp.value      # For signal test below.
                if amp > maximal:
                    maximal = amp

            # New code January 23, to reset next song's maximal during gap
            if gap == 0.0:
                reset_baseline_count += 1
                if reset_baseline_count == BASELINE_RESET:
                    maximal = Amplitude()
                    maximal_l = maximal_r = maximal
                    # print('maximal reset', maximal.value)
            else:
                reset_baseline_count = 0

            # January 24, 2021 separate left and right channels
            if parameter == 'stereo':
                amp_l.display(scale=200, mark=maximal_l, fn=AMPLITUDE_LEFT_FNAME)
                amp_r.display(scale=200, mark=maximal_r, fn=AMPLITUDE_RIGHT_FNAME)
            else:
                # Mono processing one channel combined sound
                amp.display(scale=200, mark=maximal, fn=AMPLITUDE_MONO_FNAME)

    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


if __name__ == "__main__":
    main()

# End of vu_meter.py
