#!/usr/bin/python
import master_fabric
from fabric.api import env
from fabric.context_managers import settings

def run_action_on_master(action, master):
    action_func = getattr(master_fabric, action)
    with settings(host_string=master['hostname']):
        return action_func(master)

if __name__ == '__main__':
    from optparse import OptionParser
    import textwrap
    try:
        import simplejson as json
    except ImportError:
        import json

    parser = OptionParser("""%%prog [options] action [action ...]

Supported actions:
%s""" % textwrap.fill(", ".join(master_fabric.actions)))

    parser.set_defaults(
            hosts=[],
            roles=[],
            concurrency=1,
            )
    parser.add_option("-f", "--master-file", dest="master_file", help="list/url of masters")
    parser.add_option("-H", "--host", dest="hosts", action="append")
    parser.add_option("-R", "--role", dest="roles", action="append")
    parser.add_option("-j", dest="concurrency", type="int")

    options, actions = parser.parse_args()

    if options.concurrency > 1:
        import multiprocessing

    if not options.master_file:
        parser.error("master-file is required")

    if not actions:
        parser.error("at least one action is required")

    # Load master data
    import urllib
    all_masters = json.load(urllib.urlopen(options.master_file))

    masters = []

    for m in all_masters:
        if m['name'] in options.hosts:
            masters.append(m)
        elif any(r in options.roles for r in m['roles']):
            masters.append(m)
        elif 'all' in options.hosts or 'all' in options.roles:
            masters.append(m)

    if len(masters) == 0:
        parser.error("You need to specify a master via -H and/or -R")

    env.user = 'cltbld'
    for action in actions:
        if options.concurrency == 1:
            for master in masters:
                run_action_on_master(action, master)
        else:
            results = {}
            p = multiprocessing.Pool(processes=options.concurrency)
            for master in masters:
                result = p.apply_async(run_action_on_master, (action, master))
            p.close()
            p.join()
            failed = False
            for master, result in results.items():
                if not result.successful():
                    failed = True
                    print master, "FAILED"
                    break
            if failed:
                break
