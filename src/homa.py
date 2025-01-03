#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: pippim.com
License: GNU GPLv3. (c) 2024
Source: This repository
Description: HomA - Home Automation - Main **homa** Python Module
"""

from __future__ import print_function  # Must be first import
from __future__ import with_statement  # Error handling for file opens
import warnings  # 'warnings' advises which methods aren't supported

# ==============================================================================
#
#       homa.py (Home Automation) - Manage devices
#
#       2024-10-02 - Creation date.
#       2024-12-01 - Create GitHub repo. Add dropdown menus and Big Number Calc.
#
# ==============================================================================

warnings.simplefilter('default')  # in future Python versions.

'''
    REQUIRES:
    
    python(3)-appdirs
    python(3)-xlib        # imported as Xlib.X
    python(3)-ttkwidgets  # Also stored as subdirectory in ~/python/ttkwidgets
    xdotool  # To minimize window
    systemctl  # To suspend. Or suitable replacement like `suspend` external command
    adb  # Android debugging bridge for Google Android TV's
    curl  # For Sony Bravia KDL professional displays (TV's)

'''

''' check configuration. '''
import inspect
import os

try:
    filename = inspect.stack()[1][1]  # If there is a parent, it must be 'h'
    parent = os.path.basename(filename)
    if parent != 'h':
        print("homa.py called by unrecognized:", parent)
        exit()
except IndexError:  # list index out of range
    ''' 'h' hasn't been run to get global variables or verify configuration '''
    #import mserve_config as m_cfg  # Differentiate from sql.Config as cfg

    caller = "homa.py"
    import global_variables as g
    g.init(appname="homa")

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

    PYTHON_VER = "3"
except ImportError:  # Python 2
    import Tkinter as tk
    import ttk
    import tkFont as font
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox
    import tkSimpleDialog as simpledialog
    import ScrolledText as scrolledtext

    PYTHON_VER = "2"

from PIL import Image, ImageTk, ImageDraw, ImageFont

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
parser.add_argument('-s', '--silent', action='store_true')  # Suppress info
parser.add_argument('-v', '--verbose1', action='store_true')  # Print Overview
parser.add_argument('-vv', '--verbose2', action='store_true')  # Print Functions
parser.add_argument('-vvv', '--verbose3', action='store_true')  # Print Commands
p_args = parser.parse_args()

import json  # For dictionary storage in external file
import copy  # For deepcopy of lists of dictionaries
import re  # For Regex searches
import time  # For now = time.time()
import datetime as dt  # For dt.datetime.now().strftime('%I:%M %p')

try:
    reload(sys)  # June 25, 2023 - Without utf8 sys reload, os.popen() fails on OS
    sys.setdefaultencoding('utf8')  # filenames that contain unicode characters
except NameError:  # name 'reload' is not defined
    pass  # Python 3 already in unicode by default

# Pippim libraries
import monitor  # Center window on current monitor supports multi-head rigs
import toolkit  # Various tkinter functions common to mserve apps
import message  # For dtb (Delayed Text Box)
import sql  # For color options - Lots of irrelevant mserve.py code though
import image as img  # Image processing. E.G. Create Taskbar icon
import external as ext  # Call external functions, programs, etc.
import timefmt as tmf  # Time formatting, ago(), days(), hh_mm_ss(), etc.
from calc import Calculator  # Big Number calculator

import homa_common as hc  # hc.ValidateSudoPassword()

#SONY_PWD = "123"  # Sony TV REST API password
#CONFIG_FNAME = "config.json"  # Future configuration file.
#DEVICES_FNAME = "devices.json"  # mirrors ni.arp_dicts[{}, {}, ... {}]
#VIEW_ORDER_FNAME = "view_order.json"  # Read into ni.view_order[mac1, mac2, ... mac9]

# Timeouts improve device interface performance
#PLUG_TIME = "2.0"  # Smart plug timeout to turn power on/off
#CURL_TIME = "0.2"  # Anything longer means not a Sony TV or disconnected
#ADB_CON_TIME = "0.3"  # Android TV Test if connected timeout
#ADB_PWR_TIME = "2.0"  # Android TV Test if power state is on. Test increment .5 sec
#ADB_KEY_TIME = "5.0"  # Android keyevent KEYCODE_SLEEP or KEYCODE_WAKEUP timeout
#ADB_MAGIC_TIME = "0.2"  # Android TV Magic Packet wait time.

#APP_RESTART_TIME = time.time()  # Time started or resumed. Use for elapsed time print
#REFRESH_MS = 16  # Refresh tooltip fades 60 frames per second
#REDISCOVER_SECONDS = 60  # Check devices changes every x seconds
#RESUME_TEST_SECONDS = 10  # > x seconds disappeared means system resumed
#RESUME_DELAY_RESTART = 3  # Pause x seconds after resuming from suspend
#TIMER_SEC = 600  # Tools Dropdown Menubar - Countdown Timer default
#TIMER_ALARM = "Alarm_01.wav"  # From: https://www.pippim.com/programs/tim-ta.html
#LOG_EVENTS = True  # Override runCommand event logging / --verbose3 printing
#EVENT_ERROR_COUNT = 0  # To enable/disable View Dropdown menu "Discovery errors"

#SENSOR_CHECK = 1.0  # Check `sensors` (CPU/GPU temp & fan speeds) every x seconds
#SENSOR_LOG = 3600.0  # Log `sensors` every x seconds. Log more if fan speed changes
#FAN_GRANULAR = 200  # Skip logging when fan changes <= FAN_GRANULAR

# Device type global identifier hard-coded in "inst.type_code"
#HS1_SP = 10  # TP-Link Kasa WiFi Smart Plug HS100, HS103 or HS110 using hs100.sh
#KDL_TV = 20  # Sony Bravia KDL Android TV using REST API (curl)
#TCL_TV = 30  # TCL Google Android TV using adb (after wakeonlan)
#DESKTOP = 100  # Desktop Computer, Tower, NUC, Raspberry Pi, etc.
#LAPTOP_B = 110  # Laptop base (CPU, GPU, Keyboard, Fans, Ports, etc.)
#LAPTOP_D = 120  # Laptop display (Can be turned on/off separate from base)
#SUDO_PASSWORD = None  # Sudo password required for laptop backlight
#BACKLIGHT_NAME = os.popen("ls /sys/class/backlight").read().strip()  # intel_backlight
#BACKLIGHT_ON = "0"  # Sudo echo to "/sys/class/backlight/intel_backlight/bl_power"
#BACKLIGHT_OFF = "4"  # ... will control laptop display backlight power On/Off.

#POWER_OFF_CMD_LIST = ["systemctl", "suspend"]  # When calling "Turn Off" for Computer()
#POWER_ALL_EXCL_LIST = [DESKTOP, LAPTOP_B, LAPTOP_D]  # Exclude when powering "All"


class DeviceCommonSelf:
    """ Common Variables used by NetworkInfo, SmartPlugHS100, SonyBraviaKdlTV,
        and TclGoogleTV device classes. Also used by Application() class.
    """

    def __init__(self, who):
        """ Variables used by all classes """

        self.who = who  # For debugging, print class name

        self.dependencies_installed = None  # Parent will call self.CheckDependencies()
        self.passed_dependencies = []
        self.passed_installed = []

        self.system_ctl = False  # Turning off TV shuts down / suspends system
        self.remote_suspends_system = False  # If TV powered off suspend system

        # 2024-12-17 TODO: Use inst.suspendPowerOff, instead of self.suspendPowerOff
        self.suspendPowerOff = 0  # Did suspend power off the device?
        self.resumePowerOn = 0  # Did resume power on the device?
        self.menuPowerOff = 0  # Did user power off the device via menu option?
        self.menuPowerOn = 0  # Did user power on the device via menu option?
        self.manualPowerOff = 0  # Was device physically powered off?
        self.manualPowerOn = 0  # Was device physically powered on?
        self.dayPowerOff = 0  # Did daylight power off the device?
        self.nightPowerOn = 0  # Did nighttime power on the device?

        # self.overrideLog = None  # Set True during auto rediscovery for no logging
        # self.overrideLog won't work because it is defined at instance level as well
        # as the Application() summary level

        # Separate self.cmdEvents for every instance.
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
        _who = self.who + "which():"

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

        pipe = sp.Popen(self.cmdCommand, stdout=sp.PIPE, stderr=sp.PIPE)
        text, err = pipe.communicate()  # This performs .wait() too

        self.cmdOutput = text.strip()
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
        if GLO['LOG_EVENTS'] is False:
            log = False  # Auto rediscovery has turned off logging
        if log:
            v3_print("\n" + who,  "'" + self.cmdString + "'")
            o = self.cmdOutput if isinstance(self.cmdOutput, str) else '\n'.join(self.cmdOutput)
            v3_print("  cmdOutput: '" + o + "'")
            o = self.cmdError if isinstance(self.cmdError, str) else '\n'.join(self.cmdError)
            v3_print("  cmdError : '" + o  + "'  | cmdReturncode: ",
                     self.cmdReturncode, "  | cmdDuration:", self.cmdDuration)

        if self.cmdReturncode != 0:
            if forgive is False:
                v0_print(who, "cmdReturncode:", self.cmdReturncode)

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


class Globals(DeviceCommonSelf):
    """ Globals

        What could be in sql.py too complicated to document due to mserve.py

        - timeouts for adb, REST, resume, rediscover
        - colors for toplevel, taskbar icon, treeview, scrollbars

    """

    def __init__(self):
        """ DeviceCommonSelf(): Variables used by all classes """
        DeviceCommonSelf.__init__(self, "Globals().")  # Define self.who

        self.requires = ['ls']

        # Next four lines can be defined in DeviceCommonSelf.__init__()
        self.installed = []
        self.CheckDependencies(self.requires, self.installed)
        v2_print(self.who, "Dependencies:", self.requires)
        v2_print(self.who, "Installed?  :", self.installed)

        # Defined globally with: glo = Globals()
        #                        GLO = glo.dictGlobals
        self.dictGlobals = {
            "SONY_PWD": "123",  # Sony TV REST API password
            "CONFIG_FNAME": "config.json",  # Future configuration file.
            "DEVICES_FNAME": "devices.json",  # mirrors ni.arp_dicts[{}, {}, ... {}]
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
            "REDISCOVER_SECONDS": 60,  # Check devices changes every x seconds
            "RESUME_TEST_SECONDS": 10,  # > x seconds disappeared means system resumed
            "RESUME_DELAY_RESTART": 3,  # Pause x seconds after resuming from suspend
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
            "DESKTOP": 100,  # Desktop Computer, Tower, NUC, Raspberry Pi, etc.
            "LAPTOP_B": 110,  # Laptop base (CPU, GPU, Keyboard, Fans, Ports, etc.)
            "LAPTOP_D": 120,  # Laptop display (Can be turned on/off separate from base)
            "SUDO_PASSWORD": None,  # Sudo password required for laptop backlight
            "BACKLIGHT_NAME": os.popen("ls /sys/class/backlight").read().strip(),  # intel_backlight
            "BACKLIGHT_ON": "0",  # Sudo echo to "/sys/class/backlight/intel_backlight/bl_power"
            "BACKLIGHT_OFF": "4",  # ... will control laptop display backlight power On/Off.
            # Power all On/Off controls
            "POWER_OFF_CMD_LIST": ["systemctl", "suspend"],  # Run "Turn Off" for Computer()
            "POWER_ALL_EXCL_LIST": [100, 110, 120],  # Exclude when powering "All" to "ON" / "OFF"
                                                     # 100=DESKTOP, 110=LAPTOP_B, 120=LAPTOP_D
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

        GLO['SUDO_PASSWORD'] = None  # NEVER store a password
        GLO['LOG_EVENTS'] = True  # Don't want to store False value
        GLO['EVENT_ERROR_COUNT'] = 0  # Don't want to store last error count
        with open(g.USER_DATA_DIR + os.sep + GLO['CONFIG_FNAME'], "w") as f:
            f.write(json.dumps(self.dictGlobals))

    def defineNotebook(self):
        """ defineNotebook models global data variables in dictionary. Used by
            Edit Preferences in HomA and makeNotebook() in toolkit.py.

            2025-01-01 TODO: Don't allow Suspend when Edit Preferences is active.

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
            ("Miscellaneous",
             "Variables for 'sensors' temperature monitor\n"
             "and Countdown Timer."),
            ("Power",
             "Define how the computer is turned on or\n"
             "it is resumed / woken up."),
            ("Computer",  # Only display when chassis = 'Laptop'
             "Laptop backlight display control codes.")
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
        WID = 15  # Default Width
        DEC = MIN = MAX = CB = None  # Decimal places, Minimum, Maximum, Callback
        listFields = [
            # name, tab#, ro/rw, input as, stored as, width, decimals, min, max,
            #   edit callback, tooltip text
            ("SONY_PWD", 1, RW, STR, STR, 10, DEC, MIN, MAX, CB,
             "Password for Sony REST API"),
            ("CONFIG_FNAME", 0, HD, STR, STR, WID, DEC, MIN, MAX, CB,
             "Configuration filename"),
            ("DEVICES_FNAME", 0, HD, STR, STR, WID, DEC, MIN, MAX, CB,
             "discovered network devices filename"),
            ("VIEW_ORDER_FNAME", 0, HD, STR, STR, WID, DEC, MIN, MAX, CB,
             "Network Devices Treeview display order filename"),
            # Timeouts improve device interface performance
            ("PLUG_TIME", 3, RW, FLOAT, STR, 5, DEC, MIN, MAX, CB,
             "Smart plug timeout to turn power on/off"),
            ("CURL_TIME", 1, RW, FLOAT, STR, 5, DEC, MIN, MAX, CB,
             "A longer time means this is not\na Sony TV or Sony TV disconnected"),
            ("ADB_CON_TIME", 2, RW, FLOAT, STR, 5, DEC, MIN, MAX, CB,
             "Android TV test if connected timeout"),
            ("ADB_PWR_TIME", 2, RW, FLOAT, STR, 5, DEC, MIN, MAX, CB,
             "Android TV test power state timeout"),
            ("ADB_KEY_TIME", 2, RW, FLOAT, STR, 5, DEC, MIN, MAX, CB,
             "Android keyevent KEYCODE_SLEEP\nor KEYCODE_WAKEUP timeout"),
            ("ADB_MAGIC_TIME", 2, RW, FLOAT, STR, 5, DEC, MIN, MAX, CB,
             "Android TV Wake on Lan Magic Packet wait time."),
            # Application timings and global working variables
            ("APP_RESTART_TIME", 5, RW, TM, TM, 18, DEC, MIN, MAX, CB,
             "Time HomA was started or resumed.\nUsed for elapsed time printing."),
            ("REFRESH_MS", 5, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "Refresh tooltip fades 60 frames per second"),
            ("REDISCOVER_SECONDS", 5, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "Check devices changes every x seconds"),
            ("RESUME_TEST_SECONDS", 5, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "> x seconds disappeared means system resumed"),
            ("RESUME_DELAY_RESTART", 5, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "Pause x seconds after resuming from suspend"),
            ("TIMER_SEC", 4, RW, INT, INT, 5, DEC, MIN, MAX, CB,
             "Tools Dropdown Menubar - Countdown Timer default"),
            ("TIMER_ALARM", 4, RW, STR, STR, 30, DEC, MIN, MAX, CB,
             ".wav sound file to play when timer ends."),
            ("LOG_EVENTS", 4, RO, BOOL, BOOL, 1, DEC, MIN, MAX, CB,
             "Override runCommand events'\nlogging and --verbose3 printing"),
            ("EVENT_ERROR_COUNT", 4, RO, INT, INT, 9, 0, MIN, MAX, CB,
             "To enable/disable View Dropdown menu 'Discovery errors'"),
            # 2024-12-29 TODO: SENSOR_XXX should be FLOAT not STR?
            ("SENSOR_CHECK", 4, RW, STR, STR, 6, DEC, MIN, MAX, CB,
             "Check `sensors`, CPU/GPU temperature\nand Fan speeds every x seconds"),
            ("SENSOR_LOG", 4, RW, STR, STR, 9, DEC, MIN, MAX, CB,
             "Log `sensors` every x seconds.\nLog more if Fan RPM speed changes"),
            ("FAN_GRANULAR", 4, RW, STR, STR, 5, DEC, MIN, MAX, CB,
             "Skip logging when Fan RPM changes <= FAN_GRANULAR"),
            # Device type global identifier hard-coded in "inst.type_code"
            ("HS1_SP", 3, RO, INT, INT, 2, DEC, MIN, MAX, CB,
             "TP-Link Kasa WiFi Smart Plug HS100,\nHS103 or HS110 using hs100.sh"),  #
            ("KDL_TV", 1, RO, INT, INT, 2, DEC, MIN, MAX, CB,
             "Sony Bravia KDL Android TV using REST API `curl`"),
            ("TCL_TV", 2, RO, INT, INT, 2, DEC, MIN, MAX, CB,
             "TCL Google Android TV using adb after `wakeonlan`"),
            ("DESKTOP", 6, RO, INT, INT, 3, DEC, MIN, MAX, CB,
             "Desktop Computer, Tower, NUC, Raspberry Pi, etc."),
            ("LAPTOP_B", 6, RO, INT, INT, 3, DEC, MIN, MAX, CB,
             "Laptop base ('CPU, GPU, Keyboard, Fans, Ports, etc.')"),
            ("LAPTOP_D", 6, RO, INT, INT, 3, DEC, MIN, MAX, CB,
             'Laptop display ("backlight can be turned\non/off separately from laptop base")'),
            ("SUDO_PASSWORD", 6, HD, STR, STR, WID, DEC, MIN, MAX, CB,
             "Sudo password required for laptop backlight"),
            ("BACKLIGHT_NAME", 6, RW, STR, STR, 30, DEC, MIN, MAX, CB,
             "E.G. 'intel_backlight', 'nvidia_backlight', etc."),
            ("BACKLIGHT_ON", 6, RW, STR, STR, 2, DEC, MIN, MAX, CB,
             "Sudo tee echo 'x' to\n'/sys/class/backlight/intel_backlight/bl_power'"),
            ("BACKLIGHT_OFF", 6, RW, STR, STR, 2, DEC, MIN, MAX, CB,
             "Sudo tee echo 'x' to\n'/sys/class/backlight/intel_backlight/bl_power'"),
            # Power all On/Off controls
            ("POWER_OFF_CMD_LIST", 6, RW, STR, LIST, 30, DEC, MIN, MAX, CB,
             'Run "Turn Off" for Computer'),
            ("POWER_ALL_EXCL_LIST", 6, RW, STR, LIST, 20, DEC, MIN, MAX, CB,
             'Exclude devices when powering all "ON" / "OFF"')
        ]

        return listTabs, listFields


