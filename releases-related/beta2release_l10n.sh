#!/bin/bash
# from https://wiki.mozilla.org/Release:Release_Automation_on_Mercurial:Documentation#L10N_sync
set -x
set -e

HG_USER="ffxbld <release@mozilla.com>"
HG_HOST=hg.mozilla.org
repo=mozilla-release
release_repo_path=releases/l10n/mozilla-release
beta_repo_path=releases/l10n/mozilla-beta
wd=`pwd`/l10n

mkdir -p $wd
cd $wd

for l in `wget -q -O- http://$HG_HOST/releases/$repo/raw-file/default/browser/locales/shipped-locales | grep -v en-US | awk '{print $1}'`; do
    if test -d $l -a -d $l.beta; then
        # allow re-running if script bombs out. Assumption is if both
        # repos exist, locale has been dealt with.
        continue
    fi
    hg clone http://$HG_HOST/$release_repo_path/$l
    hg clone http://$HG_HOST/$beta_repo_path/$l $l.beta
    release_rev=`hg -R $l id -i -r default`
    beta_rev=`hg -R $l.beta id -i -r default`
    hg -R $l pull $l.beta
    hg -R $l up -C default
    heads=`hg -R $l heads --template '{rev}\n' default|wc -l`
    if [ "x$heads" != "x1" ]; then
        hg -R $l up -C -r $beta_rev
        HGMERGE=true hg -R $l merge -r $release_rev
        hg -R $l revert -a -y --no-backup -r $beta_rev
        # okay if commit "fails" (it will if there is nothing to commit)
        ec=0
        hg -R $l commit -u "$HG_USER" -m "Merge from mozilla-beta. CLOSED TREE a=release" || ec=$? | tee -a merged_l10n_locales
        echo "Merge on locale '$l'; exit code '$ec'" >> merged_l10n_locales
    fi
    hg -R $l diff -r $beta_rev -r default
    hg -R $l push -f -e "ssh -l ffxbld -i ~/.ssh/ffxbld_dsa" ssh://$HG_HOST/$release_repo_path/$l
done

if test -r merged_l10n_locales; then
    echo "The following locales needed merging:"
    cat merged_l10n_locales
fi
