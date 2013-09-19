import os
import logging
import re
import argparse
import xml.etree.ElementTree as ET

import sh

logging.basicConfig(
    format='%(asctime)-15s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

skip_repos = ('gaia', 'gecko')


def listdir(directory, pattern=None):
    ls = os.listdir(directory)
    # filter out everything except file (even symlinks)
    ls = [f for f in ls
          if os.path.isfile(os.path.join(directory, f))]
    if pattern:
        ls = [f for f in ls if re.search(pattern, f)]
    return ls


def get_all_repos(manifests_dir):
    repos = {}
    for manifest in listdir(manifests_dir, ".xml"):
        tree = ET.parse(os.path.join(manifests_dir, manifest))
        root = tree.getroot()
        remotes = {}
        for r in root.iter('remote'):
            name, fetch = r.attrib['name'], r.attrib['fetch']
            # we can branch git://github.com/mozilla-b2g/ and
            # git://github.com/mozilla/
            if 'github.com/mozilla' in fetch:
                remotes[name] = fetch
        for p in root.iter('project'):
            name, remote = p.attrib['name'], p.attrib.get('remote')
            # gaia vs gaia.git
            if name.endswith(".git"):
                name = name[:-4]
            if name in skip_repos:
                continue
            if remotes.get(remote):
                revision = p.attrib.get("revision")
                if not revision:
                    log.warn("no revision set for %s in %s", name, manifest)
                if revision and \
                   repos.get(name, {}).get("revision") and \
                   repos[name]["revision"] != revision:
                    # prefer master
                    if revision == "master":
                        repos[name]["revision"] = revision
                    log.warn("revision conflict. %s: existing rev %s, new %s",
                             name, repos[name]["revision"], revision)
                else:
                    repos[name] = {
                        "fetch": "%s%s.git" % (remotes[remote], name),
                        "revision": revision
                    }
    return repos


def main(manifests_dir, new_branch, push=False):
    repos = get_all_repos(manifests_dir)
    for name, r in repos.iteritems():
        revision = r["revision"]
        if os.path.isdir(name):
            log.info("pulling %s", name)
            sh.git.pull(_cwd=name)
        else:
            fetch = r["fetch"]
            # ssh remotes
            fetch = fetch.replace("git://github.com/", "git@github.com:")
            log.info("cloning %s from %s", name, fetch)
            sh.git.clone(r["fetch"], name)

        try:
            # try to resolve branch
            sh.git("show-ref", new_branch, _cwd=name)
            log.warn("branch %s already exists in %s. Skipping.", new_branch,
                     name)
        except sh.ErrorReturnCode_1:
            log.info("Creating %s branch in %s based on %s", new_branch, name,
                     revision)
            # FIXME: uncomment the following to branch
            #sh.git.branch(new_branch, "origin/%s" % revision, _cwd=name)

        # PUSH
        if push:
            log.info("pushing %s", name)
            # FIXME: uncomment the line below to push for realz
            #sh.git.push("--dry-run", "origin",
                        #"%s:%s" % (new_branch, new_branch), _cwd=name)
        for m in listdir(manifests_dir, ".xml"):
            f_path = os.path.join(manifests_dir, m)
            text = file(f_path).read()
            with open(f_path, "w") as f:
                for l in text.splitlines():
                    if re.search('<project.*name="%s(\\.git)?"' % name, l):
                        if "revision=" in l:
                            l = re.sub('revision=".*?"',
                                       'revision="%s"' % new_branch, l)
                        else:
                            log.warn("No revision set in %s", l)
                            l = l.replace("/>", 'revision="%s"/>' % new_branch)
                    f.write("%s\n" % l)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--manifests-dir", required=True,
                        help="https://github.com/mozilla-b2g/b2g-manifest"
                        " checkout directory")
    parser.add_argument("-b", "--branch", required=True,
                        help="New branch name")
    parser.add_argument("--push", action="store_true", default=False,
                        help="Push for reals")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Supress logging messages")

    args = parser.parse_args()
    if not args.quiet:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.ERROR)

    main(manifests_dir=args.manifests_dir, new_branch=args.branch,
         push=args.push)
