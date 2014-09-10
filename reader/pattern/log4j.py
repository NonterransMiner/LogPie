# encoding=utf-8
"""
This is the LogPie.reader.pattern.log4j module.
This module provides all the implementations of functions and classes
which are designed to handle the Pattern in Log4j's configurations.
"""
import datetime
import re

from .common import ParserStatus, GeneralDirective
from .common import gen_pattern_parser, make_router
from .utils import StrUtils


DEFAULT_CONVERSION_PATTERN = "%m%n"
TTCC_CONVERSION_PATTERN = "%r [%t] %p %c %x - %m%n"
SIMPLE_CONVERSION_PATTERN = "%d [%t] %p %c - %m%n"
ROUTER = dict()
DEFAULT_DATE_PATTERN = ''

# ############### Functions to complete the pattern reader ################


def make_directive(prefix: str, directive: str, suffix: str):
    cls = ROUTER.get(directive, None)
    if not cls:
        raise ValueError(
            'Pattern %{}{}{} does not exists or not implemented yet.'
            .format(prefix, directive, suffix))
    else:
        regexp_piece = cls.regexp(prefix, suffix)
        if cls.NEED_BUILD:
            build_triad = (cls.KEY, cls,
                           cls.additional_info(prefix, suffix))
        else:
            build_triad = (cls.KEY, cls, tuple())
    return regexp_piece, build_triad


def read(current_char: str, status: ParserStatus):
    if current_char == '%':
        return status.pop_string(), read_present
    else:
        status.push_char(re.escape(current_char))
        return None, read


def read_pending(current_char: str, status: ParserStatus):
    if current_char == '{':
        return None, read_braces
    else:
        re_piece, build_triad = make_directive(*status.pop_3())
        retval, next_func = read(current_char, status)
        if isinstance(retval, str):
            return (re_piece + retval, build_triad), next_func
        if retval is None:
            return (re_piece, build_triad), next_func
        else:
            raise TypeError('Unexpected {} {}'
                            .format(retval, type(retval)))


def read_braces(current_char: str, status: ParserStatus):
    if current_char == '}':
        return make_directive(*status.pop_3()), read
    else:
        status.push_suffix(current_char)
        return None, read_braces


def read_present(current_char: str, status: ParserStatus):
    if current_char == '%':
        return '%', read
    elif current_char in ROUTER:
        status.set_nearby_directive(current_char)
        return None, read_pending
    elif current_char:
        status.push_prefix(current_char)
    else:
        raise SyntaxError('LogPie cannot parse %{}'
                          .format(current_char))


def clean(status: ParserStatus):
    if status.string_buffer:
        return status.pop_string(), ()
    if status.nearby_key:
        t, a = make_directive(*status.pop_3())
        return t, a


# ############### Classes to handle the directives ################
class Log4jDate(GeneralDirective):
    """
    Handle %D in profiles.
    Here's a long way to go.
    """

    DIRECTIVE = 'd'
    NEED_BUILD = True
    KEY = 'date'

    DATE_DIRECTIVES = {
        'y': ('%Y', '\d'),
        'M': ('%m', '\d'),
        'd': ('%d', '\d'),
        'H': ('%H', '\d'),
        'm': ('%M', '\d'),
        's': ('%S', '\d'),
        'S': ('%f', '\d'),
    }

    BUILTIN = {
        'ABSOLUTE': ('%H:%M:%S.%f',
                     r'(\d{2}:\d{2}:\d{2}.\d{3})'),
        'DATE': ('%d %b %Y %H:%M:%S.%f',
                 r'(\d{1,2} \w{3} \d{4} \d{2}:\d{2}:\d{2}.\d{3})'),
        'ISO8601': ('%Y-%m-%d %H:%M:%S.%f',
                    r'(\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}:\d{2}.\d{3})')
    }

    @classmethod
    def regexp(cls, prefix: str, suffix: str) -> str:
        if prefix:
            raise SyntaxError(
                'Cannot parse %{}d{{{}}}: no prefixing options excepted'
                .format(prefix, suffix))
        if suffix in Log4jDate.BUILTIN:
            return Log4jDate.BUILTIN[suffix][1]
        if not suffix:
            suffix = DEFAULT_DATE_PATTERN
        date_format, date_re = Log4jDate.parse_suffix(suffix)
        return '({})'.format(date_re)

    @classmethod
    def time_format(cls, prefix: str, suffix: str) -> str:
        if prefix:
            raise SyntaxError(
                'Cannot parse %{}d{{{}}}: no prefixing options excepted'
                .format(prefix, suffix))
        if suffix in Log4jDate.BUILTIN:
            return Log4jDate.BUILTIN[suffix][0]
        if not suffix:
            suffix = DEFAULT_DATE_PATTERN
        date_format, date_re = Log4jDate.parse_suffix(suffix)
        return date_format

    @classmethod
    def parse_suffix(cls, suffix: str) -> (str, str):
        """
        Parse suffix of %d directives.
        Returns 2 values, the first is a format string for datetime.strptime
        and the second is a regexp to capture the segment of date.
        :param suffix: suffix for %d
        :return: a format string and a regexp.
        """
        last_directive = None
        last_directive_count = 1
        format_pieces = []
        re_pieces = []
        for c in suffix:
            if c in cls.DATE_DIRECTIVES:
                if c == last_directive:
                    last_directive_count += 1
                    continue
                else:
                    last_directive = c
                    last_directive_count = 1
                ctrl, re_piece = cls.DATE_DIRECTIVES[c]
                if ctrl:
                    format_pieces.append(ctrl)
                    re_pieces.append(re_piece)
            else:
                if re_pieces:
                    re_pieces.append("{{{}}}".format(last_directive_count))
                format_pieces.append(c)
                re_pieces.append(c)
        if last_directive in cls.DATE_DIRECTIVES:
            re_pieces.append("{{{}}}".format(last_directive_count))
        return StrUtils.connect(format_pieces), StrUtils.connect(re_pieces)

    @classmethod
    def additional_info(cls, prefix: str, suffix: str) -> tuple:
        return Log4jDate.time_format(prefix, suffix),

    @classmethod
    def build(cls, segment: str, format_str: str) -> datetime.datetime:
        return datetime.datetime.strptime(segment, format_str)


