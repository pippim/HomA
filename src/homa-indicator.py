#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Author: pippim.com
License: GNU GPLv3. (c) 2024-2025
Source: This repository
Description: HomA Application Indicator - Systray Python Module
"""

from __future__ import print_function  # Must be first import
from __future__ import with_statement  # Error handling for file opens
import warnings  # 'warnings' advises which commands aren't supported
warnings.filterwarnings("ignore", "ResourceWarning")  # PIL python 3 unclosed file

# ==============================================================================
#
#       homa-indicator.py (Home Automation) - Systray application indicator
#
#       2024-11-18 - Creation date.
#       2024-12-08 - Use monitor.Monitors() for monitor aware window positions.
#       2025-02-10 - Support Python 3 shebang.
#       2025-06-01 - Change #!/usr/bin/env python to #!/usr/bin/python for top.
#       2025-06-13 - CheckRunning() convert from wmctrl to Wnck methods.
#       2025-07-19 - Add "YT Ad Skip" (yt-skip.py) to menu.
#       2025-11-09 - Fix check for no window returned from CheckRunning().
#       2026-02-25 - Use homa configuration sudo password when available.
#
# ==============================================================================

#warnings.simplefilter('default')  # in future Python versions.
# ./homa-indicator.py:62: PyGTKDeprecationWarning: Using positional arguments
# with the GObject constructor has been deprecated. Please specify keyword(s)
# for "label" or use a class specific constructor.
# See: https://wiki.gnome.org/PyGObject/InitializerDeprecations

'''
This code is an example for a tutorial on Ubuntu Unity/Gnome AppIndicators:
http://candidtim.github.io/appindicator/2014/09/13/ubuntu-appindicator-step-by-step.html
https://gist.github.com/candidtim/5663cc76aa329b2ddfb5
'''

import os
import signal
import time
from cryptography.fernet import Fernet  # Decrypt homa cfg sudo password using MAC

try:
    import subprocess32 as sp
    SUBPROCESS_VER = '32'
except ImportError:  # No module named subprocess32
    import subprocess as sp
    SUBPROCESS_VER = 'native'

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk
from gi.repository import AppIndicator3

try:
    reload(sys)  # June 25, 2023 - Without these commands, os.popen() fails on OS
    sys.setdefaultencoding('utf8')  # filenames that contain unicode characters
except NameError:  # name 'reload' is not defined
    pass  # Python 3 already in unicode by default

import global_variables as g
g.init(appname="homa")
import homa_common as hc  # hc.Computer() class & hc.GetMouseLocation() function
from homa_common import DeviceCommonSelf, Globals  # classes to open config file

APP_ID = "homa-indicator"  # Unique application name used for app indicator id
APP_ICON = "/usr/share/icons/gnome/32x32/devices/display.png"
SAVE_CWD = ""  # Saved current working directory. Will change to program directory
HOMA_TITLE = "HomA - Home Automation"  # Window title must match program's title bar
SKIP_TITLE = "YouTube Ad Mute and Skip"  # Window title must match program's title bar
EYESOME_TITLE = "eyesome setup"  # Move by window title under application indicator
SUDO_PASSWORD = None  # Sudo required for running eyesome
SYSTRAY_ADJUST = -40  # New Window Position Adjustment

glo = Globals()  # Global variables instance used everywhere
GLO = glo.dictGlobals  # Default global dictionary. Live read in glo.open_file()
cp = hc.Computer()  # cp = Computer Platform instance required for crypto key


def Main():
    """ Main loop """

    global SAVE_CWD  # Saved current working directory to restore on exit
    global GLO  # HomA configuration file's saved global variables dictionary

    ''' Save current working directory '''
    SAVE_CWD = os.getcwd()  # Bad habit from old code in mserve.py
    if SAVE_CWD != g.PROGRAM_DIR:
        #print("Changing from:", SAVE_CWD, "to g.PROGRAM_DIR:", g.PROGRAM_DIR)
        os.chdir(g.PROGRAM_DIR)

    if glo.openFile():

        ''' Decrypt SUDO PASSWORD using ethernet or wifi MAC crypto key '''
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
                pass
        GLO = glo.dictGlobals
        global SYSTRAY_ADJUST
        SYSTRAY_ADJUST = GLO['SYSTRAY_ADJUST']

    # https://lazka.github.io/pgi-docs/AyatanaAppIndicator3-0.1/classes/Indicator.html
    indicator = AppIndicator3.Indicator.new(
        APP_ID, os.path.abspath(APP_ICON),
        AppIndicator3.IndicatorCategory.SYSTEM_SERVICES)
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    indicator.set_menu(BuildMenu())
    Gtk.main()


def BuildMenu():
    """ Menu """

    menu = Gtk.Menu()
    item_homa = Gtk.MenuItem('HomA')
    item_homa.connect('activate', HomA)
    menu.append(item_homa)
    item_skip = Gtk.MenuItem('YT Ad Skip')
    item_skip.connect('activate', Skip)
    menu.append(item_skip)

    text = os.popen("which eyesome-cfg.sh").read()
    if len(text) > 15 and "/eyesome-cfg.sh" in text:
        # Add Eyesome option only if it is installed.
        item_eyesome = Gtk.MenuItem('Eyesome')
        item_eyesome.connect('activate', Eyesome)
        menu.append(item_eyesome)

    item_quit = Gtk.MenuItem('Quit')
    item_quit.connect('activate', Quit)
    menu.append(item_quit)
    menu.show_all()

    return menu


def HomA(_):
    """ Call HomA - Home Automation application.
        Start HomA if it's not running.
        Requires sudo permissions to change laptop display.

        Move HomeA Window to current monitor at mouse location.
    """

    new_window = False if hc.CheckRunning(HOMA_TITLE) else True
    if new_window:
        _out = os.popen("./homa.py -f -s &")
        time.sleep(1.0)

    # Move opened window to current mouse location
    hc.MoveHere(HOMA_TITLE, new_window=new_window, adjust=SYSTRAY_ADJUST)


def Skip(_):
    """ Call yt-skip.py ("YouTube Ad Mute and Skip")
        Start yt-skip if it's not running.
        If running, move window to current monitor at mouse location.
    """

    new_window = False if hc.CheckRunning(SKIP_TITLE) else True
    if new_window:
        _out = os.popen("./yt-skip.py -f -s &")
        time.sleep(1.0)

    # Move opened window to current mouse location
    hc.MoveHere(SKIP_TITLE, new_window=new_window, adjust=SYSTRAY_ADJUST)


def Eyesome(_):
    """ Call Eyesome - Sunlight percentage sets monitor brightness & color temperature.
        Start Eyesome if it's not running.
        Requires sudo permissions to change laptop display.

        Move Eyesome Window to current monitor at mouse location.


        # Has HomA saved a newer version of the configuration file?
        self.this_stat = os.stat(glo.config_fname)
        if self.this_stat.st_mtime != self.last_stat.st_mtime:
            self.insertYtSB("Read newer preferences: " +
                            self.formatTime(self.this_stat.st_mtime))
            if not glo.openFile():
                return  # TODO: Give an error message
            global GLO
            GLO = glo.dictGlobals
            GLO['APP_RESTART_TIME'] = time.time()

            self.resetSpam(1)
            v1_print(self.printTime(1), _who, "New configuration time:",
                     self.formatTime(self.this_stat.st_mtime))
            self.last_stat = self.this_stat

    """

    window = hc.CheckRunning(EYESOME_TITLE)
    # window: 0x06400007  0 3449 667  782  882  alien eyesome setup
    if not bool(window):
        window = [" "]  # Create dummy list for no window

    if len(window) < 4:  # Not running yet
        #print("homa-indicator.py Eyesome(): Starting Eyesome with sudo powers")

        global SUDO_PASSWORD

        if GLO['SUDO_PASSWORD'] is not None:
            SUDO_PASSWORD = GLO['SUDO_PASSWORD']
        if SUDO_PASSWORD is None:
            SUDO_PASSWORD = hc.GetSudoPassword()  # Get valid sudo password
            if SUDO_PASSWORD is None:
                # Cancel button (256) or escape or 'X' on window decoration (64512)
                return

        cmd1 = sp.Popen(['echo', SUDO_PASSWORD], stdout=sp.PIPE)
        _out = sp.Popen(['sudo', '-S', 'eyesome-cfg.sh', '&'],
                        stdin=cmd1.stdout, stdout=sp.PIPE)

        # print("_out.pid:", _out.pid)

        time.sleep(1.0)  # Allow 1 second startup time before moving window
        new_window = True
    else:
        new_window = False

    # Move opened window to current mouse location under the app indicator
    hc.MoveHere(EYESOME_TITLE, new_window=new_window, adjust=SYSTRAY_ADJUST)


def Quit(_):
    """ Quit homa-indicator.py """

    ''' reset to original SAVE_CWD (current working directory) '''
    if SAVE_CWD != g.PROGRAM_DIR:
        #print("Changing from g.PROGRAM_DIR:", g.PROGRAM_DIR,
        #      "to SAVE_CWD:", SAVE_CWD)
        os.chdir(SAVE_CWD)

    Gtk.main_quit()


if __name__ == "__main__":
    """ Trap Signal to kill HomA Indicator and call Mainline """
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Main()
    
# End of homa-indicator.py
