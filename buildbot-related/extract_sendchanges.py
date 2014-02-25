#!/usr/bin/env python
"""Dumps out a mapping of builders and the sendchanges that they do from dump_master.py output."""

from collections import defaultdict
import sys
import json
import re

sendchanges = defaultdict(list)
currentBuilder = None

branchRe = re.compile("'branch': '([\w-]*)'")

for line in open(sys.argv[1]).readlines():
    line = line.rstrip()
    if line.startswith('Change sources:'):
        break
    if not line.startswith(' '):
        currentBuilder = ' '.join(line.split(' ')[:-1])
        continue
    if 'SendChangeStep' not in line:
        continue
    # we have a sendchange!
    try:
        m = branchRe.search(line)
        sendchanges[currentBuilder] = m.groups()[0]
    except:
        print "Couldn't find branch in %s" % line

print json.dumps(sendchanges)
