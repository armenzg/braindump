export VERSION=9.0
export PRODUCT=fennec
export BUILD=build1

# on keymaster in ~/signing-work
cd ~/signing-work
mkdir $PRODUCT-$VERSION
cd $PRODUCT-$VERSION/

# we sign both en-US and multi 
# need sep dirs since they are both named gecko-unsigned-unaligned.apk
echo "Creating directories"
mkdir -p $BUILD/en-US
mkdir $BUILD/multi
echo "Getting the unsigned apks"
# get en-US apk
cd $BUILD/en-US/
wget http://stage.mozilla.org/pub/mozilla.org/mobile/candidates/$VERSION-candidates/$BUILD/unsigned/android/en-US/gecko-unsigned-unaligned.apk
# get multi apk
cd ../multi/
wget http://stage.mozilla.org/pub/mozilla.org/mobile/candidates/$VERSION-candidates/$BUILD/unsigned/android/multi/gecko-unsigned-unaligned.apk

# put the signing script in the ~/signing-work/fennec-4.0rc1/ dir
echo "Copying signing script from hg-tools"
cd  ~/signing-work/$PRODUCT-$VERSION/
cp ~/hg-tools/release/signing/* .
# copy the en-US apk up to pwd for signing -- there is a bug on this 
# (608432), it's because sign_android.sh relies on mozpass.py and that has to
# be in the same dir as .apk to work
echo "Prepare to sign en-US"
cp $BUILD/en-US/gecko-unsigned-unaligned.apk .
./sign_android.sh 
# if any problems with signing, remove gecko-unaligned.apk and start again
# signing successful?  copy back to the en-US
echo "en-US signed, cleaning up"
mv gecko-unaligned.apk $BUILD/en-US/
# rename the fennec.apk, then move
mv $PRODUCT.apk $PRODUCT-$VERSION.en-US.android-arm.apk
mv $PRODUCT-$VERSION.en-US.android-arm.apk $BUILD/en-US/
# clean up any left overs  
rm *.apk
# repeat for multi
echo "Prepare to sign multi"
cp $BUILD/multi/gecko-unsigned-unaligned.apk .
./sign_android.sh 
echo "multi signed, cleaning up"
mv gecko-unaligned.apk $BUILD/multi/
mv $PRODUCT.apk $PRODUCT-$VERSION.multi.android-arm.apk
mv $PRODUCT-$VERSION.multi.android-arm.apk $BUILD/multi/
rm *.apk
# upload to stage
cd $BUILD/
echo "Uploading signed builds"
ssh -i ~/.ssh/ffxbld_dsa ffxbld@stage.mozilla.org "mkdir -p /home/ftp/pub/mobile/candidates/$VERSION-candidates/$BUILD/android"
scp -i ~/.ssh/ffxbld_dsa -r * ffxbld@stage.mozilla.org:/home/ftp/pub/mobile/candidates/$VERSION-candidates/$BUILD/android

