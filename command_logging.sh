#!/usr/bin/env bash

function tail_truncate ()
{
	# 
	# Preserve the last $2 (default 5k) lines of file $1.
	# Note that redirecting directly will empty the already open file.
	# 
	if [ -z "$1" ]; then printf "tail_truncate needs a filepath as first argument"; return 1; fi
	if [ -n "$2" ]; then cnt="$2"; else cnt="5000"; fi
	touch "$1" || return 2
	content="$(tail -n $cnt $1)"
	printf "$content\n" > "$1"
}

function log_err_all () 
{
	#
	# Similar to log_err_all_named but uses the bassename of the first part as name.
	# 
	nm=$(basename $1)
	nm="${nm%.*}";
	log_err_all_named "$nm" $@
}

function log_err_all_named ()
{
	# 
	# Redirect stdout to $1.out, stderr to $2.err and the combination of them to $2.
	# A downside is that after this function, everything is in stdout.
	# 
	# Arguments:
	#  -a  Append to logs instead of overwriting.
	#  -b  Attempts to prevent mixed order (because of buffering), but doesn't 
	#		 always help, and can't be used with functions or groups of commands.
	#  -c  Write the command before any output (most useful when appending).
	#  -t  Truncate logs to 5k lines (before starting).
	#  -u  Do not add timestamps.
	# 
	
	# get flags
	flags=""
	cmd=$@
	for word in $cmd; do
		cmd=$(echo $cmd | cut -d ' ' -f 2-)
		if [[ $word == -* ]]; then
			flags="$flags $word"
		else
			fname="$word"
			break
		fi
	done
	
	# handle flags
	if [[ $flags == *"-a"* ]]; then ap="--append"; else ap=""; fi
	if [[ $flags == *"-b"* ]]; then pre="stdbuf -oL -eL "; else pre=""; fi
	if [[ $flags == *"-t"* ]]; then
		for file in "$fname.out" "$fname.err" "$fname.all"; do tail_truncate "$file"; done
	fi
	if [[ $flags == *"-c"* ]]; then
		if [[ $flags == *"-u"* ]]; then header="=== $cmd ==="; else header=$(echo "=== $cmd ===" | ts '%Y-%m-%d,%H:%M:%.S '); fi
		printf "$header\n" | tee $ap "$fname.out" | tee $ap "$fname.err" | tee $ap "$fname.all" 1> /dev/null
	fi
	
	# run the command with logging
	if [[ $flags == *"-u"* ]]; then
		{
			{
				$pre $cmd | tee $ap "$fname.out"
			} 3>&1 1>&2 2>&3 | tee $ap "$fname.err"
		} |& tee $ap "$fname.all"
		else
		{
			{
				$pre $cmd | ts '%Y-%m-%d,%H:%M:%.S ' | tee $ap "$fname.out"
			} 3>&1 1>&2 2>&3 | ts '%Y-%m-%d,%H:%M:%.S ' | tee $ap "$fname.err"
		} |& tee $ap "$fname.all" | sed 's/^.\{28\}//'
	fi
	printf '\n'
}

function test_logging_function ()
{
	# 
	# Function that can be used to test the above functions, e.g.
	#   log_err_all_named -a -c -t "/tmp/mylog" test_logging_function arg1 arg2
	# 
	sleep 0.5
	printf "output1\n"
	printf "error1\n" 1>&2
	printf "output2\n"
	printf "error2\n" 1>&2
	printf "$@\n"
	sleep 0.5
}


