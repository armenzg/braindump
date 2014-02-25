#!/usr/bin/env python
""" Generate invtool commands to add AWS hosts to DNS.

    Adds both A and PTR records.
"""
import logging
log = logging.getLogger()


def gen_cmds(args):
    app = "invtool"
    # we do want these in the private view
    options = ["--private", "--no-public"]
    if args.description:
        options.append("--description")
        options.append("'%s'" % args.description)
    if args.comment:
        options.append("--comment")
        options.append("'%s'" % args.comment)
    for sub_command, arg in (('A', 'fqdn'), ('PTR', 'target')):
        command = [app, sub_command, 'create']
        command.extend(['--ip', args.ip])
        command.extend(['--%s' % arg, args.fqdn])
        command.extend(options)
        print ' '.join(command)

if __name__ == '__main__':
    import argparse
    import re
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--description",
                        help="description of host")
    parser.add_argument("--comment",
                        help="comment for change")
    parser.add_argument("ip",
                        help="IP address of host")
    parser.add_argument("fqdn",
                        help="Fully Qualified Domain Name")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if not re.match('(\d{1,3}\.){3}\d{1,3}$', args.ip):
        parser.error("IP address format error")
    if not args.fqdn.endswith('mozilla.com'):
        parser.error("FQDN doesn't look right")

    gen_cmds(args)
