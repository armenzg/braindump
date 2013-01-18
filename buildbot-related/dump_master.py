#!/usr/bin/env python
import sys, os, re, pprint, StringIO

# WithProperties does a poor job at representing itself for our uses here
from buildbot.process.properties import WithProperties

sio = StringIO.StringIO()
ppio = pprint.PrettyPrinter(stream=sio)

def reprWithProp(self):
    if (self.__class__ == WithProperties):
      classname = "WithProperties"
    else:
      classname = self.__class__.__name__
    return "<%s \"%s\">" % (classname, self.fmtstring)

WithProperties.__repr__ = reprWithProp

def format_args(args):
    keys = sorted(args.keys())
    if 'lazylogfiles' in keys:
        keys.remove('lazylogfiles')
    retval = []
    for k in sorted(keys):
        v = ppio.pformat(args[k])
        v = re.sub('\n', ' ', v) # Cleanup pprint newlines
        v = re.sub(' (instance )?at 0x[0-9a-f]+>', '>', v)
        retval.append("'%s': %s" % (k, v))
    return "{" + ", ".join(retval) + "}"

def format_objs(*args):
    retval = []
    for a in args:
        s = pprint.pformat(a)
        s = re.sub(' (instance )?at 0x[0-9a-f]+>', '>', s)
        retval.append(s)
    return " ".join(retval)

g = {}

abspath = os.path.abspath(os.path.dirname(sys.argv[1]))
sys.path.append(abspath)
os.chdir(abspath)
execfile(os.path.basename(sys.argv[1]), g)

def sort_builders(b1, b2):
    if b1['name'] < b2['name']:
        return -1
    elif b1['name'] > b2['name']:
        return 1
    else:
        return 0

print "Builders:"
for b in sorted(g['c']['builders'], cmp=sort_builders):
    print b['name'], b['factory'].__class__.__name__
    for s in b['factory'].steps:
        step_class, args = s
        args = format_args(args)
        print "   ", step_class.__name__, args, b.get('env', {})
print

print "Change sources:"
for c in g['c']['change_source']:
    d = {}
    if hasattr(c, 'compare_attrs'):
        for a in c.compare_attrs:
            d[a] = getattr(c, a)
    if hasattr(c, '_make_url'):
        print format_objs(c, c._make_url(), d)
    else:
        print format_objs(c, d)
print

print "Schedulers:"
for s in g['c']['schedulers']:
    d = {}
    if hasattr(s, 'compare_attrs'):
        for a in s.compare_attrs:
            d[a] = getattr(s, a)
    print format_objs(s, d)
print

print "Status plugins:"
for s in g['c']['status']:
    d = {}
    if hasattr(s, 'compare_attrs'):
        for a in s.compare_attrs:
            d[a] = getattr(s, a)
    print format_objs(s, d)