class Computer(DeviceCommonSelf):
    """ Computer (from ifconfig, iwconfig, socket, /etc/hosts (NOT in arp))

        Read chassis type. If laptop there are two images - laptop_b (base)
        and laptop_d (display) which is akin to a monitor / tv with extra
        features. If a computer (not a laptop) then use one image.

        All desktops and laptops have Ethernet. The ethernet MAC address
        is used to identify the computer in arp_dicts dictionaries.

        All laptops have WiFi. The WiFi MAC address is used to identify
        the laptop display in arp_dicts dictionaries.

        A desktop with ethernet and WiFi will only have it's ethernet
        MAC address stored in arp_dicts dictionaries.
    """

    def __init__(self, mac=None, ip=None, name=None, alias=None):
        """ DeviceCommonSelf(): Variables used by all classes """
        DeviceCommonSelf.__init__(self, "Computer().")  # Define self.who
        _who = self.who + "__init()__:"

        # 192.168.0.10    Alien AW 17R3 WiFi 9c:b6:d0:10:37:f7
        # 192.168.0.12    Alien AW 17R3 Ethernet 28:f1:0e:2a:1a:ed
        self.mac = mac      # 28:f1:0e:2a:1a:ed
        self.ip = ip        # 192.168.0.12
        self.name = name    # Alien Base
        self.alias = alias  # AW 17R3 Ethernet

        self.edid = []      # Remains empty until requested. See homa-common.py
        self.xrandr = []    # Remains empty until requested. See homa-common.py

        self.nightlight_active = False  # Most popular color temperature app.
        self.redshift_active = False  # 2024-11-15 Not supported yet.
        self.eyesome_active = False  # Pippim color temperature & brightness.
        self.dimmer_active = False  # Pippim 2 out of 3 monitors dimmer.
        self.flux_active = False  # 2024-11-15 Not supported yet.
        self.sct_active = False  # 2024-11-15 Not supported yet.

        self.requires = ['ip', 'getent', 'hostnamectl', 'gsettings', 'cut',
                         'get-edid', 'parse-edid', 'xrandr']
        self.installed = []
        self.CheckDependencies(self.requires, self.installed)
        v2_print(self.who, "Dependencies:", self.requires)
        v2_print(self.who, "Installed?  :", self.installed)

        self.chassis = ""  # "desktop", "laptop", "convertible", "server",
        # "tablet", "handset", "watch", "embedded", "vm" and "container"

        if self.CheckInstalled('hostnamectl'):
            # 2024-12-16 TODO: convert to self.runCommand()
            #   universal_newlines: https://stackoverflow.com/a/38182530/6929343
            machine_info = sp.check_output(["hostnamectl", "status"], universal_newlines=True)
            m = re.search('Chassis: (.+?)\n', machine_info)
            self.chassis = m.group(1)  # TODO: Use this for Dell Virtual temp/fan driver
        else:
            self.chassis = "desktop"  # "desktop", "laptop", "convertible", "server",
            # "tablet", "handset", "watch", "embedded", "vm" and "container"

        if self.chassis == "laptop":
            if name:  # name can be None
                self.name = name + " (Base)"  # There will be two rows, one 'Display'
            self.type = "Laptop Computer"
            self.type_code = GLO['LAPTOP_B']
        else:
            self.type = "Desktop Computer"
            self.type_code = GLO['DESKTOP']
        self.power_status = "?"  # Can be "ON", "OFF" or "?"
        v2_print(self.who, "chassis:", self.chassis, " | type:", self.type)

        # When reading /etc/hosts match from MAC address if available
        # or Static IP address if MAC address not available.
        if self.name is None:
            self.name = ""  # Computer name from /etc/hosts
        if self.alias is None:
            self.alias = ""  # Computer alias from /etc/hosts

        self.ether_name = ""  # eth0, enp59s0, etc
        self.ether_mac = ""  # aa:bb:cc:dd:ee:ff
        self.ether_ip = ""  # 192.168.0.999
        self.wifi_name = ""  # wlan0, wlp60s0, etc
        self.wifi_mac = ""  # aa:bb:cc:dd:ee:ff
        self.wifi_ip = ""  # 192.168.0.999

        import socket
        _socks = [i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None)]
        #print("socks:", _socks)  # socks: ['127.0.1.1', '127.0.1.1', '127.0.1.1',
        # '192.168.0.12', '192.168.0.12', '192.168.0.12',
        # '192.168.0.10', '192.168.0.10', '192.168.0.10']

        self.Interface()  # Initial values
        self.NightLightStatus()

    def Interface(self, forgive=False):
        """ Return name of interface that is up. Either ethernet first or
            wifi second. If there is no interface return blank.
        """

        _who = self.who + "Interface():"
        v2_print(_who, "Test if Ethernet and/or WiFi interface is up.")

        if not self.CheckInstalled('ip'):
            return

        command_line_list = ["ip", "addr"]
        event = self.runCommand(command_line_list, _who, forgive=forgive)

        if not event['returncode'] == 0:
            if forgive is False:
                v0_print(_who, "pipe.returncode:", pipe.returncode)
            return ""  # Return null string = False

        interface = event['output'].splitlines()

        # noinspection SpellCheckingInspection
        ''' `ip addr` output:
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: enp59s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 28:f1:0e:2a:1a:ed brd ff:ff:ff:ff:ff:ff
    inet 192.168.0.12/24 brd 192.168.0.255 scope global dynamic enp59s0
       valid_lft 598085sec preferred_lft 598085sec
3: wlp60s0: <BROADCAST,MULTICAST> mtu 1500 qdisc mq state DOWN group default qlen 1000
    link/ether 9c:b6:d0:10:37:f7 brd ff:ff:ff:ff:ff:ff
        '''

        name = mac = ip = ""
        self.ether_name = ""  # eth0, enp59s0, etc
        self.ether_mac = ""  # aa:bb:cc:dd:ee:ff
        self.ether_ip = ""  # 192.168.0.999
        self.wifi_name = ""  # wlan0, wlp60s0, etc
        self.wifi_mac = ""  # aa:bb:cc:dd:ee:ff
        self.wifi_ip = ""  # 192.168.0.999

        def parse_interface():
            """ Process last group of name, mac and ip """
            if ip and ip.startswith("127"):
                return  # local host "127.0.0.1" is not useful

            if name and name.startswith("e"):  # Ethernet
                self.ether_name = name  # eth0, enp59s0, etc
                self.ether_mac = mac  # aa:bb:cc:dd:ee:ff
                self.ether_ip = ip  # 192.168.0.999

            elif name and name.startswith("w"):  # WiFi
                self.wifi_name = name  # eth0, enp59s0, etc
                self.wifi_mac = mac  # aa:bb:cc:dd:ee:ff
                self.wifi_ip = ip  # 192.168.0.999
            else:
                v0_print(_who, "Error parsing name:", name, "mac:", mac, "ip:", ip)

        for line in interface:

            parts = line.split(":")
            if len(parts) == 3:
                if not name == "":  # First time skip blank name
                    parse_interface()
                name = parts[1].strip()
                mac = ip = ""
                continue

            if not mac:
                r = re.search("(?:[0-9a-fA-F]:?){12}", line)
                if r:
                    mac = r.group(0)

            elif not ip:
                r = re.search("[0-9]+(?:\.[0-9]+){3}", line)
                if r:
                    ip = r.group(0)
                    # print("\n name:", name, "mac:", mac, "ip:", ip, "\n")

        parse_interface()
        v3_print(_who, "self.ether_name:", self.ether_name, " | self.ether_mac:",
                 self.ether_mac, " | self.ether_ip:", self.ether_ip)
        v3_print(_who, "self.wifi_name :", self.wifi_name,  " | self.wifi_mac :",
                 self.wifi_mac,  " | self.wifi_ip :", self.wifi_ip)

        if self.ether_ip:  # Ethernet IP is preferred if available.
            return self.ether_ip

        if self.wifi_ip:  # Ethernet IP unavailable, use WiFi IP if available
            return self.wifi_ip

        return ""  # Return null string = False

    def isDevice(self, forgive=False):
        """ Test if passed ip == ethernet ip or WiFi ip.
            Initially a laptop base could be assigned with IP but now it
            is assigned as a laptop display. A laptop will have two on/off
            settings - one for the base and one for the display. It will have
            two images in the treeview.

            A desktop will only have a single image and desktop on/off option.

        """
        _who = self.who + "isDevice():"
        v2_print(_who, "Test if device is Computer:", self.ip)

        if forgive:
            pass

        if self.ip == self.ether_ip or self.ip == self.wifi_ip:
            return True

        return False

    def TurnOn(self, forgive=False):
        """ Not needed because computer is always turned on. Defined for
            right click menu conformity reasons.
        """
        _who = self.who + "TurnOn():"
        v2_print(_who, "Turn On Computer:", self.ip)

        if forgive:
            pass

        self.power_status = "ON"  # Can be "ON", "OFF" or "?"
        return self.power_status  # Really it is "AWAKE"

    def TurnOff(self, forgive=False):
        """ Turn off computer with GLO['POWER_OFF_CMD_LIST'] which contains:
                systemctl suspend

            Prior to calling cp.TurnOff(), Application().TurnOff() calls
            SetAllPower("OFF") to turn off all other devices. If rebooting, rather
            than suspending, then devices are left powered up.
        """
        _who = self.who + "TurnOff():"
        v2_print(_who, "Turn Off Computer:", self.ip)

        if forgive:
            pass

        command_line_list = GLO['POWER_OFF_CMD_LIST']  # systemctl suspend
        _event = self.runCommand(command_line_list, _who, forgive=forgive)

        self.power_status = "OFF"  # Can be "ON", "OFF" or "?"
        return self.power_status  # Really it is "SLEEP"

    def PowerStatus(self, forgive=False):
        """ The computer is always "ON" """

        _who = self.who + "PowerStatus():"
        v2_print(_who, "Test if device is powered on:", self.ip)

        if forgive:
            pass

        self.power_status = "ON"
        return self.power_status

    def NightLightStatus(self, forgive=False):
        """ Return True if "On" or "Off"
            gsettings get org.gnome.settings-daemon.plugins.color
                night-light-enabled

            percent = cat /usr/local/bin/.eyesome-percent | cut -F1
            if percent < 100 enabled = True

        """

        _who = self.who + "NightLightStatus():"
        v2_print(_who, "Test if Night Light is active:", self.ip)

        if forgive:
            pass

        if self.CheckInstalled('gsettings'):
            command_line_list = ["gsettings", "get",
                                 "org.gnome.settings-daemon.plugins.color",
                                 "night-light-enabled"]
            command_line_str = ' '.join(command_line_list)
            pipe = sp.Popen(command_line_list, stdout=sp.PIPE, stderr=sp.PIPE)
            text, err = pipe.communicate()  # This performs .wait() too

            v3_print(_who, "Results from '" + command_line_str + "':")
            v3_print(_who, "text: '" + text.strip() + "'")
            v3_print(_who, "err: '" + err.strip() + "'  | pipe.returncode:",
                     pipe.returncode)

            if pipe.returncode == 0:
                night_light = text.strip()
                if night_light == "True":
                    return "ON"
                elif night_light == "False":
                    return "OFF"
        else:
            pass  # if no `gsettings` then no GNOME Nightlight

        if self.CheckInstalled('cut'):
            # 2024-12-16 TODO: Read file directly. Use EYESOME_PERCENT_FNAME
            command_line_str = 'cut -d" " -f1 < /usr/local/bin/.eyesome-percent'
            v3_print("\n" + _who, "command_line_str:", command_line_str, "\n")
            f = os.popen(command_line_str)

            text = f.read().splitlines()
            returncode = f.close()  # https://stackoverflow.com/a/70693068/6929343
            v3_print(_who, "text:", text, "returncode:", returncode)

            if returncode is None and text is not None and len(text) == 1:
                try:
                    percent = int(text[0])
                    v3_print(_who, "eyesome percent:", percent)
                    if percent == 100:
                        return "OFF"  # 100 % sunlight
                    else:
                        return "ON"
                except ValueError:
                    v3_print(_who, "eyesome percent VALUE ERROR:", text[0])

        return "ON"  # Default to always turn bias lights on


class NetworkInfo(DeviceCommonSelf):
    """ Network Information from arp and getent (/etc/hosts)

        ni = NetworkInfo() called on startup
        rd = NetworkInfo() rediscovery called every minute

        LISTS
        self.devices     Devices from `arp -a`
        self.hosts       Devices from `getent hosts`
        self.host_macs   Optional MAC addresses at end of /etc/hosts
        self.view_order  Treeview list of MAC addresses

        LISTS of DICTIONARIES
        self.arp_dicts   First time discovered, thereafter read from disk
        self.instances   TclGoogleAndroidTV, SonyBraviaKdlTV, etc. instances

        # Miscellaneous - nmap takes 10 seconds so call on demand with wait cursor
        # nmap 192.168.0.0/24

        # iw list: https://superuser.com/a/788789
        # iw list wlan0 scan

        # Treeview line wrap in columns on resize
        # https://stackoverflow.com/q/51131812/6929343
    """

    def __init__(self):
        """ DeviceCommonSelf(): Variables used by all classes """
        DeviceCommonSelf.__init__(self, "NetworkInfo().")  # Define self.who

        global cp  # cp = Computer() instance
        cp.Interface()  # Get current WiFi and Ethernet settings.
        _who = self.who + "__init__():"  # Long-winded debug string not used.

        self.requires = ['arp', 'getent', 'timeout', 'curl', 'adb']
        self.installed = []
        self.CheckDependencies(self.requires, self.installed)
        v2_print(self.who, "Dependencies:", self.requires)
        v2_print(self.who, "Installed?  :", self.installed)

        self.last_row = ""  # used by rediscovery processing one row at a time

        # Create self.devices from arp
        v3_print("\n===========================  arp -a  ===========================")
        # Format: 'SONY.LAN (192.168.0.19) at ac:9b:0a:df:3f:d9 [ether] on enp59s0'
        self.devices = []
        for device in os.popen('arp -a'):
            self.devices.append(device)
            v3_print(device, end="")

        # Create self.hosts from /etc/hosts
        v3_print("\n========================  getent hosts  ========================")
        # Format: '192.168.0.19    SONY.LAN Sony Bravia KDL TV Ethernet  ac:9b:0a:df:3f:d9'
        self.hosts = []
        for host in os.popen('getent hosts'):
            self.hosts.append(host)
            v3_print(host, end="")

        # Read self.hosts (/etc/hosts) to get alias to assign device/arps
        v3_print("\n=========================  host MACs  ==========================")
        v3_print("MAC address".ljust(18), "IP".ljust(14), "Name".ljust(15), "Alias\n")
        # get mac addresses: https://stackoverflow.com/a/26892371/6929343
        import re
        p = re.compile(r'(?:[0-9a-fA-F]:?){12}')  # regex MAC Address
        _host_data = {}  # keyed by host_mac, value = list [IP, name, alias, host_mac, last_IP]
        self.host_macs = []
        for host in self.hosts:
            result = re.findall(p, host)  # regex MAC Address
            if result:
                # 192.168.0.16    SONY.WiFi android-47cd abb50f83a5ee 18:4F:32:8D:AA:97
                parts = host.split()
                name = parts[1]  # Can be "unknown" when etc/self.hosts has no details
                alias = ' '.join(parts[2:-1])
                ip = parts[0]
                # The above Android device has two self.host_macs:
                # ['47cd abb50f83', '18:4F:32:8D:AA:97'] 192.168.0.16
                mac = str(result[-1])
                host_mac = mac + "  " + ip.ljust(15) + name.ljust(16) + alias
                v3_print(host_mac)
                #host_dict = {"mac": mac, "ip": ip, "name": name, "alias": alias}
                # 2024-10-14 - Future conversion from host_mac to host_dict
                self.host_macs.append(host_mac)
                # Assign Computer() attributes
                if mac == cp.ether_mac or mac == cp.wifi_mac:
                    cp.name = name  # computer name
                    cp.alias = alias  # computer alias
                    if mac == cp.ether_mac and cp.ether_ip == "":
                        v3_print("Assigning cp.ether_mac:", ip)
                        cp.ether_ip = ip
                    if mac == cp.wifi_mac and cp.wifi_ip == "":
                        v3_print("Assigning cp.wifi_mac:", ip)
                        cp.wifi_ip = ip
            else:
                parts = host.split()
                name = parts[1]  # Can be "unknown" when etc/self.hosts has no details
                alias = ' '.join(parts[2:-1])
                ip = parts[0]
                # No MAC
                # ['47cd abb50f83', '18:4F:32:8D:AA:97'] 192.168.0.16
                mac = "No MAC for: " + ip
                host_mac = mac + "  " + ip.ljust(15) + name.ljust(16) + alias
                v3_print(host_mac)
                #host_dict = {"mac": mac, "ip": ip, "name": name, "alias": alias}
                # 2024-10-14 - Future conversion from host_mac to host_dict
                self.host_macs.append(host_mac)
                # Assign Computer() attributes
                if ip == cp.ether_ip or ip == cp.wifi_ip:
                    cp.name = name  # computer name
                    cp.alias = alias  # computer alias
                    if cp.ether_ip == "":
                        cp.ether_ip = ip  # Can be overridden by MAC later
                    if cp.wifi_ip == "":
                        cp.wifi_ip = ip  # Can be overridden by MAC later

        # Append self.devices with Computer() attributes
        v3_print("\n==================== cp = Computer.__init()  ===================")
        # Format inside /etc/hosts
        # 192.168.0.10    Alien  AW 17R3 WiFi        9c:b6:d0:10:37:f7
        # 192.168.0.12    Alien  AW 17R3 Ethernet    28:f1:0e:2a:1a:ed
        #print(_who, "cp.name:", cp.name)
        #print(_who, "cp.alias:", cp.alias)

        # Add mandatory computer platform ethernet that arp never reports
        # Format: 'SONY.LAN (192.168.0.19) at ac:9b:0a:df:3f:d9 [ether] on enp59s0'
        ip = cp.ether_ip
        if not ip:
            ip = "Unknown"
        device = cp.name + " (" + ip + ") at "
        device += cp.ether_mac + " [ether] on " + cp.ether_name
        # TODO change device when connected to WiFi
        self.devices.append(device)
        v3_print(device, end="")
        #print(device)

        # Add optional laptop WiFi that arp never reports
        if cp.chassis == "laptop":
            ip = cp.wifi_ip
            if not ip:
                ip = "Unknown"
            device = cp.name + " (" + ip + ") at "
            device += cp.wifi_mac + " [ether] on " + cp.wifi_name
            # TODO change device when connected to WiFi
            self.devices.append(device)
            v3_print("\n" + device, end="")
            #print(device)

        v3_print("\n=========================  arp MACs  ===========================")
        v3_print("MAC address".ljust(18), "IP".ljust(14), "Name".ljust(15), "Alias\n")
        # get mac addresses: https://stackoverflow.com/a/26892371/6929343
        import re
        _arp_data = {}  # keyed by arp_mac, value = list [IP, name, alias, arp_mac, last_IP]
        self.arp_dicts = []  # First time discovered, thereafter read from disk
        self.instances = []  # TclGoogleAndroidTV, SonyBraviaKdlTV, etc. instances
        self.view_order = []  # Sortable list of MAC addresses matching instances
        for device in self.devices:
            # SONY.light (192.168.0.15) at 50:d4:f7:eb:41:35 [ether] on enp59s0
            parts = device.split()
            name = parts[0]  # Can be "unknown" when etc/self.hosts has no details
            ip = parts[1][1:-1]
            mac = parts[3]
            alias = self.get_alias(mac)
            arp_mac = mac + "  " + ip.ljust(15) + name.ljust(16) + alias
            v3_print(arp_mac)
            mac_dict = {"mac": mac, "ip": ip, "name": name, "alias": alias}
            self.arp_dicts.append(mac_dict)

        #print("arp_dicts:", self.arp_dicts)  # 2024-11-09 now has Computer()
        #print("instances:", self.instances)  # Empty list for now
        #print("view_order:", self.view_order)  # Empty list for now
        #print("cp.ether_name:", cp.ether_name,  " | cp.ether_mac:",
        #      cp.ether_mac,  " | cp.ether_ip:", cp.ether_ip)
        # name: enp59s0  | mac: 28:f1:0e:2a:1a:ed  | ip: 192.168.0.12
        #print("cp.wifi_name :", cp.wifi_name, " | cp.wifi_mac :",
        #      cp.wifi_mac, " | cp.wifi_ip :", cp.wifi_ip)
        # name : wlp60s0  | mac : 9c:b6:d0:10:37:f7  | ip : 192.168.0.10

    def adb_reset(self, background=False):
        """ Kill and restart ADB server. Takes 3 seconds so run in background """
        _who = self.who + "adb_reset():"

        command_line_list = \
            ["adb", "kill-server", "&&", "adb", "start-server"]
        if background:
            command_line_list.append("&")  # Has no effect in runCommand()

        command_line_str = ' '.join(command_line_list)

        if self.CheckInstalled('adb'):
            v1_print(_who, "Running: '" + command_line_str + "'")
        else:
            v1_print(_who, "adb is not installed. Skipping")
            return

        # Subprocess run external command
        self.runCommand(command_line_list, _who)

    def get_alias(self, mac):
        """ Get Alias from self.hosts matching mac address
            host_mac = mac + "  " + ip.ljust(15) + name.ljust(16) + alias
        """
        _who = self.who + "get_alias():"

        for host_mac in self.host_macs:
            if mac in host_mac:
                return host_mac[50:]

        return "No Alias"

    def make_temp_file(self, stuff=None):
        """ Make temporary file with optional text. - NOT USED but Works
            Caller must call os.remove(temp_fname)
            :returns: temp_fname (temporary filename /run/user/1000/homa.XXXXXXXX)
        """
        _who = self.who + "make_temp_file():"

        # Create temporary file in RAM for curl command
        # TODO: check dir /run/user/1000, if not use /tmp
        command_line_list = ["mktemp", "--tmpdir=/run/user/1000", "homa.XXXXXXXX"]
        event = self.runCommand(command_line_list, _who)

        if event['returncode'] != 0:
            return

        temp_fname = event['output']

        if stuff is None:
            return temp_fname

        v3_print("\n" + _who, "temp_fname:", temp_fname)
        with open(temp_fname, "w") as text_file:
            text_file.write(stuff)
            v3_print("\n" + _who, "stuff:", stuff)

        v3_print("\n" + _who, temp_fname, "contents:")
        with open(temp_fname, 'r') as f:
            v3_print(f.read().strip())

        return temp_fname

    def curl(self, JSON_str, subsystem, ip, forgive=False):
        """ Use sub-process curl to communicate with REST API
            2024-10-21 - Broken for Sony Picture On/Off and Sony On/Off.
                Use os_curl instead to prevent error message:
                     {'error': [403, 'Forbidden']}
        """
        _who = self.who + "curl():"
        # $1 = JSON String in pretty format converted to file for cURL --data.
        # $2 = Sony subsystem to talk to, eg accessControl, audio, system, etc.
        # 3  = variable name to receive reply from TV
        if not self.dependencies_installed:
            v1_print(_who, "curl dependencies are not installed. Aborting...")
            return None

        command_line_list = ["timeout", GLO['CURL_TIME'], "curl", "-s",  # -s=Silent
                             "-H", '"Content-Type: application/json; charset=UTF-8"',
                             "-H", '"X-Auth-PSK: ' + GLO['SONY_PWD'] + '"',
                             "--data", JSON_str,  # err: is unknown
                             "http://" + ip + "/sony/" + subsystem]

        event = self.runCommand(command_line_list, _who, forgive=forgive)

        if event['returncode'] != 0:
            return {"result": [{"status": event['returncode']}]}

        try:
            reply_dict = json.loads(str(event['output']))  # str to convert from bytes
        except ValueError:
            v2_print(_who, "Invalid 'output':", event['output'])  # Sample below on 2024-10-08
            # NetworkInfo().curl() Invalid 'text': <html><head></head><body>
            # 		This document has moved to a new <a href="http://192.168.0.1/login.htm">location</a>.
            # 		Please update your documents to reflect the new location.
            # 		</body></html>
            reply_dict = {"result": [{"status": _who + "json.loads(event['output']) failed!"}]}

        v3_print(_who, "reply_dict:", reply_dict)
        return reply_dict

    def os_curl(self, JSON_str, subsystem, ip, forgive=False):
        """ Use os.popen curl to communicate with REST API
            2024-10-21 - os_curl supports Sony Picture On/Off using os.popen()
        """
        _who = self.who + "os_curl():"

        self.cmdCaller = _who  # self.cmdXxx vars in DeviceCommonSelf() class
        self.cmdStart = time.time()
        self.cmdCommand = [
            'timeout', str(GLO['CURL_TIME']), 'curl',
            '-s', '-H', '"Content-Type: application/json; charset=UTF-8"',
            '-H', '"X-Auth-PSK: ' + GLO['SONY_PWD'] + '"', '--data', "'" + JSON_str + "'",
            'http://' + ip + '/sony/' + subsystem
        ]
        self.cmdString = 'timeout ' + str(GLO['CURL_TIME']) + ' curl' +\
            ' -s -H "Content-Type: application/json; charset=UTF-8" ' +\
            ' -H "X-Auth-PSK: ' + GLO['SONY_PWD'] + '" --data ' + "'" + JSON_str + "'" +\
            ' http://' + ip + '/sony/' + subsystem

        #v3_print("\n" + _who, "self.cmdString:", self.cmdString, "\n")

        ''' run command with os.popen() because sp.Popen() fails '''
        f = os.popen(self.cmdString + " 2>&1")
        text = f.read().splitlines()
        returncode = f.close()  # https://stackoverflow.com/a/70693068/6929343
        v3_print(_who, "text:", text)

        ''' log event and v3_print debug lines '''
        self.cmdOutput = "" if returncode != 0 else text
        self.cmdError = "" if returncode == 0 else text
        self.cmdReturncode = returncode
        self.cmdDuration = time.time() - self.cmdStart
        who = self.cmdCaller + " logEvent():"
        self.logEvent(who, forgive=forgive, log=True)

        if returncode is not None:
            if forgive is False:
                v0_print(_who, "text:", text)
                v0_print(_who, "returncode:", returncode)
            return {"result": [{"status": returncode}]}

        try:
            # TODO: check if more than one line returned
            reply_dict = json.loads(text[0])
        except ValueError:
            v2_print(_who, "Invalid 'text':", text)  # Sample below on 2024-10-08
            # NetworkInfo().curl() Invalid 'text': <html><head></head><body>
            # 		This document has moved to a new <a href="http://192.168.0.1/login.htm">location</a>.
            # 		Please update your documents to reflect the new location.
            # 		</body></html>
            reply_dict = {"result": [{"status": _who + "json.loads(text) failed!"}]}

        v3_print(_who, "reply_dict:", reply_dict)
        return reply_dict

    def arp_for_mac(self, mac):
        """ Get arp_dict by mac address.
            :param mac: MAC address
            :returns: arp_dict
        """
        _who = self.who + "arp_for_mac():"

        for arp_dict in self.arp_dicts:
            if arp_dict['mac'] == mac:
                return arp_dict

        v1_print(_who, "mac address unknown: '" + mac + "'")

        return {}  # TODO: Format dictionary with 'mac': and error

    def inst_for_mac(self, mac):
        """ Get instance by mac address.
            :param mac: MAC address
            :returns: instance
        """
        _who = self.who + "arp_for_mac():"

        for inst in self.instances:
            if inst['mac'] == mac:
                return inst

        v1_print(_who, "mac address unknown: '" + mac + "'")

        return {}  # TODO: Format dictionary with 'mac': and error


