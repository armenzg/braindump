#!/bin/bash

warn() { for m; do echo "$m"; done 1>&2 ; }
die() { warn "$@"; exit 1; }
usage() { warn "$@" "${USAGE:-}" ; test $# -eq 0; exit $?; }

test -n "${1:-}" || usage "Missing build nuber"

trap "echo 'FAILED to download apks for $1'; exit 1" EXIT

set -eu

# Pull binaries down, then make sure we got an archive and not a error
# page
echo "Downloading arm7 for $1"
curl -sSO https://ftp.mozilla.org/pub/mozilla.org/mobile/candidates/$1-candidates/build1/android/multi/fennec-$1.multi.android-arm.apk
file fennec-$1.multi.android-arm.apk | grep 'Zip archive'
echo "Downloading arm6 for $1"
curl -sSO https://ftp.mozilla.org/pub/mozilla.org/mobile/candidates/$1-candidates/build1/android-armv6/multi/fennec-$1.multi.android-arm-armv6.apk
file fennec-$1.multi.android-arm-armv6.apk | grep 'Zip archive'
trap "" EXIT
echo "Success! both downloaded and appear to be Zip archives"
