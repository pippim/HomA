#!/usr/bin/python
# -*- coding: utf-8 -*-
# /usr/bin/python3
# /usr/bin/env python  # puts name "python" into top, not "homa.py"
"""
Author: pippim.com
License: GNU GPLv3. (c) 2024-2025
Source: This repository
Description: HomA - Home Automation - Main **homa** Python Module
"""

from __future__ import print_function  # Must be first import
from __future__ import with_statement  # Error handling for file opens
from __future__ import division  # integer division results in float
import warnings  # 'warnings' advises which methods aren't supported
warnings.filterwarnings("ignore", "ResourceWarning")  # PIL python 3 unclosed file

# ==============================================================================
#
#       homa.py (Home Automation) - Manage devices
#
#       2024-10-02 - Creation date.
#       2024-12-01 - Create GitHub repo. Add dropdown menus and Big Number Calc.
#       2025-01-08 - Create Bluetooth LED Light Strip support.
#       2025-02-10 - Support Python 3 shebang.
#       2025-03-26 - Auto assign iid in Sensors Treeview fixes duplicate keys.
#       2025-04-18 - Spam Sony TV Remote. Refresh from 16ms to 33ms for CPU %.
#       2025-05-28 - Enhanced error checking and reporting.
#       2025-06-13 - Convert wmctrl to Wnck used in monitor.py - mon.wn_list[].
#       2025-07-18 - Move DeviceCommonSelf and Globals classes to homa-common.py
#
# ==============================================================================

'''
    TODO: create DisplayArps(), DisplayHosts(), DisplayDevices()
    WIP: Volume Meters, PulseAudio sinks and volume levels for YT ad skipping    

    REQUIRES:
    
    python(3)-appdirs
    python(3)-xlib  # imported as Xlib.X
    python(3)-ttkwidgets  # Also stored as subdirectory in ~/HomA/ttkwidgets
    trionesControl   # Also stored as subdirectory in ~/HomA/ttkwidgets 
    gatttool   # Also stored as subdirectory in ~/HomA/ttkwidgets 
    audio   # Stored as subdirectory in ~/HomA/audio 
    pulsectl   # Stored as subdirectory in ~/HomA/pulsectl 

    xdotool  # To minimize window
    systemctl  # To suspend. Or suitable replacement like `suspend` external command
    adb  # Android debugging bridge for Google Android TV's
    curl  # For Sony Bravia KDL professional displays (TV's)
    bluez-tools  # For bluetooth communications including hci tools
    wmctrl  # Get list of windows. To be removed in favour of Wnck

    Gatttool REQUIRES:
    python(3)-serial

    2025-03-01 LONG TERM (3 tasks completed by 2025-06-17):
        TODO: Sensors: Add average CPU Mhz and Load %.
                       Add Top 20 programs with Top 3 displayed.
                       Consolidate fan and temperature changes per minute with
                        up / down arrows on trend for each temp and fan 
              Dimmer (movie.sh) features where wakeup is based on mouse
                passing over monitor for five seconds.
              xrandr monitor details - geometry & resolution.
              mmm features - track window geometry every minute.

'''

''' check configuration. '''
import inspect
import os
os.environ["SUDO_PROMPT"] = ""  # Remove prompt "[sudo] password for <USER>:"

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
import logging  # Logging used in pygatt and trionesControl
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
import base64  # Required for Cryptology
from cryptography.fernet import Fernet  # To encrypt sudo password
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

# Vendor libraries preinstalled in subdirectories (ttkwidgets not used)
import pygatt  # Bluetooth Low Energy (BLE) low-level communication
import pygatt.exceptions  # pygatt error messages also used by trionesControl
import trionesControl.trionesControl as tc  # Bluetooth LED Light pygatt wrapper

# Pippim libraries
import sql  # For color options - Lots of irrelevant mserve.py code though
import monitor  # Center window on current monitor supports multi-head rigs
import toolkit  # Various tkinter functions common to Pippim apps
import message  # For dtb (Delayed Text Box)
import image as img  # Image processing. E.G. Create Taskbar icon
import timefmt as tmf  # Time formatting, ago(), days(), mm_ss(), etc.
import vu_pulse_audio  # Volume Pulse Audio class pulsectl.Pulse()
import external as ext  # Call external functions, programs, etc.
import homa_common as hc  # hc.ValidateSudoPassword()
from calc import Calculator  # Big Number calculator
from homa_common import DeviceCommonSelf, Globals, AudioControl


class DeviceCommonSelf2:
    """ Common Variables used by NetworkInfo, SmartPlugHS100, SonyBraviaKdlTV,
        and TclGoogleTV device classes. Also used by Application() class.
    """

    def __init__(self, who):
        """ Variables used by all classes """

        self.who = who  # For debugging, print class name

        self.dependencies_installed = True  # Parent will call self.checkDependencies()
        self.passed_dependencies = []
        self.passed_installed = []

        self.app = None  # Every instance has reference to Application() instance

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

    def checkDependencies(self, dependencies, installed):
        """ :param dependencies: list of required dependencies.
            :param installed: empty list to be updated with installed flags.
            Sets self.dependencies_installed True ONLY if all are installed.
        """
        self.dependencies_installed = True
        self.passed_dependencies = dependencies  # shallow copy of dependencies
        self.passed_installed = installed  # copy of mutable installed flags
        for required in dependencies:
            if self.Which(required):
                installed.append(True)
            elif self.checkImport(required):
                installed.append(True)
            else:
                v0_print("Program:", required, "is required but is not installed")
                installed.append(False)
                self.dependencies_installed = False

    def checkInstalled(self, name):
        """ Check if external program is installed. Could use `self.Which` but this
            method is faster and allows for future help text. Requires previous call
            to `self.checkDependencies(dep_list, inst_list)`.

            :param name: name of external program to check.
            :returns: False if external program is missing. Otherwise return True
        """
        try:
            ndx = self.passed_dependencies.index(name)
        except IndexError:
            v1_print(self.who, "checkInstalled(): Invalid name passed:", name)
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

    def checkImport(self, name):
        """ Check if variable name can be imported """
        _who = self.who + "checkImport():"
        try:
            if name[-3:] == ".py":
                name = name[:-3]
                v3_print("new name:", name)
        except IndexError:
            pass  # not .py extension to strip

        try:
            _module = __import__(name)
            v3_print("module can be imported:", name, _module)
            return True
        except ImportError:
            v3_print("module not found!", name)
            return False
        
    def makePercentBar(self, percent):
        """ Make percentage bar of UTF-8 characters 0 to 100%
            Initial purpose is to spam volume level with `notify-send` as the TV
                remote control changes volume with + / - keys.
            Although Sony TV shows the volume percentage that doesn't help if
                TV picture is turned off and audio only is active.

            Copied from /mnt/e/bin/tvpowered bash script VolumeBar() function.
        """
        _who = self.who + "makePercentBar():"

        Arr = ["█", "▏", "▎", "▍", "▌", "▋", "▊", "█"]
        FullBlock = percent // len(Arr)
        Bar = Arr[0] * FullBlock

        PartBlock = percent % len(Arr)  # Size of partial block (array index)
        if PartBlock > 0:  # Add partial blocks Arr[1-7] (▏▎▍▌▋▊█)
            Bar += Arr[PartBlock]

        if FullBlock < 12:  # Add padding utf-8 (▒) when < 96% (12 full blocks)
            cnt = 12 - FullBlock if PartBlock else 13 - FullBlock
            Bar += "▒" * cnt

        return Bar

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
        self.cmdOutput = text.decode().strip()  # Python 3 uses bytes
        self.cmdError = err.decode().strip()
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


class Router(DeviceCommonSelf):
    """ Router isn't physically powered on/off. Network Service is started
        and stopped.
    """

    def __init__(self, mac=None, ip=None, name=None, alias=None):
        """ DeviceCommonSelf(): Variables used by all classes """
        DeviceCommonSelf.__init__(self, "Router().")  # Define self.who
        _who = self.who + "__init()__:"

        self.mac = mac  # a8:4e:3f:82:98:b2
        self.ip = ip  # 192.168.0.1
        self.name = name  # Hitronhub.home
        self.alias = alias  # Admin

        self.requires = ['nmcli', 'ifconfig', 'sudo', 'systemctl']
        self.installed = []
        self.checkDependencies(self.requires, self.installed)
        v2_print(self.who, "Dependencies:", self.requires)
        v2_print(self.who, "Installed?  :", self.installed)
        # When reading /etc/hosts match from MAC address if available
        # or Static IP address if MAC address not available.
        if self.name is None:
            self.name = ""  # Computer name from /etc/hosts
        if self.alias is None:
            self.alias = ""  # Computer alias from /etc/hosts

        self.type = "Router"
        self.type_code = GLO['ROUTER_M']

        self.ether_name = ""  # eth0, enp59s0, etc
        self.ether_mac = ""  # aa:bb:cc:dd:ee:ff
        self.ether_ip = ""  # 192.168.0.999
        self.wifi_name = ""  # wlan0, wlp60s0, etc
        self.wifi_mac = ""  # aa:bb:cc:dd:ee:ff
        self.wifi_ip = ""  # 192.168.0.999

        self.Interface()  # Initial values

    def Interface(self, forgive=False):
        """ Return name of interface that is up. Either ethernet first or
            wifi second. If there is no interface return blank.
        """

        _who = self.who + "Interface():"
        v2_print(_who, "Test if Ethernet and/or WiFi interface is up.")

        if not self.checkInstalled('nmcli'):
            return

        command_line_list = ["nmcli", "con", "show"]
        event = self.runCommand(command_line_list, _who, forgive=forgive)
        ''' $ nmcli con show
NAME                UUID                                  TYPE             DEVICE  
Wired connection 1  378122bb-ad44-3ddd-a616-c93e1bf0f828  802-3-ethernet   enp59s0 
SHAW-8298B0         61019051-72db-4fef-ae01-759f1b4dc568  802-11-wireless  --      
SHAW-8298B0-5G      bfce8167-18fc-4646-bec3-868c097a3f4a  802-11-wireless  -- '''

        if not event['returncode'] == 0:
            if forgive is False:
                v0_print(_who, "pipe.returncode:", pipe.returncode)
            return ""  # Return null string = False

        _interface = event['output'].splitlines()

        _name = _mac = _ip = ""
        self.ether_name = ""  # eth0, enp59s0, etc
        self.ether_mac = ""  # aa:bb:cc:dd:ee:ff
        self.ether_ip = ""  # 192.168.0.999
        self.wifi_name = ""  # wlan0, wlp60s0, etc
        self.wifi_mac = ""  # aa:bb:cc:dd:ee:ff
        self.wifi_ip = ""  # 192.168.0.999
        v3_print(_who, "self.ether_name:", self.ether_name, " | self.ether_mac:",
                 self.ether_mac, " | self.ether_ip:", self.ether_ip)
        v3_print(_who, "self.wifi_name :", self.wifi_name, " | self.wifi_mac :",
                 self.wifi_mac, " | self.wifi_ip :", self.wifi_ip)

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
        v2_print(_who, "Test if device is a Router:", self.ip)

        if forgive:
            pass

        if self.ip.endswith(".0.1") or self.ip.endswith(".1.1"):
            return True

        return False

    def turnOn(self, forgive=False):
        """ Simulate turning on router using:
            sudo systemctl start NetworkManager.service
        """
        _who = self.who + "turnOn():"
        v2_print(_who, "Turn On Router:", self.ip)

        if forgive:
            pass  # Dummy argument for uniform instance parameter list

        self.setPower("ON", forgive=forgive)
        return self.powerStatus

    def turnOff(self, forgive=False):
        """ Simulate turning off router using:
            sudo systemctl stop NetworkManager.service
        """
        _who = self.who + "turnOff():"
        v2_print(_who, "Turn Off Router:", self.ip)

        if forgive:
            pass  # Dummy argument for uniform instance parameter list

        self.setPower("OFF", forgive=forgive)
        return self.powerStatus

    def getPower(self, forgive=False):
        """ Return "ON", "OFF" or "?" """

        _who = self.who + "getPower():"
        v2_print(_who, "Test if router is powered on:", self.ip)

        if forgive:
            pass  # Dummy argument for uniform instance parameter list

        command_line_list = ["systemctl", "is-active", "--quiet", "NetworkManager.service"]
        event = self.runCommand(command_line_list, _who, forgive=forgive)

        self.powerStatus = "ON" if event['returncode'] == 0 else "OFF"  # status code 3
        #print(_who, "event['returncode']:", event['returncode'])
        return self.powerStatus

    def setPower(self, status, forgive=False):
        """ Set Laptop Display Backlight Power 'OFF' or 'ON'
            If forgive=True then don't report pipe.returncode != 0
        """

        _who = self.who + "setPower(" + status + "):"
        v2_print(_who, "Set Router Power to:", status)

        # Sudo password required for powering laptop backlight on/off
        if GLO['SUDO_PASSWORD'] is None:
            GLO['SUDO_PASSWORD'] = self.app.GetPassword()
            self.app.updateDropdown()
            if GLO['SUDO_PASSWORD'] is None:
                return "?"  # Cancel button (256) or escape or 'X' on window decoration (64512)

        if status == "ON":
            mode = "start"
        elif status == "OFF":
            mode = "stop"
        else:
            V0_print(_who, "Invalid status (not 'ON' or 'OFF'):", status)
            return

        # command "echo PASSWORD | sudo -S systemctl start NetworkManager.service"
        self.cmdStart = time.time()
        cmd1 = sp.Popen(['echo', GLO['SUDO_PASSWORD']], stdout=sp.PIPE)
        pipe = sp.Popen(['sudo', '-S', 'systemctl', mode, 'NetworkManager.service'],
                        stdin=cmd1.stdout, stdout=sp.PIPE, stderr=sp.PIPE)

        # Setup command event logger manually
        self.cmdCaller = _who
        who = self.cmdCaller + " logEvent():"
        self.cmdCommand = ["echo", "GLO['SUDO_PASSWORD']", "|", "sudo", "-S",
                           'systemctl', mode, "NetworkManager.service"]
        self.cmdString = ' '.join(self.cmdCommand)
        self.cmdOutput = pipe.stdout.read().decode().strip()
        self.cmdError = pipe.stdout.read().decode().strip()
        self.cmdReturncode = pipe.returncode
        self.cmdReturncode = 0 if self.cmdReturncode is None else self.cmdReturncode
        self.cmdDuration = time.time() - self.cmdStart
        self.logEvent(who, forgive=forgive, log=True)
        self.powerStatus = status


class Globals2(DeviceCommonSelf):
    """ Globals

        What could be in sql.py too complicated to document due to mserve.py

        - timeouts for adb, REST, resume, rediscover
        - colors for toplevel, taskbar icon, treeview, scrollbars

    """

    def __init__(self):
        """ Globals(): Global variables for HomA. Traditional "GLOBAL_VALUE = 1"
            is mapped to "self.dictGlobals['GLOBAL_VALUE'] = 1".

            Stored in ~/.local/share/homa/config.json

            After adding new dictionary field, remove the config.json file and
            restart HomA. Then a new default config.json file will created.

        """
        DeviceCommonSelf.__init__(self, "Globals().")  # Define self.who

        self.requires = ['ls']

        # Next four lines can be defined in DeviceCommonSelf.__init__()
        self.installed = []
        self.checkDependencies(self.requires, self.installed)
        v2_print(self.who, "Dependencies:", self.requires)
        v2_print(self.who, "Installed?  :", self.installed)

        command_line_list = ["ls", "/sys/class/backlight"]
        event = self.runCommand(command_line_list, self.who)

        if event['returncode'] != 0:
            backlight_name = ""  # Empty string for now
        else:
            backlight_name = event['output'].strip()
        #popen("")

        # Usage: glo = Globals()
        #        GLO = glo.dictGlobals
        #        GLO['APP_RESTART_TIME'] = time.time()
        self.dictGlobals = {
            "SONY_PWD": "123",  # Sony TV REST API password
            "CONFIG_FNAME": "config.json",  # Future configuration file.
            "DEVICES_FNAME": "devices.json",  # mirrors ni.mac_dicts[{}, {}, ... {}]
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
            "REFRESH_MS": 33,  # Refresh tooltip fades 30 frames per second
            "REDISCOVER_SECONDS": 60,  # Check for device changes every x seconds
            "RESUME_TEST_SECONDS": 30,  # > x seconds disappeared means system resumed
            "RESUME_DELAY_RESTART": 10,  # Allow x seconds for network to come up
            # Sony TV error # 1792. Initial 3 sec. March 2025 6 sec. April 2025 7 sec.
            # April 2025 new router slower try 10 sec.
            "SUNLIGHT_PERCENT": "/usr/local/bin/.eyesome-percent",  # file contains 0% to 100%

            "LED_LIGHTS_MAC": "",  # Bluetooth LED Light Strip MAC address
            "LED_LIGHTS_STARTUP": True,  # "0" turn off, "1" turn on.
            "LED_LIGHTS_COLOR": None,  # Last colorchooser ((r, g, b), #000000)
            "LED_RED+GREEN_ADJ": False,  # "1" override red+green mix with less green.
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
            "ROUTER_M": 200,  # Router Modem

            "SUDO_PASSWORD": None,  # Sudo password required for laptop backlight
            "BACKLIGHT_NAME": backlight_name,  # intel_backlight
            "BACKLIGHT_ON": "0",  # Sudo echo to "/sys/class/backlight/intel_backlight/bl_power"
            "BACKLIGHT_OFF": "4",  # ... will control laptop display backlight power On/Off.
            # Power all On/Off controls
            "POWER_OFF_CMD_LIST": ["systemctl", "suspend"],  # Run "Turn Off" for Computer()
            "POWER_ALL_EXCL_LIST": [100, 110, 120, 200],  # Exclude when powering "All"
            # to "ON" / "OFF" 100=DESKTOP, 110=LAPTOP_B, 120=LAPTOP_D, 200=ROUTER_M

            "TREEVIEW_COLOR": "WhiteSmoke",  # Treeview main color
            "TREE_EDGE_COLOR": "White",  # Treeview edge color 5 pixels wide
            "ALLOW_REMOTE_TO_SUSPEND": True,  # Sony getPower()
            "ALLOW_VOLUME_CONTROL": True,  # Sony getVolume() and setVolume()
            "QUIET_VOLUME": 20,  # 10pm - 9am
            "NORMAL_VOLUME": 36,  # Normal volume (9am - 10pm)

            "YT_AD_BAR_COLOR": "",  # YouTube Ad progress bar color
            "YT_AD_BAR_POINT": [],  # YouTube Ad progress bar start coordinates
            "YT_VIDEO_BAR_COLOR": "",  # YouTube Video progress bar color
            "YT_VIDEO_BAR_POINT": [],  # YouTube Ad progress bar start coordinates
            "YT_SKIP_BTN_COLOR": "",  # YouTube Skip Ad button dominant color (white)
            "YT_SKIP_BTN_POINT": []  # YouTube Skip Ad button coordinates (triangle tip)
        }

    def openFile(self):
        """ Read dictConfig from CONFIG_FNAME = "config.json"
            cp = Computer() instance must be created for cp.crypto_key.
        """
        _who = self.who + "openFile():"

        fname = g.USER_DATA_DIR + os.sep + GLO['CONFIG_FNAME']
        if not os.path.isfile(fname):
            return  # config.json doesn't exist

        with open(fname, "r") as fcb:
            v2_print("Opening configuration file:", fname)
            self.dictGlobals = json.loads(fcb.read())

        #print("GLO['LED_LIGHTS_COLOR']:", GLO['LED_LIGHTS_COLOR'])
        # Starts as a tuple json converts to list: [[44, 28, 27], u'#2c1c1b']
        try:
            s = self.dictGlobals['LED_LIGHTS_COLOR']
            self.dictGlobals['LED_LIGHTS_COLOR'] = \
                ((s[0][0], s[0][1], s[0][2]), s[1])
        except (TypeError, IndexError):  # No color saved
            self.dictGlobals['LED_LIGHTS_COLOR'] = None

        '''
        try:  # Delete bad key
            s = self.dictGlobals['YT_SKIP_BAR_COLOR']
            del self.dictGlobals['YT_SKIP_BAR_COLOR']
            del self.dictGlobals['YT_SKIP_BAR_POINT']
            self.dictGlobals["YT_SKIP_BTN_COLOR"] = ""
            self.dictGlobals["YT_SKIP_BTN_POINT"] = []
            v0_print("Deleted two bad keys YT_SKIP_BAR_COLOR / POINT")
        except (TypeError, IndexError, KeyError):  # No bad key
            pass
        '''
        ''' TEMPLATE TO ADD A NEW FIELD TO DICTIONARY  
        try:
            _s = self.dictGlobals['YT_AD_BAR_COLOR']
            v0_print("Found GLO['YT_AD_BAR_COLOR']:", _s)
        except KeyError:
            self.dictGlobals["YT_AD_BAR_COLOR"] = ""
            self.dictGlobals["YT_AD_BAR_POINT"] = []
            self.dictGlobals["YT_VIDEO_BAR_COLOR"] = ""
            self.dictGlobals["YT_VIDEO_BAR_POINT"] = []
            self.dictGlobals["YT_SKIP_BTN_COLOR"] = ""
            self.dictGlobals["YT_SKIP_BTN_POINT"] = []

            v0_print("Create GLO['YT_AD_BAR_COLOR']:", GLO['YT_AD_BAR_COLOR'])
        '''

        ''' Decrypt SUDO PASSWORD 
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
        '''
        # 2025-01-27 override REFRESH_MS for breatheColors() testing.
        #GLO['REFRESH_MS'] = 10  # Override 16ms to 10ms

    def saveFile(self):
        """ Save dictConfig to CONFIG_FNAME = "config.json"
            cp = Computer() instance must be created for cp.crypto_key.
            
            Called when exiting and after editing preferences for YT Ad Skip
            to get new coordinates right away.
        """
        _who = self.who + "saveFile():"

        """ 2025-07-17 Move out for support for yt-skip.py
        if GLO['SUDO_PASSWORD'] is not None:
            f = Fernet(cp.crypto_key)  # Encrypt sudo password when storing
            try:
                enc = f.encrypt(GLO['SUDO_PASSWORD'].encode())  # convert to bytes
                # Works first time in Python 3, but second time (after save & restart)
                # it generates attribute error below.
            except AttributeError:
                # AttributeError: 'bytes' object has no attribute 'encode'
                #v0_print(_who, "AttributeError: 'bytes' object has no attribute 'encode'")
                enc = f.encrypt(GLO['SUDO_PASSWORD'])  # already in bytes
            if PYTHON_VER == "3":
                # noinspection SpellCheckingInspection
                '''
                Fix issue with `bytes` being used in encryption under python 3:
                    TypeError: b'gAAAAABnqjSvXmfPODPXGfmBcnRnas4oI22xMbKxTP-JZGA-6
                    -819AmJoV7kEh59d-RnKLK2HZVGwb3YppZsvgzOZcUZDsZmAg==' 
                    is not JSON serializable
                
                See: https://stackoverflow.com/a/40060181/6929343
                '''
                GLO['SUDO_PASSWORD'] = enc.decode('utf8').replace("'", '"')
            else:  # In Python 2 a string is a string, not bytes
                GLO['SUDO_PASSWORD'] = enc
       """
        # Override global dictionary values for saving
        hold_log = GLO['LOG_EVENTS']
        hold_error = GLO['EVENT_ERROR_COUNT'] 
        GLO['LOG_EVENTS'] = True  # Don't want to store False value
        GLO['EVENT_ERROR_COUNT'] = 0  # Don't want to store last error count

        with open(g.USER_DATA_DIR + os.sep + GLO['CONFIG_FNAME'], "w") as fcb:
            fcb.write(json.dumps(self.dictGlobals))

        GLO['LOG_EVENTS'] = hold_log  # Restore after Save Preferences. Not
        GLO['EVENT_ERROR_COUNT'] = hold_error  # required when exiting.

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
             "device code types excluded on resume."),
            ("YouTube",
             "YouTube Ad Mute and Skip controls.\n"
             "Colors and coordinates for the Ad and Video\n"
             "progress bars and the Skip Ad button in YouTube.")
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
        # 0=Hidden, 1=Sony, 2=TCL, 3=SmartPlug, 4=LED, 5=Misc, 6=Refresh, 7=Computer
        listFields = [
            # name, tab#, ro/rw, input as, stored as, width, decimals, min, max,
            #   edit callback, tooltip text
            ("SONY_PWD", 1, RW, STR, STR, 10, DEC, MIN, MAX, CB,
             "Password for Sony REST API"),
            ("ALLOW_REMOTE_TO_SUSPEND", 1, RW, BOOL, BOOL, 2, DEC, MIN, MAX, CB,
             "When Sony TV is powered off with the TV\n"
             "remote control, the system is suspended."),
            ("ALLOW_VOLUME_CONTROL", 1, RW, BOOL, BOOL, 2, DEC, MIN, MAX, CB,
             "Monitor Sony TV volume levels and set to\n"
             "quiet volume or normal volume on restart."),
            ("QUIET_VOLUME", 1, RW, INT, INT, 3, DEC, 5, 80, CB,
             "Audio System volume level between\n10pm and 9am (20:00 and 9:00)"),
            ("NORMAL_VOLUME", 1, RW, INT, INT, 3, DEC, 5, 80, CB,
             "Audio System volume level between\n9am and 10:00pm (9:00 and 20:00)"),
            # Timeouts improve incorrect device communication performance
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
            ("REDISCOVER_SECONDS", 6, RW, INT, INT, 5, DEC, MIN, MAX, CB,
             "Check devices changes every x seconds"),
            ("RESUME_TEST_SECONDS", 6, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "> x seconds disappeared means system resumed"),
            ("RESUME_DELAY_RESTART", 6, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "Pause x seconds after resuming from suspend"),
            ("LED_LIGHTS_MAC", 4, RW, MAC, STR, 17, DEC, MIN, MAX, CB,
             "Bluetooth Low Energy LED Light Strip address"),
            ("LED_LIGHTS_STARTUP", 4, RW, BOOL, BOOL, 2, DEC, MIN, MAX, CB,
             "LED Lights Turn On at startup? True/False"),
            ("LED_LIGHTS_COLOR", 4, RO, STR, STR, 20, DEC, MIN, MAX, CB,
             'LED Lights last used color.\nFormat: (red, green, blue) #9f9f9f"]'),
            ("LED_RED+GREEN_ADJ", 4, RW, BOOL, BOOL, 2, DEC, MIN, MAX, CB,
             "When LED Red and Green are mixed together,\n"
             "boost Red by 50% and reduce Green by 50%."),
            ("BLUETOOTH_SCAN_TIME", 4, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             'Number of seconds to perform bluetooth scan.\n'
             'A longer time may discover more devices.'),
            ("SUNLIGHT_PERCENT", 4, RW, FNAME, STR, 32, DEC, MIN, MAX, CB,
             'Pippim Eyesome sunlight percentage filename.\n'
             'Or any filename containing "0%" to "100%",\n'
             '(without the quotes) on the first line.'),
            ("TIMER_SEC", 5, RW, INT, INT, 6, DEC, MIN, MAX, CB,
             "Tools Dropdown Menubar - Countdown Timer default"),
            ("TIMER_ALARM", 5, RW, FNAME, STR, 30, DEC, MIN, MAX, CB,
             ".wav sound file to play when timer ends."),
            ("LOG_EVENTS", 0, HD, BOOL, BOOL, 2, DEC, MIN, MAX, CB,
             "Override runCommand events'\nlogging and --verbose3 printing"),
            ("EVENT_ERROR_COUNT", 0, HD, INT, INT, 9, 0, MIN, MAX, CB,
             "To enable/disable View Dropdown menu 'Discovery errors'"),
            ("SENSOR_CHECK", 5, RW, FLOAT, FLOAT, 7, DEC, MIN, MAX, CB,
             "Check `sensors`, CPU/GPU temperature\nand Fan speeds every x seconds."
             "\nTo skip sensor checks, set value to 0."),
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
            ("CONFIG_FNAME", 6, RO, STR, STR, WID, DEC, MIN, MAX, CB,
             "Configuration filename"),
            ("DEVICES_FNAME", 6, RO, STR, STR, WID, DEC, MIN, MAX, CB,
             "discovered network devices filename"),
            ("VIEW_ORDER_FNAME", 6, RO, STR, STR, WID, DEC, MIN, MAX, CB,
             "Network Devices Treeview display order filename"),
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
             "Router connecting local network to global internet"),
            ("YT_AD_BAR_COLOR", 8, RW, STR, STR, 9, DEC, MIN, MAX, CB,
             "YouTube Ad progress bar color"),
            ("YT_AD_BAR_POINT", 8, RW, STR, LIST, 30, DEC, MIN, MAX, CB,
             "YouTube Ad progress bar start coordinates"),
            ("YT_VIDEO_BAR_COLOR", 8, RW, STR, STR, 9, DEC, MIN, MAX, CB,
             "YouTube video progress bar color"),
            ("YT_VIDEO_BAR_POINT", 8, RW, STR, LIST, 30, DEC, MIN, MAX, CB,
             "YouTube video progress bar start coordinates"),
            ("YT_SKIP_BTN_COLOR", 8, RW, STR, STR, 9, DEC, MIN, MAX, CB,
             "YouTube Skip Ad button dominant color"),
            ("YT_SKIP_BTN_POINT", 8, RW, STR, LIST, 30, DEC, MIN, MAX, CB,
             "YouTube Skip Ad button coordinates (triangle right tip)")
        ]

        help_id    = "https://www.pippim.com/programs/homa.html#"  # same as g.HELP_URL
        help_tag   = "EditPreferences"
        help_text  = "Open a new window in your default web browser for\n"
        help_text += "explanations of fields in this Preferences Tab."
        listHelp   = [help_id, help_tag, help_text]

        return listTabs, listFields, listHelp

    def getDescription(self, key):
        """ return description matching dictionary key """
        listTabs, listFields, listHelp = self.defineNotebook()
        for field in listFields:
            if field[0] == key:
                return field[10]

        v0_print("Catastrophic error. Key doesn't exist:", key)

    def updateGlobalVar(self, key, new_value):
        """ Validate a new dictionary field. """
        _who = self.who + "updateGlobalVar():"
        _listTabs, listFields, _listHelp = self.defineNotebook()
        for atts in listFields:
            if atts[0] == key:
                break
        else:
            v0_print(_who, "Bad key passed:", key, new_value)
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


