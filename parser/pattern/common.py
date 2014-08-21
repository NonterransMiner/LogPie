# encoding=utf-8
"""
从pattern中生成解析器
"""


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


def gen_pattern_parser(start_function: callable, cleanup_function: callable):
    def pattern_parser(pattern: str):
        status = ParserStatus()
        re_pieces = []
        build_triads = []
        function = start_function
        for current_char in pattern:
            retval, function = function(current_char, status)
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
        remaing = cleanup_function(status)
        if remaing:
            re_pieces.append(remaing)
        return ''.join(re_pieces)

    return pattern_parser
