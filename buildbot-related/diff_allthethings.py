#!/usr/bin/env python
"""
diff_allthethings.py f1 f2

Outputs the differences between f1 and f2
"""
import json


def diff_builders(b1, b2):
    """
    Output a report of builder differences between b1 and b2
    """
    b1_names = set(b1.keys())
    b2_names = set(b2.keys())
    added = b2_names - b1_names
    removed = b1_names - b2_names

    if added:
        print "Builders added:"
        for b in sorted(added):
            print "+ %s" % b
    if removed:
        print "Builders removed"
        for b in sorted(removed):
            print "- %s" % b


def diff_things(f1, f2):
    diff_builders(f1['builders'], f2['builders'])


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs=2)

    args = parser.parse_args()

    f1 = json.load(open(args.files[0]))
    f2 = json.load(open(args.files[1]))

    diff_things(f1, f2)

if __name__ == '__main__':
    main()
