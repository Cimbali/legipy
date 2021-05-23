# coding: utf-8

import os
import six
import atexit
import requests

from six.moves.http_cookiejar import MozillaCookieJar
from legipy.services import Singleton


@six.add_metaclass(Singleton)
class Session(object):
    unique_session = None

    def __init__(self, *args, **kwargs):
        if self.unique_session is None:
            self.unique_session = requests.Session()

    def __getattr__(self, item):
        return getattr(self.unique_session, item)

    def set_headers(self, headers):
        for header in headers:
            try:
                header_name, header_value = header.split(':', 1)
            except ValueError:
                header_name, header_value = header, ''

            if not header_value:
                del self.unique_session.headers[header]
            else:
                update = {header_name: header_value.lstrip()}
                self.unique_session.headers.update(update)

    def set_user_agent(self, user_agent):
        self.set_headers(['User-Agent:' + user_agent])

    def set_cookies(self, cookies):
        if '=' not in cookies and os.path.exists(cookies):
            self.cookies = MozillaCookieJar(cookies)
            self.cookies.load()
        else:
            for cookie in cookies.split(';'):
                try:
                    name, value = cookie.split('=')
                except ValueError:
                    print('Invalid cookie', cookie, file=sys.stderr)
                else:
                    self.cookies.set(name.strip(), value.strip())

    def save_cookie_jar(self, cookie_jar):
        self.cookies = MozillaCookieJar(cookie_jar)
        atexit.register(self.cookies.save)
