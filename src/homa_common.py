#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: pippim.com
License: GNU GPLv3. (c) 2024
Source: This repository
Description: homa_common.py - Common Python Functions Module
"""

from __future__ import print_function  # Must be first import
from __future__ import with_statement  # Error handling for file opens
import warnings  # 'warnings' advises which commands aren't supported

# ==============================================================================
#
#       homa_common.py (Home Automation) - Common Python Functions Module
#
#       2024-11-24 - Creation date.
#
# ==============================================================================

#warnings.simplefilter('default')  # in future Python versions.

''' Usage:
    import homa_common as hc
    
    xPos, yPos = hc.GetMouseLocation()  # Default argument coord_only=True
    xPos, yPos, Screen, Window = hc.GetMouseLocation(coord_only=False)
    
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

SUDO_PASSWORD = None  # Parent can see as 'homa_common.SUDO_PASSWORD'


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

        :param text: The sudo password to be tested
        :returns: None if test failed else return validated password
    """

    # Test if sudo password works
    cmd1 = sp.Popen(['echo', str(text)], stdout=sp.PIPE)
    cmd2 = sp.Popen(['sudo', '-S', 'ls', '-l', '/root'],
                    stdin=cmd1.stdout, stdout=sp.PIPE)

    output = cmd2.stdout.read().decode()
    #print("output:", output)
    if output.startswith("total"):
        return text
    else:
        return None


def GetMouseLocation(coord_only=True):
    """ Get Mouse Location using xdotool
        Used by homa.py and homa-indicator.py
    """

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


# End of homa_common.py
