#!/bin/bash

# ------------------------------------------------------------------------------------
# function to build everything

function build_all() {

echo "
set -e

export HOME=/root
export LANG=C
unset LC_TIME

export CC=gcc
export CXX=g++

export CFLAGS=\"-O2 -mtune=generic -msse -msse2 -m64 -fPIC -DPIC\"
export CXXFLAGS=\$CFLAGS
export CPPFLAGS=
export LDFLAGS=\"-m64\"

export PREFIX=/opt/mod-app
export PATH=\$PREFIX/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin
export PKG_CONFIG_PATH=\$PREFIX/lib/pkgconfig

mkdir -p /src
cd /src

# ------------------------------------------------------------------------------------
# pkgconfig

if [ ! -d pkg-config-0.28 ]; then
curl -O http://pkgconfig.freedesktop.org/releases/pkg-config-0.28.tar.gz
tar -xf pkg-config-0.28.tar.gz
fi

if [ ! -f pkg-config-0.28/build-done ]; then
cd pkg-config-0.28
./configure --with-internal-glib --with-pc-path=\$PKG_CONFIG_PATH --prefix=\$PREFIX
make
make install
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
./waf configure --prefix=\$PREFIX --copy-headers --no-plugins
./waf build
./waf install
touch build-done
cd ..
fi

# ------------------------------------------------------------------------------------
# qt5-base

if [ ! -d qtbase-opensource-src-5.4.1 ]; then
curl -L http://download.qt-project.org/official_releases/qt/5.4/5.4.1/submodules/qtbase-opensource-src-5.4.1.tar.gz -o qtbase-opensource-src-5.4.1.tar.gz
tar -xf qtbase-opensource-src-5.4.1.tar.gz
fi

if [ ! -f qtbase-opensource-src-5.4.1/build-done ]; then
cd qtbase-opensource-src-5.4.1
patch -p1 -i /fix-qt5-build.patch
./configure -release -shared -opensource -confirm-license -force-pkg-config \
            -prefix \$PREFIX -plugindir \$PREFIX/lib/qt5/plugins -headerdir \$PREFIX/include/qt5 \
            -reduce-relocations -plugin-sql-sqlite \
            -xcb -opengl desktop -qpa xcb \
            -qt-harfbuzz -qt-freetype -qt-libjpeg -qt-libpng -qt-pcre -qt-sql-sqlite -qt-zlib -qt-xcb -qt-xkbcommon \
            -no-sse3 -no-ssse3 -no-sse4.1 -no-sse4.2 -no-avx -no-avx2 -no-mips_dsp -no-mips_dspr2 \
            -no-cups -no-dbus -no-evdev -no-sm -no-iconv -no-glib -no-icu -no-gif -no-nis -no-openssl -no-pch -no-sql-ibase -no-sql-odbc \
            -no-directfb -no-eglfs -no-qml-debug -no-separate-debug-info -no-rpath \
            -no-compile-examples -nomake examples -nomake tests -make libs -make tools -v
make -j 4
make install
touch build-done
cd ..
fi

# ------------------------------------------------------------------------------------
# qt5-multimedia

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

# ------------------------------------------------------------------------------------
# qt5-svg

if [ ! -d qtsvg-opensource-src-5.4.1 ]; then
curl -L http://download.qt-project.org/official_releases/qt/5.4/5.4.1/submodules/qtsvg-opensource-src-5.4.1.tar.gz -o qtsvg-opensource-src-5.4.1.tar.gz
tar -xf qtsvg-opensource-src-5.4.1.tar.gz
fi

if [ ! -f qtsvg-opensource-src-5.4.1/build-done ]; then
cd qtsvg-opensource-src-5.4.1
qmake
make -j 2
sudo make install
touch build-done
cd ..
fi

if [ ! -d qtwebkit-opensource-src-5.4.1 ]; then
curl -L http://download.qt-project.org/official_releases/qt/5.4/5.4.1/submodules/qtwebkit-opensource-src-5.4.1.tar.gz -o qtwebkit-opensource-src-5.4.1.tar.gz
tar -xf qtwebkit-opensource-src-5.4.1.tar.gz
fi

apt-get install ruby flex bison gperf
#if [ ! -f qtwebkit-opensource-src-5.4.1/build-done ]; then
cd qtwebkit-opensource-src-5.4.1
export SQLITE3SRCDIR=/src/qtbase-opensource-src-5.4.1/src/3rdparty/sqlite/
qmake
make -j 2
sudo make install
touch build-done
unset SQLITE3SRCDIR
cd ..
#fi

# ------------------------------------------------------------------------------------
# done
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
# patch to fix qt5 build

echo "
--- qtbase5-static-5.4.1.orig/src/plugins/platforms/xcb/qxcbconnection_xi2.cpp
+++ qtbase5-static-5.4.1/src/plugins/platforms/xcb/qxcbconnection_xi2.cpp
@@ -175,9 +175,11 @@ void QXcbConnection::xi2SetupDevices()
             case XIKeyClass:
                 qCDebug(lcQpaXInputDevices) << \"   it's a keyboard\";
                 break;
+#ifdef XCB_USE_XINPUT22
             case XITouchClass:
                 // will be handled in deviceForId()
                 break;
+#endif
             default:
                 qCDebug(lcQpaXInputDevices) << \"   has class\" << devices[i].classes[c]->type;
                 break;
" | sudo tee ./chroot/fix-qt5-build.patch

# ------------------------------------------------------------------------------------
# build everything

build_all

# ------------------------------------------------------------------------------------
