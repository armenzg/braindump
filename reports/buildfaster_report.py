import simplejson as json
import sqlalchemy as sa
import re, datetime, csv, urllib
import time, redis
import traceback

schedulerdb = sa.create_engine("mysql://buildbot_reader2:aequeG4ahtooz0qu@buildbot-ro-vip.db.scl3.mozilla.com/buildbot_schedulers", pool_recycle=60)
statusdb = sa.create_engine("mysql://buildbot_reader2:aequeG4ahtooz0qu@buildbot-ro-vip.db.scl3.mozilla.com/buildbot", pool_recycle=60)

#import logging
#logging.getLogger('sqlalchemy.pool').setLevel(logging.INFO)

R = redis.Redis("redis01.build.mozilla.org")

def td2secs(td):
    return td.seconds + td.days * 86400

def get_builds(db, branch, startdate, enddate):
    q = """SELECT
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
    branchprefix = branch + "%"
    branchsuffix = "%" + branch

    conn = db.connect()

    return conn.execute(sa.text(q), locals()).fetchall()

def get_props(db, buildrow):
    r_key = "buildfaster:props:%s" % buildrow.id
    retval = R.get(r_key)
    if retval:
        R.set(r_key, retval)
        R.expire(r_key, 86400*2)
        return json.loads(retval)
    q = """SELECT
                name, value
            FROM
                build_properties, properties
            WHERE
                build_properties.property_id = properties.id AND
                build_properties.build_id = :buildid
        """

    retval = {}
    conn = db.connect()
    for k, v in conn.execute(sa.text(q), buildid=buildrow.id).fetchall():
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
        ('osx10.5', ['Rev3 MacOSX Leopard', 'OS X 10.5.2']),
        ('android_armv6', ['Android Armv6']),
        ('android_armv7', ['Android Tegra ']),
        ('android_x86', ['Android X86']),
        ('android_4_x', ['Android 4.']),
        ('android_noion', ['Android no-ionmonkey']),
        ('android', ['Android']),
        ('b2g_gaia', ['b2g_panda_gaia']),
        ('b2g', ['b2g_panda']),
        ('linux64', ['Linux x86-64','B2G gb_armv7a_gecko', 'B2G linux32_gecko', 'B2G ics_armv7a_gecko', 'b2g_mozilla-central_', 'Ubuntu 12.04 x64']),
        ('linux32', ['Linux', 'Rev3 Fedora 12', 'fedora16-i386', 'b2g_ics_armv7a_gecko_emulator', 'Ubuntu 12.04']),
        ('win32', ['WINNT 5.2']),
        ('win64', ['WINNT 6.1 x86-64','B2G win32_gecko']),
        ('win7', ['Rev3 WINNT 6.1']),
        ('winxp', ['Rev3 WINNT 5.1']),
        ('win8', ['Rev3 WINNT 6.2']),
        ]
def get_platform(buildername):
    for os, patterns in _os_patterns:
        for pattern in patterns:
            if re.search(pattern, buildername):
                return os

_ignore_patterns = [
        'l10n',
        'Maemo',
        'Linux RPM',
        'Mobile Desktop',
        'hg bundle',
        'xulrunner',
        'shark',
        'code coverage',
        'blocklist update',
        'valgrind',
        'dxr',
        'hsts',
        ]
def ignore_build(buildername):
    return any(p in buildername for p in _ignore_patterns)

_jobtype_patterns = [
        ('opt pgo test', ['.*pgo test.*']),
        ('opt test', ['.*opt test.*']),
        ('talos', ['.*talos.*']),
        ('debug test', ['.*debug test.*']),
        ('debug build', ['.*leak test build$']),
        ('opt build', ['.*nightly$', '.*build$']),
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
    q = """SELECT
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

    master_name = get_master_dbname(buildrow.master_url)
    conn = schedulerdb.connect()
    rows = conn.execute(sa.text(q),
            #branch=buildrow.branch,
            #revision=buildrow.revision,
            number=buildrow.buildnumber,
            buildername=props['buildername'],
            claimed_by_name=master_name,
            ).fetchall()
    if len(rows) >= 1:
        # Find the closest starttime
        rows.sort(key=lambda row: abs(datetime.datetime.utcfromtimestamp(row.start_time) - buildrow.starttime))
        retval = rows[0].submitted_at
    elif len(rows) == 0:
        #print buildrow
        #print props
        #print master_name
        retval = None
        #assert False
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
        ('.*mochitest-other', ['mochitest-chrome', 'mochitest-browser-chrome', 'mochitest-a11y', 'mochitest-ipcplugins', 'run_script']),
        ('.*jetpack', ['jetpack', 'run_script']),
        ('.*mochitests-\d/\d', ['mochitest-plain-\d', 'run_script']),
        ('.*mochitest-\d', ['mochitest-plain', 'run_script', 'run_script']),
        ('.*robocop.*', ['mochitest-robocop', 'run_script']),
        ('.*talos.*', ['Run performance tests', 'run_script']),
        ('.*browser-chrome', ['mochitest-browser-chrome', 'run_script']),
        ('.*remote-tdhtml', ['mochitest-browser-chrome', 'run_script']),
        ('.*peptest', ['run_script']),
        ('.*marionette', ['run_script']),
        ('Android.*(?!talos)', ['compile', 'make_buildsymbols', 'make_pkg_tests', 'make_pkg', 'run_script']),
        ('(Linux|OS X|WINNT).*', ['compile', 'make_buildsymbols', 'make_pkg_tests', 'make_pkg', 'make_complete_mar', 'run_script']),
        ('b2g', ['compile', 'make_pkg', 'run_script']),
        ('B2G', ['compile', 'make_pkg', 'run_script']),
        ]