class LaptopDisplay(DeviceCommonSelf):
    """ Laptop display: /sys/class/backlight/<GLO['BACKLIGHT_NAME']>

        /sys/class/backlight/intel_backlight/brightness:1935
        /sys/class/backlight/intel_backlight/actual_brightness:1935
        /sys/class/backlight/intel_backlight/max_brightness:7500
        /sys/class/backlight/intel_backlight/device/enabled:enabled
        /sys/class/backlight/intel_backlight/bl_power:0

        Great reference: https://wiki.archlinux.org/title/Backlight

    """

    def __init__(self, mac=None, ip=None, name=None, alias=None):
        """ DeviceCommonSelf(): Variables used by all classes """
        DeviceCommonSelf.__init__(self, "LaptopDisplay().")  # Define self.who
        _who = self.who + "__init()__:"

        # 192.168.0.10    Alien AW 17R3 WiFi 9c:b6:d0:10:37:f7
        # 192.168.0.12    Alien AW 17R3 Ethernet 28:f1:0e:2a:1a:ed
        self.mac = mac      # 9c:b6:d0:10:37:f7
        self.ip = ip        # 192.168.0.10
        self.name = name    # Alien Display
        self.alias = alias  # AW 17R3 WiFi
        self.requires = ['ip', 'getent', 'hostnamectl', 'adb']
        self.installed = []
        self.CheckDependencies(self.requires, self.installed)
        v2_print(self.who, "Dependencies:", self.requires)
        v2_print(self.who, "Installed?  :", self.installed)

        self.chassis = ""  # "desktop", "laptop", "convertible", "server",
        # "tablet", "handset", "watch", "embedded", "vm" and "container"

        if self.CheckInstalled('hostnamectl'):
            # 2024-12-16 TODO: convert to self.runCommand()
            #   universal_newlines: https://stackoverflow.com/a/38182530/6929343
            machine_info = sp.check_output(["hostnamectl", "status"], universal_newlines=True)
            m = re.search('Chassis: (.+?)\n', machine_info)
            self.chassis = m.group(1)  # TODO: Use this for Dell Virtual temp/fan driver
        else:
            self.chassis = "desktop"  # "desktop", "laptop", "convertible", "server",
            # "tablet", "handset", "watch", "embedded", "vm" and "container"

        self.type = "Laptop Display"
        self.type_code = GLO['LAPTOP_D']
        self.power_status = "?"  # Can be "ON", "OFF" or "?"
        if name:  # name can be None
            self.name = name + " (Display)"  # There will be two rows, one 'Base'
        v2_print(_who, "chassis:", self.chassis, " | type:", self.type)

        self.ether_name = cp.ether_name  # eth0, enp59s0, etc
        self.ether_mac = cp.ether_mac  # aa:bb:cc:dd:ee:ff
        self.ether_ip = cp.ether_ip  # 192.168.0.999
        self.wifi_name = cp.wifi_name  # wlan0, wlp60s0, etc
        self.wifi_mac = cp.wifi_mac  # aa:bb:cc:dd:ee:ff
        self.wifi_ip = cp.wifi_ip  # 192.168.0.999

        self.app = None  # Parent app for calling GetPassword() method.

    def isDevice(self, forgive=False):
        """ Test if passed ip == ethernet ip or WiFi ip.
            Initially a laptop base could be assigned with IP but now it
            is assigned as a laptop display. A laptop will have two images
            in the treeview - laptop_b.jpg and laptop_d.jpg

            A desktop will have a single image - desktop.jpg.

        """
        _who = self.who + "isDevice():"
        v2_print(_who, "Test if device is Laptop Display:", self.ip)

        if forgive:
            pass  # Dummy argument for uniform instance parameter list

        if cp.chassis != "laptop":
            return False

        if self.ip == cp.ether_ip or self.ip == cp.wifi_ip:
            return True

        return False

    def TurnOn(self, forgive=False):
        """ Return True if "On" or "Off", False if no communication
            If forgive=True then don't report pipe.returncode != 0

            echo <PASSWORD> |
            sudo -S echo 0 |
            sudo tee /sys/class/backlight/intel_backlight/bl_power

        Note: Adding user to group "video" DOES NOT allow:
            echo 4000 > /sys/class/backlight/intel_backlight/brightness
            bash: /sys/class/backlight/intel_backlight/brightness: Permission denied

        """
        _who = self.who + "TurnOn():"
        v2_print(_who, "Turn On Laptop Display:", self.ip)

        if forgive:
            pass  # Dummy argument for uniform instance parameter list

        self.SetPower("ON", forgive=forgive)
        return self.power_status

    def TurnOff(self, forgive=False):
        """ Return True if "On" or "Off", False if no communication
            If forgive=True then don't report pipe.returncode != 0
            echo 4 > /sys/class/backlight/intel_backlight/bl_power

            echo <PASSWORD> |
            sudo -S echo 4 |
            sudo tee /sys/class/backlight/intel_backlight/bl_power

        Note: Adding user to group "video" DOES NOT allow:
            echo 4000 > /sys/class/backlight/intel_backlight/brightness
            bash: /sys/class/backlight/intel_backlight/brightness: Permission denied

        """
        _who = self.who + "TurnOn():"
        v2_print(_who, "Turn Off Laptop Display:", self.ip)

        if forgive:
            pass  # Dummy argument for uniform instance parameter list

        self.SetPower("OFF", forgive=forgive)
        return self.power_status

    def PowerStatus(self, forgive=False):
        """ Return "ON", "OFF" or "?" """

        _who = self.who + "PowerStatus():"
        v2_print(_who, "Test if device is powered on:", self.ip)
        if forgive:
            pass  # Dummy argument for uniform instance parameter list

        power = '/sys/class/backlight/' + GLO['BACKLIGHT_NAME'] + '/bl_power'
        command_line_list = ['cat', power]
        event = self.runCommand(command_line_list, _who)

        string = event['output']
        if string == GLO['BACKLIGHT_ON']:
            self.power_status = "ON"  # Can be "ON", "OFF" or "?"
        elif string == GLO['BACKLIGHT_OFF']:
            self.power_status = "OFF"  # Can be "ON", "OFF" or "?"
        else:
            v0_print(_who, "Invalid " + power + " value:", string)
            self.power_status = "?"  # Can be "ON", "OFF" or "?"

        return self.power_status

    def SetPower(self, status, forgive=False):
        """ Set Laptop Display Backlight Power 'OFF' or 'ON'
            If forgive=True then don't report pipe.returncode != 0
        """

        _who = self.who + "SetPower(" + status + "):"
        v2_print(_who, "Set Laptop Display Power to:", status)

        # Sudo password required for powering laptop backlight on/off
        if GLO['SUDO_PASSWORD'] is None:
            GLO['SUDO_PASSWORD'] = self.app.GetPassword()
            self.app.EnableMenu()
            if GLO['SUDO_PASSWORD'] is None:
                return "?"  # Cancel button (256) or escape or 'X' on window decoration (64512)

        power = '/sys/class/backlight/' + GLO['BACKLIGHT_NAME'] + '/bl_power'
        if status == "ON":
            echo = GLO['BACKLIGHT_ON']
        elif status == "OFF":
            echo = GLO['BACKLIGHT_OFF']
        else:
            echo = "?"  # For pycharm reference checker
            V0_print(_who, "Invalid status (no 'ON' or 'OFF':", status)
            exit()

        #command_line_str = "echo PASSWORD | sudo -S echo X | sudo tee BL_POWER"

        self.cmdStart = time.time()
        cmd1 = sp.Popen(['echo', GLO['SUDO_PASSWORD']], stdout=sp.PIPE)
        cmd2 = sp.Popen(['sudo', '-S', 'echo', echo], stdin=cmd1.stdout, stdout=sp.PIPE)
        pipe = sp.Popen(['sudo', 'tee', power], stdin=cmd2.stdout, stdout=sp.PIPE,
                        stderr=sp.PIPE)

        self.cmdCaller = _who
        who = self.cmdCaller + " logEvent():"
        self.cmdCommand = ["echo", "GLO['SUDO_PASSWORD']", "|", "sudo", "-S", "echo",
                           echo, "|", "sudo", "tee", power]
        self.cmdString = ' '.join(self.cmdCommand)
        self.cmdOutput = pipe.stdout.read().decode().strip()
        self.cmdError = pipe.stdout.read().decode().strip()
        self.cmdReturncode = pipe.returncode
        self.cmdReturncode = 0 if self.cmdReturncode is None else self.cmdReturncode
        self.cmdDuration = time.time() - self.cmdStart
        self.logEvent(who, forgive=forgive, log=True)
        self.power_status = status


class SmartPlugHS100(DeviceCommonSelf):
    """ TP-Link Kasa Smart Plug HS100/HS103/HS110 using hs100.sh
        https://github.com/branning/hs100
        TPlink is the manufacturing brand. Kasa, Deco, and Tapo are all product lines produced by TPlink.
    """

    def __init__(self, mac, ip, name, alias):
        """ DeviceCommonSelf(): Variables used by all classes """
        DeviceCommonSelf.__init__(self, "SmartPlugHS100().")  # Define self.who

        # 192.168.0.15    SONY.Light hs100 Sony TV Bias Light 50:d4:f7:eb:41:35
        # 192.168.0.20    TCL.Light hs100 TCL TV Bias Light 50:d4:f7:eb:46:7c
        self.mac = mac      # 50:d4:f7:eb:41:35
        self.ip = ip        # 192.168.0.15
        self.name = name    # SONY.Light
        self.alias = alias  # hs100 Sony TV Bias Light

        self.type = "TP-Link HS100 Smart Plug"
        self.type_code = GLO['HS1_SP']
        self.power_status = "?"  # Can be "ON", "OFF" or "?"
        self.requires = ['hs100.sh', 'nc', 'base64', 'od', 'nmap', 'shasum', 'arp']
        self.installed = []
        self.CheckDependencies(self.requires, self.installed)

        _who = self.who + "__init__():"
        v3_print(_who, "Dependencies:", self.requires)
        v3_print(_who, "Installed?  :", self.installed)
        if not self.dependencies_installed:
            v1_print(_who, "Smart Plug hs100.sh dependencies are not installed.")

    def isDevice(self, forgive=False):
        """ Return True if "On" or "Off", False if no communication
            If forgive=True then don't report pipe.returncode != 0
        """
        _who = self.who + "isDevice():"
        v2_print(_who, "Test if device is TP-Link Kasa HS100 Smart Plug:", self.ip)

        Reply = self.PowerStatus(forgive=forgive)  # ON, OFF or N/A
        if Reply == "N/A":
            v2_print(_who, self.ip, "Reply = 'N/A' - Not a Smart Plug!")
            return False

        if Reply == "ON" or Reply == "OFF":
            v2_print(_who, self.ip, "- Valid Smart Plug")
            return True

        v2_print(_who, self.ip,
                 "- Not a Smart Plug! (or powered off). Reply was: '" + Reply + "'.")

        return False

    def TurnOn(self, forgive=False):
        """ Turn on TP-Link Smart Plug using hs100.sh script.
            If forgive=True then don't report pipe.returncode != 0
        """
        _who = self.who + "TurnOn():"
        v2_print(_who, "Turn On TP-Link Kasa HS100 Smart Plug:", self.ip)

        Reply = self.PowerStatus(forgive=forgive)  # Get current power status

        if Reply == "?":
            v2_print(_who, self.ip, "- Not a Smart Plug!")
            return "?"

        if Reply == "ON":
            v2_print(_who, self.ip, "- is already turned on. Skipping")
            return "ON"

        self.SetPower("ON")
        v2_print(_who, self.ip, "- Smart Plug turned 'ON'")
        return "ON"

    def TurnOff(self, forgive=False):
        """ Turn off TP-Link Smart Plug using hs100.sh script.
            If forgive=True then don't report pipe.returncode != 0
        """
        _who = self.who + "TurnOn():"
        v2_print(_who, "Turn Off TP-Link Kasa HS100 Smart Plug:", self.ip)

        Reply = self.PowerStatus(forgive=forgive)

        if Reply == "?":
            v2_print(_who, self.ip, "- Not a Smart Plug!")
            return "?"

        if Reply == "OFF":
            v2_print(_who, self.ip, "- is already turned off. Skipping")
            return "OFF"

        self.SetPower("OFF")
        v2_print(_who, self.ip, "- Smart Plug turned 'OFF'")
        return "OFF"

    def PowerStatus(self, forgive=False):
        """ Return True if "On" or "Off", False if no communication
            If forgive=True then don't report pipe.returncode != 0

            NOTE1: Occasionally a HS103 smart plug stops reporting status.
            First try unplugging and replugging into wall outlet.
            The try turning it off/on with Kasa phone software.
            Then try with "hs100.sh off -i <IP>"
                          "hs100.sh on -i <IP>"
            Then rerun "homa.py -v" to see it if shows up in device list

            NOTE2: It takes 0.035-0.51 seconds to discover something NOT a plug
                   It usually takes .259 to 2.0 seconds to discover it is a plug
        """

        _who = self.who + "PowerStatus():"
        v2_print(_who, "Test TP-Link Kasa HS100 Smart Plug Power Status:", self.ip)

        command_line_list = ["hs100.sh", "check", "-i", self.ip]
        event = self.runCommand(command_line_list, _who, forgive=forgive)
        if not event['returncode'] == 0:
            return "ERROR"

        Reply = event['output']
        parts = Reply.split()
        if len(parts) != 2:
            v2_print(_who, self.ip, "- Not a Smart Plug!", parts)
            return "N/A"

        if parts[1] == "ON" or parts[1] == "OFF":
            v2_print(_who, self.ip, "Smart Plug is", "'" + parts[1] + "'")
            self.power_status = parts[1]  # Can be "ON", "OFF" or "?"
            return self.power_status

        v2_print(_who, self.ip, "- Not a Smart Plug! (or powered off)")
        self.power_status = "?"  # Can be "ON", "OFF" or "?"
        return self.power_status

    def SetPower(self, status):
        """ Set Power to status, 'OFF' or 'ON'
            Note hs100.sh requires lower() case
            If forgive=True then don't report pipe.returncode != 0
        """

        _who = self.who + "SetPower(" + status + "):"
        v2_print(_who, "Turn TP-Link Kasa HS100 Smart Plug '" + status + "'")

        command_line_list = \
            ["timeout", GLO['PLUG_TIME'], "hs100.sh", status.lower(), "-i", self.ip]

        _event = self.runCommand(command_line_list, _who)
        # Return code is always 0, even if plug doesn't exist. No text returned

        self.power_status = status  # Can be "ON", "OFF" or "?"


