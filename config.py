# encoding: utf-8

import time

CONFIG = {"phantomjs_bin": "./phantomjs-1.8.1-linux-i686/bin/phantomjs", # full path
          "firefox_bin": "/home/gb/bin/firefox/firefox", # full path or None
          "visible": False, # True = use firefox, False = use phantomjs
          "auth": None, # if you need authentication to the webpage
          "hrt_url": "http://localhost:8899/%s/__hrt__/?",
          "url_delimiter": "__hrt__",
          "server_port": 8899, # a free port, will be used by the proxy
          "dot_cmd": "dot", # add full path if necessary

          "url": None, # will be set in hrt.py
          "dot_file": "graph.dot", # temporary filename
          "out_file": "graph_%Y-%m-%d_%H-%M-%S.%E",
          "out_format": "gif"} # "gif", "svg", "isvg", "json"



def handle_fn_template(fn):

  fn = fn.replace("%E", get("out_format"))

  fn = time.strftime(fn) # use strftime-format-template

  return fn


def get(key):
    value = CONFIG[key]

    if key == "out_file":
      value = handle_fn_template(value)

    return value


def set(key, value):
    CONFIG[key] = value


