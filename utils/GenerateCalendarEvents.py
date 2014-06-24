#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Read the copy/paste output of new rows in the release duty spreadsheet.

Output a series of events in media wiki format.
"""

import csv
from datetime import datetime
import sys
import argparse

# formatted for legibility
event_template = ' '.join([
    '* <div id="{event_id}" class="vevent">',
    '<time class="dtstart" datetime="{start_iso}">{start_h}</time> &rarr;',
    '<time class="dtend" datetime="{finish_iso}">{finish_h}</time>',
    '<span class="summary">{driver} {release}</span><br />',
    '<span class="description">{comments}',
    '{bug_url_span}',
    'Build&nbsp;Notes:&nbsp;<span class="url">{build_notes_url}</span>',
    '</span>',
    '</div>',
])

field_list = ('release', 'start', 'driver', 'finish', 'formatted notes',
              'comments', 'bug url', 'bugid')

in_file = '/tmp/calendar.in'
product_name = {
    'FX': 'Firefox',
    'TB': 'Thunderbird',
}
build_notes_url_template = \
    'https://wiki.mozilla.org/Releases/{product}_{release}/BuildNotes'
bug_ref_template = '{{bug|%s}}; '
bug_url_span_template = 'Bug:&nbsp;<span class="url">{bug_url}</span>'


def get_bug_url_span(bug_url):
    ref = ''
    if bug_url:
        ref = bug_url_span_template.format(bug_url=bug_url)
    return ref


def get_bug_ref(bug_number):
    ref = ''
    if bug_number:
        ref = bug_ref_template % bug_number
    return ref


def get_build_notes_url(release):
    product, release_id = release.split(' ', 1)
    try:
        prod_name = product_name[product.upper()]
        release = release_id.replace(' ', '').lower()
        url = build_notes_url_template.format(product=prod_name,
                                              release=release)
    except KeyError:
        raise SystemExit("unknown product abbreviation %s" % product)
    return url


def convert_files(file_name=None):
    if file_name is None or len(file_name) == 0:
        csv_file = sys.stdin
    else:
        csv_file = open(file_name, 'rb')
    csv.register_dialect('tab_delim', delimiter="\t",
                         quoting=csv.QUOTE_NONE)
    reader = csv.DictReader(csv_file, field_list, dialect='tab_delim')
    for d in reader:
        try:
            start = datetime.strptime(d['start'], '%m/%d/%Y')
            finish = datetime.strptime(d['finish'], '%m/%d/%Y')
            d.update({'bug ref': get_bug_ref(d['bugid']),
                      'bug_url_span': get_bug_url_span(d['bug url']),
                      'build_notes_url': get_build_notes_url(d['release']),
                      'event_id': "%s%s" % (d['release'].replace(' ', ''),
                                            d['driver']),
                      'start_h': start.strftime('%a %b %d'),
                      'start_iso': start.isoformat()[0:10],
                      'finish_h': finish.strftime('%a %b %d'),
                      'finish_iso': finish.isoformat()[0:10], })
            print event_template.format(**d)
        except ValueError as e:
            # assume bad line - get them on at least osx
            print >> sys.stderr, "Skipped line %d %s" % (reader.line_num, e)
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', metavar='FILE', nargs='?',
                        help='Tab separated copy/paste from google doc')
    args = parser.parse_args()
    convert_files(args.files)


if __name__ == "__main__":
    main()
