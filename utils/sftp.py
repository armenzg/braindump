#!/usr/bin/env python
"""
Demo script for uploading a file to a bunch of build slaves
"""
import paramiko


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
    slaves = requests.get("http://slavealloc.build.mozilla.org/api/slaves").json()
    hosts = []
    # Let's just use the windows ones
    for s in slaves:
        if 'w64' in s['name'] and s['purpose'] == 'build':
            hosts.append(s['name'])

    failed_hosts = []

    for h in hosts:
        try:
            # XXX: Update the password below
            with Server("cltbld", "opensesame", "%s.build.mozilla.org" % h) as s:
                s.upload("/path/to/local/file.txt", "/E$/builds/file.txt")
                print h, "OK"
        except Exception as e:
            print h, "FAILED"
            failed_hosts.append((h, e))

    for h, e in failed_hosts:
        print h, e
