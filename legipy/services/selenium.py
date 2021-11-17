# coding: utf-8

import os
import io
import sys
import six
import json
import errno
import signal
import atexit
import urllib3
import requests
import threading
import http.cookiejar
import collections.abc

from legipy.services import Singleton

from selenium import webdriver
from selenium.webdriver.remote.command import Command


class RemoteDaemon(webdriver.Remote):
    def __init__(self, session_data, **kwargs):
        self.session_data = session_data
        super(RemoteDaemon, self).__init__(command_executor=self.session_data['url'], **kwargs)

    def start_session(self, *args, **kwargs):
        if self.session_data is not None:
            self.session_id = self.session_data['session_id']
            self.w3c = self.command_executor.w3c = self.session_data['w3c']
            self.capabilities = self.session_data['capabilities']
        else:
            super(RemoteDaemon, self).start_session(*args, **kwargs)

    def quit(self):
        pass

    def real_quit(self):
        super(RemoteDaemon, self).quit()


class Browser(object):
    """ Class wrapping and handling the lifetime of a WebDriver """
    browser_map = {
        'firefox': webdriver.Firefox,
        'chrome': webdriver.Chrome,
    }

    options_map = {
        'firefox': webdriver.firefox.options.Options,
        'chrome': webdriver.chrome.options.Options,
    }

    path = f'/run/user/{os.getuid()}/selenium.json'

    def __init__(self, driver_name='firefox'):
        """ Main function: starts the selenium driver, gets the element, and saves the screenshot.
        """
        session_data = None
        if os.path.exists(self.path):
            with open(self.path) as f:
                session_data = json.load(f)

        try:
            if session_data:
                driver = RemoteDaemon(session_data)
                webdriver.Remote.execute(driver, Command.W3C_GET_CURRENT_WINDOW_HANDLE)
                self.driver = driver
        except Exception as err:
            print('Failed accessing daemon', err, file=sys.stderr)
            os.unlink(self.path)
        except urllib3.exceptions.MaxRetryError:
            os.unlink(self.path)

        if not hasattr(self, 'driver'):
            self.driver = self.browser_map[driver_name]()
            atexit.register(self.driver.quit)


    def to_background(self):
        with open(self.path, 'w') as f:
            json.dump({
                'pid': os.getpid(),
                'url': self.driver.command_executor._url, 'session_id': self.driver.session_id,
                'capabilities': self.driver.desired_capabilities, 'w3c': self.driver.w3c,
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
    def __init__(self):
        super(WebdriverAdapter, self).__init__()
        self.browser = Browser()
        self.driver = self.browser.driver

    def close(self):
        pass

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        """ Sends PreparedRequest object. Returns Response object.

        Args:
            request (:class:`PreparedRequest <PreparedRequest>`): the request being sent.
            stream (bool): (optional) Whether to stream the request content.
            timeout (float or tuple): (optional) How long to wait for the server to send
                                      data before giving up, as a float, or a :ref:`(connect timeout,
                                      read timeout) <timeouts>` tuple.
            verify (bool): (optional) Either a boolean, in which case it controls whether we verify
                           the server's TLS certificate, or a string, in which case it must be a path
                           to a CA bundle to use
            cert: (optional) Any user-provided SSL certificate to be trusted.
            proxies: (optional) The proxies dictionary to apply to the request.
        """
        if request.method.upper() != 'GET':
            raise ValueError('WebdriverAdapter adapter only supports get requests')

        if timeout:
            timeout = sum(timeout) if isinstance(timeout, collections.abc.Iterable) else timeout
            self.driver.set_page_load_timeout(timeout)

        self.driver.get(request.url)
        response = requests.models.Response()
        response.request = request
        response.url = self.driver.current_url

        # Things we can’t have :( unless we use a proxy which may gets us detected or some logging-like add-on
        response.status_code = None
        response.reason = None

        # Miraculously cookies are available
        jar = requests.cookies.RequestsCookieJar()
        for cookie in self.driver.get_cookies():
            jar.set_cookie(self.to_cookielib_cookie(cookie))
        response.cookies = jar

        # Set data with default encoding as 'raw'
        response.encoding = 'utf-8'
        response.raw = io.BytesIO(self.driver.page_source.encode(response.encoding))

        return response


    @staticmethod
    def to_cookielib_cookie(selenium_cookie):
        """ https://gist.github.com/tubaman/ab4fdc3e0104a0f54046 """
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
