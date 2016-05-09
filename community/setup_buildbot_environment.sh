# Author:   Armen Zambrano Gasparnian
# Purpose:  This script does the following:
#             - create a workdir
#             - check-out and update all required Buildbot Release Engineering repositories
#             - create buildbot virtual environments
#
while getopts cdw:v:p:qh opts; do
   case ${opts} in
      c) clobber=1 ;;
      d) debug=1 ;;
      w) workdir=${OPTARG} ;;
      v) venv=${OPTARG} ;;
      p) python_path=${OPTARG} ;;
      q) quiet="-q" ;;
      h) help=1 ;;
   esac
done

if [ ! -z "$debug" ];
then
   set -ex
fi

if [ ! -z "$python_path" ];
then
   # Parameter for virtualenv
   python_path="-p $python_path"
fi

if [ ! -z $help ];
then
    echo "./setup_buildbot_environment.sh [-w alt_workdir] [-h] [-q]"
    exit 1
fi

if [ -z "$workdir" ];
then
    workdir="$HOME/.mozilla/releng"
fi

if [ -z "$venv" ];
then
    venv="$workdir/venv"
    releng_pth="$venv"/lib/python2.7/site-packages/releng.pth
fi

if [ ! -z "$clobber" ];
then
    echo "___CLOBBERING___ $workdir"
    rm -rf $workdir
    mkdir $workdir
fi

function gather_debug_information() {
    set -ex
    cd $bco
    ./test-masters.sh
    $venv/bin/pip freeze
    $venv/bin/python --version
    $venv/bin/python -c "import sys; import pprint; pprint.pprint(sys.path)"
    if [ -e $releng_pth ]; then
      cat "$venv"/lib/python2.7/site-packages/releng.pth
    fi
}

function move_and_exit() {
    echo "ERROR: Failed venv generation (moved to $workdir/failed_venv."
    # Gather information before we move the venv
    gather_debug_information

    rm -rf $workdir/failed_venv
    mv $venv $workdir/failed_venv || exit 1
    rm -rf $venv
    echo "EXIT setup_buildbot_environment.sh"
    exit 1
}

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Load important variables: venv, masters_dir, slaves_dir, repos_dir et al
# Update PATH and PYTHONPATH
. "$script_dir/buildbot_config.sh" -w "$workdir" -v "$venv"

if [ ! -d "$repos_dir" ]
then
    mkdir -p "$repos_dir"
fi
# At the end of the file there is a closing bracket
# This is used to log stdout and stderr to and output file
output_file="$workdir/output.txt"
touch $output_file

{
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
        hg clone $quiet http://hg.mozilla.org/build/$repo_name || exit 1
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
    virtualenv $python_path $quiet --no-site-packages "$venv" || move_and_exit
    $venv/bin/pip install $quiet -U pip
    # If on Mac, you might need to run `xcode-select --install`
    # XXX: Could not make it work on Mac. Cryptography on Mac needs to be installed with --no-use-wheel
    $venv/bin/pip install $quiet -r "$bdu/community/pre_buildbot_requirements.txt" \
	|| move_and_exit
    # Install buildbot
    cd "$bbo/master"
    $venv/bin/pip install $quiet -e . || move_and_exit
    # Install buildslave
    $venv/bin/pip install $quiet buildbot-slave==0.8.4-pre-moz2 \
        --find-links http://pypi.pub.build.mozilla.org/pub \
        --trusted-host pypi.pub.build.mozilla.org || move_and_exit
    # XXX: It's been reported that OpenSSL==0.13 is needed in some cases
    # This is so we can reach buildbotcustom and tools when activating the venv
    echo "$repos_dir" >> $releng_pth
    echo "$tools/lib/python" >> $releng_pth
fi

"$venv/bin/buildbot" --version > /dev/null
status=$?
if [ $status -ne 0 ]; then
    echo "Buildbot is not installed properly"; exit 1
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

if [ ! -z "$debug" ]
then
    gather_debug_information
fi

} 2>&1 | tee "$output_file"
