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

    from collections import defaultdict
    data = defaultdict(list)
    for b, br, bs, ss, c in session.query(Builds, Buildrequests, Buildsets, Sourcestamps, Changes)\
                         .outerjoin(Buildrequests, Builds.brid==Buildrequests.id)\
                         .join(Buildsets, Buildrequests.buildsetid==Buildsets.id)\
                         .join(Sourcestamps, Buildsets.sourcestampid==Sourcestamps.id)\
                         .join(SourcestampChanges, Sourcestamps.id==SourcestampChanges.sourcestampid)\
                         .join(Changes, SourcestampChanges.changeid==Changes.changeid)\
                         .filter(Buildrequests.buildername.in_(builders))\
                         .filter(Builds.start_time > since):

        #total_revs = session.query(Builds.id).join(Buildrequests, Builds.brid==Buildrequests.id).filter(Builds.number==b.number).filter(Buildrequests.buildername==br.buildername).count()
        #print "%s,%s,%s,%s,%s" % (br.buildername, b.number, final_rev, elapsed, total_revs)
        if not b.finish_time:
            continue
        rev = ss.revision[:12]
        pushed_at = c.when_timestamp
        wait_time = int(b.start_time - pushed_at)
        build_time = int(b.finish_time - b.start_time)
        total_time = int(wait_time + build_time)
        data[br.buildername].append("%s\t%s\t%s\t%s\t%s" % (rev, pushed_at, wait_time, build_time, total_time))

    for builder, row in data.iteritems():
        print builder
        print "Revision\tPushed at\tWait time\tBuild time\t Total time"
        for r in row:
            print r
