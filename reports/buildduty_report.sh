#!/bin/sh
set -e

cd $HOME/buildduty
if [ ! -d braindump ]; then
  hg clone https://hg.mozilla.org/build/braindump/
  ln -s braindump/reports/buildduty_report.py
else
  hg -q -R braindump pull -u
fi

if [ ! -d bztools ]; then
  git clone https://github.com/ccooper/bztools.git
else
  pushd bztools  
  git reset --hard
  git clean -f -d
  git pull
  popd
fi

source $HOME/buildduty/bin/activate
export PYTHONPATH=$HOME/buildduty/bztools

python buildduty_report.py
