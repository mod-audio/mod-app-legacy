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
    from PyQt5.QtCore import pyqtSignal, pyqtSlot, qCritical, qWarning, Qt, QFileInfo, QProcess, QSettings, QThread, QTimer, QUrl
    from PyQt5.QtGui import QDesktopServices, QPixmap
    from PyQt5.QtWidgets import QAction, QApplication, QDialog, QFileDialog, QInputDialog, QLineEdit, QMainWindow, QMessageBox, QSplashScreen
    from PyQt5.QtWebKitWidgets import QWebPage, QWebView #, QWebSettings
else:
    from PyQt4.QtCore import pyqtSignal, pyqtSlot, qCritical, qWarning, Qt, QFileInfo, QProcess, QSettings, QThread, QTimer, QUrl
    from PyQt4.QtGui import QDesktopServices, QPixmap
    from PyQt4.QtGui import QAction, QApplication, QDialog, QFileDialog, QInputDialog, QLineEdit, QMainWindow, QMessageBox, QSplashScreen
    from PyQt4.QtWebKit import QWebPage, QWebView, QWebSettings

# ------------------------------------------------------------------------------------------------------------
# Imports (UI)

from ui_mod_host import Ui_HostWindow

# ------------------------------------------------------------------------------------------------------------
# Import (WebServer)

# need to set initial settings before importing MOD stuff
setInitialSettings()

from mod import jack, rebuild_database, webserver

# ------------------------------------------------------------------------------------------------------------
# WebServer Thread

class WebServerThread(QThread):
    # signals
    running = pyqtSignal()

    # globals
    prepareWasCalled = False

    def __init__(self, parent=None):
        QThread.__init__(self, parent)

    def run(self):
        if not self.prepareWasCalled:
            self.prepareWasCalled = True
            webserver.prepare()

        self.running.emit()
        webserver.start()

    def stopWait(self):
        webserver.stop()
        return self.wait(5000)

# ------------------------------------------------------------------------------------------------------------
# Host WebPage

class HostWebPage(QWebPage):
    def __init__(self, parent):
        QWebPage.__init__(self, parent)

    def javaScriptAlert(self, frame, msg):
         QMessageBox.warning(self.parent(),
                             self.tr("MOD-App Alert"),
                             msg if config_UseQt5 else Qt.escape(msg),
                             QMessageBox.Ok)

    def javaScriptConfirm(self, frame, msg):
        return (QMessageBox.question(self.parent(),
                                     self.tr("MOD-App Confirm"),
                                     msg if config_UseQt5 else Qt.escape(msg),
                                     QMessageBox.Yes|QMessageBox.No, QMessageBox.No) == QMessageBox.Yes)

    def javaScriptPrompt(self, frame, msg, default):
        res, ok = QInputDialog.getText(self.parent(),
                                       self.tr("MOD-App Prompt"),
                                       msg if config_UseQt5 else Qt.escape(msg),
                                       QLineEdit.Normal, default)
        return ok, res

    def shouldInterruptJavaScript(self):
        return (QMessageBox.question(self.parent(),
                                     self.tr("MOD-App Problem"),
                                     self.tr("The script on this page appears to have a problem. Do you want to stop the script?"),
                                     QMessageBox.Yes|QMessageBox.No, QMessageBox.No) == QMessageBox.Yes)

# ------------------------------------------------------------------------------------------------------------
# Host Splash Screen (used for LV2 scanning)

class HostSplashScreen(QSplashScreen):
    # signals
    SIGTERM = pyqtSignal()
    SIGUSR1 = pyqtSignal()

    # --------------------------------------------------------------------------------------------------------

    def __init__(self):
        QSplashScreen.__init__(self, QPixmap(":/mod-splash.jpg"), Qt.SplashScreen|Qt.WindowStaysOnTopHint)

        # ----------------------------------------------------------------------------------------------------
        # Internal stuff

        self.fApp           = QApplication.instance()
        self.fStopRequested = False

        # ----------------------------------------------------------------------------------------------------
        # Connect actions to functions

        self.SIGTERM.connect(self.slot_handleSIGTERM)

        # ----------------------------------------------------------------------------------------------------
        # Rescan if needed

        settings = QSettings()

        # read current value
        self.fNeedsRescan = settings.value("NeedsRescan", True, type=bool)

        # disable for next time
        settings.setValue("NeedsRescan", False)

    # --------------------------------------------------------------------------------------------------------
    # Callback

    def rescanIfNeeded(self):
        if not self.fNeedsRescan:
            return

        self.show()
        rebuild_database(True, self.callback)

    def callback(self, percent, uri):
        if self.fStopRequested:
            return True

        msg = "Scanning plugins: %.1f%%" % percent
        if uri:
            msg += " [ %s ]" % uri

        self.showMessage(msg, Qt.AlignLeft, Qt.white)
        self.fApp.processEvents()

        return self.fStopRequested

    # --------------------------------------------------------------------------------------------------------
    # Misc

    @pyqtSlot()
    def slot_handleSIGTERM(self):
        print("Got SIGTERM -> Stop discovering now")
        self.fStopRequested = True
        self.close()
        self.fApp.quit()

