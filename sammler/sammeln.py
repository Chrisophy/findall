# -*- coding: utf-8 -*-
# zusatzmetall | IT('s) Possible
# 2026.11.25
import argparse
import gzip
import hashlib
import html
import importlib.util
import inspect
import json
import logging
import os
import re
import subprocess
import sys
import time
import traceback
import unicodedata
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

HIER = os.path.dirname(os.path.abspath(__file__))
KODI = os.path.join(HIER, 'kodi')
if HIER not in sys.path:
    sys.path.insert(0, HIER)
import quellen as Q

_MARKUP = re.compile(r'\[/?(?:B|I|U|LIGHT|UPPERCASE|LOWERCASE|CAPITALIZE|COLOR[^\]]*|CR)\]', re.I)
_SUCHTITEL = re.compile(r'^\W*(?:suche|suchen|search|globale suche|suche nach)\b', re.I)
_SEITE = re.compile(r'(weiter|n[äa]chste|weitere\s+(?:ergebnisse|eintr)|mehr laden|next page|seite\s*\d)', re.I)
_JAHR = re.compile(r'\b(19[0-9]{2}|20[0-9]{2})\b')
_LIVE_SCHNITT = re.compile(r'\s+(?:–|—|\||·)\s+.*$')
_LIVE_NUMMER = re.compile(r'^\s*\d{1,5}(?:\s*\||\s+[–-])\s*')
_OHNE = {'search', 'do_search', 'clear_cache', 'nothing', 'settings', 'ms_settings', 'toggle'}
_ARTIKEL = re.compile(r'^(?:der|die|das|the|a|an|ein|eine|le|la|les|el)\s+')

GENRES = [
    ('Action', r'action'),
    ('Abenteuer', r'abenteuer|adventure'),
    ('Animation', r'animation|animiert|zeichentrick|cartoon'),
    ('Anime', r'\banime\b'),
    ('Biografie', r'biogra|biopic'),
    ('Dokumentation', r'doku|document|dokument'),
    ('Drama', r'drama'),
    ('Familie', r'famil'),
    ('Fantasy', r'fantasy|fantasie'),
    ('Geschichte', r'geschicht|histor'),
    ('Horror', r'horror|grusel'),
    ('Kinder', r'kinder|\bkids?\b|kika'),
    ('Komödie', r'kom[öo]d|comedy|lustig|humor'),
    ('Krieg', r'\bkrieg|\bwar\b'),
    ('Krimi', r'krimi|crime|verbrechen|detektiv'),
    ('Musik', r'musik|music|konzert'),
    ('Mystery', r'myster'),
    ('Reality', r'reality|doku-?soap'),
    ('Romantik', r'romant|romanz|romance|liebe'),
    ('Science-Fiction', r'sci-?fi|science|sci fi'),
    ('Sport', r'sport'),
    ('Thriller', r'thriller|spannung'),
    ('TV-Film', r'tv-?film|fernsehfilm'),
    ('Western', r'western'),
]
_GENRE_RE = [(g, re.compile(m, re.I)) for g, m in GENRES]

KIND_ORDNER, KIND_SPIEL, KIND_SUCHE, KIND_AKTION = 'ordner', 'spiel', 'suche', 'aktion'


def jetzt_utc():
    return datetime.now(timezone.utc)


def tag(d=None):
    return (d or jetzt_utc()).strftime('%Y%m%d')


def tag_zahl(s):
    try:
        return datetime.strptime(str(s), '%Y%m%d').replace(tzinfo=timezone.utc)
    except Exception:
        return None


def sauber(t):
    if t is None:
        return ''
    s = re.sub(r'\[CR\]', ' ', str(t), flags=re.I)
    s = html.unescape(_MARKUP.sub('', s))
    s = re.sub(r'\s+', ' ', s).strip()
    m = re.match(r'^\[\s*(.+?)\s*\]$', s)
    return m.group(1) if m else s


def falten(t):
    s = str(t or '').lower()
    for a, b in (('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')):
        s = s.replace(a, b)
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c))


def norm_titel(t):
    s = falten(sauber(t))
    s = re.sub(r'\[[^\]]*\]|\([^)]*\)', ' ', s).strip()
    s = _ARTIKEL.sub('', s)
    n = re.sub(r'[^a-z0-9]+', '', s)
    return n or re.sub(r'\s+', '', falten(sauber(t)))


def sortier(t):
    s = falten(sauber(t))
    return re.sub(r'^[^a-z0-9]+', '', s)


def jahr_von(v, titel=''):
    for x in (v, titel):
        if x in (None, ''):
            continue
        m = _JAHR.search(str(x))
        if m:
            return int(m.group(1))
    return 0


