# coding: utf-8

import base64
import subprocess
import webbrowser

import config, time

try:
    from selenium import webdriver
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.keys import Keys
except:
    pass # No Selenium? No Problem...

def open_url(url, visible = False):
    """ if visible = True, use firefox/selenium, else use phantomJS """

    origin_string = base64.b64encode(url)
    url = (config.get("hrt_url") % origin_string) + url

    if visible:

        ffbin_path = config.get("firefox_bin")
        if ffbin_path:
            ffbin = webdriver.firefox.firefox_binary.FirefoxBinary(ffbin_path)
        else:
            ffbin = None

        browser = webdriver.Firefox(firefox_binary = ffbin) # Get local session of firefox

        if config.get("auth"):
            auth_header = base64.b64encode(config.get("auth")[0] + ":" + config.get("auth")[1])

        browser.get(url)
        time.sleep(5)
        browser.close()
    else:
        subprocess.call([config.get("phantomjs_bin"),
                         "open_url.js",
                         url])

