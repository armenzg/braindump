import fabric
from fabric.api import run, env
from fabric.context_managers import cd, hide, show
from fabric.operations import put

def _make_master_config(name, hostname, role, basedir):
    return {
            'name': name,
            'hostname': hostname,
            'roles': [role],
            'basedir': basedir,
            'master_dir': '%s/master' % basedir,
            'bbcustom_dir': '%s/buildbotcustom' % basedir,
            'bbconfigs_dir': '%s/buildbot-configs' % basedir,
            }

def _role_filter(masters):
    """Returns a list of masters that have roles in env.roles.  This is
    required because one host can have multiple masters on it, each with
    different roles"""
    if not env.roles:
        return masters

    retval = []
    for m in masters:
        for r in m.get('roles', []):
            if r in env.roles:
                retval.append(m)
                break
        else:
            continue
    return retval

def _make_masters(masters):
    # Construct the list of hosts and parameters
    env.masters = {}
    orig_hosts = env.hosts
    env.hosts = []
    for m in masters:
        if orig_hosts and m['name'] not in orig_hosts:
            continue
        # Fix up basedir
        if 'basedir' not in m:
            m['basedir'] = m['master_dir']

        # If roles have already been specified, e.g. on the commandline, then don't
        # add to the list of hosts to operate on
        if not env.roles:
            env.hosts.append(m['hostname'])
        env.masters.setdefault(m['hostname'], []).append(m)
        roles = m.get('roles', [])
        for r in roles:
            env.roledefs.setdefault(r, []).append(m['hostname'])

    fabric.state.output['running'] = False
    env.user = 'cltbld'

def check():
    """Checks that the master parameters are valid"""
    with hide('stdout', 'stderr'):
        run('date')
        for m in _role_filter(env.masters[env.host_string]):
            run('test -d %(bbcustom_dir)s' % m)
            run('test -d %(bbconfigs_dir)s' % m)
            run('test -d %(master_dir)s' % m)
            branch = run("hg -R %(bbcustom_dir)s branch" % m)
            assert branch == "default", branch

def checkconfig():
    """Runs buildbot checkconfig"""
    check()
    with hide('stdout', 'stderr'):
        for m in _role_filter(env.masters[env.host_string]):
            with cd(m['basedir']):
                try:
                    run('make checkconfig')
                    print "%-14s OK" % m['name']
                except:
                    print "%-14s FAILED" % m['name']
                    raise

def show_revisions():
    """Reports the revisions of buildbotcustom, buildbot-configs"""
    check()
    for m in _role_filter(env.masters[env.host_string]):
        with hide('stdout', 'stderr'):
            bbcustom_rev = run('hg -R %(bbcustom_dir)s ident' % m)
            bbconfigs_rev = run('hg -R %(bbconfigs_dir)s ident' % m)

            bbcustom_rev = bbcustom_rev.split()[0]
            bbconfigs_rev = bbconfigs_rev.split()[0]
            print "%-14s %12s %12s" % (m['name'], bbcustom_rev, bbconfigs_rev)

def reconfig():
    with show('running'):
        for m in _role_filter(env.masters[env.host_string]):
            # Copy buildbot-wrangler
            with cd(m['master_dir']):
                put('buildbot-wrangler.py', '%s/buildbot-wrangler.py' % m['master_dir'])
                run('rm -f *.pyc')
                run('python buildbot-wrangler.py reconfig .')

def stop():
    with show('running'):
        for m in _role_filter(env.masters[env.host_string]):
            with cd(m['basedir']):
                run('echo make stop')
                # TODO: Wait for process to exit

def start():
    with show('running'):
        for m in _role_filter(env.masters[env.host_string]):
            with cd(m['basedir']):
                run('echo rm *.pyc')
                run('echo make start')

def update():
    with show('running'):
        for m in _role_filter(env.masters[env.host_string]):
            with cd(m['bbcustom_dir']):
                run('hg pull')
                run('hg update -r default')
            with cd(m['bbconfigs_dir']):
                run('hg pull')
                run('hg update -r default')
