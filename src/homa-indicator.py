#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: pippim.com
License: GNU GPLv3. (c) 2024
Source: This repository
Description: HomA Application Indicator - Systray Python Module
"""

from __future__ import print_function  # Must be first import
from __future__ import with_statement  # Error handling for file opens
import warnings  # 'warnings' advises which commands aren't supported

# ==============================================================================
#
#       homa-indicator.py (Home Automation) - Systray application indicator
#
#       2024-11-18 - Creation date.
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

import homa_common as hc  # hc.GetSudoPassword() and hc.GetMouseLocation()

APP_ID = 'homa-indicator'  # Unique app indicator id
HOMA_TITLE = "HomA - Home Automation"
EYESOME_TITLE = "eyesome setup"

SUDO_PASSWORD = None


def Main():
    """ Main loop """
    indicator = AppIndicator3.Indicator.new(
        APP_ID, os.path.abspath('/usr/share/icons/gnome/32x32/devices/display.png'),
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

    text = os.popen("which eyesome-cfg.sh").read()
    if len(text) > 15 and "/eyesome-cfg.sh" in text:
        # Add Eyesome option only if it is installed.
        item_eyesome = Gtk.MenuItem('Eyesome')
        item_eyesome.connect('activate', Eyesome)
        menu.append(item_eyesome)

    item_quit = Gtk.MenuItem('Quit')
    item_quit.connect('activate', Gtk.main_quit)
    menu.append(item_quit)
    menu.show_all()

    return menu


def HomA(_):
    """ Call HomA - Home Automation application.
        Start HomA if it's not running.
        Requires sudo permissions to change laptop display.

        Move HomeA Window to current monitor at mouse location.
    """

    # If not already running, start up homa.py
    window = CheckRunning(HOMA_TITLE)
    # window: 0x05c0000a  0 4354 72   1200 700    N/A HomA - Home Automation
    if len(window) < 4:  # Not running yet
        #print("homa-indicator.py HomA(): Starting HomA with '-f -s &'")
        _out = os.popen("~/homa/homa.py -f -s &")
        time.sleep(1.0)

    MoveHere(HOMA_TITLE)  # Move opened window to current mouse location


def Eyesome(_):
    """ Call Eyesome - Sunlight percentage sets monitor brightness & color temperature.
        Start Eyesome if it's not running.
        Requires sudo permissions to change laptop display.

        Move Eyesome Window to current monitor at mouse location.
    """

    window = CheckRunning(EYESOME_TITLE)
    # window: 0x06400007  0 3449 667  782  882  alien eyesome setup

    if len(window) < 4:  # Not running yet
        #print("homa-indicator.py Eyesome(): Starting Eyesome with sudo powers")

        global SUDO_PASSWORD

        if SUDO_PASSWORD is None:
            SUDO_PASSWORD = hc.GetSudoPassword()
            if SUDO_PASSWORD is None:
                return "?"  # Cancel button (256) or escape or 'X' on window decoration (64512)

        cmd1 = sp.Popen(['echo', SUDO_PASSWORD], stdout=sp.PIPE)
        _out = sp.Popen(['sudo', '-S', 'eyesome-cfg.sh', '&'],
                        stdin=cmd1.stdout, stdout=sp.PIPE)

        # print("_out.pid:", _out.pid)

        time.sleep(1.0)  # Allow 1 second startup time before moving window

    MoveHere(EYESOME_TITLE)  # Move opened window to current mouse location


def CheckRunning(title):
    """ Check if program is running; homa.py or eyesome-cfg.sh, etc. """
    #print("homa-indicator.py CheckRunning(): grep title:", title)
    # wmctrl -lG | grep "$title"
    cmd1 = sp.Popen(['wmctrl', "-lG"], stdout=sp.PIPE)
    cmd2 = sp.Popen(['grep', title], stdin=cmd1.stdout, stdout=sp.PIPE)
    output = cmd2.stdout.read().decode()  # Works for HomA not Eyesome
    #print("homa-indicator.py CheckRunning(): output:", output)
    # HomA   : 0x05c0000a  0 4354 72   1200 700    N/A HomA - Home Automation
    # Eyesome: 0x06400007  0 3449 667  782  882  alien eyesome setup
    return output


def MoveHere(title):
    """ Move a running program's window below mouse cursor.
        Shift window left as necessary so it doesn't pass right edge of monitor.

        :param title: "HomA - Home Automation" / "eyesome setup"
        :returns True: if successful, else False

    """
    _who = "MoveHere():"

    # Get program window's geometry
    all_windows = sp.check_output(['wmctrl', '-lG']).splitlines()
    for window in all_windows:
        if title in window:
            break
    else:
        return False

    parts = window.split()
    if len(parts) < 6:
        return False

    wId, _wStrange, _wX, _wY, wWidth, wHeight = parts[0:6]
    #print(_who, "wId, wWidth, wHeight:", wId, wWidth, wHeight)

    xPos, yPos = hc.GetMouseLocation()  # Get current mouse location
    xPos2 = int(xPos) - int(wWidth) + 200  # Adjust x-offset using window's width

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


if __name__ == "__main__":
    """ Trap Signal to kill HomA Indicator and call Mainline """
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Main()
    
# End of homa-indicator.py
