#!/bin/bash -e
# Author:   Armen Zambrano Gasparnian
# Purpose:  This script does the following:
#             - generate allthethings.json
#
workdir="$HOME/.mozilla/releng"
./setup_buildbot_environment.sh -w $workdir
cd $workdir/repos/buildbot-configs
source $workdir/venv/bin/activate
# If you want to use a modified braindump repo change this
$workdir/repos/braindump/buildbot-related/dump_allthethings.sh
echo "The file is now in here $workdir/repos/buildbot-configs/allthethings.json"
