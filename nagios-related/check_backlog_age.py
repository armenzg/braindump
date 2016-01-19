#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import urllib2
import json
import time

from optparse import OptionParser

__version__ = "1.0"
submitted_at = []
pending_url = 'https://secure.pub.build.mozilla.org/builddata/buildjson/builds-pending.js'
status_code = {'OK': 0, 'WARNING': 1, "CRITICAL": 2, "UNKNOWN": 3}


# Get the current unix timestamp
def get_unix_time():
    k = int(time.time())
    return k


# Get the earliest 'submitted_at' value
def get_min_submitted_at():
    response = urllib2.urlopen(pending_url)
    result = json.loads(response.read())
    for branch in result['pending'].keys():
        for revision in result['pending'][branch].keys():
            for request in result['pending'][branch][revision]:
                submitted_at.append(request['submitted_at'])
    return min(submitted_at)


# Convert a unix timestamp to a readable value
def get_unix_to_readable(unix_time):
    m, s = divmod(unix_time, 60)
    h, m = divmod(m, 60)
    readable_time = "%dh:%02dm:%02ds" % (h, m, s)
    return readable_time


def pending_builds_status(waiting_time, critical_threshold, warning_threshold):
    if waiting_time >= critical_threshold:
        return 'CRITICAL'
    elif waiting_time >= warning_threshold:
        return 'WARNING'
    else:
        return 'OK'

if __name__ == '__main__':
    parser = OptionParser(version="%(prog)s " + __version__)
    parser.add_option(
        '-c', '--critical', action='store', type=int, dest='critical_threshold', default=43200, metavar="CRITICAL",
        help='Set CRITICAL level as integer eg. 43200')
    parser.add_option(
        '-w', '--warning', action='store', type=int, dest='warning_threshold', default=21600, metavar="WARNING",
        help='Set WARNING level as integer eg. 21600')
    (option, args) = parser.parse_args()

    try:
        unix_time = get_unix_time()
        min_submitted_at = get_min_submitted_at()
        waiting_time = unix_time - min_submitted_at
        status = pending_builds_status(waiting_time, option.critical_threshold, option.warning_threshold)
        time = get_unix_to_readable(waiting_time)
        print '%s Backlog Age: %s' % (status, time)
        sys.exit(status_code[status])
    except Exception as e:
        print e
        sys.exit(status_code.get('UNKNOWN'))
		