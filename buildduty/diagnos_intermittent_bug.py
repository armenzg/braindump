#!/usr/bin/env python

import optparse
import sys
import re
import datetime

from pprint import pprint

try:
    from bs4 import BeautifulSoup
    import requests
except ImportError, e:
    sys.exit("This script depends on two packages that should be built in to python: "
             "'BeautifulSoup' and 'requests' Please create a virtualenv and/or "
             "'pip install beautifulsoup4 requests'")


def get_source(bug):
    return requests.get("https://bugzil.la/{number}".format(number=bug)).text


def get_tbpl_comments(soup):
    comments = soup.find_all(class_='bz_comment')
    return [comment for comment in comments if 'TBPL Robot' in str(comment.find(class_='vcard'))]


def get_failed_details(tbpl_comments):
    failed_jobs = []
    categories = dict(builder='buildname: (.*)',
                      slave='machine: (.*)',
                      repo='repository: (.*)',
                      revision='revision: (.*)',
                      time='(submit_timestamp|time): (.*)')

    for comment in tbpl_comments:
        text = comment.find(class_='bz_comment_text')
        failed_job = {}
        for key, val in categories.iteritems():
            match = re.search(val, str(text))
            if match:
                if match.groups()[-1] == None:
                    x = 5
                failed_job[key] = match.groups()[-1]
        failed_jobs.append(failed_job)

    return failed_jobs


def get_counts(failed_jobs, category):
    counts = {}
    unique_vals = set(job.get(category) for job in failed_jobs if job.get(category))

    for val in unique_vals:
        counts[val] = sum(1 for job in failed_jobs if job.get(category) == val)

    return counts


def get_times(failed_jobs):
    times = []
    unique_days = set()
    counts = {}
    for job in failed_jobs:
        if job.get('time'):
            times.append(datetime.datetime.strptime(job['time'], "%Y-%m-%dT%H:%M:%S"))

    for time in times:
        unique_days.add(time.date())

    for day in unique_days:
        counts[str(day)] = sum(1 for time in times if time.date() == day)

    return counts


if __name__ == "__main__":
    parser = optparse.OptionParser()
    # TODO - add option to dump output back into bug or save to file
    # no options yet
    (opts, args) = parser.parse_args()
    if len(args) != 1:
        sys.exit("you must supply one argument: the bug number")
    bug = args[0]

    html = get_source(bug)
    # make some soup
    soup = BeautifulSoup(html)

    tbpl_comments = get_tbpl_comments(soup)
    failed_jobs = get_failed_details(tbpl_comments)

    totals = {
        'slave_counts': get_counts(failed_jobs, 'slave'),
        'builder_counts': get_counts(failed_jobs, 'builder'),
        'repo_counts': get_counts(failed_jobs, 'repo'),
        'revision_counts': get_counts(failed_jobs, 'revision'),
        'time_counts': get_times(failed_jobs),
    }

    pprint(totals)