class Computer(DeviceCommonSelf):
    """ Computer (from ifconfig, iwconfig, socket, /etc/hosts (NOT in arp))

        Read chassis type. If laptop there are two images - laptop_b (base)
        and laptop_d (display) which is akin to a monitor / tv with extra
        features. If a computer (not a laptop) then use one image.

        All desktops and laptops have Ethernet. The ethernet MAC address
        is used to identify the computer in mac_dicts dictionaries.

        All laptops have WiFi. The WiFi MAC address is used to identify
        the laptop display in mac_dicts dictionaries.

        A desktop with ethernet and WiFi will only have it's ethernet
        MAC address stored in mac_dicts dictionaries.

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

        self.requires = ['ip', 'getent', 'hostnamectl', 'gsettings',
                         'get-edid', 'parse-edid', 'xrandr']
        self.installed = []
        self.checkDependencies(self.requires, self.installed)
        v2_print(self.who, "Dependencies:", self.requires)
        v2_print(self.who, "Installed?  :", self.installed)

        self.chassis = ""  # "desktop", "laptop", "convertible", "server",
        # "tablet", "handset", "watch", "embedded", "vm" and "container"

        if self.checkInstalled('hostnamectl'):
            # 2024-12-16 TODO: convert to self.runCommand()
            #   universal_newlines: https://stackoverflow.com/a/38182530/6929343
            # 2024-12-16 TODO: convert to self.runCommand()
            machine_info = sp.check_output(
                ["hostnamectl", "status"], universal_newlines=True)
            m = re.search('Chassis: (.+?)\n', machine_info)
            self.chassis = m.group(1)  # TODO: Use this for Dell Virtual temp/fan driver
        else:
            self.chassis = "desktop"  # "desktop", "laptop", "convertible", "server",
            # "tablet", "handset", "watch", "embedded", "vm" and "container"

        if self.chassis == "laptop":
            if self.name is not None:  # self.name can be passed as None
                self.name += " (Base)"  # There will be two rows, the other is ' (Display)'
            self.type = "Laptop Computer"
            self.type_code = GLO['LAPTOP_B']
        else:
            self.type = "Desktop Computer"
            self.type_code = GLO['DESKTOP']
        v2_print(self.who, "chassis:", self.chassis, " | type:", self.type)

        # /etc/hosts is read for alias matching on MAC address if available
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

        # noinspection SpellCheckingInspection
        ''' `socket` doesn't serve any useful purpose
        import socket
        _socks = [i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None)]
        v0_print("socks:", _socks)  
        # socks: ['127.0.1.1', '127.0.1.1', '127.0.1.1',
        # '192.168.0.12', '192.168.0.12', '192.168.0.12',
        # '192.168.0.10', '192.168.0.10', '192.168.0.10']
        '''

        self.Interface()  # Initial values using `ip a show dynamic`

        self.crypto_key = self.generateCryptoKey()
        v3_print(_who, "BEFORE self.crypto_key:", self.crypto_key, "\n  length:",
                 len(self.crypto_key), type(self.crypto_key))
        b = bytearray()
        ''' Convert string to bytes
            Python2:
                s = "ABCD"
                b = bytearray()
                b.extend(s)
            Python3:
                s = "ABCD"
                b = bytearray()
                b.extend(map(ord, s)) '''
        b.extend(self.crypto_key)
        self.crypto_key = b
        v3_print(_who, " AFTER self.crypto_key:", self.crypto_key, "\n  length:",
                 len(self.crypto_key), type(self.crypto_key))
        self.getNightLightStatus()

    def Interface(self, forgive=False):
        """ Return name of interface that is up. Either ethernet first or
            wifi second. If there is no interface return blank.
        """

        _who = self.who + "Interface():"
        v2_print(_who, "Test if Ethernet and/or WiFi interface is up.")

        name = mac = ip = ""
        self.ether_name = ""  # eth0, enp59s0, etc
        self.ether_mac = ""  # aa:bb:cc:dd:ee:ff
        self.ether_ip = ""  # 192.168.0.999
        self.wifi_name = ""  # wlan0, wlp60s0, etc
        self.wifi_mac = ""  # aa:bb:cc:dd:ee:ff
        self.wifi_ip = ""  # 192.168.0.999

        if not self.checkInstalled('ip'):
            return ""  # Return null string = False

        command_line_list = ["ip", "a", "show", "dynamic"]
        event = self.runCommand(command_line_list, _who, forgive=forgive)

        if not event['returncode'] == 0:
            if forgive is False:
                v0_print(_who, "pipe.returncode:", pipe.returncode)
            return ""  # Return null string = False

        interface = event['output'].splitlines()

        # noinspection SpellCheckingInspection
        ''' CONCISE ALL METHOD: $ ip a show dynamic
2: enp59s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 28:f1:0e:2a:1a:ed brd ff:ff:ff:ff:ff:ff
    inet 192.168.0.12/24 brd 192.168.0.255 scope global dynamic enp59s0
       valid_lft 588250sec preferred_lft 588250sec
3: wlp60s0: <BROADCAST,MULTICAST> mtu 1500 qdisc mq state DOWN group default qlen 1000
    link/ether 9c:b6:d0:10:37:f7 brd ff:ff:ff:ff:ff:ff
        '''

        def tally_found():
            """ Process last group of name, mac and ip """
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
            if len(parts) == 3:  # Heading line "9: NAME: blah blah blah"
                if not name == "":  # First time skip blank name
                    tally_found()
                name = parts[1].strip()
                mac = ip = ""
                continue

            if not mac:  # First detail line has MAC address
                r = re.search("(?:[0-9a-fA-F]:?){12}", line)
                if r:
                    mac = r.group(0)

            elif not ip:  # Optional second detail line has IP address
                r = re.search("[0-9]+(?:\.[0-9]+){3}", line)
                if r:
                    ip = r.group(0)

        tally_found()  # Process last group of interface lines fields found.

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
        v2_print(_who, "Test if device is a Computer:", self.ip)

        if forgive:
            pass

        if self.ip == self.ether_ip or self.ip == self.wifi_ip:
            return True

        return False

    def turnOn(self, forgive=False):
        """ Not needed because computer is always turned on. Defined for
            right click menu conformity reasons.
        """
        _who = self.who + "turnOn():"
        v2_print(_who, "Turn On Computer:", self.ip)

        if forgive:
            pass

        self.powerStatus = "ON"  # Can be "ON", "OFF" or "?"
        return self.powerStatus  # Really it is "AWAKE"

    def turnOff(self, forgive=False):
        """ Turn off computer with GLO['POWER_OFF_CMD_LIST'] which contains:
                systemctl suspend

            Prior to calling cp.turnOff(), Application().turnOff() calls
            turnAllPower("OFF") to turn off all other devices. If rebooting, rather
            than suspending, then devices are left powered up.

            If Dell BIOS "Fan Performance Mode" is turned on suspend can fail.

        """
        _who = self.who + "turnOff():"
        v2_print(_who, "Turn Off Computer:", self.ip)

        if forgive:
            pass

        command_line_list = GLO['POWER_OFF_CMD_LIST']  # systemctl suspend
        v1_print(_who, ext.ch(), "Suspend command:", command_line_list)
        _event = self.runCommand(command_line_list, _who, forgive=forgive)
        # NOTE: this point is still reached because suspend pauses a bit
        # v0_print(_who, ext.ch(), "Command finished.")
        # Computer().turnOff(): 13:27:45.472045 Suspend command: ['systemctl', 'suspend']
        # Computer().turnOff(): 13:27:45.551357 Command finished.

        self.powerStatus = "OFF"  # Can be "ON", "OFF" or "?"
        return self.powerStatus  # Really it is "SLEEP"

    def getPower(self, forgive=False):
        """ The computer is always "ON" """

        _who = self.who + "getPower():"
        v2_print(_who, "Test if computer is powered on:", self.ip)

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

        #return base64.urlsafe_b64encode(key[:32])  # Python 2
        return base64.urlsafe_b64encode(key[:32].encode('utf-8'))  # Python 3

    def getNightLightStatus(self, forgive=False):
        """ Return "ON" if night or "OFF" if daytime

            Run `gsettings get org.gnome.settings-daemon.plugins.color`
            Returns: 'night-light-enabled=True' - nighttime
                     'night-light-enabled=False' - daytime
                     error code - GNOME Nightlight not installed

            Percent found in GLO['SUNLIGHT_PERCENT'] containing '0 %' to '100 %'.
            if percent < 100 then Nightlight is "ON". As of 2025-05-18,
            GLO['SUNLIGHT_PERCENT'] = '/usr/local/bin/.eyesome-percent'

            Percentage is also used for sunlight boost in LED breathe colors

            If Nightlight is "ON" then, resume and startup will turn on bias lights

        """

        _who = self.who + "getNightLightStatus():"
        v2_print(_who, "Test if GNOME Night Light is active:", self.ip)

        if forgive:
            pass

        self.nightlight_active = True  # Default is nighttime to turn on lights.
        self.sunlight_percent = 0  # Percentage of sunlight, 0 = nighttime.

        if self.checkInstalled('gsettings'):
            command_line_list = ["gsettings", "get",
                                 "org.gnome.settings-daemon.plugins.color",
                                 "night-light-enabled"]
            command_line_str = ' '.join(command_line_list)
            pipe = sp.Popen(command_line_list, stdout=sp.PIPE, stderr=sp.PIPE)
            text, err = pipe.communicate()  # This performs .wait() too

            v3_print(_who, "Results from '" + command_line_str + "':")
            # 2025-02-09 add .decode() for Python 3
            v3_print(_who, "text: '" + text.decode().strip() + "'")
            v3_print(_who, "err: '" + err.decode().strip() + "'  | pipe.returncode:",
                     pipe.returncode)

            if pipe.returncode == 0:
                # GNOME Nightlight is installed and gsettings was found
                night_light = text.strip()
                if night_light == "True":
                    return "ON"
                elif night_light == "False":
                    self.nightlight_active = False
                    self.sunlight_percent = 100  # LED light sunlight percentage boost
                    return "OFF"
                else:
                    v1_print(_who, "night_light is NOT 'True' or 'False':", night_light)
                    return "ON"
        else:
            pass  # if no `gsettings` then no GNOME Nightlight

        # GNOME Nightlight is not running. Check if eyesome is running.
        fname = GLO['SUNLIGHT_PERCENT']
        if not os.path.isfile(fname):
            v0_print(_who, GLO['SUNLIGHT_PERCENT'], "file not found.")
            return "ON"  # Default to always turn bias lights on

        text = ext.read_into_string(fname)
        text = text.rstrip("\n") if text else ""  # Sometimes 'OFF\n'
        v3_print("\n" + _who, "SUNLIGHT_PERCENT string:", text, "\n")

        try:
            percent_str = text.split("%")[0]  # If no "%" gets all text
        except IndexError:
            v0_print(_who, GLO['SUNLIGHT_PERCENT'], "line 1 missing '%' character:",
                     "'" + text + "'.")
            return "ON"  # Default to always turn bias lights on

        if percent_str is None:
            v0_print(_who, GLO['SUNLIGHT_PERCENT'], "Invalid text file:",
                     "'" + text + "'.")
            return "ON"

        try:
            percent = int(percent_str)
            v3_print(_who, "eyesome percent:", percent)
            self.sunlight_percent = percent  # LED light sunlight percentage boost
            if percent == 100:
                self.nightlight_active = False
                return "OFF"  # = '100 %' sunlight
        except ValueError:
            v0_print(_who, "eyesome percent VALUE ERROR",
                     "'percent_str': '" + percent_str + "'.")

        self.nightlight_active = True
        return "ON"  # Default to always turn bias lights on


class NetworkInfo(DeviceCommonSelf):
    """ Network Information from arp and getent (/etc/hosts)


        ni = NetworkInfo() called on startup
        rd = NetworkInfo() rediscovery called every minute

        LISTS
        self.arp_results Devices from `arp -a`
        self.hosts       Devices from `getent hosts`
        self.host_macs   Optional MAC addresses at end of /etc/hosts
        self.view_order  Treeview list of MAC addresses

        LISTS of DICTIONARIES
        self.device_dicts First time discovered, thereafter read from disk
        self.instances    TclGoogleAndroidTV, SonyBraviaKdlTV, etc. instances

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
        self.checkDependencies(self.requires, self.installed)
        v2_print(self.who, "Dependencies:", self.requires)
        v2_print(self.who, "Installed?  :", self.installed)

        self.last_row = ""  # used by rediscovery processing one row at a time

        # Create self.arp_results from arp
        v3_print("\n===========================  arp -a  ===========================")
        # Format: 'SONY.LAN (192.168.0.19) at ac:9b:0a:df:3f:d9 [ether] on enp59s0'
        self.arp_results = []
        command_line_list = ["arp", "-a"]
        event = self.runCommand(command_line_list, _who)

        if event['returncode'] != 0:
            devices = []  # Empty list for now
        else:
            devices = event['output'].split("\n")

        for device in devices:
            self.arp_results.append(device)
            v3_print(device, end="")

        # Create self.hosts from /etc/hosts
        v3_print("\n========================  getent hosts  ========================")
        # Format: '192.168.0.19    SONY.LAN Sony Bravia KDL TV Ethernet  ac:9b:0a:df:3f:d9'
        self.hosts = []
        command_line_list = ["getent", "hosts"]
        event = self.runCommand(command_line_list, _who)

        if event['returncode'] != 0:
            hosts = []  # Empty list for now
        else:
            hosts = event['output'].split("\n")
        for host in hosts:
            self.hosts.append(host)
            v3_print(host, end="")

        # Read self.hosts (/etc/hosts) to get alias to assign device/arps
        v3_print("\n=========================  host MACs  ==========================")
        v3_print("MAC address".ljust(18), "IP".ljust(14), "Name".ljust(15), "Alias\n")
        # get mac addresses: https://stackoverflow.com/a/26892371/6929343
        import re
        p = re.compile(r'(?:[0-9a-fA-F]:?){12}')  # regex MAC Address
        self.host_macs = []
        for host in self.hosts:
            # 192.168.0.16    SONY.WiFi android-47cdabb50f83a5ee 18:4F:32:8D:AA:97
            parts = host.split()
            name = parts[1]  # SONY.WiFi
            alias = ' '.join(parts[2:-1])  # android-47cdabb50f83a5ee
            ip = parts[0]  # 192.168.0.16

            result = re.findall(p, host)  # regex MAC Address
            if result:  # MAC found
                # result = ['47cdabb50f83', '18:4F:32:8D:AA:97']
                mac = str(result[-1])  # Last entry = '18:4F:32:8D:AA:97'

                # Assign cp = Computer() instance attributes
                if mac == cp.ether_mac or mac == cp.wifi_mac:
                    cp.name = name  # computer name
                    cp.alias = alias  # computer alias
                    if mac == cp.ether_mac and cp.ether_ip == "":
                        v3_print("Assigning cp.ether_ip:", ip)
                        cp.ether_ip = ip
                    if mac == cp.wifi_mac and cp.wifi_ip == "":
                        v3_print("Assigning cp.wifi_ip:", ip)
                        cp.wifi_ip = ip

            else:  # No MAC (result = None)
                mac = "No MAC for: " + ip

                # Assign cp = Computer() instance attributes
                if ip == cp.ether_ip or ip == cp.wifi_ip:
                    cp.name = name  # computer name
                    cp.alias = alias  # computer alias
                    if cp.ether_ip == "":
                        cp.ether_ip = ip  # Can be overridden by MAC later
                    if cp.wifi_ip == "":
                        cp.wifi_ip = ip  # Can be overridden by MAC later

            host_mac = mac + "  " + ip.ljust(15) + name.ljust(16) + alias
            v3_print(host_mac)
            #host_dict = {"mac": mac, "ip": ip, "name": name, "alias": alias}
            # 2024-10-14 - Future conversion from host_mac to host_dict
            self.host_macs.append(host_mac)

        # Append self.arp_results with Computer() attributes
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
        self.arp_results.append(device)
        v3_print(device, end="")
        #print(device)

        # Add optional laptop WiFi that arp never reports when Wired connection
        if cp.chassis == "laptop":
            ip = cp.wifi_ip
            if not ip:
                ip = "Unknown"
            device = cp.name + " (" + ip + ") at "
            device += cp.wifi_mac + " [ether] on " + cp.wifi_name
            # TODO change device when connected to WiFi
            self.arp_results.append(device)
            v3_print("\n" + device, end="")
            #print(device)

        v3_print("\n=========================  arp MACs  ===========================")
        v3_print("MAC address".ljust(18), "IP".ljust(14), "Name".ljust(15), "Alias\n")
        self.mac_dicts = []  # First time discovered, thereafter read from disk
        self.instances = []  # TclGoogleAndroidTV, SonyBraviaKdlTV, etc. instances
        self.view_order = []  # Sortable list of MAC addresses matching instances
        for device in self.arp_results:
            # e.g. "SONY.light (192.168.0.15) at 50:d4:f7:eb:41:35 [ether] on enp59s0"
            parts = None
            try:
                parts = device.split()
                name = parts[0]  # Can be "unknown" when etc/self.hosts has no details
                ip = parts[1][1:-1]
                mac = parts[3]
                alias = self.get_alias(mac)
            except IndexError:  # name = parts[0] ERROR
                v0_print(_who, "List index error: '" + str(parts) + "'.")
                name = ip = mac = alias = "N/A"

            v3_print(_who, mac + "  " + ip.ljust(15) + name.ljust(16) + alias)
            mac_dict = {"mac": mac, "ip": ip, "name": name, "alias": alias}
            self.mac_dicts.append(mac_dict)

        # Add fake arp dictionary for Bluetooth LED Light Strip
        v2_print("len(GLO['LED_LIGHTS_MAC']):", len(GLO['LED_LIGHTS_MAC']))  # 0 ???
        if len(GLO['LED_LIGHTS_MAC']) == 17:
            # When changing below, remove devices.json file to rebuild it.
            fake_dict = {"mac": GLO['LED_LIGHTS_MAC'],
                         "ip": "irrelevant",
                         "name": "Bluetooth LED",
                         "alias": "Bluetooth LED Light Strip"}
            self.mac_dicts.append(fake_dict)
            v3_print("fake_dict:", fake_dict)

        v2_print(_who, "mac_dicts:", self.mac_dicts)  # 2024-11-09 now has Computer()
        v2_print(_who, "instances:", self.instances)  # Empty list until discovery
        v2_print(_who, "view_order:", self.view_order)  # Empty list until discovery
        v2_print(_who, "cp.ether_name:", cp.ether_name,  " | cp.ether_mac:",
                 cp.ether_mac,  " | cp.ether_ip:", cp.ether_ip)
        # name: enp59s0  | mac: 28:f1:0e:2a:1a:ed  | ip: 192.168.0.12
        v2_print(_who, "cp.wifi_name :", cp.wifi_name, " | cp.wifi_mac :",
                 cp.wifi_mac, " | cp.wifi_ip :", cp.wifi_ip)
        # name : wlp60s0  | mac : 9c:b6:d0:10:37:f7  | ip : 192.168.0.10

    def adb_reset(self, background=False):
        """ Kill and restart ADB server. Takes 3 seconds so run in background 
            TV may give a message like:
            
            If problems revoke USB, turn off USB debugging, click build 7 times
            RSA key fingerprint: a7:ad:1f:82:66:16:15:eb:bc:54:85:56:ce:ad:d4:2b
            ~/.android/adb key.pub - holds a lot more complicated key 700+ characters
            
        """
        _who = self.who + "adb_reset():"

        command_line_list = \
            ["adb", "kill-server", "&&", "adb", "start-server", "&&", 
             "adb", "devices", "-l"]
        if background:
            command_line_list.append("&")  # Has no effect in runCommand()

        command_line_str = ' '.join(command_line_list)

        if self.checkInstalled('adb'):
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
        """ Make temporary file with optional text. - NOT USED
            Caller must call os.remove(temp_fname)
            :returns: temp_fname (temporary filename E.G. /run/user/1000/homa.XXXXXXXX)
        """
        _who = self.who + "make_temp_file():"

        # Create temporary file in RAM for curl command
        tmpdir = g.TEMP_DIR.rstrip(os.sep)
        command_line_list = ["mktemp", "--tmpdir=" + tmpdir, "homa.XXXXXXXX"]
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

    def curl(self, JSON_str, subsystem, ip, rid="0", forgive=False):
        """ Use sub-process curl to communicate with REST API
            2024-10-21 - Broken for Sony Picture On/Off and Sony On/Off.
                Use os_curl instead to prevent error message:
                     {'error': [403, 'Forbidden']}
        """
        # noinspection PyProtectedMember
        _who = self.who + sys._getframe(1).f_code.co_name + "().curl():"
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
            # 2025-04-12 - Missing key/value: {"id": 99}
            if forgive:
                v1_print(_who, "event['returncode']:", event['returncode'])
            else:
                v0_print(_who, "event['returncode']:", event['returncode'])
            return {"result": [{"status": event['returncode'], 'id': rid}]}

        try:
            reply_dict = json.loads(str(event['output']))  # str to convert from bytes
        except ValueError:
            v0_print(_who, "Invalid 'output':", event['output'])
            # 2025-05-28 Add 'id' dictionary expected by checkReply() method.
            reply_dict = {"result": [{'status': '"' + _who +
                                                ' json.loads(event[output]) failed!"',
                                     'id': rid}]}

        v3_print(_who, "reply_dict:", reply_dict)
        return reply_dict

    def os_curl(self, JSON_str, subsystem, ip, rid="0", forgive=False):
        """ Use os.popen curl to communicate with REST API
            2024-10-21 - os_curl supports Sony Picture On/Off using os.popen(). When
                using regular ni.curl() Sony REST API returns {"error": 403}
        """
        # noinspection PyProtectedMember
        _who = self.who + sys._getframe(1).f_code.co_name + "().os_curl():"

        self.cmdCaller = _who  # self.cmdXxx vars in DeviceCommonSelf() class
        self.cmdStart = time.time()
        self.cmdCommand = [
            'timeout', str(GLO['CURL_TIME']), 'curl',
            '-s', '-H', '"Content-Type: application/json; charset=UTF-8"',
            '-H', '"X-Auth-PSK: ' + GLO['SONY_PWD'] + '"', '--data', "'" + JSON_str + "'",
            'http://' + ip + '/sony/' + subsystem
        ]
        self.cmdString = ' '.join(self.cmdCommand)  # 2025-05-28 shorter
        #self.cmdString = 'timeout ' + str(GLO['CURL_TIME']) + ' curl' +\
        #    ' -s -H "Content-Type: application/json; charset=UTF-8" ' +\
        #    ' -H "X-Auth-PSK: ' + GLO['SONY_PWD'] + '" --data ' + "'" + JSON_str + "'" +\
        #    ' http://' + ip + '/sony/' + subsystem

        ''' run command with os.popen() because sp.Popen() fails on ">" '''
        f = os.popen(self.cmdString + " 2>&1")
        text = f.read().splitlines()
        returncode = f.close()  # https://stackoverflow.com/a/70693068/6929343
        returncode = 0 if returncode is None else returncode  # Added 2025-05-28
        v3_print(_who, "text:", text)

        ''' log event and v3_print debug lines '''
        self.cmdOutput = "" if returncode != 0 else text
        self.cmdError = "" if returncode == 0 else text
        self.cmdReturncode = returncode
        self.cmdDuration = time.time() - self.cmdStart
        who = self.cmdCaller + " logEvent():"
        self.logEvent(who, forgive=forgive, log=True)

        #if returncode is not None:  # Changed 2025-05-28
        if returncode:  # Added 2025-05-28
            if forgive:
                v1_print(_who, "text:")
                v1_print(" ", text)  # string, list
                v1_print(_who, "returncode:", returncode)
            else:
                v0_print(_who, "text:")
                v0_print(" ", text)  # string, list
                v0_print(_who, "returncode:", returncode)
            # 2025-05-28 Add 'id' dictionary expected by checkReply() method.
            return {'result': [{'status': '"' + _who + ' returncode: ' +
                                          str(returncode) + '"', 'id': rid}]}

        try:
            reply_dict = json.loads(text[0])
        except ValueError:
            v0_print(_who, "Invalid 'text':", text)  # Sample below on 2024-10-08
            # 2025-05-28 Add 'id' dictionary expected by checkReply() method.
            reply_dict = {"result": [{'status': '"' + _who +
                                                ' json.loads(text) failed!"',
                                     'id': rid}]}

        v3_print(_who, "reply_dict:", reply_dict)
        # NetworkInfo().turnPictureOn().os_curl(): reply_dict:
        #   {'result': [], 'id': 52}
        return reply_dict

    def get_mac_dict(self, mac):
        """ Get mac_dict by mac address.
            :param mac: MAC address
            :returns: mac_dict
        """
        _who = self.who + "get_mac_dict():"

        for mac_dict in self.mac_dicts:
            if mac_dict['mac'] == mac:
                v2_print(_who, "Found existing ni.mac_dict:", mac_dict['name'])
                return mac_dict

        v0_print(_who, "mac address unknown: '" + str(mac) + "'")

        return {}

    def inst_for_mac(self, mac, not_found_error=True):
        """ Get device instance for mac address. Instances are dynamically
            created at run time and cannot be saved in mac_dict.
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

        return {}

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
            """ Test if hs100, SonyTV, GoogleTV, Bluetooth LED, Laptop, etc. """
            inst = cname(arp['mac'], arp['ip'], arp['name'], arp['alias'])
            if not inst.dependencies_installed:
                # 2025-06-18 TODO: How to prevent instance init more than once to
                #   check if dependencies are installed? Global supported variables
                # v0_print("Missing Dependencies:", cname.required)
                return False
            if not inst.isDevice(forgive=True):
                return False

            v1_print(arp['mac'], " # ", arp['ip'].ljust(15),
                     "##  is a " + inst.type + " code =", inst.type_code)

            ''' 2025-01-13 Caller must do this:
            arp['type_code'] = inst.type_code  # Assign 10, 20, 30...
            instances.append({"mac": arp['mac'], "instance": inst})
            view_order.append(arp['mac'])
            if update:
                ni.mac_dicts[i] = arp  # Update arp list
            '''
            instance["mac"] = arp['mac']
            instance["instance"] = inst

            return True  # Grab next type

        # Test smart plug first because they seem most "fragile"
        if test_one(SmartPlugHS100):
            return instance

        if test_one(Router):
            return instance

        if test_one(Computer):
            return instance

        if test_one(LaptopDisplay):
            return instance

        if test_one(SonyBraviaKdlTV):
            return instance

        if test_one(TclGoogleAndroidTV):
            v0_print(_who, "Android TV found:", arp['ip'])
            v0_print("instance:", instance, "\n")
            return instance
        elif arp['ip'] == "192.168.0.17":  # "devices", "-l"
            # Special testing. android.isDevice was failing without extra time.
            v0_print(_who, "Android TV failed!:", arp['ip'])

        if test_one(BluetoothLedLightStrip):
            return instance

        return {}


class TreeviewRow(DeviceCommonSelf):
    """ Device treeview row variables and methods.

        Sensors treeview uses dummy call to TreeviewRow() class in order to call
        fadeIn() and fadeOut() methods.

    """

    def __init__(self, top):
        """ DeviceCommonSelf(): Variables used by all classes
        :param top: Toplevel created by Application() class instance.
        """
        DeviceCommonSelf.__init__(self, "TreeviewRow().")  # Define self.who

        self.top = top  # 2025-01-13 top is not passed as argument???
        self.tree = self.top.tree  # Shortcut
        self.photos = self.top.photos  # Shortcut
        self.isActive = self.top.isActive  # If False, HomA is shutting down
        self.item = None  # Treeview Row iid
        self.photo = None  # Photo image
        self.text = None  # Row text, E.G. "ON", "OFF"

        self.values = None  # Row values - Name lines, Attribute lines, MAC
        self.name_column = None  # Device Name & IP address - values[0]
        self.attribute_column = None  # 3 line device Attributes - values[1]
        self.mac = None  # MAC address - hidden column values[-1] / values[2]
        # self.mac - mac_dict['mac'] - is non-displayed treeview column
        # used to reread mac_dict

        self.mac_dict = None  # device dictionary
        self.inst = None  # device instance
        self.inst_dict = None  # instance dictionary

    def Get(self, item):
        """ Get treeview row """

        _who = self.who + "Get():"
        if not self.isActive:
            return  # Shutting down

        self.item = str(item)  # iid - Corrupted after swapping rows!
        # CANNOT USE: self.photo = self.top.tree.item(item)['image']
        self.photo = self.photos[int(item)]
        self.text = self.top.tree.item(self.item)['text']

        self.values = self.top.tree.item(self.item)['values']
        self.name_column = self.values[0]  # Host name / IP address
        self.attribute_column = self.values[1]  # Host alias / MAC / Type Code
        self.mac = self.values[2]  # mac_dict['mac'] is non-displayed value

        try:
            self.mac_dict = ni.get_mac_dict(self.mac)
            self.inst_dict = ni.inst_for_mac(self.mac)
            self.inst = self.inst_dict['instance']
        except IndexError:
            v0_print(_who, "Catastrophic Error. MAC not found:", self.mac)
            v0_print("  Name:", self.name_column)
            # Occurred 2025-04-09 for first time.

    def getIidForInst(self, inst):
        """ Using passed instance, get the treeview row. """
        if not self.isActive:
            return  # Shutting down

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
        if not self.isActive or not self.top.winfo_exists():
            return  # Shutting down. 2025-05-16 add winfo_exists test.

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
        if not self.isActive:
            return  # Shutting down
        self.mac_dict = ni.get_mac_dict(mac)

        # self.mac is non-displayed treeview column used to reread mac_dict
        self.mac = mac  # MAC address
        self.inst_dict = ni.inst_for_mac(mac)  # instance dictionary
        try:
            self.inst = self.inst_dict['instance']
        except KeyError:
            v0_print("self.inst_dict has no 'instance' key:", self.inst_dict)
            v0_print("self.mac_dict has no instance:", self.mac_dict)
            # return  # 2025-01-12 need self.values defined

        try:
            type_code = self.mac_dict['type_code']
        except KeyError:
            v0_print(_who, "Key 'type_code' not in 'mac_dict':", self.mac_dict)
            type_code = None

        # TV's are 16/9 = 1.8. Treeview uses 300/180 image = 1.7.
        if type_code == GLO['HS1_SP']:  # TP-Line Kasa Smart Plug HS100 image
            photo = img.tk_image("bias.jpg", 300, 180)
        elif type_code == GLO['KDL_TV']:  # Sony Bravia KDL TV image
            photo = img.tk_image("sony.jpg", 300, 180)
        elif type_code == GLO['TCL_TV']:  # TCL / Google Android TV image
            photo = img.tk_image("tcl.jpg", 300, 180)
        elif type_code == GLO['BLE_LS']:  # Bluetooth Low Energy LED Light Strip
            photo = img.tk_image("led_lights.jpg", 300, 180)
        elif type_code == GLO['DESKTOP']:  # Desktop computer image
            photo = img.tk_image("computer.jpg", 300, 180)
        elif type_code == GLO['LAPTOP_B']:  # Laptop Base image
            photo = img.tk_image("laptop_b.jpg", 300, 180)
        elif type_code == GLO['LAPTOP_D']:  # Laptop Display image
            photo = img.tk_image("laptop_d.jpg", 300, 180)
        elif type_code == GLO['ROUTER_M']:  # Laptop Display image
            photo = img.tk_image("router2.jpg", 300, 180)
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
        # if self.inst.powerStatus == "?":  # Initial boot  # 2025-01-12
        if status == "?":  # Initial boot
            self.text = "Wait..."  # Power status checked when updating treeview
        else:
            self.text = "  " + self.inst.powerStatus  # Power state already known
        self.name_column = name  # inst.name or "?" if not found
        self.name_column += "\nIP: " + self.mac_dict['ip']
        self.attribute_column = self.mac_dict['alias']
        self.attribute_column += "\nMAC: " + self.mac_dict['mac']
        self.attribute_column += "\n" + type_code  # inst.type or "?" if not found
        self.values = (self.name_column, self.attribute_column, self.mac)

    def Add(self, item):
        """ Set treeview row - Must call .New() beforehand.
            Handles item being a str() or an int()
            :param item: Target row can be different than original self.item
            :returns: nothing
        """
        _who = self.who + "Add():"
        if not self.isActive:
            return  # Shutting down
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

    def fadeIn(self, item):
        """ Fade In over 10 steps of 30 ms """
        if not self.isActive:
            return  # Shutting down
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
        if not self.isActive:
            return  # Shutting down
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


class SystemMonitor(DeviceCommonSelf):
    """ System Monitor - sensors CPU/GPU Temp and Fan Speeds.

        Print results to console unless `homa.py -s` (silent) was used.
    """

    def __init__(self, top):
        """ DeviceCommonSelf(): Variables used by all classes
        :param top: Toplevel created by Application() class instance.
        """
        DeviceCommonSelf.__init__(self, "SystemMonitor().")  # Define self.who

        import socket
        # https://docs.python.org/3/library/socket.html#socket.getaddrinfo
        hostname = socket.gethostname()
        # v0_print("Your Computer hostname is:", hostname)  # alien

        _IPAddr = socket.gethostbyname(hostname)
        # v0_print("Your Computer IP Address is:", _IPAddr)  # 127.0.1.1

        _IPAddr_ex = socket.gethostbyname_ex(hostname)
        # v0_print("Your Computer IP Address_ex is:")
        # for tup in IPAddr_ex:
        #    v0_print(tup)
        # ('Alien',
        # ['AW', '17R3', 'WiFi', '9c:b6:d0:10:37:f7',
        #  'AW', '17R3', 'Ethernet', '28:f1:0e:2a:1a:ed'],
        # ['127.0.1.1', '192.168.0.10', '192.168.0.12'])

        _who = self.who + "__init__():"

        self.top = top  # Copy of toplevel for creating treeview
        self.tree = self.top.tree  # Pre-existing Applications() devices tree
        self.photos = self.top.photos  # Applications() device photos
        self.isActive = self.top.isActive
        self.item = None  # Applications() Treeview Row iid
        self.photo = None  # Applications() Photo image
        self.text = None  # Applications() Row text, E.G. "ON", "OFF"

        self.values = None  # Applications() Row values - Name lines, Attribute lines, MAC
        self.name_column = None  # Applications() Device Name & IP address - values[0]
        self.attribute_column = None  # Applications() 3 line device Attributes - values[1]
        self.mac = None  # Applications() MAC address - hidden row values[-1] / values[2]

        self.mac_dict = None  # Applications() device dictionary
        self.inst = None  # Applications() device instance
        self.inst_dict = None  # Applications() instance dictionary

        self.type = "System Monitor"
        self.type_code = 900  # 2025-03-01 Fake type_code, need code setup
        self.requires = ['ifconfig', 'iwconfig', 'sensors', 'top']
        self.installed = []
        self.checkDependencies(self.requires, self.installed)

        v3_print(_who, "Dependencies:", self.requires)
        v3_print(_who, "Installed?  :", self.installed)
        if not self.dependencies_installed:
            v1_print(_who, "System Monitor dependencies are not installed.")

        self.last_sensor_check = 0.0  # check every x seconds
        self.last_sensor_log = 0.0  # log every x seconds
        self.skipped_checks = 0  # Skipped check when last check < x seconds
        self.number_checks = 0  # Number of checks
        self.skipped_fan_same = 0  # Don't log when fan speed the same
        self.skipped_fan_diff = 0  # Don't log when fan speed different by < x RPM
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
        if not self.checkInstalled('sensors'):
            return

        ''' Dell Virtual output from `sensors` (first 7 lines):
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
        self.last_sensor_check = now

        # Run `sensors` command every GLO['SENSOR_CHECK'] seconds
        self.number_checks += 1
        log = True if len(self.sensors_log) == 0 else False
        event = self.runCommand(['sensors'], _who, log=log)
        result = event['output']

        # Parse `sensors` output to dictionary key/value pairs
        dell_found = False
        self.curr_sensor = {}

        # Check one fan's RPM speed change
        def CheckFanChange(key):
            """ If fan speed changed by more than GLO['FAN_GRANULAR'] RPM, force logging.
                Called for "Processor Fan" and "Video Fan" A.K.A. "fan3".
            :param key: 'Processor Fan' or 'Video Fan', etc.
            :return: True of curr_sensor == last_sensor
            """
            try:
                if self.curr_sensor[key] == self.last_sensor[key]:
                    self.skipped_fan_same += 1
                    return False
            except (TypeError, IndexError):
                # First time last log doesn't exist. Treat as fan speed change.
                self.last_sensor_log = time.time() - GLO['SENSOR_LOG'] * 2
                return True

            # Speed can fluctuate 2400 RPM, 2600 RPM, 2400 RPM...  18 times
            # over 200 seconds. To reduce excessive fan speed change logging,
            # skip fluctuations <= GLO['FAN_GRANULAR'] RPM.
            curr = float(self.curr_sensor[key].split(" ")[0])
            last = float(self.last_sensor[key].split(" ")[0])
            diff = abs(curr - last)
            # Only report fan speed differences > 200 RPM
            if diff <= GLO['FAN_GRANULAR']:
                # v0_print("skipping diff:", diff)
                self.skipped_fan_diff += 1
                return False  # Don't override last with current

            # Fan speed changed. Force logging by resetting last log time.
            self.last_sensor_log = time.time() - GLO['SENSOR_LOG'] * 2
            return True

        # Process `sensors` output lines
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
                # 2025-02-09 For python 3 degree in bytes use str(+66.0°C)
                self.curr_sensor[parts[0]] = \
                    str(parts[1].strip()).replace("+", "").replace(".0", "")

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

            2025-05-11 - Need summary because too many changes per minute:

 5526.53 |  64°C / 5100 RPM |  68°C / 5000 RPM | 11:56 AM (1)
 8573.30 |  77°C / 5400 RPM |  73°C / 5300 RPM | 12:46 PM (5)
 8623.90 |  90°C / 6400 RPM |  74°C / 5900 RPM | 12:47 PM (12)
 8692.97 |  76°C / 6200 RPM |  74°C / 6100 RPM | 12:48 PM (9)
 8747.53 |  90°C / 6400 RPM |  75°C / 6400 RPM | 12:49 PM (12)
 8813.26 |  76°C / 6100 RPM |  74°C / 5600 RPM | 12:50 PM (5)
 8874.08 |  92°C / 6000 RPM |  75°C / 5900 RPM | 12:51 PM (6)
 8929.96 |  93°C / 6400 RPM |  75°C / 6200 RPM | 12:52 PM (10)
 8994.82 |  76°C / 5800 RPM |  75°C / 5000 RPM | 12:53 PM (16)
 9054.34 |  82°C / 5900 RPM |  76°C / 5800 RPM | 12:54 PM (6)
 9067.13 |  81°C / 5200 RPM |  76°C / 4900 RPM | 12:55 PM (3)
 9277.85 |  85°C / 5200 RPM |  77°C / 4900 RPM | 12:58 PM (2)
 9352.93 |  81°C / 6200 RPM |  77°C / 6200 RPM | 12:59 PM (4)
 9379.23 |  77°C / 6500 RPM |  76°C / 6400 RPM |  1:00 PM (1)

Later:

   11.07 |  77°C / 6400 RPM |  73°C / 6300 RPM |  1:23 PM
 1241.40 |  69°C / 6100 RPM |  68°C / 5900 RPM |  1:43 PM
 1244.89 |  65°C / 6000 RPM |  68°C / 5500 RPM |  1:44 PM
 1249.60 |  65°C / 5700 RPM |  68°C / 5000 RPM |  1:44 PM
 1256.67 |  67°C / 5300 RPM |  68°C / 5000 RPM |  1:44 PM
 1314.03 |  90°C / 5500 RPM |  71°C / 5400 RPM |  1:45 PM
 1321.96 |  90°C / 5900 RPM |  72°C / 5500 RPM |  1:45 PM
 1325.51 |  86°C / 6200 RPM |  72°C / 5900 RPM |  1:45 PM
 1330.13 |  69°C / 6100 RPM |  72°C / 5500 RPM |  1:45 PM
 1334.82 |  72°C / 5900 RPM |  71°C / 5000 RPM |  1:45 PM
 1341.56 |  77°C / 5400 RPM |  71°C / 5000 RPM |  1:45 PM
 1358.20 |  91°C / 5600 RPM |  72°C / 5400 RPM |  1:45 PM
 1367.34 |  71°C / 5600 RPM |  72°C / 5000 RPM |  1:46 PM
 1374.23 |  69°C / 5200 RPM |  72°C / 5000 RPM |  1:46 PM

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
            v0_print(" Seconds | CPU Temp/Fan RPM | GPU Temp/Fan RPM |   Time  ")
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
                         '|', opt('CPU').rjust(6) + " /", opt('Processor Fan').rjust(8),
                         '|', opt('GPU').rjust(6) + " /", opt('Video Fan').rjust(8),
                         '|', dt.datetime.now().strftime('%I:%M %p').strip('0').rjust(8))

            if self.treeview_active:
                self.InsertTreeRow(sensor)
                if i == len(self.sensors_log) - 1:
                    # 2025-01-20 getting error flashing when last row not inserted yet
                    self.FlashLastRow()  # fade in color, pause, fade out color

    def populateSensorsTree(self):
        """ Populate treeview using self.sensor_log [{}, {}... {}]
            Treeview IID is string seconds: "0.1", "1.1", "2.2" ... "9999.9"
        """
        _who = self.who + "populateSensorsTree():"

        ''' Treeview style is large images in cell 0 '''
        style = ttk.Style()
        style.configure("Treeview.Heading", font=(None, g.MED_FONT),
                        rowheight=int(g.LARGE_FONT * 2.2))  # FONT14 alias
        row_height = int(g.LARGE_FONT * 2.2)
        style.configure("Treeview", font=g.FONT14, rowheight=row_height,
                        background=GLO['TREEVIEW_COLOR'],
                        fieldbackground=GLO['TREEVIEW_COLOR'])  # Try applying later
                        #edge_color=GLO['TREE_EDGE_COLOR'], edge_px=5)

        ''' Create treeview frame with scrollbars '''
        # Also once image placed into treeview row, it can't be read from the row.
        self.tree = ttk.Treeview(self.top, column=('Seconds', 'CPU', 'GPU', 'Time'),
                                 selectmode='none', style="Treeview", show="headings")

        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scroll = tk.Scrollbar(self.top, orient=tk.VERTICAL,
                                width=14, command=self.tree.yview)
        v_scroll.grid(row=0, column=1, sticky=tk.NS)
        self.tree.configure(yscrollcommand=v_scroll.set)

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
        self.tree.tag_configure('normal', background=GLO['TREEVIEW_COLOR'],
                                foreground="Black")  # Nothing special

        # Fade in/out Row: Black fg faded green bg to White fg dark green bg
        green_back = ["#93fd93", "#7fe97f", "#6bd56b", "#57c157", "#43ad43",
                      "#39a339", "#258f25", "#117b11", "#006700", "#004900"]
        green_fore = ["#000000", "#202020", "#404040", "#606060", "#808080",
                      "#aaaaaa", "#cccccc", "#dddddd", "#eeeeee", "#ffffff"]
        for i in range(10):
            self.tree.tag_configure('fade' + str(i), background=green_back[i],
                                    foreground=green_fore[i])  # Nothing special

        # Define edge color last for Tkinter "glitch"
        style.configure("Treeview", edge_color=GLO['TREE_EDGE_COLOR'], edge_px=5)

        # Build Sensors treeview
        self.Print(start=0, end=-1, tree_only=True)

    def FlashLastRow(self):
        """ Flash the last row in Sensors Treeview """
        _who = self.who + "FlashLastRow():"
        cr = TreeviewRow(self)  # also used by Applications() devices treeview
        sec = self.sensors_log[-1]['delta']  # delta is seconds since app started

        # iid is Number right justified 8 = 5 whole + decimal + 2 fraction
        sec_str = "{0:>8.2f}".format(sec)  # E.G. sec = "2150.40" seconds
        sec_str = str(sec_str)  # 2025-01-19 strangely type is float today.

        try:
            # _item = self.tree.item(sec_str)  # 2025-03-26
            _item = self.tree.item(self.getLastRowIid())  # 2025-03-26
        except tk.TclError:
            v0_print("\n" + _who, "sec_str not found: '" + sec_str + "'",
                     " |", type(sec_str))
            v0_print("self.sensors_log[-1]:", self.sensors_log[-1])
            return

        # cr.fadeIn(sec_str)  # 2025-03-26
        cr.fadeIn(self.getLastRowIid())  # 2025-03-26
        time.sleep(3.0)
        # cr.fadeOut(sec_str)  # 2025-03-26
        cr.fadeOut(self.getLastRowIid())  # 2025-03-26

    def getLastRowIid(self):
        """ Return IID for last row of Sensors Treeview """
        return self.tree.get_children()[-1]

    def InsertTreeRow(self, sensor):
        """ Insert sensors row into sensors treeview
            :param sensor: = {delta: seconds, CPU: temp, Processor Fan: rpm,
                              GPU: temp, Video Fan: rpm}

        """
        _who = self.who + "InsertTreeRow():"

        def opt(key):
            """ Return optional key or N/A if not found. """
            try:
                return sensor[key]  # in Python 3, value is bytes
            except KeyError:
                return "N/A"

        # Possible image showing temperature of CPU?
        sec_str = "{0:>8.2f}".format(sensor['delta'])
        try:
            self.tree.insert(
                '', 'end', iid=None,  # iid=sec_str,  2025-03-26 auto assign
                value=(sec_str,
                       opt('CPU').rjust(7) + " / " + opt('Processor Fan').rjust(8),
                       opt('GPU').rjust(7) + " / " + opt('Video Fan').rjust(8),
                       dt.datetime.fromtimestamp(sensor['time']).
                       strftime('%I:%M %p').strip('0').rjust(8)))
        except tk.TclError:
            v0_print(_who, "sec_str already exists in Sensors Treeview:", sec_str)

        self.tree.see(self.getLastRowIid())
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
        self.checkDependencies(self.requires, self.installed)
        v2_print(self.who, "Dependencies:", self.requires)
        v2_print(self.who, "Installed?  :", self.installed)

        self.chassis = ""  # "desktop", "laptop", "convertible", "server",
        # "tablet", "handset", "watch", "embedded", "vm" and "container"

        if self.checkInstalled('hostnamectl'):
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

    def isDevice(self, forgive=False):
        """ Test if passed ip == ethernet ip or WiFi ip.
            Initially a laptop base could be assigned with IP but now it
            is assigned as a laptop display. A laptop will have two images
            in the treeview - laptop_b.jpg and laptop_d.jpg

            A desktop will have a single image - desktop.jpg.

        """
        _who = self.who + "isDevice():"
        v2_print(_who, "Test if device is a Laptop Display:", self.ip)

        if forgive:
            pass  # Dummy argument for uniform instance parameter list

        if cp.chassis != "laptop":
            return False

        if self.ip == cp.ether_ip or self.ip == cp.wifi_ip:
            return True

        return False

    def turnOn(self, forgive=False):
        """ Return True if "On" or "Off", False if no communication
            If forgive=True then don't report pipe.returncode != 0

            echo <PASSWORD> |
            sudo -S echo 0 |
            sudo tee /sys/class/backlight/intel_backlight/bl_power

        Note: Adding user to group "video" DOES NOT allow:
            echo 4000 > /sys/class/backlight/intel_backlight/brightness
            bash: /sys/class/backlight/intel_backlight/brightness: Permission denied

        """
        _who = self.who + "turnOn():"
        v2_print(_who, "Turn On Laptop Display:", self.ip)

        if forgive:
            pass  # Dummy argument for uniform instance parameter list

        self.setPower("ON", forgive=forgive)
        return self.powerStatus

    def turnOff(self, forgive=False):
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
        _who = self.who + "turnOn():"
        v2_print(_who, "Turn Off Laptop Display:", self.ip)

        if forgive:
            pass  # Dummy argument for uniform instance parameter list

        self.setPower("OFF", forgive=forgive)
        return self.powerStatus

    def getPower(self, forgive=False):
        """ Return "ON", "OFF" or "?" """

        _who = self.who + "getPower():"
        v2_print(_who, "Test if Laptop Display is powered on:", self.ip)
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

    def setPower(self, status, forgive=False):
        """ Set Laptop Display Backlight Power 'OFF' or 'ON'
            If forgive=True then don't report pipe.returncode != 0
        """

        _who = self.who + "setPower(" + status + "):"
        v2_print(_who, "Set Laptop Display Power to:", status)

        # Sudo password required for powering laptop backlight on/off
        if GLO['SUDO_PASSWORD'] is None:
            GLO['SUDO_PASSWORD'] = self.app.GetPassword()
            self.app.updateDropdown()
            if GLO['SUDO_PASSWORD'] is None:
                return "?"  # Cancel button (256) or escape or 'X' on window decoration (64512)

        power = '/sys/class/backlight/' + GLO['BACKLIGHT_NAME'] + '/bl_power'
        if status == "ON":
            echo = GLO['BACKLIGHT_ON']
        elif status == "OFF":
            echo = GLO['BACKLIGHT_OFF']
        else:
            V0_print(_who, "Invalid status (not 'ON' or 'OFF'):", status)
            return

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
        self.checkDependencies(self.requires, self.installed)

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
        v2_print(_who, "Test if device is a TP-Link Kasa HS100 Smart Plug:", self.ip)

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

    def turnOn(self, forgive=False):
        """ Turn on TP-Link Smart Plug using hs100.sh script.
            If forgive=True then don't report pipe.returncode != 0
        """
        _who = self.who + "turnOn():"
        v2_print(_who, "Turn On TP-Link Kasa HS100 Smart Plug:", self.ip)

        Reply = self.getPower(forgive=forgive)  # Get current power status

        if Reply == "?":
            v2_print(_who, self.ip, "- Not a Smart Plug!")
            return "?"

        if Reply == "ON":
            v2_print(_who, self.ip, "- is already turned on. Skipping")
            return "ON"

        self.setPower("ON")
        v2_print(_who, self.ip, "- Smart Plug turned 'ON'")
        return "ON"

    def turnOff(self, forgive=False):
        """ Turn off TP-Link Smart Plug using hs100.sh script.
            If forgive=True then don't report pipe.returncode != 0
        """
        _who = self.who + "turnOn():"
        v2_print(_who, "Turn Off TP-Link Kasa HS100 Smart Plug:", self.ip)

        Reply = self.getPower(forgive=forgive)

        if Reply == "?":
            v2_print(_who, self.ip, "- Not a Smart Plug!")
            return "?"

        if Reply == "OFF":
            v2_print(_who, self.ip, "- is already turned off. Skipping")
            return "OFF"

        self.setPower("OFF")
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

    def setPower(self, status):
        """ Set Power to status, 'OFF' or 'ON'
            Note hs100.sh requires lower() case
            If forgive=True then don't report pipe.returncode != 0
        """

        _who = self.who + "setPower(" + status + "):"
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

        self.powerSavingMode = "?"  # set with getPowerSavingMode()
        self.hasVolumeSet = False  # On Startup check quiet/normal volume
        self.volume = "?"  # Set with getVolume()  # 28
        self.volumeLast = "?"  # Last recorded volume for spamming notify-send
        self.volumeSpeaker = "?"
        self.volumeHeadphones = "?"
        self.outputTerminal = "?"  # Set with getSoundSettings()  # Speaker
        self.tvPosition = "?"  # Set with getSpeakerSettings()  # Table or Wall
        self.subwooferLevel = "?"  # Set with getSpeakerSettings()  # 17
        self.subwooferFreq = "?"  # Set with getSpeakerSettings()  # 10
        self.subwooferPhase = "?"  # Set with getSpeakerSettings()  # normal
        self.subwooferPower = "?"  # Set with getSpeakerSettings()  # on

        self.requires = ['curl']
        self.installed = []
        self.checkDependencies(self.requires, self.installed)
        _who = self.who + "__init__():"
        v3_print(_who, "Dependencies:", self.requires)
        v3_print(_who, "Installed?  :", self.installed)

        if not self.dependencies_installed:
            v1_print(_who, "Sony Bravia KDL TV dependencies are not installed.")

    def makeCommon(self, fname, RESTid, parm_list, ver="1.0"):
        """ Make common _who and JSON_str. Print v2 line """
        # noinspection PyProtectedMember
        _who = self.who + sys._getframe(1).f_code.co_name + "():"
        JSON_str = '{"method": "' + fname + '", "id": ' + RESTid + \
                   ', "params": ' + parm_list + ', "version": "' + ver + '"}'
        v2_print(_who, 'Send: "id": ' + RESTid + ', "params": ' +
                 parm_list + ', to:', self.ip)
        return _who, JSON_str

    def checkReply(self, reply, RESTid):
        """ Verify correct RESTid embedded in reply from REST API
            Use sys._getframe(1).f_code.co_name to get caller's name
        """
        def print_dict():
            """ Print dictionary with ppprint if available """
            if pprint_installed:
                print_string = pprint.pformat(reply, indent=2)
                v0_print(" ", print_string)
            else:
                v0_print(" ", reply)

        # noinspection PyProtectedMember
        _who = self.who + sys._getframe(1).f_code.co_name + "().checkReply():"
        try:
            embedId = str(reply['id'])  # Reply id returned as integer
            if embedId != RESTid:
                v0_print(_who, "embedId: ", embedId, "!= RESTid:", RESTid)
                print_dict()

        except (TypeError, KeyError):
            embedId = ""
            v0_print(_who, "TypeError / KeyError:")
            print_dict()

        v2_print(_who, "curl reply_dict:", reply)  # E.G. {'result': [], 'id': 55}
        return embedId == RESTid

    def checkSonyEvents(self):
        """ Called from app.refreshApp() every 16 to 33 ms.
            Check if Sony TV Remote turned off TV to suspend system.
            Check if Sony TV Remote changed volume and display percentage.
            Check one-time to set Sony TV volume to normal or quiet.

            2025-06-01 Originally in Application() moved to SonyBraviaKdlTV()
        """
        _who = self.who + "checkSonyEvents():"

        if self.powerStatus == "?":
            v1_print(_who, "old self.powerStatus:", self.powerStatus)
            self.getPower()  # "?" when network down or resuming
            v1_print(_who, "new self.powerStatus:", self.powerStatus)
            # 2025-05-31 TODO: If "ON" update treeview and dropdown menu

        life_span = time.time() - GLO['APP_RESTART_TIME'] \
            if self.powerStatus == "ON" else 0.0
        log_status = GLO['LOG_EVENTS']  # Current event logging status
        GLO['LOG_EVENTS'] = False  # Turn off logging during Sony checks

        ''' Sony TV monitored for TV Remote power off suspends system? '''
        if GLO['ALLOW_REMOTE_TO_SUSPEND'] and life_span > 2.0:
            self.powerStatus = "?"  # Default if network down
            if self.checkPowerOffSuspend(forgive=True):  # check "OFF"
                self.app.sony_suspended_system = True  # Sony TV initiated suspend
                return
                # self.Suspend(sony_remote_powered_off=True)  # Turns on event logging
                # Will not return until Suspend finishes and resume finishes

        ''' Sony TV audio channel monitored for volume up/down display? '''
        if GLO['ALLOW_VOLUME_CONTROL'] and life_span > 2.0:
            if self.checkVolumeChange(forgive=True):
                self.app.last_rediscover_time = time.time()  # 2025-05-27 review need

            ''' One-time set volume to quiet or normal on startup and resume. '''
            if not self.hasVolumeSet:
                self.setStartupVolume()  # 9am - 10pm normal, else quiet volume
                self.hasVolumeSet = True  # Don't check again

        GLO['LOG_EVENTS'] = True if log_status else False  # Sony done, restore logging

    def checkPowerOffSuspend(self, forgive=False):
        """ If TV powered off with remote control. If so suspend system.
            Called from app.refreshApp() every 16 to 33 milliseconds
            Copied from /mnt/e/bin/tvpowered

            Normally event logging would be turned off to prevent large dictionary.
        """
        _who = self.who + "checkPowerOffSuspend():"

        if self.menuPowerOff:  # Only sony tv remote control power off counts.
            return False  # Powered off by HomA Right Click doesn't count

        self.getPower(forgive=forgive)
        if self.powerStatus != "OFF":
            return False  # Sony power status is "ON" or "?" or "Error:"

        v1_print(_who, "Suspending due to Sony TV powerStatus:", self.powerStatus)

        return True  # app.refreshApp will suspend system now

    def checkVolumeChange(self, forgive=False):
        """ If current volume is different than last volume spam notify-send
            Called from app.refreshApp() every 16 to 33 milliseconds (60 to 30 fps)
            DO NOT use event logging because each volume display is separate entry

            Normally event logging would be turned off to prevent large dictionary.
        """
        _who = self.who + "checkVolumeChange():"

        if self.powerStatus != "ON":
            return False  # TV isn't powered on, can't check current volume

        self.getVolume(forgive=forgive)  # Occasionally get curl error 124 timeout
        if self.volume == self.volumeLast:
            return False
        self.volumeLast = self.volume
        title = self.ip  # 192.168.0.19
        title = self.name if self.name is not None else title  # SONY.LAN
        title = self.alias if self.alias is not None else title  # Sony Bravia KDL TV

        percentBar = self.makePercentBar(int(self.volume))
        command_line_list = [
            "notify-send", "--urgency=critical", title,
            "-h", "string:x-canonical-private-synchronous:volume",
            "--icon=/usr/share/icons/gnome/48x48/devices/audio-speakers.png",
            "Volume: {} {}".format(self.volume, percentBar)]
        event = self.runCommand(command_line_list, _who, forgive=forgive)

        # Average command time is 0.025 seconds but never logged
        if event['returncode'] != 0:  # Was there an error?
            if forgive is False:
                v0_print(_who, "Error:", event['returncode'])
                v0_print(" ", self.cmdString)

        return True  # Parent will delay rediscovery 1 minute

    def getPower(self, forgive=False):
        """ Return "ON", "OFF" or "?" if error.
            Called by self.app.getPower() and self.isDevice().

