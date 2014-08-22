# encoding=utf-8
"""
This module makes the reader.
"""
import os, os.path, sys, importlib
import reader.pattern


def make_reader(s, pattern):
    parser_module = importlib.import_module(s, 'pattern')
    print(1)
    if hasattr(parser_module, 'reader'):
        pattern_parser = parser_module.parser
        regexp, build_triads = pattern_parser(pattern)


if __name__ is '__main__':
    make_reader('.systemd', '%d %h %s: %m')