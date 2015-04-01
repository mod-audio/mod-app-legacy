#!/bin/bash

# ------------------------------------------------------------------------------------
# stop on error

set -e

# ------------------------------------------------------------------------------------
# check for needed binaries

# TODO, check for binaries like /opt/local/bin/7z

# ------------------------------------------------------------------------------------
# cd to correct path

if [ -f Makefile ]; then
  cd data/macos
fi

# ------------------------------------------------------------------------------------
# setup for base libs

export CC=gcc
export CXX=g++

export CFLAGS="-O2 -mtune=generic -msse -msse2 -m64 -fPIC -DPIC"
export CXXFLAGS=$CFLAGS
export CPPFLAGS=
export LDFLAGS="-m64"

export PREFIX=/opt/mod-app
export PATH=$PREFIX/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin
export PKG_CONFIG_PATH=$PREFIX/lib/pkgconfig

# ------------------------------------------------------------------------------------
# pkgconfig

if [ ! -d pkg-config-0.28 ]; then
curl -O http://pkgconfig.freedesktop.org/releases/pkg-config-0.28.tar.gz
tar -xf pkg-config-0.28.tar.gz
fi

if [ ! -f pkg-config-0.28/build-done ]; then
cd pkg-config-0.28
./configure --enable-indirect-deps --with-internal-glib --with-pc-path=$PKG_CONFIG_PATH --prefix=$PREFIX
make
sudo make install
touch build-done
cd ..
fi

# ------------------------------------------------------------------------------------
# lv2 (git)

if [ ! -d lv2-git ]; then
git clone http://lv2plug.in/git/lv2.git lv2-git
fi

if [ ! -f lv2-git/build-done ]; then
cd lv2-git
git pull
./waf clean || true
./waf configure --prefix=$PREFIX --copy-headers --no-plugins
./waf build
sudo ./waf install
touch build-done
cd ..
fi

# ------------------------------------------------------------------------------------
# setup for advanced libs

export CC=clang
export CXX=clang

export QMAKESPEC=macx-clang

# ------------------------------------------------------------------------------------
# qt5-base

if [ ! -d qtbase-opensource-src-5.4.1 ]; then
curl -L http://download.qt-project.org/official_releases/qt/5.4/5.4.1/submodules/qtbase-opensource-src-5.4.1.tar.gz -o qtbase-opensource-src-5.4.1.tar.gz
tar -xf qtbase-opensource-src-5.4.1.tar.gz
fi

if [ ! -f qtbase-opensource-src-5.4.1/build-done ]; then
cd qtbase-opensource-src-5.4.1
./configure -release -shared -opensource -confirm-license -force-pkg-config -platform macx-clang -framework \
            -prefix $PREFIX -plugindir $PREFIX/lib/qt5/plugins -headerdir $PREFIX/include/qt5 \
            -qt-freetype -qt-libjpeg -qt-libpng -qt-pcre -qt-sql-sqlite -qt-zlib -opengl desktop -qpa cocoa \
            -no-directfb -no-eglfs -no-kms -no-linuxfb -no-mtdev -no-xcb -no-xcb-xlib \
            -no-sse3 -no-ssse3 -no-sse4.1 -no-sse4.2 -no-avx -no-avx2 -no-mips_dsp -no-mips_dspr2 \
            -no-cups -no-dbus -no-evdev -no-fontconfig -no-harfbuzz -no-iconv -no-icu -no-gif -no-glib -no-nis -no-openssl -no-pch -no-sql-ibase -no-sql-odbc \
            -no-audio-backend -no-qml-debug -no-separate-debug-info \
            -no-compile-examples -nomake examples -nomake tests -make libs -make tools
make -j 4
sudo make install
touch build-done
cd ..
fi

# ------------------------------------------------------------------------------------
# qt5-multimedia

ignore2()
{

if [ ! -d qtmultimedia-opensource-src-5.4.1 ]; then
curl -L http://download.qt-project.org/official_releases/qt/5.4/5.4.1/submodules/qtmultimedia-opensource-src-5.4.1.tar.gz -o qtmultimedia-opensource-src-5.4.1.tar.gz
tar -xf qtmultimedia-opensource-src-5.4.1.tar.gz
fi

if [ ! -f qtmultimedia-opensource-src-5.4.1/build-done ]; then
cd qtmultimedia-opensource-src-5.4.1
qmake
make -j 4
sudo make install
touch build-done
cd ..
fi

}

# ------------------------------------------------------------------------------------
# qt5-webkit

ignore3()
{

if [ ! -d qtwebkit-opensource-src-5.4.1 ]; then
curl -L http://download.qt-project.org/official_releases/qt/5.4/5.4.1/submodules/qtwebkit-opensource-src-5.4.1.tar.gz -o qtwebkit-opensource-src-5.4.1.tar.gz
tar -xf qtwebkit-opensource-src-5.4.1.tar.gz
fi

if [ ! -f qtwebkit-opensource-src-5.4.1/build-done ]; then
cd qtwebkit-opensource-src-5.4.1
qmake
make -j 2
sudo make install
touch build-done
cd ..
fi

}

# ------------------------------------------------------------------------------------
# python

if [ ! -d Python-3.4.3 ]; then
curl -O https://www.python.org/ftp/python/3.4.3/Python-3.4.3.tgz
tar -xf Python-3.4.3.tgz
fi

if [ ! -f Python-3.4.3/build-done ]; then
cd Python-3.4.3
./configure --prefix=$PREFIX
make
sudo make install
touch build-done
cd ..
fi

exit 0

# ------------------------------------------------------------------------------------
# sip

if [ ! -d sip-4.16.7 ]; then
curl -L http://sourceforge.net/projects/pyqt/files/sip/sip-4.16.7/sip-4.16.7.tar.gz -o sip-4.16.7.tar.gz
tar -xf sip-4.16.7.tar.gz
fi

if [ ! -f sip-4.16.7/build-done ]; then
cd sip-4.16.7
python3 configure.py
make
sudo make install
touch build-done
cd ..
fi