https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/getPowerStatus/index.html

        """

        RESTid = "50"
        _who, JSON_str = self.makeCommon("getPowerStatus", RESTid, '[]')
        reply_dict = ni.curl(JSON_str, "system", self.ip, RESTid, forgive=forgive)
        self.powerStatus = "?"  # Can be "ON", "OFF" or "?"
        if not forgive and not self.checkReply(reply_dict, RESTid):
            return self.powerStatus

        try:
            reply = reply_dict['result'][0]['status']
        except (KeyError, IndexError):
            reply = reply_dict  # Probably "7" for not a Sony TV

        #print("reply:", reply, " | type(reply):", type(reply))
        if isinstance(reply, int):
            v3_print(_who, "Integer reply:", reply)  # 7
        elif u"active" == reply:
            self.powerStatus = "ON"  # Can be "ON", "OFF" or "?"
        elif u"standby" == reply:
            self.powerStatus = "OFF"  # Can be "ON", "OFF" or "?"
        else:
            v3_print(_who, "Something weird: ?")  # Router

        # 2024-12-04 - Some tests
        #self.getSoundSettings()
        #self.getSpeakerSettings()

        return self.powerStatus

    def turnOn(self, forgive=False):
        """ Turn On Sony Bravia KDL TV using os_curl
            https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/setPowerStatus/index.html
        """

        RESTid = "55"
        _who, JSON_str = self.makeCommon("setPowerStatus", RESTid, '[{"status": true}]')
        reply_dict = ni.os_curl(JSON_str, "system", self.ip, RESTid, forgive=forgive)
        self.powerStatus = "?"  # Can be "ON", "OFF" or "?"
        if not forgive and not self.checkReply(reply_dict, RESTid):
            return self.powerStatus

        try:
            result = reply_dict['result']  # can be KeyError
            if result:  # result should be empty (tests False)
                v0_print(_who, "reply_dict['result']' should be empty:", result)
        except KeyError:
            v0_print(_who, "Invalid reply_dict['result']':", reply_dict)


        return self.getPower(forgive=forgive)

    def turnOff(self, forgive=False):
        """ Turn Off Sony Bravia KDL TV using os_curl
            https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/setPowerStatus/index.html
        """

        RESTid = "55"
        _who, JSON_str = self.makeCommon("setPowerStatus", RESTid, '[{"status": false}]')
        reply_dict = ni.os_curl(JSON_str, "system", self.ip, RESTid, forgive=forgive)
        self.powerStatus = "?"  # Can be "ON", "OFF" or "?"
        if not forgive and not self.checkReply(reply_dict, RESTid):
            return self.powerStatus

        try:
            result = reply_dict['result']  # can be KeyError
            if result:  # result should be empty (tests False)
                v0_print(_who, "reply_dict['result']' should be empty:", result)
        except KeyError:
            v0_print(_who, "Invalid reply_dict['result']':", reply_dict)

        return self.getPower(forgive=forgive)

    def getPowerSavingMode(self, forgive=False):
        """ Get Sony Bravia KDL TV power savings mode """

        # "off" - Power saving mode is disabled.  The panel is turned on.
        # "low" - Power saving mode is enabled at a low level.
        # "high" - Power saving mode is enabled at a high level.
        # "pictureOff" - Power saving mode is enabled with the panel output off.

        RESTid = "51"
        _who, JSON_str = self.makeCommon("getPowerSavingMode", RESTid, '[]')
        reply_dict = ni.curl(JSON_str, "system", self.ip, RESTid, forgive=forgive)
        self.powerSavingMode = "?"  # Can be "ON", "OFF" or "?"
        if not forgive and not self.checkReply(reply_dict, RESTid):
            return self.powerSavingMode

        try:
            reply = reply_dict['result'][0]['mode']
        except (KeyError, IndexError):
            reply = reply_dict  # Probably "7" for not a Sony TV
        v2_print(_who, "curl reply_dict:", reply_dict)

        # {'result': [{'mode': 'off'}], 'id': 51}
        if isinstance(reply, int):
            v0_print(_who, "Integer found:", reply)  # 7
            self.powerSavingMode = "?"
        elif u"pictureOff" == reply:
            self.powerSavingMode = "ON"  # Reduce states from Off / Low / High / Picture Off
        elif u"off" == reply:
            self.powerSavingMode = "OFF"
        else:
            v0_print(_who, "Something weird in reply:", reply)
            self.powerSavingMode = "?"

        return self.powerSavingMode

    def turnPictureOn(self, forgive=False):
        """ Turn On Sony Bravia KDL TV Picture using ni.os_curl()
            https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/setPowerSavingMode/index.html
        """

        RESTid = "52"
        _who, JSON_str = self.makeCommon("setPowerSavingMode", RESTid, '[{"mode": "off"}]')

        reply_dict = ni.os_curl(JSON_str, "system", self.ip, RESTid, forgive=forgive)
        #reply_dict = ni.curl(JSON_str, "system", self.ip, RESTid, forgive=forgive)
        self.checkReply(reply_dict, RESTid)

        try:
            err = reply_dict['error']
            return "Err: " + str(err[0])  # 403, Forbidden
            # error only occurs when using ni.curl() instead of ni.os_curl()
        except KeyError:
            pass  # No error

        return "ON"

    def turnPictureOff(self, forgive=False):
        """ Turn Off Sony Bravia KDL TV Picture using ni.os_curl()
            https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/system/v1_0/setPowerSavingMode/index.html
        """

        RESTid = "52"
        _who, JSON_str = self.makeCommon("setPowerSavingMode", RESTid,
                                         '[{"mode": "pictureOff"}]')

        reply_dict = ni.os_curl(JSON_str, "system", self.ip, RESTid, forgive=forgive)
        # 2025-04-12 Single quotes are around --data json packet
        ''' FROM Tools, View timings:
NetworkInfo().os_curl(): timeout 0.2 curl -s -H "Content-Type: application/json; 
charset=UTF-8"  -H "X-Auth-PSK: 123" --data 
    '{"method": "setPowerSavingMode", "id": 52, "params": [{"mode": "pictureOff"}], 
    "version": "1.0"}'
http://192.168.0.19/sony/system
        '''

        ''' FROM Tools, View timings:
NetworkInfo().curl(): timeout 0.2 curl -s -H "Content-Type: application/json; 
charset=UTF-8" -H "X-Auth-PSK: 123" --data 
    {"method": "setPowerSavingMode", "id": 52, "params": [{"mode": "pictureOff"}], 
    "version": "1.0"} 
http://192.168.0.19/sony/system

        What "normal" looks like:

NetworkInfo().curl(): timeout 0.2 curl -s -H "Content-Type: application/json; 
charset=UTF-8" -H "X-Auth-PSK: 123" --data 
    {"method": "getPowerStatus", "id": 50, "params": [], 
    "version": "1.0"} 
http://192.168.0.19/sony/system
        
        '''
        self.checkReply(reply_dict, RESTid)

        try:
            err = reply_dict['error']
            return "Err: " + str(err[0])  # 403, Forbidden
        except KeyError:
            pass  # No error

        return "Pic. OFF"

    def getAllSettings(self, no_log=True):
        """ Get ALL Sony Bravia KDL TV Settings """

        curr_logging = GLO['LOG_EVENTS']
        if no_log and curr_logging:
            GLO['LOG_EVENTS'] = False  # Override event logging

        self.getPower()
        self.getVolume(target="headphones")
        self.getVolume()  # Only gets speaker volume, not headphones volume
        self.getSoundSettings()
        self.getPowerSavingMode()
        self.tvPosition = self.getSpeakerSettings()  # target="tvPosition"
        self.subwooferLevel = self.getSpeakerSettings(target="subwooferLevel")
        self.subwooferFreq = self.getSpeakerSettings(target="subwooferFreq")
        self.subwooferPhase = self.getSpeakerSettings(target="subwooferPhase")
        self.subwooferPower = self.getSpeakerSettings(target="subwooferPower")

        if no_log and curr_logging:
            GLO['LOG_EVENTS'] = True  # Restore event logging

    def getSoundSettings(self, forgive=False):
        """ Get Sony Bravia KDL TV Sound Settings (Version 1.1)
https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/audio/v1_1/getSoundSettings/index.html

        Returns:

        If "target" is "outputTerminal"
            "speaker" - Audio is output from the speaker.
            "speaker_hdmi" - Audio is output from the speaker and HDMI.
            "hdmi" - Audio is output from HDMI.
            "audioSystem" - Audio is output from HDMI or digital audio output.

        """

        RESTid = "73"
        _who, JSON_str = self.makeCommon("getSoundSettings", RESTid,
                                         '[{"target": "outputTerminal"}]', ver="1.1")
        reply_dict = ni.curl(JSON_str, "audio", self.ip, RESTid, forgive=forgive)
        self.checkReply(reply_dict, RESTid)
        # USB Subwoofer is off:
        # SonyBraviaKdlTV().getSoundSettings(): curl reply_dict: {'result': [[
        # {'currentValue': 'speaker', 'target': 'outputTerminal'}]], 'id': 73}

        # USB Subwoofer is on:
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
            self.outputTerminal = reply
        except (KeyError, IndexError):
            reply = reply_dict  # Probably "7" for not a Sony TV
        v2_print(_who, "curl reply:", reply)
        # SonyBraviaKdlTV().getSoundSettings(): curl reply: speaker

        return reply

    def getSpeakerSettings(self, target="tvPosition", forgive=False):
        """ Get Sony Bravia KDL TV Speaker Settings
