# -*- coding: UTF-8 -*-
# !/usr/bin/env python

import os
from collections import namedtuple, OrderedDict
import platform

from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import (
    pyqtSlot, Qt, QFileInfo, QSettings, QThread, QTimer, QT_VERSION_STR, PYQT_VERSION_STR
)
from PyQt5.QtGui import QKeySequence, QStandardItem, QStandardItemModel

from .conf import __author__, __title__, __description__, ROOT, MAX_RECENT_FILES
from .defaults import DELAY, THREADS, TIMEOUT
from .helpers import readTextFile
from .version import __version__

ui = uic.loadUiType(os.path.join(ROOT, "assets", "ui", "mainwindow.ui"))[0]
ColumnData = namedtuple('ColumnData', ["label", "width"])

class MainWindow(QtWidgets.QMainWindow, ui):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle("{} - {}".format(__title__, __version__))
        # Private members
        self._applicationDir = ROOT
        self._currentDir = self._applicationDir
        self._settingsFile = os.path.join(ROOT, "data", "settings.ini")
        self._recentFiles = []
        self._recentFilesActions = []
        self._proxiesModel = OrderedDict([
            ("ip", ColumnData("IP", 0)),
            ("port", ColumnData("Port", 0)),
            ("user", ColumnData("Username", 0)),
            ("pass", ColumnData("Password", 0)),
            ("type", ColumnData("Type", 0)),
            ("anon", ColumnData("Anonymous", 0)),
            ("speed", ColumnData("Speed", 0)),
            ("status", ColumnData("Status", 0)),
        ])
        self._proxiesModelColumns = list(self._proxiesModel.keys())
        # UI
        self.quitAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Q))
        self.proxiesModel = QStandardItemModel()
        self.proxiesModel.setHorizontalHeaderLabels([col.label for _, col in self._proxiesModel.items()])
        self.proxiesTable.setModel(self.proxiesModel)
        self.proxiesCountLabel = QtWidgets.QLabel(" Proxies: {:<5} ".format(0))
        self.activeThreadsLabel = QtWidgets.QLabel(" Active threads: {:<5} ".format(0))
        self.statusbar.addPermanentWidget(self.proxiesCountLabel)
        self.statusbar.addPermanentWidget(self.activeThreadsLabel)
        # Connections
        ## File Menu
        self.importProxiesAction.triggered.connect(self.importProxies)
        self.exportProxiesAction.triggered.connect(self.exportProxies)
        self.clearRecentFilesAction.triggered.connect(self.clearRecentFiles)
        self.quitAction.triggered.connect(lambda: QtWidgets.QApplication.quit())
        ## Edit menu
        self.clearTableAction.triggered.connect(self.clearTable)
        self.optionsAction.triggered.connect(self.options)
        ## Help Menu
        self.aboutAction.triggered.connect(self.about)
        ##
        self.pulseTimer = QTimer(self)
        self.pulseTimer.timeout.connect(self.pulse)
        self.pulseTimer.start(1000)
        # Events
        self.showEvent = self.onShow
        self.resizeEvent = self.onResize
        self.closeEvent = self.onClose
        # Init
        self.centerWindow()
        self.loadSettings()
        self.initRecentFiles()
        self.statusbar.showMessage("Ready.")

    # Helpers
    def centerWindow(self):
        fg = self.frameGeometry()
        c = QtWidgets.QDesktopWidget().availableGeometry().center()
        fg.moveCenter(c)
        self.move(fg.topLeft())

    def loadProxiesFromFile(self, filePath, fileType="txt", delimiter=':'):
        """
        Load proxies in valid format from file and append them to table.
        Return set of proxies if one or more proxies are successfully imported otherwise return False.
        """
        if not os.path.exists(filePath):
            return False
        # text = readTextFile(filePath)
        text = None
        with open(filePath, 'r') as f:
            text = f.read()
        if not text:
            return False
        proxies = set()
        for line in text.strip().splitlines():
            proxie = line.strip().split(delimiter)
            # TODO: validate proxie format
            if len(proxie) not in [2, 4]:
                continue
            if "{}:{}".format(proxie[0], proxie[1]) not in proxies:
                proxies.add("{}:{}".format(proxie[0], proxie[1]))
        if len(proxies) == 0:
            return False
        return proxies

    def saveProxiesToFile(self, proxies, filePath, fileType="txt"):
        """
        """
        ok = False
        msg = None
        try:
            with open(filePath, 'w') as f:
                f.write('\n'.join(proxies))
            ok = True
        except Exception as e:
            msg = str(e)

        return ok, msg

    def proxiesModelRow(self, row, columns=None):
        result = []
        model = self.proxiesModel
        if columns:
            for column in columns:
                result.append(model.data(model.index(row, self._proxiesModelColumns.index(column))))
        else:
            for i, column in self._proxiesModelColumns:
                result.append(model.data(model.index(row, i)))
        return result

    def resizeTableColumns(self):
        pass

    # Application Settings
    def loadSettings(self):
        if os.path.isfile(self._settingsFile):
            settings = QSettings(self._settingsFile, QSettings.IniFormat)
            self.restoreGeometry(settings.value("geometry", ''))
            self.restoreState(settings.value("windowState", ''))
            self._recentFiles = settings.value("recentFiles", [], type=str)

    def saveSettings(self):
        settings = QSettings(self._settingsFile, QSettings.IniFormat)
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("recentFiles", self._recentFiles)

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
            self.recentFilesMenu.addAction(self._recentFilesActions[i])
        self.updateRecentFilesActions()

    def openRecentFile(self):
        filePath = str(self.sender().data())
        proxies = self.loadProxiesFromFile(filePath)
        if proxies:
            self._currentDir = QFileInfo(filePath).absoluteDir().absolutePath()
            for proxie in proxies:
                ip, port = proxie.split(':')
                self.proxiesModel.appendRow([
                    QStandardItem(ip),
                    QStandardItem(port),
                    QStandardItem(""),
                    QStandardItem(""),
                    QStandardItem(""),
                    QStandardItem(""),
                    QStandardItem(""),
                    QStandardItem(""),
                ])

    def updateRecentFiles(self, filePath):
        if filePath not in self._recentFiles:
            self._recentFiles.insert(0, filePath)
        if len(self._recentFiles) > MAX_RECENT_FILES:
            self._recentFiles.pop()
        self.updateRecentFilesActions()
        if not self.clearRecentFilesAction.isEnabled():
            self.clearRecentFilesAction.setEnabled(True)

    def updateRecentFilesActions(self):
        for i in range(MAX_RECENT_FILES):
            if i < len(self._recentFiles):
                self._recentFilesActions[i].setText(self._recentFiles[i])
                self._recentFilesActions[i].setData(self._recentFiles[i])
                self._recentFilesActions[i].setVisible(True)
            else:
                self._recentFilesActions[i].setVisible(False)

    # Slots
    @pyqtSlot()
    def pulse(self):
        pass

    @pyqtSlot()
    def importProxies(self):
        """
        Load proxies from text file to table. Proxies should be in format ip:port or ip:port:username:password for
        private proxies, delimited by newlines
        """
        filePath, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "Import Proxies", self._currentDir, filter="Text files (*.txt)")
        proxies = self.loadProxiesFromFile(filePath, fileType)
        if proxies:
            self._currentDir = QFileInfo(filePath).absoluteDir().absolutePath()
            self.updateRecentFiles(filePath)
            for proxie in proxies:
                ip, port = proxie.split(':')
                self.proxiesModel.appendRow([
                    QStandardItem(ip),
                    QStandardItem(port),
                    QStandardItem(""),
                    QStandardItem(""),
                    QStandardItem(""),
                    QStandardItem(""),
                    QStandardItem(""),
                    QStandardItem(""),
                ])

    @pyqtSlot()
    def exportProxies(self):
        """
        Save proxies to text file in ip:port format or ip:port:username:password for private proxies, delimited by newlines
        """
        filePath, fileType = QtWidgets.QFileDialog.getSaveFileName(self, "Export Proxies", self._currentDir, filter="Text files (*.txt)")
        if ".txt" in fileType:
            fileType = "txt"
        else:
            return
        if not filePath.endswith('.' + fileType):
            filePath += '.' + fileType
        proxies = []
        for row in range(self.proxiesModel.rowCount()):
            ip, port = self.proxiesModelRow(row, ["ip", "port"])
            proxie = "{}:{}".format(ip, port)
            proxies.append(proxie)
        ok, msg = self.saveProxiesToFile(proxies, filePath, fileType)
        if ok:
            self._currentDir = QFileInfo(filePath).absoluteDir().absolutePath()
            self.updateRecentFiles(filePath)
            QtWidgets.QMessageBox.information(self, "Info", "Successfully exported proxies to {}".format(filePath))
        else:
            QtWidgets.QMessageBox.warning(self, "Error", msg)


    @pyqtSlot()
    def clearRecentFiles(self):
        self._recentFiles = []
        self.updateRecentFilesActions()
        self.clearRecentFilesAction.setEnabled(False)

    @pyqtSlot()
    def clearTable(self):
        pass

    @pyqtSlot()
    def options(self):
        pass

    @pyqtSlot()
    def about(self):
        QtWidgets.QMessageBox.about(self, "About {}".format(__title__),
            """<b>{} v{}</b>
            <p>{}
            <p>Python {} - Qt {} - PyQt {} on {}""".format(
                __title__, __version__, __description__,
                platform.python_version(), QT_VERSION_STR, PYQT_VERSION_STR,
                platform.system())
        )

    # Events
    def onResize(self, event):
        self.resizeTableColumns()
        QtWidgets.QMainWindow.resizeEvent(self, event)

    def onClose(self, event):
        self.saveSettings()
        QtWidgets.QMainWindow.closeEvent(self, event)

    def onShow(self, event):
        self.resizeTableColumns()
        QtWidgets.QMainWindow.showEvent(self, event)
