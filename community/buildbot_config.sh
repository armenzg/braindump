while getopts w:v: opts; do
   case ${opts} in
      w) workdir=${OPTARG} ;;
      v) venv=${OPTARG} ;;
   esac
done

if [ -z "$workdir" ];
then
    workdir="$HOME/.mozilla/releng"
fi

if [ -z "$venv" ];
then
    venv="$workdir/venv"
fi

masters_dir="$workdir/masters"
slaves_dir="$workdir/slaves"
repos_dir="$workdir/repos"

# Repos and branches
bco="$repos_dir/buildbot-configs"
bcu="$repos_dir/buildbotcustom"
bdu="$repos_dir/braindump"
bbo="$repos_dir/buildbot"
tools="$repos_dir/tools"

bco_b="production"
bcu_b="production-0.8"
bdu_b="default"
bbo_b="production-0.8"
tools_b="default"

export PATH="$venv/bin:$PATH"
# So we can reach buildbotcustom and python libs inside of the tools repo
export PYTHONPATH="$tools/lib/python:$repos_dir"
