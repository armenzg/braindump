#!/usr/bin/env python2

from sqlalchemy import create_engine, MetaData, Table, distinct
from sqlalchemy.orm import sessionmaker, mapper

class Builds(object):
    pass

class Buildrequests(object):
    pass

class Buildsets(object):
    pass

class Sourcestamps(object):
    pass

class SourcestampChanges(object):
    pass

class Changes(object):
    pass

if __name__ == '__main__':
    import sys

    dburi = sys.argv[1]
    since = int(sys.argv[2]) # unix time to go back as far as
    builders = sys.argv[3:]

    engine = create_engine(dburi)
    metadata = MetaData(bind=engine)
    builds = Table('builds', metadata, autoload=True)
    buildrequests = Table('buildrequests', metadata, autoload=True)
    buildsets = Table('buildsets', metadata, autoload=True)
    sourcestamps = Table('sourcestamps', metadata, autoload=True)
    sourcestampchanges = Table('sourcestamp_changes', metadata, autoload=True)
    changes = Table('changes', metadata, autoload=True)
    mapper(Builds, builds)
    mapper(Buildrequests, buildrequests)
    mapper(Buildsets, buildsets)
    mapper(Sourcestamps, sourcestamps)
    mapper(SourcestampChanges, sourcestampchanges, primary_key=[sourcestampchanges.c.sourcestampid, sourcestampchanges.c.changeid])
    mapper(Changes, changes)
    session = sessionmaker(bind=engine)()

    print "Build times:"
    print "builder name, build number, built revision, build time, # of builds coallesced"
    for b, br, bs, ss in session.query(Builds, Buildrequests, Buildsets, Sourcestamps)\
                         .outerjoin(Buildrequests, Builds.brid==Buildrequests.id)\
                         .join(Buildsets, Buildrequests.buildsetid==Buildsets.id)\
                         .join(Sourcestamps, Buildsets.sourcestampid==Sourcestamps.id)\
                         .filter(Buildrequests.buildername.in_(builders))\
                         .filter(Builds.start_time > since):

        elapsed = b.finish_time - b.start_time    
        final_rev = ss.revision
        total_revs = session.query(Builds.id).join(Buildrequests, Builds.brid==Buildrequests.id).filter(Builds.number==b.number).filter(Buildrequests.buildername==br.buildername).count()
        print "%s,%s,%s,%s,%s" % (br.buildername, b.number, final_rev, elapsed, total_revs)

    print "Wait times:"
    print "builder name, revision, wait time"
    for b, br, ss, c in session.query(Builds, Buildrequests, Sourcestamps, Changes)\
                         .outerjoin(Buildrequests, Builds.brid==Buildrequests.id)\
                         .join(Buildsets, Buildrequests.buildsetid==Buildsets.id)\
                         .join(Sourcestamps, Buildsets.sourcestampid==Sourcestamps.id)\
                         .join(SourcestampChanges, Sourcestamps.id==SourcestampChanges.sourcestampid)\
                         .join(Changes, SourcestampChanges.changeid==Changes.changeid)\
                         .filter(Buildrequests.buildername.in_(builders))\
                         .filter(Builds.start_time > since):
        if b.finish_time:
            print "%s,%s,%s" % (br.buildername, ss.revision, b.start_time - c.when_timestamp)
