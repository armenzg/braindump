#!/bin/sh
# Author:   Armen Zambrano Gasparnian
# Purpose:  It lists the list of builders that get added/removed after
#           a buildbot-configs patch
# Usage:    ./list_builder_differences.sh -j path_to_patch_to_test.diff [-w alternative_workdir]
#
while getopts j:w: opts; do
   case ${opts} in
      j) patch_to_test=${OPTARG} ;;
      w) workdir=${OPTARG} ;;
   esac
done

if [ -z "$patch_to_test" ];
then
    echo "Please pass the path to the patch you want information about."
    exit 1
fi

if [ -z "$workdir" ];
then
    workdir="$HOME/.mozilla/releng"
fi

venv="$workdir/venv"
bconfigs="buildbot-configs"
bcustom="buildbotcustom"
bdump="braindump"
bbot="buildbot"
tools="tools"

if [ ! -d "$workdir" ]
then
    mkdir $workdir
fi

for repo_name in $bconfigs $bcustom $bdump $bbot $tools
do
    if [ ! -d "$workdir/$repo_name" ]
    then
        hg clone http://hg.mozilla.org/build/$repo_name $workdir/$repo_name
    else
        cd $workdir/$repo_name
        hg pull -u
        hg up -C
        cd -
    fi
done

bconfigs="$workdir/$bconfigs"
bcustom="$workdir/$bcustom"
bdump="$workdir/$bdump"
bbot="$workdir/$bbot"
tools="$workdir/$tools"

if [ ! -d $venv ]
then
    virtualenv $venv
    /bin/bash -c ". $venv/bin/activate"
    export PATH=$venv/bin:$PATH
    #pip install pyOpenSSL
    #pip install Twisted==10.1.0
    pip install -r ~/repos/releng/braindump/buildbot-related/pre_buildbot_master_requirements.txt
    cd $bbot/master
    python setup.py install
fi

/bin/bash -c ". $venv/bin/activate"
export PATH=$venv/bin:$PATH
# So we can reach buildbotcustom
export PYTHONPATH=$tools/lib/python:$workdir

cd $bconfigs
rm -rf test-output
patch -p1 < $patch_to_test || exit
$bdump/buildbot-related/dump_allthethings.sh $workdir/allthethings_with_patch.json
hg up -C
$bdump/buildbot-related/dump_allthethings.sh $workdir/allthethings_without_patch.json
cd -
$bdump/buildbot-related/diff_allthethings.py $workdir/allthethings_without_patch.json $workdir/allthethings_with_patch.json > differences.txt
echo "Here's the file that contains your changes: differences.txt"
