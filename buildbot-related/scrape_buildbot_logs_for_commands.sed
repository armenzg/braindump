#!/usr/bin/env sed -nf
#
# This script will strip out all the commands from a buildbot slave log, and the directories
# the commands were run from, and generate a bash script from it.
#
# For example, you can use this script like this:
#     curl -L 'http://ftp.mozilla.org/pub/mozilla.org/mobile/candidates/31.1.0esr-candidates/build1/logs/release-mozilla-esr31-android-armv6_build-bm85-build1-build0.txt.gz' 2>/dev/null | gunzip | ./scrape_buildbot_logs_for_commands.sed > all_commands.sh

1a\
#!/bin/bash
/^ in dir /{
    s/^ in dir \(.*\)(timeout.*)/cd \1/
    p
    x
    p
}
/^ in dir /!x
