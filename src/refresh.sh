#!/bin/bash

# refresh.sh - Update ~/HomA/src and then publish to GitHub

# Pass commit message as first parameter (referenced as "$1")

# First time usage:
#       ~/HomA$ chmod a+x refresh.sh

# Requires two directories ~/HomA (development directory) and
# ~/HomA/src (the published clone)

# Make sure credentials are stored https://stackoverflow.com/a/17979600/6929343

#       $ git config credential.helper store
#       $ git push https://github.com/pippim/HomA.git
#       Username: <type your username>
#       Password: <type your password>

# ll ~/.git*
# -rw-rw-r-- 1 USER USER  106 Dec 28  2021 /home/USER/.gitconfig
# -rw------- 1 USER USER   67 Nov 29 15:45 /home/USER/.git-credentials
# -rw-rw-r-- 1 USER USER   23 Nov 16  2021 /home/USER/.gitignore
# -rw-rw-r-- 1 USER USER   12 Feb 19  2022 /home/USER/.gitkeep

# /home/USER/.git-credential-cache:
# total 16
# dr wx------  2 USER USER  4096 Nov 29 16:00 ./
# dr wxr-xr-x 80 USER USER 12288 Dec  1 07:22 ../

if [ ! -d ~/HomA ] ; then 
    echo Requires directories ~/HomA and ~/HomA/src
    exit 101
fi

if [ ! -d ~/HomA/src ] ; then 
    echo Requires directories ~/HomA and ~/HomA/src
    exit 102
fi

if [ -z "$1" ] ; then
    now=$(date)
    commit_message="Refresh repository on: $now"
else
    commit_message="$1"
fi

echo "=== COMMIT MESSAGE set to: '$commit_message'"

cd ~/HomA/src || exit 1

echo
echo "=== PULLING: $PWD changes from github.com"

git pull
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "git pull FAILED with code: $retVal"
    exit $retVal
fi

echo
echo "=== UPDATING: $PWD"

cp -r ~/HomA/Alarm_01.wav .
cp -L ~/HomA/audio .  # Subdirectory with files and subdirectories
cp -r ~/HomA/bias.jpg .
cp -r ~/HomA/breathing.jpeg .
cp -L ~/HomA/calc.py .  # symlink
cp -r ~/HomA/close.png .
cp -r ~/HomA/computer.jpg .
cp -r ~/HomA/down.png .
cp -L ~/HomA/external.py .  # symlink
cp -r ~/HomA/flame.png .
cp -L ~/HomA/global_variables.py .  # symlink
cp -r ~/HomA/mag_glass.png .
cp -r ~/HomA/homa_common.py .
cp -r ~/HomA/homa-indicator.py .
cp -r ~/HomA/homa.py .
cp -r ~/HomA/hs100.sh .
cp -L ~/HomA/image.py .  # symlink
cp -r ~/HomA/laptop_b.jpg .
cp -r ~/HomA/laptop_d.jpg .
cp -r ~/HomA/led_lights.jpg .
cp -r ~/HomA/lightning_bolt.png .
cp -L ~/HomA/message.py .  # symlink
cp -L ~/HomA/monitor.py .  # symlink
cp -r ~/HomA/nighttime.png .
cp -r ~/HomA/picture_off.png .
cp -r ~/HomA/picture_on.png .
cp -L ~/HomA/pimtube.py .  # Youtube video controller / ad skipper
cp -L ~/HomA/pulsectl .  # Subdirectory with files and subdirectories
cp -r ~/HomA/pygatt/ .  # Subdirectory with files and subdirectories
cp -r ~/HomA/refresh.sh .  # Copy of this bash script might be helpful
cp -r ~/HomA/reset.jpeg .
cp -r ~/HomA/set_color.jpeg .
cp -r ~/HomA/sony.jpg .
cp -L ~/HomA/sql.py .  # symlink
cp -r ~/HomA/tcl.jpg .
cp -L ~/HomA/timefmt.py .  # symlink
cp -L ~/HomA/toolkit.py .  # symlink
cp -r ~/HomA/trionesControl/ .  # Subdirectory with files and subdirectories
cp -r ~/HomA/ttkwidgets/ .  # Subdirectory with files and subdirectories
cp -r ~/HomA/turn_off.png .
cp -r ~/HomA/turn_on.png .
cp -r ~/HomA/up.png .
cp -L ~/HomA/vu_meter.py .  # Pippim volume meter
cp -L ~/HomA/vu_pulse_audio.py .  # Pippim PulseAudio controller
cp -r ~/HomA/wifi.png .
cp -L ~/HomA/x11.py .  # symlink

# Remove all .pyc files from commit
find . -name "*.pyc" -exec rm -f "{}" \;
git rm -r --cached *.pyc

git add Alarm_01.wav
git add audio
git add bias.jpg
git add breathing.jpeg
git add calc.py
git add close.png
git add computer.jpg
git add down.png
git add external.py
git add flame.png
git add global_variables.py
git add mag_glass.png
git add homa_common.py
git add homa-indicator.py
git add homa.py
git add hs100.sh
git add image.py
git add laptop_b.jpg
git add laptop_d.jpg
git add led_lights.jpg
git add lightning_bolt.png
git add message.py
git add monitor.py
git add nighttime.png
git add picture_off.png
git add picture_on.png
git add pimtube.py
git add pulsectl/
git add pygatt/
git add refresh.sh
git add reset.jpeg
git add set_color.jpeg
git add sony.jpg
git add sql.py
git add tcl.jpg
git add timefmt.py
git add toolkit.py
git add trionesControl/
git add ttkwidgets/
git add turn_off.png
git add turn_on.png
git add up.png
git add vu_meter.py
git add vu_pulse_audio.py
git add wifi.png
git add x11.py

retVal=$?
if [ $retVal -ne 0 ]; then
    echo "git add src/x11.py FAILED with code: $retVal"
    exit $retVal
fi

# Pull the trigger and commit changes
git commit -m "$commit_message"
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "git commit -m FAILED with code: $retVal"
    exit $retVal
fi

echo
echo "=== PUSHING: $PWD changes to github.com"

git push
retVal=$?
if [ $retVal -ne 0 ]; then
    echo "git push FAILED with code: $retVal"
    exit $retVal
fi

exit 0