class SonyBraviaKdlTV(DeviceCommonSelf):
    """ Sony Bravia KDL TV

    Sources:

https://gist.github.com/kalleth/e10e8f3b8b7cb1bac21463b0073a65fb#cec-sonycec
https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/audio/v1_0/setAudioVolume/index.html
https://developer.sony.com/develop/audio-control-api/get-started/http-example#tutorial-step-2
https://en.wikipedia.org/wiki/CURL
https://stackoverflow.com/questions/7172784/how-do-i-post-json-data-with-curl
https://stackoverflow.com/questions/2829613/how-do-you-tell-if-a-string-contains-another-string-in-posix-sh

    """

    def __init__(self, mac, ip, name, alias):
        """ DeviceCommonSelf(): Variables used by all classes """
        DeviceCommonSelf.__init__(self, "SonyBraviaKdlTV().")  # Define self.who

        # 192.168.0.16    SONY.WiFi Sony Bravia KDL TV WiFi 18:4f:32:8d:aa:97
        # 192.168.0.19    SONY.LAN Sony Bravia KDL TV Ethernet ac:9b:0a:df:3f:d9
        self.mac = mac      # ac:9b:0a:df:3f:d9
        self.ip = ip        # 192.168.0.19
        self.name = name    # SONY.LAN
        self.alias = alias  # Sony Bravia KDL TV Ethernet

        self.type = "SonyBraviaKdlTV"
        self.type_code = GLO['KDL_TV']
        self.power_status = "?"  # Can be "ON", "OFF" or "?"
        self.power_saving_mode = "?"  # set with PowerSavingMode()
        self.volume = "?"  # Set with getVolume()

        self.requires = ['curl']
        self.installed = []
        self.CheckDependencies(self.requires, self.installed)
        _who = self.who + "__init__():"
        v3_print(_who, "Dependencies:", self.requires)
        v3_print(_who, "Installed?  :", self.installed)

        if not self.dependencies_installed:
            v1_print(_who, "Sony Bravia KDL TV dependencies are not installed.")

    def PowerStatus(self, forgive=False):
        """ Return "ON", "OFF" or "?" if error.
            Called by TestSonyOn, TestSonyOff and TestIfSony methods.

https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/getPowerStatus/index.html

        """

        _who = self.who + "PowerStatus():"
        v2_print(_who, "Get Power Status for:", self.ip)

        # Copy and paste JSON strings from Sony website:
        # https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/getPowerStatus/index.html
        JSON_str = \
            '{"method": "getPowerStatus", "id": 50, "params": [], "version": "1.0"}'
        reply_dict = ni.curl(JSON_str, "system", self.ip, forgive=forgive)

        #echo "ReturnState: $ReturnState reply_dict: $reply_dict"    # Remove # for debugging
        # reply_dict: {"result":[{"status":"active"}],"id":50}
        #    or: {"result":[{"status":"standby"}],"id":50}

        # Does 'active' substring exist in TV's reply?
        v2_print(_who, "curl reply_dict:", reply_dict)
        try:
            reply = reply_dict['result'][0]['status']
        except (KeyError, IndexError):
            reply = reply_dict  # Probably "7" for not a Sony TV

        #print("reply:", reply, " | type(reply):", type(reply))
        if isinstance(reply, int):
            v3_print(_who, "Integer reply:", reply)  # 7
            return "?"
        elif u"active" == reply:
            self.power_status = "ON"  # Can be "ON", "OFF" or "?"
        elif u"standby" == reply:
            self.power_status = "OFF"  # Can be "ON", "OFF" or "?"
        else:
            v3_print(_who, "Something weird: ?")  # Router
            self.power_status = "?"  # Can be "ON", "OFF" or "?"

        # 2024-12-04 - Some tests
        #self.getSoundSettings()
        #self.getSpeakerSettings()
        #self.getVolume()

        return self.power_status

    def TurnOn(self, forgive=False):
        """ Turn On Sony Bravia KDL TV using os_curl """

        _who = self.who + "TurnOn():"
        v2_print(_who, 'Send: "id": 55, "params": [{"status": true}], to:', self.ip)

        # Copy and paste JSON strings from Sony website:
        # https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/getPowerStatus/index.html
        JSON_str = \
            '{"method": "setPowerStatus", "id": 55, ' +\
            '"params": [{"status": true}], "version": "1.0"}'

        reply_dict = ni.os_curl(JSON_str, "system", self.ip, forgive=forgive)
        v2_print(_who, "curl reply_dict:", reply_dict)  # {'result': [], 'id': 55}
        ret = "ON"
        try:
            result = reply_dict['result']  # can be KeyError
            if result:  # result should be empty (tests False)
                v0_print(_who, "reply_dict['result']' should be empty:", result)
                ret = "Error"
        except KeyError:
            v0_print(_who, "Invalid reply_dict['result']':", reply_dict)
            ret = "Error"

        self.power_status = ret  # Can be "ON", "OFF" or "?"
        return ret

    def TurnOff(self, forgive=False):
        """ Turn Off Sony Bravia KDL TV using os_curl """

        _who = self.who + "TurnOff():"
        v2_print(_who, 'Send: "id": 55, "params": [{"status": false}], to:', self.ip)

        # Copy and paste JSON strings from Sony website:
        # https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/getPowerStatus/index.html
        JSON_str = \
            '{"method": "setPowerStatus", "id": 55, ' +\
            '"params": [{"status": false}], "version": "1.0"}'

        reply_dict = ni.os_curl(JSON_str, "system", self.ip, forgive=forgive)
        v2_print(_who, "curl reply_dict:", reply_dict)  # {'result': [], 'id': 55}
        ret = "OFF"
        try:
            result = reply_dict['result']  # can be KeyError
            if result:  # result should be empty (tests False)
                v0_print(_who, "reply_dict['result']' should be empty:", result)
                ret = "Error"
        except KeyError:
            v0_print(_who, "Invalid reply_dict['result']':", reply_dict)
            ret = "Error"

        self.power_status = ret  # Can be "ON", "OFF" or "?"
        return self.power_status

    def PowerSavingMode(self, forgive=False):
        """ Get Sony Bravia KDL TV power savings mode """

        # "off" - Power saving mode is disabled.  The panel is turned on.
        # "low" - Power saving mode is enabled at a low level.
        # "high" - Power saving mode is enabled at a high level.
        # "pictureOff" - Power saving mode is enabled with the panel output off.

        _who = self.who + "PowerSavingMode():"
        v2_print(_who, 'Send: "id": 51, "params": [], to:', self.ip)

        # Copy and paste JSON strings from Sony website:
        # https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/getPowerStatus/index.html
        JSON_str = \
            '{"method": "getPowerSavingMode", "id": 51, "params": [], "version": "1.0"}'

        reply_dict = ni.curl(JSON_str, "system", self.ip, forgive=forgive)
        try:
            reply = reply_dict['result'][0]['mode']
        except (KeyError, IndexError):
            reply = reply_dict  # Probably "7" for not a Sony TV
        v2_print(_who, "curl reply_dict:", reply_dict)

        # {'result': [{'mode': 'off'}], 'id': 51}
        if isinstance(reply, int):
            v3_print(_who, "Integer found:", reply)  # 7
            self.power_saving_mode = "?"
        elif u"pictureOff" == reply:
            self.power_saving_mode = "ON"  # Reduce states from Off / Low / High / Picture Off
        elif u"off" == reply:
            self.power_saving_mode = "OFF"
        else:
            v3_print(_who, "Something weird in reply:", reply)
            self.power_saving_mode = "?"

        return self.power_saving_mode

    def PictureOn(self, forgive=False):
        """ Turn On Sony Bravia KDL TV Picture using os_curl """

        # https://pro-bravia.sony.net/develop/integrate/rest-api
        # /spec/service/system/v1_0/setPowerSavingMode/index.html

        _who = self.who + "PictureOn():"
        v2_print(_who, 'Send: "id": 52, "params": [{"mode": "off"}], to:', self.ip)

        # Copy and paste JSON strings from Sony website:
        # https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/getPowerStatus/index.html
        JSON_str = \
            '{"method": "setPowerSavingMode", "id": 52, "params": [{"mode": "off"}], "version": "1.0"}'

        reply_dict = ni.os_curl(JSON_str, "system", self.ip, forgive=forgive)

        v2_print(_who, "curl reply_dict:", reply_dict)

        try:
            err = reply_dict['error']
            return "Err: " + str(err[0])  # 403, Forbidden
        except KeyError:
            pass  # No error

        return "ON"

    def PictureOff(self, forgive=False):
        """ Turn Off Sony Bravia KDL TV Picture using os_curl """

        # https://pro-bravia.sony.net/develop/integrate/rest-api
        # /spec/service/system/v1_0/setPowerSavingMode/index.html

        _who = self.who + "PictureOff():"
        v2_print(_who, 'Send: "id": 52, "params": [{"mode": "pictureOff"}], to:', self.ip)

        # Copy and paste JSON strings from Sony website:
        # https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/getPowerStatus/index.html
        JSON_str = \
            '{"method": "setPowerSavingMode", "id": 52, "params": [{"mode": "pictureOff"}], "version": "1.0"}'
        reply_dict = ni.os_curl(JSON_str, "system", self.ip, forgive=forgive)

        v2_print(_who, "curl reply_dict:", reply_dict)

        try:
            err = reply_dict['error']
            return "Err: " + str(err[0])  # 403, Forbidden
        except KeyError:
            pass  # No error

        return "Pic. OFF"

    def getSoundSettings(self, forgive=False):
        """ Get Sony Bravia KDL TV Sound Settings (Version 1.1)
https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/audio/v1_1/getSoundSettings/index.html
        """

        _who = self.who + "getSoundSettings():"
        v2_print(_who, 'Send: "id": 73, "params": [], to:', self.ip)

        # Copy and paste JSON strings from Sony website:
        # https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/getPowerStatus/index.html
        JSON_str = \
            '{"method": "getSoundSettings", "id": 73, ' \
            '"params": [{"target": "outputTerminal"}], "version": "1.1"}'

        reply_dict = ni.curl(JSON_str, "audio", self.ip, forgive=forgive)
        v2_print(_who, "curl reply_dict:", reply_dict)
        # SonyBraviaKdlTV().getSoundSettings(): curl reply_dict: {'result': [[
        # {'currentValue': 'speaker', 'target': 'outputTerminal'}]], 'id': 73}
        #print(_who, "curl reply_dict:", reply_dict)
        # "outputTerminal" - Selecting speakers or terminals to output sound.
        # {
        #     "result": [[{
        #         "currentValue": "audioSystem",
        #         "target": "outputTerminal"
        #     }]],
        #     "id": 73
        # }

        try:
            reply = reply_dict['result'][0][0]['currentValue']
        except (KeyError, IndexError):
            reply = reply_dict  # Probably "7" for not a Sony TV
        v2_print(_who, "curl reply:", reply)
        # SonyBraviaKdlTV().getSoundSettings(): curl reply: speaker

        if True is True:
            return

        return

    def getSpeakerSettings(self, forgive=False):
        """ Get Sony Bravia KDL TV Sound Settings (Version 1.1)
https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/audio/v1_0/getSpeakerSettings/index.html
        """

        _who = self.who + "getSpeakerSettings():"
        v2_print(_who, 'Send: "id": 73, "params": [], to:', self.ip)

        # Copy and paste JSON strings from Sony website:
        # https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/getPowerStatus/index.html
        JSON_str = \
            '{"method": "getSpeakerSettings", "id": 67, ' \
            '"params": [{"target": "tvPosition"}], "version": "1.0"}'  # tableTop
            #'"params": [{"target": "tvPosition"}], "version": "1.0"}'  # tableTop
            # Settings below ignore the fact the subwoofer is powered off
            #'"params": [{"target": "subwooferLevel"}], "version": "1.0"}'  # 17
            #'"params": [{"target": "subwooferFreq"}], "version": "1.0"}'  # 10
            #'"params": [{"target": "subwooferPhase"}], "version": "1.0"}'  # normal
            #'"params": [{"target": "subwooferPower"}], "version": "1.0"}'  # on

        reply_dict = ni.curl(JSON_str, "audio", self.ip, forgive=forgive)
        v2_print(_who, "curl reply_dict:", reply_dict)
        # SonyBraviaKdlTV().getSoundSettings(): curl reply_dict: {'result': [[
        # {'currentValue': 'speaker', 'target': 'outputTerminal'}]], 'id': 73}
        #print(_who, "curl reply_dict:", reply_dict)
        # "outputTerminal" - Selecting speakers or terminals to output sound.
        # {
        #     "result": [[{
        #         "currentValue": "audioSystem",
        #         "target": "outputTerminal"
        #     }]],
        #     "id": 73
        # }

        try:
            reply = reply_dict['result'][0][0]['currentValue']
        except (KeyError, IndexError):
            reply = reply_dict  # Probably "7" for not a Sony TV
        v2_print(_who, "curl reply:", reply)
        # SonyBraviaKdlTV().getSoundSettings(): curl reply: speaker

        if True is True:
            return

        return

    def getVolume(self, forgive=False):
        """ Get Sony Bravia KDL TV volume """

        _who = self.who + "getVolume():"
        v2_print(_who, 'Send: "id": 33, "params": [], to:', self.ip)

        # Copy and paste JSON strings from Sony website:
        # https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/getPowerStatus/index.html
        JSON_str = \
            '{"method": "getVolumeInformation", "id": 33, "params": [], "version": "1.0"}'

        reply_dict = ni.curl(JSON_str, "audio", self.ip, forgive=forgive)
        v2_print(_who, "curl reply_dict:", reply_dict)
        # SonyBraviaKdlTV().getVolume(): curl reply_dict: {'result': [[
        # {'volume': 28, 'maxVolume': 100, 'minVolume': 0, 'target': 'speaker', 'mute': False},
        # {'volume': 15, 'maxVolume': 100, 'minVolume': 0, 'target': 'headphone', 'mute': False}
        # ]], 'id': 33}
        #print(_who, "curl reply_dict:", reply_dict)
        # SonyBraviaKdlTV().getVolume(): curl reply_dict:
        # {'result': [
        # [{'volume': 23, 'maxVolume': 100, 'minVolume': 0, 'target': 'speaker',
        # 'mute': False},
        # {'volume': 15, 'maxVolume': 100, 'minVolume': 0, 'target': 'headphone',
        # 'mute': False}]], 'id': 33}

        try:
            reply = reply_dict['result'][0][0]['volume']
        except (KeyError, IndexError):
            reply = reply_dict  # Probably "7" for not a Sony TV
        v2_print(_who, "curl reply:", reply)
        # SonyBraviaKdlTV().getVolume(): curl reply: 28

        if True is True:
            return

        return

    def isDevice(self, forgive=False):
        """ Return True if active or standby, False if power off or no communication
            If forgive=True then don't report pipe.returncode != 0

            Consider generic call to PowerStatus using isDevice, TestSonyOn and TestSonyOff
        """

        _who = self.who + "isDevice():"
        v3_print(_who, "Test if device is Sony Bravia KDL TV:", self.ip)

        Reply = self.PowerStatus(forgive=forgive)
        # Copy and paste JSON strings from Sony website:
        # https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/getPowerStatus/index.html

        v3_print(_who, "Reply:", Reply)
        # Reply: {u 'result': [{u 'status': u 'active'}], u 'id': 50}
        #try:
        #    reply = Reply['result'][0]['status']
        #except (KeyError, IndexError):
        #    reply = Reply  # Probably "7" for not a Sony TV
        #if reply == "active" or reply == "standby":
        #    return True
        if Reply == "ON" or Reply == "OFF":
            return True

        # TV is turned off (standby) or no network (blank)
        return False


class TclGoogleAndroidTV(DeviceCommonSelf):
    """ TCL Google Android TV

        Reference:
            https://developer.android.com/reference/android/view/KeyEvent

        Methods:

            AdbReset() - adb kill-server && adb start-server
            PowerStatus() - timeout 2.0 adb shell dumpsys input_method | grep -i screen on
            isDevice() - timeout 0.1 adb connect <ip>
            Connect() - Call isDevice followed by wakeonlan up to 60 times
            TurnOn() - timeout 0.5 adb shell input key event KEYCODE_WAKEUP
            TurnOff() - timeout 0.5 adb shell input key event KEYCODE_SLEEP

    """

    def __init__(self, mac, ip, name, alias):
        """ DeviceCommonSelf(): Variables used by all classes

        """

        DeviceCommonSelf.__init__(self, "TclGoogleAndroidTV().")  # Define self.who

        # 192.168.0.17    TCL.LAN TCL / Google TV Ethernet c0:79:82:41:2f:1f
        # 192.168.0.18    TCL.WiFi TCL / Google TV WiFi fc:d4:36:ea:82:36
        self.mac = mac      # c0:79:82:41:2f:1f
        self.ip = ip        # 192.168.0.17
        self.name = name    # TCL.LAN
        self.alias = alias  # TCL / Google TV Ethernet

        self.type = "TclGoogleAndroidTV"
        self.type_code = GLO['TCL_TV']
        self.power_status = "?"  # Can be "ON", "OFF" or "?"
        self.requires = ['wakeonlan', 'adb']
        self.installed = []
        self.CheckDependencies(self.requires, self.installed)
        _who = self.who + "__init__():"
        v3_print(_who, "Dependencies:", self.requires)
        v3_print(_who, "Installed?  :", self.installed)

        if not self.dependencies_installed:
            v1_print(_who, "TCL Google Android TV dependencies are not installed.")

    def Connect(self, forgive=False):
        """ Wakeonlan and Connect to TCL / Google Android TV
            Called on startup. Also called from TurnOff() and TurnOn().
        """

        _who = self.who + "Connect():"
        v1_print(_who, "Connect to:", self.ip)

        # MAGIC_TIME needs 5 seconds for timeout
        # $ time adb connect 192.168.0.17
        # * daemon not running. starting it now on port 5037 *
        # * daemon started successfully *
        # connected to 192.168.0.17:5555
        #
        # real	0m3.010s
        # user	0m0.001s
        # sys	0m0.005s
        command_line_list = ["adb", "devices", "-l"]
        self.runCommand(command_line_list, _who)  # Will force 'adb' daemon to run

        cnt = 1
        while not self.isDevice(forgive=True, timeout=GLO['ADB_MAGIC_TIME']):

            v2_print(_who, "Attempt #:", cnt, "Call 'wakeonlan' for MAC:", self.mac)
            command_line_list = ["wakeonlan", self.mac]

            event = self.runCommand(command_line_list, _who, forgive=forgive)
            if event['returncode'] != 0:
                return False

            cnt += 1
            if cnt > 60:
                v0_print(_who, "Timeout after", cnt, "attempts")
                return False

        return True

    def PowerStatus(self, forgive=False):
        """ Return "ON", "OFF" or "?".
            Calls 'timeout 2.0 adb shell dumpsys input_method | grep -i screenon'
                which replies with 'true' or 'false'.

        """

        _who = self.who + "PowerStatus():"
        v2_print("\n" + _who, "Get Power Status for:", self.ip)
        self.Connect()  # 2024-12-02 - constant connection seems to be required

        command_line_list = ["timeout", GLO['ADB_PWR_TIME'], "adb",
                             "shell", "dumpsys", "input_method",
                             "|", "grep", "-i", "screenOn"]
        event = self.runCommand(command_line_list, _who, forgive=forgive)
        v2_print(_who, "reply from grep 'screenOn':", event['output'], event['error'])

        if event['returncode'] != 0:
            if forgive is False:
                #v1_print(_who, "pipe.returncode:", pipe.returncode)
                #if pipe.returncode == 124:
                if event['returncode'] == 124:
                    v1_print(_who, self.ip, "timeout after:", GLO['ADB_PWR_TIME'])
                    self.power_status = "?"  # Can be "ON", "OFF" or "?"
                    return self.power_status
            self.power_status = "? " + str(event['returncode'])
            return self.power_status

        Reply = event['output']
        # Reply = "connected to 192.168.0.17:5555"
        # Reply = "already connected to 192.168.0.17:5555"
        # Reply = "unable to connect to 192.168.0.17:5555"
        # Reply = "error: device offline"

        if "true" in Reply:
            self.power_status = "ON"  # Can be "ON", "OFF" or "?"
        elif "false" in Reply:
            self.power_status = "OFF"  # Can be "ON", "OFF" or "?"
        else:
            self.power_status = "?"  # Can be "ON", "OFF" or "?"

        return self.power_status

    def TurnOn(self, forgive=False):
        """ Turn On TCL / Google Android TV.
            Send KEYCODE_WAKEUP 5 times until screenOn = true
        """

        _who = self.who + "TurnOn():"
        v2_print("\n" + _who, "Send KEYCODE_WAKEUP to:", self.ip)

        # Connect() will try 60 times with wakeonlan and isDevice check.
        if not self.Connect(forgive=forgive):  # TODO else: error message
            return self.PowerStatus()

        cnt = 1
        self.power_status = "?"
        while not self.power_status == "ON":

            v1_print(_who, "Attempt #:", cnt, "Send 'KEYCODE_WAKEUP' to IP:", self.ip)

            # timeout 1 adb shell input keyevent KEYCODE_WAKEUP  # Turn Google TV off
            command_line_list = ["timeout", GLO['ADB_KEY_TIME'], "adb",
                                 "shell", "input", "keyevent", "KEYCODE_WAKEUP"]
            event = self.runCommand(command_line_list, _who, forgive=forgive)
            if event['returncode'] != 0:
                # 2024-10-19 - Always returns '124' which is timeout exit code
                #   https://stackoverflow.com/a/42615416/6929343
                if forgive is False:
                    # v0_print(_who, "pipe.returncode:", pipe.returncode)
                    if event['returncode'] == 124:
                        v0_print(_who, self.ip, "timeout after:", GLO['ADB_KEY_TIME'])
                return "?"

            self.PowerStatus()
            if self.power_status == "ON" or cnt >= 5:
                return self.power_status
            cnt += 1

    def TurnOff(self, forgive=False):
        """ Send 'adb shell input keyevent KEYCODE_SLEEP' """

        _who = self.who + "TurnOff():"
        v2_print(_who, "Send KEYCODE_SLEEP to:", self.ip)

        command_line_list = ["timeout", GLO['ADB_KEY_TIME'], "adb",
                             "shell", "input", "keyevent", "KEYCODE_SLEEP"]
        event = self.runCommand(command_line_list, _who, forgive=forgive)

        if event['returncode'] != 0:
            # 2024-10-19 - When hitting timeout limit, returns '124'
            #   https://stackoverflow.com/a/42615416/6929343
            if forgive is False:
                if event['returncode'] == 124:
                    v0_print(_who, self.ip, "timeout after:", GLO['ADB_KEY_TIME'])
            return "?"

        self.power_status = "OFF"  # Can be "ON", "OFF" or "?"
        return self.power_status

    def isDevice(self, forgive=False, timeout=None):
        """ Return True if adb connection for Android device (using IP address).
            If forgive=True then don't report pipe.returncode != 0
        """

        _who = self.who + "isDevice():"
        v2_print(_who, "Test if device is TCL Google Android TV:", self.ip)

        if timeout is None:
            timeout = GLO['ADB_CON_TIME']
        command_line_list = ["timeout", timeout, "adb", "connect", self.ip]
        command_line_str = ' '.join(command_line_list)
        pipe = sp.Popen(command_line_list, stdout=sp.PIPE, stderr=sp.PIPE)
        text, err = pipe.communicate()  # This performs .wait() too

        v3_print(_who, "Results from '" + command_line_str + "':")
        Reply = text.strip()
        v3_print(_who, "Reply: '" + Reply + "' | type:", type(Reply), len(Reply))
        v3_print(_who, "err: '" + err.strip() + "'  | pipe.returncode:",
                 pipe.returncode)

        if not pipe.returncode == 0:
            if forgive is False:
                v0_print(_who, "pipe.returncode:", pipe.returncode)
            return False

        # Reply = "connected to 192.168.0.17:5555"
        # Reply = "already connected to 192.168.0.17:5555"
        # Reply = "unable to connect to 192.168.0.17:5555"
        # Reply = "error: device offline"
        return "connected" in Reply