https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/audio/v1_0/getSpeakerSettings/index.html

        Return values based on target parameter:

            '"params": [{"target": "tvPosition"}], "version": "1.0"}'  # tableTop
            '"params": [{"target": "subwooferLevel"}], "version": "1.0"}'  # 17
            '"params": [{"target": "subwooferFreq"}], "version": "1.0"}'  # 10
            '"params": [{"target": "subwooferPhase"}], "version": "1.0"}'  # normal
            '"params": [{"target": "subwooferPower"}], "version": "1.0"}'  # on
        """

        RESTid = "67"
        parm = '[{"target": "' + target + '"}]'
        _who, JSON_str = self.makeCommon("getSpeakerSettings", RESTid, parm)
        reply_dict = ni.curl(JSON_str, "audio", self.ip, RESTid, forgive=forgive)
        self.checkReply(reply_dict, RESTid)

        try:
            reply = reply_dict['result'][0][0]['currentValue']
        except (TypeError, KeyError, IndexError):
            reply = reply_dict  # Probably "7" for not a Sony TV

        return reply

    def setStartupVolume(self, target="speaker", forgive=False):
        """ Set volume to normal between 9am - 10pm or quiet 10pm - 9 am """
        _who = self.who + "setStartupVolume():"
        if self.powerStatus != "ON":
            v0_print(_who, "Sony 'powerStatus' != 'ON': '" + self.powerStatus + "'.")
            return

        isEventLogging = GLO['LOG_EVENTS']  # Log all suspend events
        GLO['LOG_EVENTS'] = True  # Log volume command events
        self.getVolume()

        curr_volume = int(self.volumeSpeaker)  # Could be self.volumeHeadphone. Not supported.
        hour = dt.datetime.today().hour
        v1_print(_who, "Current value of self.volumeSpeaker:", self.volumeSpeaker,
                 "\n  Hour of day:", hour)

        isNormal = True if 9 <= hour <= 20 else False
        isQuiet = not isNormal

        volume_str = ""  # No volume change
        if isNormal and curr_volume < GLO['NORMAL_VOLUME']:
            volume_str = str(GLO['NORMAL_VOLUME'])
        if isQuiet and curr_volume > GLO['QUIET_VOLUME']:
            volume_str = str(GLO['QUIET_VOLUME'])

        if volume_str:
            self.setVolume(volume_str, target=target, forgive=forgive)
        GLO['LOG_EVENTS'] = True if isEventLogging else False

    def getVolume(self, target="speaker", forgive=False):
        """ Get Sony Bravia KDL TV volume
            Currently just speaker volume, but headphone volume can be returned too.
        """

        RESTid = "33"
        _who, JSON_str = self.makeCommon("getVolumeInformation", RESTid, '[]')
        reply_dict = ni.curl(JSON_str, "audio", self.ip, RESTid, forgive=forgive)
        v2_print(_who, "curl reply_dict:", reply_dict)
        # SonyBraviaKdlTV().getVolume(): curl reply_dict: {'result': [[
        # {'volume': 28, 'maxVolume': 100, 'minVolume': 0, 'target': 'speaker', 'mute': False},
        # {'volume': 15, 'maxVolume': 100, 'minVolume': 0, 'target': 'headphone', 'mute': False}
        # ]], 'id': 33}

        try:
            if target == "speaker":
                reply = reply_dict['result'][0][0]['volume']
                self.volumeSpeaker = reply
            elif target == "headphones":
                reply = reply_dict['result'][0][1]['volume']  # headphones
                self.volumeHeadphones = reply
            else:
                v0_print(_who, "Unknown target:", target)
                reply = "0"
            self.volume = reply
        except (KeyError, IndexError):
            reply = reply_dict  # Probably "7" for not a Sony TV
        v2_print(_who, "curl reply:", reply)
        # SonyBraviaKdlTV().getVolume(): curl reply: 28

        return reply

    def setVolume(self, volume, target="speaker", forgive=False):
        """ Set Sony Bravia KDL TV volume

            Version 1.0:
            https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/
                audio/v1_0/setAudioVolume/index.html
                {
                    "method": "setAudioVolume",
                    "id": 601,
                    "params": [{
                        "volume": "18",
                        "target": "speaker"
                    }],
                    "version": "1.0"
                }

            Version 1.2 (display volume level on TV) gets Error code 403 (Forbidden):
            https://pro-bravia.sony.net/develop/integrate/rest-api/spec/service/
                audio/v1_2/setAudioVolume/index.html
                {
                    "method": "setAudioVolume",
                    "id": 98,
                    "params": [{
                        "volume": "5",
                        "ui": "on",
                        "target": "speaker"
                    }],
                    "version": "1.2"
                }

        """

        if True is True:
            RESTid = "601"
            params = '[{"volume": "' + str(volume) + '", "target": "' + target + '"}]'
            ver = "1.0"
        else:
            RESTid = "98"
            params = '[{"volume":"' + str(volume) + \
                     '", "ui": "on", "target": "' + target + '"}]'
            ver = "1.2"  # Unsupported version error: "[14, '1.2']"

        _who, JSON_str = self.makeCommon("setAudioVolume", RESTid, params, ver=ver)
        reply_dict = ni.os_curl(JSON_str, "audio", self.ip, RESTid, forgive=forgive)
        v2_print(_who, "curl reply_dict:", reply_dict)
        self.checkReply(reply_dict, RESTid)

        ''' Resume Error 2025-05-26
SonyBraviaKdlTV().setStartupVolume(): Current value of self.volumeSpeaker: 21 
  Hour of day: 15
SonyBraviaKdlTV().setVolume(): Error: 40801 -- "Volume is out of range"

Running via Tools Dropdown Menu doesn't cause a problem though?

        '''

        try:
            err = reply_dict['error']
            v0_print(_who, "Error:", err[0])
            return "Err: " + str(err[0])  # 403, Forbidden
            # error only occurs when using ni.curl() instead of ni.os_curl()
        except KeyError:
            pass  # No error

    def isDevice(self, forgive=False):
        """ Return True if active or standby, False if power off or no communication
            If forgive=True then don't report pipe.returncode != 0

            Consider generic call to PowerStatus using isDevice, TestSonyOn and TestSonyOff
        """

        _who = self.who + "isDevice():"
        v3_print(_who, "Test if device is a Sony Bravia KDL TV:", self.ip)

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

        If Android devices aren't automatically discovered:

            adb kill-server && adb start-server
            devices -l
            # if android device missing:
                adb connect <IP address>
            # Run File Dropdown Menu option "Rediscover now"

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
            turnOn() - timeout 0.5 adb shell input key event KEYCODE_WAKEUP
            turnOff() - timeout 0.5 adb shell input key event KEYCODE_SLEEP

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
        self.checkDependencies(self.requires, self.installed)
        _who = self.who + "__init__():"
        v3_print(_who, "Dependencies:", self.requires)
        v3_print(_who, "Installed?  :", self.installed)

        if not self.dependencies_installed:
            v1_print(_who, "TCL Google Android TV dependencies are not installed.")

    def Connect(self, forgive=False):
        """ Wakeonlan and Connect to TCL / Google Android TV in a loop until isDevice().
            Called on startup. Also called from turnOff() and turnOn().

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
            command_line_list = ["adb", "connect", self.ip]  # can take 6 seconds
            _event = self.runCommand(command_line_list, _who, forgive=forgive)

            # Reply = "connected to 192.168.0.17:5555"
            # Reply = "already connected to 192.168.0.17:5555"
            # Reply = "unable to connect to 192.168.0.17:5555"
            # Reply = "error: device offline"

            cnt += 1
            if cnt > 60:
                v0_print(_who, "Timeout after", cnt, "attempts")
                return False

        return True  # isDevice() returned True ("connected" in reply)

    def getPower(self, forgive=False):
        """ Return "ON", "OFF" or "?".
            Calls 'timeout 2.0 adb shell dumpsys input_method | grep -i screenon'
                which replies with 'true' or 'false'.

2025-04-22 broken in morning: screenOn no longer appears. Worked in afternoon

adb shell dumpsys input_method | grep -i "screenOn"
    screenOn = true
────────────────────────────────────────────────────────────────────────────────────────────
adb shell dumpsys power | grep -i "Display Power"
Display Power: state=ON
────────────────────────────────────────────────────────────────────────────────────────────
adb shell dumpsys display| grep -i mScreenState
  mScreenState=ON

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
                if event['returncode'] == 124:
                    v1_print(_who, self.ip, "timeout after:", GLO['ADB_PWR_TIME'])
                    self.powerStatus = "?"  # Can be "ON", "OFF" or "?"
                    return self.powerStatus
            self.powerStatus = "? " + str(event['returncode'])
            return self.powerStatus

        Reply = event['output']

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

    def turnOn(self, forgive=False):
        """ Turn On TCL / Google Android TV.
            Send KEYCODE_WAKEUP 5 times until screenOn = true
        """

        _who = self.who + "turnOn():"
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

    def turnOff(self, forgive=False):
        """ Send 'adb shell input keyevent KEYCODE_SLEEP' """

        _who = self.who + "turnOff():"
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
        v2_print(_who, "Test if device is a TCL Google Android TV:", self.ip)

        if timeout is None:
            timeout = GLO['ADB_CON_TIME']
        command_line_list = ["timeout", timeout, "adb", "connect", self.ip]

        # 2025-04-22 upgrade to self.runCommand to log events
        event = self.runCommand(command_line_list, _who, forgive=forgive)
        v2_print(_who, "reply from grep 'screenOn':", event['output'], event['error'])

        if event['returncode'] != 0:
            if forgive is False:
                if event['returncode'] == 124:
                    v0_print(_who, self.ip, "timeout after:", timeout)
                else:
                    v0_print(_who, self.ip, "Return Code:", event['returncode'])
                    v0_print(_who, self.ip, "Error:", self.cmdError)
            return False

        Reply = event['output']

        ''' 2025-04-22 old code
        pipe = sp.Popen(command_line_list, stdout=sp.PIPE, stderr=sp.PIPE)
        text, err = pipe.communicate()  # This performs .wait() too

        v3_print(_who, "Results from '" + command_line_str + "':")
        Reply = text.decode().strip()  # 2025-02-09 add decode() for Python 3
        v3_print(_who, "Reply: '" + Reply + "' | type:", type(Reply), len(Reply))
        v3_print(_who, "err: '" + err.decode().strip() + "'  | pipe.returncode:",
                 pipe.returncode)

        if not pipe.returncode == 0:
            if forgive is False:
                v0_print(_who, "pipe.returncode:", pipe.returncode)
            return False
        '''

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
        self.checkDependencies(self.requires, self.installed)
        v2_print(self.who, "Dependencies:", self.requires)
        v2_print(self.who, "Installed?  :", self.installed)

        self.BluetoothStatus = "?"  # "ON" or "OFF" set by getBluetoothStatus
        self.hci_device = "hci0"  # "hci0" is the default used by trionesControl.py
        # but the real name is obtained using `hcitool dev` in getBluetoothStatus()
        self.hci_mac = ""  # Bluetooth chipset MAC address
        self.device = None  # LED Light Strip device instance obtained with MAC address

        self.temp_fname = None  # Temporary filename for all devices report
        self.fake_top = None  # For color chooser placement geometry

        # Parameter & Statistics dictionaries for breathing colors fine tuning
        self.already_breathing_colors = False  # Is breathing colors running?
        self.powered_off_breathing = False  # Did TurnOff shut down breathing colors?
        self.connect_errors = 0  # Count sequential times auto-reconnect failed.
        # When changing here, change in breatheColors() as well
        self.parm = {}  # breatheColors() parameters
        self.stat = {}  # breatheColors() statistics
        self.FAST_MS = 5  # Global for breatheColors() and monitorBreatheColors()
        self.MAX_FAIL = 18  # Allow 18 connection failures before giving up
        self.red = self.green = self.blue = 0  # Current breathing colors
        self.stepNdx = 0  # Current step index (0-based) within stepping range
        self.monitor_color = None  # Monitor facsimile color of LED light strip

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
                self.turnOn()
            else:
                v2_print(_who, "Turning off LED Light.")
                self.turnOff()
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
        if not self.checkInstalled("hcitool"):
            v0_print(_who, "Program 'hcitool' is not installed.")
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
        """ Reset Bluetooth.
            Called by Application().__init__()
            Called from BLE LED Lights Right-Click menu, Reset Bluetooth
            Called by getBluetoothDevices() - View Dropdown Menu, Bluetooth devices
            LED Lights status on treeview row calls resetBluetooth() if power "?".

            Don't confuse self.BluetoothStatus (bluetooth on radio adapter) with
            self.powerStatus for Bluetooth LED Lights at specified MAC address.

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
        if not self.checkInstalled("hciconfig"):
            msg = "The program `hciconfig` is required to reset Bluetooth.\n\n"
            msg += "sudo apt-get install hciconfig bluez bluez-tools rfkill\n\n"
            self.app.showInfoMsg("Missing program.", msg, icon="error")
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

        '''
        2025-04-30 TODO: if failure display message.
        
        1. rfkill... PASSED
        2. restart bluetooth... PASSED
        3. hciconfig... FAILED
        4. LED Lights connect... SKIPPED
        
        '''
        if event['returncode'] == 0:
            # Bluetooth successfully restarted. Now reset self.hci_device ('hci0')
            msg = "'systemctl restart bluetooth' success."
            msg += "  Attempting reset." if reconnect else msg
            v1_print(_who, "\n  " + msg)
            command_line_list = ["sudo", "hciconfig", self.hci_device, "reset"]
            _event = self.runCommand(command_line_list, _who, forgive=False)
            status = "ON"
        else:
            v0_print(_who, "\n  " +
                     "'systemctl restart bluetooth' FAILED !")
            status = "OFF"

        if reconnect:
            v1_print(_who, "Bluetooth status:", status, "attempting self.Connect()")
            self.Connect(sudo_reset=True)
            v1_print(_who, self.name, "self.device:", self.device)

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
            self.app.updateDropdown()

        return GLO['SUDO_PASSWORD']

    def getBluetoothDevices(self, show_unknown=False, reconnect=True):
        """ Get list of all bluetooth devices (including unknown)

        NOTE: Called with inst.getBluetoothDevices()

        $ sudo timeout 10 hcitool -i hci0 lescan > devices.txt &

        $ sort devices.txt | uniq -c | grep -v unknown

        """
        _who = self.who + "getBluetoothDevices():"

        if self.app is None:
            v0_print(_who, "Cannot start until GUI is running.")
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
        f = os.popen(self.cmdString)

        returncode = f.close()  # https://stackoverflow.com/a/70693068/6929343
        self.cmdReturncode = returncode


        self.app.resumeWait(timer=GLO['BLUETOOTH_SCAN_TIME'], alarm=False,
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

        new = colorchooser.askcolor(  # value 1 turns color off, value 2 very very dim.
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
        return self.powerStatus

    def breatheColors(self, low=4, high=30, span=6.0, step=0.275, bots=1.5, tops=0.5):
        """ Breathe Colors: R, R&G, G, G&B, B, B&R

            Automatically called by BluetoothLedLightStrip.turnOn() method.
            BluetoothLedLightStrip.turnOn() method is automatically called
            during homa.py startup and resuming from suspend. Manually called via
            Right Click in Network Devices Treeview menu for LED light strip.

            OVERVIEW:
            Suspends self.refreshApp() running in self.App.__init__() loop.
            Calls cr.inst.breatheColors() which loops forever and:
                Exit if app.isActive is False
                Exit if self.already_breathing_colors is False
                Calls app.refreshApp after each LED set color as time permits

        :param low: Low value (darkest) E.G. 4 (Too low and lights might turn off)
        :param high: High value (brightest) E.G. 30 (Max is 255 which is too bright)
        :param span: Float seconds for one way transition E.G. 6.0 = 6 second breathe
        :param step: Float seconds to hold each step E.G. 0.275 = 21 steps if span is 6
        :param bots: Float seconds to hold bottom step E.G. 1.5 = hold dimmest 1.5 secs
        :param tops: Float seconds to hold top step E.G. 0.5 = hold brightest .5 seconds
        """
        _who = self.who + "breatheColors():"
        if self.already_breathing_colors:  # Should not happen but check anyway
            v0_print("\n" + ext.ch(), _who, "Already running breathing colors.")
            return
        if self.device is None:
            # 2025-02-11 Resuming from suspend when device not connected.
            err = "Cannot start 'Breathe Colors'. Turn on first."
            self.showMessage(err=err, count=0)  # Bluetooth device not connected to computer
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
        colors = (  # Cycle colors R=Red, G=Green, B=Blue: (R, R+G, G, G+B, B, B+R)
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
        self.app.updateDropdown()  # Allow View dropdown menu option "Breathing stats".
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
                    pygatt.exceptions.NotificationTimeout) as gatt_err:
                if self.connect_errors < self.MAX_FAIL:
                    # Try to connect 5 times. Error after 6th time never displayed
                    self.Connect(retry=self.MAX_FAIL + 1)  # Increments self.connect_errors on failure
                    delta = round(time.time() - GLO['APP_RESTART_TIME'], 2)
                    v1_print("{0:>8.2f}".format(delta), "|", _who, "Attempted reconnect:",
                             self.connect_errors + 1, "time(s).")
                else:
                    # Attempted to connect self.MAX_FAIL times.
                    self.showMessage(gatt_err, count=self.connect_errors)

                return False

        def myMonitorColor(me, other1, other2, trace=None):
            """ Calculate monitor color to display facsimile of LED Lights color.
                low color is very dark. E.G Dark Red (80, 0, 0).
                As color percentage increases gradually add color.

                'me' is my color percentage. 'other1' and 'other2' are the other two.
                Percentage is fraction E.G. 1.0 = 100%, 0.5 = 50% and 0.25 = 25%
            """
            all_percent = me + other1 + other2
            if all_percent > 100.0:
                v0_print("all_percent > 100.0:", me, other1, other2, trace)
                all_percent = 100.0
            if me == 0.0:
                my_col = int(all_percent * .25)
            else:
                my_col = int(75 + me * 180)
                if my_col < 0:
                    v0_print("my_col < 0:", me, other1, other2, trace)
                    my_col = 0
                if my_col > 255:
                    v0_print("my_col > 255:", my_col, me, other1, other2, trace)
                    my_col = 255
            return int(my_col)

        def _myMonitorColor2(me, other1, other2, trace=None):
            """ Calculate monitor color to display facsimile of LED Lights color.
                No color is very light grey (240, 240, 240).
                As color percentage increases gradually add color (by subtracting
                other colors)

                rp, gp, bp are red, green and blue percentage as a fraction.
                E.G. .5 = 50% and .25 = 25%
            """
            all_percent = me + other1 + other2
            if all_percent > 100.0:
                v0_print("all_percent > 100.0:", me, other1, other2, trace)
                all_percent = 100.0
            if me == 0.0:
                my_col = int(100.0 - all_percent * 1.25)
                my_col = 0 if my_col < 0 else 0  # Intentionally driven negative.
            else:
                my_col = int(269.0 - me * 200.0)
                if my_col < 0:
                    v0_print("my_col < 0:", me, other1, other2, trace)
                    my_col = 0
                if my_col > 255:
                    v0_print("my_col > 255:", my_col, me, other1, other2, trace)
                    my_col = 255
            return int(my_col)

        def setColor():
            """ Calculate color and call sendCommand to Bluetooth """
            tr, tg, tb = colors[color_ndx]  # Turn on red, green, blue?
            num_colors = sum(colors[color_ndx])  # How many colors are used?
            if True is False:  # Dummy to make pycharm happy
                _myMonitorColor2(1, 2, 3)

            if turning_up is True:
                if self.stepNdx == 0:
                    brightness = low
                elif self.stepNdx == step_count - 1:  # Last index in range?
                    brightness = high
                else:
                    brightness = low + int(self.stepNdx * step_amount)
            else:
                if self.stepNdx == 0:
                    brightness = high
                elif self.stepNdx == step_count - 1:  # Last index in range?
                    brightness = low
                else:
                    brightness = high - int(self.stepNdx * step_amount)

            brightness = low if brightness < low else brightness
            brightness = high if brightness > high else brightness

            if cp.sunlight_percent > 0:  # Additional brightness for sunlight % > 0
                new_high = high + int((float(high) * cp.sunlight_percent) / 100.0)
                brightness += int((float(brightness) * cp.sunlight_percent) / 100.0)
            else:
                new_high = high

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

            ''' Override red+green has too much green GLO['LED_RED+GREEN_ADJ'] '''
            if GLO['LED_RED+GREEN_ADJ'] is True and self.red and self.green:
                self.green = int(self.green / 2)  # turns olive into yellow
                self.red = int(brightness - self.green)
                if self.green == 1 and self.red > 2:  # Value of 1 is LED light off.
                    self.green += 1  # Green becomes 2, the dimmest possible color.
                    self.red -= 1  # Red decremented to compensate for Green increment.

            ''' Set LED facsimile color for computer monitor display '''
            rp = float(self.red) / float(new_high)  # rp = red percentage
            gp = float(self.green) / float(new_high)
            bp = float(self.blue) / float(new_high)
            rc = myMonitorColor(rp, gp, bp, "red")  # rc = red color
            gc = myMonitorColor(gp, rp, bp, "green")
            bc = myMonitorColor(bp, rp, gp, "blue")
            self.monitor_color = "#%02x%02x%02x" % (rc, gc, bc)  # Hex = #f9f9f9

            return sendCommand() and self.powerStatus == "ON"

        def refresh(ms):
            """ Call self.app.refreshApp() in loop for designated milliseconds. """
            while ms > 0:
                self.app.last_refresh_time = time.time()
                tk_after = False if ms < GLO['REFRESH_MS'] else True
                rst = time.time()
                self.app.refreshApp(tk_after=tk_after)
                #app.refreshApp(tk_after=tk_after)  # 2025-06-19 Display doesn't update
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
            if self.stepNdx == step_count - 1:  # Last step?
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
            for self.stepNdx in range(step_count):
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
                break

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
        self.app.updateDropdown()  # Disable "View" dropdown menu option "Breathing stats".

    def monitorBreatheColors(self, test=False):
        """ Format statistics generated inside self.breatheColors() method.
            Called by Application DisplayBreathing().
        """
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

            NOTE: Original design of tc.connect is to wait 30 seconds. This was changed to
            waiting 1 second with 18 retries.

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
            v1_print(_who, "Invalid GLO['LED_LIGHTS_MAC']:", GLO['LED_LIGHTS_MAC'])
            self.device = None
            self.powerStatus = "?"
            return self.device

        self.cmdStart = time.time()
        self.cmdCommand = ["tc.connect", GLO['LED_LIGHTS_MAC']]
        self.cmdString = ' '.join(self.cmdCommand)

        try:
            self.device = tc.connect(GLO['LED_LIGHTS_MAC'], reset_on_start=sudo_reset)
            self.connect_errors = 0  # Reset connect error counter
        except tc.pygatt.exceptions.NotConnectedError as err:
            v2_print(_who, "error:")
            v2_print(err)
            v2_print("Is bluetooth enabled?")
            self.device = None
            self.powerStatus = "?"

            # Count sequential errors and after x times showInfoMsg()
            self.connect_errors += 1
            if self.connect_errors > retry:
                # if self.app.suspending or self.app.resuming no message
                self.showMessage(err, count=self.connect_errors)
                self.connect_errors = 0  # Reset for new sequential count
            else:
                delta = round(time.time() - GLO['APP_RESTART_TIME'], 2)
                delta_str = "{0:>8.2f}".format(delta)  # "99999.99" format
                v1_print(delta_str, "|", _who, "Failed to connect:",
                         self.connect_errors, "time(s).")

                ''' log event and v3_print debug lines '''
                self.cmdOutput = ""
                self.cmdError = "Failed to connect: " + str(self.connect_errors) + \
                                " time(s)."
                self.cmdError += "\n" + str(err)
                self.cmdReturncode = 124  # Assume error is timeout.
                self.cmdDuration = time.time() - self.cmdStart
                self.cmdCaller = _who
                self.logEvent(_who, log=True)
                v2_print(_who, "Just called self.LogEvent(), use View Discovery Errors")

        if self.app:  # Prevent erroneous Resume from Suspend from running
            self.app.last_refresh_time = time.time()

        return self.device

    def showMessage(self, err=None, count=1):
        """ Show error message """
        _who = self.who + "showMessage():"
        self.device = None  # Force connect on next attempt
        self.powerStatus = "?"

        if self.app and self.app.usingDevicesTreeview:
            self.app.refreshPowerStatusForInst(self)

        # 2025-01-24 message appears multiple times in code
        if err is not None:
            msg = str(err) + "\n\n"
        else:
            msg = ""  # No gatttool error message

        if "cannot start" in msg:
            # gatttool could not find computer's bluetooth adapter (driver not running)
            msg += "Wait a minute to see if LED light strips turn on.\n\n"
            msg += "Ensure LED lights can be controlled by your smartphone.\n\n"
            msg += "In HomA, right-click on LED light strips and select:\n"
            msg += "\t'Reset Bluetooth'.\n"
            msg += "\tThen from the same menu, select 'Turn On Bluetooth LED'.\n\n"
            msg += "Turn on bluetooth in Ubuntu. If bluetooth was on and won't\n"
            msg += "restart then reboot. Sometimes two reboots are required.\n"

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
        msg += "Does Ubuntu display your Bluetooth devices? Right-click on LED lights\n"
        msg += "and try 'Reset Bluetooth' and then 'Turn on " + self.name + "' for quick fix."
        v1_print(_who, msg + "\n")
        if self.app is not None:
            if not self.app.suspending and not self.app.resuming and \
                    GLO['APP_RESTART_TIME'] < time.time() - 60:
                self.app.showInfoMsg("Not connected", msg, "error", align="left")
            else:
                v0_print(_who, "\nCannot display message when starting,",
                         "suspending or resuming.")
                v0_print(msg)

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

    def turnOn(self):
        """ Turn On BLE (Bluetooth Low Energy) LED Light Strip. """

        _who = self.who + "turnOn():"
        v2_print("\n" + _who, "Send GATT cmd to:", self.name)

        if self.device is None:
            self.Connect()

        try:
            tc.powerOn(self.device)
            self.already_breathing_colors = False
            self.powerStatus = "ON"  # Can be "ON", "OFF" or "?"
            v1_print(_who, "self.suspendPowerOff:", self.suspendPowerOff)
            # BluetoothLedLightStrip().turnOn(): self.suspendPowerOff: 1
            # BluetoothLedLightStrip().turnOn(): self.suspendPowerOff: 2

            # If suspend turned off power, start breathing
            if self.suspendPowerOff:
                self.breatheColors()  # Restart breathing
                self.suspendPowerOff = 0
            else:
                # 2025-04-22 Always turn on breathe colors
                self.breatheColors()  # Start breathing

            return self.powerStatus  # Success !

        except pygatt.exceptions.NotConnectedError as err:
            v1_print(_who, err)

        except AttributeError:
            v1_print(_who, "AttributeError: self.device:", self.device)

        self.device = None  # Force connect on next attempt
        self.powerStatus = "?"

        return self.powerStatus

    def turnOff(self):
        """ Turn Off BLE (Bluetooth Low Energy) LED Light Strip. """

        _who = self.who + "turnOff():"
        v2_print("\n" + _who, "Send GATT cmd to:", self.name)

        if self.device is None:
            if self.powerStatus == "ON":
                # Power status on but no connection, reconnect to turn off lights
                self.Connect()
            else:
                return  # Already "OFF" or "?"

        try:
            tc.powerOff(self.device)
            self.powerStatus = "OFF"  # Can be "ON", "OFF" or "?"
            self.already_breathing_colors = False
            return self.powerStatus
        except pygatt.exceptions.NotConnectedError as err:
            v0_print(_who, err)
        except AttributeError:
            v0_print(_who, "AttributeError: self.device:", self.device)

        self.device = None  # Force connect on next attempt
        self.powerStatus = "?"
        ''' 2025-05-07 ERRORS when simply turning off LED w/o suspending
Exception in Tkinter callback
Traceback (most recent call last):
  File "/usr/lib/python2.7/lib-tk/Tkinter.py", line 1540, in __call__
    return self.func(*args)
  File "./homa.py", line 5485, in <lambda>
    image=self.img_turn_off, compound=tk.LEFT,
  File "./homa.py", line 5598, in turnOn
    # NetworkInfo().getPower().curl(): event['returncode']: 124
  File "/usr/lib/python2.7/lib-tk/ttk.py", line 1353, in item
    return _val_or_dict(self.tk, kw, self._w, "item", item)
  File "/usr/lib/python2.7/lib-tk/ttk.py", line 299, in _val_or_dict
    res = tk.call(*(args + options))
TclError: invalid command name ".139620849750168.139620849192760"
        
        '''
        return self.powerStatus

    def isDevice(self, forgive=False):
        """ Return True if adb connection for Android device (using IP address).
            When called by Discovery, forgive=True (not used)
        """

        _who = self.who + "isDevice():"
        v2_print(_who, "Test if device is a Bluetooth LED Light:", self.mac)

        if forgive:
            pass  # Make pycharm happy

        if self.mac == GLO['LED_LIGHTS_MAC']:
            v0_print(_who, "MAC address matches:", self.mac)

        return self.mac == GLO['LED_LIGHTS_MAC']


class Application(DeviceCommonSelf, tk.Toplevel):
    """ tkinter main application window
        Dropdown menus File/Edit/View/Tools
        Treeview with 3 columns: image+status, name+IP, alias+MAC+type
        Button bar: Minimize, Sensors, Suspend, Help, Close
    """

    def __init__(self, master=None):
        """ DeviceCommonSelf(): Variables used by all classes
        :param toplevel: Usually <None> except when called by another program.
        """
        DeviceCommonSelf.__init__(self, "Application().")  # Define self.who
        _who = self.who + "__init__():"

        global sm  # Sensors Monitor - Fan speeds and Temperatures

        ''' Sony TV '''
        self.sonySaveInst = None  # 2025-06-20 REVIEW: Use self.sony or self.kdl?

        ''' LED VU Meters, pulseaudio sinks and volume levels '''
        self.audio = AudioControl()  # VU Meter Class instance
        global pav
        pav = self.audio.pav

        ''' Bluetooth Low Energy LED Light Strip Breathing Colors '''
        global ble  # Inside global ble, assign app = Application() which points here
        self.bleSaveInst = None  # For breathing colors monitoring of the real inst
        self.bleScrollbox = None  # Assigned when self.breatheColors() is called.
        self.last_red = self.last_green = self.last_blue = 0  # Display when different.

        self.isActive = True  # Set False when exiting or suspending
        self.requires = ['arp', 'getent', 'timeout', 'curl', 'adb', 'hs100.sh', 'aplay',
                         'ps', 'grep', 'xdotool', 'wmctrl', 'nmcli', 'sensors']
        self.installed = []
        self.checkDependencies(self.requires, self.installed)

        if not self.dependencies_installed:
            v0_print(_who, "Some Application() dependencies are not installed.")
            v0_print(self.requires)
            v0_print(self.installed)

        ''' TkDefaultFont changes default font everywhere except tk.Entry in Color Chooser '''
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=g.MON_FONT)
        text_font = font.nametofont("TkTextFont")  # tk.Entry fonts in Color Chooser
        text_font.configure(size=g.MON_FONT)
        ''' TkFixedFont, TkMenuFont, TkHeadingFont, TkCaptionFont, TkSmallCaptionFont,
            TkIconFont and TkTooltipFont - It is not advised to change these fonts.
            https://www.tcl-lang.org/man/tcl8.6/TkCmd/font.htm '''

        self.sony_suspended_system = False  # If TV powered off suspended system
        self.suspend_time = 0.0  # last time system suspended
        self.suspending = False  # When True suppress error messages that delay suspend
        self.resume_time = 0.0  # last time system resumed from suspend
        self.resuming = False  # When True suppress error messages that delay resume

        self.last_refresh_time = time.time()  # Refresh idle loop last entered time
        self.rediscovering = False
        self.last_rediscover_time = time.time()
        # self.exitRediscover() resets self.last_rediscover_time & self.rediscovering
        self.last_minute = "0"  # Check sunlight percentage every minute
        self.last_second = "0"  # Update YouTube progress every second
        self.force_refresh_power_time = time.time() + 90.0  # 1 minute after treeview done

        if p_args.fast:
            # Allow 3 seconds to move mouse else start rediscover
            self.last_rediscover_time = time.time() - GLO['REDISCOVER_SECONDS'] + 3
        self.tree = None  # Painted in populateDevicesTree()
        self.photos = None  # Protect populateDevicesTree() images from recycling

        # Button Bar button images
        self.img_minimize = img.tk_image("minimize.png", 26, 26)
        self.img_sensors = img.tk_image("flame.png", 26, 26)
        self.img_devices = img.tk_image("wifi.png", 26, 26)
        self.img_suspend = img.tk_image("lightning_bolt.png", 26, 26)
        self.img_mag_glass = img.tk_image("mag_glass.png", 26, 26)
        self.img_checkmark = img.tk_image("checkmark.png", 26, 26)

        # Right-click popup menu images common to all devices
        self.img_turn_off = img.tk_image("turn_off.png", 42, 26)
        self.img_turn_on = img.tk_image("turn_on.png", 42, 26)
        self.img_up = img.tk_image("up.png", 22, 26)
        self.img_down = img.tk_image("down.png", 22, 26)  # Move down & Minimize
        self.img_close = img.tk_image("close.png", 26, 26)  # Also close button

        # Right-click popup menu images for Sony TV Picture On/Off
        self.img_picture_on = img.tk_image("picture_on.png", 42, 26)
        self.img_picture_off = img.tk_image("picture_off.png", 42, 26)

        # Right-click popup menu images for Bluetooth LED Light Strip
        self.img_set_color = img.tk_image("set_color.jpeg", 26, 26)
        self.img_nighttime = img.tk_image("nighttime.png", 26, 26)
        self.img_breathing = img.tk_image("breathing.jpeg", 26, 26)
        self.img_reset = img.tk_image("reset.jpeg", 26, 26)

        ''' Toplevel window (self) '''
        tk.Toplevel.__init__(self, master)  # https://stackoverflow.com/a/24743235/6929343
        self.minsize(width=120, height=63)
        self.geometry('1200x700')
        self.configure(background="WhiteSmoke")
        self.rowconfigure(0, weight=1)  # Weight 1 = stretchable row
        self.columnconfigure(0, weight=1)  # Weight 1 = stretchable column
        app_title = "HomA - Home Automation"  # Used to find window ID further down
        self.title(app_title)
        self.btn_frm = None  # Used by buildButtonBar(), can be hidden by edit_pref

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

        ''' DisplayCommon() cmdEvents (toolkit.CustomScrolledText) as child window 
            Also used to display Bluetooth devices and Breathing stats '''
        self.event_top = self.event_scroll_active = self.event_frame = None
        self.event_scrollbox = self.event_btn_frm = None

        ''' Save Toplevel OS window ID for minimizing window '''
        self.update_idletasks()  # Make visible for wmctrl. Verified needed 2025-02-13
        self.getWindowID(app_title)

        ''' File/Edit/View/Tools dropdown menu bars - Window ID required '''
        self.file_menu = self.edit_menu = self.view_menu = self.tools_menu = None
        self.buildDropdown()

        ''' Create treeview with internet devices. '''
        self.populateDevicesTree()

        ''' When devices displayed show sensors button and vice versa. '''
        self.sensors_devices_btn = None
        self.sensors_btn_text = "Sensors"  # when Devices active
        self.devices_btn_text = "Devices"  # when Sensors active
        self.suspend_btn = None  # Suspend button on button bar to control tooltip
        self.close_btn = None  # Close button on button bar to control tooltip
        self.main_help_id = "HelpNetworkDevices"  # Toggles to HelpSensors and HelpDevices
        self.usingDevicesTreeview = True  # Startup uses Devices Treeview
        self.buildButtonBar(self.sensors_btn_text)

        # Experiments to delay rediscover when there is GUI activity
        self.minimizing = False  # When minimizing, override focusIn()
        self.bind("<FocusIn>", self.focusIn)  # Raise windows up
        self.bind("<Motion>", self.Motion)  # On motion reset rediscovery timer

        self.last_motion_time = GLO['APP_RESTART_TIME']

        # Monitors and window positions when un-minimizing
        #self.monitors = self.windows = []  # List of dictionaries

        ''' Assign this Application() instance to network devices (inst.app) variable:
                - Laptop Display() and Router() needs to call .GetPassword() method.
                - Sony TV assigned to self.sonySaveInst (Only the last Sony TV!)
                - BLE LED Light Strip() needs to call .showInfoMsg() method.  '''
        for instance in ni.instances:
            inst = instance['instance']
            inst.app = self  # Needed for passwords, showInfoMsg(), refreshApp(), etc
            if inst.type_code == GLO['BLE_LS']:
                # Only one BLE LED Light Strip can be supported.
                self.bleSaveInst = inst  # For breathing colors monitoring
            elif inst.type_code == GLO['KDL_TV']:
                # The last Sony KDL TV in network devices will control audio
                self.sonySaveInst = inst  # Sony TV volume change display

        ble.app = self  # For View Dropdown menu -> Display Bluetooth Devices

        ''' If bluetooth LED Light Strips used, resetBluetooth() always required '''
        if self.bleSaveInst:
            self.bleSaveInst.resetBluetooth()
            self.bleSaveInst.turnOn()

        ''' If Sony TV used, enable Sony Volume controls '''
        self.updateDropdown()

        ''' Polling and processing with refresh tkinter loop forever '''
        while self.refreshApp():  # Run forever until quit
            pass

    def getWindowID(self, title):
        """ Use wmctrl to get window ID in hex and convert to decimal for xdotool
            2025-06-13 (It's Friday 13th!) Test new mon.wm_xid_int
        """
        _who = self.who + "getWindowID():"
        GLO['WINDOW_ID'] = None  # Integer HomA OS Window ID
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

        # 2025-06-13 Test new mon.wm_xid_int
        mon = monitor.Monitors()
        mon.make_wn_list()  # Make Wnck list of all windows
        # if mon.get_wn_by_name(title):
        # GLO['WINDOW_ID'] = mon.wn_xid_int

        v2_print(_who, "GLO['WINDOW_ID']:", GLO['WINDOW_ID'])
        if GLO['WINDOW_ID'] is None:
            v0_print(_who, "ERROR `wmctrl` could not find Window.")
            v0_print("Search for title failed: '" + title + "'.\n")

    def buildDropdown(self):
        """ Build dropdown Menu bars: File, Edit, View & Tools """

        def forgetPassword():
            """ 'Tools' dropdown, 'Forget sudo password' option """
            GLO['SUDO_PASSWORD'] = None  # clear global password in HomA
            command_line_list = ["sudo", "-K"]  # clear password in Linux
            self.runCommand(command_line_list)
            self.updateDropdown()

        mb = tk.Menu(self)
        self.config(menu=mb)

        ''' Full option name is referenced to enable and disable the option. '''
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

        self.file_menu.add_command(label="Suspend", font=g.FONT, underline=0,
                                   command=self.Suspend, state=tk.DISABLED)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", font=g.FONT, underline=1,
                                   command=self.exitApp, state=tk.DISABLED)

        mb.add_cascade(label="File", font=g.FONT, underline=0, menu=self.file_menu)
        self.file_menu.config(activebackground="SkyBlue3", activeforeground="black")

        # Edit Dropdown Menu
        self.edit_menu = tk.Menu(mb, tearoff=0)
        self.edit_menu.add_command(label="Preferences", font=g.FONT, underline=0,
                                   command=self.Preferences, state=tk.NORMAL)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Monitor volume", underline=0,
                                   font=g.FONT, state=tk.DISABLED,
                                   command=self.exitApp)

        mb.add_cascade(label="Edit", font=g.FONT, underline=0, menu=self.edit_menu)
        self.edit_menu.config(activebackground="SkyBlue3", activeforeground="black")

        # View Dropdown Menu
        self.view_menu = tk.Menu(mb, tearoff=0)
        self.view_menu.add_command(label="Sensors", font=g.FONT, underline=0,
                                   command=self.toggleSensorsDevices, state=tk.DISABLED)
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Network devices", font=g.FONT, underline=0,
                                   command=self.toggleSensorsDevices, state=tk.DISABLED)
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Bluetooth devices", font=g.FONT, underline=10,
                                   command=self.DisplayBluetooth, state=tk.DISABLED)
        self.view_menu.add_command(label="Discovery timings", font=g.FONT, underline=10,
                                   command=self.DisplayTimings, state=tk.DISABLED)
        self.view_menu.add_command(label="Discovery errors", font=g.FONT, underline=10,
                                   command=self.DisplayErrors, state=tk.DISABLED)
        self.view_menu.add_command(label="Breathing stats", font=g.FONT, underline=10,
                                   command=self.DisplayBreathing, state=tk.DISABLED)

        mb.add_cascade(label="View", font=g.FONT, underline=0, menu=self.view_menu)
        self.view_menu.config(activebackground="SkyBlue3", activeforeground="black")

        # Tools Dropdown Menu
        self.tools_menu = tk.Menu(mb, tearoff=0)
        lights_menu = tk.Menu(self.tools_menu, tearoff=0)
        lights_menu.add_command(label='ON', font=g.FONT, underline=1, background="green",
                                command=lambda: self.turnAllPower(
                                    'ON', fade=True, type_code=GLO['HS1_SP']))
        lights_menu.add_command(label='OFF', font=g.FONT, underline=1, background="red",
                                command=lambda: self.turnAllPower(
                                    'OFF', fade=True, type_code=GLO['HS1_SP']))
        self.tools_menu.add_cascade(label="Turn all lights power", font=g.FONT,
                                    underline=0, menu=lights_menu)
        lights_menu.config(activebackground="SkyBlue3", activeforeground="black")
        self.tools_menu.add_command(label="Forget sudo password", underline=0,
                                    font=g.FONT, command=forgetPassword, state=tk.DISABLED)

        volume_menu = tk.Menu(self.tools_menu, tearoff=0)
        volume_menu.add_command(label='Normal', font=g.FONT, underline=1, background="green",
                                command=lambda: self.sonySaveInst.setVolume(
                                    GLO['NORMAL_VOLUME']), state=tk.NORMAL)
        volume_menu.add_command(label='Quiet', font=g.FONT, underline=1, background="red",
                                command=lambda: self.sonySaveInst.setVolume(
                                    GLO['QUIET_VOLUME']), state=tk.NORMAL)
        self.tools_menu.add_cascade(label="Sony TV volume level", font=g.FONT,
                                    underline=0, menu=volume_menu, state=tk.DISABLED)
        volume_menu.config(activebackground="SkyBlue3", activeforeground="black")

        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="Configure YouTube Ads", font=g.FONT,
                                    underline=18, command=self.configureYouTube,
                                    state=tk.DISABLED)
        self.tools_menu.add_command(label="Watch YouTube Ad-mute", font=g.FONT,
                                    underline=0, command=self.watchYouTube,
                                    state=tk.DISABLED)

        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="Big number calculator", font=g.FONT,
                                    underline=0, command=self.openCalculator,
                                    state=tk.DISABLED)
        self.tools_menu.add_command(label="Timer " + str(GLO['TIMER_SEC']) + " seconds",
                                    font=g.FONT, underline=0,
                                    command=lambda: self.resumeWait(timer=GLO['TIMER_SEC']))
        theme_menu = tk.Menu(self.tools_menu, tearoff=0)
        #     # background="LemonChiffon"    VERY NICE Debug information
        #     # background="NavajoWhite"     VERY NICE
        #     # background="LightSalmon"     BEST at night
        theme_menu.add_command(label='WhiteSmoke', font=g.FONT, underline=0,
                               background="WhiteSmoke",
                               command=lambda: self.setColorScheme('WhiteSmoke'))
        theme_menu.add_command(label='LemonChiffon', font=g.FONT, underline=0,
                               background="LemonChiffon",
                               command=lambda: self.setColorScheme('LemonChiffon'))
        theme_menu.add_command(label='NavajoWhite', font=g.FONT, underline=0,
                               background="NavajoWhite",
                               command=lambda: self.setColorScheme('NavajoWhite'))
        theme_menu.add_command(label='LightSalmon', font=g.FONT, underline=5,
                               background="LightSalmon",
                               command=lambda: self.setColorScheme('LightSalmon'))
        self.tools_menu.add_cascade(label="Color scheme", font=g.FONT,
                                    underline=0, menu=theme_menu)
        theme_menu.config(activebackground="SkyBlue3", activeforeground="black")
        mb.add_cascade(label="Tools", font=g.FONT, underline=0,
                       menu=self.tools_menu)
        self.tools_menu.config(activebackground="SkyBlue3", activeforeground="black")

    def updateDropdown(self):
        """ Enable/Disable options on Dropdown Menu """

        if not self.isActive:
            return

        ''' File Menu '''
        # During rediscovery, the "Rediscover now" dropdown menubar option disabled
        if self.rediscovering is True:
            self.file_menu.entryconfig("Rediscover now", state=tk.DISABLED)
            self.file_menu.entryconfig("Suspend", state=tk.DISABLED)
            self.file_menu.entryconfig("Exit", state=tk.DISABLED)
            self.suspend_btn['state'] = tk.DISABLED
            self.close_btn['state'] = tk.DISABLED
        else:
            self.file_menu.entryconfig("Rediscover now", state=tk.NORMAL)
            self.file_menu.entryconfig("Suspend", state=tk.NORMAL)
            self.file_menu.entryconfig("Exit", state=tk.NORMAL)
            self.suspend_btn['state'] = tk.NORMAL
            self.close_btn['state'] = tk.NORMAL

        ''' Edit Menu '''
        # 2024-12-01 - Edit menu options not written yet
        self.edit_menu.entryconfig("Preferences", state=tk.NORMAL)
        self.edit_menu.entryconfig("Monitor volume", state=tk.DISABLED)

        ''' View Menu '''
        # Default to enabled
        self.view_menu.entryconfig("Bluetooth devices", state=tk.NORMAL)
        self.view_menu.entryconfig("Discovery timings", state=tk.NORMAL)

        # Enable options depending on Sensors Treeview or Devices Treeview mounted
        if self.usingDevicesTreeview:  # Devices Treeview is displayed
            self.view_menu.entryconfig("Network devices", state=tk.DISABLED)
            self.view_menu.entryconfig("Sensors", state=tk.NORMAL)
        else:  # Sensors Treeview is displayed
            self.view_menu.entryconfig("Sensors", state=tk.DISABLED)
            self.view_menu.entryconfig("Network devices", state=tk.NORMAL)

        if GLO['EVENT_ERROR_COUNT'] == 0:
            self.view_menu.entryconfig("Discovery errors", state=tk.DISABLED)
        else:
            self.view_menu.entryconfig("Discovery errors", state=tk.NORMAL)

        if self.bleSaveInst and self.bleSaveInst.already_breathing_colors:
            self.view_menu.entryconfig("Breathing stats", state=tk.NORMAL)
        else:
            self.view_menu.entryconfig("Breathing stats", state=tk.DISABLED)

        # If one child view is running, disable all child views from starting.
        if self.event_scroll_active:
            self.view_menu.entryconfig("Bluetooth devices", state=tk.DISABLED)
            self.view_menu.entryconfig("Discovery timings", state=tk.DISABLED)
            self.view_menu.entryconfig("Discovery errors", state=tk.DISABLED)
            self.view_menu.entryconfig("Breathing stats", state=tk.DISABLED)

        ''' Tools Menu '''
        self.tools_menu.entryconfig("Configure YouTube Ads", state=tk.NORMAL)
        self.tools_menu.entryconfig("Watch YouTube Ad-mute", state=tk.NORMAL)
        self.tools_menu.entryconfig("Big number calculator", state=tk.NORMAL)
        if GLO['SUDO_PASSWORD'] is None:
            self.tools_menu.entryconfig("Forget sudo password", state=tk.DISABLED)
        else:
            self.tools_menu.entryconfig("Forget sudo password", state=tk.NORMAL)
        if self.sonySaveInst and GLO['ALLOW_VOLUME_CONTROL']:
            self.tools_menu.entryconfig("Sony TV volume level", state=tk.NORMAL)
        else:
            self.tools_menu.entryconfig("Sony TV volume level", state=tk.DISABLED)

    def exitApp(self, kill_now=False, *_args):
        """ <Escape>, X on window, 'Exit from dropdown menu or Close Button"""
        _who = self.who + "exitApp():"

        self.suspend_btn['state'] = tk.NORMAL  # 2025-02-11 color was staying blue

        ''' Is it ok to stop processing? - Make common method... '''
        msg = None
        if self.dtb:  # Cannot Close when resume countdown timer is running.
            msg = "Countdown timer is running."
        if self.rediscovering:  # Cannot suspend during rediscovery.
            msg = "Device rediscovery is in progress for a few seconds."

        if msg and not kill_now:  # Cannot suspend when other jobs are active
            self.showInfoMsg("Cannot Close now.", msg, icon="error")
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
            order.append(cr.mac)

        self.win_grp.destroy_all(tt=self.tt)  # Destroy Calculator and Countdown

        self.isActive = False  # Signal closing down so methods return

        ''' Save files '''
        ni.view_order = order
        save_files()

        ''' reset to original SAVE_CWD (saved current working directory) '''
        if SAVE_CWD != g.PROGRAM_DIR:
            v1_print("Changing from g.PROGRAM_DIR:", g.PROGRAM_DIR,
                     "to SAVE_CWD:", SAVE_CWD)
            os.chdir(SAVE_CWD)

        ''' Print `sensors` statistics - 9,999,999 right aligned. '''
        if sm.number_logs:
            v0_print()
            v0_print("sm.skipped_checks  :", "{:,d}".format(sm.skipped_checks).rjust(9))
            v0_print("sm.number_checks   :", "{:,d}".format(sm.number_checks).rjust(9))
            v0_print("sm.skipped_fan_same:", "{:,d}".format(sm.skipped_fan_same).rjust(9))
            v0_print("sm.skipped_fan_diff:", "{:,d}".format(sm.skipped_fan_diff).rjust(9))
            v0_print("sm.skipped_logs    :", "{:,d}".format(sm.skipped_logs).rjust(9))
            v0_print("sm.number_logs     :", "{:,d}".format(sm.number_logs).rjust(9))

        ''' If bluetooth LED Light Strips used, turnOff() for next HomA startup '''
        if self.bleSaveInst:
            self.bleSaveInst.turnOff()

        if self.winfo_exists():
            self.destroy()  # Destroy toplevel
        exit()  # exit() required to completely shut down app

    def minimizeApp(self, *_args):
        """ Minimize GUI Application() window using xdotool. """
        _who = self.who + "minimizeApp():"
        # noinspection SpellCheckingInspection
        command_line_list = ["xdotool", "windowminimize", str(GLO['WINDOW_ID'])]
        self.runCommand(command_line_list, _who)

    def focusIn(self, *_args):
        """ Window or menu in focus, disable rediscovery. Raise child windows above.

            NOTES: 1. Triggered two times so test current state for first time status.
                   2. When the right-click menu is closed it registers FocusOut and
                      toplevel registers focusIn again.
                   3. If preferences Notebook is active and countdown timer is started
                      the digits never appear and linux locks up totally. Mouse movement
                      can still occur but that is all. As of 2024-12-27.
        """

        if self.event_scroll_active and self.event_top:
            self.event_top.focus_force()
            self.event_top.lift()

        # 2024-12-28 Causes Xorg to freeze screen refresh.
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
            This will break resumeFromSuspend() action to force rediscovery

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
                        background=GLO['TREEVIEW_COLOR'],
                        fieldbackground=GLO['TREEVIEW_COLOR'],
                        edge_color=GLO['TREE_EDGE_COLOR'], edge_px=5)

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
        self.tree.tag_configure('normal', background=GLO['TREEVIEW_COLOR'],
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
            mac_dict = ni.get_mac_dict(mac)
            if len(mac_dict) < 2:
                v0_print(_who, "len(mac_dict) < 2 for MAC:", mac)
                continue

            nr = TreeviewRow(self)  # Setup treeview row processing instance
            nr.New(mac)  # Setup new row
            nr.Add(i)  # Add new row

            # Refresh tree display row by row for processing lag
            if not p_args.fast:
                self.tree.update_idletasks()  # Slow mode display each row.

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
        #style.theme_use("classic")

        style.map("C.TButton",  # Homa command buttons
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

        ''' Suspend Button U+1F5F2  🗲 '''
        self.suspend_btn = device_button(
            #0, 2, u"🗲 Suspend", self.Suspend,
            0, 2, "Suspend", self.Suspend,
            "Power off all devices except suspend computer.", "ne", self.img_suspend)

        ''' Help Button - ⧉ Help - Videos and explanations on pippim.com
            https://www.pippim.com/programs/homa.html#Introduction '''
        help_text = "Open new window in default web browser for\n"
        help_text += "videos and explanations on using this screen.\n"
        help_text += "https://www.pippim.com/programs/homa.html#\n"
        # Instead of "Introduction" have self.help_id with "HelpSensors" or "HelpDevices"
        device_button(0, 3, "Help", lambda: g.web_help(self.main_help_id),
                      help_text, "ne", self.img_mag_glass)

        ''' ✘ CLOSE BUTTON  '''
        # noinspection PyTypeChecker
        self.bind("<Escape>", self.exitApp)  # 2025-05-03 pycharm error appeared today
        self.protocol("WM_DELETE_WINDOW", self.exitApp)
        self.close_btn = device_button(0, 4, "Exit", self.exitApp,
                                       "Exit HomA.", "ne", pic=self.img_close)

    def toggleSensorsDevices(self):
        """ Sensors / Devices toggle button clicked.
            If button text == "Sensors" then active sm.tree.
            If button text == "Devices" then active Applications.tree.

        """
        _who = self.who + "toggleSensorsDevices()"

        # Immediately get rid of tooltip
        self.tt.zap_tip_window(self.sensors_devices_btn)

        # Get current button state and toggle it for next time.
        if "Sensors" in self.sensors_devices_btn['text']:
            self.sensors_devices_btn['text'] = toolkit.normalize_tcl(self.devices_btn_text)
            self.sensors_devices_btn['image'] = self.img_devices
            self.tt.set_text(self.sensors_devices_btn, "Show Network Devices.")
            self.main_help_id = "HelpSensors"
            self.usingDevicesTreeview = False
            self.tree.destroy()  # Destroy Network Devices Treeview
            sm.treeview_active = True
            sm.populateSensorsTree()  # Build Sensors Treeview using sm.Print(start=0, end=-1)
        elif "Devices" in self.sensors_devices_btn['text']:
            self.sensors_devices_btn['text'] = toolkit.normalize_tcl(self.sensors_btn_text)
            self.sensors_devices_btn['image'] = self.img_sensors
            self.tt.set_text(self.sensors_devices_btn, "Show Temperatures and Fans.")
            self.main_help_id = "HelpNetworkDevices"
            self.usingDevicesTreeview = True
            sm.tree.destroy()  # Destroy Sensors Treeview
            sm.treeview_active = False
            self.populateDevicesTree()  # Build Network Devices Treeview
        else:
            v0_print("Invalid Button self.sensors_devices_btn['text']:",
                     self.sensors_devices_btn['text'])
            return

        self.updateDropdown()  # NORMAL/DISABLED options for view Sensors/Devices

    def RightClick(self, event):
        """ Mouse right button click. Popup menu on selected treeview row.

            NOTE: Sub windows are designed to steal focus and lift however,
                  multiple right clicks will eventually cause menu to appear.
                  After selecting an option though, the green highlighting
                  stays in place because fadeOut() never runs.
        """
        item = self.tree.identify_row(event.y)
        help_id = "HelpRightClickMenu"  # Default, override for some instances

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
        name = cr.mac_dict['name']  # name is used in menu option text
        cr.inst.powerStatus = "?" if cr.inst.powerStatus is None else cr.inst.powerStatus
        cr.text = "  " + str(cr.inst.powerStatus)  # Display treeview row new power state
        cr.Update(item)  # Update iid with new ['text']
        self.tree.update_idletasks()  # Slow mode display each row.
        cr.fadeIn(item)  # Trigger 320 ms row highlighting fade in def fadeIn

        ''' If View Breathing Statistics is running, color options are disabled.
            Message cannot be displayed when menu painted because it causes focus out. 
        if self.bleScrollbox and cr.mac_dict['type_code'] == GLO['BLE_LS']:
            title = "View stats disables colors"  # 2025-02-09 - Doesn't work properly.
        else:
            title = None

        if title:
            menu = tk.Menu(self, title=title)  # 2025-02-09 Causes blank selectable bar
            # Once blank bar is clicked the title appears with window close decoration.
        else:
            menu = tk.Menu(self)
        '''
        menu = tk.Menu(self)

        menu.bind("<FocusIn>", self.focusIn)
        menu.bind("<Motion>", self.Motion)

        menu.post(event.x_root, event.y_root)

        if cr.mac_dict['type_code'] == GLO['LAPTOP_D']:
            help_id = "HelpRightClickLaptopDisplay"
            # Laptop display has very fast power status response time. The
            # Pippim movie.sh script powers on/off laptop display with x-idle,
            # so double check backlight power status.
            cr.inst.getPower()  # Set current laptop display cr.inst.powerStatus

        if cr.mac_dict['type_code'] == GLO['KDL_TV']:
            # Sony TV has power save mode to turn picture off and listen to music
            help_id = "HelpRightClickSonyTV"
            menu.add_command(
                label=name + " Picture On ", font=g.FONT, state=tk.DISABLED, compound=tk.LEFT,
                image=self.img_picture_on, command=lambda: self.turnPictureOn(cr))
            menu.add_command(
                label=name + " Picture Off ", font=g.FONT, state=tk.DISABLED, compound=tk.LEFT,
                image=self.img_picture_off, command=lambda: self.turnPictureOff(cr))
            menu.add_command(
                label=name + " Sound Control ", font=g.FONT, state=tk.NORMAL, compound=tk.LEFT,
                image=self.img_mag_glass, command=lambda: self.DisplaySony(cr))

            menu.add_separator()

        if cr.mac_dict['type_code'] == GLO['BLE_LS']:
            # Bluetooth Low Energy LED Light Strip
            help_id = "HelpRightClickBluetooth"
            name_string = "Set " + name + " Color"
            menu.add_command(
                label=name_string, state=tk.DISABLED, image=self.img_set_color,
                compound=tk.LEFT, font=g.FONT, command=lambda: self.setLEDColor(cr))
            menu.add_command(
                label="Nighttime brightness", font=g.FONT, state=tk.DISABLED, compound=tk.LEFT,
                image=self.img_nighttime, command=lambda: self.setLEDNight(cr))
            menu.add_command(
                label="Breathing colors", font=g.FONT, state=tk.DISABLED, compound=tk.LEFT,
                image=self.img_breathing, command=lambda: self.breatheLEDColors(cr))

            menu.add_separator()

            menu.add_command(
                label="View Breathing Statistics", font=g.FONT, image=self.img_mag_glass,
                compound=tk.LEFT, command=self.DisplayBreathing, state=tk.DISABLED)
            menu.add_command(
                label="Reset Bluetooth", font=g.FONT, image=self.img_reset, compound=tk.LEFT,
                command=cr.inst.resetBluetooth, state=tk.DISABLED)
            menu.add_command(
                label="View Bluetooth Devices", font=g.FONT, image=self.img_mag_glass,
                compound=tk.LEFT, command=self.DisplayBluetooth, state=tk.NORMAL)

            # Device must be on for Set Color, Nighttime and Breathing Colors
            state = tk.NORMAL if cr.inst.powerStatus == "ON" else tk.DISABLED

            menu.entryconfig(name_string, state=state)
            menu.entryconfig("Nighttime brightness", state=state)
            if cr.inst.already_breathing_colors is True:
                menu.entryconfig("View Breathing Statistics", state=tk.NORMAL)
                state = tk.DISABLED  # Override if breathing colors already running
            menu.entryconfig("Breathing colors", state=state)

            ''' If View Breathing Statistics is running, must close window first 
                Hard to get here because View lifts itself and steals focus.
            '''
            if self.bleScrollbox:
                menu.entryconfig(name_string, state=tk.DISABLED)
                menu.entryconfig("Nighttime brightness", state=tk.DISABLED)
                menu.entryconfig("Breathing colors", state=tk.DISABLED)
                menu.entryconfig("View Breathing Statistics", state=tk.DISABLED)

            state = tk.NORMAL if cr.inst.device is None else tk.DISABLED
            menu.entryconfig("Reset Bluetooth", state=state)
            menu.add_separator()

        menu.add_command(label="Turn On " + name, font=g.FONT, state=tk.DISABLED,
                         image=self.img_turn_on, compound=tk.LEFT,
                         command=lambda: self.turnOn(cr))
        menu.add_command(label="Turn Off " + name, font=g.FONT, state=tk.DISABLED,
                         image=self.img_turn_off, compound=tk.LEFT,
                         command=lambda: self.turnOff(cr))

        menu.add_separator()
        menu.add_command(label="Move " + name + " Up", font=g.FONT, state=tk.DISABLED,
                         image=self.img_up, compound=tk.LEFT,
                         command=lambda: self.moveRowUp(cr))
        menu.add_command(label="Move " + name + " Down", font=g.FONT, state=tk.DISABLED,
                         image=self.img_down, compound=tk.LEFT,
                         command=lambda: self.moveRowDown(cr))
        menu.add_command(label="Forget " + name, font=g.FONT, image=self.img_close,
                         compound=tk.LEFT, command=lambda: self.forgetDevice(cr))

        menu.add_separator()
        menu.add_command(label="Help", font=g.FONT, command=lambda: g.web_help(help_id),
                         image=self.img_mag_glass, compound=tk.LEFT)
        menu.add_command(label="Close menu", font=g.FONT, command=_closePopup,
                         image=self.img_close, compound=tk.LEFT)

        menu.tk_popup(event.x_root, event.y_root)

        menu.bind("<FocusOut>", _closePopup)

        # Enable Turn On/Off menu options depending on current power status.
        if cr.mac_dict['type_code'] == GLO['KDL_TV'] and cr.inst.powerStatus == "ON":
            cr.inst.getPowerSavingMode()  # Get power savings mode
            if cr.inst.powerSavingMode == "OFF":
                menu.entryconfig(name + " Picture Off ", state=tk.NORMAL)
            elif cr.inst.powerSavingMode == "ON":
                menu.entryconfig(name + " Picture On ", state=tk.NORMAL)
            else:
                pass  # powerSavingMode == "?"

        # Enable turn on/off based on current power status
        if cr.inst.powerStatus != "ON":  # Other options are "OFF" and "?"
            menu.entryconfig("Turn On " + name, state=tk.NORMAL)
        if cr.inst.powerStatus != "OFF":  # Other options are "ON" and "?"
            menu.entryconfig("Turn Off " + name, state=tk.NORMAL)

        # Never allow turning off computer by menu (breaks suspend process)
        if cr.mac_dict['type_code'] == GLO['LAPTOP_B'] or \
                cr.mac_dict['type_code'] == GLO['DESKTOP']:
            menu.entryconfig("Turn Off " + name, state=tk.DISABLED)

        # Enable moving row up and moving row down
        all_iid = self.tree.get_children()  # Get all item iid in treeview
        if item != all_iid[0]:  # Enable moving row up if not at top?
            menu.entryconfig("Move " + name + " Up", state=tk.NORMAL)
        if item != all_iid[-1]:  # Enable moving row down if not at bottom?
            menu.entryconfig("Move " + name + " Down", state=tk.NORMAL)

        menu.config(activebackground="SkyBlue3", activeforeground="black")

        # Reset last rediscovery time. Some methods can take 10 seconds to timeout
        self.last_refresh_time = time.time()
        menu.update()  # 2025-02-09 will this force title to appear?

    def turnPictureOn(self, cr):
        """ Mouse right button click selected "<name> Picture On". """
        _who = self.who + "turnPictureOn():"
        resp = cr.inst.turnPictureOn()
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()

    def turnPictureOff(self, cr):
        """ Mouse right button click selected "<name> Picture Off". """
        _who = self.who + "turnPictureOff():"
        resp = cr.inst.turnPictureOff()
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()

    def setLEDColor(self, cr):
        """ Mouse right button click selected "Set LED Lights Color".
            Note if cr.device in error a 10 second timeout can occur.
        """
        _who = self.who + "setLEDColor():"
        resp = cr.inst.setColor()
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()

    def setLEDNight(self, cr):
        """ Mouse right button click selected "Nighttime brightness".
            Note if cr.device in error a 10 second timeout can occur.
        """
        _who = self.who + "setLEDNight():"
        resp = cr.inst.setNight()
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()

    def breatheLEDColors(self, cr):
        """ Manual mouse right button click selected "Breathing colors".

            Call cr.inst.breatheColors() method. Which is also automatically
            called by BluetoothLedLightStrip.turnOn() method
            during homa.py startup and resuming from suspend.

            OVERVIEW:
            Suspends self.refreshApp() running in self.App.__init__() loop.
            Calls cr.inst.breatheColors() which loops forever and:
                Exit if app.isActive is False
                Exit if self.already_breathing_colors is False
                Calls app.refreshApp after each LED set color as time permits

        """
        _who = self.who + "breatheLEDColors():"
        resp = cr.inst.breatheColors()  # Loops forever until self.isActive False
        self.last_refresh_time = time.time()
        if not self.isActive:
            return
        text = "  " + str(resp)
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()

    def turnOn(self, cr):
        """ Mouse right button click selected "Turn On".
            Also called by turnAllPower("ON").
        """
        _who = self.who + "turnOn():"

        cr.inst.turnOn()
        text = "  " + cr.inst.powerStatus
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()  # 2025-05-02 Sony & LED show "?" instead of "ON"
        # NetworkInfo().getPower().curl(): event['returncode']: 124
        # SonyBraviaKdlTV().checkReply(): TypeError / KeyError: {'result': [{'status': 124}]}

        cr.inst.resumePowerOn = 0  # Resume didn't power on the device
        cr.inst.manualPowerOn = 0  # Was device physically powered on?
        cr.inst.nightPowerOn = 0  # Did nighttime power on the device?
        cr.inst.menuPowerOn += 1  # User powered on the device via menu

        # Setting Power can loop for a minute in worst case scenario using adb
        self.last_refresh_time = time.time()  # Refresh idle loop last entered time

    def turnOff(self, cr):
        """ Mouse right button click selected "Turn Off".
            Also be called by turnAllPower("OFF").
        """
        _who = self.who + "turnOff():"

        cr.inst.turnOff()
        text = "  " + cr.inst.powerStatus
        cr.tree.item(cr.item, text=text)
        cr.tree.update_idletasks()
        cr.inst.suspendPowerOff = 0  # Suspend didn't power off the device
        cr.inst.manualPowerOff = 0  # Was device physically powered off?
        cr.inst.dayPowerOff = 0  # Did daylight power off the device?
        cr.inst.menuPowerOff += 1  # User powered off the device via menu

        # Setting Power can loop for a minute in worst case scenario using adb
        self.last_refresh_time = time.time()  # Refresh idle loop last entered time

    def moveRowUp(self, cr):
        """ Mouse right button click selected "Move Row Up". """
        _who = self.who + "moveRowUp():"
        if str(cr.item) == "0":
            v0_print(_who, "Already on first row. Cannot move up.")
            return

        dr = TreeviewRow(self)  # Destination treeview row instance
        dr.Get(str(int(cr.item) - 1))  # Get destination row values
        v1_print(_who, "Swapping rows:", cr.mac, dr.mac)
        dr.Update(cr.item)  # Update destination row with current row
        cr.Update(dr.item)  # Update current row with destination row

    def moveRowDown(self, cr):
        """ Mouse right button click selected "Move Row Down". """
        _who = self.who + "moveRowDown():"
        if int(cr.item) >= len(cr.tree.get_children())-1:
            v0_print(_who, "Already on last row. Cannot move down.")
            return

        dr = TreeviewRow(self)  # Destination treeview row instance
        dr.Get(str(int(cr.item) + 1))  # Get destination row values
        v1_print(_who, "Swapping rows:", cr.mac, dr.mac)
        dr.Update(cr.item)  # Update destination row with current row
        cr.Update(dr.item)  # Update current row with destination row

    def forgetDevice(self, cr):
        """ Forget Device - when device removed or IP changed.
            - Remove cr.item from Devices Treeview
            - Delete mac_dict from ni.mac_dicts list
            - Delete inst_dict from ni.instances list
            - Delete MAC Address from ni.view_order list

        LISTS
        ni.devices     Devices from `arp -a`
        ni.hosts       Devices from `getent hosts`
        ni.host_macs   Optional MAC addresses at end of /etc/hosts
        ni.view_order  Treeview list of MAC addresses
        self.photos    Copy of treeview images saved from garbage collection

        LISTS of DICTIONARIES
        ni.mac_dicts   First time discovered, thereafter read from disk
        ni.instances   [{mac:99, instance:TclGoogleAndroidTV}...{}]

        """
        _who = self.who + "forgetDevice():"

        for arp_ndx, mac_dict in enumerate(ni.mac_dicts):
            if mac_dict['mac'] == cr.mac:
                v1_print(_who, "Found existing ni.mac_dict:", mac_dict['name'],
                         "arp_ndx:", arp_ndx)
                break
        else:
            v0_print(_who, "Not found ni.mac_dict!")
            return

        for inst_ndx, inst_dict in enumerate(ni.instances):
            if inst_dict['mac'] == cr.mac:
                v1_print(_who, "Found existing ni.instances:", inst_dict['mac'],
                         "inst_ndx:", inst_ndx)
                break
        else:
            v0_print(_who, "Not found ni.instances!")
            return

        for iid, view in enumerate(ni.view_order):
            if view == cr.mac:
                v1_print(_who, "Found existing ni.view_order 'iid':", iid)
                break
        else:
            v0_print(_who, "Not found ni.view_order!")
            return

        # Confirmation prompt
        title = "Confirm removal."
        text = "Are you sure you want to remove: '" + mac_dict['name'] + "'"
        answer = message.AskQuestion(self, title, text, "no", win_grp=self.win_grp,
                                     thread=self.refreshThreadSafe)

        text += "\n\t\tAnswer was: " + answer.result
        v3_print(title, text)

        v3_print(_who, "self.win_grp AFTER :")  # AskQuestion() win_grp debugging
        v3_print(self.win_grp.window_list)

        if answer.result != 'yes':
            return  # Don't delete pids

        ni.mac_dicts.pop(arp_ndx)
        ni.instances.pop(inst_ndx)

        # renumber iid for following treeview rows
        last_item = int(cr.item)
        new_count = len(cr.tree.get_children()) - 1
        v1_print(_who, "last_item:", last_item, "new_count:", new_count)
        while last_item < new_count:
            cr.Get(str(last_item + 1))  # Get source row values
            cr.Update(str(last_item))  # Update current row with source row
            v0_print(_who, "Reassigned iid:", cr.item, "to:", last_item)
            last_item += 1

        cr.tree.delete(str(new_count))  # Delete the last treeview row moved
        self.photos.pop(new_count)  # Delete the last photo moved

    def refreshApp(self, tk_after=True):
        """ Sleeping loop until need to do something. Fade tooltips. Resume from
            suspend. Monitor Sony TV settings. Rediscover devices.

            Multiple instances of refreshApp can be running:
                1) Called in mainloop of Application.__init__()
                2) Called by Right-Click Breathe Colors()
                3) Called by Suspend->Resume->Breathe Colors()
                4) Called by showInfo() and other user wait dialogs()
                5) Called by ResumeWait() countdown timer

            When a new instance of refreshApp() starts, the previous version(s)
            is paused until the caller of the new instance finishes.

        """

        _who = self.who + "refreshApp()"
        self.update_idletasks()

        if not self.winfo_exists():  # Application window destroyed?
            return False  # self.close() has destroyed window

        if killer.kill_now:  # Is system shutting down?
            v0_print('\nhoma.py refresh() closed by SIGTERM')
            self.exitApp(kill_now=True)
            return False  # Not required because this point never reached.

        now = time.time()  # lost time means suspend initiated outside of HomA
        delta = now - self.last_refresh_time
        if delta > GLO['RESUME_TEST_SECONDS']:  # Assume > is resume from suspend
            v0_print("\n" + "= "*4, _who, "Resuming from suspend after:",
                     tmf.days(delta), " ="*4 + "\n")
            self.resumeFromSuspend()  # Resume Wait + Conditionally Power on devices

        if not self.winfo_exists():  # Application window destroyed?
            return False  # self.close() has set to None

        if self.sonySaveInst:  # Check Sony TV special features if enabled
            self.sonySaveInst.checkSonyEvents()  # 2025-06-01 new method
            if self.sony_suspended_system is True:  # Sony TV initiated suspend
                self.Suspend(sony_remote_powered_off=True)  # Turns on event logging
                # Will not return until Suspend finishes and resume finishes
                now = time.time()  # Time changed after resume
                self.sony_suspended_system = False  # not needed but insurance

            if not self.winfo_exists():  # Application window destroyed?
                return False  # self.close() has set to None

        self.tt.poll_tips()  # Tooltips fade in and out
        self.update()  # process pending tk events in queue

        ''' 1 minute after restart, refresh lagging power statuses '''
        if self.force_refresh_power_time and now > self.force_refresh_power_time:
            self.force_refresh_power_time = 0.0  # Don't do it again
            self.GATTToolJobs(found_inst=self.bleSaveInst)
            self.refreshAllPowerStatuses()  # Display "ON", "OFF" or "?"

        if not self.winfo_exists():  # Application window destroyed?
            return False  # self.close() has set to None

        if self.bleSaveInst and self.bleScrollbox:  # Statistics for breathing colors?
            self.DisplayBreathing()  # Display single step in Bluetooth LEDs

        # if GLO['SENSOR_CHECK'] <= 0 the feature is turned off
        if GLO['SENSOR_CHECK'] > 0:
            sm.Sensors()  # Check `sensors` every GLO['SENSOR_CHECK'] seconds

        # Speedy derivative called by CPU intensive methods.
        if not tk_after:  # Skip tkinter update and 16 to 33ms sleep
            return self.winfo_exists()  # Application window destroyed?

        minute = ext.h(now).split(":")[1]  # Current minute for this hour
        if minute != self.last_minute:  # Get sunlight percentage every minute
            night = cp.getNightLightStatus()  # For LED light strip brightness boost
            self.last_minute = minute  # Wait for minute change to check again
            v2_print(_who, ext.t(), "cp.getNightLightStatus():", night)

        if int(now - self.last_rediscover_time) > GLO['REDISCOVER_SECONDS']:
            self.Rediscover(auto=True)  # Check for new network devices

        now = time.time()  # Time changed after .Sensors() and .Rediscover()
        if self.last_refresh_time > now:
            v0_print(_who, "self.last_refresh_time: ",
                     ext.h(self.last_refresh_time), " >  now: ", ext.h(now))
            now = self.last_refresh_time  # Reset for proper sleep time

        ''' Sleep remaining time to match GLO['REFRESH_MS'] '''
        self.update()  # Process everything in tkinter queue before sleeping
        sleep = GLO['REFRESH_MS'] - int(now - self.last_refresh_time)
        sleep = sleep if sleep > 0 else 1  # Sleep minimum 1 millisecond
        if sleep == 1:
            v0_print(_who, "Only sleeping 1 millisecond")
        self.after(sleep)  # Sleep until next GLO['REFRESH_MS'] (30 to 60 fps)
        self.last_refresh_time = time.time()

        return self.winfo_exists()  # Return app window status to caller

    def Suspend(self, sony_remote_powered_off=False, *_args):
        """ Power off devices and suspend system.
            2025-04-30 Track if Sony TV remote initiated system suspend
        """

        _who = self.who + "Suspend():"

        self.suspend_btn['state'] = tk.NORMAL  # 2025-02-11 color was staying blue

        ''' Is it ok to stop processing? - Make common method...'''
        msg = None
        if self.dtb:  # Cannot suspend when resume countdown timer is running.
            msg = "Countdown timer is running."
        if self.rediscovering:  # Cannot suspend during rediscovery.
            msg = "Device rediscovery is in progress for a few seconds."

        if msg:  # Cannot suspend when other jobs are active
            self.showInfoMsg("Cannot Suspend now.", msg, icon="error")
            v0_print(_who, "Aborting suspend.", msg)
            return

        self.exitRediscover()  # Not required now. Called after resume finishes.

        v1_print(_who, "\nSuspending system...")
        self.suspending = True  # Prevent error dialog from interrupting suspend
        self.resuming = False
        GLO['LOG_EVENTS'] = True  # Log all suspend events

        ''' Move mouse away from suspend button to close tooltip window 
            because <Enter> event generated for tooltip during system resume '''
        if not sony_remote_powered_off:
            command_line_list = ["xdotool", "mousemove_relative", "--", "-200", "-200"]
            _event = self.runCommand(command_line_list, _who)  # def runCommand
            self.tt.zap_tip_window(self.suspend_btn)  # Remove any tooltip window.

        self.isActive = False  # Signal breatheColors() to shut down elegantly
        self.suspending = True  # Don't display error messages with self.showInfo()
        self.resuming = False

        if self.bleSaveInst:  # Is breathing colors active?
            self.bleSaveInst.already_breathing_colors = False  # Force shutdown
        self.update_idletasks()
        self.after(100)  # Extra time (besides power off time) for Breathing Colors

        self.turnAllPower("OFF")  # Turn off all devices except computer
        cp.turnOff()  # suspend computer

        start_suspend = time.time()
        last_now = time.time()
        while True:  # Loop forever until suspend completed by OS
            now = time.time()
            self.update()  # update tkinter screen
            self.after(100)  # idle loop 100ms
            if now - last_now > 2.0:
                break  # s/b 100 ms but Lost more than 2 seconds so now suspended
            else:
                last_now = now

        ''' Resume from suspend '''

        time_to_suspend = last_now - start_suspend - 0.05  # assume half way of 100ms
        v1_print(_who, "Time required to suspend the system:", time_to_suspend)

        resume_now = time.time()
        delta = resume_now - last_now
        v0_print("\n" + "= "*4, _who, "Time spent sleeping / suspended:",
                 tmf.days(delta), " ="*4 + "\n")

        GLO['LOG_EVENTS'] = False  # Turn off event logging
        #self.last_refresh_time = start_suspend  # 2025-05-30 using wrong time
        self.last_refresh_time = resume_now  # 2025-05-30 was using wrong time
        self.isActive = True  # Signal breatheColors() can start
        self.suspending = False
        self.resuming = True  # Don't display error messages with self.showInfo()
        self.exitRediscover()  # 2025-05-30 After suspend, self.rediscovering was True

        ''' Automatically call resume to power on devices. '''
        self.resumeFromSuspend(suspended_by_homa=True)

    def resumeFromSuspend(self, suspended_by_homa=False):
        """ Resume from suspend. Display status of devices that were
            known at time of suspend. Then set variables to trigger
            rediscovery for any new devices added.

            Directly called by Suspend(). Called after manual suspend if time lost.

            Time lost when: now - self.last_refresh_time > GLO['RESUME_TEST_SECONDS']
            Long running processes must reseed self.last_refresh_time
            when they finish or a fake resume will occur.

            2025-03-19 Force Sensors log so temperatures and fan speeds are logged.

            2025-01-17 ERROR: Resume did not work for Sony TV, Sony Light, TCL TV,
                and TCL TV light. It did work for BLE LED Lights. Reason is resume
                wait is 3 seconds. Increase it to 6, then 7, then 10 seconds. Final
                solution is to wait for network which is 0 to 12 seconds.

            :param suspended_by_homa: Resume called after HomA suspended system

        """
        _who = self.who + "resumeFromSuspend():"
        self.exitRediscover()  # Reset time so Rediscovery doesn't start during resume.
        if not suspended_by_homa:
            v0_print(_who, "Suspend was called outside of HomA.")

        self.isActive = True  # Application GUI is active again
        self.resuming = True  # Prevent error dialogs from interrupting resume
        self.suspending = False  # No longer suspending
        self.sony_suspended_system = False  # Flag recorded on all instances earlier
        GLO['LOG_EVENTS'] = True  # Log all resume events

        start_time = time.time()
        self.resumeWait()  # Wait for network to come online
        delta = int(time.time() - start_time)
        v1_print(_who, "Waited", delta, "seconds for network to come up.")
        isNight = cp.getNightLightStatus()
        v1_print(_who, "Nightlight status: '" + isNight + "'")
        v1_print("\n" + _who, "ni.view_order:", ni.view_order)

        self.turnAllPower("ON")  # Turn all devices on and show new status in treeview

        if self.sonySaveInst and GLO['ALLOW_VOLUME_CONTROL']:
            self.sonySaveInst.hasVolumeSet = False  # Check quiet/normal volume again

        now = time.time()
        self.last_refresh_time = now  # Prevent running resumeFromSuspend() again
        sm.last_sensor_log = now - GLO['SENSOR_LOG'] * 2  # Force sensors log immediately
        self.resuming = False  # Allow error dialogs to appear on screen
        GLO['APP_RESTART_TIME'] = now  # Sensors log restart at 0.0 seconds
        GLO['LOG_EVENTS'] = False  # Turn off command event logging
        self.force_refresh_power_time = now + 60.0  # Recheck power 1 minute after resume
        self.exitRediscover()  # Should not be running, but reset time for next

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
            if self.rediscovering:  # 2025-01-08
                v0_print(_who, "Rediscovery in progress. Aborting Countdown")
                return  # if rediscovery, machine locks up when timer finishes.

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
            self.after(100)  # Suspend uses: 'self.after(100)'
            self.last_refresh_time = time.time()  # Don't trigger resume
            if timer or not self.checkInstalled("nmcli"):
                continue

            # Leave as soon as network is connected
            command_line_list = ["nmcli", "-f", "STATE", "-t", "g"]
            self.runCommand(command_line_list, _who)
            if self.cmdOutput.lower() == "connected":
                break  # 2025-04-21 - Took 12 seconds

        if timer and alarm is True:  # Play sound when timer ends
            if self.checkInstalled("aplay"):
                command_line_list = ["aplay", GLO['TIMER_ALARM']]
                self.runCommand(command_line_list, _who)

        self.dtb.close()
        self.dtb = None
        self.last_refresh_time = time.time()

    def turnAllPower(self, state, fade=False, type_code=None):
        """ Loop through instances and set power state to "ON" or "OFF".
            Called by Suspend ("OFF") and Resume ("ON")
            If devices treeview is mounted, update power status in each row

            :param state: Power state to set; "ON" or "OFF"
            :param fade: Fade in and out, false = No fading
            :param type_code: Process specific type_code outside of suspend/resume
        """
        _who = self.who + "turnAllPower(" + state + "):"
        isNight = cp.getNightLightStatus()  # Already v0 printed in resumeFromSuspend()
        v1_print(_who, "Nightlight status: '" + isNight + "'")  # Lights turn on at night
        cr = None  # Network devices treeview row instance and current iid
        if fade and self.usingDevicesTreeview:
            cr = TreeviewRow(self)  # Used to fade in row over 300ms

        # Loop through discovered devices stored in  ni.instances[]
        for i, instance in enumerate(ni.instances):
            inst = instance['instance']

            # Computer is excluded from being turned on or off.
            if inst.type_code in GLO['POWER_ALL_EXCL_LIST']:
                continue  # Device suspended with `systemctl`

            if type_code and type_code != inst.type_code:
                v1_print(_who, "type_code requested:", type_code,
                         "inst.type_code:", inst.type_code)
                continue  # Not the type code searching for

            night_powered_on = False  # Don't turn on bias light during daytime
            if type_code is None and inst.type_code == GLO['HS1_SP']:
                # 2024-11-26 - 'type_code' s/b 'BIAS_LIGHT' and
                #   'sub_type_code' s/b 'GLO['HS1_SP']`
                v1_print("\n" + _who, "Bias light device: '" + inst.type + "'",
                         " | IP: '" + inst.ip + "'")
                if state == "ON" and isNight == "OFF":
                    inst.dayPowerOff += 1
                    inst.nightPowerOn = 0
                    inst.menuPowerOff = 0
                    inst.manualPowerOff = 0
                    inst.suspendPowerOff = 0
                    inst.powerStatus = "OFF"
                    v1_print(_who, "Do not turn on Bias light in daytime.")
                    continue  # Do not turn on light during daytime
                elif state == "ON":
                    v1_print(_who, "Turn on Bias light at night.")
                    night_powered_on = True

            if type_code is None and inst.type_code == GLO['BLE_LS']:
                # Special debugging for LED Light Strips
                v1_print(_who, "BEFORE:", inst.type_code, inst.mac, inst.name)
                v1_print("inst.device:", inst.device)
                v1_print("BluetoothStatus:", inst.BluetoothStatus,
                         "powerStatus:", inst.powerStatus)

            if fade and cr:  # Is there a current row instance?
                iid = cr.getIidForInst(inst)  # Get treeview row IID
                if iid is not None:
                    self.tree.see(iid)
                    cr.fadeIn(iid)  # Fading in was requested

            if state == "ON":
                if type_code is None:  # Called by Resume()
                    v2_print(_who, "Switching power from '" + inst.powerStatus +
                             "' to 'ON':", inst.name)
                else:  # Called by "Turn ALL Lights Power" menu option or similar
                    v1_print(_who, "Switching power from '" + inst.powerStatus +
                             "' to 'ON':", inst.name)
                inst.turnOn()  # inst.menuPowerOn += 1
                if type_code is None:
                    # Assume powered on even if "?" due to timeout it can be "ON" later
                    inst.resumePowerOn += 1  # Resume powered on the device
                    inst.menuPowerOn = 0  # User didn't power on the device via menu
                    inst.nightPowerOn += 1 if night_powered_on else 0
            elif state == "OFF":
                if inst.powerStatus == "ON":
                    # To avoid errors must be "ON" in order to turn "OFF".
                    if type_code is None:  # Called by Suspend()
                        v2_print(_who, "Switching power from 'ON' to 'OFF':", inst.name)
                    else:  # Called by "Turn ALL Lights Power" menu option or similar
                        v1_print(_who, "Switching power from 'ON' to 'OFF':", inst.name)
                    inst.turnOff()  # inst.menuPowerOff += 1
                    if type_code is None:
                        inst.suspendPowerOff += 1  # Suspend powered off the device
                        inst.menuPowerOff = 0  # User didn't power on the device via menu
                        # 2025-04-30 Track if Sony TV remote initiated system suspend
                        inst.remote_suspends_system = self.sony_suspended_system
            else:
                v0_print(_who, inst.name, "power state is not 'ON' or 'OFF':", state)
                return

            if type_code is None and inst.type_code == GLO['BLE_LS']:
                # Special debugging for LED Light Strips
                v1_print(_who, "AFTER:", inst.type_code, inst.mac, inst.name)
                v1_print("inst.device:", inst.device)
                v1_print("BluetoothStatus:", inst.BluetoothStatus,
                         "powerStatus:", inst.powerStatus)

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
            cr.text = "  " + str(inst.powerStatus)  # Display treeview row new power state
            if cr.text != old_text:
                v1_print(_who, inst.name, "Power status changed from: '"
                         + old_text.strip() + "' to: '" + cr.text.strip() + "'.")
            cr.Update(iid)  # Update iid with new ['text']

            # Display row by row when there is processing lag
            self.tree.update_idletasks()  # Slow mode display each row.

            # MAC address stored in treeview row hidden values[-1]
            v2_print("\n" + _who, "i:", i, "cr.mac:", cr.mac)
            v2_print("cr.inst:", cr.inst)

            if fade:  # Was fading out requested?
                cr.fadeOut(iid)

        v2_print()  # Blank line to separate debugging output

    def setColorScheme(self, scheme):
        """ Set color scheme for devices treeview and sensors treeview
            After setting color toggle treeview for new color to appear.
        """
        _who = self.who + "setColorScheme(" + scheme + "):"
        edge_color = "White"  # Default
        if scheme == "WhiteSmoke":
            edge_color = "White"
        elif scheme == "LemonChiffon":
            edge_color = "NavajoWhite"
        elif scheme == "NavajoWhite":
            edge_color = "LightSalmon"
        elif scheme == "LightSalmon":
            edge_color = "DarkOrange"
        GLO['TREEVIEW_COLOR'] = scheme
        GLO['TREE_EDGE_COLOR'] = edge_color
        self.toggleSensorsDevices()

        # Edge color isn't appearing??
        style = ttk.Style()
        style.configure("Treeview", edge_color=edge_color, edge_px=5)

    def refreshAllPowerStatuses(self, auto=False):
        """ Read ni.instances and update the power statuses.
            Called from: self.Rediscover(auto=auto) every x seconds.
            Called from: self.refreshApp() 60 seconds after startup or resume.

            If Devices Treeview is visible (mounted) update power status.
            TreeviewRow.Get() creates a row instance to update text.
            Optional fading row instance in and out.

            :param auto: If 'False' highlight Network Devices Treeview rows.
        """
        _who = self.who + "refreshAllPowerStatuses():"

        # If auto, called automatically at GLO['REDISCOVER_SECONDS']
        cr = iid = None  # Assume Sensors Treeview is displayed
        if self.usingDevicesTreeview:
            cr = TreeviewRow(self)  # Setup treeview row processing instance

        # Loop through ni.instances
        for i, instance in enumerate(ni.instances):
            if not self.isActive:
                return  # Shutting down

            inst = instance['instance']
            if self.usingDevicesTreeview:
                # Get treeview row based on matching MAC address + device_type
                iid = cr.getIidForInst(inst)  # Get iid number and set instance
                if iid is not None:
                    # When cr.text is "Wait..." fast startup so highlight each row
                    if auto is False or cr.text == "Wait...":
                        self.tree.see(iid)
                        cr.fadeIn(iid)

            inst.getPower()  # Get the power status for device
            self.last_refresh_time = time.time()  # In case getPower() long time

            # Update Devices Treeview with power status
            if not self.usingDevicesTreeview:
                continue  # No Devices Treeview to update

            if iid is None:
                continue  # Instance not in Devices Treeview or treeview not mounted

            old_text = cr.text  # Treeview row's old power state "  ON", etc.
            cr.text = "  " + inst.powerStatus  # Display treeview row's new power state
            if cr.text != old_text:
                v1_print(_who, cr.mac, "Power status changed from: '"
                         + old_text.strip() + "' to: '" + cr.text.strip() + "'.")
            cr.Update(iid)  # Update row with new ['text']
            if auto is False or old_text == "Wait...":
                # Fade in/out performed when called from Dropdown Menu (auto=False).
                # Or on startup when status is "Wait...". Otherwise, too distracting.
                cr.fadeOut(iid)

            # Display row by row when there is processing lag
            self.tree.update_idletasks()  # Slow mode display each row.

            # MAC address stored in treeview row hidden values[-1]
            v2_print("\n" + _who, "i:", i, "cr.mac:", cr.mac)
            v2_print("cr.inst:", cr.inst)

        v2_print()  # Blank line to separate debugging output

    def Rediscover(self, auto=False):
        """ Automatically call 'arp -a' to check on network changes.
            self.refreshApp() calls every GLO['REDISCOVER_SECONDS'].

            NOTE: Used to be two step process called twice. Changed 2025-05-15.

            :param auto: If 'False', called from menu "Rediscover Now".
        """

        _who = self.who + "Rediscover():"
        if self.rediscovering:
            v0_print(_who, "Already running!")
            return
        self.rediscovering = True
        self.updateDropdown()  # Disable menu options

        # If GLO['APP_RESTART_TIME'] is within 1 minute (GLO['REDISCOVER_SECONDS']) turn off
        # auto rediscovery flags so startup commands are logged to cmdEvents
        if GLO['APP_RESTART_TIME'] > time.time() - GLO['REDISCOVER_SECONDS'] - \
                GLO['RESUME_TEST_SECONDS'] - 10:
            auto = False  # Override auto rediscovery during startup / resuming

        ''' Some `arp -a` lines are DISCARDED: 
                ? (20.20.20.1) at a8:4e:3f:82:98:b2 [ether] on enp59s0
                TCL.LAN (192.168.0.17) at <incomplete> on enp59s0  '''
        # Override event logging and v3_print(...) during auto rediscovery
        GLO['LOG_EVENTS'] = True if auto is False else False

        # First step is to create rd[] list and return to self.refreshApp()
        ext.t_init("Creating instance rd = NetworkInfo()")
        global rd
        rd = NetworkInfo()  # rd. class is newer instance ni. class
        ext.t_end('no_print')

        # tr instance only created if Network Devices treeview is mounted
        tr = TreeviewRow(self) if self.usingDevicesTreeview else None

        def addTreeviewRow(new_mac):
            """ Add network devices treeview row if mounted. """

            if not tr:
                return  # No Treeview row instance

            tr.New(new_mac)
            new_row = len(self.tree.get_children())
            tr.Add(new_row)
            self.tree.see(str(new_row))

        def checkChanges(new_dict, old_dict):
            """ Check rediscovered mac_dict to previously known mac_dict.
                Any changes are updated realtime into ni.mac_dicts[] but HomA
                may require restarting for Network Devices treeview display.

                :param new_dict: rediscovered mac_dict
                :param old_dict: mutable existing mac_dict updated with changes
            """
            if new_dict['mac'] != old_dict['mac']:
                v0_print(_who, "new_dict['mac'] != old_dict['mac']:",
                         new_dict['mac'], old_dict['mac'])
                v0_print("This should NEVER happen!")
            if new_dict['ip'] != 'irrelevant' and new_dict['ip'] != old_dict['ip']:
                v0_print(_who, "new_dict['ip'] != old_dict['ip']:",
                         new_dict['ip'], old_dict['ip'])
                old_dict['ip'] = new_dict['ip']
            if new_dict['name'] != old_dict['name']:
                v0_print(_who, "new_dict['name'] != old_dict['name']:",
                         new_dict['name'], old_dict['name'])
                old_dict['name'] = new_dict['name']
            if new_dict['alias'] != old_dict['alias']:
                v0_print(_who, "new_dict['alias'] != old_dict['alias']:",
                         new_dict['alias'], old_dict['alias'])
                old_dict['alias'] = new_dict['alias']

        v2_print(_who, "Rediscovery count:", len(rd.mac_dicts))

        self.refreshAllPowerStatuses(auto=auto)  # When auto=False, rows highlighted

        for i, rd_mac_dict in enumerate(rd.mac_dicts):
            if not self.isActive:
                self.exitRediscover()
                return

            if not self.rediscovering:
                # Not used yet but someone else can force immediate exit
                v0_print(_who, "Someone turned off rediscovering!")
                self.exitRediscover()
                return

            mac = rd_mac_dict['mac']
            # TCL.LAN (192.168.0.17) at <incomplete> on enp59s0
            if mac == '<incomplete>':
                v1_print(_who, "Skipping invalid MAC:", mac)
                continue

            ip = rd_mac_dict['ip']
            # ? (20.20.20.1) at a8:4e:3f:82:98:b2 [ether] on enp59s0
            if ip == '?':
                v1_print(_who, "Skipping invalid IP:", ip)
                continue

            v2_print("Checking MAC:", mac, "IP:", ip)
            mac_dict = ni.get_mac_dict(mac)  # NOTE different than rd_mac_dict !
            if not bool(mac_dict):
                # Add ni.mac_dicts, ni.instances, ni.devices, ni.view_order
                v0_print(_who, "new MAC discovered:", mac)

                start = len(ni.mac_dicts)  # start = offset to next added mac_dict
                # mac_dict = {"mac": mac, "ip": ip, "name": name, "alias": alias}
                ni.mac_dicts.append(rd_mac_dict)  # mac_dict for 1 found device
                discovered, instances, view_order = \
                    discover(update=False, start=start, end=start+1)  # last mac_dict

                if len(discovered) != 1:
                    v0_print(_who, "Catastrophic error! Invalid len(discovered):",
                             len(discovered))
                    self.exitRediscover()
                    return

                # Format: 'SONY.LAN (192.168.0.19) at ac:9b:0a:df:3f:d9 [ether] on enp59s0'
                ni.devices = copy.deepcopy(rd.devices)  # Copy ALL rediscovered devices.
                # Unfortunately, ni.mac_dicts saved to filename "devices.json"

                if bool(instances):
                    ni.instances.append(instances[0])
                    v0_print(_who, "Adding MAC to ni.instances:", mac)
                else:
                    v1_print(_who, "Unrecognized instance type for MAC:", mac)
                    continue

                ni.view_order.append(mac)  # New instance appears at treeview bottom.
                addTreeviewRow(mac)  # Only update Devices Treeview when mounted.

            elif mac not in ni.view_order:
                v2_print(_who, "ni.mac_dicts MAC not in view order:", mac)

            mac_inst = ni.inst_for_mac(mac)
            if bool(mac_inst):
                v2_print(_who, "found instance:", mac_inst['mac'])
                # 2025-05-14 If in tree, check changes to host name, IP, alias, etc.
                if mac not in ni.view_order:
                    v0_print(_who, "arp exists, instance exists, but no view order")
                    v0_print("Inserting", rd_mac_dict['mac'], rd_mac_dict['name'])
                    ni.view_order.append(mac)
                    addTreeviewRow(mac)  # Only update Devices Treeview when mounted.
                checkChanges(rd_mac_dict, mac_dict)
                continue

            # Instance doesn't exist for a mac_dict['mac']
            v2_print(_who, "No Instance for ni.mac_dicts MAC:", mac)
            instance = ni.test_for_instance(mac_dict)
            if not bool(instance):
                continue  # Router, ethernet adapter, wifi adapter, smartphone, etc.

            v0_print("="*80, "\n" + _who, "Discovered a NEW INSTANCE or",
                     "rediscovered a LOST INSTANCE:")
            v0_print(instance)
            ni.instances.append(instance)
            mac_dict['type_code'] = instance['instance'].type_code  # mutable mac_dict
            ni.view_order.append(rd_mac_dict['mac'])
            addTreeviewRow(mac)  # Only update Devices Treeview when mounted.
            v0_print("="*80)

        # All steps done: Wait for next rediscovery period
        if bool(rd.cmdEvents):
            ni.cmdEvents.extend(rd.cmdEvents)  # For auto-rediscover, rd.cmdEvents[] empty
        self.exitRediscover()

    def exitRediscover(self):
        """ End the rediscovery method """
        self.rediscovering = False
        self.last_rediscover_time = time.time()
        self.last_refresh_time = self.last_rediscover_time  # 2025-06-21 added not test
        self.updateDropdown()  # Enable menu options

    def refreshPowerStatusForInst(self, inst):
        """ Called by BluetoothLED """
        _who = self.who + "refreshPowerStatusForInst():"
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
        cr.fadeIn(iid)

        old_text = cr.text  # Treeview row's old power state "  ON", etc.
        cr.text = "  " + inst.powerStatus  # Display treeview row's new power state
        if cr.text != old_text:
            v1_print(_who, cr.mac, "Power status changed from: '"
                     + old_text.strip() + "' to: '" + cr.text.strip() + "'.")
        cr.Update(iid)  # Update row with new ['text']
        cr.fadeOut(iid)

    def MouseWheel(self, event):
        """ Mousewheel scroll defaults to 5 units, but tree has 3 images """
        _who = self.who + "MouseWheel():"
        if event.num == 4:  # Override mousewheel scroll up
            event.widget.yview_scroll(-1, "units")  # tree = event.widget
            return "break"  # Don't let regular event handler do scroll of 5
        if event.num == 5:  # Override mousewheel scroll down
            event.widget.yview_scroll(1, "units")  # tree = event.widget
            return "break"  # Don't let regular event handler do scroll of 5

    def GetPassword(self, msg=None):
        """ Get Sudo password with message.AskString(show='*'...). """

        if msg is None:
            msg = "Sudo password required for laptop display and Bluetooth.\n\n"
        answer = message.AskString(
            self, text=msg, thread=self.refreshThreadSafe, show='*',
            title="Enter sudo password", icon="information", win_grp=self.win_grp)

        # Setting laptop display power requires sudo prompt which causes fake resume
        self.last_refresh_time = time.time()  # Refresh idle loop last entered time

        if answer.result != "yes":
            return None  # Cancel button selected

        # Validate password, error message if invalid
        password = hc.ValidateSudoPassword(answer.string)
        if password is None:
            msg = "Invalid sudo password!\n\n"
            self.showInfoMsg("Invalid sudo password", msg, icon="error")

        self.last_refresh_time = time.time()  # Refresh idle loop last entered time
        return password  # Will be <None> if invalid password entered

    def refreshThreadSafe(self):
        """ Prevent self.refreshApp rerunning a second rediscovery during
            error message waiting for acknowledgement
        """
        self.last_refresh_time = time.time()  # Prevent resume from suspend
        self.last_rediscover_time = self.last_refresh_time
        self.refreshApp(tk_after=False)
        self.after(10)
        self.update()  # Suspend button stays blue after mouseover ends?

    def showInfoMsg(self, title, text, icon="information", align="center"):
        """ Show message with thread safe refresh that doesn't invoke rediscovery.

            Can be called from instance which has no tk reference of it's own
                From Application initialize with:   inst.app = self
                From Instance call method with:     self.app.showInfoMsg()
        """

        message.ShowInfo(self, thread=self.refreshThreadSafe, icon=icon, align=align,
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

                key = atts[0]  # E.G. 'SONY_PWD'
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

                _success = glo.updateGlobalVar(key, all_notebook.newData[key])

            # Save changes after edit so YT Ad Skip can use right away
            # glo.saveFile()

            self.notebook.destroy()
            self.notebook = None
            self.updateDropdown()
            # Restore Application() bottom button bar as pre buildButtonBar() options
            self.btn_frm.grid(row=99, column=0, columnspan=2, sticky=tk.E)

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

        self.btn_frm.grid_forget()  # Hide button bar
        self.notebook = ttk.Notebook(self)
        listTabs, listFields, listHelp = glo.defineNotebook()
        all_notebook = toolkit.makeNotebook(
            self.notebook, listTabs, listFields, listHelp, GLO, "TNotebook.Tab",
            "Notebook.TFrame", "C.TButton", close, tt=self.tt,
            help_btn_image=self.img_mag_glass, close_btn_image=self.img_checkmark)
        self.edit_pref_active = True
        self.updateDropdown()

    def openCalculator(self):
        """ Big Number Calculator allows K, M, G, T, etc. UoM """
        if self.calculator and self.calc_top:
            self.calc_top.focus_force()
            self.calc_top.lift()
            return

        geom = monitor.get_window_geom('calculator')
        self.calc_top = tk.Toplevel()

        # Set Calculator program icon in taskbar
        cfg_key = ['cfg_calculator', 'toplevel', 'taskbar_icon', 'height & colors']
        ti = cfg.get_cfg(cfg_key)
        img.taskbar_icon(self.calc_top, ti['height'], ti['outline'],
                         ti['fill'], ti['text'], char=ti['char'])

        # Create calculator class instance
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

        # Trap <Escape> key and  '✘' Window Close Button
        self.calc_top.bind("<Escape>", calculator_close)
        self.calc_top.protocol("WM_DELETE_WINDOW", calculator_close)
        self.calc_top.update_idletasks()

        # Move Calculator to cursor position
        hc.MoveHere("Big Number Calculator", 'top_left')

    def configureYouTube(self):
        """ Display Mouse Pointer coordinates (x, y) in real time. Grab
            pixel color on mouse hover. Log results for YouTube Ad skipping.

            Calls DisplayCommon to create Window, Frame and Scrollbox.
            
            Inspect and permanently store in preferences:
            
            - YouTube video playback progress bar location and color
            - YouTube Ad first few seconds of progress bar location and color
            - YouTube Ad skip button location and dominant color within button

            2025-07-12 - coordinates changed by 8 pixels less on y-axis for
                YouTube Ad and Video progress bars. Skip button also changed
                coordinates.

            NOTE: Alternate Ad Skip can be <ALT>+<Left Arrow> followed by
                <ALT>+<Right Arrow> sent to browser window. Much faster but
                not guaranteed to work all the time.
        """
        _who = self.who + "configureYouTube():"
        title = "Configure YouTube Ads"

        scrollbox = self.DisplayCommon(_who, title, width=1200, height=600,
                                       help="ViewBluetoothDevices")
        if scrollbox is None:
            return  # Window already opened and method is running

        # Tabs for self.event_scrollbox created by self.DisplayCommon()
        # Tabs for windows list output similar to `wmctrl -lGp
        #  X-offset  Y-offset  Width  Height  Name
        tabs = ("100", "right", "200", "right", "300", "right",  # Width Height X-off
                "400", "right", "420", "left")  # Y-offset Name
        scrollbox.tag_config("hanging_indent", lmargin2=440)

        def reset_tabs(event):
            """ https://stackoverflow.com/a/46605414/6929343 """
            event.widget.configure(tabs=tabs)

        scrollbox.configure(tabs=tabs, wrap=tk.WORD)
        scrollbox.bind("<Configure>", reset_tabs)

        def _in(x, y, w, h, name):
            """ Insert 2 parameter variable pairs into custom scrollbox """
            line = "\t" + str(x) + "\t" + str(y) + "\t"
            line += str(w) + "\t" + str(h) + "\t" + str(name) + "\n"
            scrollbox.insert("end", line, "hanging_indent")

        mon = monitor.Monitors()
        mon.make_wn_list()  # dont like name but get_all_windows() already used
        _in("X-offset", "Y-offset", "Width", "Height", "Window name")
        scrollbox.insert("end", "\n")

        for mon.wn_dict in mon.wn_list:
            mon.unmake_wn_dict()  # Dictionary values to attribute variables
            if mon.wn_height < 50 or mon.wn_x < 0 or mon.wn_y < 0:
                continue  # Remove non-windows from display
            _in(mon.wn_x, mon.wn_y, mon.wn_width, mon.wn_height, mon.wn_name)

        scrollbox.highlight_pattern("Width", "green")
        scrollbox.highlight_pattern("Height", "green")
        scrollbox.highlight_pattern("X-offset", "yellow")
        scrollbox.highlight_pattern("Y-offset", "yellow")
        scrollbox.highlight_pattern("Window name", "blue")

        # Display x, y pointer coordinates in self.event_top

        '''
        Skip Ad on YouTube using keyboard?
        https://webapps.stackexchange.com/questions/100869/
            keyboard-shortcut-to-close-the-ads-on-youtube
        '''
        pointer_frm = ttk.Frame(self.event_frame, borderwidth=g.FRM_BRD_WID,
                                padding=(2, 2, 2, 2), relief=tk.RIDGE)
        pointer_frm.grid(column=0, row=0, sticky=tk.NSEW)  # Label
        pointer_frm.grid_columnconfigure(1, minsize=g.MON_FONTSIZE*12, weight=1)
        pointer_frm.grid_columnconfigure(2, minsize=50, weight=0)  # Color rectangle

        def add_row(row_no, label, _val, _type="Int", tt_text=None):
            """ Add row to Pointer Location section
                Column 0 contains label, Column 1 contains passed text which is
                initialized into string variable returned to caller.
            """
            _who2 = _who[:-1] + " add_row():"
            label = ttk.Label(pointer_frm, text=label, font=g.FONT)
            label.grid(row=row_no, column=0, sticky=tk.NSEW, padx=15, pady=10)
            if _type == "String":
                _var = tk.StringVar()
            elif _type == "Int":
                _var = tk.IntVar()
            else:
                v0_print(_who, "Unknown tk variable type:", _type)
                return None

            _var.set(_val)
            text = ttk.Label(pointer_frm, textvariable=_var, font=g.FONT)
            text.grid(row=row_no, column=1, sticky=tk.NSEW, padx=15)
            if self.tt and tt_text:
                self.tt_add(label, tt_text)
            return _var

        var_x = add_row(0, "X-offset:", 0)  # Mouse Pointer X
        var_y = add_row(1, "Y-offset:", 0)  # Mouse Pointer Y
        var_r = add_row(2, "Red:", 0)  # Red integer value
        var_g = add_row(3, "Green:", 0)  # Green integer value
        var_b = add_row(4, "Blue", 0)  # Blue integer value
        var_h = add_row(5, "RGB Hex:", "?", _type="String")  # "#a1b2c3" hex color

        # ScrollText with instructions third column row span 6
        _sbt = "INSTRUCTIONS:\n\n"
        _sbt += "1. Make YouTube fullscreen. Pause video and Ad for logging.\n"
        _sbt += "2. Click on this window to regain focus for keystrokes.\n\n"
        _sbt += "3. Hover mouse pointer over YouTube window areas (don't click) and:\n"
        _sbt += "    - Press 'v' or 'V' to log red Video progress bar start.\n"
        _sbt += "    - Press 'a' or 'A' to log yellow Ad progress bar start.\n"
        _sbt += "    - Press 's' or 'S' to log Skip Ad button white triangle.\n\n"
        _sbt += "4. After successful logging, confirmation is displayed."

        _sb = toolkit.CustomScrolledText(pointer_frm, state="normal", font=g.FONT,
                                         height=11, borderwidth=15, relief=tk.FLAT)
        toolkit.scroll_defaults(_sb)  # Default tab stops are too wide
        _sb.config(tabs=("50", "100", "150"))
        _sb.grid(row=0, column=3, rowspan=6, padx=3, pady=3, sticky=tk.EW)
        pointer_frm.grid_columnconfigure(2, weight=1)  # scroll box
        _sb.insert("end", _sbt)
        _sb.highlight_pattern("red", "red")
        _sb.highlight_pattern("yellow", "yellow")
        _sb.highlight_pattern("white", "white")

        # showInfo to confirm logging key is ignored if YouTube window has focus

        def update_pointer():
            """ Get mouse position and Update Display 
                :returns True if x or y changed, else False
            """
            _x, _y = mon.get_mouse_pointer()
            if _x is not None:
                var_x.set(_x)
                var_y.set(_y)
            else:
                v0_print(_who[:-1] + " update_pointer(): ERROR:", _y)
            return _x, _y

        def on_key_press(event):
            """ Key press event """
            #v0_print(_who, "on_key_press() event_char: '" + event.char + "'.")
            _keysym = event.keysym
            #v0_print("  keysym: '" + str(_keysym) + "'.")

            if len(pointer_color) != 7:
                v0_print(_who, "Cannot log when len(_color) != 7")
                return
            if pointer_x is None or pointer_y is None:
                v0_print(_who, "Cannot log when pointer_x or pointer_y is <None>")
                return

            def _update(_color_key, _color, _point_key, _pointer_x, _pointer_y):
                """ Show message with old and new values. Update new values. """

                _msg = glo.getDescription(_color_key) + ":\n"
                _msg += "\n  OLD color: " + str(GLO[_color_key])  # Could be <None>
                _msg += "\n  NEW color: " + _color + "\n\n"
                _msg += glo.getDescription(_point_key) + ":\n"
                _msg += "\n  OLD [x, y] coordinates: " + str(GLO[_point_key])
                _msg += "\n  NEW [x, y] coordinates: ["
                _msg += str(_pointer_x) + "," + str(_pointer_y) + "]\n"
                GLO[_color_key] = _color
                GLO[_point_key] = [pointer_x, pointer_y]

                self.showInfoMsg("New Color and Coordinates logged", _msg)

            # Log Ad Progress bar starting location and color
            if _keysym == "a" or _keysym == "A":
                _update("YT_AD_BAR_COLOR", pointer_color,
                        "YT_AD_BAR_POINT", pointer_x, pointer_y)

            if _keysym == "v" or _keysym == "V":
                _update("YT_VIDEO_BAR_COLOR", pointer_color,
                        "YT_VIDEO_BAR_POINT", pointer_x, pointer_y)

            if _keysym == "s" or _keysym == "S":
                _update("YT_SKIP_BTN_COLOR", pointer_color,
                        "YT_SKIP_BTN_POINT", pointer_x, pointer_y)

        # tk.Canvas rectangle representing color in third column
        _pi = toolkit.PointerInspector(pointer_frm, column=2, rowspan=6,
                                       tt=self.tt, mon=mon)
        _pointer_changed = time.time()
        _color_changed = 0.0

        # Loop forever until window closed
        self.event_top.bind("<Key>", on_key_press)
        while self.event_top and self.event_top.winfo_exists():
            if not self.refreshApp(tk_after=False) or self.suspending:
                break
            try:
                self.after(5)  # tk_after=False is too FAST
                now = time.time()
                last_x = var_x.get()
                last_y = var_y.get()
                pointer_x, pointer_y = update_pointer()
                if pointer_x is None:
                    v0_print(_who, "Catastrophic error:", pointer_y)
                    break
                if int(pointer_x) != last_x or pointer_y != last_y:
                    _pointer_changed = now
                    v3_print("_pointer_changed:", ext.t(_pointer_changed),
                             "| last_x:", last_x, "pointer_x:", pointer_x,
                             "| last_y:", last_y, "pointer_y:", pointer_y)
                    v3_print("  type(last_x):", type(last_x), "type(pointer_x):",
                             type(pointer_x), "| type(last_y):", type(last_y),
                             "type(pointer_y):", type(pointer_y))

                if now > _pointer_changed + .2 and _pointer_changed > _color_changed:
                    # Screen grab takes longer so only do it once .1 second into hover
                    pointer_color = _pi.get_colors(pointer_x, pointer_y)
                    var_r.set(_pi.clr_r)
                    var_g.set(_pi.clr_g)
                    var_b.set(_pi.clr_b)
                    var_h.set(pointer_color)  # Display RBG Hex
                    _color_changed = now = time.time()  # old now + ~0.06
                    v1_print(_who, "pointer_color:", pointer_color)
                    _pi.refresh_canvas(pointer_color)  # canvas rectangle for color
                    self.event_top.update_idletasks()

            except (tk.TclError, AttributeError):
                break  # Break in order to terminate vu_meter.py below
            self.last_rediscover_time = now  # Prevent Rediscover
            self.last_refresh_time = self.last_rediscover_time  # Prevent Resume

        try:
            self.event_top.unbind("<Key>")  # Normally this generates error
            v0_print(_who, "self.event_top still exists after window closed")
        except AttributeError:
            pass
        #_pi.terminate()
        #DisplayCommonInst.close()  # 2025-06-26. Stale window still open??

    def watchYouTube(self):
        """ Monitor Pulse Audio for new sinks.

            2025-07-09 TODO: Can be more than one YouTube tab in browser. Track
                    each browser video independently.
                Random sounds can appear from ffplay or Telegram messenger. Do
                    not display these random new sink input indices.
                Replace Ad Start / Video Start labels with Status / Duration labels.
                Startup check for Ad/Video/Button Skip coordinates and colors.
                Verify scrolling down to make comment and then scrolling back up
                    again doesn't impair operation.
                        2025-07-10 `xprop -id 0x03c00028` testing CONFIRMS OK:
                            _NET_WM_STATE(ATOM) = _NET_WM_STATE_FULLSCREEN

            2025-07-10 TODO: Make separate application pimtube.py.
                    Called from homa-indicator.py menu.
                    Requires GLO dictionary saved whenever changed in homa.py.
                    Configure YouTube will remain in homa.py
                New variable GLO['YT_SKIP_BTN_WAIT'] = 4.7
                Sinks that appear when video or ad is paused may not have a
                    window. E.G. `ffplay` so don't put into scroll box. If the
                    next sink after that is same video, don't repeat video
                    name. Also double space new video names.
                Figure out how links to ~/python's /audio/* and /pulsectl/*
                    can be updated in github.
                When video ends, YouTube is no longer fullscreen. Otherwise,
                    when video paused the sink ends but YouTube is still fullscreen.
                    Use this rule to cleanup spamming scrollbox with new sink
                    messages from pause/play. Also use to recalculate video
                    start time for closely accurate duration.

            2025-07-11 TODO: Alarm from Firefox Browser Tab causes "A/V Check"
                    status until video paused / resumed.
                If video already playing when watchYouTube starts up there is
                    no red video progress bar to see so "A/V check" status
                    stays until an Ad starts up.

            2025-07-12 NOTE: y-axis coordinates changed 8 pixels less for Ad
                    and Video progress bars and for Skip Ad Button. The
                    "A/V check" status stays up forever.
                If Ad has white background a false positive for "Skip check"
                    is recorded about 4 seconds into the Ad. The left mouse
                    button click causes Ad to pause.

        NOTES about fullscreen:
            Wnck.Screen.Window.fullscreen() isn't supported in version 3.18.
            wmctrl -ir hex_win -b toggle,fullscreen doesn't remove YT menus.
            Use 'xdotool key "f"' instead.

        NOTES about Ad Skipping:
            False positives when only looking for a single white dot because
                looking too soon < 4.7 seconds will see white dot in ad
                and not in the ad skip button resulting in ad pause on click.
            Gtk mouse click only works on GTK windows
            Python pyautogui click only works on primary monitor
            Browser previous history (<ALT>+<Left Arrow>) followed by forward
                (<ALT>+<Right Arrow>) works sometimes but can sometimes take
                4.7 seconds which an Ad skip Button Click would take. Sometimes
                YouTube restarts video at beginning which totally breaks flow.
            Use:
                `xdotool mousemove <x> <y> click 1 sleep 0.01 mousemove restore`

        """
        _who = self.who + "watchYouTube():"
        title = "Watch YouTube Ad-mute"

        scrollbox = self.DisplayCommon(_who, title, width=1200, height=700,
                                       help="ViewBluetoothDevices")
        if scrollbox is None:
            return  # Window already opened and method is running

        # Tabs for self.event_scrollbox created by self.DisplayCommon()
        tabs = ("140", "right", "170", "left", "400", "left",
                "750", "left", "1125", "right")
        scrollbox.tag_config("hanging_indent", lmargin2=420)

        def reset_tabs(event):
            """ https://stackoverflow.com/a/46605414/6929343 """
            event.widget.configure(tabs=tabs)

        scrollbox.configure(tabs=tabs, wrap=tk.WORD)
        scrollbox.bind("<Configure>", reset_tabs)

        line = "Input\tVol.\tApplication\tVideo name\n"
        scrollbox.insert("end", line + "\n", "hanging_indent")

        # Display Audio. Rows 0 to 89 available in self.event_top
        if not self.audio.isWorking:
            self.showInfoMsg("Watch YouTube",
                             "PulseAudio isn't working or software is missing.")
            return

        ''' Cannot skip Ad on YouTube using keyboard:
                https://webapps.stackexchange.com/questions/100869/
                    keyboard-shortcut-to-close-the-ads-on-youtube '''
        audio_frm = ttk.Frame(self.event_frame, borderwidth=g.FRM_BRD_WID,
                              padding=(2, 2, 2, 2), relief=tk.RIDGE)
        audio_frm.grid(column=0, row=0, sticky=tk.NSEW)
        audio_frm.grid_columnconfigure(1, minsize=g.MON_FONTSIZE*15, weight=1)
        audio_frm.grid_columnconfigure(2, minsize=700, weight=1)  # Status scrollbox

        # Status scroll box in third column
        _sb = toolkit.CustomScrolledText(audio_frm, state="normal", font=g.FONT,
                                         height=11, borderwidth=15, relief=tk.FLAT)
        toolkit.scroll_defaults(_sb)  # Default tab stops are too wide

        # Tabs for _sb (scrollbox) created by watchYouTube
        _tabs2 = ("140", "right", "160", "left")
        _sb.tag_config("indent2", lmargin2=180)

        def _reset_tabs2(event):
            """ https://stackoverflow.com/a/46605414/6929343 """
            event.widget.configure(tabs=_tabs2)

        _sb.configure(tabs=_tabs2, wrap=tk.WORD)
        _sb.bind("<Configure>", _reset_tabs2)
        _sb.grid(row=0, column=2, rowspan=9, padx=3, pady=3, sticky=tk.NSEW)
        # ScrollText with instructions third column row span 9
        _sbt = "INSTRUCTIONS:\n\n"
        _sbt += "1. Messages automatically scroll when videos start.\n\n"
        _sbt += '2. Messages can be copied by highlighting text and\n'
        _sbt += '     typing <Control> + "C".\n\n'
        _sbt += "3. Click Help button below for more instructions.\n\n"
        _sb.insert("end", _sbt)

        self.update_idletasks()
        asi = ()

        def init_ad_or_video():
            """ YouTube is starting up.
                yt_start > 0, ad_start = 0 and video_start = 0.
                Force fullscreen in order to discover progress bar color.
                Find out if Ad or Video. Set start time for Ad or Video.

                2025-07-14 TODO: Stuck in "A/V Check" loop because video
                    already playing when watchYouTube() is started so no
                    red progress bar will appear. Also if Tim-ta sounds
                    an alarm in Firefox then video is self-positive for new
                    sink-input index. VU Meters are lagging .1 seconds every
                    16 ms.

                Status:  A/V check / Ad playing / Video playing /
                         skip check /
                Duration: 99:99:99.99

            """

            _who2 = _who[:-1] + " init_ad_or_video():"
            try:
                _x, _y = GLO["YT_AD_BAR_POINT"]
            except AttributeError:
                return  # This will repeat test forever but overhead is low.

            if not bool(asi):
                return  # Too early in the game

            if mon.wn_is_fullscreen is False:
                # If not full screen, force it.
                #os.popen("wmctrl -ir " + str(mon.wn_xid_hex) +
                #         " -b toggle,fullscreen")
                os.popen('xdotool key f')  # Full Screen on ACTIVE window
                mon.wn_is_fullscreen = True
                update_rows()
                _line = "\t" + format_time()
                _line += "\tWindow forced fullscreen:" + str(mon.wn_xid_hex)
                _sb.insert("end", _line + "\n", "indent2")
                _sb.see("end")

            _tk_clr = _pi.get_colors(_x, _y)  # Get color
            if _tk_clr == GLO["YT_AD_BAR_COLOR"] and _vars["ad_start"] == 0.0:
                # 	17:13:09.46	Ad has started on index: 1231
                # 	17:13:09.87	Ad has started on index: 1231
                _vars["ad_start"] = _vars["pav_start"]
                _vars["video_start"] = 0.0  # 2025-07-15 Extra insurance
                pav.set_volume(str(asi.index), 0)  # Set volume to zero
                update_rows()
                _line = "\t" + format_time(_vars["ad_start"])
                _line += "\tAd muted on index: " + str(_vars["pav_index"])
                _sb.insert("end", _line + "\n", "indent2")
                _sb.see("end")
            elif _tk_clr == GLO["YT_VIDEO_BAR_COLOR"] and _vars["video_start"] == 0.0:
                #_vars["video_start"] = time.time()
                _vars["video_start"] = _vars["pav_start"]
                _vars["ad_start"] = 0.0  # 2025-07-14 Extra insurance
                update_rows()
                _line = "\t" + format_time(_vars["video_start"])
                _line += "\tVideo has started on index: " + str(_vars["pav_index"])
                _sb.insert("end", _line + "\n", "indent2")
                _sb.see("end")
            else:
                v3_print(_who2)
                v3_print("  Color found at: [" + str(_x) + "," + str(_y) + "]",
                         "is:", _tk_clr)
                v3_print("  Waiting for Ad or Video color to appear...")
                # 2025-07-08 TODO: Set limit on messages 1 per second for 10 seconds?
                return

        def init_ad_skip():
            """ YouTube Ad is running.
                ad_started > 0 and video_started = 0.
                Wait 4.7 seconds.

2025-07-16 Next video after the Duran - Ad skip didn't work.

19:32:04.53	Window forced fullscreen:0x3c00028
19:32:04.90	YouTube Video: (1) Ukraine War Update: Russia DOESN'T Stop, Heavy Assault Towards Rodynske - YouTube
19:32:05.06	Window forced fullscreen:0x3c00028
19:32:05.17	A/V check
19:32:04.90	Ad has started on index: 1252
19:32:08.89	Ad has started on index: 1252
19:32:13.70	Skip Button clicked
19:32:08.89	Ad has started on index: 1252
19:32:13.91	Skip Button clicked
19:32:08.89	Ad has started on index: 1252
19:32:14.13	Skip Button clicked
19:32:14.13	A/V check
19:32:08.89	Ad has started on index: 1252
19:32:14.33	Skip Button clicked
19:32:08.89	Ad has started on index: 1252
19:32:14.54	Skip Button clicked
19:32:08.89	Ad has started on index: 1252
19:32:14.74	Skip Button clicked
19:32:08.89	Ad has started on index: 1252
19:32:14.97	Skip Button clicked
19:32:08.89	Ad has started on index: 1252
19:32:15.17	Skip Button clicked
19:32:08.89	Ad has started on index: 1252
19:32:15.36	Skip Button clicked
19:32:08.89	Ad has started on index: 1252
19:32:15.70	Skip Button clicked
19:32:16.39	Window forced fullscreen:0x3c00028
19:32:16.22	Video has started on index: 1253

            """

            _who2 = _who[:-1] + " init_ad_skip():"
            if time.time() < 4.7 + _vars["ad_start"]:
                # 2025-07-13 FIX: test was '> 4.7' causing false positives
                return  # Too soon to check because ad can be white

            try:
                _x, _y = GLO["YT_SKIP_BTN_POINT"]
            except AttributeError:  # Coordinates for skip button unknown
                return  # This will repeat test forever but overhead is low.

            _tk_clr = _pi.get_colors(_x, _y)  # Get color
            if _tk_clr != GLO["YT_SKIP_BTN_COLOR"]:
                v3_print(_who2)
                v3_print("  Color found at: [" + str(_x) + "," + str(_y) + "]",
                         "is:", _tk_clr)
                v3_print("  Waiting for Skip Button color to appear...")
                return  # Not skip button color

            # Send click to skip button coordinates
            os.popen('xdotool mousemove ' + str(_x) + ' ' + str(_y) +
                     ' click 1 sleep 0.01 mousemove restore')

            ''' 2025-07-13 TODO: Separate wait for Skip button to disappear. 
                    If it doesn't disappear in a second, repeat the click. 
            '''
            _vars["ad_start"] = 0.0  # Turn off ad running
            _line = "\t" + format_time()
            _line += "\tSkip Button clicked"
            _sb.insert("end", _line + "\n", "indent2")
            _sb.see("end")

        def update_duration():
            """ Update Status and Duration in 8th & 9th rows.
                Called every second.

                Status:   A/V check / Ad playing / Video playing /
                          Skip check / NOT YouTube

                Duration: 99:99:99.99
            """
            _who2 = _who[:-1] + " update_duration():"
            ''' _vars available for creating status
            "pav_start": 0.0, "pav_index": "", "pav_volume": 0.0,
            "pav_corked": False, "pav_application": "", "pav_name": "",
            "yt_start": 0.0, "yt_index": "", "yt_duration": 0.0, 
            "av_check": 0.0, "skip_check": 0.0,
            "ad_start": 0.0, "ad_index": "", "ad_duration": 0.0,
            "video_start": 0.0, "video_index": "", "video_duration": 0.0,
            "wn_name": "", "wn_xid_hex": ""  # Could be YT or not YT
            '''
            _now = time.time()
            _status = ""
            old_status = text_status.get()
            _dur = 0.0

            def update_sb(msg):
                """ Shared local function """
                _line = "\t" + format_time()
                _line += "\t" + msg
                _sb.insert("end", _line + "\n", "indent2")
                _sb.see("end")


            if _vars["ad_start"] > 0.0 and _now > 4.7 + _vars["ad_start"]:
                _dur = _now - _vars["ad_start"] - 4.7
                _status = "Skip check"
                if old_status != _status:
                    update_sb(_status)
            elif _vars["ad_start"] > 0.0:
                _dur = _now - _vars["ad_start"]
                _status = "Ad playing"
            elif _vars["video_start"] > 0.0:
                _dur = _now - _vars["video_start"]
                _status = "Video playing"
            elif _vars["yt_start"] > 0.0:
                _dur = _now - _vars["pav_start"]
                _status = "A/V check"
                if old_status != _status:
                    update_sb(_status)
            elif _vars["wn_name"] != "":
                _dur = _now - _vars["pav_start"]
                _status = "NOT YouTube"
                if old_status != _status:
                    update_sb(_status)

            text_status.set(_status)
            text_duration.set(tmf.mm_ss(_dur))

        def match_window(_input):
            """ Match window to pav. _input is active sink input from PulseAudio
                If found, display fullscreen status in column 2
                Before calling, buildSB() has set all _vars to null.

                    WRONG WRONG

                When a new sink appears it can happen when Video switches to an
                Ad or when user pauses video. If YouTube is still fullscreen and
                video name matches what was playing, don't toss out all variables.

                If new sink is for a stale window or for a windowless sound input
                then keep the old pulse audio info and _vars[] lists in memory.

                Once a YouTube is in memory it should stay in video status scrolled
                Text widget. The lower pulse audio scrolled Text widget will have
                each active sink input.
            """
            _who2 = _who[:-1] + " match_window():"
            mon.make_wn_list()  # Make Windows List
            _name = _input.name
            _app = _input.application
            #text_pid.set(str(_input.pid))
            if _name == "Playback Stream" and _app.startswith("Telegram"):
                _name = "Media viewer"  # Telegram in mon

            if mon.get_wn_by_name(_name, pid=_input.pid):
                #text_is_fullscreen.set(str(mon.wn_is_fullscreen))  # Boolean
                pass  # Drop down to set window name in scroll box
            else:
                if _app != 'ffplay':
                    #v0_print(_who2, "Matching window not found:")
                    #v0_print("  Name:", _name, " | PID:", _input.pid)
                    #v0_print("  Application:", _app)
                    # Rewind last scrollbox text entry?
                    pass
                else:
                    pass  # ps -ef | grep ffplay PARAMETERS.../song name

                #_vars["yt_start"] = 0.0  # 2025-07-15 comment out
                #_vars["yt_duration"] = 0.0  # 2025-07-15 comment out
                _vars["wn_found"] = False
                _vars["wn_xid_hex"] = "N/A"
                #_line = "\t" + format_time()
                #_line += "\tDismissing: " + _name
                #_sb.insert("end", _line + "\n", "indent2")
                #_sb.see("end")
                # 2025-07-15 TODO: Log to _sb_pav
                #   Create list of all pav logged.
                return False

            ''' _sb (scrollbox Text) processing 
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

            _vars["wn_found"] = True
            _vars["wn_xid_hex"] = mon.wn_xid_hex

            if _name.endswith(" - YouTube"):
                if _name != _vars['last_name']:
                    _vars["yt_start"] = _vars["pav_start"]
                    _vars["yt_duration"] = 0.0
                    _line = "\t" + format_time(_vars["yt_start"])
                    _line += "\tYouTube Video: " + _name
                    _sb.insert("end", _line + "\n", "indent2")
                    _sb.see("end")
                    _vars['last_name'] = _name
                    _vars['last_start'] = _vars["yt_start"]
                else:
                    _vars['yt_start'] = _vars["last_start"]

                # Ad has started or video is playing, find out which one
                _vars["ad_start"] = 0.0
                _vars["video_start"] = 0.0
            else:
                # Can be a Firefox sound (Tim-Ta) or a non-YouTube video playing
                #_vars["yt_start"] = 0.0  # shows YT running even if it's not
                #_vars["yt_duration"] = 0.0
                #_line = "\t" + format_time()
                #_line += "\tDismissing: " + _name
                #_sb.insert("end", _line + "\n", "indent2")
                #_sb.see("end")
                pass

            return True

        def format_time(_time=None):
            """ Format passed time or current time if none passed. 
            import datetime
            """
            if _time:
                dt_time = dt.datetime.fromtimestamp(_time)
            else:
                dt_time = dt.datetime.now()

            formatted_time = dt_time.strftime("%H:%M:%S.") + \
                dt_time.strftime("%f")[:2]
            return formatted_time

        def buildSB(_sink_inputs):
            """ Build scrollbox
            :return: _asi (Active Sink Input tuple)
            """
            scrollbox.delete("3.0", "end")  # delete all but headings
            _asi = ()  # named tuple of last active sink input
            for _si in reversed(_sink_inputs):
                _line = str(_si.index) + "\t" + str(_si.volume) + "\t"
                _line += str(_si.application) + "\t" + toolkit.normalize_tcl(_si.name)
                scrollbox.insert("end", _line + "\n", "hanging_indent")
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
                v0_print(_who, "Catastrophic error. No Sink Inputs")
                return ()

            _vars["pav_start"] = time.time()
            _vars["pav_index"] = _asi.index
            _vars["pav_application"] = _asi.application
            _vars["pav_name"] = _asi.name
            _vars["pav_volume"] = _asi.volume
            _vars["pav_corked"] = _asi.corked

            #_line = "\t" + format_time(_vars["pav_start"])
            #_line += "\tNew Sink Input #: " + str(_vars["pav_index"])
            #_sb.insert("end", _line + "\n", "indent2")
            #_sb.see("end")

            _vars["wn_found"] = False
            _vars["wn_xid_hex"] = "N/A"
            #_vars["yt_start"] = 0.0
            #_vars["yt_duration"] = 0.0
            #_vars["ad_start"] = 0.0
            #_vars["ad_duration"] = 0.0
            #_vars["video_start"] = 0.0
            #_vars["video_duration"] = 0.0

            return _asi

        def update_rows():
            """ Update rows with pulse audio active sink input (asi)
                and matching window (mon.wn) attributes. 

                2025-07-07 TODO: Relocate to only call when sink or window changes.
            """
            text_index.set(str(asi.index))  # Long Integer
            text_pid.set(asi.pid)
            text_pa_app.set(asi.application)  # Could be UTF-8

            def set_time(_val):
                """ Format date if not zero. """
                if _val == 0.0:
                    return "N/A"
                return format_time(_val)

            text_wn_xid_hex.set(str(_vars["wn_xid_hex"]))  # May already be N/A
            text_yt_start.set(set_time(_vars["yt_start"]))  # Set to N/A if zero
            #text_status.set(set_time(_vars["ad_start"]))
            #text_duration.set(set_time(_vars["video_start"]))

            if _vars["wn_found"] is False:
                text_is_YouTube.set("N/A")  # No matching window found so probably
                text_is_fullscreen.set("N/A")  # ffplay or speech-dispatcher, etc.
                return

            _yt = "yes" if asi.name.endswith(" - YouTube") else "no"
            text_is_YouTube.set(_yt)
            _fs = "yes" if mon.wn_is_fullscreen else "no"
            text_is_fullscreen.set(_fs)

        def add_row(row_no, label, _val, _type="String", tt_text=None):
            """ Add row to Pointer Location section
                Column 0 contains label, Column 1 contains passed text which is
                initialized into string variable returned to caller.
            """
            _who2 = _who[:-1] + " add_row():"
            label = ttk.Label(audio_frm, text=label, font=g.FONT)
            label.grid(row=row_no, column=0, sticky=tk.NSEW, padx=15, pady=10)

            if _type == "String":
                _var = tk.StringVar()
            elif _type == "Int":
                _var = tk.IntVar()
            else:
                v0_print(_who, "Unknown tk variable type:", _type)
                return None

            _var.set(_val)
            text = ttk.Label(audio_frm, textvariable=_var, font=g.FONT)
            text.grid(row=row_no, column=1, sticky=tk.NSEW, padx=15)
            if self.tt and tt_text:
                self.tt_add(label, tt_text)
            return _var

        # ROWS: Sink Input Index, PA PID, PA Application, PA name
        #       X11 Window Number, Full Screen?, Window App, Window Name
        text_index = add_row(0, "Sink input #:", "N/A")  # Long Integer
        text_pid = add_row(1, "Process ID (PID):", 0, _type="Int")
        text_pa_app = add_row(2, "PulseAudio App:", "N/A")
        text_is_YouTube = add_row(3, "YouTube?:", "N/A")
        text_wn_xid_hex = add_row(4, "Window number:", "N/A")
        text_is_fullscreen = add_row(5, "Fullscreen?:", "N/A")
        text_yt_start = add_row(6, "YouTube Start:", "N/A")
        text_status = add_row(7, "Status:", "N/A")
        text_duration = add_row(8, "Duration:", "N/A")

        _vars = {  # pav_ = Pulse audio volume, wn_ = Wnck Window (GNOME)
            "pav_start": 0.0, "pav_index": "", "pav_volume": 0.0,
            "pav_corked": False, "pav_application": "", "pav_name": "",
            "yt_start": 0.0, "yt_index": "", "yt_duration": 0.0,
            "av_check": 0.0, "skip_check": 0.0, "last_name": "",
            "ad_start": 0.0, "ad_index": "", "ad_duration": 0.0,
            "video_start": 0.0, "video_index": "", "video_duration": 0.0,
            "wn_name": "", "wn_xid_hex": ""  # Could be YT or not YT
        }

        # audio_frm freezes xorg, use self.event_top
        _vum = toolkit.VolumeMeters(
            'homa', self.event_top, left_col=3, right_col=4)

        _vum.reset_history_size(8)  # 2025-07-01 Change 4 to 8.
        _vum.spawn()  # Daemon to populate Amplitude in files
        mon = monitor.Monitors()  # To get Wnck Windows
        _pi = toolkit.PointerInspector(None, mon=mon)

        while not os.path.isfile(_vum.AMPLITUDE_LEFT_FNAME):
            self.refreshApp()  # wait another 16ms to 33ms for file to appear.

        last_sink_inputs = []  # Force reread
        # Loop forever until DisplayCommon() window closed
        while self.event_top and self.event_top.winfo_exists():
            if not self.refreshApp(tk_after=False) or self.suspending:
                break
            try:
                self.after(5)  # tk_after=False is too FAST
                _vum.update_display()  # paint LED meters reflecting amplitude
            except (tk.TclError, AttributeError):
                break  # Break in order to terminate vu_meter.py below

            sink_inputs = pav.get_all_inputs()
            self.last_rediscover_time = time.time()  # Prevent Rediscover
            self.last_refresh_time = self.last_rediscover_time  # Prevent Resume

            # YouTube started but Ad or Video status unknown?
            if _vars["yt_start"] != 0.0 and _vars["ad_start"] == 0.0 and \
                    _vars["video_start"] == 0.0:
                init_ad_or_video()  # Setup if Ad or Video is running

            # Is YouTube Ad intercept active?
            if _vars["ad_start"] != 0.0 and _vars["video_start"] == 0.0:
                init_ad_skip()  # Setup if Ad or Video is running

            # Update YouTube progress every second
            second = ext.h(time.time()).split(":")[2].split(".")[0]
            # Current second of "HH:MM:SS.ff"
            if second != self.last_second:
                update_duration()  # Update status and duration
                self.last_second = second  # Wait for second change to check again

            # Have sink_input(s) changed?
            if sink_inputs == last_sink_inputs:
                continue  # input_sinks didn't change

            asi = buildSB(sink_inputs)  # asi = Active Sink Input named tuple

            # Get matching window attributes
            mon.make_wn_list()
            if match_window(asi):
                v1_print(_who, "Matching window:", mon.wn_dict['xid_hex'])
            else:
                v1_print(_who, "Matching window NOT FOUND!")

            update_rows()  # 2025-07-03 - Handles mon.wn_dict is blank.

            last_sink_inputs = sink_inputs  # deepcopy NOT required

        _vum.terminate()
        #DisplayCommonInst.close()  # 2025-06-26. Stale window still open??

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
        for mac_arp in ni.mac_dicts:
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

        scrollbox = self.DisplayCommon(_who, title, x=x, y=y, width=700,
                                       help="ViewBluetoothDevices")
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
                mac_dict = ni.get_mac_dict(address)
                mac_dict['ip'] = name  # ip isn't used for bluetooth.
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

            Called about 3 times per second during self.refreshApp() cycle.
            self.refreshApp() in turn is called by bleSaveInst.breatheColors().
            bleSaveInst.monitorBreatheColors() returns formatted text lines.

            First time, calls DisplayCommon to create Window, Frame and Scrollbox.
        """
        _who = self.who + "DisplayBreathing():"
        title = "Bluetooth LED Breathing Colors Statistics"
        if self.bleSaveInst is None:
            v0_print(_who, "self.bleSaveInst is None")
            return  # Should not happen

        def close():
            """ Close callback """
            self.bleScrollbox = None

        if self.bleSaveInst.already_breathing_colors is False:
            v0_print(_who, "'self.bleSaveInst.already_breathing_colors' is <False>")
            close()
            return  # 2025-02-09 calling "Nighttime" when DisplayBreathing() is running
            
        if self.bleScrollbox is None:
            self.bleScrollbox = self.DisplayCommon(_who, title, close_cb=close,
                                                   help="ViewBreathingStats")
            # Tabs for self.event_scrollbox created by self.DisplayCommon()
            tabs = ("400", "right", "550", "right", "700", "right",
                    "750", "left", "1125", "right")  # Note "numeric" aligns on commas when no decimals!

            def reset_tabs(event):
                """ https://stackoverflow.com/a/46605414/6929343 """
                event.widget.configure(tabs=tabs)

            self.bleScrollbox.configure(tabs=tabs)
            self.bleScrollbox.bind("<Configure>", reset_tabs)

            def in4(name1, value1, name2, value2):
                """ Insert 2 parameter variable pairs into custom scrollbox """
                line = name1 + ":\t" + str(value1) + "\t\t|\t"
                line += name2 + ":\t" + str(value2) + "\n"
                self.bleScrollbox.insert("end", line)

            p = self.bleSaveInst.parm  # shorthand to dictionary
            step_count = int(float(p["span"]) / float(p["step"]))
            step_value = float(p["high"] - p["low"]) / float(step_count)
            in4("Dimmest value", p["low"], "Breathe duration", p["span"])
            in4("Brightest value", p["high"], "Step duration", p["step"])
            in4("Dimmest hold seconds", p["bots"], "Step count", step_count)
            in4("Brightest hold seconds", p["tops"], "Step value", step_value)
            self.bleScrollbox.insert("end", "\n\n")

            self.last_red = self.last_green = self.last_blue = 0

        # Body is only updated when red, green or blue change
        if self.last_red == self.bleSaveInst.red and \
                self.last_green == self.bleSaveInst.green and \
                self.last_blue == self.bleSaveInst.blue:
            return

        self.last_red = self.bleSaveInst.red
        self.last_green = self.bleSaveInst.green
        self.last_blue = self.bleSaveInst.blue

        # Delete dynamic lines in custom scrollbox
        self.bleScrollbox.delete(6.0, "end")

        all_lines = self.bleSaveInst.monitorBreatheColors()
        if all_lines is None:
            v0_print(_who, "'all_lines' is <None>. Exiting.")
            close()
            return

        try:
            self.bleScrollbox.insert("end", all_lines)  # 2025-06-19 sudden error
        except tk.TclError as err:
            v0_print(_who, "Tkinter error:")
            v0_print(err)

        self.bleScrollbox.highlight_pattern("Blue:", "blue")
        self.bleScrollbox.highlight_pattern("Green:", "green")
        self.bleScrollbox.highlight_pattern("Red:", "red")

        self.bleScrollbox.highlight_pattern("Function", "yellow")
        self.bleScrollbox.highlight_pattern("Milliseconds", "yellow")
        self.bleScrollbox.highlight_pattern("Count", "yellow", upper_and_lower=False)
        self.bleScrollbox.highlight_pattern("Average", "yellow")
        self.bleScrollbox.highlight_pattern("Lowest", "yellow")
        self.bleScrollbox.highlight_pattern("Highest", "yellow")

        ''' Button frame background shows monitor facsimile color of LED lights '''
        self.event_btn_frm.configure(bg=self.bleSaveInst.monitor_color)

    def DisplaySony(self, cr):
        """ Display Sony KDL/Bravia TV controls in real time.

            Calls DisplayCommon to create Window, Frame and Scrollbox.
        """
        _who = self.who + "DisplaySony():"
        sony = cr.inst_dict['instance']  # saveSony
        title = "Sony TV Settings"

        #x, y = hc.GetMouseLocation()  # 2025-05-30 TODO move into DisplayCommon()
        #scrollbox = self.DisplayCommon(_who, title, x=x, y=y, width=1200,
        #                               help="ViewBluetoothDevices")
        scrollbox = self.DisplayCommon(_who, title, width=1200,
                                       help="ViewBluetoothDevices")
        if scrollbox is None:
            return  # Window already opened and method is running

        sony.getAllSettings()  # defaults to no_log=True

        # Tabs for self.event_scrollbox created by self.DisplayCommon()
        tabs = ("400", "right", "550", "right", "700", "right",
                "750", "left", "1125", "right")  # Note "numeric" aligns on commas when no decimals!

        def reset_tabs(event):
            """ https://stackoverflow.com/a/46605414/6929343 """
            event.widget.configure(tabs=tabs)

        scrollbox.configure(tabs=tabs)
        scrollbox.bind("<Configure>", reset_tabs)

        def in4(name1, value1, name2=None, value2=None):
            """ Insert 2 parameter variable pairs into custom scrollbox """
            line = name1 + ":\t" + str(value1)
            if name2 is not None and value2 is not None:
                line += "\t\t|\t" + name2 + ":\t" + str(value2)
            line += "\n"
            scrollbox.insert("end", line)

        ''' Single column mode with TV Position shown
        ''' 
        in4("Power Status", sony.powerStatus)
        in4("Power Saving Mode", sony.powerSavingMode)
        in4("TV Position", sony.tvPosition)
        in4("Speaker Volume", sony.volumeSpeaker)
        in4("Headphones Volume", sony.volumeHeadphones)
        in4("Subwoofer Level", sony.subwooferLevel)
        in4("Subwoofer Freq", sony.subwooferFreq)
        in4("Subwoofer Phase", sony.subwooferPhase)
        in4("Subwoofer Power", sony.subwooferPower)
        scrollbox.insert("end", "\n\n")

        ''' Double column mode with TV Position hidden
        in4("Power Status", sony.powerStatus,
             "Subwoofer Power", sony.subwooferPower)
        in4("Power Saving Mode", sony.powerSavingMode,
             "Subwoofer Phase", sony.subwooferPhase)
        in4("Speaker Volume", sony.volumeSpeaker,
             "Subwoofer Level", sony.subwooferLevel)
        in4("Headphones Volume", sony.volumeHeadphones,
             "Subwoofer Freq", sony.subwooferFreq)
        scrollbox.insert("end", "\n\n")
        '''

        ''' Display Audio. Rows 0 to 89 available in self.event_top '''
        if not self.audio.isWorking:
            v0_print(_who, "not self.audio.isWorking")
            return  # Cannot display VU meters
        v2_print(_who, "self.audio.isWorking", self.audio.isWorking)

        '''
        Skip Ad on YouTube using keyboard?
        https://webapps.stackexchange.com/questions/100869/
            keyboard-shortcut-to-close-the-ads-on-youtube
        '''
        audio_frm = ttk.Frame(self.event_frame, borderwidth=g.FRM_BRD_WID,
                              padding=(2, 2, 2, 2), relief=tk.RIDGE)
        audio_frm.grid(column=0, row=0, sticky=tk.NSEW)
        audio_frm.grid_columnconfigure(1, weight=1)

        def add_row(row_no, label, txt, tt_text=None):
            """ Add row to PulseAudio section
                Column 0 contains label, Column 1 contains passed text which is
                initialized into string variable returned to caller.
            """
            _who2 = _who[:-1] + " add_row():"
            label = ttk.Label(audio_frm, text=label, font=g.FONT)
            label.grid(row=row_no, column=0, sticky=tk.NSEW, padx=15, pady=10)
            string_var = tk.StringVar()
            string_var.set(txt)
            text = ttk.Label(audio_frm, textvariable=string_var, font=g.FONT)
            text.grid(row=row_no, column=1, sticky=tk.NSEW, padx=15, pady=10)
            if self.tt and tt_text:
                self.tt_add(label, tt_text)
            return string_var

        def match_window(_input):
            """ Match window to pav. _input is active sink input from PulseAudio
                If found, display fullscreen status in column 2
            """
            _who2 = _who[:-1] + " match_window():"
            mon.make_wn_list()  # Make Windows List
            _name = _input.name
            _app = _input.application
            if _name == "Playback Stream" and _app.startswith("Telegram"):
                _name = "Media viewer"  # Telegram in mon
            if mon.get_wn_by_name(_name, pid=_input.pid):
                text_fullscreen.set(str(mon.wn_is_fullscreen))  # Boolean
                text_pid.set(str(_input.pid))

                return True
            else:
                v0_print(_who2, "Window name not found:")
                v0_print("  Name:", _name, " | PID:", _input.pid)
                v0_print("  Application:", _app)

            text_fullscreen.set("?")  # Boolean
            return False

        mon = monitor.Monitors()
        mon.make_wn_list()  # Make Windows List
        last_sink_inputs = pav.get_all_inputs()
        asi = pav.active_input_tuple
        asi = asi if bool(asi) else last_sink_inputs[-1]  # No active inputs
        text_fullscreen = add_row(0, "Full screen?:", "?")  # asi is <None>
        text_pid = add_row(3, "Binary PID:", "?")  # that are inactive (corked).

        # 5 rows to display in window
        try:
            v1_print(_who, "Displaying PulseAudio sink input index:", asi.index)  # 191
            v1_print(" ", "len(last_sink_inputs):", len(last_sink_inputs))  # 4
            v1_print(" ", asi)
            match_window(asi)  # Sets text_fullscreen & text_pid tkinter variables
            text_index = add_row(1, "Sink number:", str(asi.index))  # Long Integer
            text_app = add_row(2, "Application:", asi.application)
            text_video = add_row(4, "Video:", toolkit.normalize_tcl(asi.name))
        except AttributeError:
            text_index = add_row(1, "Sink number:", "?")  # Not a single sink_input
            text_app = add_row(2, "Application:", "?")  # exists including those
            text_video = add_row(4, "Video:", "?")

        # Volume Meters in third and fourth columns
        _vum = toolkit.VolumeMeters(
            'homa', self.event_top, left_col=2, right_col=3, rowspan=5)
        _vum.reset_history_size(10)  # Default is 2. Try 10 decay to slow
        _vum.reset_history_size(5)  # 2025-06-29 value 5 "feels" natural

        _vum.spawn()  # Monitor VU meters
        while not os.path.isfile(_vum.AMPLITUDE_LEFT_FNAME):
            self.refreshApp()  # wait 16ms to 33ms for file to be created.

        # Loop forever until window closed
        while self.isActive:
            # 2025-06-25 TODO: Time slice for LED breathing, or create LED daemon
            if not self.refreshApp(tk_after=False) or self.suspending:
                break
            try:
                self.after(5)  # tk_after=False is too FAST
                _vum.update_display()  # paint LED meters reflecting amplitude
            except (tk.TclError, AttributeError):
                break  # Break in order to terminate vu_meter.py below
            self.last_rediscover_time = time.time()  # Prevent Rediscover
            self.last_refresh_time = self.last_rediscover_time  # Prevent Resume

            ''' Have Pippim flavor sink_input(s) changed? '''
            sink_inputs = pav.get_all_inputs()
            if sink_inputs == last_sink_inputs:
                continue  # input_sinks didn't change

            ''' Get last active sink into new_sink. May be more than one found. '''
            active = pav.active_input_tuple  # last uncorked sink_input
            text_index.set(str(active.index))  # Could be 3 second alarm sound
            text_app.set(active.application)  #
            text_video.set(toolkit.normalize_tcl(active.name))
            v0_print("New Active Sink Input:", active)

            ''' Get matching window attributes '''
            mon.make_wn_list()
            if match_window(active):
                v0_print("Matching window:", mon.wn_dict)
            else:
                v0_print("Matching window NOT FOUND!")

            last_sink_inputs = sink_inputs  # deepcopy NOT required

        _vum.terminate()
        #DisplayCommonInst.close()  # 2025-06-26. Stale window still open??

    def DisplayCommon(self, _who, title, x=None, y=None, width=1200, height=500,
                      close_cb=None, help=None):
        """ Common method for DisplayBluetooth(), DisplayErrors(), DisplayTimings()
                DisplayBreathing()

            Caller has 90 heading rows, 10 footer rows and 10 columns to use. For
                example, DisplayBreathing() uses 4 heading rows and 5 columns.

        """

        if self.event_scroll_active and self.event_top:
            self.event_top.focus_force()
            self.event_top.lift()
            return

        # 2026-06-29 DRY: Next two lines repeated 3 times
        self.event_top = self.event_frame = self.event_scroll_active = None
        self.event_scrollbox = self.event_btn_frm = None

        def close(*_args):
            """ Close window painted by this DisplayCommon() method """
            if not self.event_scroll_active:
                return
            self.win_grp.unregister_child(self.event_top)
            self.tt.close(self.event_top)
            self.event_scroll_active = None
            self.event_top.destroy()
            self.event_top = None
            if close_cb:
                close_cb()
            self.event_top = self.event_frame = self.event_scroll_active = None
            self.event_scrollbox = self.event_btn_frm = None
            self.updateDropdown()

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

        self.event_scrollbox = toolkit.CustomScrolledText(
            self.event_frame, state="normal", font=ha_font, borderwidth=15, relief=tk.FLAT)
        toolkit.scroll_defaults(self.event_scrollbox)  # Default tab stops are too wide
        self.event_scrollbox.config(tabs=("50", "100", "150"))
        self.event_scrollbox.grid(row=90, column=0, columnspan=10, padx=3, pady=3, sticky=tk.NSEW)
        # 90 rows available for headings, 10 rows available for footers
        self.event_frame.rowconfigure(90, weight=1)
        self.event_frame.columnconfigure(0, weight=1)

        self.event_btn_frm = tk.Frame(self.event_frame, borderwidth=g.FRM_BRD_WID,
                                      relief=tk.RIDGE)
        self.event_btn_frm.grid(row=100, column=0, sticky=tk.NSEW)
        self.event_btn_frm.columnconfigure(0, weight=1)

        def button_func(row, column, txt, command, tt_text, tt_anchor, pic):
            """ Function to combine ttk.Button, .grid() and tt.add_tip() """
            widget = ttk.Button(self.event_btn_frm, text=" "+txt, width=len(txt)+2,
                                command=command, style="C.TButton",
                                image=pic, compound="left")
            widget.grid(row=row, column=column, padx=5, pady=5, sticky=tk.E)
            if tt_text is not None and tt_anchor is not None:
                self.tt.add_tip(widget, tt_text, anchor=tt_anchor)
            return widget

        if help is not None:
            ''' Help Button - ⧉ Help - Videos and explanations on pippim.com
                https://www.pippim.com/programs/homa.html#Introduction '''
            help_text  = "Open new window in default web browser for\n"
            help_text += "videos and explanations on using this screen.\n"
            help_text += "https://www.pippim.com/programs/homa.html#\n"
            button_func(0, 0, "Help", lambda: g.web_help(help),
                        help_text, "ne", self.img_mag_glass)

        button_func(0, 1, "Close", close, "Close this window.", "ne", self.img_close)

        # Foreground colors
        self.event_scrollbox.tag_config('red', foreground='red')
        self.event_scrollbox.tag_config('blue', foreground='blue')
        self.event_scrollbox.tag_config('green', foreground='green')
        self.event_scrollbox.tag_config('black', foreground='black')
        self.event_scrollbox.tag_config('gray', foreground='gray')

        # Highlighting background colors
        self.event_scrollbox.tag_config('yellow', background='yellow')
        self.event_scrollbox.tag_config('cyan', background='cyan')
        self.event_scrollbox.tag_config('magenta', background='magenta')
        self.updateDropdown()
        return self.event_scrollbox

    def GATTToolJobs(self, found_inst=None):
        """ Check quantity and percentage of gatttool process ID's.

            ps -aux | grep gatttool | grep -v grep
        """
        _who = self.who + "GATTToolJobs():"
        v1_print("\n" + _who, "Check GATTTool percentage")
        if not self.checkInstalled("ps"):
            v0_print(_who, "Command 'ps' not installed. Exiting.")
            return
        if not self.checkInstalled("grep"):
            v0_print(_who, "Command 'grep' not installed. Exiting.")
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
                # 1  [<USER>, '8336',  '10.7', '0.0', '0', '0', '?', 'Zs', '10:47', '0:24']
                # 2  [<USER>, '13964', '61.2', '0.0', '0', '0', '?', 'Zs', '10:50', '1:00']
                # 3  [<USER>, '14836', '42.2', '0.0', '0', '0', '?', 'Zs', '10:50', '0:30']
                # 4  [<USER>, '15789', '0.0',  '0.0', '0', '0', '?', 'Zs', '10:50', '0:00']
                # 5  [<USER>, '16969', '0.0',  '0.0', '21556', '3376', 'pts/27', 'Ss+', '10:51', '0:00']
                # external.kill_pid_running() ERROR: os.kill  failed for PID: 15789
                v1_print(" ", ll[:10])
                if float(ll[2]) > 5.0:  # CPU percentage > 5%?
                    v1_print("   PID:", ll[1], " | CPU usage over 5%:", ll[2])
                    high_pid_perc += 1  # Also has "?" instead of 'pts/99'
                elif ll[6] == "?":
                    v1_print("   PID:", ll[1], " | 'pts/99' == '?'.  Skipping...")
                    continue
                found_pids.append(ll)

        # If less than 4 pids and none > 5% skip AskQuestion()
        if len(found_pids) < 4 and high_pid_perc == 0:
            return

        ''' Found_pids have 12 results, 3 for each time view Bluetooth Devices is run:        
        [snip 4...]
        [<USER>, '17229', '90.9', '0.0', '21556', '3344', 'pts/31', 'Rs+', '00:59', '0:28', 
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
        answer = message.AskQuestion(self, title, text, 'no', win_grp=self.win_grp,
                                     thread=self.refreshThreadSafe)

        text += "\n\t\tAnswer was: " + answer.result
        v3_print(title, text)

        v3_print(_who, "self.win_grp AFTER :")  # AskQuestion() win_grp debugging
        v3_print(self.win_grp.window_list)

        if answer.result != 'yes':
            return  # Don't delete pids

        if found_inst and found_inst.device is not None:
            found_inst.Disconnect()  # started device's gatttool will be killed & lags
            if self.usingDevicesTreeview:
                cr = TreeviewRow(self)
                iid = cr.getIidForInst(found_inst)
                cr.Get(iid)
                if iid is not None:
                    cr.tree.item(iid, text=" ?")
                    cr.tree.update_idletasks()
                else:
                    v0_print(_who, "Could not get devices treeview row.")

        for pid in found_pids:
            ext.kill_pid_running(int(pid[1]))
            # No way to kill <defunct> : https://askubuntu.com/a/201308/307523
            # So these jobs will commit suicide when homa.py ends:
            # $ ps ux | grep gatttool | grep -v grep
            # USER  7716 13.3  0.0 0 0 ? Zs 11:44 0:46 [gatttool] <defunct>
            # USER 13317  0.0  0.0 0 0 ? Zs 11:47 0:00 [gatttool] <defunct>

            # NOTE: After killing CPU percentage declines over time for <defunct>.
            # After 15 or 20 minutes the <defunct> start to disappear on their own.


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

        Before calling use ni = NetworkInfo() to create ni.mac_dicts[{}, {}...]
        app.Rediscover() uses rd = NetworkInfo() to create rd.mac_dicts
        
        :param update: If True, update ni.mac_dicts entry with type_code
        :param start: ni.mac_dicts starting index for loop
        :param end: ni.mac_dicts ending index (ends just before passed index)
        :returns: list of known device instances
    """
    _who = "homa.py discover()"
    global ni  # NetworkInformation() class instance used everywhere
    discovered = []  # List of discovered devices in arp dict format + type_code
    instances = []  # List of device instances shadowing each discovered[] device
    view_order = []  # List of MACs discovered[] for Network Devices Treeview

    v1_print("\n")
    v1_print("="*20, " Test all arp devices for their type ", "="*20)
    v1_print()

    if not start:
        start = 0
    if not end:
        end = len(ni.mac_dicts)  # Not tested as of 2024-11-10

    for i, arp in enumerate(ni.mac_dicts[start:end]):
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
            ni.mac_dicts[i] = arp  # Update arp list with type_code found in instance

    return discovered, instances, view_order


# Display subdirectory main file being available
v1_print("homa.py - trionesControl.trionesControl:", tc.__file__)
v1_print("homa.py - pygatt:", pygatt.__file__)
v1_print("homa.py - pygatt.exceptions:", pygatt.exceptions.__file__)
#v1_print("homa.py - audio:", amplitude.__file__)  # imported by vu_meter.py
#v1_print("homa.py - pulsectl:", pulsectl.__file__)  # by vu_pulse_audio.py

v1_print(sys.argv[0], "- Home Automation", " | verbose1:", p_args.verbose1,
         " | verbose2:", p_args.verbose2, " | verbose3:", p_args.verbose3,
         "\n  | fast:", p_args.fast, " | silent:", p_args.silent)

''' Global class instances accessed by various other classes '''
root = None  # Tkinter toplevel
app = None  # Application() GUI heart of HomA allowing other instances to reference
# 2025-06-19 Why does every class have "self.app" when they could use "app" instead?
cfg = sql.Config()  # Colors configuration SQL records
glo = Globals()  # Global variables instance used everywhere
GLO = glo.dictGlobals  # Default global dictionary. Live read in glo.open_file()
ble = BluetoothLedLightStrip()  # Must follow GLO dictionary and before ni instance
#vum = toolkit.VolumeMeters('homa', master_frm)  # Display Stereo LED Volume Meters
pav = None  # PulseAudio sinks. Initialize in Application() -> AudioControl()

cp = Computer()  # cp = Computer Platform instance used everywhere
ni = NetworkInfo()  # ni = global class instance used everywhere
ni.adb_reset(background=True)  # Sometimes necessary when TCL TV isn't communicating
rd = None  # rd = Rediscovery instance for app.Rediscover() & app.Discover()
sm = None  # sm = System Monitor - fan speed and CPU temperatures

SAVE_CWD = ""  # Save current working directory before changing to program directory
killer = ext.GracefulKiller()  # Class instance for app.Close() or CTRL+C

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
            ni.mac_dicts[{}, {}...{}] - all devices, optional type_code
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
        v2_print("Opening last arp dictionaries file:", fname)
        ni.mac_dicts = json.loads(f.read())

    fname = g.USER_DATA_DIR + os.sep + GLO['VIEW_ORDER_FNAME']
    build_view_order = True
    if os.path.isfile(fname):
        with open(fname, "r") as f:
            v2_print("Opening last view order file:", fname)
            ni.view_order = json.loads(f.read())
            build_view_order = False

    # Assign instances
    for arp in ni.mac_dicts:
        try:
            type_code = arp['type_code']
        except KeyError:
            continue  # This device wasn't recognized by HomA, perhaps a smart phone?

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
        elif type_code == GLO['ROUTER_M']:  # Router Modem image
            inst = Router(arp['mac'], arp['ip'], arp['name'], arp['alias'])
        else:
            v0_print(_who, "Data corruption. Unknown type_code:", type_code)
            return

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
        f.write(json.dumps(ni.mac_dicts))
    with open(g.USER_DATA_DIR + os.sep + GLO['VIEW_ORDER_FNAME'], "w") as f:
        f.write(json.dumps(ni.view_order))

    # Close SQL History Table for color configurations
    sql.close_homa_db()

    if GLO['SUDO_PASSWORD'] is not None:
        f = Fernet(cp.crypto_key)  # Encrypt sudo password when storing
        try:
            enc = f.encrypt(GLO['SUDO_PASSWORD'].encode())  # convert to bytes
            # Works first time in Python 3, but second time (after save & restart)
            # it generates attribute error below.
        except AttributeError:
            # AttributeError: 'bytes' object has no attribute 'encode'
            # v0_print(_who, "AttributeError: 'bytes' object has no attribute 'encode'")
            enc = f.encrypt(GLO['SUDO_PASSWORD'])  # already in bytes
        if PYTHON_VER == "3":
            # noinspection SpellCheckingInspection
            '''
            Fix issue with `bytes` being used in encryption under python 3:
                TypeError: b'gAAAAABnqjSvXmfPODPXGfmBcnRnas4oI22xMbKxTP-JZGA-6
                -819AmJoV7kEh59d-RnKLK2HZVGwb3YppZsvgzOZcUZDsZmAg==' 
                is not JSON serializable

            See: https://stackoverflow.com/a/40060181/6929343
            '''
            GLO['SUDO_PASSWORD'] = enc.decode('utf8').replace("'", '"')
        else:  # In Python 2 a string is a string, not bytes
            GLO['SUDO_PASSWORD'] = enc

    glo.saveFile()


def dummy_thread():
    """ Needed for showInfoMsg from root window. """
    root.update()
    root.after(30)


def main():
    """ Save current directory, change to ~/homa directory, load app GUI
        When existing restore original current directory.
    """
    global root  # named when main() called
    global app, GLO
    global ni  # NetworkInformation() class instance used everywhere
    global SAVE_CWD  # Saved current working directory to restore on exit

    ''' Save current working directory '''
    SAVE_CWD = os.getcwd()  # Convention from old code in mserve.py
    if SAVE_CWD != g.PROGRAM_DIR:
        v1_print("Changing from:", SAVE_CWD, "to g.PROGRAM_DIR:", g.PROGRAM_DIR)
        os.chdir(g.PROGRAM_DIR)

    glo.openFile()

    ''' Decrypt SUDO PASSWORD '''
    with warnings.catch_warnings():
        # Deprecation Warning:
        # /usr/lib/python2.7/dist-packages/cryptography/x509/__init__.py:32:
        #   PendingDeprecationWarning: CRLExtensionOID has been renamed to
        #                              CRLEntryExtensionOID
        #   from cryptography.x509.oid import (
        warnings.simplefilter("ignore", category=PendingDeprecationWarning)
        f = Fernet(cp.crypto_key)  # Encrypt sudo password when storing

        if glo.dictGlobals['SUDO_PASSWORD'] is not None:
            glo.dictGlobals['SUDO_PASSWORD'] = \
                f.decrypt(glo.dictGlobals['SUDO_PASSWORD'].encode())
            # v0_print(self.dictGlobals['SUDO_PASSWORD'])

    GLO = glo.dictGlobals
    GLO['APP_RESTART_TIME'] = time.time()

    ni = NetworkInfo()  # Generate Network Information for arp and hosts

    # ni.adb_reset()  # adb kill-server && adb start-server
    # 2024-10-13 - adb_reset() is breaking TCL TV discovery???
    _discovered, _instances, _view_order = open_files()
    if len(_instances) == 0:
        # Discover all devices and update ni.mac_dicts
        ni.discovered, ni.instances, ni.view_order = discover(update=True)

        v1_print()
        v1_print("discovered list of dictionaries - [1. {}, 2. {} ... 9. {}]:")
        for i, entry in enumerate(ni.discovered):
            v1_print("  ", str(i+1) + ".", entry)
        for i, entry in enumerate(ni.instances):
            v1_print("  ", str(i+1) + ".", entry)

    ''' Tkinter root window '''
    root = tk.Tk()
    root.withdraw()

    ''' Is another copy of homa running? '''
    # result = os.popen("ps aux | grep -v grep | grep python").read().splitlines()
    programs_running = ext.get_running_apps(PYTHON_VER)
    this_pid = os.getpid()  # Don't commit suicide!
    h_pid = homa_pid = vu_meter_pid = 0  # Running PIDs found later

    ''' Loop through all running programs with 'python' in name '''
    for pid, prg, parameters in programs_running:
        if prg == "h" and pid != this_pid:
            h_pid = pid  # 'm' splash screen found
        if prg == "homa.py" and pid != this_pid:
            homa_pid = pid  # 'homa.py' found
        if prg == "vu_meter.py" and parameters[1] == "homa":
            # VU meter instance from HomA and not mserve
            vu_meter_pid = pid  # command was 'vu_meter.py stereo homa'

    ''' One or more fingerprints indicating another copy running? '''
    if h_pid or homa_pid:
        title = "Another copy of HomA is running!"
        text = "Cannot start two copies of homa. Switch to the other version."
        text += "\n\nIf the other version crashed, the process(es) still running"
        text += " can be killed:\n\n"
        if h_pid:
            text += "\t'm' (" + str(h_pid) + ") - homa splash screen\n"
        if homa_pid:
            text += "\t'homa.py' (" + str(homa_pid) + \
                    ") - homa without splash screen\n"
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

        if h_pid:
            # v0_print("killing h_pid:", h_pid)
            if not ext.kill_pid_running(h_pid):
                v0_print("killing h_pid FAILED!:", h_pid)
        if homa_pid:
            # v0_print("killing homa_pid:", homa_pid)
            if not ext.kill_pid_running(homa_pid):
                v0_print("killing homa_pid FAILED!:", homa_pid)
        if vu_meter_pid:
            # v0_print("killing vu_meter_pid:", vu_meter_pid)
            if not ext.kill_pid_running(vu_meter_pid):
                v0_print("killing vu_meter_pid FAILED!:", vu_meter_pid)

    ''' Open Main Application GUI Window '''
    app = Application(root)  # Treeview of ni.discovered[{}, {}...{}]

    app.mainloop()


if __name__ == "__main__":
    main()

# End of homa.py
