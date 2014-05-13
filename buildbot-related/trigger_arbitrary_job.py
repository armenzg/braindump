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
parser.add_argument('--buildername', dest='buildername')
parser.add_argument('--rev', dest='revision')
parser.add_argument('--branch', dest='branch')
parser.add_argument('--file', dest='files', action='append')
args = parser.parse_args()

revision = args.revision
buildername = args.buildername
branch = args.branch

payload = {}
# Adding the properties here are to allow tbpl to show the job
# as they're running
# Currently broken - bug 981825
payload['properties'] = json.dumps({"branch": branch, "revision": revision})
payload['files'] = json.dumps(args.files)

url = r'''https://secure.pub.build.mozilla.org/buildapi/self-serve/%s/builders/%s/%s''' % \
        (branch, buildername, revision)
r = requests.post(url, data=payload)
print r.status_code
# We can't yet see the jobs - bug 981825
#print "See your running jobs in here:"
#print "https://secure.pub.build.mozilla.org/buildapi/revision/%s-selfserve/%s" % (branch, revision)