def genres_von(*werte):
    out = []
    for v in werte:
        if not v:
            continue
        teile = v if isinstance(v, (list, tuple)) else re.split(r'[,/&;|]+|\s+und\s+', str(v))
        for t in teile:
            t = sauber(t)
            if not t:
                continue
            for g, rx in _GENRE_RE:
                if rx.search(t) and g not in out:
                    out.append(g)
    return out


def dauer_von(v):
    try:
        d = int(float(v))
        return d if d > 0 else 0
    except Exception:
        return 0


def kuerzen(t, n):
    t = sauber(t)
    if len(t) <= n:
        return t
    s = t[:n].rsplit(' ', 1)[0].rstrip(',.;:- ')
    return s + ' …'


def bild(u):
    if not u or not isinstance(u, str):
        return ''
    u = u.split('|')[0].strip()
    if u.startswith('//'):
        u = 'https:' + u
    return u if u.startswith(('http://', 'https://')) else ''


def jsonfaehig(o):
    try:
        return json.loads(json.dumps(o, default=lambda x: str(x), ensure_ascii=False))
    except Exception:
        return None


def item_art(it):
    nf = str(it.get('next_func') or '').strip()
    titel = sauber(it.get('title') or it.get('label') or '')
    if nf in _OHNE:
        return KIND_SUCHE if nf in ('search', 'do_search') else KIND_AKTION
    if nf == 'get_hosters':
        return KIND_SPIEL
    if 'next_func' not in it and 'is_playable' not in it:
        return KIND_SPIEL
    if not nf and it.get('is_playable'):
        return KIND_SPIEL
    if not it.get('is_playable') and _SUCHTITEL.match(titel):
        return KIND_SUCHE
    return KIND_ORDNER


def _zahl(v):
    try:
        return int(v or 0)
    except Exception:
        return 0


def kwargs_fuer(fn, item):
    item = item or {}
    params = {}
    for k, v in item.items():
        if isinstance(v, (str, int, float)) and not isinstance(v, bool) and k != 'plot':
            params[k] = str(v)
    if isinstance(item.get('params'), dict):
        params.update(item['params'])
    verf = {
        'url': '' if item.get('url') is None else str(item.get('url')),
        'params': params,
        'title': sauber(item.get('title') or ''),
        'year': item.get('year') or '',
        'season': _zahl(item.get('season')),
        'episode': _zahl(item.get('episode')),
        'imdb': item.get('imdb') or '',
        'tmdb': item.get('tmdb') or '',
        'query': '',
    }
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return verf
    var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
    return {k: v for k, v in verf.items() if var_kw or k in sig.parameters}


def schluessel(r):
    return '%s\x00%s' % (r.get('u', ''), json.dumps(r.get('pa') or {}, sort_keys=True, ensure_ascii=False))


def lies_gz(pfad, standard=None):
    try:
        with gzip.open(pfad, 'rb') as f:
            return json.loads(f.read().decode('utf-8'))
    except Exception:
        return standard


