# -*- coding: UTF-8 -*-
# !/usr/bin/env python

import os
from collections import namedtuple, OrderedDict
import platform
from queue import Queue

from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import (
    pyqtSlot, Qt, QFileInfo, QModelIndex, QSettings, QThread, QTimer, QT_VERSION_STR, PYQT_VERSION_STR
)
from PyQt5.QtGui import QKeySequence, QStandardItem, QStandardItemModel

from application.conf import __author__, __title__, __description__, ROOT, MAX_RECENT_FILES
from application.defaults import DELAY, THREADS, TIMEOUT, PROXY_SOURCES
from application.helpers import readTextFile, Logger
from application.optionsdialog import OptionsDialog
from application.proxy import Proxy
from application.utils import get_real_ip, split_list
from application.version import __version__
from application.workers import CheckProxiesWorker, MyThread, ScrapeProxiesWorker


ui = uic.loadUiType(os.path.join(ROOT, "assets", "ui", "mainwindow.ui"))[0]
ColumnData = namedtuple("ColumnData", ["label", "width"])
logger = Logger(__name__)

class MainWindow(QtWidgets.QMainWindow, ui):
    def __init__(self, parent=None):
        super().__init__(parent)
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
            ("speed", ColumnData("Speed (sec)", 0)),
            ("status", ColumnData("Status", 0)),
        ])
        self._proxiesModelColumns = list(self._proxiesModel.keys())
        self._proxies = set()
        self._progressTotal = 0
        self._progressDone = 0
        self._threadsCount = THREADS
        self._threads = []
        self._workers = []
        self._realIP = None
        self._requestTimeout = TIMEOUT
        self._requestsDelay = DELAY
        # UI
        self.quitAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Q))
        self.proxiesModel = QStandardItemModel()
        self.proxiesModel.setHorizontalHeaderLabels([col.label for _, col in self._proxiesModel.items()])
        self.proxiesTable.setModel(self.proxiesModel)
        self.proxiesTable.setColumnWidth(0, 200)
        self.proxySourcesModel = QStandardItemModel(self)
        self.proxySourcesModel.setHorizontalHeaderLabels(["URL", "Status"])
        for i, url in enumerate(PROXY_SOURCES):
            self.proxySourcesModel.appendRow([
                QStandardItem(url),
                QStandardItem(""),
            ])
        self.realIPLabel = QtWidgets.QLabel(" Real IP: {:<15} ".format("___.___.___.___"))
        self.proxiesCountLabel = QtWidgets.QLabel(" Proxies: {:<5} ".format(0))
        self.activeThreadsLabel = QtWidgets.QLabel(" Active threads: {:<5} ".format(0))
        self.statusbar.addPermanentWidget(self.realIPLabel)
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
        self.scrapeProxiesButton.clicked.connect(self.scrapeProxies)
        self.checkProxiesButton.clicked.connect(self.checkProxies)
        self.stopButton.clicked.connect(self.stop)
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
        Load proxies in valid format from file and append them to table. Ignore duplicates.
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
        added_proxies = 0
        for line in text.strip().splitlines():
            ip, port = line.strip().split(delimiter)
            try:
                proxy = Proxy(ip, int(port))
            except ValueError as e:
                logger.warning("Invalid proxy {ip}:{port}, {msg}".format(ip=ip, port=port, msg=e))
                continue
            if proxy not in self._proxies:
                self._proxies.add(proxy)
                added_proxies += 1
            else:
                logger.info("Skipped duplicate proxy: {}".format(proxy))
        if not added_proxies:
            return False

        return self._proxies

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

    def setProxiesModelCell(self, row, column, value):
        self.proxiesModel.setData(self.proxiesModel.index(row, self._proxiesModelColumns.index(column)), value)

    def resizeTableColumns(self):
        pass

    # Application Settings
    def loadSettings(self):
        if os.path.isfile(self._settingsFile):
            settings = QSettings(self._settingsFile, QSettings.IniFormat)
            self.restoreGeometry(settings.value("geometry", ''))
            self.restoreState(settings.value("windowState", ''))
            self._recentFiles = settings.value("recentFiles", [], type=str)
            self._threadsCount = settings.value("threadsCount", THREADS, type=int)
            self._requestTimeout = settings.value("requestTimeout", TIMEOUT, type=int)
            self._requestsDelay = settings.value("requestsDelay", DELAY, type=int)

    def saveSettings(self):
        settings = QSettings(self._settingsFile, QSettings.IniFormat)
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("recentFiles", self._recentFiles)
        settings.setValue("threadsCount", self._threadsCount)
        settings.setValue("requestTimeout", self._requestTimeout)
        settings.setValue("requestsDelay", self._requestsDelay)

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
            for proxy in proxies:
                self.proxiesModel.appendRow([
                    QStandardItem(proxy.ip),
                    QStandardItem(str(proxy.port)),
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

    def resetTable(self):
        for i in range(self.proxiesModel.rowCount()):
            self.setProxiesModelCell(i, "status", "")

    # Slots
    @pyqtSlot()
    def pulse(self):
        """
        Periodically update gui with usefull info and controls
        """
        self.proxiesCountLabel.setText(" Proxies: {:<5} ".format(self.proxiesModel.rowCount()))
        self.activeThreadsLabel.setText(" Active threads: {:<5} ".format(MyThread.activeCount))
        if MyThread.activeCount == 0:
            if not self.scrapeProxiesButton.isEnabled():
                self.scrapeProxiesButton.setEnabled(True)
            if not self.checkProxiesButton.isEnabled() and self.proxiesModel.rowCount() > 0:
                    self.checkProxiesButton.setEnabled(True)
            if self.stopButton.isEnabled():
                self.stopButton.setEnabled(False)
            self.statusbar.showMessage("Ready.")

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
            for proxy in proxies:
                self.proxiesModel.appendRow([
                    QStandardItem(proxy.ip),
                    QStandardItem(str(proxy.port)),
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
        self._proxies = set()
        for i in reversed(range(self.proxiesModel.rowCount())):
            self.proxiesModel.removeRow(i)

    @pyqtSlot()
    def options(self):
        dialog = OptionsDialog(self)
        dialog.exec_()
        dialog.deleteLater()

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

    @pyqtSlot()
    def scrapeProxies(self):
        self.scrapeProxiesButton.setEnabled(False)
        self.checkProxiesButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.statusbar.showMessage("Scraping proxies ...")
        self.resetTable()
        self.progressBar.setValue(0)
        queues = split_list(PROXY_SOURCES, self._threadsCount)
        self._progressTotal = len(PROXY_SOURCES)
        self._progressDone = 0
        self._threads = []
        self._workers = []
        for i, urls in enumerate(queues):
            self._threads.append(MyThread())
            queue = Queue()
            for url in urls:
                queue.put(url)
            self._workers.append(
                ScrapeProxiesWorker(queue=queue, timeout=TIMEOUT, delay=DELAY)
            )
            self._workers[i].moveToThread(self._threads[i])
            self._threads[i].started.connect(self._workers[i].start)
            self._threads[i].finished.connect(self._threads[i].deleteLater)
            self._workers[i].status.connect(self.onStatus)
            self._workers[i].result.connect(self.onResult)
            self._workers[i].finished.connect(self._threads[i].quit)
            self._workers[i].finished.connect(self._workers[i].deleteLater)
        for i in range(self._threadsCount):
            self._threads[i].start()

    @pyqtSlot()
    def checkProxies(self):
        if self.proxiesModel.rowCount() == 0:
            return
        self.scrapeProxiesButton.setEnabled(False)
        self.checkProxiesButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.statusbar.showMessage("Checking proxies ...")
        self.resetTable()
        self.progressBar.setValue(0)
        # Get real ip address
        ok, ip, msg = get_real_ip()
        if not ok:
            QtWidgets.QMessageBox.warning("Error", msg)
            return
        self._realIP = ip
        self.realIPLabel.setText(" Real IP: {:<15} ".format(ip))
        queues = split_list(range(self.proxiesModel.rowCount()), self._threadsCount)
        self._progressTotal = self.proxiesModel.rowCount()
        self._progressDone = 0
        self._threads = []
        self._workers = []
        for i, rows in enumerate(queues):
            self._threads.append(MyThread())
            queue = Queue()
            for row in rows:
                ip, port = self.proxiesModelRow(row, ["ip", "port"])
                queue.put((row, Proxy(ip, int(port))))
            self._workers.append(
                CheckProxiesWorker(queue=queue, timeout=TIMEOUT, delay=DELAY, real_ip=ip)
            )
            self._workers[i].moveToThread(self._threads[i])
            self._threads[i].started.connect(self._workers[i].start)
            self._threads[i].finished.connect(self._threads[i].deleteLater)
            self._workers[i].status.connect(self.onStatus)
            self._workers[i].result.connect(self.onResult)
            self._workers[i].finished.connect(self._threads[i].quit)
            self._workers[i].finished.connect(self._workers[i].deleteLater)
            self._workers[i].finished.connect(self.onFinished)
        for i in range(self._threadsCount):
            self._threads[i].start()

    @pyqtSlot()
    def stop(self):
        self.scrapeProxiesButton.setEnabled(False)
        self.checkProxiesButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        self.statusbar.showMessage("Stopping threads ...")
        for i, _ in enumerate(self._workers):
            self._workers[i]._running = False


    @pyqtSlot(object)
    def onStatus(self, status):
        if status["action"] == "check":
            self.setProxiesModelCell(status["row"], "status", status["status"])

    @pyqtSlot(object)
    def onResult(self, result):
        if result["action"] == "check":
            model = self.proxiesModel
            data = result["data"]
            self.setProxiesModelCell(result["row"], "anon", data["anon"])
            self._progressDone += 1
            self.progressBar.setValue(int(float(self._progressDone) / self._progressTotal * 100))
        elif result["action"] == "scrape":
            for proxy in result["data"]:
                if str(proxy) in self._proxies:
                    continue
                self.proxiesModel.appendRow([
                    QStandardItem(proxy.ip),
                    QStandardItem(str(proxy.port)),
                    QStandardItem(""),
                    QStandardItem(""),
                    QStandardItem(""),
                    QStandardItem(""),
                    QStandardItem(""),
                    QStandardItem(""),
                ])
            self._progressDone += 1
            self.progressBar.setValue(int(float(self._progressDone) / self._progressTotal * 100))

    @pyqtSlot()
    def onFinished(self):
        self.statusbar.showMessage("Ready.")

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
