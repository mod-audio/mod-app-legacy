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

from mod_settings import *

# ------------------------------------------------------------------------------------------------------------
# Imports (Global)

if config_UseQt5:
    from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QSettings, QTimer, QUrl
    from PyQt5.QtGui import QDesktopServices
    from PyQt5.QtWidgets import QAction, QInputDialog, QLineEdit, QMainWindow, QMessageBox
    from PyQt5.QtWebKitWidgets import QWebPage, QWebView, QWebSettings
else:
    from PyQt4.QtCore import pyqtSignal, pyqtSlot, Qt, QSettings, QTimer, QUrl
    from PyQt4.QtGui import QDesktopServices
    from PyQt4.QtGui import QAction, QInputDialog, QLineEdit, QMainWindow, QMessageBox
    from PyQt4.QtWebKit import QWebPage, QWebView, QWebSettings

# ------------------------------------------------------------------------------------------------------------
# Imports (UI)

from ui_mod_host import Ui_HostWindow

# ------------------------------------------------------------------------------------------------------------
# Remote WebPage

class RemoteWebPage(QWebPage):
    def __init__(self, parent):
        QWebPage.__init__(self, parent)

    def javaScriptAlert(self, frame, msg):
         QMessageBox.warning(self.parent(),
                             self.tr("MOD-Remote Alert"),
                             Qt.escape(msg),
                             QMessageBox.Ok)

    def javaScriptConfirm(self, frame, msg):
        return (QMessageBox.question(self.parent(),
                                     self.tr("MOD-Remote Confirm"),
                                     Qt.escape(msg),
                                     QMessageBox.Yes|QMessageBox.No, QMessageBox.No) == QMessageBox.Yes)

    def javaScriptPrompt(self, frame, msg, default):
        res, ok = QInputDialog.getText(self.parent(),
                                       self.tr("MOD-Remote Prompt"),
                                       Qt.escape(msg),
                                       QLineEdit.Normal, default)
        return ok, res

    def shouldInterruptJavaScript(self):
        return (QMessageBox.question(self.parent(),
                                     self.tr("MOD-Remote Problem"),
                                     self.tr("The script on this page appears to have a problem. Do you want to stop the script?"),
                                     QMessageBox.Yes|QMessageBox.No, QMessageBox.No) == QMessageBox.Yes)

# ------------------------------------------------------------------------------------------------------------
# Remote Window

