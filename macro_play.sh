#!/usr/bin/env bash

macrofile='/tmp/macro.recording'
lockfile='/tmp/macro.play.notify.lock'

if [ -e "$lockfile" ]
then
	if [ `stat --format=%Y $lockfile` -le $(( `date +%s` - 10 )) ]
	then
		notify-send "Playing back macro (on $DISPLAY) - expired lock"
	fi
else
	notify-send "Playing back macro (on $DISPLAY) - no lock"
fi

touch "$lockfile"

xmacroplay -d 2 "$DISPLAY" < "$macrofile"


