# coding: utf-8

import os
import io
import sys
import json
import errno
import signal
import atexit
import appdirs
import urllib3
import requests
import threading
import http.cookiejar
from collections.abc import Iterable
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.remote.command import Command


class RemoteDaemon(webdriver.Remote):
    """ Communicate with a running instance of a browser

    Useful to reduce browser startup & shutdown overheads, to fill in captchas,
    and to persist sessions. Requires bypassing session start and stop
    """
    def __init__(self, session_data, **kwargs):
        self.session_data = session_data
        kwargs['command_executor'] = session_data['url']
        super(RemoteDaemon, self).__init__(**kwargs)

    def start_session(self, *args, **kwargs):
        self.session_id = self.session_data['session_id']
        self.w3c = self.command_executor.w3c = self.session_data['w3c']
        self.capabilities = self.session_data['capabilities']

    def quit(self):
        pass


class Browser(object):
    """ Class wrapping and handling the lifetime of a WebDriver """
    browser_map = {driver.lower(): getattr(webdriver, driver) for driver in [
        'Chrome', 'Edge', 'Firefox', 'Ie', 'Opera', 'Safari', 'WebKitGTK',
        'Android', 'BlackBerry', 'PhantomJS',
    ]}

    path = Path(appdirs.user_cache_dir('legipy', 'regardscitoyens')) \
        / 'selenium.json'

    def __init__(self, driver_name='firefox'):
        session_data = None
        if os.path.exists(self.path):
            with open(self.path) as f:
                session_data = json.load(f)

        try:
            if session_data:
                driver = RemoteDaemon(session_data)
                webdriver.Remote.execute(driver,
                                         Command.W3C_GET_CURRENT_WINDOW_HANDLE)
                self.driver = driver
        except Exception as err:
            print('Failed accessing daemon', err, file=sys.stderr)
            os.unlink(self.path)
        except urllib3.exceptions.MaxRetryError:
            os.unlink(self.path)

        if not hasattr(self, 'driver'):
            self.driver = self.browser_map[driver_name]()
            atexit.register(self.driver.quit)

    def background(self):
        """ Background work: save infos for remote to file, wait & clean up """
        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True)

        with open(self.path, 'w') as f:
            json.dump({
                'pid': os.getpid(),
                'url': self.driver.command_executor._url,
                'session_id': self.driver.session_id,
                'capabilities': self.driver.desired_capabilities,
                'w3c': self.driver.w3c,
            }, f)

        exit = threading.Event()
        for sig in [signal.SIGTERM, signal.SIGHUP, signal.SIGINT]:
            signal.signal(sig, lambda *args: exit.set())

        while not exit.is_set():
            exit.wait(60)

        os.unlink(self.path)

    @classmethod
    def signal_daemon(cls, sig):
        try:
            with open(cls.path, 'r') as f:
                pid = json.load(f)['pid']
            if pid <= 0:
                raise ValueError(f'Invalid pid {pid}')
            os.kill(pid, sig)
            return True
        except FileNotFoundError:
            pass
        except (KeyError, ValueError):
            os.unlink(cls.path)
        except OSError as err:
            # Possible error with valid pid
            if err.errno == errno.EPERM:
                return True
            os.unlink(cls.path)
        return False

    @classmethod
    def stop_running(cls):
        cls.signal_daemon(signal.SIGINT)

    @classmethod
    def check_running(cls):
        return cls.signal_daemon(0)


class WebdriverAdapter(requests.adapters.BaseAdapter):
    """ Send get requests via the Browser’s """
    def __init__(self, *args, **kwargs):
        super(WebdriverAdapter, self).__init__()
        self.browser = Browser(*args, **kwargs)
        self.driver = self.browser.driver

    def close(self):
        pass

    def send(self, request, timeout=None, **kwargs):
        """ Sends a PreparedRequest via the webdriver. Returns Response object.

        Only takes into account the request URL and timeout.
        Only handles GET requests.  """
        if request.method.upper() != 'GET':
            raise ValueError('WebdriverAdapter only supports get requests')

        if timeout and isinstance(timeout, Iterable):
            timeout = sum(timeout)
        if timeout:
            self.driver.set_page_load_timeout(timeout)

        self.driver.get(request.url)
        response = requests.models.Response()
        response.request = request
        response.url = self.driver.current_url

        # Things we can’t have :(
        response.status_code = None
        response.reason = None

        # Miraculously cookies are available
        jar = requests.cookies.RequestsCookieJar()
        for cookie in self.driver.get_cookies():
            jar.set_cookie(self.to_cookielib_cookie(cookie))
        response.cookies = jar

        # Set data with default encoding as 'raw'
        response.encoding = 'utf-8'
        page_bytes = self.driver.page_source.encode(response.encoding)
        response.raw = io.BytesIO(page_bytes)

        return response

    @staticmethod
    def to_cookielib_cookie(selenium_cookie):
        """ Convert a selenium cookie to a http.cookiejar cookie

        From https://gist.github.com/tubaman/ab4fdc3e0104a0f54046 """
        return http.cookiejar.Cookie(
            version=0,
            name=selenium_cookie['name'],
            value=selenium_cookie['value'],
            port='80',
            port_specified=False,
            domain=selenium_cookie['domain'],
            domain_specified=True,
            domain_initial_dot=False,
            path=selenium_cookie['path'],
            path_specified=True,
            secure=selenium_cookie['secure'],
            expires=selenium_cookie.get('expiry'),
            discard=False,
            comment=None,
            comment_url=None,
            rest=None,
            rfc2109=False
        )
