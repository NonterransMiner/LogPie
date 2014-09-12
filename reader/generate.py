# encoding=utf-8
"""
This module makes the reader.
"""
import sys
import os
import time
import shutil
from .pattern import ROUTER as S_ROUTER

READER_TPL = '''
import sys

sys.path.append(\'{pie_root}\')

{directive_import}

from reader.generic import GeneralReader


class {s}LogReader(GeneralReader):
    def __init__(self, lines):
        super().__init__(lines)
        self.regexp = {regexp}
        self.triads = {triads}
        self.triads_dict = {{key: (cls, arg) for key, cls, arg in self.triads}}
        self.using_named_capture = {unc}


def main(path):
    reader = {s}LogReader(path)
    return reader.readall()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Usage:", '\\n', '$ python {fn} logfile')
'''


def gen_filepath(s: str, root: str):
    suffix = time.time() % 10000
    new_path = root + '/%s_%04d.py' % (s, suffix)
    while os.path.exists(new_path):
        suffix += 1
        new_path = root + '/%s_%04d.py' % (s, suffix)
    return new_path


def triad_to_string(triad, indent: int=3):
    key, cls, additional = triad
    cls = cls.__name__
    ts = ' ' * (indent * 4) + '({}, {}, {})'.format(
        repr(key), cls, repr(additional))
    return ts


def write_code(src_path: str, pie_root: str, s: str, regexp: str, triads: list,
               unc=True):
    class_names = map(lambda triad: triad[1].__name__, triads)
    src_filename = os.path.split(src_path)[1]
    readable_triad = "[\n{}]".format(', \n'.join(map(triad_to_string, triads)))
    # add imports
    imports = []
    for name in class_names:
        imports.append('from reader.pattern.{} import {}'.format(s, name))
    # format the class
    src = READER_TPL.format(s=s.title(), fn=src_filename, pie_root=pie_root,
                            regexp=repr(regexp), triads=readable_triad,
                            directive_import='\n'.join(imports),
                            unc=str(unc))
    with open(src_path, 'a') as src_file:
        src_file.writelines(src)


def make_reader(s, pattern) -> str:
    # get absolute root of package reader
    generate_abp = os.path.abspath(__file__)
    reader_root = os.path.split(generate_abp)[0]
    gen_root = reader_root + '/gen'
    pie_root = os.path.split(reader_root)[0]
    # init gen as a empty module
    if not os.path.exists(gen_root):
        os.mkdir(gen_root)
        shutil.copy(reader_root + '/__init__.py', gen_root + '/__init__.py')
    # chose the given pattern module
    pm = S_ROUTER[s]
    # print(pm, hasattr(pm, 'parser'), dir(pm))
    if not hasattr(pm, 'parser'):
        raise RuntimeError('{} is not a available pattern parser.'.format(s))
    else:
        # get regexp & triads to build the reader
        pattern_parser = pm.parser
        regexp, build_triads = pattern_parser(pattern)
        # initialize the new reader's source file
        filepath = gen_filepath(s, gen_root)
        # at last then write in generated new code
        write_code(filepath, pie_root, s, regexp, build_triads)
        return filepath


def main():
    if len(sys.argv) == 3:
        make_reader(*sys.argv[1:])
    else:
        print('Usage:', '\t$ python generate.py type pattern',
              'Example:', '\t$ python generate.py systemd "$d %h %s: %m"',
              sep='\n')


if __name__ == '__main__':
    main()
