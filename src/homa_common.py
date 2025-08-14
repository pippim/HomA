#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: pippim.com
License: GNU GPLv3. (c) 2024-2025
Source: This repository
Description: homa_common.py - Common Python Functions Module
"""

from __future__ import print_function  # Must be first import
from __future__ import with_statement  # Error handling for file opens
import warnings  # 'warnings' advises which commands aren't supported
warnings.filterwarnings("ignore", "ResourceWarning")  # PIL python 3 unclosed file

# ==============================================================================
#
#       homa_common.py (Home Automation) - Common Python Functions Module
#
#       2024-11-24 - Creation date.
#       2024-12-08 - Port GetMouseLocation() to monitor.py get_mouse_location().
#       2025-02-10 - Support Python 3 shebang in parent.
#       2025-07-17 - DeviceCommonSelf and Globals from homa.py for yt-skip.py.
#       2025-08-03 - Create spam_print() for reprinting on the same line.
#
# ==============================================================================

''' check configuration. '''
import inspect
import os
os.environ["SUDO_PROMPT"] = ""  # Remove prompt "[sudo] password for <USER>:"
import global_variables as g

try:
    filename = inspect.stack()[1][1]  # If there is a parent, it must be 'h'
    parent = os.path.basename(filename)
    #if parent != 'h':
    #    print("homa.py called by unrecognized:", parent)
    #    exit()
except IndexError:  # list index out of range
    ''' 'h' hasn't been run to get global variables or verify configuration '''
    #import mserve_config as m_cfg  # Differentiate from sql.Config as cfg

    caller = "homa.py"
    import global_variables as g
    g.init(appname="homa")
    g.HELP_URL = "https://www.pippim.com/programs/homa.html#"

#warnings.simplefilter('default')  # in future Python versions.
import monitor

''' Usage:
    import homa_common as hc
    
    xPos, yPos = GetMouseLocation()  # Default argument coord_only=True
    xPos, yPos, Screen, Window = GetMouseLocation(coord_only=False)
    
    if hc.SUDO_PASSWORD is None:
        SUDO_PASSWORD = hc.GetSudoPassword()
        if SUDO_PASSWORD is None:
            print("Sudo Password failed!")
            return None  
    # "echo SUDO_PASSWORD | sudo -S sudo_command"    

    REQUIRES:
        yad
        xdotool

'''

import os  # For simplistic calls to: os.popen("STRING")

try:
    import subprocess32 as sp  # Python 2 future version of Python 3 sp
    SUBPROCESS_VER = '32'
except ImportError:  # No module named subprocess32
    import subprocess as sp  # For advance calls to subprocess.Popen([LIST])
    SUBPROCESS_VER = 'native'

import time  # For now = time.time()
import datetime as dt  # For dt.datetime.now().strftime('%I:%M %p')
import json  # For dictionary storage in external file
import copy  # For deepcopy of lists of dictionaries
import random  # Temporary filenames
import string  # Temporary filenames
from collections import OrderedDict, namedtuple

SUDO_PASSWORD = None  # Parent can see as 'homa_common.SUDO_PASSWORD'


class DeviceCommonSelf:
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
        # pipe.stdout.close()  # Added 2025-02-09 for python3 error
        # pipe.stderr.close()

        # self.cmdOutput = text.strip()  # Python 2 uses strings
        # self.cmdError = err.strip()
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
            v3_print("\n" + who, "'" + self.cmdString + "'")
            o = self.cmdOutput if isinstance(self.cmdOutput, str) else '\n'.join(self.cmdOutput)
            v3_print("  cmdOutput: '" + o + "'")
            o = self.cmdError if isinstance(self.cmdError, str) else '\n'.join(self.cmdError)
            v3_print("  cmdError : '" + o + "'  | cmdReturncode: ",
                     self.cmdReturncode, "  | cmdDuration:", self.cmdDuration)

        if self.cmdReturncode != 0:
            if forgive is False:
                v1_print(who, "cmdReturncode:", self.cmdReturncode)
                v1_print(" ", self.cmdString)

            # 2024-12-21 `timeout` never returns error message
            if self.cmdReturncode == 124 and self.cmdCommand[0] == "timeout":
                self.cmdError = "Command timed out without replying after " + \
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

        # Configuration filename assigned during file open
        self.config_fname = None

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
            "YT_SKIP_BTN_COLOR": "",  # YouTube Ad Skip button dominant color (white)
            "YT_SKIP_BTN_POINT": [],  # YouTube Ad Skip button coordinates (triangle tip)
            "YT_SKIP_BTN_COLOR2": "",  # YouTube Ad Skip button not-dominant color
            "YT_SKIP_BTN_POINT2": [],  # YouTube Ad Skip button not-dominant coordinates
            "YT_SKIP_BTN_WAIT": 3.2,  # YouTube Ad Skip button wait to appear
            "YT_SKIP_BTN_WAIT2": 0.45,  # YouTube Ad Skip button wait to disappear
            "YT_REFRESH_MS": 16  # Milliseconds to wait between Tkinter updates
        }

    def openFile(self):
        """ Read dictConfig from CONFIG_FNAME = "config.json"
            self.dictGlobals['SUDO_PASSWORD'] is ENCRYPTED and only
                homa.py .open_files() will decrypt it in place.
        """
        _who = self.who + "openFile():"

        global GLO  # Required for pycharm warning, not for updating dictionary
        self.config_fname = g.USER_DATA_DIR + os.sep + GLO['CONFIG_FNAME']
        if not os.path.isfile(self.config_fname):
            return  # config.json doesn't exist

        with open(self.config_fname, "r") as fcb:
            v2_print("Opening configuration file:", self.config_fname)
            self.dictGlobals = json.loads(fcb.read())

        # print("GLO['LED_LIGHTS_COLOR']:", GLO['LED_LIGHTS_COLOR'])
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
            _s = self.dictGlobals['YT_SKIP_BTN_COLOR2']  # 2025-08-10
            v0_print("Found GLO['YT_SKIP_BTN_COLOR2']:", _s)
        except KeyError:
            self.dictGlobals["YT_SKIP_BTN_COLOR2"] = ""
            self.dictGlobals["YT_SKIP_BTN_POINT2"] = []

            v0_print("Create GLO['YT_SKIP_BTN_COLOR2']:",
                     self.dictGlobals['YT_SKIP_BTN_COLOR2'])
        '''

        # 2025-01-27 override REFRESH_MS for breatheColors() stress testing.
        # GLO['REFRESH_MS'] = 10  # Override 16ms to 10ms
        global GLO
        GLO = self.dictGlobals

    def saveFile(self):
        """ Save dictConfig to CONFIG_FNAME = "config.json"

            Called when exiting and when setting YT Ad Skip colors and
                coordinates. yt-skip.py will stat to see when file saved.

            MUST ENCRYPT PASSWORD FIRST so this method is only called by
                homa.py .save_files() function!!!
        """
        _who = self.who + "saveFile():"

        # Override global dictionary values for saving
        hold_log = GLO['LOG_EVENTS']
        hold_error = GLO['EVENT_ERROR_COUNT']
        GLO['LOG_EVENTS'] = True  # Don't want to store False value
        GLO['EVENT_ERROR_COUNT'] = 0  # Don't want to store last error count
        self.dictGlobals = GLO

        with open(self.config_fname, "w") as fcb:
            fcb.write(json.dumps(self.dictGlobals))

        GLO['LOG_EVENTS'] = hold_log  # Restore after saving YT colors. Not
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
             "progress bars and the Ad Skip button in YouTube.")
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
             "YouTube Ad Skip button dominant white color"),
            ("YT_SKIP_BTN_POINT", 8, RW, STR, LIST, 30, DEC, MIN, MAX, CB,
             "YouTube Ad Skip button white coordinates\n"
             "for triangle right tip close to bar"),
            ("YT_SKIP_BTN_COLOR2", 8, RW, STR, STR, 9, DEC, MIN, MAX, CB,
             "YouTube Ad Skip button background non-white color"),
            ("YT_SKIP_BTN_POINT2", 8, RW, STR, LIST, 30, DEC, MIN, MAX, CB,
             "YouTube Ad Skip button non-white coordinates\n"
             "very close to triangle right tip"),
            ("YT_SKIP_BTN_WAIT", 8, RW, FLOAT, FLOAT, 9, DEC, MIN, MAX, CB,
             "Seconds to wait before checking Ad Skip Button appears"),
            ("YT_SKIP_BTN_WAIT2", 8, RW, FLOAT, FLOAT, 9, DEC, MIN, MAX, CB,
             "Seconds to wait before checking Ad Skip Button disappears"),
            ("YT_REFRESH_MS", 8, RW, INT, INT, 3, DEC, MIN, MAX, CB,
             "Millisecond delay to reduce CPU usage (16 recommended)")
        ]

        help_id = "https://www.pippim.com/programs/homa.html#"  # same as g.HELP_URL
        help_tag = "EditPreferences"
        help_text = "Open a new window in your default web browser for\n"
        help_text += "explanations of fields in this Preferences Tab."
        listHelp = [help_id, help_tag, help_text]

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


class AudioControl(DeviceCommonSelf):
    """ AudioControl() utilizes:

            - vu_meter.py daemon to log PulseAudio left & right amplitudes
            - toolkit.py VolumeMeters() class to display real-time LED VU meters
            - pav = vu_pulse_audio.PulseAudio()  # PulseAudio Instance for sinks

        Called by Application()

    """

    def __init__(self):
        """ DeviceCommonSelf(): Variables used by all classes
        USAGE: aud = AudioControl()
               Application() self.audio = AudioControl()
        """
        DeviceCommonSelf.__init__(self, "AudioControl().")  # Define self.who
        _who = self.who + "__init()__:"

        self.requires = ['vu_meter.py', 'pyaudio.py', 'numpy.py', 'pulsectl.py']
        self.installed = []
        self.checkDependencies(self.requires, self.installed)
        v2_print(self.who, "Dependencies:", self.requires)
        v2_print(self.who, "Installed?  :", self.installed)

        self.vum = None  # self.vum = toolkit.VolumeMeters(...)
        self.pulse_working_on_start = False
        self.isWorking = False  # Callers must check before doing anything
        if not self.dependencies_installed:
            return  # Cannot initialize anything

        ''' dependency pulsectl.py is installed so check if pulseaudio running '''
        import vu_pulse_audio
        self.pav = vu_pulse_audio.PulseAudio()
        if not self.pav.pulse_is_working:
            return
        self.pulse_working_on_start = True
        self.isWorking = True  # All methods in AudioControl() should work now


import argparse  # Command line argument parser
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--fast', action='store_true')  # Fast startup
parser.add_argument('-s', '--silent', action='store_true')  # No info printing
parser.add_argument('-v', '--verbose1', action='store_true')  # Print Overview
parser.add_argument('-vv', '--verbose2', action='store_true')  # Print Functions
parser.add_argument('-vvv', '--verbose3', action='store_true')  # Print Commands
p_args = parser.parse_args()
spamming = False  # 2025-08-11 undefined when at bottom


def reset_spam():
    """ Reset spam printing to turn it off for regular print. """
    global spamming
    if spamming:
        spamming = False
        print()


def spam_print(*args, **kwargs):
    """ Spam printing same line repeatedly by removing '\n' """
    if p_args.silent:
        return
    global spamming
    if not spamming:
        print()
        spamming = True

    if args:  # Check if *args is not empty
        first_arg = args[0]  # This code from google search AI
        if isinstance(first_arg, str):  # Ensure the first argument is a string
            prepended_char = '\r'  # The character to prepend
            new_first_arg = prepended_char + first_arg
            # Create a new tuple with the modified first argument
            # and the rest of the original arguments
            modified_args = (new_first_arg,) + args[1:]
            print(*modified_args, end="", **kwargs)
            return

    print("\r", *args, end="", **kwargs)  # Cannot prepend "\r"


def v0_print(*args, **kwargs):
    """ Information printing silenced by argument -s / --silent """
    if not p_args.silent:
        reset_spam()
        print(*args, **kwargs)


def v1_print(*args, **kwargs):
    """ Debug printing for argument -v (--verbose1). Overrides -s (--silent) """
    if p_args.verbose1 or p_args.verbose2 or p_args.verbose3:
        reset_spam()
        print(*args, **kwargs)


def v2_print(*args, **kwargs):
    """ Debug printing for argument -vv (--verbose2). Overrides -s (--silent) """
    if p_args.verbose2 or p_args.verbose3:
        reset_spam()
        print(*args, **kwargs)


def v3_print(*args, **kwargs):
    """ Debug printing for argument -vvv (--verbose3). Overrides -s (--silent) """
    if p_args.verbose3:
        reset_spam()
        print(*args, **kwargs)


def getWindowID(title):
    """ Use wmctrl to get window ID in hex and convert to decimal for xdotool
        Caller checks wmctrl and xdotool is installed before calling.
    """
    _who = "homa_common.py getWindowID():"
    window_id = None
    v2_print(_who, "search for:", title)

    if not self.checkInstalled('wmctrl'):
        v0_print(_who, "`wmctrl` is not installed.")
        return
    if not self.checkInstalled('xdotool'):
        v0_print(_who, "`xdotool` is not installed.")
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
        window_id = int(parts[0], 0)  # Convert hex window ID to decimal

    v2_print(_who, "window_id:", window_id)
    if window_id is None:
        v0_print(_who, "ERROR `wmctrl` could not find Window.")
        v0_print("Search for title failed: '" + title + "'.\n")

    return window_id


def GetSudoPassword():
    """ Prompt for Sudo Password needed to run Eyesome.
        Because Eyesome uses `yad` anyway, use `yad` here rather than `zenity`.
        Used by homa.py and homa-indicator.py

    """

    global SUDO_PASSWORD
    ''' Prompt one time for sudo password and store in SUDO_PASSWORD.

        Return None if Cancel button (256) or escape or 
            'X' on window decoration (64512).

        If invalid sudo password, display error and reprompt.

        If valid sudo password, return the password string.

        :return SUDO_PASSWORD: So parent can skip 2nd call to GetSudoPassword()

    '''

    xPos, yPos = GetMouseLocation()

    while True:
        SUDO_PASSWORD = None

        command = "yad --title 'Sudo password' --form --field='Password:H'" + \
                  " --geometry=300x150+" + xPos + "+" + yPos + " --borders=10" + \
                  " 2>/dev/null"  # GtkDialog mapped without a transient parent.
        # print("command:", command)
        f = os.popen(command)
        text = f.read().strip()
        returncode = f.close()  # https://stackoverflow.com/a/70693068/6929343
        # print("text:", text, "returncode:", returncode)

        if returncode is not None:
            return None

        try:
            SUDO_PASSWORD = text.split("|")[0]
        except IndexError:
            continue  # empty string

        SUDO_PASSWORD = ValidateSudoPassword(SUDO_PASSWORD)
        # Test if sudo password works
        #cmd1 = sp.Popen(['echo', str(SUDO_PASSWORD)], stdout=sp.PIPE)
        #cmd2 = sp.Popen(['sudo', '-S', 'ls', '-l', '/root'],
        #                stdin=cmd1.stdout, stdout=sp.PIPE)

        #output = cmd2.stdout.read().decode()
        # print("output:", output)
        #if output.startswith("total"):
        #    return SUDO_PASSWORD
        if SUDO_PASSWORD is not None:
            return SUDO_PASSWORD
        else:
            # Error invalid sudo password
            SUDO_PASSWORD = None
            text = "Sudo password test failed using command:\n\n"
            text += "echo " + str(SUDO_PASSWORD) + " | sudo -S ls -l /root"
            text += "\n\nTry again."
            command = "yad --title 'Invalid password' --info --text='" + text + "'" + \
                      " --geometry=400x150+" + xPos + "+" + yPos + " --borders=10" + \
                      " 2>/dev/null"  # GtkDialog mapped without a transient parent.
            # print("command:", command)
            f = os.popen(command)
            _returncode = f.close()  # https://stackoverflow.com/a/70693068/6929343
            # print("text:", text, "returncode:", _returncode)

            if returncode is not None:
                return None  # Pressed cancel at invalid password message

            continue


def ValidateSudoPassword(text):
    """ Validate sudo password. Test using:

            echo PASSWORD | sudo -S ls -l /root


