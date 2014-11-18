#!/bin/bash
# Author:   Armen Zambrano Gasparnian
# Purpose:  This script does the following:
#             - update the repos under a workdir without clobbering
#
while getopts w:h opts; do
   case ${opts} in
      w) workdir=${OPTARG} ;;
      h) help=1 ;;
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

for repo in `find $repos_dir -maxdepth 1 -mindepth 1 -type d`
do
    cd $repo
    hg pull -u || exit 1
    echo "Repo info: $repo_path updated to `hg id`"
done
