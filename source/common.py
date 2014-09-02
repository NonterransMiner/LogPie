# encoding=utf-8


JAVA = 'JAVA'

IGNORE = {JAVA: ' ;'}

CONNECT = {JAVA: '+'}


def parse_msg_tpl(tpl: str, lang=JAVA) -> (str, (str,)):
    re_pieces = []
    segment_buffer = []
    segments = []
    re_segment = '(.*)'
    reading_context = False
    for c in lang:
        if c == r'"':
            if not segment_buffer:
                re_pieces.append(re_segment)
            else:
                re_pieces.append(''.join(segment_buffer))
            reading_context = not reading_context
        if reading_context:
            re_pieces.append(c)
        else:
            segment_buffer.append(c)

