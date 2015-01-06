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
    from PyQt5.QtCore import pyqtSignal, pyqtSlot, qCritical, qWarning, Qt, QByteArray, QDir, QFileInfo, QProcess, QSettings, QThread, QTimer, QUrl
    from PyQt5.QtGui import QImage
    from PyQt5.QtWidgets import QAction, QApplication, QDialog, QDialogButtonBox, QFileDialog, QFontMetrics, QMainWindow, QMessageBox
    from PyQt5.QtWebKitWidgets import QWebView
    from PyQt5.uic import loadUi
else:
    from PyQt4.QtCore import pyqtSignal, pyqtSlot, qCritical, qWarning, Qt, QByteArray, QDir, QFileInfo, QProcess, QSettings, QThread, QTimer, QUrl
    from PyQt4.QtGui import QImage
    from PyQt4.QtGui import QAction, QApplication, QDialog, QDialogButtonBox, QFileDialog, QFontMetrics, QMainWindow, QMessageBox
    from PyQt4.QtWebKit import QWebView
    from PyQt4.uic import loadUi

# ------------------------------------------------------------------------------------------------------------
# Imports (UI)

from ui_mod_host import Ui_HostWindow

# ------------------------------------------------------------------------------------------------------------
# Import (WebServer)

from mod import webserver

# ------------------------------------------------------------------------------------------------------------
# WebServer Thread

class WebServerThread(QThread):
    prepareWasCalled = False

    def __init__(self, parent=None):
        QThread.__init__(self, parent)

    def run(self):
        if not self.prepareWasCalled:
            self.prepareWasCalled = True
            webserver.prepare()

        webserver.start()

    def stopWait(self):
        webserver.stop()
        return self.wait(5000)

# ------------------------------------------------------------------------------------------------------------
# About Window - TODO