class Application(DeviceCommonSelf, tk.Toplevel):
    """ tkinter main application window
        Dropdown menus File/Edit/View/Tools
        Treeview with columns image, name/alias/IP,
    """

    def __init__(self, master=None):
        """ DeviceCommonSelf(): Variables used by all classes
        :param toplevel: Usually <None> except when called by another program.
        """
        DeviceCommonSelf.__init__(self, "Application().")  # Define self.who

        global sm  # This machines fan speed and CPU temperatures

        ''' Future read-only display fields for .Config() screen 
        v0_print("\n")
        v0_print("g.USER:", g.USER)  # User ID, Name, GUID varies by platform
        v0_print("g.USER_ID:", g.USER_ID)  # Numeric User ID in Linux
        v0_print("g.HOME:", g.HOME)  # In Linux = /home/USER
        v0_print("g.APPNAME:", g.APPNAME)  # Originally "mserve" Different for homa.py
        v0_print("g.USER_CONFIG_DIR:", g.USER_CONFIG_DIR)  # /home/user/.config/mserve
        v0_print("g.USER_DATA_DIR:", g.USER_DATA_DIR)  # /home/user/.local/share/mserve
        v0_print("g.MSERVE_DIR:", g.MSERVE_DIR)   # /home/user/.config/mserve/ <- historically wrong suffix /
        #                         # Bad name. It implies where mserve programs are
        v0_print("g.PROGRAM_DIR:", g.PROGRAM_DIR)  # Directory where mserve.py is stored.
        v0_print("g.TEMP_DIR:", g.TEMP_DIR)  # /tmp/ temporary files OR: /run/user/1000/ preferred
        #                         # also with trailing '/' to make concatenating simpler
        v0_print()
        '''

        self.requires = ['arp', 'getent', 'timeout', 'curl', 'adb', 'hs100.sh', 'aplay']
        self.installed = []
        self.CheckDependencies(self.requires, self.installed)

        if not self.dependencies_installed:
            v1_print(_who, "Some Application() dependencies are not installed.")
            v1_print(self.requires)
            v1_print(self.installed)

        self.last_refresh_time = time.time()  # Refresh idle loop last entered time
        # Normal 1 minute delay to rediscover is shortened at boot time if fast start
        self.last_rediscover_time = time.time()  # Last analysis of `arp -a`
        if p_args.fast:
            # Allow 3 seconds to move mouse else start rediscover
            self.last_rediscover_time = time.time() - GLO['REDISCOVER_SECONDS'] + 3
        self.rediscover_done = True  # 16ms time slices until done.
        self.rediscover_row = 0  # Current row processed in Treeview
        self.tree = None  # Painted in PopulateTree()
        self.photos = None  # Used in PopulateTree() and many other methods

        ''' Toplevel window (self) '''
        tk.Toplevel.__init__(self, master)  # https://stackoverflow.com/a/24743235/6929343
        self.minsize(width=120, height=63)
        self.geometry('1200x700')
        self.configure(background="WhiteSmoke")
        self.rowconfigure(0, weight=1)  # Weight 1 = stretchable row
        self.columnconfigure(0, weight=1)  # Weight 1 = stretchable column
        # self.xdo_os_window_id = os.popen("xdotool getactivewindow").read().strip()
        # self.xdo_os_window_id: 92274698  # THIS CHANGES BELOW TO 102760472
        self.title("HomA - Home Automation")
        self.btn_frm = None  # Used by BuildButtonBar(), can be hidden by edit_pref

        ''' ChildWindows() moves children with toplevel and keeps children on top '''
        self.win_grp = toolkit.ChildWindows(self, auto_raise=False)

        ''' Tooltips() - if --silent argument, then suppress error printing '''
        print_error = False if p_args.silent else True
        self.tt = toolkit.ToolTips(print_error=print_error)

        ''' Set program icon in taskbar. '''
        img.taskbar_icon(self, 64, 'white', 'green', 'yellow', char='HA')

        ''' System Monitor '''
        sm = SystemMonitor(self)  # sm = This machines fan speed and CPU temperatures

        ''' Preferences Notebook '''
        self.pref_nb = self.edit_pref_active = None

        ''' Big Number Calculator and Delayed Textbox (dtb) are child windows '''
        self.calculator = self.calc_top = self.dtb = None

        ''' Display cmdEvents (toolkit.CustomScrolledText) as child window '''
        self.event_top = self.event_scroll_active = None

        ''' File/Edit/View/Tools dropdown menu bars '''
        self.file_menu = self.edit_menu = self.view_menu = self.tools_menu = None
        self.BuildMenu()  # Dropdown Menu Bars after 'sm ='

        ''' Create treeview with internet devices. '''
        self.PopulateTree()

        ''' When devices displayed show sensors button and vice versa. '''
        self.sensors_devices_btn = None
        self.sensors_btn_text = "🌡  Sensors"  # (U+1F321) when Devices active
        self.devices_btn_text = "🗲  Devices"  # (U+1F5F2) when Sensors active
        self.BuildButtonBar(self.sensors_btn_text)

        # Dropdown Menu Bars after 'sm =' and BuildButtonBar() sets button text
        self.EnableMenu()

        # Experiments to delay rediscover when there is GUI activity
        self.minimizing = False  # When minimizing, override FocusIn()
        self.bind("<FocusIn>", self.FocusIn)  # Raise windows up
        self.bind("<Motion>", self.Motion)  # On motion reset rediscovery timer

        self.last_motion_time = GLO['APP_RESTART_TIME']

        # Monitors and window positions when un-minimizing
        self.monitors = self.windows = []  # List of dictionaries

        # Laptop Display needs to call .GetPassword() method in this Application()
        # Assign this Application() instance to the LaptopDisplay() instance self.app
        for instance in ni.instances:
            inst = instance['instance']
            if inst.type_code == GLO['LAPTOP_D']:
                inst.app = self

        ''' Save Toplevel OS window ID for minimizing window '''
        command_line_list = ["xdotool", "getactivewindow"]
        event = self.runCommand(command_line_list, forgive=False)
        self.xdo_os_window_id = event['output']
        # self.xdo_os_window_id: 102760472  THIS CHANGED FROM ABOVE 92274698

        while self.Refresh():  # Run forever until quit
            self.update_idletasks()  # Get queued tasks

    def BuildMenu(self):
        """ Build dropdown Menu bars: File, Edit, View & Tools """

        def ForgetPassword():
            """ Clear sudo password for extreme caution """
            GLO['SUDO_PASSWORD'] = None  # clear global password in homa
            command_line_list = ["sudo", "-K"]
            self.runCommand(command_line_list)

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
        self.file_menu.add_command(label="Minimize", font=g.FONT, underline=0,
                                   command=self.MinimizeApp, state=tk.NORMAL)
        self.file_menu.add_command(label="Suspend", font=g.FONT, underline=0,
                                   command=self.Suspend, state=tk.NORMAL)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", font=g.FONT, underline=1,
                                   command=self.CloseApp, state=tk.DISABLED)

        mb.add_cascade(label="File", font=g.FONT, underline=0, menu=self.file_menu)

        # Edit Dropdown Menu
        self.edit_menu = tk.Menu(mb, tearoff=0)
        self.edit_menu.add_command(label="Preferences", font=g.FONT, underline=0,
                                   command=self.Preferences, state=tk.NORMAL)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Monitor volume", underline=0,
                                   font=g.FONT, state=tk.DISABLED,
                                   command=self.CloseApp)

        mb.add_cascade(label="Edit", font=g.FONT, underline=0, menu=self.edit_menu)

        # View Dropdown Menu
        self.view_menu = tk.Menu(mb, tearoff=0)
        self.view_menu.add_command(label="Sensors", font=g.FONT, underline=0,
                                   command=self.SensorsDevicesToggle, state=tk.DISABLED)
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Network devices", font=g.FONT, underline=0,
                                   command=self.SensorsDevicesToggle, state=tk.DISABLED)
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Discovery timings", font=g.FONT, underline=10,
                                   command=self.DisplayTimings)
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
                                    command=lambda: self.ResumeWait(timer=GLO['TIMER_SEC']))
        # 2024-12-04 TODO: After timer ends, Resume from Suspend countdown starts with
        #   3 seconds to go.
        self.tools_menu.add_separator()

        self.tools_menu.add_command(label="Forget sudo password", underline=0,
                                    font=g.FONT, command=ForgetPassword, state=tk.DISABLED)
        self.tools_menu.add_command(label="Debug information", font=g.FONT,
                                    underline=0, command=self.CloseApp,
                                    state=tk.DISABLED)
        mb.add_cascade(label="Tools", font=g.FONT, underline=0,
                       menu=self.tools_menu)

    def EnableMenu(self):
        """ Called from build_lib_menu() and passed to self.playlists to call.
            Also passed with lcs.register_menu(self.EnableMenu)
        :return: None """

        ''' File Menu '''
        # During rediscovery, the "Rediscover now" dropdown menubar option disabled
        self.file_menu.entryconfig("Rediscover now", state=tk.NORMAL)
        self.file_menu.entryconfig("Exit", state=tk.NORMAL)

        ''' Edit Menu '''
        # 2024-12-01 - Edit menu options not written yet
        self.edit_menu.entryconfig("Preferences", state=tk.NORMAL)
        self.edit_menu.entryconfig("Monitor volume", state=tk.DISABLED)

        ''' View Menu '''
        # Enable options depending on Sensors Treeview or Devices Treeview mounted
        if self.sensors_devices_btn['text'] == self.devices_btn_text:
            # Sensors Treeview is displayed
            self.view_menu.entryconfig("Sensors", state=tk.DISABLED)
            self.view_menu.entryconfig("Network devices", state=tk.NORMAL)
        else:
            # Devices Treeview is displayed
            self.view_menu.entryconfig("Sensors", state=tk.NORMAL)
            self.view_menu.entryconfig("Network devices", state=tk.DISABLED)

        if GLO['EVENT_ERROR_COUNT'] != 0:
            # 2024-12-17 - Working when called from command line, not from indicator
            self.view_menu.entryconfig("Discovery errors", state=tk.NORMAL)
        else:
            self.view_menu.entryconfig("Discovery errors", state=tk.DISABLED)

        ''' Tools Menu '''
        self.tools_menu.entryconfig("Big number calculator", state=tk.NORMAL)
        if GLO['SUDO_PASSWORD'] is None:
            self.tools_menu.entryconfig("Forget sudo password", state=tk.DISABLED)
        else:
            self.tools_menu.entryconfig("Forget sudo password", state=tk.NORMAL)
        self.tools_menu.entryconfig("Debug information", state=tk.DISABLED)

    def CloseApp(self, *_args):
        """ <Escape>, X on window, 'Exit from dropdown menu or Close Button"""

        # Need Devices treeview displayed to save ni.view_order
        if self.sensors_devices_btn['text'] == self.devices_btn_text:
            self.SensorsDevicesToggle()  # Toggle off Sensors Treeview

        # Generate new ni.view_order list of MAC addresses
        order = []
        for item in self.tree.get_children():
            cr = TreeviewRow(self)
            cr.Get(item)
            order.append(cr.mac)

        self.win_grp.destroy_all(tt=self.tt)  # Destroy Calculator and Countdown
        self.destroy()  # Destroy Toplevel window

        ''' Save files '''
        ni.view_order = order
        save_files()

        ''' reset to original SAVE_CWD (saved current working directory) '''
        if SAVE_CWD != g.PROGRAM_DIR:
            v1_print("Changing from g.PROGRAM_DIR:", g.PROGRAM_DIR,
                     "to SAVE_CWD:", SAVE_CWD)
            os.chdir(SAVE_CWD)

        ''' Print statistics - 9,999,999 right aligned. '''
        if sm.number_logs:
            v0_print()
            v0_print("sm.skipped_checks  :", "{:,d}".format(sm.skipped_checks).rjust(9))
            v0_print("sm.number_checks   :", "{:,d}".format(sm.number_checks).rjust(9))
            v0_print("sm.skipped_fan_same:", "{:,d}".format(sm.skipped_fan_same).rjust(9))
            v0_print("sm.skipped_fan_200d:", "{:,d}".format(sm.skipped_fan_200d).rjust(9))
            v0_print("sm.skipped_logs    :", "{:,d}".format(sm.skipped_logs).rjust(9))
            v0_print("sm.number_logs     :", "{:,d}".format(sm.number_logs).rjust(9))

        self.destroy()  # Destroy toplevel
        exit()

    def MinimizeApp(self, *_args):
        """ Minimize GUI Application() window using xdotool.
            2024-12-08 TODO: Minimize child windows (Countdown and Big Number Calc.)
                However, when restoring windows it can be on another monitor.
        """
        _who = self.who + "MinimizeApp():"
        # noinspection SpellCheckingInspection
        command_line_list = ["xdotool", "windowminimize", self.xdo_os_window_id]
        self.runCommand(command_line_list, _who)

    def Suspend(self, *_args):
        """ Suspend system. """

        _who = self.who + "Suspend():"
        v0_print(_who, "Suspending system...")

        ''' Is countdown already running? '''
        # Cannot suspend when countdown timer is running. It resets last refresh
        # time which tricks refresh into thinking it's not a resume from suspend
        # when system comes back up.
        if self.dtb:
            if True is True:
                # 2024-12-13: Safe method of suspending. However countdown timer
                #   disappears until message acknowledged
                message.ShowInfo(self, thread=self.Refresh,
                                 icon='warning', title="Cannot Suspend now.",
                                 text="Countdown timer must be closed.")
                v0_print(_who, "Aborting suspend. Countdown timer active.")
                return
            v0_print(_who, "Aborting countdown timer.")
            self.dtb.close()
            self.after(300)  # Give time for countdown window to close
            # Countdown timer (ResumeWait) uses: 'self.after(100)'
            # 2024-12-13 - self.after(150ms not enough time.

        ''' Is rediscovery in progress? '''
        if not self.rediscover_done:
            # 2024-12-14: Safe method of suspending. Last night during suspend the
            #   system rebooted. TODO: Disable suspend button during rediscovery.
            message.ShowInfo(self, thread=self.Refresh,
                             icon='warning', title="Cannot Suspend now.",
                             text="Device rediscovery is in progress for a few seconds.")
            v0_print(_who, "Aborting suspend. Device rediscovery in progress.")
            return

        self.SetAllPower("OFF")  # Turn off all devices except computer
        cp.TurnOff()  # suspend the computer

    def FocusIn(self, *_args):
        """ Window or menu in focus, disable rediscovery. Raise child windows above.
            NOTE: triggered two times so test current state for first time status.
            NOTE: When the right-click menu is closed it registers FocusOut and
                  toplevel registers FocusIn again.
            NOTE: If preferences Notebook is active and countdown timer is started
                  the digits never appear and linux locks up totally. Mouse movement
                  can still occur but that is all. As of 2024-12-27.
        """

        if self.event_scroll_active and self.event_top:
            self.event_top.focus_force()
            self.event_top.lift()

        # 2024-12-28 Causes Xorg to freeze. Only mouse can move.
        #if self.edit_pref_active and self.pref_nb:
        #    self.pref_nb.focus_force()
        #    self.pref_nb.lift()

        if self.calculator and self.calc_top:
            self.calc_top.focus_force()
            self.calc_top.lift()

        if self.dtb and self.dtb.mounted is True:
            self.dtb.msg_top.focus_force()
            self.dtb.msg_top.lift()

    def Motion(self, *_args):
        """ Window or menu had motion, reset last rediscovery time.
            This will break ResumeFromSuspend() action to force rediscovery

            See: https://www.tcl.tk/man/tcl8.4/TkCmd/bind.htm#M15
        """
        self.last_motion_time = time.time()
        self.last_rediscover_time = self.last_motion_time

    def PopulateTree(self):
        """ Populate treeview using ni.Discovered[{}, {}...{}]
            Treeview IID is string: "0", "1", "2" ... "99"
        """
        _who = self.who + "PopulateTree():"

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
        self.tree.heading('#0', text='Device Image & Status')
        self.tree.heading('#1', text='Device Name & IP', anchor='center')
        self.tree.heading('#2', text='Device Attributes', anchor='center')
        self.tree.column('#0', width=450, stretch=False)
        self.tree.column('name', anchor='center', width=220, stretch=True)
        self.tree.column('attributes', anchor='center', width=300, stretch=True)

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

        # Build treeview in last used MAC Address Order
        for i, mac in enumerate(ni.view_order):
            arp_dict = ni.arp_for_mac(mac)
            if len(arp_dict) < 2:
                v1_print(_who, "len(arp_dict) < 2")
                continue  # TODO: Error message on screen

            nr = TreeviewRow(self)  # Setup treeview row processing instance
            nr.New(mac)  # Setup new row
            nr.Add(i)  # Add new row

            # Refresh tree display row by row for processing lag
            if not p_args.fast:
                self.tree.update_idletasks()  # Slow mode display each row.

    def BuildButtonBar(self, toggle_text):
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
        self.btn_frm.grid(row=99, column=0, columnspan=2, sticky=tk.E)
        '''
        2024-09-07 - Xorg or Tkinter glitch only fixed by reboot makes tk.Button
          3x wider and taller. Use ttk.Button which defaults to regular size.
          The 'font=' keyword is NOT supported in ttk.Button which uses -style.
        '''
        style = ttk.Style()
        # Credit: https://stackoverflow.com/a/62506279
        #style.theme_use("classic")

        style.map("C.TButton",  # mserve play_button() in build_play_btn_frm()
                  foreground=[('!active', 'Black'), ('pressed', 'White'),
                              ('active', 'Black')],
                  background=[('!active', 'Grey75'), ('pressed', 'ForestGreen'),
                              ('active', 'SkyBlue3')]  # lighter than DodgerBlue
                  )

        style.configure("C.TButton", font=g.MED_FONT)

        def device_button(row, column, txt, command, tt_text, tt_anchor):
            """ Function to combine ttk.Button, .grid() and tt.add_tip() """
            # font=
            widget = ttk.Button(self.btn_frm, text=txt, width=len(txt),
                                command=command, style="C.TButton")
            widget.grid(row=row, column=column, padx=5, pady=5, sticky=tk.E)
            if tt_text is not None and tt_anchor is not None:
                self.tt.add_tip(widget, tt_text, anchor=tt_anchor)
            return widget

        ''' Minimize Button - U+1F847 🡇  -OR-  U+25BC ▼ '''
        device_button(0, 0, "▼  Minimize", self.MinimizeApp,
                      "Quickly and easily minimize HomA.", "nw")

        # noinspection SpellCheckingInspection
        ''' 🌡 (U+1F321) Sensors Button  -OR-  🗲 (U+1F5F2) Devices Button '''
        if toggle_text == self.sensors_btn_text:
            text = "Show Temperatures and Fans."
        else:
            text = "Show Network Devices."

        self.sensors_devices_btn = device_button(
            0, 1, toggle_text, self.SensorsDevicesToggle,
            text, "nw")

        ''' Suspend Button U+1F5F2  🗲 '''
        device_button(0, 2, "🗲 Suspend", self.Suspend,
                      "Power off all devices except suspend computer.", "ne")

        ''' Help Button - ⧉ Help - Videos and explanations on pippim.com
            https://www.pippim.com/programs/HomA.html#HelpMusicLocationTree '''
        help_text = "Open new window in default web browser for\n"
        help_text += "videos and explanations on using this screen.\n"
        help_text += "https://www.pippim.com/programs/HomA.html#\n"
        device_button(0, 3, "⧉ Help", lambda: g.web_help("HelpMusicLocationTree"),
                      help_text, "ne")

        ''' ✘ Close Button '''
        self.bind("<Escape>", self.CloseApp)
        self.protocol("WM_DELETE_WINDOW", self.CloseApp)
        device_button(0, 4, "✘ Close", self.CloseApp,
                      "Close HomA and all windows HomA opened.", "ne")

    def SensorsDevicesToggle(self):
        """ Sensors / Devices toggle button clicked.
            If button text == "Sensors" then active sm.tree.
            If button text == "Devices" then active Applications.tree.

        """
        _who = self.who + "SensorsDevicesToggle()"
        show_devices = show_sensors = False

        # Get current button state and toggle it for next time.
        if self.sensors_devices_btn['text'] == self.sensors_btn_text:
            show_sensors = True
            self.sensors_devices_btn['text'] = self.devices_btn_text
            self.tt.set_text(self.sensors_devices_btn, "Show Network Devices.")
        elif self.sensors_devices_btn['text'] == self.devices_btn_text:
            show_devices = True
            self.sensors_devices_btn['text'] = self.sensors_btn_text
            self.tt.set_text(self.sensors_devices_btn, "Show Temperatures and Fans.")
        else:
            v0_print("Invalid Button self.sensors_devices_btn['text']:",
                     self.sensors_devices_btn['text'])
            exit()

        self.EnableMenu()  # NORMAL/DISABLED options for view Sensors/Devices

        if show_sensors:
            self.tree.destroy()
            sm.treeview_active = True
            sm.PopulateTree()  # Calls sm.Print(start=0, end=-1)
            self.BuildButtonBar(self.devices_btn_text)

        if show_devices:
            sm.tree.destroy()
            sm.treeview_active = False
            self.PopulateTree()
            self.BuildButtonBar(self.sensors_btn_text)

    def RightClick(self, event):
        """ Mouse right button click. Popup menu overtop of treeview. """
        item = self.tree.identify_row(event.y)

        if item is None:
            return  # Empty row, nothing to do
        try:
            _no = str(int(item) + 1)
        except ValueError:
            return  # Clicked on empty row

        def ClosePopup(*_event):
            """ Close popup menu on focus out or selection """
            cr.FadeOut(item)
            menu.unpost()

        menu = tk.Menu(self)
        menu.bind("<FocusIn>", self.FocusIn)
        menu.bind("<Motion>", self.Motion)

        menu.post(event.x_root, event.y_root)

        cr = TreeviewRow(self)  # Make current row instances
        cr.Get(item)  # Get current row
        name = cr.arp_dict['name']

        # 320 ms row highlighting fade in
        cr.FadeIn(item)

        if cr.arp_dict['type_code'] == GLO['KDL_TV']:
            # Sony TV has power save mode to turn picture off and listen to music
            menu.add_command(label="Turn " + name + " Picture On ",
                             font=g.FONT, state=tk.DISABLED,
                             command=lambda: self.PictureOn(cr))
            menu.add_command(label="Turn " + name + " Picture Off ",
                             font=g.FONT, state=tk.DISABLED,
                             command=lambda: self.PictureOff(cr))
            cr.inst.getVolume()
            menu.add_separator()

        menu.add_command(label="Turn On " + name, font=g.FONT, state=tk.DISABLED,
                         command=lambda: self.TurnOn(cr))
        menu.add_command(label="Turn Off " + name, font=g.FONT, state=tk.DISABLED,
                         command=lambda: self.TurnOff(cr))
        menu.add_separator()
        menu.add_command(label="Move " + name + " Up", font=g.FONT, state=tk.DISABLED,
                         command=lambda: self.MoveRowUp(cr))
        menu.add_command(label="Move " + name + " Down", font=g.FONT, state=tk.DISABLED,
                         command=lambda: self.MoveRowDown(cr))
        menu.add_separator()
        menu.add_command(label="Close this menu", font=g.FONT, command=ClosePopup)

        menu.tk_popup(event.x_root, event.y_root)

        menu.bind("<FocusOut>", ClosePopup)

        # Enable Turn On/Off menu options depending on current power status.
        if cr.arp_dict['type_code'] == GLO['KDL_TV']:
            cr.inst.PowerSavingMode()
            if cr.inst.power_saving_mode != "ON":
                menu.entryconfig("Turn " + name + " Picture Off ", state=tk.NORMAL)
            if cr.inst.power_saving_mode != "OFF":
                menu.entryconfig("Turn " + name + " Picture On ", state=tk.NORMAL)

        if cr.inst.power_status != "ON":
            menu.entryconfig("Turn On " + name, state=tk.NORMAL)
        if cr.inst.power_status != "OFF":
            menu.entryconfig("Turn Off " + name, state=tk.NORMAL)

        # Allow moving up unless at top, allow moving down unless at bottom
        all_iid = self.tree.get_children()
        if item != all_iid[0]:
            menu.entryconfig("Move " + name + " Up", state=tk.NORMAL)
        if item != all_iid[-1]:
            menu.entryconfig("Move " + name + " Down", state=tk.NORMAL)

    def PictureOn(self, cr):
        """ Mouse right button click selected "Turn Picture On". """
        _who = self.who + "PictureOn():"
        resp = cr.inst.PictureOn()
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()

    def PictureOff(self, cr):
        """ Mouse right button click selected "Turn Picture Off". """
        _who = self.who + "PictureOff():"
        resp = cr.inst.PictureOff()
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()

    def TurnOn(self, cr):
        """ Mouse right button click selected "Turn On".
            Also be called by SetAllPower("ON").
        """
        _who = self.who + "TurnOn():"
        resp = cr.inst.TurnOn()
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()
        self.resumePowerOn = 0  # Resume didn't power on the device
        self.manualPowerOn = 0  # Was device physically powered on?
        self.nightPowerOn = 0  # Did nighttime power on the device?
        self.menuPowerOn += 1  # User powered on the device via menu

        # Setting Power can loop for a minute in worst case scenario using adb
        self.last_refresh_time = time.time()  # Refresh idle loop last entered time

    def TurnOff(self, cr):
        """ Mouse right button click selected "Turn Off".
            Also be called by SetAllPower("OFF").
        """
        _who = self.who + "TurnOff():"
        if cr.inst.type_code == GLO['DESKTOP'] or cr.inst.type_code == GLO['LAPTOP_B']:
            self.SetAllPower("OFF")  # Turn all devices off
        resp = cr.inst.TurnOff()
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()
        self.suspendPowerOff = 0  # Suspend didn't power off the device
        self.manualPowerOff = 0  # Was device physically powered off?
        self.dayPowerOff = 0  # Did daylight power off the device?
        self.menuPowerOff += 1  # User powered off the device via menu

        # Setting Power can loop for a minute in worst case scenario using adb
        self.last_refresh_time = time.time()  # Refresh idle loop last entered time

    def MoveRowUp(self, cr):
        """ Mouse right button click selected "Move Row Up". """
        _who = self.who + "MoveRowUp():"
        if str(cr.item) == "0":
            v0_print(_who, "Already on first row. Cannot move up.")
            return

        dr = TreeviewRow(self)  # Destination treeview row instance
        dr.Get(str(int(cr.item) - 1))  # Get destination row values
        v1_print(_who, "Swapping rows:", cr.mac, dr.mac)
        dr.Update(cr.item)  # Update destination row with current row
        cr.Update(dr.item)  # Update current row with destination row

    def MoveRowDown(self, cr):
        """ Mouse right button click selected "Move Row Down". """
        _who = self.who + "MoveRowDown():"
        if int(cr.item) >= len(cr.tree.get_children())-1:
            v0_print(_who, "Already on last row. Cannot move down.")
            return

        dr = TreeviewRow(self)  # Destination treeview row instance
        dr.Get(str(int(cr.item) + 1))  # Get destination row values
        v1_print(_who, "Swapping rows:", cr.mac, dr.mac)
        dr.Update(cr.item)  # Update destination row with current row
        cr.Update(dr.item)  # Update current row with destination row

    def Refresh(self, tk_after=True):
        """ Sleeping loop until need to do something. Fade tooltips. Resume from
            suspend. Rediscover devices.

            When a message is displayed, or input is requested, lost time causes
            a fake resume from suspend condition. After dialog boxes, use command:

                self.last_refresh_time = time.time()  # Refresh idle loop

        """

        _who = self.who + "Refresh()"
        if not self.winfo_exists():
            return False  # self.close() has destroyed window

        ''' Is system shutting down? '''
        if killer.kill_now:
            v0_print('\nhoma.py refresh() closed by SIGTERM')
            self.CloseApp()
            return False  # Not required because this point never reached.

        ''' Resuming from suspend? '''
        now = time.time()
        delta = now - self.last_refresh_time
        if delta > GLO['RESUME_TEST_SECONDS']:  # Assume > is resume from suspend
            v0_print("\n" + "= "*4, _who, "Resuming from suspend after:",
                     tmf.days(delta), " ="*4 + "\n")
            self.ResumeFromSuspend()  # Power on all devices
            now = time.time()  # can be 15 seconds or more later
            GLO['APP_RESTART_TIME'] = now  # Reset app started time to resume time

        ''' Is there a TV to be monitored for power off to suspend system? '''
        # 2024-12-23 TODO: SETUP FOR SONY TV REST API

        ''' Always give time slice to tooltips - requires sql.py color config '''
        self.tt.poll_tips()  # Tooltips fade in and out. self.info piggy backing
        self.update()  # process events in queue. E.G. message.ShowInfo()

        if not self.winfo_exists():  # Second check needed June 2023
            return False  # self.close() has set to None

        ''' Speedy derivative when called by CPU intensive methods '''
        if not tk_after:
            return self.winfo_exists()

        ''' Check `sensors` (if installed) every GLO['SENSOR_CHECK'] seconds '''
        sm.Sensors()

        ''' Rediscover devices every GLO['REDISCOVER_SECONDS'] '''
        if int(now - self.last_rediscover_time) > GLO['REDISCOVER_SECONDS']:
            self.Rediscover(auto=True)  # Check for changes in IP addresses, etc
            night = cp.NightLightStatus()
            v1_print(_who, "cp.NightLightStatus():", night)

        ''' sleep remaining time until GLO['REFRESH_MS'] expires '''
        sleep = GLO['REFRESH_MS'] - int(now - self.last_refresh_time)
        sleep = sleep if sleep > 0 else 1  # Sleep minimum 1 millisecond
        if sleep == 1:
            v0_print(_who, "Only sleeping 1 millisecond")
        self.last_refresh_time = time.time()  # 2024-12-05 was 'now' too stale?
        self.after(sleep)  # Sleep until next 60 fps time

        ''' Wrapup '''
        return self.winfo_exists()  # Go back to caller as success or failure

    def ResumeFromSuspend(self):
        """ Resume from suspend. Display status of devices that were
            known at time of suspend. Then set variables to trigger
            rediscovery for any new devices added.

            Called when: now - self.last_refresh_time > GLO['RESUME_TEST_SECONDS']
            Consequently long running processes must reseed self.last_refresh_time
            when they finish.
        """
        global rd
        _who = self.who + "ResumeFromSuspend():"

        self.ResumeWait()  # Display countdown waiting for devices to come online
        v1_print("\n" + _who, "ni.view_order:", ni.view_order)

        # Turn all devices on
        self.SetAllPower("ON")  # This also shows new status in devices treeview

        # Set variables to force rediscovery
        now = time.time()
        rd = None  # Just in case rediscovery was in progress during suspend
        self.rediscover_done = True
        # Force rediscovery immediately after resume from suspend
        self.last_rediscover_time = now - GLO['REDISCOVER_SECONDS'] * 10.0
        self.last_refresh_time = now + 1.0  # If abort, don't come back here
        sm.last_sensor_log = now - GLO['SENSOR_LOG'] - 1.0  # Force initial sensor log

    def ResumeWait(self, timer=None):
        """ Wait x seconds for devices to come online. If 'timer' passed do a
            simple countdown.

            :param timer: When time passed it's a countdown timer
        """

        _who = self.who + "ResumeWait():"

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
            title = "Countdown timer"

        if countdown_sec <= 0:
            return  # No delay after resume

        tf = (None, 96)  # default font family with 96 point size for countdown
        # 2 digits needs 300px width, 3 digits needs 450px width
        width = len(str(countdown_sec)) * 150
        self.dtb = message.DelayedTextBox(title=title, toplevel=self, width=width,
                                          height=250, startup_delay=0, abort=True,
                                          tf=tf, ta="center", win_grp=self.win_grp)
        # Loop until delay resume countdown finished or menu countdown finishes
        start = time.time()
        while time.time() < start + countdown_sec:
            if self.dtb.forced_abort:
                break
            if not self.winfo_exists():
                break  # self.CloseApp() has destroyed window
            self.dtb.update(str(int(start + countdown_sec - time.time())))
            # Suspend uses: 'self.after(150)'
            self.after(100)
            # During countdown timer, don't trigger ResumeFromSuspend()
            self.last_refresh_time = time.time() + 1.0

        if timer:  # Play sound when timer ends
            if self.CheckInstalled("aplay"):
                command_line_list = ["aplay", GLO['TIMER_ALARM']]
                self.runCommand(command_line_list, _who)
        self.dtb.close()
        self.dtb = None

    def SetAllPower(self, state):
        """ Loop through instances and set power state to "ON" or "OFF".
            Called by Suspend ("OFF") and Resume ("ON")
            If devices treeview is mounted, update power status in each row
        """
        _who = self.who + "SetAllPower(" + state + "):"
        night = cp.NightLightStatus()
        v1_print(_who, "Nightlight status: '" + night + "'")

        usingDevicesTreeview = \
            self.sensors_devices_btn['text'] != self.devices_btn_text

        # Loop through ni.instances
        for i, instance in enumerate(ni.instances):
            inst = instance['instance']

            # Computer is excluded from being turned on or off.
            if inst.type_code in GLO['POWER_ALL_EXCL_LIST']:
                continue

            # Don't turn on bias light during daytime
            night_powered_on = False
            if inst.type_code == GLO['HS1_SP']:
                # 2024-11-26 - 'type_code' s/b 'BIAS_LIGHT' and
                #   'sub_type_code' s/b 'GLO['HS1_SP']`
                v1_print("\n" + _who, "Bias light device: '" + inst.type + "'",
                         " | IP: '" + inst.ip + "'")
                if state == "ON" and night == "OFF":
                    self.dayPowerOff += 1
                    self.nightPowerOn = 0
                    self.menuPowerOff = 0
                    self.manualPowerOff = 0
                    self.suspendPowerOff = 0
                    v1_print(_who, "Do not turn on Bias light in daytime.")
                    continue  # Do not turn on light during daytime
                else:
                    v1_print(_who, "Turn on Bias light at night.")
                    night_powered_on = True

            if state == "ON":
                inst.TurnOn()
                self.resumePowerOn += 1  # Resume powered on the device
                self.menuPowerOn = 0  # User didn't power on the device via menu
                self.nightPowerOn += 1 if night_powered_on else 0
            elif state == "OFF":
                inst.TurnOff()
                self.suspendPowerOff += 1  # Suspend powered off the device
                self.menuPowerOff = 0  # User didn't power on the device via menu
            else:
                v0_print(_who, "state is not 'ON' or 'OFF':", state)
                exit()

            # Update Devices Treeview with power status
            if not usingDevicesTreeview:
                continue  # No Devices Treeview to update

            # Get treeview row based on matching MAC address + type
            # Note that Laptop MAC address can have two types (Base and Display)
            cr = TreeviewRow(self)  # Setup treeview row processing instance
            iid = cr.getInstanceIid(inst)  # Get iid number and set instance
            if iid is None:
                continue  # Instance not in Devices Treeview, perhaps a smartphone?

            old_text = cr.text  # Treeview row old power state "  ON", etc.
            cr.text = "  " + state  # Display treeview row new power state
            if cr.text != old_text:
                v1_print(_who, cr.mac, "Power status changed from: '"
                         + old_text.strip() + "' to: '" + cr.text.strip() + "'.")
            cr.Update(iid)  # Update iid with new ['text']

            # Display row by row when there is processing lag
            self.tree.update_idletasks()  # Slow mode display each row.

            # MAC address stored in treeview row hidden values[-1]
            v2_print("\n" + _who, "i:", i, "cr.mac:", cr.mac)
            v2_print("cr.inst:", cr.inst)

        v2_print()  # Blank line to separate debugging output

    def RefreshPowerStatus(self, start, end):
        """ 2024-11-27 - No longer used. Was always full range of devices treeview.
                Today replaced by RefreshAllPowerStatuses()

            Read range of treeview rows and reset power status.
            Device mac is stored in treeview row hidden column.
            TreeviewRow.Get() creates a device instance.
            Use device instance to get Power Status.
        """
        _who = self.who + "RefreshPowerStatus():"

        # MAC address stored in treeview row hidden values[-1]
        for i in range(start, end):  # loop rows
            cr = TreeviewRow(self)  # Setup treeview row processing instance
            cr.Get(i)  # Get existing row
            old_text = cr.text
            power_status = cr.inst.PowerStatus()
            cr.text = "  " + power_status
            if cr.text != old_text:
                v1_print(_who, cr.mac, "Power status changed from: '"
                         + old_text.strip() + "' to: '" + cr.text.strip() + "'.")
            cr.Update(i)  # Update row with new ['text']

            # Display row by row when there is processing lag
            self.tree.update_idletasks()  # Slow mode display each row.

            v2_print("\n" + _who, "i:", i, "cr.mac:", cr.mac)
            v2_print("cr.inst:", cr.inst)
            v2_print("power_status:", power_status)

        v2_print()  # Blank line to separate debugging output

    def RefreshAllPowerStatuses(self, auto=False):
        """ Read ni.instances and update the power statuses.
            Called from one place: self.Rediscover(auto=False)
            If Devices Treeview is visible (mounted) update power status.
            TreeviewRow.Get() creates a device instance.
            Use device instance to get Power Status.
        """
        _who = self.who + "RefreshAllPowerStatuses():"

        usingDevicesTreeview = \
            self.sensors_devices_btn['text'] != self.devices_btn_text

        # If auto, called automatically at GLO['REDISCOVER_SECONDS']
        cr = iid = None  # Assume Sensors Treeview is displayed
        if usingDevicesTreeview:
            cr = TreeviewRow(self)  # Setup treeview row processing instance

        # Loop through ni.instances
        for i, instance in enumerate(ni.instances):
            inst = instance['instance']
            if usingDevicesTreeview:
                # Get treeview row based on matching MAC address + device_type
                iid = cr.getInstanceIid(inst)  # Get iid number and set instance
                if iid is not None:
                    if auto is False or cr.text == "Wait...":
                        self.tree.see(iid)
                        cr.FadeIn(iid)

            inst.PowerStatus()  # Get the power status for device

            # Update Devices Treeview with power status
            if not usingDevicesTreeview:
                continue  # No Devices Treeview to update

            if iid is None:
                continue  # Instance not in Devices Treeview, perhaps a smartphone?

            old_text = cr.text  # Treeview row's old power state "  ON", etc.
            cr.text = "  " + inst.power_status  # Display treeview row's new power state
            if cr.text != old_text:
                v1_print(_who, cr.mac, "Power status changed from: '"
                         + old_text.strip() + "' to: '" + cr.text.strip() + "'.")
            cr.Update(iid)  # Update row with new ['text']
            if auto is False or old_text == "Wait...":
                # Fade in/out performed when called from Dropdown Menu.
                # Or on startup when status is "Wait...". Otherwise, too distracting.
                cr.FadeOut(iid)

            # Display row by row when there is processing lag
            self.tree.update_idletasks()  # Slow mode display each row.

            # MAC address stored in treeview row hidden values[-1]
            v2_print("\n" + _who, "i:", i, "cr.mac:", cr.mac)
            v2_print("cr.inst:", cr.inst)

        v2_print()  # Blank line to separate debugging output

    def Rediscover(self, auto=False):
        """ Automatically call 'arp -a' to check on network changes.
            Job split into many slices of 16ms until done.
            Sleep time between calls set with GLO['REDISCOVER_SECONDS'].

            2024-12-01 - TODO: Mouse motion resets last rediscovery time
        """

        _who = self.who + "Rediscover():"

        # Disable calling from File Dropdown Menubar
        self.file_menu.entryconfig("Rediscover now", state=tk.DISABLED)

        # If GLO['APP_RESTART_TIME'] is within 1 minute (GLO['REDISCOVER_SECONDS']) turn off
        # auto rediscovery flags so startup commands are logged to cmdEvents
        if GLO['APP_RESTART_TIME'] > time.time() - GLO['REDISCOVER_SECONDS'] - \
                GLO['RESUME_TEST_SECONDS'] - 10:
            auto = False  # Override auto rediscovery during startup / resuming

        # If called from menu, reseed last rediscovery time:
        if auto is False:
            self.last_rediscover_time = time.time() - GLO['REDISCOVER_SECONDS'] * 1.5

        # Is Devices Treeview mounted? (Other option is Sensors Treeview)
        usingDevicesTreeview = \
            self.sensors_devices_btn['text'] != self.devices_btn_text

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
        global rd  # global variable that allows rentry to split job into slices
        if rd is None:
            ext.t_init("Creating instance rd = NetworkInfo()")
            rd = NetworkInfo()  # rd. class is newer instance ni. class
            self.rediscover_done = False  # Signal job in progress
            ext.t_end('no_print')
            if auto:  # If called from File dropdown menubar DON'T return
                self.last_refresh_time = time.time()  # Override resume from suspend
                return  # Reenter refresh loop. Return here in 16 ms

        arp_count = len(rd.arp_dicts)
        v1_print(_who, "arp_count:", arp_count)

        # Refresh power status for all device instances in ni.arp_dicts
        self.RefreshAllPowerStatuses(auto=auto)
        GLO['LOG_EVENTS'] = True  # Reset to log events as required

        # TODO: process one row at a time to reduce chances of mouse-click lag
        #  OR:  Use splash message stating Refresh in progress

        # TODO: Process all rd.arp_dict entries for ip changes or new entries
        for i, rediscover in enumerate(rd.arp_dicts):
            mac = rediscover['mac']
            # TCL.LAN (192.168.0.17) at <incomplete> on enp59s0
            if mac == '<incomplete>':
                v1_print(_who, "Invalid MAC:", mac)
                continue

            ip = rediscover['ip']
            # ? (20.20.20.1) at a8:4e:3f:82:98:b2 [ether] on enp59s0
            if ip == '?':
                v1_print(_who, "Invalid IP:", ip)
                continue

            arp_mac = ni.arp_for_mac(mac)
            if not arp_mac:
                v1_print(_who, "MAC not found to treeview:", mac)
                #print("\n new arp_mac in rd.arp_dicts:", mac)
                # new arp_mac: 28:f1:0e:2a:1a:ed
                # new arp_mac: 9c:b6:d0:10:37:f7
                # add ni.arp_dicts, ni.instances, ni.devices, ni.view_order
                # add treeview row
                start = len(ni.arp_dicts)
                ni.arp_dicts.append(rediscover)
                discovered, instances, view_order = \
                    discover(update=False, start=start, end=start+1)

                if instances:
                    ni.instances.append(instances[0])
                    v1_print(_who, "Adding MAC to treeview:", mac)
                else:
                    v1_print(_who, "No instance for MAC:", mac)
                    continue
                ni.view_order.append(mac)
                ni.devices = copy.deepcopy(rd.devices)

                # Only update Devices Treeview when mounted.
                if not usingDevicesTreeview:
                    continue

                tr = TreeviewRow(self)
                tr.New(mac)
                new_row = len(self.tree.get_children())
                tr.Add(new_row)
                self.tree.see(str(new_row))
            else:
                pass  # TODO: 2024-11-28 - Check rd.arp changes from ni.arp

        # All steps done: Wait for next rediscovery period
        ni.cmdEvents.extend(rd.cmdEvents)  # For auto-rediscover, rd.cmdEvents[] empty
        rd = None
        self.rediscover_done = True
        self.last_rediscover_time = time.time()
        # 2024-12-02 - Couple hours watching TV, suddenly ResumeFromSuspend() ran
        #   a few times with 3 second countdown. Reset self.last_refresh_time.
        self.last_refresh_time = time.time()  # Prevent resume from suspend
        self.file_menu.entryconfig("Rediscover now", state=tk.NORMAL)
        self.EnableMenu()

    @staticmethod
    def MouseWheel(event):
        """ Mousewheel scroll defaults to 5 units, but tree has 4 images """
        if event.num == 4:  # Override mousewheel scroll up
            event.widget.yview_scroll(-1, "units")  # tree = event.widget
            return "break"  # Don't let regular event handler do scroll of 5
        if event.num == 5:  # Override mousewheel scroll down
            event.widget.yview_scroll(1, "units")  # tree = event.widget
            return "break"  # Don't let regular event handler do scroll of 5

    def GetPassword(self):
        """ Get Sudo password with message.AskString(show='*'...). """

        msg = "Sudo password required for laptop display.\n\n"
        answer = message.AskString(
            self, text=msg, thread=self.Refresh, show='*',
            title="Enter sudo password", icon="information")

        # Setting laptop display power requires sudo prompt which causes fake resume
        self.last_refresh_time = time.time()  # Refresh idle loop last entered time

        if answer.result != "yes":
            return None  # Cancel button selected

        # Validate password, error message if invalid
        password = hc.ValidateSudoPassword(answer.string)
        if password is None:
            msg = "Invalid sudo password!\n\n"
            message.ShowInfo(
                self, text=msg, thread=self.Refresh,
                title="Invalid sudo password", icon="error")

        self.last_refresh_time = time.time()  # Refresh idle loop last entered time
        return password  # Will be <None> if invalid password entered

    def Preferences(self):
        """ Edit preferences """

        if self.edit_pref_active and self.pref_nb:
            self.pref_nb.focus_force()
            self.pref_nb.lift()
            return

        self.pref_nb = notebook = self.edit_pref_active = None

        def close(*_args):
            """ Close window painted by this pretty_column() method """
            if not self.edit_pref_active:
                return
            #notebook.unbind("<Button-1>")  # 2024-12-21 TODO: old code, use unknown
            #self.win_grp.unregister_child(self.pref_nb)
            self.tt.close(self.pref_nb)
            self.edit_pref_active = None  # 2024-12-24 needed in homa?
            self.pref_nb.destroy()
            self.pref_nb = None
            #self.btn_frm.grid()  # Restore Application() bottom button bar

        #self.btn_frm.grid_forget()  # Hide Application() bottom button bar
        ha_font = (None, g.MON_FONT)  # ms_font = mserve, ha_font = HomA
        # style: https://stackoverflow.com/a/54213658/6929343
        style = ttk.Style()
        style.configure('TNotebook.Tab', font=ha_font, padding=[10, 10],
                        relief="sunken", background="WhiteSmoke",
                        borderwidth=3, highlightthickness=3)
        style.map("TNotebook.Tab",
                  background=[("active", "SkyBlue3"), ("selected", "LightBlue")],
                  foreground=[("active", "Black"), ("selected", "Black")])

        style.configure("TNotebook", background="White", padding=[10, 10],
                        relief="raised")
        style.configure("TFrame", background="WhiteSmoke")
        style.configure("Notebook.TFrame", background="WhiteSmoke")
        style.configure("TLabel", background="WhiteSmoke")

        # Not working:
        style.map('TEntry', lightcolor=[('focus', 'LemonChiffon')])
        
        self.pref_nb = ttk.Notebook(self)
        self.edit_pref_active = True

        listTabs, listFields = glo.defineNotebook()
        toolkit.makeNotebook(self.pref_nb, listTabs, listFields,
                             GLO, "TNotebook.Tab", "Notebook.TFrame",
                             "C.TButton", close, tt=self.tt)

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
        # Do not auto raise children. homa.py will take care of that with FocusIn()

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
            :param events: self.cmdEvents from DeviceCommonSelf() class
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

                errors = event['error'].splitlines()  # Error lines split on "\n"
                for error in errors:
                    scrollbox.insert("end", "\t\t" + error + "\n")

        # Loop through ni.instances
        for i, instance in enumerate(ni.instances):
            inst = instance['instance']
            insertEvents(inst.cmdEvents)

        # NetworkInfo (ni) and SystemMonitor (sm) have cmdEvents too!
        insertEvents(ni.cmdEvents)
        insertEvents(sm.cmdEvents)
        insertEvents(cp.cmdEvents)  # cp = Computer() class
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
        insertEvents(ni.cmdEvents)
        insertEvents(sm.cmdEvents)
        insertEvents(cp.cmdEvents)  # cp = Computer() class
        insertEvents(self.cmdEvents)  # This app = Application() class

        scrollbox.highlight_pattern("Min:", "green")
        scrollbox.highlight_pattern("Max:", "red")
        scrollbox.highlight_pattern("Avg:", "yellow")

    def DisplayCommon(self, _who, title):
        """ Common method for DisplayErrors() and DisplayTime() """

        if self.event_scroll_active and self.event_top:
            self.event_top.focus_force()
            self.event_top.lift()
            return

        self.event_top = scrollbox = self.event_scroll_active = None

        def close(*_args):
            """ Close window painted by this pretty_column() method """
            if not self.event_scroll_active:
                return
            scrollbox.unbind("<Button-1>")  # 2024-12-21 TODO: old code, use unknown
            self.win_grp.unregister_child(self.event_top)
            self.event_scroll_active = None
            self.event_top.destroy()
            self.event_top = None

        self.event_top = tk.Toplevel()
        x, y = hc.GetMouseLocation()
        self.event_top.geometry('%dx%d+%d+%d' % (1200, 500, int(x), int(y)))
        self.event_top.minsize(width=120, height=63)
        self.event_top.title(title)

        self.event_top.columnconfigure(0, weight=1)
        self.event_top.rowconfigure(0, weight=1)
        self.event_top.configure(background="WhiteSmoke")  # Future user configuration
        self.win_grp.register_child(title, self.event_top)  # Lifting & moving with parent
        self.event_scroll_active = True

        ''' Bind <Escape> to close window '''
        self.event_top.bind("<Escape>", close)
        self.event_top.protocol("WM_DELETE_WINDOW", close)

        ''' frame - Holds scrollable text entry and button(s) '''
        frame = ttk.Frame(self.event_top, borderwidth=g.FRM_BRD_WID,
                          padding=(2, 2, 2, 2), relief=tk.RIDGE)
        frame.grid(column=0, row=0, sticky=tk.NSEW)
        ha_font = (None, g.MON_FONT)  # ms_font = mserve, ha_font = HomA

        close_btn = ttk.Button(
            frame, width=7, text="✘ Close", style="C.TButton", command=close)
        close_btn.grid(row=1, column=0, padx=10, pady=5, sticky=tk.E)

        scrollbox = toolkit.CustomScrolledText(
            frame, state="normal", font=ha_font, borderwidth=15, relief=tk.FLAT)
        toolkit.scroll_defaults(scrollbox)  # Default tab stops are too wide
        scrollbox.config(tabs=("5m", "10m", "15m"))
        scrollbox.grid(row=0, column=0, padx=3, pady=3, sticky=tk.NSEW)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)  # 2024-07-13 - Was column 1

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

        return scrollbox


