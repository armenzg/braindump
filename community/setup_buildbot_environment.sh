# Author:   Armen Zambrano Gasparnian
# Purpose:  This script does the following:
#             - create a workdir
#             - check-out and update all required Buildbot Release Engineering repositories
#             - create buildbot virtual environments
#
while getopts cw:qh opts; do
   case ${opts} in
      c) clobber=1 ;;
      w) workdir=${OPTARG} ;;
      q) quiet="-q" ;;
      h) help=1 ;;
   esac
done

if [ ! -z $help ];
then
    echo "./setup_buildbot_environment.sh [-w alt_workdir] [-h] [-q]"
    exit
fi

if [ -z "$workdir" ];
then
    workdir="$HOME/.mozilla/releng"
fi

if [ ! -z "$clobber" ];
then
    echo "___CLOBBERING___ $workdir"
    rm -rf $workdir
fi

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load common variables
. "$script_dir/buildbot_config.sh" -w "$workdir"

if [ ! -d "$repos_dir" ]
then
    mkdir -p "$repos_dir"
fi

# Checkout and update all repos
OLDIFS=$IFS
IFS=','
for repo in $bco,$bco_b $bcu,$bcu_b $bdu,$bdu_b $bbo,$bbo_b $tools,$tools_b
do
    cd $repos_dir
    set $repo
    repo_path=$1
    repo_name=`basename $repo_path`
    branch=$2
    if [ ! -d "$repo_path" ]
    then
        hg clone $quiet http://hg.mozilla.org/build/$repo_name || exit
    fi
    # Let's update to the right branch
    cd $repo_path
    hg up -C $quiet
    hg pull $quiet
    hg up -r $branch $quiet
    untracked_files=`hg status -u -0 | wc -l`
    if [ ! $untracked_files -eq 0 ]
    then
        hg status -u -0 | xargs -0 rm #Remove untracked files
    fi
    if [ -z "$quiet" ]; then echo "Repo info: $repo_path updated to `hg id`"; fi
done
IFS=$OLDIFS

if [ ! -d "$venv" ]
then
    virtualenv --no-site-packages "$venv" || exit
    pip install -U pip
    $venv/bin/pip install -r "$bdu/community/pre_buildbot_requirements.txt"
    # Install buildbot
    cd "$bbo/master"
    $venv/bin/python setup.py install || exit
    # Install buildslave
    $venv/bin/pip install buildbot-slave==0.8.4-pre-moz2 \
        --find-links http://pypi.pub.build.mozilla.org/pub \
        --trusted-host pypi.pub.build.mozilla.org || exit
    # XXX: It's been reported that OpenSSL==0.13 is needed in some cases
    # This is so we can reach buildbotcustom and tools when activating the venv
    echo "$repos_dir" >> "$venv"/lib/python2.7/site-packages/releng.pth
    echo "$tools/lib/python" >> "$venv"/lib/python2.7/site-packages/releng.pth
fi

if [ -z "$quiet" ]
then
    echo ""
    echo ""
    echo "Congratulations! You now have a virtual environment set-up for your buildbot "
    echo "masters and slaves under $venv."
    echo "You should call this script every time you want to bring your environment up-to-date."
    echo ""
    echo "We have optimized the code so it updates fast and we don't clobber your "
    echo "environment."
    echo ""
fi
