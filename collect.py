#!/usr/bin/env python3
"""EV 브리핑 목록 수집기. GitHub Actions가 매시간 실행합니다.

  python3 collect.py OUT_DIR

sources.md A·B절과 watchlist.md를 읽어 목록·검색어를 조회하고,
OUT_DIR/items.jsonl에 처음 본 항목만 first_seen과 함께 추가합니다(10일 보관).
OUT_DIR/status.json에는 목록·검색어별 조회 결과를 남깁니다.
"""
import sys, os, re, json, html, hashlib, datetime as dt, urllib.parse
from zoneinfo import ZoneInfo
import requests, feedparser

KEEP_DAYS = 10
VER = 2  # 형식이 바뀌면 올림. 다른 버전 항목은 버리고 다시 쌓음
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36',
      'Accept-Language': 'ko,en;q=0.8,zh;q=0.6,ja;q=0.5,de;q=0.4'}
BING = 'https://www.bing.com/news/search?q={q}&format=RSS&qft=interval%3d%228%22'
NOW = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
TZ = {'한국': 'Asia/Seoul', '일본': 'Asia/Tokyo', '중국': 'Asia/Shanghai', 'EU': 'Europe/Berlin', '미국': 'America/New_York'}
HAS_TZ = re.compile(r'([+-]\d{2}:?\d{2}|\bZ\b|\d(Z)$|\b(GMT|UTC|UT|[ECMP][SD]T|KST|JST|CST|CET|CEST|BST)\b)', re.I)


def iso(t):
    return t.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def nurl(u):
    u = re.sub(r'#.*$', '', (u or '').strip())
    u = re.sub(r'([?&])(utm_[^=&]+|fbclid|gclid)=[^&]*', r'\1', u)
    u = re.sub(r'[?&]+$', '', u)
    return re.sub(r'^https?://(www\.|m\.)?', '', u, flags=re.I).rstrip('/').lower()


def parse_sources(path):
    txt = open(path, encoding='utf-8').read()
    a = txt[txt.index('## A.'):txt.index('## B.')]
    b = txt[txt.index('## B.'):txt.index('## C.')]
    feeds = []
    for ln in a.splitlines():
        if not ln.startswith('- ') or ln.count('|') < 3 or '방식' in ln:
            continue
        p = [x.strip() for x in ln[2:].split('|')]
        if not p[3].startswith('http'):
            continue
        feeds.append({'name': p[0], 'region': p[1], 'how': p[2], 'url': p[3], 'all': len(p) > 4 and '전체' in p[4]})
    words = []
    for ln in b.splitlines()[1:]:
        if ln.startswith('옵션') or not ln.strip():
            continue
        words += [w.strip() for w in ln.split(',') if w.strip()]
    return feeds, words


def parse_watch(path):
    out = []
    for ln in open(path, encoding='utf-8').read().splitlines():
        if ln.startswith('- '):
            out.append(ln[2:].strip())
    return out


def matcher(words):
    latin = [w for w in words if re.fullmatch(r'[A-Za-z0-9 \-]+', w)]
    other = [w for w in words if w not in latin]
    rx = re.compile(r'(?<![A-Za-z])(' + '|'.join(re.escape(w) for w in latin) + r')(?![A-Za-z])', re.I)
    return lambda t: bool(rx.search(t)) or any(w.lower() in t.lower() for w in other)


def get(url):
    for i in range(2):
        try:
            r = requests.get(url, headers=UA, timeout=25 if i == 0 else 45)
            r.raise_for_status()
            return r
        except (requests.Timeout, requests.ConnectionError):
            if i: raise


def rss_items(url, region=''):
    fp = feedparser.parse(get(url).content)
    out = []
    for e in fp.entries:
        t = e.get('published_parsed') or e.get('updated_parsed')
        raw = e.get('published') or e.get('updated') or ''
        pub = None
        if t:
            d = dt.datetime(*t[:6], tzinfo=dt.timezone.utc)
            if raw and not HAS_TZ.search(raw) and region in TZ:  # 시간대 없는 표기는 매체 현지 시간
                d = d.replace(tzinfo=ZoneInfo(TZ[region]))
            pub = iso(min(d, NOW + dt.timedelta(minutes=5)))
        out.append({'title': html.unescape(re.sub(r'<[^>]+>', '', e.get('title', ''))).strip(), 'url': e.get('link', ''), 'pub': pub})
    return out