class TreeviewRow(DeviceCommonSelf):
    """ Device treeview row variables and methods.

        Sensors treeview uses dummy call to TreeviewRow() class in order to call
        FadeIn() and FadeOut() methods.

    """

    def __init__(self, top):
        """ DeviceCommonSelf(): Variables used by all classes
        :param top: Toplevel created by Application() class instance.
        """
        DeviceCommonSelf.__init__(self, "TreeviewRow().")  # Define self.who

        self.top = top
        self.tree = self.top.tree  # Shortcut
        self.photos = self.top.photos  # Shortcut
        self.item = None  # Treeview Row iid
        self.photo = None  # Photo image
        self.text = None  # Row text, E.G. "ON", "OFF"

        self.values = None  # Row values - Name lines, Attribute lines, MAC
        self.name_column = None  # Device Name & IP address - values[0]
        self.attribute_column = None  # 3 line device Attributes - values[1]
        self.mac = None  # MAC address - hidden row values[-1] / values[2]
        # self.mac - arp_dict['mac'] - is non-displayed treeview column 
        # used to reread arp_dict
        
        self.arp_dict = None  # device dictionary
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
        self.mac = self.values[2]  # arp_dict['mac'] is non-displayed value

        self.arp_dict = ni.arp_for_mac(self.mac)
        self.inst_dict = ni.inst_for_mac(self.mac)
        self.inst = self.inst_dict['instance']

    def getInstanceIid(self, inst):
        """ Using passed instance, get the treeview row. """
        for iid in self.tree.get_children():
            self.Get(iid)
            if self.inst.mac == inst.mac and self.inst.type == inst.type:
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

    def New(self, mac):
        """ Create default treeview row """

        _who = self.who + "New():"
        self.arp_dict = ni.arp_for_mac(mac)

        # self.mac is non-displayed treeview column used to reread arp_dict
        self.mac = mac  # MAC address
        self.inst_dict = ni.inst_for_mac(mac)  # instance dictionary
        try:
            self.inst = self.inst_dict['instance']
        except KeyError:
            v0_print("self.inst_dict has no 'instance' key:", self.inst_dict)
            v0_print("self.arp_dict has no instance:", self.arp_dict)
            return

        try:
            type_code = self.arp_dict['type_code']
        except KeyError:
            v0_print(_who, "Key 'type_code' not in 'arp_dict':", self.arp_dict)
            type_code = None

        # TV's are 16/9 = 1.8. Treeview uses 300/180 image = 1.7.
        if type_code == GLO['HS1_SP']:  # TP-Line Kasa Smart Plug HS100 image
            photo = ImageTk.PhotoImage(Image.open("bias.jpg").resize((300, 180), Image.ANTIALIAS))
        elif type_code == GLO['KDL_TV']:  # Sony Bravia KDL TV image
            photo = ImageTk.PhotoImage(Image.open("sony.jpg").resize((300, 180), Image.ANTIALIAS))
        elif type_code == GLO['TCL_TV']:  # TCL / Google Android TV image
            photo = ImageTk.PhotoImage(Image.open("tcl.jpg").resize((300, 180), Image.ANTIALIAS))
        elif type_code == GLO['DESKTOP']:  # Desktop computer image
            photo = ImageTk.PhotoImage(Image.open("computer.jpg").resize((300, 180), Image.ANTIALIAS))
        elif type_code == GLO['LAPTOP_B']:  # Laptop Base image
            photo = ImageTk.PhotoImage(Image.open("laptop_b.jpg").resize((300, 180), Image.ANTIALIAS))
        elif type_code == GLO['LAPTOP_D']:  # Laptop Display image
            photo = ImageTk.PhotoImage(Image.open("laptop_d.jpg").resize((300, 180), Image.ANTIALIAS))
        else:
            v0_print(_who, "Unknown 'type_code':", type_code)
            photo = None

        self.photo = photo
        # Did program just start, or is power status already known?
        if self.inst.power_status == "?":  # Initial boot
            self.text = "Wait..."  # Power status checked when updating treeview
        else:
            self.text = "  " + self.inst.power_status  # Power state already known
        self.name_column = self.inst.name
        self.name_column += "\nIP: " + self.arp_dict['ip']
        self.attribute_column = self.arp_dict['alias']
        self.attribute_column += "\nMAC: " + self.arp_dict['mac']
        self.attribute_column += "\n" + self.inst.type
        self.values = (self.name_column, self.attribute_column, self.mac)

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

        ''' 2024-11-29 - Use faster method for repainting devices treeview '''
        if p_args.fast:
            text = "Wait..."  # Wait for idle loop
        else:
            self.inst.PowerStatus()
            text = "  " + self.inst.power_status

        self.text = text

        self.top.tree.insert(
            '', 'end', iid=trg_iid, text=self.text,
            image=self.top.photos[-1], value=self.values)

    def FadeIn(self, item):
        """ Fade In over 10 steps of 30 ms """
        toolkit.tv_tag_remove(self.tree, item, 'normal')  # Same as step 10
        for i in range(10):
            if i != 0:
                toolkit.tv_tag_remove(self.tree, item, 'fade' + str(i - 1))
            if i != 9:
                toolkit.tv_tag_add(self.tree, item, 'fade' + str(i))
            else:
                toolkit.tv_tag_add(self.tree, item, 'curr_sel')  # Same as step 10
            #self.top.update()
            #self.top.after(10)  # 20 milliseconds
            self.tree.update()  # Change from .top to .tree for SystemMonitor to use
            self.tree.after(10)  # 20 milliseconds

    def FadeOut(self, item):
        """ Fade Out over 10 steps of 30 ms """
        toolkit.tv_tag_remove(self.tree, item, 'curr_sel')  # Same as step 10
        for i in range(9, -1, -1):
            if i != 9:
                toolkit.tv_tag_remove(self.tree, item, 'fade' + str(i))
            if i > 0:
                toolkit.tv_tag_add(self.tree, item, 'fade' + str(i))
            else:
                toolkit.tv_tag_add(self.tree, item, 'normal')  # Same as step 10
            self.tree.update()
            self.tree.after(10)  # 30 milliseconds


