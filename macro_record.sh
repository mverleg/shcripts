#!/usr/bin/env bash

source "${BASH_SOURCE%/*}/macro_setup.sh"

notify_capped "Recording macro; press ESC to stop" 

timeout 150 xmacrorec2 -k 9 > "$macrofile" &

newpid="$!"
echo "$newpid" > "$pidfile"
wait "$newpid"

notify_capped "Recording macro finished; use F10 to play it"

rm -f "$pidfile"


