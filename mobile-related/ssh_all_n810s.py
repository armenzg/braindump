#!/usr/bin/python

import sys
import subprocess

def run_cmd(ip, argv, logfile, user='root', passwd='rootme'):
    p = subprocess.Popen(['ssh', '-l', user, '-o',
                        'UserKnownHostsFile=n810-hosts', '-o',
                        'StrictHostKeyChecking=no', '-o',
                        'ConnectTimeout=2', ip] + argv,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
    stdout, stderr = p.communicate()
    print 'COMMAND ON %s' % ip
    print 'STDOUT: %s' % stdout
    print 'STDERR: %s' % stderr
    if p.returncode is not 0:
        print 'FAILURE ON %s' % ip
        print >> logfile, 'FAILURE (%s) ON %s' % (argv, ip)
        rc = False
    else:
        print 'Success on %s' % ip
        print >> logfile, 'Success (%s) on %s' % (argv, ip)
        rc = True
    logfile.flush()
    return rc

logfile = open('commands.log', 'w+')

outcomes = {}
for i in range(1,81):
    print '=' * 80
    ip = 'maemo-n810-%02d.build.mozilla.org' % i
    outcomes[i] = run_cmd(ip, sys.argv[1:], logfile)
    print '-' * 80

logfile.close()

passes = []
fails = []
for i in outcomes.keys():
    if outcomes[i] is True:
        passes.append(i)
    else:
        fails.append(i)
print '=' * 80
print '=' * 80
print '=' * 80
print 'PASS ON: %s' % ', '.join([str(x) for x in passes])
print 'FAIL ON: %s' % ', '.join([str(x) for x in fails])

