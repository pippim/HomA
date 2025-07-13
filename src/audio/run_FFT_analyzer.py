# -*- coding: utf-8 -*-

"""
Stuff installed that should be reversed after project failure:

:~/python/audio$ cat /var/log/dpkg.log | grep " install "

2021-01-20 17:06:36 install libmikmod3:amd64 <none> 3.3.8-2
2021-01-20 17:06:36 install libsdl-mixer1.2:amd64 <none> 1.2.12-11build1
2021-01-20 17:06:36 install libsdl-ttf2.0-0:amd64 <none> 2.0.11-3
2021-01-20 17:06:37 install libsmpeg0:amd64 <none> 0.4.5+cvs20030824-7.1
2021-01-20 17:06:37 install libportmidi0:amd64 <none> 1:200-0ubuntu3
2021-01-20 17:06:37 install python-pygame:amd64 <none> 1.9.1release+dfsg-10
2021-01-21 04:39:40 install libportaudiocpp0:amd64 <none> 19+svn20140130-1build1
2021-01-21 04:41:09 install libjack0:amd64 <none> 1:0.124.1+20140122git5013bed0-3build2
2021-01-21 04:41:09 install libasound2-dev:amd64 <none> 1.1.0-0ubuntu1
2021-01-21 04:41:09 install uuid-dev:amd64 <none> 2.27.1-6ubuntu3.10
2021-01-21 04:41:10 install libjack-dev:amd64 <none> 1:0.124.1+20140122git5013bed0-3build2
2021-01-21 04:41:10 install portaudio19-dev:amd64 <none> 19+svn20140130-1build1
2021-01-21 05:25:39 install python-ply:all <none> 3.7-1
2021-01-21 05:25:40 install python-pycparser:all <none> 2.14+dfsg-2build1
2021-01-21 05:25:40 install python-cffi:all <none> 1.5.2-1ubuntu1

"""

import argparse
from src.stream_analyzer import Stream_Analyzer
import time

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', type=int, default=None, dest='device',
                        help='pyaudio (portaudio) device index')
    parser.add_argument('--height', type=int, default=450, dest='height',
                        help='height, in pixels, of the visualizer window')
    parser.add_argument('--n_frequency_bins', type=int, default=400, dest='frequency_bins',
                        help='The FFT features are grouped in bins')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--window_ratio', default='24/9', dest='window_ratio',
                        help='float ratio of the visualizer window. e.g. 24/9')
    parser.add_argument('--sleep_between_frames', dest='sleep_between_frames', action='store_true',
                        help='when true process sleeps between frames to reduce CPU usage (recommended for low update rates)')
    return parser.parse_args()

def convert_window_ratio(window_ratio):
    if '/' in window_ratio:
        dividend, divisor = window_ratio.split('/')
        try:
            float_ratio = float(dividend) / float(divisor)
        except:
            raise ValueError('window_ratio should be in the format: float/float')
        return float_ratio
    raise ValueError('window_ratio should be in the format: float/float')

def run_FFT_analyzer():
    args = parse_args()
    window_ratio = convert_window_ratio(args.window_ratio)

    ear = Stream_Analyzer(
                    device = args.device,        # Pyaudio (portaudio) device index, defaults to first mic input
                    rate   = None,               # Audio samplerate, None uses the default source settings
                    FFT_window_size_ms  = 60,    # Window size used for the FFT transform
                    updates_per_second  = 1000,  # How often to read the audio stream for new data
                    smoothing_length_ms = 50,    # Apply some temporal smoothing to reduce noisy features
                    n_frequency_bins = args.frequency_bins, # The FFT features are grouped in bins
                    visualize = 1,               # Visualize the FFT features with PyGame
                    verbose   = args.verbose,    # Print running statistics (latency, fps, ...)
                    height    = args.height,     # Height, in pixels, of the visualizer window,
                    window_ratio = window_ratio  # Float ratio of the visualizer window. e.g. 24/9
                    )

    fps = 60  #How often to update the FFT features + display
    last_update = time.time()
    while True:
        if (time.time() - last_update) > (1./fps):
            last_update = time.time()
            raw_fftx, raw_fft, binned_fftx, binned_fft = ear.get_audio_features()
        elif args.sleep_between_frames:
            time.sleep(((1./fps)-(time.time()-last_update)) * 0.99)

if __name__ == '__main__':
    run_FFT_analyzer()
