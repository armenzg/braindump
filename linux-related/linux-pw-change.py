#!/usr/bin/env python

from optparse import OptionParser
import pexpect
import sys

def usage(msg):
    if msg:
        print("ERROR: %s" % msg)
    print """
Usage: %prog --username=%s --current-password=%s --new-password=%s [--vnc-password=%s] [--skip-passwd] --host=%s
"""
    sys.exit(1)


if __name__ == '__main__':
    parser = OptionParser(usage="usage: %prog [options] <directory> <files>")
    parser.add_option("--username",
                      action="store", dest="username")
    parser.add_option("--current-password",
                      action="store", dest="current_password")
    parser.add_option("--new-password",
                      action="store", dest="new_password")
    parser.add_option("--vnc-password",
                      action="store", dest="vnc_password")
    parser.add_option("--host",
                      action="store", dest="host")
    parser.add_option("--skip-passwd",
                      action="store_true", dest="skip_passwd", default=False)

    (options, args) = parser.parse_args()
    if not options.username:
        usage("--username is required")
    if not options.current_password:
        usage("--current-password is required")
    if not options.new_password:
        usage("--new-password is required")
    if not options.host:
        usage("--host is required")

    child = pexpect.spawn("ssh -o PubkeyAuthentication=no -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null %s@%s" % (options.username, options.host))
    child.expect('[pP]assword:')
    child.sendline(options.current_password)
    n = child.expect(['Last login:','Password:'])
    if n == 1:
        print("ERROR: Failed to login. Is password already updated?")
        sys.exit(2)
    print("logged in!")
    if not options.skip_passwd:
        child.sendline('passwd')
        child.expect('[cC]urrent.*[pP]assword:')
        child.sendline(options.current_password)
        child.expect('[nN]ew [pP]assword:')
        child.sendline(options.new_password)
        child.expect('[rR]etype [nN]ew [pP]assword:')
        child.sendline(options.new_password)
        print("passwd changed")
    if options.vnc_password:
        print("Running vncpasswd")
        # echo 'Done' on success so we have something good to watch for
        child.sendline('vncpasswd && echo Done')
        child.expect('[pP]assword:')
        child.sendline(options.vnc_password)
        child.expect('[vV]erify:')
        child.sendline(options.vnc_password)
        child.expect('Done')
        print("VNC password updated")
