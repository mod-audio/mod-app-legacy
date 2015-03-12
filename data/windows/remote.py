#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------------------------------------
# Imports (cx_Freeze)

from cx_Freeze import setup, Executable

# ------------------------------------------------------------------------------------------------------------
# Imports (Custom Stuff)

from mod_common import config

# ------------------------------------------------------------------------------------------------------------

options = {
  #"icon": ".\\resources\\ico\\mod.ico",
  "packages": ["PyQt5.QtNetwork", "PyQt5.QtPrintSupport", "PyQt5.QtWebKit"],
  "includes": ["re", "sip", "subprocess", "inspect"],
  "build_exe": ".\\data\\windows\\MOD-Remote\\",
  "create_shared_zip":    False,
  "append_script_to_exe": True,
  "optimize":   True,
  "compressed": True
}

setup(name = "MOD-Remote",
      version = config['version'],
      description = "MOD Remote",
      options = {"build_exe": options},
      executables = [Executable(".\\source\\mod-remote.pyw", base="Win32GUI")])

# ------------------------------------------------------------------------------------------------------------