# ------------------------------------------------------------------------------------------------------------
# Host Window

class HostWindow(QMainWindow):
    # signals
    SIGTERM = pyqtSignal()
    SIGUSR1 = pyqtSignal()

    # --------------------------------------------------------------------------------------------------------

    def __init__(self, splashScreen):
        QMainWindow.__init__(self)
        self.ui = Ui_HostWindow()
        self.ui.setupUi(self)

        # ----------------------------------------------------------------------------------------------------
        # Internal stuff

        # Current project filename (used via 'File' menu actions)
        self.fProjectFilename = ""

        # first attempt of auto-start backend doesn't show an error
        self.fFirstBackendInit = True

        # Qt idle timer
        self.fIdleTimerId = 0

        # Qt web frame, used for evaluating javascript
        self.fWebFrame = None

        # to be filled with key-value pairs of current settings
        self.fSavedSettings = {}

        # Splash screen as passed in the constructor
        self.fSplashScreen = splashScreen

        # Process that runs the backend
        self.fProccessBackend = QProcess(self)
        self.fProccessBackend.setProcessChannelMode(QProcess.MergedChannels)
        self.fProccessBackend.setReadChannel(QProcess.StandardOutput)
        self.fStoppingBackend = False

        # Thread for managing the webserver
        self.fWebServerThread = WebServerThread(self)

        # ----------------------------------------------------------------------------------------------------
        # Set up GUI

        self.ui.webview = QWebView(self.ui.swp_webview)
        self.ui.webview.setMinimumWidth(980)
        self.ui.swp_webview.layout().addWidget(self.ui.webview)

        self.ui.webpage = HostWebPage(self)
        self.ui.webview.setPage(self.ui.webpage)

        self.ui.act_file_connect.setEnabled(False)
        self.ui.act_file_connect.setVisible(False)
        self.ui.act_file_disconnect.setEnabled(False)
        self.ui.act_file_disconnect.setVisible(False)

        self.ui.label_app.setText("MOD Application v%s" % config["version"])

        # disable file menu
        self.ui.act_file_new.setEnabled(False)
        self.ui.act_file_open.setEnabled(False)
        self.ui.act_file_save.setEnabled(False)
        self.ui.act_file_save_as.setEnabled(False)

        # disable pedalboard menu
        self.ui.act_pedalboard_new.setEnabled(False)
        self.ui.act_pedalboard_save.setEnabled(False)
        self.ui.act_pedalboard_save_as.setEnabled(False)
        self.ui.act_pedalboard_share.setEnabled(False)
        self.ui.menu_Pedalboard.setEnabled(False)

        # initial stopped state
        self.slot_backendFinished(-1, -1)

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

        self.fProccessBackend.error.connect(self.slot_backendError)
        self.fProccessBackend.started.connect(self.slot_backendStarted)
        self.fProccessBackend.finished.connect(self.slot_backendFinished)
        self.fProccessBackend.readyRead.connect(self.slot_backendRead)

        self.fWebServerThread.running.connect(self.slot_webServerRunning)
        self.fWebServerThread.finished.connect(self.slot_webServerFinished)

        self.ui.webview.loadStarted.connect(self.slot_webviewLoadStarted)
        self.ui.webview.loadProgress.connect(self.slot_webviewLoadProgress)
        self.ui.webview.loadFinished.connect(self.slot_webviewLoadFinished)

        self.ui.menu_Pedalboard.aboutToShow.connect(self.slot_pedalboardCheckOnline)

        self.ui.act_file_new.triggered.connect(self.slot_fileNew)
        self.ui.act_file_open.triggered.connect(self.slot_fileOpen)
        self.ui.act_file_save.triggered.connect(self.slot_fileSave)
        self.ui.act_file_save_as.triggered.connect(self.slot_fileSaveAs)

        self.ui.act_backend_start.triggered.connect(self.slot_backendStart)
        self.ui.act_backend_stop.triggered.connect(self.slot_backendStop)
        self.ui.act_backend_restart.triggered.connect(self.slot_backendRestart)
        self.ui.act_backend_rescan.triggered.connect(self.slot_backendRescan)
        #self.ui.act_backend_alternate_ui.triggered.connect(self.slot_backendAlternateUI)

        self.ui.act_pedalboard_new.triggered.connect(self.slot_pedalboardNew)
        self.ui.act_pedalboard_save.triggered.connect(self.slot_pedalboardSave)
        self.ui.act_pedalboard_save_as.triggered.connect(self.slot_pedalboardSaveAs)
        self.ui.act_pedalboard_share.triggered.connect(self.slot_pedalboardShare)

        self.ui.act_settings_configure.triggered.connect(self.slot_configure)

        self.ui.act_help_about.triggered.connect(self.slot_about)
        self.ui.act_help_project.triggered.connect(self.slot_showProject)
        self.ui.act_help_website.triggered.connect(self.slot_showWebsite)

        self.ui.b_start.clicked.connect(self.slot_backendStart)
        self.ui.b_configure.clicked.connect(self.slot_configure)
        self.ui.b_about.clicked.connect(self.slot_about)

        # ----------------------------------------------------------------------------------------------------
        # Final setup

        self.setProperWindowTitle()

        #QTimer.singleShot(0, self.slot_backendStart)

    def __del__(self):
        self.stopAndWaitForWebServer()
        self.stopAndWaitForBackend()

    # --------------------------------------------------------------------------------------------------------
    # Files

    def loadProjectNow(self):
        if not self.fProjectFilename:
            return qCritical("ERROR: loading project without filename set")

        self.ui.webview.setEnabled(False)

        # TODO
        #self.host.load_project(self.fProjectFilename)

        self.ui.webview.setEnabled(True)

    def loadProjectLater(self, filename):
        self.fProjectFilename = QFileInfo(filename).absoluteFilePath()
        self.setProperWindowTitle()
        #QTimer.singleShot(0, self.slot_loadProjectNow)

    def saveProjectNow(self):
        if not self.fProjectFilename:
            return qCritical("ERROR: saving project without filename set")

        # TODO
        #self.host.save_project(self.fProjectFilename)

    # --------------------------------------------------------------------------------------------------------
    # Files (menu actions)

    @pyqtSlot()
    def slot_fileNew(self):
        return QMessageBox.information(self, self.tr("information"), "TODO")
        # TODO - clear pedalboard
        self.fProjectFilename = ""
        self.setProperWindowTitle()

    @pyqtSlot()
    def slot_fileOpen(self):
        return QMessageBox.information(self, self.tr("information"), "TODO")

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
            #self.fProjectFilename = filename
            self.setProperWindowTitle()
            self.loadProjectNow()
        else:
            #filenameOld = self.fProjectFilename
            #self.fProjectFilename = filename
            self.loadProjectNow()
            #self.fProjectFilename = filenameOld

    @pyqtSlot()
    def slot_fileSave(self, saveAs=False):
        return QMessageBox.information(self, self.tr("information"), "TODO")

        if self.fProjectFilename and not saveAs:
            return self.saveProjectNow()

        name, ok = QInputDialog.getText(self, self.tr("Pedalboard name"), self.tr("Pedalboard name"),
                                        QLineEdit.Normal, self.fProjectFilename if saveAs else "")

        print(name, ok)

        #fileFilter = self.tr("MOD Project File (*.mod-app)")
        #filename   = QFileDialog.getSaveFileName(self, self.tr("Save MOD Project File"), self.fSavedSettings[MOD_KEY_MAIN_PROJECT_FOLDER], filter=fileFilter)

        #if config_UseQt5:
            #filename = filename[0]
        #if not filename:
            #return

        #if not filename.lower().endswith(".mod-app"):
            #filename += ".mod-app"

        if self.fProjectFilename != name:
            self.fProjectFilename = name
            self.setProperWindowTitle()

        self.saveProjectNow()

    @pyqtSlot()
    def slot_fileSaveAs(self):
        return QMessageBox.information(self, self.tr("information"), "TODO")

        self.slot_fileSave(True)

    @pyqtSlot()
    def slot_loadProjectNow(self):
        return QMessageBox.information(self, self.tr("information"), "TODO")

        self.loadProjectNow()

    # --------------------------------------------------------------------------------------------------------
    # Pedalboard (menu actions)

    @pyqtSlot()
    def slot_pedalboardCheckOnline(self):
        if self.fWebFrame is None:
            return
        isOnline = self.fWebFrame.evaluateJavaScript("$('#mod-cloud').hasClass('logged')")
        self.ui.act_pedalboard_share.setEnabled(isOnline)

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
        if self.fWebFrame is None:
            return
        self.fWebFrame.evaluateJavaScript("desktop.shareCurrentPedalboard()")

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
            <b>MOD Desktop Application</b><br/><br/>
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
    # Host (menu actions)

    @pyqtSlot()
    def slot_backendStart(self):
        if self.fProccessBackend.state() == QProcess.Running:
            print("slot_backendStart ignored")
            return

        print("slot_backendStart in progress...")

        hostPath = self.fSavedSettings[MOD_KEY_HOST_PATH]
        if hostPath.endswith("mod-host"):
            hostPath = MOD_DEFAULT_HOST_PATH

        #hostArgs = "--verbose" if self.fSavedSettings[MOD_KEY_HOST_VERBOSE] else "--nofork"
        hostArgs = ["-e", "-n", "mod-app"]

        if self.fProjectFilename and not self.fFirstBackendInit:
            hostArgs.append(self.fProjectFilename)

        self.fProccessBackend.start(hostPath, hostArgs)

    @pyqtSlot()
    def slot_backendStop(self, forced = False):
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

        # testing red color for server stopped
        self.ui.webview.blockSignals(True)
        self.ui.webview.setHtml("<html><body bgcolor='green'></body></html>")
        self.ui.webview.blockSignals(False)

        self.stopAndWaitForWebServer()
        self.stopAndWaitForBackend()

    @pyqtSlot()
    def slot_backendRestart(self):
        #self.ui.stackedwidget.setCurrentIndex(0)
        self.slot_backendStop()
        #QApplication.instance().processEvents()
        self.slot_backendStart()

    @pyqtSlot()
    def slot_backendRescan(self):
        QSettings().setValue("NeedsRescan", True)

        QMessageBox.information(self, self.tr("information"),
                                      self.tr("Rescan is now enabled for the next time you start MOD-App."))

    @pyqtSlot()
    def slot_backendAlternateUI(self):
        pass

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_backendStarted(self):
        self.fFirstBackendInit = False
        self.fSplashScreen.close()
        self.ui.act_backend_start.setEnabled(False)
        self.ui.act_backend_stop.setEnabled(True)
        self.ui.act_backend_restart.setEnabled(True)
        self.ui.w_buttons.setEnabled(False)
        self.ui.label_progress.setText(self.tr("Loading backend..."))

    @pyqtSlot(int, QProcess.ExitStatus)
    def slot_backendFinished(self, exitCode, exitStatus):
        self.fStoppingBackend = False
        self.ui.act_backend_start.setEnabled(True)
        self.ui.act_backend_stop.setEnabled(False)
        self.ui.act_backend_restart.setEnabled(False)
        self.ui.w_buttons.setEnabled(True)
        self.ui.label_progress.setText(self.tr(""))
        self.ui.stackedwidget.setCurrentIndex(0)

    @pyqtSlot(QProcess.ProcessError)
    def slot_backendError(self, error):
        firstBackendInit = self.fFirstBackendInit
        self.fFirstBackendInit = False
        self.fSplashScreen.close()

        # crashed while stopping, ignore
        if error == QProcess.Crashed and self.fStoppingBackend:
            return

        # stop webserver
        self.stopAndWaitForWebServer()

        errorStr = self.tr("Could not start host backend.\n") + self.getProcessErrorAsString(error)
        qWarning(errorStr)

        # don't show error if this is the first time starting the host
        if firstBackendInit:
            return

        # show the error message
        QMessageBox.critical(self, self.tr("Error"), errorStr)

    @pyqtSlot()
    def slot_backendRead(self):
        #if self.fProccessBackend.state() != QProcess.Running:
            #return

        for line in str(self.fProccessBackend.readAllStandardOutput().trimmed(), encoding="utf-8", errors="ignore").strip().split("\n"):
            if not line:
                continue
            if not line.strip():
                continue
            #print("INGEN:", line)

            if "Listening on socket unix:///tmp/ingen.sock" in line:
                QTimer.singleShot(0, self.fWebServerThread.start)
            elif "Activated Jack client" in line:
                QTimer.singleShot(0, self.slot_ingenStarted)
            elif "Failed to create UNIX socket" in line:
                # need to wait for ingen to create sockets so it can delete them on termination
                QTimer.singleShot(1000, self.slot_ingenStartError)
            #else:
                #print("INGEN:", line)

    @pyqtSlot()
    def slot_ingenStarted(self):
        pass

    @pyqtSlot()
    def slot_ingenStartError(self):
        self.stopAndWaitForBackend()
        self.slot_backendError(-2)

    # --------------------------------------------------------------------------------------------------------
    # Web Server

    @pyqtSlot()
    def slot_webServerRunning(self):
        print("webserver running")
        self.ui.webview.load(QUrl(config["addr"]))

    @pyqtSlot()
    def slot_webServerFinished(self):
        print("webserver finished")
        # testing red color for server finished
        self.ui.webview.blockSignals(True)
        self.ui.webview.setHtml("<html><body bgcolor='red'></body></html>")
        self.ui.webview.blockSignals(False)

    # --------------------------------------------------------------------------------------------------------
    # Web View

    @pyqtSlot()
    def slot_webviewLoadStarted(self):
        self.ui.label_progress.setText(self.tr("Loading UI..."))
        print("load started")

    @pyqtSlot(int)
    def slot_webviewLoadProgress(self, progress):
        self.ui.label_progress.setText(self.tr("Loading UI... %i%%" % progress))
        print("load progress", progress)

    @pyqtSlot(bool)
    def slot_webviewLoadFinished(self, ok):
        if ok:
            # message
            self.ui.label_progress.setText(self.tr("Loading UI... finished!"))

            # enable file menu
            self.ui.act_file_new.setEnabled(True)
            self.ui.act_file_open.setEnabled(True)
            self.ui.act_file_save.setEnabled(True)
            self.ui.act_file_save_as.setEnabled(True)

            # enable pedalboard menu
            self.ui.act_pedalboard_new.setEnabled(True)
            self.ui.act_pedalboard_save.setEnabled(True)
            self.ui.act_pedalboard_save_as.setEnabled(True)
            self.ui.act_pedalboard_share.setEnabled(True)
            self.ui.menu_Pedalboard.setEnabled(True)

            # for js evaulation
            self.fWebFrame = self.ui.webview.page().currentFrame()

            # postpone app stuff
            QTimer.singleShot(0, self.slot_webviewPostFinished)

        else:
            # message
            self.ui.label_progress.setText(self.tr("Loading UI... failed!"))

            # disable file menu
            self.ui.act_file_new.setEnabled(False)
            self.ui.act_file_open.setEnabled(False)
            self.ui.act_file_save.setEnabled(False)
            self.ui.act_file_save_as.setEnabled(False)

            # disable pedalboard menu
            self.ui.act_pedalboard_new.setEnabled(False)
            self.ui.act_pedalboard_save.setEnabled(False)
            self.ui.act_pedalboard_save_as.setEnabled(False)
            self.ui.act_pedalboard_share.setEnabled(False)
            self.ui.menu_Pedalboard.setEnabled(False)

            # stop js evaulation
            self.fWebFrame = None

            # stop backend&server
            self.stopAndWaitForWebServer()
            self.stopAndWaitForBackend()

        print("load finished")

    @pyqtSlot()
    def slot_webviewPostFinished(self):
        self.fWebFrame.evaluateJavaScript("desktop.prepareForApp()")

        settings = QSettings()

        if settings.value(MOD_KEY_HOST_AUTO_CONNNECT_INS, MOD_DEFAULT_HOST_AUTO_CONNNECT_INS, type=bool):
            os.system("jack_connect system:capture_1 mod-app:audio_in_1")
            os.system("jack_connect system:capture_2 mod-app:audio_in_2")

        if settings.value(MOD_KEY_HOST_AUTO_CONNNECT_OUTS, MOD_DEFAULT_HOST_AUTO_CONNNECT_OUTS, type=bool):
            os.system("jack_connect mod-app:audio_out_1 system:playback_1")
            os.system("jack_connect mod-app:audio_out_2 system:playback_2")

        QTimer.singleShot(0, self.slot_webviewPostFinished2)

    @pyqtSlot()
    def slot_webviewPostFinished2(self):
        self.ui.stackedwidget.setCurrentIndex(1)

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
            MOD_KEY_MAIN_PROJECT_FOLDER:      qsettings.value(MOD_KEY_MAIN_PROJECT_FOLDER,      MOD_DEFAULT_MAIN_PROJECT_FOLDER,      type=str),
            MOD_KEY_MAIN_REFRESH_INTERVAL:    qsettings.value(MOD_KEY_MAIN_REFRESH_INTERVAL,    MOD_DEFAULT_MAIN_REFRESH_INTERVAL,    type=int),
            # Host
            MOD_KEY_HOST_JACK_BUFSIZE_CHANGE: qsettings.value(MOD_KEY_HOST_JACK_BUFSIZE_CHANGE, MOD_DEFAULT_HOST_JACK_BUFSIZE_CHANGE, type=bool),
            MOD_KEY_HOST_JACK_BUFSIZE_VALUE:  qsettings.value(MOD_KEY_HOST_JACK_BUFSIZE_VALUE,  MOD_DEFAULT_HOST_JACK_BUFSIZE_VALUE,  type=int),
            MOD_KEY_HOST_VERBOSE:             qsettings.value(MOD_KEY_HOST_VERBOSE,             MOD_DEFAULT_HOST_VERBOSE,             type=bool),
            MOD_KEY_HOST_PATH:                qsettings.value(MOD_KEY_HOST_PATH,                MOD_DEFAULT_HOST_PATH,                type=str),
            # WebView
            MOD_KEY_WEBVIEW_INSPECTOR:        qsettings.value(MOD_KEY_WEBVIEW_INSPECTOR,        MOD_DEFAULT_WEBVIEW_INSPECTOR,        type=bool),
            MOD_KEY_WEBVIEW_VERBOSE:          qsettings.value(MOD_KEY_WEBVIEW_VERBOSE,          MOD_DEFAULT_WEBVIEW_VERBOSE,          type=bool)
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
        self.slot_backendStop(True)

        QMainWindow.closeEvent(self, event)

        # Needed in case the web inspector is still alive
        QApplication.instance().quit()

    def timerEvent(self, event):
        if event.timerId() == self.fIdleTimerId:
            pass

        QMainWindow.timerEvent(self, event)

    # --------------------------------------------------------------------------------------------------------
    # Internal stuff

    def getProcessErrorAsString(self, error):
        if error == -2:
            return self.tr("Ingen failed to create UNIX socket.")
        if error == QProcess.FailedToStart:
            return self.tr("Process failed to start.")
        if error == QProcess.Crashed:
            return self.tr("Process crashed.")
        if error == QProcess.Timedout:
            return self.tr("Process timed out.")
        if error == QProcess.WriteError:
            return self.tr("Process write error.")
        return self.tr("Unkown error.")

    def stopAndWaitForBackend(self):
        if self.fProccessBackend.state() == QProcess.NotRunning:
            return

        self.fStoppingBackend = True
        self.fProccessBackend.terminate()
        if not self.fProccessBackend.waitForFinished(2000):
            qWarning("Backend failed top stop cleanly, forced kill")
            self.fProccessBackend.kill()

    def stopAndWaitForWebServer(self):
        if not self.fWebServerThread.isRunning():
            return

        if not self.fWebServerThread.stopWait():
            qWarning("WebServer Thread failed top stop cleanly, forced terminate")
            self.fWebServerThread.terminate()

    def setProperWindowTitle(self):
        title = "MOD Application"

        if self.fProjectFilename:
            title += " - %s" % self.fProjectFilename

        self.setWindowTitle(title)

# ------------------------------------------------------------------------------------------------------------
