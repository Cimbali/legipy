# coding: utf-8

import requests
import six

from legipy.common import page_url
from legipy.parsers.legislature_list_parser import parse_legislature_list
from legipy.services import Singleton, Service


@six.add_metaclass(Singleton)
class LegislatureService(Service):
    url = page_url('liste/legislatures')
    cache = None

    def legislatures(self):
        if self.cache is None:
            response = self.get(self.url)
            print(response.url, response.status_code, response.history)
            print(response.request.headers)
            print(response.headers)
            print(response.cookies)
            print(response.text)
            self.cache = parse_legislature_list(response.url, response.content)

        return self.cache

    def current_legislature(self):
        for leg in self.legislatures():
            if leg.end is None:
                return leg
        raise ValueError('No current legislature')
