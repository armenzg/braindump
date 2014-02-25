#!/usr/bin/env python
import sys
import os
import json
import time

combo_count = 0
start_time = time.time()

def addSlaveCombination(slave_list):
    global combo_count;
    combo_count += 1
    newpool = '%s_combination%d' % (prefix, combo_count)
    pools[newpool] = {
        'slaves': slave_list,
        'builders': []
    }
    for s in slave_list:
        slaves.setdefault(s, []).append(newpool)
    return newpool

def identifyPool(pools, slaves):
    pool = 'unknown' 
    for pool in pools:
        if set(slaves) == set(pools[pool]['slaves']):
            return pool
    # we've hit some new combination
    newpool = addSlaveCombination(slaves)
    return newpool

# usage 
# python .../builder_slaves.py <master_dir>
# write <master_dir>/master_dump.py
# run sequentially then call combine.py

# TODO read from argv properly
prefix = sys.argv[1]
if not prefix:
    print 'whoop! no prefix given'
    sys.exit(1)
if not os.path.isdir(prefix):
    print '%s is not a directory' % prefix
    sys.exit(1)
    
# exec the master to generate buildbot objects    
g = {}
abspath = os.path.abspath(prefix)
sys.path.append(abspath)
os.chdir(abspath)
execfile('master.cfg', g)
mid_time = time.time()

# remove empty pools
for pool in g['SLAVES'].keys():
    if g['SLAVES'][pool] == []:
        print "whoop! %s has no slaves, deleting" % pool
        del(g['SLAVES'][pool])
        continue

# check for duplicates pools, eg in test land
pools = g['SLAVES'].keys()
kaput = []
for i in range(1, len(pools)):
    for j in range(i+1, len(pools)):
        if set(g['SLAVES'][pools[i]]) == set(g['SLAVES'][pools[j]]):
            kaput.append(sorted([pools[i], pools[j]])[-1])
            print "whoop! %s is the same slaves as %s, deleting %s" % (pools[i], pools[j], kaput[-1])
for k in kaput:
    if k in g['SLAVES']:
        del(g['SLAVES'][k])

# build up dicts of pools and slaves (and the pools they belong to)
pools = {}
slaves = {}
for pool in g['SLAVES'].keys():
    newpool = '%s_%s' % (prefix, pool)
    pools[newpool] = {
        'slaves': g['SLAVES'][pool],
        'builders': []
    }
    for s in g['SLAVES'][pool]:
        slaves.setdefault(s, []).append(newpool)

# build up a list of builders, and builders for a pool
builders = {}
for b in g['c']['builders']:
    pool = identifyPool(pools, b['slavenames'])
    builders[b['name']] = pool
    pools[pool]['builders'].append(b['name'])

# tidy up sorting
for pool in pools:
    pools[pool]['slaves'] = sorted(pools[pool]['slaves'])
    pools[pool]['builders'] = sorted(pools[pool]['builders'])
# sorted unique values
for s in slaves:
    slaves[s] = sorted(list(set(slaves[s])))


# write out some info for the all powerful machines
output = {
    'builders': builders,
    'slaves': slaves,
    'schedulers': {},    # TODO
    'pools': pools,
}

f = open('master_dump.json.tmp', 'w')
json.dump(output, f, indent=4, sort_keys=True)
f.close()
os.rename('master_dump.json.tmp', 'master_dump.json')

end_time = time.time()
print "total: %1.1fs, loading master: %1.1fs, processing: %1.1fs" % (end_time-start_time, mid_time-start_time, end_time-mid_time)