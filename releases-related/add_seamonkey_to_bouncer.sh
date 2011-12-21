#!/bin/bash
# Example script which adds SeaMonkey 2.6.1 to Bouncer
# Run it from tools/release
# Adjust variables below including your Bouncer username and password
# You can also use --credentials-file=/path/to/file which have to be like this:
# tuxedoUsername = 'user'
# tuxedoPassword = 'password'

VERSION=2.6.1
OLDV=2.6
PRODUCT=seamonkey
BRAND=SeaMonkey

USERNAME=
PASSWORD=

PYTHONPATH=../lib/python \
python tuxedo-add.py --config firefox-tuxedo.ini \
  --product $PRODUCT --bouncer-product-name $BRAND --brand-name $BRAND \
  --version $VERSION --old-version $OLDV --milestone $VERSION \
  --platform linux --platform linux64 --platform macosx64 --platform win32 \
  --add-mars \
  --tuxedo-server-url https://bounceradmin.mozilla.com/api/ \
  --username=$USERNAME --password=$PASSWORD

