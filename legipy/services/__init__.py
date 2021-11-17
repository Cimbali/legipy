# coding: utf-8

import sys
import requests
import requests_cache
from bs4 import BeautifulSoup

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = (super(Singleton, cls)
                                   .__call__(*args, **kwargs))
        return cls._instances[cls]


class Service(object):
    session = requests.Session()
    domain = 'https://www.legifrance.gouv.fr/'
    retries = 10

    @classmethod
    def add_cache(cls, *args, **kwargs):
        adapter = cls.session.adapters.get(cls.domain)
        # WebdriverAdapter sets None as HTTP Code
        cls.session = requests_cache.CachedSession(*args, **kwargs, allowable_codes=(200, None,))
        if adapter:
            cls.set_adapter(adapter)

    @classmethod
    def set_adapter(cls, adapter):
        cls.session.mount(cls.domain, adapter)

    def get(self, url, *args, **kwargs):
        for _ in range(self.retries):
            response = Service.session.get(url, *args, **kwargs)
            soup = BeautifulSoup(response.content, 'html5lib', from_encoding='utf-8')
            # If error or valid contents, return the resposne
            if response.status_code != 200 or len(soup.body.contents) > 1:
                print(Service.session.cache.urls, file=sys.stderr)
                return response.url, soup

            if hasattr(Service.session, 'cache'):
                key = Service.session.cache.create_key(response.request)
                Service.session.cache.delete(key)

            err = 'Request unsuccessful.'
            if len(soup.body.contents) == 1:
                err = f'{err[:-1]}: "{soup.body.contents[0].string.replace(f"{err} ", "").strip()}"'
            print(err, file=sys.stderr)
            print(f'Try opening the page and filling any captchas: {url}', file=sys.stderr)
            input()

        raise ValueError(f'Too many tries for {url}')
