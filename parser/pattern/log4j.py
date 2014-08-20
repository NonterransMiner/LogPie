# encoding=utf-8
"""
This is the LogPie.parser.pattern.log4j module.
This module provides all the implementations of functions and classes
which are designed to handle the Pattern in Log4j's configurations.
"""
import datetime
from .pattern import ParserStatus
from utils import strutils

ROUTER = dict()
DEFAULT_DATE_PATTERN = ''

################ Functions to complete the pattern parser ################


def read(current_char: str, status: ParserStatus):
    if current_char == '%':
        return status.pop_string(), read_present
    else:
        status.push_char(current_char)
        return None, read


def read_pending(current_char: str, status: ParserStatus):
    if current_char == '{':
        return None, read_braces
    else:
        prefix = status.pop_prefix()
        key = status.pop_nearby_key()
        suffix = status.pop_suffix()
        directive = ROUTER.get(key, None)
        if issubclass(directive, Log4jDirective):
            re_piece = directive.regexp(prefix, suffix)
        else:
            raise KeyError(
                'Pattern %{}{}{} does not exists or not implemented yet.'
                .format(prefix, key, suffix))
        retval, next_func = read(current_char, status)
        if isinstance(retval, str):
            return re_piece + retval, next_func
        if retval is None:
            return re_piece, next_func
        else:
            raise TypeError('Unexpected {} {}'
                            .format(retval, type(retval)))


def read_braces(current_char: str, status: ParserStatus):
    if current_char == '}':
        prefix = status.pop_prefix()
        key = status.pop_nearby_key()
        suffix = status.pop_suffix()
        re_piece = ROUTER[key].regexp(prefix, suffix)
        if isinstance(re_piece, str):
            return re_piece, read
        else:
            raise TypeError('Unexpected {} {}'
                            .format(re_piece, type(re_piece)))
    else:
        status.push_suffix(current_char)
        return None, read_braces


def read_present(current_char: str, status: ParserStatus):
    if current_char == '%':
        return '%', read
    elif current_char in ROUTER:
        status.set_nearby_key(current_char)
        return None, read_pending
    elif current_char:
        status.push_prefix(current_char)
    else:
        raise SyntaxError('LogPie cannot parse %{}'
                          .format(current_char))


################ Classes to handle the directives ################


class Log4jDirective:
    # None for N/A and a single-character for directive which this class
    # handles
    DIRECTIVE = None
    # Whether this classes needs to call build method to generate a custom
    # object
    NEED_BUILD = False

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


class Log4jDate(Log4jDirective):
    """
    Handle %D in profiles.
    Here's a long way to go.
    """

    DIRECTIVE = 'd'
    NEED_BUILD = True

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
                'Cannot parse %{}c{}: no prefixing options excepted'
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
                'Cannot parse %{}c{}: no prefixing options excepted'
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
        return strutils.connect(format_pieces), strutils.connect(re_pieces)

    @classmethod
    def build(cls, segment: str, format_str: str):
        return datetime.datetime.strptime(segment, format_str)


class Log4jLoggerNamespace(Log4jDirective):
    DIRECTIVE = 'c'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        return r"([.\w]+)"


class Log4jLoggerClassName(Log4jDirective):
    DIRECTIVE = 'C'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        return r"([.\w]+)"


class Log4jSourceFile(Log4jDirective):
    DIRECTIVE = 'F'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        return r'(\w[\w.]+\.java)'


class Log4jCallerPosition(Log4jDirective):
    DIRECTIVE = 'l'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        return r'(\d+)'


class Log4jCallerLineNumber(Log4jDirective):
    DIRECTIVE = 'L'


class Log4jMessage(Log4jDirective):
    DIRECTIVE = 'm'


class Log4jCallerMethodName(Log4jDirective):
    DIRECTIVE = 'M'


class Log4jLogLevel(Log4jDirective):
    DIRECTIVE = 'p'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        return "(DEBUG|INFO|WARN|ERROR|FATAL)"


class Log4jRuntimeMillisecond(Log4jDirective):
    DIRECTIVE = 'r'

    @classmethod
    def regexp(cls, prefix: str, suffix: str):
        return '(\d+)'


class Log4jCallerThreadName(Log4jDirective):
    DIRECTIVE = 't'


class Log4jNDC(Log4jDirective):
    DIRECTIVE = 'x'


class Log4jMDC(Log4jDirective):
    DIRECTIVE = 'X'

################ MAKE ROUTER ###############
import sys

log4j = sys.modules[__name__]
for key in dir(log4j):
    item = getattr(log4j, key, None)
    if hasattr(item, "DIRECTIVE") and item is not Log4jDirective:
        ROUTER[item.DIRECTIVE] = item
