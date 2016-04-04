# A fairly dumb script that compares a release blob from Balrog with
# a SHA512SUMS file, to make sure the hashes all match. You need both
# of those things on disk already.
# 
# usage: python compare-balrog-sha512sums.py <balrog.json> <sha512sums>

from collections import defaultdict 
import json
import sys

# read json
j = json.load(open(sys.argv[1]))
hashes_json = defaultdict(list)
for p, pdata in j["platforms"].iteritems():
    if "alias" in pdata:
        continue
    for l, ldata in pdata["locales"].iteritems():
        for update_type in ('partials', 'completes'):
            for update in ldata.get(update_type):
                hashes_json[update["hashValue"]] = \
                   "%s/%s/%s/%s" % (p, l, update_type, update["from"])

# read hashes
hashes_sumsfile = defaultdict(list)
for l in open(sys.argv[2]).readlines():
     hash, fullpath = l.strip().split(' ', 1)
     if fullpath.endswith('.mar'):
         hashes_sumsfile[hash].append(fullpath)

# look for differences
print "Hashes only found in Balrog" 
output = []
for hit in set(hashes_json.keys()) - set(hashes_sumsfile.keys()):
    if hit in hashes_json:
        output.append("%-80s %s" % (hashes_json[hit], hit))
if output:
    print "\n".join(sorted(output))
else:
    print "None"

print "\nHashes only found in SHA512SUMS"
output = []
for hit in set(hashes_sumsfile.keys()) - set(hashes_json.keys()):
    if hit in hashes_sumsfile:
        output.append("%-80s %s" % (hashes_sumsfile[hit], hit))
if output:
    print "\n".join(sorted(output))
else:
    print "None"
