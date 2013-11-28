#!/bin/bash

RAWSLAVE=$1
if [ "${RAWSLAVE}" == "" ]; then
  echo "Usage: ${0} slavename"
  exit 1
fi

if [[ "${RAWSLAVE}" == *"ec2"* ]]; then
  echo 'Downloading host mapping for ec2 slaves...'
  rm -f ec2_slavelist
  wget http://cruncher.build.mozilla.org/~buildduty/hosts -q -O ec2_slavelist
  SLAVE=`grep ${RAWSLAVE} ec2_slavelist | awk '{ print $1 }'`
  # Need to add the trailing : when checking by ip.
  # This prevents us from matching (e.g.) 10.132.58.64 when we're looking for 10.132.58.6
  SLAVE="${SLAVE}:"
else 
  SLAVE=${RAWSLAVE}
fi
echo "Retrieving filehandle for: ${SLAVE}"

MASTER_PID=`ps auxww | grep buildbot | grep start | grep -v grep | awk '{ print $2 }'`
echo "Master PID is:             ${MASTER_PID}"

SLAVE_FH=`/usr/sbin/lsof -p ${MASTER_PID} | grep "${SLAVE}" | grep -v grep | awk '{ gsub("u",""); print $4 }'`
echo "Slave filehandle is:       ${SLAVE_FH}"
#ssh localhost -p 7201 "import os && os.close(${SLAVE_FH}) && exit()" 
