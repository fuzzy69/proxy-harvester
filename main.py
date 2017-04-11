# -*- coding: UTF-8 -*-
# !/usr/bin/env python

import os
import sys

from PyQt5.QtCore import QSettings
from PyQt5 import uic, QtWidgets

__author__ = "fuzzy69"
__title__ = "Proxy Harvester"

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)))
ui = uic.loadUiType(os.path.join(ROOT, "assets", "ui", "mainwindow.ui"))[0]

class MainWindow(QtWidgets.QMainWindow, ui):
    def __init__(self, parent=None, update_status=None, update_message=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self._settingsFile = os.path.join(ROOT, "data", "settings.ini")
        self.closeEvent = self.onClose
        self.loadSettings()
        self.centerWindow()

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

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()