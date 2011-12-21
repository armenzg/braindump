#!/bin/bash
set -x
set -e

PRODUCT=xulrunner
VERSION=9.0.1
BUILD=1
TAG=FIREFOX_9_0_1_RELEASE

KEYDIR=d:/2011-keys
REPO="releases/mozilla-release"
EMAIL=release@mozilla.com

cd ~/hg-tools
hg pull
hg up -r ${TAG}

mkdir -p ~/signing-work/${PRODUCT}-${VERSION}
cd ~/signing-work/${PRODUCT}-${VERSION}
cp ~/hg-tools/release/signing/* .

make setup PRODUCT=${PRODUCT} VERSION=${VERSION} \
  BUILD=${BUILD} REPO=${REPO} EMAIL=${EMAIL} KEYDIR=${KEYDIR}
rsync -av -e "ssh -i /home/cltsign/.ssh/xrbld_dsa" \
  --exclude=*.txt --exclude=*-symbols.zip --exclude=jsshell* \
  xrbld@stage.mozilla.org:/home/ftp/pub/${PRODUCT}/nightly/${VERSION}-candidates/build${BUILD}/ \
  unsigned-build${BUILD}
rsync -av --exclude=unsigned unsigned-build${BUILD}/ signed-build${BUILD}/
rsync -av unsigned-build${BUILD}/unsigned/ signed-build${BUILD}/

make checksum-files create-sigs stage verify-sigs \
  PRODUCT=${PRODUCT} VERSION=${VERSION} BUILD=${BUILD} \
  REPO=${REPO} EMAIL=${EMAIL} KEYDIR=${KEYDIR}

rmdir signed-build${BUILD}/contrib{,-localized}

rsync -av -e "ssh -i /home/cltsign/.ssh/xrbld_dsa" \
  signed-build${BUILD}/ \
  xrbld@stage.mozilla.org:/home/ftp/pub/${PRODUCT}/nightly/${VERSION}-candidates/build${BUILD}/
