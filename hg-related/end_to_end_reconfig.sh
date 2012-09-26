#!/bin/bash
set -ex

# Customize this for your own venv
activate_venv() {
  source ~/.virtualenvs/buildbot-0.8/bin/activate
}

# Update and tag the buildbot repos
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
    continue
  elif [ ${RETVAL} -ne 0 ]; then 
    exit ${RETVAL}
  fi
  set -e
  hg commit -l preview_changes.txt
  hg push
  popd
done

# Start the reconfig process
activate_venv
cd tools/buildfarm/maintenance
for action in show_revisions update checkconfig; do 
    python manage_masters.py -f production-masters.json -R scheduler -R build -R try -R tests ${action}
done
# Reconfigs for tests masters take longer, so start them last so they don't block.
python manage_masters.py -f production-masters.json -R scheduler reconfig
python manage_masters.py -f production-masters.json -R build -R try reconfig
python manage_masters.py -f production-masters.json -R tests reconfig
