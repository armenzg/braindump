#!/usr/bin/env python
"Generates puppet node definitions for masters from production-masters.json"

import argparse
import json
import re


TEMPLATE = """node "%(fqdn)s" {
    buildmaster::buildbot_master {
        "%(name)s":
            http_port => %(http_port)s,
            master_type => "%(master_type)s",
            basedir => "%(basedir)s";
    }
    include toplevel::server::buildmaster
}
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("masters", nargs="+", metavar="host",
                        help="List of REs of master names, e.g. bm54")
    parser.add_argument("--config", "-c", default="production-masters.json",
                        type=argparse.FileType('r'))
    args = parser.parse_args()

    config = json.load(args.config)

    for m in config:
        if any(re.search(pattern, m["name"])
               for pattern in args.masters):
            # Determine master type dropping the master prefix
            m_parts = m['name'].split('-')[1:]
            if any("scheduler" in p for p in m_parts):
                master_type = "scheduler"
            elif any("try" in p for p in m_parts):
                master_type = "try"
            elif any("tests" in p for p in m_parts):
                master_type = "tests"
            elif any("build" in p for p in m_parts):
                master_type = "build"

            basedir = m['basedir'].split("/")[-1]
            print TEMPLATE % dict(fqdn=m['hostname'], name=m['name'],
                                  http_port=m['http_port'],
                                  master_type=master_type,
                                  basedir=basedir)
