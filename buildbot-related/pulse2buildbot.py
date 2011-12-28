#!/usr/bin/env python
# pulse2buildbot <master:port>
# listens for pulse events about new changes, and replays them to the specified
# master
import uuid
try:
    import simplejson as json
except ImportError:
    import json

from mozillapulse import consumers
from subprocess import check_call

def changeFromMessage(message):
    """Returns a dictionary representing change object from a pulse message"""
    retval = message['payload']['change']
    retval['revision'] = retval['rev']
    retval['properties'] = dict((k,v) for (k,v,s) in retval['properties'])
    retval['files'] = [f['name'] for f in retval['files']]
    if not retval['files']:
        retval['files'] = ['dummy']
    retval['user'] = retval['who']
    del retval['rev']
    del retval['who']
    del retval['number']
    del retval['at']
    return retval

def sendchange(master, data, message):
    change = changeFromMessage(data)
    print "Sending", change
    props = []
    for k,v in change['properties'].items():
        props.extend(['-p', '%s:%s' % (k,v)])
    check_call(['buildbot', 'sendchange', '--master', master,
                '--branch', change['branch'],
                '--revision', change['revision'],
                '--username', change['user'],
                '--comments', change['comments'],
                ] + props + change['files'])
    message.ack()

def main():
    import sys
    master = sys.argv[1]
    pulse = consumers.BuildConsumer(applabel=str(uuid.uuid4()))
    pulse.configure(topic='change.*.added', callback=lambda data, message: sendchange(master, data, message))
    pulse.listen()

if __name__ == '__main__':
    main()
