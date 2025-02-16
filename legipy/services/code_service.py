import datetime

from legipy.common import page_url
from legipy.parsers.code_parser import CodeParser
from legipy.parsers.code_parser import parser_articles
from legipy.services import Singleton, Service


class CodeService(Service, metaclass=Singleton):
    code_list_url = page_url('liste/code')
    code_url = page_url('codes/texte_lc/{id_code}/{date}/')

    def codes(self):
        # https://www.legifrance.gouv.fr/liste/code?etatTexte=VIGUEUR
        # NB: valeurs etatTexte cumulables: VIGUEUR, VIGUEUR_DIFF, ABROGE
        url, soup = self.get(
            self.code_list_url,
        )
        return CodeParser.parse_code_list(url, soup)

    def code(self, id_code, date_pub, with_articles):
        # https://www.legifrance.gouv.fr/codes/texte_lc/LEGITEXT000006075116/2021-04-28/
        date_pub = date_pub or datetime.date.today().strftime('%Y-%m-%d')
        url, soup = self.get(
            self.code_url.format(id_code=id_code, date=date_pub),
        )
        parser = CodeParser(id_code, date_pub, with_articles=with_articles)
        return parser.parse_code(url, soup)


class SectionService(Service, metaclass=Singleton):
    section_url = page_url('codes/section_lc/{id_code}/{id_section}/{date}/')

    def articles(self, id_code, id_section, date_pub):
        # https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006071190/LEGISCTA000006151283/2021-04-28/
        date_pub = date_pub or datetime.date.today().strftime('%Y-%m-%d')
        url, soup = self.get(
            self.section_url.format(id_code=id_code, id_section=id_section,
                                    date=date_pub)
        )
        return parser_articles(url, soup)
