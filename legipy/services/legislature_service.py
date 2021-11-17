# coding: utf-8

from legipy.common import page_url
from legipy.parsers.legislature_list_parser import parse_legislature_list
from legipy.services import Singleton, Service


class LegislatureService(Service, metaclass=Singleton):
    url = page_url('liste/legislatures')
    cache = None

    def legislatures(self):
        if self.cache is None:
            url, soup = self.get(self.url)
            self.cache = parse_legislature_list(url, soup)

        return self.cache

    def current_legislature(self):
        for leg in self.legislatures():
            if leg.end is None:
                return leg
        raise ValueError('No current legislature')
