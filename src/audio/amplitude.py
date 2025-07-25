from __future__ import print_function       # Must be first import
from __future__ import with_statement       # Error handling for file opens

"""
https://github.com/kmein/vu-meter


.gitignore          NOT INSTALLED
LICENSE             NOT INSTALLED
README.md           NOT INSTALLED
amplitude.py                         THIS MODULE
record.py           NOT INSTALLED
vu_constants.py
vu_meter.py
"""

''' This module introduces the Amplitude class which collects methods for
calculating, adding and displaying. '''


import math
import struct
from vu_constants import SHORT_NORMALIZE, VU_METER_FNAME

class Amplitude(object):
    ''' an abstraction for Amplitudes (with an underlying float value)
    that packages a display function and many more '''

    def __init__(self, value=0):
        self.value = value

    def __add__(self, other):
        return Amplitude(self.value + other.value)

    def __sub__(self, other):
        return Amplitude(self.value - other.value)

    def __gt__(self, other):
        return self.value > other.value

    def __lt__(self, other):
        return self.value < other.value

    def __eq__(self, other):
        return self.value == other.value

    def to_int(self, scale=1):
        ''' convert an amplitude to an integer given a scale such that one can
        choose the precision of the resulting integer '''
        return int(self.value * scale)

    def __int__(self):
        return self.to_int()

    def __str__(self):
        return self.value + " dB"

    @staticmethod
    def from_data(block):
        ''' generate an Amplitude object based on a block of audio input data '''
        count = len(block) / 2
        shorts = struct.unpack("%dh" % count, block)
        sum_squares = sum(s**2 * SHORT_NORMALIZE**2 for s in shorts)
        return Amplitude(math.sqrt(sum_squares / count))

    def display(self, mark, scale=50):
        ''' display an amplitude and another (marked) maximal Amplitude
        graphically '''
        int_val = self.to_int(scale)
        mark_val = mark.to_int(scale)
        delta = abs(int_val - mark_val)
        # print(int_val * '*', (delta-1) * ' ', '|',mark_val,int_val,delta)
        with open(VU_METER_FNAME, "w") as vufile:
            vufile.write(str(mark_val) + " " + str(int_val))

        
