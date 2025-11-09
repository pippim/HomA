#!/usr/bin/python
# -*- coding: utf-8 -*-
# Line 1 Use: #!/usr/bin/python3 or #!/usr/bin/python2 or #!/usr/bin/python
# /usr/bin/env python  # puts name "python" into top, not "yt-skip.py"
"""
Author: pippim.com
License: GNU GPLv3. (c) 2024-2025
Source: This repository
Description: HomA - Home Automation - YouTube Ad Mute and Skip Python Module
"""

from __future__ import print_function  # Must be first import
from __future__ import with_statement  # Error handling for file opens
from __future__ import division  # integer division results in float
import warnings  # 'warnings' advises which methods aren't supported
warnings.filterwarnings("ignore", "ResourceWarning")  # PIL python 3 unclosed file

# ==============================================================================
#
#       yt-skip.py - YouTube Ad Mute and Skip
#
#       2025-07-18 - Copy homa.py and refactor code.
#       2025-08-10 - Test coordinates immediately outside Skip Button triangle.
#
# ==============================================================================

'''

    REQUIRES:
    
    python(3)-appdirs
    python(3)-xlib  # imported as Xlib.X
    python(3)-ttkwidgets  # Also stored as subdirectory in ~/HomA/ttkwidgets
    audio   # Stored as subdirectory in ~/HomA/audio 
    pulsectl   # Stored as subdirectory in ~/HomA/pulsectl 

    xdotool  # To minimize window
    wmctrl  # Get list of windows. To be removed in favour of Wnck

'''

''' check configuration. '''
import inspect
import os
#os.environ["SUDO_PROMPT"] = ""  # Remove prompt "[sudo] password for <USER>:"

try:
    filename = inspect.stack()[1][1]  # If there is a parent, it must be 'h'
    parent = os.path.basename(filename)
    if parent != 'h':
        print("yt-skip.py called by unrecognized:", parent)
        exit()
except IndexError:  # list index out of range
    ''' 'h' hasn't been run to get global variables or verify configuration '''
    #import mserve_config as m_cfg  # Differentiate from sql.Config as cfg

    caller = "homa.py"  # yt-skip.py has same profile as homa.py
    import global_variables as g
    g.init(appname="homa")
    g.HELP_URL = "https://www.pippim.com/programs/homa.html#"

import sys
PYTHON_VERSION = sys.version
# 3.5.2 (default, Sep 30 2024, 10:28:02)\n [GCC 5.4.0 20160609]  -- OR --
# 2.7.12 (default, Sep 30 2024, 14:00:27)\n [GCC 5.4.0 20160609]

try:  # Python 3
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.font as font
    import tkinter.filedialog as filedialog
    import tkinter.messagebox as messagebox
    import tkinter.simpledialog as simpledialog
    import tkinter.scrolledtext as scrolledtext
    import tkinter.colorchooser as colorchooser
    PYTHON_VER = "3"
except ImportError:  # Python 2
    import Tkinter as tk
    import ttk
    import tkFont as font
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox
    import tkSimpleDialog as simpledialog
    import ScrolledText as scrolledtext
    import tkColorChooser as colorchooser
    PYTHON_VER = "2"

from PIL import Image, ImageTk, ImageDraw, ImageFont

try:
    import subprocess32 as sp
    SUBPROCESS_VER = '32'
except ImportError:  # No module named subprocess32
    import subprocess as sp
    SUBPROCESS_VER = 'native'

import json  # For dictionary storage in external file
import time  # For now = time.time()
import signal  # Shutdown signals
import datetime as dt  # For dt.datetime.now().strftime('%I:%M %p')
from collections import namedtuple


try:
    reload(sys)  # June 25, 2023 - Without utf8 sys reload, os.popen() fails on OS
    sys.setdefaultencoding('utf8')  # filenames that contain unicode characters
except NameError:  # name 'reload' is not defined
    pass  # Python 3 already in unicode by default

pprint_installed = True  # Hope for the best
try:  # pprint (dictionary pretty print) is usually installed. But...
    import pprint
except ImportError:
    pprint_installed = False  # But expect the worst

# Pippim modules
import sql  # For color options - Lots of irrelevant mserve.py code though
import monitor  # Center window on current monitor supports multi-head rigs
import toolkit  # Various tkinter functions common to Pippim apps
import message  # message.showInfo()
import image as img  # Image processing. E.G. Create Taskbar icon
import timefmt as tmf  # text_duration.set(tmf.mm_ss(_dur))
import external as ext  # Call external functions, programs, etc.
from homa_common import DeviceCommonSelf, Globals, AudioControl
from homa_common import p_args, v0_print, v1_print, v2_print, v3_print


