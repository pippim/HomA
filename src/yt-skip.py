#!/usr/bin/python
# -*- coding: utf-8 -*-
# /usr/bin/python3
# /usr/bin/env python  # puts name "python" into top, not "homa.py"
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

# v0_print("PYTHON_VER", PYTHON_VER)

from PIL import Image, ImageTk, ImageDraw, ImageFont

try:
    import subprocess32 as sp
    SUBPROCESS_VER = '32'
except ImportError:  # No module named subprocess32
    import subprocess as sp
    SUBPROCESS_VER = 'native'

import signal  # Shutdown signals
#import logging  # Logging used in pygatt and trionesControl
import argparse  # Command line argument parser
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--fast', action='store_true')  # Fast startup
parser.add_argument('-s', '--silent', action='store_true')  # No info printing
parser.add_argument('-v', '--verbose1', action='store_true')  # Print Overview
parser.add_argument('-vv', '--verbose2', action='store_true')  # Print Functions
parser.add_argument('-vvv', '--verbose3', action='store_true')  # Print Commands
p_args = parser.parse_args()

import json  # For dictionary storage in external file
import copy  # For deepcopy of lists of dictionaries
import re  # For Regex searches
import time  # For now = time.time()
import datetime as dt  # For dt.datetime.now().strftime('%I:%M %p')
import random  # Temporary filenames
import string  # Temporary filenames
#import base64  # Required for Cryptology
#from cryptography.fernet import Fernet  # To encrypt sudo password
from collections import OrderedDict, namedtuple

try:
    reload(sys)  # June 25, 2023 - Without utf8 sys reload, os.popen() fails on OS
    sys.setdefaultencoding('utf8')  # filenames that contain unicode characters
except NameError:  # name 'reload' is not defined
    pass  # Python 3 already in unicode by default

# pprint (dictionary pretty print) is usually installed. But...
pprint_installed = True
try:
    import pprint
except ImportError:
    pprint_installed = False

# Pippim libraries
import sql  # For color options - Lots of irrelevant mserve.py code though
import monitor  # Center window on current monitor supports multi-head rigs
import toolkit  # Various tkinter functions common to Pippim apps
import message  # message.showInfo()
import image as img  # Image processing. E.G. Create Taskbar icon
import timefmt as tmf  # Time formatting, ago(), days(), mm_ss(), etc.
import vu_pulse_audio  # Volume Pulse Audio class pulsectl.Pulse()
import external as ext  # Call external functions, programs, etc.

from homa_common import DeviceCommonSelf, Globals, AudioControl
from homa_common import v0_print, v1_print, v2_print, v3_print


