import os, difflib, urllib2
from release.info import readReleaseConfig, readConfig
from optparse import OptionParser
from util.hg import make_hg_url
import logging
log = logging.getLogger(__name__)

HG_HOST = "hg.mozilla.org"

"""
    This needs to be run in a build-master virtualenv so that it can import from tools/lib/python properly
    eg: ../bin/python ../../braindump/utils/diff_mozconfigs.py --branch mozilla-release -c release-firefox-mozilla-release.py -c release-fennec-mozilla-release.py
"""

def verify_mozconfigs(branch, platforms, revision, whitelist): 
    success = True
    if whitelist:
        mozconfigWhitelist = readConfig(whitelist, ['whitelist'])
    else:
        mozconfigWhitelist = {}
    types = {'+': 'release', '-': 'nightly'}
    for platform in platforms:
        urls = []
        mozconfigs = []
        for type in types.values():
            urls.append(make_hg_url(HG_HOST, 'build/buildbot-configs', 'http', 
                                revision, os.path.join('mozilla2', platform, 
                                branch, type,'mozconfig')))
        for url in urls:
            try:
                mozconfigs.append(urllib2.urlopen(url).readlines())
            except urllib2.HTTPError as e:
                log.error("MISSING: %s - ERROR: %s" % (url, e.msg))
        diffInstance = difflib.Differ()
        if len(mozconfigs) == 2:
            log.info("Comparing %s..." % platform)
            diffList = list(diffInstance.compare(mozconfigs[0],mozconfigs[1]))
            for line in diffList:
                clean_line = line[1:].strip()
                if (line[0] == '-'  or line[0] == '+') and len(clean_line) > 1:
                    # skip comment lines
                    if clean_line.startswith('#'):
                        continue
                    # compare to whitelist
                    if line[0] == '-' and mozconfigWhitelist.get(branch, {}).has_key(platform) \
                        and clean_line in mozconfigWhitelist[branch][platform]:
                            continue
                    if line[0] == '+' and mozconfigWhitelist.get('nightly', {}).has_key(platform) \
                        and clean_line in mozconfigWhitelist['nightly'][platform]:
                            continue
                    if line[0] == '-':
                        opposite = 'release'
                    else:
                        opposite = 'nightly'
                    log.error("not in %s mozconfig's whitelist (%s/%s/%s) : %s" % (opposite, branch, platform, types[line[0]], clean_line))
                    success = False
        else:
            log.info("Missing mozconfigs to compare for %s" % platform)
        
    return success

if __name__ == '__main__':
    parser = OptionParser(__doc__)
    parser.set_defaults(
            whitelist='../tools/buildbot-helpers/mozconfig_whitelist',
            loglevel=logging.INFO,
            revision='tip',
            )
    parser.add_option("-w", "--whitelist", dest="whitelist",
            help="whitelist for known mozconfig differences")
    parser.add_option("-r", "--revision", dest="revision",
            help="revision to pull")
    parser.add_option("-c", "--release-config", dest="releaseConfigFiles",
            action="append",
            help="specify the release-config files (the first is primary)")
    parser.add_option("-B", "--branch", dest="branch",
            help="branch name for this release, uses release_config otherwise")
    options, args = parser.parse_args()

    logging.basicConfig(level=options.loglevel,
            format="%(asctime)s : %(levelname)s : %(message)s")

    if not options.branch or not options.releaseConfigFiles:
        sys.exit(1)
    else:
        test_success = True
        for releaseConfigFile in list(reversed(options.releaseConfigFiles)):
            releaseConfig = readReleaseConfig(releaseConfigFile)
    
            if not verify_mozconfigs(
                options.branch,
                releaseConfig['enUSPlatforms'],
                options.revision,
                options.whitelist
            ):
                test_success = False
                log.error("Verifying mozconfigs for %s failed." % releaseConfigFile)
            else:
                log.info("Verifying mozconfigs for %s passed." % releaseConfigFile)