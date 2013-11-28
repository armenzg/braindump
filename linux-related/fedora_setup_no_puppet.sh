#!/bin/bash
set -x

hardwaremodel="i686"
#hardwaremodel="x86_64"
fqdn="talos-r3-fed-036.build.mozilla.org"
hostname ${fqdn}

package_base="http://dev-stage01.srv.releng.scl3.mozilla.com/pub/mozilla.org/mozilla/libraries/linux"

/bin/rpm -e `rpm -q fedora-screensaver-theme fedorainfinity-screensaver-theme gnome-screensaver | grep -v 'is not installed'`

puppet_base="${package_base}/fedora12-${hardwaremodel}/test"
rpm_dir="./RPMs"
mkdir -p ${rpm_dir}
pushd ${rpm_dir}
for rpm in alsa-plugins-pulseaudio-1.0.22-1.fc12.${hardwaremodel}.rpm \
    pulseaudio-0.9.21-6.fc12.${hardwaremodel}.rpm \
    pulseaudio-gdm-hooks-0.9.21-6.fc12.${hardwaremodel}.rpm \
    pulseaudio-libs-0.9.21-6.fc12.${hardwaremodel}.rpm \
    pulseaudio-libs-glib2-0.9.21-6.fc12.${hardwaremodel}.rpm \
    pulseaudio-module-bluetooth-0.9.21-6.fc12.${hardwaremodel}.rpm \
    pulseaudio-module-gconf-0.9.21-6.fc12.${hardwaremodel}.rpm \
    pulseaudio-module-x11-0.9.21-6.fc12.${hardwaremodel}.rpm \
    pulseaudio-utils-0.9.21-6.fc12.${hardwaremodel}.rpm; \
    do
  wget ${puppet_base}/RPMS/${rpm}
done
popd

/bin/rpm -U ${rpm_dir}/alsa-plugins-pulseaudio-1.0.22-1.fc12.${hardwaremodel}.rpm \
            ${rpm_dir}/pulseaudio-0.9.21-6.fc12.${hardwaremodel}.rpm \
            ${rpm_dir}/pulseaudio-gdm-hooks-0.9.21-6.fc12.${hardwaremodel}.rpm \
            ${rpm_dir}/pulseaudio-libs-0.9.21-6.fc12.${hardwaremodel}.rpm \
            ${rpm_dir}/pulseaudio-libs-glib2-0.9.21-6.fc12.${hardwaremodel}.rpm \
            ${rpm_dir}/pulseaudio-module-bluetooth-0.9.21-6.fc12.${hardwaremodel}.rpm \
            ${rpm_dir}/pulseaudio-module-gconf-0.9.21-6.fc12.${hardwaremodel}.rpm \
            ${rpm_dir}/pulseaudio-module-x11-0.9.21-6.fc12.${hardwaremodel}.rpm \
            ${rpm_dir}/pulseaudio-utils-0.9.21-6.fc12.${hardwaremodel}.rpm

/bin/rpm -U ${rpm_dir}/mercurial-1.5.1-1.fc12.${hardwaremodel}.rpm
/bin/rpm -e gtk2-immodule-xim
/bin/rpm -U ${rpm_dir}/gtk2-2.18.9-3.fc12.${hardwaremodel}.rpm

/bin/rpm -U ${rpm_dir}/python-devel-2.6.2-2.fc12.${hardwaremodel}.rpm

/sbin/service NetworkManager stop

wget -O/home/cltbld/.fonts.conf ${puppet_base}/etc/fonts.conf
chown cltbld /home/cltbld/.fonts.conf
chgrp cltbld /home/cltbld/.fonts.conf

wget -O/home/cltbld/.bash_profile ${puppet_base}/home/cltbld/.bash_profile
chown cltbld /home/cltbld/.bash_profile
chgrp cltbld /home/cltbld/.bash_profile

mkdir -p /home/cltbld/.ssh
chown cltbld /home/cltbld/.ssh
chgrp cltbld /home/cltbld/.ssh
chmod 700 /home/cltbld/.ssh

wget -O/home/cltbld/.ssh/authorized_keys ${puppet_base}/home/cltbld/.ssh/authorized_keys
chown cltbld /home/cltbld/.ssh/authorized_keys
chgrp cltbld /home/cltbld/.ssh/authorized_keys
chmod 644 /home/cltbld/.ssh/authorized_keys

wget -O/usr/bin/node ${puppet_base}/home/cltbld/bin/node.exe
chmod 755 /usr/bin/node

