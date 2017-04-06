# -*- coding: UTF-8 -*-
# !/usr/bin/env python

import os
import sys

from PyQt5 import uic, QtWidgets

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)))
ui = uic.loadUiType(os.path.join(ROOT, "assets", "ui", "mainwindow.ui"))[0]

class MainWindow(QtWidgets.QMainWindow, ui):
    def __init__(self, parent=None, update_status=None, update_message=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()