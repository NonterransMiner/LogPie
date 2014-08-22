# encoding=utf-8
"""
This module makes the reader.
"""
import sys, os, importlib, time, math, shutil

import pattern

READER_TPL = '''
class {}LogReader(GeneralReader):
    def __init__(self, lines):
        super().__init__(lines)
        self.regexp = {}
        self.triads = {}
    '''


def gen_filepath(s: str, root: str):
    return root + '/{}_{}.py'.format(s,
                                     # math.floor(time.time()) % 10000)
                                     0000)


def triad_to_string(triad, indent: int=3):
    key, cls, additional = triad
    cls = cls.__name__
    ts = ' ' * (indent * 4) + '({}, {}, {})'.format(
        repr(key), cls, repr(additional))
    return ts


def write_code(s:str, src_path: str, regexp: str, triads: list):
    src = ['\n']
    # add imports
    class_names = map(lambda triad: triad[1].__name__, triads)
    readable_triad = "[\n{}]".format(', \n'.join(map(triad_to_string, triads)))
    for name in class_names:
        src.append('from reader.pattern.{} import {}\n'.format(s, name))
    src.append('\n')
    # format the class
    src.append(READER_TPL
               .format(s.title(), repr(regexp), readable_triad))
    # print('\n'.join(src))
    with open(src_path, 'a') as src_file:
        src_file.writelines(src)


def make_reader(s, pattern):
    # get absolute root of package reader
    this_file_abs = os.path.abspath(sys.argv[0])
    abs_root = os.path.split(this_file_abs)[0]
    abs_gen = abs_root + '/gen'
    # init gen as a empty module
    if not os.path.exists(abs_gen):
        os.mkdir(abs_gen)
        shutil.copy(abs_root + '/__init__.py', abs_gen + '/__init__.py')
    # dynamic import the given pattern module
    pm = importlib.import_module('.' + s.lower(), 'pattern')
    # print(pm, hasattr(pm, 'parser'), dir(pm))
    if not hasattr(pm, 'parser'):
        raise RuntimeError('{} is not a available pattern parser.'.format(s))
    else:
        # get regexp & triads to build the reader
        pattern_parser = pm.parser
        regexp, build_triads = pattern_parser(pattern)
        # initialize the new reader's source file
        filepath = gen_filepath(s, abs_gen)
        if os.path.exists(filepath):
            os.remove(filepath)
        shutil.copy(abs_root + '/generic.py', filepath)
        # at last then write in generated new code
        write_code(s, filepath, regexp, build_triads)
        # print(regexp, '\n', build_triads)


if __name__ == '__main__':
    make_reader('systemd', '%d %h %s: %m')