class RemoteWindow(QMainWindow):
    # signals
    SIGTERM = pyqtSignal()

    # --------------------------------------------------------------------------------------------------------

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_HostWindow()
        self.ui.setupUi(self)

        # ----------------------------------------------------------------------------------------------------
        # Internal stuff

        # Current remote url
        self.fRemoteURL = ""

        # Qt idle timer
        self.fIdleTimerId = 0

        # Qt web frame, used for evaulating javascript
        self.fWebFrame = None

        # to be filled with key-value pairs of current settings
        self.fSavedSettings = {}

        # ----------------------------------------------------------------------------------------------------
        # Set up GUI

        self.ui.webview = QWebView(self.ui.swp_webview)
        self.ui.webview.setMinimumWidth(980)
        self.ui.swp_webview.layout().addWidget(self.ui.webview)

        self.ui.webpage = RemoteWebPage(self)
        self.ui.webview.setPage(self.ui.webpage)

        self.ui.label_progress.hide()
        self.ui.stackedwidget.setCurrentIndex(0)

        self.ui.act_file_new.setEnabled(False)
        self.ui.act_file_new.setVisible(False)
        self.ui.act_file_open.setEnabled(False)
        self.ui.act_file_open.setVisible(False)
        self.ui.act_file_save.setEnabled(False)
        self.ui.act_file_save.setVisible(False)
        self.ui.act_file_save_as.setEnabled(False)
        self.ui.act_file_save_as.setVisible(False)

        self.ui.act_host_start.setEnabled(False)
        self.ui.act_host_start.setVisible(False)
        self.ui.act_host_stop.setEnabled(False)
        self.ui.act_host_stop.setVisible(False)
        self.ui.act_host_restart.setEnabled(False)
        self.ui.act_host_restart.setVisible(False)
        self.ui.menu_Host.menuAction().setEnabled(False)
        self.ui.menu_Host.menuAction().setVisible(False)

        self.ui.act_pedalboard_new.setEnabled(False)
        self.ui.act_pedalboard_new.setVisible(False)
        self.ui.act_pedalboard_save.setEnabled(False)
        self.ui.act_pedalboard_save.setVisible(False)
        self.ui.act_pedalboard_save_as.setEnabled(False)
        self.ui.act_pedalboard_save_as.setVisible(False)
        self.ui.act_pedalboard_share.setEnabled(False)
        self.ui.act_pedalboard_share.setVisible(False)
        self.ui.menu_Pedalboard.menuAction().setEnabled(False)
        self.ui.menu_Pedalboard.menuAction().setVisible(False)

        self.ui.act_settings_configure.setText(self.tr("Configure MOD-Remote"))
        self.ui.b_start.setText(self.tr("Connect..."))
        self.ui.label_app.setText("MOD Remote v%s" % config["version"])

        # TODO - set connect icon

        # ----------------------------------------------------------------------------------------------------
        # Set up GUI (special stuff for Mac OS)

        if MACOS:
            self.ui.act_file_quit.setMenuRole(QAction.QuitRole)
            self.ui.act_settings_configure.setMenuRole(QAction.PreferencesRole)
            self.ui.act_help_about.setMenuRole(QAction.AboutRole)
            #self.ui.menu_Settings.setTitle("Panels")
            #self.ui.menu_Help.hide()

        # ----------------------------------------------------------------------------------------------------
        # Load Settings

        self.loadSettings(True)

        # ----------------------------------------------------------------------------------------------------
        # Connect actions to functions

        self.SIGTERM.connect(self.slot_handleSIGTERM)

        self.ui.act_file_connect.triggered.connect(self.slot_fileConnect)

        self.ui.act_pedalboard_new.triggered.connect(self.slot_pedalboardNew)
        self.ui.act_pedalboard_save.triggered.connect(self.slot_pedalboardSave)
        self.ui.act_pedalboard_save_as.triggered.connect(self.slot_pedalboardSaveAs)
        self.ui.act_pedalboard_share.triggered.connect(self.slot_pedalboardShare)

        self.ui.act_settings_configure.triggered.connect(self.slot_configure)

        self.ui.act_help_about.triggered.connect(self.slot_about)
        self.ui.act_help_project.triggered.connect(self.slot_showProject)
        self.ui.act_help_website.triggered.connect(self.slot_showWebsite)

        self.ui.b_start.clicked.connect(self.slot_fileConnect)
        self.ui.b_configure.clicked.connect(self.slot_configure)
        self.ui.b_about.clicked.connect(self.slot_about)

        # ----------------------------------------------------------------------------------------------------
        # Final setup

        self.setProperWindowTitle()

    # --------------------------------------------------------------------------------------------------------
    # Pedalboard (menu actions)

    # --------------------------------------------------------------------------------------------------------
    # Files (menu actions)

    @pyqtSlot()
    def slot_fileConnect(self):
        return QMessageBox.information(self, self.tr("information"), "TODO")

    @pyqtSlot()
    def slot_pedalboardNew(self):
        if self.fWebFrame is None:
            return
        self.fWebFrame.evaluateJavaScript("desktop.reset()")

    @pyqtSlot()
    def slot_pedalboardSave(self):
        if self.fWebFrame is None:
            return
        self.fWebFrame.evaluateJavaScript("desktop.saveCurrentPedalboard(false)")

    @pyqtSlot()
    def slot_pedalboardSaveAs(self):
        if self.fWebFrame is None:
            return
        self.fWebFrame.evaluateJavaScript("desktop.saveCurrentPedalboard(true)")

    @pyqtSlot()
    def slot_pedalboardShare(self):
        return QMessageBox.information(self, self.tr("information"), "TODO")

        if self.fWebFrame is None:
            return
        self.fWebFrame.evaluateJavaScript("")

    # --------------------------------------------------------------------------------------------------------
    # Settings (menu actions)

    @pyqtSlot()
    def slot_configure(self):
        dialog = SettingsWindow(self)
        if not dialog.exec_():
            return

        self.loadSettings(False)

    # --------------------------------------------------------------------------------------------------------
    # About (menu actions)

    @pyqtSlot()
    def slot_about(self):
        QMessageBox.about(self, self.tr("About"), self.tr("""
            <b>MOD Remote</b><br/><br/>
            Some text will be here.<br/>
            And some more will be here too, and here and here.
        """))

    @pyqtSlot()
    def slot_showProject(self):
        QDesktopServices.openUrl(QUrl("https://github.com/portalmod/mod-app"))

    @pyqtSlot()
    def slot_showWebsite(self):
        QDesktopServices.openUrl(QUrl("http://portalmod.com/"))

    # --------------------------------------------------------------------------------------------------------
    # Web View

    @pyqtSlot()
    def slot_webviewLoadStarted(self):
        self.ui.label_progress.setText(self.tr("Loading backend..."))
        self.ui.label_progress.show()
        print("load started")

    @pyqtSlot(int)
    def slot_webviewLoadProgress(self, progress):
        self.ui.label_progress.setText(self.tr("Loading backend... %i%%" % progress))
        print("load progress", progress)

    @pyqtSlot(bool)
    def slot_webviewLoadFinished(self, ok):
        # load finished or failed
        self.ui.webview.loadStarted.disconnect(self.slot_webviewLoadStarted)
        self.ui.webview.loadProgress.disconnect(self.slot_webviewLoadProgress)
        self.ui.webview.loadFinished.disconnect(self.slot_webviewLoadFinished)

        if ok:
            # for js evaulation
            self.fWebFrame = self.ui.webview.page().currentFrame()

            # show webpage
            self.ui.label_progress.setText("")
            self.ui.label_progress.hide()
            self.ui.stackedwidget.setCurrentIndex(1)

            # postpone app stuff
            QTimer.singleShot(0, self.slot_webviewPostFinished)

        else:
            # stop js evaulation
            self.fWebFrame = None

            # hide webpage
            self.ui.label_progress.setText(self.tr("Loading backend... failed!"))
            self.ui.label_progress.show()
            self.ui.stackedwidget.setCurrentIndex(0)

        print("load finished")

    @pyqtSlot(bool)
    def slot_webviewPostFinished(self):
        self.fWebFrame.evaluateJavaScript("desktop.prepareForApp()")

    # --------------------------------------------------------------------------------------------------------
    # Settings

    def saveSettings(self):
        settings = QSettings()

        settings.setValue("Geometry", self.saveGeometry())

    def loadSettings(self, firstTime):
        qsettings   = QSettings()
        websettings = self.ui.webview.settings()

        if firstTime:
            if qsettings.contains("Geometry"):
                self.restoreGeometry(qsettings.value("Geometry", ""))
            else:
                self.setWindowState(self.windowState() | Qt.WindowMaximized)

        self.fSavedSettings = {
            # Main
            MOD_KEY_MAIN_PROJECT_FOLDER:   qsettings.value(MOD_KEY_MAIN_PROJECT_FOLDER,   MOD_DEFAULT_MAIN_PROJECT_FOLDER,   type=str),
            MOD_KEY_MAIN_REFRESH_INTERVAL: qsettings.value(MOD_KEY_MAIN_REFRESH_INTERVAL, MOD_DEFAULT_MAIN_REFRESH_INTERVAL, type=int),
            # WebView
            MOD_KEY_WEBVIEW_INSPECTOR:     qsettings.value(MOD_KEY_WEBVIEW_INSPECTOR,     MOD_DEFAULT_WEBVIEW_INSPECTOR,     type=bool),
            MOD_KEY_WEBVIEW_VERBOSE:       qsettings.value(MOD_KEY_WEBVIEW_VERBOSE,       MOD_DEFAULT_WEBVIEW_VERBOSE,       type=bool)
        }

        websettings.setAttribute(QWebSettings.DeveloperExtrasEnabled, self.fSavedSettings[MOD_KEY_WEBVIEW_INSPECTOR])

        if self.fIdleTimerId != 0:
            self.killTimer(self.fIdleTimerId)

        self.fIdleTimerId = self.startTimer(self.fSavedSettings[MOD_KEY_MAIN_REFRESH_INTERVAL])

    # --------------------------------------------------------------------------------------------------------
    # Misc

    @pyqtSlot()
    def slot_handleSIGTERM(self):
        print("Got SIGTERM -> Closing now")
        self.close()

    # --------------------------------------------------------------------------------------------------------
    # Qt events

    def closeEvent(self, event):
        if self.fIdleTimerId != 0:
            self.killTimer(self.fIdleTimerId)
            self.fIdleTimerId = 0

        self.saveSettings()

        QMainWindow.closeEvent(self, event)

    def timerEvent(self, event):
        if event.timerId() == self.fIdleTimerId:
            pass

        QMainWindow.timerEvent(self, event)

    # --------------------------------------------------------------------------------------------------------
    # Internal stuff

    def setProperWindowTitle(self):
        title = "MOD Remote"

        if self.fRemoteURL:
            title += " - %s" % self.fRemoteURL

        self.setWindowTitle(title)

# ------------------------------------------------------------------------------------------------------------
