#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import datetime
import json
import sys
import os

import click
import requests
import requests_cache


from legipy.models.base import LegipyModel
from legipy.services import Service
from legipy.services.code_service import CodeService
from legipy.services.code_service import SectionService
from legipy.services.law_service import LawService
from legipy.services.legislature_service import LegislatureService
from legipy.services.session import set_headers, set_user_agent, set_cookies, save_cookie_jar
from legipy.services.selenium import Browser, WebdriverAdapter


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, LegipyModel):
        return obj.to_json()
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError("Type {0} not serializable".format(repr(type(obj))))


def _dump_item(obj, error=None):
    if obj:
        print(json.dumps(obj, sort_keys=True, indent=2, default=json_serial))
    elif error:
        sys.stderr.write('ERROR: %s\n' % error)
        exit(1)


def _dump_items(ary):
    print(
        json.dumps(
            [i for i in ary],
            sort_keys=True,
            indent=2,
            default=json_serial
        )
    )


@click.group(short_help=u"Client for the `legifrance.gouv.fr` website.")
@click.option('--cache/--no-cache', default=False,
              help='Cache requests locally')
@click.option('-H', '--header', 'headers', multiple=True, type=str,
              help='HTTP Header, option can be passed multiple times')
@click.option('-b', '--cookie', 'cookies', type=str,
              help='Cookies as "NAME1=VALUE1; NAME2=VALUE2", or filename')
@click.option('-c', '--cookie-jar', help='Save cookies in Netscape format',
              type=click.Path(dir_okay=False, writable=True, allow_dash=True))
@click.option('-A', '--user-agent', type=str, help='Specify user agent')
@click.option('-s', '--session', is_flag=True, help='Use requests.sessions')
@click.option('-w/-W', '--webdriver/--no-webdriver', default=Browser.check_running(),
              help='Use selenium webdriver')
@click.help_option('-h')
@click.pass_context
def cli(context, cache, headers, cookies, user_agent, cookie_jar, session, webdriver):
    if 'daemon' in context.invoked_subcommand.split('-'):
        return

    if cache:
        requests_cache.install_cache('legipy_cache')

    session = requests.Session()
    if webdriver:
        session.mount('https://www.legifrance.gouv.fr/', WebdriverAdapter())
    if headers:
        set_headers(session, headers)
    if user_agent is not None:
        set_user_agent(session, user_agent)
    if cookie_jar is not None:
        atexit.register(save_cookie_jar, session, cookie_jar)
    if cookies is not None:
        set_cookies(session, cookies)
    Service.session = session


@cli.command()
def start_daemon():
    if Browser.check_running():
        Browser.stop_running()
    # Create a webdriver, fork and kill the parent, wait for commands
    browser = Browser()
    if os.fork():
        os._exit(0)
    browser.to_background()


@cli.command()
def stop_daemon():
    Browser.stop_running()


@cli.command(short_help=u"List published laws")
@click.option('--legislature', default=None, help='Legislature number')
def published_laws(legislature):
    if legislature is None:
        legislature = LegislatureService().current_legislature()
    _dump_items(LawService().published_laws(legislature))


@cli.command(short_help=u"List pending law projects")
@click.option('--legislature', default=None, help='Legislature number')
def law_projects(legislature):
    if legislature is None:
        legislature = LegislatureService().current_legislature()
    _dump_items(LawService().pending_laws(legislature, True))


@cli.command(short_help=u"List pending law proposals")
@click.option('--legislature', default=None, help='Legislature number')
def law_proposals(legislature):
    if legislature is None:
        legislature = LegislatureService().current_legislature()
    _dump_items(LawService().pending_laws(legislature, False))


@cli.command(short_help=u"List common laws (« lois dites »)")
def common_laws():
    _dump_items(LawService().common_laws())


@cli.command(short_help=u"Show specific law")
@click.argument('legi_id')
def law(legi_id):
    _dump_item(
        LawService().get_law(legi_id),
        error='No such law: %s' % legi_id
    )


@cli.command(short_help=u"List legislatures")
def legislatures():
    _dump_items(LegislatureService().legislatures())


@cli.command(short_help=u"List applicable codes")
def codes():
    _dump_items(CodeService().codes())


@cli.command(short_help=u"Show code details")
@click.argument('id-code')
@click.option('--date-pub',
              help=u"Publication date (ISO format), default to today")
@click.option('--with-articles/--without-articles', default=False,
              help=u"Show details for each articles")
def code(id_code, date_pub, with_articles):
    _dump_item(
        CodeService().code(id_code, date_pub, with_articles),
        error='No such code: %s' % id_code
    )


@cli.command(short_help=u"Show code section detail")
@click.argument('id-code')
@click.argument('id-section')
@click.option('--date-pub',
              help=u"Publication date (ISO format), default to today")
def code_section(id_code, id_section, date_pub):
    _dump_item(SectionService().articles(id_code, id_section, date_pub))


if __name__ == '__main__':
    cli()