class Application(DeviceCommonSelf, tk.Toplevel):
    """ tkinter main application window
        Button bar: Minimize, Help, Close
    """

    def __init__(self, master=None):
        """ DeviceCommonSelf(): Variables used by all classes """
        DeviceCommonSelf.__init__(self, "Application().")  # Define self.who
        _who = "__init__():"

        self.isActive = True  # Set False when exiting or suspending
        self.requires = ['ps', 'grep', 'xdotool', 'wmctrl', 'notify-send',
                         'pyaudio.py', 'numpy.py']  # .py also checked in AudioControl
        self.installed = []
        self.checkDependencies(self.requires, self.installed)

        if not self.dependencies_installed:
            v0_print(self.printTime(), _who,
                     "Some Application() dependencies are not installed.")
            v0_print(self.requires)
            v0_print(self.installed)

        self.pav_count = 0  # How many times PulseAudio Sink-Inputs have changed
        self.audio = AudioControl()
        ''' TkDefaultFont changes default font everywhere except tk.Entry in Color Chooser '''
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=g.MON_FONT)
        self.text_font = font.nametofont("TkTextFont")  # tk.Entry fonts in Color Chooser
        self.text_font.configure(size=g.MON_FONT)

        self.last_refresh_time = time.time()  # Refresh idle loop last entered time
        self.last_vum_update = time.time()  # Faster than 32ms causes eye fatigue
        self.last_minute = "0"  # Check sunlight percentage every minute
        self.last_second = "0"  # Update YouTube progress every second
        self.last_sink_inputs = []  # Last Pulse Audio sinks

        # Button Bar button images
        self.img_minimize = img.tk_image("minimize.png", 26, 26)
        self.img_mag_glass = img.tk_image("mag_glass.png", 26, 26)  # Help
        self.img_close = img.tk_image("close.png", 26, 26)  # Big Red X

        ''' Toplevel window (self) '''
        tk.Toplevel.__init__(self, master)  # https://stackoverflow.com/a/24743235/6929343
        self.minsize(width=120, height=63)
        self.geometry('1200x700')
        self.configure(background="WhiteSmoke")
        self.rowconfigure(0, weight=1)  # Weight 1 = stretchable row
        self.columnconfigure(0, weight=1)  # Weight 1 = stretchable column

        self.app_title = "YouTube Ad Mute and Skip"  # Used to find window ID
        self.title(self.app_title)
        self.btn_frm = None  # Used by buildButtonBar(), can be hidden by edit_pref

        ''' ChildWindows() moves children with toplevel and keeps children on top '''
        self.win_grp = toolkit.ChildWindows(self, auto_raise=False)

        ''' Tooltips() - if --silent argument, then suppress error printing '''
        print_error = False if p_args.silent else True
        self.tt = toolkit.ToolTips(print_error=print_error)

        ''' Set program icon in taskbar. '''
        # char='YT' used in self.sendNotification() too.
        img.taskbar_icon(self, 64, 'green', 'white', 'red', char='YT')

        ''' Save Toplevel OS window ID for minimizing window '''
        self.buildButtonBar()  # Must be called after Tooltips defined
        self.update_idletasks()  # Make visible for wmctrl. Verified needed 2025-02-13
        #GLO["WINDOW_ID"] = getWindowID(self.app_title)  # Needs Work
        self.getWindowID(self.app_title)

        ''' When devices displayed show sensors button and vice versa. '''
        self.close_btn = None  # Close button on button bar to control tooltip
        self.main_help_id = "HelpNetworkDevices"  # Toggles to HelpSensors and HelpDevices

        self.main_frm = self.audio_frm = self.yt_sb = self.vum = None
        self.pa_sb = None
        self.mon = monitor.Monitors()  # To get Wnck Windows
        self.pi = toolkit.PointerInspector(None, mon=self.mon)  # To get color at coordinates
        self.ffplay_pid = self.ffplay_name = None
        # set name with `ps -ef | grep ffplay` returns: "PARAMETERS.../song name"
        self.asi = ()  # Active Sink-Input named tuple

        ''' frame - Holds scrollable text entry and button(s) '''
        self.main_frm = ttk.Frame(self, borderwidth=g.FRM_BRD_WID,
                                  padding=(2, 2, 2, 2), relief=tk.RIDGE)
        self.main_frm.grid(column=0, row=0, sticky=tk.NSEW)
        ha_font = (None, g.MON_FONT)  # ms_font = mserve, ha_font = HomA

        self.pa_sb = toolkit.CustomScrolledText(
            self.main_frm, state="normal", font=ha_font, borderwidth=15, relief=tk.FLAT)
        toolkit.scroll_defaults(self.pa_sb)  # Default tab stops are too wide
        self.pa_sb.config(tabs=("50", "100", "150"))
        self.pa_sb.grid(row=90, column=0, padx=3, pady=3, sticky=tk.NSEW)
        # 90 rows available before self.pa_sb and 10 rows available after
        self.main_frm.rowconfigure(90, weight=1)
        self.main_frm.columnconfigure(0, weight=1)

        # Tabs for self.pa_sb PulseAudio Sink-Inputs Scrolled Text
        tabs = ("75", "left", "170", "left", "400", "left")
        self.pa_sb.tag_config("pav_sb_indent", lmargin2=420)

        def reset_tabs(event):
            """ https://stackoverflow.com/a/46605414/6929343 """
            event.widget.configure(tabs=tabs)

        self.pa_sb.configure(tabs=tabs, wrap=tk.WORD)
        self.pa_sb.bind("<Configure>", reset_tabs)

        line = "Input\tCorked\tApplication\tWindow title\n"
        self.pa_sb.insert("end", line + "\n", "pav_sb_indent")

        # Display Audio. Rows 0 to 89 available in self
        if not self.audio.isWorking:
            self.showInfoMsg(self.app_title,
                             "PulseAudio isn't working or software is missing.")
            return

        ''' Create audio_frm for columns 1, 2, 3: labels, values, scrollbox '''
        self.audio_frm = ttk.Frame(self.main_frm, borderwidth=g.FRM_BRD_WID,
                                   padding=(2, 2, 2, 2), relief=tk.RIDGE)
        self.audio_frm.grid(column=0, row=0, sticky=tk.NSEW)
        self.audio_frm.grid_columnconfigure(1, minsize=g.MON_FONTSIZE*15, weight=1)
        self.audio_frm.grid_columnconfigure(2, minsize=600, weight=1)  # scrollbox

        # Status scrollbox Text widget in third column, spanning 9 rows
        self.yt_sb = toolkit.CustomScrolledText(
            self.audio_frm, state="normal", font=g.FONT,
            height=11, borderwidth=15, relief=tk.FLAT)
        self.yt_sb.grid(row=0, column=2, rowspan=9, padx=3, pady=3, sticky=tk.NSEW)
        toolkit.scroll_defaults(self.yt_sb)  # Default tab stops are too wide
        _tabs2 = ("140", "right", "160", "left")  # Time right just, message left just
        self.yt_sb.configure(tabs=_tabs2, wrap=tk.WORD)  # Wrap long messages on word
        self.yt_sb.tag_config("audio_sb_indent", lmargin2=180)  # wrapped lines hanging indent

        def _reset_tabs2(event):
            """ https://stackoverflow.com/a/46605414/6929343 """
            event.widget.configure(tabs=_tabs2)

        self.yt_sb.bind("<Configure>", _reset_tabs2)

        _sb2_text = "INSTRUCTIONS:\n\n"
        _sb2_text += "1. Messages automatically scroll when videos start.\n\n"
        _sb2_text += '2. Messages can be copied by highlighting text and\n'
        _sb2_text += '     typing <Control> + "C".\n\n'
        _sb2_text += "3. Click Help button below for more instructions.\n\n"
        self.yt_sb_last_time = self.print_last_time = self.spam_last_time = \
            "00:00:00.00"  # Last time for suppressing duplicate HH:MM:SS
        self.insertYtSB(_sb2_text)

        self.update_idletasks()

        # Label / Value pairs in first and second column spanning 9 rows.
        self.text_index = self.addRow(0, "Sink input #:", "N/A")  # Long Integer
        self.text_pid = self.addRow(1, "Process ID (PID):", 0, _type="Int")
        self.text_pa_app = self.addRow(2, "PulseAudio App:", "N/A")
        self.text_is_YouTube = self.addRow(3, "YouTube?:", "N/A")
        self.text_wn_xid_hex = self.addRow(4, "Window number:", "N/A")
        self.text_is_fullscreen = self.addRow(5, "Fullscreen?:", "N/A")
        self.text_yt_start = self.addRow(6, "YouTube Start:", "N/A")
        self.text_status = self.addRow(7, "Status:", "N/A")
        self.text_duration = self.addRow(8, "Duration:", "N/A")

        ''' Create vum_frm for vu meters in fourth and fifth columns '''
        self.vum_frm = ttk.Frame(self.main_frm, borderwidth=g.FRM_BRD_WID,
                                 padding=(2, 2, 2, 2), relief=tk.RIDGE)
        self.vum_frm.grid(column=3, row=0, rowspan=99, sticky=tk.NSEW)
        self.vum_frm.grid_rowconfigure(0, weight=1)
        self.vum = toolkit.VolumeMeters('yt-skip', self.vum_frm)
        self.vum.reset_history_size(12)  # 2025-07-20 Change 8 to 12.
        self.vum.spawn()  # Daemon records Amplitude in temporary files
        self.update()  # paint meters for set_height() to calculate rectangles
        self.vum.set_height()  # Set initial height for VU meters

        _start = time.time()  # Wait up to 3 seconds for vu_meter.py startup
        while not os.path.isfile(self.vum.AMPLITUDE_LEFT_FNAME):
            self.refreshApp()  # wait another 16ms to 33ms for file to appear.
            if time.time() > _start + 3.0:
                self.showInfoMsg(self.app_title,
                                 "Daemon vu_meter.py did not start.")
                return

        # self.vars {} dictionary reduces number of class attributes
        # 2025-08-18 Start converting dictionary variables to attributes 
        self.vars = {  # pav_ = Pulse audio volume, wn_ = Wnck Window (GNOME)
            "pav_start": 0.0, "pav_index": 0, "pav_volume": 0.0,
            # 2025-09-28 - When using Python 3 get error:
            #   File "./yt-skip.py", line 311
            #     "pav_start": 0.0, "pav_index": 0L, "pav_volume": 0.0,
            #                                     ^
            # SyntaxError: invalid syntax
            "pav_corked": False, "pav_application": "", "pav_name": "",
            "wn_name": "", "wn_xid_hex": ""  # Could be YT or not YT
        }

        ''' 2025-08-18 PROBLEM self.vars dictionary takes .2 seconds to update 
                between calls to waitAdOrVideo(). E.G.:
                
                    self.vars["ad_start"] = time.time()
                    self.vars["av_start"] = 0.0
                    self.vars["video_start"] = 0.0  # 2025-07-15 Extra insurance

            Change to:
                    self.ad_start
                    self.av_start
                    self.video_start 

            2025-09-07 NOTE: still getting two hits for Ad and Video Playing
        
        '''
        self.yt_start = 0.0  # time YouTube video name first encountered
        self.ad_start = 0.0  # time yellow ad progress bar first detected
        self.av_start = 0.0  # time red video progress bar first detected
        self.video_start = 0.0  # time red video progress bar check started
        self.video_ended = 0.0  # time video sink-input window disappeared
        self.pause_start = 0.0  # 2025-10-25 time video was paused
        self.skip_btn_start = 0.0  # time Ad Skip Button check started
        self.skip_clicked = 0.0  # time Ad skip button clicked (sometimes ignored)
        self.last_grab_time = 0.0  # screen grabs limited to 10 / second.
        self.last_grab_inside = None
        self.last_grab_outside = None
        self.last_name = ""  # Last YouTube video name encountered
        self.last_corked_and_dropped = False
        self.last_index = 0

        self.spam_time = 0.0  # Spam reprinting on the same console line.
        self.spam_count = 0  # Vars set in self.printSpam() and self.resetSpam()

        self.this_stat = os.stat(glo.config_fname)  # Monitor homa.py saving
        self.last_stat = self.this_stat  # changes to configuration file

        self.blacklist = []  # Blacklisted PulseAudio sink-inputs

        if not self.checkPreferences():
            self.exitApp()
            return  # Test by making invalid color code > hex f or coordinate > 50000

        self.loopForever()  # Loop until exit

    def checkPreferences(self):
        """ Check GLO dictionary for colors and coordinates """
        _who = "checkPreferences():"
        _isHex = True  # Contains valid hex color string of "#a1b2c3"
        _isPoint = True  # Valid coordinates > 0 and < 50,000
        _hasAd = True
        _hasVideo = True
        _hasSkip = True
        _hasSkip2 = True

        def test_color(_color):
            """ Test for # followed by 6 hexadecimal characters """
            if not isinstance(_color, str) and not isinstance(_color, unicode):
                v0_print("color is not string or unicode. Type is:", type(_color))
                return False

            if not _color.startswith("#"):
                v0_print("color does not start with '#'")
                return False

            _color2 = _color.replace("#", "")
            if len(_color2) != 6:
                v0_print("Length of Tkinter hex color code with '#' is not 6")
                return False

            try:
                int(_color2, 16)
                return True
            except ValueError:
                v0_print("Tkinter hex color without '#' is not hexadecimal.")
                return False

        def test_point(_point):
            """ Test for valid [x, y] coordinates list """
            if type(_point) is not list:
                v0_print("Coordinates is not a list of '[]'")
                return False

            if len(_point) != 2:
                v0_print("Coordinates is not a list of [x, y]")
                return False

            try:
                if 0 < _point[0] < 50000:
                    if 0 < _point[1] < 50000:
                        return True
                    else:
                        v0_print("Coordinates of y inside [x, y] not 1 to 50000")
                        return False
                else:
                    v0_print("Coordinates of x inside [x, y] not 1 to 50000")
                    return False
            except ValueError:
                return False

        _hasAdColor = test_color(GLO["YT_AD_BAR_COLOR"])
        _hasAdPoint = test_point(GLO["YT_AD_BAR_POINT"])
        _hasVideoColor = test_color(GLO["YT_VIDEO_BAR_COLOR"])
        _hasVideoPoint = test_point(GLO["YT_VIDEO_BAR_POINT"])
        _hasSkipColor = test_color(GLO["YT_SKIP_BTN_COLOR"])
        _hasSkipPoint = test_point(GLO["YT_SKIP_BTN_POINT"])
        _hasSkipColor2 = test_color(GLO["YT_SKIP_BTN_COLOR2"])
        _hasSkipPoint2 = test_point(GLO["YT_SKIP_BTN_POINT2"])

        _hasAd = _hasAdColor and _hasAdPoint
        _hasVideo = _hasVideoColor and _hasVideoPoint
        _hasSkip = _hasSkipColor and _hasSkipPoint
        _hasSkip2 = _hasSkipColor2 and _hasSkipPoint2
        
        if _hasAd and _hasVideo and _hasSkip and _hasSkip2:
            return True

        v0_print("_hasAd, _hasVideo, _hasSkip, _hasSkip2:",
                 _hasAd, _hasVideo, _hasSkip, _hasSkip2)
        v0_print("_hasAdColor, _hasVideoColor, _hasSkipColor, _hasSkip2Color:",
                 _hasAdColor, _hasVideoColor, _hasSkipColor, _hasSkipColor2)
        v0_print("_hasAdPoint, _hasVideoPoint, _hasSkipPoint, _hasSkip2Point:",
                 _hasAdPoint, _hasVideoPoint, _hasSkipPoint, _hasSkipPoint2)

        def buildMessage(_color_key, _point_key):
            """ Build message liens for color and coordinates """
            _msg = "\n" + glo.getDescription(_color_key)
            _msg += " : " + str(GLO[_color_key]) + "\n"
            _msg += glo.getDescription(_point_key)
            _msg += " [x, y]: " + str(GLO[_point_key]) + "\n"
            return _msg
        
        title = self.app_title + " Requirements"
        text = "Colors and Coordinates defined in homa.py\n"
        text += buildMessage("YT_AD_BAR_COLOR", "YT_AD_BAR_POINT")
        text += buildMessage("YT_VIDEO_BAR_COLOR", "YT_VIDEO_BAR_POINT")
        text += buildMessage("YT_SKIP_BTN_COLOR", "YT_SKIP_BTN_POINT")
        text += buildMessage("YT_SKIP_BTN_COLOR2", "YT_SKIP_BTN_POINT2")

        if _hasAd and _hasVideo and _hasSkip:
            self.showInfoMsg(title, text, icon="warning")
            return True  # Will work but white ads will cause ad pause
        else:
            self.showInfoMsg(title, text, icon="error")
            return False

    def insertYtSB(self, msg, _time=None):
        """ Insert line into YouTube Scrollbox """
        _who = "insertYtSB(" + str(self.pav_count) + "):"

        # Suppress repeating HH: then MM: then SS
        _time = self.formatTime(_time=_time)
        _t = self.suppressTime(_time, self.yt_sb_last_time)
        self.yt_sb_last_time = _time

        _line = "\t" + _t + "\t" + msg + "\n"
        self.yt_sb.insert("end", _line, "audio_sb_indent")
        self.yt_sb.see("end")
        self.yt_sb_last_time = _time
        return _t

    def rebuildPaSB(self, _sink_inputs):
        """ Rebuild self.pa_sb (PulseAudio Scrollbox) and
            recreate self.asi (active sink-input)

            Called when new Pulse Audio sink-input discovered.
            Called when current sink-input corked status changes.
            Both instances occur if current sink_inputs list changes.

        """
        _who = "rebuildPaSB(" + str(self.pav_count) + "):"
        self.pa_sb.delete("3.0", "end")  # delete all but headings
        self.asi = ()  # named tuple of active sink input
        self.last_corked_and_dropped = False
        self.last_index = 0

        for _si in reversed(_sink_inputs):  # Read reversed to get last active

            # Override with ffplay song name instead of generic ffplay player name
            _name = self.ffplay_name if _si.application == "ffplay" else _si.name
            _corked = "Yes" if _si.corked else "No"  # True = "Yes", False = "No"

            # _si. attributes: index corked mute volume name application pid user
            _line = str(_si.index) + "\t" + _corked + "\t"
            _line += str(_si.application) + "\t" + str(_name)
            self.pa_sb.insert("end", _line + "\n", "pav_sb_indent")

            if _si.corked is True:
                # 2025-08-23 TODO: If the corked sink-input matches the same index
                #   as the last active sink-input index number, override exclusion
                #   and simply record new corked status. Later Ad or video status
                #   changes from "muted" or "playing" to "paused".
                if _si.name == self.last_name:
                    self.last_corked_and_dropped = True
                    self.last_index = _si.index
                    self.resetSpam(3)  # Just in case spam printing was in progress
                    v3_print(self.printTime(3), _who,
                             "'self.last_corked_and_dropped' = 'True'. Index:",
                             _si.index)
                continue  # Corked sink-inputs excluded as the last active

            if bool(self.asi):
                continue  # Already have last active sink input
            self.asi = _si  # Set last non-corked (active) sink-input

        try:  # Set fallback to last inactive sink-input when no active inputs
            self.asi = self.asi if bool(self.asi) else self.last_sink_inputs[-1]
        except IndexError:
            v0_print(self.printTime(), _who, "Catastrophic error. No Sink Inputs")
            return ()

        self.vars["pav_start"] = time.time()
        self.vars["pav_index"] = int(str(self.asi.index))
        self.vars["pav_application"] = self.asi.application
        self.vars["pav_name"] = self.asi.name
        self.vars["pav_volume"] = self.asi.volume
        self.vars["pav_corked"] = self.asi.corked
        self.vars["wn_found"] = False  # Reset last MatchWindow() results
        self.vars["wn_xid_hex"] = "N/A"

        return self.asi

    def matchWindow(self, _sink_inputs):
        """ Find matching window for self.asi(named tuple) Active Sink-Input.

            When a new sink appears it can happen when Video switches to an
            Ad. The same sink can reappear when a video is paused and "corked"
            equals True.

            If new sink is for a stale window or for a windowless sound input
            then keep the current self.vars{} YouTube dictionary in memory.

            Once a YouTube Video Name is used it stays in video status scrolled
            Text widget until a new name is encountered.

            NOTE: After upgrading FireFox in the background, unique PulseAudio
                sink-inputs no longer appear per video and ad. Instead a static
                "Firefox" "AudioStream" appears. Close and reopen Firefox to fix.
        """
        _who = "matchWindow(" + str(self.pav_count) + "):"
        self.resetSpam(1)  # Send spam \n print line if level 1 or greater

        try:
            _test = self.asi.name
        except AttributeError:
            # AttributeError: 'tuple' object has no attribute 'name'
            try:
                self.asi = self.last_sink_inputs[-1]
            except IndexError:
                # IndexError: List index out of range
                v0_print()  # resets last spam to level 0 instead of level 1
                v0_print(_who, "self.last_sink_inputs is empty")

        _name = self.asi.name
        _app = self.asi.application
        _pid = self.asi.pid

        if _name == "Playback Stream" and _app.startswith("Telegram"):
            _name = "Media viewer"  # Telegram's name in mon.wn_name

        def updateBlacklist(_msg):
            """ If sink-input index # not in blacklist append it to list. """
            if self.asi.index not in self.blacklist:
                self.blacklist.append(self.asi.index)
                v1_print(self.printTime(1), _who,
                         "adding to blacklist:", self.asi.index, _msg)

        # 2025-08-20 TODO: If pid = saved non-YouTube Window, restore
        #   non-YouTube Values, reset status to "Video paused" and exit
        time.sleep(0.1)  # Pulse Audio sink-input plays a bit before video mounted
        self.mon.make_wn_list()  # Rebuild list of active DM windows
        if not self.mon.get_wn_by_name(_name, pid=_pid):
            if _app == 'ffplay':
                _name = self.getFfPlayName(_pid)  # mserve ffplay song name

            v3_print(self.printTime(3), _who, "Matching window not found:")
            v3_print("  Name:", _name, " | PID:", _pid)
            v3_print("  Application:", _app)
            self.vars["wn_found"] = False
            self.vars["wn_xid_hex"] = "N/A"
            updateBlacklist(" | sink-input has no window")
            return False  # Matching window not found

        self.vars["wn_found"] = True  # Matching window found
        self.vars["wn_xid_hex"] = self.mon.wn_xid_hex

        if _name.endswith(" - YouTube"):  # YouTube window found?
            if self.asi.index in self.blacklist:
                self.blacklist.remove(self.asi.index)
                v1_print(self.printTime(1), _who, "remove from blacklist:",
                         self.asi.index, " | Ends with '- YouTube'")
            self.checkNewVideo(_name)  # True = new video name
            self.ad_start = 0.0  # A new sink-input will be an Ad or Video. Set both
            self.video_start = 0.0  # start times to 0 to force discovery.
            self.pause_start = 0.0  # 2025-10-25 time video was paused
            if self.skip_clicked:
                v1_print(self.printTime(1), _who, "'self.skip_clicked' reset:",
                         time.time() - self.skip_clicked)
                self.skip_clicked = 0.0  # Reset 2025-09-02

        else:
            updateBlacklist(" | Doesn't end with '- YouTube'")

        v3_print(self.printTime(3), _who,
                 "Matching window:", self.mon.wn_dict['xid_hex'])
        return True  # Matching window found

    def getFfPlayName(self, _pid):
        # noinspection SpellCheckingInspection
        """ If _pid = self.ffplay_pid, return self.ffplay_name and return.

            Use `ps -ef | grep ffplay` and parse parameters:

            rick     23661  2517  0 Jul25 pts/22   00:00:06 ffplay -autoexit
            /media/rick/SANDISK128/Music/AC_DC/Dirty Deeds Done Dirt Cheap/
            03 Big Balls.m4a -ss 0.0 -af
            afade=type=in:start_time=0.0:duration=1 -nodisp

        """
        _who = "getFfPlayName(" + str(self.pav_count) + "):"
        if _pid == self.ffplay_pid:
            return self.ffplay_name  # pid matches so last name still active

        result = os.popen("ps -ef | grep ffplay | grep -v grep").read().strip()
        self.ffplay_pid = _pid
        try:
            self.ffplay_name = result.split("ffplay -autoexit ")[1]
            self.ffplay_name = self.ffplay_name.split(" -ss ")[0]
            self.ffplay_name = self.ffplay_name.split(os.sep)[-1]
        except IndexError:
            self.ffplay_name = "Simply DirectMedia Layer"  # Old name
        return self.ffplay_name

    def checkNewVideo(self, _name):
        """ Check for new YouTube video name to initialize variables.
            If not fullscreen, force YouTube fullscreen with 'f' key.

            Blacklisted sink-inputs are never passed to this method. If
            they were blacklisted at first, they are un-blacklisted
            before this method is called.

            NOTE conventional OS fullscreen function is inadequate:

                os.popen("wmctrl -ir " + str(self.mon.wn_xid_hex) +
                         " -b toggle,fullscreen")

                `wmctrl` uses OS fullscreen however YouTube keeps extra
                icons and search bars which are distracting. Using
                YouTube fullscreen (with 'f' keystroke) invokes OS fullscreen
                and removes icons and search bars.

            2025-08-29 YouTube changed technique and no longer updates new
                video names in `wmctrl` or PulseAudio. It is like prime video
                now where the first video watched is the window name for
                subsequent new videos.

        """
        _who = "checkNewVideo(" + str(self.pav_count) + "):"
        self.resetSpam(1)  # Send spam \n print line if level 1 or greater
        self.video_ended = 0.0

        _msg = "Forcing window fullscreen"

        def forceFullscreen(_time):
            """ Force YouTube window to fullscreen. """
            self.sendCommand("fullscreen")  # YT fullscreen xdotool command
            self.mon.wn_is_fullscreen = True
            self.updateRows()  # Display new fullscreen status
            self.sendNotification(_msg + ". ")
            v1_print(self.printTime(1), _who, _msg + ":",
                     self.mon.wn_dict['xid_hex'])
            self.insertYtSB(_msg)
            self.yt_sb.highlight_pattern("fullscreen", "yellow")
            self.av_start = _time  # 0.0 = Video name is the same. else time.time()
            self.updateDuration()

        if _name == self.last_name:  # Same YouTube video window name?
            if self.mon.wn_is_fullscreen is False:
                forceFullscreen(0.0)  # Video was paused and set non-fullscreen
            return False  # Same video window name for A/V check

        # New YouTube Video
        self.last_name = _name
        self.yt_start = self.vars["pav_start"]
        self.yt_sb_last_time = "00:00:00.00"  # Force next time to print in full
        if " - YouTube" in _name:  # Remove "- YouTube" suffix from YouTube SB
            _name = _name.replace(" - YouTube", "")
        _time = self.insertYtSB(_name, self.yt_start)
        self.yt_sb.highlight_pattern(_time, "blue")

        if self.last_corked_and_dropped:
            self.last_corked_and_dropped = False
            v1_print(self.printTime(1), _who,
                     "New video forcing off: 'self.last_corked_and_dropped'.")

        if self.skip_clicked:
            self.skip_clicked = 0.0
            v1_print(self.printTime(1), _who,
                     "New video forcing off: 'self.skip_clicked'.")

        if self.mon.wn_is_fullscreen is True:
            self.av_start = time.time()  # Already full screen, nothing to force
            self.updateDuration()
            v1_print(self.printTime(1), _who,
                     "Window already fullscreen:", self.mon.wn_dict['xid_hex'])
            return True  # New window name discovered

        # YT fullscreen provides consistent ad/video progress bar coordinates
        if not self.checkInstalled('xdotool'):
            v1_print(_who, "`xdotool` is not installed. Cannot set fullscreen")
            self.av_start = time.time()  # A/V Check even if fullscreen fails
        else:
            forceFullscreen(time.time())

        return True  # New window name discovered

    def waitAdOrVideo(self):
        """ A new YouTube PulseAudio sink-input is analyzed when:
                yt_start != 0 and ad_start = 0 and video_start = 0.

            os.stat() configuration file to see if modification time
                was changed by homa.py - Tools - Configure YouTube Ads.
                If time changed, reread coordinates and colors.

            Find out if Ad or Video by testing colors @ coordinates. Always
                use the Ad coordinates because Video progress bar balloons
                when mouse hovers over the progress bar.

            If stuck in "A/V Check" loop for 6.0 seconds, assume video
                already playing.

            2025-08-13 Progress y-offsets changed +5, from 997 to 1002.

                                        x,y          Color
                YT_AD_BAR_POINT     [35, 1002]      #ffcc00
                YT_VIDEO_BAR_POINT  [35, 1002]      #ff0033
                YT_SKIP_BTN_POINT   [1830, 916]     #ffffff
                YT_SKIP_BTN_POINT2  [1834, 908]     #3f3f3f

            2025-08-24 Progress x-offsets changed -16, y-offsets changed +9.

                YT_AD_BAR_POINT     [19, 1013]      -16, +9
                YT_SKIP_BTN_POINT   [1859, 925]     +29, +9
                YT_SKIP_BTN_POINT2  [1862, 924]     +28, +16

            2025-08-28 Progress y-offsets changed -5

                YT_AD_BAR_POINT     [22, 1008]      +3, -5
                YT_SKIP_BTN_POINT   [1854, 922]     -5, -3
                YT_SKIP_BTN_POINT2  [1860, 916]     -2, -8

            2025-10-10 Progress y-offsets changed -4

                YT_AD_BAR_POINT     [21, 1004]      -1, -4
                YT_SKIP_BTN_POINT   [1851, 909]     -3, -13
                YT_SKIP_BTN_POINT2  [1855, 906]     -5, -10

            2025-10-12 Progress y-offsets changed +3 (Back to pre 2025-10-10)

                YT_AD_BAR_POINT     [18, 1007]      -3, +3

            2025-10-14 Progress y-offsets changed -15 (Back to pre 2025-08-13)
                Fonts and icons are larger even though browser magnification
                is still at 110%. New icon bar has been added above progress
                bar. Four icons: Like, Dislike, comments & share.

                YT_AD_BAR_POINT     [19, 992]       +1, -15
                YT_SKIP_BTN_POINT   [1855, 946]     +4, +37
                YT_SKIP_BTN_POINT2  [1858, 944]     +3, +38

        """

        _who = "waitAdOrVideo(" + str(self.pav_count) + "):"

        # Has HomA saved a newer version of the configuration file?
        self.this_stat = os.stat(glo.config_fname)
        if self.this_stat.st_mtime != self.last_stat.st_mtime:
            self.insertYtSB("Read newer preferences: " +
                            self.formatTime(self.this_stat.st_mtime))
            glo.openFile()
            global GLO
            GLO = glo.dictGlobals
            GLO['APP_RESTART_TIME'] = time.time()

            self.resetSpam(1)
            v1_print(self.printTime(1), _who, "New configuration time:",
                     self.formatTime(self.this_stat.st_mtime))
            self.last_stat = self.this_stat

        try:
            # noinspection PyUnboundLocalVariable
            _x, _y = GLO["YT_AD_BAR_POINT"]  # GLO is defined in main
        except AttributeError:
            v0_print(self.printTime(), _who,
                     'failure: _x, _y = GLO["YT_AD_BAR_POINT"]')
            return  # Tested at startup and should never happen

        if self.av_start == 0.0:
            self.av_start = time.time()  # "A/V check" start time
            v3_print(self.printTime(3), _who, 'self.av_start was 0.0')

        def setVideo(_text):
            """ Shared function for knowing or assuming video (not ad).
                Video may be paused or playing.
            """
            _who2 = _who + "setVideo():"
            self.video_start = time.time()
            self.av_start = 0.0
            self.ad_start = 0.0  # 2025-07-14 Extra insurance
            self.updateRows()
            self.resetSpam()
            if self.asi.index in self.blacklist:
                v1_print(self.printTime(1), _who2,
                         "Ignoring blacklisted:", self.asi.index)
                #self.video_start = 0.0  # Reset to get matching window
                # Above causes endless loop
            else:
                self.insertYtSB(_text + " on input #: " + str(self.vars["pav_index"]),
                                self.video_start)
                # _text = "Video playing" or "Video paused"
                _mark = "orange" if "paused" in _text else "green"
                self.yt_sb.highlight_pattern(_text, _mark)

        # noinspection SpellCheckingInspection
        ''' Is YouTube video newly corked? 
            2025-08-18 display "Video paused" in orange but input # stays same.
                Red progress bar is frozen on screen. An Ad can also be paused.
                This means the av_start, ad_start and video_start variables
                need to be taken into consideration.

            Ignore changes between sink-inputs when older input shows up:

                Input	Corked	Application	Video name

                1190	No	    Firefox	Zelensky, EU Visit IRRELEVANT, Russia is 
                                  Demilitarizing NATO –Andrei Martyanov - YouTube
                249	    No	    speech-dispatcher	playback
                248	    No	    speech-dispatcher	playback
                247	    No	    speech-dispatcher	playback
                246	    No	    speech-dispatcher	playback

            E.G. Sink-input # 1190 disappears after Ad Skip button click and 
            "Video playing on input#: 249" appears. This is false though and
            then .2 seconds later "Video playing on input #: 1191" appears".

            Build list of non-YouTube windows to be ignored. If list is empty
            then allow "No Pulse Audio" situation.
        '''

        _tk_clr = self.pi.get_colors(_x, _y)  # Get color
        self.printSpam(self.formatTime(), _who,
                       self.printXY(_x, _y), "color:", _tk_clr)

        if _tk_clr == GLO["YT_AD_BAR_COLOR"] and self.ad_start == 0.0:
            self.ad_start = time.time()
            self.av_start = 0.0
            self.video_start = 0.0  # 2025-07-15 Extra insurance
            self.pause_start = 0.0  # 2025-10-25 time video was paused

            self.resetSpam(1)  # Do this before normal printing (3 places)
            v2_print(self.printTime(2), _who)
            v2_print("  Coordinates: [{}, {}] color: {}".format(_x, _y, _tk_clr))

            # If already muted, this is a deprecating sink-input
            _vol = self.audio.pav.get_volume(str(self.asi.index), print_error=False)
            if _vol == 24.2424:
                v1_print(self.printTime(1), _who,
                         "Sink input obsolete:", str(self.vars["pav_index"]))

            elif _vol != 0:  # First time, turn down volume
                #self.audio.pav.set_volume(str(self.asi.index), 0)  # Set volume to zero
                self.setVolume(0)  # Set volume
                self.updateRows()
                text_str = "Ad muted"
                self.insertYtSB(text_str + " on input #: " + str(self.vars["pav_index"]),
                                self.ad_start)
                self.yt_sb.highlight_pattern(text_str, "red")
                _msg = "Muting Ad on input: " + str(self.vars["pav_index"])
                self.sendNotification(_msg)

                v2_print(self.printTime(2), _who, _msg,
                         "volume: " + str(self.vars["pav_volume"]),
                         "corked: " + str(self.vars["pav_corked"]))

            else:  # mute command already issued to PAV
                v1_print(self.printTime(1), _who,
                         "Already muted: " + str(self.vars["pav_index"]),
                         "volume: " + str(self.vars["pav_volume"]),
                         "corked: " + str(self.vars["pav_corked"]))
            return

        elif _tk_clr == GLO["YT_VIDEO_BAR_COLOR"] and self.video_start == 0.0:
            text_str = "Video "
            text_str += "paused" if self.last_corked_and_dropped else "playing"
            # 2025-10-25 Above added months ago but, status is always "playing"
            setVideo(text_str)
            v2_print(self.printTime(2), _who)
            v2_print("  Coordinates: [{}, {}] color: {}".format(_x, _y, _tk_clr))
            return

        # Wait x seconds for progress bar then assume video already playing
        # 2025-08-31 Change wait time from 2.0 seconds to 4.0 seconds
        # 2025-09-07 Change wait time from 4.0 seconds to 6.0 seconds
        if time.time() > self.av_start + 6.0 \
                and self.ad_start == 0.0 \
                and self.video_start == 0.0:
            self.resetSpam(2)
            v2_print(self.printTime(2), _who,
                     "A/V Check timeout. Assume video already playing.")
            text_str = "Assume video"
            setVideo(text_str)

    def waitAdSkip(self):
        """ Called when YouTube Ad is running.
            Caller discovered ad_start != 0 and video_start == 0.

            Wait 3.2 seconds before checking if ad skip button color #ffffff appears:
                If color matches, send click to skip button coordinates.
                If color doesn't disappear after 0.45 seconds, send another click.

            Status display in self.printSpam() line:
                "DC" = Delay checking for Ad Skip Button appearance
                "C1" = checking for white triangle color
                "C2" = checking for non-white color immediately outside triangle
                "SC" = sent ad skip button mouse click
                "SW" = waiting .45 seconds for ad skip button to disappear
                "AS" = Ad skipped

            2025-10-14 Limit screen grabs to every 100 ms (10 times per second).
                Normal refresh rate can be 16 ms to 33 ms (60fps to 30fps). Set
                limit of 15 seconds (longest duration before skip button) in order
                to catch instances when ad starts and user backs out.

            2025-08-27 Usually Ad Skip color is #ffffff. Today it was #f1f1f1 when
                ad skip button had focus. TODO: Rewrite to test r>F0, g>F0 and b>F0.

            2025-10-12 Back button during ad causes xorg to churn at 10% CPU usage:
19:11:15.55 waitAdOrVideo(784): Muting Ad on input: 1616 volume: 0.0 corked: False
19:11:22.26 waitAdSkip(784): C1 x=1851, y=909   color: #000000  | Cnt:  25  | Dur: 4.09
19:13:45.28 waitAdSkip(785): C1 x=1851, y=909   color: #000000  | Cnt: 1045  | Dur: 2:22.74
19:13:45.44 matchWindow(786): adding to blacklist: 1617  | sink-input has no window
19:15:22.55 waitAdSkip(786): C1 x=1851, y=909   color: #000000  | Cnt: 676  | Dur: 1:36.94
19:15:22.71 matchWindow(787): adding to blacklist: 1618  | window doesn't end in '- YouTube'
19:17:51.20 waitAdSkip(787): C1 x=1851, y=909   color: #080501  | Cnt: 985  | Dur: 2:28.29
19:29:21.34 waitAdSkip(788): C1 x=1851, y=909   color: #000000  | Cnt: 5392  | Dur: 11:29.85
Changing from g.PROGRAM_DIR: . to SAVE_CWD: /home/rick/HomA
EXIT yt-skip to bring CPU back to normal


            2025-10-20 Second Ad Skip Button click invokes Share button:
16:16:24.43 waitAdSkip(20): SC x=1858, y=944   color: #564133  | Cnt:  13  | Dur: 2.83
       5.29 waitAdSkip(20): SC x=1858, y=944   color: #452f21  | Cnt:   6  | Dur: 0.53
        .89 waitAdSkip(21): AS x=1855, y=946   color: #000000  | Cnt:   1  | Dur: 0.00

            Normal single Ad Skip Button click looks like this:
16:09:39.45 waitAdSkip(13): SC x=1858, y=944   color: #050606  | Cnt:  13  | Dur: 2.86
        .81 waitAdSkip(13): SW x=1855, y=946   color: #ffffff  | Cnt:   2  | Dur: 0.00
      40.21 waitAdSkip(14): AS x=1855, y=946   color: #000000  | Cnt:   1  | Dur: 0.00

        """

        _who = "waitAdSkip(" + str(self.pav_count) + "):"

        if time.time() < GLO['YT_SKIP_BTN_WAIT'] + self.ad_start:
            self.printSpam(self.formatTime(), _who, "DC",  # Need 30 chars now
                           # 23456789012345678901234567890
                           "Delay Ad Skip Button check ...")
            return  # Delay button check for a few seconds after ad starts

        if time.time() < self.last_grab_time + .1:
            return  # Limit screen color grabs to 10 per second

        self.updateDuration()  # Force "Ad skip button color check" status display

        try:  # Get white triangle color
            _x, _y = GLO["YT_SKIP_BTN_POINT"]
            self.last_grab_inside = self.pi.get_colors(_x, _y)
        except AttributeError:  # Coordinates for skip button unknown
            return  # Should never happen because startup tests for _x & _y

        try:  # Get non-white color outside of triangle
            _x2, _y2 = GLO["YT_SKIP_BTN_POINT2"]
            self.last_grab_outside = self.pi.get_colors(_x2, _y2)
        except (AttributeError, ValueError):
            _x2 = _y2 = 9999  # Optional not-while coordinates undefined
            self.last_grab_outside = "#1a2b3c"  # Color when no coordinates

        self.last_grab_time = time.time()  # Limit grabs to 10 per second

        def resetAd():
            """ Ad has finished. """
            self.ad_start = 0.0  # Turn off ad running
            self.skip_clicked = 0.0  # Reset for ad
            # 2025-08-30 TODO: Review if av_start should be set
            self.resetSpam()  # Turn off spam printing to console

        if self.last_grab_inside != GLO["YT_SKIP_BTN_COLOR"]:
            if self.skip_clicked > 0.0:
                resetAd()  # Ad Skip button clicked and now it's disappeared
                # 2025-09-01 Just added but rarely prints, "SW" is last printed
                #   because a new sink-input resets wait loop.
                # 2025-10-15 Code "AS" appears frequently if `yt-skip.py -v` used.
                self.printSpam(self.formatTime(), _who, "AS",
                               self.printXY(_x, _y), "color:", self.last_grab_inside)
                self.resetSpam()  # Repeat from resetAd()
            else:
                # Ad Skip button has not been clicked yet
                self.printSpam(self.formatTime(), _who, "C1",
                               self.printXY(_x, _y), "color:", self.last_grab_inside)
            return  # Waiting for white color to appear or Ad Skipped

        # 2025-11-08 Was browser back button pressed while ad was playing?
        if self.last_name != self.vars["pav_name"]:
            _print_name = self.last_name  # save for printing
            self.last_name = ""  # Force printing time in full next time
            self.yt_start = self.av_start = self.ad_start = self.skip_clicked = 0.0
            self.resetSpam()
            v1_print(self.printTime(1), _who, "Ad cancelled:", _print_name)
            return

        ''' At this point right tip of Ad skip Button triangle is confirmed
            to be white because self.last_grab_inside == GLO["YT_SKIP_BTN_COLOR"]. 
            
            If near non-white color is <= 176 (b0) it's an Ad Skip Button. 
            If near non-white color is > 176 (b0) it's an Ad with a white background. 
            self.last_grab_outside contains the near non-white color. 
        '''

        self.printSpam(self.formatTime(), _who, "C2",
                       self.printXY(_x2, _y2), "color:", self.last_grab_outside)

        # Check if this is a white-ish ad, and not the ad skip button
        #if self.last_grab_outside == GLO["YT_SKIP_BTN_COLOR"]:  # 2025-10-19 OLD
        _rgb = img.hex_to_rgb(self.last_grab_outside)  # 2025-10-17 non-white compare
        _high = max(_rgb)  # 2025-10-17 _high = "de" when value is "#ded8cf"
        if _high > 176:  # 2025-10-19 r, g, or b is greater than hex b0
            self.resetSpam(3)
            v3_print(self.printTime(3), _who)
            v3_print("  Coordinates: [{}, {}] color: {}"
                     .format(_x2, _y2, self.last_grab_outside))
            v3_print("  Waiting for Ad skip button non-white color to appear...")
            return  # White-ish ad, not the Ad Skip button

        # If a click was already sent, wait before sending another in order to
        #   give the browser enough time to process the last click.
        if time.time() < self.skip_clicked + GLO['YT_SKIP_BTN_WAIT2']:
            # 0.15, 0.25, 0.35 too short for YouTube button to disappear.
            #   Wait 0.45 seconds (GLO['YT_SKIP_BTN_WAIT2']) in HomA Preferences.
            # NOTE: 0.25 works ok until ffmpeg volume analyzer is run. Then the
            #       CPU temperature reached 94 degrees and CPU usage was 63%.
            # 2025-08-31 bump to 0.5 seconds because second click paused video.
            # 2025-10-23 hola.com running on background tab also pushes 94 degrees.
            self.printSpam(self.formatTime(), _who, "SW",
                           self.printXY(_x, _y), "color:", self.last_grab_inside)

            self.resetSpam(3)  # New line only if -vvv parameter was used
            v3_print(self.printTime(3), _who)
            v3_print("  Ad skip button color found:",
                     "'" + GLO["YT_SKIP_BTN_COLOR"] + "'.")
            v3_print("  Waiting for Ad skip button color to disappear...")
            return  # Too soon to assume last click was too early.
            # If last click worked the second click causes video pause.

        if not self.checkInstalled('xdotool'):
            resetAd()
            v0_print(_who, "`xdotool` is not installed. Cannot click Ad Skip")
            return

        self.printSpam(self.formatTime(), _who, "SC",
                       self.printXY(_x2, _y2), "color:", self.last_grab_outside)
        # outside triangle: #000000 (4x), #011b30, #040302, #060606, #091113, #0b0908,
        #   #11160f, #161c16, #171513, #1a1a1a, #1c1c1c, #1e0f0d, #1e2018, #1f0a06,
        #   #270506, #322c2c, #371f13, #382e19 (2x), #3c3632, #3d3635,
        #   #44392e, #453a2c, #454543, #46110f, #473b2e, #491211, #493d30, #4b3f33,
        #   #533d30, #555555, #5b4637, #5e5d5f, #665001 (2x), #666666

        # False positives: #fffffd
        self.resetSpam()  # Want to see outside color so force printing
        v3_print(self.printTime(3), _who, 'self.last_grab_outside "_high":', _high)
                                                    # When hex 66: _high  =  102
        self.sendCommand("click", _x, _y)  # xdotool: 0.0370068550 to 0.1740691662

        self.skip_clicked = time.time()  # When skip color disappears, it is success
        self.insertYtSB("Ad skip button mouse click")
        v2_print(self.printTime(2), _who)
        v2_print("  Mouse click sent to coordinates: ["
                 + str(_x) + ',' + str(_y) + "].")

    def waitVideoEnd(self):
        """ Called when YouTube Video is running.
            Caller discovered video_start != 0 and ad_start == 0.
        """

        _who = "waitVideoEnd(" + str(self.pav_count) + "):"

        if self.last_name == self.vars["pav_name"]:  # Compare to active name
            return  # Last name is still the active sink-input name

        if self.last_corked_and_dropped:  # Was last active sink-input corked?
            return  # Video is paused, not ended

        if self.video_ended == 0.0:  # First video end suspected?
            self.video_ended = time.time()  # Time video end encountered

        if self.video_ended + 3.0 > time.time():  # 3 seconds passed?
            return  # Wait to confirm video has truly ended

        _print_name = self.last_name  # save for printing
        self.last_name = ""  # Force printing time in full next time
        self.yt_start = self.av_start = self.video_start = 0.0
        self.resetSpam(1)
        v1_print(self.printTime(1), _who, "Video ended:", _print_name)

    def updateRows(self):
        """ Update rows with pulse audio active sink input (asi)
            and matching window (self.mon.wn) attributes.
        """
        self.text_index.set(str(self.asi.index))  # Long Integer
        self.text_pid.set(self.asi.pid)
        self.text_pa_app.set(self.asi.application)  # Could be UTF-8

        def set_time(_val):
            """ Format date if not zero. """
            if _val == 0.0:
                return "N/A"  # Don't want to print January 1, 1970 midnight
            return self.formatTime(_val)

        self.text_wn_xid_hex.set(str(self.vars["wn_xid_hex"]))  # May already be N/A
        self.text_yt_start.set(set_time(self.yt_start))  # Set to N/A if zero
        # text_status.set and text_duration.set done in updateDuration()

        if self.vars["wn_found"] is False:
            self.text_is_YouTube.set("N/A")  # No matching window found so probably
            self.text_is_fullscreen.set("N/A")  # ffplay or speech-dispatcher, etc.
            return

        _yt = "yes" if self.asi.name.endswith(" - YouTube") else "no"
        self.text_is_YouTube.set(_yt)
        _fs = "yes" if self.mon.wn_is_fullscreen else "no"
        self.text_is_fullscreen.set(_fs)

    def addRow(self, row_no, label, _val, _type="String", tt_text=None):
        """ Add row to Pointer Location section
            Column 0 contains label, Column 1 contains passed text which is
            initialized into string variable returned to caller.
        """
        _who = "addRow(" + str(self.pav_count) + "):"
        label = ttk.Label(self.audio_frm, text=label, font=g.FONT)
        label.grid(row=row_no, column=0, sticky=tk.NSEW, padx=15, pady=10)

        if _type == "String":
            _var = tk.StringVar()
        elif _type == "Int":
            _var = tk.IntVar()
        else:
            v0_print(self.printTime(), _who, "Unknown tk variable type:", _type)
            return None

        _var.set(_val)
        text = ttk.Label(self.audio_frm, textvariable=_var, font=g.FONT)
        text.grid(row=row_no, column=1, sticky=tk.NSEW, padx=15)
        if self.tt and tt_text:
            self.tt_add(label, tt_text)
        return _var

    def updateVuMeter(self):
        """ Update VU Meter maximum 100 frames per second. """
        _who = "updateVuMeter():"
        _now = time.time()
        if _now < self.last_vum_update + 0.01:
            return True  # Don't want to update VU Meter too quickly

        try:
            self.vum.update_display()  # paint LED meters reflecting amplitude
        except (tk.TclError, AttributeError) as err:
            v0_print(_who, "Call to self.vum.update_display() failed!")
            v0_print(" ", err)
            return False

        self.last_vum_update = _now
        return True

    def updateDuration(self):
        """ Update Status and Duration in 8th & 9th rows.
            Called every second.

            Status:   A/V check / Ad playing / Video playing /
                      Ad skip button color check / NOT YouTube

            Duration: 99:99:99.99

            2025-10-25 When self.last_corked_and_dropped == True:
                If the last status was "Video paused" set "External".
                If the last status was "Video playing" set "Video paused".
        """
        _who = "updateDuration():"
        _now = time.time()
        _status = ""
        old_status = self.text_status.get()
        _dur = 0.0

        def setVideoStatus():
            """ 2025-10-25 New function for self.video_start > 0.0
                if self.last_corked_and_dropped == True:
                    if the old_status was "Video playing" or "Assume video":
                        and self.pause_start == 0.0
                            set the new status to "Video paused".
                            reset self.video_start to current time.
                            set self.pause_start to current time.
                    if the last status was none of above, video has just
                        started playing and variable should have been False.
                else self.last_corked_and_dropped == False:
                    if last status was "Video paused":
                        set the new status to "Video resumed"
                        reset self.video_start to current time.
                        set self.pause_start to 0.0.
                    else
                        set status to "Video playing"
                        set self.pause_start to 0.0.  # Extra insurance
                        # self.video_start time was set by parents.

            """
            def newStatus(_index):
                """ Insert into scroll box with pattern highlighting. """
                self.insertYtSB(_new_status + " on input #: " + str(_index),
                                self.video_start)
                _mark = "orange" if "paused" in _new_status else "green"
                self.yt_sb.highlight_pattern(_new_status, _mark)

            now = time.time()
            if self.last_corked_and_dropped is True:
                _new_status = "Video paused"
                if self.pause_start == 0.0:
                    self.pause_start = now
                    self.video_start = now
                    newStatus(self.last_index)
            else:  # self.last_corked_and_dropped is False
                _new_status = "Video playing"
                self.pause_start = 0.0
                if old_status == "Video paused":
                    self.video_start = now
                    # newStatus(self.vars["pav_index"]) false dummy input

            return _new_status

        if self.ad_start > 0.0 and \
                _now > GLO['YT_SKIP_BTN_WAIT'] + self.ad_start:
            _dur = _now - self.ad_start - GLO['YT_SKIP_BTN_WAIT']
            _status = "Ad skip button color check"
            if old_status != _status:
                self.insertYtSB(_status)
        elif self.ad_start > 0.0:
            _dur = _now - self.ad_start
            _status = "Ad playing"
        elif self.video_start > 0.0:
            _status = setVideoStatus()
            _dur = _now - self.video_start
            #_status = "Video playing"  # 2025-10-25 Set in new setVideoStatus()
        elif self.yt_start > 0.0:
            _dur = _now - self.vars["pav_start"]
            _status = "A/V check"
            if old_status != _status:
                self.insertYtSB(_status)
        elif self.vars["wn_name"] != "":
            # 2025-10-25 TODO: review with new setVideoStatus() function
            _dur = _now - self.vars["pav_start"]
            _status = "NOT YouTube"
            if old_status != _status:
                self.insertYtSB(_status)

        self.text_status.set(_status)
        self.text_duration.set(tmf.mm_ss(_dur))

    def sendNotification(self, _msg, icon=None):
        """ Send Desktop notification to current active monitor.
            Called when forcing full screen and muting Ad volume.
            2025-09-21 Added today. Need more than just speaker icon.
        """
        _who = "sendNotification():"

        if not self.checkInstalled('notify-send'):
            v3_print(_who, "`notify-send` not installed.")
            return False

        if icon is None:
            #icon = "/usr/share/icons/gnome/48x48/devices/audio-speakers.png"
            _path = os.path.abspath(g.PROGRAM_DIR)  # '.' to '/home/USER/HomA'
            icon = _path + os.sep + "YT_taskbar_icon.png"  # set in __init__()

        command_line_list = [
            "notify-send", "--urgency=critical", self.app_title,
            "-h", "string:x-canonical-private-synchronous:yt-skip",
            "--icon=" + icon, _msg]
        event = self.runCommand(command_line_list, _who, forgive=False)

        # Average command time is 0.025 seconds but never logged
        if event['returncode'] != 0:  # Was there an error?
            v0_print(_who, "Error:", event['returncode'])
            v0_print(" ", self.cmdString)

        return True  # Parent will delay rediscovery 1 minute

    def setVolume(self, _percent):
        """ Set volume to integer percent. """
        _who = "setVolume(" + str(self.pav_count) + "):"
        self.audio.pav.set_volume(str(self.asi.index), 0)  # Set volume to zero
        self.vars["pav_volume"] = 0.0
        Input = namedtuple('Input', 
                           'index corked mute volume name application pid user')
        for i, _lsi in enumerate(self.last_sink_inputs):
            if _lsi.index == self.asi.index:
                self.resetSpam(3)
                v3_print(_who, "Changing volume:", i, _lsi)
                # noinspection PyArgumentList
                _new = Input(_lsi.index, _lsi.corked, _lsi.mute, 0, _lsi.name,
                             _lsi.application, _lsi.pid, _lsi.user)
                self.last_sink_inputs[i] = _new
                v3_print(_who, "New volume:", i, _new)
                break

    def updateVideos(self):
        # noinspection SpellCheckingInspection
        """ Called from self.loopForever() every 16 to 33 ms.
            Monitor Pulse Audio for new sinks. Check if ad progress bar or
            video progress bar color is shown. If ad progress bar wait for
            Ad Skip Button to appear and click it.

        2025-08-11 - Reboot and reset screens last night and today y-offsets
            dropped down by 62 pixels. Ad/Video progress bars can't be seen.
            Running `ssr`, and begin recording, shows:
            - [X11Input::Init] Screen 1: x1 = 0, y1 = 62, x2 = 1920, y2 = 1142
            - [X11Input::Init] Dead space 0: x1 = 0, y1 = 0, x2 = 1920, y2 = 62

        FULLSCREEN NOTES:
            Wnck.Screen.Window.fullscreen() isn't supported in version 3.18.
            wmctrl -ir hex_win -b toggle,fullscreen doesn't remove YT menus.
            Use 'xdotool key "f"' for YouTube fullscreen method.

        AD SKIP BUTTON CLICK NOTES:
            Gtk mouse click only works on GTK windows
            Python pyautogui click only works on primary monitor
            Browser previous history (<ALT>+<Left Arrow>) followed by forward
                (<ALT>+<Right Arrow>) works sometimes but can sometimes take
                3.2 (GLO['YT_SKIP_BTN_WAIT']) seconds which an Ad skip Button
                Click would take. Sometimes YouTube restarts video at beginning
                which totally breaks flow.
            Cannot skip Ad on YouTube using keyboard:
                https://webapps.stackexchange.com/questions/100869/
                    keyboard-shortcut-to-close-the-ads-on-youtube
            Use:
                `xdotool mousemove <x> <y> click 1 sleep 0.01 mousemove restore`


        2025-10-05 Currently no window active. Last pav is "ffplay" that has no
            window. 'YouTube?', 'Window number:' and 'Fullscreen?' are all "N/A".
            NOTE: Variable "YouTube start" is really "Last video start".
            'YouTube start: 99:99:99.99', 'Status: Video Playing' and
            'Duration: 9:99' are still actively updated from last video. When a
            new video is started false update:

15:10:04.31	Killzone🔴The Ring Around Siversk Continues to Tighten⚔️🔥
              Military Summary And Analysis For 2025.10.05
        .55	Ad muted on input #: 189
       7.06	Ad skip button color check
      10.02	Ad skip button mouse click
        .87	Video playing on input #: 190       <<< Old video ends, then new video picked
   19:38.79	Window forced to fullscreen.        <<< First Ad should have forced new video
      39.09	A/V check
        .61	Ad muted on input #: 191
      42.12	Ad skip button color check
15:19:44.86	Insane moment of Geran dives the railway station in Shostka!
      45.10	Ad muted on input #: 192            <<< Second Ad did force new video
      47.64	Ad skip button color check
      51.05	Video playing on input #: 193


        2025-09-03 Error if `pulseaudio -k` used to reset:

Traceback (most recent call last):
File "./yt-skip.py", line 1632, in <module>
main()
File "./yt-skip.py", line 1626, in main
app = Application(root)  # Main GUI window
File "./yt-skip.py", line 355, in __init__
self.loopForever()  # Loop until exit
File "./yt-skip.py", line 1192, in loopForever
sink_inputs = self.audio.pav.get_all_inputs()
File "/home/rick/HomA/vu_pulse_audio.py", line 702, in get_all_inputs
for sink in self.pulse.sink_input_list():
File "/home/rick/HomA/pulsectl/pulsectl.py", line 563, in _wrapper_method
*([index, cb, None] if index is not None else [cb, None]) )
File "/usr/lib/python2.7/context lib.py", line 24, in __exit__
self.gen.next()
File "/home/rick/HomA/pulsectl/pulsectl.py", line 523, in _pulse_op_cb
if not self._actions[act_id]: raise PulseOperationFailed(act_id)
pulsectl.pulsectl.PulseOperationFailed: 946012


        """
        _who = "updateVideos():"

        sink_inputs = self.audio.pav.get_all_inputs()

        # sink-input changes means an Ad or Video started, paused or ended
        if sink_inputs != self.last_sink_inputs:
            self.pav_count += 1  # PulseAudio Sink-Inputs changed count
            if not bool(self.last_sink_inputs):
                # last sink-inputs empty first time so use current sink-inputs
                self.last_sink_inputs = sink_inputs  # for matchWindow()
            self.rebuildPaSB(sink_inputs)  # Build scrollbox and self.asi
            self.matchWindow(sink_inputs)  # X11 window for self.asi
            self.updateRows()  # 2025-07-03 - Handles no X11 window
            self.last_sink_inputs = sink_inputs  # deepcopy NOT required

        # YouTube started but Ad or Video started not set yet
        if self.yt_start != 0.0 and self.ad_start == 0.0 and \
                self.video_start == 0.0:
            self.waitAdOrVideo()  # Set yellow Ad bar or red Video bar

        # Is YouTube Ad active?
        if self.ad_start != 0.0 and self.video_start == 0.0:
            self.waitAdSkip()  # Wait to click Ad Skip button when it appears

        # Is YouTube Video active?
        if self.video_start != 0.0 and self.ad_start == 0.0:
            self.waitVideoEnd()  # Wait for video to end

        # Update duration once per second
        second = ext.h(time.time()).split(":")[2].split(".")[0]
        if second != self.last_second:
            self.updateDuration()  # Update status and duration
            self.last_second = second  # Save current second for next test

    def loopForever(self):
        """ Loop forever refreshing App every 16 to 33 ms.
            Update VU Meters display.
            Call updateVideo() to monitor Pulse Audio for new sinks and Videos. 
        """
        _who = "loopForever():"

        _vum_working = True  # Assume VU meter is working

        while self and self.winfo_exists():  # Loop until window closed

            if not self.refreshApp():  # sleeps 16 to 33 milliseconds
                break  # exiting app

            if _vum_working:  # VU Meters still working after last display?
                _vum_working = self.updateVuMeter()

            self.updateVideos()

        # Application shutting down. Is VU meter still running?
        if self.vum and ext.check_pid_running(self.vum.pid):
            self.vum.terminate()  # Also closed in exitApp()

    # noinspection SpellCheckingInspection
    def sendCommand(self, _command, _x=None, _y=None):
        """ Send xdotool commands
                - f for fullscreen or left-click for ad skip
                - For left-click _x and _y parameters are required

        """
        _who = "sendCommand(" + str(self.pav_count) + "):"
        ext.t_init("4 xdotool commands")
        _active = os.popen('xdotool getactivewindow').read().strip()

        if _command == "click":
            os.popen('xdotool mousemove ' + str(_x) + ' ' + str(_y) +
                     ' click 1 sleep 0.01 mousemove restore')
        elif _command == "fullscreen":
            os.popen('xdotool windowactivate --sync ' +
                     str(self.mon.wn_dict['xid_int']))
            os.popen('xdotool key f &')
            time.sleep(0.1)  # sleep stops fullscreen toggling twice by YouTube.
            # If && was used time.sleep(0.2) is required instead of (0.1)
            self.resetSpam(2)  # Just in case spam printing was active
            v2_print(self.printTime(2), _who, 'xdotool windowactivate --sync ' +
                     str(self.mon.wn_dict['xid_int']) + ' && xdotool key f &')

        else:
            v0_print(self.printTime(0, dec=False), _who,
                     "Bad '_command' parameter: '" + str(_command) + "'.")

        if len(_active) > 4:
            # Occasionally xdotool doesn't reactivate window. Do it manually.
            os.popen('xdotool windowfocus ' + _active)
            os.popen('xdotool windowactivate ' + _active)
            self.resetSpam(2)  # Just in case spam printing was active
            v2_print("  Restoring previous active window: '" +
                     str(hex(int(_active))) + "'")
        else:
            v0_print(self.printTime(0, dec=False), _who,
                     "Could not restore active window: '" +
                     str(hex(int(_active))) + "'")
        ext.t_end("no_print")  # 4 xdotool commands: 0.0370068550 to 0.1740691662

    def printSpam(self, *args, **kwargs):
        """ Spam printing repeats printing on same line. Check for first time.
        """
        _duration = 0.0  # How long spam printing has been active
        if self.spam_time:
            _duration = time.time() - self.spam_time
        else:
            self.spam_time = time.time()  # Time spam printing started
            # 2025-11-02 Set significant HH:MM to print
        self.spam_count += 1

        if args:  # Check if *args is not empty
            first_arg = args[0]  # This code from google search AI
            if isinstance(first_arg, str):  # Ensure the first argument is a string
                # 2025-11-01 suppress repeating HH:MM:SS
                _t = self.suppressTime(first_arg, self.spam_last_time)

                prepended_char = '\r'  # The character to prepend
                new_first_arg = prepended_char + _t
                new_end_arg = " | Cnt: %3d  | Dur: " % self.spam_count
                new_end_arg += tmf.mm_ss(_duration, rem='h')
                # Create a new tuple with the modified first argument
                # and the rest of the original arguments
                modified_args = (new_first_arg,) + args[1:] + (new_end_arg, )
                v0_print(*modified_args, end="", **kwargs)
                return

        v0_print("\r", *args, end="", **kwargs)  # Cannot prepend "\r"

    def resetSpam(self, _v=0):
        """ Reset spam printing for next print group. Check to ensure last
            print group actually printed something by checking spam_time
        """
        if not checkVerbose(_v):
            return  # Requested level is not printing so don't reset

        if self.spam_time:
            v0_print()  # Force newline
            self.spam_time = 0.0
            self.spam_count = 0
            #self.spam_last_time = self.print_last_time  # inherit last print
            #self.spam_last_time = self.formatTime()  # Prepends leading space?
            # 2025-11-02 Just before new v9_print() direct call not printSpam()
            #   Set time baseline for HH:MM:SS for suppressTime() function
            self.spam_last_time = self.formatTime()  # v9_print() will use this time

    def printTime(self, _v=0, _time=None, dec=True):
        """ Format passed _time as HH:MM:SS or use current time if _time=None.
            If dec=True append decimal seconds for HH:MM:SS.dd format.

            Only called by debug printing => v0_print() -> v3_print().
            The last formatted time is saved for comparison on next call.
            If level > 0, check if debug printing is set >= verbose level.
        """
        _who = "printTime():"
        if not checkVerbose(_v):
            return "N/A"  # Requested level is not printing so don't format time

        _time = self.formatTime(_time, dec)
        # If last spam print time is newer, use that as baseline HH:MM:SS
        if self.print_last_time < self.spam_last_time:
            self.print_last_time = self.spam_last_time

        # Suppress repeating HH: then MM: then SS
        _t = self.suppressTime(_time, self.print_last_time)
        self.print_last_time = self.spam_last_time = _time
        return _t

    @staticmethod
    def formatTime(_time=None, dec=True):
        """ Format passed _time as HH:MM:SS or use current time if _time=None.
            If dec=True append decimal seconds for HH:MM:SS.dd format.
        """
        _who = "formatTime():"
        if _time:
            dt_time = dt.datetime.fromtimestamp(_time)
        else:
            dt_time = dt.datetime.now()

        formatted_time = dt_time.strftime("%H:%M:%S")
        if dec:
            formatted_time += "." + dt_time.strftime("%f")[:2]

        return formatted_time

    @staticmethod
    def suppressTime(_time, _last_time):
        """ Return parts of _time that are different from _last_time """

        # Suppress repeating HH: then MM: then SS
        _h = _time[0:3]  # HH: <--- suppress duplicates
        _m = _time[3:6]  # MM: <--- suppress duplicates
        _s = _time[6:8]  # SS  <--- suppress duplicates
        _f = _time[8:]   # .FF <--- always prints
        if _time[0:3] == _last_time[0:3]:
            _h = "   "  # Suppress hour which hasn't changed
            if _time[3:6] == _last_time[3:6]:
                _m = "   "  # Suppress hour and minutes are the same
                if _time[6:8] == _last_time[6:8]:
                    _s = "   "  # Suppress hour, minutes and seconds
        _t = _h + _m + _s + _f
        _t = _t.replace("0", " ", 1) if _t.lstrip().startswith("0") else _t

        if len(_t) > 11:
            _t = _t[1:]  # 2025-11-02 Getting a leading space?

        return _t

    @staticmethod
    def printXY(_x, _y):
        """ Return 'x=9,   y=9   ' to
                   'x=9999,y=9999'
        """
        _who = "printXY():"
        _x = str(_x) + ","
        _y = str(_y)
        return 'x=' + _x.ljust(6) + 'y=' + _y.ljust(5)

    def getWindowID(self, title):
        """ Use wmctrl to get window ID in hex and convert to decimal for xdotool
            2025-06-13 (It's Friday 13th!) Test new mon.wm_xid_int
        """
        _who = "getWindowID():"
        GLO['WINDOW_ID'] = None  # yt-skip Window ID, must restore after reading GLO
        v2_print(_who, "search for:", title)

        if not self.checkInstalled('wmctrl'):
            v0_print(_who, "`wmctrl` is not installed.")
            return

        command_line_list = ["wmctrl", "-l"]
        event = self.runCommand(command_line_list, _who, forgive=False)
        for line in event['output'].splitlines():
            ''' $ wmctrl -l
                0x05600018  0   N/A HomA - Home Automation '''
            parts = line.split()
            if ' '.join(parts[3:]) != title:
                continue
            v2_print("Title matches:", ' '.join(parts[3:]))
            GLO['WINDOW_ID'] = int(parts[0], 0)  # Convert hex window ID to decimal

        v2_print(_who, "Integer GLO['WINDOW_ID']: '" + str(GLO['WINDOW_ID']) + "'")
        if GLO['WINDOW_ID'] is None:
            v0_print(self.printTime(), _who, "ERROR `wmctrl` could not find Window.")
            v0_print("Search for title failed: '" + title + "'.\n")

    def exitApp(self, kill_now=False, *_args):
        """ <Escape>, X on window, 'Exit from dropdown menu or Close Button"""
        _who = "exitApp():"

        ''' Is it ok to stop processing? - Make common method... '''
        msg = None

        if msg and not kill_now:  # Cannot suspend when other jobs are active
            self.showInfoMsg("Cannot Close now.", msg, icon="error")
            v0_print(self.printTime(), _who, "Aborting Close.", msg)
            return

        sql.close_homa_db()  # Close SQL History Table

        self.win_grp.destroy_all(tt=self.tt)  # Destroy Calculator and Countdown
        #if self.vum and self.vum.pid:
        #    ext.kill_pid_running(self.vum.pid)  # Already killed on exit
        self.isActive = False  # Signal closing down so methods return

        if self.vum and ext.check_pid_running(self.vum.pid):
            self.vum.terminate()  # Also closed in loopForever()

        ''' reset to original SAVE_CWD (saved current working directory) '''
        if SAVE_CWD != g.PROGRAM_DIR:
            v1_print("Changing from g.PROGRAM_DIR:", g.PROGRAM_DIR,
                     "to SAVE_CWD:", SAVE_CWD)
            os.chdir(SAVE_CWD)

        if self.winfo_exists():
            self.destroy()  # Destroy toplevel
        exit()  # exit() required to completely shut down app

    def minimizeApp(self, *_args):
        """ Minimize GUI Application() window using xdotool. """
        _who = "minimizeApp():"
        if not self.checkInstalled('xdotool'):
            v0_print(_who, "`xdotool` is not installed. Cannot minimize window")
            return

        # noinspection SpellCheckingInspection
        command_line_list = ["xdotool", "windowminimize", str(GLO['WINDOW_ID'])]
        self.runCommand(command_line_list, _who)

    def buildButtonBar(self):
        """ Paint button bar below treeview.
            Minimize - Minimize window.
            Help - www.pippim.com/HomA.
            Close - Close HomA.
        """

        ''' self.btn_frm holds Application() bottom bar buttons '''
        self.btn_frm = tk.Frame(self)
        self.btn_frm.grid_rowconfigure(0, weight=1)
        self.btn_frm.grid_columnconfigure(0, weight=1)
        # When changing grid options, also change in self.Preferences()
        self.btn_frm.grid(row=99, column=0, columnspan=3, sticky=tk.E)

        '''
        2024-09-07 - Xorg or Tkinter glitch only fixed by reboot makes tk.Button
          3x wider and taller. Use ttk.Button which defaults to regular size.
          The 'font=' keyword is NOT supported in ttk.Button which uses -style.
        '''
        style = ttk.Style()
        # Credit: https://stackoverflow.com/a/62506279
        #style.theme_use("classic")

        style.map("C.TButton",  # Homa command buttons
                  foreground=[('!active', 'Black'), ('pressed', 'White'),
                              ('active', 'Black')],
                  background=[('!active', 'Grey75'), ('pressed', 'ForestGreen'),
                              ('active', 'SkyBlue3')]  # lighter than DodgerBlue
                  )

        style.configure("C.TButton", font=g.MED_FONT)

        def make_button(row, column, txt, command, tt_text, tt_anchor, pic=None):
            """ Function to combine ttk.Button, .grid() and tt.add_tip() """
            # font=
            txt = toolkit.normalize_tcl(txt)  # Python 3 lose 🌡 (U+1F321)
            # above was python 3 short term fix, use an image for permanent fix
            if pic:
                widget = ttk.Button(self.btn_frm, text=" "+txt, width=len(txt)+2,
                                    command=command, style="C.TButton",
                                    image=pic, compound="left")
            else:
                widget = ttk.Button(self.btn_frm, text=txt, width=len(txt),
                                    command=command, style="C.TButton")
            widget.grid(row=row, column=column, padx=5, pady=5, sticky=tk.E)
            if tt_text is not None and tt_anchor is not None:
                self.tt.add_tip(widget, tt_text, anchor=tt_anchor)
            return widget

        ''' Minimize Button - U+1F847 🡇  -OR-  U+25BC ▼ '''
        if GLO['WINDOW_ID'] is not None:
            # xdotool and wmctrl must be installed for Minimize button
            make_button(0, 0, "Minimize", self.minimizeApp,
                        "Quickly and easily minimize window.", "nw", self.img_minimize)

        ''' Help Button - ⧉ Help - Videos and explanations on pippim.com '''
        help_text = "Open new window in default web browser for\n"
        help_text += "videos and explanations on using this screen.\n"
        help_text += "https://www.pippim.com/programs/homa.html#\n"
        # Instead of "Introduction" have self.help_id with "HelpSensors" or "HelpDevices"
        make_button(0, 1, "Help", lambda: g.web_help(self.main_help_id),
                    help_text, "ne", self.img_mag_glass)

        ''' ✘ CLOSE BUTTON  '''
        # noinspection PyTypeChecker
        self.bind("<Escape>", self.exitApp)  # 2025-05-03 pycharm error appeared today
        self.protocol("WM_DELETE_WINDOW", self.exitApp)
        self.close_btn = make_button(0, 2, "Exit", self.exitApp,
                                     "Exit " + self.app_title + ".",
                                     "ne", pic=self.img_close)

    def refreshApp(self, tk_after=True):
        """ Sleeping loop until need to do something. Fade tooltips.
        """

        _who = "refreshApp()"
        self.update_idletasks()

        if not self.winfo_exists():  # Application window destroyed?
            return False  # self.close() has destroyed window

        if killer.kill_now:  # Is system shutting down?
            v0_print(self.printTime(), '\nyt-skip.py refresh() closed by SIGTERM')
            self.exitApp(kill_now=True)
            return False  # Not required because this point never reached.

        now = time.time()  # lost time means suspend initiated outside of HomA
        _delta = now - self.last_refresh_time

        if not self.winfo_exists():  # Application window destroyed?
            return False  # self.close() has set to None

        self.tt.poll_tips()  # Tooltips fade in and out
        self.update()  # process pending tk events in queue

        if not self.winfo_exists():  # Application window destroyed?
            return False  # self.close() has set to None

        # Speedy derivative called by CPU intensive methods.
        if not tk_after:  # Skip tkinter update and 16 to 33ms sleep
            return self.winfo_exists()  # Application window destroyed?

        now = time.time()  # Time changed after .Sensors() and .Rediscover()
        if self.last_refresh_time > now:
            v0_print(self.printTime(), _who, "self.last_refresh_time: ",
                     ext.h(self.last_refresh_time), " >  now: ", ext.h(now))
            now = self.last_refresh_time  # Reset for proper sleep time

        ''' Sleep remaining time to match GLO['YT_REFRESH_MS'] '''
        self.update()  # Process everything in tkinter queue before sleeping
        sleep = GLO['YT_REFRESH_MS'] - int(now - self.last_refresh_time)
        sleep = sleep if sleep > 0 else 1  # Sleep minimum 1 millisecond
        self.after(sleep)  # Sleep until next GLO['YT_REFRESH_MS'] (30 to 60 fps)
        self.last_refresh_time = time.time()

        return self.winfo_exists()  # Return app window status to caller

    def refreshThreadSafe(self):
        """ Prevent self.refreshApp rerunning a second error message during
            first error message waiting for acknowledgement
        """
        self.last_refresh_time = time.time()  # Prevent elapsed time methods
        self.refreshApp(tk_after=False)
        self.after(10)

    def showInfoMsg(self, title, text, icon="information", align="center"):
        """ Show message with thread safe refresh that doesn't invoke rediscovery.

            Can be called from instance which has no tk reference of it's own
                From Application initialize with:   inst.app = self
                From Instance call method with:     self.app.showInfoMsg()
        """

        message.ShowInfo(self, thread=self.refreshThreadSafe, icon=icon, align=align,
                         title=title, text=text, win_grp=self.win_grp)


