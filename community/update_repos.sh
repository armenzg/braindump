#!/bin/bash
# Author:   Armen Zambrano Gasparnian
# Purpose:  This script does the following:
#             - update the repos under a workdir without clobbering
#
while getopts w:hc opts; do
   case ${opts} in
      w) workdir=${OPTARG} ;;
      h) help=1 ;;
      c) clobber=1 ;;
   esac
done

if [ ! -z $help ];
then
    echo "./update_repos.sh [-w alt_workdir] [-h]"
    exit
fi

if [ -z "$workdir" ];
then
    workdir="$HOME/.mozilla/releng"
fi

# Load common variables
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
. "$script_dir/buildbot_config.sh" -w "$workdir"

# Checkout and update all repos
OLDIFS=$IFS
IFS=','
for repo_info in $bco,$bco_b $bcu,$bcu_b $bdu,$bdu_b $bbo,$bbo_b $tools,$tools_b
do
    set $repo_info
    repo_path=$1
    repo_name=`basename $repo_path`
    branch=$2
    cd $repo_path
    hg pull -q -u || exit 1
    if [ ! -z $clobber ];
    then
        #hg up -q -C
        hg up -q -r $branch
    fi
    echo "Repo info: $repo_name updated to `hg id`"
done
IFS=$OLDIFS
