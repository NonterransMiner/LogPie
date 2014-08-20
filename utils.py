# encoding=utf-8
"""
A collection of assistant classes, functions and constants
to develop & build LogPie.
"""


class StrUtils:
    @classmethod
    def join(cls, comma: str, iterable):
        """
        A more tolerant version of str.join, apply str() on each element.
        Or, a short for `comma.join(map(lambda x: str(x) if x else '')`
        :param comma: comma to insert
        :param iterable: iterable of elements
        :return: joined string
        """
        return comma.join(map(lambda x: str(x) if x else '',
                              iterable))

    @classmethod
    def connect(cls, iterable):
        """
        Short for `strutils.join('', iterable)
        :param iterable:
        :return:
        """
        return cls.join('', iterable)