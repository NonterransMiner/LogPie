# encoding=utf-8
import os
import re
import sys

RE = "(\S+)\.([a-z]{4,5})\((.*)\);"


def main():
    rec = re.compile(RE)
    for line in sys.stdin:
        file, lineno, invoke = line.split(':', maxsplit=2)
        logger, level, message_tpl = rec.match(invoke).groups()
        logpoint = {'file': file,
                    'lineno': int(lineno),
                    'logger': logger,
                    'level': level,
                    'message_tpl': message_tpl}
        sys.stdout.write(str(logpoint)+'\n')
    sys.stdout.close()


if __name__ == '__main__':
    main()



