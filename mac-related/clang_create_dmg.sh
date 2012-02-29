#!/bin/bash
# example script to generate clang dmg package
# in ~/src/clang

REPO_REV=151655
PREFIX=/tools/clang-3.0-$REPO_REV

svn co -r $REPO_REV http://llvm.org/svn/llvm-project/llvm/trunk llvm
svn co -r $REPO_REV http://llvm.org/svn/llvm-project/cfe/trunk clang
svn co -r $REPO_REV http://llvm.org/svn/llvm-project/compiler-rt/trunk compiler-rt

# Apple's gcc 4.2 doesn't include cpuid.h. Having it causes firefox's build to enable SSE.
# While that is probably a good thing, disable it for now to reduce the differences.
rm clang/lib/Headers/cpuid.h

ln -s ../../clang llvm/tools
ln -s ../../compiler-rt llvm/projects

mkdir build
cd build
../llvm/configure --enable-optimized --prefix=$PREFIX \
 CC=gcc-4.2 CXX=g++-4.2
make -j8

sudo rm -rf $PREFIX
sudo make install
cd ../../puppet-manifests/ # from http://hg.mozilla.org/build/puppet-manifests
sudo ./create-dmg.sh $PREFIX clang-3.0-r$REPO_REV.moz0 clang /tools
