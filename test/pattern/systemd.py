# encoding=utf-8

from unittest import TestCase
from reader.pattern.systemd import test_parser as parser


class ParserTest(TestCase):
    def test_parser(self):
        self.assertEqual(
            r'([A-Za-z]{3} \d{2} \d{2}:\d{2}:\d{2})\ (\w+)\ ([\w\[\]]+)\:\ (.*)',
            parser('%d %h %s: %m'))
