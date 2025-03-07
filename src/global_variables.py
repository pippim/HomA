#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: Pippim
License: GNU GPLv3
Source: This repository
Description: mserve - Music Server - Global variables shared by all modules
"""
from __future__ import print_function  # Must be first import
from __future__ import with_statement  # Error handling for file opens

# ==============================================================================
#
#       global_variables.py - Global variables shared by all mserve modules
#
#       May. 19 2023 - appdirs for universal application & storage directories
#       July 10 2023 - Begin mserve_config.py development (check dependencies)
#       Aug. 04 2023 - Add FONT, NO_ARTIST_STR and NO_ALBUM_STR constants
#       Sep. 04 2023 - Add MUSIC_FILE_TYPES list, MSERVE_VERSION = u"3.5.0"
#       Jun. 02 2024 - MSG_WIDTH_ADJUST + .02 for message.py data_w_l() function
#       Sep. 09 2024 - Define global g.TButton style.
#       Oct. 13 2024 - Make appname a parameter used by "homa". mkdir DATA_DIR
#       Nov. 02 2024 - Add PYTHON_VERSION variable. Fix PROGRAM_DIR for homa.py
#
# ==============================================================================

# 2024-09-09 Breaks splash window
#try:
#    import tkinter as tk
#    import tkinter.ttk as ttk
#    PYTHON_VER = "3"
#except ImportError:
#    import Tkinter as tk
#    import ttk  # for ttk.Style()
#    PYTHON_VER = "2"

# Get application & storage directory names
from appdirs import user_data_dir, user_config_dir

import tempfile         # Gets TMP_DIR /tmp, C:\Temp, etc.
import inspect          # To get parent's name
import os               # USER_ID = str(os.get uid())
import pwd              # USER = pwd.get pw uid(os.get uid()).pw_name
import sys              # PYTHON_VERSION = sys.version  <--  attribute not method()
import webbrowser       # Display help text on www.pippim.com

''' Code duplicated in mserve_config.py '''
import platform as plat  # Gets OS Name, Version, Release
OS_PLATFORM = plat.platform()  # 'Linux-4.14.216-0414216-generic-x86_64-with-Ubuntu-16.04-xenial'
OS_NAME = plat.system()  # 'Linux'
OS_VERSION = plat.release()  # '4.14.216-0414216-generic'
OS_RELEASE = plat.version()  # '#202101171339 SMP Sun Jan 17 13:56:04 UTC 2021'
PYTHON_VERSION = sys.version  # 2.7.12 (default, Sep 30 2024, 14:00:27)\n [GCC 5.4.0 20160609]

##import external as ext  # Check if command installed to support features
# Cannot import external because it imports toolkit which imports global_variables.py
# Circular references give error g.USER is not defined

USER = None             # User ID, Name, GUID varies by platform
USER_ID = None          # Numeric User ID in Linux
HOME = None             # In Linux = /home/USER
APPNAME = None          # Originally "mserve" Different behavior for homa.py
USER_CONFIG_DIR = None  # /home/user/.config/mserve
USER_DATA_DIR = None    # /home/user/.local/share/mserve
MSERVE_DIR = None       # /home/user/.config/mserve/ <- historically wrong suffix /
                        # Bad name. It implies where mserve programs are
PROGRAM_DIR = None      # Directory where mserve.py is stored.
TEMP_DIR = None         # /tmp/ temporary files OR: /run/user/1000/ preferred
                        # also with trailing '/' to make concatenating simpler
MUSIC_FILE_TYPES = [".aiff", ".caf", ".flac", ".mp3", ".mp4", ".m4a",
                    ".oga", ".ogg", ".PCM", ".wav", ".wma"]
MUSIC_MIN_SIZE = 100000  # Music Files must be > 100 KB. 99999 for debug to print.
DEBUG_LEVEL = 0         # Set to 1 for warning / trace messages to print

MSERVE_VERSION = u"3.5.0"  # Make .lrc file (synchronized lyrics standard)
WIN_MIN_WIDTH = 142     # Same values used by gnome-terminal to prevent window 
WIN_MIN_HEIGHT = 63     # resizing to shrink too much

# Older Global variables from mmm (multiple monitors manager), so need renaming.
BIG_FONT = 18           # Font size
LARGE_FONT = 14         # Font size
MON_FONTSIZE = 12       # Size commonly used across most modules
WIN_FONTSIZE = 11       # Default size set in image.set_font_style()
MED_FONT = 10           # Medium Font size
MON_FONT = 12           # Alias to MON_FONTSIZE (Historical names need revamping) 

FONT = (None, MON_FONTSIZE)  # Current font setting for mserve
FONT14 = (None, LARGE_FONT)  # Make UTF-8 speakers a little arger

BTN_WID = 17            # Width for buttons on main window
BTN_WID2 = 15           # Width for buttons on play window
BTN_BRD_WID = 3         # Width for button border
FRM_BRD_WID = 2         # Width for frame border
MSG_WIDTH_ADJUST = .90  # message.py data_w_l() override width (a bit too long)
# 2024-06-02 Change .88 to .90 because last character wrapping.
# TODO: Calculate PANEL_HGT (height)
PANEL_HGT = 24          # Height of Unity panel

NO_ARTIST_STR = "<No Artist>"  # Substitute null subdirectory with string
NO_ALBUM_STR = "<No Album>"  # Used in mserve.py and location.py
CFG_DECIMAL_PLACES = 0  # 0 decimal place, eg "38 MB"
CFG_DIVISOR_AMT = 1000000  # Divide by million
CFG_DIVISOR_UOM = "MB"  # Unit of Measure becomes Megabyte

HELP_URL = "https://www.pippim.com/programs/mserve.html#"  # Default, HomA will change


def init(caller=None, appname="mserve"):
    """ This should only be called once by the main module
        Child modules will inherit values. For example if they contain
        
            import global_variables as g
            
        Then reference 'g.USER' to get the User Login Name.
        or 'g.USER_ID' to get the Numerical User ID

        0   pw_name     Login name
        1   pw_passwd   Optional encrypted password
        2   pw_uid      Numerical user ID
        3   pw_gid      Numerical group ID
        4   pw_gecos    User name or comment field
        5   pw_dir      User home directory
        6   pw_shell    User command interpreter
    """
    if caller and caller != "mserve_config.py":
        print('if caller and caller != "mserve_config.py":')
        if not cfg.main(caller):
            print("mserve not fully installed. Aborting...")
            exit()
        else:
            print("mserve_config.py is calling global_variables.py !")
            pass
    if caller and caller == "mserve_config.py":
        #print('if caller and caller == "mserve_config.py":')
        pass

    global USER, USER_ID, HOME, USER_DATA_DIR, USER_CONFIG_DIR, MSERVE_DIR
    global PROGRAM_DIR, TEMP_DIR, APPNAME

    if USER is not None:
        # print('User already set:', USER, USER_ID, HOME)
        return

    USER = pwd.getpwuid(os.getuid()).pw_name
    USER_ID = str(os.getuid())
    HOME = os.path.expanduser("~")  # Works in Windows too. EG C:\Users\rick
    APPNAME = appname
    # print('User:', USER, USER_ID, HOME)
    #appname = "mserve"  # pass as parameter that can be replaced with "homa"
    app_author = "pippim"
    USER_DATA_DIR = MSERVE_DIR = user_data_dir(appname, app_author)

    if not MSERVE_DIR.endswith(os.sep):  # 2024-10-20 - Note trailing '/' !!!
        MSERVE_DIR += os.sep

    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)
        print("Created directory:", USER_DATA_DIR)
    USER_CONFIG_DIR = user_config_dir(appname, app_author)
    # print("USER_CONFIG_DIR:", USER_CONFIG_DIR)

    if not os.path.exists(USER_CONFIG_DIR):
        os.makedirs(USER_CONFIG_DIR)
        print("Created directory:", USER_CONFIG_DIR)

    # noinspection Pep8CodingStyleViolationW605
    '''
        What directory should your app use for storing user data? If running on Mac OS X, you
        should use::
        
            ~/Library/Application Support/<AppName>
        
        If on Windows (at least English Win XP) that should be::
        
            C:\\Documents and Settings\\<User>\\Application Data\\Local Settings\\<AppAuthor>\\<AppName>
        
        or possibly::
        
            C:\\Documents and Settings\\<User>\\Application Data\\<AppAuthor>\\<AppName>
        
        for `roaming profiles <http://bit.ly/9yl3b6>`_ but that is another story.
        
        On Linux (and other Unixes) the dir, according to the `XDG
        spec <http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html>`_, is::
        
            ~/.local/share/<AppName>
        
    '''

    # PROGRAM_DIR is directory where parent resides. Parent will change to this
    # current working directory so any image files opened default to that path.
    try:
        filename = inspect.stack()[1][1]  # Caller's PROGRAM_DIR
        parts = filename.split(os.sep)
        PROGRAM_DIR = os.sep.join(parts[:-1])  # Strip out basename
    except IndexError:
        PROGRAM_DIR = os.path.dirname(os.path.realpath(__file__))

    TEMP_DIR = tempfile.gettempdir()
    if not TEMP_DIR.endswith(os.sep):  # 2024-10-20 - Note trailing '/' !!!
        TEMP_DIR += os.sep
    TEMP_DIR += USER_ID + "_"  # /tmp/1000_

    # Override if directory /run/user/ exists (no disk light flashing)
    systemd = "/run/user/" + USER_ID
    if os.path.isdir(systemd):
        TEMP_DIR = systemd + os.sep

    # global style for ttt.Button: https://stackoverflow.com/a/62506279
    # 2024-09-09 Destroys splash screen somehow?
    #style = ttk.Style()
    #style.map("g.TButton",  # Used by play_button() in build_play_btn_frm()
    #          foreground=[('!active', 'Black'), ('pressed', 'White'),
    #                      ('active', 'Black')],
    #          background=[('!active', 'Grey75'), ('pressed', 'ForestGreen'),
    #                      ('active', 'LightSkyBlue')]
    #          )


# ==============================================================================
#
#       Independent (Stand Alone) Functions
#
# ==============================================================================


def web_help(id_name):
    # noinspection SpellCheckingInspection
    """
        g.HELP_URL defined in global_variables.py imported as g.  It contains:
        https://www.pippim.com/programs/mserve.html#

    :param id_name: E.G. "HelpT", "HelpB" and "HelpS" used above
    :return None: You will see an error message if there is a typo in the link:
            gvfs-open: # https://www.pippim.com/programs/mserve.html#HelpT:
            error opening location: Error when getting information for file
            '/.../# https:/www.pippim.com/programs/mserve.html#HelpT':
            No such file or directory

    """
    link = HELP_URL + id_name
    webbrowser.open_new(link)
    # see: https://docs.python.org/3/library/webbrowser.html


def main(caller=None):
    """ July 10, 2023 - was always calling .init() directly. Test with main. """
    init(caller)
    return True


if __name__ == "__main__":
    main()

# End of global_variables.py
