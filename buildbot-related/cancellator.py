#!/usr/bin/env python
import urllib, time
import sqlalchemy
from sqlalchemy import *

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
    buildername = urllib.quote(buildername)

    if hostname == 'production-master02.build.mozilla.org':
        port = 8011
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

if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("--db", dest="db", help="db url")
    parser.add_option("-b", dest="branch")
    parser.add_option("-r", dest="revision")
    parser.add_option("--yes-really", dest="force", action="store_true")
    parser.set_defaults(
            force=False,
            )

    options, args = parser.parse_args()

    if not options.db or not options.branch or not options.revision:
        parser.error("Must specify db, branch, and revision")

    if len(options.revision) < 8:
        parser.error("Revision must be at least 8 characters long")

    engine = sqlalchemy.create_engine(options.db)
    db = sqlalchemy.MetaData()
    db.reflect(bind=engine)
    db.bind = engine

    found = True

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
