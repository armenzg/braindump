#!/bin/bash
set -e

PN=reports_rsync
LOCKDIR="/tmp/${PN}"
PIDFILE="${LOCKDIR}/PID"

# exit codes and text
ENO_SUCCESS=0; ETXT[0]="ENO_SUCCESS"
ENO_GENERAL=1; ETXT[1]="ENO_GENERAL"
ENO_LOCKFAIL=2; ETXT[2]="ENO_LOCKFAIL"
ENO_RECVSIG=3; ETXT[3]="ENO_RECVSIG"

trap 'ECODE=$?; echo "[${PN}] Exit: ${ETXT[ECODE]}($ECODE)" >&2' 0

if mkdir "${LOCKDIR}" &>/dev/null; then
    trap 'ECODE=$?;
          echo "[${PN}] Removing lock. Exit: ${ETXT[ECODE]}($ECODE)" >&2
          rm -rf "${LOCKDIR}"' 0
    echo "$$" >"${PIDFILE}"
    trap 'echo "[${PN}] Killed by a signal." >&2
          exit ${ENO_RECVSIG}' 1 2 3 15
else
    # lock failed, check if the other PID is alive
    OTHERPID="$(cat "${PIDFILE}")"
    if [ $? != 0 ]; then
      echo "lock failed, PID ${OTHERPID} is active" >&2
      exit ${ENO_LOCKFAIL}
    fi

    if ! kill -0 $OTHERPID &>/dev/null; then
        echo "removing stale lock of nonexistant PID ${OTHERPID}" >&2
        rm -rf "${LOCKDIR}"
        echo "[${PN}] restarting myself" >&2
        exec "$0" "$@"
    else
        echo "lock failed, PID ${OTHERPID} is active" >&2
        exit ${ENO_LOCKFAIL}
    fi
fi

REMOTE_USER=syncbld
REMOTE_SERVER=cruncher-aws.srv.releng.usw2.mozilla.com

/usr/bin/rsync -r --links --delete ${REMOTE_USER}@${REMOTE_SERVER}:/var/www/html/builds/ /mnt/netapp/relengweb/builddata/reports/
