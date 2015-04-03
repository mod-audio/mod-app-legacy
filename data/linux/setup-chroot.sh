#!/bin/bash

# ------------------------------------------------------------------------------------
# function to run a command inside the chroot

function run_chroot_cmd() {

echo "
export HOME=/root
export LANG=C
unset LC_TIME
$@
" | sudo tee ./chroot/cmd

sudo chroot ./chroot /bin/bash /cmd

}

# ------------------------------------------------------------------------------------
# stop on error

set -e

# ------------------------------------------------------------------------------------
# cd to correct path

if [ -f Makefile ]; then
  cd data/linux
fi

# ------------------------------------------------------------------------------------
# check if already set up

if [ -f ./chroot/chroot-done ]; then
  echo \
"
chroot is already set up.
Delete $(pwd)/chroot/chroot-done to start over.
"
  exit 0
else
  if [ -x chroot ]; then
      sudo mv chroot chroot_delete
  fi
  sudo rm -rf ./chroot_delete || true
fi

# ------------------------------------------------------------------------------------
# create the chroot

sudo debootstrap --arch=amd64 lucid ./chroot http://archive.ubuntu.com/ubuntu/

# ------------------------------------------------------------------------------------
# enable network access

sudo rm -f ./chroot/etc/hosts
sudo rm -f ./chroot/etc/resolv.conf
sudo cp /etc/resolv.conf /etc/hosts ./chroot/etc/

# ------------------------------------------------------------------------------------
# mount basic chroot points

run_chroot_cmd mount -t devpts none /dev/pts
run_chroot_cmd mount -t proc none /proc
run_chroot_cmd mount -t sysfs none /sys

# ------------------------------------------------------------------------------------
# fix upstart

run_chroot_cmd dpkg-divert --local --rename --add /sbin/initctl
run_chroot_cmd ln -s /bin/true /sbin/initctl
run_chroot_cmd touch /etc/init.d/systemd-logind
run_chroot_cmd touch /etc/init.d/modemmanager

# ------------------------------------------------------------------------------------
# proper lucid repos + backports

echo "
deb http://archive.ubuntu.com/ubuntu/ lucid main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ lucid-updates main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu/ lucid-backports main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu lucid-security main restricted universe multiverse
" | sudo tee ./chroot/etc/apt/sources.list

# ------------------------------------------------------------------------------------
# enable repo from which we'll install kxstudio-repos package

mkdir -p ./chroot/etc/apt/sources.list.d
echo "deb http://ppa.launchpad.net/kxstudio-debian/kxstudio/ubuntu lucid main" | sudo tee ./chroot/etc/apt/sources.list.d/kxstudio-repos-tmp.list

# ------------------------------------------------------------------------------------
# enable kxstudio-repos

run_chroot_cmd apt-get update
run_chroot_cmd apt-get install kxstudio-repos kxstudio-repos-backports -y --force-yes

# ------------------------------------------------------------------------------------
# enable toolchain

echo "deb http://ppa.launchpad.net/kxstudio-debian/toolchain/ubuntu lucid main" | sudo tee -a ./chroot/etc/apt/sources.list.d/kxstudio-debian.list

# ------------------------------------------------------------------------------------
# cleanup

sudo rm ./chroot/etc/apt/sources.list.d/kxstudio-repos-tmp.list

# ------------------------------------------------------------------------------------
# install updates

run_chroot_cmd apt-get update
run_chroot_cmd apt-get dist-upgrade -y

# ------------------------------------------------------------------------------------
# now finally install all needed tools

run_chroot_cmd apt-get install -y autotools-dev build-essential cmake premake git-core subversion
run_chroot_cmd apt-get install -y libasound2-dev libjack-dev/lucid libjack0/lucid ladspa-sdk lv2-dev
run_chroot_cmd apt-get install -y libosmesa6-dev libgl1-mesa-dev libglu1-mesa-dev
run_chroot_cmd apt-get install -y libxinerama-dev libxi-dev libxrender-dev libxcomposite-dev libxcursor-dev
run_chroot_cmd apt-get install -y libx11-dev libx11-xcb-dev xvfb
run_chroot_cmd apt-get install -y libcups2-dev libdbus-1-dev
run_chroot_cmd apt-get install -y libfontconfig1-dev libfreetype6-dev
run_chroot_cmd apt-get install -y libglib2.0-dev libgtk2.0-dev
run_chroot_cmd apt-get install -y ruby flex bison gperf

# ------------------------------------------------------------------------------------
# done

sudo touch ./chroot/chroot-done

# ------------------------------------------------------------------------------------
