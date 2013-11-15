#!/usr/bin/env python
'''Find master(s) which have run a particluar builder.

In the multi-master world, it's not easy to find a master which has run a
little used builder. This automates that search.
'''
try:
    import simplejson as json
except ImportError:
    import json
import argparse
import urllib
import urllib2
import logging

log = logging.getLogger(__name__)


def check_masters(masters, find_only_one, builder_name):
    for master in masters:
        master['builder'] = builder_name
        found = check_master(master)
        if found and find_only_one:
            return


def load_masters(url):
    if 'http' in url:
        fp = urllib.urlopen(url)
    else:
        fp = open(url)
    return json.load(fp)


def check_master(master):
    found = False
    try:
        if master['enabled'] and master['environment'] == 'production':
            pattern = \
                "http://{hostname}:{http_port}/builders/{builder}/builds/0"
            url = pattern.format(**master)
            request = urllib2.Request(url)
            request.get_method = lambda: 'HEAD'
            response = urllib2.urlopen(request)
            if response.code == 200:
                found = True
                print(response.url)
    except urllib2.URLError as e:
        if e.code == 404:
            # just a not found, that's okay
            pass
        log.debug(e.code)
    except Exception as e:
        # something else -- still means not found
        log.debug(e)
    return found


def main():
    logging.basicConfig()
    parser = argparse.ArgumentParser(description=__doc__,
                                     usage='%(prog)s [options] builder-name')

    parser.add_argument('--masters', '-m',
                        default='http://hg.mozilla.org/build/tools/raw-file/default/buildfarm/maintenance/production-masters.json',
                        dest='masters_json',
                        help='URL or path to json file')
    parser.add_argument('--one-only', '-o',
                        default=False,
                        dest='one_only',
                        action='store_true',
                        help='stop after finding one master')

    parser.add_argument('builder', help='name of builder to check for')
    options = parser.parse_args()

    masters = load_masters(options.masters_json)
    check_masters(masters, options.one_only, options.builder)

if __name__ == '__main__':
    main()
