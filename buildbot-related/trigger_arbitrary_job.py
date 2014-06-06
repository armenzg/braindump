#! /usr/bin/env python
# This script is designed to trigger a job arbitrarily
# http://johnzeller.com/blog/2014/03/12/triggering-of-arbitrary-buildstests-is-now-possible/
#
# KNOWN ISSUES:
# * tbpl/self-serve will not show up your job running - bug 981825
#
# SETUP:
# * Install requests
# * Add your credentials to ~/.netrc
#
# .NETRC:
# * Place it under $HOME with this format (one line):
# machine secure.pub.build.mozilla.org login your_email password your_pswd
import json
import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--buildername', dest='buildername', required=True)
parser.add_argument('--branch', dest='branch', required=True)
parser.add_argument('--rev', dest='revision', required=True)
parser.add_argument('--file', dest='files', action='append')
args = parser.parse_args()

branch = args.branch
revision = args.revision
buildername = args.buildername
files = args.files or []

def all_files_are_reachable(files):
    ''' All files should be reachable or requirying basic http authentication
    '''
    reachable_files = True
    for file in files:
        r = requests.head(file)
        if r.status_code != 200 and r.status_code != 401:
            # 401 files to us can be reachable within the releng network
            print "Status code: %d - The following files cannot be reached: %s" \
                    % (r.status_code, file)
            reachable_files = False

    return reachable_files

assert all_files_are_reachable(files), "All files should be reachable"

# Check that files is either 0 (build job) or 2 (test job: installer + tests.zip)
# XXX: Talos might be one file, I'm not sure
assert len(files) != 1, "You can either have no files or two files specified"
assert len(files) <= 2, "You have specified more than 2 files"

payload = {}
# Adding the properties here is so tbpl can show the job as they run
payload['properties'] = json.dumps({"branch": branch, "revision": revision})
payload['files'] = json.dumps(files)

url = r'''https://secure.pub.build.mozilla.org/buildapi/self-serve/%s/builders/%s/%s''' % \
        (branch, buildername, revision)
r = requests.post(url, data=payload)

print "You return code is: %s" % r.status_code
print "See your running jobs in here:"
print "https://secure.pub.build.mozilla.org/buildapi/revision/%s/%s" % (branch, revision)
