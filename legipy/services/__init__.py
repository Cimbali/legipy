# coding: utf-8

import sys
import requests
from bs4 import BeautifulSoup

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = (super(Singleton, cls)
                                   .__call__(*args, **kwargs))
        return cls._instances[cls]


class Service(object):
    backend = requests
    retries = 10
    def get(self, *args, **kwargs):
        for _ in range(self.retries):
            response = self.backend.get(*args, **kwargs)
            soup = BeautifulSoup(response.content, 'html5lib', from_encoding='utf-8')
            # If error or valid contents, return the resposne
            if response.status_code != 200 or len(soup.body.contents) > 1:
                return response.url, soup

            err = 'Request unsuccessful.'
            if len(soup.body.contents) == 1:
                err = f'{err[:-1]}: "{soup.body.contents[0].string.replace(f"{err} ", "").strip()}"'
            print(err, file=sys.stderr)
            print(f'Try opening the page and filling any captchas: {response.url}', file=sys.stderr)
            input()

        raise ValueError