def html_items(url, pattern):
    r = get(url)
    r.encoding = r.apparent_encoding or r.encoding
    rx = re.compile(pattern)
    out, seen = [], set()
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r.text, re.S | re.I):
        href = urllib.parse.urljoin(url, html.unescape(m.group(1)))
        title = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', m.group(2)))).strip()
        if not rx.search(href) or len(title) < 6 or href in seen:
            continue
        seen.add(href)
        out.append({'title': title, 'url': href, 'pub': None})
    return out


def bing_url(link):
    m = re.search(r'[?&]url=([^&]+)', link or '')
    return urllib.parse.unquote(m.group(1)) if m and 'bing.com' in link else link


def main(out):
    here = os.path.dirname(os.path.abspath(__file__))
    feeds, words = parse_sources(os.path.join(here, 'sources.md'))
    watch = parse_watch(os.path.join(here, 'watchlist.md'))
    ok = matcher(words)
    path = os.path.join(out, 'items.jsonl')
    old = []
    if os.path.exists(path):
        old = [json.loads(l) for l in open(path, encoding='utf-8') if l.strip()]
    lim = iso(NOW - dt.timedelta(days=KEEP_DAYS))
    old = [o for o in old if o.get('v') == VER and o['first_seen'] >= lim]
    known = {o['key'] for o in old}
    status = {'generated_at': iso(NOW), 'lists': {}, 'watch': {}}
    new = []

    def add(src, region, kind, it, first_seen):
        if not it['url'].startswith('http') or not it['title']:
            return False
        key = hashlib.sha1(nurl(it['url']).encode()).hexdigest()[:12]
        if key in known:
            return False
        known.add(key)
        new.append({'v': VER, 'key': key, 'first_seen': first_seen, 'pub': it['pub'], 'src': src, 'region': region,
                    'kind': kind, 'title': it['title'][:300], 'url': it['url']})
        return True

    backfill = not old
    for f in feeds:
        st = {'ok': False, 'fetched': 0, 'matched': 0, 'new': 0, 'error': ''}
        try:
            items = rss_items(f['url'], f['region']) if f['how'] == 'rss' else html_items(f['url'], f['how'].split(':', 1)[1])
            st['ok'], st['fetched'] = True, len(items)
            for it in items:
                if f['all'] or ok(it['title']):
                    st['matched'] += 1
                    fs = it['pub'] if backfill and it['pub'] and it['pub'] <= iso(NOW) else iso(NOW)
                    st['new'] += add(f['name'], f['region'], 'list', it, fs)
        except Exception as e:  # noqa: BLE001
            st['error'] = f'{type(e).__name__}: {str(e)[:160]}'
        status['lists'][f['name']] = st
    for q in watch:
        st = {'ok': False, 'fetched': 0, 'new': 0, 'error': ''}
        try:
            items = rss_items(BING.format(q=urllib.parse.quote(q)))
            st['ok'], st['fetched'] = True, len(items)
            for it in items:
                it['url'] = bing_url(it['url'])
                fs = it['pub'] if backfill and it['pub'] and it['pub'] <= iso(NOW) else iso(NOW)
                st['new'] += add('watch:' + q, '', 'watch', it, fs)
        except Exception as e:  # noqa: BLE001
            st['error'] = f'{type(e).__name__}: {str(e)[:160]}'
        status['watch'][q] = st
    os.makedirs(out, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        for o in old + new:
            fh.write(json.dumps(o, ensure_ascii=False) + '\n')
    status['total'] = len(old) + len(new)
    status['added'] = len(new)
    json.dump(status, open(os.path.join(out, 'status.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    bad = [k for k, v in {**status['lists'], **status['watch']}.items() if not v['ok']]
    print(f"추가 {len(new)} / 보관 {status['total']} / 실패 {len(bad)}: {bad}")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'out')
