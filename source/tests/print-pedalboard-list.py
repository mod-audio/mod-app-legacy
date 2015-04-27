#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

CWD = sys.path[0]

if not CWD:
    CWD = os.path.dirname(sys.argv[0])

# make it work with cxfreeze
if os.path.isfile(CWD):
    CWD = os.path.dirname(CWD)

sys.path = [os.path.join(CWD, "..", "modules", "mod-ui")] + sys.path

from mod.lv2 import *

for x in get_pedalboards():
    print(x, "\n")
