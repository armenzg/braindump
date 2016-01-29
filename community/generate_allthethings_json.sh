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
original_file="/var/www/html/builds/allthethings.json"
publishing_path="/var/www/html/builds/allthethings"
repos_dir="$workdir/repos"
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $script_dir

function make_allthethings() {
    source $workdir/venv/bin/activate
    echo "making all the things!"
    (
    cd $repos_dir/buildbot-configs
    # Generate allthethings.json
    $dump_script $allthethings || exit 1
    )
}

# If we're executing this in cruncher we don't need to call
# setup_buildbot_environment.sh (since we've already done so)
# The main difference here is the "updated" or not logic
if [ -d /var/www/html/builds/ ]; then
    cd $repos_dir
    # Logic borrowed from catlee
    updated=0
    rev_signature=''
    for d in buildbot-configs buildbotcustom tools; do
        hg -R $d pull -q
        prev_rev=$(hg -R $d id)
        hg -R $d update -q
        cur_rev=$(hg -R $d id)
        if [ "$prev_rev" != "$cur_rev" ]; then
            updated=1
        fi
        only_hash=`echo $cur_rev | awk -F " " '{print $1}'`
        rev_signature="${rev_signature}_${only_hash}"
    done

    if [ "$updated" = "1" ]; then
        date=`date +%Y%m%d%H%M%S`
        log="$publishing_path/allthethings.${date}.log"
        # Generate allthethings.json
        make_allthethings 2>&1 > $log || cat $log

        original_file="$publishing_path/allthethings.json"
        new_file="$publishing_path/allthethings.${date}.${rev_signature}.json"
        # Publish new file
        cp $allthethings $new_file
        # Generate differences with the previous allthethings.json
        $repos_dir/braindump/buildbot-related/diff_allthethings.py \
           $original_file $new_file > \
           $publishing_path/allthethings.${date}.${rev_signature}.differences.txt
        # Overwrite the previous allthethings.json
        cp $new_file $original_file
        gzip -c $new_file > $publishing_path/allthethings.json.gz
        chmod 644 $original_file
        chmod 644 $publishing_path/allthethings.*
    fi
else
    ./setup_buildbot_environment.sh $quiet "$python_path" -w $workdir

    make_allthethings
    echo "The file is now in here $allthethings"
fi
