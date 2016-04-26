#!/usr/bin/env bash

macrofile="$HOME/.cache/macro.recording"
pidfile="$HOME/.cache/macro.record.pid"
notifylock="$HOME/.cache/ubuntu.notify.lock"
mkdir -p -m 700 "$HOME/.cache"

function notify_capped ()
{
	if [ ! -e "$notifylock" ]
	then
		touch "$notifylock"
		{ sleep 9; rm -f "$notifylock"; } &
		notify-send "$@"
	fi
}

if [ -e "$pidfile" ]
then
	prevpid="$(cat $pidfile)"
	echo "killing previous recording process $prevpid"
	kill -9 "$prevpid"
	rm -f "$pidfile"
fi


