import os
import subprocess
import time

REPO_FILE='repos.list'


class Repository:
    '''Represent a Mercurial Repository.  This class assumes that file:// is used
    instead of a raw path.  Port numbers, usernames and passwords are to be part
    of the host variable'''
    def __init__(self, host, repository, proto='http:', subdirs=[]):
        self.host = host
        self.repository = repository
        self.proto = proto
        self.subdirs = subdirs
        self.os_subdir = '.'
        for i in subdirs:
            self.os_subdir = os.path.join(self.os_subdir, i)
        self.os_repodir = os.path.join(self.os_subdir, self.repository)
        self.full_host = '%s//%s' % (self.proto, self.host)
        self.url_dir = ''.join(['/%s' % i for i in self.subdirs + [self.repository]])
        self.url = '%s%s' % (self.full_host, self.url_dir)

    def exists(self):
        return os.path.exists(os.path.join(self.os_repodir, '.hg'))

def parse_file(f):
    '''This function takes the path to a repository
    list file and parses it to a list of Repository objects'''
    f = open(f, 'r')
    lines = f.readlines()
    f.close()
    repos = []
    for line in lines:
        if line[-1] == '\n': #make sure there is no new line added
            line = line[:-1]
        tokens = line.split('/')
        #handle the blank string created by '//' HACK
        if tokens[1] == '':
            del tokens[1]
        repos.append(Repository(host=tokens[1],
                                repository=tokens[-1],
                                subdirs=tokens[2:-1],
                                proto=tokens[0],
                                )
                    )
    return repos


def hg_op(repo, operation, logfile, hg_opts=None, op_opts=None, hg='hg'):
    '''This function takes a Repository object and performs operation to it'''
    #the clone, pull and push require the url as an operation argument
    if operation == 'clone' or operation == 'pull' or operation == 'push':
        if op_opts == None:
            op_opts = []
        op_opts.append(repo.url)
    #always have noninteractive mode and default to using --time and --verbose
    if hg_opts == None:
        hg_opts = ['--noninteractive', '--time', '--verbose']
    elif '--noninteractive' not in hg_opts:
        hg_opts.append('--noninteractive')
    if op_opts == None:
        op_opts = []
    command = [hg] + hg_opts + [operation] + op_opts
    if operation == 'clone':
        cwd = repo.os_subdir
    else:
        cwd = repo.os_repodir
    logfile.write('Running command:\n%s\nin "%s"\n' % (command, cwd))
    logfile.flush()
    rc = subprocess.call(command, cwd=cwd, stdout=logfile, stderr=logfile)
    logfile.flush()
    return rc


def process_repo(repo):
    try:
       os.makedirs(repo.os_subdir)
    except OSError, a:
        if a.errno == 17:
            pass #Ignore issues recreating a present file -- might not work elsewhere
        else:
            raise a
    logfile = open(os.path.join(repo.os_subdir, 'hg_%s.log' % repo.repository), 'a+')
    logfile.write('Processing %s - %s\n' % (repo.repository, time.asctime(time.localtime())))
    logfile.write('='*80)
    logfile.write('\n')
    logfile.flush()
    if not repo.exists():
        rc = hg_op(repo, 'clone', logfile, op_opts=['--noupdate'])
    else:
        rc = hg_op(repo, 'pull', logfile)
    if rc != 0:
        logfile.write('WARNING: This repository operation returned a non-zero status (%s)\n' % rc)
    branch_rc = hg_op(repo, 'branches', logfile)
    if branch_rc != 0:
        logfile.write('Could not the branches operation on %s' % repo.repository)
    logfile.write('='*80)
    logfile.write('\n')
    logfile.write('Command finished with RC=%s\n' % rc)
    logfile.flush()
    logfile.close()
    return rc

def main():
    if os.path.exists(REPO_FILE):
        exitcode=0
        print 'Parsing file'
        repos = parse_file(REPO_FILE)
        print 'Processing %d repositories' % len(repos)
        for repo in repos:
            rc = process_repo(repo)
            if rc == 0:
                print 'Success on %s' % repo.repository
            else:
                print 'WARN: updating %s RC=%d' % (repo.repository, rc)
                exitcode=1
        print 'Finished processing repositories'
        exit(exitcode)
    else:
        print 'ERROR: %s does not exist' % REPO_FILE
        exit(1)


if __name__ == '__main__':
    main()
