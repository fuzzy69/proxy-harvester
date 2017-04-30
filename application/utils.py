# -*- coding: UTF-8 -*-
#!/usr/bin/env python

from time import sleep

import requests

class HttpClient(object):
    """HttpClient"""
    def __init__(self, arg):
        super(HttpClient, self).__init__()
        self.arg = arg

def dummy(delay):
    print("dummy start")
    sleep(delay)
    print("dummy done")