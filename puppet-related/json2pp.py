#!/usr/bin/env python
"Generates puppet node definitions for masters from production-masters.json"

import argparse
import csv
import json
import re
import sys


TEMPLATE = """node "%(fqdn)s" {
    $node_security_level = 'high'
    buildmaster::buildbot_master::mozilla {
        "%(name)s":
            http_port => %(http_port)s,
            master_type => "%(master_type)s",
            basedir => "%(basedir)s";
    }
    include toplevel::server::buildmaster
}
"""

CREATE_INSTANCE_TEMPLATE = r"""python \
 aws_create_instance.py -c configs/master-linux64 -r %(region_name)s -s aws-releng  \
  -k /home/buildduty/aws/cloud-tools/aws/secrets/aws-secrets.json \
  -i %(region_name)s.instance_data_master.json %(short_hostname)s
"""

# CSV information: dict of inventory_name: value (can ref json names),
# additional defined keys:
inventory_record = {
    'hostname': '%(hostname)s',
    'system_status %status': '%(environment)s',
    'system_rack %id': '%(system_rack_id)s',
    'operating_system %name%version': 'Centos %% 6',
    # due to bug in cvs import, can't do allocation yet
    #'allocation': inventory_db_ids['release allocation id'],
}

# ugly database stuff we need to know in current version of the CVS importer
inventory_db_ids = {
    'usw2 system rack id': 285,
    'use1 system rack id': 286,
    'usw1 system rack id': 287,
    'release allocation id': 2,
}

# region is 3rd level domain
aws_region_pattern = re.compile(r'\.([^\.]+)\.mozilla\.com$')


def write_bash_script(scriptfile, input_dict):
    context = input_dict.copy()
    aws_region = aws_region_pattern.search(m['hostname']).group(1).lower()
    if 'e' in aws_region:
        region_name = aws_region.replace('e', '-east-')
    elif 'w' in aws_region:
        region_name = aws_region.replace('w', '-west-')
    else:
        raise KeyError("unknown aws region '%s'" % aws_region)
    fqdn = context['hostname']
    short_hostname = fqdn[:fqdn.index('.')]
    context.update({'region_name': region_name, 'short_hostname': short_hostname})
    scriptfile.write(CREATE_INSTANCE_TEMPLATE % context)


def write_inventory_csv(csvfile, input_dict):
    aws_region = aws_region_pattern.search(m['hostname']).group(1).lower()
    input_dict['system_rack_id'] = inventory_db_ids['%s system rack id' % aws_region]
    host_info = {}
    for key, value in inventory_record.items():
        host_info[key] = value % input_dict
    inventory.writerow(host_info)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("masters", nargs="+", metavar="host",
                        help="List of REs of master names, e.g. bm54")
    parser.add_argument("--config", "-c", default="production-masters.json",
                        type=argparse.FileType('r'))
    parser.add_argument("--no-puppet", default=False, action='store_true',
                        help="Suppress puppet output")
    parser.add_argument("--inventory-csv", default=None,
                        type=argparse.FileType('w'),
                        help="generate INVENTORY_CSV file to import into inventory system")
    parser.add_argument("--bash", default=None,
                        type=argparse.FileType('w'),
                        help="generate BASH file to create AWS instance")
    # make --help work
    # from http://stackoverflow.com/questions/8236954/specifying-default-filenames-with-argparse-but-not-opening-them-on-help
    parser._parse_known_args(sys.argv[1:], argparse.Namespace())
    args = parser.parse_args()

    write_csv = args.inventory_csv is not None
    if write_csv:
        inventory = csv.DictWriter(args.inventory_csv, inventory_record.keys())
        inventory.writeheader()

    write_bash = args.bash is not None

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

            if not args.no_puppet:
                basedir = m['basedir'].split("/")[-1]
                print TEMPLATE % dict(fqdn=m['hostname'], name=m['name'],
                                      http_port=m['http_port'],
                                      master_type=master_type,
                                      basedir=basedir)
            if write_bash:
                write_bash_script(args.bash, m)

            if write_csv:
                write_inventory_csv(inventory, m)
