#!/bin/bash

set -e

v_dot="v2.1"
v_under="v2_1"
v_none="v21"

prefix="https://hg.mozilla.org/releases/gaia-l10n"
configs_repo="../../repo-sync-configs"

for l in $(python gaia_l10n_list.py); do
    if [ "$l" = "sw" ]; then
        continue
    fi

    h="$configs_repo/releases-l10n-${l}-gaia/hgrc"
    g="$configs_repo/releases-l10n-${l}-gaia/config"
    if [ ! -e $h ]; then
        echo "can't find $h"
    fi
    if [ ! -e $g ]; then
        echo "can't find $g"
    fi
    if ! grep -q renameremote $g; then
        echo $l
    fi
    #path="${v_under} = ${prefix}/${v_under}/${l}"
    #rename="renameremote${v_none}defaultbranchto = $v_dot"
    #sed "s,\[mozilla.vcs-sync\],$path\n[mozilla.vcs-sync],g" $h > ${h}.tmp
    #sed -i "s,.*remotes_to_pull.*,\0 ${v_under},g" ${h}.tmp
    #mv ${h}.tmp ${h}
    #echo -e "\t$rename" >> $g
done
