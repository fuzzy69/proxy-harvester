# -*- coding: UTF-8 -*-
# !/usr/bin/env python

import os

from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import pyqtSlot, QSettings, QThread, QTimer

from .conf import __author__, __title__, __description__, ROOT, MAX_RECENT_FILES
from .defaults import DELAY, THREADS, TIMEOUT
from .helpers import readTextFile
from .version import __version__

ui = uic.loadUiType(os.path.join(ROOT, "assets", "ui", "mainwindow.ui"))[0]

class MainWindow(QtWidgets.QMainWindow, ui):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle("{} - {}".format(__title__, __version__))
        # Private members
        self._settingsFile = os.path.join(ROOT, "data", "settings.ini")
        self._recentFiles = []
        self._recentFilesActions = []
        # UI
        self.proxiesCountLabel = QtWidgets.QLabel(" Proxies: {:<5} ".format(0))
        self.activeThreadsLabel = QtWidgets.QLabel(" Active threads: {:<5} ".format(0))
        self.statusbar.addPermanentWidget(self.proxiesCountLabel)
        self.statusbar.addPermanentWidget(self.activeThreadsLabel)
        # Connections
        self.pulseTimer = QTimer(self)
        self.pulseTimer.timeout.connect(self.pulse)
        self.pulseTimer.start(1000)
        # Events
        # Init
        self.initRecentFiles()
        self.statusbar.showMessage("Ready.")
        self.centerWindow()

    # Helpers
    def centerWindow(self):
        fg = self.frameGeometry()
        c = QtWidgets.QDesktopWidget().availableGeometry().center()
        fg.moveCenter(c)
        self.move(fg.topLeft())

    # Application Settings
    def loadSettings(self):
        if os.path.isfile(self._settingsFile):
            settings = QSettings(self._settingsFile, QSettings.IniFormat)
            self.restoreGeometry(settings.value("geometry", ''))
            self.restoreState(settings.value("windowState", ''))

    def saveSettings(self):
        settings = QSettings(self._settingsFile, QSettings.IniFormat)
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    # Recent Files
    def initRecentFiles(self):
        for i in range(MAX_RECENT_FILES):
            self._recentFilesActions.append(QtWidgets.QAction(self))
            self._recentFilesActions[i].triggered.connect(self.openRecentFile)
            if i < len(self._recentFiles):
                if not self.clearRecentFilesAction.isEnabled():
                    self.clearRecentFilesAction.setEnabled(True)
                self._recentFilesActions[i].setData(self._recentFiles[i])
                self._recentFilesActions[i].setText(self._recentFiles[i])
                self._recentFilesActions[i].setVisible(True)
            else:
                self._recentFilesActions[i].setVisible(False)
            # self.menuRecent_Files.addAction(self._recentFilesActions[i])
        # self.updateRecentFilesActions()

    def openRecentFile(self):
        filePath = str(self.sender().data())

    # Slots
    @pyqtSlot()
    def pulse(self):
        pass

    # Events
    def onClose(self, event):
        self.saveSettings()
        QtWidgets.QMainWindow.closeEvent(self, event)
