#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------------------------------------
# Imports (cx_Freeze)

from cx_Freeze import setup, Executable
from os import getenv

# ------------------------------------------------------------------------------------------------------------
# Imports (Custom Stuff)

from mod_common import config

# ------------------------------------------------------------------------------------------------------------

options = {
  "packages": [],
  "includes": ["re", "sip", "subprocess", "inspect"],
  "build_exe": ".\\data\\windows\\%s\\" % getenv("SCRIPT_NAME"),
  "create_shared_zip":    False,
  "append_script_to_exe": True,
  "optimize":   True,
  "compressed": True
}

boptions = {
  #"iconfile": "./resources/ico/mod.icns"
}

setup(name = "MOD-Remote",
      version = config['version'],
      description = "MOD Remote",
      options = {"build_exe": options, "bdist_mac": boptions},
      executables = [Executable("./source/%s.pyw" % getenv("SCRIPT_NAME"))])

# ------------------------------------------------------------------------------------------------------------
