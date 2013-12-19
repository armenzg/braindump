import simplejson as json
import sqlalchemy as sa
import re, datetime, csv, urllib
import time, redis
import traceback
import argparse
import logging

schedulerdb = sa.create_engine("mysql://buildbot_reader2:aequeG4ahtooz0qu@buildbot-ro-vip.db.scl3.mozilla.com/buildbot_schedulers", pool_recycle=60)
statusdb = sa.create_engine("mysql://buildbot_reader2:aequeG4ahtooz0qu@buildbot-ro-vip.db.scl3.mozilla.com/buildbot", pool_recycle=60)

builds_sql = """SELECT
             builders.name as buildername,
             builds.*,
             sourcestamps.branch, sourcestamps.revision,
             masters.url as master_url
       FROM
             builds, builders, sourcestamps, masters
       WHERE
             builds.master_id = masters.id AND
             builds.builder_id = builders.id AND
             builds.source_id = sourcestamps.id AND
             (
              sourcestamps.branch LIKE :branchprefix OR
              sourcestamps.branch LIKE :branchsuffix
             ) AND
             builds.starttime >= :startdate AND
             builds.endtime < :enddate AND
             builds.result != 5
       ORDER BY
             builds.starttime ASC
"""
props_sql = """SELECT
              name, value
       FROM
              build_properties, properties
       WHERE
              build_properties.property_id = properties.id AND
              build_properties.build_id = :buildid
"""
submittime_sql = """SELECT
              buildrequests.*, builds.*
       FROM
              buildsets, buildrequests, builds
       WHERE
              buildrequests.buildsetid = buildsets.id AND
              builds.brid = buildrequests.id AND
              builds.number = :number AND
              buildrequests.buildername = :buildername AND
              buildrequests.claimed_by_name = :claimed_by_name
"""
worksteps_sql = """SELECT * FROM steps WHERE steps.build_id = :buildid"""

R = redis.Redis("redis01.build.mozilla.org")

@sa.event.listens_for(sa.pool.Pool, "checkout")
def check_connection(dbapi_con, con_record, con_proxy):
    '''Listener for Pool checkout events that pings every connection before using.
    Implements pessimistic disconnect handling strategy. See also:
    http://docs.sqlalchemy.org/en/rel_0_8/core/pooling.html#disconnect-handling-pessimistic'''

    cursor = dbapi_con.cursor()
    try:
        cursor.execute("SELECT 1")  # could also be dbapi_con.ping(),
                                    # not sure what is better
    except sa.exc.OperationalError, ex:
        if ex.args[0] in (2006,   # MySQL server has gone away
                          2013,   # Lost connection to MySQL server during query
                          2055):  # Lost connection to MySQL server at '%s', system error: %d
            # caught by pool, which will retry with a new connection
            raise sa.exc.DisconnectionError()
        else:
            raise

def td2secs(td):
    return td.seconds + td.days * 86400

def get_builds(branch, startdate, enddate):
    branchprefix = branch + "%"
    branchsuffix = "%" + branch
    statusdb_conn = statusdb.connect()
    return statusdb_conn.execute(builds_q,
                                 branchprefix=branchprefix,
                                 branchsuffix=branchsuffix,
                                 startdate=startdate,
                                 enddate=enddate
                                 ).fetchall()

def get_props(buildrow):
    r_key = "buildfaster:props:%s" % buildrow.id
    retval = R.get(r_key)
    if retval:
        R.set(r_key, retval)
        R.expire(r_key, 86400*2)
        return json.loads(retval)

    retval = {}
    statusdb_conn = statusdb.connect()
    for k, v in statusdb_conn.execute(props_q, buildid=buildrow.id).fetchall():
        if v is not None:
            v = json.loads(v)
        retval[k] = v
    R.set(r_key, json.dumps(retval))
    R.expire(r_key, 86400*2)
    return retval

