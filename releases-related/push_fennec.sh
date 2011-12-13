#!/bin/bash
export VERSION=9.0
export BUILDNUM=1
export RD=/home/ftp/pub/mozilla.org/mobile/releases
export CD=/home/ftp/pub/mozilla.org/mobile/candidates

set -x
set -e

mkdir $RD/$VERSION
cd $RD/$VERSION

rsync -av --exclude=unsigned --exclude=*.txt --exclude=*crashreporter* \
 --exclude=*tests* --exclude=*unaligned* --exclude=*old* --exclude=*install* \
 --exclude=*logs* --exclude=*xpi* --exclude=**/win32/*/win32 \
 --exclude=**/linux/*/linux-i686 --exclude=**/macosx/*/mac \
 $CD/$VERSION-candidates/build$BUILDNUM/ $RD/$VERSION/

for p in linux macosx win32; do
    locales=`cd $CD/$VERSION-candidates/build$BUILDNUM/$p/; ls -1 --hide=en-US`
    for i in $locales; do
        cp -av $CD/$VERSION-candidates/build$BUILDNUM/$p/$i/*/xpi/*.xpi \
          $RD/$VERSION/$p/$i
    done
done

# update symlinks only for releases, ignore beta (b) versions
if ! echo $VERSION | grep -q b; then
    cd $RD
    rm -f latest
    ln -s $VERSION latest
fi
