#!/bin/bash

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
"""
chroot is already set up.
Delete $(pwd)/chroot/chroot-done to start over.
"""
  exit 0
else
  sudo rm -rf ./chroot_delete || true
  sudo mv chroot chroot_delete
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
# done

sudo touch ./chroot/chroot-done

# ------------------------------------------------------------------------------------