_os_patterns = [
        ('osx10.6', ['Rev3 MacOSX Snow Leopard', 'OS X 10.6.2']),
        ('osx10.6-r4', ['Rev4 MacOSX Snow Leopard']),
        ('osx10.7-r4', ['Rev4 MacOSX Lion']),
        ('osx10.7', ['OS X 10.7', 'B2G macosx64_gecko']),
        ('osx10.8', ['Rev5 MacOSX Mountain Lion 10.8']),
        ('osx10.9', ['Rev5 MacOSX Mavericks 10.9']),
        ('osx10.5', ['Rev3 MacOSX Leopard', 'OS X 10.5.2']),
        ('android_armv6', ['Android Armv6',
                           'Android 2.2 Armv6']),
        ('android_armv7', ['Android Tegra ',
                           'Android 2.2 Tegra ']),
        ('android_x86', ['Android x86',
                         'Android 4.2 x86']),
        ('android_4_x', ['Android 4.0']),
        ('android_noion', ['Android no-ionmonkey',
                           'Android 2.2 no-ionmonkey']),
        ('android', ['Android']),
        ('b2g_hamachi_dep', ['b2g_mozilla-central_hamachi_dep',
                             'b2g_mozilla-central_hamachi_eng_dep']),
        ('b2g_helix_dep', ['b2g_mozilla-central_helix_dep',
                           'b2g_mozilla-central_helix_eng_dep']),
        ('b2g_inari_dep', ['b2g_mozilla-central_inari_dep',
                           'b2g_mozilla-central_inari_eng_dep']),
        ('b2g_leo_dep', ['b2g_mozilla-central_leo_dep',
                         'b2g_mozilla-central_leo_eng_dep']),
        ('b2g_nexus-4_dep', ['b2g_mozilla-central_nexus-4_dep',
                             'b2g_mozilla-central_nexus-4_eng_dep']),
        ('b2g_panda_dep', ['b2g_mozilla-central_panda_dep',
                           'b2g_mozilla-central_panda_eng_dep']),
        ('b2g_unagi_dep', ['b2g_mozilla-central_unagi_dep',
                           'b2g_mozilla-central_unagi_eng_dep']),
        ('b2g_emulator', ['b2g_mozilla-central_emulator', 'b2g_emulator']),
        ('b2g_linux32', ['b2g_mozilla-central_linux32_gecko',
                         'b2g_mozilla-central_linux32_gecko_locali|zer']),
        ('b2g_linux64', ['b2g_mozilla-central_linux64_gecko',
                         'b2g_mozilla-central_linux64_gecko_localizer']),
        ('b2g_osx', ['b2g_mozilla-central_macosx64_gecko',
                     'b2g_mozilla-central_macosx64_gecko_localizer']),
        ('b2g_hamachi', ['b2g_mozilla-central_hamachi_nightly',
                         'b2g_mozilla-central_hamachi_eng_nightly']),
        ('b2g_helix', ['b2g_mozilla-central_helix_nightly',
                       'b2g_mozilla-central_helix_eng_nightly']),
        ('b2g_inari', ['b2g_mozilla-central_inari_nightly',
                       'b2g_mozilla-central_inari_eng_nightly']),
        ('b2g_leo', ['b2g_mozilla-central_leo_nightly',
                     'b2g_mozilla-central_leo_eng_nightly']),
        ('b2g_nexus-4', ['b2g_mozilla-central_nexus-4_nightly',
                         'b2g_mozilla-central_nexus-4_eng_nightly']),
        ('b2g_panda', ['b2g_mozilla-central_panda_nightly',
                       'b2g_mozilla-central_panda_eng_nightly']),
        ('b2g_unagi', ['b2g_mozilla-central_unagi_nightly',
                       'b2g_mozilla-central_unagi_eng_nightly']),
        ('b2g_win32', ['b2g_mozilla-central_win32_gecko',
                       'b2g_mozilla-central_win32_gecko_localizer']),
        ('b2g_panda', ['b2g_panda']),
        ('linux64', ['Linux x86-64', 'linux64',
                     'Ubuntu 12.04 x64', 'Ubuntu VM 12.04 x64', 'Ubuntu HW 12.04 x64', 'Ubuntu ASAN VM 12.04 x64',
                     'b2g_ubuntu64_vm']),
        ('linux32', ['Linux',
                     'Rev3 Fedora 12', 'fedora16-i386',
                     'Ubuntu 12.04', 'Ubuntu VM 12.04', 'Ubuntu HW 12.04', 'Ubuntu ASAN VM 12.04',
                     'b2g_ubuntu32_vm']),
        ('win32', ['WINNT 5.2']),
        ('win64', ['WINNT 6.1 x86-64']),
        ('win7', ['Rev3 WINNT 6.1', 'Windows 7 32-bit']),
        ('winxp', ['Rev3 WINNT 5.1', 'Windows XP 32-bit']),
        ('win8', ['WINNT 6.2']),
        ]

def get_platform(buildername):
    for os, patterns in _os_patterns:
        for pattern in patterns:
            if re.search(pattern, buildername):
                return os

_ignore_patterns = [
        'l10n',
        'hg bundle',
        'xulrunner',
        'blocklist update',
        'valgrind',
        'hsts',
        'dxr',
        'br-haz'
        ]

def ignore_build(buildername):
    return any(p in buildername for p in _ignore_patterns)

_jobtype_patterns = [
        ('opt pgo test', ['.*pgo test.*']),
        ('opt test', ['.*opt test.*']),
        ('talos', ['.*talos.*']),
        ('debug test', ['.*debug test.*']),
        ('debug build', ['.*leak test build$', '.*br-haz.*']),
        ('opt build', ['.*nightly$', '.*build$']),
        ('b2g test', ['b2g_ubuntu64_vm','B2G.*']),
        ('b2g build', ['b2g.*','B2G.*']),
        ]

