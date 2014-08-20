#encoding=utf-8
"""
从pattern中生成解析器
"""

DEFAULT_CONVERSION_PATTERN = "%m%n"
TTCC_CONVERSION_PATTERN = "%r [%t] %p %c %x - %m%n"
SIMPLE_CONVERSION_PATTERN = "%d [%t] %p %c - %m%n"


class ParserStatus(object):
    def __init__(self):
        self.string_buffer = []
        self.prefix_buffer = []
        self.suffix_buffer = []
        self.nearby_key = None

    def set_nearby_key(self, key):
        self.nearby_key = key

    def pop_nearby_key(self):
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


def gen_pattern_parser(start_function: callable):
    def pattern_parser(pattern: str):
        status = ParserStatus()
        re_pieces = []
        function = start_function
        for current_char in pattern:
            retval, function = function(current_char, status)
            if isinstance(retval, str):
                re_pieces.append(retval)
            elif retval is None:
                continue
            else:
                raise TypeError('Unexpected type during parsing: {} as {}'
                                .format(str(retval), type(retval)))
        re_pieces.append(status.pop_string())
        return ''.join(re_pieces)
    # 装饰参数列
    return pattern_parser
