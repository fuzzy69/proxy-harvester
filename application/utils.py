# -*- coding: UTF-8 -*-
#!/usr/bin/env python

import re
from time import sleep

import json
import lxml.html
import requests

from application.conf import HEADERS
from application.defaults import TIMEOUT

MATCH_WHITESPACE = "\s+"
MATCH_PROXY = "((\d{1,3})(\.\d{1,3}){3})(?:\s)*(?::)?(\d{1,5})"

regex_whitespace = re.compile(MATCH_WHITESPACE)
regex_proxy = re.compile(MATCH_PROXY)

class HttpClient(object):
    """HttpClient"""
    def __init__(self, arg):
        super(HttpClient, self).__init__()
        self.arg = arg

def dummy(delay):
    print("dummy start")
    sleep(delay)
    print("dummy done")

def split_list(li, n):
    """
    Split list into n lists

    Parameters
    ----------
    li : list
        List to split

    n : int
        Split count

    Returns
    -------
    list
        List of n lists

    Examples
    --------
    >>> split_list([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 3)
    [[1, 2, 3, 4], [5, 6, 7], [8, 9, 10]]
    """
    k, m = divmod(len(li), n)

    return [li[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]

def scrape_proxies(url="http://free-proxy-list.net/"):
    ok = True
    result = set()
    message = None

    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            doc = lxml.html.fromstring(r.content)
            els = doc.xpath("//text()")
            text = ' '.join(els)
            text = re.sub(regex_whitespace, ' ', text)
            # print(text)
            matches = re.findall(regex_proxy, text)
            for match in matches:
                # TODO: validate proxy format
                result.add("{}:{}".format(match[0], match[-1]))
    # TODO: manage errors
    except Exception as e:
        message = str(e)

    return ok, result, message

urls = [
'http://httpbin.org/get', 'https://httpbin.org/get',
'http://httpbin.org/redirect/1', 'http://httpbin.org/status/404']

def check_proxie(proxy, real_ip, timeout=5):
    ok = False
    result = {}
    message = None
#     proxies = {
#         "http": "http://",
#         "https": "http://",
#         proxies = {
#     "http": "http://user:pass@10.10.1.10:3128/"
# }
# # ((?:\d{1,3})(?:\.\d{1,3}){3}(?:\s)*(?::)?(?:\d{1,5}))
#     }
#     # TODO:
#     # is alive
#     # get proxie type
#     # get proxie speed
    # is anonymous
    result["anon"] = check_anonymity(proxy,real_ip)
#     # get country
#     try:
#         response = requests.get(urls[0], timeout=timeout, headers=HEADERS, proxies=proxies)
#         resp = response.content
#         result = resp
#         print(resp)
#         result = response.status_code
#         ok = True
#     except (IOError, requests.exceptions.Timeout,) as e:
#         result = False
#         message = str(e)

    return ok, result, message

def get_real_ip():
    ok = True
    ip = None
    message = None

    try:
        r = requests.get("http://httpbin.org/get?show_env", headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            data = json.loads(r.text)
            ip = data["origin"]
    except Exception as e:
        message = str(e)

    return ok, ip, message

def check_anonymity(proxy, real_ip):
    result = None
    proxies = {
        "http": "http://{}/".format(proxy),
        "https": "https://{}/".format(proxy),
    }
    try:
        r = requests.get("http://httpbin.org/get?show_env", proxies=proxies, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            data = json.loads(r.text)
            origin = data["origin"]
            via = data["headers"]["Via"]
            if real_ip in origin:
                result = "Transparent"
            elif via:
                result = "Anonymous"
            else:
                result = "High"
    except Exception as e:
        pass

    return result
