#!/usr/bin/env python2

from collections import defaultdict
import logging
import json
import os
from os import path
import sys

d = sys.argv[1]

allocated = set()
builders = defaultdict(set)
machines = defaultdict(set)

allocated.update(json.load(open(path.join(d, "allocated", "all")))["machines"])

for m in os.listdir(path.join(d, "machines")):
    for b in json.load(open(path.join(d, "machines", m)))["builders"]:
        machines[m].add(b)
        
for b in os.listdir(path.join(d, "builders")):
    for m in json.load(open(path.join(d, "builders", b)))["machines"]:
        builders[b].add(m)

    # Verify that every the builder allocations match the machines'.
    builder_machines = set()
    for m in machines:
        if b in machines[m]:
            builder_machines.add(m)
    if builders[b] != builder_machines:
        logging.warning("Mismatch in builder machines for %s: %s", b, sorted(builders[b].difference(builder_machines)))

# Verify that machine allocations match the builders', and also obey our other constraints
for m in machines:
    machine_builders = set()
    for b in builders:
        if m in builders[b]:
            machine_builders.add(b)
    if machines[m] != machine_builders:
        logging.warning("Mismatch in machine builders for %s: %s", m, sorted(machines[m].difference(machine_builders)))
    for b in machine_builders:
        if "l10n" not in b:
            break
    else:
        logging.warning("%s only has l10n builders configured", m)
    if len(machine_builders) > 2:
        logging.warning("%s has more than 2 builders", m)

# And verify that all of the machines in machines/ are listed in the list of allocated machines
all_machines = set(machines.keys())
if allocated != all_machines:
    logging.warning("Mismatch in allocated/all vs. machines/*: %s, %s", sorted(allocated.difference(all_machines)), sorted(all_machines.difference(allocated)))

for m in sorted(machines):
    print "%s is allocated to %s builders" % (m, len(machines[m]))

for b in sorted(builders):
    print "%s has %s machines allocated to it" % (b, len(builders[b]))