────────────────────────────────────────────────────────────────────────────────────────────
$ sudo -n true 2>/dev/null
────────────────────────────────────────────────────────────────────────────────────────────
$ echo $?
0
────────────────────────────────────────────────────────────────────────────────────────────
$ sudo cat /etc/sudoers | grep ^"Defaults" | grep timestamp_timeout
Defaults	env_reset, timestamp_timeout=120

        :param text: The sudo password to be tested
        :returns: None if test failed else return validated password
    """

    # Test if sudo password is valid
    os.environ["SUDO_PROMPT"] = ""  # Change prompt "[sudo] password for <USER>:"
    cmd1 = sp.Popen(['echo', str(text)], stdout=sp.PIPE)
    cmd2 = sp.Popen(['sudo', '-S', 'ls', '-l', '/root'],
                    stdin=cmd1.stdout, stdout=sp.PIPE)

    output = cmd2.stdout.read().decode()
    cmd2.communicate()  # 2025-02-10 Python 3 ResourceWarning: unclosed file
    cmd1.communicate()  # 2025-02-10 Python 3 ResourceWarning: unclosed file

    if output.startswith("total"):
        return text
    else:
        return None


def GetMouseLocation(coord_only=True):
    """ Get Mouse Location using xdotool
        Used by homa.py and homa-indicator.py
        2024-12-08 Port GetMouseLocation() to monitor.py get_mouse_location()
    """

    if True is True:
        # 2024-12-08 Port GetMouseLocation() to monitor.py get_mouse_location()
        return monitor.get_mouse_location(coord_only=coord_only)

    f = os.popen("xdotool getmouselocation")
    text = f.read().strip()
    _returncode = f.close()  # https://stackoverflow.com/a/70693068/6929343

    # print("text:", text, "returncode:", _returncode)
    # text: ['x:5375 y:2229 screen:0 window:56623114'] returncode: None

    def get_value(offset):
        """ Get value from key: value pair """
        try:
            # text: ['x:5375 y:2229 screen:0 window:56623114'] returncode: None
            key_value = text.split()[offset]
        except IndexError:
            return "30"

        try:
            # key_value[0]: 'x:5375' -OR- key_value[1]: 'y:2229'
            value = key_value.split(":")[1]
        except IndexError:
            value = 30
        return value

    xPos = get_value(0)
    yPos = get_value(1)

    if coord_only:
        return xPos, yPos

    Screen = get_value(2)
    Window = get_value(3)
    return xPos, yPos, Screen, Window


def CheckRunning(name):
    """ Check if program is running; homa.py or eyesome-cfg.sh, etc.
        Match passed 'name' to window decoration application name.
    """

    mon = monitor.Monitors()  # Traditional Pippim abbreviation for Monitors() instance
    #print("homa-indicator.py CheckRunning(): grep name:", name)
    # wmctrl -lG | grep "$name"
    #cmd1 = sp.Popen(['wmctrl', "-lG"], stdout=sp.PIPE)
    #cmd2 = sp.Popen(['grep', name], stdin=cmd1.stdout, stdout=sp.PIPE)
    #output = cmd2.stdout.read().decode()  # Decode stdout stream to text
    #print("homa-indicator.py CheckRunning(): output:", output)
    # HomA   : 0x05c0000a  0 4354 72   1200 700    N/A HomA - Home Automation
    # Eyesome: 0x06400007  0 3449 667  782  882  alien eyesome setup
    #_line = output.split()
    #print("_line[0]:", _line[0])  # _line[0]: 0x06000018

    #_active_window = mon.get_active_window()
    #print("mon.get_active_window():", _active_window)
    # (number=92274698L, name='homa-indicator', x=2261, y=1225, width=1734, height=902)
    #_active_monitor = mon.get_active_monitor()
    #print("mon.get_active_monitor():", _active_monitor)
    # (number=1, name='DP-1-1', x=1920, y=0, width=3840, height=2160, primary=False)
    #_mouse_monitor = mon.get_mouse_monitor()
    #print("mon.get_mouse_monitor():", _mouse_monitor)
    # (number=2, name='eDP-1-1', x=3840, y=2160, width=1920, height=1080, primary=True)

    # Caller checks for len(output) > 4
    mon.make_wn_list()
    return mon.get_wn_by_name(name)


def MoveHere(title, pos='top_right', adjust=0, new_window=True):
    """ Move a running program's window below mouse cursor. Program may have been
        started by homa-indicator or it may have already been running. When program
        was already running and this is the same monitor, simply un-minimize and lift
        window in the stacking order.

        :param title: "HomA - Home Automation" / "eyesome setup" / "Big Number Calculator"
        :param pos: Position window's 'top_left' or 'top_right' to mouse position. 
        :param adjust: adjustment value to add to position. Can be a negative integer.
        :param new_window: Always move to app indicator position + offset
        :returns True: if successful, else False

    """
    _who = "MoveHere():"

    # Get program window's geometry
    all_windows = sp.check_output(['wmctrl', '-lG']).splitlines()
    for window in all_windows:
        #print("type(title):", type(title))
        #print("type(window):", type(window))
        # Python 3 window is type bytes
        window = str(window)
        if title in window:
            break
    else:
        return False

    parts = window.split()
    if len(parts) < 6:
        return False

    #print("parts:", parts)  # Python 3:
    # parts: ["b'0x05600018", '0', '4144', '126', '1200', '740',
    # '       N/A', 'HomA', '-', 'Home', "Automation'"]
    if "b'" in parts[0]:
        parts[0] = parts[0][2:]
    #print("parts:", parts)  # Python 3:

    wId, _wStrange, _wX, _wY, wWidth, wHeight = parts[0:6]

    xPos, yPos = GetMouseLocation()  # Get current mouse location
    # Adjust x-offset using window's width
    if pos == 'top_right':
        xPos2 = int(xPos) - int(wWidth) + adjust
    else:
        xPos2 = int(xPos) + adjust

    if not new_window:
        # Use previously saved window position if on same monitor
        pass

    # Move program window to mouse position
    # wmctrl -ir $window -e 1,$x2Pos,$yPos,$width,$height
    command = 'wmctrl -ir ' + wId + ' -e 1,'
    command += str(xPos2) + ',' + yPos + ',' + wWidth + ',' + wHeight
    f = os.popen(command)
    text = f.read().strip()
    returncode = f.close()  # https://stackoverflow.com/a/70693068/6929343
    if text:
        print(_who, "text:", text)
        return False
    if returncode:
        print(_who, "returncode:", returncode)
        return False

    # always un-minimize just in case
    f = os.popen('wmctrl -ia ' + wId)
    result = f.read().strip()
    returncode = f.close()  # https://stackoverflow.com/a/70693068/6929343
    if result:
        print(_who, "result:", result)
        return False
    if returncode:
        print(_who, "returncode:", returncode)
        return False

    return True


def display_edid():
    """ Display monitor edid information. Requires sudo powers. """

    # noinspection SpellCheckingInspection
    """
    ────────────────────────────────────────────────────────────────────────────────────────────
    $ get-edid -h
    get-edid, from read-edid 3.0.2. Licensed under the GPL.
    Current version by Matthew Kern <pyrophobicman@gmail.com>
    Previous work by John Fremlin <vii@users.sourceforge.net>
    and others (See AUTHORS).
    
    Usage:
     -b BUS, --bus BUS	    Only scan the i2c bus BUS.
     -c, --classiconly	    Do not check the i2c bus for an EDID
     -h, --help		        Display this help
     -i, --i2conly		    Do not check for an EDID over VBE
     -m NUM, --monitor NUM	For VBE only - some lame attempt at selecting monitors.
     -q, --quiet		    Do not output anything over stderr (messages, essentially)
    
    For help, go to <http://polypux.org/projects/read-edid/> or
    email <pyrophobicman@gmail.com>.

    ────────────────────────────────────────────────────────────────────────────────────────────
    $ sudo get-edid  | parse-edid 
              
    This is read-edid version 3.0.2. Prepare for some fun.
    Attempting to use i2c interface
    No EDID on bus 0
    No EDID on bus 1
    No EDID on bus 2
    No EDID on bus 5
    No EDID on bus 6
    3 potential busses found: 3 4 7
    Will scan through until the first EDID is found.
    Pass a bus number as an option to this program to go only for that one.
    256-byte EDID successfully retrieved from i2c bus 3
    Looks like i2c was successful. Have a good day.
    Checksum Correct
    
    Section "Monitor"
        Identifier ""
        ModelName ""
        VendorName "LGD"
        # Monitor Manufactured week 0 of 2014
        # EDID version 1.4
        # Digital Display
        DisplaySize 380 210
        Gamma 2.20
        Option "DPMS" "false"
        Modeline 	"Mode 0" 138.70 1920 1968 2000 2080 1080 1083 1088 1111 +hsync -vsync 
        Modeline 	"Mode 1" 110.96 1920 1968 2000 2080 1080 1083 1088 1111 +hsync -vsync 
    EndSection
    
    ────────────────────────────────────────────────────────────────────────────────────────────
    $ sudo get-edid --bus 3 --quiet | parse-edid
    3
    Checksum Correct
    
    Section "Monitor"
        Identifier ""
        ModelName ""
        VendorName "LGD"
        # Monitor Manufactured week 0 of 2014
        # EDID version 1.4
        # Digital Display
        DisplaySize 380 210
        Gamma 2.20
        Option "DPMS" "false"
        Modeline 	"Mode 0" 138.70 1920 1968 2000 2080 1080 1083 1088 1111 +hsync -vsync 
        Modeline 	"Mode 1" 110.96 1920 1968 2000 2080 1080 1083 1088 1111 +hsync -vsync 
    EndSection

    ────────────────────────────────────────────────────────────────────────────────────────────
    $ sudo get-edid --bus 4 --quiet | parse-edid
    4
    Checksum Correct
    
    Section "Monitor"
        Identifier "Beyond TV"
        ModelName "Beyond TV"
        VendorName "XXX"
        # Monitor Manufactured week 20 of 2019
        # EDID version 1.3
        # Digital Display
        DisplaySize 1210 680
        Gamma 2.20
        Option "DPMS" "false"
        Horizsync 30-80
        VertRefresh 50-75
        # Maximum pixel clock is 600MHz
        #Not giving standard mode: 1280x960, 60Hz
        #Not giving standard mode: 1600x1200, 60Hz
        #Not giving standard mode: 1280x1024, 60Hz
        #Not giving standard mode: 1280x720, 60Hz
        #Not giving standard mode: 1600x900, 60Hz
    
        #Extension block found. Parsing...
    #WARNING: I may have missed a mode (CEA mode 102)
    #DOUBLE WARNING: It's your first mode, too, so this may actually be important.
    #WARNING: I may have missed a mode (CEA mode 101)
    #DOUBLE WARNING: It's your first mode, too, so this may actually be important.
    #WARNING: I may have missed a mode (CEA mode 100)
    #DOUBLE WARNING: It's your first mode, too, so this may actually be important.
    #WARNING: I may have missed a mode (CEA mode 98)
    #DOUBLE WARNING: It's your first mode, too, so this may actually be important.
    #WARNING: I may have missed a mode (CEA mode 97)
    #DOUBLE WARNING: It's your first mode, too, so this may actually be important.
    #WARNING: I may have missed a mode (CEA mode 95)
    #DOUBLE WARNING: It's your first mode, too, so this may actually be important.
    #WARNING: I may have missed a mode (CEA mode 93)
    #DOUBLE WARNING: It's your first mode, too, so this may actually be important.
        Modeline 	"Mode 13" 148.50 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync 
        Modeline 	"Mode 0" 594.00 3840 4016 4104 4400 2160 2168 2178 2250 +hsync +vsync 
        Modeline 	"Mode 1" 248.88 2560 2608 2640 2720 1440 1443 1448 1525 +hsync +vsync 
        Modeline 	"Mode 2" 148.500 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync
        Modeline 	"Mode 3" 148.500 1920 2448 2492 2640 1080 1084 1089 1125 +hsync +vsync
        Modeline 	"Mode 4" 74.250 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync
        Modeline 	"Mode 5" 74.250 1920 2558 2602 2750 1080 1084 1089 1125 +hsync +vsync
        Modeline 	"Mode 6" 74.250 1920 2008 2052 2200 1080 1082 1087 1125 +hsync +vsync interlace
        Modeline 	"Mode 7" 74.250 1920 2448 2492 2640 1080 1082 1089 1125 +hsync +vsync interlace
        Modeline 	"Mode 8" 74.250 1280 1390 1420 1650 720 725 730 750 +hsync +vsync
        Modeline 	"Mode 9" 74.250 1280 1720 1760 1980 720 725 730 750 +hsync +vsync
        Modeline 	"Mode 10" 27.027 720 736 798 858 480 489 495 525 -hsync -vsync
        Modeline 	"Mode 11" 27.027 720 736 798 858 480 489 495 525 -hsync -vsync
        Modeline 	"Mode 12" 27.027 1440 1478 1602 1716 480 484 487 525 -hsync -vsync interlace
        Modeline 	"Mode 14" 74.25 1280 1390 1430 1650 720 725 730 750 +hsync +vsync 
        Option "PreferredMode" "Mode 13"
    EndSection

    ────────────────────────────────────────────────────────────────────────────────────────────
    $ sudo get-edid --bus 7 --quiet | parse-edid
    7
    Checksum Correct
    
    Section "Monitor"
        Identifier "SONY TV  *00"
        ModelName "SONY TV  *00"
        VendorName "SNY"
        # Monitor Manufactured week 1 of 2015
        # EDID version 1.3
        # Digital Display
        DisplaySize 1110 620
        Gamma 2.20
        Option "DPMS" "false"
        Horizsync 14-70
        VertRefresh 48-62
        # Maximum pixel clock is 150MHz
        #Not giving standard mode: 1280x1024, 60Hz
        #Not giving standard mode: 1600x900, 60Hz
        #Not giving standard mode: 1152x864, 75Hz
        #Not giving standard mode: 1680x1050, 60Hz
    
        #Extension block found. Parsing...
    #WARNING: I may have missed a mode (CEA mode 60)
    #WARNING: I may have missed a mode (CEA mode 62)
        Modeline 	"Mode 2" 148.500 1920 2448 2492 2640 1080 1084 1089 1125 +hsync +vsync
        Modeline 	"Mode 0" 148.50 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync 
        Modeline 	"Mode 1" 74.25 1280 1390 1430 1650 720 725 730 750 +hsync +vsync 
        Modeline 	"Mode 3" 148.500 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync
        Modeline 	"Mode 4" 74.250 1920 2448 2492 2640 1080 1082 1089 1125 +hsync +vsync interlace
        Modeline 	"Mode 5" 74.250 1920 2008 2052 2200 1080 1082 1087 1125 +hsync +vsync interlace
        Modeline 	"Mode 6" 74.250 1280 1720 1760 1980 720 725 730 750 +hsync +vsync
        Modeline 	"Mode 7" 74.250 1280 1390 1420 1650 720 725 730 750 +hsync +vsync
        Modeline 	"Mode 8" 74.250 1920 2558 2602 2750 1080 1084 1089 1125 +hsync +vsync
        Modeline 	"Mode 9" 74.250 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync
        Modeline 	"Mode 10" 27.000 720 732 796 864 576 581 586 625 -hsync -vsync
        Modeline 	"Mode 11" 27.000 1440 1464 1590 1728 576 578 581 625 -hsync -vsync interlace
        Modeline 	"Mode 12" 27.027 720 736 798 858 480 489 495 525 -hsync -vsync
        Modeline 	"Mode 13" 27.027 1440 1478 1602 1716 480 484 487 525 -hsync -vsync interlace
        Modeline 	"Mode 14" 27.000 720 732 796 864 576 581 586 625 -hsync -vsync
        Modeline 	"Mode 15" 27.000 1440 1464 1590 1728 576 578 581 625 -hsync -vsync interlace
        Modeline 	"Mode 16" 27.027 720 736 798 858 480 489 495 525 -hsync -vsync
        Modeline 	"Mode 17" 27.027 1440 1478 1602 1716 480 484 487 525 -hsync -vsync interlace
        Modeline 	"Mode 18" 25.200 640 656 752 800 480 490 492 525 -hsync -vsync
        Modeline 	"Mode 19" 148.50 1920 2448 2492 2640 1080 1084 1089 1125 +hsync +vsync 
        Modeline 	"Mode 20" 74.25 1280 1720 1760 1980 720 725 730 750 +hsync +vsync 
        Modeline 	"Mode 21" 74.25 1920 2448 2492 2640 540 542 547 562 +hsync +vsync interlace
        Option "PreferredMode" "Mode 2"
    EndSection

    ────────────────────────────────────────────────────────────────────────────────────────────
    
    $ xrandr -v
    xrandr program version       1.5.1
    Server reports RandR version 1.5
    
    ────────────────────────────────────────────────────────────────────────────────────────────

    $ xrandr --help
    usage: xrandr [options]
      where options are:
      --display <display> or -d <display>
      --help
      -o <normal,inverted,left,right,0,1,2,3>
                or --orientation <normal,inverted,left,right,0,1,2,3>
      -q        or --query
      -s <size>/<width>x<height> or --size <size>/<width>x<height>
      -r <rate> or --rate <rate> or --refresh <rate>
      -v        or --version
      -x        (reflect in x)
      -y        (reflect in y)
      --screen <screen>
      --verbose
      --current
      --dryrun
      --nograb
      --prop or --properties
      --fb <width>x<height>
      --fbmm <width>x<height>
      --dpi <dpi>/<output>
      --output <output>
          --auto
          --mode <mode>
          --preferred
          --pos <x>x<y>
          --rate <rate> or --refresh <rate>
          --reflect normal,x,y,xy
          --rotate normal,inverted,left,right
          --left-of <output>
          --right-of <output>
          --above <output>
          --below <output>
          --same-as <output>
          --set <property> <value>
          --scale <x>[x<y>]
          --scale-from <w>x<h>
          --transform <a>,<b>,<c>,<d>,<e>,<f>,<g>,<h>,<i>
          --filter nearest,bilinear
          --off
          --crtc <crtc>
          --panning <w>x<h>[+<x>+<y>[/<track:w>x<h>+<x>+<y>[/<border:l>/<t>/<r>/<b>]]]
          --gamma <r>[:<g>:<b>]
          --brightness <value>
          --primary
      --noprimary
      --newmode <name> <clock MHz>
                <hdisp> <hsync-start> <hsync-end> <htotal>
                <vdisp> <vsync-start> <vsync-end> <vtotal>
                [flags...]
                Valid flags: +HSync -HSync +VSync -VSync
                             +CSync -CSync CSync Interlace DoubleScan
      --rmmode <name>
      --addmode <output> <name>
      --delmode <output> <name>
      --listproviders
      --setprovideroutputsource <prov-xid> <source-xid>
      --setprovideroffloadsink <prov-xid> <sink-xid>
      --listmonitors
      --listactivemonitors
      --setmonitor <name> {auto|<w>/<mmw>x<h>/<mmh>+<x>+<y>} {none|<output>,<output>,...}
      --delmonitor <name>
    
    ────────────────────────────────────────────────────────────────────────────────────────────

    $ xrandr --listactivemonitors

    Monitors: 3
     0: +*eDP-1-1 1920/382x1080/215+3840+2160  eDP-1-1
     1: +HDMI-0 1920/1107x1080/623+0+0  HDMI-0
     2: +DP-1-1 3840/1209x2160/680+1920+0  DP-1-1
    
    ────────────────────────────────────────────────────────────────────────────────────────────

    $ xrandr --listproviders

    Providers: number : 2
    Provider 0: id: 0x25a cap: 0x1, Source Output crtcs: 4 outputs: 1 associated providers: 1 name:NVIDIA-0
    Provider 1: id: 0x47 cap: 0x2, Sink Output crtcs: 3 outputs: 5 associated providers: 1 name:modesetting

    ────────────────────────────────────────────────────────────────────────────────────────────

    $ xrandr --verbose

    Screen 0: minimum 8 x 8, current 5760 x 3240, maximum 16384 x 16384
    HDMI-0 connected 1920x1080+0+0 (0xaf) normal (normal left inverted right x axis y axis) 1107mm x 623mm
        Identifier: 0x25f
        Timestamp:  199901742
        Subpixel:   unknown
        Gamma:      1.0:1.0:1.0
        Brightness: 1.0
        Clones:    
        CRTC:       1
        CRTCs:      1 2 3 4
        Transform:  1.000000 0.000000 0.000000
                    0.000000 1.000000 0.000000
                    0.000000 0.000000 1.000000
                   filter: 
        CscMatrix: 65536 0 0 0 0 65536 0 0 0 0 65536 0 
        EDID: 
            00ffffffffffff004dd9039d01010101
            (... SNIP ...)
            4200009e000000000000000000000084
        BorderDimensions: 4 
            supported: 4
        Border: 0 0 0 0 
            range: (0, 65535)
        SignalFormat: TMDS 
            supported: TMDS
        ConnectorType: HDMI 
        ConnectorNumber: 0 
        _ConnectorLocation: 0 
      1920x1080 (0xaf) 148.500MHz +HSync +VSync *current +preferred
            h: width  1920 start 2008 end 2052 total 2200 skew    0 clock  67.50KHz
            v: height 1080 start 1084 end 1089 total 1125           clock  60.00Hz
      (... SNIP ...)
      640x480 (0x26a) 25.170MHz -HSync -VSync
            h: width   640 start  656 end  752 total  800 skew    0 clock  31.46KHz
            v: height  480 start  490 end  492 total  525           clock  59.93Hz

    eDP-1-1 connected primary 1920x1080+3840+2160 (0x49) normal (normal left inverted right x axis y axis) 382mm x 215mm
        Identifier: 0x42
        Timestamp:  199901742
        Subpixel:   unknown
        Gamma:      1.0:1.0:1.0
        Brightness: 1.0
        Clones:    
        CRTC:       0
        CRTCs:      0 5 6
        Transform:  1.000000 0.000000 0.000000
                    0.000000 1.000000 0.000000
                    0.000000 0.000000 1.000000
                   filter: 
        EDID: 
            00ffffffffffff0030e4590400000000
            (... SNIP ...)
            000041319e001000000a010a20200097
        PRIME Synchronization: 0 
            supported: 0, 1
        scaling mode: Full aspect 
            supported: Full, Center, Full aspect
        Broadcast RGB: Automatic 
            supported: Automatic, Full, Limited 16:235
        audio: auto 
            supported: force-dvi, off, auto, on
        link-status: Good 
            supported: Good, Bad
      1920x1080 (0x48) 138.700MHz +HSync -VSync +preferred
            h: width  1920 start 1968 end 2000 total 2080 skew    0 clock  66.68KHz
            v: height 1080 start 1083 end 1088 total 1111           clock  60.02Hz
      1920x1080 (0x49) 356.375MHz -HSync +VSync DoubleScan *current
            h: width  1920 start 2080 end 2288 total 2656 skew    0 clock 134.18KHz
            v: height 1080 start 1081 end 1084 total 1118           clock  60.01Hz
      (... SNIP ...)
      320x180 (0xa4)  8.875MHz +HSync -VSync DoubleScan
            h: width   320 start  344 end  360 total  400 skew    0 clock  22.19KHz
            v: height  180 start  181 end  184 total  187           clock  59.32Hz

    DP-1-1 connected 3840x2160+1920+0 (0x2a5) normal (normal left inverted right x axis y axis) 1209mm x 680mm
        Identifier: 0x43
        Timestamp:  199901742
        Subpixel:   unknown
        Gamma:      1.0:1.0:1.0
        Brightness: 1.0
        Clones:     HDMI-1-1
        CRTC:       5
        CRTCs:      0 5 6
        Transform:  1.000000 0.000000 0.000000
                    0.000000 1.000000 0.000000
                    0.000000 0.000000 1.000000
                   filter: 
        EDID: 
            00ffffffffffff006318512800000100
            (... SNIP ...)
            000000000000000000000000000000ac
        PRIME Synchronization: 0 
            supported: 0, 1
        Broadcast RGB: Automatic 
            supported: Automatic, Full, Limited 16:235
        audio: auto 
            supported: force-dvi, off, auto, on
        link-status: Good 
            supported: Good, Bad
      3840x2160 (0x2a5) 594.000MHz +HSync +VSync *current +preferred
            h: width  3840 start 4016 end 4104 total 4400 skew    0 clock 135.00KHz
            v: height 2160 start 2168 end 2178 total 2250           clock  60.00Hz
      (... SNIP ...)
      640x480 (0x89) 25.175MHz -HSync -VSync
            h: width   640 start  656 end  752 total  800 skew    0 clock  31.47KHz
            v: height  480 start  490 end  492 total  525           clock  59.94Hz

    HDMI-1-1 disconnected (normal left inverted right x axis y axis)
        Identifier: 0x44
            (... SNIP ...)

    DP-1-2 disconnected (normal left inverted right x axis y axis)
        Identifier: 0x45
            (... SNIP ...)

    HDMI-1-2 disconnected (normal left inverted right x axis y axis)
        Identifier: 0x46
            (... SNIP ...)

    """
    pass


glo = Globals()  # Global variables instance used everywhere
GLO = glo.dictGlobals  # Default global dictionary. Live read in glo.openFile()
#spamming = False  # Used by spam_print for new line control


# End of homa_common.py
