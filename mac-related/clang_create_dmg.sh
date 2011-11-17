#!/bin/bash
# example script to generate clang dmg package
# in ~/src/clang

REPO_REV=142296
PREFIX=/tools/clang-3.0

svn co -r $REPO_REV http://llvm.org/svn/llvm-project/llvm/trunk llvm
svn co -r $REPO_REV http://llvm.org/svn/llvm-project/cfe/trunk clang

cd llvm/tools/
ln -s ../../clang
cd ../../
mkdir build
cd build
../llvm/configure --enable-optimized --prefix=$PREFIX \
 CC=gcc-4.2 CXX=g++-4.2
make -j8

sudo rm -rf $PREFIX
sudo make install
cd ../../puppet-manifests/ # from http://hg.mozilla.org/build/puppet-manifests
sudo ./create-dmg.sh $PREFIX clang-3.0-r$REPO_REV.moz0 clang /tools