def schreib_gz(pfad, daten):
    roh = json.dumps(daten, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    gz = gzip.compress(roh, 9, mtime=0)
    tmp = pfad + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(gz)
    os.replace(tmp, pfad)
    return hashlib.sha1(gz).hexdigest()[:12], len(gz)


def schreib_json(pfad, daten, kompakt=True):
    tmp = pfad + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        if kompakt:
            json.dump(daten, f, ensure_ascii=False, separators=(',', ':'))
        else:
            json.dump(daten, f, ensure_ascii=False, indent=1)
    os.replace(tmp, pfad)


def statische_meta(pfad):
    meta = {}
    try:
        with open(pfad, encoding='utf-8', errors='replace') as f:
            kopf = f.read(20000)
        for k in ('SITE_ID', 'SITE_NAME', 'SITE_DOMAIN'):
            m = re.search(r'^%s\s*=\s*[\'"]([^\'"]+)[\'"]' % k, kopf, re.M)
            if m:
                meta[k] = m.group(1)
    except Exception:
        pass
    return meta


class Lauf:
    def __init__(self, mod, cfg, allg, ende, aus, stem):
        self.mod, self.cfg, self.allg, self.ende, self.aus, self.stem = mod, cfg, allg, ende, aus, stem
        self.filme, self.serien, self.live = {}, {}, {}
        self.aufrufe = 0
        self.teil = False
        self.fertig = False
        self.fehler = []
        self.t0 = time.time()
        self._wurzel = None
        self._geschrieben = time.time()
        self.max_aufrufe = int(cfg.get('max_aufrufe') or allg['max_aufrufe'])
        self.plot_laenge = int(allg.get('plot_laenge') or 400)

    def zeit_um(self):
        return time.time() >= self.ende

    def rufe(self, fname, item=None, args=None):
        fn = getattr(self.mod, fname, None)
        if not callable(fn):
            raise RuntimeError('Funktion fehlt: %s' % fname)
        self.aufrufe += 1
        res = fn(*args) if args is not None else fn(**kwargs_fuer(fn, item))
        if res is None:
            return []
        if isinstance(res, dict):
            res = res.get('items') or []
        try:
            return [x for x in list(res) if isinstance(x, dict)]
        except TypeError:
            return []

    def wurzel(self):
        if self._wurzel is None:
            try:
                self._wurzel = self.rufe('load', {'url': '', 'params': {}})
            except Exception as e:
                self._wurzel = []
                self.fehler.append('load(): %s' % self._kurz(e))
        return self._wurzel

    def pick(self, name):
        ziel = norm_titel(name)
        kand = [(norm_titel(it.get('title') or ''), it) for it in self.wurzel() if item_art(it) == KIND_ORDNER]
        for pruef in (lambda n: n == ziel, lambda n: n.startswith(ziel), lambda n: ziel in n):
            for n, it in kand:
                if n and pruef(n):
                    return it
        return None

    def _kurz(self, e):
        return ('%s: %s' % (type(e).__name__, e))[:240]

    def anzahl(self):
        return len(self.filme) + len(self.serien) + len(self.live)

    def start(self, st):
        vorher = self.anzahl()
        try:
            self._start(st)
        except Exception as e:
            self.fehler.append('Start %s: %s' % (st.get('pick') or st.get('func') or st.get('roh'), self._kurz(e)))
        if self.anzahl() == vorher and isinstance(st.get('alt'), dict) and not self.zeit_um():
            alt = dict(st)
            alt.pop('alt', None)
            alt.pop('args', None)
            alt.update(st['alt'])
            try:
                self._start(alt)
            except Exception as e:
                self.fehler.append('Ersatzstart %s: %s' % (alt.get('pick') or alt.get('func'), self._kurz(e)))

    def _start(self, st):
        if st.get('roh') == 'gez':
            return self.roh_gez(st)
        wurzel = None
        if st.get('pick'):
            f = self.pick(st['pick'])
            if f is not None:
                wurzel = ((f.get('next_func') or 'load').strip(), f, None, sauber(f.get('title')))
        if wurzel is None and st.get('func'):
            item = {'url': st.get('url', ''), 'params': dict(st.get('params') or {})}
            wurzel = (st['func'], item, st.get('args'), '')
        if wurzel is None:
            raise RuntimeError('Startpunkt nicht gefunden')
        self.laufen(st, *wurzel)

    def laufen(self, st, fname, item, args, start_titel):
        art = st.get('art') or 'film'
        max_tiefe = int(st.get('tiefe') or self.allg['tiefe'])
        max_seiten = int(st.get('max_seiten') or self.allg['max_seiten'])
        genre_tiefe = int(st.get('genre_tiefe') or 0)
        serien_tiefe = int(st.get('serien_tiefe') or 0)
        nur = set(st.get('nur') or [])
        fix = genres_von(st.get('genre'))
        alle = bool(st.get('alle_abspielbar'))
        gesehen = set()
        schlange = deque([(fname, item, args, 0, list(fix), 0, '')])
        while schlange:
            if self.zeit_um() or self.aufrufe >= self.max_aufrufe:
                self.teil = True
                return
            fname, item, args, tiefe, genres, seiten, gruppe = schlange.popleft()
            if time.time() - self._geschrieben > 20:
                self.schreiben()
            k = (fname, str((item or {}).get('url')), json.dumps((item or {}).get('params') or {}, sort_keys=True, default=str), json.dumps(args))
            if k in gesehen:
                continue
            gesehen.add(k)
            try:
                res = self.rufe(fname, item, args)
            except Exception as e:
                self.fehler.append('%s(%s): %s' % (fname, str((item or {}).get('url'))[:60], self._kurz(e)))
                continue
            for it in res:
                titel = sauber(it.get('title') or it.get('label') or '')
                if not titel:
                    continue
                nf = str(it.get('next_func') or '').strip()
                kind = item_art(it)
                mt = str(it.get('mediatype') or '').lower()
                if kind in (KIND_SUCHE, KIND_AKTION):
                    continue
                if kind == KIND_SPIEL:
                    if art == 'live':
                        self.merke_live(it, titel, gruppe)
                    elif art in ('film', 'mix') and (alle or mt in ('movie', '')):
                        self.merke(self.filme, it, titel, genres, 'get_hosters' if not nf else nf)
                    continue
                if art != 'live' and (mt == 'tvshow' or (art == 'serie' and serien_tiefe and tiefe + 1 == serien_tiefe)):
                    if art in ('serie', 'mix'):
                        self.merke(self.serien, it, titel, genres, nf or 'load')
                    continue
                if mt in ('season', 'episode'):
                    continue
                if _SEITE.search(titel) and nf == fname:
                    if seiten + 1 <= max_seiten:
                        schlange.append((nf, it, None, tiefe, genres, seiten + 1, gruppe))
                    continue
                if nur and nf not in nur:
                    continue
                if tiefe + 1 >= max_tiefe:
                    continue
                g2 = list(genres)
                if genre_tiefe and tiefe + 1 == genre_tiefe:
                    for g in genres_von(re.sub(r'\s*\(\d+\)\s*$', '', titel)):
                        if g not in g2:
                            g2.append(g)
                schlange.append((nf or 'load', it, None, tiefe + 1, g2, 0, gruppe or (titel if art == 'live' else '')))

    def _direkt(self, it):
        if self.cfg.get('direkt') == 'kmt':
            p = it.get('params') if isinstance(it.get('params'), dict) else {}
            for k in ('hd', 'sd', 'low'):
                u = p.get(k) or ''
                if isinstance(u, str) and u.startswith('http'):
                    return u
        return ''

    def merke(self, ziel, it, titel, genres, nf):
        pa = it.get('params') if isinstance(it.get('params'), dict) else None
        j = jahr_von(it.get('year'), '')
        m = re.search(r'\s*\((19\d{2}|20\d{2})\)\s*$', titel)
        if m and titel[:m.start()].strip():
            j = j or int(m.group(1))
            titel = titel[:m.start()].strip()
        r = {'t': titel, 'u': '' if it.get('url') is None else str(it.get('url')), 'nf': nf}
        if pa:
            pa = jsonfaehig(pa)
            if pa:
                r['pa'] = pa
        if j:
            r['j'] = j
        p = kuerzen(it.get('plot') or '', self.plot_laenge)
        if p:
            r['p'] = p
        b = bild(it.get('poster')) or bild(it.get('thumb')) or bild(it.get('icon'))
        if b:
            r['b'] = b
        f = bild(it.get('fanart'))
        if f and f != b:
            r['f'] = f
        g = list(genres)
        for x in genres_von(it.get('genre'), it.get('genres')):
            if x not in g:
                g.append(x)
        if g:
            r['g'] = g
        d = dauer_von(it.get('duration'))
        if d:
            r['d'] = d
        dl = self._direkt(it)
        if dl:
            r['dl'] = dl
        k = schluessel(r)
        alt = ziel.get(k)
        if alt is None:
            ziel[k] = r
        elif r.get('g'):
            for x in r['g']:
                if x not in alt.setdefault('g', []):
                    alt['g'].append(x)

    def merke_live(self, it, titel, gruppe):
        t = _LIVE_NUMMER.sub('', titel).strip() or titel
        t = _LIVE_SCHNITT.sub('', t).strip() or t
        r = {'t': t, 'u': '' if it.get('url') is None else str(it.get('url')), 'nf': str(it.get('next_func') or 'get_hosters')}
        pa = it.get('params') if isinstance(it.get('params'), dict) else None
        if pa:
            pa = jsonfaehig(pa)
            if pa:
                r['pa'] = pa
        b = bild(it.get('poster')) or bild(it.get('icon')) or bild(it.get('thumb'))
        if b:
            r['b'] = b
        if gruppe:
            r['gr'] = gruppe
        self.live.setdefault(schluessel(r), r)

    def roh_gez(self, st):
        daten = None
        f = getattr(self.mod, '_download_movies_json', None)
        if callable(f):
            daten = f()
        if not daten and callable(getattr(self.mod, '_get_movies', None)):
            daten = self.mod._get_movies()
        self.aufrufe += 1
        for m in daten or []:
            if not isinstance(m, dict):
                continue
            titel = sauber(m.get('title'))
            vu = str(m.get('video_url') or '').strip()
            if not titel or not vu.startswith('http'):
                continue
            jahr = str(m.get('year') or '')
            if jahr.upper() == 'LIVE':
                r = {'t': titel, 'u': '%s||%s' % (m.get('title'), vu), 'nf': 'get_hosters', 'dl': vu}
                b = bild(m.get('thumb'))
                if b:
                    r['b'] = b
                self.live.setdefault(schluessel(r), r)
                continue
            r = {'t': titel, 'u': '%s||%s' % (m.get('title'), vu), 'nf': 'get_hosters', 'dl': vu}
            j = jahr_von(jahr)
            if j:
                r['j'] = j
            p = kuerzen(m.get('plot') or '', self.plot_laenge)
            if p:
                r['p'] = p
            b = bild(m.get('thumb'))
            if b:
                r['b'] = b
            g = genres_von(m.get('genres_list'))
            if g:
                r['g'] = g
            self.filme.setdefault(schluessel(r), r)

    def schreiben(self):
        self._geschrieben = time.time()
        try:
            from resources.lib import multiquest as MQ
            anfragen, http_fehler = MQ.ZAEHLER['n'], MQ.ZAEHLER['fehler']
        except Exception:
            anfragen = http_fehler = 0
        schreib_json(self.aus, {
            'filme': list(self.filme.values()), 'serien': list(self.serien.values()), 'live': list(self.live.values()),
            'aufrufe': self.aufrufe, 'anfragen': anfragen, 'http_fehler': http_fehler, 'fehler': self.fehler[:30],
            'teil': self.teil, 'fertig': self.fertig, 'sek': int(time.time() - self.t0),
            'sid': getattr(self.mod, 'SITE_ID', ''), 'name': getattr(self.mod, 'SITE_NAME', ''),
            'domain': getattr(self.mod, 'SITE_DOMAIN', ''),
        })


def lade_modul(pfad):
    stem = os.path.splitext(os.path.basename(pfad))[0]
    spec = importlib.util.spec_from_file_location(stem, pfad)
    mod = importlib.util.module_from_spec(spec)
    vorher = sys.modules.get(stem)
    sys.modules[stem] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        if vorher is None:
            sys.modules.pop(stem, None)
        else:
            sys.modules[stem] = vorher
    sys.modules['ms_scraper_' + stem] = mod
    return mod


def quelle_cfg(datei):
    for q in Q.QUELLEN:
        if q['datei'] == datei:
            return q
    raise SystemExit('Unbekannte Quelle: %s' % datei)


def arbeiter(a):
    if KODI not in sys.path:
        sys.path.insert(0, KODI)
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr, format='%(levelname)s %(name)s: %(message)s')
    cfg = quelle_cfg(a.arbeiter)
    allg = dict(Q.ALLGEMEIN)
    ende = time.time() + float(a.budget)
    stem = os.path.splitext(os.path.basename(a.pfad))[0]
    from resources.lib import multiquest as MQ
    MQ.installieren()
    lauf = Lauf(None, cfg, allg, ende, a.aus, stem)
    try:
        lauf.mod = lade_modul(a.pfad)
    except BaseException as e:
        lauf.fehler.append('Import: %s' % lauf._kurz(e))
        traceback.print_exc()
        lauf.mod = type('Leer', (), {})()
        lauf.fertig = True
        lauf.schreiben()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)
    for st in cfg.get('starts') or []:
        if lauf.zeit_um():
            lauf.teil = True
            break
        lauf.start(st)
        lauf.schreiben()
    lauf.fertig = True
    lauf.schreiben()
    print('fertig: %d Filme, %d Serien, %d Live, %d Aufrufe' % (len(lauf.filme), len(lauf.serien), len(lauf.live), lauf.aufrufe))
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


