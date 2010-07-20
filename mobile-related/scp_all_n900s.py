#!/usr/bin/python

import sys
import os
import subprocess

def run_cmd(ip, infiles, outfile, logfile, user='root', passwd='rootme'):
    p = subprocess.Popen(['scp', '-o', 'UserKnownHostsFile=n900-hosts', 
                          '-o', 'StrictHostKeyChecking=no', 
                          '-o', 'ConnectTimeout=2', ip] + infiles + ['%s@%s:%s' % (user, ip, outfile)],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         stdin=subprocess.PIPE)
    stdout, stderr = p.communicate()
    print 'STDOUT: %s' % stdout
    print 'STDERR: %s' % stderr
    if p.returncode is not 0:
        print 'FAILURE ON %s' % ip
        print >> logfile, 'FAILURE (%s -> %s) ON %s' % (infiles, outfile, ip)
    else:
        print 'Success on %s' % ip
        print >> logfile, 'Success (%s -> %s) on %s' % (infiles, outfile, ip)
    logfile.flush()

if len(sys.argv) < 3:
    print >>sys.stderr, 'usage: %s infile1 [infile2 ..] outfile' % sys.argv[0]
    print >>sys.stderr, 'The infile(s) is relative to pwd and the outfile is relative to home dir on device'
    exit(1)

logfile = open('commands.log', 'w+')

for i in sys.argv[1:-1]:
    if not os.path.exists(i):
        print >>sys.stderr, "the file %s does not exist" % i
        exit(1)

for i in range(1,21) + range(121, 151):
    ip = '10.250.50.%d' % i
    print 'Running command on %s' % ip
    run_cmd(ip, sys.argv[1:-1], sys.argv[-1], logfile)

logfile.close()
