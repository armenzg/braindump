# /usr/bin/env python2.7

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import argparse
import urllib2
import json
import StringIO
import gzip

__version__ = "1.3"

pending_url = 'https://secure.pub.build.mozilla.org/builddata/buildjson/builds-pending.js'
allthethings_url = 'https://secure.pub.build.mozilla.org/builddata/reports/allthethings.json.gz'
status_code = {'OK': 0, 'WARNING': 1, "CRITICAL": 2, "UNKNOWN": 3}


def get_allthethings_json():
    response = urllib2.urlopen(allthethings_url, timeout=30)
    compressed_data = StringIO.StringIO(response.read())
    decompressed_data = gzip.GzipFile(fileobj=compressed_data)
    return json.load(decompressed_data)


# get the pending builds and their count
def get_pending_builds():
    pending_builds = {}
    response = urllib2.urlopen(pending_url, timeout=30)
    result = json.loads(response.read())
    for branch in result['pending'].keys():
        for revision in result['pending'][branch].keys():
            for request in result['pending'][branch][revision]:
                k = request['buildername']
                if k in pending_builds.keys():
                    pending_builds[k] += 1
                else:
                    pending_builds[k] = 1
    return pending_builds


# get the builder names and their corresponding slavepools
def get_builders_and_slavepools(allthethings_json):
    builders_and_slavepools = []
    slavepool_cache = {}
    for builder_name in allthethings_json['builders'].keys():
        slavepool_id = allthethings_json['builders'][builder_name]['slavepool']
        pools = []
        if slavepool_id in slavepool_cache:
            pools = slavepool_cache[slavepool_id]
        else:
            slavepool = allthethings_json['slavepools'][slavepool_id]
            for s in slavepool:
                if s[:s.rfind('-')] not in pools:
                    pools.append(s[:s.rfind('-')])
            slavepool_cache[slavepool_id] = pools
        if not pools:
            builders_and_slavepools.append([builder_name, 'None'])
        else:
            for i in range(0, len(pools)):
                pools[i] = str(pools[i])
            builders_and_slavepools.append([builder_name, pools])
    return builders_and_slavepools


# get the slavepools
def get_slavepools(builders_and_slavepools):
    slavepools = []
    for j in range(0, len(builders_and_slavepools)):
        duplicate = 0
        for k in range (0,j):
            if builders_and_slavepools[j][1] == builders_and_slavepools[k][1]:
                duplicate = 1
                break
        if duplicate == 0:
            slavepools.append([builders_and_slavepools[j][1]])
    return slavepools


# compute the number of pending builds by slavepool
def get_count_by_slavepool(pending_builds, builders_and_slavepools, slavepools):
    count_by_slavepool = []
    for m in range(0, len(slavepools)):
        count_by_slavepool.append([slavepools[m][0], 0])
    for i,j in pending_builds.iteritems():
        for k in range(0, len(builders_and_slavepools)):
            if i == builders_and_slavepools[k][0]:
                for m in range(0, len(count_by_slavepool)):
                    if builders_and_slavepools[k][1] == slavepools[m][0]:
                        count_by_slavepool[m][1] += j
    top_count_by_slavepool = sorted(count_by_slavepool, key=lambda list: list[1], reverse=True)
    return top_count_by_slavepool


def pending_builds_status(pending, critical_threshold, warning_threshold):
    if pending >= critical_threshold:
        return 'CRITICAL'
    elif pending >= warning_threshold:
        return 'WARNING'
    else:
        return 'OK'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(version="%(prog)s " + __version__)
    parser.add_argument(
        '-c', '--critical', action='store', type=int, dest='critical_threshold', default=2000, metavar="CRITICAL",
        help='Set CRITICAL level as integer eg. 2000')
    parser.add_argument(
        '-w', '--warning', action='store', type=int, dest='warning_threshold', default=1200, metavar="WARNING",
        help='Set WARNING level as integer eg. 1200')
    args = parser.parse_args()

    try:
        allthethings_json = get_allthethings_json()
        pending_builds = get_pending_builds()
        builders_and_slavepools = get_builders_and_slavepools(allthethings_json)
        slavepools = get_slavepools(builders_and_slavepools)
        top_count_by_slavepool = get_count_by_slavepool(pending_builds, builders_and_slavepools, slavepools)
        status = pending_builds_status(
            top_count_by_slavepool[0][1], args.critical_threshold, args.warning_threshold)
        output = '%s Pending Jobs: %i' % (status, top_count_by_slavepool[0][1])
        if top_count_by_slavepool[0][1] > 0:
            output += " on %s" % top_count_by_slavepool[0][0]
        print output
        sys.exit(status_code[status])
    except Exception as e:
        print e
        sys.exit(status_code.get('UNKNOWN'))

