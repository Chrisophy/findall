# -*- coding: utf-8 -*-
# zusatzmetall | IT('s) Possible
# 2026.11.25
import gzip
import http.cookiejar
import json as _json
import os
import re
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

_DEFAULT_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
               '(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36')
_DEFAULT_LANG = 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7'
_DEFAULT_TIMEOUT = 15
_STATUS_TEXT = {200: 'OK', 301: 'Moved Permanently', 302: 'Found', 400: 'Bad Request', 401: 'Unauthorized',
                403: 'Forbidden', 404: 'Not Found', 429: 'Too Many Requests', 500: 'Internal Server Error',
                502: 'Bad Gateway', 503: 'Service Unavailable'}

ZAEHLER = {'n': 0, 'fehler': 0}
try:
    PAUSE = max(0.0, float(os.environ.get('MS_PAUSE') or 0.1))
except Exception:
    PAUSE = 0.1
_LOCK = threading.Lock()
_LETZTE = {}
HOOK = None


def _zaehle(url):
    host = urllib.parse.urlsplit(url).netloc.lower()
    with _LOCK:
        ZAEHLER['n'] += 1
        jetzt = time.time()
        frei = _LETZTE.get(host, 0.0)
        start = max(jetzt, frei)
        _LETZTE[host] = start + PAUSE
    warte = start - jetzt
    if warte > 0:
        time.sleep(warte)


class ZaehlHandler(urllib.request.BaseHandler):
    handler_order = 100

    def http_request(self, req):
        _zaehle(req.full_url)
        return req

    https_request = http_request


def installieren():
    urllib.request.install_opener(urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=_ssl_context()), ZaehlHandler()))


class HTTPError(Exception):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


class CaseInsensitiveDict(dict):
    def __init__(self, data=None):
        super().__init__()
        self._keys = {}
        if data:
            for k, v in (data.items() if hasattr(data, 'items') else data):
                self[k] = v

    def __setitem__(self, key, value):
        lk = str(key).lower()
        old = self._keys.get(lk)
        if old is not None and old != key:
            super().__delitem__(old)
        self._keys[lk] = key
        super().__setitem__(key, value)

    def __getitem__(self, key):
        return super().__getitem__(self._keys[str(key).lower()])

    def __contains__(self, key):
        return str(key).lower() in self._keys

    def __delitem__(self, key):
        real = self._keys.pop(str(key).lower())
        super().__delitem__(real)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    def pop(self, key, *default):
        lk = str(key).lower()
        if lk in self._keys:
            real = self._keys.pop(lk)
            return super().pop(real)
        if default:
            return default[0]
        raise KeyError(key)

    def copy(self):
        return CaseInsensitiveDict(self)


def _decode(content, content_type=''):
    if not content:
        return ''
    charset = None
    m = re.search(r'charset=["\']?([\w\-]+)', content_type or '', re.I)
    if m:
        charset = m.group(1)
    if not charset:
        m = re.search(r'<meta[^>]+charset=["\']?([\w\-]+)', content[:2048].decode('ascii', 'ignore'), re.I)
        if m:
            charset = m.group(1)
    for enc in ([charset] if charset else []) + ['utf-8']:
        try:
            return content.decode(enc)
        except (LookupError, UnicodeDecodeError):
            continue
    return content.decode('cp1252', 'replace')


class Response:
    def __init__(self, status_code, headers, content, url, history=None, cookies=None, elapsed=0.0):
        self.status_code = int(status_code)
        self.headers = headers if isinstance(headers, CaseInsensitiveDict) else CaseInsensitiveDict(headers)
        self.content = content or b''
        self.url = url
        self.history = history or []
        self.cookies = cookies or {}
        self.elapsed = elapsed
        self.encoding = None
        self._text = None

    @property
    def text(self):
        if self._text is None:
            self._text = _decode(self.content, self.headers.get('Content-Type', ''))
        return self._text

    @property
    def ok(self):
        return self.status_code < 400

    @property
    def reason(self):
        return _STATUS_TEXT.get(self.status_code, '')

    def json(self, **kw):
        return _json.loads(self.text, **kw)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise HTTPError('HTTP Error %s for url: %s' % (self.status_code, self.url), self)

    def iter_content(self, chunk_size=8192):
        for i in range(0, len(self.content), chunk_size):
            yield self.content[i:i + chunk_size]

    def __repr__(self):
        return '<Response [%s]>' % self.status_code

    def __bool__(self):
        return self.ok


def _build_url(url, params=None):
    if not params:
        return url
    if isinstance(params, dict):
        params = [(k, v) for k, v in params.items() if v is not None]
    q = urllib.parse.urlencode(params, doseq=True)
    return url + ('&' if '?' in url else '?') + q if q else url


