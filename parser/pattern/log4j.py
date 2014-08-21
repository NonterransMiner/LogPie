# encoding=utf-8
"""
This is the LogPie.parser.pattern.log4j module.
This module provides all the implementations of functions and classes
which are designed to handle the Pattern in Log4j's configurations.
"""
import datetime
import re

from .pattern import ParserStatus
from utils import StrUtils


DEFAULT_CONVERSION_PATTERN = "%m%n"
TTCC_CONVERSION_PATTERN = "%r [%t] %p %c %x - %m%n"
SIMPLE_CONVERSION_PATTERN = "%d [%t] %p %c - %m%n"
ROUTER = dict()
DEFAULT_DATE_PATTERN = ''

# ############### Functions to complete the pattern parser ################


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
        return status.pop_string()
    if status.nearby_key:
        return make_directive(*status.pop_3())


# ############### Classes to handle the directives ################


class Log4jDirective:
    # None for N/A and a single-character for directive which this class
    # handles
    DIRECTIVE = None
    # Whether this classes needs to call build method to generate a custom
    # object
    NEED_BUILD = False
    # The key for the output dict
    KEY = 'LOG4J'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        """
        Generate a regexp to capture this segment from the log line.
        """
        pass

    @classmethod
    def build(cls, segment: str, format_str: str):
        """
        Build a custom object if the builtins cannot describe this segment
        elegantly.
        """
        pass

    @classmethod
    def additional_info(cls, prefix: str, suffix: str):
        return tuple()


class Log4jDate(Log4jDirective):
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
        'ABSOLUTE': ('%H:%M:%S,%f',
                     r'(\d{2}:\d{2}:\d{2},\d{3})'),
        'DATE': ('%d %b %Y %H:%M:%S,%f',
                 r'(\d{1,2} \w{3} \d{4} \d{2}:\d{2}:\d{2},\d{3})'),
        'ISO8601': ('%Y-%m-%d %H:%M:%S,%f',
                    r'(\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}:\d{2},\d{3})')
    }

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
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
    def time_format(cls, prefix: str, suffix: str):
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
    def parse_suffix(cls, suffix: str):
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
                ctrl, re = cls.DATE_DIRECTIVES[c]
                if ctrl:
                    format_pieces.append(ctrl)
                    re_pieces.append(re)
            else:
                if re_pieces:
                    re_pieces.append("{{{}}}".format(last_directive_count))
                format_pieces.append(c)
                re_pieces.append(c)
        if last_directive in cls.DATE_DIRECTIVES:
            re_pieces.append("{{{}}}".format(last_directive_count))
        return StrUtils.connect(format_pieces), StrUtils.connect(re_pieces)

    @classmethod
    def additional_info(cls, prefix: str, suffix: str):
        return Log4jDate.time_format(prefix, suffix)

    @classmethod
    def build(cls, segment: str, format_str: str):
        return datetime.datetime.strptime(segment, format_str)


class Log4jLoggerNamespace(Log4jDirective):
    DIRECTIVE = 'c'
    KEY = 'logger.namespace'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        return r"([.\w]+)"


class Log4jLoggerClassName(Log4jDirective):
    DIRECTIVE = 'C'
    KEY = 'logger.class'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        return r"([.\w]+)"


class Log4jSourceFile(Log4jDirective):
    DIRECTIVE = 'F'
    KEY = 'source.file'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        return r'(\w[\w.]+\.java)'


class Log4jCallerPosition(Log4jDirective):
    DIRECTIVE = 'l'
    KEY = 'caller.position'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        return r'(\d+)'


class Log4jCallerLineNumber(Log4jDirective):
    DIRECTIVE = 'L'
    KEY = 'caller.lineno'


class Log4jMessage(Log4jDirective):
    DIRECTIVE = 'm'
    KEY = 'message'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        return r'(.*)'


class Log4jCallerMethodName(Log4jDirective):
    DIRECTIVE = 'M'
    KEY = 'caller.method'


class Log4jLogLevel(Log4jDirective):
    DIRECTIVE = 'p'
    KEY = 'level'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        return "(DEBUG|INFO|WARN|ERROR|FATAL)"


class Log4jRuntimeMillisecond(Log4jDirective):
    DIRECTIVE = 'r'
    KEY = 'runtime'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        return '(\d+)'


class Log4jCallerThreadName(Log4jDirective):
    DIRECTIVE = 't'
    KEY = 'caller.thread'


class Log4jNDC(Log4jDirective):
    DIRECTIVE = 'x'
    KEY = 'ndc'


class Log4jMDC(Log4jDirective):
    DIRECTIVE = 'X'
    KEY = 'mdc'

# ############### MAKE ROUTER ###############
import sys

log4j = sys.modules[__name__]
for key in dir(log4j):
    item = getattr(log4j, key, None)
    if hasattr(item, "DIRECTIVE") and item is not Log4jDirective:
        ROUTER[item.DIRECTIVE] = item
