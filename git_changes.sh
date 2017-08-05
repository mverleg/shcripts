#!/usr/bin/env bash

function git_changes_curdir ()
{
	# 
	# Find and print the status of git in the current directory.
	# 
	nm="$(printf "%-20s" $(basename $(pwd)))"
	if [[ $* == *-p* ]]
	then
		pth="$(pwd)"
		[[ "$pth" =~ ^"$HOME"(/|$) ]] && pth="~${pth#$HOME}"
		nm="$nm $(printf "%-30s" $pth)"
	fi
	if [[ $* == *-o* ]]
	then
		nm="$nm $(printf "%-26s" $(git config --get remote.origin.url))"
	fi
	do_push=false
    if [[ $* == *-d* ]]
    then
		do_push=true
    fi
	if [ ! -z "$(git status --porcelain)" ]
	then # check uncomitted changes
		echo "$nm [commit]"
		if $do_push; then pushd . 1> /dev/null ; fi
	elif ! git rev-list '@{u}' &> /dev/null
	then # check no remote
		echo "$nm [no remote]"
		if $do_push; then pushd . 1> /dev/null ; fi
	elif [ ! -z "$(git rev-list '@{u}..HEAD')" ]
	then # check unpushed changes
		echo "$nm [push]"
		if $do_push; then pushd . 1> /dev/null ; fi
	elif [[ $* == *-a* ]]
	then
		echo "$nm [ok]"
	fi
}

function git_changes_recursive ()
{
	# 
	# Search for all ancestors that are git repositories 
	#	and call git_changes_curdir on them.
	# 
	maindir="$(pwd)"
	echo "searching repositories..."
	findflag=""
	if [[ ! $* == *-a* ]]
	then 
		echo "hint: use -a to see all repositories"
	fi
	if [[ ! $* == *-p* ]]
	then
		echo "hint: use -p to see full paths"
	fi
	if [[ ! $* == *-o* ]]
	then
		echo "hint: use -o to see remote origin url"
	fi
	if [[ ! $* == *-x* ]]
	then 
		echo "hint: use -x to stay on fs (no mounts; faster)"
	else
		findflag="$findflag -xdev"
	fi
	if [[ ! $* == *-s* ]]
	then 
		echo "hint: use -s to skip hidden directories"
		repopths="$(find $PWD $findflag -type d -name '.git' -print 2> /dev/null)"
	else
		repopths="$(find $PWD $findflag -type d -name '.*' -prune -type d -name '.git' -print 2> /dev/null)"
	fi
	if [[ ! $* == *-d* ]]
	then
		echo "hint: use -d to pushd all the directories which have changes"
	fi
	for line in $repopths
		do
			cd "$line/.."
			git_changes_curdir $*
			cd "$maindir"
		done
	echo "done!"
}



