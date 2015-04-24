#!/bin/bash

VERSION="0.0.1"

set -e

MINGW=x86_64-w64-mingw32
MINGW_PATH=/opt/mingw64

JOBS="-j 2"

if [ ! -f Makefile ]; then
  cd ../..
fi

export WIN32=true
export WIN64=true

export PATH=$MINGW_PATH/bin:$MINGW_PATH/$MINGW/bin:$PATH
export CC=$MINGW-gcc
export CXX=$MINGW-g++
export WINDRES=$MINGW-windres

unset CFLAGS
unset CXXFLAGS
unset CPPFLAGS
unset LDFLAGS

export WINEARCH=win64
export WINEPREFIX=~/.winepy3_x64
export PYTHON_EXE="wine C:\\\\Python34\\\\python.exe"

export CXFREEZE="$PYTHON_EXE C:\\\\Python34\\\\Scripts\\\\cxfreeze"
export PYUIC="$PYTHON_EXE -m PyQt5.uic.pyuic"
export PYRCC="wine C:\\\\Python34\\\\Lib\\\\site-packages\\\\PyQt5\\\\pyrcc5.exe"

export DEFAULT_QT=5

make clean
make $JOBS

export PYTHONPATH=`pwd`/source

rm -f  ./data/windows/MOD-*.exe
rm -rf ./data/windows/MOD-Remote
rm -rf ./data/windows/MOD-Remote-win*
cp ./source/mod-app    ./source/mod-app.pyw
cp ./source/mod-remote ./source/mod-remote.pyw
# $PYTHON_EXE ./data/windows/app.py    build_exe
$PYTHON_EXE ./data/windows/remote.py build_exe
rm -f ./source/*.pyw

cd data/windows/

cp $WINEPREFIX/drive_c/Python34/python34.dll                                     MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/*eay32.dll               MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/icu*.dll                 MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/libEGL.dll               MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/libGLESv2.dll            MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5Core.dll              MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5Gui.dll               MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5Multimedia.dll        MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5MultimediaWidgets.dll MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5Network.dll           MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5OpenGL.dll            MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5PrintSupport.dll      MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5Positioning.dll       MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5Qml.dll               MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5Quick.dll             MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5Sensors.dll           MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5Sql.dll               MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5Svg.dll               MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5WebChannel.dll        MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5WebKit.dll            MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5WebKitWidgets.dll     MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5Widgets.dll           MOD-Remote/

# Build unzipfx
make -C unzipfx-remote -f Makefile.win32 clean
make -C unzipfx-remote -f Makefile.win32

# Create zip of MOD-Remote
rm -f MOD-Remote.zip
zip -r -9 MOD-Remote.zip MOD-Remote

# Create static build
rm -f MOD-Remote.exe
cat unzipfx-remote/unzipfx2cat.exe MOD-Remote.zip > MOD-Remote.exe
chmod +x MOD-Remote.exe

# Cleanup
rm -f MOD-Remote.zip

# Create release zip
rm -rf MOD-Remote-win64
mkdir MOD-Remote-win64
mkdir MOD-Remote-win64/vcredist
cp MOD-Remote.exe README.txt MOD-Remote-win64
cp ~/.cache/winetricks/vcrun2010/vcredist_x64.exe MOD-Remote-win64/vcredist
zip -r -9 MOD-Remote_"$VERSION"_win64.zip MOD-Remote-win64

cd ../..

# Testing:
echo "export WINEPREFIX=~/.winepy3_x64"
echo "$PYTHON_EXE ./source/mod-remote"
