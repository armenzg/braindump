#!/usr/bin/env python

import argparse
import requests

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-locales-url",
                        default="https://raw.githubusercontent.com/mozilla-b2g/gaia/master/locales/languages_all.json",
                        help="URL of Gaia's languages_all.json")
    parser.add_argument("-p", "--prefix", required=True,
                        help="Prefix to be added to each locale to be used as"
                        " a part of hg.m.o, e.g. releases/gaia-l10n/v2_0")
    args = parser.parse_args()

    locales = requests.get(args.all_locales_url).json()
    for l in locales.iterkeys():
        print "{}/{}".format(args.prefix, l)

if __name__ == '__main__':
    main()
