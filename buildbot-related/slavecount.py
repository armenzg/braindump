#!/usr/bin/python
import re, os, urllib, time
import logging

def parseSlavesPage(data):
    retval = []
    slaveLine = re.compile("href=\"buildslaves/([A-Za-z].*?)\"")
    statusLine = re.compile("td class=\"(offline|idle|building)\"")

    curSlave = None
    for line in data.split("\n"):
        m = slaveLine.search(line)
        if m:
            curSlave = m.group(1)
            continue
        if not curSlave:
            continue
        m = statusLine.search(line)
        if m:
            status = m.group(1)
            if status == 'offline':
                retval.append( (curSlave, False, False) )
            elif status == 'idle':
                retval.append( (curSlave, True, True) )
            elif status == 'building':
                retval.append( (curSlave, True, False) )
            else:
                raise ValueError("Unknown status line: %s" % line)
            curSlave = None

    return retval

def mergeBuildSlaves(slaves1, slaves2):
    """Merges data about build slaves from two lists of (name, connected, idle) tuples.

    Data for a slave which is connected overrides data for a slave which is disconnected.

    It is an error for a slave to be connected to more than one master.
    """

    slaves1 = dict( (s[0], s[1:]) for s in slaves1)
    slaves2 = dict( (s[0], s[1:]) for s in slaves2)

    retval = {}

    names = set(slaves1.keys())
    names.update(slaves2.keys())

    for name in names:
        c1, i1 = slaves1.get(name, (None, None))
        c2, i2 = slaves2.get(name, (None, None))

        assert not (c1 and c2)

        if c1:
            retval[name] = (c1, i1)
        elif c2:
            retval[name] = (c2, i2)
        else:
            assert not i1
            assert not i2
            retval[name] = (False, False)

    retval = sorted((name, c, i) for name, (c, i) in retval.items())
    return retval

def slaveStatus(quiet, name, connected, idle):
    if quiet:
        return name
    elif not connected:
        return "%s disconnected" % name
    elif idle:
        return "%s idle" % name
    else:
        return "%s busy" % name

def loadRemoteData(url, cache_time=300):
    cacheDir = os.path.expanduser("~/.slaves_cache")
    if not os.path.exists(cacheDir):
        os.makedirs(cacheDir)

    cacheFile = os.path.join(cacheDir, urllib.quote(url, ""))
    if os.path.exists(cacheFile):
        mtime = os.path.getmtime(cacheFile)
        if mtime + cache_time > time.time():
            # Use the cache
            logging.info("Using cached file for %s", url)
            return open(cacheFile).read()
        else:
            logging.info("Cache expired for %s", url)

    logging.info("Downloading %s", url)
    data = urllib.urlopen(url).read()
    open(cacheFile, "w").write(data)

    return data

if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.set_defaults(
            filter=[],
            quiet=False,
            masters=[],
            )
    parser.add_option("--connected", dest="filter", action="append_const",
            const="connected", help="Show connected slaves")
    parser.add_option("--disconnected", dest="filter", action="append_const",
            const="disconnected", help="Show disconnected slaves")
    parser.add_option("--busy", dest="filter", action="append_const",
            const="busy", help="Show busy slaves")
    parser.add_option("--idle", dest="filter", action="append_const",
            const="idle", help="Show idle slaves")
    parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
            help="Show only slave names, not status")

    parser.add_option("--test-masters", dest="masters", action="append_const",
            const="test-masters", help="Load data from test masters")
    parser.add_option("--build-masters", dest="masters", action="append_const",
            const="build-masters", help="Load data from build masters")

    options, masters = parser.parse_args()

    if not options.filter:
        options.filter = ["connected", "disconnected", "busy", "idle"]

    if "test-masters" in options.masters:
        masters.append("http://talos-master02.build.mozilla.org:8012/buildslaves")
        masters.append("http://test-master01.build.mozilla.org:8012/buildslaves")
        masters.append("http://test-master02.build.mozilla.org:8012/buildslaves")
    if "build-masters" in options.masters:
        masters.append("http://production-master01.build.mozilla.org:8010/buildslaves")
        masters.append("http://production-master03.build.mozilla.org:8010/buildslaves")

    if not masters:
        parser.error("You must specify at least one data source")

    if options.quiet:
        level = logging.WARNING
    else:
        level = logging.INFO
    logging.basicConfig(level=level, format="%(message)s")

    slaveData =[]
    for f in masters:
        if f.startswith("http://"):
            data = loadRemoteData(f)
        else:
            data = open(f).read()
        data = parseSlavesPage(data)
        slaveData = mergeBuildSlaves(data, slaveData)

    for name, connected, idle in slaveData:
        if not connected:
            if "disconnected" in options.filter:
                print slaveStatus(options.quiet, name, connected, idle)
            continue
        elif idle and "idle" in options.filter:
            print slaveStatus(options.quiet, name, connected, idle)
        elif not idle and "busy" in options.filter:
            print slaveStatus(options.quiet, name, connected, idle)
