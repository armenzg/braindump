#!/bin/sh
set -e

cd $HOME/buildfaster
hg -q -R braindump pull -u

source $HOME/buildfaster/bin/activate

output=/home/buildduty/buildfaster/buildfaster.csv.gz
weboutput=/var/www/html/builds/buildfaster.csv.gz
tmp=$(mktemp)
trap "rm -f $tmp" EXIT

ITER=1
for i in `seq ${ITER}`; do
    if (/home/buildduty/buildfaster/bin/python $HOME/buildfaster/buildfaster_report.py $tmp); then
        break
    fi
    sleep 60
done
gzip $tmp
mv $tmp.gz $output
chmod 644 $output
cp $output $weboutput
