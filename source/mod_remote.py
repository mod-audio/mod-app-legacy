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
    from PyQt5.QtWebKitWidgets import QWebPage, QWebView #, QWebSettings
else:
    from PyQt4.QtCore import pyqtSignal, pyqtSlot, Qt, QSettings, QTimer, QUrl
    from PyQt4.QtGui import QDesktopServices
    from PyQt4.QtGui import QAction, QInputDialog, QLineEdit, QMainWindow, QMessageBox
    from PyQt4.QtWebKit import QWebPage, QWebView, QWebSettings

# ------------------------------------------------------------------------------------------------------------
# Imports (UI)

from ui_mod_connect import Ui_ConnectDialog
from ui_mod_host import Ui_HostWindow

# ------------------------------------------------------------------------------------------------------------
# Remote WebPage

class RemoteWebPage(QWebPage):
    def __init__(self, parent):
        QWebPage.__init__(self, parent)

    def javaScriptAlert(self, frame, msg):
         QMessageBox.warning(self.parent(),
                             self.tr("MOD-Remote Alert"),
                             msg if config_UseQt5 else Qt.escape(msg),
                             QMessageBox.Ok)

    def javaScriptConfirm(self, frame, msg):
        return (QMessageBox.question(self.parent(),
                                     self.tr("MOD-Remote Confirm"),
                                     msg if config_UseQt5 else Qt.escape(msg),
                                     QMessageBox.Yes|QMessageBox.No, QMessageBox.No) == QMessageBox.Yes)

    def javaScriptPrompt(self, frame, msg, default):
        res, ok = QInputDialog.getText(self.parent(),
                                       self.tr("MOD-Remote Prompt"),
                                      msg if config_UseQt5 else Qt.escape(msg),
                                       QLineEdit.Normal, default)
        return ok, res

    def shouldInterruptJavaScript(self):
        return (QMessageBox.question(self.parent(),
                                     self.tr("MOD-Remote Problem"),
                                     self.tr("The script on this page appears to have a problem. Do you want to stop the script?"),
                                     QMessageBox.Yes|QMessageBox.No, QMessageBox.No) == QMessageBox.Yes)

# ------------------------------------------------------------------------------------------------------------
# Remote Connect Dialog

