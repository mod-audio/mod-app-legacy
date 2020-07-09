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

if using_Qt4:
    from PyQt4.QtCore import pyqtSignal, pyqtSlot, qCritical, qWarning, Qt, QFileInfo, QProcess, QSettings, QSize, QThread, QTimer, QUrl
    from PyQt4.QtGui import QDesktopServices, QImage, QPainter, QPixmap
    from PyQt4.QtGui import QAction, QApplication, QDialog, QFileDialog, QInputDialog, QLineEdit, QListWidgetItem
    from PyQt4.QtGui import QMainWindow, QMessageBox, QPlainTextEdit, QVBoxLayout
    from PyQt4.QtWebKit import QWebSettings
    from PyQt4.QtWebKit import QWebInspector, QWebPage, QWebView
else:
    from PyQt5.QtCore import pyqtSignal, pyqtSlot, qCritical, qWarning, Qt, QFileInfo, QProcess, QSettings, QSize, QThread, QTimer, QUrl
    from PyQt5.QtGui import QDesktopServices, QImage, QPainter, QPixmap
    from PyQt5.QtWidgets import QAction, QApplication, QDialog, QFileDialog, QInputDialog, QLineEdit, QListWidgetItem
    from PyQt5.QtWidgets import QMainWindow, QMessageBox, QPlainTextEdit, QVBoxLayout
    from PyQt5.QtWebKit import QWebSettings
    from PyQt5.QtWebKitWidgets import QWebInspector, QWebPage, QWebView

from tornado.ioloop import IOLoop

# ------------------------------------------------------------------------------------------------------------
# Imports (UI)

from ui_mod_host import Ui_HostWindow
from ui_mod_pedalboard_open import Ui_PedalboardOpen
from ui_mod_pedalboard_save import Ui_PedalboardSave

# ------------------------------------------------------------------------------------------------------------
# Import (WebServer)

# need to set initial settings before importing MOD stuff
setInitialSettings()

from mod import webserver
from mod.session import SESSION
from modtools.utils import get_bundle_dirname, get_all_pedalboards, get_pedalboard_info

# ------------------------------------------------------------------------------------------------------------
# Imports (asyncio)

try:
    from asyncio import new_event_loop, set_event_loop
    haveAsyncIO = True
except:
    haveAsyncIO = False

# ------------------------------------------------------------------------------------------------------------
# WebServer Thread

class WebServerThread(QThread):
    # signals
    running = pyqtSignal()

    # globals
    prepareWasCalled = False

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.eventLoop = None

    def checkReady(self):
        if not SESSION.host.connected:
            IOLoop.instance().call_later(0.25, self.checkReady)
            return
        self.running.emit()

    def run(self):
        if haveAsyncIO:
            self.eventLoop = new_event_loop()
            set_event_loop(self.eventLoop)

        SESSION.host.init_host()

        if not self.prepareWasCalled:
            self.prepareWasCalled = True
            webserver.prepare(True)

        self.checkReady()
        webserver.start()

    def stopWait(self):
        webserver.stop()
        if self.eventLoop is not None:
            self.eventLoop.call_soon_threadsafe(self.eventLoop.stop)
        return self.wait(5000)

# ------------------------------------------------------------------------------------------------------------
# Host WebPage

class HostWebPage(QWebPage):
    def __init__(self, parent):
        QWebPage.__init__(self, parent)

    def javaScriptAlert(self, frame, msg):
        if USING_LIVE_ISO: return
        QMessageBox.warning(self.parent(),
                            self.tr("MOD-App Alert"),
                            msg,
                            QMessageBox.Ok)

    def javaScriptConfirm(self, frame, msg):
        if USING_LIVE_ISO: return True
        return (QMessageBox.question(self.parent(),
                                     self.tr("MOD-App Confirm"),
                                     msg,
                                     QMessageBox.Yes|QMessageBox.No, QMessageBox.No) == QMessageBox.Yes)

    def javaScriptPrompt(self, frame, msg, default):
        if USING_LIVE_ISO: return True, "live"
        res, ok = QInputDialog.getText(self.parent(),
                                       self.tr("MOD-App Prompt"),
                                       msg,
                                       QLineEdit.Normal, default)
        return ok, res

    def shouldInterruptJavaScript(self):
        if USING_LIVE_ISO: return False
        return (QMessageBox.question(self.parent(),
                                     self.tr("MOD-App Problem"),
                                     self.tr("The script on this page appears to have a problem. Do you want to stop the script?"),
                                     QMessageBox.Yes|QMessageBox.No, QMessageBox.No) == QMessageBox.Yes)

