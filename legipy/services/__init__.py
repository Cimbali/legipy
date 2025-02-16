# coding: utf-8

import sys
import appdirs
import requests
import requests_cache
from bs4 import BeautifulSoup
from pathlib import Path


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
    def add_cache(cls, **kwargs):
        adapter = cls.session.adapters.get(cls.domain)
        # WebdriverAdapter sets None as HTTP Code
        if kwargs.get('backend', 'sqlite') == 'sqlite':
            path = Path(appdirs.user_cache_dir('legipy', 'regardscitoyens'))
            if not path.exists():
                path.mkdir(parents=True)
            cache = str(path / 'requests_cache.sqlite')
        else:
            cache = 'legipy_requests'

        kwargs.update(dict(cache_name=cache, allowable_codes=(200, None,)))
        cls.session = requests_cache.CachedSession(**kwargs)
        if adapter:
            cls.set_adapter(adapter)

    @classmethod
    def set_adapter(cls, adapter):
        cls.session.mount(cls.domain, adapter)

    def get(self, url, *args, **kwargs):
        for _ in range(self.retries):
            response = Service.session.get(url, *args, **kwargs)
            soup = BeautifulSoup(response.content, 'html5lib',
                                 from_encoding='utf-8')
            # If error or valid contents, return the resposne
            if response.status_code != 200 or len(soup.body.contents) > 1:
                return response.url, soup

            if hasattr(Service.session, 'cache'):
                key = Service.session.cache.create_key(response.request)
                Service.session.cache.delete(key)

            err = 'Request unsuccessful.'
            if len(soup.body.contents) == 1:
                msg = soup.body.contents[0].string.replace(f"{err} ", "")
                err = f'{err[:-1]}: "{msg.strip()}"'
            print(err, file=sys.stderr)
            print(f'Try opening the page and filling any captchas: {url}',
                  file=sys.stderr)
            input()

        raise ValueError(f'Too many tries for {url}')