class Application(DeviceCommonSelf, tk.Toplevel):
    """ tkinter main application window
        Button bar: Minimize, Help, Close
    """

    def __init__(self, master=None):
        """ DeviceCommonSelf(): Variables used by all classes
        :param toplevel: Usually <None> except when called by another program.
        """
        DeviceCommonSelf.__init__(self, "Application().")  # Define self.who
        _who = self.who + "__init__():"

        self.isActive = True  # Set False when exiting or suspending
        self.requires = ['ps', 'grep', 'xdotool', 'wmctrl']
        self.installed = []
        self.checkDependencies(self.requires, self.installed)

        if not self.dependencies_installed:
            v0_print(self.formatTime() ,_who, 
                     "Some Application() dependencies are not installed.")
            v0_print(self.requires)
            v0_print(self.installed)

        self.audio = AudioControl()
        ''' TkDefaultFont changes default font everywhere except tk.Entry in Color Chooser '''
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=g.MON_FONT)
        self.text_font = font.nametofont("TkTextFont")  # tk.Entry fonts in Color Chooser
        self.text_font.configure(size=g.MON_FONT)
        ''' TkFixedFont, TkMenuFont, TkHeadingFont, TkCaptionFont, TkSmallCaptionFont,
            TkIconFont and TkTooltipFont - It is not advised to change these fonts.
            https://www.tcl-lang.org/man/tcl8.6/TkCmd/font.htm '''

        self.last_refresh_time = time.time()  # Refresh idle loop last entered time
        self.last_minute = "0"  # Check sunlight percentage every minute
        self.last_second = "0"  # Update YouTube progress every second

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

        app_title = "YouTube Ad Mute and Skip"  # Used to find window ID further down
        self.title(app_title)
        self.btn_frm = None  # Used by buildButtonBar(), can be hidden by edit_pref

        ''' ChildWindows() moves children with toplevel and keeps children on top '''
        self.win_grp = toolkit.ChildWindows(self, auto_raise=False)

        ''' Tooltips() - if --silent argument, then suppress error printing '''
        print_error = False if p_args.silent else True
        self.tt = toolkit.ToolTips(print_error=print_error)

        ''' Set program icon in taskbar. '''
        img.taskbar_icon(self, 64, 'red', 'green', 'blue', char='AS')

        ''' Save Toplevel OS window ID for minimizing window '''
        self.buildButtonBar()  # Must be called after Tooltips defined
        self.update_idletasks()  # Make visible for wmctrl. Verified needed 2025-02-13
        self.getWindowID(app_title)

        ''' When devices displayed show sensors button and vice versa. '''
        self.close_btn = None  # Close button on button bar to control tooltip
        self.main_help_id = "HelpNetworkDevices"  # Toggles to HelpSensors and HelpDevices

        self.main_frm = self.audio_frm = self.sb2 = self.vum = None
        self.pav_sb = None
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

        self.pav_sb = toolkit.CustomScrolledText(
            self.main_frm, state="normal", font=ha_font, borderwidth=15, relief=tk.FLAT)
        toolkit.scroll_defaults(self.pav_sb)  # Default tab stops are too wide
        self.pav_sb.config(tabs=("50", "100", "150"))
        self.pav_sb.grid(row=90, column=0, padx=3, pady=3, sticky=tk.NSEW)
        # 90 rows available before scrollbox and 10 rows available after
        self.main_frm.rowconfigure(90, weight=1)
        self.main_frm.columnconfigure(0, weight=1)

        # Tabs for self.pav_sb created by self.DisplayCommon()
        tabs = ("140", "right", "170", "left", "400", "left",
                "750", "left", "1125", "right")
        self.pav_sb.tag_config("hanging_indent", lmargin2=420)

        def reset_tabs(event):
            """ https://stackoverflow.com/a/46605414/6929343 """
            event.widget.configure(tabs=tabs)

        self.pav_sb.configure(tabs=tabs, wrap=tk.WORD)
        self.pav_sb.bind("<Configure>", reset_tabs)

        line = "Input\tVol.\tApplication\tVideo name\n"
        self.pav_sb.insert("end", line + "\n", "hanging_indent")

        # Display Audio. Rows 0 to 89 available in self
        if not self.audio.isWorking:
            self.showInfoMsg("Watch YouTube",
                             "PulseAudio isn't working or software is missing.")
            return

        ''' Create audio_frm for columns 1, 2, 3: labels, values, scrollbox '''
        self.audio_frm = ttk.Frame(self.main_frm, borderwidth=g.FRM_BRD_WID,
                                   padding=(2, 2, 2, 2), relief=tk.RIDGE)
        self.audio_frm.grid(column=0, row=0, sticky=tk.NSEW)
        self.audio_frm.grid_columnconfigure(1, minsize=g.MON_FONTSIZE*15, weight=1)
        self.audio_frm.grid_columnconfigure(2, minsize=700, weight=1)  # Status self.pav_sb

        # Status scroll box in third column
        self.sb2 = toolkit.CustomScrolledText(self.audio_frm, state="normal", font=g.FONT,
                                              height=11, borderwidth=15, relief=tk.FLAT)
        toolkit.scroll_defaults(self.sb2)  # Default tab stops are too wide

        # Tabs for self.sb2 (scrollbox) created by monitorVideos
        _tabs2 = ("140", "right", "160", "left")
        self.sb2.tag_config("indent2", lmargin2=180)

        def _reset_tabs2(event):
            """ https://stackoverflow.com/a/46605414/6929343 """
            event.widget.configure(tabs=_tabs2)

        self.sb2.configure(tabs=_tabs2, wrap=tk.WORD)
        self.sb2.bind("<Configure>", _reset_tabs2)
        self.sb2.grid(row=0, column=2, rowspan=9, padx=3, pady=3, sticky=tk.NSEW)
        # ScrollText with instructions third column row span 9
        _sb2_text = "INSTRUCTIONS:\n\n"
        _sb2_text += "1. Messages automatically scroll when videos start.\n\n"
        _sb2_text += '2. Messages can be copied by highlighting text and\n'
        _sb2_text += '     typing <Control> + "C".\n\n'
        _sb2_text += "3. Click Help button below for more instructions.\n\n"
        self.sb2_time = "00:00:00.00"  # Last formatted time
        self.insertSB2(_sb2_text)

        self.update_idletasks()

        # ROWS: Sink Input Index, PA PID, PA Application, PA name
        #       X11 Window Number, Full Screen?, Window App, Window Name
        self.text_index = self.addRow(0, "Sink input #:", "N/A")  # Long Integer
        self.text_pid = self.addRow(1, "Process ID (PID):", 0, _type="Int")
        self.text_pa_app = self.addRow(2, "PulseAudio App:", "N/A")
        self.text_is_YouTube = self.addRow(3, "YouTube?:", "N/A")
        self.text_wn_xid_hex = self.addRow(4, "Window number:", "N/A")
        self.text_is_fullscreen = self.addRow(5, "Fullscreen?:", "N/A")
        self.text_yt_start = self.addRow(6, "YouTube Start:", "N/A")
        self.text_status = self.addRow(7, "Status:", "N/A")
        self.text_duration = self.addRow(8, "Duration:", "N/A")

        ''' Create vum_frm for columns 1, 2, 3: labels, values, scrollbox '''
        self.vum_frm = ttk.Frame(self.main_frm, borderwidth=g.FRM_BRD_WID,
                                 padding=(2, 2, 2, 2), relief=tk.RIDGE)
        self.vum_frm.grid(column=3, row=0, rowspan=99, sticky=tk.NSEW)
        self.vum_frm.grid_rowconfigure(0, weight=1)
        #self.vum_frm.grid_columnconfigure(0, minsize=g.MON_FONTSIZE*15, weight=1)
        #self.vum_frm.grid_columnconfigure(1, minsize=700, weight=1)
        self.vum = toolkit.VolumeMeters('yt-skip', self.vum_frm)
        self.update()  # paint meters

        self.vum.reset_history_size(12)  # 2025-07-20 Change 8 to 12.
        self.vum.spawn()  # Daemon to populate Amplitude in files
        self.vum.set_height()
        global pav
        pav = self.audio.pav

        while not os.path.isfile(self.vum.AMPLITUDE_LEFT_FNAME):
            self.refreshApp()  # wait another 16ms to 33ms for file to appear.

        # self.vars {} dictionary to reduce class attributes
        self.vars = {  # pav_ = Pulse audio volume, wn_ = Wnck Window (GNOME)
            "pav_start": 0.0, "pav_index": "", "pav_volume": 0.0,
            "pav_corked": False, "pav_application": "", "pav_name": "",
            "yt_start": 0.0, "yt_index": "", "yt_duration": 0.0,
            "av_start": 0.0, "skip_check": 0.0, "last_name": "",
            "ad_start": 0.0, "ad_index": "", "ad_duration": 0.0,
            "video_start": 0.0, "video_index": "", "video_duration": 0.0,
            "wn_name": "", "wn_xid_hex": ""  # Could be YT or not YT
        }

        self.this_stat = os.stat(glo.config_fname)
        self.last_stat = self.this_stat
        self.skip_clicked = 0.0  # Sometimes one click doesn't work

        self.monitorVideos()

    def insertSB2(self, msg, _time=None):
        """ Shared local function """
        _who = self.who + "insertSB2():"

        # Suppress repeating HH: then MM: then SS
        _time = self.formatTime(_time=_time)
        _h = _time[0:3]  # HH: <--- suppress duplicates
        _m = _time[3:6]  # MM: <--- suppress duplicates
        _s = _time[6:8]  # SS  <--- suppress duplicates
        _f = _time[8:]   # .FF <--- always prints
        if _time[0:3] == self.sb2_time[0:3]:
            _h = "   "  # Suppress hour which hasn't changed
            if _time[3:6] == self.sb2_time[3:6]:
                _m = "   "  # Suppress hour and minutes are the same
                if _time[6:8] == self.sb2_time[6:8]:
                    _s = "   "  # Suppress hour, minutes and seconds
        _t = _h + _m + _s + _f
        _t = _t.replace("0", " ", 1) if _t.lstrip().startswith("0") else _t

        _line = "\t" + _t + "\t" + msg + "\n"
        self.sb2.insert("end", _line, "indent2")
        self.sb2.see("end")
        self.sb2_time = _time

    def formatTime(self, _time=None):
        """ Format passed time or current time if none passed.
        import datetime
        """
        _who = self.who + "formatTime():"
        if _time:
            dt_time = dt.datetime.fromtimestamp(_time)
        else:
            dt_time = dt.datetime.now()

        formatted_time = dt_time.strftime("%H:%M:%S.") + \
            dt_time.strftime("%f")[:2]
        return formatted_time

    def buildPavSB(self, _sink_inputs):
        """ Build self.pav_sb
        :return: _asi (Active Sink Input tuple)
        """
        self.pav_sb.delete("3.0", "end")  # delete all but headings
        _asi = ()  # named tuple of last active sink input
        for _si in reversed(_sink_inputs):
            if _si.application == "ffplay":
                _name = self.ffplay_name  # 2025-07-19 First run this is blank?
            else:
                _name = _si.name
            _line = str(_si.index) + "\t" + str(_si.volume) + "\t"
            #_line += str(_si.application) + "\t" + toolkit.normalize_tcl(_name)
            _line += str(_si.application) + "\t" + str(_name)  # No normalize for Text
            self.pav_sb.insert("end", _line + "\n", "hanging_indent")
            # _si. 'index corked mute volume name application pid user')
            if _si.corked is True:
                continue  # Corked will not count as the last active
            # Do something for non-corked (active) sink-inputs
            if bool(_asi):
                continue  # Already have last active sink input
            _asi = _si

        try:
            _asi = _asi if bool(_asi) else last_sink_inputs[-1]  # No active inputs fallback
        except IndexError:
            v0_print(self.formatTime(), _who, "Catastrophic error. No Sink Inputs")
            return ()

        self.vars["pav_start"] = time.time()
        self.vars["pav_index"] = _asi.index
        self.vars["pav_application"] = _asi.application
        self.vars["pav_name"] = _asi.name
        self.vars["pav_volume"] = _asi.volume
        self.vars["pav_corked"] = _asi.corked
        self.vars["wn_found"] = False  # Reset last MatchWindow() results
        self.vars["wn_xid_hex"] = "N/A"

        return _asi

    def matchWindow(self):
        """ Match window to pav. _input is active sink input from PulseAudio
            If found, display fullscreen status in column 2
            Before calling, self.buildPavSB() has set all self.vars to null.

                WRONG WRONG

            When a new sink appears it can happen when Video switches to an
            Ad or when user pauses video. If YouTube is still fullscreen and
            video name matches what was playing, don't toss out all variables.

            If new sink is for a stale window or for a windowless sound input
            then keep the old pulse audio info and self.vars[] lists in memory.

            Once a YouTube is in memory it should stay in video status scrolled
            Text widget. The lower pulse audio scrolled Text widget will have
            each active sink input.
        """
        _who2 = self.who + "matchWindow():"
        self.mon.make_wn_list()  # Make Windows List
        _name = self.asi.name
        _app = self.asi.application
        _pid = self.asi.pid  # When PID reappears, use last diagnosis
        #text_pid.set(str(self.asi.pid))
        if _name == "Playback Stream" and _app.startswith("Telegram"):
            _name = "Media viewer"  # Telegram in mon

        if self.mon.get_wn_by_name(_name, pid=self.asi.pid):
            #text_is_fullscreen.set(str(self.mon.wn_is_fullscreen))  # Boolean
            pass  # Drop down to set window name in scroll box
        else:
            if _app == 'ffplay':
                _name = self.getVideoName(_pid)
            else:
                #v0_print(self.formatTime(), _who2, "Matching window not found:")
                #v0_print("  Name:", _name, " | PID:", self.asi.pid)
                #v0_print("  Application:", _app)
                # Rewind last self.pav_sb text entry?
                pass

            #self.vars["yt_start"] = 0.0  # 2025-07-15 comment out
            #self.vars["yt_duration"] = 0.0  # 2025-07-15 comment out
            self.vars["wn_found"] = False
            self.vars["wn_xid_hex"] = "N/A"
            return False

        ''' self.sb2 (scrollbox Text) processing 
            1) 99:99:99.999 New Sink Input Index: 999
            2) 99:99:99.999 YouTube video: Start of name(25)...
                              ...End of Name
               99:99:99.999 Forced fullscreen window 0x3400034
            3) 99:99:99.999 Video color Xxxx found at [9999, 9999]
            4) 99:99:99.999 Ad muted
               99:99:99.999 Waiting 4.7 seconds for Skip Ad Button to appear
               99:99:99.999 Skip Ad Button color Xxxx NOT found at [9999, 9999]
               99:99:99.999 Skip Ad Button color Xxxx found at [9999, 9999]
               99:99:99.999 Skip Ad Button took 99 seconds to appear
               99:99:99.999 Skip Ad Button clicked
            5) 99:99:99.999 New Sink Input Index: 999
            6) 99:99:99.999 Video color Xxxx found at [9999, 9999]
            7) 99:99:99.999 Waiting for new Sink Input...
        '''

        self.vars["wn_found"] = True
        self.vars["wn_xid_hex"] = self.mon.wn_xid_hex

        if _name.endswith(" - YouTube"):
            if _name != self.vars["last_name"]:
                self.vars["yt_start"] = self.vars["pav_start"]
                self.vars["yt_duration"] = 0.0
                self.sb2_time = "00:00:00.00"  # Force full time to print
                self.insertSB2("YouTube Video: " + _name, self.vars["yt_start"])

                self.vars["last_name"] = _name
                self.vars["last_start"] = self.vars["yt_start"]
            else:
                self.vars["yt_start"] = self.vars["last_start"]

            # Ad has started or video is playing, find out which one
            self.vars["ad_start"] = 0.0
            self.vars["video_start"] = 0.0
        else:
            # Can be a Firefox sound (Tim-Ta) or a non-YouTube video playing
            pass

        return True

    def getVideoName(self, _pid):
        """ If _pid = self.ffplay_pid, return self.ffplay_name and return.
            Otherwise run `ps -ef | grep ffplay` and parse parameters.
        """
        _who = self.who + "getVideoName():"
        # ps -ef | grep ffplay PARAMETERS.../song name
        if _pid == self.ffplay_pid:
            return self.ffplay_name

        result = os.popen("ps -ef | grep ffplay | grep -v grep").read().strip()
        self.ffplay_pid = _pid
        try:
            self.ffplay_name = result.split("ffplay -autoexit ")[1]
            self.ffplay_name = self.ffplay_name.split(" -ss ")[0]
            self.ffplay_name = self.ffplay_name.split(os.sep)[-1]
        except IndexError:
            self.ffplay_name = "Simply DirectMedia Layer"  # Old name
        return self.ffplay_name

    def waitAdOrVideo(self):
        """ YouTube PulseAudio sink-input is starting up when:
                yt_start != 0, ad_start = 0 and video_start = 0.

            Force fullscreen in order to discover progress bar color.

            os.stat() configuration file to see if modification time
                has changed. If changed, reread coordinates and colors.

            Find out if Ad or Video by testing colors @ coordinates.

            If stuck in "A/V Check" loop for two seconds assume video
                already playing.
        """

        _who = self.who + "self.waitAdOrVideo():"
        self.this_stat = os.stat(glo.config_fname)
        if self.this_stat.st_mtime != self.last_stat.st_mtime:
            glo.openFile()
        self.last_stat = self.this_stat

        try:
            _x, _y = GLO["YT_AD_BAR_POINT"]
        except AttributeError:
            # TODO: display message and exit App.
            return  # This will repeat test forever but overhead is low.

        if not bool(self.asi):
            v0_print(self.formatTime(), _who, "buildPavSB has never been run")
            return  # buildPavSB has never been run

        if self.vars["wn_found"] is False:
            return  # sink-input has no window, can't be Firefox

        if self.vars["av_start"] == 0.0:
            self.vars["av_start"] = time.time()  # "A/V check" start time
            # Will wait maximum of two seconds before assuming video is playing

        if self.mon.wn_is_fullscreen is False:
            # If not full screen, force it.
            #os.popen("wmctrl -ir " + str(self.mon.wn_xid_hex) +
            #         " -b toggle,fullscreen")  # YT decorations still active
            os.popen('xdotool key f')  # Full Screen removes YT decorations
            self.mon.wn_is_fullscreen = True
            self.updateRows()
            self.insertSB2("Window forced fullscreen:" + str(self.mon.wn_xid_hex))

        _tk_clr = self.pi.get_colors(_x, _y)  # Get color
        if _tk_clr == GLO["YT_AD_BAR_COLOR"] and self.vars["ad_start"] == 0.0:
            self.vars["ad_start"] = self.vars["pav_start"]
            self.vars["av_start"] = 0.0
            self.vars["video_start"] = 0.0  # 2025-07-15 Extra insurance
            # 	17:13:09.46	Ad has started on index: 1231
            # 	17:13:09.87	Ad has started on index: 1231
            # If already muted, this is a duplicate
            _vol = pav.get_volume(str(self.asi.index), print_error=False)
            if _vol == 24.2424:
                v0_print(self.formatTime(), _who,
                         "Sink doesn't exist: " + str(self.vars["pav_index"]))
            elif _vol != 0:
                pav.set_volume(str(self.asi.index), 0)  # Set volume to zero
                self.updateRows()
                self.insertSB2("Ad muted on index: " + str(self.vars["pav_index"]),
                               self.vars["ad_start"])
            else:
                # Checking too soon after last mute command issued to PAV
                v1_print(self.formatTime(), _who,
                         "Already muted: " + str(self.vars["pav_index"]))
            return

        elif _tk_clr == GLO["YT_VIDEO_BAR_COLOR"] and self.vars["video_start"] == 0.0:
            #self.vars["video_start"] = time.time()
            self.vars["video_start"] = self.vars["pav_start"]
            self.vars["av_start"] = 0.0
            self.vars["ad_start"] = 0.0  # 2025-07-14 Extra insurance
            self.updateRows()
            self.insertSB2("Video playing on index: " +
                           str(self.vars["pav_index"]), self.vars["video_start"])
            return

        else:
            v3_print(_who)
            v3_print("  Color found at: [" + str(_x) + "," + str(_y) + "]",
                     "is:", _tk_clr)
            v3_print("  Waiting for Ad or Video color to appear...")

        if time.time() > self.vars["av_start"] + 2.0\
                and self.vars["ad_start"] == 0.0 and self.vars["video_start"] == 0.0:
            #self.vars["video_start"] = self.vars["yt_start"]  # Time rewinds is weird
            self.vars["video_start"] = time.time()  # Duration resets to 0
            self.vars["av_start"] = 0.0
            self.vars["ad_start"] = 0.0
            self.updateRows()
            self.insertSB2("Assume video on index: " +
                           str(self.vars["pav_index"]), self.vars["video_start"])
            v1_print(_who, "A/V Check timeout. Assume video continuing.")

    # noinspection SpellCheckingInspection
    def waitAdSkip(self):
        """ YouTube Ad is running.
            ad_started > 0 and video_started = 0.
            Wait 4.7 seconds.
            If color matches, send click to skip button coordinates.
        """

        _who = self.who + "waitAdSkip():"
        if time.time() < 4.7 + self.vars["ad_start"]:
            return  # Too soon to check because ad can be white

        self.updateDuration()  # Force "Skip Color check" status display
        try:
            _x, _y = GLO["YT_SKIP_BTN_POINT"]
        except AttributeError:  # Coordinates for skip button unknown
            return  # This will repeat test forever but overhead is low.

        _tk_clr = self.pi.get_colors(_x, _y)  # Get color
        if _tk_clr != GLO["YT_SKIP_BTN_COLOR"]:
            if self.skip_clicked > 0.0:
                # Skip button clicked last loop turn off checking.
                self.vars["ad_start"] = 0.0  # Turn off ad running
                self.skip_clicked = 0.0  # Reset for next skip click test cycle
            else:
                v3_print(_who)
                v3_print("  Color found at: [" + str(_x) + "," + str(_y) + "]",
                         "is:", _tk_clr)
                v3_print("  Waiting for Skip Button color to appear...")
            return  # Not skip button color

        # .34 too short of time for YouTube to make button disappear. Wait .5
        if time.time() < self.skip_clicked + 0.5:
            return  # Too soon to assume last click failed

        ext.t_init("4 xdotool commands")
        _active = os.popen('xdotool getactivewindow').read().strip()

        os.popen('xdotool mousemove ' + str(_x) + ' ' + str(_y) +
                 ' click 1 sleep 0.01 mousemove restore')

        self.skip_clicked = time.time()  # When skip color disappears, it is success
        self.insertSB2("Skip Button clicked")

        if len(_active) > 4:
            os.popen('xdotool windowfocus ' + _active)
            os.popen('xdotool windowactivate ' + _active)
        else:
            v0_print(self.formatTime(), _who, "Could not find active window. Result:", _active)
        ext.t_end("no_print")  # 4 xdotool commands: 0.0370068550 to 0.1740691662

    def updateRows(self):
        """ Update rows with pulse audio active sink input (asi)
            and matching window (self.mon.wn) attributes.

            2025-07-07 TODO: Relocate to only call when sink or window changes.
        """
        self.text_index.set(str(self.asi.index))  # Long Integer
        self.text_pid.set(self.asi.pid)
        self.text_pa_app.set(self.asi.application)  # Could be UTF-8

        def set_time(_val):
            """ Format date if not zero. """
            if _val == 0.0:
                return "N/A"
            return self.formatTime(_val)

        self.text_wn_xid_hex.set(str(self.vars["wn_xid_hex"]))  # May already be N/A
        self.text_yt_start.set(set_time(self.vars["yt_start"]))  # Set to N/A if zero
        #text_status.set(set_time(self.vars["ad_start"]))
        #text_duration.set(set_time(self.vars["video_start"]))

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
        _who2 = self.who + "addRow():"
        label = ttk.Label(self.audio_frm, text=label, font=g.FONT)
        label.grid(row=row_no, column=0, sticky=tk.NSEW, padx=15, pady=10)

        if _type == "String":
            _var = tk.StringVar()
        elif _type == "Int":
            _var = tk.IntVar()
        else:
            v0_print(self.formatTime(), _who, "Unknown tk variable type:", _type)
            return None

        _var.set(_val)
        text = ttk.Label(self.audio_frm, textvariable=_var, font=g.FONT)
        text.grid(row=row_no, column=1, sticky=tk.NSEW, padx=15)
        if self.tt and tt_text:
            self.tt_add(label, tt_text)
        return _var

    def updateDuration(self):
        """ Update Status and Duration in 8th & 9th rows.
            Called every second.

            Status:   A/V check / Ad playing / Video playing /
                      Skip Color check / NOT YouTube

            Duration: 99:99:99.99
        """
        _who2 = self.who + "updateDuration():"
        _now = time.time()
        _status = ""
        old_status = self.text_status.get()
        _dur = 0.0

        if self.vars["ad_start"] > 0.0 and _now > 4.7 + self.vars["ad_start"]:
            _dur = _now - self.vars["ad_start"] - 4.7
            _status = "Skip Color check"
            if old_status != _status:
                self.insertSB2(_status)
        elif self.vars["ad_start"] > 0.0:
            _dur = _now - self.vars["ad_start"]
            _status = "Ad playing"
        elif self.vars["video_start"] > 0.0:
            _dur = _now - self.vars["video_start"]
            _status = "Video playing"
        elif self.vars["yt_start"] > 0.0:
            _dur = _now - self.vars["pav_start"]
            _status = "A/V check"
            if old_status != _status:
                self.insertSB2(_status)
        elif self.vars["wn_name"] != "":
            _dur = _now - self.vars["pav_start"]
            _status = "NOT YouTube"
            if old_status != _status:
                self.insertSB2(_status)

        self.text_status.set(_status)
        self.text_duration.set(tmf.mm_ss(_dur))

    def monitorVideos(self):
        """ Monitor Pulse Audio for new sinks.

            2025-07-10 TODO:
                New variable GLO['YT_SKIP_BTN_WAIT'] = 4.7
                New variable GLO['YT_SKIP_BTN_WAIT2'] = 0.3

        FULLSCREEN NOTES:
            Wnck.Screen.Window.fullscreen() isn't supported in version 3.18.
            wmctrl -ir hex_win -b toggle,fullscreen doesn't remove YT menus.
            Use 'xdotool key "f"' instead.

        AD SKIP NOTES:
            False positives when only looking for a single white dot because
                looking too soon < 4.7 seconds will see white dot in ad
                and not in the ad skip button resulting in ad pause on click.
            Gtk mouse click only works on GTK windows
            Python pyautogui click only works on primary monitor
            Browser previous history (<ALT>+<Left Arrow>) followed by forward
                (<ALT>+<Right Arrow>) works sometimes but can sometimes take
                4.7 seconds which an Ad skip Button Click would take. Sometimes
                YouTube restarts video at beginning which totally breaks flow.
            Cannot skip Ad on YouTube using keyboard:
                https://webapps.stackexchange.com/questions/100869/
                    keyboard-shortcut-to-close-the-ads-on-youtube
            Use:
                `xdotool mousemove <x> <y> click 1 sleep 0.01 mousemove restore`

        """
        _who = self.who + "monitorVideos():"

        last_sink_inputs = []  # Force reread
        # Loop forever until DisplayCommon() window closed
        while self and self.winfo_exists():
            if not self.refreshApp():
                break
            try:
                self.vum.update_display()  # paint LED meters reflecting amplitude
            except (tk.TclError, AttributeError):
                break  # Break in order to terminate vu_meter.py below

            sink_inputs = pav.get_all_inputs()
            self.last_refresh_time = time.time()  # set sleep duration

            if sink_inputs != last_sink_inputs:
                self.asi = self.buildPavSB(sink_inputs)  # asi = Active Sink Input named tuple
                self.mon.make_wn_list()
                if self.matchWindow():
                    v1_print(_who, "Matching window:", self.mon.wn_dict['xid_hex'])
                else:
                    v1_print(_who, "Matching window NOT FOUND!")

                self.updateRows()  # 2025-07-03 - Handles self.mon.wn_dict is blank.
                last_sink_inputs = sink_inputs  # deepcopy NOT required

            # YouTube started but Ad or Video status unknown?
            if self.vars["yt_start"] != 0.0 and self.vars["ad_start"] == 0.0 and \
                    self.vars["video_start"] == 0.0:
                self.waitAdOrVideo()  # Setup if Ad or Video is running

            # Is YouTube Ad intercept active?
            if self.vars["ad_start"] != 0.0 and self.vars["video_start"] == 0.0:
                self.waitAdSkip()  # Setup if Ad or Video is running

            # Update YouTube progress every second
            second = ext.h(time.time()).split(":")[2].split(".")[0]
            # Current second of "HH:MM:SS.ff"
            if second != self.last_second:
                self.updateDuration()  # Update status and duration
                self.last_second = second  # Wait for second change to check again

        if self.vum and ext.check_pid_running(self.vum.pid):
            self.vum.terminate()  # Also closed in exitApp()

    def getWindowID(self, title):
        """ Use wmctrl to get window ID in hex and convert to decimal for xdotool
            2025-06-13 (It's Friday 13th!) Test new self.mon.wm_xid_int
        """
        _who = self.who + "getWindowID():"
        GLO['WINDOW_ID'] = None  # yt-skip Window ID, must restore after reading GLO
        v2_print(_who, "search for:", title)

        if not self.checkInstalled('wmctrl'):
            v2_print(_who, "`wmctrl` is not installed.")
            return
        if not self.checkInstalled('xdotool'):
            v2_print(_who, "`xdotool` is not installed.")
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

        # 2025-06-13 Test new self.mon.wm_xid_int
        self.mon = monitor.Monitors()
        self.mon.make_wn_list()  # Make Wnck list of all windows
        # if self.mon.get_wn_by_name(title):
        # GLO['WINDOW_ID'] = self.mon.wn_xid_int

        v2_print(_who, "GLO['WINDOW_ID']:", GLO['WINDOW_ID'])
        if GLO['WINDOW_ID'] is None:
            v0_print(self.formatTime(), _who, "ERROR `wmctrl` could not find Window.")
            v0_print("Search for title failed: '" + title + "'.\n")

    def exitApp(self, kill_now=False, *_args):
        """ <Escape>, X on window, 'Exit from dropdown menu or Close Button"""
        _who = self.who + "exitApp():"

        ''' Is it ok to stop processing? - Make common method... '''
        msg = None

        if msg and not kill_now:  # Cannot suspend when other jobs are active
            self.showInfoMsg("Cannot Close now.", msg, icon="error")
            v0_print(self.formatTime(), _who, "Aborting Close.", msg)
            return

        sql.close_homa_db()  # Close SQL History Table

        self.win_grp.destroy_all(tt=self.tt)  # Destroy Calculator and Countdown
        #if self.vum and self.vum.pid:
        #    ext.kill_pid_running(self.vum.pid)  # Already killed on exit
        self.isActive = False  # Signal closing down so methods return

        if self.vum and ext.check_pid_running(self.vum.pid):
            self.vum.terminate()  # Also closed in monitorVideos()

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
        _who = self.who + "minimizeApp():"
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
                                     "Exit YouTube Ad Mute and Skip.",
                                     "ne", pic=self.img_close)

    def refreshApp(self, tk_after=True):
        """ Sleeping loop until need to do something. Fade tooltips.
        """

        _who = self.who + "refreshApp()"
        self.update_idletasks()

        if not self.winfo_exists():  # Application window destroyed?
            return False  # self.close() has destroyed window

        if killer.kill_now:  # Is system shutting down?
            v0_print(self.formatTime(), '\nyt-skip.py refresh() closed by SIGTERM')
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

        minute = ext.h(now).split(":")[1]  # Current minute for this hour
        if minute != self.last_minute:  # Get sunlight percentage every minute
            v2_print(_who, ext.t(), "minute changed:", minute)

        now = time.time()  # Time changed after .Sensors() and .Rediscover()
        if self.last_refresh_time > now:
            v0_print(self.formatTime(), _who, "self.last_refresh_time: ",
                     ext.h(self.last_refresh_time), " >  now: ", ext.h(now))
            now = self.last_refresh_time  # Reset for proper sleep time

        ''' Sleep remaining time to match GLO['REFRESH_MS'] '''
        self.update()  # Process everything in tkinter queue before sleeping
        sleep = GLO['REFRESH_MS'] - int(now - self.last_refresh_time)
        sleep = sleep if sleep > 0 else 1  # Sleep minimum 1 millisecond
        if sleep == 1:
            v0_print(self.formatTime(), _who, "Only sleeping 1 millisecond")
        self.after(sleep)  # Sleep until next GLO['REFRESH_MS'] (30 to 60 fps)
        self.last_refresh_time = time.time()

        return self.winfo_exists()  # Return app window status to caller

    def refreshThreadSafe(self):
        """ Prevent self.refreshApp rerunning a second error message during
            first error message waiting for acknowledgement
        """
        self.last_refresh_time = time.time()  # Prevent resume from suspend
        self.refreshApp(tk_after=False)
        self.after(10)
        #self.update()  # Suspend button stays blue after mouseover ends?

    def showInfoMsg(self, title, text, icon="information", align="center"):
        """ Show message with thread safe refresh that doesn't invoke rediscovery.

            Can be called from instance which has no tk reference of it's own
                From Application initialize with:   inst.app = self
                From Instance call method with:     self.app.showInfoMsg()
        """

        message.ShowInfo(self, thread=self.refreshThreadSafe, icon=icon, align=align,
                         title=title, text=text, win_grp=self.win_grp)


