# encoding=utf-8

from unittest import TestCase, TestSuite, TextTestRunner

from reader.pattern.common import gen_pattern_parser
from reader.pattern.log4j import Log4jDate
from reader.pattern.log4j import test_parser as parser


class ParserTest(TestCase):
    def test_parser(self):
        self.assertEqual("123", parser("123"))
        self.assertEqual(r'(\d{1,2} \w{3} \d{4} \d{2}:\d{2}:\d{2},\d{3})',
                         parser("%d{DATE}"))

    def test_build(self):
        pass


class DirectiveTestDate(TestCase):
    def test_regexp(self):
        self.assertEqual(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2},\d{3})',
                         Log4jDate.regexp('', 'yyyy/MM/dd HH:mm:ss,SSS'))

    def test_format(self):
        self.assertEqual('%Y/%m/%d %H:%M:%S,%f',
                         Log4jDate.time_format('', 'yyyy/MM/dd HH:mm:ss,SSS'))

    def test_strptime(self):
        pass


def main():
    suite = TestSuite()
    suite.addTest(ParserTest("test_parser"))
    suite.addTest(DirectiveTestDate("test_regexp"))
    suite.addTest(DirectiveTestDate("test_format"))
    runner = TextTestRunner()
    runner.run(suite)


def manual():
    parser = gen_pattern_parser(read, clean)
    var = parser("%p %d{DATE} - %m")
    return var


if __name__ is '__main__':
    # main()
    manual()