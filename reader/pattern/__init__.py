# encoding=utf-8
from . import log4j
from . import systemd

ROUTER = {
    'log4j': log4j,
    'systemd': systemd
}
