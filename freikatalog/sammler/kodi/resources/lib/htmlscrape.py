# -*- coding: utf-8 -*-
# zusatzmetall | IT('s) Possible
# 2026.11.25
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

_VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
_SKIP = {'script', 'style', 'noscript', 'template', 'svg'}
_IMPLIED = {
    'li': {'ul', 'ol'}, 'dt': {'dl'}, 'dd': {'dl'}, 'tr': {'table'}, 'td': {'tr', 'table'}, 'th': {'tr', 'table'},
    'option': {'select'}, 'p': {'div', 'section', 'article', 'body', 'li', 'td'},
}
_URL_ATTRS = {'href', 'src', 'data-src', 'data-lazy-src', 'data-original', 'data-lazy', 'data-url', 'data-link',
              'data-href', 'data-embed', 'data-player-url', 'srcset', 'data-srcset', 'bg', 'content', 'poster', 'action'}
_PLACEHOLDER = re.compile(r'placeholder|blank\.|spacer|1x1|loading|lazy\.(?:gif|png)|pixel|transparent|noimage|no-image', re.I)
MAX_HTML = 3_000_000


class Node:
    __slots__ = ('tag', 'attrs', 'children', 'parent')

    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.children, self.parent = tag, attrs or {}, [], parent

    @property
    def classes(self):
        return (self.attrs.get('class') or '').split()

    def elements(self):
        return [c for c in self.children if isinstance(c, Node)]

    def iter(self):
        stack = list(reversed(self.elements()))
        while stack:
            n = stack.pop()
            yield n
            stack.extend(reversed(n.elements()))

    def text(self):
        parts = []

        def walk(n):
            for c in n.children:
                if isinstance(c, str):
                    parts.append(c)
                else:
                    if c.tag in ('br', 'p', 'div', 'li'):
                        parts.append(' ')
                    walk(c)
        walk(self)
        return re.sub(r'\s+', ' ', ''.join(parts)).strip()


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('#root')
        self.stack = [self.root]
        self.skip_tag = None
        self.skip_depth = 0

    def _open(self, tag, attrs, void):
        if self.skip_tag:
            if tag == self.skip_tag:
                self.skip_depth += 1
            return
        if tag in _SKIP:
            if not void:
                self.skip_tag, self.skip_depth = tag, 1
            return
        bound = _IMPLIED.get(tag)
        if bound:
            for i in range(len(self.stack) - 1, 0, -1):
                t = self.stack[i].tag
                if t == tag:
                    del self.stack[i:]
                    break
                if t in bound:
                    break
        node = Node(tag, {k: (v if v is not None else '') for k, v in attrs}, self.stack[-1])
        self.stack[-1].children.append(node)
        if not void and tag not in _VOID:
            self.stack.append(node)

    def handle_starttag(self, tag, attrs):
        self._open(tag, attrs, False)

    def handle_startendtag(self, tag, attrs):
        self._open(tag, attrs, True)

    def handle_endtag(self, tag):
        if self.skip_tag:
            if tag == self.skip_tag:
                self.skip_depth -= 1
                if self.skip_depth <= 0:
                    self.skip_tag = None
            return
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if not self.skip_tag and data:
            self.stack[-1].children.append(data)


def parse(html):
    b = _Builder()
    try:
        b.feed((html or '')[:MAX_HTML])
        b.close()
    except Exception:
        pass
    return b.root


def _tokens(sel):
    out, cur, depth, comb, pend = [], '', 0, ' ', None
    for ch in sel.strip():
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth = max(0, depth - 1)
        if depth == 0 and (ch.isspace() or ch == '>'):
            if cur:
                out.append((comb, cur))
                cur, comb = '', ' '
            if ch == '>':
                comb = '>'
            continue
        cur += ch
    if cur:
        out.append((comb, cur))
    return out


_COMPOUND = re.compile(r'''\.(?P<cls>[\w\-]+)|\#(?P<id>[\w\-]+)|\[(?P<attr>[^\]]+)\]|:contains\((?P<contains>[^)]*)\)''')


def _compound(text):
    m = re.match(r'[A-Za-z][\w\-]*|\*', text)
    tag = m.group(0).lower() if m else ''
    rest = text[m.end():] if m else text
    c = {'tag': '' if tag == '*' else tag, 'cls': [], 'id': '', 'attrs': [], 'contains': []}
    for mm in _COMPOUND.finditer(rest):
        if mm.group('cls'):
            c['cls'].append(mm.group('cls'))
        elif mm.group('id'):
            c['id'] = mm.group('id')
        elif mm.group('attr'):
            a = mm.group('attr').strip()
            m2 = re.match(r'([\w:\-]+)\s*(\*=|\^=|\$=|=)?\s*(.*)$', a)
            if m2:
                c['attrs'].append((m2.group(1), m2.group(2) or '', m2.group(3).strip('\'"')))
        elif mm.group('contains') is not None:
            c['contains'].append(mm.group('contains').strip('\'"').lower())
    return c


def compile_selector(sel):
    return [(comb, _compound(tok)) for comb, tok in _tokens(sel)]


