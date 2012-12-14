#!/usr/bin/python
import sys, os, re

def format_args(args):
    keys = sorted(args.keys())
    if 'lazylogfiles' in keys:
        keys.remove('lazylogfiles')
    retval = []
    for k in keys:
        v = repr(args[k])
        v = re.sub(' (instance )?at 0x[0-9a-f]+>', '>', v)
        retval.append("'%s': %s" % (k, v))
    return "{" + ", ".join(retval) + "}"

g = {}

abspath = os.path.abspath(os.path.dirname(sys.argv[1]))
sys.path.append(abspath)
os.chdir(abspath)
execfile(os.path.basename(sys.argv[1]), g)

for b in g['c']['builders']:
    print b['name'], b['factory'].__class__.__name__
    '''
    for s in b['factory'].steps:
        step_class, args = s
        #args = re.sub(' (instance )?at 0x[0-9a-f]+>', '>', str(args))
        args = format_args(args)
        print "   ", step_class.__name__, args
    '''