v1_print(sys.argv[0], "- YouTube Ad Mute & Skip", " | verbose1:", p_args.verbose1,
         " | verbose2:", p_args.verbose2, " | verbose3:", p_args.verbose3,
         "\n  | fast:", p_args.fast, " | silent:", p_args.silent)

''' Global class instances accessed by various other classes '''
root = None  # Tkinter toplevel
app = None  # Application() GUI heart of HomA allowing other instances to reference
# 2025-06-19 Why does every class have "self.app" when they could use "app" instead?
cfg = sql.Config()  # Colors configuration SQL records
glo = Globals()  # Global variables instance used everywhere
GLO = glo.dictGlobals  # Default global dictionary. Live read in glo.open_file()
pav = None  # PulseAudio sinks. Initialize in Application() -> AudioControl()

SAVE_CWD = ""  # Save current working directory before changing to program directory
killer = ext.GracefulKiller()  # Class instance for app.Close() or CTRL+C

v0_print()
v0_print(r'  ######################################################')
v0_print(r' //////////////                            \\\\\\\\\\\\\\')
v0_print(r'<<<<<<<<<<<<<<   yt-skip - Ad Mute & Skip   >>>>>>>>>>>>>>')
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
                    ") - YouTube Ad Mute & Skip\n"
        if vu_meter_pid:
            text += "\t'vu_meter.py' (" + str(vu_meter_pid) + \
                    ") - VU Meter speaker to microphone\n"
        text += "\nDo you want to kill previous crashed version?"

        v0_print(title + "\n\n" + text)
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

# End of homa.py
