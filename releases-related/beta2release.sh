#!/bin/bash
# from https://wiki.mozilla.org/Release:Release_Automation_on_Mercurial:Documentation#Sync_mozilla-beta_to_mozilla-release

set -x
set -e

# Adjust VERSION variable which stands for the current Firefox version in mozilla-release
VERSION=10
HG_USER="ffxbld <release@mozilla.com>"

hg clone http://hg.mozilla.org/releases/mozilla-release
hg clone http://hg.mozilla.org/releases/mozilla-beta

beta_rev=$(hg -R mozilla-beta id -i -r default)
release_rev=$(hg -R mozilla-release id -i -r default)

RELEASE_BASE_TAG="RELEASE_BASE_`date +%Y%m%d`"
RELEASE_TAG="FIREFOX_RELEASE_$VERSION"

hg -R mozilla-beta tag -r $beta_rev -u "$HG_USER" -m "Added tag $RELEASE_BASE_TAG for changeset $beta_rev. CLOSED TREE a=release DONTBUILD" $RELEASE_BASE_TAG
hg -R mozilla-beta push -e "ssh -l ffxbld -i ~/.ssh/ffxbld_dsa" ssh://hg.mozilla.org/releases/mozilla-beta

hg -R mozilla-release tag -r $release_rev -u "$HG_USER" -m "Added tag $RELEASE_TAG for changeset $release_rev. CLOSED TREE a=release" $RELEASE_TAG
hg -R mozilla-release commit -u "$HG_USER" -m "Closing old head. CLOSED TREE a=release" --close-branch

hg -R mozilla-release pull mozilla-beta
hg -R mozilla-release up -C default

# edit shipped-locales file if you need to remove some beta locales

# push back
# hg -R mozilla-release push -f -e "ssh -l ffxbld -i ~/.ssh/ffxbld_dsa" ssh://hg.mozilla.org/releases/mozilla-release

