#!/bin/bash
set -e

LOCK=/tmp/reports_rsync
/usr/bin/lockfile-create --retry 1 ${LOCK} 2>&1
trap "/usr/bin/lockfile-remove $LOCK" EXIT

REMOTE_USER=syncbld
REMOTE_SERVER=cruncher-aws.srv.releng.usw2.mozilla.com

/usr/bin/rsync --progress -r --links --delete ${REMOTE_USER}@${REMOTE_SERVER}:/var/www/html/builds/ /mnt/netapp/relengweb/builddata/reports/ 2>&1 | logger -t pull_builddata_reports
