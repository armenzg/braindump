#!/bin/bash

mkdir tmp-$$
cd tmp-$$
mkdir unpacked && cd unpacked
7z x "../../$1"
cd ..
rsync -a unpacked/localized/ ./
rsync -a unpacked/nonlocalized/ ./
rsync -a unpacked/optional/ ./
