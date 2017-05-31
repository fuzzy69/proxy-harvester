# -*- coding: UTF-8 -*-
#!/usr/bin/env python

import ipaddress


class IPAddress(object):

    def __init__(self, ip):
        self._ip = ip

    @staticmethod
    def validate(ip):
        try:
            ipaddress.IPv4Address(ip)
        except ipaddress.AddressValueError:
            return False
        else:
            return True

    @staticmethod
    def geo_info(ip):
        pass

    @staticmethod
    def external_ip(ip):
        pass

class ProxyError(Exception):
    pass

class Proxy(object):

    def __init__(self, ip, port, username=None, password=None, timeout=10, ssl=False):
        Proxy.validate(ip, port)
        self._ip = ip
        self._port = port
        self._username = username
        self._password = password
        self._is_alive = False

    def __repr__(self):
        return "<Proxie {}:{}>".format(self.ip, self.port)

    def __str__(self):
        return "{}:{}".format(self.ip, self.port)

    def __eq__(self, other):
        return self.ip == other.ip and self.port == other.port

    def __hash__(self):
        return hash((self.ip, self.port))

    @classmethod
    def validate(cls, ip, port):
        if not IPAddress.validate(ip):
            raise ValueError("Invalid ip address format")
        if type(port) is not int:
            raise ValueError("Invalid port value type, int required")
        if not (0 <= port <= 65535):
            raise ValueError("Invalid port number")

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    @property
    def is_alive(self):
        return self._is_alive

    @is_alive.setter
    def is_alive(self, value):
        self._is_alive = value
