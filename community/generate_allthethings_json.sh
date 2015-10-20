#!/bin/bash -e
# Author:   Armen Zambrano Gasparnian
# Purpose:  This script does the following:
#             - generate allthethings.json
#
while getopts p:q opts; do
   case ${opts} in
      p) python_path=${OPTARG} ;;
      q) quiet="-q" ;;
   esac
done

if [ ! -z "$python_path" ];
then
   # Parameter for virtualenv
   python_path="-p $python_path"
fi

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $script_dir
workdir="$HOME/.mozilla/releng"
# Quiet set up
./setup_buildbot_environment.sh $quiet "$python_path" -w $workdir

cd $workdir/repos/buildbot-configs
source $workdir/venv/bin/activate
# If you want to use a modified braindump repo change this
$workdir/repos/braindump/buildbot-related/dump_allthethings.sh
allthethings="$workdir/repos/buildbot-configs/allthethings.json"

# If we're executing this in cruncher
if [ -d /var/www/html/builds/ ]
then
    # Do not overwrite the older allthethings
    cp $allthethings /var/www/html/builds/allthethings.new.json
    gzip -c $allthethings > /var/www/html/builds/allthethings.new.json.gz
    chmod 644 /var/www/html/builds/allthethings.new.json*
else
    echo "The file is now in here $allthethings"
fi
