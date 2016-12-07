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

if using_Qt4:
    from PyQt4.QtCore import pyqtSlot
    from PyQt4.QtGui import QFontMetrics, QIcon
    from PyQt4.QtGui import QDialog, QDialogButtonBox, QFileDialog, QMessageBox
else:
    from PyQt5.QtCore import pyqtSlot
    from PyQt5.QtGui import QFontMetrics, QIcon
    from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QMessageBox

# ------------------------------------------------------------------------------------------------------------
# Imports (UI)

from ui_mod_settings import Ui_SettingsWindow

# ------------------------------------------------------------------------------------------------------------
# Settings Dialog

class SettingsWindow(QDialog):
    # Tab indexes
    TAB_INDEX_MAIN    = 0
    TAB_INDEX_HOST    = 1
    TAB_INDEX_WEBVIEW = 2

    # --------------------------------------------------------------------------------------------------------

    def __init__(self, parent, isApp):
        QDialog.__init__(self, parent)
        self.ui = Ui_SettingsWindow()
        self.ui.setupUi(self)

        # ----------------------------------------------------------------------------------------------------
        # Set up GUI

        self.ui.lw_page.setFixedWidth(48 + 6*4 + QFontMetrics(self.ui.lw_page.font()).width("  WebView  "))

        if not isApp:
            self.ui.lw_page.hideRow(self.TAB_INDEX_MAIN)
            self.ui.lw_page.hideRow(self.TAB_INDEX_HOST)
            self.ui.cb_webview_verbose.setEnabled(False)
            self.ui.cb_webview_verbose.setVisible(False)

        # ----------------------------------------------------------------------------------------------------
        # Load Settings

        self.loadSettings()

        # ----------------------------------------------------------------------------------------------------
        # Set-up connections

        self.accepted.connect(self.slot_saveSettings)
        self.ui.buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.slot_resetSettings)

        self.ui.tb_main_proj_folder_open.clicked.connect(self.slot_getAndSetProjectPath)
        self.ui.tb_host_path.clicked.connect(self.slot_getAndSetIngenPath)

        # ----------------------------------------------------------------------------------------------------
        # Post-connect setup

        self.ui.lw_page.setCurrentCell(self.TAB_INDEX_MAIN if isApp else self.TAB_INDEX_WEBVIEW, 0)

    # --------------------------------------------------------------------------------------------------------

    def loadSettings(self):
        settings = QSettings()

        # ----------------------------------------------------------------------------------------------------
        # Main

        self.ui.le_main_proj_folder.setText(settings.value(MOD_KEY_MAIN_PROJECT_FOLDER, MOD_DEFAULT_MAIN_PROJECT_FOLDER, type=str))
        self.ui.sb_main_refresh_interval.setValue(settings.value(MOD_KEY_MAIN_REFRESH_INTERVAL, MOD_DEFAULT_MAIN_REFRESH_INTERVAL, type=int))

        # ----------------------------------------------------------------------------------------------------
        # Host

        self.ui.cb_host_verbose.setChecked(settings.value(MOD_KEY_HOST_VERBOSE, MOD_DEFAULT_HOST_VERBOSE, type=bool))

        hostPath = settings.value(MOD_KEY_HOST_PATH, MOD_DEFAULT_HOST_PATH, type=str)
        if hostPath.endswith("ingen"):
            hostPath = MOD_DEFAULT_HOST_PATH
        self.ui.le_host_path.setText(hostPath)

        # ----------------------------------------------------------------------------------------------------
        # WebView

        self.ui.cb_webview_inspector.setChecked(settings.value(MOD_KEY_WEBVIEW_INSPECTOR, MOD_DEFAULT_WEBVIEW_INSPECTOR, type=bool))
        self.ui.cb_webview_verbose.setChecked(settings.value(MOD_KEY_WEBVIEW_VERBOSE, MOD_DEFAULT_WEBVIEW_VERBOSE, type=bool))
        self.ui.cb_webview_show_inspector.setChecked(settings.value(MOD_KEY_WEBVIEW_SHOW_INSPECTOR, MOD_DEFAULT_WEBVIEW_SHOW_INSPECTOR, type=bool))
        self.ui.cb_webview_show_inspector.setEnabled(self.ui.cb_webview_inspector.isChecked())

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_saveSettings(self):
        settings = QSettings()

        # ----------------------------------------------------------------------------------------------------
        # Main

        settings.setValue(MOD_KEY_MAIN_PROJECT_FOLDER,   self.ui.le_main_proj_folder.text())
        settings.setValue(MOD_KEY_MAIN_REFRESH_INTERVAL, self.ui.sb_main_refresh_interval.value())

        # ----------------------------------------------------------------------------------------------------
        # Host

        settings.setValue(MOD_KEY_HOST_VERBOSE, self.ui.cb_host_verbose.isChecked())
        settings.setValue(MOD_KEY_HOST_PATH,    self.ui.le_host_path.text())

        # ----------------------------------------------------------------------------------------------------
        # WebView

        settings.setValue(MOD_KEY_WEBVIEW_INSPECTOR,      self.ui.cb_webview_inspector.isChecked())
        settings.setValue(MOD_KEY_WEBVIEW_VERBOSE,        self.ui.cb_webview_verbose.isChecked())
        settings.setValue(MOD_KEY_WEBVIEW_SHOW_INSPECTOR, self.ui.cb_webview_show_inspector.isChecked())

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_resetSettings(self):
        # ----------------------------------------------------------------------------------------------------
        # Main

        if self.ui.lw_page.currentRow() == self.TAB_INDEX_MAIN:
            self.ui.le_main_proj_folder.setText(MOD_DEFAULT_MAIN_PROJECT_FOLDER)
            self.ui.sb_main_refresh_interval.setValue(MOD_DEFAULT_MAIN_REFRESH_INTERVAL)

        # ----------------------------------------------------------------------------------------------------
        # Host

        elif self.ui.lw_page.currentRow() == self.TAB_INDEX_HOST:
            self.ui.sb_backend_audio_ins.setValue(MOD_DEFAULT_HOST_NUM_AUDIO_INS)
            self.ui.sb_backend_audio_outs.setValue(MOD_DEFAULT_HOST_NUM_AUDIO_OUTS)
            self.ui.sb_backend_midi_ins.setValue(MOD_DEFAULT_HOST_NUM_MIDI_INS)
            self.ui.sb_backend_midi_outs.setValue(MOD_DEFAULT_HOST_NUM_MIDI_OUTS)
            self.ui.sb_backend_cv_ins.setValue(MOD_DEFAULT_HOST_NUM_CV_INS)
            self.ui.sb_backend_cv_outs.setValue(MOD_DEFAULT_HOST_NUM_CV_OUTS)
            self.ui.cb_host_verbose.setChecked(MOD_DEFAULT_HOST_VERBOSE)
            self.ui.le_host_path.setText(MOD_DEFAULT_HOST_PATH)

        # ----------------------------------------------------------------------------------------------------
        # WebView

        elif self.ui.lw_page.currentRow() == self.TAB_INDEX_WEBVIEW:
            self.ui.cb_webview_inspector.setChecked(MOD_DEFAULT_WEBVIEW_INSPECTOR)
            self.ui.cb_webview_verbose.setChecked(MOD_DEFAULT_WEBVIEW_VERBOSE)
            self.ui.cb_webview_show_inspector.setChecked(MOD_DEFAULT_WEBVIEW_SHOW_INSPECTOR)

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_getAndSetProjectPath(self):
        newPath = QFileDialog.getExistingDirectory(self, self.tr("Set Default Project Path"), self.ui.le_main_proj_folder.text(), QFileDialog.ShowDirsOnly)
        if not newPath:
            return

        if not os.path.isdir(newPath):
            return QMessageBox.critical(self, self.tr("Error"), "Path must be a valid directory")

        self.ui.le_main_proj_folder.setText(newPath)

    @pyqtSlot()
    def slot_getAndSetIngenPath(self):
        path, ok = QFileDialog.getOpenFileName(self, self.tr("Set Path to ingen"), self.ui.le_host_path.text())

        if not ok:
            return
        if not path:
            return
        if not os.path.isfile(path):
            return QMessageBox.critical(self, self.tr("Error"), "Path to ingen must be a valid filename")

        self.ui.le_host_path.setText(path)

    # --------------------------------------------------------------------------------------------------------

    def done(self, r):
        QDialog.done(self, r)
        self.close()

# ------------------------------------------------------------------------------------------------------------
# Main (for testing Settings UI)

if __name__ == '__main__':
    # --------------------------------------------------------------------------------------------------------
    # App initialization

    if False:
        from PyQt4.QtGui import QApplication
    else:
        from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("MOD-Settings")
    app.setApplicationVersion(config["version"])
    app.setOrganizationName("MOD")
    app.setWindowIcon(QIcon(":/48x48/mod.png"))

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
