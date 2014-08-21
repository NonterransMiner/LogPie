# encoding=utf-8
"""
This module gives out a generic single-line based log reader.
When profiles of log system was analysed, this fill will act as
a template, and few constant, which could change the behavior of
this reader, will be changed.
"""

import re
import os.path


class GeneralReader(object):
    """
    This class implements a general line-based log reader.
    """
    # This will be overwrite by each sub classes

    def __init__(self, lines):
        """
        Initialize an instance with correct #lines#.
        :param lines: A path to the log file, or an iterable object holding log.
        """
        # override these fields to custom the behavior of parser
        # the regexp to capture segments in a single-line
        self.regexp = r''
        # a list of triads with a key, a class like Log4jDate
        # and a tuple of addition information to call cls.build
        self.handlers = []
        # cache compiled re if using iterable accessing
        self.compiled_re = None
        # parser behavior flags
        self.using_file = False
        # if set to True, parser will pass when some line cannot match the
        # given regexp
        self.tolerant = False
        # resources
        self.lines = None
        self.path = None
        self.cache = []
        self.file_bind = None
        self.iter_log_bind = None
        self.iter_lineno = 1
        self.iter_inited = False
        # if lines is  a path to file, keep the path and set flag
        if isinstance(lines, str) and os.path.exists(lines):
            self.path = lines
            self.using_file = True
        # if line is a iterable object, bind it to self.lines
        elif hasattr(lines, '__iter__'):
            self.lines = lines
        # otherwise, raise a TypeError
        else:
            raise TypeError(
                'Given lines as {} is neither a available path'
                'nor a iterable object.'
                .format(type(lines)))

    def execute(self):
        """
        A wrapper to the parse method.
        """
        if self.using_file:
            with open(self.path) as logfile:
                try:
                    self.parse_log(logfile)
                except Exception as e:
                    self.cache.clear()
                    raise e

        else:
            self.parse_log(self.lines)

    def process_matches(self, matches):
        for match in matches:
            log_item = dict()
            mixup = zip(self.handlers, match)
            for (key, cls, addition), segment in mixup:
                log_item[key] = cls.build(segment, *addition)
            self.cache.append(log_item)

    def parse_log(self, log):
        """
        The core parser of the general line-based parser.
        WARNING: This will use A LOT OF MEMORY.
        """
        lineno = 1
        compiled_re = re.compile(self.regexp)
        for line in log:
            matches = compiled_re.findall(line)
            if matches:
                self.process_matches(matches)
            else:
                if self.tolerant:
                    continue
                self.cache.clear()
                raise ValueError(
                    '{}:{}: Line \'{}\' Cannot matches {}.'
                    .format(self.path if self.using_file else '<ITER>',
                            lineno, line, self.regexp))
            lineno += 1

    def _init_iter(self):
        if self.using_file:
            self.iter_log_bind = open(self.path)
        else:
            self.iter_log_bind = self.lines
        self.compiled_re = re.compile(self.regexp)

    def __iter__(self):
        """
        use this instant of calling execute()
        :return:
        """
        if not self.iter_inited:
            self._init_iter()
            self.iter_inited = True
        if self.cache:
            yield self.cache.pop(0)
        else:
            try:
                line = next(self.iter_log_bind)
                matches = self.compiled_re.findall(line)
                if matches:
                    self.process_matches(matches)
                elif not matches and not self.tolerant:
                    raise ValueError(
                        '{}:{}: Line \'{}\' Cannot matches {}.'
                        .format(self.path if self.using_file else '<ITER>',
                                self.iter_lineno, line, self.regexp))
            except StopIteration as si:
                raise si
        if self.cache:
            yield self.cache.pop(0)
        else:
            raise StopIteration()

    def __del__(self):
        del self.cache
        if self.using_file:
            if self.file_bind:
                self.file_bind.close()
        if self.iter_log_bind:
            self.iter_log_bind.close()