mkdir -p /home/cltbld/talos-slave/talos-data
chown cltbld /home/cltbld/talos-slave/talos-data
chgrp cltbld /home/cltbld/talos-slave/talos-data
chmod 775 /home/cltbld/talos-slave/talos-data

libdir="lib"
if [ "${hardwaremodel}" == "x86_64" ]; then
  libdir="lib64"
fi
ln -s /usr/${libdir}/libGL.so.1.2 /usr/${libdir}/libGL.so

/sbin/service avahi-daemon stop

# buildslave::install
production_version="0.8.4-pre-moz2"
source /tools/buildbot-${production_version}/bin/activate
mkdir -p python-packages
for package in simplejson-2.1.3 SQLAlchemy-0.6.6 zope.interface-3.6.1 Twisted-10.2.0 buildbot-0.8.4-pre-moz2 buildbot-slave-0.8.4-pre-moz2; do
  echo Downloading ${package}
  wget -Opython-packages/${package}.tar.gz ${package_base}/python-packages/${package}.tar.gz 
  tar zxf python-packages/${package}.tar.gz
  pushd ${package}
  python setup.py install
  popd
done

rm -rf /tools/buildbot
ln -s /tools/buildbot-${production_version} /tools/buildbot

hg clone http://hg.mozilla.org/build/puppet-manifests

cp ./puppet-manifests/modules/buildslave/files/runslave.py /usr/local/bin/runslave.py
chown root /usr/local/bin/runslave.py
chgrp root /usr/local/bin/runslave.py
chmod 755 /usr/local/bin/runslave.py

cp ./puppet-manifests/modules/buildslave/files/linux-initd-buildbot.sh /etc/init.d/buildbot
chown root /etc/init.d/buildbot
chgrp root /etc/init.d/buildbot
chmod 755 /etc/init.d/buildbot
rm -f /etc/default/buildbot
/sbin/chkconfig --del buildbot && /sbin/chkconfig --add buildbot
/sbin/service buildbot-tac stop
rm -f /etc/init.d/buildbot-tac

wget -O/home/cltbld/run-puppet-and-buildbot.sh ${package_base}/run-puppet-and-buildbot.sh 
chown cltbld /home/cltbld/run-puppet-and-buildbot.sh
chgrp cltbld /home/cltbld/run-puppet-and-buildbot.sh

find /tmp/* -mmin +15 -print | xargs -n1 rm -rf
rm -rf /home/cltbld/.mozilla/firefox/console.log

rm -f tooltool.py
wget ${puppet_base}/tools/tooltool.py
cp tooltool.py /tools/tooltool.py
chown root /tools/tooltool.py
chgrp root /tools/tooltool.py
chmod 0755 /tools/tooltool.py

rm -f xorg.conf
wget ${puppet_base}/etc/X11/xorg.conf
cp xorg.conf /etc/X11/xorg.conf
chown root /etc/X11/xorg.conf
chgrp root /etc/X11/xorg.conf
chmod 644 /etc/X11/xorg.conf

cp ./puppet-manifests/modules/network/files/fedora-hosts /etc/hosts

cp ./puppet-manifests/modules/network/files/fedora-ifcfg-eth0 /etc/sysconfig/network-scripts/ifcfg-eth0
echo "# clobbered on startup by puppet" > /etc/udev/rules.d/70-persistent-net.rules

cp ./puppet-manifests/modules/boot/files/e2fsck.conf /etc/e2fsck.conf

rm -f grub.conf
wget ${puppet_base}/etc/grub.conf
cp grub.conf /boot/grub/grub.conf
chown root /boot/grub/grub.conf
chgrp root /boot/grub/grub.conf
chmod 600 /boot/grub/grub.conf

wget ${puppet_base}/etc/sudoers
cp sudoers /etc/sudoers
chown root /etc/sudoers
chgrp root /etc/sudoers
chmod 0440 /etc/sudoers

wget ${puppet_base}/etc/ntp.conf
cp ntp.conf /etc/ntp.conf
chown root /etc/ntp.conf
chgrp root /etc/ntp.conf
chmod 644 /etc/ntp.conf

/sbin/service ntpdate start

mkdir -p /home/cltbld/.config/autostart/
chown -R cltbld /home/cltbld/.config
chgrp -R cltbld /home/cltbld/.config
cp ./puppet-files/local/home/cltbld/.config/autostart/gnome-terminal.desktop 
chown cltbld /home/cltbld/.config/autostart/gnome-terminal.desktop
chgrp cltbld /home/cltbld/.config/autostart/gnome-terminal.desktop

echo "NOTE: Remember to set passwords for root, cltbld, and VNC!"
