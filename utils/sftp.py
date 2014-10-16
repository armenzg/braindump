#!/usr/bin/env python
"""
Demo script for uploading a file to a bunch of build slaves
Prerequisites: you need paramiko and requests in your python environment
"""
import paramiko
from requests.auth import HTTPBasicAuth

class Server(object):
    """
    Wraps paramiko for super-simple SFTP uploading and downloading.
    from:
    http://ginstrom.com/scribbles/2009/09/14/easy-sftp-uploading-with-paramiko/
    """
    def __init__(self, username, password, host, port=22):
        self.transport = paramiko.Transport((host, port))
        self.transport.connect(username=username, password=password)
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)

    def upload(self, local, remote):
        self.sftp.put(local, remote)

    def download(self, remote, local):
        self.sftp.get(remote, local)

    def close(self):
        if self.transport.is_active():
            self.sftp.close()
            self.transport.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.close()

if __name__ == '__main__':
    import requests

    # Get a list of all the slaves from slavealloc
    # XXX: Update LDAP credentials below
    slaves = requests.get('https://secure.pub.build.mozilla.org/slavealloc/api/slaves', auth=HTTPBasicAuth('<my-ldap-user@mozilla.com>', 'my-very-secret-password')).json()
    hosts = []
    # Let's just use the Windows production builders
    for s in slaves:
        if s['distro'] == 'win2k8' and s['environment'] == 'prod' and s['trustid'] == 5:
            hosts.append(s['name'])

    print 'Uploading to hosts: %s' % hosts

    failed_hosts = []

    for h in hosts:
        try:
            # XXX: Update the password below
            with Server("cltbld", "opensesame", "%s.build.mozilla.org" % h) as s:
                # XXX: Update the local file and remote file below
                s.upload("/path/to/local/file.txt", "/C$/Users/cltbld/sample-file.txt")
                print h, "OK"
        except Exception as e:
            print h, "FAILED"
            failed_hosts.append((h, e))

    for h, e in failed_hosts:
        print h, e
