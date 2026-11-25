# -*- coding: utf-8 -*-
# zusatzmetall | IT('s) Possible
# 2026.11.25
import logging
import time

LOGDEBUG = 0
LOGINFO = 1
LOGNOTICE = 1
LOGWARNING = 2
LOGERROR = 3
LOGSEVERE = 4
LOGFATAL = 4
LOGNONE = 5

PLAYLIST_MUSIC = 0
PLAYLIST_VIDEO = 1

_log = logging.getLogger('kodi')
_lv = {0: 10, 1: 20, 2: 30, 3: 40, 4: 50, 5: 60}
_INFO = {'System.BuildVersion': '21.0 (21.0.0)', 'System.Language': 'German', 'System.Platform': 'Linux'}


class _Nichts:
    def __init__(self, *a, **k):
        pass

    def __call__(self, *a, **k):
        return _Nichts()

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return _Nichts()

    def __bool__(self):
        return False

    def __iter__(self):
        return iter(())

    def __len__(self):
        return 0

    def __str__(self):
        return ''

    def __int__(self):
        return 0


def log(msg, level=LOGDEBUG):
    _log.log(_lv.get(level, 10), '%s', msg)


def sleep(ms):
    time.sleep(max(0, int(ms or 0)) / 1000.0)


def getCondVisibility(cond):
    c = str(cond or '').lower()
    return c == 'system.platform.linux'


def getInfoLabel(label):
    return _INFO.get(label, '')


def getLanguage(fmt=None, region=False):
    return 'de' if fmt in (0, 1) else 'German'


def getRegion(key=''):
    return {'dateshort': '%d.%m.%Y', 'datelong': '%A, %d. %B %Y', 'time': '%H:%M:%S', 'tempunit': '°C'}.get(key, '')


def getUserAgent():
    return 'Kodi/21.0 (X11; Linux x86_64)'


def executebuiltin(cmd, wait=False):
    return None


def executeJSONRPC(cmd):
    return '{"id":1,"jsonrpc":"2.0","result":{}}'


def getSkinDir():
    return 'skin.estuary'


def translatePath(path):
    import xbmcvfs
    return xbmcvfs.translatePath(path)


def makeLegalFilename(name):
    return name


def validatePath(path):
    return path


def getFreeMem():
    return 2048


def getGlobalIdleTime():
    return 0


def getCacheThumbName(path):
    return '00000000.tbn'


def getIPAddress():
    return '127.0.0.1'


def convertLanguage(lang, fmt=0):
    return lang


def audioResume():
    pass


def audioSuspend():
    pass


def enableNavSounds(yes):
    pass


def playSFX(*a, **k):
    pass


def stopSFX():
    pass


def startServer(*a, **k):
    return False


class Monitor:
    def __init__(self, *a, **k):
        pass

    def abortRequested(self):
        return False

    def waitForAbort(self, timeout=0):
        time.sleep(min(float(timeout or 0), 2.0))
        return False

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return lambda *a, **k: None


class Player:
    def __init__(self, *a, **k):
        pass

    def play(self, item=None, listitem=None, windowed=False, startpos=-1):
        return None

    def isPlaying(self):
        return False

    def isPlayingVideo(self):
        return False

    def getTime(self):
        return 0.0

    def getTotalTime(self):
        return 0.0

    def getPlayingFile(self):
        return ''

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return lambda *a, **k: None


class PlayList:
    def __init__(self, *a, **k):
        self._items = []

    def add(self, url, listitem=None, index=-1):
        self._items.append(url)

    def clear(self):
        self._items = []

    def size(self):
        return len(self._items)

    def __len__(self):
        return len(self._items)

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return lambda *a, **k: None


class Keyboard:
    def __init__(self, default='', heading='', hidden=False):
        self._text = default or ''

    def doModal(self, autoclose=0):
        pass

    def isConfirmed(self):
        return False

    def getText(self):
        return self._text

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return lambda *a, **k: None


class InfoTagVideo(_Nichts):
    pass


def __getattr__(name):
    if name.startswith('__'):
        raise AttributeError(name)
    if name.isupper():
        return 0
    return _Nichts

