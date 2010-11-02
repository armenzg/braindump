#!/usr/bin/env python
import urllib, time
import sqlalchemy
from sqlalchemy import *


_config_file = os.path.expanduser('~/.cancellator.cfg')

def getPendingBuilds(db, branch, revision):
    br = db.tables['buildrequests']
    bs = db.tables['buildsets']
    ss = db.tables['sourcestamps']

    q = select([br.c.id, br.c.buildername],
            and_(br.c.buildsetid == bs.c.id,
                 bs.c.sourcestampid == ss.c.id,
                 br.c.claimed_at == 0,
                 br.c.complete == 0,
                 ss.c.branch.startswith(branch),
                 ss.c.revision.startswith(revision),
                 ),
            )
    return q.execute()

def getRunningBuilds(db, branch, revision):
    b = db.tables['builds']
    br = db.tables['buildrequests']
    bs = db.tables['buildsets']
    ss = db.tables['sourcestamps']

    q = select([br.c.claimed_by_name, br.c.buildername, b.c.number],
            and_(br.c.buildsetid == bs.c.id,
                 bs.c.sourcestampid == ss.c.id,
                 br.c.claimed_at != 0,
                 br.c.complete == 0,
                 ss.c.branch.startswith(branch),
                 ss.c.revision.startswith(revision),
                 b.c.brid == br.c.id,
                 ),
            )

    return q.execute()

def cancelPendingBuild(brid):
    br = db.tables['buildrequests']

    q = br.update().where(and_(br.c.id == brid, br.c.complete == 0))
    q = q.values(complete=1, results=2, complete_at=time.time())

    res = q.execute()

def urlFromResult(result):
    host, buildername, number = result
    hostname = host.split(":")[0]
    buildername = urllib.quote(buildername, "")

    # try master
    if hostname == 'production-master02.build.mozilla.org':
        port = 8011
    # mini masters
    elif hostname.split('.')[0] in ('talos-master02','test-master01','test-master02'):
        port = 8012
    # pm01/pm03
    else:
        port = 8010

    return "http://%(hostname)s:%(port)i/builders/%(buildername)s/builds/%(number)s" % locals()

def cancelBuild(url):
    stopUrl = url + "/stop"
    data = urllib.urlencode({
        "comments": "Stopped by the cancellator!",
        })
    # TODO: If we can avoid following the redirect, this will probably be faster
    urllib.urlopen(stopUrl, data)

def readDefaults():
    defaults = { 'db':       None,
                 'branch':   None,
                 'revision': None,
                 'force':    False,
               }

    if os.path.isfile(_config_file):
        for line in open(_config_file, 'r').readlines():
            if len(line) > 0 and line[0] not in ('#', ';'):
                item = line.split('=')

                if len(item) == 2:
                    key = item[0].strip()
                    val = item[1].strip()

                    if key.lower() in ('force'):
                        val = val.lower() in ('true',)

                    defaults[key] = val

    return defaults

def getOptions():
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("--db",         dest="db",       help="db url")
    parser.add_option("-b",           dest="branch",   help="branch name")
    parser.add_option("-r",           dest="revision", help="revision id")
    parser.add_option("--yes-really", dest="force",    help="yes, perform the cancels", action="store_true")

    defaults = getDefaults()

    parser.set_defaults(**defaults)

    options, args = parser.parse_args()

    if not options.db or not options.branch or not options.revision:
        parser.error("Must specify db, branch, and revision")

    if len(options.revision) < 8:
        parser.error("Revision must be at least 8 characters long")

    return options

if __name__ == "__main__":
    options = getOptions()

    engine = sqlalchemy.create_engine(options.db)
    db = sqlalchemy.MetaData()
    db.reflect(bind=engine)
    db.bind = engine

    for i in range(10):
        found = False
        killed = False
        for brid, buildername in getPendingBuilds(db, options.branch, options.revision):
            found = True
            if options.force:
                print "Cancelling pending build on", buildername,
                try:
                    cancelPendingBuild(brid)
                    print "OK"
                    killed = True
                except:
                    print "FAILED"
            else:
                print "Would cancel pending build on", buildername

        for r in getRunningBuilds(db, options.branch, options.revision):
            found = True
            url = urlFromResult(r)
            if options.force:
                print "Cancelling running build", url,
                try:
                    cancelBuild(url)
                    print "OK"
                    killed = True
                except:
                    print "FAILED"
            else:
                print "Would cancel running build at", url

        if not options.force:
            break

        if not found:
            break
        elif not killed:
            print "Waiting for things to get better..."
            time.sleep(10)
