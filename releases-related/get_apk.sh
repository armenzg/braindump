#!/bin/bash

warn() { for m; do echo "$m"; done 1>&2 ; }
die() { warn "$@"; exit 1; }
usage() { warn "$@" "${USAGE:-}" ; test $# -eq 0; exit $?; }

test -n "${1:-}" || usage "Missing build nuber"

set -eux

# Pull binaries down, then make sure we got an archive and not a error
# page
curl -O https://ftp.mozilla.org/pub/mozilla.org/mobile/candidates/$1-candidates/build1/android/multi/fennec-$1.multi.android-arm.apk
file fennec-$1.multi.android-arm.apk | grep 'Zip archive'
curl -O https://ftp.mozilla.org/pub/mozilla.org/mobile/candidates/$1-candidates/build1/android-armv6/multi/fennec-$1.multi.android-arm-armv6.apk
file fennec-$1.multi.android-arm-armv6.apk | grep 'Zip archive'
echo "Success! both downloaded and appear to be Zip archives"
