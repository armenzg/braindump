#!/bin/bash
USAGE="usage: ${0##*/} [options] version_number
    download APKs so they can be uploaded to stores
Arguements:
    version_number  version number to donwload, e.g. 23.0b7

Options:
    -b|--build N    specify build number (default 1)
    -h|--help       this help
"

warn() { for m; do echo "$m"; done 1>&2 ; }
die() { warn "$@"; exit 1; }
usage() { warn "$@" "${USAGE:-}" ; test $# -eq 0; exit $?; }

test -n "${1:-}" || usage "Missing build nuber"

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

test $# -eq 1 || usage "wrong number of arguements '$#'"

# Pull binaries down, then make sure we got an archive and not a error
# page
echo "Downloading arm7 for $1 build $build"
curl -sSO https://ftp.mozilla.org/pub/mozilla.org/mobile/candidates/$1-candidates/build${build}/android/multi/fennec-$1.multi.android-arm.apk
file fennec-$1.multi.android-arm.apk | grep 'Zip archive'
echo "Downloading arm6 for $1 build $build"
curl -sSO https://ftp.mozilla.org/pub/mozilla.org/mobile/candidates/$1-candidates/build${build}/android-armv6/multi/fennec-$1.multi.android-arm-armv6.apk
file fennec-$1.multi.android-arm-armv6.apk | grep 'Zip archive'
echo "Downloading x86 for $1 build $build"
curl -sSO https://ftp.mozilla.org/pub/mozilla.org/mobile/candidates/$1-candidates/build${build}/android-x86/multi/fennec-$1.multi.android-i386.apk
file fennec-$1.multi.android-i386.apk | grep 'Zip archive'
trap "" EXIT
echo "Success! All three apks downloaded and appear to be Zip archives"