def _encode_body(data, json_obj, headers):
    if json_obj is not None:
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        return _json.dumps(json_obj, separators=(',', ':')).encode('utf-8')
    if data is None:
        return None
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    if isinstance(data, str):
        return data.encode('utf-8')
    if 'Content-Type' not in headers:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
    return urllib.parse.urlencode(data, doseq=True).encode('utf-8')


def _ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _unverified_context():
    c = ssl.create_default_context()
    c.check_hostname = False
    c.verify_mode = ssl.CERT_NONE
    return c


class Session:
    def __init__(self, headers=None, use_cf=False, cookies=None, **_ignored):
        self.headers = CaseInsensitiveDict(headers or {})
        self.jar = http.cookiejar.CookieJar()
        self.max_redirects = 20
        for k, v in dict(cookies or {}).items():
            self.jar.set_cookie(http.cookiejar.Cookie(0, k, v, None, False, '', False, False, '/', False, False,
                                                      None, False, None, None, {}))

    @property
    def cookies(self):
        return {c.name: c.value for c in self.jar}

    def _opener(self, allow_redirects, history, verify):
        class _Redirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                history.append(code)
                if not allow_redirects:
                    return None
                return super().redirect_request(req, fp, code, msg, headers, newurl)

        return urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar),
            urllib.request.HTTPSHandler(context=_ssl_context() if verify else _unverified_context()),
            _Redirect(), ZaehlHandler())

    def request(self, method, url, headers=None, params=None, data=None, json=None,
                timeout=_DEFAULT_TIMEOUT, allow_redirects=True, verify=True, no_verify=False, **_ignored):
        h = CaseInsensitiveDict(self.headers)
        if 'User-Agent' not in h:
            h['User-Agent'] = _DEFAULT_UA
        if 'Accept' not in h:
            h['Accept'] = '*/*'
        if 'Accept-Language' not in h:
            h['Accept-Language'] = _DEFAULT_LANG
        if headers:
            h.update({k: v for k, v in dict(headers).items() if v is not None})
        body = _encode_body(data, json, h)
        full = _build_url(url, params)
        hdr = dict(h)
        hdr.setdefault('Accept-Encoding', 'gzip, deflate')
        if 'br' in str(hdr.get('Accept-Encoding', '')):
            hdr['Accept-Encoding'] = 'gzip, deflate'
        history = []
        req = urllib.request.Request(full, data=body, method=method.upper(), headers=hdr)
        t0 = time.time()
        try:
            resp = self._opener(allow_redirects, history, not (no_verify or verify is False)).open(
                req, timeout=timeout or _DEFAULT_TIMEOUT)
        except urllib.error.HTTPError as e:
            resp = e
        except Exception:
            with _LOCK:
                ZAEHLER['fehler'] += 1
            raise
        raw = resp.read()
        hdrs = CaseInsensitiveDict()
        for k, v in resp.headers.items():
            hdrs[k] = v if k not in hdrs else hdrs[k] + ', ' + v
        enc = (hdrs.get('Content-Encoding') or '').lower()
        try:
            if 'gzip' in enc:
                raw = gzip.decompress(raw)
            elif 'deflate' in enc:
                try:
                    raw = zlib.decompress(raw)
                except zlib.error:
                    raw = zlib.decompress(raw, -zlib.MAX_WBITS)
        except Exception:
            pass
        status = getattr(resp, 'status', None) or getattr(resp, 'code', 200)
        if int(status) >= 400:
            with _LOCK:
                ZAEHLER['fehler'] += 1
        return Response(status, hdrs, raw, resp.geturl() if hasattr(resp, 'geturl') else full,
                        history, self.cookies, time.time() - t0)

    def get(self, url, **kw):
        return self.request('GET', url, **kw)

    def post(self, url, **kw):
        return self.request('POST', url, **kw)

    def head(self, url, **kw):
        return self.request('HEAD', url, **kw)

    def put(self, url, **kw):
        return self.request('PUT', url, **kw)

    def delete(self, url, **kw):
        return self.request('DELETE', url, **kw)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def request(method, url, **kw):
    kw.pop('use_cf', None)
    return Session().request(method, url, **kw)


def get(url, headers=None, params=None, timeout=_DEFAULT_TIMEOUT, **kw):
    return request('GET', url, headers=headers, params=params, timeout=timeout, **kw)


def post(url, data=None, json=None, headers=None, timeout=_DEFAULT_TIMEOUT, **kw):
    return request('POST', url, data=data, json=json, headers=headers, timeout=timeout, **kw)


def head(url, headers=None, timeout=_DEFAULT_TIMEOUT, **kw):
    return request('HEAD', url, headers=headers, timeout=timeout, **kw)
