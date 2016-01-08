#!/usr/bin/env bash

# get path to this directory
here="${BASH_SOURCE%/*}"

# logging
source "$here/command_logging.sh"
alias logto="log_err_all_named"
alias log="log_err_all"

# git changes
source "$here/git_changes.sh"
alias git_changes="git_changes_recursive"

# json
alias json_zoom="python $here/json_zoom.py"

# Chinese
alias pinyin_tones="python $here/pinyin_tones.py"



