#!/bin/bash
#
# Author:        Armen Zambrano Gasparnian
# Purpose:       This script does the following:
#                  - create generic build, try and test masters
#                  - create generic slaves for each of the previous masters
# Requirements:  You need GNU getopt and bash 4 (to use arrays)
# Usage:         Run ./create_community.sh -h for usage
#
command -v getopt >/dev/null 2>&1 || \
    { echo >&2 "I require GNU getopt but it's not installed.  Aborting."; exit 1; }

progname=$(basename $0) 
SHORTOPTS="w:r:"
LONGOPTS="start,stop"
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
path=$PATH

if $(getopt -T >/dev/null 2>&1) ; [ $? = 4 ] ; then # New longopts getopt.
    OPTS=$(getopt -o $SHORTOPTS --long $LONGOPTS -n "$progname" -- "$@")
fi

eval set -- "$OPTS"

while [ $# -gt 0 ]; do
    : debug: $1
    case $1 in
        --start)
            echo "Not implemented"
            exit 1;;
        --stop)
            echo "Not implemented"
            exit 1;;
        --help)
            echo "${progname} [-w alt_workdir] [-r {test|build|try}] [--help] [--start|--stop]"
            exit 0;;
        -w)
            workdir=$2; shift;;
        -r)
            role=$2; shift;;
        --)
            shift; break;; 
        -*)
            echo "$0: error - unrecognized option $1" 1>&2; exit 1;;
        *)
            break;;
    esac
    shift
done 

if [ -z "$workdir" ];
then
    workdir="$HOME/.mozilla/releng"
fi

if [ -z $role ];
then
    role=("test build try")
fi

# Load common variables
. $script_dir/buildbot_config.sh -w $workdir

for dir in "$slaves_dir" "$masters_dir"
do
    if [ ! -d "$dir" ]; then mkdir "$dir"; fi
done

if [ ! -d "$venv" ];
then
    "$script_dir/setup_buildbot_environment.sh" -w "$workdir"
fi

# Load up virtual environment
/bin/bash -c ". $venv/bin/activate"

for master_name in ${role[@]}
do
    master_name=${master_name}_master
    if [ ! -d ${masters_dir}/${master_name} ]
    then
        cd $bco
        $bco/setup-master.py -j $bdu/community/community-masters.json ${masters_dir}/${master_name} ${master_name} || exit
    fi
done

declare -A slaves=( 
 ["build"]="9010" ["build_slave"]="bld-linux64-ec2-001" \
 ["try"]="9011" ["try_slave"]="b-linux64-001" \
 ["test"]="9012" ["test_slave"]="tst-linux64-ec2-001" \
)

# NOTE: This is prone to use slaves that will not exist in the future
for slave_type in ${role[@]}
do
    if [ ! -d ${slaves_dir}/${slave_type} ]; then
        buildslave create-slave "$slaves_dir"/${slave_type} \
            localhost:${slave["${slave_type}"]} ${slaves["${slave_type}_slave"]} pass > /dev/null
    fi
done

echo ""
echo ""
echo "Congratulations! You should now have created buildbot masters and associated slaves."
echo ""
echo "You can activate the environment by calling 'source $venv/bin/activate'"
echo "You can then start the masters with 'buildbot start $masters_dir/name_of_master'"
echo "You can then start the slaves with 'buildslave start $slaves_dir/name_of_slave'"
