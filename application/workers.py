# -*- coding: UTF-8 -*-
#!/usr/bin/env python

from PyQt5.QtCore import QThread, QMutex, pyqtSlot, pyqtSignal, QObject

class Worker(QObject):
    """Worker"""
    start = pyqtSignal()
    finished = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super(Worker, self).__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self.start.connect(self.run)

    @pyqtSlot()
    def run(self):
        raise NotImplementedError