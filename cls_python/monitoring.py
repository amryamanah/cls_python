# -- coding: utf-8 --

__author__ = 'amryfitra'

import psutil
import requests
import urllib.parse

class ClsMonitor(object):
    def __init__(self):
        self.server_url = "http://localhost:8000"
        self.device_name = "WA-02"

    def build_url(self, api_path):
        scheme, netloc, path, query, fragment = urllib.parse.urlsplit(self.server_url)
        path = api_path
        return urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))


if __name__ == "__main__":
    a = ClsMonitor()
    b = a.build_url("device-properties")
    c = requests.get(b, auth=('admin', 'adminpass'))
    print(c.content)