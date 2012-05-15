#!/bin/bash
export VERSION=14.0b1
export BUILDNUM=3
export RD=/home/ftp/pub/mozilla.org/mobile/releases
export CD=/home/ftp/pub/mozilla.org/mobile/candidates
export PLATFORMS="android"

set -x
set -e

mkdir $RD/$VERSION
for platform in $PLATFORMS; do
    cd $CD/$VERSION-candidates/build$BUILDNUM/$platform/
    LOCALES=`ls -1`

    cd $RD/$VERSION

    for locale in $LOCALES ; do
        mkdir -p -m 755 $platform/$locale
        rsync -av \
          $CD/$VERSION-candidates/build$BUILDNUM/$platform/$locale/ \
          $RD/$VERSION/$platform/$locale/
    done
done
