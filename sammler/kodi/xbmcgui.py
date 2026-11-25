# -*- coding: utf-8 -*-
# zusatzmetall | IT('s) Possible
# 2026.11.25
from xbmc import _Nichts

NOTIFICATION_INFO = 'info'
NOTIFICATION_WARNING = 'warning'
NOTIFICATION_ERROR = 'error'
INPUT_ALPHANUM = 0
INPUT_NUMERIC = 1
INPUT_DATE = 2
INPUT_TIME = 3
INPUT_IPADDRESS = 4
INPUT_PASSWORD = 5
ALPHANUM_HIDE_INPUT = 2
PASSWORD_VERIFY = 1
DLG_YESNO_NO_BTN = 10
DLG_YESNO_YES_BTN = 11
DLG_YESNO_CUSTOM_BTN = 12
ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
ACTION_SELECT_ITEM = 7


class Dialog:
    def __init__(self, *a, **k):
        pass

    def notification(self, *a, **k):
        return None

    def ok(self, *a, **k):
        return True

    def yesno(self, *a, **k):
        return False

    def yesnocustom(self, *a, **k):
        return -1

    def select(self, *a, **k):
        return -1

    def contextmenu(self, *a, **k):
        return -1

    def multiselect(self, *a, **k):
        return None

    def input(self, *a, **k):
        return ''

    def numeric(self, *a, **k):
        return ''

    def browse(self, *a, **k):
        return ''

    def browseSingle(self, *a, **k):
        return ''

    def browseMultiple(self, *a, **k):
        return []

    def textviewer(self, *a, **k):
        return None

    def info(self, *a, **k):
        return False


class DialogProgress:
    def __init__(self, *a, **k):
        pass

    def create(self, *a, **k):
        return None

    def update(self, *a, **k):
        return None

    def iscanceled(self):
        return False

    def close(self):
        return None


class DialogProgressBG:
    def __init__(self, *a, **k):
        pass

    def create(self, *a, **k):
        return None

    def update(self, *a, **k):
        return None

    def isFinished(self):
        return False

    def close(self):
        return None


class _InfoTag(_Nichts):
    pass


class ListItem:
    def __init__(self, label='', label2='', iconImage='', thumbnailImage='', path='', offscreen=False, **k):
        self._label, self._label2, self._path = label or '', label2 or '', path or ''
        self._props, self._art, self._info = {}, {}, {}

    def getLabel(self):
        return self._label

    def setLabel(self, label):
        self._label = label

    def getLabel2(self):
        return self._label2

    def setLabel2(self, label):
        self._label2 = label

    def getPath(self):
        return self._path

    def setPath(self, path):
        self._path = path

    def setProperty(self, key, value):
        self._props[str(key).lower()] = value

    def setProperties(self, d):
        for k, v in (d or {}).items():
            self.setProperty(k, v)

    def getProperty(self, key):
        return self._props.get(str(key).lower(), '')

    def setArt(self, d):
        self._art.update(d or {})

    def getArt(self, key):
        return self._art.get(key, '')

    def setInfo(self, typ, d):
        self._info.update(d or {})

    def getVideoInfoTag(self):
        return _InfoTag()

    def getMusicInfoTag(self):
        return _InfoTag()

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return lambda *a, **k: None


class Window(_Nichts):
    pass


class WindowDialog(_Nichts):
    pass


class WindowXML(_Nichts):
    pass


class WindowXMLDialog(_Nichts):
    pass


def getCurrentWindowId():
    return 10000


def getCurrentWindowDialogId():
    return 9999


def __getattr__(name):
    if name.startswith('__'):
        raise AttributeError(name)
    if name.isupper():
        return 0
    return _Nichts
