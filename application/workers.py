# -*- coding: UTF-8 -*-
#!/usr/bin/env python

from time import sleep

from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal, QObject

from application.utils import check_proxie, scrape_proxies

class MyThread(QThread):
    activeCount = 0

    def __init__(self, parent=None):
        super(QThread, self).__init__()
        self.started.connect(self.increaseActiveThreads)
        self.finished.connect(self.decreaseActiveThreads)

    @pyqtSlot()
    def increaseActiveThreads(self):
        MyThread.activeCount += 1

    @pyqtSlot()
    def decreaseActiveThreads(self):
        MyThread.activeCount -= 1

class Worker(QObject):
    start = pyqtSignal()
    stop = pyqtSignal()
    finished = pyqtSignal()
    result = pyqtSignal(object)

    def __init__(self, func, *args, **kwargs):
        super(Worker, self).__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._running = True
        self.start.connect(self.run)
        self.stop.connect(self.onStop)

    @pyqtSlot()
    def run(self):
        result = self.doWork(*self._args, **self._kwargs)
        self.finished.emit()

    @pyqtSlot()
    def onStop(self):
        self._running = False

    def doWork(self, *args, **kwargs):
        raise NotImplementedError

class CheckProxiesWorker(Worker):
    status = pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(check_proxie, *args, **kwargs)

    def doWork(self, *args, **kwargs):
        queue = kwargs["queue"]
        timeout = kwargs["timeout"]
        delay = kwargs["delay"]
        real_ip = kwargs["real_ip"]
        while self._running and not queue.empty():
            row, ip, port = queue.get()
            self.status.emit({
                "action": "check",
                "row": row,
                "status": "Checking ...",
            })
            ok, result, message = self._func("{}:{}".format(ip, port), real_ip)
            self.result.emit({
                "action": "check",
                "row": row,
                "ok": ok,
                "data": result,
                "message": message,
            })
            self.status.emit({
                "action": "check",
                "row": row,
                "status": "Done",
            })
            # if queue.empty():
            #     self.finished.emit()
            sleep(delay)

class ScrapeProxiesWorker(Worker):
    status = pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(scrape_proxies, *args, **kwargs)

    def doWork(self, *args, **kwargs):
        queue = kwargs["queue"]
        timeout = kwargs["timeout"]
        delay = kwargs["delay"]
        while self._running and not queue.empty():
            url = queue.get()
            self.status.emit({
                "action": "scrape",
                "status": None,
            })
            ok, proxies, message = self._func(url)
            self.result.emit({
                "action": "scrape",
                "ok": ok,
                "data": proxies,
                "message": message,
            })
            self.status.emit({
                "action": "scrape",
                "status": None,
            })
            sleep(delay)
