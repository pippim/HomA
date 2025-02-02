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
#       2025-01-08 - Create Bluetooth LED Light Strip support.
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
import random  # Temporary filenames
import string  # Temporary filenames
import base64  # Required for Cryptology
from cryptography.fernet import Fernet  # To encrypt sudo password

try:
    reload(sys)  # June 25, 2023 - Without utf8 sys reload, os.popen() fails on OS
    sys.setdefaultencoding('utf8')  # filenames that contain unicode characters
except NameError:  # name 'reload' is not defined
    pass  # Python 3 already in unicode by default

import trionesControl.trionesControl as tc  # Bluetooth LED Light strips

# 2025-01-09 TODO: direct access to GATT bypassing trionesControl
import pygatt
import pygatt.exceptions

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


class Globals(DeviceCommonSelf):
    """ Globals

        What could be in sql.py too complicated to document due to mserve.py

        - timeouts for adb, REST, resume, rediscover
        - colors for toplevel, taskbar icon, treeview, scrollbars

    """

    def __init__(self):
        """ DeviceCommonSelf(): Variables used by all classes
            Stored in ~/.local/share/hom/config.json
            After adding new dictionary field, remove the config.json file and
            restart HomA.
        """
        DeviceCommonSelf.__init__(self, "Globals().")  # Define self.who

        self.requires = ['ls']

        # Next four lines can be defined in DeviceCommonSelf.__init__()
        self.installed = []
        self.CheckDependencies(self.requires, self.installed)
        v2_print(self.who, "Dependencies:", self.requires)
        v2_print(self.who, "Installed?  :", self.installed)

        # Usage: glo = Globals()
        #        GLO = glo.dictGlobals
        #        GLO['APP_RESTART_TIME'] = time.time()
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
            "REDISCOVER_SECONDS": 60,  # Check for device changes every x seconds
            "RESUME_TEST_SECONDS": 30,  # > x seconds disappeared means system resumed
            "RESUME_DELAY_RESTART": 5,  # Allow x seconds for network to come up

            "LED_LIGHTS_MAC": "",  # Bluetooth LED Light Strip MAC address
            "LED_LIGHTS_STARTUP": True,  # "0" turn off, "1" turn on.
            "LED_LIGHTS_COLOR": None,  # Last colorchooser ((r, g, b), #000000)
            "BLUETOOTH_SCAN_TIME": 10,  # Number of seconds to scan bluetooth devices

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

            "SUDO_PASSWORD": None,  # Sudo password required for laptop backlight
            # 2025-01-04 TODO: get backlight with runCommand()
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

            #print("GLO['LED_LIGHTS_COLOR']:", GLO['LED_LIGHTS_COLOR'])
            # Starts as a tuple json converts to list: [[44, 28, 27], u'#2c1c1b']
            try:
                s = self.dictGlobals['LED_LIGHTS_COLOR']
                self.dictGlobals['LED_LIGHTS_COLOR'] = \
                    ((s[0][0], s[0][1], s[0][2]), s[1])
            except (TypeError, IndexError):  # No color saved
                self.dictGlobals['LED_LIGHTS_COLOR'] = None

            with warnings.catch_warnings():
                # Deprecation Warning:
                # /usr/lib/python2.7/dist-packages/cryptography/x509/__init__.py:32:
                #   PendingDeprecationWarning: CRLExtensionOID has been renamed to
                #                              CRLEntryExtensionOID
                #   from cryptography.x509.oid import (
                warnings.simplefilter("ignore", category=PendingDeprecationWarning)
                f = Fernet(cp.crypto_key)  # Encrypt sudo password when storing

            if self.dictGlobals['SUDO_PASSWORD'] is not None:
                self.dictGlobals['SUDO_PASSWORD'] = \
                    f.decrypt(self.dictGlobals['SUDO_PASSWORD'].encode())
                #v0_print(self.dictGlobals['SUDO_PASSWORD'])

            # 2025-01-27 override REFRESH_MS for breatheColors() testing.
            #GLO['REFRESH_MS'] = 10  # Override 16ms to 10ms

    def saveFile(self):
        """ Save dictConfig to CONFIG_FNAME = "config.json" """
        _who = self.who + "saveFile():"

        f = Fernet(cp.crypto_key)  # Encrypt sudo password when storing
        if GLO['SUDO_PASSWORD'] is not None:
            GLO['SUDO_PASSWORD'] = f.encrypt(GLO['SUDO_PASSWORD'].encode())
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
        FNAME = "filename"
        MAC = "MAC-address"
        WID = 15  # Default Width
        DEC = MIN = MAX = CB = None  # Decimal places, Minimum, Maximum, Callback
        listFields = [
            # name, tab#, ro/rw, input as, stored as, width, decimals, min, max,
            #   edit callback, tooltip text
            ("SONY_PWD", 1, RW, STR, STR, 10, DEC, MIN, MAX, CB,
             "Password for Sony REST API"),
            ("CONFIG_FNAME", 5, RO, STR, STR, WID, DEC, MIN, MAX, CB,
             "Configuration filename"),
            ("DEVICES_FNAME", 5, RO, STR, STR, WID, DEC, MIN, MAX, CB,
             "discovered network devices filename"),
            ("VIEW_ORDER_FNAME", 5, RO, STR, STR, WID, DEC, MIN, MAX, CB,
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
            ("APP_RESTART_TIME", 0, HD, TM, TM, 18, DEC, MIN, MAX, CB,
             "Time HomA was started or resumed.\nUsed for elapsed time printing."),
            ("REFRESH_MS", 5, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "Refresh tooltip fades 60 frames per second"),
            ("REDISCOVER_SECONDS", 5, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "Check devices changes every x seconds"),
            ("RESUME_TEST_SECONDS", 5, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "> x seconds disappeared means system resumed"),
            ("RESUME_DELAY_RESTART", 5, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "Pause x seconds after resuming from suspend"),
            ("LED_LIGHTS_MAC", 4, RW, MAC, STR, 17, DEC, MIN, MAX, CB,
             "Bluetooth Low Energy LED Light Strip address"),
            ("LED_LIGHTS_STARTUP", 4, RW, BOOL, BOOL, 1, DEC, MIN, MAX, CB,
             "LED Lights Turn On at startup? True/False"),
            ("LED_LIGHTS_COLOR", 4, RO, STR, STR, 20, DEC, MIN, MAX, CB,
             'LED Lights last used color.\nFormat: (red, green, blue) #9f9f9f"]'),
            ("BLUETOOTH_SCAN_TIME", 4, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             'Number of seconds to perform bluetooth scan.\n'
             'A longer time may discover more devices.'),
            ("TIMER_SEC", 4, RW, INT, INT, 5, DEC, MIN, MAX, CB,
             "Tools Dropdown Menubar - Countdown Timer default"),
            ("TIMER_ALARM", 4, RW, FNAME, STR, 30, DEC, MIN, MAX, CB,
             ".wav sound file to play when timer ends."),
            ("LOG_EVENTS", 0, HD, BOOL, BOOL, 1, DEC, MIN, MAX, CB,
             "Override runCommand events'\nlogging and --verbose3 printing"),
            ("EVENT_ERROR_COUNT", 0, HD, INT, INT, 9, 0, MIN, MAX, CB,
             "To enable/disable View Dropdown menu 'Discovery errors'"),
            # 2024-12-29 TODO: SENSOR_XXX should be FLOAT not STR?
            ("SENSOR_CHECK", 4, RW, FLOAT, FLOAT, 6, DEC, MIN, MAX, CB,
             "Check `sensors`, CPU/GPU temperature\nand Fan speeds every x seconds"),
            ("SENSOR_LOG", 4, RW, FLOAT, FLOAT, 9, DEC, MIN, MAX, CB,
             "Log `sensors` every x seconds.\nLog more if Fan RPM speed changes"),
            ("FAN_GRANULAR", 4, RW, INT, INT, 5, DEC, MIN, MAX, CB,
             "Skip logging if Fan RPM changes <= FAN_GRANULAR"),
            # Device type global identifier hard-coded in "inst.type_code"
            ("HS1_SP", 3, RO, INT, INT, 2, DEC, MIN, MAX, CB,
             "TP-Link Kasa WiFi Smart Plug HS100,\nHS103 or HS110 using hs100.sh"),  #
            ("KDL_TV", 1, RO, INT, INT, 2, DEC, MIN, MAX, CB,
             "Sony Bravia KDL Android TV using REST API `curl`"),
            ("TCL_TV", 2, RO, INT, INT, 2, DEC, MIN, MAX, CB,
             "TCL Google Android TV using adb after `wakeonlan`"),
            ("BLE_LS", 2, RO, INT, INT, 2, DEC, MIN, MAX, CB,
             "Bluetooth LED Light Strip"),
            ("DESKTOP", 6, RO, INT, INT, 3, DEC, MIN, MAX, CB,
             "Desktop Computer, Tower, NUC, Raspberry Pi, etc."),
            ("LAPTOP_B", 6, RO, INT, INT, 3, DEC, MIN, MAX, CB,
             "Laptop base ('CPU, GPU, Keyboard, Fans, Ports, etc.')"),
            ("LAPTOP_D", 6, RO, INT, INT, 3, DEC, MIN, MAX, CB,
             'Laptop display ("backlight can be turned\non/off separately from laptop base")'),
            # Once entered, sudo password stored encrypted on disk until "forget" is run.
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
        self.sunlight_percent = 0  # Percentage of sunlight, 0 = nighttime.
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

        '''
        Convert string to bytes
            Python2:
            
            s = "ABCD"
            b = bytearray()
            b.extend(s)
            
            Python3:
            
            s = "ABCD"
            b = bytearray()
            b.extend(map(ord, s))
        '''
        self.crypto_key = self.generateCryptoKey()
        v3_print(_who, "BEFORE self.crypto_key:", self.crypto_key, "\n  length:",
                 len(self.crypto_key), type(self.crypto_key))
        b = bytearray()
        b.extend(self.crypto_key)
        self.crypto_key = b
        v3_print(_who, " AFTER self.crypto_key:", self.crypto_key, "\n  length:",
                 len(self.crypto_key), type(self.crypto_key))
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

        self.powerStatus = "ON"  # Can be "ON", "OFF" or "?"
        return self.powerStatus  # Really it is "AWAKE"

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

        self.powerStatus = "OFF"  # Can be "ON", "OFF" or "?"
        return self.powerStatus  # Really it is "SLEEP"

    def getPower(self, forgive=False):
        """ The computer is always "ON" """

        _who = self.who + "getPower():"
        v2_print(_who, "Test if device is powered on:", self.ip)

        if forgive:
            pass

        self.powerStatus = "ON"
        return self.powerStatus

    def generateCryptoKey(self, key=None):
        """ 32 byte key can be passed or generated based on device. """
        _who = self.who + "generateCryptoKey():"
        if key is None:
            if self.ether_mac is not None:
                key = self.ether_mac + ":" + self.ether_mac
            elif self.wifi_mac is not None:
                key = self.wifi_mac + ":" + self.wifi_mac

        key = key + " "*32
        v3_print(_who, "key[32]", key[:32])
        # Computer().generateCryptoKey(): key[32] 28:f1:0e:2a:1a:ed:28:f1:0e:2a:1a:
        # Computer().__init()__: self.crypto_key: Mjg6ZjE6MGU6MmE6MWE6ZWQ6Mjg6ZjE6MGU6MmE6MWE6

        # https://www.microfocus.com/documentation/visual-cobol/vc80/CSWin/BKCJCJDEFNS009.html
        # The resulting base64-encoded data is approximately 33% longer than the
        # original data, and typically appears as seemingly random characters.
        # Base64 encoding is specified in full in RFC 1421 and RFC 2045.

        return base64.urlsafe_b64encode(key[:32])

    def NightLightStatus(self, forgive=False):
        """ Return True if "On" or "Off"
            gsettings get org.gnome.settings-daemon.plugins.color
                night-light-enabled

            percent = cat /usr/local/bin/.eyesome-percent | cut -F1
            if percent < 100 enabled = True

        """

        _who = self.who + "NightLightStatus():"
        v2_print(_who, "Test if GNOME Night Light is active:", self.ip)

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
                    self.nightlight_active = True
                    return "ON"
                elif night_light == "False":
                    self.nightlight_active = False
                    return "OFF"
        else:
            pass  # if no `gsettings` then no GNOME Nightlight

        if self.CheckInstalled('cut'):
            # 2024-12-16 TODO: Read file directly. Use EYESOME_PERCENT_FNAME
            command_line_str = 'cut -d" " -f1 < /usr/local/bin/.eyesome-percent'
            v3_print("\n" + _who, "command_line_str:", command_line_str, "\n")
            f = os.popen(command_line_str)

            text = f.read().splitlines()  # NOTE: text is a list with 1 entry
            returncode = f.close()  # https://stackoverflow.com/a/70693068/6929343
            v3_print(_who, "text:", text, "returncode:", returncode)

            if returncode is None and text is not None and len(text) == 1:
                self.eyesome_active = True
                try:
                    percent = int(text[0])
                    v3_print(_who, "eyesome percent:", percent)
                    self.sunlight_percent = percent
                    if percent == 100:
                        return "OFF"  # 100 % sunlight
                    else:
                        return "ON"
                except ValueError:
                    v3_print(_who, "eyesome percent VALUE ERROR:", text[0])

            else:
                self.eyesome_active = False

        return "ON"  # Default to always turn bias lights on


class NetworkInfo(DeviceCommonSelf):
    """ Network Information from arp and getent (/etc/hosts)

        If Android devices aren't automatically discovered:

            adb kill-server && adb start-server
            devices -l
            # if android device missing:
                adb connect <IP address>
            # Run File Dropdown Menu option "Rediscover now"


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

        # Add fake arp dictionary for Bluetooth LED Light Strip
        v2_print("len(GLO['LED_LIGHTS_MAC']):", len(GLO['LED_LIGHTS_MAC']))  # 0 ???
        if len(GLO['LED_LIGHTS_MAC']) == 17:
            # When changing below, remove devices.json file to rebuild it.
            fake_dict = {"mac": GLO['LED_LIGHTS_MAC'],
                         "ip": "irrelevant",
                         "name": "Bluetooth LED",
                         "alias": "Bluetooth LED Light Strip"}
            self.arp_dicts.append(fake_dict)
            v3_print("fake_dict:", fake_dict)

        v2_print(_who, "arp_dicts:", self.arp_dicts)  # 2024-11-09 now has Computer()
        v2_print(_who, "instances:", self.instances)  # Empty list for now noy in
        v2_print(_who, "view_order:", self.view_order)  # Empty list for now
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
            ["adb", "kill-server", "&&", "adb", "start-server", "&&", 
             "adb", "devices", "-l"]
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

        ''' run command with os.popen() because sp.Popen() fails on ">" '''
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
                v0_print(_who, "text:")
                v0_print(" ", text)  # string, list
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
                v2_print(_who, "Found existing ni.arp_dict:", arp_dict['name'])
                return arp_dict

        v2_print(_who, "mac address unknown: '" + mac + "'")

        return {}  # TODO: Format dictionary with 'mac': and error

    def inst_for_mac(self, mac, not_found_error=True):
        """ Get device instance for mac address. Instances are dynamically
            created at run time and cannot be saved in arp_dict.
            :param mac: MAC address
            :param not_found_error: When True print debug error message
            :returns: existing class instance for controlling device
        """
        _who = self.who + "inst_for_mac():"

        for instance in self.instances:
            if instance['mac'] == mac:
                return instance

        if not_found_error:
            v2_print(_who, "mac address unknown: '" + mac + "'")

        return {}  # TODO: Format dictionary with 'mac': and error

    def test_for_instance(self, arp):
        """ Test if arp dictionary is a known device type and create
            an instance for the device.
        :param arp: dictionary {mac: ip: name: alias: type_code:}
        :returns: {mac: "xx:xx...", instance: <object>}
        """
        _who = self.who + "test_for_instance():"
        # Next two sanity checks copied from Application().Rediscover()
        mac = arp['mac']
        # TCL.LAN (192.168.0.17) at <incomplete> on enp59s0
        if mac == '<incomplete>':
            v2_print(_who, "Invalid MAC:", mac)
            return {}

        ip = arp['ip']
        # ? (20.20.20.1) at a8:4e:3f:82:98:b2 [ether] on enp59s0
        if ip == '?':
            v2_print(_who, "Invalid IP:", ip)
            return {}

        instance = {}

        def test_one(cname):
            """ Test if hs100, SonyTV, GoogleTV, etc. """
            inst = cname(arp['mac'], arp['ip'], arp['name'], arp['alias'])
            if not inst.isDevice(forgive=True):
                return False

            v1_print(arp['mac'], " # ", arp['ip'].ljust(15),
                     "##  is a " + inst.type + " code =", inst.type_code)

            ''' 2025-01-13 Caller must do this:
            arp['type_code'] = inst.type_code  # Assign 10, 20, 30...
            instances.append({"mac": arp['mac'], "instance": inst})
            view_order.append(arp['mac'])
            if update:
                ni.arp_dicts[i] = arp  # Update arp list
            '''
            instance["mac"] = arp['mac']
            instance["instance"] = inst

            return True  # Grab next type

        # Test smart plug first because they seem most "fragile"
        if test_one(SmartPlugHS100):
            return instance

        if test_one(Computer):
            return instance

        if test_one(LaptopDisplay):
            return instance

        if test_one(SonyBraviaKdlTV):
            return instance

        # Special testing. android.isDevice was failing without extra time.
        #   TODO: ni.adb_reset() too long or android.Connect() is timing out.
        if test_one(TclGoogleAndroidTV):
            v0_print(_who, "Android TV found:", arp['ip'])
            v0_print("instance:", instance, "\n")
            return instance
        elif arp['ip'] == "192.168.0.17":  # "devices", "-l"
            v0_print(_who, "Android TV failed!:", arp['ip'])

        if test_one(BluetoothLedLightStrip):
            return instance

        return {}


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
        return self.powerStatus

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
        return self.powerStatus

    def getPower(self, forgive=False):
        """ Return "ON", "OFF" or "?" """

        _who = self.who + "getPower():"
        v2_print(_who, "Test if device is powered on:", self.ip)
        if forgive:
            pass  # Dummy argument for uniform instance parameter list

        power = '/sys/class/backlight/' + GLO['BACKLIGHT_NAME'] + '/bl_power'
        command_line_list = ['cat', power]
        event = self.runCommand(command_line_list, _who)

        back = event['output']
        if back == GLO['BACKLIGHT_ON']:
            self.powerStatus = "ON"  # Can be "ON", "OFF" or "?"
        elif back == GLO['BACKLIGHT_OFF']:
            self.powerStatus = "OFF"  # Can be "ON", "OFF" or "?"
        else:
            v0_print(_who, "Invalid " + power + " value:", back)
            self.powerStatus = "?"  # Can be "ON", "OFF" or "?"

        return self.powerStatus

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
        self.powerStatus = status


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

        Reply = self.getPower(forgive=forgive)  # ON, OFF or N/A
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

        Reply = self.getPower(forgive=forgive)  # Get current power status

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

        Reply = self.getPower(forgive=forgive)

        if Reply == "?":
            v2_print(_who, self.ip, "- Not a Smart Plug!")
            return "?"

        if Reply == "OFF":
            v2_print(_who, self.ip, "- is already turned off. Skipping")
            return "OFF"

        self.SetPower("OFF")
        v2_print(_who, self.ip, "- Smart Plug turned 'OFF'")
        return "OFF"

    def getPower(self, forgive=False):
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

        _who = self.who + "getPower():"
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
            self.powerStatus = parts[1]  # Can be "ON", "OFF" or "?"
            return self.powerStatus

        v2_print(_who, self.ip, "- Not a Smart Plug! (or powered off)")
        self.powerStatus = "?"  # Can be "ON", "OFF" or "?"
        return self.powerStatus

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

        self.powerStatus = status  # Can be "ON", "OFF" or "?"


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

    def getPower(self, forgive=False):
        """ Return "ON", "OFF" or "?" if error.
            Called by TestSonyOn, TestSonyOff and TestIfSony methods.

https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/getPowerStatus/index.html

        """

        _who = self.who + "getPower():"
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
            self.powerStatus = "ON"  # Can be "ON", "OFF" or "?"
        elif u"standby" == reply:
            self.powerStatus = "OFF"  # Can be "ON", "OFF" or "?"
        else:
            v3_print(_who, "Something weird: ?")  # Router
            self.powerStatus = "?"  # Can be "ON", "OFF" or "?"

        # 2024-12-04 - Some tests
        #self.getSoundSettings()
        #self.getSpeakerSettings()
        #self.getVolume()

        return self.powerStatus

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

        self.powerStatus = ret  # Can be "ON", "OFF" or "?"
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

        self.powerStatus = ret  # Can be "ON", "OFF" or "?"
        return self.powerStatus

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

        Reply = self.getPower(forgive=forgive)
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

$ adb devices -l
List of devices attached
192.168.0.17:5555      device product:G03_4K_US_NF model:Smart_TV device:BeyondTV4

        Reference:
            https://developer.android.com/reference/android/view/KeyEvent

        Methods:

            AdbReset() - adb kill-server && adb start-server
            getPower() - timeout 2.0 adb shell dumpsys input_method | grep -i screen on
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

        DEBUGGING:

        $ time adb connect 192.168.0.17

* daemon not running. starting it now on port 5037 *
* daemon started successfully *
connected to 192.168.0.17:5555

real	0m3.010s
user	0m0.003s
sys	    0m0.000s

        Next, run Rediscover Now from Dropdown File menu.

        Command line will show:

Application().Rediscover(): FOUND NEW INSTANCE or REDISCOVERED LOST INSTANCE:
{'instance': <__main__.TclGoogleAndroidTV instance at 0x7f59af94d3f8>,
'mac': u'c0:79:82:41:2f:1f'}

        Now restart HomA and missing TV will reappear.

        """

        _who = self.who + "Connect():"
        v2_print(_who, "Attempt to connect to:", self.ip)

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

            # 2025-01-13 Added but should not be needed except isDevice timeout is
            #   now too short.
            command_line_list = ["adb", "connect", self.ip]
            _event = self.runCommand(command_line_list, _who, forgive=forgive)

            cnt += 1
            if cnt > 60:
                v0_print(_who, "Timeout after", cnt, "attempts")
                return False

        return True

    def getPower(self, forgive=False):
        """ Return "ON", "OFF" or "?".
            Calls 'timeout 2.0 adb shell dumpsys input_method | grep -i screenon'
                which replies with 'true' or 'false'.

        """

        _who = self.who + "getPower():"
        v2_print("\n" + _who, "Get Power Status for:", self.ip)
        self.Connect()  # 2024-12-02 - constant reconnection seems to be required

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
                    self.powerStatus = "?"  # Can be "ON", "OFF" or "?"
                    return self.powerStatus
            self.powerStatus = "? " + str(event['returncode'])
            return self.powerStatus

        Reply = event['output']
        # Reply = "connected to 192.168.0.17:5555"
        # Reply = "already connected to 192.168.0.17:5555"
        # Reply = "unable to connect to 192.168.0.17:5555"
        # Reply = "error: device offline"

        if "true" in Reply:
            self.powerStatus = "ON"  # Can be "ON", "OFF" or "?"
        elif "false" in Reply:
            self.powerStatus = "OFF"  # Can be "ON", "OFF" or "?"
        else:
            self.powerStatus = "?"  # Can be "ON", "OFF" or "?"

        #v0_print(_who, "SPECIAL self.mac", self.mac, "self.name:", self.name)
        #  SPECIAL self.mac c0:79:82:41:2f:1f self.name: TCL.LAN
        #  above is working for this inst. class but not for LED Lights inst. class

        return self.powerStatus

    def TurnOn(self, forgive=False):
        """ Turn On TCL / Google Android TV.
            Send KEYCODE_WAKEUP 5 times until screenOn = true
        """

        _who = self.who + "TurnOn():"
        v2_print("\n" + _who, "Send KEYCODE_WAKEUP to:", self.ip)

        # Connect() will try 60 times with wakeonlan and isDevice check.
        if not self.Connect(forgive=forgive):  # TODO else: error message
            return self.getPower()

        cnt = 1
        self.powerStatus = "?"

        while not self.powerStatus == "ON":

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
                return "?"  # self.powerStatus already has this value

            self.getPower()
            if self.powerStatus == "ON" or cnt >= 5:
                return self.powerStatus
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

        self.powerStatus = "OFF"  # Can be "ON", "OFF" or "?"
        return self.powerStatus

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

        # NEED self.runCommand to log events !!!!
        # event = self.runCommand(command_line_list, _who, forgive=forgive)


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


class BluetoothLedLightStrip(DeviceCommonSelf):
    # noinspection SpellCheckingInspection
    """
        If Bluetooth isn't connecting, check gatttool percentage. If 100% of CPU
        core then restart homa.py.

        A recent version of Bluez is NOT required for Bluetooth LED light strips.

        Bluez: https://www.makeuseof.com/install-bluez-latest-version-on-ubuntu/

        Depends ON build-essential OR build-essentials PLUS:
        libreadline-dev libical-dev libdbus-1-dev libudev-dev libglib2.0-dev python3-docutils

        trionesControl: https://github.com/Aritzherrero4/python-trionesControl

        pygatt (2019 version 4.0.5): https://pypi.org/project/pygatt/4.0.5/#history
            requires bluez version 5.18 +
            requires Bluegiga’s BGAPI, compatible with USB adapters like the BLED112.
            requires python-pexpect or python3-pexpect
            requires python-serial or python3-serial

        Requires MAC address for Bluetooth LED Light strips or light bulb. To
        find your MAC address turn on Android Phone Debugging Options. Turn on
        Bluetooth snoop. Turn your lights on / off with Android. Create Bug Report
        and scour the report for your MAC address.

        Happy Lighting Bluetooth LED Light Strip name shows as "QHM-T095" in Ubuntu.
    """

    def __init__(self, mac=None, ip=None, name=None, alias=None):
        """ DeviceCommonSelf(): Variables used by all classes """
        DeviceCommonSelf.__init__(self, "BluetoothLedLightStrip().")  # Define self.who
        _who = self.who + "__init()__:"

        # 192.168.0.10    Alien AW 17R3 WiFi 9c:b6:d0:10:37:f7
        # 192.168.0.12    Alien AW 17R3 Ethernet 28:f1:0e:2a:1a:ed
        self.mac = mac      # 36:46:3E:F3:09:5E
        self.ip = ip        # None
        self.name = name    # LED Light Strip
        self.alias = alias  # Happy Lighting

        self.type = "BluetoothLedLightStrip"
        self.type_code = GLO['BLE_LS']
        self.requires = ["rfkill", "systemctl", "hcitool", "hciconfig",
                         "grep", "sort", "uniq"]
        self.installed = []
        self.CheckDependencies(self.requires, self.installed)
        v2_print(self.who, "Dependencies:", self.requires)
        v2_print(self.who, "Installed?  :", self.installed)

        self.BluetoothStatus = "?"  # "ON" or "OFF" set by getBluetoothStatus
        self.hci_device = "hci0"  # "hci0" is the default used by trionesControl.py
        # but the real name is obtained using `hcitool dev` in getBluetoothStatus()
        self.hci_mac = ""  # Bluetooth chipset MAC address
        self.device = None  # LED Light Strip device instance obtained with MAC address
        self.app = None  # Parent app for calling GetPassword() and other methods.

        self.temp_fname = None  # Temporary filename for all devices report
        self.fake_top = None  # For color chooser placement geometry

        # Parameter & Statistics dictionaries for breathing colors fine tuning
        self.already_breathing_colors = False  # Is breathing colors running?
        self.connect_errors = 0  # Count sequential times auto-reconnect failed.
        # When changing here, change in breatheColors() as well
        self.parm = {}  # breatheColors() parameters
        self.stat = {}  # breatheColors() statistics
        self.FAST_MS = 5  # Global for breatheColors() and monitorBreatheColors()
        self.MAX_FAIL = 18  # Allow 18 connection failures before giving up
        self.red = self.green = self.blue = 0  # Current breathing colors

    def startDevice(self):
        """ Called during startup and resume.
            Caller see GLO['LED_LIGHTS_MAC'] is not None and self.device is None.
        """
        _who = self.who + "startDevice():"

        if self.powerStatus != "?":
            v1_print(_who, "Power status is already:", self.powerStatus)
            v1_print("nothing to do for:", self.mac, self.type_code, "-", self.type)
            return

        self.powerStatus = "?"
        self.getBluetoothStatus()
        if self.BluetoothStatus != "ON":
            v1_print("_who", "Bluetooth is turned off. Reset Bluetooth.")
            return

        # BLE LED Light Strips requires connection
        v2_print(_who, self.name, self.mac)
        self.Connect()
        #time.sleep(1.0)  # self.Connect doesn't wait for reply from lights

        if self.device is not None:
            v2_print(_who, self.mac, "successfully connected.")
            v2_print(self.device)
            if GLO['LED_LIGHTS_STARTUP'] is not False:
                v2_print(_who, "Turning on LED Light.")
                self.TurnOn()
            else:
                v2_print(_who, "Turning off LED Light.")
                self.TurnOff()
        else:
            v1_print(_who, self.mac, "failed to connect.")

        if self.app is not None:
            v2_print(_who, "Reset self.app.last_refresh_time")
            self.app.last_refresh_time = time.time()  # Recover lost 5 seconds

    def getBluetoothStatus(self):
        """ Connect to Bluetooth Low Energy with GATT.
            Test if adapter is turned on with:
                $ hcitool dev
                Devices:
                    hci0	9C:B6:D0:10:37:F8

            If "hci0" lines doesn't follow "Devices" line then Bluetooth turned off.

        """
        _who = self.who + "getBluetoothStatus():"
        self.hci_device = "hci0"  # Default if turned off and unknown
        self.hci_mac = ""
        self.BluetoothStatus = "?"
        if not self.CheckInstalled("hcitool"):
            # 2025-01-10 TODO: Message `hcitool` required
            return self.BluetoothStatus

        command_line_list = ["hcitool", "dev"]
        event = self.runCommand(command_line_list, _who)  # def runCommand

        if event['returncode'] == 0:
            lines = event['output'].splitlines()
            v3_print(_who, "lines:", lines)
            if len(lines) != 2:
                v0_print(_who, "len(lines):", len(lines))
                self.BluetoothStatus = "OFF"
            else:
                parts = lines[1].split("\t")
                # parts = ["", "xx:xx:xx:xx:xx:xx", "Device_Name"]
                if len(parts) == 3:
                    self.BluetoothStatus = "ON"
                    self.hci_device = parts[1]
                    self.hci_mac = parts[2]
                    v2_print(_who, "self.hci_device:", self.hci_device)
                    v2_print(_who, "self.hci_mac   :", self.hci_mac)
                else:
                    # Invalid devices line
                    v0_print(_who, "len(parts):", len(parts))
                    v0_print(_who, "parts:", parts)
                    self.BluetoothStatus = "?"

        v2_print(_who, "self.BluetoothStatus:", self.BluetoothStatus)
        return self.BluetoothStatus

    def resetBluetooth(self, reconnect=True):
        """ Turn Bluetooth on. Called from Right-Click menu, Reset Bluetooth
            Called from Dropdown View Menu - Bluetooth devices, getBluetoothDevices()
            Visible on Right click treeview row - reset Bluetooth if power "?"

            When called from Right click treeview row, auto reconnect.

            Lifted from gatttool.py connect()

            def reset(self):
                subprocess.Popen(["sudo", "systemctl", "restart", "bluetooth"]).wait()
                subprocess.Popen([
                    "sudo", "hciconfig", self._hci_device, "reset"]).wait()

        """
        _who = self.who + "resetBluetooth():"

        if self.app is None:
            v0_print(_who, "Cannot reset Bluetooth until GUI is running.")
            return "?"

        # Dependencies installed?
        if not self.CheckInstalled("hciconfig"):
            # 2025-01-10 TODO: Message `hcitool` required
            msg = "The program `hciconfig` is required to reset Bluetooth.\n\n"
            msg += "sudo apt-get install hciconfig bluez bluez-tools rfkill\n\n"
            self.app.ShowInfo("Missing program.", msg, icon="error")
            return "OFF"  # Prevents other methods running until turned "ON"

        msg = "Sudo password required to reset bluetooth."
        if not self.elevateSudo(msg=msg):
            return "?"  # Cancel button (256) or escape or 'X' on window decoration (64512)

        # Remove any bluetooth soft blocking
        command_line_list = ["rfkill", "unblock", "bluetooth"]
        _event = self.runCommand(command_line_list, _who, forgive=False)
        # Don't bother to see if rfkill was successful

        # restart bluetooth, all devices will disconnect!
        command_line_list = ["sudo", "systemctl", "restart", "bluetooth"]
        event = self.runCommand(command_line_list, _who, forgive=False)

        if event['returncode'] == 0:
            # Bluetooth successfully restarted. Now reset self.hci_device ('hci0')
            msg = "'systemctl restart bluetooth' success."
            #if reconnect:
            msg += "  Attempting reset." if reconnect else msg
            v1_print(_who, "\n  " + msg)
            command_line_list = ["sudo", "hciconfig", self.hci_device, "reset"]
            _event = self.runCommand(command_line_list, _who, forgive=False)
            status = "ON"
        else:
            v1_print(_who, "\n  " +
                     "'systemctl restart bluetooth' FAILED !")
            status = "OFF"

        if reconnect:
            v0_print(_who, "Bluetooth status:", status, "attempting self.Connect()")
            self.Connect(sudo_reset=True)
            v0_print(_who, self.name, "self.device:", self.device)

        self.BluetoothStatus = status
        return self.BluetoothStatus

    def elevateSudo(self, msg=None):
        """ If already sudo, validate timestamp hasn't expired.
            Otherwise get sudo password and validate.
        """
        _who = self.who + "elevateSudo():"

        # Sudo password required for resetting bluetooth
        if GLO['SUDO_PASSWORD'] is not None:
            # If sudo password timestamp has expired, set password to None
            GLO['SUDO_PASSWORD'] = hc.ValidateSudoPassword(GLO['SUDO_PASSWORD'])

        if GLO['SUDO_PASSWORD'] is None:
            GLO['SUDO_PASSWORD'] = self.app.GetPassword(msg=msg)
            self.app.EnableMenu()

        return GLO['SUDO_PASSWORD']

    def getBluetoothDevices(self, show_unknown=False, reconnect=True):
        """ Get list of all bluetooth devices (including unknown)

        NOTE: Called with inst.getBluetoothDevices()

        $ sudo timeout 10 hcitool -i hci0 lescan > devices.txt &

        $ sort devices.txt | uniq -c | grep -v unknown

        """
        _who = self.who + "getBluetoothDevices():"

        if self.app is None:
            print(_who, "Cannot start until GUI is running.")
            return ""

        if not self.elevateSudo():
            return ""  # Cancel button (256) or escape or 'X' on window decoration (64512)

        self.resetBluetooth(reconnect=reconnect)
        # Hammer connections in order to prevent:
        # Set scan parameters failed: Input/output error

        TMP_FFPROBE = g.TEMP_DIR + "homa_bluetooth_devices"  # _a3sd24 appended

        ''' Make TMP names unique for multiple FileControls racing at once '''
        letters = string.ascii_lowercase + string.digits
        temp_suffix = (''.join(random.choice(letters) for _i in range(6)))
        self.temp_fname = TMP_FFPROBE + "_" + temp_suffix

        self.cmdStart = time.time()
        self.cmdCommand = ["sudo", "timeout", str(GLO['BLUETOOTH_SCAN_TIME']),
                           "hcitool", "-i", self.hci_device, "lescan", ">",
                           self.temp_fname, "&"]
        self.cmdString = ' '.join(self.cmdCommand)
        v2_print(self.cmdString)

        ''' run command with os.popen() because sp.Popen() fails on ">" '''
        # 2025-01-15 TODO: Log to cmdEvents
        os.popen(self.cmdString)

        self.app.ResumeWait(timer=GLO['BLUETOOTH_SCAN_TIME'], alarm=False,
                            title="Scanning Bluetooth Devices", abort=False)
        #self.app.after(500)  # Slush fund sleep extra 1/2 second
        # 2025-01-15 NOTE: It takes another 3 to 7 seconds for window to open ???
        #   Each time running without restart, gatttool is using 100% of a core
        #   Turning off existing HomA connection to LED lights necessary to appear.
        time.sleep(.5)  # self.app.after() appears to take too long

        lines = ext.read_into_string(self.temp_fname)
        lines = "" if lines is None else lines

        ''' log event and v3_print debug lines '''
        line_count = len(lines.splitlines())
        self.cmdOutput = "Line Count: " + str(line_count)
        self.cmdError = "N/A"
        self.cmdReturncode = 0
        self.cmdDuration = time.time() - self.cmdStart
        self.cmdCaller = _who
        who = self.cmdCaller + " logEvent():"
        self.logEvent(who, forgive=False, log=True)

        # STEP 2: Sort and uniq. Optional remove "unknown"
        self.cmdCommand = ["sort", self.temp_fname, "|", "uniq", "-c"]
        if show_unknown is False:
            self.cmdCommand.extend(["|", "grep", "-v", "unknown"])
        self.cmdString = ' '.join(self.cmdCommand)
        v2_print(self.cmdString)

        ''' run command with os.popen() because sp.Popen() fails on "|" '''
        f = os.popen(self.cmdString)

        text = f.read().strip()
        returncode = f.close()  # https://stackoverflow.com/a/70693068/6929343
        returncode = 0 if returncode is None else returncode

        ''' log event and v3_print debug lines '''
        self.cmdOutput = "" if returncode != 0 else text
        self.cmdError = "" if returncode == 0 else text
        self.cmdReturncode = returncode
        self.cmdDuration = time.time() - self.cmdStart
        self.cmdCaller = _who
        who = self.cmdCaller + " logEvent():"
        self.logEvent(who, forgive=False, log=True)

        if returncode:
            v0_print(_who, "text:")
            v0_print(" ", text)  # string, list
            v0_print(_who, "returncode:", returncode)

        device_list = []
        for line in text.splitlines():
            parts = line.split()
            # "1", "xx:xx:xx:xx:xx:xx" "QHM-T095"
            #       12345678901234567
            if len(parts) < 3:
                continue
            if len(parts[1]) != 17:
                continue
            count = parts[0]
            address = parts[1]
            name = ' '.join(parts[2:])  # Device name was split on spaces

            v2_print("address:", address, "name:", name, "count:", count)
            device_list.append((address, name, count))

        self.resetBluetooth(reconnect=False)
        # Hammer connections in order to prevent:
        # Set scan parameters failed: Input/output error

        ext.remove_existing(self.temp_fname)  # Clean up temporary output file

        return device_list

    def setColor(self):
        """ Set color.
            When color picker used, brightness goes to 100% unless values low. E.G.:
                #090000 - Red very low brightness

            Alternatives to trionesControl.py to try:
                https://github.com/LedFx/LedFx (LED controlled by music)
        """
        _who = self.who + "setColor():"
        if self.device is None:
            self.showMessage()  # self.powerStatus = "?"
            return self.powerStatus

        x, y = hc.GetMouseLocation()
        self.fake_top = tk.Toplevel(self.app)  # For color chooser placement geometry
        self.fake_top.geometry('1x1+%s+%s' % (x, y))
        self.fake_top.wm_attributes('-type', 'splash')  # No window decorations

        #self.fake_top.withdraw()  # 2025-01-12 Cannot withdraw as in example:
        # https://stackoverflow.com/a/78437258/6929343
        # So no window decorations and size of 1x1 is good compromise

        # variable to store hexadecimal code of color = ((r, g, b), #xxxxxx)
        #print("GLO['LED_LIGHTS_COLOR']:", GLO['LED_LIGHTS_COLOR'])
        # Starts as a tuple json converts to list: [[44, 28, 27], u'#2c1c1b']
        default = 'red' if GLO['LED_LIGHTS_COLOR'] is None else GLO['LED_LIGHTS_COLOR'][1]

        new = colorchooser.askcolor(
            default, parent=self.fake_top, title="Choose color")
        self.fake_top.destroy()
        try:
            # noinspection PyTupleAssignmentBalance
            red, green, blue = new[0]
        except TypeError:
            return "ON"  # Cancel button
        GLO['LED_LIGHTS_COLOR'] = new
        v2_print(_who, "GLO['LED_LIGHTS_COLOR']:", GLO['LED_LIGHTS_COLOR'])
        self.already_breathing_colors = False  # Turn it off, just in case on
        try:
            tc.setRGB(red, green, blue, self.device, wait_for_response=False)
            # wait_for_response takes 10 seconds when device not connected
            return "ON"
        except (pygatt.exceptions.NotConnectedError, AttributeError) as err:
            self.showMessage(err)  # self.device = None & self.powerStatus = "?"
            return self.powerStatus

    def setNight(self):
        """ Set to lowest brightness.
            When color picker used, brightness goes to 100%. Cannot control brightness.
            setNight() method sets brightness to 10 (minimum) but cannot set color. Color
            defaults to "White" which is really "light green" on Happy Lighting LEDs.
        """
        _who = self.who + "setNight():"
        self.already_breathing_colors = False  # Turn it off, just in case on
        if self.device is None:
            self.showMessage()  # self.device = None & self.powerStatus = "?"
            return self.powerStatus

        try:
            # Value of 1 turns off the light strip, 10 is lowest value tested
            tc.setWhite(10, self.device, wait_for_response=True)
            # 2025-01-18 New error. Taking 10 seconds with invalid self.device
            #   leftover from view Bluetooth Devices. No error.
            return "ON"
        except (pygatt.exceptions.NotConnectedError, AttributeError,
                pygatt.exceptions.NotificationTimeout) as err:
            self.showMessage(err)  # self.device = None & self.powerStatus = "?"


        self.device = None  # Force connect on next attempt
        self.powerStatus = "?"
        # self.app.EnableMenu()  # 'NoneType' object has no attribute 'EnableMenu'
        return self.powerStatus

    def breatheColors(self, low=4, high=30, span=6.0, step=0.275, bots=1.5, tops=0.5):
        """ Breathe Colors: R, R&G, G, G&B, B, B&R

        :param low: Low value (darkest) E.G. 9 (Lowest brightness before lights turn off)
        :param high: High value (brightest) E.G. 180 (About 75% brightness)
        :param span: Float seconds for one way transition E.G. 3.0 (3 second breath)
        :param step: Float seconds to hold each step E.G. 0.33 (would be 90 steps)
        :param bots: Float seconds to hold bottom step E.G. 1.0 (hold bottom 1 second)
        :param tops: Float seconds to hold top step E.G. 3.0 (hold top 3 seconds)
        """
        _who = self.who + "breatheColors():"
        if self.already_breathing_colors:  # Should not happen but check anyway
            v0_print("\n" + ext.ch(), _who, "Already running breathing colors.")
            return
        if self.device is None:
            self.showMessage()  # Bluetooth device not connected to computer
            return self.powerStatus

        # Parameters, Statistics and Color controls
        self.parm = {"low": low, "high": high, "span": span, "step": step,
                     "bots": bots, "tops": tops}  # breatheColors() parameters
        self.stat = {
            "gatt_ms": 0, "gatt_cnt": 0, "gatt_low": 0, "gatt_high": 0, 
            "sleep_ms": 0, "sleep_cnt": 0, "sleep_low": 0, "sleep_high": 0, 
            "fast_ms": 0, "fast_cnt": 0, "norm_ms": 0, "norm_cnt": 0, 
            "fail_ms": 0, "fail_cnt": 0
        }
        colors = (  # Cycle Red, Green, Blue: R, R+G, G, G+B, B, B+R
            (True, False, False), (True, True, False), (False, True, False),
            (False, True, True), (False, False, True), (True, False, True)
        )
        color_ndx = 0
        color_max = len(colors) - 1
        turning_up = True  # False = turning down
        step_count = int(float(span) / float(step))
        step_amount = float(high - low) / float(step_count)
        step_ms = int(float(step) * 1000.0)  # E.G. 0.333 = 333ms = 3 times / second
        bots = int(bots * 1000.0)  # Milliseconds to sleep at Dimmest (bottom)
        tops = int(tops * 1000.0)  # Milliseconds to sleep at Brightest (top)
        fast_sleep = float(self.FAST_MS) / 1000.0  # When not enough time for refresh

        self.already_breathing_colors = True
        self.app.EnableMenu()  # Allow View dropdown menu option "Breathing stats".
        v1_print("\n" + ext.ch(), _who, "Breathing colors - Starting up.")

        def sendCommand():
            """ Set colors: red, green and blue """
            if not self.app.isActive or not self.already_breathing_colors:
                return False
            try:
                tc.setRGB(self.red, self.green, self.blue,
                          self.device, wait_for_response=True)
                # wait_for_response takes 10 seconds when device not connected
                # When not waiting GATT cmd used which results in 100% CPU core
                self.powerStatus = "ON"  # Reset "?" for previous failures
                self.connect_errors = 0
                return self.app.isActive and self.powerStatus == "ON"
            except (pygatt.exceptions.NotConnectedError, AttributeError,
                    pygatt.exceptions.NotificationTimeout) as err:
                if self.connect_errors < self.MAX_FAIL:
                    # Try to connect 5 times. Error after 6th time never displayed
                    self.Connect(retry=self.MAX_FAIL + 1)  # Increments self.connect_errors on failure
                    # APP_RESTART_TIME  TODO: Make global method in self.app.delta_str
                    delta = round(time.time() - GLO['APP_RESTART_TIME'], 2)
                    delta_str = "{0:>8.2f}".format(delta)  # "99999.99" format
                    v0_print(delta_str, "|", _who, "Attempted reconnect:",
                             self.connect_errors + 1, "time(s).")
                else:
                    # Attempted to connect 3 times. Error that Connect() never gave
                    self.showMessage(err, count=self.connect_errors)

                return False

        def setColor():
            """ Calculate color and call sendCommand to Bluetooth """
            tr, tg, tb = colors[color_ndx]  # Turn on red, green, blue?
            num_colors = sum(colors[color_ndx])  # How many colors are used?
            if turning_up is True:
                if step_ndx == 0:
                    brightness = low
                elif step_ndx == step_count - 1:  # Last index in range?
                    brightness = high
                else:
                    brightness = low + int(step_ndx * step_amount)
            else:
                if step_ndx == 0:
                    brightness = high
                elif step_ndx == step_count - 1:  # Last index in range?
                    brightness = low
                else:
                    brightness = high - int(step_ndx * step_amount)

            brightness = low if brightness < low else brightness
            brightness = high if brightness > high else brightness

            if cp.sunlight_percent > 0:  # Additional brightness for sunlight % > 0
                brightness += int((float(brightness) * cp.sunlight_percent) / 100.0)

            # When two colors, each color gets half brightness
            half_bright = int(brightness / num_colors)  # 1 or 2 colors

            # Integer rounding can make half_bright 1 less than true half
            v3_print(_who, "1st half_bright:", half_bright)
            self.red = half_bright if tr else 0
            half_bright = brightness - half_bright if self.red > 0 else half_bright
            self.green = half_bright if tg else 0
            half_bright = brightness - half_bright if self.green > 0 else half_bright
            self.blue = half_bright if tb else 0
            v3_print(_who, "2nd half_bright:", half_bright)
            return sendCommand() and self.powerStatus == "ON"

        def refresh(ms):
            """ Call self.app.Refresh() in loop for designated milliseconds. """
            while ms > 0:
                self.app.last_refresh_time = time.time()
                tk_after = False if ms < GLO['REFRESH_MS'] else True
                rst = time.time()
                self.app.Refresh(tk_after=tk_after)
                if not tk_after:
                    time.sleep(fast_sleep)  # give 5 ms idle time
                    self.app.update_idletasks()  # Give screen and mouse response
                refresh_ms = int((time.time() - rst) * 1000)
                ms -= refresh_ms
                
                if tk_after:  # tally normal refresh
                    self.stat["norm_ms"] += refresh_ms
                    self.stat["norm_cnt"] += 1
                else:  # tally fast refresh
                    self.stat["fast_ms"] += refresh_ms
                    self.stat["fast_cnt"] += 1

        def processStep():
            """ Process One Step """
            if not self.app.isActive:
                v2_print(_who, "Closing down. self.app.isActive:", self.app.isActive)
                return False
            if not self.already_breathing_colors:
                return False  # Nighttime and Set Color can turn off breathing

            start_step = time.time()
            result = setColor()  # Waits 1 second for a response
            end_step = time.time()
            gatt_ms = int((end_step - start_step) * 1000.0)

            if result:
                self.stat["gatt_ms"] += gatt_ms
                self.stat["gatt_cnt"] += 1
                if self.stat["gatt_high"] == 0:  # First gatt encountered?
                    self.stat["gatt_low"] = self.stat["gatt_high"] = gatt_ms
                if gatt_ms < self.stat["gatt_low"]:
                    self.stat["gatt_low"] = gatt_ms
                if gatt_ms > self.stat["gatt_high"]:
                    self.stat["gatt_high"] = gatt_ms
            else:
                if not self.app.isActive:  # Shutting down?
                    self.already_breathing_colors = False  # End this method
                    return False
                self.stat["fail_ms"] += gatt_ms  # Time waiting for response
                self.stat["fail_cnt"] += 1

                # LED Light strip not connected OR Nighttime/Set Color menu options
                # v2_print(_who, "LED Light strip not connected.")
                if self.connect_errors == self.MAX_FAIL:  # Give up
                    self.connect_errors = 0  # Reset self.Connect() errors
                    self.already_breathing_colors = False  # End this method
                    self.device = None
                    self.powerStatus = "?"
                    return False

            self.app.last_refresh_time = time.time()
            sleep_ms = step_ms - gatt_ms
            sleep_ms = 0 if sleep_ms < 0 else sleep_ms

            # Sleep low & high are exempt from bots and tops
            if self.stat["sleep_high"] == 0:  # First sleep encountered?
                self.stat["sleep_low"] = self.stat["sleep_high"] = sleep_ms
            if self.stat["sleep_low"] > sleep_ms > 0:
                self.stat["sleep_low"] = sleep_ms
            if sleep_ms > self.stat["sleep_high"]:
                self.stat["sleep_high"] = sleep_ms

            # Override sleep_ms - at low, sleep for bots, at high, sleep for tops
            if step_ndx == step_count - 1:  # Last step?
                if turning_up:
                    sleep_ms = tops
                    v2_print(ext.ch(), "HIGHEST Brightness")
                else:
                    sleep_ms = bots
                    v2_print(ext.ch(), "LOWEST Brightness")

            if sleep_ms:  # Time for sleeping after gatt command?
                self.stat["sleep_ms"] += sleep_ms
                self.stat["sleep_cnt"] += 1
                refresh(sleep_ms)  # Normal / Fast Refresh in loop

            return True

        # Main loop until app closes or method ends
        while self.app.isActive:
            for step_ndx in range(step_count):
                if not processStep():
                    break

            if not self.already_breathing_colors:  # Is method ending?
                if self.powerStatus == "ON":
                    v2_print(_who, "Forced off by Nighttime or Set Color menu option.")
                elif self.powerStatus == "?":
                    v2_print(_who, "Lost connection to: '" + self.name + "'.")
                elif self.powerStatus == "OFF":
                    v2_print(_who, "'" + self.name + "' was manually turned off.")
                else:
                    v0_print(_who, "Breathing Colors invalid power",
                             "status: '" + self.powerStatus + "'.")
                break  # 2025-01-25 TODO: Display self.stat and self.parm

            if turning_up:  # End turning up. Begin turning down.
                v2_print(ext.ch(), "Turning down brightness")
            else:  # End turning down. Begin turning up.
                color_ndx += 1  # Next color
                color_ndx = color_ndx if color_ndx <= color_max else 0
                v2_print(ext.ch(), "New color_ndx:", color_ndx)
            turning_up = not turning_up  # Flip direction

        # Statistics displayed with "View" dropdown, "Breathing stats"
        v1_print("\n" + ext.ch() + _who, "Parameters:")
        v1_print("  low:", low, " | high:", high, " | span:", span,
                 " | step:", step, " | bots:", bots, " | tops:", tops)
        v1_print("  step_count:", step_count, " | step_amount:", step_amount,
                 " | step_ms:", step_ms)

        v1_print("\n" + _who, "Run Statistics:")
        gatt_avg = 0 if self.stat["gatt_cnt"] == 0 else self.stat["gatt_ms"] / self.stat["gatt_cnt"]
        v1_print("  gatt_ms:", self.stat["gatt_ms"], " | gatt_cnt:", 
                 self.stat["gatt_cnt"], " | average:", gatt_avg, 
                 " | low:", self.stat["gatt_low"], " | high:", self.stat["gatt_high"])

        sleep_avg = 0 if self.stat["sleep_cnt"] == 0 else self.stat["sleep_ms"] / self.stat["sleep_cnt"]
        v1_print("  sleep_ms:", self.stat["sleep_ms"], " | sleep_cnt:",
                 self.stat["sleep_cnt"], " | average:", sleep_avg, 
                 " | low:", self.stat["sleep_low"], " | high:", self.stat["sleep_high"])

        norm_avg = 0 if self.stat["norm_cnt"] == 0 else self.stat["norm_ms"] / self.stat["norm_cnt"]
        v1_print("  norm_ms:", self.stat["norm_ms"], " | norm_cnt:", self.stat["norm_cnt"],
                 " | average:", norm_avg, " | REFRESH_MS:", GLO['REFRESH_MS'])

        fast_avg = 0 if self.stat["fast_cnt"] == 0 else self.stat["fast_ms"] / self.stat["fast_cnt"]
        v1_print("  fast_ms:", self.stat["fast_ms"], " | fast_cnt:", self.stat["fast_cnt"],
                 " | average:", fast_avg, " | self.FAST_MS:", self.FAST_MS)

        fail_avg = 0 if self.stat["fail_cnt"] == 0 else self.stat["fail_ms"] / self.stat["fail_cnt"]
        v1_print("  fail_ms:", self.stat["fail_ms"], " | fail_cnt:", self.stat["fail_cnt"],
                 " | average:", fail_avg, " | self.MAX_FAIL:", self.MAX_FAIL, "\n")

        v2_print(self.monitorBreatheColors(test=True))

        self.already_breathing_colors = False
        self.app.EnableMenu()  # Disable View dropdown menu option "Breathing stats".

    def monitorBreatheColors(self, test=False):
        """ Monitor statistics generated inside self.breatheColors() method. """
        _who = self.who + "monitorBreatheColors():"
        if self.already_breathing_colors is False and test is False:
            v0_print("\n" + ext.ch(), _who, "Breathe Colors is NOT running!")
            return
        
        ''' parm = {"low": low, "high": high, "span": span, "step": step,
                    "bots": bots, "tops": tops}  # breatheColors() parameters '''

        txt = "\tRed:  " + str(self.red) + "\tGreen:  " + str(self.green)
        txt += "\tBlue:  " + str(self.blue)
        if cp.sunlight_percent > 0:
            txt += "\tSunlight percentage boost:\t"
            txt += str(cp.sunlight_percent) + " %"
        txt += "\n\n"

        def one(name, ms, cnt, ms2=None, ms3=None):
            """ Format one line. """
            ret = name + "\t" + '{:,}'.format(self.stat[ms])
            ret += "\t" + '{:,}'.format(self.stat[cnt])  # integer w/ comma thousands
            avg = 0 if self.stat[cnt] == 0 else int(self.stat[ms] / self.stat[cnt])
            ret += "\t" + '{:,}'.format(avg)  # integer with comma thousands separator
            if ms2 is None:  # Last two columns aren't used
                ret += "\n"  # append new line character
            elif isinstance(ms3, str):  # gatt or sleep: low and high?
                ret += "\t" + '{:,}'.format(self.stat[ms2])  # lowest found
                ret += "\t" + '{:,}'.format(self.stat[ms3]) + "\n"  # highest found
            else:  # ms2 is variable name string, ms3 is an integer
                ret += "\t" + ms2 + "\t" + '{:,}'.format(ms3) + "\n"
            return ret

        ''' stat = {
            "gatt_ms": 0, "gatt_cnt": 0, "gatt_low": 0, "gatt_high": 0, "sleep_ms": 0,
            "sleep_cnt": 0, "fast_ms": 0, "fast_cnt": 0, "norm_ms": 0, "norm_cnt": 0,
            "fail_ms": 0, "fail_cnt": 0
        } '''

        # Tabs= Left             Right  Right    Right  Left    Left
        txt += "Function\tMilliseconds\tCount\tAverage\tLowest\tHighest\n\n"

        txt += one("Set LED Color", "gatt_ms", "gatt_cnt", "gatt_low", "gatt_high")
        txt += one("Set LED Sleep", "sleep_ms", "sleep_cnt", "sleep_low", "sleep_high")
        txt += one("Regular Refresh", "norm_ms", "norm_cnt", "REFRESH_MS:", GLO['REFRESH_MS'])
        txt += one("Fast Refresh", "fast_ms", "fast_cnt", "FAST_MS:", self.FAST_MS)
        txt += one("LED Failures", "fail_ms", "fail_cnt", "MAX_FAIL:", self.MAX_FAIL)

        return txt

    def Connect(self, sudo_reset=False, retry=0):
        """ Connect to Bluetooth Low Energy with GATT.

            Sometimes two or three attempts to connect and turn on power is required.
            Sometimes that doesn't work and a resetBluetooth() is required followed by
            turnOn()

            :param sudo_reset: bluetooth is restarted in gatttool.py using:
                subprocess.Popen(["sudo", "systemctl", "restart", "bluetooth"]).wait()
                subprocess.Popen([
                    "sudo", "hciconfig", self._hci_device, "reset"]).wait()
            :param retry: Number of sequential failures to display errors.
        """

        _who = self.who + "Connect():"
        v2_print("\n" + _who, "self.hci_device:", self.hci_device, " | name:", self.name,
                 "\n  GLO['LED_LIGHTS_MAC']:", GLO['LED_LIGHTS_MAC'],
                 " | sudo_reset:", sudo_reset)

        if len(GLO['LED_LIGHTS_MAC']) != 17:  # Can be "" for new dictionary
            v0_print(_who, "Invalid GLO['LED_LIGHTS_MAC']:", GLO['LED_LIGHTS_MAC'])

        try:
            self.device = tc.connect(GLO['LED_LIGHTS_MAC'], reset_on_start=sudo_reset)
            self.connect_errors = 0  # Reset connect error counter
        except tc.pygatt.exceptions.NotConnectedError as err:
            v2_print(_who, "error:")
            v2_print(err)
            v2_print("Is bluetooth enabled?")
            self.device = None
            self.powerStatus = "?"

            # Count sequential errors and after x times ShowInfo()
            self.connect_errors += 1
            if self.connect_errors > retry:
                self.showMessage(err, count=self.connect_errors)
                self.connect_errors = 0  # Reset for new sequential count
            else:
                delta = round(time.time() - GLO['APP_RESTART_TIME'], 2)
                delta_str = "{0:>8.2f}".format(delta)  # "99999.99" format
                v1_print(delta_str, "|", _who, "Failed to connect:",
                         self.connect_errors, "time(s).")

        if self.app:  # Prevent erroneous Resume from Suspend from running
            self.app.last_refresh_time = time.time()

        return self.device

    def showMessage(self, err=None, count=1):
        """ Show error message """
        _who = self.who + "showMessage():"
        self.device = None  # Force connect on next attempt
        self.powerStatus = "?"

        if self.app and self.app.usingDevicesTreeview:
            self.app.refreshDeviceStatusForInst(self)

        # 2025-01-24 message appears multiple times in code
        if str(err) is not "None":
            msg = str(err) + "\n\n"
        else:
            msg = ""  # No gatttool error message

        if "cannot start" in msg:
            # gatttool could not find computer's bluetooth adapter (driver not running)
            msg += "Turn on bluetooth in Ubuntu. If bluetooth was on and won't\n"
            msg += "restart then you can reboot or try these commands:\n\n"
            # noinspection SpellCheckingInspection
            msg += "\tsudo rmmod btusb btintel\n"
            # noinspection SpellCheckingInspection
            msg += "\tsudo modprobe btusb btintel\n"
            msg += "\tsudo service bluetooth restart\n\n"

        elif "not connected" in msg:
            # bluetooth device not connected to computer's bluetooth adapter
            msg += "Verify correct MAC address with Tools - View Bluetooth Devices."
            msg += "\nYou can also view Device name with Happy Lighting Phone App.\n\n"
            msg += "You can Right-Click on device picture and use 'Reset Bluetooth'.\n"
            msg += "Also from same popup menu select 'Turn On "
            msg += self.name + "'.\n"
            msg += "The 'View Bluetooth Devices' feature is also on this menu.\n\n"

        elif "No response received" in msg:
            # waited for response and device timed out in 10 seconds
            msg += "Waited for response from: '" + self.name + "' but none received.\n\n"
            msg += "Right-Click on: '" + self.name + "' picture for menu.\n\n"
            msg += "First try turning on: '" + self.name + "' a few times.\n"
            msg += "Otherwise, try 'Reset Bluetooth' to see if that fixes the problem.\n"
            msg += "Finally, try 'View Bluetooth Devices' and look for: '"
            msg += self.ip + "'.\n\n"

        if count > 0:
            msg += "Error occurred " + str(count) + " times.\n\n"
        msg += "At command line, does 'bluetoothctl show' display your devices?\n"
        msg += "NOTE: Type 'exit' to exit the 'bluetoothctl' application.\n\n"
        msg += "Always try: 'Turn on " + self.name + "' a few times for quick fix."
        v1_print(_who, msg + "\n")
        if self.app is not None:
            self.app.ShowInfo("Not connected", msg, "error", align="left")

    def getPower(self):
        """ Return "ON", "OFF" or "?".
            On startup cannot query LED's so status unknown until turned on or off
                using the self.startDevice() method.
$ ps aux | grep gatttool | grep -v grep | wc -l
46

# Run getPower() which doesn't initialize Bluetooth Low Energy LED Lights device

$ ps aux | grep gatttool | grep -v grep | wc -l
47

        """
        _who = self.who + "getPower():"
        v2_print("\n" + _who, "Get Power Status for:", self.name)

        # BLE LED Light Strips requires connection
        if GLO['LED_LIGHTS_MAC'] is not None and self.device is None:
            self.startDevice()  # Will test self.BluetoothStatus attribute.
            # self.startDevice() runs self.Connect()

        return self.powerStatus

    def Disconnect(self):
        """ Disconnect device """
        _who = self.who + "Disconnect():"
        if self.device is not None:
            try:
                tc.disconnect(self.device)
            except pygatt.exceptions.NotConnectedError as err:
                v1_print(_who, err)  # Device not connected!
            except AttributeError:
                v1_print(_who, "self.device:", self.device)
        self.device = None
        self.powerStatus = "?"

    def TurnOn(self):
        """ Turn On BLE (Bluetooth Low Energy) LED Light Strip. """

        _who = self.who + "TurnOn():"
        v2_print("\n" + _who, "Send GATT cmd to:", self.name)

        if self.device is None:
            self.Connect()

        try:
            tc.powerOn(self.device)
            self.powerStatus = "ON"  # Can be "ON", "OFF" or "?"
            return self.powerStatus
        except pygatt.exceptions.NotConnectedError as err:
            v1_print(_who, err)
        except AttributeError:
            v1_print(_who, "AttributeError: self.device:", self.device)

        self.device = None  # Force connect on next attempt
        self.powerStatus = "?"

        return self.powerStatus

    def TurnOff(self):
        """ Turn Off BLE (Bluetooth Low Energy) LED Light Strip.
            Warning: Does NOT disconnect. This must be done when suspending system.
        """

        _who = self.who + "TurnOff():"
        v2_print("\n" + _who, "Send GATT cmd to:", self.name)

        if self.device is None:
            self.Connect()

        try:
            tc.powerOff(self.device)
            self.powerStatus = "OFF"  # Can be "ON", "OFF" or "?"
            return self.powerStatus
        except pygatt.exceptions.NotConnectedError as err:
            v0_print(_who, err)
        except AttributeError:
            v0_print(_who, "AttributeError: self.device:", self.device)

        self.device = None  # Force connect on next attempt
        self.powerStatus = "?"
        return self.powerStatus

    def isDevice(self, forgive=False):
        """ Return True if adb connection for Android device (using IP address).
            When called by Discovery, forgive=True (not used)
        """

        _who = self.who + "isDevice():"
        v2_print(_who, "Test if device is Bluetooth LED Light:", self.mac)

        if forgive:
            pass  # Make pycharm happy

        if self.mac == GLO['LED_LIGHTS_MAC']:
            v0_print(_who, "MAC address matches:", self.mac)

        return self.mac == GLO['LED_LIGHTS_MAC']


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
        global ble  # Inside global ble, assign app = Application() which points here
        self.bleSaveInst = None  # For breathing colors monitoring of the real inst
        self.bleScrollbox = None
        self.last_red = self.last_green = self.last_blue = 0

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

        self.isActive = True  # Set False when exiting or suspending
        self.requires = ['arp', 'getent', 'timeout', 'curl', 'adb', 'hs100.sh', 'aplay',
                         'ps', 'grep']
        self.installed = []
        self.CheckDependencies(self.requires, self.installed)

        if not self.dependencies_installed:
            v1_print(_who, "Some Application() dependencies are not installed.")
            v1_print(self.requires)
            v1_print(self.installed)

        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=g.MON_FONT)

        self.last_refresh_time = time.time()  # Refresh idle loop last entered time
        # Normal 1 minute delay to rediscover is shortened at boot time if fast start
        self.last_rediscover_time = time.time()  # Last analysis of `arp -a`
        if p_args.fast:
            # Allow 3 seconds to move mouse else start rediscover
            self.last_rediscover_time = time.time() - GLO['REDISCOVER_SECONDS'] + 3
        self.rediscover_done = True  # 16ms time slices until done.
        self.rediscover_row = 0  # Current row processed in Treeview
        self.tree = None  # Painted in PopulateTree()
        # Images used in PopulateTree() and/or other methods
        self.photos = None

        # Right-click popup menu images
        on = "turn_on.png"
        off = "turn_off.png"
        up = "up.png"
        down = "down.png"
        close = "close.jpeg"
        self.img_turn_off = ImageTk.PhotoImage(
            Image.open(off).resize((42, 26), Image.ANTIALIAS))
        self.img_turn_on = ImageTk.PhotoImage(
            Image.open(on).resize((42, 26), Image.ANTIALIAS))
        self.img_up = ImageTk.PhotoImage(
            Image.open(up).resize((22, 26), Image.ANTIALIAS))
        self.img_down = ImageTk.PhotoImage(
            Image.open(down).resize((22, 26), Image.ANTIALIAS))
        self.img_close = ImageTk.PhotoImage(
            Image.open(close).resize((26, 26), Image.ANTIALIAS))

        # Sony TV Picture On/Off
        picture_on = "picture_on.png"
        picture_off = "picture_off.png"
        self.img_picture_on = ImageTk.PhotoImage(
            Image.open(picture_on).resize((42, 26), Image.ANTIALIAS))
        self.img_picture_off = ImageTk.PhotoImage(
            Image.open(picture_off).resize((42, 26), Image.ANTIALIAS))

        # Bluetooth LED Light Strip
        set_color = "set_color.jpeg"
        nighttime = "nighttime.png"
        breathing = "breathing.jpeg"
        reset = "reset.jpeg"
        self.img_set_color = ImageTk.PhotoImage(
            Image.open(set_color).resize((26, 26), Image.ANTIALIAS))
        self.img_nighttime = ImageTk.PhotoImage(
            Image.open(nighttime).resize((26, 26), Image.ANTIALIAS))
        self.img_breathing = ImageTk.PhotoImage(
            Image.open(breathing).resize((26, 26), Image.ANTIALIAS))
        self.img_reset = ImageTk.PhotoImage(
            Image.open(reset).resize((26, 26), Image.ANTIALIAS))


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
        self.notebook = self.edit_pref_active = None

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
        self.usingDevicesTreeview = True  # Startup uses Devices Treeview
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
        # Also assign to BLE LED Light Strip which calls ShowInfo
        for instance in ni.instances:
            inst = instance['instance']
            if inst.type_code == GLO['LAPTOP_D']:
                inst.app = self
            elif inst.type_code == GLO['BLE_LS']:
                inst.app = self  # BluetoothLedLightStrip
                ble.app = self  # For functions called from Dropdown menu
                self.bleSaveInst = inst  # For breathing colors monitoring

        ''' Save Toplevel OS window ID for minimizing window '''
        command_line_list = ["xdotool", "getactivewindow"]
        event = self.runCommand(command_line_list, forgive=False)
        self.xdo_os_window_id = event['output']
        # self.xdo_os_window_id: 102760472  THIS CHANGED FROM ABOVE 92274698

        while self.Refresh():  # Run forever until quit
            pass

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
        self.view_menu.add_command(label="Bluetooth devices", font=g.FONT, underline=10,
                                   command=self.DisplayBluetooth, state=tk.NORMAL)
        self.view_menu.add_command(label="Discovery timings", font=g.FONT, underline=10,
                                   command=self.DisplayTimings)
        self.view_menu.add_command(label="Discovery errors", font=g.FONT, underline=10,
                                   command=self.DisplayErrors, state=tk.DISABLED)
        self.view_menu.add_command(label="Breathing stats", font=g.FONT, underline=10,
                                   command=self.DisplayBreathing, state=tk.DISABLED)

        mb.add_cascade(label="View", font=g.FONT, underline=0, menu=self.view_menu)

        # Tools Dropdown Menu
        self.tools_menu = tk.Menu(mb, tearoff=0)
        self.tools_menu.add_command(label="Big number calculator", font=g.FONT,
                                    underline=0, command=self.OpenCalculator,
                                    state=tk.DISABLED)
        self.tools_menu.add_command(label="Timer " + str(GLO['TIMER_SEC']) + " seconds",
                                    font=g.FONT, underline=0,
                                    command=lambda: self.ResumeWait(timer=GLO['TIMER_SEC']))
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

        if not self.isActive:
            return

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
        if not self.usingDevicesTreeview:
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

        if self.bleSaveInst and self.bleSaveInst.already_breathing_colors:
            self.view_menu.entryconfig("Breathing stats", state=tk.NORMAL)
        else:
            self.view_menu.entryconfig("Breathing stats", state=tk.DISABLED)

        ''' Tools Menu '''
        self.tools_menu.entryconfig("Big number calculator", state=tk.NORMAL)
        if GLO['SUDO_PASSWORD'] is None:
            self.tools_menu.entryconfig("Forget sudo password", state=tk.DISABLED)
        else:
            self.tools_menu.entryconfig("Forget sudo password", state=tk.NORMAL)
        self.tools_menu.entryconfig("Debug information", state=tk.DISABLED)

    def CloseApp(self, *_args):
        """ <Escape>, X on window, 'Exit from dropdown menu or Close Button"""

        self.isActive = False  # Signal closing down so methods return

        # Need Devices treeview displayed to save ni.view_order
        if not self.usingDevicesTreeview:
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
        #if self.edit_pref_active and self.notebook:
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
            self.usingDevicesTreeview = False
        elif self.sensors_devices_btn['text'] == self.devices_btn_text:
            show_devices = True
            self.sensors_devices_btn['text'] = self.sensors_btn_text
            self.tt.set_text(self.sensors_devices_btn, "Show Temperatures and Fans.")
            self.usingDevicesTreeview = True
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

        cr.inst.powerStatus = "?" if cr.inst.powerStatus is None else cr.inst.powerStatus
        # 320 ms row highlighting fade in
        cr.FadeIn(item)

        if cr.arp_dict['type_code'] == GLO['KDL_TV']:
            # Sony TV has power save mode to turn picture off and listen to music
            menu.add_command(label=name + " Picture On ",
                             font=g.FONT, state=tk.DISABLED,
                             image=self.img_picture_on, compound=tk.LEFT,
                             command=lambda: self.PictureOn(cr))
            menu.add_command(label=name + " Picture Off ",
                             font=g.FONT, state=tk.DISABLED,
                             image=self.img_picture_off, compound=tk.LEFT,
                             command=lambda: self.PictureOff(cr))
            cr.inst.getVolume()
            menu.add_separator()

        if cr.arp_dict['type_code'] == GLO['BLE_LS']:
            # Bluetooth Low Energy LED Light Strip
            name_string = "Set " + name + " Color"
            menu.add_command(label=name_string,
                             font=g.FONT, state=tk.DISABLED,
                             image=self.img_set_color, compound=tk.LEFT,
                             command=lambda: self.setColor(cr))
            menu.add_command(label="Nighttime brightness",
                             font=g.FONT, state=tk.DISABLED,
                             image=self.img_nighttime, compound=tk.LEFT,
                             command=lambda: self.setNight(cr))
            menu.add_command(label="Breathing colors",
                             font=g.FONT, state=tk.DISABLED,
                             image=self.img_breathing, compound=tk.LEFT,
                             command=lambda: self.breatheColors(cr))

            menu.add_separator()

            menu.add_command(label="Reset Bluetooth", font=g.FONT,
                             image=self.img_reset, compound=tk.LEFT,
                             command=cr.inst.resetBluetooth, state=tk.DISABLED)
            menu.add_command(label="View Bluetooth Devices", font=g.FONT,
                             image=self.img_reset, compound=tk.LEFT,
                             command=self.DisplayBluetooth, state=tk.NORMAL)

            # Device must be on for Set Color, Nighttime and Breathing Colors
            if cr.inst.powerStatus == "ON":
                state = tk.NORMAL
            else:
                state = tk.DISABLED

            menu.entryconfig(name_string, state=state)
            menu.entryconfig("Nighttime brightness", state=state)
            if cr.inst.already_breathing_colors:
                state = tk.DISABLED  # Override if breathing colors already running
            menu.entryconfig("Breathing colors", state=state)

            menu.add_separator()

            if cr.inst.device is None:
                menu.entryconfig("Reset Bluetooth", state=tk.NORMAL)
            else:
                menu.entryconfig("Reset Bluetooth", state=tk.DISABLED)

        menu.add_command(label="Turn On " + name, font=g.FONT, state=tk.DISABLED,
                         image=self.img_turn_on, compound=tk.LEFT,
                         command=lambda: self.TurnOn(cr))
        menu.add_command(label="Turn Off " + name, font=g.FONT, state=tk.DISABLED,
                         image=self.img_turn_off, compound=tk.LEFT,
                         command=lambda: self.TurnOff(cr))
        menu.add_separator()
        menu.add_command(label="Move " + name + " Up", font=g.FONT, state=tk.DISABLED,
                         image=self.img_up, compound=tk.LEFT,
                         command=lambda: self.MoveRowUp(cr))
        menu.add_command(label="Move " + name + " Down", font=g.FONT, state=tk.DISABLED,
                         image=self.img_down, compound=tk.LEFT,
                         command=lambda: self.MoveRowDown(cr))
        menu.add_separator()
        menu.add_command(label="Close menu", font=g.FONT, command=ClosePopup,
                         image=self.img_close, compound=tk.LEFT)

        menu.tk_popup(event.x_root, event.y_root)

        menu.bind("<FocusOut>", ClosePopup)

        # Enable Turn On/Off menu options depending on current power status.
        if cr.arp_dict['type_code'] == GLO['KDL_TV']:
            cr.inst.PowerSavingMode()
            if cr.inst.power_saving_mode == "OFF":
                menu.entryconfig(name + " Picture Off ", state=tk.NORMAL)
            elif cr.inst.power_saving_mode == "ON":
                menu.entryconfig(name + " Picture On ", state=tk.NORMAL)
            else:
                pass  # power_saving_mode == "?"

        if cr.inst.powerStatus != "ON":
            menu.entryconfig("Turn On " + name, state=tk.NORMAL)
        if cr.inst.powerStatus != "OFF":
            menu.entryconfig("Turn Off " + name, state=tk.NORMAL)

        # Allow moving up unless at top, allow moving down unless at bottom
        all_iid = self.tree.get_children()
        if item != all_iid[0]:
            menu.entryconfig("Move " + name + " Up", state=tk.NORMAL)
        if item != all_iid[-1]:
            menu.entryconfig("Move " + name + " Down", state=tk.NORMAL)

        # Reset last rediscovery time. Some methods can take 10 seconds to timeout
        self.last_refresh_time = time.time()

    def PictureOn(self, cr):
        """ Mouse right button click selected "<name> Picture On". """
        _who = self.who + "PictureOn():"
        resp = cr.inst.PictureOn()
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()

    def PictureOff(self, cr):
        """ Mouse right button click selected "<name> Picture Off". """
        _who = self.who + "PictureOff():"
        resp = cr.inst.PictureOff()
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()

    def setColor(self, cr):
        """ Mouse right button click selected "Set LED Lights Color".
            Note if cr.device in error a 10 second timeout can occur.
        """
        _who = self.who + "setColor():"
        resp = cr.inst.setColor()
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()

    def setNight(self, cr):
        """ Mouse right button click selected "Nighttime brightness".
            Note if cr.device in error a 10 second timeout can occur.
        """
        _who = self.who + "setNight():"
        resp = cr.inst.setNight()
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()

    def breatheColors(self, cr):
        """ Mouse right button click selected "Set LED Lights Color".
            Note if cr.device in error a 10 second timeout can occur.
        """
        _who = self.who + "breatheColors():"
        resp = cr.inst.breatheColors()
        self.last_refresh_time = time.time()
        if not self.isActive:
            return
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()

    def TurnOn(self, cr):
        """ Mouse right button click selected "Turn On".
            Also called by SetAllPower("ON").
        """
        _who = self.who + "TurnOn():"
        resp = cr.inst.TurnOn()
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()
        cr.inst.powerStatus = str(resp)
        cr.inst.resumePowerOn = 0  # Resume didn't power on the device
        cr.inst.manualPowerOn = 0  # Was device physically powered on?
        cr.inst.nightPowerOn = 0  # Did nighttime power on the device?
        cr.inst.menuPowerOn += 1  # User powered on the device via menu

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
        cr.inst.powerStatus = str(resp)
        cr.inst.suspendPowerOff = 0  # Suspend didn't power off the device
        cr.inst.manualPowerOff = 0  # Was device physically powered off?
        cr.inst.dayPowerOff = 0  # Did daylight power off the device?
        cr.inst.menuPowerOff += 1  # User powered off the device via menu

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
        self.update_idletasks()
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
            self.ResumeFromSuspend()  # Resume Wait + Conditionally Power on devices
            now = time.time()  # can be 15 seconds or more later
            GLO['APP_RESTART_TIME'] = now  # Reset app started time to resume time

        if not self.winfo_exists():  # Second check needed June 2023
            return False  # self.close() has set to None

        ''' Is there a TV to be monitored for power off to suspend system? '''
        # 2024-12-23 TODO: SETUP FOR SONY TV REST API

        ''' Always give time slice to tooltips - requires sql.py color config '''
        self.tt.poll_tips()  # Tooltips fade in and out. self.info piggy backing
        self.update()  # process events in queue. E.G. message.ShowInfo()

        if not self.winfo_exists():  # Second check needed June 2023
            return False  # self.close() has set to None

        ''' Displaying statistics for Bluetooth LED Light Strip breathing colors? '''
        if self.bleSaveInst and self.bleScrollbox:
            self.DisplayBreathing()

        ''' Check `sensors` (if installed) every GLO['SENSOR_CHECK'] seconds '''
        sm.Sensors()

        ''' Rediscover devices every GLO['REDISCOVER_SECONDS'] '''
        if int(now - self.last_rediscover_time) > GLO['REDISCOVER_SECONDS']:
            self.Rediscover(auto=True)  # Check for changes in IP addresses, etc
            night = cp.NightLightStatus()
            v2_print(_who, "cp.NightLightStatus():", night)

        ''' Speedy derivative when called by CPU intensive methods '''
        if not tk_after:
            return self.winfo_exists()

        ''' Should not happen very often, except after suspend resume '''
        if self.last_refresh_time > now:
            v3_print(_who, "self.last_refresh_time: ",
                     ext.h(self.last_refresh_time), " >  now: ", ext.h(now))
            now = self.last_refresh_time

        ''' Sleep remaining time until GLO['REFRESH_MS'] expires '''
        sleep = GLO['REFRESH_MS'] - int(now - self.last_refresh_time)
        sleep = sleep if sleep > 0 else 1  # Sleep minimum 1 millisecond
        if sleep == 1:
            v0_print(_who, "Only sleeping 1 millisecond")
        self.after(sleep)  # Sleep until next 60 fps time
        self.last_refresh_time = time.time()  # 2024-12-05 was 'now' too stale?

        ''' Wrapup '''
        return self.winfo_exists()  # Go back to caller as success or failure

    def Suspend(self, *_args):
        """ Suspend system. """

        _who = self.who + "Suspend():"
        v0_print(_who, "Suspending system...")

        ''' Is countdown already running? '''
        if self.dtb:  # Cannot suspend when countdown timer is running.
            message.ShowInfo(self, thread=self.Refresh, win_grp=self.win_grp,
                             icon='warning', title="Cannot Suspend now.",
                             text="Countdown timer must be closed.")
            v0_print(_who, "Aborting suspend. Countdown timer active.")
            return

        ''' Is rediscovery in progress? '''
        if not self.rediscover_done:  # Cannot suspend during rediscovery.
            message.ShowInfo(self, thread=self.Refresh, win_grp=self.win_grp,
                             icon='warning', title="Cannot Suspend now.",
                             text="Device rediscovery is in progress for a few seconds.")
            v0_print(_who, "Aborting suspend. Device rediscovery in progress.")
            return

        self.isActive = False  # Signal closing down so methods return
        if self.bleSaveInst:  # Is breathing colors active?
            self.bleSaveInst.already_breathing_colors = False  # Force shutdown
        self.update_idletasks()
        self.after(100)
        self.SetAllPower("OFF")  # Turn off all devices except computer

        ''' Close any tooltip windows that will be expired on resume '''
        self.tt.poll_tips()

        cp.TurnOff()  # suspend computer

    def ResumeFromSuspend(self):
        """ Resume from suspend. Display status of devices that were
            known at time of suspend. Then set variables to trigger
            rediscovery for any new devices added.

            Called when: now - self.last_refresh_time > GLO['RESUME_TEST_SECONDS']
            Consequently long running processes must reseed self.last_refresh_time
            when they finish.

            2025-01-17 ERROR: Resume did not work for Sony TV, Sony Light, TCL TV,
                and TCL TV light. It did work for BLE LED Lights. Reason is resume
                wait is 3 seconds. Increase it to 6 seconds.

        """
        global rd
        rd = None  # In case rediscovery was in progress during suspend
        self.rediscover_done = True
        _who = self.who + "ResumeFromSuspend():"
        self.isActive = True  # Application GUI is active again

        self.ResumeWait()  # Display countdown waiting for devices to come online
        v1_print("\n" + _who, "ni.view_order:", ni.view_order)

        # Turn all devices on
        self.SetAllPower("ON")  # This also shows new status in devices treeview

        # Set variables to force rediscovery
        now = time.time()
        # Force rediscovery immediately after resume from suspend
        self.last_rediscover_time = now - GLO['REDISCOVER_SECONDS'] * 10.0
        self.last_refresh_time = now + 1.0  # If abort, don't come back here
        sm.last_sensor_log = now - GLO['SENSOR_LOG'] - 1.0  # Force initial sensor log

    def ResumeWait(self, timer=None, alarm=True, title=None, abort=True):
        """ Wait x seconds for devices to come online. If 'timer' passed do a
            simple countdown.


            :param timer: When time passed it's a countdown timer
            :param alarm: When True, sound alarm when countdown timer ends
            :param title: Title when it's not countdown timer
            :param abort: Allow countdown timer to be ended early (closed)
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
                break  # self.CloseApp() has destroyed window
            self.dtb.update(str(int(start + countdown_sec - time.time())))
            # Suspend uses: 'self.after(150)'
            self.after(100)
            # During countdown timer, don't trigger ResumeFromSuspend()
            self.last_refresh_time = time.time() + 1.0

        if timer and alarm is True:  # Play sound when timer ends
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
                    inst.dayPowerOff += 1
                    inst.nightPowerOn = 0
                    inst.menuPowerOff = 0
                    inst.manualPowerOff = 0
                    inst.suspendPowerOff = 0
                    inst.powerStatus = "OFF"
                    v1_print(_who, "Do not turn on Bias light in daytime.")
                    continue  # Do not turn on light during daytime
                else:
                    v1_print(_who, "Turn on Bias light at night.")
                    night_powered_on = True

            if inst.type_code == GLO['BLE_LS']:
                # Special debugging for LED Light Strips
                #v0_print(_who, "BEFORE:", inst.type_code, inst.mac, inst.name)
                #v0_print("inst.device:", inst.device)
                #v0_print("BluetoothStatus:", inst.BluetoothStatus,
                #         "powerStatus:", inst.powerStatus)
                pass
            resp = "?"  # Necessary for pyCharm checker only
            if state == "ON":
                v0_print(_who, "Unconditionally turning power 'ON':", inst.name)
                resp = inst.TurnOn()
                inst.powerStatus = str(resp)
                # TODO Check response
                inst.resumePowerOn += 1  # Resume powered on the device
                inst.menuPowerOn = 0  # User didn't power on the device via menu
                inst.nightPowerOn += 1 if night_powered_on else 0
            elif state == "OFF":
                ''' Timing out if power is already OFF
                Application().Suspend(): Suspending system...
                TclGoogleAndroidTV().TurnOff(): runCommand(): cmdReturncode: 124
                TclGoogleAndroidTV().TurnOff(): 192.168.0.17 timeout after: 5.0
                NetworkInfo().os_curl(): logEvent(): cmdReturncode: None

                If inst.Power is "OFF" do not try to turn off again and waste time.                
                '''
                if inst.powerStatus != "OFF":
                    v0_print(_who, "Conditionally turning power 'OFF':", inst.name)
                    resp = inst.TurnOff()
                    inst.powerStatus = str(resp)
                    inst.suspendPowerOff += 1  # Suspend powered off the device
                    inst.menuPowerOff = 0  # User didn't power on the device via menu
            else:
                v0_print(_who, "state is not 'ON' or 'OFF':", state)
                exit()

            if inst.type_code == GLO['BLE_LS']:
                # Special debugging for LED Light Strips
                #v0_print(_who, "AFTER:", inst.type_code, inst.mac, inst.name)
                #v0_print("inst.device:", inst.device)
                #v0_print("BluetoothStatus:", inst.BluetoothStatus,
                #         "powerStatus:", inst.powerStatus)
                pass

            # Update Devices Treeview with power status
            if not self.usingDevicesTreeview:
                continue  # No Devices Treeview to update

            # Get treeview row based on matching MAC address + type
            # Note that Laptop MAC address can have two types (Base and Display)
            cr = TreeviewRow(self)  # Setup treeview row processing instance
            iid = cr.getIidForInst(inst)  # Get iid number and set instance
            if iid is None:
                continue  # Instance not in Devices Treeview, perhaps a smartphone?

            old_text = cr.text  # Treeview row old power state "  ON", etc.
            cr.text = "  " + str(resp)  # Display treeview row new power state
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

        # Loop through ni.instances
        for i, instance in enumerate(ni.instances):
            inst = instance['instance']
            if self.usingDevicesTreeview:
                # Get treeview row based on matching MAC address + device_type
                iid = cr.getIidForInst(inst)  # Get iid number and set instance
                if iid is not None:
                    if auto is False or cr.text == "Wait...":
                        self.tree.see(iid)
                        cr.FadeIn(iid)

            inst.getPower()  # Get the power status for device
            self.last_refresh_time = time.time()  # In case getPower() long time

            # Update Devices Treeview with power status
            if not self.usingDevicesTreeview:
                continue  # No Devices Treeview to update

            if iid is None:
                continue  # Instance not in Devices Treeview, perhaps a smartphone?

            old_text = cr.text  # Treeview row's old power state "  ON", etc.
            cr.text = "  " + inst.powerStatus  # Display treeview row's new power state
            if cr.text != old_text:
                v1_print(_who, cr.mac, "Power status changed from: '"
                         + old_text.strip() + "' to: '" + cr.text.strip() + "'.")
            cr.Update(iid)  # Update row with new ['text']
            if auto is False or old_text == "Wait...":
                # Fade in/out performed when called from Dropdown Menu (auto=False).
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
            Caller sleeps between calls using GLO['REDISCOVER_SECONDS'].

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

        def resetRediscovery():
            """ Reset variables for exit. """
            global rd
            rd = None
            self.rediscover_done = True
            self.last_rediscover_time = time.time()
            # 2024-12-02 - Couple hours watching TV, suddenly ResumeFromSuspend() ran
            #   a few times with 3 second countdown. Reset self.last_refresh_time.
            self.last_refresh_time = time.time()  # Prevent resume from suspend
            self.file_menu.entryconfig("Rediscover now", state=tk.NORMAL)
            self.EnableMenu()

        v2_print(_who, "Rediscovery count:", len(rd.arp_dicts))

        # Refresh power status for all device instances in ni.arp_dicts
        self.RefreshAllPowerStatuses(auto=auto)
        GLO['LOG_EVENTS'] = True  # Reset to log events as required

        # TODO: Check rd.arp_dict entries for ip changes or new entries
        for i, rediscover in enumerate(rd.arp_dicts):
            if not self.isActive:
                # 2025-01-31 Resuming from suspend sometimes rd is None
                #   File "./homa.py", line 4299, in Refresh
                #     self.Rediscover(auto=True)  # Check for changes in IP addresses, etc
                #   File "./homa.py", line 4668, in Rediscover
                #     for i, rediscover in enumerate(rd.arp_dicts):
                # AttributeError: 'NoneType' object has no attribute 'arp_dicts'
                resetRediscovery()
                return

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

            v2_print("Checking MAC:", mac, "IP:", ip)
            arp_mac = ni.arp_for_mac(mac)  # NOTE different than rediscover !
            if not arp_mac:
                v1_print(_who, "new MAC discovered:", mac)
                #print("\n new arp_mac in rd.arp_dicts:", mac)
                # new arp_mac: 28:f1:0e:2a:1a:ed
                # new arp_mac: 9c:b6:d0:10:37:f7
                # add ni.arp_dicts, ni.instances, ni.devices, ni.view_order
                # add treeview row
                start = len(ni.arp_dicts)
                ni.arp_dicts.append(rediscover)
                discovered, instances, view_order = \
                    discover(update=False, start=start, end=start+1)

                if not self.isActive or rd is None:
                    resetRediscovery()
                    return

                if len(discovered) != 1:
                    print(_who, "Catastrophic error! len(discovered):",
                          len(discovered))
                    exit()

                if instances:
                    ni.instances.append(instances[0])
                    v1_print(_who, "Adding MAC to ni.instances:", mac)
                else:
                    v1_print(_who, "No new instance for MAC:", mac)
                    continue

                ni.view_order.append(mac)

                ni.devices = copy.deepcopy(rd.devices)  # Prevent rediscovery

                # Only update Devices Treeview when mounted.
                if not self.usingDevicesTreeview:
                    continue

                tr = TreeviewRow(self)
                tr.New(mac)
                new_row = len(self.tree.get_children())
                tr.Add(new_row)
                self.tree.see(str(new_row))
            elif mac not in ni.view_order:
                v2_print(_who, "ni.arp_dicts MAC not in view order:", mac)
                # ni.arp_dicts MAC not in view order: a8:4e:3f:82:98:b2   <-- ROUTER
                pass  # TODO: 2024-11-28 - Check rd.arp changes from ni.arp

            arp_inst = ni.inst_for_mac(mac)
            if bool(arp_inst):
                v2_print(_who, "found instance:", arp_inst['mac'], arp_mac['name'])
                if mac not in ni.view_order:
                    v0_print(_who, "arp exists, instance exists, but no view order")
                    v0_print("Inserting", rediscover['mac'], rediscover['name'])
                    ni.view_order.append(mac)
                    if not self.usingDevicesTreeview:
                        continue

                    tr = TreeviewRow(self)
                    tr.New(mac)
                    new_row = len(self.tree.get_children())
                    tr.Add(new_row)
                    self.tree.see(str(new_row))
                    # 2025-01-16 - At this point HomA locks up ???
                continue

            # Instance doesn't exist for existing arp mac
            v2_print(_who, "No Instance for ni.arp_dicts MAC:", mac)
            # No Instance for ni.arp_dicts MAC: a8:4e:3f:82:98:b2   <-- ROUTER

            # Application().Rediscover(): ni.arp_dicts MAC not in view order: c0:79:82:41:2f:1f
            # NetworkInfo().inst_for_mac(): mac address unknown: 'c0:79:82:41:2f:1f'
            # Application().Rediscover(): No Instance for ni.arp_dicts MAC: c0:79:82:41:2f:1f
            instance = ni.test_for_instance(arp_mac)
            if not bool(instance):
                continue

            v0_print("="*80, "\n" + _who, "FOUND NEW INSTANCE or",
                     "REDISCOVERED LOST INSTANCE:")
            v0_print(instance)
            ni.instances.append(instance)
            arp_mac['type_code'] = instance['instance'].type_code
            ni.view_order.append(rediscover['mac'])
            #ni.arp_dicts[i] = arp_mac  # Update arp list
            # 2025-01-16 arp_mac s/b updated in place. Check all usage above
            v0_print("="*80)

            if not self.usingDevicesTreeview:
                continue
            tr = TreeviewRow(self)
            tr.New(mac)
            new_row = len(self.tree.get_children())
            tr.Add(new_row)
            self.tree.see(str(new_row))

        # All steps done: Wait for next rediscovery period
        ni.cmdEvents.extend(rd.cmdEvents)  # For auto-rediscover, rd.cmdEvents[] empty
        resetRediscovery()

    def refreshDeviceStatusForInst(self, inst):
        """ Called by BluetoothLED """
        _who = self.who + "refreshDeviceStatusForInst():"
        if not self.usingDevicesTreeview:
            return
        # Find instance in treeview
        cr = TreeviewRow(self)
        iid = cr.getIidForInst(inst)
        if iid is None:
            v0_print(_who, "No iid for inst:", inst)
            return

        cr.Get(iid)
        self.tree.see(iid)
        cr.FadeIn(iid)

        old_text = cr.text  # Treeview row's old power state "  ON", etc.
        cr.text = "  " + inst.powerStatus  # Display treeview row's new power state
        if cr.text != old_text:
            v1_print(_who, cr.mac, "Power status changed from: '"
                     + old_text.strip() + "' to: '" + cr.text.strip() + "'.")
        cr.Update(iid)  # Update row with new ['text']
        cr.FadeOut(iid)

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
            message.ShowInfo(
                self, text=msg, thread=self.Refresh,
                title="Invalid sudo password", icon="error", win_grp=self.win_grp)

        self.last_refresh_time = time.time()  # Refresh idle loop last entered time
        return password  # Will be <None> if invalid password entered

    def ShowInfo(self, title, text, icon="information", align="center"):
        """ Called from instance which has no tk reference of it's own 
            From Application initialize with:   inst.app = self
            From Instance call method with:     self.app.ShowInfo()
        """
        message.ShowInfo(self, thread=self.Refresh, icon=icon, align=align,
                         title=title, text=text, win_grp=self.win_grp)
        self.last_refresh_time = time.time()  # Prevent resume from suspend

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
            #notebook.unbind("<Button-1>")  # 2024-12-21 TODO: old code, use unknown
            #self.win_grp.unregister_child(self.notebook)
            self.tt.close(self.notebook)
            self.edit_pref_active = None  # 2024-12-24 needed in homa?
            for key in GLO:
                atts_list = [x for x in all_notebook.listFields if x[0] == key]
                atts = atts_list[0]  # Only one entry in list
                if atts[2] != "read-write":
                    continue  # Only update dictionary with read-write variables
                if str(type(GLO[key])) != str(type(all_notebook.newData[key])):
                    print(_who, "Catastrophic error for:", key)
                    print("  type(GLO[key]):", type(GLO[key]),
                          "type(all_notebook.newData[key]):",
                          type(all_notebook.newData[key]))
                    #exit()
                    # Application().Preferences(): close(): Catastrophic error for: 0.3
                    #   type(GLO[key]): <type 'unicode'> type(all_notebook.newData[key]): <type 'str'>
                if GLO[key] != all_notebook.newData[key]:
                    v0_print(_who, "key:", key, "old:", GLO[key],
                             "new:", all_notebook.newData[key])
            self.notebook.destroy()
            self.notebook = None
            self.EnableMenu()
            #self.btn_frm.grid()  # Restore Application() bottom button bar

        #self.btn_frm.grid_forget()  # Hide Application() bottom button bar
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

        self.notebook = ttk.Notebook(self)
        listTabs, listFields = glo.defineNotebook()
        all_notebook = toolkit.makeNotebook(
            self.notebook, listTabs, listFields, GLO, "TNotebook.Tab",
            "Notebook.TFrame", "C.TButton", close, tt=self.tt)
        self.edit_pref_active = True
        self.EnableMenu()

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

                try:
                    errors = event['error'].splitlines()  # Error lines split on "\n"
                except AttributeError:
                    errors = event['error']  # Already a list
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

    def DisplayBluetooth(self):
        """ Display Bluetooth devices that have a name
            May have to call a few times to see a device that was connected.
            See: https://wiki.archlinux.org/title/Bluetooth#Troubleshooting
            for general problems and solutions with deprecated Bluez Tools.
        """
        _who = self.who + "DisplayBluetooth():"
        title = "Bluetooth devices"

        # Save mouse position because it can change over next 10 seconds
        x, y = hc.GetMouseLocation()

        found_inst = None
        for mac_arp in ni.arp_dicts:
            instance = ni.inst_for_mac(mac_arp['mac'], not_found_error=False)
            if not bool(instance):
                continue  # empty dictionary
            if instance['mac'] == GLO['LED_LIGHTS_MAC']:
                found_inst = instance['instance']

        if found_inst:
            found_inst.Disconnect()
            status = found_inst.getBluetoothStatus()  # Check for hci0 device active
        else:
            status = ble.getBluetoothStatus()  # Check for hci0 device active
        if status != "ON" and found_inst:
            status = found_inst.resetBluetooth(reconnect=False)
        if status != "ON" and found_inst is None:
            status = ble.resetBluetooth(reconnect=False)

        if status != "ON":
            v0_print(_who, "Bluetooth will not turn on.")
            return

        if found_inst:
            found_inst.Disconnect()
            v1_print(_who, "Using existing instance:", found_inst)
            device_list = found_inst.getBluetoothDevices(reconnect=False)
        else:
            v1_print(_who, "Creating new instance for reset.")
            device_list = ble.getBluetoothDevices(reconnect=False)
            # 10 second scan with countdown dtb
        if len(device_list) == 0:
            return

        scrollbox = self.DisplayCommon(_who, title, x=x, y=y, width=700)
        if scrollbox is None:
            return  # Window already opened and method is running

        # Loop through device_list
        for i, device in enumerate(device_list):
            address, name, count = device

            scrollbox.insert("end", address)
            scrollbox.insert("end", " - " + name + "  (")
            scrollbox.insert("end", str(count) + ")\n")

            instance = ni.inst_for_mac(address)
            if bool(instance):  # MAC address matches BLE device's MAC discovered
                scrollbox.highlight_pattern(address, "red")
                scrollbox.highlight_pattern(name, "yellow")
                arp_dict = ni.arp_for_mac(address)
                arp_dict['ip'] = name  # ip isn't used for bluetooth.
                # 2025-01-15 TODO: Update Treeview Row with new name.
            else:  # empty dictionary
                scrollbox.highlight_pattern(address, "blue")
                scrollbox.highlight_pattern(name, "green")

        if found_inst:
            v1_print(_who, "Restarting existing instance.")
            found_inst.startDevice()

        # After running gatttool taking 100% of a single CPU core
        # until homa.py exits. Fix by calling self.GATTToolJobs()

        self.update_idletasks()
        self.GATTToolJobs(found_inst=found_inst)

    def DisplayBreathing(self):
        """ Display Breathing Colors parameters and statistics in real time.
            Called about 3 times per second during self.Refresh() cycle.
            self.Refresh() in turn is called by bleSaveInst.breatheColors().
            bleSaveInst.monitorBreatheColors() returns formatted text lines.
            When first_time is True, create self.
        """
        _who = self.who + "DisplayBreathing():"
        title = "Bluetooth LED Breathing Colors Statistics"
        if self.bleSaveInst is None:
            return  # Should not happen
        if self.bleSaveInst.already_breathing_colors is False:
            return  # Should not happen

        def close():
            """ Close callback """
            self.bleScrollbox = None
            
        if self.bleScrollbox is None:
            self.bleScrollbox = self.DisplayCommon(_who, title, close_cb=close)
            # Compromise tabs shared by header parameters and body dynamic statistics
            tabs = ("400", "right", "550", "right", "700", "right",
                    "750", "left", "1125", "right")  # Note "numeric" aligns commas too!

            def reset_tabs(event):
                """ https://stackoverflow.com/a/46605414/6929343 """
                event.widget.configure(tabs=tabs)

            def in4(name1, value1, name2, value2):
                """ Insert 2 parameter variable pairs into custom scrollbox """
                line = name1 + ":\t" + str(value1) + "\t\t|\t"
                line += name2 + ":\t" + str(value2) + "\n"
                self.bleScrollbox.insert("end", line)

            self.bleScrollbox.configure(tabs=tabs)
            self.bleScrollbox.bind("<Configure>", reset_tabs)
            self.last_red = self.last_green = self.last_blue = 0

            p = self.bleSaveInst.parm  # shorthand to dictionary
            step_count = int(float(p["span"]) / float(p["step"]))
            step_value = float(p["high"] - p["low"]) / float(step_count)
            in4("Dimmest value", p["low"], "Breathe in/out duration", p["span"])
            in4("Brightest value", p["high"], "Step duration", p["step"])
            in4("Dimmest hold seconds", p["bots"], "Number of steps", step_count)
            in4("Brightest hold seconds", p["tops"], "Step value", step_value)
            self.bleScrollbox.insert("end", "\n\n")

        # Body is only updated when red, green or blue change
        if self.last_red == self.bleSaveInst.red and \
                self.last_green == self.bleSaveInst.green and \
                self.last_blue == self.bleSaveInst.blue:
            return

        # Delete dynamic lines in custom scrollbox
        self.bleScrollbox.delete(6.0, "end")

        all_lines = self.bleSaveInst.monitorBreatheColors()
        self.bleScrollbox.insert("end", all_lines)

        self.bleScrollbox.highlight_pattern("Blue:", "blue")
        self.bleScrollbox.highlight_pattern("Green:", "green")
        self.bleScrollbox.highlight_pattern("Red:", "red")

        self.bleScrollbox.highlight_pattern("Function", "yellow")
        self.bleScrollbox.highlight_pattern("Milliseconds", "yellow")
        self.bleScrollbox.highlight_pattern("Count", "yellow")
        self.bleScrollbox.highlight_pattern("Average", "yellow")
        self.bleScrollbox.highlight_pattern("Lowest", "yellow")
        self.bleScrollbox.highlight_pattern("Highest", "yellow")

        self.last_red = self.bleSaveInst.red
        self.last_green = self.bleSaveInst.green
        self.last_blue = self.bleSaveInst.blue

    def DisplayCommon(self, _who, title, x=None, y=None, width=1200, height=500,
                      close_cb=None):
        """ Common method for DisplayBluetooth, DisplayErrors(), DisplayTimings() """

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
            if close_cb:
                close_cb()

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

    def GATTToolJobs(self, found_inst=None):
        """ Check quantity and percentage of gatttool process ID's.

            ps -aux | grep gatttool | grep -v grep
        """
        _who = self.who + "GATTToolJobs():"
        v1_print("\n" + _who, "Check GATTTool percentage")
        if not self.CheckInstalled("ps"):
            v1_print(_who, "Command 'ps' not installed. Exiting.")
            return
        if not self.CheckInstalled("grep"):
            v1_print(_who, "Command 'grep' not installed. Exiting.")
            return

        # When calling 'ps ux' for current user, can get a PID that is ending.
        # external.kill_pid_running() ERROR: os.kill  failed for PID: 3962
        # external.kill_pid_running() ERROR: os.kill  failed for PID: 9915

        ''' ps | grep FAILS:
            Shell parameter expansion happens after the high-level parsing of 
            pipes breaks the line into structured commands, so your function 
            body runs as though you'd written:
            
                ps ax '|' grep -v grep '|'
            
            - that is, with the pipes as literal arguments to ps. That's why 
            you're getting the error from ps (not from grep!) complaining it 
            doesn't understand the | argument.
        '''
        command_line_list = ["ps", "ux"]  # "aux" is all users. Just get current.
        event = self.runCommand(command_line_list, _who)
        v3_print(_who, self.cmdString, event['output'], event['error'])

        found_pids = []
        high_pid_perc = 0
        lines = self.cmdOutput.splitlines()
        # 'ps ux' results but, twist the truth for meaningful reality
        # Change v1_print to v1_print after testing, reverse for testing.
        v1_print(_who, "'ps ux | grep -v grep | grep gatttool' results:")
        for line in lines:
            if "gatttool" in line and "grep" not in line:
                # equivalent of "ps ux | grep -v grep | grep gatttool"
                ll = line.split()
                # Line 4 is job closing down that can't be killed
                # 1  ['rick', '8336',  '10.7', '0.0', '0', '0', '?', 'Zs', '10:47', '0:24']
                # 2  ['rick', '13964', '61.2', '0.0', '0', '0', '?', 'Zs', '10:50', '1:00']
                # 3  ['rick', '14836', '42.2', '0.0', '0', '0', '?', 'Zs', '10:50', '0:30']
                # 4  ['rick', '15789', '0.0',  '0.0', '0', '0', '?', 'Zs', '10:50', '0:00']
                # 5  ['rick', '16969', '0.0',  '0.0', '21556', '3376', 'pts/27', 'Ss+', '10:51', '0:00']
                # external.kill_pid_running() ERROR: os.kill  failed for PID: 15789
                v1_print(" ", ll[:10])
                if float(ll[2]) > 10.0:  # CPU percentage > 10%?
                    v1_print("   PID:", ll[1], " | CPU usage over 10%:", ll[2])
                    high_pid_perc += 1  # Also has "?" instead of 'pts/99'
                elif ll[6] == "?":
                    v1_print("   PID:", ll[1], " | 'pts/99' == '?'.  Skipping...")
                    continue
                found_pids.append(ll)

        # If less than 5 pids and none > 10% skip AskQuestion()
        if len(found_pids) < 5 and high_pid_perc == 0:
            return

        ''' Found_pids have 12 results, 3 for each time view Bluetooth Devices is run:        
        [snip 4...]
        ['rick', '17229', '90.9', '0.0', '21556', '3344', 'pts/31', 'Rs+', '00:59', '0:28', 
            '/usr/bin/gatttool', '-i', 'hci0', '-I'], 
        [...snip 7] '''

        v3_print(_who, "self.win_grp BEFORE:")  # AskQuestion() win_grp debugging
        v3_print(self.win_grp.window_list)

        title = "GATTTool Jobs Discovered."
        text = str(len(found_pids)) + " instance(s) of GATTTool"
        text += " have been found.\n\n"
        if high_pid_perc:
            text += str(high_pid_perc) + " job(s) have high CPU percentage.\n\n"
        text += "Do you want to cancel the job(s)?\n"  # centered: \t breaks
        answer = message.AskQuestion(self, title, text, 'no',
                                     thread=self.Refresh, win_grp=self.win_grp)

        text += "\n\t\tAnswer was: " + answer.result
        v3_print(title, text)

        v3_print(_who, "self.win_grp AFTER :")  # AskQuestion() win_grp debugging
        v3_print(self.win_grp.window_list)

        if answer.result != 'yes':
            return  # Don't delete pids

        if found_inst and found_inst.device is not None:
            found_inst.Disconnect()  # started device's gatttool will be killed & lags
            # TODO: Update treeview with "?" power status like .setNight() & .setColor()
            if self.usingDevicesTreeview:
                cr = TreeviewRow(self)
                iid = cr.getIidForInst(found_inst)
                cr.Get(iid)
                if iid is not None:
                    resp = "?"
                    text = "  " + str(resp)
                    cr.tree.item(iid, text=text)
                    cr.tree.update_idletasks()
                else:
                    v0_print(_who, "Could not get devices treeview row.")

        for pid in found_pids:
            ext.kill_pid_running(int(pid[1]))
            # No way to kill <defunct> : https://askubuntu.com/a/201308/307523
            # So these jobs will commit suicide when homa.py ends:
            # $ ps ux | grep gatttool | grep -v grep
            # rick  7716 13.3  0.0 0 0 ? Zs 11:44 0:46 [gatttool] <defunct>
            # rick 13317  0.0  0.0 0 0 ? Zs 11:47 0:00 [gatttool] <defunct>

            # NOTE: After killing CPU percentage declines over time for <defunct>.
            # After 15 or 20 minutes the <defunct> start to disappear on their own.


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

        self.top = top  # 2025-01-13 top is not passed as argument???
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

    def getIidForInst(self, inst):
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
        """ Create default treeview row
            During startup / resume, BLE LED Light Strips require extra connect
        """

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
            # return  # 2025-01-12 need self.values defined

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
        elif type_code == GLO['BLE_LS']:  # Bluetooth Low Energy LED Light Strip
            photo = ImageTk.PhotoImage(Image.open("led_lights.jpg").resize((300, 180), Image.ANTIALIAS))
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

        # 2025-01-12 no instance
        if self.inst is None:
            status = "?"
            type_code = "?"
            name = "?"
        else:
            status = self.inst.powerStatus
            type_code = self.inst.type
            name = self.inst.name

        # Did program just start, or is power status already known?
        #if self.inst.powerStatus == "?":  # Initial boot  # 2025-01-12
        if status == "?":  # Initial boot
            self.text = "Wait..."  # Power status checked when updating treeview
        else:
            self.text = "  " + self.inst.powerStatus  # Power state already known
        #self.name_column = self.inst.name # 2025-01-12
        self.name_column = name  # 2025-01-12
        self.name_column += "\nIP: " + self.arp_dict['ip']
        self.attribute_column = self.arp_dict['alias']
        self.attribute_column += "\nMAC: " + self.arp_dict['mac']
        #self.attribute_column += "\n" + self.inst.type
        self.attribute_column += "\n" + type_code
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
        elif self.inst is not None:  # 2025-01-12 new error self.inst is None
            self.inst.getPower()
            text = "  " + self.inst.powerStatus
        else:
            text = " Error!"

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
            self.tree.after(10)  # 10 milliseconds


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
                    # 2025-01-26 noticed that "Video Fan" has returned and "fan3" gone.
                    parts[0] = "Video Fan"
                self.curr_sensor[parts[0]] = parts[1].strip()
                CheckFanChange(parts[0])  # Over 200 RPM change will be logged.
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
                if i == len(self.sensors_log) - 1:
                    # 2025-01-20 getting error flashing when last row not inserted yet
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
        iid = self.sensors_log[-1]['delta']  # delta is seconds since app started

        # iid is Number right justified 8 = 5 whole + decimal + 2 fraction
        trg_iid = "{0:>8.2f}".format(iid)  # E.G. iid = "2150.40" seconds
        trg_iid = str(trg_iid)  # 2025-01-19 strangely type is float today.

        try:
            _item = self.tree.item(trg_iid)
        except tk.TclError:
            v0_print("\n" + _who, "trg_iid not found: '" + trg_iid + "'",
                     " |", type(trg_iid))
            # SystemMonitor().FlashLastRow(): trg_iid not found: '20.04'
            #   | <type 'float'>
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
        # arp dictionary = {
        # "mac": mac, "ip": ip, "name": name, "alias": alias, "type_code": 99}
        v2_print("\nTest for device type using 'arp' dictionary:", arp)

        instance = ni.test_for_instance(arp)
        if len(instance) == 0:
            continue

        discovered.append(arp)  # Saved to disk

        # Get class instance information
        #instances.append({"mac": arp['mac'], "instance": inst})
        instances.append(instance)
        arp['type_code'] = instance['instance'].type_code
        view_order.append(arp['mac'])
        # Instance always rebuilt at run time and never saved to disk
        if update:
            ni.arp_dicts[i] = arp  # Update arp list

    return discovered, instances, view_order


v1_print("homa.py - trionesControl.trionesControl:", tc.__file__)
v1_print("homa.py - pygatt:", pygatt.__file__)
v1_print("homa.py - pygatt.exceptions:", pygatt.exceptions.__file__)

v1_print(sys.argv[0], "- Home Automation", " | verbose1:", p_args.verbose1,
         " | verbose2:", p_args.verbose2, " | verbose3:", p_args.verbose3,
         "\n  | fast:", p_args.fast, " | silent:", p_args.silent)

''' Global classes '''
root = None  # Tkinter toplevel
app = None  # Application GUI
cfg = sql.Config()  # Colors configuration SQL records
glo = Globals()  # Global variables
GLO = glo.dictGlobals  # global dictionary. Dummy, reset during main() glo.open_file().
ble = BluetoothLedLightStrip()  # Must follow GLO dictionary and before ni instance
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

    #glo.openFile()  2025-01-11 Moved to call before ni instance
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
        elif type_code == GLO['BLE_LS']:  # Bluetooth Low Energy LED Light Strip
            inst = BluetoothLedLightStrip(arp['mac'], arp['ip'], arp['name'], arp['alias'])
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
    global app, GLO
    global ni  # NetworkInformation() class instance used everywhere
    global SAVE_CWD  # Saved current working directory to restore on exit

    ''' Save current working directory '''
    SAVE_CWD = os.getcwd()  # Bad habit from old code in mserve.py
    if SAVE_CWD != g.PROGRAM_DIR:
        v1_print("Changing from:", SAVE_CWD, "to g.PROGRAM_DIR:", g.PROGRAM_DIR)
        os.chdir(g.PROGRAM_DIR)

    glo.openFile()
    GLO = glo.dictGlobals
    GLO['APP_RESTART_TIME'] = time.time()

    # 2025-01-18 Temporary declarations whilst dictionary recreated during development
    GLO['LED_LIGHTS_MAC'] = "36:46:3E:F3:09:5E"
    GLO['LED_LIGHTS_STARTUP'] = True  # Displayed as "0" (off), "1" (on), "?"
    GLO["RESUME_TEST_SECONDS"] = 30  # > x seconds disappeared means system resumed
    GLO["RESUME_DELAY_RESTART"] = 5  # Allow x seconds for network to come up

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
