# -*- coding: utf-8 -*-
# zusatzmetall | IT('s) Possible
# 2026.11.25
import os
import shutil
import tempfile

_PROFIL = os.path.abspath(os.environ.get('MS_PROFIL') or os.path.join(tempfile.gettempdir(), 'ms_profil'))
_HOME = os.path.dirname(os.path.abspath(__file__))


def translatePath(path):
    p = str(path or '')
    if not p.startswith('special://'):
        return p
    rest = p[len('special://'):]
    root, _, sub = rest.partition('/')
    if root in ('profile', 'masterprofile', 'userdata'):
        base = _PROFIL
    elif root == 'temp':
        base = os.path.join(_PROFIL, 'temp')
    elif root in ('home', 'xbmc', 'xbmcbin'):
        base = os.path.join(_PROFIL, 'home')
    else:
        base = os.path.join(_PROFIL, root)
    out = os.path.join(base, *[x for x in sub.split('/') if x])
    if p.endswith('/'):
        out = out.rstrip(os.sep) + os.sep
    return out


def exists(path):
    return os.path.exists(translatePath(path))


def mkdir(path):
    try:
        os.mkdir(translatePath(path))
        return True
    except Exception:
        return False


def mkdirs(path):
    try:
        os.makedirs(translatePath(path), exist_ok=True)
        return True
    except Exception:
        return False


def delete(path):
    try:
        os.remove(translatePath(path))
        return True
    except Exception:
        return False


def rmdir(path, force=False):
    try:
        p = translatePath(path)
        shutil.rmtree(p) if force else os.rmdir(p)
        return True
    except Exception:
        return False


def rename(src, dst):
    try:
        os.replace(translatePath(src), translatePath(dst))
        return True
    except Exception:
        return False


def copy(src, dst):
    try:
        shutil.copyfile(translatePath(src), translatePath(dst))
        return True
    except Exception:
        return False


def listdir(path):
    p = translatePath(path)
    dirs, files = [], []
    try:
        for n in sorted(os.listdir(p)):
            (dirs if os.path.isdir(os.path.join(p, n)) else files).append(n)
    except Exception:
        pass
    return dirs, files


def makeLegalFilename(name):
    return name


def validatePath(path):
    return path


class Stat:
    def __init__(self, path):
        try:
            self._st = os.stat(translatePath(path))
        except Exception:
            self._st = None

    def st_size(self):
        return self._st.st_size if self._st else 0

    def st_mtime(self):
        return int(self._st.st_mtime) if self._st else 0


class File:
    def __init__(self, path, mode='r'):
        p = translatePath(path)
        m = 'wb' if 'w' in mode else ('ab' if 'a' in mode else 'rb')
        if 'b' not in m:
            m += 'b'
        if m.startswith(('w', 'a')):
            d = os.path.dirname(p)
            if d:
                os.makedirs(d, exist_ok=True)
        try:
            self._f = open(p, m)
        except Exception:
            self._f = None

    def read(self, n=-1):
        if not self._f:
            return ''
        b = self._f.read() if n is None or n < 0 else self._f.read(n)
        return b.decode('utf-8', 'replace')

    def readBytes(self, n=-1):
        if not self._f:
            return b''
        return self._f.read() if n is None or n < 0 else self._f.read(n)

    def write(self, data):
        if not self._f:
            return False
        self._f.write(data.encode('utf-8') if isinstance(data, str) else bytes(data))
        return True

    def size(self):
        try:
            return os.fstat(self._f.fileno()).st_size
        except Exception:
            return 0

    def seek(self, pos, whence=0):
        return self._f.seek(pos, whence) if self._f else 0

    def tell(self):
        return self._f.tell() if self._f else 0

    def close(self):
        if self._f:
            self._f.close()
            self._f = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False
