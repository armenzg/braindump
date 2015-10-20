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

workdir="$HOME/.mozilla/releng"
allthethings="$workdir/repos/buildbot-configs/allthethings.json"
# If you want to use a modified braindump repo change this path
dump_script="$workdir/repos/braindump/buildbot-related/dump_allthethings.sh"
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $script_dir

function make_allthethings() {
    cd $workdir/repos/buildbot-configs
    source $workdir/venv/bin/activate
    echo "making all the things!"
    # Generate allthethings.json
    $dump_script
}

# If we're executing this in cruncher we don't need to call
# setup_buildbot_environment.sh (since we've already done so)
# The main difference here is the "updated" or not logic
if [ -d /var/www/html/builds/ ]; then
    cd $workdir/repos
    # Logic borrowed from catlee
    updated=0
    for d in buildbot-configs buildbotcustom tools; do
        t=$(mktemp)
        hg -R $d pull -q
        prev_rev=$(hg -R $d id)
        hg -R $d update -q
        cur_rev=$(hg -R $d id)
        if [ "$prev_rev" != "$cur_rev" ]; then
            echo "$d updated something"
            updated=1
        fi
    done

    if [ "$updated" = "1" ]; then
        make_allthethings
        # Do not overwrite the older allthethings
        cp $allthethings /var/www/html/builds/allthethings.new.json
        gzip -c $allthethings > /var/www/html/builds/allthethings.new.json.gz
        chmod 644 /var/www/html/builds/allthethings.new.json*
    fi
else
    ./setup_buildbot_environment.sh $quiet "$python_path" -w $workdir

    make_allthethings
    echo "The file is now in here $allthethings"
fi