class AboutWindow(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        #self.ui = ui_mod_about.Ui_AboutWindow()
        #self.ui.setupUi(self)

# ------------------------------------------------------------------------------------------------------------
# Host Window

class HostWindow(QMainWindow):
    # signals
    SIGTERM = pyqtSignal()
    SIGUSR1 = pyqtSignal()

    # --------------------------------------------------------------------------------------------------------

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_HostWindow()
        self.ui.setupUi(self)

        # ----------------------------------------------------------------------------------------------------
        # Internal stuff

        self.fExportImage     = QImage()
        self.fFirstHostInit   = True
        self.fIdleTimerId     = 0
        self.fProjectFilename = ""

        # to be filled with key-value pairs of current settings
        self.fSavedSettings = {}

        self.fHostProccess = QProcess(self)
        self.fHostProccess.setProcessChannelMode(QProcess.ForwardedChannels)

        self.fWebServerThread = WebServerThread(self)

        # ----------------------------------------------------------------------------------------------------
        # Set up GUI

        self.ui.webview = QWebView(self.ui.stackedwidget)
        self.ui.webview.setMinimumWidth(980)
        self.ui.swp_webview.layout().addWidget(self.ui.webview)

        self.ui.label_progress.hide()
        self.ui.stackedwidget.setCurrentIndex(0)

        # TODO - file open/save operations
        self.ui.act_file_new.setEnabled(False)
        self.ui.act_file_open.setEnabled(False)
        self.ui.act_file_save.setEnabled(False)
        self.ui.act_file_save_as.setEnabled(False)

        # TESTING
        # webview will be blue until host and webserver are running
        # when webserver finishes color will be red
        # when host is stopped manually color will be green
        self.ui.webview.setHtml("<html><body bgcolor='blue'></body></html>")

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

        self.SIGUSR1.connect(self.slot_handleSIGUSR1)
        self.SIGTERM.connect(self.slot_handleSIGTERM)

        self.fWebServerThread.started.connect(self.slot_webServerStarted)
        self.fWebServerThread.finished.connect(self.slot_webServerFinished)

        self.ui.act_file_new.triggered.connect(self.slot_fileNew)
        self.ui.act_file_open.triggered.connect(self.slot_fileOpen)
        self.ui.act_file_save.triggered.connect(self.slot_fileSave)
        self.ui.act_file_save_as.triggered.connect(self.slot_fileSaveAs)

        self.ui.act_settings_configure.triggered.connect(self.slot_configure)

        self.ui.act_help_about.triggered.connect(self.slot_about)
        self.ui.act_help_project.triggered.connect(self.slot_showProject)
        self.ui.act_help_website.triggered.connect(self.slot_showWebsite)

        # ----------------------------------------------------------------------------------------------------
        # Final setup

        self.setProperWindowTitle()

        QTimer.singleShot(0, self.slot_hostStart)

    # --------------------------------------------------------------------------------------------------------
    # Setup

    def setProperWindowTitle(self):
        title = "MOD Application"

        if self.fProjectFilename:
            title += " - %s" % os.path.basename(self.fProjectFilename)

        self.setWindowTitle(title)

    # --------------------------------------------------------------------------------------------------------
    # Files

    def loadProjectNow(self):
        if not self.fProjectFilename:
            return qCritical("ERROR: loading project without filename set")

        # TODO

    def loadProjectLater(self, filename):
        self.fProjectFilename = QFileInfo(filename).absoluteFilePath()
        self.setProperWindowTitle()
        QTimer.singleShot(0, self.slot_loadProjectNow)

    def saveProjectNow(self):
        if not self.fProjectFilename:
            return qCritical("ERROR: saving project without filename set")

        # TODO

    # --------------------------------------------------------------------------------------------------------
    # Files (menu actions)

    @pyqtSlot()
    def slot_fileNew(self):
        # TODO - clear all

        self.fProjectFilename = ""
        self.setProperWindowTitle()

    @pyqtSlot()
    def slot_fileOpen(self):
        fileFilter = self.tr("MOD Project File (*.modp)")
        filename   = QFileDialog.getOpenFileName(self, self.tr("Open MOD Project File"), self.fSavedSettings[MOD_KEY_MAIN_PROJECT_FOLDER], filter=fileFilter)

        if config_UseQt5:
            filename = filename[0]
        if not filename:
            return

        newFile = True

        #if self.fPluginCount > 0:
            #ask = QMessageBox.question(self, self.tr("Question"), self.tr("There are some plugins loaded, do you want to remove them now?"),
                                                                          #QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            #newFile = (ask == QMessageBox.Yes)

        if newFile:
            # TODO - clear all
            self.fProjectFilename = filename
            self.setProperWindowTitle()
            self.loadProjectNow()
        else:
            filenameOld = self.fProjectFilename
            self.fProjectFilename = filename
            self.loadProjectNow()
            self.fProjectFilename = filenameOld

    @pyqtSlot()
    def slot_fileSave(self, saveAs=False):
        if self.fProjectFilename and not saveAs:
            return self.saveProjectNow()

        fileFilter = self.tr("MOD Project File (*.mod-app)")
        filename   = QFileDialog.getSaveFileName(self, self.tr("Save MOD Project File"), self.fSavedSettings[MOD_KEY_MAIN_PROJECT_FOLDER], filter=fileFilter)

        if config_UseQt5:
            filename = filename[0]
        if not filename:
            return

        if not filename.lower().endswith(".mod-app"):
            filename += ".mod-app"

        if self.fProjectFilename != filename:
            self.fProjectFilename = filename
            self.setProperWindowTitle()

        self.saveProjectNow()

    @pyqtSlot()
    def slot_fileSaveAs(self):
        self.slot_fileSave(True)

    @pyqtSlot()
    def slot_loadProjectNow(self):
        self.loadProjectNow()

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
        AboutWindow(self).exec_()

    @pyqtSlot()
    def slot_showProject(self):
        # TODO
        pass

    @pyqtSlot()
    def slot_showWebsite(self):
        # TODO
        pass

    # --------------------------------------------------------------------------------------------------------
    # Host (menu actions)

    @pyqtSlot()
    def slot_hostStart(self):
        # start mod-host asynchronously
        # qt will signal either "error" or "started" depending on the process state
        self.fHostProccess.error.connect(self.slot_hostStartError)
        self.fHostProccess.started.connect(self.slot_hostStartSuccess)
        self.fHostProccess.finished.connect(self.slot_hostFinished)
        self.fHostProccess.start("mod-host", ["--nofork"])

    @pyqtSlot(QProcess.ProcessError)
    def slot_hostStartError(self, error):
        # we're not interested on any more errors
        self.fHostProccess.error.disconnect(self.slot_hostStartError)
        self.fHostProccess.started.disconnect(self.slot_hostStartSuccess)
        self.fHostProccess.finished.disconnect(self.slot_hostFinished)

        if error == QProcess.FailedToStart:
            errorStr = self.tr("Process failed to start.")
        elif error == QProcess.Crashed:
            errorStr = self.tr("Process crashed.")
        elif error == QProcess.Timedout:
            errorStr = self.tr("Process timed out.")
        elif error == QProcess.WriteError:
            errorStr = self.tr("Process write error.")
        else:
            errorStr = self.tr("Unkown error.")

        errorStr = self.tr("Could not start host backend.\n") + errorStr
        qWarning(errorStr)

        if self.fFirstHostInit:
            self.fFirstHostInit = False
            return

        QMessageBox.critical(self, self.tr("Error"), errorStr)

    @pyqtSlot()
    def slot_hostStartSuccess(self):
        self.fFirstHostInit = False

        self.fWebServerThread.start()
        #self.fWebServerThread.wait()

        print("success")

    @pyqtSlot()
    def slot_hostStop(self, forced = False):
        # we're done with mod-host, disconnect to ignore possible errors when closing
        try:
            self.fHostProccess.error.disconnect(self.slot_hostStartError)
            self.fHostProccess.started.disconnect(self.slot_hostStartSuccess)
            self.fHostProccess.finished.disconnect(self.slot_hostFinished)
        except:
            pass

        #if self.fPluginCount > 0:
            #if not forced:
                #ask = QMessageBox.question(self, self.tr("Warning"), self.tr("There are still some plugins loaded, you need to remove them to stop the engine.\n"
                                                                            #"Do you want to do this now?"),
                                                                            #QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                #if ask != QMessageBox.Yes:
                    #return

            #self.removeAllPlugins()
            #self.host.set_engine_about_to_close()
            #self.host.remove_all_plugins()

        # unload page
        self.ui.webview.setHtml("<html><body bgcolor='green'></body></html>")

        # stop webserver
        if self.fWebServerThread.isRunning() and not self.fWebServerThread.stopWait():
            qWarning("WebServer Thread failed top stop cleanly, forcing terminate")
            self.fWebServerThread.terminate()

        # stop mod-host
        if self.fHostProccess.state() == QProcess.Running:
            self.fHostProccess.terminate()
            self.fHostProccess.waitForFinished()

    @pyqtSlot(int, QProcess.ExitStatus)
    def slot_hostFinished(self, exitCode, exitStatus):
        print("process finished")

    # --------------------------------------------------------------------------------------------------------
    # Web Server

    @pyqtSlot()
    def slot_webServerStarted(self):
        # load webserver page in our webview
        self.ui.webview.loadStarted.connect(self.slot_webviewLoadStarted)
        self.ui.webview.loadProgress.connect(self.slot_webviewLoadProgress)
        self.ui.webview.loadFinished.connect(self.slot_webviewLoadFinished)

        self.ui.webview.load(QUrl(config["addr"]))

    @pyqtSlot()
    def slot_webServerFinished(self):
        print("webserver finished")
        # testing red color for server finished
        self.ui.webview.setHtml("<html><body bgcolor='red'></body></html>")

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
            self.ui.label_progress.hide()
            self.ui.stackedwidget.setCurrentIndex(1)
        else:
            self.ui.label_progress.setText(self.tr("Loading backend... failed!"))
        print("load finished")

    # --------------------------------------------------------------------------------------------------------
    # Settings

    def saveSettings(self):
        settings = QSettings()

        settings.setValue("Geometry", self.saveGeometry())

    def loadSettings(self, firstTime):
        settings = QSettings()

        if firstTime:
            self.restoreGeometry(settings.value("Geometry", ""))

        self.fSavedSettings = {
            MOD_KEY_MAIN_PROJECT_FOLDER:   settings.value(MOD_KEY_MAIN_PROJECT_FOLDER,   MOD_DEFAULT_MAIN_PROJECT_FOLDER,   type=str),
            MOD_KEY_MAIN_REFRESH_INTERVAL: settings.value(MOD_KEY_MAIN_REFRESH_INTERVAL, MOD_DEFAULT_MAIN_REFRESH_INTERVAL, type=int)
        }

        if self.fIdleTimerId != 0:
            self.killTimer(self.fIdleTimerId)

        self.fIdleTimerId = self.startTimer(self.fSavedSettings[MOD_KEY_MAIN_REFRESH_INTERVAL])

    # --------------------------------------------------------------------------------------------------------
    # Misc

    @pyqtSlot()
    def slot_handleSIGUSR1(self):
        print("Got SIGUSR1 -> Saving project now")
        self.slot_fileSave()

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
        self.slot_hostStop(True)

        QMainWindow.closeEvent(self, event)

    def timerEvent(self, event):
        if event.timerId() == self.fIdleTimerId:
            pass

        QMainWindow.timerEvent(self, event)

# ------------------------------------------------------------------------------------------------------------
