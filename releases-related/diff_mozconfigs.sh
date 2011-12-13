#!/bin/bash

platforms="linux linux64 macosx64 win32 linux-android linux-mobile macosx-mobile win32-mobile"

for p in $platforms; do
    diff -Nabu mozilla2/$p/mozilla-beta/release/mozconfig \
        mozilla2/$p/mozilla-release/release/mozconfig
done
