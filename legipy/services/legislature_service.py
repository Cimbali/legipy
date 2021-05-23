# coding: utf-8

import requests
import six

from legipy.common import page_url
from legipy.parsers.legislature_list_parser import parse_legislature_list
from legipy.services import Singleton


@six.add_metaclass(Singleton)
class LegislatureService(object):
    url = page_url('liste/legislatures')
    cache = None

    def legislatures(self):
        if self.cache is None:
            response = requests.get(self.url)
            self.cache = parse_legislature_list(response.url, response.content)

        return self.cache

    def current_legislature(self):
        for leg in self.legislatures():
            if leg.end is None:
                return leg
        raise ValueError('No current legislature')
