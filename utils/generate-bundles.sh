#!/bin/bash
set -e
set -x

WRK_DIR=~/tmp/bundle
cd $WRK_DIR
for repo in tools mozharness; do
    rm -rf $repo $repo.bundle
    hg clone https://hg.mozilla.org/build/$repo
    hg -R $repo bundle -t gzip -a $repo.bundle
    for bucket in mozilla-releng-tarballs-use1 mozilla-releng-tarballs-usw2; do
        s3cmd -P put $repo.bundle s3://$bucket
    done
done
