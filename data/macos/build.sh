#!/bin/bash

set -e

JOBS="-j 2"

if [ ! -f Makefile ]; then
  cd ../..
fi

export MACOS="true"
export CXFREEZE="/opt/carla/bin/cxfreeze --include-modules=re,sip,subprocess,inspect"
export DEFAULT_QT=5
export PATH=/opt/carla/bin:/opt/carla64/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin
export PYTHONPATH=`pwd`/source
export PYUIC5=/opt/carla/bin/pyuic5

##############################################################################################
# Build Mac App

rm -rf ./data/macos/MOD-*
rm -rf ./data/macos/exe.*

cp ./source/mod-app    ./source/MOD-App.pyw
cp ./source/mod-remote ./source/MOD-Remote.pyw
# env SCRIPT_NAME=MOD-App    python3 ./data/macos/bundle.py bdist_mac --bundle-name=MOD-App
env SCRIPT_NAME=MOD-Remote python3 ./data/macos/bundle.py bdist_mac --bundle-name=MOD-Remote
rm ./source/*.pyw

##############################################################################################
