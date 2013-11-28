import os
import logging
import re
import argparse
import xml.etree.ElementTree as ET

import sh

logging.basicConfig(
    format='%(asctime)-15s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

skip_repos = (
    'gaia',  # branched separately
    'gecko',  # branched by syncyng from HG
)


def listdir(directory, pattern=None):
    ls = os.listdir(directory)
    # filter out everything except file (even symlinks)
    ls = [f for f in ls
          if os.path.isfile(os.path.join(directory, f))
          and not os.path.islink(os.path.join(directory, f))]
    if pattern:
        ls = [f for f in ls if re.search(pattern, f)]
    return ls


def get_all_repos(manifests_dir, branch_order):
    repos = {}
    for manifest in listdir(manifests_dir, ".xml"):
        log.info("processing %s", manifest)
        tree = ET.parse(os.path.join(manifests_dir, manifest))
        root = tree.getroot()
        default = root.find("default")
        if default is not None:
            default_revison = default.attrib["revision"]
        else:
            default_revison = None
        remotes = {}
        for r in root.iter('remote'):
            name, fetch = r.attrib['name'], r.attrib['fetch']
            # we can branch git://github.com/mozilla-b2g/ and
            # git://github.com/mozilla/
            if 'github.com/mozilla' in fetch:
                log.debug("I'll process %s, because I can push to %s", name,
                          fetch)
                remotes[name] = fetch
            else:
                log.debug("Ignoring %s, because I cannot push to %s", name,
                          fetch)
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
                    if default_revison:
                        log.warn("%s: %s, using default revision (%s)",
                                 manifest, name, default_revison)
                        revision = default_revison
                if revision and \
                   repos.get(name, {}).get("revision") and \
                   repos[name]["revision"] != revision:
                    if revision in branch_order:
                        if repos[name]["revision"] not in branch_order or \
                           branch_order.index(revision) < branch_order.index(repos[name]["revision"]):
                            log.info("Prefering %s over %s for %s", revision,
                                     repos[name]["revision"], name)
                            repos[name]["revision"] = revision
                    repos[name]["manifests"].append(manifest)
                    repos[name]["revisions"].append(revision)
                    log.warn(
                        "revision conflict in %s. %s: existing rev %s, new %s %s",
                        repos[name]["manifests"], name,
                        repos[name]["revision"], revision,
                        repos[name]["revisions"])
                else:
                    repos[name] = {
                        "fetch": "%s%s.git" % (remotes[remote], name),
                        "revision": revision,
                        "revisions": [revision],
                        "manifests": [manifest]
                    }
    for name, r in repos.iteritems():
        if r["revision"] is None:
            log.warn("Sanity: No revision set for %s %s", name, r["fetch"])
    return repos


def main(manifests_dir, new_branch, branch_order, push=False):
    repos = get_all_repos(manifests_dir, branch_order)
    for name, r in repos.iteritems():
        revision = r["revision"]
        if os.path.isdir(name):
            log.info("fetching %s", name)
            sh.git.fetch(_cwd=name)
        else:
            fetch = r["fetch"]
            # ssh remotes
            fetch = fetch.replace("git://github.com/", "git@github.com:")
            log.info("cloning %s from %s", name, fetch)
            sh.git.clone(fetch, name)

        try:
            # try to resolve branch
            sh.git("show-ref", new_branch, _cwd=name)
            log.warn("branch %s already exists in %s. Skipping.", new_branch,
                     name)
        except sh.ErrorReturnCode_1:
            log.info("Creating %s branch in %s based on %s", new_branch, name,
                     revision)
            sh.git.branch(new_branch, "origin/%s" % revision, _cwd=name)

        if push:
            log.info("pushing %s", name)
            sh.git.push("origin", "%s:%s" % (new_branch, new_branch),
                        _cwd=name)
        for m in listdir(manifests_dir, ".xml"):
            f_path = os.path.join(manifests_dir, m)
            text = file(f_path).read()
            with open(f_path, "w") as f:
                for l in text.splitlines():
                    if re.search('<project.*name="%s(\\.git)?"' % name, l):
                        if "revision=" in l:
                            # check if the initial branching point matches
                            # manifest revision, don't touch otherwise
                            name = re.search(r'\bname="([^"]+)"',
                                             l).groups()[0]
                            revision = re.search(r'\brevision="([^"]+)"',
                                                 l).groups()[0]
                            if repos[name]["revision"] == revision:
                                l = re.sub('revision=".*?"',
                                           'revision="%s"' % new_branch, l)
                            else:
                                log.warn("Not updating %s's %s revision (%s), "
                                         "because it is ponting to a revision "
                                         "different from our branchig point "
                                         "%s.", m, name, revision,
                                         repos[name]["revision"])
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
    parser.add_argument("--branch-order", required=True,
                        help="Coma separated list of branches to be used in "
                        "case if manifests contain conflicting references, "
                        "e.g. --branch-order v1.2,master")
    parser.add_argument("--push", action="store_true", default=False,
                        help="Push for reals")
    parser.add_argument("-v", "--verbose", action="count",
                        help="Verbose mode")

    args = parser.parse_args()
    if args.verbose == 1:
        log.setLevel(logging.INFO)
    elif args.verbose >= 2:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.WARNING)
    branch_order = args.branch_order.split(",")

    main(manifests_dir=args.manifests_dir, new_branch=args.branch,
         push=args.push, branch_order=branch_order)
