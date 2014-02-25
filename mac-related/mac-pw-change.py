#!/usr/bin/env python

from optparse import OptionParser
import pexpect
import sys
from base64 import b64encode

def kcpassword_xor(passwd):
        ### The magic 11 bytes - these are just repeated 
        # 0x7D 0x89 0x52 0x23 0xD2 0xBC 0xDD 0xEA 0xA3 0xB9 0x1F
        key = [125,137,82,35,210,188,221,234,163,185,31]
        key_len = len(key)

        passwd = [ord(x) for x in list(passwd)]
        # pad passwd length out to an even multiple of key length
        r = len(passwd) % key_len
        if (r > 0):
            passwd = passwd + [0] * (key_len - r)

        for n in range(0, len(passwd), len(key)):
           ki = 0
           for j in range(n, min(n+len(key), len(passwd))):
               passwd[j] = passwd[j] ^ key[ki]
               ki += 1

        passwd = [chr(x) for x in passwd]
        return "".join(passwd)

def usage(msg):
    if msg:
        print("ERROR: %s" % msg)
    print """
Usage: %prog --username=%s --current-password=%s --new-password=%s --host=%s
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

    base64_kcpassword = b64encode(kcpassword_xor(options.new_password))
    print("base64'd kcpassword: %s" % base64_kcpassword)

    child = pexpect.spawn("ssh -o PubkeyAuthentication=no -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null %s@%s" % (options.username, options.host))
    child.expect('Password:')
    child.sendline(options.current_password)
    n = child.expect(['Last login:','Password:'])
    if n == 1:
        print("ERROR: Failed to login. Is password already updated?")
        sys.exit(2)
    print("logged in!")
    if not options.skip_passwd:
        child.sendline('passwd')
        child.expect('Old Password:')
        child.sendline(options.current_password)
        child.expect('New Password:')
        child.sendline(options.new_password)
        child.expect('Retype New Password:')
        child.sendline(options.new_password)
        print("passwd changed")
    print("writing ~cltbld/kcpassword")
    # use perl to decode base64 because moz2-darwin10-slaveXX do
    # not have the base64 binary installed.
    cmd = "perl -MMIME::Base64 -e 'print decode_base64(shift @ARGV)'"
    child.sendline("%s %s > /Users/cltbld/kcpassword" % (cmd, base64_kcpassword))
    print("copying to /etc/kcpassword")
    # run 'sudo -k' separately because moz2-darwin10-slaveXX refuses
    # to run a command in addition to the -k option.
    child.sendline("sudo -k")
    # echo 'Done' on success so we have something good to watch for
    child.sendline("sudo cp /Users/cltbld/kcpassword /etc/kcpassword && echo Done")
    child.expect('Password:')
    if options.skip_passwd:
        child.sendline(options.current_password)
    else:
        child.sendline(options.new_password)
    n = child.expect(['Done', 'Sorry, try again'])
    if n == 1:
        print("ERROR: Could not authenticate to sudo")
        sys.exit(3)
    child.sendline('rm -f /Users/cltbld/kcpassword')
    print("updated /etc/kcpassword")
    child.sendline('rm -rf /Users/cltbld/Library/Keychains/login.keychain')
    print("removed old keychain")
