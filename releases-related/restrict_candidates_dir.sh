#!/bin/bash
# vim: sw=4 sts=4 et ai:

set -eu

USAGE="usage: ${0##*/} version new_build_number
Create and restrict the shadow build dir for FF Desktop
needed until https://bugzil.la/865701 resolved

Arguements:
    version     numeric version, e.g. '19.3.4'
    new_build_number    the new build to be hidden, e.g. '2'
"

warn() { for m; do echo "$m"; done 2>&1; }
die() { warn "$@" ; exit 1; }
usage() { warn "$@" "${USAGE:-}" ; test $# -eq 0; exit $? ; }

test $# -eq 2 || usage "incorrect number of args: $#"
VERSION="$1"
BUILD="$2"
candidates_dir=/mnt/netapp/stage/archive.mozilla.org/pub/firefox/candidates/$VERSION-candidates/build$BUILD
old_build=`expr $BUILD - 1`
test -d ${candidates_dir%$BUILD}$old_build || die "Old build doesn't exist."
mkdir -p $candidates_dir
cp -ip ~/release-htpasswd $candidates_dir/.htpasswd
# We don't care if people who can access the directory can read this file
chmod 644 $candidates_dir/.htpasswd
cat > $candidates_dir/.htaccess <<_END
Satisfy Any

AuthType Basic
AuthName "Please use build$old_build unless you are validating this release for Mozilla"
AuthUserFile $candidates_dir/.htpasswd
Require valid-user

SetEnvIf X-Cluster-Client-Ip "^63\.245\.2(08|09|1[0-9]|2[0-3])" mozilla

SetEnvIf X-Cluster-Client-Ip "^80\.97\.161\.([0-9]|[1-8][0-9]|9[0-5])" mozilla

SetEnvIf X-Cluster-Client-Ip "^188\.27\.147\.153$" mozilla
SetEnvIf X-Cluster-Client-Ip "^82\.137\.35\.243$" mozilla

Order allow,deny
Allow from env=mozilla
_END
echo "directory created and protected @"
echo " https://ftp.mozilla.org/pub/mozilla.org/firefox/candidates/${VERSION}-candidates/build${BUILD}/"
echo "you should get warned away from that directory with authentication"
