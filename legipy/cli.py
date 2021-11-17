#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import datetime
import json
import sys
import os

import click

from legipy.models.base import LegipyModel
from legipy.services import Service
from legipy.services.code_service import CodeService
from legipy.services.code_service import SectionService
from legipy.services.law_service import LawService
from legipy.services.legislature_service import LegislatureService
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
@click.option('-c/-C', '--cache/--no-cache', default=True,
              help='Cache requests locally')
@click.option('-w/-W', '--webdriver/--no-webdriver', default=Browser.check_running(),
              help='Use selenium webdriver')
@click.help_option('-h')
@click.pass_context
def cli(context, cache, webdriver):
    if 'daemon' in context.invoked_subcommand.split('-'):
        return

    if cache:
        Service.add_cache('legipy_cache')

    if webdriver:
        # How should we allow options such as chrome or headless?
        Service.set_adapter(WebdriverAdapter())


@cli.command()
def start_daemon():
    if Browser.check_running():
        Browser.stop_running()
    browser = Browser()
    if os.fork():
        os._exit(0)
    browser.background()


@cli.command()
def stop_daemon():
    Browser.stop_running()


@cli.command()
def daemon():
    if Browser.check_running():
        Browser.stop_running()
    Browser().background()


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
