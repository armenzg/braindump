#!/usr/bin/env python

import sys
import argparse
import urllib2
import json

__version__ = "1.0"

pending_url = 'https://secure.pub.build.mozilla.org/builddata/buildjson/builds-pending.js'
status_code = {'OK': 0, 'WARNING': 1, "CRITICAL": 2, "UNKNOWN": 3}


def get_num_pending_builds():
    response = urllib2.urlopen(pending_url)
    result = json.loads(response.read())
    num_pending = 0
    for key in result['pending'].keys():
        for k in result['pending'][key].keys():
            num_pending += len(result['pending'][key][k])
    return num_pending


def pending_builds_status(num_pending, critical_threshold, warning_threshold):
    if num_pending >= critical_threshold:
        return 'CRITICAL'
    elif num_pending >= warning_threshold:
        return 'WARNING'
    else:
        return 'OK'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(version="%(prog)s " + __version__)
    parser.add_argument(
        '-c', '--critical', action='store', type=int, dest='critical_threshold', default=5000, metavar="CRITICAL",
        help='Set CRITICAL level as integer eg. 5000')
    parser.add_argument(
        '-w', '--warning', action='store', type=int, dest='warning_threshold', default=2000, metavar="WARNING",
        help='Set WARNING level as integer eg. 2000')
    args = parser.parse_args()

    try:
        num_pending = get_num_pending_builds()
        status = pending_builds_status(
            num_pending, args.critical_threshold, args.warning_threshold)
        print '%s Pending Builds: %i' % (status, num_pending)
        sys.exit(status_code[status])
    except Exception as e:
        print e
        sys.exit(status_code.get('UNKNOWN'))
