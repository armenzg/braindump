#!/bin/bash

# Creates a directory containing the schema of the buildbot status db, and then a
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
DB=buildbot
ORDER=DESC
TABLE_DIR=status_tables

mkdir -p ${TABLE_DIR}

# Dump the schema first.
mysqldump -d --databases ${DB} -u ${USER} -p -h ${HOST} > ./buildbot_status_schema.sql

# Now dump each table individually.
mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY property_id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables build_properties \
  > ./${TABLE_DIR}/build_properties.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY build_id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables build_requests \
  > ./${TABLE_DIR}/build_requests.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables builder_slaves \
  > ./${TABLE_DIR}/builder_slaves.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables builders \
  > ./${TABLE_DIR}/builders.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables builds \
  > ./${TABLE_DIR}/builds.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables changes \
  > ./${TABLE_DIR}/changes.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY file_id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables file_changes \
  > ./${TABLE_DIR}/file_changes.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables files \
  > ./${TABLE_DIR}/files.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables master_slaves \
  > ./${TABLE_DIR}/master_slaves.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables masters \
  > ./${TABLE_DIR}/masters.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables patches \
  > ./${TABLE_DIR}/patches.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables properties \
  > ./${TABLE_DIR}/properties.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY property_id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables request_properties \
  > ./${TABLE_DIR}/request_properties.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables requests \
  > ./${TABLE_DIR}/requests.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY status_build_id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables schedulerdb_requests \
  > ./${TABLE_DIR}/schedulerdb_requests.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables slaves \
  > ./${TABLE_DIR}/slaves.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables source_changes \
  > ./${TABLE_DIR}/source_changes.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables sourcestamps \
  > ./${TABLE_DIR}/sourcestamps.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY status_build_id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables sr \
  > ./${TABLE_DIR}/sr.sql

mysqldump --no-create-info --skip-compact --skip-extended-insert --opt -u ${USER} -p -h ${HOST} --databases ${DB} \
  --where="1 ORDER BY id ${ORDER} LIMIT ${ROW_LIMIT}" \
  --tables steps \
  > ./${TABLE_DIR}/steps.sql
