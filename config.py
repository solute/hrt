# encoding: utf-8

CONFIG = {"phantomjs_bin": "./phantomjs-1.8.1-linux-i686/bin/phantomjs", # full path
          "firefox_bin": "/home/gb/bin/firefox/firefox", # full path or None
          "auth": None, # if you need authentication to the webpage
          "hrt_url": "http://localhost:8899/%s/__hrt__/?",
          "url_delimiter": "__hrt__",
          "server_port": 8899, # a free port, will be used by the proxy
          "dot_cmd": "dot", # add full path if necessary

          "url": None, # will be set in hrt.py
          "dot_file": "graph.dot", # temporary filename
          "out_file": "graph.gif",
          "out_format": "gif"} # "svg", "isvg"


def get(key):
    return CONFIG[key]


def set(key, value):
    CONFIG[key] = value


