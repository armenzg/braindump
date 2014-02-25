#!/bin/bash

USAGE="usage: ${0##*/} hosts...
Return the Mac model number for each host"

# adapted from
# http://apple.stackexchange.com/questions/98080/can-a-macs-model-year-be-determined-via-terminal-command
# use MacTracker to interpret model numbers: http://mactracker.ca/

warn() { for m; do echo "$m" ; done 1>&2 ; }
die() { warn "$@"; exit 1 ; }
usage() { warn "$@" "${USAGE:-}" ; test $# -eq 0 ; exit $? ; }

while test $# -gt 0; do
    case "$1" in
        -h|--help) usage ;;
    -*) usage "unknown option '$1'" ;;
*) break ;;
    esac
    shift
done

test $# -eq 0 && usage "Missing host names"

for host in "$@"; do

    ssh 2>/dev/null $host \
        system_profiler SPHardwareDataType \
    | awk '/Identifier:/ {printf "%s", $3}'
    echo " for $host"
done
