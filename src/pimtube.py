#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: Pippim
License: GNU GPLv3
Source: This repository
Description: pimtube - Pippim YouTube Media Player
"""

from __future__ import print_function  # Must be first import
from __future__ import with_statement  # Error handling for file opens
import warnings  # 'warnings' advises which methods aren't supported
warnings.filterwarnings("ignore", "ResourceWarning")  # PIL python 3 unclosed file

#==============================================================================
#
#       pimtube.py - Pippim YouTube Media Player
#
#       Feb. 25 2025 - Copy Playlists() class from mserve.py (4,700 lines)
#
#==============================================================================

'''

2025-03-20 - Many problems trying to get various Python 3.x versions working
on a new project so I want to create a Python 3.13.2 virtual environment (venv):

1) Current partition is filling up so want to use /mnt/new partition instead of
/bin/usr.
2) Do not want to impact existing Python 3 installation
3) Do not want to impact existing apt functionality so apt get install can't be used
4) Want existing libraries in /usr/bin to be used unless incompatible in
which case pip would be used to install new versions in /mnt/new partition.

I think I'm basically looking for a deadsnakes tarball but I'm not sure.
Any ideas?

pimtube.py was created taking 4,700 lines of code out of mserve.py. This was
to reduce the size of mserve.py from 24k lines of code. At the same time more
functionality was added.

pimtube.py usage:

1) Open Youtube in normal browser window.
2) Right click on video you want to play and select "Copy Clean Link (U)"
    E.G. https://www.youtube.com/watch?v=RGlZ4AlAOtg Instead of regular copy:
    https://www.youtube.com/watch?v=RGlZ4AlAOtg&pp=ygUOZGlhbG9ndWUgd29ya3M%3D
3) Run `pimtube.py`
4) Right click within the "New videos" frame and select "Paste from clipboard"
5) Right click on the video image that appears and select "Play"
6) A new chromium window is opened using selenium.
7) The video is played in YouTube - Move to monitor and set full screen.
8) Each second of video is logged. If commercial (every 5 minutes), proceed to Step 9)
9) Back button is sent, screen automatically goes non-full screen
10) Forward button is sent, another commercial can start up if so go back to step 9)
11) Advance video 5 seconds with right arrow if time < last logged second + 5
12) Go back to 8) until video ends.

2025-03-05 NOTE: every 10 minutes of 90 minute video two commercials appear:
    https://www.youtube.com/watch?v=RXGw4YpZE6s

2025-03-21: https://www.youtube.com/watch?v=nJR1g2AZufU&t=749s reload fails!
    Play video and pause at 12 minute mark for a long time. Come back to resume
    playing and it fails to start. Try to restart from beginning and YouTube
    automatically appends &t=749s and starting at time fails. Manually remove
    suffix and video successfully plays.
    
    In a new private window same thing except it starts up with three paused
    ads.

---

Future enhancement based on how mserve.py does it now:

Open Treeview with 1 row per video:

    Image & status             Channel          Attributes

   +-----------------+         The Duran        New / Viewed on
   |      Image      | NEW     Duration         99 Comments
   +-----------------+         Title            9 posted by me

NOTE: "NEW" can be replaced with 100% (viewed) or 50% if half watched.

Right click on row for menu. Option 1 is play

Write comment. Post it under video and email it to yourself in order to:

    1) monitor comment deletions by Google.
    2) have record of what you posted where and when in case others plagiarize.
    3) mass datamine emails to write a book of comments. 

'''

''' check configuration. '''
import inspect
import os
os.environ["SUDO_PROMPT"] = ""  # Change prompt "[sudo] password for <USER>:"

try:
    filename = inspect.stack()[1][1]  # If there is a parent, it must be 'y'
    parent = os.path.basename(filename)
    if parent != 'y':
        print("pimtube.py called by unrecognized:", parent)
        exit()
except IndexError:  # list index out of range
    ''' 'y' hasn't been run to get global variables or verify configuration '''
    #import mserve_config as m_cfg  # Differentiate from sql.Config as cfg

    caller = "pimtube.py"
    import global_variables as g
    g.init(appname="pimtube")  # PimTube for YouTube set ~/.local/share/pimtube
    g.HELP_URL = "https://www.pippim.com/programs/homa.html#"

import sys
PYTHON_VERSION = sys.version

try:
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.font as font
    import tkinter.filedialog as filedialog
    import tkinter.messagebox as messagebox
    import tkinter.scrolledtext as scrolledtext
    PYTHON_VER = "3"
except ImportError:  # Python 2
    import Tkinter as tk
    import ttk
    import tkFont as font
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox
    import ScrolledText as scrolledtext
    PYTHON_VER = "2"
# print ("Python version: ", PYTHON_VER)

from PIL import Image, ImageTk  # For MoveTreeviewColumn

import signal  # Shutdown signals
import sqlite3  # Was only used for error messages but needed sql. in front


try:
    import subprocess32 as sp
    SUBPROCESS_VER = '32'
except ImportError:  # No module named subprocess32
    import subprocess as sp
    SUBPROCESS_VER = 'native'

import sys
import logging
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--fast', action='store_true')  # Fast startup
parser.add_argument('-s', '--silent', action='store_true')  # No info printing
parser.add_argument('-v', '--verbose1', action='store_true')  # Print Overview
parser.add_argument('-vv', '--verbose2', action='store_true')  # Print Functions
parser.add_argument('-vvv', '--verbose3', action='store_true')  # Print Commands
p_args = parser.parse_args()

# from ttkwidgets import CheckboxTreeview  # 2025-02-12 - Import not used

# python standard library modules
import json  # For dictionary storage in external file
import copy  # For deepcopy of lists of dictionaries
import re  # For Regex searches
import time
import datetime as dt  # For dt.datetime.now().strftime('%I:%M %p')
from collections import OrderedDict, namedtuple
import re                   # w, h, old_x, old_y = re.split(r'\D+', geom)
import copy
import traceback  # To display call stack (functions that got us here)
import locale  # Use decimals or commas for float remainder?
import webbrowser
import requests  # retrieve YouTube thumbnail images Python Version 2.7 works not 3.5
import textwrap  # Wrap long text string into treeview column
from io import BytesIO  # convert YouTube thumbnail images to TK image format
try:
    import subprocess32 as sp
    SUBPROCESS_VER = '32'
except ImportError:  # No module named subprocess32
    import subprocess as sp
    SUBPROCESS_VER = 'native'

# Pippim modules
import global_variables as g
if g.USER is None:
    print('toolkit.py was forced to run g.init()')
    g.init()
import toolkit          # Tkinter methods
import message          # Rename column heading (AskString)
import external as ext  # External program calls ext.h(float_time)
import timefmt as tmf   # Time formatting routines tmf.days(float_seconds)
import image as img     # Pippim image.py module
import sql              # Pippim sqlite3 methods
import monitor          # Display, Screen, Monitor and Window functions

# Selenium chromium browser controller
from selenium import webdriver  # For YouTube Videos
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException

# Above Selenium for Firefox marionette using geckodriver

#import marionette_driver

# ERROR: pip's legacy dependency resolver does not consider dependency conflicts
# when selecting packages. This behaviour is the source of the following
# dependency conflicts.
# mozrunner 8.3.2 requires six<2,>=1.13.0, but you'll have six 1.11.0 which is incompatible.
# mozlog 8.0.0 requires six>=1.13.0, but you'll have six 1.11.0 which is incompatible.
# mozprofile 3.0.0 requires six<2,>=1.13.0, but you'll have six 1.11.0 which is incompatible.
# mozversion 2.4.0 requires six>=1.13.0, but you'll have six 1.11.0 which is incompatible.
# mozfile 3.0.0 requires six>=1.13.0, but you'll have six 1.11.0 which is incompatible.
# Successfully installed backports.functools-lru-cache-1.6.6 blessed-1.20.0
# distro-1.6.0 marionette-driver-3.4.0 mozdevice-4.2.0 mozfile-3.0.0 mozinfo-1.2.3
# mozlog-8.0.0 mozprocess-1.4.0 mozprofile-3.0.0 mozrunner-8.3.2 mozterm-1.0.0
# mozversion-2.4.0 wcwidth-0.2.13

XDOTOOL_INSTALLED = ext.check_command('xdotool')
WMCTRL_INSTALLED = ext.check_command('wmctrl')
WEB_PLAY = True  # Does directory ~/.local/share/mserve/YouTubePlaylists/ exist?
WEB_PLAY_DIR = g.USER_DATA_DIR + os.sep + "YouTubePlaylists"  # + playlist.name + ".csv"
# YouTube Resolution: default = 120x90(2.8K), hq default = 480x360(35.6K)
# mqdefault = 320x180
# noinspection SpellCheckingInspection
YOUTUBE_RESOLUTION = "mqdefault.jpg"  # 63 videos = 176.4 KB


class ClassCommonSelf:
    """ Common Variables used by all classes. E.G. Globals(), YouTube().
        Also used by Application() class.
    """

    def __init__(self, who):
        """ Variables used by all classes

            'New' - https://www.youtube.com/watch?v=lnIUy9gk9Fc
                Macron Challenges Russia⚔️ Fierce Battles Near Toretsk and Pokrovsk💥
                Military Summary For 2025.03.06 - YouTube — Mozilla Firefox

        """

        self.who = who  # For debugging, print class name

        self.dependencies_installed = None  # Parent will call self.CheckDependencies()
        self.passed_dependencies = []
        self.passed_installed = []

        self.system_ctl = False  # Turning off TV shuts down / suspends system
        self.remote_suspends_system = False  # If TV powered off suspend system

        self.powerStatus = "?"  # "ON" or "OFF" after discovery
        self.suspendPowerOff = 0  # Did suspend power off the device?
        # 2024-12-17 REVIEW: Use inst.suspendPowerOff instead of self.suspendPowerOff
        self.resumePowerOn = 0  # Did resume power on the device?
        self.menuPowerOff = 0  # Did user power off the device via menu option?
        self.menuPowerOn = 0  # Did user power on the device via menu option?
        self.manualPowerOff = 0  # Was device physically powered off?
        self.manualPowerOn = 0  # Was device physically powered on?
        self.dayPowerOff = 0  # Did daylight power off the device?
        self.nightPowerOn = 0  # Did nighttime power on the device?

        # Separate self.cmdEvents for every instance.
        # 'New', 'Play', 'Pause', 'FullScreen', 'NotFullScreen', 'Ad'
        self.cmdEvents = []  # Command events log
        self.cmdEvent = {}  # Single command event
        self.cmdCaller = ""  # Command caller (self.who) {caller: ""}
        self.cmdCommand = []  # Command list to execute. {command: []}
        self.cmdString = ""  # Command list as string. {command_string: ""}
        self.cmdStart = 0.0  # When command started {start_time: 9.99}
        self.cmdDuration = 0.0  # Command duration {duration: 9.99}
        self.cmdOutput = ""  # stdout.strip() from command {output: Xxx}
        self.cmdError = ""  # stderr.strip() from command {error: Xxx}
        self.cmdReturncode = 0  # return code from command {returncode: 9}
        # time: 999.99 duration: 9.999 who: <_who> command: <command str>
        # text: <text> err: <text> return: <return code>

    def CheckDependencies(self, dependencies, installed):
        """ :param dependencies: list of dependencies.
            :param installed: passed list of installed flags to be updated with test
            :returns: False if any of dependency is missing. Otherwise return True
        """
        self.dependencies_installed = True
        self.passed_dependencies = dependencies
        self.passed_installed = installed
        for required in dependencies:
            if self.Which(required):
                installed.append(True)
            else:
                v0_print("Program:", required, "is required but is not installed")
                installed.append(False)
                self.dependencies_installed = False

    def CheckInstalled(self, name):
        """ Check if external program is installed. Could use `self.Which` but this
            method is faster and allows for future help text. Requires previous call
            to `self.CheckDependencies(dep_list, inst_list)`.

            :param name: name of external program to check.
            :returns: False if external program is missing. Otherwise return True
        """
        try:
            ndx = self.passed_dependencies.index(name)
        except IndexError:
            v1_print(self.who, "CheckInstalled(): Invalid name passed:", name)
            return False
        return self.passed_installed[ndx]

    def Which(self, program):
        """ From: https://stackoverflow.com/a/377028/6929343 """
        _who = self.who + "Which():"

        def is_exe(f_path):
            """ Check if filename in path and is executable """
            return os.path.isfile(f_path) and os.access(f_path, os.X_OK)

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ.get("PATH", "").split(os.pathsep):
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file

        return None

    def runCommand(self, command_line_list, who=None, forgive=False, log=True):
        """ Run command and return dictionary of results. Print to console
            when -vvv (verbose3) debug printing is used.

            During automatic rediscovery, logging is turned off (log=False) to
            reduce size of cmdEvents[list].
        """

        self.cmdCaller = who if who is not None else self.who
        _who = self.cmdCaller + " runCommand():"
        self.cmdCommand = command_line_list
        self.cmdString = ' '.join(command_line_list)
        self.cmdStart = time.time()

        # Python 3 error: https://stackoverflow.com/a/58696973/6929343
        pipe = sp.Popen(self.cmdCommand, stdout=sp.PIPE, stderr=sp.PIPE)
        text, err = pipe.communicate()  # This performs .wait() too
        #pipe.stdout.close()  # Added 2025-02-09 for python3 error
        #pipe.stderr.close()

        #self.cmdOutput = text.strip()  # Python 2 uses strings
        #self.cmdError = err.strip()
        try:
            self.cmdOutput = text.decode().strip()  # Python 3 uses bytes
        except UnicodeDecodeError:
            self.cmdOutput = text.strip()
        try:
            self.cmdError = err.decode().strip()
        except UnicodeDecodeError:
            self.cmdError = err.strip()
        self.cmdReturncode = pipe.returncode
        self.cmdDuration = time.time() - self.cmdStart
        return self.logEvent(_who, forgive=forgive, log=log)

    def logEvent(self, who, forgive=False, log=True):
        """
            who = self.cmdCaller + "runCommand():"
            Build self.cmdEvent{} dictionary from self.cmdXxx variables.
            During automatic rediscovery, logging is turned off (log=False) to
            reduce size of cmdEvents[list].
        """

        # GLO['LOG_EVENTS'] global variable is set during auto rediscovery
        try:
            if GLO['LOG_EVENTS'] is False:
                log = False  # Auto rediscovery has turned off logging
        except NameError:
            pass  # Early on, GLO is not defined so assume logging is on

        if log:
            v3_print("\n" + who,  "'" + self.cmdString + "'")
            o = self.cmdOutput if isinstance(self.cmdOutput, str) else '\n'.join(self.cmdOutput)
            v3_print("  cmdOutput: '" + o + "'")
            o = self.cmdError if isinstance(self.cmdError, str) else '\n'.join(self.cmdError)
            v3_print("  cmdError : '" + o  + "'  | cmdReturncode: ",
                     self.cmdReturncode, "  | cmdDuration:", self.cmdDuration)

        if self.cmdReturncode != 0:
            if forgive is False:
                v1_print(who, "cmdReturncode:", self.cmdReturncode)
                v1_print(" ", self.cmdString)
                # 2025-01-13 TODO: Log this. Also log the time-outs.

            # 2024-12-21 `timeout` never returns error message
            if self.cmdReturncode == 124 and self.cmdCommand[0] == "timeout":
                self.cmdError = "Command timed out without replying after " +\
                    self.cmdCommand[1] + " seconds."

        # Log event
        self.cmdEvent = {
            'caller': self.cmdCaller,  # Command caller (self.who)
            'command': self.cmdCommand,  # Command list to executed
            'command_string': self.cmdString,  # Command list as string
            'start_time': self.cmdStart,  # When command started
            'duration': self.cmdDuration,  # Command duration
            'output': self.cmdOutput,  # stdout.strip() from command
            'error': self.cmdError,  # stderr.strip() from command
            'returncode': self.cmdReturncode  # return code from command
        }

        if log:
            self.cmdEvents.append(self.cmdEvent)
            if self.cmdError or self.cmdReturncode:
                # When one or more errors, menu is enabled.
                GLO['EVENT_ERROR_COUNT'] += 1
        return self.cmdEvent


class Globals(ClassCommonSelf):
    """ Globals

        YTV = YouTube Video
        YTP = YouTube Player

    """

    def __init__(self):
        """ Globals(): Global variables for HomA. Traditional "GLOBAL_VALUE = 1"
            is mapped to "self.dictGlobals['GLOBAL_VALUE'] = 1".

            Stored in ~/.local/share/homa/config.json

            After adding new dictionary field, remove the config.json file and
            restart HomA. Then a new default config.json file will created.

        """
        ClassCommonSelf.__init__(self, "Globals().")  # Define self.who

        self.requires = ['ls']

        # Next four lines can be defined in ClassCommonSelf.__init__()
        self.installed = []
        self.CheckDependencies(self.requires, self.installed)
        v2_print(self.who, "Dependencies:", self.requires)
        v2_print(self.who, "Installed?  :", self.installed)

        command_line_list = ["ls", "/sys/class/backlight"]
        event = self.runCommand(command_line_list, self.who)

        if event['returncode'] != 0:
            backlight_name = ""  # Empty string for now
        else:
            backlight_name = event['output'].strip()
        # popen("")

        # Usage: glo = Globals()
        #        GLO = glo.dictGlobals
        #        GLO['APP_RESTART_TIME'] = time.time()
        self.dictGlobals = {
            # YouTube Video URL. E.G. 'https://www.youtube.com/watch?v=u0z5Bo3VwtE'
            "YTV_URL_PREFIX": "https://www.youtube.com",  # YouTube URL prefix
            "YTV_URL_WATCH": "/watch?v=",  # Required to isolate video basename
            "YTV_URL_BASENAME": None,  # Video basename. E.G. 'u0z5Bo3VwtE'
            "CONFIG_FNAME": "config.json",  # Future configuration file.
            "VIDEOS_FNAME": "videos.json",  # mirrors ni.ytv_dicts[{}, {}, ... {}]
            "VIEW_ORDER_FNAME": "view_order.json",  # Read into ni.view_order[mac1, mac2, ... mac9]
            # Timeouts improve device interface performance

            "PLUG_TIME": "2.0",  # Smart plug timeout to turn power on/off
            "CURL_TIME": "0.2",  # Anything longer means not a Sony TV or disconnected
            "ADB_CON_TIME": "0.3",  # Android TV Test if connected timeout
            "ADB_PWR_TIME": "2.0",  # Android TV Test power state timeout
            "ADB_KEY_TIME": "5.0",  # Android keyevent KEYCODE_SLEEP or KEYCODE_WAKEUP timeout
            "ADB_MAGIC_TIME": "0.2",  # Android TV Wake on Lan Magic Packet wait time.
            # Application timings and global working variables

            "APP_RESTART_TIME": time.time(),  # Time started or resumed. Use for elapsed time print
            "REFRESH_MS": 16,  # Refresh tooltip fades 60 frames per second
            "REDISCOVER_SECONDS": 60,  # Check for device changes every x seconds
            "RESUME_TEST_SECONDS": 30,  # > x seconds disappeared means system resumed
            "RESUME_DELAY_RESTART": 5,  # Allow x seconds for network to come up

            "YTV_NFS_X": 100,  # YouTube Video window non-full screen X-offset
            "YTV_NFS_Y": 100,  # YouTube Video window non-full screen Y-offset
            "YTV_NFS_WID": 1700,  # YouTube Video window non-full screen width
            "YTV_NFS_HGT": 1000,  # YouTube Video window non-full screen height

            "YTV_WIN_ID_STR": None,  # YouTube Video window ID string
            "YTV_WIN_ID_INT": None,  # YouTube Video window ID Integer
            "YTV_WIN_ID_HEX": None,  # YouTube Video window ID Hex

            "YTV_DRIVER_WAIT": 10,  # Number of seconds to wait for Selenium YTV driver
            "YTV_IMG_RESOLUTION": "mqdefault.jpg",  # Medium quality 320x180

            "YTP_STATUS": 1,  # YouTube Media Player Status. Integer: -1, 1, 2, 3, 5
            "YTP_STATUS_CHANGED": 0.0,  # Time that Player Status changed.
            "YTP_TIME_PLAYED": 0.0,  # Amount of current video played in float seconds.
            "YTP_AD_COUNT": 0,  # Number of Ads skipped all videos.

            "TREE_IMG_WID": 320,  # Medium Image Width 320 in Column 0
            "TREE_IMG_HGT": 180,  # Medium Image Height 180 in Column 0
            "TREE_COL0_WID": 450,  # fixed Video Image and status: "NEW" / percentage played
            "TREE_COL1_WID": 220,  # Channel Name (pixels) stretches
            "TREE_COL1_WRAP": 20,  # Text wrap length (characters)
            "TREE_COL2_WID": 300,  # Video Title (pixels) stretches
            "TREE_COL2_WRAP": 29,  # Text wrap length (characters)

            "TIMER_SEC": 600,  # Tools Dropdown Menubar - Countdown Timer default
            "TIMER_ALARM": "Alarm_01.wav",  # From: https://www.pippim.com/programs/tim-ta.html
            "LOG_EVENTS": True,  # Override runCommand event logging / --verbose3 printing
            "EVENT_ERROR_COUNT": 0,  # To enable/disable View Dropdown menu "Discovery errors"
            "SENSOR_CHECK": 1.0,  # Check `sensors` (CPU/GPU temp & fan speeds) every x seconds
            "SENSOR_LOG": 3600.0,  # Log `sensors` every x seconds. Log more if fan speed changes
            "FAN_GRANULAR": 200,  # Skip logging when fan changes <= FAN_GRANULAR
            # Device type global identifier hard-coded in "inst.type_code"

            "HS1_SP": 10,  # TP-Link Kasa WiFi Smart Plug HS100, HS103 or HS110 using hs100.sh
            "KDL_TV": 20,  # Sony Bravia KDL Android TV using REST API (curl)
            "TCL_TV": 30,  # TCL Google Android TV using adb (after wakeonlan)
            "BLE_LS": 40,  # Bluetooth Low Energy LED Light Strip
            "DESKTOP": 100,  # Desktop Computer, Tower, NUC, Raspberry Pi, etc.
            "LAPTOP_B": 110,  # Laptop base (CPU, GPU, Keyboard, Fans, Ports, etc.)
            "LAPTOP_D": 120,  # Laptop display (Can be turned on/off separate from base)
            "ROUTER_M": 200,  # Router Modem

            "SUDO_PASSWORD": None,  # Sudo password required for laptop backlight
            # 2025-01-04 TODO: get backlight with runCommand()
            "BACKLIGHT_NAME": backlight_name,  # intel_backlight
            "BACKLIGHT_ON": "0",  # Sudo echo to "/sys/class/backlight/intel_backlight/bl_power"
            "BACKLIGHT_OFF": "4",  # ... will control laptop display backlight power On/Off.
            # Power all On/Off controls
            "POWER_OFF_CMD_LIST": ["systemctl", "suspend"],  # Run "Turn Off" for Computer()
            "POWER_ALL_EXCL_LIST": [100, 110, 120, 200],  # Exclude when powering "All"
            # to "ON" / "OFF" 100=DESKTOP, 110=LAPTOP_B, 120=LAPTOP_D, 200=ROUTER_M
        }

    def openFile(self):
        """ Read dictConfig from CONFIG_FNAME = "config.json" """
        _who = self.who + "openFile():"

        fname = g.USER_DATA_DIR + os.sep + GLO['CONFIG_FNAME']
        if os.path.isfile(fname):
            with open(fname, "r") as f:
                v2_print("Opening configuration file:", fname)
                self.dictGlobals = json.loads(f.read())

    def saveFile(self):
        """ Save dictConfig to CONFIG_FNAME = "config.json" """
        _who = self.who + "saveFile():"
        GLO['LOG_EVENTS'] = True  # Don't want to store False value
        GLO['EVENT_ERROR_COUNT'] = 0  # Don't want to store last error count

        with open(g.USER_DATA_DIR + os.sep + GLO['CONFIG_FNAME'], "w") as f:
            f.write(json.dumps(self.dictGlobals))

    def defineNotebook(self):
        """ defineNotebook models global data variables in dictionary. Used by
            Edit Preferences in HomA and makeNotebook() in toolkit.py.

            2025-01-01 TODO: Don't allow Suspend when Edit Preferences is active
                because the Devices Treeview may show as active when it really
                isn't. Plus any changes will be lost.

            https://stackoverflow.com/questions/284234/notebook-widget-in-tkinter
        """
        _who = self.who + "defineNotebook():"

        listTabs = [
            ("Sony TV",
             "Variables improving performance of HomA\n"
             "communicating with Sony Televisions on LAN."),
            ("Google TV",
             "Variables improving performance of HomA\n"
             "communicating with Google Televisions on LAN."),
            ("Smart Plug",
             "Variables improving performance of HomA\n"
             "communicating with TP-Link Smart Plugs."),
            ("LED Lights",
             "Variables for Bluetooth Low Energy (BLE)\n"
             "LED Light Strips from Happy Lighting."),
            ("Miscellaneous",
             "Variables for 'sensors' temperature and\n"
             "fan speed monitor plus Countdown Timer."),
            ("Refresh",
             "Define how the often HomA checks mouse clicks\n"
             "and runs automatic network device rediscovery."),
            ("Computer",
             "Laptop backlight display control codes.\n"
             "Define how the computer is suspended and\n"
             "device code types excluded on resume.")
        ]

        HD = "hidden"
        RO = "read-only"
        RW = "read-write"
        STR = "string"
        INT = "integer"
        FLOAT = "float"
        TM = "time"
        BOOL = "boolean"
        LIST = "list"
        FNAME = "filename"
        MAC = "MAC-address"
        WID = 15  # Default Width
        DEC = MIN = MAX = CB = None  # Decimal places, Minimum, Maximum, Callback
        listFields = [
            # name, tab#, ro/rw, input as, stored as, width, decimals, min, max,
            #   edit callback, tooltip text
            ("YTV_URL_PREFIX", 1, RW, STR, STR, 33, DEC, MIN, MAX, CB,
             "YouTube Video URL prefix"),
            ("CONFIG_FNAME", 6, RO, STR, STR, WID, DEC, MIN, MAX, CB,
             "PimTube Configuration filename"),
            ("VIDEOS_FNAME", 6, RO, STR, STR, WID, DEC, MIN, MAX, CB,
             "Discovered YouTube Videos filename"),
            ("VIEW_ORDER_FNAME", 6, RO, STR, STR, WID, DEC, MIN, MAX, CB,
             "YouTube Videos Treeview display order filename"),
            # Timeouts improve device interface performance
            ("PLUG_TIME", 3, RW, FLOAT, STR, 6, DEC, MIN, MAX, CB,
             "Smart plug timeout to turn power on/off"),
            ("CURL_TIME", 1, RW, FLOAT, STR, 6, DEC, MIN, MAX, CB,
             "A longer time means this is not\na Sony TV or Sony TV disconnected"),
            ("ADB_CON_TIME", 2, RW, FLOAT, STR, 6, DEC, MIN, MAX, CB,
             "Android TV test if connected timeout"),
            ("ADB_PWR_TIME", 2, RW, FLOAT, STR, 6, DEC, MIN, MAX, CB,
             "Android TV test power state timeout"),
            ("ADB_KEY_TIME", 2, RW, FLOAT, STR, 6, DEC, MIN, MAX, CB,
             "Android keyevent KEYCODE_SLEEP\nor KEYCODE_WAKEUP timeout"),
            ("ADB_MAGIC_TIME", 2, RW, FLOAT, STR, 6, DEC, MIN, MAX, CB,
             "Android TV Wake on Lan Magic Packet wait time."),
            # Application timings and global working variables
            ("APP_RESTART_TIME", 0, HD, TM, TM, 18, DEC, MIN, MAX, CB,
             "Time HomA was started or resumed.\nUsed for elapsed time printing."),
            ("REFRESH_MS", 6, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "Refresh tooltip fades 60 frames per second"),
            ("REDISCOVER_SECONDS", 6, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "Check devices changes every x seconds"),
            ("RESUME_TEST_SECONDS", 6, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "> x seconds disappeared means system resumed"),
            ("RESUME_DELAY_RESTART", 6, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "Pause x seconds after resuming from suspend"),
            ("YTV_NFS_X", 1, RW, INT, INT, 5, DEC, MIN, MAX, CB,
             "YouTube Video window non-full screen X-offset"),
            ("YTV_NFS_Y", 1, RW, INT, INT, 5, DEC, MIN, MAX, CB,
             "YouTube Video window non-full screen Y-offset"),
            ("YTV_NFS_WID", 1, RW, INT, INT, 5, DEC, MIN, MAX, CB,
             'YouTube Video window non-full screen Width'),
            ("YTV_NFS_HGT", 1, RW, RW, INT, INT, 5, DEC, MIN, MAX, CB,
             "YouTube Video window non-full screen Height"),
            ("YTV_DRIVER_WAIT", 4, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             'Number of seconds to perform bluetooth scan.\n'
             'A longer time may discover more devices.'),
            ("TIMER_SEC", 5, RW, INT, INT, 6, DEC, MIN, MAX, CB,
             "Tools Dropdown Menubar - Countdown Timer default"),
            ("TIMER_ALARM", 5, RW, FNAME, STR, 30, DEC, MIN, MAX, CB,
             ".wav sound file to play when timer ends."),
            ("LOG_EVENTS", 0, HD, BOOL, BOOL, 2, DEC, MIN, MAX, CB,
             "Override runCommand events'\nlogging and --verbose3 printing"),
            ("EVENT_ERROR_COUNT", 0, HD, INT, INT, 9, 0, MIN, MAX, CB,
             "To enable/disable View Dropdown menu 'Discovery errors'"),
            # 2024-12-29 TODO: SENSOR_XXX should be FLOAT not STR?
            ("SENSOR_CHECK", 5, RW, FLOAT, FLOAT, 7, DEC, MIN, MAX, CB,
             "Check `sensors`, CPU/GPU temperature\nand Fan speeds every x seconds"),
            ("SENSOR_LOG", 5, RW, FLOAT, FLOAT, 9, DEC, MIN, MAX, CB,
             "Log `sensors` every x seconds.\nLog more if Fan RPM speed changes"),
            ("FAN_GRANULAR", 5, RW, INT, INT, 6, DEC, MIN, MAX, CB,
             "Only log when Fan RPM speed changes > 'FAN_GRANULAR'.\n"
             "Avoids excessive up/down minor fan speed logging."),
            # Device type global identifier hard-coded in "inst.type_code"
            ("HS1_SP", 3, RO, INT, INT, 2, DEC, MIN, MAX, CB,
             "TP-Link Kasa WiFi Smart Plug HS100,\nHS103 or HS110 using hs100.sh"),  #
            ("KDL_TV", 1, RO, INT, INT, 2, DEC, MIN, MAX, CB,
             "Sony Bravia KDL Android TV using REST API `curl`"),
            ("TCL_TV", 2, RO, INT, INT, 2, DEC, MIN, MAX, CB,
             "TCL Google Android TV using adb after `wakeonlan`"),
            ("BLE_LS", 4, RO, INT, INT, 2, DEC, MIN, MAX, CB,
             "Bluetooth LED Light Strip"),
            ("BACKLIGHT_NAME", 7, RW, STR, STR, 30, DEC, MIN, MAX, CB,
             "E.G. 'intel_backlight', 'nvidia_backlight', etc."),
            ("BACKLIGHT_ON", 7, RW, STR, STR, 2, DEC, MIN, MAX, CB,
             "Sudo tee echo 'x' to\n'/sys/class/backlight/intel_backlight/bl_power'"),
            ("BACKLIGHT_OFF", 7, RW, STR, STR, 2, DEC, MIN, MAX, CB,
             "Sudo tee echo 'x' to\n'/sys/class/backlight/intel_backlight/bl_power'"),
            # Power all On/Off controls
            ("POWER_OFF_CMD_LIST", 7, RW, STR, LIST, 30, DEC, MIN, MAX, CB,
             'Run "Turn Off" for Computer'),
            ("POWER_ALL_EXCL_LIST", 7, RW, STR, LIST, 20, DEC, MIN, MAX, CB,
             'Exclude devices when powering all "ON" / "OFF"'),
            # Once entered, sudo password stored encrypted on disk until "forget" is run.
            # ("SUDO_PASSWORD", 7, HD, STR, STR, WID, DEC, MIN, MAX, CB,
            # "Sudo password required for laptop backlight"),  # HD Hidden NOT working yet.
            ("DESKTOP", 7, RO, INT, INT, 3, DEC, MIN, MAX, CB,
             "Desktop Computer, Tower, NUC, Raspberry Pi, etc."),
            ("LAPTOP_B", 7, RO, INT, INT, 3, DEC, MIN, MAX, CB,
             "Laptop base (CPU, GPU, Keyboard, Fans, Ports, etc.)"),
            ("LAPTOP_D", 7, RO, INT, INT, 3, DEC, MIN, MAX, CB,
             'Laptop display (backlight can be turned\n'
             'on/off separately from laptop base)'),
            ("ROUTER_M", 7, RO, INT, INT, 3, DEC, MIN, MAX, CB,
             "Router connecting local network to global internet")
        ]

        help_id = "https://www.pippim.com/programs/homa.html#"  # same as g.HELP_URL
        help_tag = "EditPreferences"
        help_text = "Open a new window in your default web browser for\n"
        help_text += "explanations of fields in this Preferences Tab."
        listHelp = [help_id, help_tag, help_text]

        return listTabs, listFields, listHelp

    def updateNewGlobal(self, key, new_value):
        """ Validate a new dictionary field. """
        _who = self.who + "updateNewGlobal():"
        _listTabs, listFields, _listHelp = self.defineNotebook()
        for atts in listFields:
            if atts[0] == key:
                break
        else:
            v0_print("Bad key passed:", key, new_value)
            return False

        # atts = (name, tab#, ro/rw, input as, stored as, width, decimals, min, max,
        #         edit callback, tooltip text)
        stored_type = atts[4]
        if stored_type == "list":
            new_value = new_value.replace("u'", '"').replace("'", '"')
            # u 'suspend' -> "suspend"
            try:
                new_list = json.loads(new_value)
            except ValueError:
                v0_print("Bad list passed:", key, new_value, type(new_value))
                return False

            if key == "POWER_ALL_EXCL_LIST":  # List longer for future device types
                subset_list = [10, 20, 30, 40, 50, 60, 70, 100, 110, 120, 200]
                if not set(new_list).issubset(subset_list):
                    v0_print(_who, "POWER_ALL bad value:", key, new_value)
                    v0_print("Not in list:", subset_list)
                    return False

            new_value = new_list  # Passed all tests

        GLO[key] = new_value
        return True


# ==============================================================================
#
#       YouTube() class.
#
# ==============================================================================
class YouTube(ClassCommonSelf):
    """ Usage:

        self.playlists = Playlists(
            self.lib_top, apply_callback=self.apply_playlists, tooltips=self.tt,
            pending=self.get_pending_cnt_total, enable_lib_menu=self.enable_lib_menu,
            thread=self.get_refresh_thread, play_close=self.play_close, info=self.info)

              - Geometry in Type-'window', action-'playlists'.
              - build_lib_menu will look at self.playlists.status

        if self.playlists.top:
            - Playlists top level exists so lift() to top of stack

    History Record Formats

        Type-Playlist, Action-P999999, Master-L999, Detail-Playlist Name,
            Target-JSON list of sorted Music IDs, Size=MB, Count=# Songs,
            Seconds=Total Duration, Comments=Playlist Description

        Type-P999999, Action-'resume', Master-'playing'/'paused'...

        Type-P999999, Action-'chron_state', Master-'show'/'hide'...

        Type-P999999, Action-'hockey_state', Master-'on'/'off'...

        Type-P999999, Action-<Artist Name>, Master-<Image Pil>

    """

    def __init__(self, tk_top=None, text=None, pending=None, info=None,
                 apply_callback=None, enable_lib_menu=None, play_close=None,
                 # 2024-05-20 - display_lib_title() overused
                 # tooltips=None, thread=None, display_lib_title=None):
                 tooltips=None, thread=None, real_paths=None):
        """

        Monitor YouTube for media actions Pause/Play/Skip.

        Monitor Pippim controls for Pause/Play/Load video #.

        Usage:

        self.playlists = Playlists(
            self.lib_top, apply_callback=self.apply_playlists, tooltips=self.tt,
            pending=self.get_pending_cnt_total, enable_lib_menu=self.enable_lib_menu,
            thread=self.get_refresh_thread, play_close=self.play_close, info=self.info)

        """
        """ YouTube(): Class to open webpage, play videos and skip commercials. """
        ClassCommonSelf.__init__(self, "YouTube().")  # Define self.who

        ''' self-ize parameter list '''
        self.parent = tk_top  # FOR NOW self.parent MUST BE: lib_top
        self.text = text  # Text replacing treeview when no playlists on file
        self.get_pending = pending  # What is pending in parent?  - Could be favorites
        self.info = info  # InfoCentre()
        self.apply_callback = apply_callback
        self.play_close = play_close  # Main music playing window to close down
        self.enable_lib_menu = enable_lib_menu
        self.tt = tooltips  # Tooltips pool for buttons
        self.get_thread = thread  # E.G. self.get_refresh_thread
        self.real_paths = real_paths

        # For refresh from parent()
        self.app = None

        # self.who = "pimtube.py YouTube()."
        # Dummy fields in Application()__init__()
        self.last_refresh_time = time.time()  # Prevent resume from suspend
        self.last_rediscover_time = self.last_refresh_time

        self.currentWebpage = None  # Desired YouTube Video URL
        self.currentURL = None  # Current URL which is currentWebpage if successful
        self.currentYtvImage = None  # YouTube Video Thumbnail URL address
        self.currentTkImage = None  # Tkinter Image formatted
        self.currentPhotoIm = None  # Tkinter photo image formatted
        self.currentTitle = None  # Video's title
        self.currentOwner = None  # Channel name
        self.currentSubCount = None  # Channel owner subscriber count
        self.currentUploadDate = None  # Video upload date
        self.currentTime = None  # Current time offset into playing video
        self.currentDur = None  # Total length (duration) of video

        ''' Renamed variables '''
        self.webDriver = None  # self.webDriver = webdriver.Chrome()  # It will search path
        self.webWinGeom = None  # # Window(number, name, x, y, width, height)


        ''' YouTube Playlist work fields '''
        self.youDebug = 1  # Debug level. 0=None, 1=min(default), 7=max
        self.isSmartPlayYouTube = False  # is Smart YouTube Player running?
        self.isViewCountBoost = False  # 30 second play to boost view counts?
        self.youViewCountSkipped = 0  # How many videos skipped so far?
        # 2023-12-24-17:00 - ^^^-- First cycle is 1 video short --^^^
        self.youViewSkippedTime = 0.0  # Time a video last skipped
        self.nameYouTube = None  # = WEB_PLAY_DIR + os.sep + self.act_name + ".csv"
        self.linkYouTube = None  # YouTube links retrieved from .csv file
        self.listYouTube = None  # [dictYouTube, dictYouTube, ... dictYouTube]
        self.dictYouTube = None  # { name: link: duration: image: }
        self.photosYouTube = None  # Photos saved from garbage collector (GIC)
        self.privateYouTube = "0"  # Saved count of private/unavailable videos
        self.listMergeYouTube = None  # Stored list + new videos
        self.youLastLink = None  # Last video ID link found and verified
        self.listYouTubeCurrIndex = None  # Same as YouTube Tree 0's-Index (Integer)
        self.gotAllGoodLinks = None  # All 100 video chunk lists have scrolled
        self.youValidLinks = None  # Video links minus private and deleted videos
        self.youUnavailableShown = None  # Unavailable videos displayed?
        self.youFullScreen = None  # Was YouTube full screen before?
        self.youForceVideoFull = None  # After video starts send "f" key

        self.scrollYT = None  # Custom Scrolled Text Box
        self.youAssumedAd = None  # Volume was forced automatically down
        self.hasLrcForVideo = None  # Are synchronized lyrics (LRC) stored in dict?
        self.listLrcLines = None  # List of LRC ([mm:ss.hh] "lyrics line text")
        self.ndxLrcCurrentLine = None  # Current index within listYouTubeLRC
        self.youProLrcVar = None  # Progress label variable tk string
        self.youLrcTimeOffsetVar = None  # LRC time offset (+/- seconds)
        self.youLrcTimeOffset = None  # LRC time offset (+/- seconds)
        self.youLrcBgColorVar = None  # LRC highlight yellow/cyan/magenta
        self.youLrcBgColor = None  # LRC highlight yellow/cyan/magenta
        self.youFirstLrcTimeNdx = None  # 0-Index of first line with [mm:ss.99]
        self.youFirstLrcTime = None  # Float Seconds of [mm:ss.99]

        ''' YouTube video progress and player controls '''
        self.durationYouTube = 0.0  # Length of song (Duration)
        self.progressYouTube = 0.0  # Progress (Duration) within playing song
        self.progressLastYouTube = 0.0  # Last progress, if same then stuck
        self.timeLastYouTube = 0.0  # Last System time playing video (33ms)
        self.timeForwardYouTube = 0.0  # System time self.webDriver.forward()
        self.isSongRepeating = None  # Fall out from .back() and .forward()
        self.youProVar = None  # YouTube Video progress TK variable, percent float
        self.youProBar = None  # YouTube Video TK Progress Bar element / instance
        self.youPlayerButton = None  # Tkinter element mounted with .grid
        self.youPlayerCurrText = None  # "None" / "Pause" / "Play" button
        self.youPlayerNoneText = "?  None"  # Music Player Text options
        self.youPlayerPlayText = "▶  Play"  # used when music player status
        self.youPlayerPauseText = "❚❚ Pause"  # changes between 1 & 2
        self.youPlayerSink = None  # Audio Sink (sink_no_str)

        ''' Playlists Maintenance Window and fields '''
        self.top = None  # tk.Toplevel

        self.frame = None  # main tk.Frame inside self.top
        self.tree_frame = None  # .grid_remove() for youLrcFrame (Lyrics)
        self.youLrcFrame = None  # .grid_remove() for you_tree_fame (Treeview)
        # self.tree_frame will also contain:
        # self.dd_view = None  # SQL Hist tk.Treeview managed by Data Dictionary
        # self.you_tree = None  # YouTube Playlist Tree
        self.dd_view = None  # SQL Hist tk.Treeview managed by Data Dictionary
        self.you_tree = None  # YouTube Playlist Tree (All songs)

        self.you_btn_frm = None  # Tk.Frame button bar
        self.fld_name = None  # Field tk.Entry for toggling readonly state
        self.fld_description = None
        self.scr_name = tk.StringVar()  # Input fields
        self.scr_description = tk.StringVar()
        self.scr_location = tk.StringVar()

        self.fld_count = None  # Playlist song count
        self.fld_size = None  # Playlist all songs MB
        self.fld_seconds = None  # Playlist all songs duration

        self.apply_button = None
        self.help_button = None
        self.close_button = None

    # New methods created from 4.7k lines below

    def openSelenium(self):
        """ Create Selenium browser instance
            Create Selenium self.webDriver instance
            Get Window ID for self.webDriver instance

        :return self.webDriver, window: Selenium self.webDriver and WM window tuple
        """
        _who = self.who + "openSelenium():"
        self.webDriver = None
        self.webWinGeom = ()  # Window(number, name, x, y, width, height)

        web = webbrowser.get()
        # print("browser name:", web.name)  # xdg-open
        try:
            mon = monitor.Monitors()  # Monitors class list of dicts
            # Start windows
            end_wins = start_wins = mon.get_all_windows()
        except Exception as err:
            self.youPrint(_who, "mon = monitor.Monitors() Exception:")
            self.youPrint(err)
            return self.webDriver, self.webWinGeom

        def startChromeOrChromium():
            """ Start Chrome or Chromium Web Browser based on which is installed. """
            useChrome = useChromium = False
            CHROME_DRIVER_VER = "chromedriver108"  # 108 replaced with actual version
            ver = os.popen("google-chrome --version").read().strip()
            ver = ver.split()
            try:
                ver = ver[2].split(".")[0]
                # _ver_int = int(ver)
                useChrome = True
            except IndexError:
                # google-chrome: command not found
                ver = os.popen("chromium --version").read().strip()
                # Chromium 133.0.6943.53 snap
                ver = ver.split()
                ver = ver[1].split(".")[0]  # 133
                useChromium = True
            CHROME_DRIVER_VER = CHROME_DRIVER_VER.replace("108", ver)
            CHROME_DRIVER_PATH = \
                g.PROGRAM_DIR + os.sep + CHROME_DRIVER_VER + os.sep + "chromedriver"
            v0_print(_who, "CHROME_DRIVER_PATH:", CHROME_DRIVER_PATH)

            # add the --incognito argument to the ChromeOptions before initializing the WebDriver.
            # ^^^ not needed: https://stackoverflow.com/a/27630230/6929343
            if useChrome:
                self.webDriver = webdriver.Chrome(CHROME_DRIVER_PATH)
                # Automated Test Software message suppression (Doesn't work)
                # https://stackoverflow.com/a/71257995/6929343
                chromeOptions = webdriver.ChromeOptions()
                chromeOptions.add_experimental_option("excludeSwitches", ['enable-automation'])
            elif useChromium:
                self.webDriver = webdriver.Chrome()  # It will search path

                """
                    Maintainer: https://chromedriver.chromium.org/home
                    WebDriverException: Message: 'chromedriver' executable 
                    needs to be in PATH. Please see 
                    https://sites.google.com/a/chromium.org/chromedriver/home
                    New download links:
                    https://sites.google.com/chromium.org/driver/downloads?authuser=0

                    For chrome > 115: https://googlechromelabs.github.io/chrome-for-testing/
                    E.G. version 120: https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/
                                      120.0.6099.109/linux64/chromedriver-linux64.zip

                    To use Chromium instead of Chrome use:
                    sudo apt install chromium-chromedriver
                    Credit: https://stackoverflow.com/a/75241037/6929343
                """

        # Get default browser name
        if web.name.startswith("xdg-open"):
            xdg_browser = os.popen("xdg-settings get default-web-browser"). \
                read().strip()
            if "FIREFOX2" in xdg_browser.upper():
                # Using Marionette directly
                os.popen("firefox -marionette")

                # Connect to the Marionette server
                driver = marionette_driver.MarionetteDriver()

                # Navigate to a website
                driver.get("https://www.example.com")

                # Get the title of the page
                title = driver.title

                print(title)

                # Close the browser
                driver.quit()

                '''
To use Marionette (the Firefox automation protocol) without Selenium, you'll 
need to interact directly with the Marionette server using a client library or 
tool that understands the Marionette protocol, such as the Python client. 
Here's a breakdown:
1. Understanding Marionette:

    Marionette is a remote protocol that allows out-of-process programs to 
    communicate with, instrument, and control Gecko-based browsers (like Firefox). 

It provides interfaces for interacting with both the internal JavaScript runtime
and UI elements of Gecko-based browsers. 

It's similar to Selenium in its purpose, but it's a lower-level protocol designed 
for more direct browser control. 

2. Setting up the Marionette Client:

    Download and install the Python client for Marionette: You'll need to have 
    Python installed and then use pip to install the Marionette client. 

Code

    pip install marionette

    Start the Marionette server: You'll need to start the Marionette server 
    within Firefox (usually by running Firefox with the -marionette flag). 

Code

    firefox -marionette

3. Interacting with Marionette:

    Use the Python client to send commands: The Python client provides 
    functions to interact with the Marionette server, allowing you to control 
    the browser.
    Example (very basic): 

Python

    import marionette

    # Connect to the Marionette server
    driver = marionette.MarionetteDriver()

    # Navigate to a website
    driver.get("https://www.example.com")

    # Get the title of the page
    title = driver.title

    print(title)

    # Close the browser
    driver.quit()

    Explore the Marionette API: The Marionette documentation provides a 
    detailed list of available commands and functions. 

4. Tips for Debugging:

    Use the Marionette console: The Marionette server can output debugging 
    information to the console.
    Check the network traffic: Use a network monitoring tool to see the 
    commands being sent to and from the Marionette server. 

In summary, to use Marionette directly without Selenium, you need to:

    Set up the Marionette server in Firefox.
    Install and use a Marionette client (like the Python client).
    Use the client to send commands to the Marionette server to control 
    the browser.
                
                '''

            if "FIREFOX" in xdg_browser.upper():
                # Using Marionette with geckodriver and Selenium where YouTube
                # video only plays 20 seconds of video.
                binary = '/usr/bin/firefox'
                options = webdriver.FirefoxOptions()
                options.binary = binary

                cap = DesiredCapabilities().FIREFOX
                cap["marionette"] = True

                path_to_driver = "./geckodriver"  # Install to HomA directory

                # run firefox webdriver using Selenium version: 2.48.0
                # IOError: [Errno 2] No such file or directory:
                #   '/usr/lib/firefoxdriver/webdriver.xpi'
                # 2025-03-17 upgraded to Selenium 3.141.0 on Python 2.7 for Gecko
                self.webDriver = webdriver.Firefox(
                    firefox_options=options, capabilities=cap, executable_path=path_to_driver)

            elif "CHROME" in xdg_browser.upper():
                startChromeOrChromium()

            elif "CHROMIUM" in xdg_browser.upper():
                startChromeOrChromium()

        start = time.time()
        while len(end_wins) == len(start_wins):
            end_wins = mon.get_all_windows()
            if time.time() - start > GLO['YTV_DRIVER_WAIT']:
                title = "Could not start Browser"
                text = "Browser would not start.\n"
                text += "Check console for error\n"
                text += "messages and try again."
                message.ShowInfo(self.top, title, text, icon='error', thread=self.get_thread)
                return self.webDriver, self.webWinGeom

        if not len(start_wins) + 1 == len(end_wins):
            title = "Could not start Browser"
            text = "Old Window count: " + str(len(start_wins)) + "\n\n"
            text += "New Window count: " + str(len(end_wins)) + "\n\n"
            text += "There should only be one new window.\n"
            text += "Check console for error messages.\n"
            message.ShowInfo(self.top, title, text, icon='error', thread=self.get_thread)
            return self.webDriver, self.webWinGeom

        win_list = list(set(end_wins) - set(start_wins))
        self.webWinGeom = win_list[0]  # Window(number, name, x, y, width, height)
        GLO['YTV_WIN_ID_STR'] = str(self.webWinGeom.number)  # should remove L in python 2.7.5+
        GLO['YTV_WIN_ID_INT'] = int(GLO['YTV_WIN_ID_STR'])  # https://stackoverflow.com/questions
        GLO['YTV_WIN_ID_HEX'] = hex(GLO['YTV_WIN_ID_INT'])  # /5917203/python-trailing-l-problem
        v1_print(_who, self.webWinGeom)
        v1_print("  GLO['YTV_WIN_ID_STR']:", GLO['YTV_WIN_ID_STR'])
        v1_print("  GLO['YTV_WIN_ID_INT']:", GLO['YTV_WIN_ID_INT'])
        v1_print("  GLO['YTV_WIN_ID_HEX']:", GLO['YTV_WIN_ID_HEX'])

        # Move window from default window geometry to GLO dictionary location
        # wmctrl -ir $window -e 1,$x2Pos,$yPos,$width,$height
        geom = "1," + str(GLO['YTV_NFS_X']) + "," + str(GLO['YTV_NFS_Y']) + ","
        geom += str(GLO['YTV_NFS_WID']) + "," + str(GLO['YTV_NFS_HGT'])
        command_line_list = ["wmctrl", "-ir", GLO['YTV_WIN_ID_HEX'], "-e", geom]
        if WMCTRL_INSTALLED:
            _event = self.runCommand(command_line_list, _who)
            # TODO: Update webWinGeom(x, y, width, height)
            v1_print(_who, "Moved window with command:")
            v1_print(" ", self.cmdString)
        else:
            v0_print(_who, "wmctrl not installed. Cannot move window.")

        return self.webDriver, self.webWinGeom

    def openVideo(self, link=None, seconds=None):
        """ Open YouTube subscriptions at https://www.youtube.com/feed/subscriptions

        View music videos natively on website

        https://youtube.com/watch?v=xUfXiI6tV8w&t=0m42s
        https://stackoverflow.com/a/72481880/6929343
        add time to the url like so "https://youtu.be/5ygpvZbxA6w?t=465" the video
        will start at 465 which is 7 min 45 sec

        """
        _who = self.who + "openVideo():"

        if link is None:
            link = self.currentWebpage  # https://www.youtube.com/watch?v=RGlZ4AlAOtg
        # OTHER VIDEOS:
        # https://www.youtube.com/watch?v=u0z5Bo3VwtE
        # https://www.youtube.com/watch?v=9uj8SI8xWGc  # Invalid TCL characters (UTF-8)

        if seconds is not None:
            link += "&t=" + str(seconds)
            v0_print(_who, "seconds offset:", seconds)

        try:
            self.webDriver.get(link)
            # 2025-03-08 Video opens in playing mode, non full-screen
        except Exception as err:
            v0_print(_who, "self.webDriver.get(link) Exception 1:")
            v0_print(err)
            # Selenium Window may have been closed
            self.openSelenium()  # 2025-03-08: Should this be wrapped in try?
            try:
                self.webDriver.get(link)
                # 2025-03-08 Video opens in paused mode, non full-screen
            except Exception as err:
                v0_print(_who, "self.webDriver.get(link) Exception 2:")
                v0_print(err)
                return False

        if not self.isBrowserAlive():
            v0_print(_who, "self.webDriver died unexpectedly.")

        return True

    # Move askVideoLink to self.app
    def askVideoLink(self, msg=None):
        """ Prompt user to paste video link. """
        _who = self.who + "askVideoLink():"

        if msg is None:
            msg = "1. Open YouTube in your web browser.\n"
            msg += "2. Select the video you want to watch.\n"
            msg += "3. Right-click on the address bar and select\n"
            msg += "   'Copy Clean Link' (if enabled) or 'Copy'.\n\n"
            msg += "4. Position to field below and use <CTRL>+V.\n\n"
            msg += "5. Click the `Apply' button below.\n\n"
        try:
            answer = message.AskString(
                self.app, text=msg, thread=self.app.refreshApp, align="left", string_width=50,
                title="YouTube Video Link", icon="information", win_grp=self.app.win_grp)
        except tk.TclError as err:
            v0_print(_who, "message.AskString() tk.TclError:")
            v0_print(" ", err)  # TclError: grab failed: another application has grab
            return None


        # Setting laptop display power requires sudo prompt which causes fake resume
        self.last_refresh_time = time.time()  # Refresh idle loop last entered time

        if answer.result == "no" or answer.string is None or answer.string == "":
            return None

        self.currentWebpage = answer.string
        #     https://www.youtube.com/watch?v=RGlZ4AlAOtg 'Copy Clean Link' instead of:
        #     https://www.youtube.com/watch?v=RGlZ4AlAOtg&pp=ygUOZGlhbG9ndWUgd29ya3M%3D
        if "&" in self.currentWebpage:
            parts = self.currentWebpage.split("&")
            self.currentWebpage = parts[0]
        return self.currentWebpage

    def getVideoDetails(self, *_args):
        """ Open Selenium, load YouTube Video and get details. """

        _who = self.who + "getVideoDetails():"

        # If browser is not already open, open it with Selenium
        if not yt.isBrowserAlive():
            yt.openSelenium()

        # Did selenium fail? E.G. No window visible
        if not bool(yt.webWinGeom):  # (x_id, name, x, y, width, height)
            return False

        if not self.openVideo(link=self.currentWebpage):  # Create self.webDriver
            v0_print(_who, "Invalid YouTube video URL.")
            self.webDriver.quit()  # Closes driver and Selenium window
            return False  # Driver timed out or link is bad

        # Minimize Selenium Window
        # Is minimizing causing Gecko to break?
        #command_line_list = ["xdotool", "windowminimize", str(GLO['YTV_WIN_ID_INT'])]
        #self.runCommand(command_line_list, _who)

        if not self.getVideoTitle():
            v0_print(_who, "Can't find YouTube video title.")
            self.webDriver.quit()  # Closes driver and Selenium window
            return False

        # xdotool space bar to minimized window because self.sendSpaceBar() won't work
        command_line_list = ["xdotool", "type", "--window", str(GLO['YTV_WIN_ID_INT']), " "]
        self.runCommand(command_line_list, _who)

        self.getChannelName()  # Author / video owner
        self.getCurrentTime()  # How much time of video has played (Float)
        self.getVideoDuration()  # How long is the video (Float)
        self.webDriver.quit()  # Closes driver and Selenium window

        return True

    def downloadVideoImage(self, link=None):
        """
        Copied from self.buildYouTubePlaylist()

        Access YouTube video image from:
            "https://i.ytimg.com/vi/" + video_basename + "/" + GLO['YTV_IMG_RESOLUTION']
            Where: GLO['YTV_IMG_RESOLUTION'] = "mqdefault.jpg"

2025-03-15 python 3.5 requests module broken:

    import requests  # retrieve YouTube thumbnail images
  File "/usr/lib/python3/dist-packages/requests/__init__.py", line 53, in <module>
    from .packages.urllib3.contrib import pyopenssl
  File "/usr/lib/python3/dist-packages/requests/packages/__init__.py", line 29, in <module>
    import urllib3
  File "/home/rick/.local/lib/python3.5/site-packages/urllib3/__init__.py", line 37
    f"the 'ssl' module is compiled with {ssl.OPENSSL_VERSION!r}. "
    ^
SyntaxError: invalid syntax

        requests works in Python 2.7 but not Python 3.5 so switch to curl

        """
        _who = self.who + "downloadVideoImage():"
        if link is None:
            link = self.currentWebpage
        # sample 'link' var: https://www.youtube.com/watch?v=RGlZ4AlAOtg

        try:  # split link into segments
            v1_print("link:", link)
            video_basename = link.split(GLO['YTV_URL_WATCH'])[1]
            image_name = "https://i.ytimg.com/vi/" + video_basename
            image_name += "/" + GLO['YTV_IMG_RESOLUTION']  # "mqdefault.jpg"
            # https://i.ytimg.com/vi/RGlZ4AlAOtg/mqdefault.jpg
            self.currentYtvImage = image_name  # Needed for not found message
        except (ValueError, IndexError) as err:
            v0_print(_who, "Exception:")
            v0_print(err)
            return False

        #os.popen("curl " + image_name + " -o temp.jpg")  # python 3.5 version
        try:  # grab image thumbnail
            raw_data = requests.get(image_name).content  # 2.7 version works
        except requests.exceptions.RequestException as err:
            v0_print(_who, "RequestException:")
            v0_print(err)
            return False

        try:  # convert thumbnail image into tkinter format
            #im = Image.open("temp.jpg")  # python 3.5 version with curl
            im = Image.open(BytesIO(raw_data))  # 2.7 version with requests
            im = im.resize((GLO['TREE_IMG_WID'], GLO['TREE_IMG_HGT']), Image.ANTIALIAS)
            _image = {
                'pixels': im.tobytes(),
                'size': im.size,  # If "mqdefault" it is tuple: (320, 180)
                'mode': im.mode,  # String: "RGB"
            }
            self.currentTkImage = im
        except tk.TclError as err:  # Not sure if this works for PIL yet....
            v0_print(_who, "tk.TclError:")
            v0_print(err)
            return False

        return True  # smart play all will now automatically build list

    def getVideoTitle(self):
        """ Get Video Title https://stackoverflow.com/a/51032412/6929343
            self.webDriver.get() has already been performed and video is open / opening

            Wait until element is present:

                <h1 class="title style-scope ytd-video-primary-info-renderer">
                <yt-formatted-string force-default-style=
                "" class="style-scope ytd-video-primary-info-renderer">
                John Helmer: Trump’s Ukraine War Numbers: The Truth vs. Lies
                </yt-formatted-string>

        """
        _who = self.who + "getVideoTitle():"
        wait = WebDriverWait(self.webDriver, GLO['YTV_DRIVER_WAIT'])

        try:
            # sample 'link' var: https://www.youtube.com/watch?v=RGlZ4AlAOtg
            _element = wait.until(EC.presence_of_element_located((
                By.CLASS_NAME, "ytd-video-primary-info-renderer")))  # Title wait class
        except NoSuchElementException:
            return False
        except TimeoutException as err:
            print(_who, "TimeoutException():")
            print(" ", err)
            return False

        # https://stackoverflow.com/a/70511822/6929343
        videoTitle = self.webDriver.find_element_by_xpath(
            "//h1//*[@class='style-scope ytd-video-primary-info-renderer']")  # Title get xpath
        title_text = videoTitle.get_attribute('innerHTML')
        v0_print(_who, "title_text:", title_text)
        self.currentTitle = title_text
        return title_text

    def getChannelName(self):
        """ Get channel owner name, video upload date and subscriber count """
        _who = self.who + "getChannelName():"

        # 'yt-simple-endpoint style-scope ytd-video-owner-renderer'  # 297K subscribers
        subscriberCount = self.webDriver.find_element_by_xpath(
            '//yt-formatted-string[@class="style-scope ytd-video-owner-renderer"]')
        self.currentSubCount = subscriberCount.get_attribute('innerHTML')
        v0_print(_who, "self.currentSubCount:", self.currentSubCount)

        # https://stackoverflow.com/a/68148793/6929343
        uploaded = self.webDriver.find_element(
            By.CSS_SELECTOR, value='#info-strings yt-formatted-string')  # Get author CSS
        self.currentUploadDate = uploaded.get_attribute('innerHTML')
        # Upload Date text is a moving target depending on when you look at it:
        # Streamed live on 5 Mar 2025 / 9 Mar 2025 / Premiered 5 hours ago
        self.currentUploadDate = self.currentUploadDate.replace("Premieres ", "")
        self.currentUploadDate = self.currentUploadDate.replace("Premiered ", "")
        self.currentUploadDate = self.currentUploadDate.replace("Streamed live on ", "")
        v0_print(_who, "self.currentUploadDate:", self.currentUploadDate)

        # https://stackoverflow.com/a/75851201/6929343
        creator = self.webDriver.find_element(By.XPATH, value='//*[@id="text"]/a')
        channel_name = creator.get_attribute('innerHTML')

        v0_print(_who, "channel_name:", channel_name)
        self.currentOwner = channel_name  # currentChannel
        return channel_name

    def getCurrentTime(self, echo=True):
        """ Get video play current time offset and video total duration. """
        _who = self.who + "getCurrentTime():"
        video_time = self.webDriver.execute_script(
            "return document.getElementById('movie_player').getCurrentTime()")

        if echo:
            v0_print(_who, "video_time:", video_time)
        # E.G. https://www.youtube.com/watch?v=RGlZ4AlAOtg video_time: 2.229145
        self.currentTime = video_time  # String format
        return float(video_time)

    def getVideoDuration(self):
        """ Get video total duration. """
        _who = self.who + "getVideoDuration():"
        video_dur = self.webDriver.execute_script(
            "return document.getElementById('movie_player').getDuration()")

        v0_print(_who, "video_dur:", video_dur)
        # E.G. https://www.youtube.com/watch?v=RGlZ4AlAOtg video_dur: 3877.241
        self.currentDur = video_dur

    def isBrowserAlive(self):
        """ Check if user has closed Selenium Web Driver window
        if "disconnected" in self.webDriver.get_log('driver')[-1]['message']:
            print 'Browser window closed by user'
        """
        _who = self.who + "isBrowserAlive():"
        try:
            self.currentURL = self.webDriver.current_url
            return True
        except Exception as err:
            self.currentURL = None
            v0_print(_who, "self.webDriver (Selenium) DISCONNECTED !!:")
            v0_print(" ", err)  # "chrome not reachable"
            return False

    #  +===============================================================+
    #  |                                                               |
    #  |   YouTube Media Player section   |
    #  |                                                               |
    #  +===============================================================+

    def playVideo(self, link, refresh):
        """ Play video:

            1) Open www.youtube.com as an anchor for back button
            2) Play video sending back button when commercial appears
            3) Play video at the last time when commercial appeared
            4) When video ends, close driver
            5) If driver closed early, exit

        """
        _who = self.who + "playVideo():"
        global GLO  # required to update amount of video time played
        v0_print(_who, "Starting up")
        if not self.isBrowserAlive():
            self.openSelenium()  # Initialize self.webDriver
            if not self.isBrowserAlive():
                v0_print(_who, "Could not start Selenium!")
                return  # TODO: error message

        if not self.openVideo(GLO['YTV_URL_PREFIX']):  # Open YouTube & move to monitor
            v0_print(_who, "Could not open YouTube using:", GLO['YTV_URL_PREFIX'])
            return  # TODO: error message

        # TODO: set video full screen
        if not self.openVideo(link):
            v0_print(_who, "Could not open:", link)
            return  # TODO: error message

        # Dummy call to get video title which waits until video starts
        if not self.getVideoTitle():
            v0_print(_who, "Video will not play:", link)
            return

        while self.isBrowserAlive():  # Sets self.currentURL to web browser address bar

            GLO['YTP_STATUS'] = self.getPlayerStatus()
            if GLO['YTP_STATUS'] == 1:
                # Amount of current video played in float seconds.
                GLO['YTP_TIME_PLAYED'] = self.getCurrentTime(echo=False)
                # Comment out above to verify this isn't why YouTube freezes after 20 seconds
                pass

            self.monitorPlayerStatus(GLO['YTP_STATUS'], refresh)  
            # Will freeze interface during ad skip

            if not refresh():
                break  # app closing down

        v0_print(_who, "Finishing")

    def monitorPlayerStatus(self, player_status, refresh):
        """ Update progress display in button bar and skip commercials

            2025-03-09: Originally used back > forward technique.
            Not reliable because YouTube restarts video at beginning
            instead of where it left off. Major rewrite required.

        :param player_status: Music player status (-1, 1, 2, 3, 5)
        :param refresh: Print debug statements
        :return: False when closing down, else True
        """
        _who = self.who + "monitorPlayerStatus():"
        # Capture weird player status == 0
        if player_status not in [-1, 1, 2, 3, 5]:
            v0_print(_who, "Unknown player_status: ", player_status)
            return

        _now = time.time()

        # Has YouTube popped up an ad?
        if not self.checkAdRunning():
            return True  # Nothing to do

        while True:  # Ad was visible. Loop until status is song playing (1)

            self.checkContinue()  # Respond to "Continue Watching?" prompt

            # Ad is running
            """  TODO: When resuming from suspend, 100's of ads can appear for
                       duration of sleep. Unlike above where Ads are .1 second
                       apart, these Ads are 2 seconds apart. Fastest way out is
                       to reload the last song. 
            """
            count = 0
            # self.webDriver.find_element(By.CSS_SELECTOR, ".ytp-ad-duration-remaining")

            while self.checkAdRunning():
                # Back button goes to previous song played
                #self.youVolumeOverride(True)  # Ad playing override
                self.webDriver.back()
                v0_print(_who, "BACK LOOP Ad still visible:", count)
                if self.checkAdRunning():
                    count += 1
                    if not refresh():
                        self.webDriver.quit()
                        break  # app closing down

            v0_print("webDriver.back() visible loops:", str(count).ljust(2))
            # count is always 1?

            # Reopen video at last recorded time
            try:
                time_str = str(GLO['YTP_TIME_PLAYED']).split(".")[0] + "s"
            except IndexError:
                time_str = "1s"

            # TODO: set video full screen
            if not self.openVideo(link, seconds=time_str):
                v0_print(_who, "Could not open:", link)
                v0_print(" ", "at seconds time offset:", time_str)
                return False  # TODO: error message

            # Dummy call to get video title which waits until video starts
            if not self.getVideoTitle():
                v0_print(_who, "Video will not play:", self.currentURL)
                v0_print(" ", "at seconds time offset:", time_str)
                return False

            player_status = self.getPlayerStatus()
            # If status is NONE probably dialog prompt
            if not player_status:
                # Answer dialog box for "Video paused. Continue watching?"
                # self.youHousekeeping()  # Not working as intended...
                # Check now inside self.youWaitMusicPlayer
                player_status = self.youWaitMusicPlayer()
                if not player_status:
                    v0_print("Shutting down, dialog prompt or player broken!")
                    return False

            if not self.checkAdRunning():
                break

        # Force on full screen
        actions = ActionChains(self.webDriver)
        actions.send_keys('f')  # Send full screen key
        actions.perform()

        return True

    def getPlayerStatus(self):
        """ Get movie player state:
                -1 = ad is playing
                0 = Unknown (First time appeared on Oct 29/23 - 9:50 am)
                1 = playing
                2 = paused or user dragging YT progress bar
                3 = begin playing song or YouTube prompting to play after suspend
                5 = Status prior to Play All and starting Ad

        Credit: https://stackoverflow.com/q/29706101/6929343

        "YTP_STATUS": None,  # YouTube Media Player Status. Integer: -1, 1, 2, 3, 5
        "YTP_STATUS_CHANGED": None,  # Time that Player Status changed.
        "YTP_TIME_PLAYED": 0,  # Amount of current video played in seconds.
        "YTP_AD_COUNT": 0,  # Number of Ads skipped all videos.

        """
        _who = self.who + "getPlayerStatus():"
        try:
            # Player status for accurate duration countdown
            player_status = self.webDriver.execute_script(
                "return document.getElementById('movie_player').getPlayerState()")
            if GLO['YTP_STATUS'] and player_status != GLO['YTP_STATUS']:
                GLO['YTP_STATUS'] = player_status
                GLO['YTP_STATUS_CHANGED'] = time.time()
            return player_status
        except WebDriverException as err:
            v0_print(_who, "WebDriverException:")
            v0_print(" ", err)
            return None
        except AttributeError as err:
            v0_print(_who, "AttributeError:")
            v0_print(" ", err)
            v0_print("  Was video paused at very start then resumed?")
            return None

    def checkAdRunning(self):
        """ NOTE: When ad starts playing it opens a new PulseAudio instance.
                  1) Turn down volume immediately
                  2) Test what happens when job is killed?

            NOTE: Player status will be "-1" while ad is running or "3" if ad
                  is starting. May also be "5" (in between songs in a playlist)

        :return: True if ad displaying, False if no ad displayed
        """
        try:
            # TODO Start Duration Countdown
            _ad = self.webDriver.find_element(
                By.CSS_SELECTOR, ".ytp-ad-duration-remaining")
            return True
        except (NoSuchElementException, WebDriverException):
            return False

    def checkContinue(self):
        """ YouTube Housekeeping.
            Respond to prompt: "Video paused. Continue Watching?"

                                ......                  "Yes"

        """
        element = None
        # try:  # element is never found so comment out to save time
        #    element = self.webDriver.find_element_by_xpath(
        #        "//*[contains(text(), 'Video paused. Continue Watching?')]")
        # except NoSuchElementException:
        #    element = None
        try:
            element2 = self.webDriver.find_element_by_id("confirm-button")
        except NoSuchElementException:
            element2 = None
        if not element and not element2:
            return

        # print("youHousekeeping() - Found element:", element,
        #      " | element2:", element2)
        # youHousekeeping() - Found element: None  | element2:
        #   <selenium.webdriver.remote.web element.WebElement
        #   (session="6ac4176d1ef05a453703aea114ac5541",
        #   element="0.16380191644441688-11")>
        if element2.is_displayed():
            # Initially element2 is not present. First time is present during
            # self.youWaitMusicPlayer() after 10 songs have played. Thereafter,
            # element2 is present during 1 minute check but is not displayed.
            # element2 is displayed for song #17. It is present every minute
            # until Song #20 and disappears during Song #21 which is first time
            # for MicroFormat is forced after 0.9 seconds. Song #30 gets confirm
            # when ad visible and player status -1 in endless loop.
            self.youPrint("youHousekeeping() - click ID: 'confirm-button'", lv=2, nl=True)
            stat = self.youGetPlayerStatus()  # Status = 2
            self.youPrint("Player Status BEFORE click:", stat, lv=2)
            element2.click()  # result1
            time.sleep(.33)  # Nov 6/23 was 1.0, try shorter time for Status
            stat = self.youGetPlayerStatus()  # Status = 1
            self.youPrint("Player Status AFTER click :", stat, "\n", lv=2)
            return
        '''
    <yt-button-renderer id="confirm-button" 
        class="style-scope yt-confirm-dialog-renderer" button-renderer="" 
        button-next="" dialog-confirm=""><!--css-build:shady--><yt-button-shape>
        <button class="yt-spec-button-shape-next yt-spec-button-shape-next--text 
        yt-spec-button-shape-next--call-to-action 
        yt-spec-button-shape-next--size-m" aria-label="Yes" title="" style="">

        <div class="yt-spec-button-shape-next__button-text-content">
        <span class="yt-core-attributed-string 
        yt-core-attributed-string--white-space-no-wrap" 
        role="text">Yes</span></div>

        <yt-touch-feedback-shape style="border-radius: inherit;">
        <div class="yt-spec-touch-feedback-shape 
            yt-spec-touch-feedback-shape--touch-response" aria-hidden="true">
            <div class="yt-spec-touch-feedback-shape__stroke" style=""></div>
            <div class="yt-spec-touch-feedback-shape__fill" style=""></div>
        </div>
        '''
        # if not self.youDriverClick("id", "confirm-button"):
        #    print("youHousekeeping(): Error clicking 'Yes' button")

        # youHousekeeping() - Found element: None
        #   element2: <selenium.webdriver.remote.web element.WebElement
        #   (session="394498a9a5db08d5b6dbd83e27591f34",
        #   element="0.951519416280243-15")>
        # youHousekeeping() - Found element: None
        #   element2: <selenium.webdriver.remote.web element.WebElement
        #   (session="394498a9a5db08d5b6dbd83e27591f34",
        #   element="0.951519416280243-15")>
        # Exception in Tkinter callback
        # Traceback (most recent call last):
        #   File "/usr/lib/python2.7/lib-tk/Tkinter.py", line 1540, in __call__
        #     return self.func(*args)
        #   File "/home/rick/python/mserve.py", line 15699, in <lambda>
        #     command=lambda: self.youSmartPlayAll())
        #   File "/home/rick/python/mserve.py", line 16316, in youSmartPlayAll
        #     self.youHousekeeping()
        #   File "/home/rick/python/mserve.py", line 17879, in youHousekeeping
        #     if not self.youDriverClick("id", "confirm-button"):
        #   File "/home/rick/python/mserve.py", line 17665, in youDriverClick
        #     wait.until(EC.element_to_be_clickable((By.ID, desc))).click()
        #   File "/usr/lib/python2.7/dist-packages/selenium/webdriver/support/wait.py", line 80, in until
        #     raise TimeoutException(message, screen, stacktrace)
        # TimeoutException: Message:

        return

    def waitVideoRestart(self, startup=False):
        """ Formally "YouWaitMediaPlayer"

            openVideo() was just executed. Wait for browser to process.
            Wait until YouTube video player status is:
                1 Music Playing or,
               -1 Ad Playing

            :param startup: When True override 10 second timeout to 1 second
            :return: None = timeout reached, 99 = startup 1 sec timeout reached,
                     player_status = -1 ad playing, = 1 video playing """

        ''' Housekeeping every 1 second (out of 10) '''
        lastHousekeepingTime = time.time()

        count_none = count_2 = count_3 = count_5 = 0
        start = time.time()
        while True:
            if not lcs.fast_refresh(tk_after=False):
                return None
            elapsed = (time.time() - start) * 1000
            if elapsed > 10000.0:  # Greater than 10 seconds?
                self.youPrint("youWaitMusicPlayer() took",
                              "more than 10,000 milliseconds", lv=1, nl=True)
                self.youPrint(
                    "Elapsed:", '{:n}'.format(elapsed),
                    "ms  | Null:", count_none, " | Paused:", count_2,
                    " | Starting:", count_3, " | Idle:", count_5, "\n", lv=1)
                return None

            ad_playing = None  # def getPlayerStatus(
            player_status = self.getPlayerStatus()
            if player_status is None:
                count_none += 1  # Still initializing
            elif player_status == 2:
                count_2 += 1  # Music Paused... this is a problem
            elif player_status == 3:
                count_3 += 1  # Something is about to play
            elif player_status == 5:
                ad_playing = self.youCheckAdRunning()
                if ad_playing:
                    break  # Oct 5/23 new technique
                count_5 += 1  # Between songs or Ad before 1st song
                if elapsed > 1000.0 and startup:
                    print("Overriding 1 second IPL player delay")
                    return 99
            elif player_status == 1 or player_status == -1:
                break

            ''' Test 1 second out of 10 seconds when not startup '''
            now = time.time()
            if not startup and now - lastHousekeepingTime > 1.0:
                # Prints for song #10, #17
                self.youPrint(
                    "youWaitMusicPlayer() - 1 second Housekeeping check.")
                lastHousekeepingTime = now
                self.checkPlaylistTimeout()   # def checkPlaylistTimeout(

        self.youPrint("youWaitMusicPlayer", '{:n}'.format(elapsed),
                      "ms | Null:", count_none, " | Paused:", count_2,
                      " | Starting:", count_3, " | Idle:", count_5, lv=7, nl=True)

        # Potentially reverse volume override earlier.
        # Getting many false positives as already at desired volume...
        ad = player_status == -1 or ad_playing
        if not ad:  # Music Video is playing
            # self.youPrint("Reversing self.youAssumeAd")
            self.youAssumedAd = None
            self.youVolumeOverride(ad)  # Restore volume 100%
        elif not self.youAssumedAd:  # Ad is running
            self.youVolumeOverride(ad)  # Turn down volume 25%
            self.youAssumedAd = True

        return player_status

    def checkPlaylistTimeout(self):
        """ Respond to prompt: "Video paused. Continue Watching?"

                                ......                  "Yes"

        """
        element = None
        # try:  # element is never found so comment out to save time
        #    element = self.webDriver.find_element_by_xpath(
        #        "//*[contains(text(), 'Video paused. Continue Watching?')]")
        # except NoSuchElementException:
        #    element = None
        try:
            element2 = self.webDriver.find_element_by_id("confirm-button")
        except NoSuchElementException:
            element2 = None
        if not element and not element2:
            return

        # print("youHousekeeping() - Found element:", element,
        #      " | element2:", element2)
        # youHousekeeping() - Found element: None  | element2:
        #   <selenium.webdriver.remote.web element.WebElement
        #   (session="6ac4176d1ef05a453703aea114ac5541",
        #   element="0.16380191644441688-11")>
        if element2.is_displayed():
            # Initially element2 is not present. First time is present during
            # self.youWaitMusicPlayer() after 10 songs have played. Thereafter,
            # element2 is present during 1 minute check but is not displayed.
            # element2 is displayed for song #17. It is present every minute
            # until Song #20 and disappears during Song #21 which is first time
            # for MicroFormat is forced after 0.9 seconds. Song #30 gets confirm
            # when ad visible and player status -1 in endless loop.
            self.youPrint("youHousekeeping() - click ID: 'confirm-button'", lv=2, nl=True)
            stat = self.getPlayerStatus()  # Status = 2
            self.youPrint("Player Status BEFORE click:", stat, lv=2)
            element2.click()  # result1
            time.sleep(.33)  # Nov 6/23 was 1.0, try shorter time for Status
            stat = self.getPlayerStatus()  # Status = 1
            self.youPrint("Player Status AFTER click :", stat, "\n", lv=2)
            return
        '''
    <yt-button-renderer id="confirm-button" 
        class="style-scope yt-confirm-dialog-renderer" button-renderer="" 
        button-next="" dialog-confirm=""><!--css-build:shady--><yt-button-shape>
        <button class="yt-spec-button-shape-next yt-spec-button-shape-next--text 
        yt-spec-button-shape-next--call-to-action 
        yt-spec-button-shape-next--size-m" aria-label="Yes" title="" style="">

        <div class="yt-spec-button-shape-next__button-text-content">
        <span class="yt-core-attributed-string 
        yt-core-attributed-string--white-space-no-wrap" 
        role="text">Yes</span></div>

        <yt-touch-feedback-shape style="border-radius: inherit;">
        <div class="yt-spec-touch-feedback-shape 
            yt-spec-touch-feedback-shape--touch-response" aria-hidden="true">
            <div class="yt-spec-touch-feedback-shape__stroke" style=""></div>
            <div class="yt-spec-touch-feedback-shape__fill" style=""></div>
        </div>
        '''
        # if not self.youDriverClick("id", "confirm-button"):
        #    print("youHousekeeping(): Error clicking 'Yes' button")

        # youHousekeeping() - Found element: None
        #   element2: <selenium.webdriver.remote.web element.WebElement
        #   (session="394498a9a5db08d5b6dbd83e27591f34",
        #   element="0.951519416280243-15")>
        # youHousekeeping() - Found element: None
        #   element2: <selenium.webdriver.remote.web element.WebElement
        #   (session="394498a9a5db08d5b6dbd83e27591f34",
        #   element="0.951519416280243-15")>
        # Exception in Tkinter callback
        # Traceback (most recent call last):
        #   File "/usr/lib/python2.7/lib-tk/Tkinter.py", line 1540, in __call__
        #     return self.func(*args)
        #   File "/home/rick/python/mserve.py", line 15699, in <lambda>
        #     command=lambda: self.youSmartPlayAll())
        #   File "/home/rick/python/mserve.py", line 16316, in youSmartPlayAll
        #     self.youHousekeeping()
        #   File "/home/rick/python/mserve.py", line 17879, in youHousekeeping
        #     if not self.youDriverClick("id", "confirm-button"):
        #   File "/home/rick/python/mserve.py", line 17665, in youDriverClick
        #     wait.until(EC.element_to_be_clickable((By.ID, desc))).click()
        #   File "/usr/lib/python2.7/dist-packages/selenium/webdriver/support/wait.py", line 80, in until
        #     raise TimeoutException(message, screen, stacktrace)
        # TimeoutException: Message:

        return

    def waitDriverForward(self, startup=False):
        """ Formally "YouWaitMediaPlayer"

            self.webDriver.forward() was just executed. Wait for browser to process.
            Wait until YouTube video player status is:
                1 Music Playing or,
               -1 Ad Playing

            :param startup: When True override 10 second timeout to 1 second
            :return: None = timeout reached, 99 = startup 1 sec timeout reached,
                     player_status = -1 ad playing, = 1 video playing """

        ''' Housekeeping every 1 second (out of 10) '''
        lastHousekeepingTime = time.time()

        count_none = count_2 = count_3 = count_5 = 0
        start = time.time()
        while True:
            if not lcs.fast_refresh(tk_after=False):
                return None
            elapsed = (time.time() - start) * 1000
            if elapsed > 10000.0:  # Greater than 10 seconds?
                self.youPrint("youWaitMusicPlayer() took",
                              "more than 10,000 milliseconds", lv=1, nl=True)
                self.youPrint(
                    "Elapsed:", '{:n}'.format(elapsed),
                    "ms  | Null:", count_none, " | Paused:", count_2,
                    " | Starting:", count_3, " | Idle:", count_5, "\n", lv=1)
                return None

            ad_playing = None
            player_status = self.getPlayerStatus()
            if player_status is None:
                count_none += 1  # Still initializing
            elif player_status == 2:
                count_2 += 1  # Music Paused... this is a problem
            elif player_status == 3:
                count_3 += 1  # Something is about to play
            elif player_status == 5:
                ad_playing = self.youCheckAdRunning()
                if ad_playing:
                    break  # Oct 5/23 new technique
                count_5 += 1  # Between songs or Ad before 1st song
                if elapsed > 1000.0 and startup:
                    print("Overriding 1 second IPL player delay")
                    return 99
            elif player_status == 1 or player_status == -1:
                break

            ''' Test 1 second out of 10 seconds when not startup '''
            now = time.time()
            if not startup and now - lastHousekeepingTime > 1.0:
                # Prints for song #10, #17
                self.youPrint(
                    "youWaitMusicPlayer() - 1 second Housekeeping check.")
                lastHousekeepingTime = now
                self.youHousekeeping()

        self.youPrint("youWaitMusicPlayer", '{:n}'.format(elapsed),
                      "ms | Null:", count_none, " | Paused:", count_2,
                      " | Starting:", count_3, " | Idle:", count_5, lv=7, nl=True)

        # Potentially reverse volume override earlier.
        # Getting many false positives as already at desired volume...
        ad = player_status == -1 or ad_playing
        if not ad:  # Music Video is playing
            # self.youPrint("Reversing self.youAssumeAd")
            self.youAssumedAd = None
            self.youVolumeOverride(ad)  # Restore volume 100%
        elif not self.youAssumedAd:  # Ad is running
            self.youVolumeOverride(ad)  # Turn down volume 25%
            self.youAssumedAd = True

        return player_status

    def adVolumeOverride(self, ad=True):
        """ If commercial at 100% set to 25%. If not commercial and
            25%, set to 100% """

        second = self.youGetChromeSink()  # Set active self.youPlayerSink
        first = self.youPlayerSink  # 2023-12-04 used to be 2nd, but swapped

        if self.youPlayerSink is None:
            self.youPrint("youVolumeOverride() sink failure!")
            # First video after age restricted video that won't play
            return

        sink_no = self.youPlayerSink.sink_no_str
        if self.youPlayerSink != first:
            self.youPrint("Multiple Google Chrome Audio Sinks !!!",
                          first.sink_no_str, sink_no)
            print("First :", first)
            print("Second:", second)

        try:
            vol = pav.get_volume(sink_no)
        except Exception as err:
            self.youPrint("youVolumeOverride() Exception:", err)
            return

        if vol != 25 and vol != 100:
            self.youPrint("Sink:", sink_no,
                          "Invalid VOLUME:", vol, type(vol))
        if ad:
            # self.youPrint("Sink:", self.youPlayerSink.sink_no_str,
            #              "Volume during commercial:", vol, type(vol))
            if vol == 100:
                pav.set_volume(sink_no, 25.0)
                self.youPrint("Sink No:", sink_no, "Volume forced to 25%", level=5)
            else:
                self.youPrint("Sink No:", sink_no, "Volume NOT forced:", vol, level=5)
                pass
        else:
            self.youPrint("Sink:", sink_no,
                          "Volume NO commercial:", vol, type(vol), level=5)
            if vol == 25:
                pav.set_volume(sink_no, 100.0)
                self.youPrint("Sink No:", sink_no, "Volume forced to 100%", level=5)
            else:
                self.youPrint("Sink No:", sink_no, "Volume NOT forced:", vol, level=5)
                pass

    def sendSpaceBar(self):
        """ Sending space bar toggles pause/play in YouTube """
        _who = self.who + "sendSpaceBar():"

        ''' YouTube toggle player with space bar '''
        actions = ActionChains(self.webDriver)
        actions.send_keys(' ')  # Send space
        actions.perform()

    #  +===============================================================+
    #  |                                                               |
    #  |   Playlists Class Toplevel Methods used by all entry points   |
    #  |                                                               |
    #  +===============================================================+

    def create_window(self, name=None):
        """ Mount window with Playlist Treeview or placeholder text when none.
            :param name: "New Playlist", "Open Playlist", etc.
        """
        self.pending_counts = self.get_pending()  # Count of playlist additions and deletes
        self.build_playlists()  # Rebuild playlist changes since last time
        self.create_top(name)  # create_top() shared with buildYouTubePlaylist

        ''' Create master frame '''
        self.frame = tk.Frame(self.top, borderwidth=g.FRM_BRD_WID,
                              relief=tk.RIDGE, bg="WhiteSmoke")
        self.frame.grid(sticky=tk.NSEW)
        # self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=3)  # Data entry fields
        self.frame.rowconfigure(0, weight=1)
        ms_font = g.FONT

        ''' Instructions when no playlists have been created yet. '''
        if not self.text:  # If text wasn't passed as a parameter use default
            self.text = "\nNo Playlists have been created.\n\n" + \
                        "Create a playlist with the 'File' dropdown menu.\n" + \
                        "Select the 'New Playlist' option from the menu.\n\n" + \
                        "Playlists will then appear in this spot.\n\n"

        if len(self.all_numbers) == 0:  # 2024-04-03 change "==" to "!=" to test
            # No playlists have been created
            tk.Label(self.frame, text=self.text, bg="WhiteSmoke", font=ms_font). \
                grid(row=0, column=0, columnspan=4, sticky=tk.EW)
        else:
            self.populate_dd_view()  # Paint treeview of playlists

        ''' Playlist Name is readonly except for 'new' and 'rename' '''
        tk.Label(self.frame, text="Playlist name:", bg="WhiteSmoke",
                 font=ms_font).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.fld_name = tk.Entry(self.frame, textvariable=self.scr_name,
                                 state='readonly', font=ms_font)
        self.fld_name.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.scr_name.set("")  # Clear left over from last invocation

        ''' Playlist Description is readonly except for 'new' and 'rename' '''
        tk.Label(self.frame, text="Playlist description:", bg="WhiteSmoke",
                 font=ms_font).grid(row=2, column=0, sticky=tk.W, padx=5)
        self.fld_description = tk.Entry(
            self.frame, textvariable=self.scr_description, state='readonly',
            font=ms_font)
        self.fld_description.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        self.scr_description.set("")  # Clear left over from last invocation

        ''' Device Location is always readonly '''
        tk.Label(self.frame, text="Device location:", bg="WhiteSmoke",
                 font=ms_font).grid(row=3, column=0, sticky=tk.W, padx=5)
        tk.Entry(self.frame, textvariable=self.scr_location, state='readonly',
                 font=ms_font).grid(row=3, column=1, sticky=tk.W, padx=5,
                                    pady=5)
        self.scr_location.set(lcs.open_code + " - " + lcs.open_name)
        self.input_active = False

        ''' Song Count display only field '''
        tk.Label(self.frame, text="Song Count:", bg="WhiteSmoke",
                 font=ms_font).grid(row=1, column=2, sticky=tk.W, padx=5)
        self.fld_count = tk.Label(self.frame, text="0", font=ms_font)
        self.fld_count.grid(row=1, column=3, sticky=tk.W, padx=5)

        ''' Size of Files display only field '''
        tk.Label(self.frame, text="Size of Files:", bg="WhiteSmoke",
                 font=ms_font).grid(row=2, column=2, sticky=tk.W, padx=5)
        self.fld_size = tk.Label(self.frame, text="0", font=ms_font)
        self.fld_size.grid(row=2, column=3, sticky=tk.W, padx=5)

        ''' Music Duration display only field '''
        tk.Label(self.frame, text="Music Duration:", bg="WhiteSmoke",
                 font=ms_font).grid(row=3, column=2, sticky=tk.W, padx=5)
        self.fld_seconds = tk.Label(self.frame, text="0", font=ms_font)
        self.fld_seconds.grid(row=3, column=3, sticky=tk.W, padx=5)

        ''' button frame '''
        bottom_frm = tk.Frame(self.frame, bg="WhiteSmoke")
        bottom_frm.grid(row=4, columnspan=4, sticky=tk.E)

        ''' Apply Button '''
        _close_tt_text = "Close Playlist window."
        # if self.state != 'view':
        close_tt_text = "Discard any changes and close Playlist window."
        action = name.split(" Playlist")[0]

        if name.startswith("Create"):
            action = "Create"  # name is "Create Loudness Normalization Playlist"
            # 2024-04-28 temporary values until AVO settings saved in config
            self.scr_name.set(lcs.avo_playlist_name)
            self.scr_description.set(lcs.avo_playlist_description)

        self.apply_button = ttk.Button(bottom_frm, text="✔ " + action, style="P.TButton",
                                       width=g.BTN_WID2 - 2, command=self.apply)
        self.apply_button.grid(row=0, column=0, padx=10, pady=5, sticky=tk.E)
        self.tt.add_tip(self.apply_button, action + " Playlist and return.",
                        anchor="nw")
        self.top.bind("<Return>", self.apply)

        ''' Help Button - https://www.pippim.com/programs/mserve.html#HelpPlaylists '''
        help_text = "Open new window in default web browser for\n"
        help_text += "videos and explanations on using this screen.\n"
        help_text += "https://www.pippim.com/programs/mserve.html#\n"
        self.help_button = ttk.Button(
            bottom_frm, text="⧉ Help", width=g.BTN_WID2 - 4,
            style="P.TButton", command=lambda: g.web_help("HelpPlaylists"))
        self.help_button.grid(row=0, column=1, padx=10, pady=5, sticky=tk.E)
        self.tt.add_tip(self.help_button, help_text, anchor="ne")

        ''' Close Button - NOTE: This calls reset() function !!! '''
        self.close_button = ttk.Button(bottom_frm, text="✘ Close", style="P.TButton",
                                       width=g.BTN_WID2 - 4, command=self.reset)
        self.close_button.grid(row=0, column=2, padx=(10, 5), pady=5, sticky=tk.E)
        self.tt.add_tip(self.close_button, close_tt_text, anchor="ne")
        self.top.bind("<Escape>", self.reset)
        self.top.protocol("WM_DELETE_WINDOW", self.reset)

        ''' Refresh screen '''
        if self.top:  # May have been closed above.
            self.top.update_idletasks()

    def create_top(self, name):
        """ Shared with self.create_window(), self.displayMusicIds()
            self.displayPlaylistCommonTop() and self.buildYouTubePlaylist() """

        self.top = tk.Toplevel()  # Playlists top level
        ''' Save geometry for Playlists() '''
        geom = monitor.get_window_geom('playlists')
        self.top.geometry(geom)
        self.top.minsize(width=g.BTN_WID * 10, height=g.PANEL_HGT * 10)
        name = name if name is not None else "Playlists"
        self.top.title(name + " - mserve")
        # self.top.configure(background="Gray")  # Sep 5/23 - Use new default
        self.top.configure(background="#eeeeee")  # Replace "LightGrey"
        self.top.columnconfigure(0, weight=1)
        self.top.rowconfigure(0, weight=1)
        ''' After top created, disable all File Menu options for playlists '''
        self.enable_lib_menu()

        ''' Set program icon in taskbar '''
        # cfg = sql.Config()  # 2024-03-13 Use SQL for Configuration colors
        sql_key = ['cfg_playlists', 'toplevel', 'taskbar_icon', 'height & colors']
        ti = cfg.get_cfg(sql_key)
        img.taskbar_icon(self.top, ti['height'], ti['outline'],
                         ti['fill'], ti['text'], char=ti['char'])
        # img.taskbar_icon(self.top, 64, 'white', 'lightskyblue', 'black')

    def enable_input(self):
        """ Turn on input fields for 'new', 'rename' and 'save_as' """
        self.input_active = True
        self.fld_name['state'] = 'normal'  # 'normal' allows input
        self.fld_description['state'] = 'normal'  # vs 'read_only'

    def build_playlists(self):
        """ Get ALL configuration history rows for Type = 'playlist'
            Create sorted list of names for current location. Called
            each time Playlists.function() used. """
        ''' Read all playlists from SQL History Table into work lists '''
        for row in sql.hist_cursor.execute(
                "SELECT * FROM History INDEXED BY TypeActionIndex " +
                "WHERE Type = 'playlist'"):
            d = dict(row)
            self.make_act_from_hist(d)
            self.all_numbers.append(self.act_code)
            self.all_names.append(self.act_name)
            self.names_all_loc.append(self.act_name)
            if self.act_loc_id == lcs.open_code:
                self.names_for_loc.append(self.act_name)
        self.names_all_loc.sort()
        self.names_for_loc.sort()

    def populate_dd_view(self):
        """ Data Dictionary routines for managing treeview. """

        ''' Data Dictionary and Treeview column names '''
        history_dict = sql.playlist_treeview()

        # Without the FAKE first call, dd_view is empty on the REAL second call
        t2 = tk.Toplevel()
        f2 = tk.Frame(t2)
        f2.grid()
        _v2 = toolkit.DictTreeview(history_dict, t2, f2, sql_type="playlists")
        _v2 = None
        t2.destroy()

        ''' Create treeview frame with scrollbars '''
        self.tree_frame = tk.Frame(self.frame, relief=tk.RIDGE)
        self.tree_frame.grid(row=0, column=0, sticky=tk.NSEW, columnspan=4)
        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.rowconfigure(0, weight=1)

        # Note self.dd_view.frame is created inside self.tree_frame
        # Then self.dd_view.tree is created inside self.dd_view.frame
        # self.dd_view.frame is needed for edge borders around tree

        self.dd_view = toolkit.DictTreeview(
            history_dict, self.top, self.tree_frame, sql_type="playlists",
            highlight_callback=self.highlight_callback)

        # print("save_dict2 == history_dict:", save_dict2 == history_dict)
        # print([x for x in history_dict if x not in save_dict2])

        ''' Override formatting of 'size' column to MB '''
        self.dd_view.change_column_format("MB", "size")
        ''' Override formatting of 'seconds' column to Days:Hours:Min:Sec '''
        self.dd_view.change_column_format("days", "seconds")

        ''' Treeview click and drag columns to different order '''
        # Moving columns needs work and probably isn't even needed
        # toolkit.MoveTreeviewColumn(self.top, self.dd_view.tree,
        #                           row_release=self.dd_view_click)

        ''' Treeview select item with button clicks '''

        def double_click(event):
            """ double click - 2024-05-04 only works second time??? """
            # print("double_click")
            if self.dd_view_click(event):
                # print("self.dd_view_click(event) SUCCESS")
                self.apply(event)

        self.dd_view.tree.bind("<Button-1>", self.dd_view_click)
        self.dd_view.tree.bind("<Button-3>", self.dd_view_click)
        self.dd_view.tree.bind("<Double-Button-1>", double_click)
        # 2024-04-03 SQL Config() to-do: highlight colors
        self.dd_view.tree.tag_configure('play_sel', background='ForestGreen',
                                        foreground="White")

        ''' Loop through sorted lists, reread history and insert in tree '''
        for name in self.names_for_loc:  # Sorted alphabetically
            ndx = self.all_names.index(name)  # In key order P000001, P000002, etc.
            number_str = self.all_numbers[ndx]
            playlist = sql.get_config('playlist', number_str)  # Must be here
            self.dd_view.insert("", playlist, number_str)  # 2024-04-04

        # self.dd_view.tree['show'] = 'headings'  # 2024-04-03 treeview is blank
        # self.top.update_idletasks()  # 2024-04-03 treeview is blank

    def dd_view_click(self, event):
        """ Left button clicked on Playlist row. """
        number_str = self.dd_view.tree.identify_row(event.y)
        if self.state == "new" or self.state == "save_as" \
                or self.state == "create_loudnorm":
            # cannot use enable_input because rename needs to pick old name first
            text = "Cannot pick an old playlist when new playlist name required.\n\n" + \
                   "Enter a new Playlist name and description below."
            message.ShowInfo(self.top, "Other playlists are for reference only!",
                             text, icon='warning', thread=self.get_thread)
            return False
        else:
            ''' Highlight row clicked '''
            toolkit.tv_tag_remove_all(self.dd_view.tree, 'play_sel')
            toolkit.tv_tag_add(self.dd_view.tree, number_str, 'play_sel')

            self.read_playlist(number_str)
            self.scr_name.set(self.act_name)
            self.scr_description.set(self.act_description)
            self.scr_location.set(self.act_loc_id)
            self.fld_count['text'] = '{:n}'.format(self.act_count)
            self.fld_size['text'] = toolkit.human_mb(self.act_size)
            self.youDebug = self.act_size  # YouTube Print Debug level
            self.fld_seconds['text'] = tmf.days(self.act_seconds)
            self.top.update_idletasks()
            # print("Music IDs", self.act_music_ids)
            return True

    def highlight_callback(self, number_str):
        """ As lines are highlighted in treeview, this function is called.
        :param number_str: Playlist number used as iid inside treeview
        :return: None """
        pass

    def checkYouTubePlaylist(self):
        """ Is Playlist from YouTube? """

        if not self.act_description.startswith("https://www.youtube.com"):
            return False
        self.nameYouTube = WEB_PLAY_DIR + os.sep + self.act_name + ".csv"
        # if not os.path.isfile(self.nameYouTube):
        #    return True
        self.linkYouTube = ext.read_into_list(self.nameYouTube)
        if not self.linkYouTube:
            # return False
            self.linkYouTube = []  # YouTube Video Links need to be built

        return True

    def buildYouTubePlaylist(self):
        """ Build list of dictionaries
            TODO: 2024-01-28 - Build Chill playlist video #90 should be hidden
                but it appears in mserve. Then video counts are out of sync.
                https://www.youtube.com/watch?v=562VuMrFUys
        """
        self.listYouTube = []
        # self.dictYouTube = {}  # Oct 8/23 - wasn't referenced
        self.photosYouTube = []

        ''' Previous generation available? '''
        fname = self.nameYouTube.replace(".csv", ".pickle")
        fname2 = self.nameYouTube.replace(".csv", ".private")
        if os.path.isfile(fname):
            self.listYouTube = ext.read_from_pickle(fname)
            self.privateYouTube = ext.read_into_string(fname2)
            if self.linkYouTube and self.listYouTube:
                if len(self.linkYouTube) == len(self.listYouTube):
                    return True

        self.act_count = 0  # Music video count (excludes private & deleted)
        self.act_seconds = 0.0  # Duration of all songs

        ''' dtb for retrieving YouTube Images first time. '''
        dtb = message.DelayedTextBox(title="Get YouTube Playlist", width=1000,
                                     toplevel=self.top, startup_delay=0)
        for link in self.linkYouTube:
            try:  # split link into segments
                song_name = link.rsplit(";", 2)[0]
                link_name = link.rsplit(";", 2)[1]
                duration = link.rsplit(";", 2)[2].strip()
                video_name = link_name.split("/watch?v=")[1]  # 7lYOmkBRs3s
                image_name = "https://i.ytimg.com/vi/" + video_name
                image_name += "/" + YOUTUBE_RESOLUTION
                # YOUTUBE_RESOLUTION = "mqdefault.jpg"  # 63 videos = 176.4 KB
            except ValueError:
                print("buildYouTubePlaylist() Value Error.")
                continue

            try:  # grab image thumbnail
                raw_data = requests.get(image_name).content
            except requests.exceptions.RequestException as e:  # This is the correct syntax
                print("RequestException:", e)
                continue

            try:  # convert thumbnail image into tkinter format
                im = Image.open(BytesIO(raw_data))
                image = {
                    'pixels': im.tobytes(),
                    'size': im.size,
                    'mode': im.mode,
                }
                dictYouTube = dict()
                dictYouTube['name'] = song_name
                dictYouTube['link'] = link_name
                dictYouTube['duration'] = duration
                dictYouTube['image'] = image
                self.listYouTube.append(dictYouTube)
                # print("song:", song_name, "duration:", duration)
                self.act_count += 1
                self.act_seconds += float(tmf.get_sec(duration))

                if not lcs.fast_refresh():
                    self.webDriver.quit()
                    return False
                """
                thread = self.get_thread()  # repeated 3 times....
                if thread:
                    thread()
                else:
                    return False  # closing down...
                """
            except tk.TclError:  # Not sure if this works for PIL yet....
                print("buildYouTubePlaylist() tk.TclError.")
                continue
            dtb_line = "Name: " + song_name + " Image: " + image_name
            dtb.update(dtb_line)

        dtb.close()

        ''' Save list so it doesn't have to be regenerated '''
        self.save_act()  # Save count and seconds
        ext.write_to_pickle(fname, self.listYouTube)
        # return len(self.listYouTube) > 0
        return True  # smart play all will now automatically build list

    def mergeYouTubePlaylist(self, listVideos, private_count):
        """ Playlists already built with buildYouTubePlaylist. When opening
            YouTube new videos discovered. Rebuild using previous lists.
            TODO: 2024-01-28 - Build Chill playlist video #90 should be hidden
                but it appears in mserve. Then video counts are out of sync.
                https://www.youtube.com/watch?v=562VuMrFUys
        """
        self.listMergeYouTube = []

        ''' Previous generation available? '''
        # fname = self.nameYouTube.replace(".csv", ".pickle")
        # if os.path.isfile(fname):
        #    self.listYouTube = ext.read_from_pickle(fname)
        #    if self.listYouTube and self.listYouTube:
        #        if len(self.linkYouTube) == len(self.listYouTube):
        #            return True

        self.act_count = 0
        self.act_seconds = 0.0  # Duration of all songs
        existing_count = new_count = 0

        ''' dtb for retrieving YouTube Images first time. '''
        dtb = message.DelayedTextBox(title="Merge YouTube Playlist", width=1000,
                                     toplevel=self.top, startup_delay=0)
        # for link in self.linkYouTube:
        for link in listVideos:
            try:  # split link into segments
                song_name = link.rsplit(";", 2)[0]
                song_name = toolkit.normalize_tcl(song_name)
                # Fix: self.tk.call((self._w, 'insert', index, chars) + args)
                # TclError: character U+1f98b is above the range (U+0000-U+FFFF) allowed by Tcl
                link_name = link.rsplit(";", 2)[1]
                duration = link.rsplit(";", 2)[2].strip()
                video_name = link_name.split("/watch?v=")[1]
                image_name = "https://i.ytimg.com/vi/" + video_name
                image_name += "/" + YOUTUBE_RESOLUTION
            except ValueError:
                print("mergeYouTubePlaylist() Value Error.")
                continue

            try:
                # If existing link / list, reuse it.
                ndx = self.linkYouTube.index(link)
                # dictYouTube = dict()
                dictExisting = self.listYouTube[ndx]
                self.listMergeYouTube.append(dictExisting)
                existing_count += 1
                self.act_count += 1
                self.act_seconds += float(tmf.get_sec(duration))
                continue
            except ValueError:
                # New video
                new_count += 1

            try:  # grab image thumbnail
                raw_data = requests.get(image_name).content
            except requests.exceptions.RequestException as e:  # This is the correct syntax
                print("RequestException:", e)
                continue

            # Below code shared with buildYouTubePlaylist -- DRY
            try:  # convert thumbnail image into tkinter format
                im = Image.open(BytesIO(raw_data))
                image = {
                    'pixels': im.tobytes(),
                    'size': im.size,
                    'mode': im.mode,
                }
                dictYouTube = dict()
                dictYouTube['name'] = song_name
                dictYouTube['link'] = link_name
                dictYouTube['duration'] = duration
                dictYouTube['image'] = image
                # self.listYouTube.append(dictYouTube)
                self.listMergeYouTube.append(dictYouTube)
                # print("song:", song_name, "duration:", duration)
                self.act_count += 1
                self.act_seconds += float(tmf.get_sec(duration))

                if not lcs.fast_refresh():
                    self.webDriver.quit()
                    return False

            except tk.TclError:  # Not sure if this works for PIL yet....
                print("mergeYouTubePlaylist() tk.TclError.")
                continue
            dtb_line = "Name: " + song_name + " Image: " + image_name
            dtb.update(dtb_line)

        dtb.close()

        # TODO: Save listVideos            as self.linkYouTube
        #            self.listMergeYouTube as self.listYouTube
        if True is True:
            print("existing_count:", existing_count, "new_count:", new_count)
            print("len(self.listMergeYouTube):", len(self.listMergeYouTube))
            print("self.listMergeYouTube[0]['name']:",
                  self.listMergeYouTube[0]['name'])
            print("self.listMergeYouTube[1]['name']:",
                  self.listMergeYouTube[1]['name'])
            print("self.listMergeYouTube[-2]['name']:",
                  self.listMergeYouTube[-2]['name'])
            print("self.listMergeYouTube[-1]['name']:",
                  self.listMergeYouTube[-1]['name'])
            self.listYouTube = self.listMergeYouTube

        ''' Save files '''
        fname = self.nameYouTube.replace(".csv", ".pickle")
        fname2 = self.nameYouTube.replace(".csv", ".private")
        self.save_act()  # Save count and seconds
        ext.write_to_pickle(fname, self.listYouTube)
        ext.write_from_string(fname2, str(private_count))
        ext.write_from_list(self.nameYouTube, listVideos)
        return len(self.listYouTube) > 0

    def displayYouTubePlaylist(self):
        """ Read all self.dictYouTube inside self.listYouTube and create
            treeview.
        """

        self.displayPlaylistCommonTop("YouTube")

        for i, self.dictYouTube in enumerate(self.listYouTube):
            song_name = self.dictYouTube['name']
            song_name = toolkit.normalize_tcl(song_name)
            duration = self.dictYouTube['duration']
            lrc = self.dictYouTube.get('lrc', None)
            if lrc:
                lrc_list = lrc.splitlines()
                song_name += "\n\n" + lrc_list[0]
            image = self.dictYouTube['image']
            # from bytes() converts jpg in memory instead of reading from disk
            im = Image.frombytes(image['mode'], image['size'], image['pixels'])

            # Text Draw duration over image & place into self.photosYouTube[]
            self.displayPlaylistCommonDuration(im, duration)
            """ # Text Draw duration over image
            width, height = im.size
            draw_font = ImageFont.true type("DejaVuSans.ttf", 24)
            draw = ImageDraw.Draw(im)
            x0 = width - 75  # text start x
            y0 = height - 30  # text start y
            x1 = x0 + 70
            y1 = y0 + 25
            draw.rectangle((x0 - 10, y0 - 5, x1, y1), fill="#333")
            draw.text((x0, y0), duration, font=draw_font, fill="white")
            # Convert image to tk photo and save from garbage collection
            photo = ImageTk.PhotoImage(im)
            self.photosYouTube.append(photo)  # Save from GIC
            """
            # https://stackoverflow.com/questions/49307497/
            # python-tkinter-treeview-add-an-image-as-a-column-value
            self.you_tree.insert('', 'end', iid=str(i), text="№ " + str(i + 1),
                                 image=self.photosYouTube[-1],
                                 value=(song_name,))
            if not lcs.fast_refresh():
                self.webDriver.quit()
                return False

        self.displayPlaylistCommonBottom(player_button=True)

        if len(self.listYouTube) < 1:
            title = "YouTube Playlist Unknown"
            text = "The YouTube Playlist is unknown to mserve.\n\n"
            text += "It needs to be scanned for mserve to display songs.\n\n"
            text += "Do you want to scan it now?"
            answer = message.AskQuestion(self.top, confirm="No",
                                         thread=self.get_thread,
                                         title=title, text=text)
            if answer.result != 'yes':
                return
            else:
                ''' youSmartPlayAll will calls us when done  '''
                self.youSmartPlayAll()

    def displayPlaylistCommonTop(self, name):
        """ Shared by: displayYouTubePlaylist and displayMusicIds """

        if self.tt and self.tt.check(self.top) is not None:
            self.tt.close(self.top)
        if self.top:
            geom = monitor.get_window_geom_string(self.top, leave_visible=False)
            monitor.save_window_geom('playlists', geom)
            self.top.destroy()
            self.top = None

        ''' create_top() shared with create_window() '''
        common_name = " Playlist: " + self.act_name
        common_name += " - " + str(self.act_count) + " Videos."
        common_name += " - " + tmf.days(self.act_seconds)
        if name == "YouTube":
            # create_top does name += " - mserve"
            self.create_top("YouTube" + common_name)
        else:
            self.create_top("mserve" + common_name)

        ''' Create master frame '''
        self.frame = tk.Frame(self.top, borderwidth=g.FRM_BRD_WID,
                              relief=tk.RIDGE)
        self.frame.grid(sticky=tk.NSEW)

        ''' Refresh screen '''
        if self.top:  # May have been closed above.
            self.top.update_idletasks()

        ''' Create treeview frame with scrollbars '''
        self.tree_frame = tk.Frame(self.frame, bg="LightGrey", relief=tk.RIDGE)
        self.tree_frame.grid(row=0, sticky=tk.NSEW)
        self.tree_frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        #         self.you_btn_frm = tk.Frame(self.frame)
        #         self.you_btn_frm.grid(row=4, column span=4, sticky=tk.NSEW)

        ''' Treeview style is large images in cell 0 '''
        style = ttk.Style()
        style.configure("YouTube.Treeview.Heading", font=(None, MED_FONT),
                        rowheight=int(g.LARGE_FONT * 2.2))  # FONT14 alias
        row_height = 200
        style.configure("YouTube.Treeview", font=g.FONT14, rowheight=row_height)

        # Create Treeview
        self.you_tree = ttk.Treeview(self.tree_frame, column=('name',),
                                     selectmode='none', height=4,
                                     style="YouTube.Treeview")
        self.you_tree.grid(row=0, column=0, sticky='nsew')
        v_scroll = tk.Scrollbar(self.tree_frame, orient=tk.VERTICAL,
                                width=SCROLL_WIDTH, command=self.you_tree.yview)
        v_scroll.grid(row=0, column=1, sticky=tk.NS)
        self.you_tree.configure(yscrollcommand=v_scroll.set)
        # v_scroll.config(trough color='black', bg='gold')
        # https://stackoverflow.com/a/17457843/6929343

        # Left-click, requires two presses to fire
        # self.you_tree.bind('<Button-1>', self.youTreeClick)  # Needs 2 clicks
        # self.you_tree.bind('<ButtonPress-1>', self.youTreeClick)  # Needs 2 clicks
        # self.you_tree.bind('<ButtonRelease-1>', self.youTreeClick)  # Needs 2 clicks
        # self.you_tree.bind("<<TreeviewSelect>>", self.youTreeClick)  # 1 click

        # Right-click - reliable works on first click, first time, all the time
        self.you_tree.bind('<Button-3>', self.youTreeClick)  # Right-click

        # Oct 1, 2023 - MouseWheel event does NOT capture any events
        self.you_tree.bind("<MouseWheel>", lambda event: self.youTreeMouseWheel(event))
        # Button-4 is mousewheel scroll up event
        self.you_tree.bind("<Button-4>", lambda event: self.youTreeMouseWheel(event))
        # Button-5 is mousewheel scroll down event
        self.you_tree.bind("<Button-5>", lambda event: self.youTreeMouseWheel(event))

        # Setup column heading
        self.you_tree.heading('#0', text='Thumbnail Image')
        if name == "YouTube":
            self.you_tree.heading('#1', text='Song Name', anchor='center')
        else:
            self.you_tree.heading('#1', text='Title / Artist / Album / Year')

        # #0, #01, #02 denotes the 0, 1st, 2nd columns

        # Setup column hq default
        # YouTube Resolution: default=120x90(2.8K), hq default=480x360(35.6K)
        # mqdefault = 320x180
        self.you_tree.column('#0', width=450, stretch=False)
        self.you_tree.column('name', anchor='center', width=570, stretch=True)

        # Give some padding between triangles and border, between tree & scroll bars
        self.you_tree["padding"] = (10, 10, 10, 10)  # left, top, right, bottom

        # Highlight current song in green background, white text
        self.you_tree.tag_configure('play_sel', background='ForestGreen',
                                    foreground="White")

        self.top.bind("<Escape>", self.youClosePlayLrc)
        self.top.protocol("WM_DELETE_WINDOW", self.youClosePlayLrc)

    def displayPlaylistCommonDuration(self, im, duration):
        """ Text Draw duration over image
            Shared by: displayYouTubePlaylist and displayMusicIds
        """
        width, height = im.size  # 320x180
        draw_font = ImageFont.truetype("DejaVuSans.ttf", 24)
        draw = ImageDraw.Draw(im)
        x0 = width - 75  # text start x
        y0 = height - 30  # text start y
        x1 = x0 + 70
        y1 = y0 + 25
        draw.rectangle((x0 - 10, y0 - 5, x1, y1), fill="#333")
        draw.text((x0, y0), duration, font=draw_font, fill="white")

        photo = ImageTk.PhotoImage(im)
        self.photosYouTube.append(photo)  # Save from GIC

    def displayPlaylistCommonBottom(self, player_button=False):
        """ Shared by: displayYouTubePlaylist and displayMusicIds
            Column 1 has progress bar hidden until music playing.
            Column 3 has None / Pause / Play button player button.
            Column 4 has Close button.
        """

        ''' button frame '''
        self.you_btn_frm = tk.Frame(self.frame)
        self.you_btn_frm.grid(row=4, columnspan=4, sticky=tk.NSEW)

        ''' Player Button - NOTE: Starts as "None" '''
        if player_button:
            # self.youPlayerButton = None  # Tkinter element mounted with .grid
            # self.youPlayerCurrText = None  # "None" / "Pause" / "Play" button
            # self.youPlayerNoneText = "?  None"  # Music Player Text options
            # self.youPlayerPlayText = "▶  Play"  # used when music player status
            # self.youPlayerPauseText = "❚❚ Pause"  # changes between 1 & 2
            self.youPlayerButton = tk.Button(self.you_btn_frm, text="None",
                                             width=g.BTN_WID2 - 4,
                                             command=self.youTogglePlayer)
            self.youPlayerButton.grid(row=0, column=3, padx=(10, 5),
                                      pady=5, sticky=tk.E)
            self.tt.add_tip(self.youPlayerButton,
                            "Music not playing", anchor="ne")

        ''' Close Button - NOTE: This calls reset() function !!! '''
        self.close_button = tk.Button(self.you_btn_frm, text="✘ Close",
                                      width=g.BTN_WID2 - 4,
                                      command=self.youClosePlayLrc)
        self.close_button.grid(row=0, column=4, padx=(10, 5), pady=5, sticky=tk.E)
        self.tt.add_tip(self.close_button, "Close YouTube Playlist", anchor="ne")

        # Move close higher to CommonTop
        # self.top.bind("<Escape>", self.youClosePlayLrc)
        # self.top.protocol("WM_DELETE_WINDOW", self.youClosePlayLrc)

        ''' Snapshot Pulse Audio '''
        # pav.get_all_sinks  # 2024-01-20 - missing (), not sure of intent...

        ''' Refresh screen '''
        if self.top:  # May have been closed above.
            self.top.update_idletasks()

    def displayPlaylistCommonTitle(self):
        """ Set title for Playlist without LRC or for LRC Frame """
        ''' create_top() shared with create_window() '''
        common_name = "YouTube Playlist: " + self.act_name
        common_name += " - " + str(self.act_count) + " Videos."
        common_name += " - " + tmf.days(self.act_seconds)
        if self.listYouTubeCurrIndex:
            common_name += " - Video № " + str(self.listYouTubeCurrIndex + 1)
        self.top.title(common_name + " - mserve")

    def youSetCloseButton(self):
        """ Set self.close_button tooltip text to:
            "Close Playlist"
            "Close Synchronized Lyrics (LRC)" """
        if self.hasLrcForVideo:
            tt_text = "Close Synchronized Lyrics (LRC)"
        else:
            tt_text = "Close YouTube Playlist"
        self.tt.set_text(self.close_button, tt_text)

    def youTreeClick(self, event):
        """ Popup menu has two different sets of options:

            If self.isSmartPlayYouTube:
                ----
                return (EXPLICIT)

            ELSE NOT self.isSmartPlayYouTube: (IMPLICIT)
            ----
            return (IMPLICIT)

        """
        item = self.you_tree.identify_row(event.y)

        if item is None:
            # self.info.cast("Cannot click on an empty row.")
            return  # Empty row, nothing to do

        menu = tk.Menu(root, tearoff=0)
        menu.post(event.x_root, event.y_root)
        no = str(int(item) + 1)  # file_menu.add  # font=(None, MED_FONT)

        if self.isSmartPlayYouTube:
            # Already smart playing YouTube playlist
            menu.add_command(label="Smart Play Song № " + no, font=g.FONT,
                             command=lambda: self.youSmartPlaySong(item))
            menu.add_command(label="Middle 15 Seconds № " + no, font=g.FONT,
                             command=lambda: self.youSmartPlaySample(item))
            menu.add_command(label="Copy Link № " + no, font=g.FONT,
                             command=lambda: self.youTreeCopyLink(item))
            menu.add_separator()  # "#" replaced with: "№ "
            menu.add_command(label="Copy LRC Search № " + no, font=g.FONT,
                             command=lambda: self.youTreeCopySearchLrc(item))
            menu.add_command(label="Paste LRC № " + no, font=g.FONT,
                             command=lambda: self.youTreePasteLrc(item))
            # TODO: Next two Active only when LRC dictionary exists
            menu.add_command(label="View LRC № " + no, font=g.FONT,
                             command=lambda: self.youTreeViewLrc(item))
            menu.add_command(label="Delete LRC № " + no, font=g.FONT,
                             command=lambda: self.youTreeDeleteLrc(item))
            menu.add_separator()
            menu.add_command(label="Close Smart Playlist", font=g.FONT,
                             command=self.youClosePlayLrc)
            menu.add_command(label="Copy Playlist Link", font=g.FONT,
                             command=lambda: self.youTreeCopyAll())
            menu.add_separator()

            menu.add_command(label="30 Second View Counts", font=g.FONT,
                             command=lambda: self.youViewCountBoost())
            menu.add_command(label="Set Debug Level", font=g.FONT,
                             command=lambda: self.youSetDebug())
            menu.add_command(label="Ignore click", font=g.FONT,
                             command=lambda: self.youClosePopup(menu, item))

            menu.tk_popup(event.x_root, event.y_root)
            menu.bind("<FocusOut>", lambda _: self.youClosePopup(menu, item))
            return

        global XDOTOOL_INSTALLED, WMCTRL_INSTALLED
        XDOTOOL_INSTALLED = ext.check_command('xdotool')
        WMCTRL_INSTALLED = ext.check_command('wmctrl')

        if XDOTOOL_INSTALLED and WMCTRL_INSTALLED:
            menu.add_command(label="Smart Play All", font=g.FONT,
                             command=lambda: self.youSmartPlayAll())
            menu.add_separator()

        menu.add_command(label="Copy Playlist Link", font=g.FONT,
                         command=lambda: self.youTreeCopyAll())

        # TODO: Check selenium version installed:
        #   https://stackoverflow.com/a/76915412/6929343
        #       ~/.cache/selenium

        menu.add_separator()

        # menu.add_command(label="Play Song № " + no, font=g.FONT,
        #                 command=lambda: self.you_tree_play(item))

        # TODO: Check Selenium Installed
        #       Check ChromeDriver installed & matches version
        #       Check Firefox Driver installed

        # if XDOTOOL_INSTALLED and WMCTRL_INSTALLED:
        #    menu.add_command(label="Smart Play № " + no, font=g.FONT,
        #                     command=lambda: self.you_tree_smart_play(item))

        menu.add_command(label="Copy Link № " + no, font=g.FONT,
                         command=lambda: self.youTreeCopyLink(item))
        menu.add_separator()

        menu.add_command(label="Copy LRC Search № " + no, font=g.FONT,
                         command=lambda: self.youTreeCopySearchLrc(item))
        menu.add_command(label="Paste LRC № " + no, font=g.FONT,
                         command=lambda: self.youTreePasteLrc(item))
        # TODO: Next two appear only when LRC dictionary exists
        menu.add_command(label="View LRC № " + no, font=g.FONT,
                         command=lambda: self.youTreeViewLrc(item))
        menu.add_command(label="Delete LRC № " + no, font=g.FONT,
                         command=lambda: self.youTreeDeleteLrc(item))
        menu.add_separator()

        menu.add_command(label="Set Debug Level", font=g.FONT,
                         command=lambda: self.youSetDebug())
        menu.add_command(label="Ignore click", font=g.FONT,
                         command=lambda: self.youClosePopup(menu, item))

        menu.tk_popup(event.x_root, event.y_root)
        menu.bind("<FocusOut>", lambda _: self.youClosePopup(menu, item))
        # '_' prevents: TypeError: <lambda>() takes no arguments (1 given)

    @staticmethod
    def youClosePopup(menu, _item):
        """ Close the YouTube Playlist popup menu """
        menu.unpost()  # Remove popup menu

    def youClosePlayLrc(self, *_args):
        """ Close YouTube Playlist or Lrc Frame depending on active frame. """

        # Is Lrc Frame active?
        if self.hasLrcForVideo:
            self.youLrcFrame.grid_remove()  # Remove LRC frame
            self.tree_frame.grid()  # Restore Treeview frame
            self.hasLrcForVideo = None
            self.youSetCloseButton()
            return

        # Normal close window and destroy top
        if self.webDriver:
            self.webDriver.quit()
        self.reset()

    def you_tree_play(self, item):
        """ Play song highlighted in YouTube treeview.
            2023-12-02 - Not called by popup menu.
        """
        title = "NOT IMPLEMENTED."
        text = "Calling YouTube regular play"
        message.ShowInfo(self.top, title, text, icon='warning',
                         thread=self.get_thread)
        ndx = int(item)
        webbrowser.open_new(self.listYouTube[ndx]['link'])

    def you_tree_smart_play(self):
        """ Smart Play single YouTube song for unopened Playlist.
            2023-12-02 - Not called by popup menu.
        """
        title = "NOT IMPLEMENTED."
        text = "Calling YouTube regular play"
        message.ShowInfo(self.top, title, text, icon='warning',
                         thread=self.get_thread)
        ndx = int(item)
        webbrowser.open_new(self.listYouTube[ndx]['link'])

    # noinspection SpellCheckingInspection
    def you_tree_play_all(self, item):
        """ Play all songs in treeview (Entire YouTube Playlist).
            NOT TESTED YET (October 16, 2023)
        """

        _title = "WARNING: Experimental feature"
        _text = "Currently this features moves YouTube from right to left monitor."
        # message.ShowInfo(self.top, _title, _text, icon='warning',
        #                 thread=self.get_thread)
        mon = monitor.Monitors()  # Monitors class list of dicts
        # Start windows
        start_wins = mon.get_all_windows()

        ndx = int(item)
        webbrowser.open_new(self.listYouTube[ndx]['link'])
        time.sleep(1.0)  # TODO: Loop for 30 seconds until list changes
        end_wins = mon.get_all_windows()

        if not len(start_wins) + 1 == len(end_wins):
            print("Could not find new window")
            print("start/end window count:", len(start_wins), len(end_wins))
            return

        win_list = list(set(end_wins) - set(start_wins))
        window = win_list[0]
        # print("\n window list:", window)
        # [Window(number=130028740L, name='Mozilla Firefox', x=1920, y=24,
        #         width=1728, height=978)]

        str_win = str(window.number)  # should remove L in python 2.7.5+
        int_win = int(str_win)  # https://stackoverflow.com/questions
        hex_win = hex(int_win)  # /5917203/python-trailing-l-problem

        # If last usage was full screen, reverse it
        net_states = os.popen('xprop -id ' + str_win).read().strip()
        # print("net_states:", net_states)
        if "_NET_WM_STATE_FULLSCREEN" in net_states:
            os.popen('wmctrl -ir ' + hex_win +
                     ' -b toggle,fullscreen')  # DOES NOT WORK !!!
        # Remove maximized, don't have to test first
        os.popen('wmctrl -ir ' + hex_win +
                 ' -b remove,maximized_vert,maximized_horz')
        # os.popen('wmctrl - r: ACTIVE: -e 0, 300, 168, 740, 470')

        new_x = new_y = 30  # Move to top left monitor @ 30,30 (x, y)
        os.popen('xdotool windowmove ' + hex_win + ' ' +
                 str(new_x) + ' ' + str(new_y))
        # time.sleep(0.5)  # After window move, need a little time
        # message.ShowInfo(self.top, title, text, icon='warning',
        #                 thread=self.get_thread)

        # Could remove target window's above setting (Always On Top):
        #   os.popen('wmctrl -ir ' + trg_win + ' -b toggle,above')

        # Make full screen. Have to reverse before closing because setting
        # remembered by firefox for next window open

        os.popen('wmctrl -ir ' + hex_win + ' -b add,maximized_vert')
        os.popen('wmctrl -ir ' + hex_win + ' -b add,maximized_horz')
        # Making above removes system title bar
        os.popen('wmctrl -ir ' + hex_win + ' -b add,above')
        # Move to screen center and click to play
        # os.popen('xdotool mousemove 1860 900')  # 1920/2 x 1080/2
        time.sleep(7.0)  # Time for YouTube to load up and build page
        # os.popen('xdotool click --window ' + hex_win + ' --delay 5000 1')
        os.popen('xdotool key f')  # Full Screen
        os.popen('xdotool key space')  # Start playing

        # Selenium to watch for skip ad button to appear and click it
        # sudo apt install python-selenium

        web = webbrowser.get()
        print("browser name:", web.name)
        if web.name.startswith("xdg-open"):
            xdg_browser = os.popen("xdg-settings get default-web-browser"). \
                read().strip()
            if "FIREFOX" in xdg_browser.upper():
                self.webDriver = webdriver.Firefox()
                print("driver = webdriver.Firefox()")
            if "CHROME" in xdg_browser.upper():
                self.webDriver = webdriver.Chrome()
                print("driver = webdriver.Chrome()")

    # Playlists Class YouTube Video Player

    def youSmartPlaySong(self, item):
        """
        Build: https://www.youtube.com/watch
            ?v=0n3cUPTKnl0
            &list=PLthF248A1c68TAKl5DB skfJ2fwr1sk9aM
            &index=17

        :param item: item (iid) in YouTube playlist
        :return: None
        """

        # Shared function to start playing at playlist index
        self.youPlaylistIndexStartPlay(item)

    def youSmartPlaySample(self, item):
        """ Start playing video then advance to middle of song
        :param item: item (iid) in YouTube playlist
        :return: None
        """

        self.youPlaylistIndexStartPlay(item)
        # Advance to middle of song
        duration_str = self.dictYouTube['duration']
        duration = int(tmf.get_sec(duration_str))
        mid_start = (duration / 2) - 8
        if mid_start > 0:
            self.webDriver.execute_script(
                'document.getElementsByTagName("video")[0].currentTime += ' +
                str(mid_start) + ';')

    # noinspection SpellCheckingInspection
    def youPlaylistIndexStartPlay(self, item, restart=False):
        """ Shared by youSmartPlaySong and youSmartPlaySample methods

            Build full_link containing:
                https://www.youtube.com/watch
                ?v=0n3cUPTKnl0
                &list=PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM
                &index=17

            self.act_description =
                https://www.youtube.com/
                playlist?list=PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM

        :param item: item (iid) in YouTube playlist
        :param restart: End of Playlist, restart from beginning.
        :return: None
        """

        # Is last video playing in full screen?
        self.youForceVideoFull = self.youCheckVideoFullScreen()

        ndx = int(item)
        self.dictYouTube = self.listYouTube[ndx]
        link = self.dictYouTube['link']
        youPlaylistName = self.act_description.split("list=")[1]
        full_link = link + "&list=" + youPlaylistName
        full_link += "&index=" + item

        self.webDriver.get(full_link)
        status = self.youWaitMusicPlayer(startup=True)
        while status == 99 or self.youCheckAdRunning():
            self.youVolumeOverride(True)  # Ad playing override
            self.webDriver.back()
            self.webDriver.forward()
            status = self.youWaitMusicPlayer(startup=True)

        if restart:
            self.youPrint("Forced refresh at beginning:", full_link)
            # EXPECT:&list=PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM
            # SHOWN: &list=PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM
            # 01:20:38.8 STARTING Playlist - Song № 1     | a-Xfv64uhMI
            # https://www.youtube.com/watch?v=a-Xfv64uhMI&list=PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM&index=1
            # 01:20:38.0 STARTING Playlist - Song № 1     | nYSdFra_Amc
            # 01:24:59.6 STARTING Playlist - Song № 1     | kuoZTxfe6tA
            time.sleep(2.0)
            self.webDriver.refresh()

    def youSmartPlayAll(self):
        """ Smart Play entire YouTube Playlist.

            1. youOpenSelenium() Get browser (web) and Open browser (self.webDriver)
            2. Open YouTube Playlist, Move window, 'Play all', full screen
            3. Loop forever playing all songs - self.youMonitorLinks()
            4. self.youMonitorPlayerStatus() Update progress and skip Ads

        TODO:
            Resume from suspend after day at work results in 443 ads. Set limit
                of 3 ads then interrupt and self.webDriver.get(video)

        """

        ''' 1. youOpenSelenium() Get browser (web) and Open browser (self.webDriver) '''
        self.webDriver, window = self.youOpenSelenium()
        if not window:
            if self.webDriver:
                self.webDriver.quit()
            return  # No window tuple, cannot proceed even if self.webDriver succeeded

        ''' 2. Open YouTube Playlist, Move window, 'Play all', full screen '''
        if not self.youPlayAllFullScreen(window):
            print("youPlayAllFullScreen(window) Failed!")
            self.webDriver.quit()
            return

        self.youLastLink = ""  # When link changes highlight row in self.you_tree
        last_player_status = None

        self.durationYouTube = 0.0  # Extra insurance
        self.resetYouTubeDuration()
        self.buildYouTubeDuration()
        self.isSmartPlayYouTube = True  # Smart Play is active
        self.youDebug = self.act_size  # Print Debug level from last save

        ad_conflict_count = 0  # Player status -1 but No Ad visible (yet).
        lastHousekeepingTime = time.time()  # Check resume every minute

        ''' 3. Loop forever playing all songs - self.youMonitorLinks() '''
        while True:
            if not self.top:
                return False  # Closing down

            # play top refresh + .after(16). With this, CPU load is 3.5% not 6%
            if not lcs.fast_refresh(tk_after=True):
                if self.webDriver:
                    self.webDriver.quit()
                self.isSmartPlayYouTube = False
                self.webDriver = None
                return False

            ''' Housekeeping every minute 
                Respond to prompt: "Video paused. Continue Watching?" '''
            now = time.time()
            if now - lastHousekeepingTime > 60.0:
                lastHousekeepingTime = now
                self.youHousekeeping()

            ''' Check if Browser Address Bar URL link has changed. '''
            link = self.youMonitorLinks()
            if link is None:
                continue  # Error getting link

            # Get YouTube Music Player Status
            player_status = self.youGetPlayerStatus()
            if player_status is None:
                player_status = last_player_status  # Use last know state
                self.youPrint("player_status is <Type> 'None'!",
                              "Resorting to last status:", player_status)

            ''' 4. self.youMonitorPlayerStatus() Update progress and skip Ads '''
            self.youMonitorPlayerStatus(player_status, debug=False)

            self.youLastLink = link
            last_player_status = player_status

            # Continue beyond this point when YouTube Ad is running
            # self.webDriver.find_element(By.CSS_SELECTOR, ".ytp-ad-duration-remaining")
            if not self.youCheckAdRunning():
                if player_status == -1:
                    ad_conflict_count += 1
                continue  # Skip while loop below

            if ad_conflict_count > 0:
                self.youPrint("player_status == '-1' but no Ad running. Count:",
                              ad_conflict_count)
                ad_conflict_count = 0  # Reset for next group count

    def youOpenSelenium(self):
        """ Create Selenium browser instance
            Create Selenium self.webDriver instance
            Get Window ID for self.webDriver instance

        :return self.webDriver, window: Selenium self.webDriver and WM window tuple
        """

        self.webDriver = self.webWinGeom = None
        useChrome = useChromium = _useFirefox = False
        CHROME_DRIVER_VER = "chromedriver108"  # 108 replaced with actual version
        ver = os.popen("google-chrome --version").read().strip()
        ver = ver.split()
        try:
            ver = ver[2].split(".")[0]
            # _ver_int = int(ver)
            useChrome = True
        except IndexError:
            ver = os.popen("chromium --version").read().strip()
            ver = ver.split()
            ver = ver[1].split(".")[0]
            useChromium = True
        CHROME_DRIVER_VER = CHROME_DRIVER_VER.replace("108", ver)
        CHROME_DRIVER_PATH = \
            g.PROGRAM_DIR + os.sep + CHROME_DRIVER_VER + os.sep + "chromedriver"
        self.youPrint("CHROME_DRIVER_PATH:", CHROME_DRIVER_PATH, nl=True)

        web = webbrowser.get()
        # print("browser name:", web.name)  # xdg-open
        try:
            mon = monitor.Monitors()  # Monitors class list of dicts
            # Start windows
            end_wins = start_wins = mon.get_all_windows()
        except Exception as err:
            self.youPrint("youOpenSelenium() Exception:", err)
            return self.webDriver, window

        if web.name.startswith("xdg-open"):
            xdg_browser = os.popen("xdg-settings get default-web-browser"). \
                read().strip()
            if "FIREFOX" in xdg_browser.upper():
                """
                selenium has been replaced by marionette:

                https://firefox-source-docs.mozilla.org/python/marionette_driver.html

                For ubuntu:

                https://stackoverflow.com/a/39536091/6929343
                https://stackoverflow.com/questions/43272919/difference-between-webdriver-firefox-marionette-webdriver-gecko-driver
                https://stackoverflow.com/questions/38916650/what-are-the-benefits-of-using-marionette-firefoxdriver-instead-of-the-old-selen/38917100#38917100

                """
                if useChrome:
                    self.webDriver = webdriver.Chrome(CHROME_DRIVER_PATH)
                    # Automated Test Software message suppression (Doesn't work)
                    # https://stackoverflow.com/a/71257995/6929343
                    chromeOptions = webdriver.ChromeOptions()
                    chromeOptions.add_experimental_option("excludeSwitches", ['enable-automation'])
                elif useChromium:
                    print("Using Chromium Branch 1")
                    # self.webDriver = webdriver.Chrome(CHROME_DRIVER_PATH)
                    # executable_path = "/usr/bin/chromedriver
                    # self.webDriver = webdriver.chromium.Chrome(CHROME_DRIVER_PATH)
                    # Optional argument, if not specified will search path.
                    self.webDriver = webdriver.Chrome()  # It will search path

                """
                    Maintainer: https://chromedriver.chromium.org/home
                    WebDriverException: Message: 'chromedriver' executable 
                    needs to be in PATH. Please see 
                    https://sites.google.com/a/chromium.org/chromedriver/home
                    New download links:
                    https://sites.google.com/chromium.org/driver/downloads?authuser=0

                    For chrome > 115: https://googlechromelabs.github.io/chrome-for-testing/
                    E.G. version 120: https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/
                                      120.0.6099.109/linux64/chromedriver-linux64.zip

                    To use Chromium instead of Chrome use:
                    sudo apt install chromium-chromedriver
                    Credit: https://stackoverflow.com/a/75241037/6929343
                """
            if "CHROME" in xdg_browser.upper():
                if useChrome:
                    self.webDriver = webdriver.Chrome(CHROME_DRIVER_PATH)
                    # Automated Test Software message suppression (Doesn't work)
                    # https://stackoverflow.com/a/71257995/6929343
                    chromeOptions = webdriver.ChromeOptions()
                    chromeOptions.add_experimental_option("excludeSwitches", ['enable-automation'])
                elif useChromium:
                    print("Using Chromium Branch 2")
                    self.webDriver = webdriver.Chrome()  # It will search path

        start = time.time()
        while len(end_wins) == len(start_wins):
            end_wins = mon.get_all_windows()
            if time.time() - start > 5.0:
                title = "Could not start Browser"
                text = "Browser would not start.\n"
                text += "Check console for error\n"
                text += "messages and try again."
                message.ShowInfo(self.top, title, text, icon='error',
                                 thread=self.get_thread)
                return self.webDriver, self.webWinGeom

        if not len(start_wins) + 1 == len(end_wins):
            title = "Could not start Browser"
            text = "Old Window count: " + str(len(start_wins)) + "\n\n"
            text += "New Window count: " + str(len(end_wins)) + "\n\n"
            text += "There should only be one new window.\n"
            text += "Check console for error messages.\n"
            message.ShowInfo(self.top, title, text, icon='error',
                             thread=self.get_thread)
            return self.webDriver, self.webWinGeom

        win_list = list(set(end_wins) - set(start_wins))
        self.webWinGeom = win_list[0]

        return self.webDriver, self.webWinGeom

    # noinspection SpellCheckingInspection
    def youPlayAllFullScreen(self, window):
        """ Open YouTube Playlist, Move window, 'Play all', full screen
            self.act_description =
                https://www.youtube.com/
                playlist?list=PLthF248A1c68TAKl5DB skfJ2fwr1sk9aM
        """

        self.webDriver.get(self.act_description)  # Open Youtube playlist
        # print("self.act_description   :", self.act_description)
        # print("self.webDriver.current_url:", self.webDriver.current_url)

        if self.act_description != self.webDriver.current_url:
            print("youPlayAllFullScreen(window) - Open YouTube Playlist Failed!")
            return False

        # print("\n window list:", window)
        # [Window(number=130028740L, name='Mozilla Firefox', x=1920, y=24,
        #         width=1728, height=978)]

        str_win = str(window.number)  # should remove L in python 2.7.5+
        int_win = int(str_win)  # https://stackoverflow.com/questions
        hex_win = hex(int_win)  # /5917203/python-trailing-l-problem
        # print("\n str_win:", str_win, "int_win:", int_win, "hex_win:", hex_win)

        # If last usage was full screen, reverse it
        net_states = os.popen('xprop -id ' + str_win).read().strip()
        # print("net_states:", net_states)
        if "_NET_WM_STATE_FULLSCREEN" in net_states:
            self.youFullScreen = True  # Was YouTube full screen before?
            os.popen('wmctrl -ir ' + hex_win +
                     ' -b toggle,fullscreen')  # DOES NOT WORK !!!

        # Remove maximized, don't worry if not maximized already
        os.popen('wmctrl -ir ' + hex_win +
                 ' -b remove,maximized_vert,maximized_horz')

        new_x = new_y = 30  # Move to top left monitor @ 30,30 (x, y)
        os.popen('xdotool windowmove ' + hex_win + ' ' +
                 str(new_x) + ' ' + str(new_y))

        # Could remove target window's above setting (Always On Top):
        #   os.popen('wmctrl -ir ' + trg_win + ' -b toggle,above')

        self.webDriver.maximize_window()
        # Making "Above" removes system title bar
        os.popen('wmctrl -ir ' + hex_win + ' -b add,above')

        # Automated Test Software message suppression (Doesn't work)
        # https://stackoverflow.com/a/71257995/6929343
        # Manually position mouse over "Automated Test Software" message
        os.popen('xdotool mousemove 1890 140')  # Assume top-left monitor Full HD
        # Send left click (1) after 50ms delay
        os.popen('xdotool click --window ' + hex_win + ' --delay 50 1')
        # os.popen('xdotool windowactivate ' + hex_win)  # Verify activate needed
        # os.popen('xdotool click 1')

        byline = self.webDriver.find_element(By.CLASS_NAME, 'byline-item')
        """ byline-item has video count in YouTube Playlist
            <span dir="auto" class="style-scope yt-formatted-string">47</span>
            <span dir="auto" class="style-scope yt-formatted-string"> videos</span>
            XPATH:
            /html/body/ytd-app/div[1]/ytd-page-manager/ytd-browse[2]/
                ytd-playlist-header-renderer/div/div[2]/div[1]/div/div[1]/div[1]/
                ytd-playlist-byline-renderer/div/yt-formatted-string[1] """
        video_count = byline.get_attribute('innerHTML').split("</span>")[0]
        video_count = video_count.split(">")[1]

        self.youPrint("youPlayAllFullScreen() video_count:", video_count,
                      lv=8, nl=True)

        fname2 = self.nameYouTube.replace(".csv", ".private")
        self.privateYouTube = ext.read_into_string(fname2)
        if self.privateYouTube:  # Saved count of private videos in playlist
            private_links = int(self.privateYouTube)
        else:
            private_links = 0

        if int(video_count) - private_links != len(self.listYouTube):
            title = "YouTube Playlist Needs Updating"
            text = "mserve copy of YouTube Playlist is out-of-date.\n\n"
            text += "YouTube Playlist count: " + video_count + "\n\n"
            text += "mserve Playlist count:  " + str(len(self.listYouTube))
            message.ShowInfo(self.top, title, text, icon='warning',
                             thread=self.get_thread)
            start = time.time()  # Track elapsed time

            self.youShowUnavailableVideos()  # When hamburger menu exists

            self.youValidLinks, private_links, listVideos = \
                self.youGetAllGoodLinks(video_count)

            good_times, listTimes = self.youGetAllGoodTimes(self.youValidLinks)

            # Join two lists in same format as self.listYouTube
            for i, video in enumerate(listVideos):
                listVideos[i] = listVideos[i] + ';' + listTimes[i]

            # print("listVideos[0]:", listVideos[0],
            #      "listVideos[-1]:", listVideos[-1])

            self.mergeYouTubePlaylist(listVideos, private_links)
            self.displayYouTubePlaylist()  # Recreate Treeview see Song #19 added
            self.youShowUnavailableVideos(show=False)  # When hamburger menu exists
            self.youPrint("elapsed time:", time.time() - start)

        # Find and click to "Play all" button
        if not self.youDriverClick('link_text', "Play all"):
            # TODO: Fails when buried behind Firefox running full screen
            self.youPrint("Play all button click FAILED!")
            os.popen('xdotool mousemove 500 790')
            # Send left click (1) after 3 second delay
            time.sleep(3.0)  # Wait 3 seconds
            os.popen('xdotool click --window ' + hex_win + ' 1')
            # os.popen('xdotool windowactivate ' + hex_win)  # Verify activate needed
            # os.popen('xdotool click 1')  # Click on play all button

        # Skip commercial with driver.back() then driver.forward()
        status = self.youWaitMusicPlayer(startup=True)
        while status == 99 or self.youCheckAdRunning():
            self.youVolumeOverride(True)  # Ad playing override
            self.webDriver.back()
            self.webDriver.forward()
            # Get player status without debug which can spam console
            status = self.youWaitMusicPlayer(startup=True)

        player_status = self.youGetPlayerStatus()
        if not player_status:
            self.webDriver.quit()
            title = "Smart Play FAILED"
            text = "Play All did not work. Try again later.\n\n"
            text += "Check console for messages."
            message.ShowInfo(self.top, title, text, icon='error',
                             thread=self.get_thread)
            return False

        ''' Make YouTube full screen '''
        actions = ActionChains(self.webDriver)
        actions.send_keys('f')  # work around self.webDriver.fullscreen_window()
        actions.perform()
        # self.webDriver.fullscreen_window()  # Doesn't work
        # driver.fullscreen_window()
        #   File "/home/rick/python/mserve.py", line 15834, in youSmartPlayAll
        #     self.webDriver.fullscreen_window()
        # AttributeError: 'WebDriver' object has no attribute 'fullscreen_window'

        return True

    # noinspection SpellCheckingInspection
    def youCheckVideoFullScreen(self):
        """ Check if YouTube Browser Window is currently full screen
            Use new self.webWinGeom variable. Called during startup and
            when video link changes (new video started)

            There is Full Screen in Desktop Manager (DM):

                _NET_WM_STATE(ATOM) =
                    _NET_WM_STATE_MAXIMIZED_VERT,
                    _NET_WM_STATE_MAXIMIZED_HORZ,
                    _NET_WM_STATE_FULLSCREEN,
                    _NET_WM_STATE_ABOVE

            DM not full screen:

                _NET_WM_STATE(ATOM) =

            To check if Video taking all of window in YouTube:

                full_screen = True
                try:
                    path = '//input[@id="search"]'
                    search_area = self.webDriver.find_element(By.XPATH, path)
                    full_screen = search_area.is_displayed()
                except:
                    print("Bad element path or too soon:", path)

        """
        # print("\n Browser Window:", self.webWinGeom)
        # [Window(number=130028740L, name='Mozilla Firefox', x=1920, y=24,
        #         width=1728, height=978)]

        str_win = str(self.webWinGeom.number)  # Remove L in python 2.7.5+
        int_win = int(str_win)  # https://stackoverflow.com/questions
        _hex_win = hex(int_win)  # /5917203/python-trailing-l-problem
        # print("\n str_win:", str_win, "int_win:", int_win, "hex_win:", hex_win)

        # If last usage was full screen, reverse it
        net_states = os.popen('xprop -id ' + str_win).read().strip()
        # print("net_states:", net_states)
        path = None
        self.youFullScreen = None  # Was YouTube full screen before?
        if "_NET_WM_STATE_FULLSCREEN" in net_states:
            self.youFullScreen = True  # YouTube is full screen

        self.youPrint("Full screen state:", self.youFullScreen)
        # self.youPrint("str_win:", str_win, "net_states:", net_states)
        self.youPrint("Window:", self.webWinGeom)

        self.youForceVideoFull = False
        if not self.youFullScreen:
            self.youPrint("self.youForceVideoFull:", self.youForceVideoFull)
            return self.youForceVideoFull

        try:
            # https://stackoverflow.com/a/72820435/6929343
            path = '//input[@id="search"]'
            search_area = self.webDriver.find_element(By.XPATH, path)
            self.youForceVideoFull = search_area.is_displayed() is not True
            self.youPrint("self.youForceVideoFull:", self.youForceVideoFull)
        except Exception as err:
            self.youPrint("youCheckVideoFullScreen() Exception:", err)
            print("Bad XPATH name or need to wait:", path)

        return self.youForceVideoFull

    # noinspection SpellCheckingInspection
    def youGetAllGoodLinks(self, video_count):
        """ Get all the good links and private links in playlist. Scrolling
            is necessary after 100 video chunks.
            TODO: 2024-01-28 - Build Chill playlist video #90 should be hidden
                but it appears in mserve. Then video counts are out of sync.
                https://www.youtube.com/watch?v=562VuMrFUys
        :return: good_links, private_links, listVideos
        """

        self.gotAllGoodLinks = None
        good_links, private_links, listVideos = self.youGetBatchGoodLinks()

        # last_good_links is stop-gap measure until show hidden videos
        # button is clicked on player hamburger menu.
        last_good_links = good_links
        # When more than 100 videos, need to scroll
        while good_links < int(video_count) - private_links:
            # HTML By.ID Looping forever when 242 < 243
            try:
                # Need wait until visible when playing random song
                wait = WebDriverWait(self.webDriver, GLO['YTV_DRIVER_WAIT'])
                id_name = 'items'  # _located
                # element = self.webDriver.find_element_by_id(id_name)
                item_list = wait.until(EC.presence_of_element_located((
                    By.ID, id_name)))

                # print("item_list:", item_list)
                _dictItem = self.webDriver.execute_script(
                    'var items = {}; \
                    for (index = 0; index < \
                    arguments[0].attributes.length; ++index) \
                    { items[arguments[0].attributes[index].name] = \
                    arguments[0].attributes[index].value }; \
                    return items;',
                    item_list)
                # print("dictItem:", dictItem)
                # dictItem: {u'class': u'playlist-items style-scope
                #           ytd-playlist-panel-renderer', u'id': u'items'}

                ActionChains(self.webDriver).move_to_element(item_list)
                # self.webDriver.send_keys(Keys.END) fails
                actions = ActionChains(self.webDriver)
                actions.send_keys(Keys.END)
                actions.perform()
                time.sleep(1.5)  # Oct 8/23: Verified necessary!
                good_links, private_links, listVideos = self.youGetBatchGoodLinks()
                if good_links == last_good_links:
                    # Oct 8/23 - Message no longer appears for private videos
                    title = "Unavailable Videos"
                    text = "YouTube reporting more videos than scrollable.\n"
                    text += 'Check for deleted videos and change this code.'
                    message.ShowInfo(self.top, title, text, icon='error',
                                     thread=self.get_thread)
                    break
                last_good_links = good_links
            except WebDriverException as err:
                title = "Selenium WebDriverException"
                text = str(err)
                message.ShowInfo(self.top, title, text, icon='error',
                                 thread=self.get_thread)
                self.youPrint("id_name = 'items' WebDriverException:\n", err)
                break
                # return None

        self.gotAllGoodLinks = True
        return good_links, private_links, listVideos

    # noinspection SpellCheckingInspection
    def youGetBatchGoodLinks(self):
        """
            TODO: Devine item number to click on.
                  Note unavailable video setting.
                  Note stale element errors and video skipped.
            TODO: 2024-01-28 - Build Chill playlist video #90 should be hidden
                but it appears in mserve. Then video counts are out of sync.
                https://www.youtube.com/watch?v=562VuMrFUys
            :return: good_links, private_links, listVideos
        """

        listVideos = []
        good_links = private_links = bad_links = 0
        links = self.webDriver.execute_script(
            "return document.querySelectorAll('a')")

        # ERROR:
        # CHROME_DRIVER_PATH: /home/rick/python/chromedriver108/chromedriver
        #
        # 07:11:59.3 youWaitMusicPlayer 930.478 ms | Null: 0  | Paused: 0  | Starting: 5  | Idle: 5
        #
        # 07:12:00.1 STARTING Playlist - Song № 1     | a-Xfv64uhMI
        #
        # 07:16:08.3 STARTING Playlist - Song № 2     | HnilTXUQtag
        # 07:16:08.7 Ad visible. Player status: 5
        # 07:16:10.8 MicroFormat found after: 0.4     | HnilTXUQtag
        # CHROME_DRIVER_PATH: /home/rick/python/chromedriver108/chromedriver
        # 07:17:23.8 Clicking xpath: //*[@id="page-manager"]/ytd-browse/
        #   ytd-playlist-header-renderer/div/div[2]/div[1]/div/div[1]/div[2]/ytd-menu-renderer
        # 07:17:24.4 Clicking 'Show unavailable videos': Show unavailable videos
        # Exception in Tkinter callback
        # Traceback (most recent call last):
        #   File "/usr/lib/python2.7/lib-tk/Tkinter.py", line 1540, in __call__
        #     return self.func(*args)
        #   File "/home/rick/python/mserve.py", line 15698, in <lambda>
        #     command=lambda: self.youSmartPlayAll())
        #   File "/home/rick/python/mserve.py", line 15925, in youSmartPlayAll
        #     if not self.youPlayAllFullScreen(window):
        #   File "/home/rick/python/mserve.py", line 16172, in youPlayAllFullScreen
        #     self.youGetAllGoodLinks(video_count)
        #   File "/home/rick/python/mserve.py", line 16237, in youGetAllGoodLinks
        #     good_links, private_links, listVideos = self.youGetBatchGoodLinks()
        #   File "/home/rick/python/mserve.py", line 16311, in youGetBatchGoodLinks
        #     link)
        #   File "/usr/lib/python2.7/dist-packages/selenium/webdriver/remote/webdriver.py", line 429, in execute_script
        #     {'script': script, 'args':converted_args})['value']
        #   File "/usr/lib/python2.7/dist-packages/selenium/webdriver/remote/webdriver.py", line 201, in execute
        #     self.error_handler.check_response(response)
        #   File "/usr/lib/python2.7/dist-packages/selenium/webdriver/remote/
        #       errorhandler.py", line 181, in check_response
        #     raise exception_class(message, screen, stacktrace)
        # StaleElementReferenceException: Message: stale element reference: element is not attached to the page document
        #   (Session info: chrome=108.0.5359.124)
        #   (Driver info: chromedriver=108.0.5359.71 (1e0e3868ee06e91ad636a874420e3ca3ae3756ac-refs/
        #       branch-heads/5359@{#1016}),platform=Linux 4.14.216-0414216-generic x86_64)
        for link in links:
            # StaleElementReferenceException:
            #   https://stackoverflow.com/a/40070927/6929343
            #       wait.until(ExpectedConditions.stalenessOf(whatever element));
            try:
                dictLink = self.webDriver.execute_script(
                    'var items = {}; \
                    for (index = 0; index < \
                    arguments[0].attributes.length; ++index) \
                    { items[arguments[0].attributes[index].name] = \
                    arguments[0].attributes[index].value }; \
                    return items;',
                    link)
            except StaleElementReferenceException:
                print("Stale element")
                continue

            link_url = dictLink.get('href', None)
            link_title = dictLink.get('title', None)
            class_list = dictLink.get('class', None)

            if u'[Private video]' == link_title:
                # Link # 119 is private video, get keys
                self.youPrint("link_url  :", link_url)
                self.youPrint("link_title:", link_title)
                self.youPrint("class_list:", class_list)
                private_links += 1
                continue
                # print("\ndictLink:", dictLink)

            if u'[Deleted video]' == link_title:
                # Link # 6 is deleted video, get keys
                self.youPrint("link_url  :", link_url)
                self.youPrint("link_title:", link_title)
                self.youPrint("class_list:", class_list)
                private_links += 1
                continue
                # print("\ndictLink:", dictLink)

            if not link_url or not link_title or not class_list or \
                    "style-scope ytd-playlist-video-renderer" \
                    not in class_list or len(link_title) < 1:
                bad_links += 1
                continue

            good_links += 1
            part = link_url.split("&list=")[0]
            listVideos.append(link_title + ";https://www.youtube.com" + part)

        self.youPrint("good_links:", good_links, "bad_links:", bad_links)

        return good_links, private_links, listVideos

    # noinspection SpellCheckingInspection
    def youShowUnavailableVideos(self, show=True):
        """

        WHEN MENU BUTTON APPEARS:

document.querySelector("#page-manager > ytd-browse > ytd-playlist-header-renderer
> div > div.immersive-header-content.style-scope.ytd-playlist-header-renderer
> div.thumbnail-and-metadata-wrapper.style-scope.ytd-playlist-header-renderer
> div > div.metadata-action-bar.style-scope.ytd-playlist-header-renderer
> div.metadata-buttons-wrapper.style-scope.ytd-playlist-header-renderer
> ytd-menu-renderer")

        WHEN MENU BUTTON APPEARS:

//*[@id="page-manager"]/ytd-browse/ytd-playlist-header-renderer/div/div[2]/div[1]/div/div[1]/div[2]/ytd-menu-renderer

        <ytd-menu-renderer force-icon-button="" tonal-override=""
        class="style-scope ytd-playlist-header-renderer"
        safe-area=""><!--css-build:shady--><!--css-build:shady-->
        <div id="top-level-buttons-computed"
        class="top-level-buttons style-scope ytd-menu-renderer"></div>
        <div id="flexible-item-buttons"
        class="style-scope ytd-menu-renderer"></div>
        <yt-icon-button id="button"
        class="dropdown-trigger style-scope ytd-menu-renderer"
        style-target="button" hidden="">
        <!--css-build:shady--><!--css-build:shady-->
        <button id="button" class="style-scope yt-icon-button"
        aria-label="Action menu"><yt-icon class="style-scope ytd-menu-renderer">
        <!--css-build:shady--><!--css-build:shady-->
        <yt-icon-shape class="style-scope yt-icon"><icon-shape
        class="yt-spec-icon-shape"><
        div style="width: 100%; height: 100%; fill: currentcolor;">
        <svg enable-background="new 0 0 24 24" height="24"
        viewBox="0 0 24 24" width="24" focusable="false"
        style="pointer-events: none; display: block; width: 100%; height: 100%;">
        <path d="M12 16.5c.83 .... 1.5-1.5-.67-1.5-1.5-1.5-1.5.67-1.5 1.5z">
        </path></svg></div></icon-shape></yt-icon-shape></yt-icon></button>
        <yt-interaction id="interaction" class="circular style-scope yt-icon-button">
        <!--css-build:shady--><!--css-build:shady-->
        <div class="stroke style-scope yt-interaction"></div>
        <div class="fill style-scope yt-interaction"></div>
        </yt-interaction></yt-icon-button><yt-button-shape id="button-shape"
        version="modern" class="style-scope ytd-menu-renderer">
        <button class="yt-spec-button-shape-next
        yt-spec-button-shape-next--tonal yt-spec-button-shape-next--overlay
        yt-spec-button-shape-next--size-m yt-spec-button-shape-next--icon-button "
        aria-label="Action menu" title="" style="">
        <div class="yt-spec-button-shape-next__icon" aria-hidden="true">
        <yt-icon style="width: 24px; height: 24px;">
        <!--css-build:shady--><!--css-build:shady-->
        <yt-icon-shape class="style-scope yt-icon">
        <icon-shape class="yt-spec-icon-shape">
        <div style="width: 100%; height: 100%; fill: currentcolor;">
        <svg enable-background="new 0 0 24 24" height="24" viewBox="0 0 24 24"
        width="24" focusable="false" style="pointer-events: none;
        display: block; width: 100%; height: 100%;">
        <path d="M12 16.5c.83 ...  1.5-1.5-.67-1.5-1.5-1.5-1.5.67-1.5 1.5z"></path>
        </svg></div></icon-shape></yt-icon-shape></yt-icon></div>
        <yt-touch-feedback-shape style="border-radius: inherit;">
        <div class="yt-spec-touch-feedback-shape
        yt-spec-touch-feedback-shape--overlay-touch-response" aria-hidden="true">
        <div class="yt-spec-touch-feedback-shape__stroke" style=""></div>
        <div class="yt-spec-touch-feedback-shape__fill" style=""></div></div>
        </yt-touch-feedback-shape></button></yt-button-shape></ytd-menu-renderer>
        :return:
        """
        _query = "#page-manager > ytd-browse > ytd-playlist-header-renderer \
            > div > \
            div.immersive-header-content.style-scope.ytd-playlist-header-renderer > \
            div.thumbnail-and-metadata-wrapper.style-scope.ytd-playlist-header-renderer \
            > div > \
            div.metadata-action-bar.style-scope.ytd-playlist-header-renderer > \
            div.metadata-buttons-wrapper.style-scope.ytd-playlist-header-renderer \
            > ytd-menu-renderer"

        xpath = '//*[@id="page-manager"]/ytd-browse/ytd-playlist-header-renderer'
        xpath += "/div/div[2]/div[1]/div/div[1]/div[2]/ytd-menu-renderer"
        if show:
            link_text = "Show unavailable videos"
        else:
            link_text = "Hide unavailable videos"
        # Reverse is "Hide unavailable videos"
        result1 = result2 = None
        try:
            result1 = self.webDriver.find_element(By.XPATH, xpath)
        except Exception as err:
            self.youPrint("Exception reading menu hamburger:\n", err)

        # print("result1:", result1, "result2:", result2)
        # Hamburger menu is hidden unless action can be taken
        if result1 and result1.is_displayed():
            self.youPrint("Clicking xpath:", xpath)
            self.youDriverClick("xpath", xpath)
            try:
                # Button is hidden until hamburger clicked
                result2 = self.webDriver.find_element(By.LINK_TEXT, link_text)
            except Exception as err:
                self.youPrint("Exception 'Show unavailable videos':\n", err)

        if result2:
            self.youPrint("Clicking: '" + link_text + "'.")
            self.youDriverClick("link_text", link_text)
            if self.youUnavailableShown is None:
                self.youUnavailableShown = True
        elif self.youUnavailableShown:
            self.youPrint("Cannot click: '" + link_text + "'.")
            self.youPrint("link_text not found!")
            self.youUnavailableShown = None

        """ Button to click:

        <a class="yt-simple-endpoint style-scope ytd-menu-navigation-item-renderer" tabindex="-1" 
            href="/playlist?list=PLthF248A1c69kNWZ9Q39Dow3S2Lxp74mF">
    <tp-yt-paper-item class="style-scope ytd-menu-navigation-item-renderer" style-target="host" role="option" 
    tabindex="0" aria-disabled="false"><!--css-build:shady-->
      <yt-icon class="style-scope ytd-menu-navigation-item-renderer"
        ><!--css-build:shady--><!--css-build:shady--><yt-icon-shape 
        class="style-scope yt-icon"><icon-shape class="yt-spec-icon-shape">
        <div style="width: 100%; height: 100%; fill: currentcolor;"><svg height="24" 
        viewBox="0 0 24 24" width="24" focusable="false" 
        style="pointer-events: none; display: block; width: 100%; height: 100%;"
        ><path d="M12 8.91c1.7 0 3.09 1.39 3.09 3.09S13.7 15.09 12 15.09 8.91 13.7 
        8.91 12 10.3 8.91 12 8.91m0-1c-2.25 0-4.09 1.84-4.09 4.09s1.84 4.09 4.09 
        4.09 4.09-1.84 4.09-4.09S14.25 7.91 12 7.91zm0-1.73c3.9 0 7.35 2.27 8.92 
        5.82-1.56 3.55-5.02 5.82-8.92 5.82-3.9 0-7.35-2.27-8.92-5.82C4.65 8.45 8.1 
        6.18 12 6.18m0-1C7.45 5.18 3.57 8.01 2 12c1.57 3.99 5.45 6.82 10 
        6.82s8.43-2.83 10-6.82c-1.57-3.99-5.45-6.82-10-6.82z"
        ></path></svg></div></icon-shape></yt-icon-shape></yt-icon>
      <yt-formatted-string class="style-scope ytd-menu-navigation-item-renderer"
      >Show unavailable videos</yt-formatted-string>

</tp-yt-paper-item>
  </a>

        XPATH: //*[@id="items"]/ytd-menu-navigation-item-renderer/a
        JSPATH: document.querySelector("#items > ytd-menu-navigation-item-renderer > a")

        OUTER OUTER:
        <tp-yt-iron-dropdown horizontal-align="auto" vertical-align="top" aria-disabled="false" 
            class="style-scope ytd-popup-container" prevent-autonav="true" 
            style="outline: none; z-index: 2202; position: fixed; left: 208px; top: 439.5px;"
            ><!--css-build:shady--><div id="contentWrapper" 
            class="style-scope tp-yt-iron-dropdown">
  <ytd-menu-popup-renderer slot="dropdown-content" class="style-scope ytd-popup-container" tabindex="-1" use-icons="" 
      style="outline: none; box-sizing: border-box; max-width: 244.477px; max-height: 52px;"
      ><!--css-build:shady--><!--css-build:shady--><tp-yt-paper-listbox id="items" 
      class="style-scope ytd-menu-popup-renderer" role="listbox" tabindex="0"
      ><!--css-build:shady--><ytd-menu-navigation-item-renderer 
      class="style-scope ytd-menu-popup-renderer iron-selected" use-icons="" 
      system-icons="" role="menuitem" tabindex="-1" aria-selected="true"
      ><!--css-build:shady--><!--css-build:shady-->
  <a class="yt-simple-endpoint style-scope ytd-menu-navigation-item-renderer" tabindex="-1" 
        href="/playlist?list=PLthF248A1c69kNWZ9Q39Dow3S2Lxp74mF">
    <tp-yt-paper-item class="style-scope ytd-menu-navigation-item-renderer" style-target="host" role="option" 
        tabindex="0" aria-disabled="false"><!--css-build:shady-->
      <yt-icon class="style-scope ytd-menu-navigation-item-renderer">
        <!--css-build:shady--><!--css-build:shady--><yt-icon-shape 
        class="style-scope yt-icon"><icon-shape class="yt-spec-icon-shape"
        ><div style="width: 100%; height: 100%; fill: currentcolor;">
        <svg height="24" viewBox="0 0 24 24" width="24" focusable="false" 
        style="pointer-events: none; display: block; width: 100%; height: 100%;"
        ><path d="M12 8.91c1.7 0 3.09 1.39 3.09 3.09S13.7 15.09 12 15.09 8.91 13.7 
        8.91 12 10.3 8.91 12 8.91m0-1c-2.25 0-4.09 1.84-4.09 4.09s1.84 4.09 4.09 
        4.09 4.09-1.84 4.09-4.09S14.25 7.91 12 7.91zm0-1.73c3.9 0 7.35 2.27 8.92 
        5.82-1.56 3.55-5.02 5.82-8.92 5.82-3.9 0-7.35-2.27-8.92-5.82C4.65 8.45 8.1 
        6.18 12 6.18m0-1C7.45 5.18 3.57 8.01 2 12c1.57 3.99 5.45 6.82 10 
        6.82s8.43-2.83 10-6.82c-1.57-3.99-5.45-6.82-10-6.82z"
        ></path></svg></div></icon-shape></yt-icon-shape></yt-icon>
      <yt-formatted-string class="style-scope ytd-menu-navigation-item-renderer"
        >Show unavailable videos</yt-formatted-string>

</tp-yt-paper-item>
  </a>
<dom-if class="style-scope ytd-menu-navigation-item-renderer"><template is="dom-if"></template></dom-if>
</ytd-menu-navigation-item-renderer>
</tp-yt-paper-listbox>
<div id="footer" class="style-scope ytd-menu-popup-renderer"></div>
</ytd-menu-popup-renderer>
</div>
</tp-yt-iron-dropdown>


        <yt-icon class="style-scope ytd-menu-navigation-item-renderer"
            ><!--css-build:shady--><!--css-build:shady--><yt-icon-shape 
            class="style-scope yt-icon"><icon-shape class="yt-spec-icon-shape"
            ><div style="width: 100%; height: 100%; fill: currentcolor;"
            ><svg height="24" viewBox="0 0 24 24" width="24" focusable="false" 
            style="pointer-events: none; display: block; width: 100%; height: 100%;"
            ><path d="M12 8.91c1.7 0 3.09 1.39 3.09 3.09S13.7 15.09 12 15.09 8.91 13.7 
            8.91 12 10.3 8.91 12 8.91m0-1c-2.25 0-4.09 1.84-4.09 4.09s1.84 4.09 4.09 
            4.09 4.09-1.84 4.09-4.09S14.25 7.91 12 7.91zm0-1.73c3.9 0 7.35 2.27 8.92 
            5.82-1.56 3.55-5.02 5.82-8.92 5.82-3.9 0-7.35-2.27-8.92-5.82C4.65 8.45 
            8.1 6.18 12 6.18m0-1C7.45 5.18 3.57 8.01 2 12c1.57 3.99 5.45 6.82 10 
            6.82s8.43-2.83 10-6.82c-1.57-3.99-5.45-6.82-10-6.82z"
            ></path></svg></div></icon-shape></yt-icon-shape></yt-icon>
        XPATH FULL:
        /html/body/ytd-app/ytd-popup-container/tp-yt-iron-dropdown        

        TOP LEVEL?
<div id="contentWrapper" class="style-scope tp-yt-iron-dropdown">
  <ytd-menu-popup-renderer slot="dropdown-content" class="style-scope ytd-popup-container" tabindex="-1" use-icons="" 
    style="outline: none; box-sizing: border-box; max-width: 244.477px; max-height: 52px;"
    ><!--css-build:shady--><!--css-build:shady--><tp-yt-paper-listbox id="items" 
    class="style-scope ytd-menu-popup-renderer" role="listbox" tabindex="0"
    ><!--css-build:shady--><ytd-menu-navigation-item-renderer 
    class="style-scope ytd-menu-popup-renderer iron-selected" use-icons="" 
    system-icons="" role="menuitem" tabindex="-1" aria-selected="true"
    ><!--css-build:shady--><!--css-build:shady-->
  <a class="yt-simple-endpoint style-scope ytd-menu-navigation-item-renderer" tabindex="-1" 
    href="/playlist?list=PLthF248A1c69kNWZ9Q39Dow3S2Lxp74mF">
    <tp-yt-paper-item class="style-scope ytd-menu-navigation-item-renderer" 
        style-target="host" role="option" tabindex="0" aria-disabled="false"
        ><!--css-build:shady-->
      <yt-icon class="style-scope ytd-menu-navigation-item-renderer"><!--css-build:shady--><!--css-build:shady-->
          <yt-icon-shape class="style-scope yt-icon"><icon-shape 
          class="yt-spec-icon-shape"><div 
          style="width: 100%; height: 100%; fill: currentcolor;">
          <svg height="24" viewBox="0 0 24 24" width="24" focusable="false" 
          style="pointer-events: none; display: block; width: 100%; height: 100%;"
          ><path d="M12 8.91c1.7 0 3.09 1.39 3.09 3.09S13.7 15.09 12 15.09 8.91 
          13.7 8.91 12 10.3 8.91 12 8.91m0-1c-2.25 0-4.09 1.84-4.09 4.09s1.84 
          4.09 4.09 4.09 4.09-1.84 4.09-4.09S14.25 7.91 12 7.91zm0-1.73c3.9 0 
          7.35 2.27 8.92 5.82-1.56 3.55-5.02 5.82-8.92 5.82-3.9 
          0-7.35-2.27-8.92-5.82C4.65 8.45 8.1 6.18 12 6.18m0-1C7.45 5.18 3.57 
          8.01 2 12c1.57 3.99 5.45 6.82 10 6.82s8.43-2.83 
          10-6.82c-1.57-3.99-5.45-6.82-10-6.82z"
          ></path></svg></div></icon-shape></yt-icon-shape></yt-icon>
      <yt-formatted-string class="style-scope ytd-menu-navigation-item-renderer"
        >Show unavailable videos</yt-formatted-string>

</tp-yt-paper-item>
  </a>
<dom-if class="style-scope ytd-menu-navigation-item-renderer"><template is="dom-if"></template></dom-if>
</ytd-menu-navigation-item-renderer>
</tp-yt-paper-listbox>
<div id="footer" class="style-scope ytd-menu-popup-renderer"></div>
</ytd-menu-popup-renderer>
</div>        
        """
        return

    def youGetAllGoodTimes(self, good_links):
        """ Get Relevant Video Durations (4x's more are irrelevant)
            TODO: 2024-01-28 - Build Chill playlist video #90 should be hidden
                but it appears in mserve. Then video counts are out of sync.
                https://www.youtube.com/watch?v=562VuMrFUys
        :param good_links: Count to stop at
        :return: good_times, listTimes
        """

        listTimes = []
        good_times = bad_times = 0
        spans = self.webDriver.execute_script(
            "return document.querySelectorAll('span')")
        for span in spans:
            if good_times == good_links:
                break  # There are extra 90 durations not wanted
            dictSpan = self.webDriver.execute_script(
                'var items = {}; \
                for (index = 0; index < \
                arguments[0].attributes.length; ++index) \
                { items[arguments[0].attributes[index].name] = \
                arguments[0].attributes[index].value }; \
                return items;',
                span)
            class_list = dictSpan.get('class', None)
            duration_str = dictSpan.get('aria-label', None)
            span_id = dictSpan.get('id', None)
            if not class_list or not duration_str or not span_id or \
                    "style-scope ytd-thumbnail-overlay-time-status-renderer" \
                    not in class_list or span_id != "text":
                bad_times += 1
                # print("\ndictSpan:", dictSpan)
                continue

            good_times += 1
            # duration_str = duration_str.replace(",", ":")
            # duration = re.sub(r'[^0-9,:]', '', duration_str)
            # Above should work but isn't :(
            parts = duration_str.split(", ")
            mins = "0"
            secs = "00"
            if len(parts) == 1:
                # Either "minutes" or "seconds" is missing (so is zero)
                if "minutes" in parts[0]:
                    mins = parts[0].split(" ")[0]
                else:
                    secs = parts[0].split(" ")[0].rjust(2, "0")
            else:
                mins = parts[0].split(" ")[0]
                secs = parts[1].split(" ")[0].rjust(2, "0")

            listTimes.append(mins + ":" + secs)
            # if good_times < 10:
            # print("\ndictSpan:", dictSpan)
            # print("#", good_times, "duration_str:", duration_str,
            #      "duration:", mins + ":" + secs)

        self.youPrint("good_times:", good_times, "bad_times:", bad_times)

        return good_times, listTimes

    # noinspection SpellCheckingInspection
    def youMonitorLinks(self):
        """ YouTube address bar URL link changes with each new video.
            Test if changed from last check and update treeview.
        :returns: None: Error getting link. Link: video ID link found
        """

        _now = time.time()
        link = self.youCurrentLink()
        _link_time = time.time() - _now  # 0.12 seconds
        if not link:
            return None

        if link == self.youLastLink:  # Oct 28/23 Was last_link
            return link

        if "/playlist?list=" in link:
            self.youPrint('"/playlist?list=" found in "link"!', link, lv=0)
            self.youPrint('youMonitorLinks() cannot deal with this!', lv=0)
            return None

        # FIRST SONG
        #   https://www.youtube.com/watch?v=a-Xfv64uhMI&list=
        #       PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM
        # SECOND+ SONG
        #   https://www.youtube.com/watch?v=bePCRKGUwAY&list=
        #       PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM&index=2

        try:
            video_link = link.split("&list=")[0]
        except IndexError:
            self.youPrint("Could not find '&list=' in link!", link, lv=0)
            return None

        try:
            video_link_id = video_link.split("/watch?v=")[1]
        except IndexError:
            self.youPrint("Could not find '/watch?v=' in video_link!",
                          video_link)
            return None

        make_link = "https://www.youtube.com/watch?v=" + video_link_id
        you_tree_iid_int = self.youTreeNdxByLink(make_link, link)

        # Don't test you_tree_iid_int for True because first index is 0
        if you_tree_iid_int is None:
            self.youPrint("youSmartPlayAll() - " +
                          "you_tree_iid_int is type: <None>", nl=True)
            self.youPrint("Error on make_link    :", make_link)
            self.youPrint("Original video_link   :", video_link)
            self.youPrint("Original video_link_id:", video_link_id)
            self.youPrint("len(self.listYouTube) :", len(self.listYouTube))
            self.youPrint("self.listYouTube[0]   :", self.listYouTube[0]['link'])
            self.youPrint("youViewCountSkipped   :",
                          self.youViewCountSkipped, lv=0)  # 2023-12-16 Always print
            self.youPrint("Remove:   '", self.act_description,
                          "'.csv', '.pickle' and '.private'")
            self.youPrint("Directory: '" + g.USER_DATA_DIR +
                          os.sep + "YouTubePlaylists'")
            '''
                06:22:17.2 STARTING Playlist - Song # 5     | bEWHpHlfuVU
                Link: https://www.youtube.com/watch?v=DLOth-BuCNY   NOT FOUND!
                                           Should be: bEWHpHlfuVU
            '''
            # May have hit end of list or YouTube playing recommendation 2023-12-18
            if self.listYouTubeCurrIndex < len(self.listYouTube) - 1:
                you_tree_iid_int = self.listYouTubeCurrIndex + 1
            else:
                you_tree_iid_int = 0
                self.youViewSkippedTime = time.time()
                self.youViewCountSkipped += 1

            self.youPlaylistIndexStartPlay(str(you_tree_iid_int), restart=True)

        song_no = str(you_tree_iid_int + 1).ljust(4)
        self.youPrint("STARTING Playlist - Song №",
                      song_no, " |", video_link_id, nl=True)

        # self.youPrint("Assume Ad. Automatically turn down volume.")
        self.youVolumeOverride(ad=True)  # Set volume 25% for last sink
        # Some songs do not have ads at start so need to reverse manually
        self.youAssumedAd = True  # Reset after player status == 1

        self.youLrcDestroyFrame()  # If last song had lyrics, swap frames
        try:
            self.you_tree.see(str(you_tree_iid_int))
        except tk.TclError:
            self.youPrint("self.you_tree.see(str(you_tree_iid_int)) tcl error:",
                          you_tree_iid_int, lv=0)
            you_tree_iid_int = self.listYouTubeCurrIndex
            self.you_tree.see(str(you_tree_iid_int))
            '''
22:29:20.5 youViewCountSkipped   : 118
Exception in Tkinter callback
Traceback (most recent call last):
  File "/usr/lib/python2.7/lib-tk/Tkinter.py", line 1540, in __call__
    return self.func(*args)
  File "/home/rick/python/mserve.py", line 15837, in <lambda>
    command=lambda: self.youSmartPlayAll())
  File "/home/rick/python/mserve.py", line 16150, in youSmartPlayAll
    link = self.youMonitorLinks()
  File "/home/rick/python/mserve.py", line 17068, in youMonitorLinks
    self.you_tree.see(str(you_tree_iid_int))
  File "/usr/lib/python2.7/lib-tk/ttk.py", line 1392, in see
    self.tk.call(self._w, "see", item)
TclError: Item 123 not found
            '''

        toolkit.tv_tag_remove_all(self.you_tree, 'play_sel')
        toolkit.tv_tag_add(
            self.you_tree, str(you_tree_iid_int), 'play_sel')
        # Keep second place. See two past, then one above
        two_past = you_tree_iid_int + 2
        if two_past < len(self.listYouTube):
            self.you_tree.see(str(two_past))
        one_before = you_tree_iid_int - 1
        if one_before >= 0:
            self.you_tree.see(str(one_before))

        self.resetYouTubeDuration()  # Reset one song duration
        self.youCurrentIndex()  # Set self.durationYouTube var

        ''' Get lyrics from list of dictionaries '''
        lrc = self.listYouTube[you_tree_iid_int].get('lrc', None)
        if lrc:
            self.hasLrcForVideo = True
            self.listLrcLines = lrc.splitlines()
            self.youLrcBuildFrame(str(you_tree_iid_int))

        self.listYouTubeCurrIndex = you_tree_iid_int
        self.displayPlaylistCommonTitle()
        return link

    # noinspection SpellCheckingInspection
    def youMonitorPlayerStatus(self, player_status, debug=False):
        """ Update progress display in button bar and skip commercials

            2025-03-09: Uses back > forward technique which is no longer
            reliable because YouTube can now restart video at beginning
            instead of where it left off. Major rewrite required.

            Check if self.topYouTreeLRC window exists and update lyrics
            line currently being sung with "lrc_sel" tag

        :param player_status: Music player status (-1, 1, 2, 3, 5)
        :param debug: Print debug statements
        :return: False mserve is closing, else True
        """

        # Capture weird player status == 0
        if player_status not in [-1, 1, 2, 3, 5]:
            self.youPrint("Unknown player_status: ", player_status)
            # -1 = ad is playing

            # 0 = Unknown (First time appeared on Oct 29/23 - 9:50 am)
            # 09:50:17.0 STARTING Playlist - Song # 9     | mrojrDCI02k
            # 09:50:17.3 Ad visible. Player status: -1
            # 09:50:18.2 Ad visible. Player status: -1
            # 09:50:20.2 Forced driver refresh after: 0.9
            # 09:50:20.2 MicroFormat video found playing  | zQAd7eQzLus
            # 09:50:21.9 Browser Address Bar URL Link ID  | mrojrDCI02k
            # 09:50:22.0 Ad visible. Player status: -1
            # 09:50:26.4 MicroFormat found after: 0.7     | mrojrDCI02k
            # Unknown player_status:  0

            # 1 = playing
            # 2 = paused or user dragging YT progress bar
            # 3 = begin playing song or YouTube prompting to play after suspend
            # 5 = Status prior to Play All and starting Ad
            return

        now = time.time()
        if player_status == 1:
            # If volume was forced down set it back
            if self.youAssumedAd:
                self.youPrint("Reversing self.youAssumeAd", level=5)
                self.youAssumedAd = None
                self.youVolumeOverride(ad=False)
            delta = now - self.timeLastYouTube
            self.timeLastYouTube = now
            self.progressYouTube += delta
            # print("Duration:", tmf.mm_ss(self.progressYouTube, rem='d'),
            #      "of:", self.durationYouTube, self.youProVar.get(), end="\r")
            # mm_ss(seconds, brackets=False, trim=True, rem=None)

            if self.hasLrcForVideo and self.youLrcFrame:  # Oct 22/23
                self.youLrcHighlightLine()
        else:
            self.timeLastYouTube = now

        self.youUpdatePlayerButton(player_status)
        self.updateYouTubeDuration()

        # Must wait to fix repeating song until "microformat" is refreshed
        MICRO_FORMAT_WAIT = 0.9  # 1.5x longest known early found of 0.6

        if self.isSongRepeating:
            micro_id = self.youGetMicroFormat()
            link_id = self.youCurrentVideoId()
            elapsed = time.time() - self.timeForwardYouTube

            # Has elapsed time reached wait limit?
            if elapsed > MICRO_FORMAT_WAIT:
                self.isSongRepeating = None  # Turn off future checks
                # Is micro_id inside video different than link?
                if micro_id != link_id:
                    self.youPrint("Force browser refresh after:",
                                  tmf.mm_ss(elapsed, rem='d'), "|", link_id, level=4)
                    self.webDriver.refresh()
                    self.youPrint("MicroFormat video found playing  |", micro_id, level=4)
                    self.youWaitMusicPlayer()  # wait for music player
                    self.youPrint("Browser Address Bar URL Link ID  |", link_id, level=4)
                    self.resetYouTubeDuration()  # Reset one song duration

            # Is micro_id inside video different than link?
            elif micro_id == link_id:
                # ID inside video matches address bar url
                self.isSongRepeating = None
                self.youPrint("MicroFormat found after:",
                              tmf.mm_ss(elapsed, rem='d'), "    |", micro_id, level=4)

        # Has YouTube popped up an ad?
        if not self.youCheckAdRunning():

            # DRY - Reset full screen if last video playing in full screen
            if self.youForceVideoFull:
                ''' Make YouTube full screen '''
                self.youPrint("Make YouTube full screen")
                actions = ActionChains(self.webDriver)
                actions.send_keys('f')  # Send full screen key
                actions.perform()
                self.youForceVideoFull = None

            # NOT WORKING:
            # 19:02:29.0 STARTING Playlist - Song № 2     | HnilTXUQtag
            # 19:02:29.0 Assume Ad. Automatically turn down volume.
            # 19:02:29.0 Reversing self.youAssumeAd
            # 19:02:29.2 Make YouTube full screen
            #
            # 19:02:30.7 STARTING Playlist - Song № 2     | HnilTXUQtag
            # 19:02:30.7 Assume Ad. Automatically turn down volume.
            # 19:02:31.0 Reversing self.youAssumeAd
            return True  # Nothing to do

        self.youVolumeOverride(True)  # Ad playing override

        ''' Ad Running - reset start variables '''
        self.isSongRepeating = None
        self.resetYouTubeDuration()  # Reset one song duration

        # Music Player final_status printed at top of loop below.
        self.youWaitMusicPlayer()

        while True:  # Ad was visible. Loop until status is song playing (1)
            """  TODO: At start, quickly ramp down volume over 1/10 second
                       At end, Slowly ramp up volume over 1/2 second
                       However, setup mute mode too, so no ramping
                       Need to capture web browsers sink and then use: 
                            pav.fade(self.webDriver_sink, start, end, time) """

            """ No longer needed - inside youWaitMusicPlayer()
            # play top refresh + .after(16). With this, CPU load is 3.5% not 6%
            if not lcs.fast_refresh(tk_after=True):
                self.webDriver.quit()
                return False
            """

            ''' TODO: if self.youDebugLevel == 1: '''
            # self.youPrint("Ad visible. Player status:", final_status)

            # print(ext.t(short=True, hun=True),
            #      "Ad visible. Player status:", final_status)

            # TODO: Only all housekeeping when < .1 second since last time
            #       at this point. E.G.
            # 20:10:55.2 Ad visible. Player status: -1
            # 20:10:55.3 Ad visible. Player status: -1
            # 20:10:55.3 Ad visible. Player status: -1
            # 20:10:55.4 Ad visible. Player status: -1
            # 20:10:55.5 Ad visible. Player status: -1
            self.youHousekeeping()

            # Ad is running
            """  TODO: When resuming from suspend, 100's of ads can appear for
                       duration of sleep. Unlike above where Ads are .1 second
                       apart, these Ads are 2 seconds apart. Fastest way out is
                       to reload the last song. 
            """
            count = 0
            # self.webDriver.find_element(By.CSS_SELECTOR, ".ytp-ad-duration-remaining")

            self.youPrint("# 0. Player Status:",
                          self.youGetPlayerStatus(), lv=9, nl=True)

            while self.youCheckAdRunning():
                # Back button goes to previous song played
                self.youVolumeOverride(True)  # Ad playing override
                self.webDriver.back()
                self.youPrint("BACK LOOP Ad still visible:", count, end="\r", lv=9)
                if self.youCheckAdRunning():
                    count += 1
                    if not lcs.fast_refresh():
                        self.webDriver.quit()
                        return False

            self.youPrint("webDriver.back() visible loops:", str(count).ljust(2),
                          " | Video Index:", self.youCurrentIndex(), lv=9, nl=True)
            # count is always 1?
            self.youPrint("# 1. Player Status:", self.youGetPlayerStatus(), lv=9)
            self.youPrint("# 1. Video Index before FIRST forward:",
                          self.youCurrentIndex(), lv=9)

            self.webDriver.forward()  # Send forward page event
            player_status = self.youWaitMusicPlayer()
            # If status is NONE probably dialog prompt
            if not player_status:
                # Answer dialog box for "Video paused. Continue watching?"
                # self.youHousekeeping()  # Not working as intended...
                # Check now inside self.youWaitMusicPlayer
                player_status = self.youWaitMusicPlayer()
                if not player_status:
                    self.youPrint("Shutting down, dialog prompt or player broken!",
                                  level=0)  # 0 = forced printing all the time
                    continue

            if debug:
                self.youPrint("# 2. Player Status after 400ms:",
                              self.youGetPlayerStatus(), lv=9)
                self.youPrint("# 2. Video Index:", self.youCurrentIndex(), lv=9)
                video_id = self.youGetMicroFormat()
                self.youPrint("# 2. youGetMicroFormat() video_id:", video_id, lv=9)

            if self.youCheckAdRunning():
                # With this test, don't know if ad #1 or #2 is visible...
                self.webDriver.forward()
                if debug:
                    self.youPrint("THREE FORWARDS", "Video Index:",
                                  self.youCurrentIndex(), lv=9)
                    self.youPrint("# 3A. Player Status: BEFORE 2nd forward wait",
                                  self.youGetPlayerStatus(), lv=9)
                    self.youPrint("# 3A. Video Index:", self.youCurrentIndex(), lv=9)
                    video_id = self.youGetMicroFormat()
                    self.youPrint("# 3A. youGetMicroFormat() video_id:",
                                  video_id, lv=9)

                # self.top.after(350)  # 300 too short for triple ad
                player_status = self.youWaitMusicPlayer()
                if not player_status:
                    self.youPrint("Shutting down or player broken!")
                    continue
                if debug:
                    self.youPrint("# 3B. Player Status after 350ms:",
                                  self.youGetPlayerStatus(), lv=9)
                    self.youPrint("# 3B. URL Index:", self.youCurrentIndex(), lv=9)
                    video_id = self.youGetMicroFormat()
                    self.youPrint("# 3B. youGetMicroFormat() video_id:", video_id, lv=9)
            else:
                if debug:
                    self.youPrint("TWO FORWARDS",
                                  "Video Index:", self.youCurrentIndex(), lv=9)
                    self.youPrint("# 3. Player Status:", self.youGetPlayerStatus(), lv=9)
                    self.youPrint("# 3. Video Index:", self.youCurrentIndex(), lv=9)
                    video_id = self.youGetMicroFormat()
                    self.youPrint("# 3. youGetMicroFormat() video_id:", video_id, lv=9)

            # Could be within second ad but extra forward needed for next
            self.webDriver.forward()  # Extra forward needed for next song
            final_status = self.youWaitMusicPlayer()
            if not final_status:
                self.youPprint("Weird Error: youWaitMusicPlayer(self.webDriver,",
                               "debug=False)", lv=0)
                """ CAUSED BY INTERRUPTION to confirm to continue when screen dim

                    21:31:25.3 STARTING Playlist - Song # 16    | KZjnJ_9GR5o
                    21:31:26.7 Ad visible. Music player status: -1

                    youWaitMusicPlayer() more than 10 seconds

                    youWaitMusicPlayer() 10,001.6 Null: 0 Paused: 2953 Starting: 0 Between Songs: 0

                    Weird Error: youWaitMusicPlayer(self.webDriver, debug=False)

                    21:35:18.3 STARTING Playlist - Song # 17    | I9xpq3KGkSM
                    21:35:19.8 Ad visible. Music player status: -1
                    21:35:26.0 MicroFormat found early: I9xpq3KGkSM after: 0.6

                """
                return False  # Weird error

            if debug:
                self.youPrint("# 4. Player Status:", self.youGetPlayerStatus(), lv=9)
                self.youPrint("# 4. Video Index:", self.youCurrentIndex(), lv=9)
                video_id = self.youGetMicroFormat()  # From mini-player script
                self.youPrint("# 4. youGetMicroFormat() video_id:", video_id, lv=9)
            else:
                _video_id = self.youGetMicroFormat()  # From mini-player script

            if final_status == 1 and not self.youCheckAdRunning():
                self.isSongRepeating = True  # Means we have to check
                self.resetYouTubeDuration()  # Reset one song duration

                # DRY - Reset full screen if last video playing in full screen
                if self.youForceVideoFull:
                    ''' Make YouTube full screen '''
                    self.youPrint("Make YouTube full screen")
                    actions = ActionChains(self.webDriver)
                    actions.send_keys('f')  # Send full screen key
                    actions.perform()
                    self.youForceVideoFull = None

                return True

    def youWaitMusicPlayer(self, startup=False):
        """ self.webDriver.forward() was just executed. Wait for browser to process.
            Wait until YouTube music player status is:
                1 Music Playing or,
               -1 Ad Playing

            :param startup: When True override 10 second timeout to 1 second
            :return: None = timeout reached, 99 = startup 1 sec timeout reached,
                     player_status = -1 ad playing, = 1 music playing """

        ''' Housekeeping every 1 second (out of 10) '''
        lastHousekeepingTime = time.time()

        count_none = count_2 = count_3 = count_5 = 0
        start = time.time()
        while True:
            if not lcs.fast_refresh(tk_after=False):
                return None
            elapsed = (time.time() - start) * 1000
            if elapsed > 10000.0:  # Greater than 10 seconds?
                self.youPrint("youWaitMusicPlayer() took",
                              "more than 10,000 milliseconds", lv=1, nl=True)
                self.youPrint(
                    "Elapsed:", '{:n}'.format(elapsed),
                    "ms  | Null:", count_none, " | Paused:", count_2,
                    " | Starting:", count_3, " | Idle:", count_5, "\n", lv=1)
                return None

            ad_playing = None
            player_status = self.youGetPlayerStatus()
            if player_status is None:
                count_none += 1  # Still initializing
            elif player_status == 2:
                count_2 += 1  # Music Paused... this is a problem
            elif player_status == 3:
                count_3 += 1  # Something is about to play
            elif player_status == 5:
                ad_playing = self.youCheckAdRunning()
                if ad_playing:
                    break  # Oct 5/23 new technique
                count_5 += 1  # Between songs or Ad before 1st song
                if elapsed > 1000.0 and startup:
                    print("Overriding 1 second IPL player delay")
                    return 99
            elif player_status == 1 or player_status == -1:
                break

            ''' Test 1 second out of 10 seconds when not startup '''
            now = time.time()
            if not startup and now - lastHousekeepingTime > 1.0:
                # Prints for song #10, #17
                self.youPrint(
                    "youWaitMusicPlayer() - 1 second Housekeeping check.")
                lastHousekeepingTime = now
                self.youHousekeeping()

        self.youPrint("youWaitMusicPlayer", '{:n}'.format(elapsed),
                      "ms | Null:", count_none, " | Paused:", count_2,
                      " | Starting:", count_3, " | Idle:", count_5, lv=7, nl=True)

        # Potentially reverse volume override earlier.
        # Getting many false positives as already at desired volume...
        ad = player_status == -1 or ad_playing
        if not ad:  # Music Video is playing
            # self.youPrint("Reversing self.youAssumeAd")
            self.youAssumedAd = None
            self.youVolumeOverride(ad)  # Restore volume 100%
        elif not self.youAssumedAd:  # Ad is running
            self.youVolumeOverride(ad)  # Turn down volume 25%
            self.youAssumedAd = True

        return player_status

    def youVolumeOverride(self, ad=True):
        """ If commercial at 100% set to 25%. If not commercial and
            25%, set to 100% """

        second = self.youGetChromeSink()  # Set active self.youPlayerSink
        first = self.youPlayerSink  # 2023-12-04 used to be 2nd, but swapped

        if self.youPlayerSink is None:
            self.youPrint("youVolumeOverride() sink failure!")
            # First video after age restricted video that won't play
            return

        sink_no = self.youPlayerSink.sink_no_str
        if self.youPlayerSink != first:
            self.youPrint("Multiple Google Chrome Audio Sinks !!!",
                          first.sink_no_str, sink_no)
            print("First :", first)
            print("Second:", second)

        try:
            vol = pav.get_volume(sink_no)
        except Exception as err:
            self.youPrint("youVolumeOverride() Exception:", err)
            return

        '''
Redundant calls after turning down to 25% and up to 100%:

18:18:10.3 STARTING Playlist - Song № 65    | rgWr2nln83s
18:18:10.3 Assume Ad. Automatically turn down volume.
18:18:10.3 Sink No: 870 Volume forced to 25%
18:18:11.0 Sink No: 870 Volume NOT forced: 25
18:18:11.2 Ad visible. Player status: -1
18:18:11.4 Sink No: 870 Volume NOT forced: 25
18:18:12.7 Sink No: 870 Volume forced to 100%
18:18:13.1 Sink No: 870 Volume NOT forced: 100
18:18:13.7 MicroFormat found after: 0.3     | rgWr2nln83s
18:22:02.3 Sink No: 870 Volume forced to 25%
18:22:02.4 Sink No: 870 Volume NOT forced: 25
18:22:02.4 Ad visible. Player status: -1
18:22:02.5 Sink No: 870 Volume NOT forced: 25
18:22:03.7 Ad visible. Player status: -1
18:22:04.3 Sink No: 870 Volume NOT forced: 25
18:22:05.2 Sink No: 870 Volume forced to 100%
18:22:05.3 Sink No: 870 Volume NOT forced: 100
        '''

        if vol != 25 and vol != 100:
            self.youPrint("Sink:", sink_no,
                          "Invalid VOLUME:", vol, type(vol))
        if ad:
            # self.youPrint("Sink:", self.youPlayerSink.sink_no_str,
            #              "Volume during commercial:", vol, type(vol))
            if vol == 100:
                pav.set_volume(sink_no, 25.0)
                self.youPrint("Sink No:", sink_no, "Volume forced to 25%", level=5)
            else:
                self.youPrint("Sink No:", sink_no, "Volume NOT forced:", vol, level=5)
                pass
        else:
            self.youPrint("Sink:", sink_no,
                          "Volume NO commercial:", vol, type(vol), level=5)
            if vol == 25:
                pav.set_volume(sink_no, 100.0)
                self.youPrint("Sink No:", sink_no, "Volume forced to 100%", level=5)
            else:
                self.youPrint("Sink No:", sink_no, "Volume NOT forced:", vol, level=5)
                pass

    def youLrcBuildFrame(self, item):
        """ Build Frame for YouTube Video LRC (synchronized lyrics)

            One time create LRC frame and TreeFrame.grid_remove()
            If created, TreeFrame.grid_remove() and lrcFrame.grid() reactivate.

        """
        if self.youLrcFrame:
            # 2023-12-28 - This branch never executed. Lag after 500 x.
            self.tree_frame.grid_remove()  # Remove row 0 Treeview Frame
            self.youLrcFrame.grid()  # Reactivate row 1 LRC Frame
            self.youSetCloseButton()  # Set close button text
        else:

            tree_width = self.tree_frame.winfo_width()
            tree_height = self.tree_frame.winfo_height()
            self.tree_frame.grid_remove()  # Remove row 0 Treeview Frame

            # Master frame for Artwork and LRC Lyrics lines
            self.youLrcFrame = tk.Frame(self.frame, height=tree_height)
            self.youLrcFrame.grid_propagate(False)  # Don't grow the new frame
            self.youLrcFrame.grid(row=1, sticky=tk.NSEW)  # Row 1 new LRC frame
            self.youLrcFrame.columnconfigure(0, minsize=350, weight=1)  # Art
            self.youLrcFrame.columnconfigure(  # Subtract art & vert scroll size
                1, minsize=tree_width - 350, weight=1)  # for LRC lyrics width.

        ''' Song Artwork, Song Name, Progress, Time offset & highlight Color '''
        info_frame = tk.Frame(self.youLrcFrame)
        info_frame.grid(row=0, column=0, sticky=tk.NS)
        art_label = tk.Label(info_frame, borderwidth=0,
                             image=self.photosYouTube[int(item)])
        art_label.grid(row=0, column=0, sticky=tk.EW, padx=5, pady=10)

        song = tk.Label(info_frame, text=self.listYouTube[int(item)]['name'],
                        font=g.FONT14, wraplength=320, justify="center")
        song.grid(row=1, column=0, sticky=tk.EW, padx=5, pady=21)

        # Links https://stackoverflow.com/a/23482749/6929343
        link1 = tk.Label(info_frame, text="Google Song Meaning",
                         fg="blue", cursor="hand2",
                         font=g.FONT, wraplength=320, justify="center")
        link1.grid(row=2, column=0, sticky=tk.EW, padx=5, pady=21)
        url = "https://www.google.com/search?q=song meaning " + \
              self.listYouTube[int(item)]['name']
        link1.bind("<Button-1>", lambda e: webbrowser.open_new(url))

        # Song progress seconds into duration
        self.youProLrcVar = tk.StringVar()
        self.youProLrcVar.set("Progress: 0")
        position = tk.Label(info_frame, textvariable=self.youProLrcVar,
                            font=g.FONT, wraplength=320, justify="center")
        position.grid(row=3, column=0, sticky=tk.EW, padx=5, pady=21)

        # Lyrics Time Offset +/- seconds
        time_string = tk.Label(info_frame, text="Lyrics Time Offset",
                               font=g.FONT, wraplength=320, justify="center")
        time_string.grid(row=4, column=0, sticky=tk.EW, padx=5, pady=(20, 0))
        self.youLrcTimeOffsetVar = tk.DoubleVar()
        ndx = int(item)
        self.youLrcTimeOffset = self.listYouTube[ndx].get('lrc_timeoff', None)
        if self.youLrcTimeOffset is None:
            self.youLrcTimeOffset = 0.0
        self.youLrcTimeOffsetVar.set(self.youLrcTimeOffset)
        time_offset = tk.Entry(info_frame, textvariable=self.youLrcTimeOffsetVar,
                               font=g.FONT14, justify="center")
        time_offset.grid(row=5, column=0, sticky=tk.EW,
                         padx=5, pady=(0, 40))
        time_offset.bind("<FocusOut>", lambda e: self.youLrcUpdateTimeOffset(item))

        # Highlight background color
        bg_string = tk.Label(info_frame, text="Red / Green / Blue / Black" +
                                              " / Yellow / Cyan / Magenta",
                             font=g.FONT, wraplength=320, justify="center")
        bg_string.grid(row=6, column=0, sticky=tk.EW, padx=5, pady=(20, 0))
        self.youLrcBgColorVar = tk.StringVar()
        self.youLrcBgColor = self.listYouTube[ndx].get('lrc_color', None)
        if self.youLrcBgColor is None:
            self.youLrcBgColor = 'Yellow'
        self.youLrcBgColorVar.set(self.youLrcBgColor)
        bg_color = tk.Entry(info_frame, textvariable=self.youLrcBgColorVar,
                            font=g.FONT14, justify="center")
        # Want to increase X padding but it's forcing info_frame wider?
        bg_color.grid(row=7, column=0, sticky=tk.EW,
                      padx=5, pady=(0, 40))
        # bg_color.bind("<FocusOut>", self.youLrcUpdateBgColor)
        bg_color.bind("<FocusOut>", lambda e: self.youLrcUpdateBgColor(item))

        ''' Scrolled Text with LRC Lyrics '''
        # Text padding not working: https://stackoverflow.com/a/51823093/6929343
        self.scrollYT = toolkit.CustomScrolledText(
            self.youLrcFrame, state="normal", font=g.FONT14,
            borderwidth=15, relief=tk.FLAT)

        ''' Insert Lyrics Lines '''
        self.youFirstLrcTimeNdx = None  # 0-Index of first line with [mm:ss.99]
        self.youFirstLrcTime = None
        self.scrollYT.configure(state="normal")
        for ndx, line in enumerate(self.listLrcLines):
            line_time, line_text = self.youLrcParseLine(line)
            # print("line_time:", line_time, "line_text:", line_text)
            if not line_time:  # two spaces for background color before & after
                # one extra leading space for left-margin gutter not highlighted
                line = self.youLrcParseMeta(line)
                self.scrollYT.insert("end", "   " + line + "  \n")
            else:
                self.scrollYT.insert("end", "   " + line_text + "  \n")
                if self.youFirstLrcTimeNdx is None:  # don't test for not 0
                    self.youFirstLrcTimeNdx = ndx
                    self.youFirstLrcTime = line_time
        self.scrollYT.configure(state="disabled")

        self.scrollYT.configure(background="#eeeeee")  # Replace "LightGrey"
        self.scrollYT.config(spacing1=20)  # Spacing above the first line in a block of text
        self.scrollYT.config(spacing2=10)  # Spacing between the lines in a block of text
        self.scrollYT.config(spacing3=20)  # Spacing after the last line in a block of text
        self.scrollYT.tag_configure("center", justify='center')

        self.scrollYT.tag_add("center", "1.0", "end")
        self.scrollYT.grid(row=0, column=1, padx=3, pady=3, sticky=tk.NSEW)
        tk.Grid.rowconfigure(self.youLrcFrame, 0, weight=1)
        tk.Grid.columnconfigure(self.youLrcFrame, 1, weight=1)

        self.scrollYT.tag_config('red', background='Red', foreground='White',
                                 font=font.Font(size=14, weight="bold"))
        self.scrollYT.tag_config('green', background='Green', foreground='White',
                                 font=font.Font(size=14, weight="bold"))
        self.scrollYT.tag_config('blue', background='Blue', foreground='Yellow',
                                 font=font.Font(size=14, weight="bold"))
        self.scrollYT.tag_config('black', background='Black', foreground='Gold',
                                 font=font.Font(size=14, weight="bold"))
        self.scrollYT.tag_config('yellow', background='Yellow',
                                 font=font.Font(size=14, weight="bold"))
        self.scrollYT.tag_config('cyan', background='Cyan',
                                 font=font.Font(size=14, weight="bold"))
        self.scrollYT.tag_config('magenta', background='Magenta', foreground='White',
                                 font=font.Font(size=14, weight="bold"))

        # self.scrollYT.config(tabs=("2m", "40m", "50m"))  # Apr 9, 2023
        # self.scrollYT.config(tabs=("2m", "65m", "80m"))  # Apr 27, 2023

        # 2024-09-12 - TODO: https://stackoverflow.com/a/78976310/6929343
        self.scrollYT.config(tabs=("10", "240", "360"))  # Sep 11, 2024
        self.scrollYT.tag_configure("margin", lmargin1="10", lmargin2="240")

        # Fix Control+C  https://stackoverflow.com/a/64938516/6929343
        self.scrollYT.bind("<Button-1>", lambda event: self.scrollYT.focus_set())

        self.displayPlaylistCommonTitle()  # is self.top.update() needed?

        self.youLrcFrame.update()  # 2023-12-15 - Fixes .dlineinfo() errors

    def youLrcUpdateTimeOffset(self, item, *_args):
        """ Time Offset has just been changed. """
        old_time = self.youLrcTimeOffset
        self.youLrcTimeOffset = self.youLrcTimeOffsetVar.get()
        # Sanity check
        if not -150.0 < self.youLrcTimeOffset < 150.0:
            print("Offset entered:", self.youLrcTimeOffset, "is beyond 150 seconds.")
            self.youLrcTimeOffset = old_time
            self.youLrcTimeOffsetVar.set(self.youLrcTimeOffset)
            self.top.update()
            return

        if old_time == 0.0 and self.youLrcTimeOffset == 0.0:
            return  # No point saving default

        # Write new value to disk
        ndx = int(item)
        start = time.time()
        self.listYouTube[ndx]['lrc_timeoff'] = self.youLrcTimeOffset
        fname = self.nameYouTube.replace(".csv", ".pickle")
        ext.write_to_pickle(fname, self.listYouTube)
        print("youLrcUpdateTimeOffset():", self.youLrcTimeOffset, "ext.write_to_pickle:",
              tmf.mm_ss(time.time() - start, rem='h'), "sec")  # 1.55 sec

        self.top.update()

    def youLrcUpdateBgColor(self, item, *_args):
        """ Time Offset has just been changed. """
        old_color = self.youLrcBgColor
        self.youLrcBgColor = self.youLrcBgColorVar.get()
        if self.youLrcBgColor.lower() != 'red' and \
                self.youLrcBgColor.lower() != 'green' and \
                self.youLrcBgColor.lower() != 'blue' and \
                self.youLrcBgColor.lower() != 'black' and \
                self.youLrcBgColor.lower() != 'yellow' and \
                self.youLrcBgColor.lower() != 'cyan' and \
                self.youLrcBgColor.lower() != 'magenta':
            print("Bad color:", self.youLrcBgColor, " | Keeping old:", old_color)
            self.youLrcBgColor = old_color
            self.youLrcBgColorVar.set(self.youLrcBgColor)
            self.top.update()
            return

        if old_color.lower() == 'yellow' and self.youLrcBgColor.lower() == 'yellow':
            return  # No point saving default

        if old_color.lower() == self.youLrcBgColor.lower():
            return  # Color not changed

        self.scrollYT.tag_remove(old_color.lower(), "1.0", "end")
        print("New color:", self.youLrcBgColor, " | Old color:", old_color)

        # Write new value to disk
        ndx = int(item)
        start = time.time()
        self.listYouTube[ndx]['lrc_color'] = self.youLrcBgColor
        fname = self.nameYouTube.replace(".csv", ".pickle")
        ext.write_to_pickle(fname, self.listYouTube)
        print("bg_focusout():", self.youLrcBgColor, "ext.write_to_pickle:",
              tmf.mm_ss(time.time() - start, rem='h'), "sec")  # 1.55 sec

        self.top.update()

    def youLrcDestroyFrame(self, *_args):
        """ Remove Frame for YouTube Video LRC (synchronized lyrics) """
        if self.youLrcFrame is None:
            return  # Frame hasn't been created yet

        # self.youLrcFrame.grid_remove()  # Remove LRC frame
        self.youLrcFrame.destroy()  # Destroy LRC frame
        self.youLrcFrame = None  # Reflect LRC frame is NOT mounted
        # Above: Quick and dirty speed test after 600 videos is remove slow?
        self.tree_frame.grid()  # Restore Treeview frame
        self.hasLrcForVideo = None
        self.youSetCloseButton()
        self.top.update_idletasks()

    def youLrcHighlightLine(self):
        """ Highlight LRC (synchronized lyrics) line based on progress """

        # Calculate progress
        # position = tmf.mm_ss(self.progressYouTube, rem='d')  # decisecond
        position = tmf.mm_ss(self.progressYouTube)  # Less distracting seconds
        self.youProLrcVar.set("Progress: " + position)
        progress = self.progressYouTube + self.youLrcTimeOffset
        progress = 0.0 if progress < 0.0 else progress
        if self.progressYouTube and \
                self.progressYouTube == self.progressLastYouTube:
            self.youPrint("Video stuck? self.progressYouTube:",
                          self.progressYouTube)
        self.progressLastYouTube = self.progressYouTube

        # Find line matching progress
        last_ndx = len(self.listLrcLines) - 1
        for i, line in enumerate(self.listLrcLines):
            line_time, line_text = self.youLrcParseLine(line, i)
            # if i == 4:
            #    print(line_time, line_text)
            if i < last_ndx:
                next_line = self.listLrcLines[i + 1]
                next_time, _next_text = \
                    self.youLrcParseLine(next_line, i + 1)
            else:
                next_time = 9999999999999.9

            if line_time is None or next_time is None:
                continue  # Cannot test None

            if not line_time < progress < next_time:
                continue  # Line is the wrong time

            if i == self.ndxLrcCurrentLine:
                return  # index hasn't changed
            self.ndxLrcCurrentLine = i

            # print("New lyrics line:", line_text)
            # Remove pattern green for all
            # Apply pattern green for active line
            try:
                self.scrollYT.tag_remove(
                    self.youLrcBgColor.lower(), "1.0", "end")
            except tk.TclError:  # Oct 22/23 - 8:45pm
                # Working fine for week until housekeeping added
                self.youPrint("ERROR self.scrollYT.tag_remove()")

            two_before = i - 1 if i > 2 else 1
            two_before = str(two_before) + ".0"
            # Start highlight 1 char in so gutter isn't highlighted
            text_start = str(i + 1) + ".0+1c"  # start line + 1 for gutter
            text_end = str(i + 2) + ".0-1c"  # next line - 1 char = end line

            # TODO: More efficient using self.scrollYT.tag_add
            try:
                self.scrollYT.highlight_pattern(
                    "  " + line_text + "  ", self.youLrcBgColor.lower(),
                    start=text_start, end=text_end)
            except tk.TclError:  # Oct 22/23 - 8:45pm
                # Working fine for week until housekeeping added
                self.youPrint("ERROR self.scrollYT.highlight_pattern()")

            # https://stackoverflow.com/a/62765724/6929343
            self.scrollYT.see(text_start)  # Ensure highlighted line is visible
            self.top.update_idletasks()  # 2023-12-10 - Required before dlineinfo()
            # Prevent scrolling down to bottom.
            two_bbox = self.scrollYT.dlineinfo(two_before)  # bbox=[L,T,R,B]
            '''


            '''
            if two_bbox:
                # Scroll to top pixel of two lines before highlighted lyric line
                self.scrollYT.yview_scroll(two_bbox[1], 'pixels')
            else:
                self.youPrint("youLrcHighlightLine() two_bbox is NoneType!",
                              two_before, nl=True, lv=0)
                print("dict['name']:", self.dictYouTube.get('name', None))
                print("Video No.   :", self.listYouTubeCurrIndex + 1,
                      " | line_time   :", line_time)
                print("text_start  :", text_start, " | line_text:", line_text)

    def youLrcParseLine(self, line, ndx=None):
        """ Split line into seconds float and lyrics text
            ['[length:03:51.71]',
             '[re:www.megalobiz.com/lrc/maker]',
             '[ve:v1.2.3]',
             '[00:00.01]Ooh, stop',
                ...
             '[03:37.20]Ooh'
            ]

        When ndx == None populating scroll box. Else get line time.
        """
        time_float = None
        lyrics_text = None

        try:
            parts = line.split(']', 1)  # split "[00:00.00] Blah blah" in two
            time_str = parts[0].lstrip('[')
            colon_count = time_str.count(":")
            # Trap metadata which contains text instead of time
            contains_text = re.search('[a-zA-Z]', time_str)
            # print("colon_count:", colon_count, parts)
            if colon_count and not contains_text:
                time_float = tmf.get_sec(time_str)
        except IndexError:
            parts = None
            pass  # Could be a blank line

        try:
            lyrics_text = parts[1]
            if len(lyrics_text) == 0:
                # Scroll through Metadata Tags prior to first lyrics line
                if ndx is not None and self.youFirstLrcTimeNdx is not None and \
                        ndx < self.youFirstLrcTimeNdx:
                    # Calculate metadata tag artificial time
                    step = self.youFirstLrcTime / self.youFirstLrcTimeNdx
                    # time_float = step * (ndx + 1)
                    time_float = step * ndx  # 2023-11-25 17:55
                    time_float = float(time_float)  # just in case
                    lyrics_text = self.youLrcParseMeta(line)  # For highlighting
                    # print("step:", step, "time_float:", time_float)
        except IndexError:
            # Blank line
            # print("\nIndexError:", line)
            pass

        return time_float, lyrics_text

    @staticmethod
    def youLrcParseMeta(line):
        """ Pretty format LRC metadata

            [ar:Lyrics artist]
            [al:Album where the song is from]
            [ti:Lyrics (song) title]
            [au:Creator of the Songtext]
            [length:How long the song is]
            [by:Creator of the LRC file]
            [offset:+/- Overall timestamp adjustment in milliseconds, + shifts time up,
                - shifts down i.e. a positive value causes lyrics to appear sooner,
                a negative value causes them to appear later]
            [re:The player or editor that created the LRC file]
            [ve:version of program]
        """
        meta_dict = {"ar": "Artist",
                     "al": "Album",
                     "ti": "Song Title",
                     "au": "Composer",
                     "length": "Length",
                     "by": "LRC Creator",
                     "offset": "Timestamp adjustment in milliseconds",
                     "re": "LRC App",
                     "ve": "LRC App Version"}
        fmt_line = line
        stripped = fmt_line.strip()
        if len(stripped) < 2:
            # print("len(stripped):", len(stripped))
            return fmt_line
        if not stripped[0] == "[" or not stripped[-1] == "]":
            # print("stripped[0]:", stripped[0], "stripped[-1]:", stripped[-1])
            return fmt_line
        fmt_line = stripped.lstrip("[").rstrip("]")
        parts = fmt_line.split(":", 1)

        try:
            key = parts[0]
            value = parts[1].strip()
            tag = meta_dict.get(key.lower(), key)
            # print("key:", key, " | value:", value, " | tag:", tag)
            fmt_line = tag + ": " + value
            return fmt_line
        except IndexError:
            return fmt_line

    def buildYouTubeDuration(self):
        """ Build progress bar under self.you_tree  """
        s = ttk.Style()
        s.theme_use("default")
        # https://stackoverflow.com/a/18140195/6929343
        s.configure("TProgressbar", thickness=6)  # Thinner bar
        self.youProVar = tk.DoubleVar()  # Close"
        self.youProBar = ttk.Progressbar(
            self.you_btn_frm, style="TProgressbar", variable=self.youProVar,
            length=1000)
        # https://stackoverflow.com/a/4027297/6929343
        self.youProBar.grid(row=0, column=1, padx=20, pady=30, sticky=tk.NSEW)
        self.you_btn_frm.pack_slaves()

    def resetYouTubeDuration(self):
        """ Set duration fields for a new song.
            The variable self.durationYouTube is set by youCurrentIndex()
        """

        now = time.time()  # DRY - Four lines repeated
        self.timeForwardYouTube = now
        self.timeLastYouTube = now
        self.progressYouTube = 0.0
        self.youPlayerSink = None  # Force Audio Sink read
        self.youPlayerCurrText = "?"  # Force button text & tooltip setup

    def updateYouTubeDuration(self):
        """ Query YouTube duration and update progress bar.
            If self.isViewCountBoost active then click next video.

            If errors occur, first step rebuild mserve playlists with:
              cd ~/.local/share/mserve/YoutubePlaylists
              rm <PLAYLIST NAME>.csv
              rm <PLAYLIST NAME>.private
              Start mserve, view <PLAYLIST NAME> and select "Smart Play All".
              If playlist doesn't rebuild then also use:
                  rm <PLAYLIST NAME>.pickle

        """
        '''
            "How often does YouTube update view count?
            Though YouTube doesn't publish this information,
            we know that it updates views approximately every
            24 to 48 hours. It does not update views instantly.
            Apr 13, 2021"

2024-01-23-05:01 - START Bombs 6:00-109, 17:29-219, 18:28-329, 19:26-439
2024-01-23-19:19 - Chill 6,050+323 Rock 25,585+462 Bombs 160+0 Gangs 3,480+17
2024-01-23-19:27 - START Gangs 6:00-339, 2024-01-24-19:37-681, 06:05-1,023
2024-01-24-05:59 - self.you_tree.see(str(you_tree_iid_int)) tcl error: 355

2024-01-25-05:00 - Chill 6,050+0 Rock 25,585+0 Bombs 601+441 Gangs 3,762+282
2024-01-25-19:35 - Gangster Skipped: 1364 (The day the music died)
2024-01-30-18:39 - Chill 5,849-201 Rock 25,594+9 Bombs 672+71 Gangs 3,641-121
            Currently only subscriber to channel but just now told another.

===============================================================================

        '''
        if self.durationYouTube == 0.0:
            self.youPrint("updateYouTubeDuration() video duration is ZERO!")
            return  # Can't divide by zero

        try:
            # CPU load = 0.00641703605652
            time_video = self.webDriver.execute_script(
                "return document.getElementsByTagName('video')[0].currentTime;")
        except Exception as err:
            print("updateYouTubeDuration() 'video[0].currentTime' not found!")
            print(err)
            time_video = 0.0

        # Over 45 seconds and view count speed boost active?
        if time_video >= 31.0 and self.isViewCountBoost:
            self.youPlayNext()
            # if not self.youPlayNext():
            #    print("self.isViewCountBoost TURNED OFF!")
            #    self.isViewCountBoost = None

        if time_video > 0.0:
            self.progressYouTube = time_video
        percent = float(100.0 * self.progressYouTube / self.durationYouTube)
        self.youProVar.set(percent)
        self.youProBar.update_idletasks()

    def youPlayNext(self):
        """ Play next video in YouTube Playlist.
            Called with Video Count Speed Boost is active. """
        now = time.time()
        if self.youViewSkippedTime != 0.0 and \
                now - self.youViewSkippedTime < 20.0:
            # TODO: What about deleted, private & age restricted videos?
            self.youPrint("Last video skipped < 20 seconds ago.",
                          "Song index:", self.listYouTubeCurrIndex)
            return False

        self.youViewSkippedTime = now
        self.youViewCountSkipped += 1
        ''' Duplicates: #216/#215, #219/#218, #251/#250, #256/#255, #259/#258, 
            #263/#262, #274/#273, #288/#287, #340/#339. The duplicate repeats
            play in YT when clicking Next or <Shift>+N. '''
        curr_dict = self.listYouTube[self.listYouTubeCurrIndex]
        curr_link = curr_dict['link']
        self.youPrint("self.listYouTubeCurrIndex:", self.listYouTubeCurrIndex,
                      "curr_link:", curr_link, lv=9)
        for i, search_dict in enumerate(self.listYouTube):
            search_link = search_dict['link']
            if search_link == curr_link:
                self.youPrint("i:", i, "search_link:", search_link, lv=9)
                if i == self.listYouTubeCurrIndex:
                    continue  # Don't compare to ourself
                if i < self.listYouTubeCurrIndex:
                    # Found original, so this is duplicate to skip.
                    self.youPrint("Skipping duplicate:", search_dict['name'], lv=1)
                    self.youSmartPlaySong(str(self.listYouTubeCurrIndex + 2))
                    # + 1 to convert to 1's index, + 1 for next song
                    # Not tested if duplicate is last song on playlist...
                    return

        actions = ActionChains(self.webDriver)
        actions.key_down(Keys.SHIFT)
        actions.send_keys('N')  # PLAY NEXT VIDEO
        actions.perform()
        if True is True:
            return True

        # OLD code to archive

        elem = self.webDriver.find_element_by_xpath(
            '//*[@class="ytp-next-button ytp-button"]')
        try:
            elem.click()  # survey can block next button
            return True
        except WebDriverException as err:
            title = "updateYouTubeDuration WebDriverException"
            text = str(err)
            message.ShowInfo(self.top, title, text, icon='error',
                             thread=self.get_thread)
            self.youPrint("updateYouTubeDuration WebDriverException:\n", err,
                          nl=True, lv=0)
            # Can't really do anything until user finishes survey or 'X' it
        return False

    def youUpdatePlayerButton(self, player_status):
        """ YouTube Music Player Status determines button text.
            1 = Music video is playing
            2 = Music video is paused
            otherwise ad playing or music player idle
        """
        if player_status == 1:
            # self.youPlayerPauseText = "❚❚ Pause"
            self.youSetPlayerButton(self.youPlayerPauseText)
        elif player_status == 2:
            # self.youPlayerPlayText = "▶  Play"
            self.youSetPlayerButton(self.youPlayerPlayText)
        else:
            # self.youPlayerNoneText = "?  None"
            self.youSetPlayerButton(self.youPlayerNoneText)

    def youSetPlayerButton(self, new):
        """ If changed, Set button player text and tool tip.
            Get Audio Sink.
        """
        if new == self.youPlayerCurrText:
            return  # No change from previous text

        self.youPlayerCurrText = new
        try:
            self.youPlayerButton.config(text=new)
            if "None" in new:
                self.tt.set_text(self.youPlayerButton, "Nothing can be done")
            if "Play" in new:
                self.tt.set_text(self.youPlayerButton, "Resume playing video")
            if "Pause" in new:
                self.tt.set_text(self.youPlayerButton, "Pause music video")
        except Exception as err:
            self.youPrint("youSetPlayerButton Exception:", err)

        # Set Audio Sink number (Done too many times in program?)
        self.youGetChromeSink()

    def youGetChromeSink(self):
        """ Get Audio Sink.
            There is often two sinks for Chrome and the last is set
            The first is returned.

        2025-02-26 REVIEW: Variable 'second' is initially set to first sink

        """

        self.youPlayerSink = None
        second = self.youPlayerSink = None
        pav.get_all_sinks()
        for Sink in pav.sinks_now:
            if "Chrome" in Sink.name:
                self.youPlayerSink = Sink  # Audio Sink (sink_no_str)
                if self.youPlayerSink:
                    second = Sink
                # self.youPrint(self.youPlayerSink)
        return second

    def youTogglePlayer(self):
        """ Pause/Play Button has been clicked.
        """
        if self.youPlayerNoneText == self.youPlayerCurrText:
            # self.youPlayerButton = None  # Tkinter element mounted with .grid
            # self.youPlayerCurrText = None  # "None" / "Pause" / "Play" button
            # self.youPlayerNoneText = "?  None"  # Music Player Text options
            # self.youPlayerPlayText = "▶  Play"  # used when music player status
            # self.youPlayerPauseText = "❚❚ Pause"  # changes between 1 & 2
            return  # Can't divide by zero

        ''' YouTube toggle player with space bar '''
        actions = ActionChains(self.webDriver)
        actions.send_keys(' ')  # Send space
        actions.perform()

    # noinspection SpellCheckingInspection
    def youCurrentIndex(self):
        """ Get link URL from Browser address bar & return index

            Before play all:
                https://www.youtube.com/playlist?list=
                   PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM
            During play all:
                https://www.youtube.com/watch?v=bePCRKGUwAY&list=
                   PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM&index=15

            self.webDriver.refresh() will increment index beyond reality.
            Lookup video ID to get the real index.

            :returns: None = closing down. 0 = Not found, invalid link.
                      >=1 = playlist video 1's index
        """

        if not self.top:
            return None  # Closing down
        self.durationYouTube = 0.0
        link = self.youCurrentLink()
        try:
            currVideo = link.split("&list=")[0]
        except IndexError:
            print("youCurrentIndex() Playing video not in saved list")
            print("Unknown results and instability may occur.")
            return 0

        index0s = self.youTreeNdxByLink(currVideo, link)
        if index0s is None:
            print("youCurrentIndex() Playing video not in saved list")
            print("Unknown results and instability may occur.")
            print("currVideo not found:", currVideo)
            return 0

        # Found valid index
        duration_str = self.dictYouTube['duration']
        self.durationYouTube = float(tmf.get_sec(duration_str))
        index1s = int(index0s) + 1
        return index1s

    # noinspection SpellCheckingInspection
    def youUrlIndex(self, url=None):
        """ Get link URL from Browser address bar & return index

            Before play all:
                https://www.youtube.com/playlist?list=
                   PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM
            During play all:
                https://www.youtube.com/watch?v=bePCRKGUwAY&list=
                   PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM&index=15

            self.webDriver.refresh() will increment index beyond reality.
            Lookup video ID to get the real index.

            :returns: None = closing down. 0 = Not found, invalid link.
                      >=1 = playlist video 1's index
        """

        if url:
            link = url  # Used passed link
        else:
            link = self.youCurrentLink()  # Get address bar URL link
        try:
            currIndex = int(link.split("&index=")[1])
            ''' Duplicates: #216/#215, #219/#218, #251/#250, #256/#255, #259/#258, 
                #263/#262, #274/#273, #288/#287, #340/#339. The duplicate repeats
                play in YT when clicking Next or <Shift>+N. '''
            return currIndex
        except IndexError:
            if link:
                try:
                    playlist = link.split("&list=")[1]
                    return playlist
                except IndexError:
                    self.youPrint("ERROR #2 on link = youUrlIndex()")  # End list
                    return None

        self.youPrint("ERROR #1 on link = youUrlIndex()")  # Never prints?
        return None

    # noinspection SpellCheckingInspection
    def youCurrentVideoId(self):
        """ Get link URL from Browser address bar & return Video ID

            Before play all:
                https://www.youtube.com/playlist?list=
                   PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM
            During play all:
                https://www.youtube.com/watch?v=bePCRKGUwAY&list=
                   PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM&index=15

        """
        if not self.top:
            return None  # Closing down

        link = self.youCurrentLink()
        try:
            currVideo = link.split("&list=")[0]
            currVideo = currVideo.split("/watch?v=")[1]
            return currVideo
        except IndexError:
            if link:
                try:
                    # return first video in playlist
                    play_dict = self.listYouTube[0]
                    link_name = play_dict['link']
                    currVideo = link_name.split("/watch?v=")[1]
                    return currVideo
                except IndexError:
                    print("ERROR #2 on link = getCurrentVideo()")
                    return None

        print("ERROR #1 on link = getCurrentVideo()")
        return None

    # noinspection SpellCheckingInspection
    def youCurrentLink(self):
        """ Get link URL from Browser address bar

            Before play all:
                https://www.youtube.com/playlist?list=
                   PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM
            During play all:
                https://www.youtube.com/watch?v=bePCRKGUwAY&list=
                   PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM&index=15
        """
        if not self.top:
            return None  # Closing down
        try:
            link = self.webDriver.current_url
            return link
        except Exception as err:
            print("Exception:", err)
            print("ERROR on link = self.webDriver.current_url")
            return None

    def youDriverClick(self, by, desc):
        """ Credit: https://itecnote.com/tecnote/
        python-wait-for-element-to-be-clickable-using-python-and-selenium/
        """
        start = time.time()
        wait = WebDriverWait(self.webDriver, GLO['YTV_DRIVER_WAIT'])
        by = by.upper()
        try:
            if by == 'XPATH':
                wait.until(EC.element_to_be_clickable((By.XPATH, desc))).click()
            if by == 'ID':
                wait.until(EC.element_to_be_clickable((By.ID, desc))).click()
            if by == 'LINK_TEXT':
                wait.until(EC.element_to_be_clickable((By.LINK_TEXT, desc))).click()
        except TimeoutException:
            print("\nClickable element not found!")
            toolkit.print_trace()
            return False
        return time.time() - start < 9.0

    def youGetPlayerStatus(self):
        """ Credit: https://stackoverflow.com/q/29706101/6929343

2023-12-08 Resume from suspend error:

  File "/home/rick/python/mserve.py", line 16128, in youSmartPlayAll
    self.youMonitorPlayerStatus(player_status, debug=False)
  File "/home/rick/python/mserve.py", line 17133, in youMonitorPlayerStatus
    player_status = self.youWaitMusicPlayer(debug=True)
  File "/home/rick/python/mserve.py", line 17255, in youWaitMusicPlayer
    player_status = self.youGetPlayerStatus()
  File "/home/rick/python/mserve.py", line 18042, in youGetPlayerStatus
    player_status = self.webDriver.execute_script(
AttributeError: 'NoneType' object has no attribute 'execute_script'

        """
        try:
            # Player status for accurate duration countdown
            player_status = self.webDriver.execute_script(
                "return document.getElementById('movie_player').getPlayerState()")
            return player_status
        except WebDriverException as _err:
            # WebDriverException: Message: javascript error: Cannot read
            #       properties of null (reading 'getPlayerState')
            #   (Session info: chrome=108.0.5359.124)
            #       (Driver info: chromedriver=108.0.5359.71
            #       (1e0e3868ee06e91ad636a874420e3ca3ae3756ac-refs/
            #       branch-heads/5359@{#1016}),
            #       platform=Linux 4.14.216-0414216-generic x86_64)
            # print("WebDriverException:", err)
            return None
        except AttributeError:
            #   File "/home/rick/python/mserve.py", line 16137, in youSmartPlayAll
            #     self.youMonitorPlayerStatus(player_status, debug=False)
            #   File "/home/rick/python/mserve.py", line 17141, in youMonitorPlayerStatus
            #     player_status = self.youWaitMusicPlayer(debug=False)
            #   File "/home/rick/python/mserve.py", line 17269, in youWaitMusicPlayer
            #     player_status = self.youGetPlayerStatus()
            #   File "/home/rick/python/mserve.py", line 18328, in youGetPlayerStatus
            #     player_status = self.webDriver.execute_script(
            # AttributeError: 'NoneType' object has no attribute 'execute_script'
            print("youGetPlayerStatus() self.webDriver is 'NoneType'")
            print("Was video paused at very start then resumed?")
            return None

    # noinspection SpellCheckingInspection
    def youGetMicroFormat(self):
        """ Rock Song # 10 is playing but Address URL shows # 11 expected.

        microformat:

        <div id="microformat" class="style-scope ytd-watch-flexy">
        <ytd-player-microformat-renderer
        class="style-scope ytd-watch-flexy">
        <!--css-build:shady--><!--css-build:shady-->
        <script type="application/ld+json"
        id="scriptTag" nonce="VKUa9bVN8W-_ltE725Jfgw"
        class="style-scope ytd-player-microformat-renderer">
        {
            "@context":"https://schema.org",
            "@type":"VideoObject",
            "description":"I wish I could ... My beautiful girl.",
            "duration":"PT288S",
            "embedUrl":"https://www.youtube.com/embed/mS8xDo-qM8w
                       ?list=PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM",
            "interactionCount":"21422290",
            "name":"City And Colour - The Girl (Lyrics)",
            "thumbnailUrl":["https://i.ytimg.com/vi/mS8xDo-qM8w/maxresdefault.jpg?
                          sqp=-oaymwEmCIAKENAF8quKqQMa8AEB-AG-B4AC0AWKAgwIABABGGU
                          gVShbMA8=&rs=AOn4CLBTqtLGNpEVXZ8uQBKGUfAZ7MkvnA"],
            "uploadDate":"2011-12-23",
            "genre":"Music",
            "author":"Fran Smyth"
        }
        </script> </ytd-player-microformat-renderer></div>

        """
        try:
            # Need wait until visible when playing random song
            wait = WebDriverWait(self.webDriver, 2)
            # Was waiting 10 seconds but that's way too long. Try 2 seconds
            id_name = 'microformat'  # _located
            # element = self.webDriver.find_element_by_id(id_name)
            element = wait.until(EC.presence_of_element_located((
                By.ID, id_name)))
        except WebDriverException as err:
            print(ext.t(short=True, hun=True),
                  "youGetMicroFormat() WebDriverException:\n", err)
            stat = self.youGetPlayerStatus()
            print(ext.t(short=True, hun=True), "self.youGetPlayerStatus():", stat)
            return None

        try:
            inner = element.get_attribute('innerHTML')
            dict_list = self.extract_dict(inner)
            video_id = None
            if len(dict_list) >= 1:
                inner_dict = dict_list[0]
                embed = inner_dict.get("embedUrl", None)
                '''
                "embedUrl":"https://www.youtube.com/embed/mS8xDo-qM8w
                       ?list=PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM",
                '''
                link = embed.split('?list=')[0]
                video_id = link.rsplit("/", 1)[1]
            else:
                self.youPrint("youGetMicroFormat() innerHTML:", inner, nl=True)
                stat = self.youGetPlayerStatus()
                self.youPrint("self.youGetPlayerStatus():", stat)
                """ PROBLEM TWO DICTIONARIES:
                    {
                    "@context":"https://schema.org",
                    "@type":"VideoObject",
                    "description":"Official music  .../QigvUc",
                    "duration":"PT222S",
                    "embedUrl":"https://www.youtube.com/embed/9SRxBTtspYM?list=PLthF248A1c69kNWZ9Q39Dow3S2Lxp74mF",
                    "interactionCount":"240630662",
                    "name":"Ariana Grande, Social House - boyfriend (Official Video)",
                    "thumbnailUrl":["https://i.ytimg.com/vi/9SRxBTtspYM/maxresdefault.jpg"],
                    "uploadDate":"2019-08-01",
                    "genre":"Music",
                    "author":"ArianaGrandeVevo",
                    "publication":
                        [{
                        "@type":"BroadcastEvent",
                        "isLiveBroadcast":true,
                        "startDate":"2019-08-02T04:00:09+00:00",
                        "endDate":"2019-08-02T04:05:47+00:00"
                        }]
                    }
               """
            return video_id

        except Exception as err:
            print(ext.t(short=True, hun=True),
                  "youGetMicroFormat() Exception:\n", err)
            stat = self.youGetPlayerStatus()
            print(ext.t(short=True, hun=True), "self.youGetPlayerStatus():", stat)
            return None

    # noinspection RegExpRedundantEscape
    @staticmethod
    def extract_dict(s):
        """ Extract all valid dicts from a string.
            https://stackoverflow.com/a/63850091/6929343
            Called by youGetMicroFormat()
        Args:
            s (str): A string possibly containing dicts.

        Returns:
            A list containing all valid dicts.

        """
        # REMOVE LIST WITH DICTIONARY (Publication)
        # https://stackoverflow.com/a/8784436/6929343
        s = re.sub(r'\[\{.+?\}\]', '"Deleted by mserve"', s)
        # ORIGINAL CODE
        results = []
        s_ = ' '.join(s.split('\n')).strip()
        exp = re.compile(r'(\{.*?\})')
        for i in exp.findall(s_):
            try:
                results.append(json.loads(i))
            except ValueError:
                pass  # JSON Python < 3.5
            except json.JSONDecodeError:
                pass  # JSON >= 3.5  https://stackoverflow.com/a/44714607/6929343
            except AttributeError:
                #   File "/home/rick/python/mserve.py", line 16387, in youMonitorPlayerStatus
                #     video_id = self.youGetMicroFormat()  # From mini-player script
                #   File "/home/rick/python/mserve.py", line 16753, in youGetMicroFormat
                #     dict_list = self.extract_dict(inner)
                #   File "/home/rick/python/mserve.py", line 16789, in extract_dict
                #     except json.JSONDecodeError:
                # AttributeError: 'module' object has no attribute 'JSONDecodeError'
                pass
        return results

    def youCheckAdRunning(self):
        """ NOTE: When ad starts playing it opens a new PulseAudio instance.
                  1) Turn down volume immediately
                  2) Test what happens when job is killed?

            NOTE: Player status will be "-1" while ad is running or "3" if ad
                  is starting. May also be "5" (in between songs in a playlist)

        :return: True if ad displaying, False if no ad displayed
        """
        try:
            # TODO Start Duration Countdown
            _ad = self.webDriver.find_element(
                By.CSS_SELECTOR, ".ytp-ad-duration-remaining")
            return True
        except (NoSuchElementException, WebDriverException):
            return False

    def youHousekeeping(self):
        """ YouTube Housekeeping.
            Respond to prompt: "Video paused. Continue Watching?"

                                ......                  "Yes"

        """
        element = None
        # try:  # element is never found so comment out to save time
        #    element = self.webDriver.find_element_by_xpath(
        #        "//*[contains(text(), 'Video paused. Continue Watching?')]")
        # except NoSuchElementException:
        #    element = None
        try:
            element2 = self.webDriver.find_element_by_id("confirm-button")
        except NoSuchElementException:
            element2 = None
        if not element and not element2:
            return

        # print("youHousekeeping() - Found element:", element,
        #      " | element2:", element2)
        # youHousekeeping() - Found element: None  | element2:
        #   <selenium.webdriver.remote.web element.WebElement
        #   (session="6ac4176d1ef05a453703aea114ac5541",
        #   element="0.16380191644441688-11")>
        if element2.is_displayed():
            # Initially element2 is not present. First time is present during
            # self.youWaitMusicPlayer() after 10 songs have played. Thereafter,
            # element2 is present during 1 minute check but is not displayed.
            # element2 is displayed for song #17. It is present every minute
            # until Song #20 and disappears during Song #21 which is first time
            # for MicroFormat is forced after 0.9 seconds. Song #30 gets confirm
            # when ad visible and player status -1 in endless loop.
            self.youPrint("youHousekeeping() - click ID: 'confirm-button'", lv=2, nl=True)
            stat = self.youGetPlayerStatus()  # Status = 2
            self.youPrint("Player Status BEFORE click:", stat, lv=2)
            element2.click()  # result1
            time.sleep(.33)  # Nov 6/23 was 1.0, try shorter time for Status
            stat = self.youGetPlayerStatus()  # Status = 1
            self.youPrint("Player Status AFTER click :", stat, "\n", lv=2)
            return
        '''
    <yt-button-renderer id="confirm-button" 
        class="style-scope yt-confirm-dialog-renderer" button-renderer="" 
        button-next="" dialog-confirm=""><!--css-build:shady--><yt-button-shape>
        <button class="yt-spec-button-shape-next yt-spec-button-shape-next--text 
        yt-spec-button-shape-next--call-to-action 
        yt-spec-button-shape-next--size-m" aria-label="Yes" title="" style="">

        <div class="yt-spec-button-shape-next__button-text-content">
        <span class="yt-core-attributed-string 
        yt-core-attributed-string--white-space-no-wrap" 
        role="text">Yes</span></div>

        <yt-touch-feedback-shape style="border-radius: inherit;">
        <div class="yt-spec-touch-feedback-shape 
            yt-spec-touch-feedback-shape--touch-response" aria-hidden="true">
            <div class="yt-spec-touch-feedback-shape__stroke" style=""></div>
            <div class="yt-spec-touch-feedback-shape__fill" style=""></div>
        </div>
        '''
        # if not self.youDriverClick("id", "confirm-button"):
        #    print("youHousekeeping(): Error clicking 'Yes' button")

        # youHousekeeping() - Found element: None
        #   element2: <selenium.webdriver.remote.web element.WebElement
        #   (session="394498a9a5db08d5b6dbd83e27591f34",
        #   element="0.951519416280243-15")>
        # youHousekeeping() - Found element: None
        #   element2: <selenium.webdriver.remote.web element.WebElement
        #   (session="394498a9a5db08d5b6dbd83e27591f34",
        #   element="0.951519416280243-15")>
        # Exception in Tkinter callback
        # Traceback (most recent call last):
        #   File "/usr/lib/python2.7/lib-tk/Tkinter.py", line 1540, in __call__
        #     return self.func(*args)
        #   File "/home/rick/python/mserve.py", line 15699, in <lambda>
        #     command=lambda: self.youSmartPlayAll())
        #   File "/home/rick/python/mserve.py", line 16316, in youSmartPlayAll
        #     self.youHousekeeping()
        #   File "/home/rick/python/mserve.py", line 17879, in youHousekeeping
        #     if not self.youDriverClick("id", "confirm-button"):
        #   File "/home/rick/python/mserve.py", line 17665, in youDriverClick
        #     wait.until(EC.element_to_be_clickable((By.ID, desc))).click()
        #   File "/usr/lib/python2.7/dist-packages/selenium/webdriver/support/wait.py", line 80, in until
        #     raise TimeoutException(message, screen, stacktrace)
        # TimeoutException: Message:

        return

    def youViewCountBoost(self, *_args):
        """ Toggle self.isViewCountBoost. """

        self.isViewCountBoost = not self.isViewCountBoost

        title = "30 second View Count Boost"
        text = \
            "View Count Boost active?: " + str(self.isViewCountBoost) + "\n" + \
            "Number of videos skipped: " + str(self.youViewCountSkipped) + "\n" + \
            "When View Count Boost is active, only the first 30 seconds" + "\n" + \
            "plays. This creates more view counts for YouTube Playlist.\n"

        self.youPrint(text, nl=True, lv=0)
        message.ShowInfo(self.top, title, text, 'left', thread=self.get_thread)

    def youSetDebug(self, *_args):
        """ Set Debug level (self.youDebug) for self.youPrint(level). """

        title = "Set YouTube Debug Level"

        text = \
            "Current Debug Level: " + str(self.youDebug) + "\n\n" + \
            "Print debug lines for the debug level and below:" + "\n\n" + \
            "0 = Nothing prints to console\n" + \
            "1 = Song numbers and initialization (Default)\n" + \
            "2 = Continue watching dialogs\n" + \
            "3 = Ad playing & player status\n" + \
            "4 = Video MicroFormat monitoring\n" + \
            "5 = Ad Volume up/down overrides\n" + \
            "6 = Multiple Audio Sinks when discovered\n" + \
            "7 = Selenium driver.back() / driver.forward()\n" + \
            "8 = Selenium query results\n" + \
            "9 = Detailed driver.back() / driver.forward()\n" + \
            "Enter single digit from '0' to '9' below\n\n"

        answer = message.AskString(
            self.top, thread=self.get_thread,  # update_display()
            title=title, text=text, icon="information")

        if answer.result != "yes":
            return False

        # print('answer.string:', answer.string)
        if len(answer.string) != 1:
            # TODO: ShowInfo that single digit from 0 to 7 is required.
            return False

        try:
            int_answer = int(answer.string)
        except Exception as err:
            print("self.youSetDebug() Exception:", err)
            return False

        self.youDebug = int_answer
        self.youPrint("Debug level set to:", self.youDebug, "\n", lv=0, nl=True)
        self.act_size = self.youDebug
        # Write history record from act_size
        self.save_act()
        return True

    def youPrint(self, *args, **kwargs):
        """ Print debug lines based on debug level (self.youDebug):
                0 = Nothing prints, except level=0
                1 = Song numbers and initialization (Default)
                2 = 1 and continue watching dialogs
                3 = 2 and Ad playing & player status
                4 = 3 and Video MicroFormat monitoring
                5 = 4 and Ad Volume up/down overrides
                6 = 5 and Multiple Audio Sinks when discovered
                7 = 6 and driver.back / driver.forward
        """
        # https://stackoverflow.com/a/37308684/6929343
        level = kwargs.pop('level', 1)  # 1 is default level (old name)
        lv = kwargs.pop('lv', 1)  # New level= being converted
        if lv != 1:
            level = lv
        nl = kwargs.pop('nl', False)  # New line before?

        if self.youDebug >= level:
            if nl:
                print()
            print(ext.t(short=True, hun=True), *args)

    def youTreeNdxByLink(self, link_search, link):
        """ Highlight row black & gold as second entry (see 2 below + 1 before)
            If same link used twice in playlist the first will be highlighted.

            https://www.youtube.com/playlist?list=PLthF248A1c68TAKl5DBskfJ2fwr1sk9aM
            https://www.youtube.com/watch?v=HAQQUDbuudY


        """
        index1 = self.youUrlIndex(url=link)
        try:
            index1 = int(index1)
            return index1 - 1
        except (ValueError, TypeError):
            pass  # No '&index=' at end of address bar url link
        for i, self.dictYouTube in enumerate(self.listYouTube):
            if link_search == self.dictYouTube['link']:
                return i

        self.youPrint("youTreeNdxByLink():", link_search,
                      "NOT FOUND!", nl=True)
        return None

    def youTreeCopyLink(self, item):
        """ Copy Single Song link to clipboard. """
        ndx = int(item)
        self.youTreeSharedCopyText(self.listYouTube[ndx]['link'])

    def youTreeCopySearchLrc(self, item):
        """ Copy Single Song Name with search prefix to clipboard. """
        ndx = int(item)
        search_name = "synchronized lyrics lrc " + self.listYouTube[ndx]['name']
        self.youTreeSharedCopyText(search_name)

    def youTreeCopyAll(self):
        """ Copy Playlist link to clipboard. """
        self.youTreeSharedCopyText(self.act_description)

    def youTreeSharedCopyText(self, text):
        """ Copy text to clipboard. """
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.update()
        r.destroy()
        title = "Copy Complete."
        msg = "The following was copied to the Clipboard:\n\n"
        msg += text
        # message.ShowInfo(self.top, title, msg,
        #                 thread=self.get_thread)
        self.info.cast(title + "\n\n" + msg)

    def youTreePasteLrc(self, item):
        """ Paste Song's LRC (LyRiCs) to clipboard. """
        clip_text = self.youTreeSharedPaste()
        # TODO: validate [mm:ss.hh] 'blah blah' exists at least 10 times?

        # Write new LRC to disk
        ndx = int(item)
        start = time.time()
        self.listYouTube[ndx]['lrc'] = clip_text
        fname = self.nameYouTube.replace(".csv", ".pickle")
        ext.write_to_pickle(fname, self.listYouTube)
        print("youTreePasteLrc() ext.write_to_pickle:",
              tmf.mm_ss(time.time() - start, rem='h'), "sec")  # 1.55 sec
        #  New file self.lrcYouTube list[ list[], list[]... list[] ]?

        # Strip "\n\n" + old lyrics line 1 and insert new "\n\n" lyrics line 1.
        all_values = self.you_tree.item(item)['values']
        song_name = all_values[0].split("\n\n")[0]
        lrc = self.listYouTube[ndx].get('lrc', None)
        if lrc:
            lrc_list = lrc.splitlines()
            song_name += "\n\n" + lrc_list[0]  # first lrc line into treeview
            print("append lyrics[0]:", song_name)
        self.you_tree.item(item, values=(song_name,))
        self.you_tree.update_idletasks()

    def youTreeViewLrc(self, item):
        """ View Song's LRC (LyRiCs). """

        # Verify LRC exists in dictionary
        ndx = int(item)
        result = self.listYouTube[ndx].get('lrc', None)
        title = "View LRC № " + str(int(item) + 1)
        if result is None:
            text = "LRC not found!"
            message.ShowInfo(self.top, title, text,
                             thread=self.get_thread)
            return

        message.ShowInfo(self.top, title, result,
                         thread=self.get_thread)

    def youTreeDeleteLrc(self, item):
        """ Delete Song's LRC (LyRiCs).
            Confirm intent then delete.
        """

        # Delete old LRC from disk
        ndx = int(item)
        start = time.time()

        # Verify LRC exists in dictionary
        result = self.listYouTube[ndx].get('lrc', None)
        title = "Delete LRC № " + str(int(item) + 1)
        if result is None:
            text = "LRC not found!"
            message.ShowInfo(self.top, title, text,
                             thread=self.get_thread)
            return

        try:
            result = self.listYouTube[ndx].get('lrc', None)
            del self.listYouTube[ndx]['lrc']
            _text = "LRC successfully deleted"
        except KeyError:
            self.youPrint("KeyError no LRC in dictionary")
            _text = "LRC not found!"
            return

        if result is not None:
            # If None the key didn't exist
            fname = self.nameYouTube.replace(".csv", ".pickle")
            ext.write_to_pickle(fname, self.listYouTube)
            print("youTreeDeleteLrc() ext.write_to_pickle:",
                  tmf.mm_ss(time.time() - start, rem='h'), "sec")  # 1.55 sec

        # Strip "\n\n" + old lyrics line 1 and insert new "\n\n" lyrics line 1.
        all_values = self.you_tree.item(item)['values']
        song_name = all_values[0].split("\n\n")[0]
        lrc = self.listYouTube[ndx].get('lrc', None)
        if lrc:
            lrc_list = lrc.splitlines()
            song_name += "\n\n" + lrc_list[0]  # first lrc line into treeview
            print("append lyrics[0]:", song_name)
        self.you_tree.item(item, values=(song_name,))
        self.you_tree.update_idletasks()

    def youTreeSharedPaste(self):
        """ Read clipboard. """
        r = tk.Tk()
        r.withdraw()
        # r.clipboard_clear()
        try:
            c = r.clipboard_get()
        except tk.TclError:
            c = None  # https://stackoverflow.com/a/43328523/6929343
        r.update()
        r.destroy()
        title = "Paste Complete."
        text = "The following was read from the Clipboard:\n\n"
        text += c
        # message.ShowInfo(self.top, title, text,
        #                 thread=self.get_thread)
        self.info.cast(title + "\n\n" + text)
        return c

    @staticmethod
    def youTreeMouseWheel(event):
        """ Mousewheel scroll defaults to 5 units, but tree has 4 images """
        if event.num == 4:  # Override mousewheel scroll up
            event.widget.yview_scroll(-4, "units")  # tree = event.widget
            return "break"  # Don't let regular event handler do scroll of 5
        if event.num == 5:  # Override mousewheel scroll down
            event.widget.yview_scroll(4, "units")  # tree = event.widget
            return "break"  # Don't let regular event handler do scroll of 5

    def displayMusicIds(self):
        """ Read Music Id's from Playlist History record that was read using:
                self.act_music_ids = ['Target']  # Music Id's in play order
        """

        self.displayPlaylistCommonTop("MusicIds")

        # file control class
        view_ctl = FileControl(self.top, self.info)
        self.photosYouTube = []
        toolkit.wait_cursor(self.top)  # 16.04 "watch" / 18.04 "clock" cursor

        for i, music_id in enumerate(self.act_music_ids):
            if not self.top:
                return False  # top window closed
            d = sql.music_get_row(music_id)
            if not d:
                print("Invalid SQL music ID:", music_id)
                continue

            os_filename = PRUNED_DIR + d['OsFileName']
            view_ctl.new(os_filename)  # Declaring new file populates metadata

            # TODO: Image needs to be pre-stored for speed view_ctl
            #       get_artwork should pad edges when rectangle
            #       im = resized_art (rectangle), image = original art (square)
            photo, im, original = view_ctl.get_artwork(320, 180)
            if not self.top:
                return False  # top window closed

            if im is None:
                original = img.make_image(NO_ART_STR,
                                          image_w=1200, image_h=1200)
                im = original.resize((320, 180), Image.ANTIALIAS)
                # photo = ImageTk.PhotoImage(im)  Not needed

            song_name = d['Title']
            song_name += "\n\n\tartist \t" + d['Artist']
            song_name += "\n\talbum \t" + d['Album']
            if d['FirstDate']:
                song_name += "\n\tyear \t" + sql.sql_format_value(d['FirstDate'])[:4]
            duration = tmf.mm_ss(d['Seconds'])  # Strip hours and fractions

            # Text Draw duration over image & place into self.photosYouTube[]
            self.displayPlaylistCommonDuration(im, duration)
            try:
                self.you_tree.insert('', 'end', iid=str(i), text="№ " + str(i + 1),
                                     image=self.photosYouTube[-1],
                                     value=(song_name,))
            except tk.TclError:
                # 2024-05-20 - Error when .top was X closed
                print(self.who + "displayMusicIds():",
                      "self.playlists.top NOT found!")
                self.reset()  # Too late to save geometry
                return False  # playlists.top destroyed
            self.you_tree.see(str(i))
            self.top.update_idletasks()
            thread = self.get_thread()  # repeated 3 times...
            if thread:
                thread()
            else:
                return False  # closing down...

        view_ctl.close()

        # Below is identical to displayYouTubePlaylist()
        self.top.config(cursor="")  # Reset mouse pointer/cursor to default
        self.displayPlaylistCommonBottom()


class Application(ClassCommonSelf, tk.Toplevel):
    """ tkinter main application window
        Dropdown menus File/Edit/View/Tools
        Treeview with columns image, name/alias/IP,
    """

    def __init__(self, master=None):
        """ ClassCommonSelf(): Variables used by all classes
        :param toplevel: Usually <None> except when called by another program.
        """
        ClassCommonSelf.__init__(self, "Application().")  # Define self.who

        global yt  # YouTube() class instance
        yt = YouTube()

        self.isActive = True  # Set False when exiting or suspending
        self.requires = ['ps', 'grep', 'xdotool', 'wmctrl']
        self.installed = []
        self.CheckDependencies(self.requires, self.installed)

        if not self.dependencies_installed:
            v1_print(_who, "Some Application() dependencies are not installed.")
            v1_print(self.requires)
            v1_print(self.installed)

        ''' TkDefaultFont changes default font everywhere except tk.Entry in Color Chooser '''
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=g.MON_FONT)
        text_font = font.nametofont("TkTextFont")  # tk.Entry fonts in Color Chooser
        text_font.configure(size=g.MON_FONT)
        ''' TkFixedFont, TkMenuFont, TkHeadingFont, TkCaptionFont, TkSmallCaptionFont,
            TkIconFont and TkTooltipFont - It is not advised to change these fonts.
            https://www.tcl-lang.org/man/tcl8.6/TkCmd/font.htm '''

        self.last_refresh_time = time.time()  # Refresh idle loop last entered time
        # Normal 1 minute delay to rediscover is shortened at boot time if fast start
        self.last_rediscover_time = time.time()  # Last analysis of `arp -a`
        if p_args.fast:
            # Allow 3 seconds to move mouse else start rediscover
            self.last_rediscover_time = time.time() - GLO['REDISCOVER_SECONDS'] + 3
        self.rediscover_done = True  # 16ms time slices until done.
        self.rediscover_row = 0  # Current row processed in Treeview
        self.tree = None  # Painted in populateDevicesTree()
        # Images used in populateDevicesTree() and/or other methods
        self.photos = None

        # Button Bar button images
        self.img_minimize = img.tk_image("taskbar_icon.png", 26, 26)
        self.img_sensors = img.tk_image("taskbar_icon.png", 26, 26)
        self.img_devices = img.tk_image("taskbar_icon.png", 26, 26)
        self.img_new_video = img.tk_image("taskbar_icon.png", 26, 26)
        self.img_mag_glass = img.tk_image("taskbar_icon.png", 26, 26)

        # Right-click popup menu images common to all devices
        self.img_turn_off = img.tk_image("taskbar_icon.png", 42, 26)
        self.img_turn_on = img.tk_image("taskbar_icon.png", 42, 26)
        self.img_up = img.tk_image("taskbar_icon.png", 22, 26)
        self.img_down = img.tk_image("taskbar_icon.png", 22, 26)  # Move down & Minimize
        self.img_close = img.tk_image("taskbar_icon.png", 26, 26)  # Also close button

        # Right-click popup menu images for Sony TV Picture On/Off
        self.img_picture_on = img.tk_image("taskbar_icon.png", 42, 26)
        self.img_picture_off = img.tk_image("taskbar_icon.png", 42, 26)

        # Right-click popup menu images for Bluetooth LED Light Strip
        self.img_set_color = img.tk_image("taskbar_icon.png", 26, 26)
        self.img_nighttime = img.tk_image("taskbar_icon.png", 26, 26)
        self.img_breathing = img.tk_image("taskbar_icon.png", 26, 26)
        self.img_reset = img.tk_image("taskbar_icon.png", 26, 26)

        ''' Toplevel window (self) '''
        tk.Toplevel.__init__(self, master)  # https://stackoverflow.com/a/24743235/6929343
        self.minsize(width=120, height=63)
        self.geometry('1200x700')
        self.configure(background="WhiteSmoke")
        self.rowconfigure(0, weight=1)  # Weight 1 = stretchable row
        self.columnconfigure(0, weight=1)  # Weight 1 = stretchable column
        app_title = "pimtube.py - YouTube Control"  # Used to find window ID further down
        self.title(app_title)
        self.btn_frm = None  # Used by buildButtonBar(), can be hidden by edit_pref

        ''' ChildWindows() moves children with toplevel and keeps children on top '''
        self.win_grp = toolkit.ChildWindows(self, auto_raise=False)

        ''' Tooltips() - if --silent argument, then suppress error printing '''
        print_error = False if p_args.silent else True
        self.tt = toolkit.ToolTips(print_error=print_error)

        ''' Set program icon in taskbar. '''
        img.taskbar_icon(self, 64, 'white', 'green', 'yellow', char='yt')

        ''' Preferences Notebook '''
        self.notebook = self.edit_pref_active = None

        ''' Big Number Calculator and Delayed Textbox (dtb) are child windows '''
        self.calculator = self.calc_top = self.dtb = None

        ''' Display cmdEvents (toolkit.CustomScrolledText) as child window 
            Also used to display Bluetooth devices and Breathing stats 
        '''
        self.event_top = self.event_scroll_active = self.event_frame = None
        self.event_btn_frm = None

        ''' Save Toplevel OS window ID for minimizing window '''
        self.update_idletasks()  # Make visible for wmctrl. Verified needed 2025-02-13
        self.getWindowID(app_title)

        ''' File/Edit/View/Tools dropdown menu bars - Window ID required '''
        self.file_menu = self.edit_menu = self.view_menu = self.tools_menu = None
        self.buildDropdown()  # Build Dropdown Menu Bars after 'sm =' class declared

        ''' Create treeview with internet devices. '''
        self.populateDevicesTree()

        ''' When devices displayed show sensors button and vice versa. '''
        self.sensors_devices_btn = None
        self.sensors_btn_text = "Sensors"  # when Devices active
        self.devices_btn_text = "Devices"  # when Sensors active
        self.clipboard_btn = None  # Read video link from system clipboard
        self.new_video_btn = None  # Suspend button on button bar to control tooltip
        self.close_btn = None  # Close button on button bar to control tooltip
        self.main_help_id = "HelpNetworkDevices"  # Toggles to HelpSensors and HelpDevices
        self.usingDevicesTreeview = True  # Startup uses Devices Treeview
        self.buildButtonBar(self.sensors_btn_text)

        # Dropdown Menu Bars after 'sm =' and buildButtonBar() sets button text
        self.enableDropdown()

        # Experiments to delay rediscover when there is GUI activity
        self.minimizing = False  # When minimizing, override focusIn()
        self.bind("<FocusIn>", self.focusIn)  # Raise windows up
        self.bind("<Motion>", self.Motion)  # On motion reset rediscovery timer

        self.last_motion_time = GLO['APP_RESTART_TIME']

        # Monitors and window positions when un-minimizing
        self.monitors = self.windows = []  # List of dictionaries

        # Assign this Application() instance to the YouTube() instance self.app
        yt.app = self

        # 2025-03-08 Temporary Open Selenium Tests
        self.newVideo()  # Prompt for initial first video

        while self.refreshApp():  # Run forever until quit
            pass

    def getWindowID(self, title):
        """ Use wmctrl to get window ID in hex and convert to decimal for xdotool """
        _who = self.who + "getWindowID():"
        GLO['WINDOW_ID'] = None  # Integer HomA OS Window ID
        v2_print(_who, "search for:", title)

        if not self.CheckInstalled('wmctrl'):
            v2_print(_who, "`wmctrl` is not installed.")
            return
        if not self.CheckInstalled('xdotool'):
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

        v2_print(_who, "GLO['WINDOW_ID']:", GLO['WINDOW_ID'])
        if GLO['WINDOW_ID'] is None:
            v0_print(_who, "ERROR `wmctrl` could not find Window.")
            v0_print("Search for title failed: '" + title + "'.\n")

    def buildDropdown(self):
        """ Build dropdown Menu bars: File, Edit, View & Tools """

        def ForgetPassword():
            """ Clear sudo password for extreme caution """
            GLO['SUDO_PASSWORD'] = None  # clear global password in homa
            command_line_list = ["sudo", "-K"]  # clear password in linux
            self.runCommand(command_line_list)
            self.enableDropdown()

        mb = tk.Menu(self)
        self.config(menu=mb)

        ''' Option names are referenced for enabling and disabling.
            Before changing an "option name", search "option name" occurrences. '''

        # File Dropdown Menu
        self.file_menu = tk.Menu(mb, tearoff=0)

        # "Rediscover now" - argument count error: lambda _:
        self.file_menu.add_command(label="Rediscover now", font=g.FONT,
                                   underline=0, state=tk.DISABLED,
                                   command=lambda: self.Rediscover(auto=False))
        self.file_menu.add_separator()

        if GLO['WINDOW_ID'] is not None:
            # xdotool and wmctrl must be installed for Minimize button
            self.file_menu.add_command(label="Minimize", font=g.FONT, underline=0,
                                       command=self.minimizeApp, state=tk.NORMAL)

        self.file_menu.add_command(label="New video", font=g.FONT, underline=0,
                                   command=self.newVideo, state=tk.DISABLED)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", font=g.FONT, underline=1,
                                   command=self.exitApp, state=tk.DISABLED)

        mb.add_cascade(label="File", font=g.FONT, underline=0, menu=self.file_menu)

        # Edit Dropdown Menu
        self.edit_menu = tk.Menu(mb, tearoff=0)
        self.edit_menu.add_command(label="Preferences", font=g.FONT, underline=0,
                                   command=self.Preferences, state=tk.NORMAL)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Monitor volume", underline=0,
                                   font=g.FONT, state=tk.DISABLED,
                                   command=self.exitApp)

        mb.add_cascade(label="Edit", font=g.FONT, underline=0, menu=self.edit_menu)

        # View Dropdown Menu
        self.view_menu = tk.Menu(mb, tearoff=0)
        self.view_menu.add_command(label="Discovery timings", font=g.FONT, underline=10,
                                   command=self.DisplayTimings, state=tk.DISABLED)
        self.view_menu.add_command(label="Discovery errors", font=g.FONT, underline=10,
                                   command=self.DisplayErrors, state=tk.DISABLED)

        mb.add_cascade(label="View", font=g.FONT, underline=0, menu=self.view_menu)

        # Tools Dropdown Menu
        self.tools_menu = tk.Menu(mb, tearoff=0)
        self.tools_menu.add_command(label="Big number calculator", font=g.FONT,
                                    underline=0, command=self.OpenCalculator,
                                    state=tk.DISABLED)
        self.tools_menu.add_command(label="Timer " + str(GLO['TIMER_SEC']) + " seconds",
                                    font=g.FONT, underline=0,
                                    command=lambda: self.resumeWait(timer=GLO['TIMER_SEC']))
        self.tools_menu.add_separator()

        self.tools_menu.add_command(label="Forget sudo password", underline=0,
                                    font=g.FONT, command=ForgetPassword, state=tk.DISABLED)
        self.tools_menu.add_command(label="Debug information", font=g.FONT,
                                    underline=0, command=self.exitApp,
                                    state=tk.DISABLED)
        mb.add_cascade(label="Tools", font=g.FONT, underline=0,
                       menu=self.tools_menu)

    def enableDropdown(self):
        """ Called from build_lib_menu() and passed to self.playlists to call.
            Also passed with lcs.register_menu(self.enableDropdown)
        :return: None """

        if not self.isActive:
            return

        ''' File Menu '''
        # During rediscovery, the "Rediscover now" dropdown menubar option disabled

        ''' Edit Menu '''
        # 2024-12-01 - Edit menu options not written yet

        ''' View Menu '''
        # Default to enabled

        if GLO['EVENT_ERROR_COUNT'] != 0:
            self.view_menu.entryconfig("Discovery errors", state=tk.NORMAL)
        else:
            self.view_menu.entryconfig("Discovery errors", state=tk.DISABLED)

        # If one child view is running, disable all child views from starting.
        if self.event_scroll_active:
            self.view_menu.entryconfig("Discovery timings", state=tk.DISABLED)
            self.view_menu.entryconfig("Discovery errors", state=tk.DISABLED)

        ''' Tools Menu '''
        self.tools_menu.entryconfig("Big number calculator", state=tk.NORMAL)
        self.tools_menu.entryconfig("Debug information", state=tk.DISABLED)

    def exitApp(self, *_args):
        """ <Escape>, X on window, 'Exit from dropdown menu or Close Button"""
        _who = self.who + "exitApp():"

        ''' Is it ok to stop processing? - Make common method...'''
        msg = None
        if self.dtb:  # Cannot Close when resume countdown timer is running.
            msg = "Countdown timer is running."
        if not self.rediscover_done:  # Cannot suspend during rediscovery.
            msg = "Device rediscovery is in progress for a few seconds."
        if msg:  # Cannot suspend when other jobs are active
            self.ShowInfo("Cannot Close now.", msg, icon="error")
            v0_print(_who, "Aborting Close.", msg)
            return

        # Need Devices treeview displayed to save ni.view_order
        if not self.usingDevicesTreeview:
            self.toggleSensorsDevices()  # Toggle off Sensors Treeview

        # Generate new ni.view_order list of MAC addresses
        order = []
        for item in self.tree.get_children():
            cr = TreeviewRow(self)
            cr.Get(item)
            order.append(cr.ytv_basename)

        self.win_grp.destroy_all(tt=self.tt)  # Destroy Calculator and Countdown

        self.isActive = False  # Signal closing down so methods return

        # urllib2.URLError: <urlopen error [Errno 111] Connection refused>
        try:
            yt.webDriver.quit()
        #except URLError as err:
        except:
            v0_print(_who, "err")

        ''' reset to original SAVE_CWD (saved current working directory) '''
        if SAVE_CWD != g.PROGRAM_DIR:
            v1_print("Changing from g.PROGRAM_DIR:", g.PROGRAM_DIR,
                     "to SAVE_CWD:", SAVE_CWD)
            os.chdir(SAVE_CWD)

        self.destroy()  # Destroy toplevel
        exit()  # exit() required to completely shut down app

    def minimizeApp(self, *_args):
        """ Minimize GUI Application() window using xdotool.
            2024-12-08 TODO: Minimize child windows (Countdown and Big Number Calc.)
                However, when restoring windows it can be on another monitor.
        """
        _who = self.who + "minimizeApp():"
        # noinspection SpellCheckingInspection
        command_line_list = ["xdotool", "windowminimize", str(GLO['WINDOW_ID'])]
        self.runCommand(command_line_list, _who)

    def focusIn(self, *_args):
        """ Window or menu in focus, disable rediscovery. Raise child windows above.
            NOTE: triggered two times so test current state for first time status.
            NOTE: When the right-click menu is closed it registers FocusOut and
                  toplevel registers focusIn again.
            NOTE: If preferences Notebook is active and countdown timer is started
                  the digits never appear and linux locks up totally. Mouse movement
                  can still occur but that is all. As of 2024-12-27.
        """

        if self.event_scroll_active and self.event_top:
            self.event_top.focus_force()
            self.event_top.lift()

        # 2024-12-28 Causes Xorg to freeze. Only mouse can move.
        # if self.edit_pref_active and self.notebook:
        #    self.notebook.focus_force()
        #    self.notebook.lift()

        if self.calculator and self.calc_top:
            self.calc_top.focus_force()
            self.calc_top.lift()

        if self.dtb and self.dtb.mounted is True:
            self.dtb.msg_top.focus_force()
            self.dtb.msg_top.lift()

    def Motion(self, *_args):
        """ Window or menu had motion, reset last rediscovery time.

            See: https://www.tcl.tk/man/tcl8.4/TkCmd/bind.htm#M15
        """
        self.last_motion_time = time.time()
        self.last_rediscover_time = self.last_motion_time

    def populateDevicesTree(self):
        """ Populate treeview using ni.Discovered[{}, {}...{}]
            Treeview IID is string: "0", "1", "2" ... "99"
        """
        _who = self.who + "populateDevicesTree():"

        ''' Treeview style is large images in cell 0 '''
        style = ttk.Style()
        style.configure("Treeview.Heading", font=(None, g.MED_FONT),
                        rowheight=int(g.LARGE_FONT * 2.2))  # FONT14 alias
        row_height = 200
        style.configure("Treeview", font=g.FONT14, rowheight=row_height,
                        background="WhiteSmoke", fieldbackground="WhiteSmoke")

        ''' Create treeview frame with scrollbars '''
        self.photos = []  # list of device images to stop garbage collection
        # Also once image placed into treeview row, it can't be read from the row.
        self.tree = ttk.Treeview(self, column=('name', 'attributes'),  # mac hidden
                                 selectmode='none', style="Treeview")

        self.update()  # Paint something before populating lag
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scroll = tk.Scrollbar(self, orient=tk.VERTICAL,
                                width=14, command=self.tree.yview)
        v_scroll.grid(row=0, column=1, sticky=tk.NS)
        self.tree.configure(yscrollcommand=v_scroll.set)

        # Right-click - reliable works on first click, first time, all the time
        self.tree.bind('<Button-3>', self.RightClick)  # Right-click

        # Oct 1, 2023 - MouseWheel event does NOT capture any events
        self.tree.bind("<MouseWheel>", lambda event: self.MouseWheel(event))
        # Button-4 is mousewheel scroll up event
        self.tree.bind("<Button-4>", lambda event: self.MouseWheel(event))
        # Button-5 is mousewheel scroll down event
        self.tree.bind("<Button-5>", lambda event: self.MouseWheel(event))

        # Setup column heading - #0, #1, #2 denotes the 1st, 2nd & 3rd, etc. columns
        self.tree.heading('#0', text='Video Image & Status')
        self.tree.heading('#1', text='Channel Name', anchor='center')
        self.tree.heading('#2', text='Video Title', anchor='center')
        self.tree.column('#0', width=GLO['TREE_COL0_WID'], stretch=False)
        self.tree.column('name', anchor='center', width=GLO['TREE_COL1_WID'], stretch=True)
        self.tree.column('attributes', anchor='center', width=GLO['TREE_COL2_WID'], stretch=True)

        # Give some padding between image and left border, between tree & scroll bars
        self.tree["padding"] = (10, 10, 10, 10)  # left, top, right, bottom

        # Treeview Row Colors
        self.tree.tag_configure('curr_sel', background='#004900',
                                foreground="White")  # Right click on row
        self.tree.tag_configure('highlight', background='LightSkyBlue',
                                foreground="Black")  # Mouse over row
        self.tree.tag_configure('normal', background='WhiteSmoke',
                                foreground="Black")  # Nothing special

        # Fade in/out Row: Black fg faded green bg to White fg dark green bg
        green_back = ["#93fd93", "#7fe97f", "#6bd56b", "#57c157", "#43ad43",
                      "#39a339", "#258f25", "#117b11", "#006700", "#004900"]
        green_fore = ["#000000", "#202020", "#404040", "#606060", "#808080",
                      "#aaaaaa", "#cccccc", "#dddddd", "#eeeeee", "#ffffff"]
        for i in range(10):
            self.tree.tag_configure('fade' + str(i), background=green_back[i],
                                    foreground=green_fore[i])  # Nothing special

    def buildButtonBar(self, toggle_text):
        """ Paint button bar below treeview.
            Minimize - Minimize window.
            Tree Toggle - Button toggles between show Sensors or show Devices.
            Suspend - Power off all devices and suspend system.
            Help - www.pippim.com/HomA.
            Close - Close HomA.
        """

        ''' self.btn_frm holds Application() bottom bar buttons '''
        self.btn_frm = tk.Frame(self)
        self.btn_frm.grid_rowconfigure(0, weight=1)
        self.btn_frm.grid_columnconfigure(0, weight=1)
        # When changing grid options, also change in self.Preferences()
        self.btn_frm.grid(row=99, column=0, columnspan=2, sticky=tk.E)

        '''
        2024-09-07 - Xorg or Tkinter glitch only fixed by reboot makes tk.Button
          3x wider and taller. Use ttk.Button which defaults to regular size.
          The 'font=' keyword is NOT supported in ttk.Button which uses -style.
        '''
        style = ttk.Style()
        # Credit: https://stackoverflow.com/a/62506279
        # style.theme_use("classic")

        style.map("C.TButton",  # mserve play_button() in build_play_btn_frm()
                  foreground=[('!active', 'Black'), ('pressed', 'White'),
                              ('active', 'Black')],
                  background=[('!active', 'Grey75'), ('pressed', 'ForestGreen'),
                              ('active', 'SkyBlue3')]  # lighter than DodgerBlue
                  )

        style.configure("C.TButton", font=g.MED_FONT)

        def device_button(row, column, txt, command, tt_text, tt_anchor, pic=None):
            """ Function to combine ttk.Button, .grid() and tt.add_tip() """
            # font=
            txt = toolkit.normalize_tcl(txt)  # Python 3 lose 🌡 (U+1F321)
            # above was python 3 short term fix, use an image for permanent fix
            if pic:
                widget = ttk.Button(self.btn_frm, text=" " + txt, width=len(txt) + 2,
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
            device_button(0, 0, "Minimize", self.minimizeApp,
                          "Quickly and easily minimize HomA.", "nw", self.img_minimize)

        # noinspection SpellCheckingInspection
        ''' 🌡 (U+1F321) Sensors Button  -OR-  🗲 (U+1F5F2) Devices Button '''
        if toggle_text == self.sensors_btn_text:
            text = "Show Temperatures and Fans."
            self.main_help_id = "HelpNetworkDevices"
            pic_image = self.img_sensors
        else:
            text = "Show Network Devices."
            self.main_help_id = "HelpSensors"
            pic_image = self.img_devices

        self.sensors_devices_btn = device_button(
            0, 1, toggle_text, self.toggleSensorsDevices,
            text, "nw", pic_image)

        ''' Video Link from clipboard U+1F5F2  🗲 '''
        self.clipboard_btn = device_button(
            # 0, 2, u"🗲 Suspend", self.Suspend,  # c = root.clipboard_get()
            0, 2, "Clipboard", self.getClipboard,
            "Read clipboard for YouTube video address.", "ne", self.img_new_video)

        ''' New Video Button U+1F5F2  🗲 '''
        self.new_video_btn = device_button(
            # 0, 2, u"🗲 Suspend", self.Suspend,
            0, 3, "New Video", self.newVideo,
            "Add a new YouTube video.", "ne", self.img_new_video)

        ''' Help Button - ⧉ Help - Videos and explanations on pippim.com
            https://www.pippim.com/programs/homa.html#Introduction '''
        help_text = "Open new window in default web browser for\n"
        help_text += "videos and explanations on using this screen.\n"
        help_text += "https://www.pippim.com/programs/homa.html#\n"
        # Instead of "Introduction" have self.help_id with "HelpSensors" or "HelpDevices"
        device_button(0, 4, "Help", lambda: g.web_help(self.main_help_id),
                      help_text, "ne", self.img_mag_glass)

        ''' ✘ CLOSE BUTTON  '''
        self.bind("<Escape>", self.exitApp)
        self.protocol("WM_DELETE_WINDOW", self.exitApp)
        self.close_btn = device_button(0, 5, "Exit", self.exitApp,
                                       "Exit HomA.", "ne", pic=self.img_close)

    def toggleSensorsDevices(self):
        """ Sensors / Devices toggle button clicked.
            If button text == "Sensors" then active sm.tree.
            If button text == "Devices" then active Applications.tree.

        """
        _who = self.who + "toggleSensorsDevices()"
        show_devices = show_sensors = False

        # Immediately get rid of tooltip
        self.tt.zap_tip_window(self.sensors_devices_btn)

        # Get current button state and toggle it for next time.
        if "Sensors" in self.sensors_devices_btn['text']:
            show_sensors = True
            self.sensors_devices_btn['text'] = toolkit.normalize_tcl(self.devices_btn_text)
            self.sensors_devices_btn['image'] = self.img_devices
            self.tt.set_text(self.sensors_devices_btn, "Show Network Devices.")
            self.main_help_id = "HelpSensors"
            self.usingDevicesTreeview = False
        elif "Devices" in self.sensors_devices_btn['text']:
            show_devices = True
            self.sensors_devices_btn['text'] = toolkit.normalize_tcl(self.sensors_btn_text)
            self.sensors_devices_btn['image'] = self.img_sensors
            self.tt.set_text(self.sensors_devices_btn, "Show Temperatures and Fans.")
            self.main_help_id = "HelpNetworkDevices"
            self.usingDevicesTreeview = True
        else:
            print("Invalid Button self.sensors_devices_btn['text']:",
                  self.sensors_devices_btn['text'])
            return

        self.enableDropdown()  # NORMAL/DISABLED options for view Sensors/Devices

        if show_sensors:
            self.tree.destroy()

        if show_devices:
            self.populateDevicesTree()

    def readClipboard(self):
        """ https://stackoverflow.com/a/64886943/6929343 """
        _who = self.who + "readClipboard():"

        r = tk.Tk()
        r.withdraw()
        try:
            return r.selection_get(selection="CLIPBOARD")  # Method 1
            # return r.clipboard_get()  # Method 2
        except tk.TclError:
            return None
        finally:
            r.destroy()

    def RightClick(self, event):
        """ Mouse right button click. Popup menu on selected treeview row.

            NOTE: Sub windows are designed to steal focus and lift however,
                  multiple right clicks will eventually cause menu to appear.
                  After selecting an option though, the green highlighting
                  stays in place because fadeOut() never runs.
        """
        item = self.tree.identify_row(event.y)
        help_id = "HelpRightClickMenu"

        if item is None:
            return  # Empty row, nothing to do
        try:
            _no = str(int(item) + 1)
        except ValueError:
            return  # Clicked on empty row

        def _closePopup(*_event):
            """ Close popup menu on focus out or selecting an option """
            cr.fadeOut(item)
            menu.unpost()
            self.last_refresh_time = time.time()

        ''' Highlight selected treeview row '''
        cr = TreeviewRow(self)  # Make current row instances
        cr.Get(item)  # Get current row
        # 320 ms row highlighting fade in
        cr.fadeIn(item)

        menu = tk.Menu(self)
        menu.bind("<FocusIn>", self.focusIn)
        menu.bind("<Motion>", self.Motion)
        menu.post(event.x_root, event.y_root)

        menu.add_command(label="Play Video", font=g.FONT, state=tk.NORMAL,
                         image=self.img_new_video, compound=tk.LEFT,
                         command=lambda: self.playVideo(cr))
        menu.add_separator()
        menu.add_command(label="Move Video Up", font=g.FONT, state=tk.DISABLED,
                         image=self.img_up, compound=tk.LEFT,
                         command=lambda: self.moveRowUp(cr))
        menu.add_command(label="Move Video Down", font=g.FONT, state=tk.DISABLED,
                         image=self.img_down, compound=tk.LEFT,
                         command=lambda: self.moveRowDown(cr))

        menu.add_separator()
        menu.add_command(label="Help", font=g.FONT, command=lambda: g.web_help(help_id),
                         image=self.img_mag_glass, compound=tk.LEFT)
        menu.add_command(label="Close menu", font=g.FONT, command=_closePopup,
                         image=self.img_close, compound=tk.LEFT)

        menu.tk_popup(event.x_root, event.y_root)

        menu.bind("<FocusOut>", _closePopup)

        # Enable moving row up and moving row down
        all_iid = self.tree.get_children()  # Get all item iid in treeview
        if item != all_iid[0]:  # Enable moving row up if not at top?
            menu.entryconfig("Move Video Up", state=tk.NORMAL)
        if item != all_iid[-1]:  # Enable moving row down if not at bottom?
            menu.entryconfig("Move Video Down", state=tk.NORMAL)

        # Reset last rediscovery time. Some methods can take 10 seconds to timeout
        self.last_refresh_time = time.time()
        menu.update()  # 2025-02-09 will this force title to appear?

    def playVideo(self, cr):
        """ Play YouTube Video. """
        _who = self.who + "playVideo():"
        v1_print(_who, "Playing Video:", cr.name_column)
        # sample 'link' var: https://www.youtube.com/watch?v=RGlZ4AlAOtg
        link = GLO['YTV_URL_PREFIX'] + GLO['YTV_URL_WATCH'] + cr.ytv_basename
        # Don't force 'link' into yt.currentWebpage because new videos can be inserted
        yt.playVideo(link, self.refreshApp)

    def moveRowUp(self, cr):
        """ Mouse right button click selected "Move Row Up". """
        _who = self.who + "moveRowUp():"
        if str(cr.item) == "0":
            v0_print(_who, "Already on first row. Cannot move up.")
            return

        dr = TreeviewRow(self)  # Destination treeview row instance
        dr.Get(str(int(cr.item) - 1))  # Get destination row values
        v1_print(_who, "Swapping rows:", cr.ytv_basename, dr.ytv_basename)
        dr.Update(cr.item)  # Update destination row with current row
        cr.Update(dr.item)  # Update current row with destination row

    def moveRowDown(self, cr):
        """ Mouse right button click selected "Move Row Down". """
        _who = self.who + "moveRowDown():"
        if int(cr.item) >= len(cr.tree.get_children()) - 1:
            v0_print(_who, "Already on last row. Cannot move down.")
            return

        dr = TreeviewRow(self)  # Destination treeview row instance
        dr.Get(str(int(cr.item) + 1))  # Get destination row values
        v1_print(_who, "Swapping rows:", cr.ytv_basename, dr.ytv_basename)
        dr.Update(cr.item)  # Update destination row with current row
        cr.Update(dr.item)  # Update current row with destination row

    def refreshApp(self, tk_after=True):
        """ Sleeping loop until need to do something. Fade tooltips. Resume from
            suspend. Rediscover devices.

            When a message is displayed, or input is requested, lost time causes
            a fake resume from suspend condition. After dialog boxes, use command:

                self.last_refresh_time = time.time()  # Refresh idle loop

        """

        _who = self.who + "refreshApp()"
        self.update_idletasks()
        if not self.winfo_exists():
            self.isActive = False
            return False  # self.close() has destroyed window

        ''' Is system shutting down? '''
        if killer.kill_now:
            v0_print('\nhoma.py refresh() closed by SIGTERM')
            self.exitApp()
            return False  # Not required because this point never reached.

        ''' Resuming from suspend? '''
        now = time.time()
        delta = now - self.last_refresh_time
        if delta > GLO['RESUME_TEST_SECONDS']:  # Assume > is resume from suspend
            v0_print("\n" + "= " * 4, _who, "Resuming from suspend after:",
                     tmf.days(delta), " =" * 4 + "\n")
            now = time.time()  # can be 15 seconds or more later
            GLO['APP_RESTART_TIME'] = now  # Reset app started time to resume time

        if not self.winfo_exists():  # Second check needed June 2023
            return False  # self.close() has set to None

        ''' Is there a TV to be monitored for power off to suspend system? '''
        # 2024-12-23 TODO: SETUP FOR SONY TV REST API

        ''' Always give time slice to tooltips - requires sql.py color config '''
        self.tt.poll_tips()  # Tooltips fade in and out. self.info piggy backing
        self.update()  # process pending tk events in queue

        if not self.winfo_exists():  # Second check needed June 2023
            self.isActive = False
            return False  # self.close() has set to None

        ''' Speedy derivative when called by CPU intensive methods. Also  
            called by waiting messages within first rediscovery process when
            a second rediscovery will break things. '''
        if not tk_after:
            if not self.winfo_exists():  # Second check needed June 2023
                self.isActive = False
            return self.isActive

        ''' Should not happen very often, except after suspend resume '''
        if self.last_refresh_time > now:
            v3_print(_who, "self.last_refresh_time: ",
                     tmf.days(self.last_refresh_time), " >  now: ", ext.h(now))
            now = self.last_refresh_time

        ''' Sleep remaining time until GLO['REFRESH_MS'] expires '''
        self.update()  # Process everything in tkinter queue before sleeping
        sleep = GLO['REFRESH_MS'] - int(now - self.last_refresh_time)
        sleep = sleep if sleep > 0 else 1  # Sleep minimum 1 millisecond
        if sleep == 1:
            v0_print(_who, "Only sleeping 1 millisecond")
        self.after(sleep)  # Sleep until next 60 fps time
        self.last_refresh_time = time.time()  # 2024-12-05 was 'now' too stale?

        ''' Wrapup '''
        return self.winfo_exists()  # Go back to caller as success or failure

    def getClipboard(self, *_args):
        """ Call readClipboard and parse contents for for legal link. 
            E.G. https://www.youtube.com/watch?v=RGlZ4AlAOtg video_dur: 3877.241

            If valid link, call getVideoDetails().
        """
        _who = self.who + "getClipboard():"

        yt.currentWebpage = self.readClipboard()

        if not self.validateURL(yt.currentWebpage):
            return

        self.insertVideo()  # Get video details and insert into treeview

    def validateURL(self, test_URL):
        """ Validate URL for legal link. 
            E.G. https://www.youtube.com/watch?v=RGlZ4AlAOtg video_dur: 3877.241
        """
        _who = self.who + "validateURL():"

        title = "Clipboard Error"
        if test_URL is None:
            msg = "Clipboard doesn't contain any text!"
            self.ShowInfo(title, msg, icon="error")
            v0_print(_who, title, msg)
            return False

        if not test_URL.startswith(GLO['YTV_URL_PREFIX']):
            msg = "Clipboard's URL Address must start with:\n"
            msg += GLO['YTV_URL_PREFIX']
            msg += "\n\nActual clipboard contents starts with:\n"
            msg += test_URL[:len(GLO['YTV_URL_PREFIX'])]
            self.ShowInfo(title, msg, icon="error")
            v0_print(_who, title, msg)
            return False

        if not GLO['YTV_URL_WATCH'] in test_URL:
            msg = "Clipboard's URL Address is missing " + GLO['YTV_URL_WATCH']
            self.ShowInfo(title, msg, icon="error")
            v0_print(_who, title, msg)
            return False

        #     https://www.youtube.com/watch?v=RGlZ4AlAOtg 'Copy Clean Link' instead of:
        #     https://www.youtube.com/watch?v=RGlZ4AlAOtg&pp=ygUOZGlhbG9ndWUgd29ya3M%3D
        if "&" in test_URL:
            parts = test_URL.split("&")
            test_URL = parts[0]

        try:
            video_basename = test_URL.split(GLO['YTV_URL_WATCH'])[1]
        except IndexError as err:
            v0_print(_who, err)
            return False

        if len(video_basename) != 11:
            msg = "Clipboard's YouTube video basename '" + video_basename
            msg += "',\nshould be 11 characters but is " + str(len(video_basename))
            msg += " characters.\n"
            self.ShowInfo(title, msg, icon="error")
            v0_print(_who, title, msg)
            return False

        tr = TreeviewRow(self)  # Make a dummy Treeview Row instance
        if tr.getIidForYtvBasename(video_basename):  # Is video already in treeview?
            msg = "YouTube video basename '" + video_basename
            msg += "' already exists.\n"
            self.ShowInfo(title, msg, icon="error")
            v0_print(_who, title, msg)
            return False

        return True

    def insertVideo(self):
        """ Get video details (including image) and insert into clipboard. """

        _who = self.who + "insertVideo():"
        title = "YouTube Error"
        if not yt.getVideoDetails():
            msg = "Video Details couldn't be obtained for:\n\n"
            msg += yt.currentWebpage
            self.ShowInfo(title, msg, icon="error")
            v0_print(_who, title, msg)
            return False

        if yt.downloadVideoImage(link=yt.currentWebpage):
            nr = TreeviewRow(self)  # Setup treeview row processing instance
            nr.New(yt)  # Setup new row
            nr.Add(len(self.tree.get_children()))  # Add new row
            self.tree.update_idletasks()  # Slow mode display each row.
        else:
            msg = "Video thumbnail image not found for:\n\n"
            msg += str(yt.currentWebpage)
            msg += "\n\nusing URL address of:\n\n"
            msg += str(yt.currentYtvImage)
            self.ShowInfo(title, msg, icon="error")
            v0_print(_who, title, msg)
            return False

        self.update()

        return True

    def newVideo(self, *_args):
        """ Prompt for new video link and add to treeview.
            Use this when getClipboard() complains about clipboard URL address.
        """

        _who = self.who + "newVideo():"

        if not yt.askVideoLink():  # TODO: Move method inside here (Application() class)
            return

        if not self.validateURL(yt.currentWebpage):
            return

        self.insertVideo()  # Get video details and insert into treeview

    def resumeWait(self, timer=None, alarm=True, title=None, abort=True):
        """ Wait x seconds for devices to come online. If 'timer' passed do a
            simple countdown.


            :param timer: When time passed it's a countdown timer
            :param alarm: When True, sound alarm when countdown timer ends
            :param title: Title when it's not countdown timer
            :param abort: Allow countdown timer to be ended early (closed)
        """

        _who = self.who + "resumeWait():"

        ''' Is countdown already running? '''
        if self.dtb:
            if self.dtb.mounted:  # Is textbox mounted yet?
                v0_print(_who, "Countdown already running.")
                self.dtb.msg_top.focus_force()
                self.dtb.msg_top.lift()
            return

        if timer is None:
            countdown_sec = GLO['RESUME_DELAY_RESTART']
            title = "Waiting after resume to check devices"
        else:
            countdown_sec = timer + 1  # 2024-12-01 - Losing 1 second on startup???
            if title is None:  # E.G. title="Scanning Bluetooth devices"
                title = "Countdown timer"
            if self.rediscover_done is not True:  # 2025-01-08
                return  # if rediscovery, machine locks up when timer finishes.
                # 2025-01-10 TODO: Disable timer menu option when rediscovery is
                #   running or when timer is already running.

        if countdown_sec <= 0:
            return  # No delay after resume

        tf = (None, 96)  # default font family with 96 point size for countdown
        # 2 digits needs 300px width, 3 digits needs 450px width
        width = len(str(countdown_sec)) * 150
        self.dtb = message.DelayedTextBox(title=title, toplevel=self, width=width,
                                          height=250, startup_delay=0, abort=abort,
                                          tf=tf, ta="center", win_grp=self.win_grp)
        # Loop until delay resume countdown finished or menu countdown finishes
        start = time.time()
        while time.time() < start + countdown_sec:
            if self.dtb.forced_abort:
                break
            if not self.winfo_exists():
                break  # self.exitApp() has destroyed window
            self.dtb.update(str(int(start + countdown_sec - time.time())))
            # Suspend uses: 'self.after(150)'
            self.after(100)
            self.last_refresh_time = time.time() + 1.0

        if timer and alarm is True:  # Play sound when timer ends
            if self.CheckInstalled("aplay"):
                command_line_list = ["aplay", GLO['TIMER_ALARM']]
                self.runCommand(command_line_list, _who)
        self.dtb.close()
        self.dtb = None

    def turnAllPower(self, state):
        """ Loop through instances and set power state to "ON" or "OFF".
            Called by Suspend ("OFF") and Resume ("ON")
            If devices treeview is mounted, update power status in each row
        """
        _who = self.who + "turnAllPower(" + state + "):"

        ''' 2025-02-19 Stale loop? resume and eventually close button error:

  File "./homa.py", line 3726, in __init__
    while self.refreshApp():  # Run forever until quit
  File "./homa.py", line 4558, in refreshApp
    self.Rediscover(auto=True)  # Check for new network devices
  File "./homa.py", line 4948, in Rediscover
    self.RefreshAllPowerStatuses(auto=auto)  # When auto false, rows highlighted
  File "./homa.py", line 4861, in RefreshAllPowerStatuses
    cr.Update(iid)  # Update row with new ['text']
  File "./homa.py", line 5894, in Update
    str(item), image=self.photo, text=self.text, values=self.values)
  File "/usr/lib/python2.7/lib-tk/ttk.py", line 1353, in item
    return _val_or_dict(self.tk, kw, self._w, "item", item)
  File "/usr/lib/python2.7/lib-tk/ttk.py", line 299, in _val_or_dict
    res = tk.call(*(args + options))
_tkinter.TclError: invalid command name ".140335699394216.140335510496752"

        '''

        v2_print()  # Blank line to separate debugging output

    def RefreshAllPowerStatuses(self, auto=False):
        """ Read ni.instances and update the power statuses.
            Called from one place: self.Rediscover(auto=False)
            If Devices Treeview is visible (mounted) update power status.
            TreeviewRow.Get() creates a device instance.
            Use device instance to get Power Status.
        """
        _who = self.who + "RefreshAllPowerStatuses():"

        # If auto, called automatically at GLO['REDISCOVER_SECONDS']
        cr = iid = None  # Assume Sensors Treeview is displayed
        if self.usingDevicesTreeview:
            cr = TreeviewRow(self)  # Setup treeview row processing instance

        v2_print()  # Blank line to separate debugging output

    def Rediscover(self, auto=False):
        """ Automatically call 'arp -a' to check on network changes.
            Job split into many slices of 16ms until done.
            Caller sleeps between calls using GLO['REDISCOVER_SECONDS'].
        """

        _who = self.who + "Rediscover():"

        ''' Calling a second time when first time is still running?
            Happens during message wait calling self.refreshApp() calling us.
        '''

        # If GLO['APP_RESTART_TIME'] is within 1 minute (GLO['REDISCOVER_SECONDS']) turn off
        # auto rediscovery flags so startup commands are logged to cmdEvents
        if GLO['APP_RESTART_TIME'] > time.time() - GLO['REDISCOVER_SECONDS'] - \
                GLO['RESUME_TEST_SECONDS'] - 10:
            auto = False  # Override auto rediscovery during startup / resuming

        # If called from menu, reseed last rediscovery time:
        if auto is False:
            self.last_rediscover_time = time.time() - GLO['REDISCOVER_SECONDS'] * 1.5

        ''' Some arp lines are DISCARDED: 
        arp -a
        SONY.LAN (192.168.0.19) at ac:9b:0a:df:3f:d9 [ether] on enp59s0
        ? (20.20.20.1) at a8:4e:3f:82:98:b2 [ether] on enp59s0          <- DISCARD
        hit ron hub.home (192.168.0.1) at a8:4e:3f:82:98:b2 [ether] on enp59s0
        TCL.light (192.168.0.20) at 50:d4:f7:eb:46:7c [ether] on enp59s0
        TCL.LAN (192.168.0.17) at <incomplete> on enp59s0               <- DISCARD
        SONY.light (192.168.0.15) at 50:d4:f7:eb:41:35 [ether] on enp59s0
        '''

        # Override event logging and v3_print(...) during auto rediscovery
        GLO['LOG_EVENTS'] = True if auto is False else False

        # Start looping create rd
        if rd is None:
            ext.t_init("Creating instance rd = NetworkInfo()")
            self.rediscover_done = False  # Signal job in progress
            self.enableDropdown()
            ext.t_end('no_print')
            if auto:  # If called from File dropdown menubar DON'T return
                self.last_refresh_time = time.time()  # Override resume from suspend
                return  # Reenter refresh loop. Return here in 16 ms

        def resetRediscovery():
            """ Reset variables for exit. """
            self.rediscover_done = True
            self.last_rediscover_time = time.time()
            self.last_refresh_time = time.time()  # Prevent resume from suspend
            self.file_menu.entryconfig("Rediscover now", state=tk.NORMAL)
            self.enableDropdown()

        v2_print(_who, "Rediscovery count:", len(rd.ytv_dicts))

        # Refresh power status for all device instances in ni.ytv_dicts
        self.RefreshAllPowerStatuses(auto=auto)  # When auto false, rows highlighted
        GLO['LOG_EVENTS'] = True  # Reset to log events as required
        if rd is None:
            resetRediscovery()
            return

        # All steps done: Wait for next rediscovery period
        resetRediscovery()

    def refreshDeviceStatusForInst(self, inst):
        """ Called by BluetoothLED """
        _who = self.who + "refreshDeviceStatusForInst():"
        if not self.usingDevicesTreeview:
            return
        # Find instance in treeview
        cr = TreeviewRow(self)
        iid = cr.getIidForYtvBasename(inst)
        if iid is None:
            v0_print(_who, "No iid for inst:", inst)
            return

        cr.Get(iid)
        self.tree.see(iid)
        cr.fadeIn(iid)

        old_text = cr.text  # Treeview row's old power state "  ON", etc.
        cr.text = "  " + inst.powerStatus  # Display treeview row's new power state
        if cr.text != old_text:
            v1_print(_who, cr.ytv_basename, "Power status changed from: '"
                     + old_text.strip() + "' to: '" + cr.text.strip() + "'.")
        cr.Update(iid)  # Update row with new ['text']
        cr.fadeOut(iid)

    @staticmethod
    def MouseWheel(event):
        """ Mousewheel scroll defaults to 5 units, but tree has 4 images """
        if event.num == 4:  # Override mousewheel scroll up
            event.widget.yview_scroll(-1, "units")  # tree = event.widget
            return "break"  # Don't let regular event handler do scroll of 5
        if event.num == 5:  # Override mousewheel scroll down
            event.widget.yview_scroll(1, "units")  # tree = event.widget
            return "break"  # Don't let regular event handler do scroll of 5

    def GetPassword(self, msg=None):
        """ Get Sudo password with message.AskString(show='*'...).
>>> from cryptography.fernet import Fernet
>>> # Put this somewhere safe!
>>> key = Fernet.generate_key()
>>> f = Fernet(key)
>>> token = f.encrypt(b"A really secret message. Not for prying eyes.")
>>> token
b'...'
>>> f.decrypt(token)
b'A really secret message. Not for prying eyes.'
        """

        if msg is None:
            msg = "Sudo password required for laptop display.\n\n"
        answer = message.AskString(
            self, text=msg, thread=self.Refresh, show='*',
            title="Enter sudo password", icon="information", win_grp=self.win_grp)

        # Setting laptop display power requires sudo prompt which causes fake resume
        self.last_refresh_time = time.time()  # Refresh idle loop last entered time

        if answer.result != "yes":
            return None  # Cancel button selected

        # Validate password, error message if invalid
        password = hc.ValidateSudoPassword(answer.string)
        if password is None:
            msg = "Invalid sudo password!\n\n"
            self.ShowInfo("Invalid sudo password", msg, icon="error")
            # message.ShowInfo(
            #    self, text=msg, thread=self.Refresh,
            #    title="Invalid sudo password", icon="error", win_grp=self.win_grp)

        self.last_refresh_time = time.time()  # Refresh idle loop last entered time
        return password  # Will be <None> if invalid password entered

    def ShowInfo(self, title, text, icon="information", align="center"):
        """ Show message with thread safe refresh that doesn't invoke rediscovery.

            Can be called from instance which has no tk reference of it's own
            From Application initialize with:   inst.app = self
            From Instance call method with:     self.app.ShowInfo()
            #ShowInfo(self, title, text, icon="information", align="center")
        """

        def thread_safe():
            """ Prevent self.Refresh rerunning a second rediscovery during
                Bluetooth connect error message waiting for acknowledgement
            """
            self.last_refresh_time = time.time()  # Prevent resume from suspend
            self.last_rediscover_time = self.last_refresh_time
            self.refreshApp(tk_after=False)
            self.after(10)
            self.update()  # Suspend button stays blue after mouseover ends>?

        message.ShowInfo(self, thread=thread_safe, icon=icon, align=align,
                         title=title, text=text, win_grp=self.win_grp)

    def Preferences(self):
        """ Edit preferences """

        if self.edit_pref_active and self.notebook:
            self.notebook.focus_force()
            self.notebook.lift()
            return

        self.notebook = self.edit_pref_active = None
        all_notebook = None

        def close(*_args):
            """ Close window painted by this pretty_column() method """
            _who = self.who + "Preferences(): close():"
            if not self.edit_pref_active:
                return
            self.tt.close(self.notebook)
            self.edit_pref_active = None

            ''' Update GLO[key] with new value '''
            for atts in all_notebook.listFields:
                if atts[2] != "read-write":
                    continue  # Only update read-write variables

                key = atts[0]  # E.G. 'YTV_URL_PREFIX'
                glo_type = str(type(GLO[key]))  # Can be <type 'unicode'> then new can be
                new_type = str(type(all_notebook.newData[key]))  # <type 'str'> no error.
                if glo_type != new_type:
                    if "'unicode'" not in glo_type and "'str'" not in new_type:
                        v0_print(_who, "Catastrophic error for:", key)
                        v0_print("  type(GLO[key]):", glo_type,
                                 " | type(all_notebook.newData[key]):", new_type)
                        continue  # Cannot populate dictionary with corrupt new value

                if GLO[key] == all_notebook.newData[key]:
                    continue  # No changes

                v1_print(_who, "key:", key, "\n  | old:", GLO[key],
                         " | new:", all_notebook.newData[key],
                         "\n  |", atts)

                _success = glo.updateNewGlobal(key, all_notebook.newData[key])

            self.notebook.destroy()
            self.notebook = None
            self.enableDropdown()
            # Restore Application() bottom button bar as pre buildButtonBar() options
            self.btn_frm.grid(row=99, column=0, columnspan=2, sticky=tk.E)

        # self.btn_frm.grid_forget()  # Hide Application() bottom button bar
        ha_font = (None, g.MON_FONT)  # ms_font = mserve, ha_font = HomA
        # style: https://stackoverflow.com/a/54213658/6929343
        style = ttk.Style()
        style.configure("TNotebook", background="White", padding=[10, 10], relief="raised")
        style.configure("TFrame", background="WhiteSmoke")
        style.configure("Notebook.TFrame", background="WhiteSmoke")
        style.configure("TLabel", background="WhiteSmoke")
        style.configure('TNotebook.Tab', font=ha_font, padding=[10, 10], relief="sunken",
                        background="WhiteSmoke", borderwidth=3, highlightthickness=3)
        style.map("TNotebook.Tab",
                  background=[("active", "SkyBlue3"), ("selected", "LightBlue")],
                  foreground=[("active", "Black"), ("selected", "Black")])
        style.map('TEntry', lightcolor=[('focus', 'LemonChiffon')])  # Not working

        self.btn_frm.grid_forget()  # Hide button bar
        self.notebook = ttk.Notebook(self)
        listTabs, listFields, listHelp = glo.defineNotebook()
        all_notebook = toolkit.makeNotebook(
            self.notebook, listTabs, listFields, listHelp, GLO, "TNotebook.Tab",
            "Notebook.TFrame", "C.TButton", close, tt=self.tt,
            help_btn_image=self.img_mag_glass, close_btn_image=self.img_close)
        self.edit_pref_active = True
        self.enableDropdown()

    def OpenCalculator(self):
        """ Big Number Calculator allows K, M, G, T, etc. UoM """
        if self.calculator and self.calc_top:
            self.calc_top.focus_force()
            self.calc_top.lift()
            return

        geom = monitor.get_window_geom('calculator')
        self.calc_top = tk.Toplevel()

        ''' Set Calculator program icon in taskbar '''
        cfg_key = ['cfg_calculator', 'toplevel', 'taskbar_icon', 'height & colors']
        ti = cfg.get_cfg(cfg_key)
        img.taskbar_icon(self.calc_top, ti['height'], ti['outline'],
                         ti['fill'], ti['text'], char=ti['char'])

        ''' Create calculator class instance '''
        self.calculator = Calculator(self.calc_top, g.BIG_FONT, geom,
                                     btn_fg=ti['text'], btn_bg=ti['fill'])
        self.win_grp.register_child('Calculator', self.calc_top)

        # Do not auto raise children. homa.py will take care of that with focusIn()

        def calculator_close(*_args):
            """ Save last geometry for next Calculator startup """
            last_geom = monitor.get_window_geom_string(
                self.calc_top, leave_visible=False)  # Leave toplevel invisible
            monitor.save_window_geom('calculator', last_geom)
            self.win_grp.unregister_child(self.calc_top)
            self.calc_top.destroy()
            self.calc_top = None  # Prevent lifting window
            self.calculator = None  # Prevent lifting window

        ''' Trap <Escape> key and  '✘' Window Close Button '''
        self.calc_top.bind("<Escape>", calculator_close)
        self.calc_top.protocol("WM_DELETE_WINDOW", calculator_close)
        self.calc_top.update_idletasks()

        ''' Move Calculator to cursor position '''
        hc.MoveHere("Big Number Calculator", 'top_left')

    def DisplayErrors(self):
        """ Loop through ni.instances and display cmdEvents errors
            2024-12-18 - Initial version displays all errors in scrolled textbox.
                Future versions treeview with tree parent by expandable instance.
        """
        _who = self.who + "DisplayErrors():"
        title = "Discovery errors"
        scrollbox = self.DisplayCommon(_who, title)
        if scrollbox is None:
            return  # Window already opened and method is running

        def insertEvents(events):
            """
            :param events: self.cmdEvents from ClassCommonSelf() class
            :return:
            """
            for event in events:
                ''' self.cmdEvent = {
                    'caller': self.cmdCaller,  # Command caller: 'who+method():'
                    'command': self.cmdCommand,  # Command list to executed
                    'command_string': self.cmdString,  # Command list as string
                    'start_time': self.cmdStart,  # When command started
                    'duration': self.cmdDuration,  # Command duration
                    'output': self.cmdOutput,  # stdout.strip() from command
                    'error': self.cmdError,  # stderr.strip() from command
                    'returncode': self.cmdReturncode  # return code from command } '''

                if event['error'] == "" and event['returncode'] == 0:
                    continue  # Not an error

                time_str = time.strftime('%b %d %H:%M:%S',
                                         time.localtime(event['start_time']))
                duration = '{0:.3f}'.format(event['duration'])
                scrollbox.insert("end", "\n" + time_str + "  | " + event['caller'] +
                                 "  | Time: " + duration +
                                 "  | Return: " + str(event['returncode']) + "\n")
                scrollbox.highlight_pattern(event['caller'], "blue")
                scrollbox.highlight_pattern("Time:", "green")
                scrollbox.highlight_pattern("Return:", "red")

                scrollbox.insert("end", "\tCommand: " + event['command_string'] + "\n")
                scrollbox.highlight_pattern("Command:", "blue")
                scrollbox.highlight_pattern(event['command_string'], "yellow")

                try:
                    errors = event['error'].splitlines()  # Error lines split on "\n"
                except AttributeError:
                    errors = event['error']  # Already a list
                for error in errors:
                    scrollbox.insert("end", "\t\t" + error + "\n")
        insertEvents(self.cmdEvents)  # This app = Application() class

    def DisplayTimings(self):
        """ Loop through ni.instances and display cmdEvents times:
                Count: 9, Minimum: 9.99, Maximum: 9.99, Average 9.99.

            2024-12-21 TODO: Merge common code with DisplayErrors() > DisplayCommon()
        """
        _who = self.who + "DisplayTimings():"
        title = "Discovery timings"
        scrollbox = self.DisplayCommon(_who, title)
        if scrollbox is None:
            return  # Window already opened and method is running

        def insertEvents(events):
            """ cmdEvents from ni.instances or from ni itself
            :param events: cmdEvents
            :return: None
            """
            timings = {}  # caller + command_string: [count, all_times, min, max, avg]
            for event in events:
                ''' self.cmdEvent = {
                    'caller': self.cmdCaller,  # Command caller: 'who+method():'
                    'command': self.cmdCommand,  # Command list to executed
                    'command_string': self.cmdString,  # Command list as string
                    'start_time': self.cmdStart,  # When command started
                    'duration': self.cmdDuration,  # Command duration
                    'output': self.cmdOutput,  # stdout.strip() from command
                    'error': self.cmdError,  # stderr.strip() from command
                    'returncode': self.cmdReturncode  # return code from command } '''

                keyT = event['caller'] + " " + event['command_string']
                val = timings.get(keyT, None)
                if val is None:
                    val = {'count': 0, 'all_times': 0.0, 'min': 999999999.9,
                           'max': 0.0, 'avg': 9.9}
                val['count'] += 1
                val['all_times'] += event['duration']
                val['min'] = event['duration'] if event['duration'] < val['min'] else val['min']
                val['max'] = event['duration'] if event['duration'] > val['max'] else val['max']
                val['avg'] = val['all_times'] / val['count']
                timings[keyT] = val

            if not timings:
                # 192.168.0.19 - Sony.LAN (using ni.os_curl not logging)
                # 192.168.0.10 - WiFi (laptop display echo | sudo tee)
                return  # No events for instance?

            for keyT in timings:
                scrollbox.insert("end", "\n" + keyT + "\n")

                val = timings[keyT]
                scrollbox.insert("end", "\tCnt:" + str(val['count']) +
                                 "  | Tot: " + '{0:.3f}'.format(val['all_times']) +
                                 "  | Min: " + '{0:.3f}'.format(val['min']) +
                                 "  | Max: " + '{0:.3f}'.format(val['max']) +
                                 "  | Avg: " + '{0:.3f}'.format(val['avg']) +
                                 "\n")
                scrollbox.highlight_pattern(keyT, "blue")

        # Loop through ni.instances
        for i, instance in enumerate(ni.instances):
            inst = instance['instance']
            insertEvents(inst.cmdEvents)

        # NetworkInfo (ni) and SystemMonitor (sm) have cmdEvents too!
        insertEvents(self.cmdEvents)  # This app = Application() class

        scrollbox.highlight_pattern("Min:", "green")
        scrollbox.highlight_pattern("Max:", "red")
        scrollbox.highlight_pattern("Avg:", "yellow")

    def DisplayCommon(self, _who, title, x=None, y=None, width=1200, height=500,
                      close_cb=None, help=None):
        """ Common method for DisplayErrors(), DisplayTimings()

            Caller has 90 heading rows, 10 footer rows and 10 columns to use. For
                example, uses 4 heading rows and 5 columns.

            2025-02-04 TODO: create self.event_scrollbox instead of 'return scrollbox'

        """

        if self.event_scroll_active and self.event_top:
            self.event_top.focus_force()
            self.event_top.lift()
            return

        self.event_top = self.event_frame = scrollbox = self.event_scroll_active = None
        self.event_btn_frm = None

        def close(*_args):
            """ Close window painted by this pretty_column() method """
            if not self.event_scroll_active:
                return
            scrollbox.unbind("<Button-1>")  # 2024-12-21 TODO: old code, use unknown
            self.win_grp.unregister_child(self.event_top)
            self.tt.close(self.event_top)
            self.event_scroll_active = None
            self.event_top.destroy()
            self.event_top = None
            if close_cb:
                close_cb()
            self.enableDropdown()

        self.event_top = tk.Toplevel()
        if x is None or y is None:
            x, y = hc.GetMouseLocation()
        self.event_top.geometry('%dx%d+%d+%d' % (width, height, int(x), int(y)))
        self.event_top.minsize(width=120, height=63)
        self.event_top.title(title)

        self.event_top.columnconfigure(0, weight=1)
        self.event_top.rowconfigure(0, weight=1)
        self.event_top.configure(background="WhiteSmoke")  # Future user configuration
        self.win_grp.register_child(title, self.event_top)  # Lifting & moving with parent
        self.event_scroll_active = True

        ''' Borrow Calculator program icon for taskbar '''
        cfg_key = ['cfg_calculator', 'toplevel', 'taskbar_icon', 'height & colors']
        ti = cfg.get_cfg(cfg_key)
        img.taskbar_icon(self.event_top, ti['height'], ti['outline'],
                         ti['fill'], ti['text'], char="V")

        ''' Bind <Escape> to close window '''
        self.event_top.bind("<Escape>", close)
        self.event_top.protocol("WM_DELETE_WINDOW", close)

        ''' frame - Holds scrollable text entry and button(s) '''
        self.event_frame = ttk.Frame(self.event_top, borderwidth=g.FRM_BRD_WID,
                                     padding=(2, 2, 2, 2), relief=tk.RIDGE)
        self.event_frame.grid(column=0, row=0, sticky=tk.NSEW)
        ha_font = (None, g.MON_FONT)  # ms_font = mserve, ha_font = HomA

        scrollbox = toolkit.CustomScrolledText(
            self.event_frame, state="normal", font=ha_font, borderwidth=15, relief=tk.FLAT)
        toolkit.scroll_defaults(scrollbox)  # Default tab stops are too wide
        scrollbox.config(tabs=("50", "100", "150"))
        scrollbox.grid(row=90, column=0, columnspan=10, padx=3, pady=3, sticky=tk.NSEW)
        # 90 rows available for headings, 10 rows available for footers
        self.event_frame.rowconfigure(90, weight=1)
        self.event_frame.columnconfigure(0, weight=1)

        self.event_btn_frm = tk.Frame(self.event_frame, borderwidth=g.FRM_BRD_WID,
                                      relief=tk.RIDGE)
        self.event_btn_frm.grid(row=100, column=0, sticky=tk.NSEW)
        self.event_btn_frm.columnconfigure(0, weight=1)

        def button_func(row, column, txt, command, tt_text, tt_anchor, pic):
            """ Function to combine ttk.Button, .grid() and tt.add_tip() """
            widget = ttk.Button(self.event_btn_frm, text=" " + txt, width=len(txt) + 2,
                                command=command, style="C.TButton",
                                image=pic, compound="left")
            widget.grid(row=row, column=column, padx=5, pady=5, sticky=tk.E)
            if tt_text is not None and tt_anchor is not None:
                self.tt.add_tip(widget, tt_text, anchor=tt_anchor)
            return widget

        if help is not None:
            ''' Help Button - ⧉ Help - Videos and explanations on pippim.com
                https://www.pippim.com/programs/homa.html#Introduction '''
            help_text = "Open new window in default web browser for\n"
            help_text += "videos and explanations on using this screen.\n"
            help_text += "https://www.pippim.com/programs/homa.html#\n"
            button_func(0, 0, "Help", lambda: g.web_help(help),
                        help_text, "ne", self.img_mag_glass)

        button_func(0, 1, "Close", close, "Close this window.", "ne", self.img_close)

        # Foreground colors
        scrollbox.tag_config('red', foreground='red')
        scrollbox.tag_config('blue', foreground='blue')
        scrollbox.tag_config('green', foreground='green')
        scrollbox.tag_config('black', foreground='black')
        scrollbox.tag_config('gray', foreground='gray')

        # Highlighting background colors
        scrollbox.tag_config('yellow', background='yellow')
        scrollbox.tag_config('cyan', background='cyan')
        scrollbox.tag_config('magenta', background='magenta')
        self.enableDropdown()
        return scrollbox


class TreeviewRow(ClassCommonSelf):
    """ Device treeview row variables and methods.

        Sensors treeview uses dummy call to TreeviewRow() class in order to call
        fadeIn() and fadeOut() methods.

    """

    def __init__(self, top):
        """ ClassCommonSelf(): Variables used by all classes
        :param top: Toplevel created by Application() class instance.
        """
        ClassCommonSelf.__init__(self, "TreeviewRow().")  # Define self.who

        self.top = top  # 2025-01-13 top is not passed as argument???
        self.tree = self.top.tree  # Shortcut
        self.photos = self.top.photos  # Shortcut
        self.item = None  # Treeview Row iid
        self.photo = None  # Photo image
        self.text = None  # Row text, E.G. "ON", "OFF"

        self.values = None  # Row values - Name lines, Attribute lines, MAC
        self.name_column = None  # Device Name & IP address - values[0]
        self.attribute_column = None  # 3 line device Attributes - values[1]
        self.ytv_basename = None  # ytv_basename - hidden column values[-1] / values[2]
        # self.ytv_basename - ytv_dict['ytv_basename'] - is non-displayed treeview column
        # used to reread ytv_dict

        self.ytv_dict = None  # device dictionary
        self.inst = None  # device instance
        self.inst_dict = None  # instance dictionary

    def Get(self, item):
        """ Get treeview row """

        _who = self.who + "Get():"

        self.item = str(item)  # iid - Corrupted after swapping rows!
        # CANNOT USE: self.photo = self.top.tree.item(item)['image']
        self.photo = self.photos[int(item)]
        self.text = self.top.tree.item(self.item)['text']

        self.values = self.top.tree.item(self.item)['values']
        self.name_column = self.values[0]  # Host name / IP address
        self.attribute_column = self.values[1]  # Host alias / MAC / Type Code
        self.ytv_basename = self.values[2]  # ytv_dict['mac'] is non-displayed value

    def getIidForYtvBasename(self, basename):
        """ Using passed instance, get the treeview row. """
        for iid in self.tree.get_children():
            self.Get(iid)
            if self.ytv_basename == basename:
                return iid

        return None  # Passed instance is not in treeview

    def Update(self, item):
        """ Set treeview row - Must call .Get() beforehand.
            Handles item being a str() or an int()
            :param item: Target row can be different than original self.item
            :returns: nothing
        """
        _who = self.who + "Update():"

        self.top.photos[int(item)] = self.photo  # changes if swapping rows
        self.top.tree.item(
            str(item), image=self.photo, text=self.text, values=self.values)

        if self.item != str(item):  # Swapping rows
            v1_print(_who, "NOT resetting iid from self.item:", self.item,
                     "to:", str(item))

    def New(self, ytc):
        """ Create default treeview row
            During startup / resume, BLE LED Light Strips require extra connect
            :param ytc: YouTube() class instance
        """

        _who = self.who + "New():"
        self.photo = ImageTk.PhotoImage(ytc.currentTkImage.resize((300, 180), Image.ANTIALIAS))
        # sample 'link' var: https://www.youtube.com/watch?v=RGlZ4AlAOtg
        # OTHER VIDEOS:
        # https://www.youtube.com/watch?v=u0z5Bo3VwtE
        # https://www.youtube.com/watch?v=9uj8SI8xWGc  # Invalid TCL characters (UTF-8)
        self.ytv_basename = ytc.currentWebpage.split(GLO['YTV_URL_WATCH'])[1]  # key: RGlZ4AlAOtg
        # Do not force GLO['YTV_URL_BASENAME'] because another video could be playing
        wrapped_owner = '\n'.join(textwrap.wrap(ytc.currentOwner, GLO['TREE_COL1_WRAP']))
        self.name_column = wrapped_owner  # Channel Name
        wrapped_upload = '\n'.join(textwrap.wrap(ytc.currentUploadDate, GLO['TREE_COL1_WRAP']))
        self.name_column += "\n" + wrapped_upload  # Uploaded Date
        self.name_column += "\n" + tmf.days(ytc.currentDur)  # Video Duration
        wrapped_title = '\n'.join(textwrap.wrap(ytc.currentTitle, GLO['TREE_COL2_WRAP']))
        self.attribute_column = toolkit.normalize_tcl(wrapped_title)
        self.values = (self.name_column, self.attribute_column, self.ytv_basename)

    def Add(self, item):
        """ Set treeview row - Must call .New() beforehand.
            Handles item being a str() or an int()
            :param item: Target row can be different than original self.item
            :returns: nothing
        """
        _who = self.who + "Add():"
        trg_iid = str(item)  # Target row can be different than original self.item
        # Inserting into treeview must save from garbage collection
        # using self.top.photos in Toplevel instance. Note self.photo is in this
        # TreeviewRow instance and not in Toplevel instance.
        self.top.photos.append(self.photo)
        text = "  NEW"  # New video
        self.text = text

        self.top.tree.insert(
            '', 'end', iid=trg_iid, text=self.text,
            image=self.top.photos[-1], value=self.values)

    def fadeIn(self, item):
        """ Fade In over 10 steps of 30 ms """
        toolkit.tv_tag_remove(self.tree, item, 'normal')  # Same as step 10
        for i in range(10):
            try:
                if i != 0:
                    toolkit.tv_tag_remove(self.tree, item, 'fade' + str(i - 1))
                if i != 9:
                    toolkit.tv_tag_add(self.tree, item, 'fade' + str(i))
                else:
                    toolkit.tv_tag_add(self.tree, item, 'curr_sel')  # Same as step 10
                self.tree.update()  # Change from .top to .tree for SystemMonitor to use
                self.tree.after(10)  # 20 milliseconds
            except tk.TclError:
                return  # Changed treeview during fade in

    def fadeOut(self, item):
        """ Fade Out over 10 steps of 30 ms """
        toolkit.tv_tag_remove(self.tree, item, 'curr_sel')  # Same as step 10
        for i in range(9, -1, -1):
            try:
                if i != 9:
                    toolkit.tv_tag_remove(self.tree, item, 'fade' + str(i))
                if i > 0:
                    toolkit.tv_tag_add(self.tree, item, 'fade' + str(i))
                else:
                    toolkit.tv_tag_add(self.tree, item, 'normal')  # Same as step 10
                self.tree.update()
                self.tree.after(10)  # 10 milliseconds
            except tk.TclError:
                return  # Changed tree during fade out


def v0_print(*args, **kwargs):
    """ Information printing silenced by argument -s / --silent """
    if not p_args.silent:
        print(*args, **kwargs)


def v1_print(*args, **kwargs):
    """ Debug printing for argument -v (--verbose1). Overrides -s (--silent) """
    if p_args.verbose1 or p_args.verbose2 or p_args.verbose3:
        print(*args, **kwargs)


def v2_print(*args, **kwargs):
    """ Debug printing for argument -vv (--verbose2). Overrides -s (--silent) """
    if p_args.verbose2 or p_args.verbose3:
        print(*args, **kwargs)


def v3_print(*args, **kwargs):
    """ Debug printing for argument -vvv (--verbose3). Overrides -s (--silent) """
    if p_args.verbose3:
        print(*args, **kwargs)


def discover(update=False, start=None, end=None):
    """ Test arp devices for device type using .isDevice() by mac address.
        Called from mainline and app.Rediscover()

        Before calling use ni = NetworkInfo() to create ni.ytv_dicts[{}, {}...]
        app.Rediscover() uses rd = NetworkInfo() to create rd.ytv_dicts

        :param update: If True, update ni.ytv_dicts entry with type_code
        :param start: ni.ytv_dicts starting index for loop
        :param end: ni.ytv_dicts ending index (ends just before passed value)
        :returns: list of known device instances
    """
    _who = "homa.py discover()"
    global ni  # NetworkInformation() class instance used everywhere
    discovered = []  # List of discovered devices in arp dictionary format
    instances = []  # List of instances shadowing each discovered device
    view_order = []  # Order of macs discovered

    v1_print("\n")
    v1_print("=" * 20, " Test all arp devices for their type ", "=" * 20)
    v1_print()

    if not start:
        start = 0
    if not end:
        end = len(ni.ytv_dicts)  # Not tested as of 2024-11-10

    for i, arp in enumerate(ni.ytv_dicts[start:end]):
        # arp = {"mac": mac, "ip": ip, "name": name, "alias": alias, "type_code": 99}
        v2_print("\nTest for device type using 'arp' dictionary:", arp)

        # Get class instance information rebuilt at run time and never saved to disk
        instance = ni.test_for_instance(arp)  # test against known device types
        if not bool(instance):  # Is instance an empty dictionary?
            continue  # No instance found, perhaps it's a router or smart phone, etc.

        arp['type_code'] = instance['instance'].type_code  # type_code unknown until now
        discovered.append(arp)  # list of arp dictionaries are saved to disk
        instances.append(instance)  # instance = {"mac": arp['mac'], "instance": inst}
        view_order.append(arp['mac'])  # treeview ordered by MAC address saved to disk
        if update:
            ni.ytv_dicts[i] = arp  # Update arp list with type_code found in instance

    return discovered, instances, view_order


v1_print(sys.argv[0], "- YouTube control", " | verbose1:", p_args.verbose1,
         " | verbose2:", p_args.verbose2, " | verbose3:", p_args.verbose3,
         "\n  | fast:", p_args.fast, " | silent:", p_args.silent)

''' Global classes '''
root = None  # Tkinter toplevel
app = None  # Application GUI instance
yt = None  # YouTube class instance

cfg = sql.Config()  # Colors configuration SQL records
glo = Globals()  # Global variables instance used everywhere
GLO = glo.dictGlobals  # Default global dictionary. Live read in glo.open_file()

SAVE_CWD = ""  # Save current working directory before changing to program directory
killer = ext.GracefulKiller()  # Class instance for app.Close() or CTRL+C

v0_print()
v0_print(r'  ######################################################')
v0_print(r' //////////////                            \\\\\\\\\\\\\\')
v0_print(r'<<<<<<<<<<<<<<      PimTube Media Player    >>>>>>>>>>>>>>')
v0_print(r' \\\\\\\\\\\\\\                            //////////////')
v0_print(r'  ######################################################')
v0_print(r' '*20, r'Started:', dt.datetime.now().strftime('%I:%M %p').strip('0'))


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

    sql.open_homa_db()  # Open SQL History Table only for saved configs

    glo.openFile()
    GLO = glo.dictGlobals
    GLO['APP_RESTART_TIME'] = time.time()

    # ni.adb_reset()  # adb kill-server && adb start-server
    # 2024-10-13 - adb_reset() is breaking TCL TV discovery???

    ''' Open Main Application Window '''
    root = tk.Tk()
    #root.overrideredirect(1)  # Get rid of flash when root window created
    #monitor.center(root)  # Get rid of top-left flash when root window created
    #img.taskbar_icon(root, 64, 'black', 'green', 'red', char='H')
    # Above no effect, taskbar icon is still a question mark with no color
    root.withdraw()
    app = Application(root)

    app.mainloop()


if __name__ == "__main__":
    main()

# End of: pimtube.py