def get_jobtype(buildername):
    for jobtype, patterns in _jobtype_patterns:
        for pattern in patterns:
            if re.match(pattern, buildername):
                return jobtype

def get_suitename(buildername):
    test_names = ['opt test', 'debug test', 'talos']
    if not any(t in buildername for t in test_names):
        return None

    return buildername.split()[-1]

def get_submittime(schedulerdb, buildrow, props):
    r_key = "buildfaster:submittime:%s" % buildrow.id
    if R.exists(r_key):
        try:
            retval = R.get(r_key)
            R.set(r_key, retval)
            R.expire(r_key, 86400*2)
            if retval is None or retval == 'None':
                return None
            return datetime.datetime.utcfromtimestamp(int(retval))
        except:
            traceback.print_exc()
            R.delete(r_key)

    master_name = get_master_dbname(buildrow.master_url)
    schedulerdb_conn = schedulerdb.connect()
    rows = schedulerdb_conn.execute(
        submittime_q,
        number=buildrow.buildnumber,
        buildername=props['buildername'],
        claimed_by_name=master_name,
        ).fetchall()
    if len(rows) >= 1:
        # Find the closest starttime
        rows.sort(key=lambda row: abs(datetime.datetime.utcfromtimestamp(row.start_time) - buildrow.starttime))
        retval = rows[0].submitted_at
    elif len(rows) == 0:
        logger.debug(str(buildrow))
        logger.debug(str(props))
        logger.debug(str(master_name))
        retval = None
        if args.assert_on_missing:
            assert False
        return None
    R.set(r_key, retval)
    R.expire(r_key, 86400*2)
    if retval is None:
        return None
    return datetime.datetime.utcfromtimestamp(retval)

def get_revision(buildrow):
    return buildrow.revision

def get_master_dbname(master_url):
    name = master_url[len("http://"):]
    name, port = name.split(":")
    port = int(port)
    name = name.split(".")[0]

    for m in masters:
        if m['db_name'].startswith(name) and m['http_port'] == port:
            return m['db_name']

def get_masterurl(claimed_by_name):
    for m in masters:
        if m['db_name'] == claimed_by_name:
            hostname = m['db_name'].split(":")[0]
            port = m['http_port']
            return "http://%s:%s" % (hostname, port)

_worksteps = [
        ('.*jsreftest', ['jsreftest', 'run_script']),
        ('.*reftest-no-accel', ['opengl-no-accel', 'reftest-no-d2d-d3d', 'run_script']),
        ('.*reftest', ['reftest', 'run_script']),
        ('.*reftest-ipc', ['reftest', 'run_script']),
        ('.*crashtest', ['crashtest', 'run_script']),
        ('.*xpcshell', ['xpcshell', 'run_script']),
        ('.*cppunit', ['run_script']),
        ('.*mochitest-other', ['mochitest-chrome', 'mochitest-browser-chrome', 'mochitest-a11y', 'mochitest-ipcplugins', 'run_script']),
        ('.*jetpack', ['jetpack', 'run_script', 'testpkgs', 'testaddons']),
        ('.*mochitests-\d/\d', ['mochitest-plain-\d', 'run_script']),
        ('.*mochitest-metro-chrome', ['mochitest-metro-chrome', 'run_script']),
        ('.*mochitest-\d', ['mochitest-plain', 'run_script']),
        ('.*mochitest-gl', ['mochitest-plain', 'run_script']),
        ('.*robocop.*', ['mochitest-robocop', 'run_script']),
        ('.*talos.*', ['Run performance tests', 'run_script']),
        ('.*browser-chrome', ['mochitest-browser-chrome', 'run_script']),
        ('.*remote-tdhtml', ['mochitest-browser-chrome', 'run_script']),
        ('.*peptest', ['run_script']),
        ('.*marionette', ['run_script']),
        ('Android.*(?!talos)', ['compile', 'make_buildsymbols', 'make_pkg_tests', 'make_pkg', 'run_script']),
        ('(Linux|OS X|WINNT).*', ['compile', 'make_buildsymbols', 'make_pkg_tests', 'make_pkg', 'make_complete_mar', 'run_script', 'check']),
        ('b2g', ['compile', 'make_pkg', 'run_script']),
        ('B2G', ['compile', 'make_pkg', 'run_script']),
        ]