class RemoteConnectDialog(QDialog):
    INDEX_BT  = 0
    INDEX_LAN = 1
    INDEX_USB = 2

    def __init__(self, parent):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_ConnectDialog()
        self.ui.setupUi(self)

        self.fAddress = QUrl("")

        self.accepted.connect(self.slot_setAddress)

    def getAddress(self):
        return self.fAddress

    @pyqtSlot()
    def slot_setAddress(self):
        index = self.ui.stackedWidget.currentIndex()

        if index == self.INDEX_BT:
            address = "192.168.50.%i" % self.ui.sb_devnumber_bt.value()
            port    = 0
        elif index == self.INDEX_LAN:
            address = self.ui.le_ip_lan.text()
            port    = self.ui.sb_port_lan.value()
        elif index == self.INDEX_USB:
            address = self.ui.le_ip_usb.text()
            port    = 0
        else:
            return

        url = "http://%s" % address

        if port != 0:
            url += ":%i" % port

        self.fAddress = QUrl(url)

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

        self.ui.act_backend_start.setEnabled(False)
        self.ui.act_backend_start.setVisible(False)
        self.ui.act_backend_stop.setEnabled(False)
        self.ui.act_backend_stop.setVisible(False)
        self.ui.act_backend_restart.setEnabled(False)
        self.ui.act_backend_restart.setVisible(False)
        self.ui.act_backend_rescan.setEnabled(False)
        self.ui.act_backend_rescan.setVisible(False)
        self.ui.menu_Backend.menuAction().setEnabled(False)
        self.ui.menu_Backend.menuAction().setVisible(False)

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

        # Qt needs this so it properly creates & resizes the webview
        self.ui.stackedwidget.setCurrentIndex(1)
        self.ui.stackedwidget.setCurrentIndex(0)

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
        self.ui.act_file_disconnect.triggered.connect(self.slot_fileDisconnect)

        self.ui.act_settings_configure.triggered.connect(self.slot_configure)

        self.ui.act_help_about.triggered.connect(self.slot_about)
        self.ui.act_help_project.triggered.connect(self.slot_showProject)
        self.ui.act_help_website.triggered.connect(self.slot_showWebsite)

        self.ui.b_start.clicked.connect(self.slot_fileConnect)
        self.ui.b_configure.clicked.connect(self.slot_configure)
        self.ui.b_about.clicked.connect(self.slot_about)

        self.ui.webview.loadStarted.connect(self.slot_webviewLoadStarted)
        self.ui.webview.loadProgress.connect(self.slot_webviewLoadProgress)
        self.ui.webview.loadFinished.connect(self.slot_webviewLoadFinished)

        # ----------------------------------------------------------------------------------------------------
        # Final setup

        self.setProperWindowTitle()

        QTimer.singleShot(1, self.fixWebViewSize)

    # --------------------------------------------------------------------------------------------------------
    # Files (menu actions)

    @pyqtSlot()
    def slot_fileConnect(self):
        dialog = RemoteConnectDialog(self)
        if not dialog.exec_():
            return
        self.ui.w_buttons.setEnabled(False)
        self.ui.webview.load(dialog.getAddress())

    @pyqtSlot()
    def slot_fileDisconnect(self):
        # testing cyan color for disconnected
        self.ui.webview.blockSignals(True)
        self.ui.webview.setHtml("<html><body bgcolor='cyan'></body></html>")
        self.ui.webview.blockSignals(False)

        self.ui.w_buttons.setEnabled(True)
        self.ui.stackedwidget.setCurrentIndex(0)

    # --------------------------------------------------------------------------------------------------------
    # Settings (menu actions)

    @pyqtSlot()
    def slot_configure(self):
        dialog = SettingsWindow(self, False)
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
        self.ui.w_buttons.setEnabled(False)
        self.ui.label_progress.setText(self.tr("Loading remote..."))
        self.ui.label_progress.show()
        print("load started")

    @pyqtSlot(int)
    def slot_webviewLoadProgress(self, progress):
        self.ui.label_progress.setText(self.tr("Loading remote... %i%%" % progress))
        print("load progress", progress)

    @pyqtSlot(bool)
    def slot_webviewLoadFinished(self, ok):
        self.ui.w_buttons.setEnabled(True)

        if ok:
            # show webpage
            self.ui.label_progress.setText("")
            self.ui.label_progress.hide()
            self.ui.stackedwidget.setCurrentIndex(1)

        else:
            # hide webpage
            self.ui.label_progress.setText(self.tr("Loading remote... failed!"))
            self.ui.label_progress.show()
            self.ui.stackedwidget.setCurrentIndex(0)

        print("load finished")

    # --------------------------------------------------------------------------------------------------------
    # Settings

    def saveSettings(self):
        settings = QSettings()

        settings.setValue("Geometry", self.saveGeometry())

    def loadSettings(self, firstTime):
        qsettings   = QSettings()
        websettings = self.ui.webview.settings()

        if firstTime:
            self.restoreGeometry(qsettings.value("Geometry", ""))

        self.fSavedSettings = {
            # Main
            MOD_KEY_MAIN_PROJECT_FOLDER:   qsettings.value(MOD_KEY_MAIN_PROJECT_FOLDER,   MOD_DEFAULT_MAIN_PROJECT_FOLDER,   type=str),
            MOD_KEY_MAIN_REFRESH_INTERVAL: qsettings.value(MOD_KEY_MAIN_REFRESH_INTERVAL, MOD_DEFAULT_MAIN_REFRESH_INTERVAL, type=int),
            # WebView
            MOD_KEY_WEBVIEW_INSPECTOR:     qsettings.value(MOD_KEY_WEBVIEW_INSPECTOR,     MOD_DEFAULT_WEBVIEW_INSPECTOR,     type=bool),
            MOD_KEY_WEBVIEW_VERBOSE:       qsettings.value(MOD_KEY_WEBVIEW_VERBOSE,       MOD_DEFAULT_WEBVIEW_VERBOSE,       type=bool)
        }

        # FIXME
        if not config_UseQt5:
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

    def resizeEvent(self, event):
        QMainWindow.resizeEvent(self, event)
        self.fixWebViewSize()

    # --------------------------------------------------------------------------------------------------------
    # Internal stuff

    def fixWebViewSize(self):
        if self.ui.stackedwidget.currentIndex() == 1:
            return

        size = self.ui.swp_intro.size()
        self.ui.swp_webview.resize(size)
        self.ui.webview.resize(size)
        self.ui.webpage.setViewportSize(size)

    def setProperWindowTitle(self):
        title = "MOD Remote"

        if self.fRemoteURL:
            title += " - %s" % self.fRemoteURL

        self.setWindowTitle(title)

# ------------------------------------------------------------------------------------------------------------
