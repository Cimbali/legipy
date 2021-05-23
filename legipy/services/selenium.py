# coding: utf-8

import os
import six
import atexit
import requests

from six.moves.http_cookiejar import MozillaCookieJar
from legipy.services import Singleton


import seleniumrequests
from selenium import webdriver


@six.add_metaclass(Singleton)
class Browser(object):
    browser_map = {
        'firefox': seleniumrequests.Firefox,
        'chrome': seleniumrequests.Chrome,
        'ie': seleniumrequests.Ie,
        'opera': seleniumrequests.Opera,
        'safari': seleniumrequests.Safari,
    }

    options_map = {
        'firefox': webdriver.firefox.options.Options,
        'chome': webdriver.chrome.options.Options,
    }

    def __init__(self, driver_name='firefox'):
        """ Main function: starts the selenium driver, gets the element, and saves the screenshot.
        """
        if driver_name in self.options_map:
            # browsers that support setting headless
            opts = self.options_map[driver_name]()
            opts.headless = True
        else:
            opts = None

        self.driver = self.browser_map[driver_name](options=opts)
        atexit.register(self.driver.quit)


    def get(self, *args, **kwargs):
        return self.driver.request('GET', *args, **kwargs)