def finde_datei(datei, ordner):
    treffer = []
    for o in ordner:
        if not o or not os.path.isdir(o):
            continue
        for wurzel, dirs, files in os.walk(o):
            dirs[:] = [d for d in dirs if not d.startswith(('.', '_alt', '__pycache__'))]
            if datei + '.py' in files:
                treffer.append((wurzel.count(os.sep), len(treffer), os.path.join(wurzel, datei + '.py')))
        if treffer:
            break
    return min(treffer)[2] if treffer else ''


def starte(q, pfad, a, allg, tmp):
    datei = q['datei']
    aus = os.path.join(tmp, datei + '.json')
    logdatei = os.path.join(tmp, datei + '.log')
    ergebnis = {'datei': datei, 'pfad': pfad, 'aus': aus, 'log': logdatei, 'zeitlimit': False, 'code': None}
    if not pfad:
        return ergebnis
    budget = int(q.get('budget') or allg['budget'])
    if a.budget_max:
        budget = min(budget, int(a.budget_max))
    profil = os.path.abspath(os.path.join(a.profil, datei))
    os.makedirs(profil, exist_ok=True)
    env = dict(os.environ)
    env['MS_PROFIL'] = profil
    env['MS_EINSTELLUNGEN'] = json.dumps(q.get('einstellungen') or {})
    env['MS_KOPFZEILEN'] = json.dumps(q.get('kopfzeilen') or {})
    env['MS_PAUSE'] = str(q.get('pause', allg.get('pause', 0.1)))
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    proxy = (os.environ.get('KATALOG_PROXY') or '').strip()
    if proxy and q.get('proxy', True):
        for k in ('HTTPS_PROXY', 'HTTP_PROXY', 'https_proxy', 'http_proxy'):
            env[k] = proxy
    cmd = [sys.executable, '-u', os.path.abspath(__file__), '--arbeiter', datei, '--pfad', os.path.abspath(pfad),
           '--aus', aus, '--budget', str(budget)]
    t0 = time.time()
    with open(logdatei, 'wb') as log:
        p = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, cwd=profil)
        try:
            ergebnis['code'] = p.wait(timeout=budget + int(os.environ.get('KATALOG_NACHLAUF') or 120 + budget // 10))
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
            ergebnis['zeitlimit'] = True
    print('%-16s beendet nach %ds (Code %s)%s' % (datei, time.time() - t0, ergebnis['code'],
                                                  ', Zeitlimit' if ergebnis['zeitlimit'] else ''))
    sys.stdout.flush()
    return ergebnis


def log_ende(pfad, n=6):
    try:
        with open(pfad, encoding='utf-8', errors='replace') as f:
            zeilen = [z.rstrip() for z in f if z.strip()]
        return ' | '.join(z[:200] for z in zeilen[-n:])
    except Exception:
        return ''


def kombinieren(neu, alt, grenze):
    schl = {schluessel(r) for r in neu}
    for r in alt or []:
        if schluessel(r) in schl:
            continue
        d = tag_zahl(r.get('z'))
        if d is not None and d >= grenze:
            neu.append(r)
    return neu


def auswerten(q, erg, alt_dir, aus_dir, heute, allg):
    datei = q['datei']
    meta = statische_meta(erg['pfad']) if erg['pfad'] else {}
    altpfad = os.path.join(alt_dir or '', 'quellen', datei + '.json.gz')
    alt = lies_gz(altpfad, None) if alt_dir else None
    neu = None
    if erg['pfad'] and os.path.exists(erg['aus']):
        try:
            with open(erg['aus'], encoding='utf-8') as f:
                neu = json.load(f)
        except Exception:
            neu = None
    grenze = heute - timedelta(days=int(allg.get('alt_tage') or 14))
    heute_s = tag(heute)
    sid = (neu or {}).get('sid') or meta.get('SITE_ID') or (alt or {}).get('sid') or datei
    name = (neu or {}).get('name') or meta.get('SITE_NAME') or (alt or {}).get('name') or datei
    domain = (neu or {}).get('domain') or meta.get('SITE_DOMAIN') or (alt or {}).get('domain') or ''
    bericht = {'n': name, 'f': datei, 'd': domain, 'prio': q.get('prio', 99), 'status': 'fehler', 'hinweis': '',
               'anfragen': (neu or {}).get('anfragen', 0), 'http_fehler': (neu or {}).get('http_fehler', 0),
               'sek': (neu or {}).get('sek', 0), 'aufrufe': (neu or {}).get('aufrufe', 0)}
    hinweise = []
    if not erg['pfad']:
        hinweise.append('Scraper-Datei nicht gefunden')
    if erg['zeitlimit']:
        hinweise.append('Zeitlimit, Lauf abgebrochen')
    if neu and neu.get('teil'):
        hinweise.append('Zeit- oder Aufruflimit erreicht')
    if neu and neu.get('fehler'):
        hinweise.append('; '.join(neu['fehler'][:3]))
    if erg['pfad'] and not neu:
        hinweise.append(log_ende(erg['log']) or 'kein Ergebnis')
    if neu and not sum(len(neu.get(k) or []) for k in ('filme', 'serien', 'live')):
        hinweise.append('keine Einträge erhalten (%d Anfragen, %d davon fehlerhaft)' % (neu.get('anfragen', 0), neu.get('http_fehler', 0)))
    sig = hashlib.sha1(json.dumps(q, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()[:10]
    alt_gleich = alt if (alt and alt.get('sig') == sig) else None
    daten = {'sid': sid, 'name': name, 'domain': domain, 'datei': datei, 'stand': heute_s, 'sig': sig,
             'filme': [], 'serien': [], 'live': []}
    gesamt_neu = sum(len((neu or {}).get(k) or []) for k in ('filme', 'serien', 'live'))
    if neu and gesamt_neu:
        teil = bool(neu.get('teil')) or not neu.get('fertig') or erg['zeitlimit']
        status = 'teil' if teil else 'ok'
        for k in ('filme', 'serien', 'live'):
            liste = list(neu.get(k) or [])
            for r in liste:
                r['z'] = heute_s
            alt_liste = (alt_gleich or {}).get(k) or []
            einbruch = bool(alt_liste) and (not liste or (len(alt_liste) >= 10 and len(liste) < len(alt_liste) * 0.5))
            if teil or einbruch:
                if einbruch and not teil:
                    hinweise.append('%s: nur %d statt %d, alte Einträge bleiben' % (k, len(liste), len(alt_liste)))
                    status = 'teil'
                liste = kombinieren(liste, alt_liste, grenze)
            daten[k] = liste
    elif alt:
        status = 'alt'
        for k in ('filme', 'serien', 'live'):
            daten[k] = kombinieren([], alt.get(k) or [], grenze)
        daten['stand'] = alt.get('stand') or ''
        daten['sig'] = alt.get('sig') or ''
        hinweise.insert(0, 'Abruf fehlgeschlagen, Daten vom %s' % (daten['stand'] or '?'))
    else:
        status = 'fehler'
    bericht['status'] = status
    bericht['hinweis'] = ' | '.join(h for h in hinweise if h)[:500]
    bericht['stand'] = daten['stand'] if status != 'fehler' else ''
    for k in ('filme', 'serien', 'live'):
        bericht[k] = len(daten[k])
    if status != 'fehler':
        schreib_gz(os.path.join(aus_dir, 'quellen', datei + '.json.gz'), daten)
    return sid, bericht, daten


def gruppieren(eintraege, mit_jahr=True):
    gruppen = {}
    reihen = []
    for prio, sid, r in sorted(eintraege, key=lambda x: x[0]):
        n = norm_titel(r.get('t'))
        cl = gruppen.get(n)
        if cl is None:
            cl = gruppen[n] = []
        y = (r.get('j') or 0) if mit_jahr else 0
        ziel = None
        if y:
            ziel = next((c for c in cl if c['j'] and abs(c['j'] - y) <= 1), None)
            if ziel is None:
                ziel = next((c for c in cl if not c['j']), None)
                if ziel is not None:
                    ziel['j'] = y
        elif len(cl) == 1:
            ziel = cl[0]
        else:
            ziel = next((c for c in cl if not c['j']), None)
        if ziel is None:
            ziel = {'n': n, 'j': y, 'r': []}
            cl.append(ziel)
            reihen.append(ziel)
        if any(s == sid for _, s, _ in ziel['r']):
            continue
        ziel['r'].append((prio, sid, r))
    return reihen


def eintrag_bauen(c, ids, erstmals, neu_tag, live=False):
    recs = c['r']
    erste = recs[0][2]
    e = {'t': erste['t']}
    basis = ('live|%s' % c['n']) if live else ('%s|%s' % (c['n'], c['j'] or ''))
    i = hashlib.sha1(basis.encode('utf-8')).hexdigest()[:10]
    z = 1
    while i in ids:
        z += 1
        i = hashlib.sha1(('%s|%d' % (basis, z)).encode('utf-8')).hexdigest()[:10]
    ids.add(i)
    e['i'] = i
    if not live:
        for feld in ('j', 'p', 'b', 'f', 'd'):
            for _, _, r in recs:
                if r.get(feld):
                    e[feld] = r[feld]
                    break
        g = []
        for _, _, r in recs:
            for x in r.get('g') or []:
                if x not in g:
                    g.append(x)
        if g:
            e['g'] = g
        if i not in erstmals:
            erstmals[i] = neu_tag
        e['n'] = erstmals[i]
    else:
        for _, _, r in recs:
            if r.get('b'):
                e['b'] = r['b']
                break
        for _, _, r in recs:
            if r.get('gr'):
                e['gr'] = r['gr']
                break
    e['q'] = [[sid, r.get('u', ''), r.get('pa') or None, r.get('dl') or '', '' if r.get('nf') == 'get_hosters' else r.get('nf', '')]
              for _, sid, r in recs]
    return e


def zusammenfuehren(alle, alt_dir, aus_dir, heute, erster):
    erstmals_alt = lies_gz(os.path.join(alt_dir or '', 'erstmals.json.gz'), None) if alt_dir else None
    erstmals = dict(erstmals_alt or {})
    neu_tag = tag(heute) if erstmals_alt is not None and not erster else '0'
    ids = set()
    out = {}
    for art, live in (('filme', False), ('serien', False), ('live', True)):
        ein = [(prio, sid, r) for sid, prio, daten in alle for r in daten.get(art) or []]
        reihen = gruppieren(ein, mit_jahr=not live)
        liste = [eintrag_bauen(c, ids, erstmals, neu_tag, live) for c in reihen]
        liste.sort(key=lambda x: (sortier(x['t']), x.get('j') or 0))
        out[art] = liste
    erstmals = {k: v for k, v in erstmals.items() if k in ids}
    schreib_gz(os.path.join(aus_dir, 'erstmals.json.gz'), erstmals)
    return out


def zusammenfassung(index, pfad):
    zeilen = ['## Freikatalog %s' % index['stand'], '',
              '| Quelle | Status | Filme | Serien | Live | Anfragen | Sek. | Hinweis |', '|---|---|---|---|---|---|---|---|']
    for sid, b in sorted(index['quellen'].items(), key=lambda x: x[1]['prio']):
        zeilen.append('| %s | %s | %d | %d | %d | %d | %d | %s |' % (
            b['n'], b['status'], b['filme'], b['serien'], b['live'], b['anfragen'], b['sek'],
            (b['hinweis'] or '').replace('|', '/')[:160]))
    z = index['zahlen']
    zeilen += ['', 'Gesamt: %d Filme, %d Serien, %d Live-Sender' % (z['filme'], z['serien'], z['live'])]
    text = '\n'.join(zeilen) + '\n'
    print(text)
    if pfad:
        try:
            with open(pfad, 'a', encoding='utf-8') as f:
                f.write(text)
        except Exception:
            pass


def haupt(a):
    allg = dict(Q.ALLGEMEIN)
    heute = jetzt_utc()
    aus_dir = os.path.abspath(a.aus)
    alt_dir = os.path.abspath(a.alt) if a.alt and os.path.isdir(a.alt) else ''
    os.makedirs(os.path.join(aus_dir, 'quellen'), exist_ok=True)
    tmp = os.path.abspath(a.arbeit)
    os.makedirs(tmp, exist_ok=True)
    nur = set(x.strip() for x in (a.nur or '').split(',') if x.strip())
    plan = [q for q in Q.QUELLEN if not nur or q['datei'] in nur]
    jobs = [(q, finde_datei(q['datei'], a.scraper)) for q in plan]
    for q, p in jobs:
        print('%-16s %s' % (q['datei'], p or '(nicht gefunden)'))
    sys.stdout.flush()
    parallel = max(1, int(a.parallel or allg.get('parallel') or 4))
    with ThreadPoolExecutor(max_workers=parallel) as ex:
        ergebnisse = list(ex.map(lambda j: starte(j[0], j[1], a, allg, tmp), jobs))
    berichte, alle = {}, []
    for (q, _), erg in zip(jobs, ergebnisse):
        sid, bericht, daten = auswerten(q, erg, alt_dir, aus_dir, heute, allg)
        berichte[sid] = bericht
        if bericht['status'] != 'fehler':
            alle.append((sid, q.get('prio', 99), daten))
    alt_index = {}
    if alt_dir:
        try:
            with open(os.path.join(alt_dir, 'index.json'), encoding='utf-8') as f:
                alt_index = json.load(f)
        except Exception:
            alt_index = {}
    erster = not alt_index
    out = zusammenfuehren(alle, alt_dir, aus_dir, heute, erster)
    index = {'v': 1, 'stand': heute.strftime('%Y-%m-%dT%H:%M:%SZ'), 'datum': tag(heute),
             'seit': alt_index.get('seit') or tag(heute), 'quellen': berichte, 'dateien': {},
             'zahlen': {k: len(v) for k, v in out.items()}}
    for k, v in out.items():
        sha, groesse = schreib_gz(os.path.join(aus_dir, k + '.json.gz'), v)
        index['dateien'][k] = {'sha': sha, 'n': len(v), 'bytes': groesse}
    schreib_json(os.path.join(aus_dir, 'index.json'), index, kompakt=False)
    zusammenfassung(index, os.environ.get('GITHUB_STEP_SUMMARY'))
    if not any(index['zahlen'].values()):
        print('Kein einziger Eintrag - nichts veröffentlichen.')
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arbeiter', default='')
    ap.add_argument('--pfad', default='')
    ap.add_argument('--budget', default='900')
    ap.add_argument('--scraper', nargs='*', default=['scraper', '_scraper'])
    ap.add_argument('--alt', default='_alt/katalog')
    ap.add_argument('--aus', default='_neu/katalog')
    ap.add_argument('--profil', default='.profil')
    ap.add_argument('--nur', default='')
    ap.add_argument('--parallel', default='')
    ap.add_argument('--budget-max', dest='budget_max', default='')
    ap.add_argument('--arbeit', default='_arbeit')
    a = ap.parse_args()
    if a.arbeiter:
        a.aus = os.path.abspath(a.aus)
        return arbeiter(a)
    sys.exit(haupt(a))


if __name__ == '__main__':
    main()
