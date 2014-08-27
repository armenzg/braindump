#!/usr/bin/env python

from os import path, walk
import sys

dir_ = sys.argv[1]


created_dirs = set()

instructions = []

def add_mkdir(d):
    start, end = path.split(d)
    if start:
        add_mkdir(start)

    if d not in created_dirs:
        instructions.append("mkdir \"%s\"" % d)
        created_dirs.add(d)

for top, dirs, files in walk(dir_):
    for f in files:
        if f.endswith(".dmg"):
            add_mkdir(top)
            instructions.append("put \"%s\" \"%s\"" % (path.join(top, f), top))

print "\n".join(instructions)
