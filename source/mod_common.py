#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# MOD-App
# Copyright (C) 2014-2015 Filipe Coelho <falktx@falktx.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of
# the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the LICENSE file.

# ------------------------------------------------------------------------------------------------------------
# Generate a random port number between 9000 and 18000

from random import random

_PORT = str(8998 + int(random()*9000))
using_Qt4 = False

# ------------------------------------------------------------------------------------------------------------
# Mod-App Configuration

config = {
    # Address used for the webserver
    "addr": "http://127.0.0.1:%s" % _PORT,
    # Port used for the webserver
    "port": _PORT,
    # MOD-App version
    "version": "0.0.1"
}

del _PORT

# ------------------------------------------------------------------------------------------------------------
# Imports (Global)

import os
import sys

if using_Qt4:
    from PyQt4.QtCore import QDir, QSettings
else:
    from PyQt5.QtCore import QDir, QSettings

# ------------------------------------------------------------------------------------------------------------
# Set CWD

CWD = sys.path[0]

if not CWD:
    CWD = os.path.dirname(sys.argv[0])

# make it work with cxfreeze
if os.path.isfile(CWD):
    CWD = os.path.dirname(CWD)

# ------------------------------------------------------------------------------------------------------------
# Set Platform

if sys.platform == "darwin":
    LINUX   = False
    MACOS   = True
    WINDOWS = False
elif "linux" in sys.platform:
    LINUX   = True
    MACOS   = False
    WINDOWS = False
elif sys.platform in ("win32", "win64", "cygwin"):
    LINUX   = False
    MACOS   = False
    WINDOWS = True
else:
    LINUX   = False
    MACOS   = False
    WINDOWS = False

# ------------------------------------------------------------------------------------------------------------
# Use custom modules if available

if os.path.exists(os.path.join(CWD, "modules", "mod-ui", "html", "index.html")):
    print("NOTE: Using custom mod-ui module")
    sys.path = [os.path.join(CWD, "modules", "mod-ui")] + sys.path
    USING_CUSTOM_MOD_UI = True
else:
    USING_CUSTOM_MOD_UI = False

# ------------------------------------------------------------------------------------------------------------
# Set up environment for the webserver

if USING_CUSTOM_MOD_UI:
    ROOT = os.path.join(CWD, "modules", "mod-ui")
else:
    ROOT = "/usr/share/mod"

DATA_DIR = os.path.expanduser("~/.local/share/mod-data/")

os.environ['MOD_DEV_HMI']         = "1"
os.environ['MOD_DEV_HOST']        = "0"
os.environ['MOD_DEV_ENVIRONMENT'] = "0"
os.environ['MOD_LOG']             = "0"

os.environ['MOD_DATA_DIR']           = DATA_DIR
os.environ['MOD_PLUGIN_LIBRARY_DIR'] = os.path.join(DATA_DIR, "lib")
os.environ['MOD_KEY_PATH']           = os.path.join(DATA_DIR, "keys")
os.environ['MOD_CLOUD_PUB']          = os.path.join(ROOT, "keys", "cloud_key.pub")
os.environ['MOD_HTML_DIR']           = os.path.join(ROOT, "html")

os.environ['MOD_DEVICE_WEBSERVER_PORT'] = config["port"]

# ------------------------------------------------------------------------------------------------------------
# Settings keys

# Main
MOD_KEY_MAIN_PROJECT_FOLDER      = "Main/ProjectFolder"    # str
MOD_KEY_MAIN_REFRESH_INTERVAL    = "Main/RefreshInterval"  # int

# Host
MOD_KEY_HOST_VERBOSE             = "Host/Verbose"          # bool
MOD_KEY_HOST_PATH                = "Host/Path2"            # str

# WebView
MOD_KEY_WEBVIEW_INSPECTOR        = "WebView/Inspector"     # bool
MOD_KEY_WEBVIEW_VERBOSE          = "WebView/Verbose"       # bool
MOD_KEY_WEBVIEW_SHOW_INSPECTOR   = "WebView/ShowInspector" # bool

# ------------------------------------------------------------------------------------------------------------
# Settings defaults

# Main
MOD_DEFAULT_MAIN_REFRESH_INTERVAL = 30
MOD_DEFAULT_MAIN_PROJECT_FOLDER   = QDir.toNativeSeparators(QDir.homePath())

# Host
MOD_DEFAULT_HOST_VERBOSE          = False
MOD_DEFAULT_HOST_PATH             = os.path.join(os.path.dirname(__file__), "modules", "mod-host", "mod-host")

if not os.path.exists(MOD_DEFAULT_HOST_PATH):
    MOD_DEFAULT_HOST_PATH = "/usr/bin/mod-host"

# WebView
MOD_DEFAULT_WEBVIEW_INSPECTOR       = False
MOD_DEFAULT_WEBVIEW_VERBOSE         = False
MOD_DEFAULT_WEBVIEW_SHOW_INSPECTOR  = False

# ------------------------------------------------------------------------------------------------------------
# Set initial settings

def setInitialSettings():
    qsettings = QSettings("MOD", "MOD-App")
    webviewVerbose = qsettings.value(MOD_KEY_WEBVIEW_VERBOSE, MOD_DEFAULT_WEBVIEW_VERBOSE, type=bool)
    del qsettings

    os.environ['MOD_LOG'] = "1" if webviewVerbose else "0"

    from mod import settings
    settings.LOG = webviewVerbose

    # cleanup
    del webviewVerbose

# ------------------------------------------------------------------------------------------------------------
