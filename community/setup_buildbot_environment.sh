#!/bin/bash
# Author:   Armen Zambrano Gasparnian
# Purpose:  This script does the following:
#             - create a workdir
#             - check-out and update all required Buildbot Release Engineering repositories
#             - create buildbot virtual environments
#
while getopts w:qh opts; do
   case ${opts} in
      w) workdir=${OPTARG} ;;
      q) verbosity="-q" ;;
      h) help=1 ;;
   esac
done

if [ ! -z $help ];
then
    echo "./setup_buildbot_environment.sh [-w alt_workdir] [-h] [-q]"
    exit
fi

if [ -z "$workdir" ];
then
    workdir="$HOME/.mozilla/releng"
fi

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load common variables
. "$script_dir/buildbot_config.sh" -w "$workdir"

if [ ! -d "$repos_dir" ]
then
    mkdir -p "$repos_dir"
fi

# Checkout and update all repos
OLDIFS=$IFS
IFS=','
for repo in $bco,$bco_b $bcu,$bcu_b $bdu,$bdu_b $bbo,$bbo_b $tools,$tools_b
do
    cd $repos_dir
    set $repo
    repo_path=$1
    repo_name=`basename $repo_path`
    branch=$2
    if [ ! -d "$repo_path" ]
    then
        hg clone $verbosity http://hg.mozilla.org/build/$repo_name || exit
    fi
    # Let's update to the right branch
    cd $repo_path
    hg up -C $verbosity
    hg pull $verbosity
    hg up -r $branch $verbosity
    hg status -u -0 | xargs -0 rm #Remove untracked files
    if [ ! -z $verbosity ]; then echo "Repo info: $repo_path updated to `hg id`"; fi
done
IFS=$OLDIFS

if [ ! -d "$venv" ]
then
    virtualenv --no-site-packages "$venv" || exit
    source ". $venv/bin/activate"
    pip install -r "$bdu/community/pre_buildbot_requirements.txt"
    # Install buildbot
    cd "$bbo/master"
    python setup.py install || exit
    # Install buildslave
    pip install buildbot-slave==0.8.4-pre-moz2 \
        --find-links http://pypi.pub.build.mozilla.org/pub || exit
    # This is so we can reach buildbotcustom and tools when activating the venv
    echo "$repos_dir" >> "$venv"/lib/python2.7/site-packages/releng.pth
    echo "$tools/lib/python" >> "$venv"/lib/python2.7/site-packages/releng.pth
fi

if [ ! -z $verbosity ]
then
    echo ""
    echo ""
    echo "Congratulations! You now have a virtual environment set-up for your buildbot "
    echo "masters and slaves under $venv."
    echo "You should call this script every time you want to bring your environment up-to-date."
    echo ""
    echo "We have optimized the code so it updates fast and we don't clobber your "
    echo "environment."
    echo ""
fi
