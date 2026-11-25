# -*- coding: utf-8 -*-
# zusatzmetall | IT('s) Possible
# 2026.11.25
from xbmc import _Nichts

SORT_METHOD_NONE = 0
SORT_METHOD_LABEL = 1
SORT_METHOD_TITLE = 9
SORT_METHOD_VIDEO_YEAR = 18
SORT_METHOD_UNSORTED = 40


def addDirectoryItem(*a, **k):
    return True


def addDirectoryItems(*a, **k):
    return True


def endOfDirectory(*a, **k):
    return None


def setResolvedUrl(*a, **k):
    return None


def setContent(*a, **k):
    return None


def setPluginCategory(*a, **k):
    return None


def addSortMethod(*a, **k):
    return None


def setProperty(*a, **k):
    return None


def getSetting(*a, **k):
    return ''


def __getattr__(name):
    if name.startswith('__'):
        raise AttributeError(name)
    if name.isupper():
        return 0
    return _Nichts
