#!/bin/bash

##############################################################################################
# MacOS X default environment for Carla, adjusted for MOD-App/Remote

export MACOS="true"

export PATH=/opt/carla/bin:/opt/carla64/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin
export PKG_CONFIG_PATH=/opt/carla/lib/pkgconfig:/opt/carla64/lib/pkgconfig

export DEFAULT_QT=5
export PYUIC5=/opt/carla/bin/pyuic5
