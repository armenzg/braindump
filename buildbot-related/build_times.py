#!/usr/bin/env python
import sqlalchemy as sa
import time
from datetime import timedelta, datetime
from collections import defaultdict
import calendar
import socket

import logging
log = logging.getLogger(__name__)

def get_build_times(db, starttime, endtime):
    q = sa.text("""
        SELECT builders.name, builds.starttime, builds.endtime FROM
            builders, builds
        WHERE
            builds.builder_id = builders.id AND
            builds.starttime >= :starttime AND
            builds.starttime < :endtime
            """)
    return db.execute(q, starttime=starttime, endtime=endtime)


def td2s(td):
    "timedelta to seconds"
    return td.days * 86400 + td.seconds + td.microseconds / 1000000.0


def dt2ts(dt):
    "datetime to epoch time"
    return calendar.timegm(dt.timetuple())


def get_builder_times(results):
    retval = defaultdict(list)
    for row in results:
        retval[row.name].append(td2s(row.endtime - row.starttime))

    return retval


def get_percentile(l, n):
    "get the nth percentile of l. n should be in the range [0,1]"
    i = int(len(l) * n)
    return sorted(l)[i]


class GraphiteSubmitter(object):
    def __init__(self, host, port, prefix):
        self.host = host
        self.port = port
        self.prefix = prefix
        self._sock = socket.create_connection((host, port))

    def submit(self, name, value, timestamp=None):
        line = "%s.%s %s" % (self.prefix, name, value)
        if timestamp:
            line += " %i" % timestamp

        #print line
        self._sock.sendall(line + "\n")

    def wait(self):
        self._sock.close()


def main():
    import config
    logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.DEBUG)
    db = sa.create_engine(config.db_url)

    now = datetime.utcfromtimestamp(time.time())
    start = now - timedelta(days=1)
    end = now

    log.info("Getting build times from %s to %s", start, end)

    all_results = get_build_times(db, start, end)

    log.debug("got %i results", all_results.rowcount)

    # Filter only certain branches
    branches = ['mozilla-inbound', 'try', 'mozilla-central']
    results = [row for row in all_results if any(b in row.name for b in branches)]

    log.debug("got %i filtered results", len(results))

    times_per_builder = get_builder_times(results)

    log.debug("connecting to graphite")
    g = GraphiteSubmitter("carbon.hostedgraphite.com", 2003, "%s.buildtimes" % config.graphite_api_key)

    n = 0
    for builder, times in times_per_builder.iteritems():
        assert " " not in builder
        p95 = get_percentile(times, .95)
        p50 = get_percentile(times, .50)
        g.submit("%s.p95" % builder, p95)
        g.submit("%s.p50" % builder, p50)
        n += 2

    log.info("submitted %i metrics", n)
    log.info("waiting for graphite to finish")
    g.wait()

if __name__ == '__main__':
    main()