class SystemMonitor(DeviceCommonSelf):
    """ System Monitor - sensors CPU/GPU Temp and Fan Speeds.

        Print results to console unless `homa.py -s` (silent) was used.

        TODO: Add average CPU Mhz and Load %.
              Add Top 20 programs with Top 3 displayed.
              Display volume level changes with lib-notify (tvpowered).
              Suspend all and resume all (tvpowered).
              Dimmer (movie.sh) features where wakeup is based on mouse
                passing over monitor for five seconds.
              xrandr monitor details - geometry & resolution.
              mmm features - track window geometry every minute.
              eyesome interface for functions needing sudo permissions.
    """

    def __init__(self, top):
        """ DeviceCommonSelf(): Variables used by all classes
        :param top: Toplevel created by Application() class instance.
        """
        DeviceCommonSelf.__init__(self, "SystemMonitor().")  # Define self.who

        import socket
        # https://docs.python.org/3/library/socket.html#socket.getaddrinfo
        hostname = socket.gethostname()
        #print("Your Computer hostname is:", hostname)  # alien

        _IPAddr = socket.gethostbyname(hostname)
        #print("Your Computer IP Address is:", _IPAddr)  # 127.0.1.1

        _IPAddr_ex = socket.gethostbyname_ex(hostname)
        #print("Your Computer IP Address_ex is:")
        #for tup in IPAddr_ex:
        #    print(tup)
        # ('Alien',
        # ['AW', '17R3', 'WiFi', '9c:b6:d0:10:37:f7',
        #  'AW', '17R3', 'Ethernet', '28:f1:0e:2a:1a:ed'],
        # ['127.0.1.1', '192.168.0.10', '192.168.0.12'])

        _who = self.who + "__init__():"

        self.top = top  # Copy of toplevel for creating treeview
        self.tree = self.top.tree  # Pre-existing Applications() devices tree
        self.photos = self.top.photos  # Applications() device photos
        self.item = None  # Applications() Treeview Row iid
        self.photo = None  # Applications() Photo image
        self.text = None  # Applications() Row text, E.G. "ON", "OFF"

        self.values = None  # Applications() Row values - Name lines, Attribute lines, MAC
        self.name_column = None  # Applications() Device Name & IP address - values[0]
        self.attribute_column = None  # Applications() 3 line device Attributes - values[1]
        self.mac = None  # Applications() MAC address - hidden row values[-1] / values[2]

        self.arp_dict = None  # Applications() device dictionary
        self.inst = None  # Applications() device instance
        self.inst_dict = None  # Applications() instance dictionary

        self.type = "System Monitor"
        self.type_code = 200  # Need CODE setup
        self.requires = ['ifconfig', 'iwconfig', 'sensors', 'top']
        self.installed = []
        self.CheckDependencies(self.requires, self.installed)

        v3_print(_who, "Dependencies:", self.requires)
        v3_print(_who, "Installed?  :", self.installed)
        if not self.dependencies_installed:
            v1_print(_who, "System Monitor dependencies are not installed.")

        self.last_sensor_check = 0.0  # check every x seconds
        self.last_sensor_log = 0.0  # log every x seconds
        self.skipped_checks = 0  # Skipped check when last check < x seconds
        self.number_checks = 0  # Number of checks
        self.skipped_fan_same = 0  # Don't log when fan speed the same
        self.skipped_fan_200d = 0  # Don't log when fan speed different by 200 RPM
        self.skipped_logs = 0  # Skipped logs due to time or fan speed ~ the same
        self.number_logs = 0  # Number of logs
        self.sensors_log = []  # List of self.curr_sensor dictionaries
        self.curr_sensor = None  # Dict {"Processor Fan": "4500 RPM", ... }
        self.last_sensor = None  # Last version of curr_sensor

        ''' Sensor treeview - redeclare self.tree - Applications().tree '''
        self.treeview_created = False  # If false create treeview first time
        self.treeview_active = False  # If false then Application devices tree active
        # Note devices tree must be reset to height 1 before self.treeview displayed
        self.fade_in_row = None  # 300ms flash new row in treeview
        self.fade_in_time = None
        self.fade_in_step = None

    def Sensors(self):
        """ Wait for appropriate sleep time to expire.
            Call `sensors` (if installed), else return.
            If not dell machine with `sensors` output, then return.
            Record CPU & GPU temperatures and fan speeds to self.sensors_log.
        """

        _who = self.who + "Sensors():"
        if not self.CheckInstalled('sensors'):
            return

        ''' Sample output from `sensors` (first 7 lines):
            $ sensors
            dell_smm-virtual-0
            Adapter: Virtual device
            Processor Fan: 5200 RPM
            Video Fan:     5000 RPM
            CPU:            +59.0°C  
            GPU:            +64.0°C  
            SODIMM:         +61.0°C  

        '''
        now = time.time()
        if now - self.last_sensor_check < GLO['SENSOR_CHECK']:
            self.skipped_checks += 1
            return

        def CheckFanChange(key):
            """ If fan speed changed by more than GLO['FAN_GRANULAR'] RPM, force logging.
                Called for "Processor Fan" and "Video Fan" A.K.A. "fan3".
            :param key: 'Processor Fan' or 'Video Fan', etc.
            :return: True of curr_sensor == last_sensor
            """
            try:
                curr = self.curr_sensor[key]
                last = self.last_sensor[key]
                if curr == last:
                    self.skipped_fan_same += 1
                    return False
            except (TypeError, IndexError):
                # First time last log doesn't exist. Treat as fan speed change.
                self.last_sensor_log = time.time() - GLO['SENSOR_LOG'] * 2
                return True

            # Speed can fluctuate 2400 RPM, 2600 RPM, 2400 RPM...  18 times
            # over 200 seconds. To reduce excessive fan speed change logging,
            # skip fluctuations <= GLO['FAN_GRANULAR'] RPM.
            curr = float(curr.split(" ")[0])
            last = float(last.split(" ")[0])
            diff = abs(curr - last)
            # Only report fan speed differences > 200 RPM
            if diff <= GLO['FAN_GRANULAR']:
                #print("skipping diff:", diff)
                self.skipped_fan_200d += 1
                return False  # Don't override last with current

            # Fan speed changed. Force logging by resetting last log time.
            self.last_sensor_log = time.time() - GLO['SENSOR_LOG'] * 2
            return True

        self.number_checks += 1
        log = True if len(self.sensors_log) == 0 else False
        event = self.runCommand(['sensors'], _who, log=log)
        result = event['output']
        self.last_sensor_check = now

        # Parse `sensors` output to dictionary key/value pairs
        dell_found = False
        self.curr_sensor = {}
        for res in result.split("\n"):
            parts = res.split(":")
            # Keys not logged: SODIMM:, temp1:, id 0: Core 0:, Core 1:...
            if len(parts) != 2:
                if "dell_smm-virtual-0" in res:
                    dell_found = True
                continue  # Line doesn't have Key/Value pair
            if "fan" in parts[0].lower():
                if "fan3" in parts[0]:
                    # 2024-11-12 - Glitch "Video Fan" was replaced with "fan3" today.
                    parts[0] = "Video Fan"
                self.curr_sensor[parts[0]] = parts[1].strip()
                CheckFanChange(parts[0])
            if "PU" in parts[0]:
                self.curr_sensor[parts[0]] = parts[1].strip().encode('utf-8')

        if not dell_found:
            return  # Not an Alienware 17R3 or similar DELL machine

        # Is it time to log data?
        if now - self.last_sensor_log < GLO['SENSOR_LOG']:
            self.skipped_logs += 1
            return

        # Add dictionary to list
        self.last_sensor_log = now
        log_delta = round(now - GLO['APP_RESTART_TIME'], 2)
        self.curr_sensor['delta'] = log_delta
        self.curr_sensor['time'] = time.time()
        self.sensors_log.append(self.curr_sensor)
        self.number_logs += 1
        self.last_sensor = self.curr_sensor

        self.Print()  # print the last log and/or insert tree row

    def Print(self, start=-1, end=-1, tree_only=False):
        """ Print self.sensors_log[start:end] to console
            2024-11-03 - Rudimentary format with hard-coded keys.
            2024-11-22 - Now homa.py called from homa-indicator.py with no console.
            2024-11-24 - Enhance with treeview to show sensors.
        """

        if start == -1:
            start = len(self.sensors_log) - 1
        if end == -1:
            end = len(self.sensors_log)

        def headings():
            """ Print headings when log count = 1 """

            # TODO: first check if Dell fans can be discovered.
            v0_print()
            v0_print("= = = = = System Monitor Processor Temps & Fans = = = = =")
            v0_print(" Seconds | CPU Temp Fan RPM | GPU Temp Fan RPM |   Time  ")
            v0_print("-------- | ---------------- | ---------------- | --------")

        def opt(key):
            """ Return optional key or N/A if not found. """
            try:
                return sensor[key]
            except KeyError:
                return "N/A"

        if len(self.sensors_log) == 1 and not tree_only:
            headings()  # If first sensors log, print headings

        for i in range(start, end):
            sensor = self.sensors_log[i]
            # When tree_only is True, printing has already been done to console
            if not tree_only:
                v0_print("{0:>8.2f}".format(sensor['delta']),  # "999.99" format
                         '|', opt('CPU').rjust(7), opt('Processor Fan').rjust(8),
                         '|', opt('GPU').rjust(7), opt('Video Fan').rjust(8),
                         '|', dt.datetime.now().strftime('%I:%M %p').strip('0').rjust(8))

            if self.treeview_active:
                self.InsertTreeRow(sensor)
                self.FlashLastRow()  # fade in color, pause, fade out color

    def PopulateTree(self):
        """ Populate treeview using self.sensor_log [{}, {}... {}]
            Treeview IID is string seconds: "0.1", "1.1", "2.2" ... "9999.9"
        """
        _who = self.who + "PopulateTree():"

        ''' Treeview style is large images in cell 0 '''
        style = ttk.Style()
        style.configure("Treeview.Heading", font=(None, g.MED_FONT),
                        rowheight=int(g.LARGE_FONT * 2.2))  # FONT14 alias
        row_height = int(g.LARGE_FONT * 2.2)
        style.configure("Treeview", font=g.FONT14, rowheight=row_height,
                        background="WhiteSmoke", fieldbackground="WhiteSmoke")

        ''' Create treeview frame with scrollbars '''
        # Also once image placed into treeview row, it can't be read from the row.
        self.tree = ttk.Treeview(self.top, column=('Seconds', 'CPU', 'GPU', 'Time'),
                                 selectmode='none', style="Treeview", show="headings")

        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scroll = tk.Scrollbar(self.top, orient=tk.VERTICAL,
                                width=14, command=self.tree.yview)
        v_scroll.grid(row=0, column=1, sticky=tk.NS)
        self.tree.configure(yscrollcommand=v_scroll.set)
        #self.top.rowconfigure(0, weight=0)  # Devices Tree
        #self.top.rowconfigure(1, weight=1)  # Sensors Tree
        #self.top.rowconfigure(2, weight=1)  # Button bar

        # Oct 1, 2023 - MouseWheel event does NOT capture any events
        self.tree.bind("<MouseWheel>", lambda event: self.MouseWheel(event))
        # Button-4 is mousewheel scroll up event
        self.tree.bind("<Button-4>", lambda event: self.MouseWheel(event))
        # Button-5 is mousewheel scroll down event
        self.tree.bind("<Button-5>", lambda event: self.MouseWheel(event))

        # Setup column heading - #0, #1, #2 denotes the 1st, 2nd & 3rd, etc. columns
        self.tree.heading('#1', text='Seconds', anchor=tk.E)
        self.tree.heading('#2', text='CPU Temp / Fan Speed')  # anchor defaults to center
        self.tree.heading('#3', text='GPU Temp / Fan Speed')
        self.tree.heading('#4', text='Time')
        # anchor defaults to left
        self.tree.column('Seconds', anchor=tk.E, width=100, stretch=True)
        self.tree.column('CPU', anchor='center', width=250, stretch=True)
        self.tree.column('GPU', anchor='center', width=250, stretch=True)
        self.tree.column('Time', anchor='center', width=100, stretch=True)

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

        # Build Sensors treeview
        self.Print(start=0, end=-1, tree_only=True)

    def FlashLastRow(self):
        """ Flash the last row in Sensors Treeview """
        _who = self.who + "FlashLastRow():"
        cr = TreeviewRow(self)  # also used by Applications() devices treeview
        iid = self.sensors_log[-1]['delta']  # delta is time since app started

        # iid is Number right justified 8 = 5 whole + decimal + 2 fraction
        trg_iid = "{:>8.2f}".format(iid)  # E.G. iid = "2150.40" seconds

        try:
            _item = self.tree.item(trg_iid)
        except tk.TclError:
            v0_print("\n" + _who, "trg_iid not found: '" + str(iid) + "'",
                     " | <type>:", type(iid))
            # SystemMonitor().FlashLastRow(): trg_iid not found: '20.04'
            #   | <type>: <type 'float'>
            v0_print("self.sensors_log[-1]:", self.sensors_log[-1])
            # self.sensors_log[-1]:
            #   {'Processor Fan': '4500 RPM', 'delta': 20.04,
            #   'Video Fan': '4600 RPM', 'time': 1735398654.633827,
            #   'GPU': '+78.0\xc2\xb0C', 'CPU': '+78.0\xc2\xb0C'}
            return

        cr.FadeIn(trg_iid)
        time.sleep(3.0)
        cr.FadeOut(trg_iid)

    def InsertTreeRow(self, sensor):
        """ Insert sensors row into sensors treeview
            :param sensor: = {delta: seconds, CPU: temp, Processor Fan: rpm,
                              GPU: temp, Video Fan: rpm}

        """
        _who = self.who + "InsertTreeRow():"

        def opt(key):
            """ Return optional key or N/A if not found. """
            try:
                return sensor[key]
            except KeyError:
                return "N/A"

        # Possible image showing temperature of CPU?
        trg_iid = "{0:>8.2f}".format(sensor['delta'])
        try:
            self.tree.insert(
                '', 'end', iid=trg_iid,
                value=(trg_iid,
                       opt('CPU').rjust(7) + " / " + opt('Processor Fan').rjust(8),
                       opt('GPU').rjust(7) + " / " + opt('Video Fan').rjust(8),
                       dt.datetime.fromtimestamp(sensor['time']).
                       strftime('%I:%M %p').strip('0').rjust(8)))
        except tk.TclError:
            v0_print(_who, "trg_iid already exists in Sensors Treeview:", trg_iid)

        self.tree.see(trg_iid)
        # 2024-12-28: Occasionally iid not found in FlashLastRow() so update_idletasks
        self.tree.update_idletasks()

    @staticmethod
    def MouseWheel(event):
        """ Mousewheel scroll defaults to 5 units """
        if True is True:  # 2024-11-24 - initial creation
            return  # Leave at default 5 rows scrolling

        if event.num == 4:  # Override mousewheel scroll up
            event.widget.yview_scroll(-1, "units")  # tree = event.widget
            return "break"  # Don't let regular event handler do scroll of 5
        if event.num == 5:  # Override mousewheel scroll down
            event.widget.yview_scroll(1, "units")  # tree = event.widget
            return "break"  # Don't let regular event handler do scroll of 5


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
    """ Return list of all macs and their types discovered. 
        :param update: If True update ni.arp_dicts
        :param start: ni.arp_dicts starting index for loop
        :param end: ni.arp_dicts ending index (before) for loop
    """
    global ni  # NetworkInformation() class instance used everywhere
    _who = "homa.py discover()"
    discovered = []  # List of discovered devices in arp dictionary format
    instances = []  # List of instances shadowing each discovered device
    view_order = []  # Order of macs discovered

    v1_print("\n")
    v1_print("="*20, " Test all arp devices for their type ", "="*20)
    v1_print()

    if not start:
        start = 0
    if not end:
        end = len(ni.arp_dicts)  # Not tested as of 2024-11-10

    for i, arp in enumerate(ni.arp_dicts[start:end]):
        v2_print("\nTest for device type using 'arp' dictionary:", arp)

        # Next two sanity checks copied from Application().Rediscover()
        mac = arp['mac']
        # TCL.LAN (192.168.0.17) at <incomplete> on enp59s0
        if mac == '<incomplete>':
            v1_print(_who, "Invalid MAC:", mac)
            continue

        ip = arp['ip']
        # ? (20.20.20.1) at a8:4e:3f:82:98:b2 [ether] on enp59s0
        if ip == '?':
            v1_print(_who, "Invalid IP:", ip)
            continue

        def test_one(cname):
            """ Test if hs100, SonyTV, GoogleTV, etc. """
            inst = cname(arp['mac'], arp['ip'], arp['name'], arp['alias'])
            is_device = inst.isDevice(forgive=True)
            if not is_device:
                return False

            v1_print(arp['mac'], " # ", arp['ip'].ljust(15),
                     "##  is a " + inst.type + " code =", inst.type_code)
            arp['type_code'] = inst.type_code  # Assign 10, 20 or 30
            discovered.append(arp)  # Saved to disk

            # Get class instance information
            instances.append({"mac": arp['mac'], "instance": inst})
            view_order.append(arp['mac'])
            # Instance always rebuilt at run time and never saved to disk
            if update:
                ni.arp_dicts[i] = arp  # Update arp list
            return True  # Grab next type

        # Test smart plug first because they seem most "fragile"
        if test_one(SmartPlugHS100):
            continue

        if test_one(Computer):
            continue

        if test_one(LaptopDisplay):
            continue

        if test_one(SonyBraviaKdlTV):
            continue

        if test_one(TclGoogleAndroidTV):
            continue

    return discovered, instances, view_order


