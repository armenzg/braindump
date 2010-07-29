#!/usr/bin/python

import sys
import subprocess

def run_cmd(ip, argv, logfile, user='root', timeout=5):
    p = subprocess.Popen(['ssh', '-l', user, '-o',
                        'UserKnownHostsFile=mobile-hosts', '-o',
                        'StrictHostKeyChecking=no', '-o',
                        'ConnectTimeout=%d' % timeout, ip] + argv,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
    stdout, stderr = p.communicate()
    print "COMMAND: '%s'" % "', '".join(argv)
    print 'IP:       %s' % ip
    print 'STDOUT:   %s' % stdout
    print 'STDERR:   %s' % stderr
    if p.returncode is not 0:
        print 'FAILURE ON %s' % ip
        print >> logfile, 'FAILURE (%s) ON %s' % (argv, ip)
        print >> logfile, 'STDOUT: %s' % stdout
        print >> logfile, 'STDERR: %s' % stderr
        rc = False
    else:
        print 'Success on %s' % ip
        print >> logfile, 'Success (%s) on %s' % (argv, ip)
        rc = True
    logfile.flush()
    return rc

def run_on_devices(argv, ips, logfilename, timeout=5):
    logfile = open(logfilename, 'w+')
    outcomes = {}
    for ip in ips:
        outcomes[ip] = run_cmd(ip, argv, logfile, user='root', timeout=timeout)
    passes = []
    fails = []
    for i in outcomes.keys():
        if outcomes[i] is True:
            passes.append(i)
        else:
            fails.append(i)
    print 'PASS ON: %s' % ', '.join(passes)
    print >> logfile, 'PASS ON: %s' % ', '.join(passes)
    print 'FAIL ON: %s' % ', '.join(passes)
    print >> logfile, 'FAIL ON: %s' % ', '.join(passes)
    logfile.close()


def generate_n810s(numbers):
    return ['maemo-n810-%02d.build.mozilla.org' % x for x in [int(x) for x in numbers]]

def generate_n900s(numbers):
    return ['n900-%03d.build.mozilla.org' % x for x in [int(x) for x in numbers]]

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print 'You must have a non-zero length argument argv to run on device'
        exit(1)

    argv = sys.argv[2:]
    hosts = []

    if sys.argv[1].startswith('n900'):
        hosts = generate_n900s(sys.argv[1].split(':')[1:])
    elif sys.argv[1].startswith('n810'):
        hosts = generate_n900s(sys.argv[1].split(':')[1:])
    else:
        hosts = sys.argv[1].split(':')

    run_on_devices(argv, hosts, logfilename='command.log', timeout=5)

