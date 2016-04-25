#!/bin/bash
set -e
set -x

WRK_DIR=~/tmp/bundle
TOOLS_DIR=~/work/mozilla/build/tools

GITTOOL=$TOOLS_DIR/buildfarm/utils/gittool.py
HGTOOL=$TOOLS_DIR/buildfarm/utils/hgtool.py
REPO_DIR=$WRK_DIR/git-shared/repo
export HG_SHARE_BASE_DIR=$WRK_DIR/hg-shared

DEVICES="emulator emulator-jb emulator-kk flame-kk nexus-4"
TRY_DEVICES="emulator"

prep_hg_shares(){
    # Clone mozilla-central
    python $HGTOOL https://hg.mozilla.org/mozilla-central mozilla-central

}

prep_try_git_shares(){
    # Clone B2G
    python $GITTOOL https://git.mozilla.org/b2g/B2G.git B2G
    rm -rf $REPO_DIR
    mkdir -p $REPO_DIR

    cd B2G
    rm -rf .repo
    ln -sf $REPO_DIR .repo
    # No need to update the working copy
    export REPO_SYNC_FLAGS="--network-only --force-sync"
    for device in $TRY_DEVICES; do
        time ./config.sh -q $device ../mozilla-central/b2g/config/$device/sources.xml < /dev/null
    done

    cd $REPO_DIR
    rm -rfv manifest*
    find . -name clone.bundle -o -name '*.lock' -print -delete
    time tar cf ../git-shared-repo-try.tar .
}

prep_git_shares(){
    # Clone B2G
    python $GITTOOL https://git.mozilla.org/b2g/B2G.git B2G
    rm -rf $REPO_DIR
    mkdir -p $REPO_DIR

    cd B2G
    rm -rf .repo
    ln -sf $REPO_DIR .repo
    # No need to update the working copy
    export REPO_SYNC_FLAGS="--network-only --force-sync"
    for device in $DEVICES; do
        time ./config.sh -q $device ../mozilla-central/b2g/config/$device/sources.xml < /dev/null
    done

    cd $REPO_DIR
    rm -rfv manifest*
    find . -name clone.bundle -o -name '*.lock' -print -delete
    time tar cf ../git-shared-repo.tar .
}

prep_hg_tarballs(){
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
}

upload(){
    for bucket in mozilla-releng-tarballs-use1 mozilla-releng-tarballs-usw2; do
        for tarball in mozilla-central.tar mozilla-inbound.tar try.tar ; do
            time s3cmd --acl-public put $HG_SHARE_BASE_DIR/$tarball s3://$bucket/$tarball
        done

        time s3cmd  --acl-public put $WRK_DIR/git-shared/git-shared-repo.tar s3://$bucket/git-shared-repo.tar
        time s3cmd  --acl-public put $WRK_DIR/git-shared/git-shared-repo-try.tar s3://$bucket/git-shared-repo-try.tar
    done
}

prep_hg_shares
prep_git_shares
prep_try_git_shares
prep_hg_tarballs
upload
