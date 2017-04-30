# -*- coding: UTF-8 -*-
# !/usr/bin/env python

import os

from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import QSettings, QThread

from .conf import ROOT
from .helpers import readTextFile
from .utils import dummy
from .workers import Worker

ui = uic.loadUiType(os.path.join(ROOT, "assets", "ui", "mainwindow.ui"))[0]

class MainWindow(QtWidgets.QMainWindow, ui):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self._settingsFile = os.path.join(ROOT, "data", "settings.ini")
        # self._threadPool = []
        # self.startButton.clicked.connect(self.test)
        # self.closeEvent = self.onClose
        # self.loadSettings()
        # self.centerWindow()
        # self.progressBar = QtWidgets.QProgressBar()
        # self.progressBar.setGeometry(10, 10, 100, 20)
        # self.progressBar.setValue(50)
        # self.statusbar.addPermanentWidget(self.progressBar)

    def centerWindow(self):
        fg = self.frameGeometry()
        c = QtWidgets.QDesktopWidget().availableGeometry().center()
        fg.moveCenter(c)
        self.move(fg.topLeft())

    def loadSettings(self):
        if os.path.isfile(self._settingsFile):
            settings = QSettings(self._settingsFile, QSettings.IniFormat)
            self.restoreGeometry(settings.value("geometry", ''))
            self.restoreState(settings.value("windowState", ''))

    def saveSettings(self):
        settings = QSettings(self._settingsFile, QSettings.IniFormat)
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    def onClose(self, event):
        self.saveSettings()
        QtWidgets.QMainWindow.closeEvent(self, event)

    def test(self):
        print("Ok")
        text = readTextFile(os.path.join(ROOT, "data", "settings.ini"))
        print(text)
        # self.thread = QThread()
        # self.thread.start()
        # self.worker = Worker(dummy, 1)
        # self.worker.moveToThread(self.thread)
        # self.worker.start.emit()
        # self.worker.finished.connect(self.test2)
        # self.thread.finished.connect(self.worker.deleteLater)
        # self._threadPool.append(thread)

    def test2(self, string):
        print(string)

        print("Ok")