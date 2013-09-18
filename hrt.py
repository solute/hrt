# coding: utf-8

"""

HRT - HTTP Request Tree

Main File


Usage

1. Modify this file and config.py
2. Call "python hrt.py"
3. See the output .gif or .svg-file

"""

import sys, time

import server
import config
import client

url = sys.argv[1]

config.set("url", url)

s = server.start()

client.open_url(url, visible = config.get("visible"))

s.stop()
