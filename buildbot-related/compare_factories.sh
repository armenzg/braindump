#!/bin/bash
# compare_factories.sh mastercfg [oldrev] newrev
set -e

CONFIGS_DIR=$HOME/mozilla/buildbot-configs
BBCUSTOM_DIR=$HOME/mozilla/buildbotcustom

DIFFCMD=vimdiff
DUMPCMD="python $HOME/mozilla/braindump/buildbot-related//builder_list.py"

# Returns the revision that is the (first) parent of the given revision
function getparent() {
    repo=$1
    rev=$2
    hg parents -R "$repo" -r "$rev" --template "{rev}:" | cut -f1 -d:
}

if [ -z "$1" ]; then
    echo "mastercfg required"
    exit 1
fi
mastercfg=$1

if [ -z "$3" ]; then
    if [ -z "$2" ]; then
        newrev=tip
    else
        newrev=$2
    fi
    oldrev=$(getparent $CONFIGS_DIR $newrev)
else
    oldrev=$2
    newrev=$3
fi

export PYTHONPATH=$(dirname $BBCUSTOM_DIR):$PYTHONPATH

new=$(mktemp)
old=$(mktemp)

trap "rm -rf $new $old" EXIT

# Goto the old revision
hg -R "$CONFIGS_DIR" update -r $oldrev
$DUMPCMD $mastercfg > $old

# Goto the new revision
hg -R "$CONFIG_DIR" update -r $newrev
$DUMPCMD $mastercfg > $new

$DIFFCMD $old $new
