# coding: utf-8

import os

from http.cookiejar import MozillaCookieJar


def set_headers(session, headers):
    for header in headers:
        try:
            header_name, header_value = header.split(':', 1)
        except ValueError:
            header_name, header_value = header, ''

        if not header_value:
            del session.headers[header]
        else:
            update = {header_name: header_value.lstrip()}
            session.headers.update(update)

def set_user_agent(session, user_agent):
    set_headers(session, ['User-Agent:' + user_agent])

def set_cookies(session, cookies):
    if '=' not in cookies and os.path.exists(cookies):
        cookiejar = MozillaCookieJar(cookies)
        cookiejar.load()
        session.cookies.update(cookiejar)
    else:
        for cookie in cookies.split(';'):
            try:
                name, value = cookie.split('=')
            except ValueError:
                print('Invalid cookie', cookie, file=sys.stderr)
            else:
                session.cookies.set(name.strip(), value.strip())

def save_cookie_jar(session, cookie_jar):
    cookies = MozillaCookieJar(cookie_jar)
    cookies.update(session.cookies)
    cookies.save()