def _match_one(n, c):
    if c['tag'] and n.tag != c['tag']:
        return False
    if c['id'] and n.attrs.get('id') != c['id']:
        return False
    if c['cls']:
        have = n.classes
        if any(k not in have for k in c['cls']):
            return False
    for name, op, val in c['attrs']:
        v = n.attrs.get(name)
        if v is None:
            return False
        if op == '=' and v != val:
            return False
        if op == '*=' and val not in v:
            return False
        if op == '^=' and not v.startswith(val):
            return False
        if op == '$=' and not v.endswith(val):
            return False
    if c['contains']:
        t = n.text().lower()
        if any(s not in t for s in c['contains']):
            return False
    return True


def _match(n, steps, i):
    if not _match_one(n, steps[i][1]):
        return False
    if i == 0:
        return True
    p = n.parent
    if steps[i][0] == '>':
        return p is not None and p.tag != '#root' and _match(p, steps, i - 1)
    while p is not None and p.tag != '#root':
        if _match(p, steps, i - 1):
            return True
        p = p.parent
    return False


def select(root, sel):
    steps = compile_selector(sel or '')
    if not steps:
        return []
    return [n for n in root.iter() if _match(n, steps, len(steps) - 1)]


def _first_url(v):
    v = (v or '').strip()
    if ',' in v and ' ' in v:
        v = v.split(',')[0].strip().split(' ')[0]
    return v


def _attr(n, name):
    if name == 'text':
        return n.text()
    if name == 'bg':
        m = re.search(r'url\(\s*[\'"]?([^\'")]+)', n.attrs.get('style') or '')
        return m.group(1).strip() if m else ''
    v = n.attrs.get(name)
    if v is None:
        return ''
    v = v.strip()
    if name in ('srcset', 'data-srcset'):
        v = _first_url(v)
    if name in _URL_ATTRS and (v.startswith('data:') or _PLACEHOLDER.search(v)) and name != 'href':
        return ''
    return v


def get(node, rule, base=''):
    for alt in (rule or '').split('||'):
        alt = alt.strip()
        if not alt:
            continue
        sel, attrs = (alt.rsplit('@', 1) + [''])[:2] if '@' in alt else (alt, 'text')
        sel = sel.strip()
        target = node
        if sel:
            hits = select(node, sel)
            if not hits:
                continue
            target = hits[0]
        for a in attrs.split('|'):
            a = a.strip() or 'text'
            v = _attr(target, a)
            if v:
                if base and a in _URL_ATTRS and not v.startswith(('http://', 'https://', 'javascript:', '#')):
                    v = urljoin(base, v)
                return v
    return ''


def items(html, spec, base=''):
    root = parse(html)
    out, seen = [], set()
    for n in select(root, spec.get('item') or ''):
        title = get(n, spec.get('title', ''), base)
        link = get(n, spec.get('link', ''), base)
        if not title or not link or link.startswith(('#', 'javascript:')) or link in seen:
            continue
        seen.add(link)
        out.append({'title': title, 'link': link, 'poster': get(n, spec.get('poster', ''), base),
                    'year': get(n, spec.get('year', ''), base), 'plot': get(n, spec.get('plot', ''), base)})
    return out


def pick(html_or_root, rule, base=''):
    root = html_or_root if isinstance(html_or_root, Node) else parse(html_or_root)
    return get(root, rule, base)


KNOWN_HOSTS = ('voe', 'streamtape', 'doodstream', 'dood', 'mixdrop', 'filemoon', 'supervideo', 'vidoza', 'upstream',
               'streamwish', 'vidhide', 'luluvdo', 'lulustream', 'savefiles', 'streamlare', 'veev', 'vinovo',
               'vidmoly', 'jwplayer', 'ok.ru', 'dailymotion', 'youtube', 'youtu.be', 'vimeo', 'bigwarp', 'wolfstream')
_DIRECT = re.compile(r'''https?:\\?/\\?/[^"'\s<>\\]+(?:\\/[^"'\s<>\\]+)*?\.(?:m3u8|mp4|mpd)(?:\?[^"'\s<>\\]*)?''', re.I)


def _label(url):
    host = (urlparse(url).hostname or '').lower()
    host = re.sub(r'^(www|embed|e|v|player|play|stream)\.', '', host)
    name = host.split('.')[0] or host
    return name[:1].upper() + name[1:]


def embeds(html, base=''):
    root = parse(html)
    found, seen = [], set()
    own = (urlparse(base).hostname or '').lower().replace('www.', '')

    def add(url, direct=False):
        url = (url or '').strip().replace('\\/', '/')
        if url.startswith('//'):
            url = 'https:' + url
        elif base and not url.startswith(('http://', 'https://')):
            url = urljoin(base, url)
        if not url.startswith(('http://', 'https://')) or url in seen:
            return
        host = (urlparse(url).hostname or '').lower().replace('www.', '')
        if not direct and host == own:
            return
        seen.add(url)
        found.append({'name': 'Direkt' if direct else _label(url), 'url': url, 'direct': direct})

    for n in root.iter():
        if n.tag == 'iframe':
            add(n.attrs.get('src') or n.attrs.get('data-src') or n.attrs.get('data-lazy-src'))
        for k in ('data-player-url', 'data-embed', 'data-link', 'data-video', 'data-iframe'):
            if n.attrs.get(k, '').startswith(('http', '//')):
                add(n.attrs[k])
        if n.tag == 'a':
            h = n.attrs.get('href') or ''
            host = (urlparse(h).hostname or '').lower()
            if h.startswith('http') and any(k in host for k in KNOWN_HOSTS):
                add(h)
    for m in _DIRECT.finditer(html or ''):
        add(m.group(0), True)
    return found
