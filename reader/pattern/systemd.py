# encoding=utf-8

"""
This is the LogPie.reader.pattern.systemd module.
This module DOSE NOT PROVIDE SERIOUS TOOLS to build a systemd's log reader,
instant, this more likely a MODULE TO TEST THE READER.
"""

import datetime
import re

from .common import ParserStatus, GeneralDirective
from .common import gen_pattern_parser, make_router

DEFAULT_PATTERN = r''

# ############### Functions to complete the pattern reader ################

ROUTER = {}


def read(c: str, status: ParserStatus):
    if c == '%':
        return status.pop_string(), read_present
    else:
        status.push_char(re.escape(c))
        return None, read


def read_present(c: str, status: ParserStatus):
    if c in ROUTER:
        cls = ROUTER[c]
        regexp = cls.regexp(None, None)
        triad = (cls.KEY, cls, cls.additional_info(None, None))
        return (regexp, triad), read


def clean(status: ParserStatus) -> str:
    if status.string_buffer:
        return status.pop_string()


# ############### Classes to handle the directives ################

class SystemdDate(GeneralDirective):
    DIRECTIVE = 'd'
    NEED_BUILD = True
    KEY = 'datetime'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        # return r'([Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec] \d{2} \d{2}:\d{2}:\d{2})'
        return r'([A-Za-z]{3} \d{2} \d{2}:\d{2}:\d{2})'

    @classmethod
    def additional_info(cls, prefix: str, suffix: str):
        return '%b %d %H:%M:%S',

    @classmethod
    def build(cls, segment: str, format_str: str) -> datetime.datetime:
        return datetime.datetime.strptime(segment, format_str)


class SystemdHostname(GeneralDirective):
    DIRECTIVE = 'h'
    NEED_BUILD = False
    KEY = 'hostname'

    @classmethod
    def regexp(cls, prefix: str, suffix: str) -> str:
        return r'(\w+)'


class SystemdSource(GeneralDirective):
    DIRECTIVE = 's'
    NEED_BUILD = True
    KEY = 'source'

    @classmethod
    def regexp(cls, prefix: str, suffix: str) -> str:
        return r'([\.\-\w\[\]]+)'

    @classmethod
    def build(cls, segment: str, *args) -> {'pname': str, 'pid': int}:
        match = re.match('(\S+)\[(\d+)\]', segment)
        if match:
            pname, pid = match.groups()
            return {'pname': pname, 'pid': int(pid)}
        else:
            return {'pname': segment, 'pid': -1}


class SystemdMessage(GeneralDirective):
    DIRECTIVE = 'm'
    NEED_BUILD = False
    KEY = 'message'

    @classmethod
    def regexp(cls, prefix: str, suffix: str) -> str:
        return r'(.*)'


# ############### MAKE ROUTER ################


make_router(__name__, ROUTER)
# ############## MAKE PARSER ################

parser = gen_pattern_parser(read, clean)
test_parser = gen_pattern_parser(read, clean, regexp_only=True)
