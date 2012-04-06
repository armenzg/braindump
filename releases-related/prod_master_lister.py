#!/usr/bin/env python

# From Aki, modified to take file on command line and filter from
# environment

# TODO: add proper command line parsing & help
# TODO: add unit tests
# TODO: add pull from repo tip if not otherwise found

try:
    import simplejson as json
except ImportError:
    import json

import os, sys

if len(sys.argv) == 2:
    pm = sys.argv[1]
else:
    pm = "build-tools/buildfarm/maintenance/production-masters.json"

if not os.path.exists(pm):
    # TODO mercurial update?
    pm = "/src/clean/build-tools/buildfarm/maintenance/production-masters.json"

fh = open(pm)
contents = json.load(fh)
fh.close()

just_this_role = os.environ.get('JUST_ROLE', None)
if just_this_role:
    these_roles = (just_this_role,)
else:
    these_roles = ("scheduler", "build", "tests", "try")

for role in these_roles:
    print """
#################
# %s
#################
""" % role
    for d in contents:
        if d.get("enabled") and d.get("environment") == "production" and d.get("role") == role:
            print "http://%s:%d" % (d["hostname"], d.get("http_port", d['pb_port']))
