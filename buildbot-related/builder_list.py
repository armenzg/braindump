#!/usr/bin/python
import sys, os, re

g = {}

sys.path.append(os.path.abspath(os.path.dirname(sys.argv[1])))
os.chdir(os.path.dirname(sys.argv[1]))
execfile(os.path.basename(sys.argv[1]), g)

for b in g['c']['builders']:
    print b['name'], b['factory'].__class__.__name__
    for s in b['factory'].steps:
        step_class, args = s
        args = re.sub(' (instance )?at 0x[0-9a-f]+>', '>', str(args))
        print "   ", step_class.__name__, args
