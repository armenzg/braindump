#!/usr/bin/env python

import nagiosplugin
import argparse
import logging
import subprocess
import re
from nagiosplugin.state import Ok, Critical, Unknown

# until we have a py2.7 machine to run this on, include missing routine in py2.6
# this also requires a version of nagios plugin that works on py2.6
# from http://stackoverflow.com/questions/4814970/subprocess-check-output-doesnt-seem-to-exist-python-2-6-5
if "check_output" not in dir(subprocess):  # duck punch it in!
    def f(*popenargs, **kwargs):
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        # just grab the output
        output = process.communicate()[0]
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd)
        return output
    subprocess.check_output = f


# set up the default set of products to check
class BouncerProduct(object):
    re_last_code = re.compile(r'''.*^HTTP\S+\s+(\d+)''', re.MULTILINE + re.DOTALL)
    re_last_location = re.compile(r'''..*^Location:\s+(\S+)''', re.MULTILINE + re.DOTALL)

    def __init__(self, product_name, is_localized):
        self.product_name = product_name
        self.is_localized = is_localized
        self.results = {}

    def get_code(self, locale):
        url = "https://download.mozilla.org/?product=%s&os=win&lang=%s" % (self.product_name, locale)
        logging.debug('checking for %s in %s locale at %s', self.product_name, locale, url)
        curl_output = subprocess.check_output(['curl', '-sIL', url])
        # we want to remember the last HTTP code & the last Location value
        try:
            code = self.re_last_code.match(curl_output).group(1)
        except AttributeError:
            code = '999'
        try:
            location = self.re_last_location.match(curl_output).group(1)
        except AttributeError:
            location = '<unknown>'
        logging.debug('key: %s; code: %s; location: %s', locale, code, location)
        self.results.update({locale: {'code': code, 'location': location}})
        return code

    def check_localization(self):
        unique_locations = set()
        for data in self.results.values():
            unique_locations.add(data['location'])
        if not self.is_localized:
            consistent = len(unique_locations) == 1
            if not consistent:
                logging.warn("multiple locales for non-localized %s - found %d different values %s",
                             self.product_name, len(unique_locations),
                             ', '.join(x['location'] for x in self.results.values()))
        else:
            consistent = len(unique_locations) == len(self.results)
            if not consistent:
                logging.warn("duplicate products for localized %s - expected %d found %d different values %s",
                             self.product_name, len(self.results), len(unique_locations),
                             ', '.join(x['location'] for x in self.results.values()))

        return consistent

default_products = [
    # localized_products
    BouncerProduct("firefox-latest", True),
    BouncerProduct("firefox-beta-latest", True),
    # not sure if beta stub intended to be localized, but it is atm
    BouncerProduct("firefox-beta-stub", True),
    # non_localized_products
    BouncerProduct("firefox-nightly-latest", False),
    BouncerProduct("firefox-aurora-latest", False),
    BouncerProduct("firefox-aurora-stub", False),
    BouncerProduct("firefox-release-stub", False),
]


class BouncerEntry(nagiosplugin.Resource):
    """Bouncer Entries to check

    For each product, check if the redirected URL eventually gets to a 2xx
    result. Also, check for locale differentiated URL when applicable

    The `probe` method returns info for two contexts:
        'availability' - whether the URL resolves to a 2xx
        'locale' - whether the locale variation is correct
    """

    def __init__(self, products=None, alt_locale=None):
        self.products = products
        if self.products is None:
            self.products = default_products
        self.locales = ['en-US']
        if alt_locale is None:
            self.locales.append('fr')  # major language, should be everywhere
        else:
            self.locales.append(alt_locale)
        super(BouncerEntry, self).__init__()

    def probe(self):
        logging.info('checking accessibility')
        for product in self.products:
            for locale in self.locales:
                name = '%s %s' % (product.product_name, locale)
                http_code = product.get_code(locale)
                yield nagiosplugin.Metric(name, http_code, context='availability')
            localized_properly = product.check_localization()
            yield nagiosplugin.Metric(product.product_name, localized_properly, context='localized')


class AvailabilityContext(nagiosplugin.Context):
    def evaluate(self, metric, resource):
        # we're good if 200 <= code < 300
        try:
            code = int(metric.value)
            if 200 <= code < 300:
                logging.info('pass on %s availability (%s)', metric.name, metric.value)
                result = self.result_cls(Ok, metric=metric)
            elif 300 <= code < 999:
                logging.warning('WARN on %s availability (%s)', metric.name, metric.value)
                result = self.result_cls(Critical, metric=metric)
            else:
                logging.warning('UNKNOWN on %s availability (%s)', metric.name, metric.value)
                result = self.result_cls(Unknown, metric=metric)
        except ValueError:
            result = self.result_cls(Unknown, metric=metric)
        return result


class LocalizedContext(nagiosplugin.Context):
    def evaluate(self, metric, resource):
        if metric.value:
            result = self.result_cls(Ok, metric=metric)
        else:
            result = self.result_cls(Critical, metric=metric)
        return result


class BouncerSummary(nagiosplugin.Summary):
    def ok(self, results):
        return "pass - %d products checked" % (len(default_products),)

    def problem(self, results):
        return "FAIL - %d products checked" % (len(default_products),)


@nagiosplugin.guarded
def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument('-w', '--warning', metavar='RANGE', default='',
                      help='return warning if load is outside RANGE')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='',
                      help='return critical if load is outside RANGE')
    argp.add_argument('-v', '--verbose', action='count', default=0)
    argp.add_argument('-t', '--timeout', default=30,
                      help='abort execution after TIMEOUT seconds')
    args = argp.parse_args()
    check = nagiosplugin.Check(
        BouncerEntry(),
        AvailabilityContext('availability'),
        LocalizedContext('localized'),
        BouncerSummary(),
    )
    check.main(args.verbose, args.timeout)

if __name__ == '__main__':
    main()