def get_worktime(db, buildrow, props):
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
        print "Couldn't determine worksteps for", buildername
        worksteps = None

    worktime = datetime.timedelta()
    overhead = datetime.timedelta()

    # Get the steps
    q = """SELECT * FROM steps WHERE steps.build_id = :buildid"""
    conn = db.connect()
    steps = conn.execute(sa.text(q), dict(buildid=buildrow.id)).fetchall()
    matched = False
    for step in steps:
        if not worksteps:
            print step
            continue

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
        print buildername
        for step in steps:
            print step
        assert False

    if not worksteps:
        assert False
    #print worktime + overhead

    R.set(r_key, td2secs(worktime))
    R.expire(r_key, 86400*2)
    return worktime

import sys
masters = json.load(urllib.urlopen("http://hg.mozilla.org/build/tools/raw-file/default/buildfarm/maintenance/production-masters.json"))

today = datetime.datetime.now().strftime("%Y-%m-%d")
start = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

t = time.time()
builds = get_builds(statusdb, 'mozilla-central', start, today)
#print "get_builds", time.time() - t

output = csv.writer(open(sys.argv[1], 'w'))

output.writerow(['submitted_at', 'revision', 'os', 'jobtype', 'suitename', 'uid', 'results', 'wait_time', 'start_time', 'finish_time', 'elapsed', 'work_time', 'builder_name', 'slave_name'])
for buildrow in builds:
    t = time.time()
    props = get_props(statusdb, buildrow)
    #print "get_props", time.time() - t
    if 'buildername' not in props:
        #print "Skipping"
        #print buildrow
        #print props
        continue

    if ignore_build(props['buildername']):
        continue

    uid = props.get('builduid')
    os = get_platform(props['buildername'])
    jobtype = get_jobtype(props['buildername'])
    suitename = get_suitename(props['buildername'])

    if os is None or jobtype is None:
        print props['buildername']
        assert False, props['buildername']

    t = time.time()
    submitted_at = get_submittime(schedulerdb, buildrow, props)
    #print "get_submittime", time.time() - t
    if not submitted_at:
        continue

    started_at = buildrow.starttime
    finished_at = buildrow.endtime
    revision = get_revision(buildrow)
    wait_time = started_at - submitted_at
    elapsed_time = finished_at - started_at
    results = buildrow.result
    t = time.time()
    work_time = get_worktime(statusdb, buildrow, props)
    buildername = props['buildername']
    slavename = props['slavename']
    #print "get_worktime", time.time() - t

    if True:
        output.writerow([
            submitted_at.strftime("%Y-%m-%dT%H:%M:%S"), revision, os, jobtype,
            suitename, uid, results, wait_time,
            started_at.strftime("%Y-%m-%dT%H:%M:%S"),
            finished_at.strftime("%Y-%m-%dT%H:%M:%S"), elapsed_time, work_time,
            buildername, slavename])
    #print buildrow.buildername, uid, os, jobtype
    if os is None:
        break
    if jobtype is None:
        break
    if revision is None:
        break