# Only prints if yt-skip.py started with '-v' or, '-vv' or, '-vvv' parameter.
v1_print(sys.argv[0], "- YouTube Ad Mute and Skip", " | verbose1:", p_args.verbose1,
         " | verbose2:", p_args.verbose2, "\n  | verbose3:", p_args.verbose3,
         " | fast:", p_args.fast, " | silent:", p_args.silent)


def checkVerbose(_v):
    """ Check if requested verbose level is turned on. Automatically passes
        v0_print (verbose 0 is information printing, NOT a verbose level).

        Called by resetSpam() and printTime().
    """
    if p_args.silent:
        return False  # Silent mode turns off all verbose levels

    if _v == 0:
        return True  # v0_print always prints

    if p_args.verbose1 and _v == 1:
        return True  # Verbose level is 1 and matches request of 1

    if p_args.verbose2 and 1 <= _v <= 2:
        return True  # Verbose level is 1 or 2 and matches request of 2
    
    if p_args.verbose3 and 1 <= _v <= 3:
        return True  # Verbose level is 1, 2 or 3 and matches request of 3
    
    return False


''' Global class instances accessed by various other classes '''
root = None  # Tkinter toplevel
app = None  # Application() GUI heart of HomA allowing other instances to reference
cfg = sql.Config()  # Colors configuration SQL records
glo = Globals()  # Global variables instance used everywhere
GLO = glo.dictGlobals  # Default global dictionary. Live read in glo.open_file()

