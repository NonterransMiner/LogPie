# encoding=utf-8

"""
This is the LogPie.reader.pattern.systemd module.
This module DOSE NOT PROVIDE SERIOUS TOOLS to build a systemd's log reader,
instant, this more likely a MODULE TO TEST THE READER.
"""

import datetime
import multiprocessing
import re

from .common import ParserStatus, GeneralDirective
from .common import gen_pattern_parser, make_router

DEFAULT_PATTERN = r''

# ############### Functions to complete the pattern reader ################

ROUTER = {}


def read(c: str, status: ParserStatus,
         named=True, lang=None):
    if c == '%':
        return status.pop_string(), read_present
    else:
        status.push_char(re.escape(c))
        return None, read


def read_present(c: str, status: ParserStatus,
                 named=True, lang=None):
    if c in ROUTER:
        cls = ROUTER[c]
        regexp = cls.regexp(None, None, named=named, lang=lang)
        triad = (cls.KEY, cls, cls.additional_info(None, None))
        return (regexp, triad), read


def clean(status: ParserStatus,
          named=True, lang=None):
    if status.string_buffer:
        return status.pop_string(), None
    else:
        return None, None


# ############### Classes to handle the directives ################

class SystemdDate(GeneralDirective):
    DIRECTIVE = 'd'
    NEED_BUILD = True
    KEY = 'datetime'
    MON_NAMES = {'Jan': 1, 'Feb': 2, 'Mar': 3, "Apr": 4, 'May': 5, 'Jun': 6,
                 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

    @classmethod
    def gen_regexp(cls, prefix: str, suffix: str, named=False,
                   lang=None) -> str:
        return r'[A-Za-z]{3} \d{2} \d{2}:\d{2}:\d{2}'

    @classmethod
    def additional_info(cls, prefix: str, suffix: str):
        return '%b %d %H:%M:%S',

    @classmethod
    def build(cls, segment: str, format_str: str) -> datetime.datetime:
        mon, day, c = segment.split()
        mon = cls.MON_NAMES[mon]
        hour, minutes, s = c.split(':')
        return datetime.datetime(2014, mon, int(day),
                                 int(hour), int(minutes), int(s))


class SystemdHostname(GeneralDirective):
    DIRECTIVE = 'h'
    NEED_BUILD = False
    KEY = 'hostname'

    @classmethod
    def gen_regexp(cls, prefix: str, suffix: str, named=False,
                   lang=None) -> str:
        return r'\w+'


class SystemdSource(GeneralDirective):
    DIRECTIVE = 's'
    NEED_BUILD = True
    KEY = 'source'

    @classmethod
    def gen_regexp(cls, prefix: str, suffix: str, named=False,
                   lang=None) -> str:
        return r'[\.\-\w\[\]]+'

    @classmethod
    def build(cls, segment: str, *args) -> {'pname': str, 'pid': int}:
        sep_index = segment.rfind('[')
        pname = segment[:sep_index]
        if sep_index == -1:
            return {'pname': segment, 'pid': -1}
        else:
            return {'pname': pname, 'pid': int(segment[sep_index + 1:-1])}


class SystemdMessage(GeneralDirective):
    DIRECTIVE = 'm'
    NEED_BUILD = False
    KEY = 'message'

    @classmethod
    def gen_regexp(cls, prefix: str, suffix: str, named=False,
                   lang=None) -> str:
        return r'.*'


# ############### MAKE ROUTER ################


make_router(__name__, ROUTER)
# ############## MAKE PARSER ################

parser = gen_pattern_parser(read, clean)
test_parser = gen_pattern_parser(read, clean, regexp_only=True)
