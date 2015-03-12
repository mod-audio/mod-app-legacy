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
  "packages": [],
  "includes": ["re", "sip", "subprocess", "inspect"],
  "build_exe": ".\\data\\windows\\MOD-Remote\\",
  "optimize": True,
  "compressed": True
}

setup(name = "MOD-Remote",
      version = config['version'],
      description = "MOD Remote",
      options = {"build_exe": options},
      executables = [Executable(".\\source\\mod-remote.pyw", base="Win32GUI")])

# ------------------------------------------------------------------------------------------------------------
