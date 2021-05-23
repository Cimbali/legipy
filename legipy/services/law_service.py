# coding: utf-8

import six

from legipy.common import page_url
from legipy.parsers.law_parser import parse_law
from legipy.parsers.pending_law_list_parser import parse_pending_law_list
from legipy.parsers.published_law_list_parser import parse_published_law_list
from legipy.services.session import SessionService
from legipy.services import Singleton


@six.add_metaclass(Singleton)
class LawService(SessionService):
    pub_url = page_url('liste/dossierslegislatifs/{legislature}/')
    law_url = page_url('dossierlegislatif/{id_legi}/')
    comm_url = None

    def pending_laws(self, legislature, government=True):
        response = self.get(
            self.pub_url.format(legislature=legislature),
            params={'type': 'PROJET_LOI' if government else 'PROPOSITION_LOI'}
        )
        return parse_pending_law_list(response.url, response.content,
                                      legislature=legislature)

    def published_laws(self, legislature):
        response = self.get(
            self.pub_url.format(legislature=legislature),
            params={'type': 'LOI_PUBLIEE'}
        )
        return parse_published_law_list(response.url, response.content,
                                        legislature=legislature)

    def common_laws(self):
        raise NotImplementedError('Common laws not updated to 2020 format')

    def get_law(self, id_legi):
        response = self.get(
            self.law_url.format(id_legi=id_legi)
        )
        return parse_law(response.url, response.content, id_legi)
