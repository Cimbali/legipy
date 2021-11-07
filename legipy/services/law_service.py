# coding: utf-8

import six

from legipy.common import page_url
from legipy.parsers.law_parser import parse_law
from legipy.parsers.pending_law_list_parser import parse_pending_law_list
from legipy.parsers.published_law_list_parser import parse_published_law_list
from legipy.services import Singleton, Service


@six.add_metaclass(Singleton)
class LawService(Service):
    pub_url = page_url('liste/dossierslegislatifs/{legislature}/')
    law_url = page_url('dossierlegislatif/{id_legi}/')
    comm_url = None

    def pending_laws(self, legislature, government=True):
        url, soup = self.get(
            self.pub_url.format(legislature=legislature),
            params={'type': 'PROJET_LOI' if government else 'PROPOSITION_LOI'}
        )
        return parse_pending_law_list(url, soup, legislature=legislature)

    def published_laws(self, legislature):
        url, soup = self.get(
            self.pub_url.format(legislature=legislature),
            params={'type': 'LOI_PUBLIEE'}
        )
        return parse_published_law_list(url, soup, legislature=legislature)

    def common_laws(self):
        raise NotImplementedError('Common laws not updated to 2020 format')

    def get_law(self, id_legi):
        url, soup = self.get(
            self.law_url.format(id_legi=id_legi)
        )
        return parse_law(url, soup, id_legi)
