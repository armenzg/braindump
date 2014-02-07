#!/usr/bin/env python2

import re, string

from distutils.version import StrictVersion

class ModeratelyStrictVersion(StrictVersion):
    version_re = re.compile(r'^(\d+) \. (\d+) (\. (\d+))? (\. (\d+))? ([ab](\d+))?$', re.VERBOSE)

    def parse(self, vstring):
        match = self.version_re.match(vstring)
        if not match:
            raise ValueError("problem!")

        major, minor, patch1, patch2, prerelease, prerelease_num = match.group(1, 2, 4, 6, 7, 8)

        if not patch1:
            patch1 = '0'
        if not patch2:
            patch2 = '0'

        self.version = tuple(map(string.atoi, [major, minor, patch1, patch2]))

        if prerelease:
            self.prerelease = (prerelease[0], string.atoi(prerelease_num))

a = ModeratelyStrictVersion('1.2')
b = ModeratelyStrictVersion('1.2.0.4')
c = ModeratelyStrictVersion('1.2.1')

print a < c < b
