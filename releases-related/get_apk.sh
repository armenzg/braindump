#!/bin/bash
USAGE="usage: ${0##*/} [options] version_number
    download APKs so they can be uploaded to stores
    always downloads all of them, even if not needed
    (e.g. x86 & ko)
Arguments:
    version_number  version number to download, e.g. 23.0b7

Options:
    -b|--build N    specify build number (default 1)
    -h|--help       this help
"

warn() { for m; do echo "$m"; done 1>&2 ; }
die() { warn "$@"; exit 1; }
usage() { warn "$@" "${USAGE:-}" ; test $# -eq 0; exit $?; }

checkAPK() {
    file $1 | grep 'Zip archive'
}

generateURL() {

    local VERSION=$1
    local ARCH=$2
    local BUILD=$3
    local LOCALE=$4
    local ANDROID_LAYOUT=$5
    local ARCH_FILE=$6

    # From FX 37, we separated arm api v9 & v11. So, the URL changed.
    # Example:
    # http://ftp.mozilla.org/pub/mozilla.org/mobile/candidates/37.0b1-candidates/build1/android-api-9/multi/fennec-37.0b1.multi.android-arm.apk
    echo "https://ftp.mozilla.org/pub/mozilla.org/mobile/candidates/$VERSION-candidates/build${BUILD}/${ANDROID_LAYOUT}/${LOCALE}/fennec-$VERSION.${LOCALE}.android-$ARCH_FILE.apk"

}

downloadAPK() {
    local VERSION=$1
    local ARCH=$2
    local BUILD=$3
    local ANDROID_LAYOUT=""
    local LOCALE="multi"

    MAJOR=$(echo $VERSION|cut -d\. -f1)

    if test "$ARCH" == "arm"; then
        # Change introduced in Fx 37 (arm v7 only)
        ANDROID_LAYOUT="v9_v11"
    else
        # android-x86 for example
        ANDROID_LAYOUT="android-$ARCH"
    fi

    if test "$ARCH" == "x86"; then
        # the filename contains i386 instead of x86
        ARCH_FILE="i386"
    else
        ARCH_FILE=$ARCH
    fi

    if test $# -eq 4; then
        # For t-store (ko)
        LOCALE=$4
    fi

    echo "Downloading version $VERSION build #$BUILD for arch $ARCH (locale $LOCALE)"

    if test "$ANDROID_LAYOUT" == "v9_v11"; then
        # When dealing with API v9 & V11, we want to rename the file
        # until bug 1122059 is fixed
        # Also manage the KO locale
        FILENAME_ARM_V9=fennec-$VERSION.$LOCALE.android-arm-api-9.apk
        curl -sS $(generateURL $VERSION $ARCH $BUILD $LOCALE android-api-9 $ARCH_FILE) -o $FILENAME_ARM_V9
        checkAPK $FILENAME_ARM_V9

        FILENAME_ARM_V11=fennec-$VERSION.$LOCALE.android-arm-api-11.apk
        curl -sS $(generateURL $VERSION $ARCH $BUILD $LOCALE android-api-11 $ARCH_FILE) -o $FILENAME_ARM_V11
        checkAPK $FILENAME_ARM_V11
    else
        # Manage x86
        FILENAME=fennec-$VERSION.$LOCALE.android-$ARCH_FILE.apk
        curl -sSO $(generateURL $VERSION $ARCH $BUILD $LOCALE $ANDROID_LAYOUT $ARCH_FILE)
        checkAPK $FILENAME
    fi
}

test -n "${1:-}" || usage "Missing build number"

trap "echo 'FAILED to download apks for $1'; exit 1" EXIT

set -eu

build=1
while test $# -gt 0; do
    case "$1" in
    -b|--build) build="$2" ; shift ;;
    -h|--help) usage ;;
    -* ) usage "unknown option '$1'" ;;
    *) break ;;
    esac
    shift
done

test $# -eq 1 || usage "wrong number of arguments '$#'"
version="$1"

# Pull binaries down, then make sure we got an archive and not a error
# page
downloadAPK $version "arm" $build
downloadAPK $version "arm" $build "ko"
downloadAPK $version "x86" $build

trap "" EXIT
echo "Success! All apks downloaded and appear to be Zip archives"

push_script_file=push_fennec.sh
if test -r $push_script_file; then
    sed -i.bak \
        -e "s,^\(export VERSION=\).*$,\1$version," \
        -e "s,^\(export BUILDNUM=\).*$,\1$build," \
        $push_script_file
    ec=$?
    if test $ec -eq 0; then
        warn "modified $push_script_file ready for commit" \
             "please verify the PLATFORMS line before commit:"
        grep -m 1 "^export PLATFORMS=" $push_script_file
    else
        warn "failed to modify $push_script_file ($ec)," \
             "original in $push_script_file.bak"
    fi
fi