# ------------------------------------------------------------------------------------------------------------
# Open Pedalboard Window

class OpenPedalboardWindow(QDialog):
    def __init__(self, parent, pedalboards):
        QDialog.__init__(self)
        self.ui = Ui_PedalboardOpen()
        self.ui.setupUi(self)

        self.fSelectedURI = ""

        for pedalboard in pedalboards:
            item = QListWidgetItem(self.ui.listWidget)
            item.setData(Qt.UserRole, pedalboard['uri'])
            item.setIcon(QIcon(os.path.join(pedalboard['bundle'], "thumbnail.png")))
            item.setText(pedalboard['title'])
            self.ui.listWidget.addItem(item)

        self.ui.listWidget.setCurrentRow(0)

        self.accepted.connect(self.slot_setSelectedURI)
        self.ui.listWidget.doubleClicked.connect(self.accept)

    def getSelectedURI(self):
        return self.fSelectedURI

    @pyqtSlot()
    def slot_setSelectedURI(self):
        item = self.ui.listWidget.currentItem()

        if item is None:
            return

        self.fSelectedURI = item.data(Qt.UserRole)

    def done(self, r):
        QDialog.done(self, r)
        self.close()

# ------------------------------------------------------------------------------------------------------------
# Host Window

class HostWindow(QMainWindow):
    # signals
    SIGTERM = pyqtSignal()
    SIGUSR1 = pyqtSignal()

    # --------------------------------------------------------------------------------------------------------

    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_HostWindow()
        self.ui.setupUi(self)

        # ----------------------------------------------------------------------------------------------------
        # Internal stuff

        # Current mod-ui title
        #self.fCurrentBundle = ""
        self.fCurrentTitle  = ""

        # Next bundle to load (done by startup arguments)
        self.fNextBundle = ""

        # first attempt of auto-start backend doesn't show an error
        self.fFirstBackendInit = True

        # need to call session reconnect after connecting the 1st time
        self.fNeedsSessionReconnect = False

        # Qt idle timer
        self.fIdleTimerId = 0

        # Qt web frame, used for evaluating javascript
        self.fWebFrame = None

        # to be filled with key-value pairs of current settings
        self.fSavedSettings = {}

        # List of pedalboards
        self.fPedalboards = get_all_pedalboards()

        # List of current-pedalboard presets
        self.fPresetMenuList = []

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
        self.ui.webpage.setViewportSize(QSize(980, 600))
        self.ui.webview.setPage(self.ui.webpage)

        self.ui.webinspector = QWebInspector(None)
        self.ui.webinspector.resize(800, 600)
        self.ui.webinspector.setPage(self.ui.webpage)
        self.ui.webinspector.setVisible(False)

        self.ui.act_file_connect.setEnabled(False)
        self.ui.act_file_connect.setVisible(False)
        self.ui.act_file_disconnect.setEnabled(False)
        self.ui.act_file_disconnect.setVisible(False)

        self.ui.label_app.setText("MOD Application v%s" % config["version"])

        # disable file menu
        self.ui.act_file_refresh.setEnabled(False)
        self.ui.act_file_inspect.setEnabled(False)

        # disable pedalboard menu
        self.ui.act_pedalboard_new.setEnabled(False)
        self.ui.act_pedalboard_open.setEnabled(False)
        self.ui.act_pedalboard_save.setEnabled(False)
        self.ui.act_pedalboard_save_as.setEnabled(False)
        self.ui.act_pedalboard_share.setEnabled(False)
        self.ui.menu_Pedalboard.setEnabled(False)

        # disable presets menu
        self.ui.act_presets_new.setEnabled(False)
        self.ui.act_presets_save.setEnabled(False)
        self.ui.act_presets_save_as.setEnabled(False)
        self.ui.menu_Presets.setEnabled(False)

        # initial stopped state
        self.slot_backendFinished(-1, -1)

        # Qt needs this so it properly creates & resizes the webview
        self.ui.stackedwidget.setCurrentIndex(1)
        self.ui.stackedwidget.setCurrentIndex(0)

        # FIXME
        #self.ui.act_backend_stop.setVisible(False)
        #self.ui.act_backend_restart.setVisible(False)

        # ----------------------------------------------------------------------------------------------------
        # Set up GUI (special stuff for Mac OS)

        if MACOS:
            self.ui.act_file_quit.setMenuRole(QAction.QuitRole)
            self.ui.act_settings_configure.setMenuRole(QAction.PreferencesRole)
            self.ui.act_help_about.setMenuRole(QAction.AboutRole)
            #self.ui.menu_Settings.setTitle("Panels")
            #self.ui.menu_Help.hide()

        # ----------------------------------------------------------------------------------------------------
        # Set up GUI (special stuff for Live-MOD ISO)

        if USING_LIVE_ISO:
            self.ui.menubar.hide()
            self.ui.b_start.hide()
            self.ui.b_configure.hide()
            self.ui.b_about.hide()

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

        self.ui.menu_Pedalboard.aboutToShow.connect(self.slot_pedalboardCheckOnline)

        self.ui.act_file_refresh.triggered.connect(self.slot_fileRefresh)
        self.ui.act_file_inspect.triggered.connect(self.slot_fileInspect)

        self.ui.act_backend_information.triggered.connect(self.slot_backendInformation)
        self.ui.act_backend_start.triggered.connect(self.slot_backendStart)
        self.ui.act_backend_stop.triggered.connect(self.slot_backendStop)
        self.ui.act_backend_restart.triggered.connect(self.slot_backendRestart)

        self.ui.act_pedalboard_new.triggered.connect(self.slot_pedalboardNew)
        self.ui.act_pedalboard_open.triggered.connect(self.slot_pedalboardOpen)
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

        # force our custom refresh
        webReloadAction = self.ui.webpage.action(QWebPage.Reload)
        webReloadAction.triggered.disconnect()
        webReloadAction.triggered.connect(self.slot_fileRefresh)

        # ----------------------------------------------------------------------------------------------------
        # Final setup

        self.setProperWindowTitle()
        SESSION.setupApp(self._pedal_changed_callback)

        if not "--no-autostart" in sys.argv:
            QTimer.singleShot(0, self.slot_backendStart)

        QTimer.singleShot(1, self.fixWebViewSize)

    def __del__(self):
        self.stopAndWaitForWebServer()
        self.stopAndWaitForBackend()

    def _pedal_changed_callback(self, ok, bundlepath, title):
        #self.fCurrentBundle = bundlepath
        self.fCurrentTitle = title or ""
        #self.updatePresetsMenu()
        self.setProperWindowTitle()

    # --------------------------------------------------------------------------------------------------------
    # Files (menu actions)

    @pyqtSlot()
    def slot_fileRefresh(self):
        if self.fWebFrame is None:
            return

        self.ui.label_progress.setText(self.tr("Refreshing UI..."))
        self.ui.stackedwidget.setCurrentIndex(0)
        QTimer.singleShot(0, self.ui.webview.reload)

    @pyqtSlot()
    def slot_fileInspect(self):
        self.ui.webinspector.show()

    # --------------------------------------------------------------------------------------------------------
    # Pedalboard (menu actions)

    @pyqtSlot()
    def slot_pedalboardCheckOnline(self):
        if self.fWebFrame is None:
            return
        isOnline = self.fWebFrame.evaluateJavaScript("$('#mod-cloud').hasClass('logged')")
        if isOnline is None:
            return print("isOnline is None")
        self.ui.act_pedalboard_share.setEnabled(isOnline)

    @pyqtSlot()
    def slot_pedalboardNew(self):
        if self.fWebFrame is None:
            return

        self.fWebFrame.evaluateJavaScript("desktop.reset()")

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_pedalboardOpen(self):
        if len(self.fPedalboards) == 0:
            return QMessageBox.information(self, self.tr("information"), "No pedalboards found")

        dialog = OpenPedalboardWindow(self, self.fPedalboards)

        if not dialog.exec_():
            return

        pedalboard = dialog.getSelectedURI()

        if not pedalboard:
            return QMessageBox.information(self, self.tr("information"), "Invalid pedalboard selected")

        try:
            bundle = get_bundle_dirname(pedalboard)
        except:
            return

        if self.fWebFrame is None:
            return

        self.fWebFrame.evaluateJavaScript("desktop.loadPedalboard(\"%s\")" % bundle)

    def openPedalboardLater(self, filename):
        try:
            self.fNextBundle   = QFileInfo(filename).absoluteFilePath()
            self.fCurrentTitle = get_pedalboard_info(self.fNextBundle)['name']
        except:
            self.fNextBundle   = ""
            self.fCurrentTitle = ""

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_pedalboardSave(self, saveAs=False):
        if self.fWebFrame is None:
            return

        self.fWebFrame.evaluateJavaScript("desktop.saveCurrentPedalboard(%s)" % ("true" if saveAs else "false"))

    @pyqtSlot()
    def slot_pedalboardSaveAs(self):
        self.slot_pedalboardSave(True)

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_pedalboardShare(self):
        if self.fWebFrame is None:
            return

        self.fWebFrame.evaluateJavaScript("desktop.shareCurrentPedalboard()")

    # --------------------------------------------------------------------------------------------------------
    # Presets (menu actions)

    @pyqtSlot()
    def slot_presetClicked(self):
        print(self.sender().data())

    # --------------------------------------------------------------------------------------------------------
    # Settings (menu actions)

    @pyqtSlot()
    def slot_configure(self):
        dialog = SettingsWindow(self, True)
        if not dialog.exec_():
            return

        self.loadSettings(False)

    # --------------------------------------------------------------------------------------------------------
    # About (menu actions)

    @pyqtSlot()
    def slot_about(self):
        QMessageBox.about(self, self.tr("About"), self.tr("""
            <b>MOD Desktop Application</b><br/>
            <br/>
            A software to have the complete MOD environment running in your desktop.<br/>
            (C) 2015-2016 - The MOD Team<br/>
            <br/>
            Publications, products, content or services referenced herein or on the website are the exclusive trademarks or servicemarks of MOD.<br/>
            Other product and company names mentioned in the site may be the trademarks of their respective owners.<br/>
            <br/>
            All software is available under the <a href="https://www.gnu.org/licenses/gpl-2.0.html">GPL license</a>.<br/>
        """))

    @pyqtSlot()
    def slot_showProject(self):
        QDesktopServices.openUrl(QUrl("https://github.com/moddevices/mod-app"))

    @pyqtSlot()
    def slot_showWebsite(self):
        QDesktopServices.openUrl(QUrl("http://moddevices.com/"))

    # --------------------------------------------------------------------------------------------------------
    # Backend (menu actions)

    @pyqtSlot()
    def slot_backendInformation(self):
        table = """
        <table><tr>
        <td> MOD-UI port:     <td></td> %s </td>
        </tr></table>
        """ % (config["port"],)
        QMessageBox.information(self, self.tr("information"), table)

    @pyqtSlot()
    def slot_backendStart(self):
        if self.fProccessBackend.state() != QProcess.NotRunning:
            print("slot_backendStart ignored")
            return

        print("slot_backendStart in progress...")

        if USING_LIVE_ISO:
            os.system("jack_wait -w")
            os.system("jack_load mod-monitor")

            hostPath = "jack_load"
            hostArgs = ["-w", "-a", "mod-host"]

        else:
            hostPath = self.fSavedSettings[MOD_KEY_HOST_PATH]
            if hostPath.endswith("ingen"):
                hostPath = MOD_DEFAULT_HOST_PATH

            hostArgs = ["-p", "5555", "-f", "5556"]
            if self.fSavedSettings[MOD_KEY_HOST_VERBOSE]:
                hostArgs.append("-v")
            else:
                hostArgs.append("-n")

        self.fProccessBackend.start(hostPath, hostArgs)

    @pyqtSlot()
    def slot_backendStop(self):
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
        self.slot_backendStop()
        self.slot_backendStart()

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_backendStarted(self):
        self.ui.act_backend_start.setEnabled(False)
        self.ui.act_backend_stop.setEnabled(True)
        self.ui.act_backend_restart.setEnabled(True)
        self.ui.w_buttons.setEnabled(False)
        self.ui.label_progress.setText(self.tr("Loading backend..."))

    @pyqtSlot(int, QProcess.ExitStatus)
    def slot_backendFinished(self, exitCode, exitStatus):
        self.fFirstBackendInit = False
        self.fStoppingBackend = False
        self.ui.act_backend_start.setEnabled(True)
        self.ui.act_backend_stop.setEnabled(False)
        self.ui.act_backend_restart.setEnabled(False)
        self.ui.w_buttons.setEnabled(True)
        self.ui.label_progress.setText("")
        self.ui.stackedwidget.setCurrentIndex(0)

        # stop webserver
        self.stopAndWaitForWebServer()

    @pyqtSlot(QProcess.ProcessError)
    def slot_backendError(self, error):
        firstBackendInit = self.fFirstBackendInit
        self.fFirstBackendInit = False

        # stop webserver
        self.stopAndWaitForWebServer()

        # crashed while stopping, ignore
        if error == QProcess.Crashed and self.fStoppingBackend:
            return

        errorStr = self.tr("Could not start host backend.\n") + self.getProcessErrorAsString(error)
        qWarning(errorStr)

        # don't show error if this is the first time starting the host or using live-iso
        if firstBackendInit or USING_LIVE_ISO:
            return

        # show the error message
        QMessageBox.critical(self, self.tr("Error"), errorStr)

    @pyqtSlot()
    def slot_backendRead(self):
        #if self.fProccessBackend.state() != QProcess.Running:
            #return

        for line in str(self.fProccessBackend.readAllStandardOutput().trimmed(), encoding="utf-8", errors="ignore").strip().split("\n"):
            line = line.replace("\x1b[0m","").replace("\x1b[0;31m","").replace("\x1b[0;33m","").strip()
            if not line:
                continue

            if self.fSavedSettings[MOD_KEY_HOST_VERBOSE]:
                print("BACKEND:", line)

            if line == "mod-host ready!" or line == "mod-host is running.":
                QTimer.singleShot(0, self.slot_backendStartPhase2)
            #elif "Listening on socket " in line:
                #QTimer.singleShot(1000, self.slot_ingenStarted)
            ##elif "Activated Jack client " in line:
                ##QTimer.singleShot(1000, self.fWebServerThread.start)
            #elif "Failed to create UNIX socket" in line or "Could not activate Jack client" in line:
                ## need to wait for ingen to create sockets so it can delete them on termination
                #QTimer.singleShot(1000, self.slot_ingenStartError)

    @pyqtSlot()
    def slot_backendStartPhase2(self):
        if self.fProccessBackend.state() == QProcess.NotRunning:
            return

        if not self.fNeedsSessionReconnect:
            # we'll need it for next time
            self.fNeedsSessionReconnect = True
        else:
            # we need it now
            SESSION.reconnectApp()

        self.fWebServerThread.start()

    @pyqtSlot()
    def slot_backendStartError(self):
        self.stopAndWaitForBackend()
        self.slot_backendError(-2)

    # --------------------------------------------------------------------------------------------------------
    # Web Server

    @pyqtSlot()
    def slot_webServerRunning(self):
        self.ui.webview.loadStarted.connect(self.slot_webviewLoadStarted)
        self.ui.webview.loadProgress.connect(self.slot_webviewLoadProgress)
        self.ui.webview.loadFinished.connect(self.slot_webviewLoadFinished)

        print("webserver running with URL:", config["addr"])
        self.ui.webview.load(QUrl(config["addr"]))

    @pyqtSlot()
    def slot_webServerFinished(self):
        try:
            self.ui.webview.loadStarted.disconnect(self.slot_webviewLoadStarted)
            self.ui.webview.loadProgress.disconnect(self.slot_webviewLoadProgress)
            self.ui.webview.loadFinished.disconnect(self.slot_webviewLoadFinished)
        except:
            pass

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

    @pyqtSlot(bool)
    def slot_webviewLoadFinished(self, ok):
        self.ui.webview.loadStarted.disconnect(self.slot_webviewLoadStarted)
        self.ui.webview.loadProgress.disconnect(self.slot_webviewLoadProgress)
        self.ui.webview.loadFinished.disconnect(self.slot_webviewLoadFinished)

        if ok:
            # message
            self.ui.label_progress.setText(self.tr("Loading UI... finished!"))

            # enable file menu
            self.ui.act_file_refresh.setEnabled(True)
            self.ui.act_file_inspect.setEnabled(True)

            # for js evaulation
            self.fWebFrame = self.ui.webpage.currentFrame()

            # postpone app stuff
            QTimer.singleShot(100, self.slot_webviewPostFinished)

        else:
            # message
            self.ui.label_progress.setText(self.tr("Loading UI... failed!"))

            # disable file menu
            self.ui.act_file_refresh.setEnabled(False)
            self.ui.act_file_inspect.setEnabled(False)

            # disable pedalboard menu
            self.ui.act_pedalboard_new.setEnabled(False)
            self.ui.act_pedalboard_open.setEnabled(False)
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
        if self.fNextBundle:
            bundle = self.fNextBundle
            self.fNextBundle = ""
            self.fWebFrame.evaluateJavaScript("desktop.loadPedalboard(\"%s\")" % bundle)

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

        self.fSavedSettings = {
            # Main
            MOD_KEY_MAIN_PROJECT_FOLDER:    qsettings.value(MOD_KEY_MAIN_PROJECT_FOLDER,    MOD_DEFAULT_MAIN_PROJECT_FOLDER,    type=str),
            MOD_KEY_MAIN_REFRESH_INTERVAL:  qsettings.value(MOD_KEY_MAIN_REFRESH_INTERVAL,  MOD_DEFAULT_MAIN_REFRESH_INTERVAL,  type=int),
            # Host
            MOD_KEY_HOST_VERBOSE:           qsettings.value(MOD_KEY_HOST_VERBOSE,           MOD_DEFAULT_HOST_VERBOSE,           type=bool),
            MOD_KEY_HOST_PATH:              qsettings.value(MOD_KEY_HOST_PATH,              MOD_DEFAULT_HOST_PATH,              type=str),
            # WebView
            MOD_KEY_WEBVIEW_INSPECTOR:      qsettings.value(MOD_KEY_WEBVIEW_INSPECTOR,      MOD_DEFAULT_WEBVIEW_INSPECTOR,      type=bool),
            MOD_KEY_WEBVIEW_VERBOSE:        qsettings.value(MOD_KEY_WEBVIEW_VERBOSE,        MOD_DEFAULT_WEBVIEW_VERBOSE,        type=bool),
            MOD_KEY_WEBVIEW_SHOW_INSPECTOR: qsettings.value(MOD_KEY_WEBVIEW_SHOW_INSPECTOR, MOD_DEFAULT_WEBVIEW_SHOW_INSPECTOR, type=bool)
        }

        inspectorEnabled = self.fSavedSettings[MOD_KEY_WEBVIEW_INSPECTOR] and not USING_LIVE_ISO

        websettings.setAttribute(QWebSettings.DeveloperExtrasEnabled, inspectorEnabled)

        if firstTime:
            if qsettings.contains("Geometry"):
                self.restoreGeometry(qsettings.value("Geometry", ""))
            else:
                self.setWindowState(self.windowState() | Qt.WindowMaximized)

            if inspectorEnabled and self.fSavedSettings[MOD_KEY_WEBVIEW_SHOW_INSPECTOR]:
                QTimer.singleShot(1000, self.ui.webinspector.show)

        self.ui.act_file_inspect.setVisible(inspectorEnabled)

        if self.fIdleTimerId != 0:
            self.killTimer(self.fIdleTimerId)

        self.fIdleTimerId = self.startTimer(self.fSavedSettings[MOD_KEY_MAIN_REFRESH_INTERVAL])

    # --------------------------------------------------------------------------------------------------------
    # Misc

    @pyqtSlot()
    def slot_handleSIGUSR1(self):
        print("Got SIGUSR1 -> Saving project now")
        self.slot_pedalboardSave()

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
        self.slot_backendStop()

        QMainWindow.closeEvent(self, event)

        # Needed in case the web inspector is still alive
        #self.ui.webinspector.close()
        QApplication.instance().quit()

    def timerEvent(self, event):
        if event.timerId() == self.fIdleTimerId:
            pass

        QMainWindow.timerEvent(self, event)

    def resizeEvent(self, event):
        QMainWindow.resizeEvent(self, event)
        self.fixWebViewSize()

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

    def fixWebViewSize(self):
        if self.ui.stackedwidget.currentIndex() == 1:
            return

        size = self.ui.swp_intro.size()
        self.ui.swp_webview.resize(size)
        self.ui.webview.resize(size)
        self.ui.webpage.setViewportSize(size)

    def stopAndWaitForBackend(self):
        SESSION.host.close_jack()

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

        if self.fCurrentTitle:
            title += " - %s" % self.fCurrentTitle

        self.setWindowTitle(title)

    #def updatePresetsMenu(self):
        #for action in self.fPresetMenuList:
            #self.ui.menu_Presets.removeAction(action)

        #self.fPresetMenuList = []

        #if not self.fCurrentBundle:
            #return

        #for pedalboard in self.fPedalboards:
            #if self.fCurrentBundle not in pedalboard['uri']:
                #continue
            #for preset in pedalboard['presets']:
                #act = self.ui.menu_Presets.addAction(preset['label'])
                #act.setData(preset['uri'])
                #act.triggered.connect(self.slot_presetClicked)
                #self.fPresetMenuList.append(act)
