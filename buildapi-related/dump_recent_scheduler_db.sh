#!/bin/bash

# Creates a directory containing the schema of the buildbot_schedulers db, and then a
# data dump of each table in the db. We dump each table individually because not all 
# tables have the same key for sorting purposes.
#
# By default, it will dump the most recent entries from each table.
#
# The schema is accurate as of 2013/11/15. It's a good idea to double-check the schema before 
# to see if new tables have been added before plowing ahead with the data.

ROW_LIMIT=100000
USER=buildbot2
HOST=buildbot-rw-vip.db.scl3.mozilla.com
DB=buildbot_schedulers
ORDER=DESC
TABLE_DIR=scheduler_tables

mkdir -p ${TABLE_DIR}

# Dump the schema first.
mysqldump -d --databases ${DB} -u ${USER} -p -h ${HOST} > ./${TABLE_DIR}/buildbot_schedulers_schema.sql

# Now dump each table individually.
mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables buildrequests \
  > ./scheduler_tables/buildrequests.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables builds \
  > ./scheduler_tables/builds.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY buildsetid ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables buildset_properties \
  > ./scheduler_tables/buildset_properties.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables buildsets \
  > ./scheduler_tables/buildsets.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY changeid ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables change_files \
  > ./scheduler_tables/change_files.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY changeid ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables change_links \
  > ./scheduler_tables/change_links.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY changeid ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables change_properties \
  > ./scheduler_tables/change_properties.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY changeid ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables changes \
  > ./scheduler_tables/changes.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables patches \
  > ./scheduler_tables/patches.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY schedulerid ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables scheduler_changes \
  > ./scheduler_tables/scheduler_changes.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY buildsetid ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables scheduler_upstream_buildsets \
  > ./scheduler_tables/scheduler_upstream_buildsets.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY schedulerid ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables schedulers \
  > ./scheduler_tables/schedulers.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY sourcestampid ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables sourcestamp_changes \
  > ./scheduler_tables/sourcestamp_changes.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables sourcestamps \
  > ./scheduler_tables/sourcestamps.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} \
  --where="1 ORDER BY version ${ORDER} LIMIT ${ROW_LIMIT}" \
  --databases buildbot_schedulers \
  --tables version \
  > ./scheduler_tables/version.sql