SAVE_CWD = ""  # Save current working directory before changing to program directory
killer = ext.GracefulKiller()  # Class instance for app.Close() or CTRL+C

v0_print()
v0_print(r'  ######################################################')
v0_print(r' //////////////                            \\\\\\\\\\\\\\')
v0_print(r'<<<<<<<<<<<<<<   YouTube Ad Mute and Skip   >>>>>>>>>>>>>>')
v0_print(r' \\\\\\\\\\\\\\                            //////////////')
v0_print(r'  ######################################################')
v0_print(r'                    Started:',
         dt.datetime.now().strftime('%I:%M %p').strip('0'))


def main():
    """ Save current directory, change to ~/homa directory, load app GUI
        When existing restore original current directory.
    """
    global root  # named when main() called
    global app, GLO
    global SAVE_CWD  # Saved current working directory to restore on exit

    ''' Save current working directory '''
    SAVE_CWD = os.getcwd()  # Convention from old code in mserve.py
    if SAVE_CWD != g.PROGRAM_DIR:
        v1_print("Changing from:", SAVE_CWD, "to g.PROGRAM_DIR:", g.PROGRAM_DIR)
        os.chdir(g.PROGRAM_DIR)

    sql.open_homa_db()  # Open SQL History Table for saved configs
    glo.openFile()
    GLO = glo.dictGlobals
    GLO['APP_RESTART_TIME'] = time.time()
    root = tk.Tk()
    root.withdraw()

    ''' Is another copy of yt-skip running? '''
    # result = os.popen("ps aux | grep -v grep | grep python").read().splitlines()
    programs_running = ext.get_running_apps(PYTHON_VER)
    this_pid = os.getpid()  # Don't commit suicide!
    yt_skip_pid = vu_meter_pid = 0  # Running PIDs found later

    ''' Loop through all running programs with 'python' in name '''
    for pid, prg, parameters in programs_running:
        if prg == "yt-skip.py" and pid != this_pid:
            yt_skip_pid = pid  # 'homa.py' found
        if prg == "vu_meter.py" and parameters[1] == "yt-skip":
            # VU meter instance from HomA and not mserve
            vu_meter_pid = pid  # command was 'vu_meter.py stereo yt-skip'

    ''' One or more fingerprints indicating another copy running? '''
    if yt_skip_pid:
        title = "Another copy of yt-skip is running!"
        text = "Cannot start two copies of yt-skip. Switch to the other version."
        text += "\n\nIf the other version crashed, the process(es) still running"
        text += " can be killed:\n\n"
        if yt_skip_pid:
            text += "\t'yt-skip.py' (" + str(yt_skip_pid) + \
                    ") - YouTube Ad Mute and Skip\n"
        if vu_meter_pid:
            text += "\t'vu_meter.py' (" + str(vu_meter_pid) + \
                    ") - VU Meter speaker to microphone\n"
        text += "\nDo you want to kill previous crashed version?"
        v0_print(title + "\n\n" + text)

        def dummy_thread():
            """ Needed for showInfoMsg from root window. """
            root.update()
            root.after(30)

        answer = message.AskQuestion(
            root, title=title, text=text, align='left', confirm='no',
            icon='error', thread=dummy_thread)

        if answer.result != 'yes':
            exit()

        if yt_skip_pid:
            # v0_print("killing yt_skip_pid:", yt_skip_pid)
            if not ext.kill_pid_running(yt_skip_pid):
                v0_print("killing yt_skip_pid FAILED!:", yt_skip_pid)
        if vu_meter_pid:
            # v0_print("killing vu_meter_pid:", vu_meter_pid)
            if not ext.kill_pid_running(vu_meter_pid):
                v0_print("killing vu_meter_pid FAILED!:", vu_meter_pid)

    ''' Open Main Application GUI Window '''
    app = Application(root)  # Main GUI window

    app.mainloop()


if __name__ == "__main__":
    main()

# End of yt-skip.py
