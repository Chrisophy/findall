# -*- coding: utf-8 -*-
# zusatzmetall | IT('s) Possible
# 2026.11.25
import logging
import traceback

LOGDEBUG = 0
LOGINFO = 1
LOGWARNING = 2
LOGERROR = 3
LOGFATAL = 4

_log = logging.getLogger('scraper')
_lv = {0: 10, 1: 20, 2: 30, 3: 40, 4: 50}


def log(msg, level=LOGINFO):
    _log.log(_lv.get(level, 20), '%s', msg)


def error(msg=''):
    _log.error('%s\n%s', msg, traceback.format_exc())
