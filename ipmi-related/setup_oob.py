#! /usr/bin/python

import os
import sys
import ConfigParser
import traceback
import subprocess
import optparse

class Cred(object):

    def __init__(self, username, password, enabled):
        self.username = username
        self.password = password
        self.enabled = enabled

    def args(self):
        return [ '-U', self.username, '-P', self.password ]

def call_ipmitool(host, cred, fail_ok=False, command=[]):
    clean_command = ['user', 'set', 'password', '..'] if 'password' in command else command
    print (">>> ipmitool -H %s -U %s " % (host, cred.username)) + " ".join(clean_command)
    p = subprocess.Popen(['/usr/bin/ipmitool', '-H', host ] + cred.args() + list(command),
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()[:2]
    if p.returncode != 0:
        if not fail_ok:
            print stderr
            raise RuntimeError
        return None
    return stdout

def get_user_list(host, cred, fail_ok=False):
    "Return a dictionary of user information for the host"
    stdout = call_ipmitool(host, cred, fail_ok=fail_ok, command=['user', 'list'])
    if stdout is None:
        return
    users = {}
    lines = stdout.split('\n')
    for line in lines[1:]:
        if not line:
            continue
        id = int(line[:4].strip())
        name = line[4:21].strip()
        priv = line[51:].strip()
        if not name:
            continue
        users[name] = {'id': id, 'name': name, 'priv': priv}
    return users

def get_creds(config):
    rv = []
    for sect in config.sections():
        username = sect
        password = config.get(sect, 'password')
        enabled = True
        if config.has_option(sect, 'enabled'):
            enabled = config.getboolean(sect, 'enabled')
        rv.append(Cred(username, password, enabled))
    return rv

def setup_host(host, creds):
    try:
        subprocess.check_call(['fping', host])
    except Exception:
        print "*** host not pingable"
        return False

    # see what does and does not allow login, while grabbing the user list
    user_list = {}
    to_enable = []
    to_disable = []
    working_cred = None
    for cred in creds:
        ul = get_user_list(host, cred, fail_ok=True)
        if ul is None:
            if cred.enabled:
                to_enable.append(cred)
        else:
            if not cred.enabled:
                to_disable.append(cred.username)
            user_list.update(ul)
            if not working_cred:
                working_cred = cred

    # if nothing worked, we're stuck
    if working_cred is None:
        raise RuntimeError("could not find working credentials")

    # find any unknown users should get deleted
    creds_usernames = [ cred.username for cred in creds ]
    to_disable.extend(set(user_list) - set(creds_usernames))

    # enable everything that needs it, using the best working cred
    def find_id(name):
        if name in user_list:
            return user_list[name]['id']
        else:
            current_ids = set([u['id'] for u in user_list.values()])
            for id in range(2, 11):
                if id not in current_ids:
                    return id
    for cred in to_enable:
        id = find_id(cred.username)
        print ">> enabling", cred.username, "with id", id
        call_ipmitool(host, working_cred, command=map(str, ('user', 'enable', id)))
        call_ipmitool(host, working_cred, command=map(str, ('user', 'set', 'password', id, cred.password)))
        if cred.username != 'ADMIN': # ADMIN is a sacred cow
            call_ipmitool(host, working_cred, command=map(str, ('user', 'set', 'name', id, cred.username)))
            # priv 4 is ADMINISTRATOR; this sets it on channels 1 and 14; older IPMI implementations
            # don't accept channel 14, so failure there is OK
            call_ipmitool(host, working_cred, command=map(str, ('user', 'priv', id, 4, 1)))
            call_ipmitool(host, working_cred, command=map(str, ('user', 'priv', id, 4, 14)), fail_ok=True)
        # use the new cred to get a new user list
        user_list = get_user_list(host, cred)

    # then disable stuff, using an enabled cred
    working_cred = [cred for cred in creds if cred.enabled][0]
    for username in to_disable:
        print ">> disabling", username
        id = user_list[username]['id']
        call_ipmitool(host, working_cred, command=map(str, ('user', 'disable', id)))
        if username != 'ADMIN': # ADMIN is a sacred cow
            # 1=CALLBACK -- not even read-only
            call_ipmitool(host, working_cred, command=map(str, ('user', 'priv', id, 1, 1)))
            call_ipmitool(host, working_cred, command=map(str, ('user', 'priv', id, 1, 14)), fail_ok=True)
            # blank out the username
            call_ipmitool(host, working_cred, command=map(str, ('user', 'set', 'name', id, '')))

    return True

usage = """\
usage: %prog [options] hostnames..

Set up the IPMI interfaces on the given hostnames.  The configuration file
('./oob.cfg' by default) should contain a section for each desired user, with
options 'password' and 'enabled'.  A user that might be useful for login, but
which should be disabled, can be specified with `enabled = no`.
"""

def main():
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-c', '--config', dest='config_file',
                      help="set config file", default="oob.cfg")
    parser.add_option('-H', '--host-file', dest='host_file',
                      help="text file of hostnames to check")
    options, args = parser.parse_args()

    config = ConfigParser.RawConfigParser()
    if not os.path.exists(options.config_file):
        print options.config_file, "not found"
        sys.exit(1)
    config.read(options.config_file)

    creds = get_creds(config)

    hosts = args
    if options.host_file:
        for l in open(options.host_file):
            l = l.strip()
            if not l:
                continue
            hosts.append(l)

    ev = 0
    badhosts = []
    for host in hosts:
        print ">", host
        try:
            rv = setup_host(host, creds)
        except RuntimeError:
            print "*** HOST FAILED"
            rv = False
        if not rv:
            badhosts.append(host)

    if badhosts:
        print "BAD HOSTS:"
    for h in badhosts:
        print h

    sys.exit(ev)

main()
