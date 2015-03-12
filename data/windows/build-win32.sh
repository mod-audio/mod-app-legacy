#!/bin/bash

set -e

JOBS="-j 2"

if [ ! -f Makefile ]; then
  cd ../..
fi

export WIN32=true
export WINEARCH=win32
export WINEPREFIX=~/.winepy3_x86
export PYTHON_EXE="wine C:\\\\Python34\\\\python.exe"

export CXFREEZE="$PYTHON_EXE C:\\\\Python34\\\\Scripts\\\\cxfreeze"
export PYUIC="$PYTHON_EXE -m PyQt5.uic.pyuic"
export PYRCC="wine C:\\\\Python34\\\\Lib\\\\site-packages\\\\PyQt5\\\\pyrcc5.exe"

export DEFAULT_QT=5

make $JOBS

export PYTHONPATH=`pwd`/source

rm -rf ./data/windows/MOD-*
cp ./source/mod-app    ./source/mod-app.pyw
cp ./source/mod-remote ./source/mod-remote.pyw
# $PYTHON_EXE ./data/windows/app.py    build_exe
$PYTHON_EXE ./data/windows/remote.py build_exe
rm -f ./source/*.pyw

cd data/windows/

# rm -f MOD-*/PyQt5.Qsci.pyd MOD-*/PyQt5.QtSvg.pyd MOD-*/PyQt5.QtTest.pyd MOD-*/PyQt5.QtXml.pyd

cp $WINEPREFIX/drive_c/Python34/python34.dll                                     MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/icu*.dll                 MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/libEGL.dll               MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/libGLESv2.dll            MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/*eay32.dll               MOD-Remote/
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
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5Widgets.dll           MOD-Remote/
cp $WINEPREFIX/drive_c/Python34/Lib/site-packages/PyQt5/Qt5WebKitWidgets.dll     MOD-Remote/

cd ../..

# Testing:
echo "export WINEPREFIX=~/.winepy3_x86"
echo "$PYTHON_EXE ./source/mod-remote"
