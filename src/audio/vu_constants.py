"""
https://github.com/kmein/vu-meter


.gitignore          NOT INSTALLED
LICENSE             NOT INSTALLED
README.md           NOT INSTALLED
amplitude.py
record.py           NOT INSTALLED
vu_constants.py                         THIS MODULE
vu_meter.py
"""

RATE = 44100
INPUT_BLOCK_TIME = 0.05
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
SHORT_NORMALIZE = 1.0 / 32768.0
VU_METER_FNAME  = "/run/user/1000/mserve.vu-meter.txt"
