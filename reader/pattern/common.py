# encoding=utf-8
"""
This module provides common components to construct the pattern parser
"""

# # Constants

ELIXIR = 'Elixir'


class ParserStatus(object):
    def __init__(self):
        self.string_buffer = []
        self.prefix_buffer = []
        self.suffix_buffer = []
        self.nearby_key = None

    def set_nearby_directive(self, key):
        self.nearby_key = key

    def pop_nearby_directive(self):
        key, self.nearby_key = self.nearby_key, None
        return key

    def push_char(self, char: str):
        self.string_buffer.append(char)

    def push_suffix(self, opt: str):
        self.suffix_buffer.append(opt)

    def push_prefix(self, opt: str):
        self.prefix_buffer.append(opt)

    def pop_string(self):
        s = ''.join(self.string_buffer)
        self.string_buffer.clear()
        return s

    def pop_prefix(self):
        s = ''.join(self.prefix_buffer)
        self.prefix_buffer.clear()
        return s

    def pop_suffix(self):
        s = ''.join(self.suffix_buffer)
        self.suffix_buffer.clear()
        return s

    def pop_3(self):
        prefix = self.pop_prefix()
        directive = self.pop_nearby_directive()
        suffix = self.pop_suffix()
        return prefix, directive, suffix


class GeneralDirective:
    # None for N/A and a single-character for directive which this class
    # handles
    DIRECTIVE = None
    # Whether this classes needs to call build method to generate a custom
    # object
    NEED_BUILD = False
    # The key for the output dict
    KEY = 'GENERAL'

    @classmethod
    def regexp(cls, prefix: str, suffix: str, named=False, lang=None) -> str:
        """
        Generate a regexp to capture this segment from the log line.
        if `named` is True, this function will return a regexp using
        name group.
        if `lang` is None for Python, or, which is still planning, 'Elixir'
        This function is just a wrapper, it calls the gen_regexp to make
        the pattern and format it as `named` and `lang` says.
        """
        basic_re = cls.gen_regexp(prefix, suffix, named, lang)
        if not named:
            return '({})'.format(basic_re)
        else:
            if lang is None:
                return '(?P<{}>{})'.format(cls.KEY, basic_re)
            elif lang == ELIXIR:
                return '(?<{}>{})'.format(cls.KEY, basic_re)


    @classmethod
    def gen_regexp(cls, prefix: str, suffix: str, named=False,
                   lang=None) -> str:
        """
        This function will generate the real `pattern` for the given directive
        """
        pass

    @classmethod
    def build(cls, segment: str, *args):
        """
        Build a custom object if the builtins cannot describe this segment
        properly.
        """
        return segment

    @classmethod
    def additional_info(cls, prefix: str, suffix: str) -> tuple:
        """
        Provide additional params to .build method in a tuple.
        If have nothing to do, return an empty tuple.
        """
        return tuple()


def gen_pattern_parser(start_function: callable,
                       cleanup_function: callable,
                       regexp_only: bool=False,
                       named=True,
                       lang=None):
    def pattern_parser(pattern: str):
        status = ParserStatus()
        re_pieces = []
        build_triads = []
        function = start_function
        for current_char in pattern:
            retval, function = function(current_char, status,
                                        named=named, lang=lang)
            if isinstance(retval, str):
                re_pieces.append(retval)
            elif isinstance(retval, tuple) and len(retval) == 2:
                regexp_piece, build_triad = retval
                re_pieces.append(regexp_piece)
                build_triads.append(build_triad)
            elif retval is None:
                continue
            else:
                raise TypeError('Unexpected type during parsing: {} as {}'
                                .format(str(retval), type(retval)))
        remaining_reg, remaining_tri = cleanup_function(status,
                                                        named=named, lang=lang)
        if remaining_reg:
            re_pieces.append(remaining_reg)
        if remaining_tri:
            build_triads.append(remaining_tri)
        regexp = ''.join(re_pieces)
        if regexp_only:
            return regexp
        else:
            return regexp, build_triads

    return pattern_parser


def make_router(module_name: str, router):
    import sys

    module = sys.modules[module_name]
    for key in dir(module):
        item = getattr(module, key, None)
        if hasattr(item, "DIRECTIVE") and item is not GeneralDirective:
            router[item.DIRECTIVE] = item
