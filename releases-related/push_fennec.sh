#!/bin/bash
# VERSION & BUILDNUM are the "version" and "buildNumber" from the
# release's cofiguration file
export VERSION=28.0b6
export BUILDNUM=1
export RD=/home/ftp/pub/mozilla.org/mobile/releases
export CD=/home/ftp/pub/mozilla.org/mobile/candidates
export PLATFORMS="android android-armv6 android-x86"
#export PLATFORMS="android android-armv6"

set -x
set -e

if [[ $VERSION != ${VERSION/b[1-9]/} ]]; then
  export LATEST=latest-beta
else
  export LATEST=latest
fi

mkdir $RD/$VERSION
cd $RD/$VERSION
mkdir source
rsync -av $CD/$VERSION-candidates/build$BUILDNUM/source/ \
  $RD/$VERSION/source
for platform in $PLATFORMS; do
    cd $CD/$VERSION-candidates/build$BUILDNUM/$platform/
    LOCALES=`ls -1`

    cd $RD/$VERSION

    for locale in $LOCALES ; do
        mkdir -p -m 755 $platform/$locale
        rsync -av --exclude=host \
          --exclude=gecko-unsigned-unaligned.apk --exclude=robocop.apk \
          --exclude=*symbols.zip --exclude=*tests.zip --exclude=jsshell*.zip \
          --exclude=*.txt --exclude=*.json \
          $CD/$VERSION-candidates/build$BUILDNUM/$platform/$locale/ \
          $RD/$VERSION/$platform/$locale/
    done

    cd $RD
    rm $LATEST
    ln -s $VERSION $LATEST
done
