#!/bin/bash
# from https://wiki.mozilla.org/Release:Release_Automation_on_Mercurial:Documentation#L10N_sync
set -x
set -e

# if you choose to use your own credentials, you also have to change the
# hg push line below.
HG_USER="ffxbld <release@mozilla.com>"
HG_HOST=hg.mozilla.org
# IGNORE_LOCALES is here because these locales had zero checkins, and so no 'default' branch
# We probably want to clear out this list, and add to it as we hit that issue; alternately we can get rid of it and allow for no default branch to just skip the locale.
IGNORE_LOCALES="af zu"
BRANCH=v2.0
TO_REPO_PATH=releases/gaia-l10n/v2_0
from_repo_path=gaia-l10n/
wd=`pwd`/l10n

mkdir -p $wd
cd $wd

for l in `wget -q -O- https://raw.githubusercontent.com/mozilla-b2g/gaia/$BRANCH/locales/languages_all.json | awk '{print $1}' | sed -e 's/[{}"]*//g'`; do
    count=`echo $IGNORE_LOCALES | grep -cw $l || true`  # End with 'true' so -e doesn't kill the script
    if [ $count -ge 1 ] ; then
        echo "Ignoring $l ..."
        continue
    fi
    if test -d $l -a -d $l.from; then
        # allow re-running if script bombs out. Assumption is if both
        # repos exist, locale has been dealt with.
        continue
    fi
    hg clone http://$HG_HOST/$TO_REPO_PATH/$l
    hg clone http://$HG_HOST/$from_repo_path/$l $l.from
    to_rev=`hg -R $l id -i -r default`
    from_rev=`hg -R $l.from id -i -r default`
    if [ $to_rev == $from_rev ] ; then
        echo "Same rev on $l; skipping"
        continue
    fi
    hg -R $l pull $l.from
    hg -R $l up -C default
    new_rev=`hg -R $l id -i -r default`
    if [ $to_rev == $new_rev ] ; then
        echo "WARNING $TO_REPO_PATH/$l is newer!" | tee -a merged_l10n_locales
        continue
    fi
    heads=`hg -R $l heads --template '{rev}\n' default|wc -l|sed -e 's/ *//'`
    if [ "x$heads" != "x1" ]; then
        hg -R $l up -C -r $from_rev
        HGMERGE=true hg -R $l merge -r $to_rev
        hg -R $l revert -a -y --no-backup -r $from_rev
        # okay if commit "fails" (it will if there is nothing to commit)
        ec=0
        hg -R $l commit -u "$HG_USER" -m "Merge from gaia-l10n. CLOSED TREE a=release" || ec=$? | tee -a merged_l10n_locales
        echo "Merge on locale '$l'; exit code '$ec'" >> merged_l10n_locales
    fi
    hg -R $l push -f -e "ssh -l ffxbld -i ~/.ssh/ffxbld_dsa" ssh://$HG_HOST/$TO_REPO_PATH/$l
done

if test -r merged_l10n_locales; then
    # annecdotal reports of the merge not working correctly, however
    # that was before the syntax, etc. was corrected. Do want to call
    # attention to the list, just in case, until we have confidence in
    # the automation. No manual corrections were needed for FF 28 (the
    # first use of the corrected script).
    echo "The following locales needed merging:"
    cat merged_l10n_locales
fi
