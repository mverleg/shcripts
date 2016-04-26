#!/usr/bin/env bash

source "${BASH_SOURCE%/*}/macro_setup.sh"

if [ -e "$macrofile" ]
then
	echo "no recording to play ($macrofile does not exist)"
	exit 1
fi

notify_capped "Playing back macro" 

xmacroplay -d 2 "$DISPLAY" < "$macrofile"


