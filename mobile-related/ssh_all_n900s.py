#!/usr/bin/python

import sys
import subprocess

def run_cmd(ip, argv, logfile, user='root', passwd='rootme'):
    p = subprocess.Popen(['ssh', '-l', user, '-o',
                        'UserKnownHostsFile=n900-hosts', '-o',
                        'StrictHostKeyChecking=no', '-o',
                        'ConnectTimeout=2', ip] + argv,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
    stdout, stderr = p.communicate()
    print 'STDOUT: %s' % stdout
    print 'STDERR: %s' % stderr
    if p.returncode is not 0:
        print 'FAILURE ON %s' % ip
        print >> logfile, 'FAILURE (%s) ON %s' % (argv, ip)
    else:
        print 'Success on %s' % ip
        print >> logfile, 'Success (%s) on %s' % (argv, ip)
    logfile.flush()

logfile = open('commands.log', 'w+')

for i in range(1,21) + range(121, 151):
    ip = '10.250.50.%d' % i
    print 'Running command on %s' % ip
    run_cmd(ip, sys.argv[1:], logfile)

logfile.close()
