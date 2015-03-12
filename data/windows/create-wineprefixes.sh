#!/bin/bash

rm -rf ~/.winepy3
rm -rf ~/.winepy3_x86
rm -rf ~/.winepy3_x64

export WINEARCH=win32
export WINEPREFIX=~/.winepy3_x86
wineboot
regsvr32 wineasio.dll
winetricks vcrun2010
winetricks corefonts
winetricks fontsmooth=rgb

# cd data/windows/python
# msiexec /i python-3.4.2.msi /qn
# wine cx_Freeze-4.3.3.win32-py3.4.exe
# wine PyQt5-5.3.2-gpl-Py3.4-Qt5.3.1-x32.exe
# cd ../../..
