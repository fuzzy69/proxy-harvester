# -*- coding: UTF-8 -*-
# !/usr/bin/env python

import os
from collections import namedtuple, OrderedDict
import platform
from queue import Queue
import webbrowser

from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import pyqtSlot, Qt, QModelIndex

from application.conf import ROOT

OptionsUI = uic.loadUiType(os.path.join(ROOT, "assets", "ui", "optionsdialog.ui"))[0]

class OptionsDialog(QtWidgets.QDialog, OptionsUI):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._mainWindow = parent
        generalItem = QtWidgets.QListWidgetItem(self.listWidget)
        generalItem.setText("General")
        generalItem.setTextAlignment(Qt.AlignHCenter)
        proxySourcesItem = QtWidgets.QListWidgetItem(self.listWidget)
        proxySourcesItem.setText("Proxy Sources")
        proxySourcesItem.setTextAlignment(Qt.AlignHCenter)
        # Init values
        self.listWidget.setCurrentItem(generalItem)
        self.threadsCountSpinbox.setValue(self._mainWindow._threadsCount)
        self.requestTimeoutSpinbox.setValue(self._mainWindow._requestTimeout)
        self.requestsDelaySpinbox.setValue(self._mainWindow._requestsDelay)
        self.proxySourcesTable.setModel(self._mainWindow.proxySourcesModel)
        self.proxySourcesTable.setColumnWidth(0, 300)
        # Connections
        self.listWidget.currentItemChanged.connect(self.changePange)
        self.threadsCountSpinbox.valueChanged[int].connect(self.setThreadsCount)
        self.requestTimeoutSpinbox.valueChanged[int].connect(self.setRequestTimeout)
        self.requestsDelaySpinbox.valueChanged[int].connect(self.setRequestsDelay)
        self.proxySourcesTable.doubleClicked[QModelIndex].connect(self.openProxySourceInBrowser)

    @pyqtSlot(QtWidgets.QListWidgetItem, QtWidgets.QListWidgetItem)
    def changePange(self, current, previous):
        if not current:
            current = previous
        self.stackedWidget.setCurrentIndex(self.listWidget.row(current))

    @pyqtSlot(int)
    def setThreadsCount(self, threads):
        self._mainWindow._threadsCount = threads

    @pyqtSlot(int)
    def setRequestTimeout(self, timeout):
        self._mainWindow._requestTimeout = timeout

    @pyqtSlot(int)
    def setRequestsDelay(self, delay):
        self._mainWindow._requestsDelay = delay

    @pyqtSlot(QModelIndex)
    def openProxySourceInBrowser(self, modelIndex):
        model = modelIndex.model()
        row = modelIndex.row()
        webbrowser.open(model.data(model.index(row, 0)))