class Log4jLoggerNamespace(GeneralDirective):
    DIRECTIVE = 'c'
    KEY = 'logger.namespace'

    @classmethod
    def regexp(cls, prefix: str, suffix: str) -> str:
        return r"([.\w]+)"


class Log4jLoggerClassName(GeneralDirective):
    DIRECTIVE = 'C'
    KEY = 'logger.class'

    @classmethod
    def regexp(cls, prefix: str, suffix: str) -> str:
        return r"([.\w]+)"


class Log4jSourceFile(GeneralDirective):
    DIRECTIVE = 'F'
    KEY = 'source.file'

    @classmethod
    def regexp(cls, prefix: str, suffix: str) -> str:
        return r'(\w[\w.]+\.java)'


class Log4jCallerPosition(GeneralDirective):
    DIRECTIVE = 'l'
    KEY = 'caller.position'

    @classmethod
    def regexp(cls, prefix: str, suffix: str) -> str:
        return r'(\d+)'


class Log4jCallerLineNumber(GeneralDirective):
    DIRECTIVE = 'L'
    KEY = 'caller.lineno'
    NEED_BUILD = True

    @classmethod
    def regexp(cls, prefix: str, suffix: str) -> str:
        return r'(\d+1)'

    @classmethod
    def build(cls, segment: str, *args):
        return int(segment)


class Log4jMessage(GeneralDirective):
    DIRECTIVE = 'm'
    KEY = 'message'

    @classmethod
    def regexp(cls, prefix: str, suffix: str) -> str:
        return r'(.*)'


class Log4jCallerMethodName(GeneralDirective):
    DIRECTIVE = 'M'
    KEY = 'caller.method'

    @classmethod
    def regexp(cls, prefix: str, suffix: str) -> str:
        return r'(\w[\d\w\._]+)'


class Log4jLogLevel(GeneralDirective):
    DIRECTIVE = 'p'
    KEY = 'level'

    @classmethod
    def regexp(cls, prefix: str, suffix: str) -> str:
        return "(DEBUG|INFO|WARN|ERROR|FATAL)"


class Log4jRuntimeMillisecond(GeneralDirective):
    DIRECTIVE = 'r'
    KEY = 'runtime'
    NEED_BUILD = True

    @classmethod
    def regexp(cls, prefix: str, suffix: str) -> str:
        return '(\d+)'

    @classmethod
    def build(cls, segment: str, *args):
        return int(segment)


class Log4jCallerThreadName(GeneralDirective):
    DIRECTIVE = 't'
    KEY = 'caller.thread'

    @classmethod
    def regexp(cls, prefix: str, suffix: str) -> str:
        return r'(\w[\d\w\._]+)'


class Log4jNDC(GeneralDirective):
    DIRECTIVE = 'x'
    KEY = 'ndc'


class Log4jMDC(GeneralDirective):
    DIRECTIVE = 'X'
    KEY = 'mdc'

# ############### MAKE ROUTER ###############
make_router(__name__, ROUTER)
# ############## MAKE PARSER ################
parser = gen_pattern_parser(read, clean)
test_parser = gen_pattern_parser(read, clean, regexp_only=True)
