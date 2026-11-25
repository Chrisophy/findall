# -*- coding: utf-8 -*-
# zusatzmetall | IT('s) Possible
# 2026.11.25
import json
import os
import threading

import xbmcvfs

_LOCK = threading.Lock()
try:
    _SETTINGS = dict(json.loads(os.environ.get('MS_EINSTELLUNGEN') or '{}'))
except Exception:
    _SETTINGS = {}
_SETTINGS = {str(k): str(v) for k, v in _SETTINGS.items()}


def all_settings():
    return dict(_SETTINGS)


class Addon:
    def __init__(self, id=None, *a, **k):
        self._id = id or 'plugin.video.moviescout'

    def getAddonInfo(self, key):
        if key == 'id':
            return self._id
        if key == 'name':
            return 'MovieScout'
        if key == 'version':
            return '9.9.9'
        if key == 'profile':
            p = xbmcvfs.translatePath('special://profile/addon_data/%s/' % self._id)
            os.makedirs(p, exist_ok=True)
            return p
        if key == 'path':
            return xbmcvfs.translatePath('special://home/addons/%s/' % self._id)
        if key == 'author':
            return 'MovieScout'
        return ''

    def getSetting(self, key):
        with _LOCK:
            return _SETTINGS.get(str(key), '')

    def getSettingString(self, key):
        return self.getSetting(key)

    def getSettingBool(self, key):
        return self.getSetting(key).lower() == 'true'

    def getSettingInt(self, key):
        try:
            return int(float(self.getSetting(key) or 0))
        except Exception:
            return 0

    def getSettingNumber(self, key):
        try:
            return float(self.getSetting(key) or 0)
        except Exception:
            return 0.0

    def setSetting(self, key, value):
        with _LOCK:
            _SETTINGS[str(key)] = str(value)
        return True

    def setSettingString(self, key, value):
        return self.setSetting(key, value)

    def setSettingBool(self, key, value):
        return self.setSetting(key, 'true' if value else 'false')

    def setSettingInt(self, key, value):
        return self.setSetting(key, int(value))

    def setSettingNumber(self, key, value):
        return self.setSetting(key, value)

    def getLocalizedString(self, sid):
        return ''

    def openSettings(self):
        return None

    def getSettings(self):
        return self