def get_worktime(buildrow, props):
    r_key = "buildfaster:worktime:%s" % buildrow.id
    retval = R.get(r_key)
    if retval:
        try:
            R.set(r_key, retval)
            R.expire(r_key, 86400*2)
            return datetime.timedelta(seconds=int(retval))
        except:
            traceback.print_exc()
            R.delete(r_key)

    buildername = props['buildername']
    for builder, worksteps in _worksteps:
        if re.match(builder, buildername):
            break
    else:
        logger.warning("Couldn't determine worksteps for %s", buildername)
        worksteps = None
        if args.assert_on_missing:
            assert False

    worktime = datetime.timedelta()
    overhead = datetime.timedelta()

    matched = False
    if not worksteps:
        logger.debug('No worksteps to match. Skipping step lookup.')
    else:
        # Get the steps
        statusdb_conn = statusdb.connect()
        steps = statusdb_conn.execute(worksteps_q, buildid=buildrow.id).fetchall()
        for step in steps:
            if any(re.match(ws, step.name) for ws in worksteps):
                matched = True
                if not step.starttime or not step.endtime:
                    continue
                worktime += (step.endtime - step.starttime)
            else:
                if not step.starttime or not step.endtime:
                    continue
                overhead += (step.endtime - step.starttime)

    if not matched:
        logger.warning("Workstep not matched.")
        logger.warning(buildername)
        # New builds may introduce new steps. Spit out a list of steps
        # when running in debug mode so we can make additions. Our warnings
        # above will let us know when we should turn debug on.
        for step in steps:
            logger.debug(step)
        if args.assert_on_missing:
            assert False
        return None

    logger.debug("worktime + overhead: %s", worktime + overhead)

    R.set(r_key, td2secs(worktime))
    R.expire(r_key, 86400*2)
    return worktime

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csvfile", type=str, help="CSV outputfile")
    parser.add_argument("-v", "--verbose", help="Output debug info",
                        action="store_true")
    parser.add_argument("-a", "--assert_on_missing", help="Assert on missing lookups",
                        action="store_true")
    args = parser.parse_args()

    logger = logging.getLogger('buildfaster')
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    else :
        logger.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    if not args.csvfile:
        logger.warning("csvfile not set!")
        assert args.csvfile

    # Do db query setup
    builds_q = sa.text(builds_sql)
    props_q = sa.text(props_sql)
    submittime_q = sa.text(submittime_sql)
    worksteps_q =  sa.text(worksteps_sql)

    masters = json.load(urllib.urlopen("http://hg.mozilla.org/build/tools/raw-file/default/buildfarm/maintenance/production-masters.json"))

    start = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    t = time.time()
    builds = get_builds('mozilla-central', start, today)
    logger.debug("get_builds: %s", str(time.time() - t))

    output = csv.writer(open(args.csvfile, 'w'))
    output.writerow(['submitted_at', 'revision', 'os', 'jobtype', 'suitename', 'uid', 'results', 'wait_time', 'start_time', 'finish_time', 'elapsed', 'work_time', 'builder_name', 'slave_name'])

    for buildrow in builds:
        t = time.time()
        props = get_props(buildrow)
        logger.debug("get_props: %s", str(time.time() - t))
        if 'buildername' not in props:
            logger.debug("Skipping...")
            logger.debug(str(buildrow))
            logger.debug(str(props))
            continue

        if ignore_build(props['buildername']):
            continue

        uid = props.get('builduid')
        os = get_platform(props['buildername'])
        jobtype = get_jobtype(props['buildername'])
        suitename = get_suitename(props['buildername'])

        if os is None or jobtype is None:
            if os is None:
                logger.warning("OS lookup failed")
            elif jobtype is None:
                logger.warning("Jobtype lookup failed")
            logger.warning(props['buildername'])
            if args.assert_on_missing:
                assert False, props['buildername']
            continue

        t = time.time()
        submitted_at = get_submittime(schedulerdb, buildrow, props)
        logger.debug("get_submittime: %s", str(time.time() - t))
        if not submitted_at:
            continue

        started_at = buildrow.starttime
        finished_at = buildrow.endtime
        revision = get_revision(buildrow)
        if revision is None:
            if args.assert_on_missing:
                assert False
            continue
        wait_time = started_at - submitted_at
        elapsed_time = finished_at - started_at
        results = buildrow.result
        t = time.time()
        work_time = get_worktime(buildrow, props)
        if work_time is None:
            if args.assert_on_missing:
                assert False
            continue

        buildername = props['buildername']
        slavename = props['slavename']
        logger.debug("get_worktime: %s", str(time.time() - t))

        output.writerow([
            submitted_at.strftime("%Y-%m-%dT%H:%M:%S"), revision, os, jobtype,
            suitename, uid, results, wait_time,
            started_at.strftime("%Y-%m-%dT%H:%M:%S"),
            finished_at.strftime("%Y-%m-%dT%H:%M:%S"), elapsed_time, work_time,
            buildername, slavename])
        logger.debug("%s %s %s %s", buildrow.buildername, uid, os, jobtype)
