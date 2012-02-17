#!/bin/bash
export VERSION=11.0b3
export BUILDNUM=2
export RD=/home/ftp/pub/mozilla.org/mobile/releases
export CD=/home/ftp/pub/mozilla.org/mobile/candidates
export PLATFORMS="android-xul"

set -x
set -e

mkdir $RD/$VERSION
cd $RD/$VERSION

for platform in $PLATFORMS; do
    for locale in en-US multi ; do
        mkdir -p -m 755 $platform/$locale
        rsync -av --exclude=*gecko*  \
          $CD/$VERSION-candidates/build$BUILDNUM/$platform/$locale/ \
          $RD/$VERSION/$platform/$locale/
    done
done
