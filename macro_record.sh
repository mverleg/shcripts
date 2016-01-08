#!/usr/bin/env bash

macrofile='/tmp/macro.recording'
lockfile='/tmp/macro.record.lock'

if [ -e "$lockfile" ]
then
	if [ `stat --format=%Y $lockfile` -le $(( `date +%s` - 150 )) ]
	then
		notify-send "It appears a macro is already being recorded (manually delete $lockfile if not). Stopping."
		exit 1;
	else
		rm -f "$lockfile"
	fi
fi

notify-send "Recording macro; press ESC to stop" 

timeout 150 xmacrorec2 -k 9 > "$macrofile"

notify-send "Recording macro finished; use F10 to play it"

rm -f "$lockfile"


