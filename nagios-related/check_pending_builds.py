import sys
import argparse
import urllib2
import json

__version__ = "1.1"

pending_url = 'https://secure.pub.build.mozilla.org/builddata/buildjson/builds-pending.js'
all_things_url = 'https://secure.pub.build.mozilla.org/builddata/reports/allthethings.json'
status_code = {'OK': 0, 'WARNING': 1, "CRITICAL": 2, "UNKNOWN": 3}
pending_builds = []
builds_platform = []
platforms = []
platforms_count = []


def get_num_pending_builds():
    response = urllib2.urlopen(pending_url)
    result = json.loads(response.read())
    num_pending = 0
    for key in result['pending'].keys():
        for k1 in result['pending'][key].keys():
            for k2 in range (0, (len(result['pending'][key][k1]))):
                 pending_builds.append(result['pending'][key][k1][k2]['buildername'])
            num_pending += len(result['pending'][key][k1])
    return num_pending


def get_builder_and_platform():
    response = urllib2.urlopen(all_things_url)
    result = json.loads(response.read())
    for key in result['builders'].keys():
        if result['builders'][key]['properties']['platform'] is None:
            builds_platform.append([key, 'None'])
        else:
            builds_platform.append([key, (result['builders'][key]['properties']['platform']).encode('utf-8')])
    num_builders = len(result['builders'])
    return num_builders


def get_platforms(num_builders):
    for j in range(0, num_builders):
        if builds_platform[j][1].find('-debug') != -1:
            builds_platform[j][1] = builds_platform[j][1].replace('-debug', '')
    for j in range(0, num_builders):
        duplicate = 0
        for k in range (0,j):
            if builds_platform[j][1] == builds_platform[k][1]:
                duplicate = 1
                break
        if duplicate == 0:
            platforms.append([builds_platform[j][1]])
    return platforms


def get_builders_by_platform(num_pending, num_builders, platforms):
    for m in range(0, len(platforms)):
        platforms_count.append([platforms[m][0], 0])
    for i in range(0, num_pending):
        for j in range(0, num_builders):
            if pending_builds[i] == builds_platform[j][0]:
                for m in range(0, len(platforms_count)):
                    if builds_platform[j][1] == platforms[m][0]:
                        platforms_count[m][1] = platforms_count[m][1] + 1
    return platforms_count


def sort_builders_by_platform(platforms_count):
    swapped = True
    while swapped:
        swapped = False
        for m in range(0, (len(platforms_count) - 1)):
            if platforms_count[m][1] < platforms_count[m+1][1]:
                swapped = True
                aux0 = platforms_count[m][0]
                aux1 = platforms_count[m][1]
                platforms_count[m][0] = platforms_count[m + 1][0]
                platforms_count[m][1] = platforms_count[m + 1][1]
                platforms_count[m + 1][0] = aux0
                platforms_count[m + 1][1] = aux1
    return platforms_count


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
        num_pending = get_num_pending_builds()
        num_builders = get_builder_and_platform()
        list_platforms = get_platforms(num_builders)
        list_platforms_count = get_builders_by_platform(num_pending, num_builders, list_platforms)
        list_sort_builders_by_platform = sort_builders_by_platform(list_platforms_count)
        status = pending_builds_status(
        list_sort_builders_by_platform[0][1], args.critical_threshold, args.warning_threshold)
        print '%s Pending Builds: %i' % (status, list_sort_builders_by_platform[0][1]),\
            "on '%s'" % list_sort_builders_by_platform[0][0]
        print 'Top Builds by Platform:'
        for k in range(0, len(list_sort_builders_by_platform)):
            if k < 3:
                print list_sort_builders_by_platform[k][0], '-->', list_sort_builders_by_platform[k][1]
        sys.exit(status_code[status])
    except Exception as e:
        print e
        sys.exit(status_code.get('UNKNOWN'))

