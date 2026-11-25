# -*- coding: utf-8 -*-
# zusatzmetall | IT('s) Possible
# 2026.11.25
import xbmc
import xbmcaddon
import xbmcgui


def addon():
    return xbmcaddon.Addon()


def addonProfile():
    return xbmcaddon.Addon().getAddonInfo('profile')


def addonPath():
    return xbmcaddon.Addon().getAddonInfo('path')


def getSetting(key, default=''):
    v = xbmcaddon.Addon().getSetting(key)
    return v if v != '' else default


def setSetting(key, value):
    xbmcaddon.Addon().setSetting(key, value)


def keyboard(default='', heading='', hidden=False):
    return xbmc.Keyboard(default, heading, hidden)


def infoDialog(message, heading='MovieScout', icon='', time=3000):
    xbmcgui.Dialog().notification(heading, message, icon or xbmcgui.NOTIFICATION_INFO, time, False)


def notification(heading, message, icon='', time=3000):
    xbmcgui.Dialog().notification(heading, message, icon or xbmcgui.NOTIFICATION_INFO, time, False)


def sleep(ms):
    xbmc.sleep(ms)
