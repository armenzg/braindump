#!/bin/bash
set -e
master_dir=master_dir
builder_list="$(dirname $0)/builder_list.py"

if [ ".$@" != "." ] ; then
    extra_args="$@"
else
    extra_args="--tested-only"
fi

for master_name in $(python setup-master.py $extra_args -l | grep -v universal); do
    rm -rf $master_dir
    mkdir $master_dir
    echo "Master ${master_name}"
    python setup-master.py $extra_args $master_dir $master_name
    (cd $master_dir; buildbot checkconfig > /dev/null 2>&1 || (echo "Broken pieces are in $master_dir" 1>&2; false))
    (cd $master_dir; python $builder_list master.cfg | sort)
    rm -rf $master_dir
done
