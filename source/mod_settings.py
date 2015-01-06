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
# Imports (Custom)

from mod_common import *

# ------------------------------------------------------------------------------------------------------------
# Imports (Global)

if config_UseQt5:
    from PyQt5.QtCore import pyqtSlot, QDir, QSettings
    from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFontMetrics
else:
    from PyQt4.QtCore import pyqtSlot, QDir, QSettings
    from PyQt4.QtGui import QDialog, QDialogButtonBox, QFontMetrics

# ------------------------------------------------------------------------------------------------------------
# Imports (UI)

from ui_mod_settings import Ui_CarlaSettingsW

# ------------------------------------------------------------------------------------------------------------
# Settings keys

# Main
MOD_KEY_MAIN_PROJECT_FOLDER   = "Main/ProjectFolder"   # str
MOD_KEY_MAIN_REFRESH_INTERVAL = "Main/RefreshInterval" # int

# ------------------------------------------------------------------------------------------------------------
# Settings defaults

# Main
MOD_DEFAULT_MAIN_PROJECT_FOLDER   = QDir.toNativeSeparators(QDir.homePath())
MOD_DEFAULT_MAIN_REFRESH_INTERVAL = 30

# ------------------------------------------------------------------------------------------------------------
# Settings Dialog

class SettingsWindow(QDialog):
    # Tab indexes
    TAB_INDEX_MAIN   = 0
    TAB_INDEX_CANVAS = 1

    # --------------------------------------------------------------------------------------------------------

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.ui = Ui_CarlaSettingsW()
        self.ui.setupUi(self)

        # ----------------------------------------------------------------------------------------------------
        # Internal stuff

        # ----------------------------------------------------------------------------------------------------
        # Set up GUI

        self.ui.lw_page.setFixedWidth(48 + 6 + 6 + QFontMetrics(self.ui.lw_page.font()).width("88888888"))

        # ----------------------------------------------------------------------------------------------------
        # Load Settings

        self.loadSettings()

        # ----------------------------------------------------------------------------------------------------
        # Set-up connections

        self.accepted.connect(self.slot_saveSettings)
        self.ui.buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.slot_resetSettings)

        # ----------------------------------------------------------------------------------------------------
        # Post-connect setup

        self.ui.lw_page.setCurrentCell(0, 0)

    # --------------------------------------------------------------------------------------------------------

    def loadSettings(self):
        settings = QSettings()
        # TODO

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_saveSettings(self):
        settings = QSettings()
        # TODO

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_resetSettings(self):
        pass # TODO

    # --------------------------------------------------------------------------------------------------------

    def done(self, r):
        QDialog.done(self, r)
        self.close()

# ------------------------------------------------------------------------------------------------------------
# Main (for testing Settings UI)

if __name__ == '__main__':
    # --------------------------------------------------------------------------------------------------------
    # App initialization

    if config_UseQt5:
        from PyQt5.QtWidgets import QApplication
    else:
        from PyQt4.QtGui import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("MOD-Settings")
    app.setApplicationVersion(config["version"])
    app.setOrganizationName("MOD")
    #app.setWindowIcon(QIcon(":/scalable/mod-app.svg"))

    # --------------------------------------------------------------------------------------------------------
    # Create GUI

    gui = SettingsWindow()

    # --------------------------------------------------------------------------------------------------------
    # Show GUI

    gui.show()

    # --------------------------------------------------------------------------------------------------------
    # App-Loop

    sys.exit(app.exec_())

# ------------------------------------------------------------------------------------------------------------
