#!/bin/bash
# from https://wiki.mozilla.org/Release:Release_Automation_on_Mercurial:Documentation#L10N_sync
set -eu
USAGE="usage: ${0##*/} [options] [locales...]
where:
    locales         are a space separated list of locales to operate on
                    if empty, the values will be extracted from the
                    current value in the mozilla-beta repo for both
                    desktop and fennec

and options are:
    -h | --help     show this text
    --user USER     hg commit as USER (default 'ffxbld <release@mozilla.com>' or HG_USER)
    --ssh-key KEY   ssh key for USER (default ffxbld_rsa or SSH_KEY)
    --ssh-user LOGIN    ssh USER for login (default ffxbld or HG_SSH_USER)
    --no-merge      only check, do not merge
    --mrproper      remove any state from prior run first
"

# if you choose to use your own credentials, you also have to change the
# hg push line below.
HG_USER="${HG_USER:-ffxbld <release@mozilla.com>}"      # used for commit message
HG_SSH_USER="${HG_SSH_USER:-ffxbld}"                    # used to push
SSH_KEY="${SSH_KEY:-$PWD/ffxbld_rsa}"
HG_HOST=hg.mozilla.org
repo=mozilla-release
release_repo_path=releases/l10n/mozilla-release
beta_repo_path=releases/l10n/mozilla-beta
wd=`pwd`/l10n

warn() { for m; do echo "$m"; done 1>&2 ; }
die() { warn "$@"; exit 1; }
usage() { warn "$@" "${USAGE:-}" ; test $# -eq 0 ; exit $? ; }

do_merge=true
do_mrproper=false

while test $# -gt 0 ; do
    case "$1" in
        --no-merge) do_merge=false ;;
        --user) HG_USER="$2" ; shift ;;
        --ssh-key) SSH_KEY="$2" ; shift ;;
        --ssh-user) HG_SSH_USER="$2" ; shift ;;
        --mrproper) do_mrproper=true ;;
        -h | --help) usage ;;
        -*) usage "Unknown option '$1'" ;;
        *) break ;;
    esac
    shift
done

if $do_merge && ! test -e $SSH_KEY; then
    warn "cannot access $SSH_KEY" "no merging will be done"
    do_merge=false
elif test "$HG_USER" == "${HG_USER/@/}"; then
    usage "HG_USER must contain an '@' sign"
fi

if $do_mrproper ; then
    if test -d $wd ; then
        warn "Removing old state at user's request"
        rm -rf $wd
    else
        warn "No old state to remove"
    fi
fi
mkdir -p $wd
cd $wd

if test $# -gt 0; then
    locales=("$@")
else
    # for desktop
    wget -q -O- http://$HG_HOST/releases/$repo/raw-file/default/browser/locales/shipped-locales \
        | grep -v en-US | awk '{print $1}' \
        > locales.desktop
    # for fennec (brittle parsing of json, but good enough for now)
    wget -q -O- http://$HG_HOST/build/buildbot-configs/raw-file/default/mozilla/l10n-changesets_mobile-release.json \
        | awk '/".*":/ {print $1}' \
        | sed -e 's/[":]//g' \
        | egrep -v 'revision|platforms' \
        > locales.fennec
    locales=( $(sort -u locales.*) )
fi


echo "Checking ${#locales[@]} repositories"
echo "$(date -u +%Y-%m-%dT%H:%M:%S%Z) Started run" >> merged_l10n_locales

for l in ${locales[@]} ; do
    mr_id=$(hg id -r default http://$HG_HOST/$release_repo_path/$l)
    mb_id=$(hg id -r default http://$HG_HOST/$beta_repo_path/$l)
    if ! test "$mr_id" == "$mb_id" ; then
        echo "$l needs checking" >> merged_l10n_locales
        if $do_merge ; then
            if test -d $l -a -d $l.beta; then
                # allow re-running if script bombs out. Assumption is if both
                # repos exist, locale has been dealt with.
                warn "Found prior work for $l, not updating."
                continue
            fi
            hg clone http://$HG_HOST/$release_repo_path/$l
            hg clone http://$HG_HOST/$beta_repo_path/$l $l.beta
            # -r default doesn't work in empty repos
            release_rev=`hg -R $l id -i`
            beta_rev=`hg -R $l.beta id -i -r default`
            if [ $release_rev == $beta_rev ] ; then
                echo "Same beta/release rev on $l; skipping"
                continue
            fi
            # actual merging starts here
            set -x
            hg -R $l pull $l.beta
            hg -R $l up -C default
            heads=`hg -R $l heads --template '{rev}\n' default|wc -l|sed -e 's/ *//'`
            if [ "x$heads" != "x1" ]; then
                hg -R $l up -C -r $beta_rev
                HGMERGE=true hg -R $l merge -r $release_rev
                hg -R $l revert -a -y --no-backup -r $beta_rev
                # okay if commit "fails" (it will if there is nothing to commit)
                ec=0
                hg -R $l commit -u "$HG_USER" -m "Merge from mozilla-beta. CLOSED TREE a=release" || ec=$? | tee -a merged_l10n_locales
                echo "Merge on locale '$l'; exit code '$ec'" >> merged_l10n_locales
            fi
            hg -R $l push -f -e "ssh -l $HG_SSH_USER -i $SSH_KEY" ssh://$HG_HOST/$release_repo_path/$l
            set +x
        fi
    fi
done

if test -r merged_l10n_locales; then
    # annecdotal reports of the merge not working correctly, however
    # that was before the syntax, etc. was corrected. Do want to call
    # attention to the list, just in case, until we have confidence in
    # the automation. No manual corrections were needed for FF 28 (the
    # first use of the corrected script).
    echo "The following locales needed some action:"
    cat merged_l10n_locales
fi