v1_print(sys.argv[0], "- Home Automation", " | verbose1:", p_args.verbose1,
         " | verbose2:", p_args.verbose2, " | verbose3:", p_args.verbose3,
         " | fast:", p_args.fast, " | silent:", p_args.silent)

''' Global classes '''
root = None  # Tkinter toplevel
app = None  # Application GUI
cfg = sql.Config()  # Colors configuration SQL records
glo = Globals()  # Global variables
GLO = glo.dictGlobals  # global dictionary
cp = Computer()  # cp = Computer Platform
ni = NetworkInfo()  # ni = global class instance used everywhere
ni.adb_reset(background=True)  # When TCL TV is communicating this is necessary
rd = NetworkInfo()  # rd = Rediscovery instance for app.Rediscover() & app.Discover()
sm = None  # sm = System Monitor - fan speed and CPU temperatures

SAVE_CWD = ""  # Saved current working directory. Will change to program directory.
killer = ext.GracefulKiller()  # Class instance for shutdown or CTRL+C

v0_print()
v0_print(r'  ######################################################')
v0_print(r' //////////////                            \\\\\\\\\\\\\\')
v0_print(r'<<<<<<<<<<<<<<    HomA - Home Automation    >>>>>>>>>>>>>>')
v0_print(r' \\\\\\\\\\\\\\                            //////////////')
v0_print(r'  ######################################################')
v0_print(r'                    Started:',
         dt.datetime.now().strftime('%I:%M %p').strip('0'))


def open_files():
    """ Called during startup. Read "devices.json" file if it exists.
        Return previously discovered devices and build new instances.
        Reading from disk quickly mirrors discover() generation:
            ni.arp_dicts[{}, {}...{}] - all devices, optional type_code
            discovered[{}, {}...{}] - devices only with type_code
            ni.instances[{}, {}...{}] - instances matching discovered
    """
    _who = "homa.py open_files():"

    glo.openFile()
    sql.open_homa_db()  # Open SQL History Table for saved configs

    ni.discovered = []  # NetworkInfo() lists
    ni.instances = []
    ni.view_order = []
    fname = g.USER_DATA_DIR + os.sep + GLO['DEVICES_FNAME']
    if not os.path.isfile(fname):
        return ni.discovered, ni.instances, ni.view_order

    with open(fname, "r") as f:
        # TODO: discover() will wipe out ni.arp_dicts.
        #       Must merge old and new ni.arp_dicts.
        v2_print("Opening last arp dictionaries file:", fname)
        ni.arp_dicts = json.loads(f.read())

    fname = g.USER_DATA_DIR + os.sep + GLO['VIEW_ORDER_FNAME']
    build_view_order = True
    if os.path.isfile(fname):
        with open(fname, "r") as f:
            v2_print("Opening last view order file:", fname)
            ni.view_order = json.loads(f.read())
            build_view_order = False

    # Assign instances
    for arp in ni.arp_dicts:
        try:
            type_code = arp['type_code']
        except KeyError:
            continue  # This device isn't recognized as actionable

        ni.discovered.append(arp)  # Add discovered device that can be instantiated

        if type_code == GLO['HS1_SP']:  # TP-Link Kasa HS100 smart plug?
            inst = SmartPlugHS100(arp['mac'], arp['ip'], arp['name'], arp['alias'])
        elif type_code == GLO['KDL_TV']:  # Sony Bravia KDL TV supporting REST API?
            inst = SonyBraviaKdlTV(arp['mac'], arp['ip'], arp['name'], arp['alias'])
        elif type_code == GLO['TCL_TV']:  # TCL / Google Android TV supporting adb?
            inst = TclGoogleAndroidTV(arp['mac'], arp['ip'], arp['name'], arp['alias'])
        elif type_code == GLO['DESKTOP']:  # Desktop computer image
            inst = Computer(arp['mac'], arp['ip'], arp['name'], arp['alias'])
        elif type_code == GLO['LAPTOP_B']:  # Laptop Base image
            inst = Computer(arp['mac'], arp['ip'], arp['name'], arp['alias'])
        elif type_code == GLO['LAPTOP_D']:  # Laptop Display image
            inst = LaptopDisplay(arp['mac'], arp['ip'], arp['name'], arp['alias'])
        else:
            inst = None  # Oops
            v0_print(_who, "Data corruption. Unknown type_code:", type_code)
            exit()

        # Device instances created for this session.
        ni.instances.append({"mac": arp['mac'], "instance": inst})
        if build_view_order:
            ni.view_order.append(arp['mac'])
        else:
            pass  # Check for new MACs not in saved ni.view_order

    # Same return structure as discover()
    return ni.discovered, ni.instances, ni.view_order  


def save_files():
    """ Called when exiting and on demand. """
    with open(g.USER_DATA_DIR + os.sep + GLO['DEVICES_FNAME'], "w") as f:
        f.write(json.dumps(ni.arp_dicts))
    with open(g.USER_DATA_DIR + os.sep + GLO['VIEW_ORDER_FNAME'], "w") as f:
        f.write(json.dumps(ni.view_order))

    # Close SQL History Table for color configurations
    sql.close_homa_db()
    glo.saveFile()


def main():
    """ Save current directory, change to ~/homa directory, load app GUI
        When existing restore original current directory.
    """
    global root  # named when main() called
    global app
    global ni  # NetworkInformation() class instance used everywhere
    global SAVE_CWD  # Saved current working directory to restore on exit

    ''' Save current working directory '''
    SAVE_CWD = os.getcwd()  # Bad habit from old code in mserve.py
    if SAVE_CWD != g.PROGRAM_DIR:
        v1_print("Changing from:", SAVE_CWD, "to g.PROGRAM_DIR:", g.PROGRAM_DIR)
        os.chdir(g.PROGRAM_DIR)

    ni = NetworkInfo()  # Generate Network Information for arp and hosts

    # ni.adb_reset()  # adb kill-server && adb start-server
    # 2024-10-13 - adb_reset() is breaking TCL TV discovery???
    _discovered, _instances, _view_order = open_files()
    if len(_instances) == 0:
        # Discover all devices and update ni.arp_dicts
        ni.discovered, ni.instances, ni.view_order = discover(update=True)

        v1_print()
        v1_print("discovered list of dictionaries - [1. {}, 2. {} ... 9. {}]:")
        for i, entry in enumerate(ni.discovered):
            v1_print("  ", str(i+1) + ".", entry)
        for i, entry in enumerate(ni.instances):
            v1_print("  ", str(i+1) + ".", entry)

    ''' OBSOLETE - Create Tkinter "very top" Top Level window '''
    #root = tk.Tk()  # Create "very top" toplevel for all top levels
    #monitor.center(root)
    #root.withdraw()  # Remove default window because we have own windows

    ''' Open Main Application Window '''
    root = tk.Tk()
    #root.overrideredirect(1)  # Get rid of flash when root window created
    #monitor.center(root)  # Get rid of top-left flash when root window created
    #img.taskbar_icon(root, 64, 'black', 'green', 'red', char='H')
    # Above no effect, taskbar icon is still a question mark with no color
    root.withdraw()
    app = Application(root)  # Treeview of ni.discovered[{}, {}...{}]

    app.mainloop()


if __name__ == "__main__":
    main()

# End of homa.py
