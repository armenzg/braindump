#!/bin/bash
set -e
set -x

WRK_DIR=~/tmp/bundle
TOOLS_DIR=~/work/mozilla/build/tools

GITTOOL=$TOOLS_DIR/buildfarm/utils/gittool.py
HGTOOL=$TOOLS_DIR/buildfarm/utils/hgtool.py
REPO_DIR=$WRK_DIR/git-shared/repo
export HG_SHARE_BASE_DIR=$WRK_DIR/hg-shared

DEVICES="dolphin emulator emulator-jb emulator-kk flame flame-kk hamachi helix nexus-4 wasabi"

# Clone mozilla-central
python $HGTOOL https://hg.mozilla.org/mozilla-central mozilla-central

# Clone B2G
python $GITTOOL https://git.mozilla.org/b2g/B2G.git B2G

mkdir -p $REPO_DIR

cd B2G
rm -rf .repo
ln -sf $REPO_DIR .repo
# No need to update the working copy
export REPO_SYNC_FLAGS=--network-only
for device in $DEVICES; do
    time ./config.sh -q $device ../mozilla-central/b2g/config/$device/sources.xml < /dev/null
done

cd $REPO_DIR/..
rm -rfv repo/manifest*
find repo -name clone.bundle -o -name '*.lock' -print -delete
time tar cf git-shared-repo.tar repo/

cd $HG_SHARE_BASE_DIR/mozilla-central/.hg
# central
cat << EOF > hgrc
[paths]
default = https://hg.mozilla.org/mozilla-central
EOF
time tar cf ../../mozilla-central.tar .

# try
cat << EOF > hgrc
[paths]
default = https://hg.mozilla.org/try
EOF
time tar cf ../../try.tar .
# inbound
cat << EOF > hgrc
[paths]
default = https://hg.mozilla.org/integration/mozilla-inbound
EOF
time tar cf ../../mozilla-inbound.tar .

# revert to central
cat << EOF > hgrc
[paths]
default = https://hg.mozilla.org/mozilla-central
EOF


# upload $HG_SHARE_BASE_DIR/mozilla-central.tar and $WRK_DIR/git-shared/repo.tar
time s3cmd put $HG_SHARE_BASE_DIR/mozilla-central.tar s3://mozilla-releng-tarballs/mozilla-central.tar
s3cmd setacl --acl-public s3://mozilla-releng-tarballs/mozilla-central.tar
time s3cmd put $WRK_DIR/git-shared/git-shared-repo.tar s3://mozilla-releng-tarballs/git-shared-repo.tar
s3cmd setacl --acl-public s3://mozilla-releng-tarballs/git-shared-repo.tar

time s3cmd put $HG_SHARE_BASE_DIR/mozilla-inbound.tar s3://mozilla-releng-tarballs/mozilla-inbound.tar
s3cmd setacl --acl-public s3://mozilla-releng-tarballs/mozilla-inbound.tar
time s3cmd put $HG_SHARE_BASE_DIR/try.tar s3://mozilla-releng-tarballs/try.tar
s3cmd setacl --acl-public s3://mozilla-releng-tarballs/try.tar
