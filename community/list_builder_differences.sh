#!/bin/bash -e
# Author:   Armen Zambrano Gasparnian
# Purpose:  It lists the list of builders that get added/removed after
#           a buildbot-configs patch
#

# This determines the directory where the script lives
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
with_patch=`pwd`/allthethings_with_patch.json
without_patch=`pwd`/allthethings_without_patch.json
differences_path=`pwd`/differences.txt

while getopts cj:w:fhp opts; do
   case ${opts} in
      c) clobber="-c" ;;
      j) patch_to_test=${OPTARG} ;;
      w) workdir=${OPTARG} ;;
      f) faster=1 ;;
      h) help=1 ;;
      p) production=1 ;;
   esac
done

if [ ! -z $help ];
then
    echo "This script helps discover which builders get added/removed to"
    echo "Release Engineering buildbot masters (aka jobs on tbpl.mozilla.org)."
    echo ""
    echo "NOTE: This only works against patches from the buildbot-configs repo"
    echo ""
    echo "Usage: ./list_builder_differences.sh -j /path/to/patch/to/test.diff"
    echo "           [-f] [-w alternative_workdir]"
    echo " -j Specifies the path to the patch you're trying to test."
    echo " -w This specifies where to setup your buildbot environment."
    echo "    buildbot_config.sh contains the default value if not specified."
    echo " -f This skips running test-masters.sh."
    echo "    The first time and the last time you run this script for a patch"
    echo "    make sure that you run it without this flag."
    echo " -h It shows this help menu\n"
    exit 0
fi

if [ -z "$patch_to_test" ]
then
    echo "Please pass the path to the patch you want information about with -j path_to_patch."
    exit 1
fi

if [ ! -f "$patch_to_test" ]
then
    echo "We can't reach the file you specified: $patch_to_test"
    echo "Current directory is '$(pwd)'."
    echo "Please make sure that it is an absolute path"
    exit 1
fi

# Load common variables
. "$script_dir/buildbot_config.sh" -w "$workdir"

# Let's setup the buildbot environment and update it
"$script_dir/setup_buildbot_environment.sh" -w "$workdir" -q $clobber

if test "$?" -ne 0 ; then
    echo "We have failed to setup the buildbot environment".
    exit 1
fi

# setup_buildbot_environment always updates us to the production branches
# We write patches against the default branches
# If -p is not specified we use the default branch
if [ ! -z $production ]
then
    cd $bco
    hg up -r default
    cd $bcu
    hg up -r default
fi

# Activate the virtual environment
/bin/bash -c ". $venv/bin/activate"

cd $bco && patch -p1 < $patch_to_test || exit

if [ -z $faster ] # We can skip the testing if we want
then
    # This step checks that the patch is actually good
    export VIRTUAL_ENV="1" # This is to remove an unneeded warning in test-masters.sh
    rm -rf test-output
    $bco/test-masters.sh
    if test "$?" -ne 0 ; then
        echo "\nFAILED TESTS: test-masters.sh did not pass.\n"
        echo "Your patch does not pass the tests. See the masters that failed above and"
        echo "you can fix it by doing the following:"
        echo " - source $venv/bin/activate"
        echo " - ./setup-master.py master <master_short_name> && cd master"
        echo " - buildbot checkconfig ."
        echo "Once you make the changes required to make checkconfig pass, you can then"
        echo "run the tests for all the masters by running './test-masters.sh'."
        echo "If non of the masters fail, create a new patch and run this script again."
        echo "Otherwise, go back to the previous steps and fix one by one all failing masters."
        exit 1
    fi
fi

# Create new list of builders
rm -f $with_patch && cd $bco && $bdu/buildbot-related/dump_allthethings.sh $with_patch

if [ -z $faster ] # We are *not* asking for a faster run
then
    # Create current list of builders
    hg up -C
    rm -f $without_patch && cd $bco && $bdu/buildbot-related/dump_allthethings.sh $without_patch
fi

rm -f $differences_path
$bdu/buildbot-related/diff_allthethings.py $without_patch $with_patch > $differences_path
echo "\n"
cat $differences_path
echo -e "\\nHere's the file that contains your changes: $differences_path"
