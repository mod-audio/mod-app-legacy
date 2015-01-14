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
# Mod-App Configuration

from mod_config import *

config = {
    # Address used for the webserver
    "addr": "http://127.0.0.1:7988",
    # Port used for the webserver
    "port": "7988",
    # MOD-App version
    "version": "0.0.0"
}

# ------------------------------------------------------------------------------------------------------------
# Imports (Global)

import os
import sys

# ------------------------------------------------------------------------------------------------------------
# Set CWD

CWD = sys.path[0]

if not CWD:
    CWD = os.path.dirname(sys.argv[0])

# make it work with cxfreeze
if os.path.isfile(CWD):
    CWD = os.path.dirname(CWD)

# ------------------------------------------------------------------------------------------------------------
# Use custom modules if available

if os.path.exists(os.path.join(CWD, "modules", "mod-ui")):
    print("NOTE: Using custom mod-ui module")
    sys.path = [os.path.join(CWD, "modules", "mod-ui")] + sys.path
    usingCustomModules = True
else:
    usingCustomModules = False

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
# Set up environment for the webserver

if usingCustomModules:
    ROOT = os.path.join(CWD, "modules")
else:
    ROOT = "/usr/share"

DATA_DIR = os.path.expanduser("~/.local/share/mod-data/")

os.environ['MOD_DEV_HOST'] = "0"
os.environ['MOD_DEV_HMI']  = "1"
os.environ['MOD_DESKTOP']  = "1"
os.environ['MOD_LOG']      = "0"

os.environ['MOD_DATA_DIR']           = DATA_DIR
os.environ['MOD_HTML_DIR']           = os.path.join(ROOT, "mod-ui", "html")
os.environ['MOD_PLUGIN_LIBRARY_DIR'] = os.path.join(DATA_DIR, 'lib')

os.environ['MOD_PHANTOM_BINARY']        = "/usr/bin/phantomjs"
os.environ['MOD_SCREENSHOT_JS']         = os.path.join(ROOT, "mod-ui", "screenshot.js")
os.environ['MOD_DEVICE_WEBSERVER_PORT'] = config["port"]

# ------------------------------------------------------------------------------------------------------------
