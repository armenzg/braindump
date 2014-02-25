#!/bin/bash
set -e
master_dir=master_dir
dump_master="$(dirname $0)/dump_master.py"
extra_args="$@"
for master_name in $(python setup-master.py $extra_args -l); do
    rm -rf $master_dir
    mkdir $master_dir
    echo "Master ${master_name}"
    python setup-master.py $extra_args $master_dir $master_name
    (cd $master_dir; buildbot checkconfig > /dev/null 2>&1 || (echo "Broken pieces are in $master_dir" 1>&2; false))
    (cd $master_dir; python $dump_master master.cfg)
    rm -rf $master_dir
done
