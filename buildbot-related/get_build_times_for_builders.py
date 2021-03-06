#!/usr/bin/env python2

from sqlalchemy import create_engine, MetaData, Table, distinct, func
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
    builder_data = defaultdict(list)
    for b, br, bs, ss, c in session.query(Builds, Buildrequests, Buildsets, Sourcestamps, Changes)\
                         .join(Buildrequests, Builds.brid==Buildrequests.id)\
                         .join(Buildsets, Buildrequests.buildsetid==Buildsets.id)\
                         .join(Sourcestamps, Buildsets.sourcestampid==Sourcestamps.id)\
                         .outerjoin(SourcestampChanges, Sourcestamps.id==SourcestampChanges.sourcestampid)\
                         .outerjoin(Changes, SourcestampChanges.changeid==Changes.changeid)\
                         .filter(Buildrequests.buildername.in_(builders))\
                         .filter(Builds.start_time > since):

        if not b.finish_time:
            continue
        rev = ss.revision[:12]
        # If we have a Change object, this was a normal build (ie, triggered by a push).
        if c:
            pushed_at = c.when_timestamp
        # If not, this was probably a forced build or periodic. Buildsets.submitted_at should be accurate.
        else:
            pushed_at = int(bs.submitted_at)
        wait_time = int(b.start_time - pushed_at)
        build_time = int(b.finish_time - b.start_time)
        total_time = int(wait_time + build_time)
        builder_data[br.buildername].append("%s\t%s\t%s\t%s\t%s" % (rev, pushed_at, wait_time, build_time, total_time))

    for builder, data in builder_data.iteritems():
        coalesced = 0
        for r in session.query(func.count(Buildrequests.complete_at)).outerjoin(Builds, Buildrequests.id==Builds.brid).filter(Buildrequests.buildername==builder).filter(Builds.start_time > since).group_by(Buildrequests.complete_at).having(func.count(Buildrequests.complete_at) > 1):
            coalesced += (r[0] - 1)
        print builder
        print "Revision\tPushed at\tWait time\tBuild time\t Total time"
        for j in data:
            print j
        print
        print "Coalesced:\t%s" % coalesced
