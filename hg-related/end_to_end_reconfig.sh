#!/bin/bash
set -ex

# Update and merge the buildbot repos
echo -n "Merge started..."
date
#for d in mozharness buildbot-configs buildbotcustom tools; do
for d in buildbot-configs buildbotcustom tools; do
  rm -rf ${d}
  hg clone ssh://hg.mozilla.org/build/${d}
  if [ "${d}" == "tools" ]; then
    continue
  fi
  pushd ${d}
  hg pull && hg up -r default
  branch='production'
  if [ "${d}" == "buildbotcustom" ]; then
    branch='production-0.8'
  fi
  hg up -r ${branch}
  echo "Merging from default" > preview_changes.txt
  echo "" >> preview_changes.txt
  hg merge -P default >> preview_changes.txt
  # Merging can fail if there are no changes between default and $branch
  set +e
  hg merge default
  RETVAL=$?
  if [ ${RETVAL} -eq 255 ]; then
    popd
    continue
  elif [ ${RETVAL} -ne 0 ]; then 
    exit ${RETVAL}
  fi
  set -e
  hg commit -l preview_changes.txt
  cp preview_changes.txt ../${d}_preview_changes.txt
  hg push
  popd
done

echo '|-' > reconfig_update_for_maintenance.wiki
echo '| in production' >> reconfig_update_for_maintenance.wiki
echo "| `TZ=America/Los_Angeles date +"%Y-%m-%d %H:%M PT"`" >> reconfig_update_for_maintenance.wiki
echo '|' >> reconfig_update_for_maintenance.wiki
grep summary *_preview_changes.txt | awk '{sub (/ r=.*$/,"");print substr($0, index($0,$2))}' | sed 's/[Bb]ug \([0-9]*\):* *-* */\* {{bug|\1}} - /' | sort -u >> reconfig_update_for_maintenance.wiki

echo -n "Merge finished..."
date

cd tools/buildfarm/maintenance
reconfig_tmux.sh -f
