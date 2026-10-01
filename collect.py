#!/usr/bin/env python3
"""EV 브리핑 목록 수집기. GitHub Actions가 매시간 실행합니다.

  python3 collect.py OUT_DIR

sources.md A·B·E절과 watchlist.md를 읽어 목록·검색어를 조회하고,
검색어는 구글 뉴스 RSS(주)로, 실패·0건·변환 실패가 많으면 Bing 뉴스 RSS(예비)로 조회하고,
OUT_DIR/items.jsonl에 처음 본 항목만 first_seen과 함께 추가합니다(10일 보관).
OUT_DIR/status.json에는 목록·검색어별 조회 결과를 남깁니다.
"""
import sys, os, re, json, html, time, hashlib, datetime as dt, urllib.parse
from zoneinfo import ZoneInfo
import requests, feedparser
try:
    from googlenewsdecoder import gnewsdecoder
except ImportError:  # 없으면 구글 경로를 건너뛰고 Bing만 씀
    gnewsdecoder = None

KEEP_DAYS = 10
VER = 3  # 형식이 바뀌면 올림. 다른 버전 항목은 버리고 다시 쌓음
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36',
      'Accept-Language': 'ko,en;q=0.8,zh;q=0.6,ja;q=0.5,de;q=0.4'}
BING = 'https://www.bing.com/news/search?q={q}&format=RSS&qft=interval%3d%228%22'
GOOG = 'https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}'
GN_WHEN = os.environ.get('GN_WHEN', '2d')
FRESH_H = 72  # 게재 시각이 이보다 오래된 결과는 수집하지 않음
CAP = 15  # 검색어 하나가 한 번 수집에 넣는 새 항목 상한(최신순)
DECODE_BUDGET = 180  # 한 번 수집에서 원주소 변환에 쓰는 최대 초. 넘으면 남은 것은 다음 수집으로
# 구매 가이드·해설형 제목(뉴스 아님). 검색 결과에만 적용
GUIDE = re.compile(r'值不值得买|值得买吗|值不值|FAQ|怎么选|榜单|排行榜|攻略|避坑|指南|吗？|'
                   r'방법|점검 순서|하는 법|총정리|체크리스트|'
                   r'\bhow to\b|buyer.?s guide|\btips\b|\bexplained\b|選び方|おすすめ|ランキング', re.I)
EDITIONS = {'KR:ko': ('ko', 'KR'), 'JP:ja': ('ja', 'JP'), 'CN:zh-Hans': ('zh-CN', 'CN'), 'DE:de': ('de', 'DE'),
            'US:en': ('en-US', 'US'), 'GB:en': ('en-GB', 'GB')}
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
    e = txt[txt.index('## E.'):] if '## E.' in txt else ''
    doms = {k: [d.strip().lower() for d in v.split(',') if d.strip()]
            for k, v in re.findall(r'^(제외|발견 전용):\s*(.+)$', e, re.M)}
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
    return feeds, words, doms.get('제외', []), doms.get('발견 전용', [])


def edition(q):
    if re.search('[\u3040-\u30ff]|価|中古', q): return 'JP:ja'
    if re.search('[가-힣]', q): return 'KR:ko'
    if re.search('[\u4e00-\u9fff]', q): return 'CN:zh-Hans'
    if re.search('[äöüß]|gebraucht|elektro', q, re.I): return 'DE:de'
    return 'US:en'


def parse_watch(path):
    """`- 검색어 | 지역판 | !` → [{'q','ed','brand'}]"""
    out = []
    for ln in open(path, encoding='utf-8').read().splitlines():
        if not ln.startswith('- '): continue
        p = [x.strip() for x in ln[2:].split('|')]
        ed = p[1] if len(p) > 1 and p[1] in EDITIONS else edition(p[0])
        out.append({'q': p[0], 'ed': ed, 'brand': len(p) > 2 and p[2] == '!'})
    return out


def dom_in(u, doms):
    m = re.match(r'https?://([^/]+)', u or '')
    h = m.group(1).lower() if m else ''
    h = re.sub(r'^(www\.|m\.)', '', h).replace('.m.', '.')  # 모바일 주소도 같은 도메인으로 봄
    return any(h == d or h.endswith('.' + d) for d in doms)


def google_items(q, ed):
    hl, gl = EDITIONS[ed]
    fp = feedparser.parse(get(GOOG.format(q=urllib.parse.quote(f'{q} when:{GN_WHEN}'), hl=hl, gl=gl, ceid=ed)).content)
    out = []
    for e in fp.entries:
        t = e.get('published_parsed')
        src = (e.get('source') or {}).get('title', '')
        title = html.unescape(e.get('title', '')).strip()
        if src and title.endswith(' - ' + src): title = title[:-len(src) - 3].strip()
        out.append({'title': title, 'url': e.get('link', ''), 'outlet': src,
                    'pub': iso(min(dt.datetime(*t[:6], tzinfo=dt.timezone.utc), NOW + dt.timedelta(minutes=5))) if t else None})
    return out


def gkey(u):
    return hashlib.sha1((u or '').encode()).hexdigest()[:12]


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
    feeds, words, excl, portal = parse_sources(os.path.join(here, 'sources.md'))
    watch = parse_watch(os.path.join(here, 'watchlist.md'))
    ok = matcher(words)
    brand = {w['q'] for w in watch if w['brand']}

    def keep_watch(q, title):  # EV 문맥 필수(업체명 검색어(!)는 고유 단어로도 통과), 가이드·해설형 제외
        if GUIDE.search(title): return False
        term = max(re.sub(r'"|\bOR\b', '', q).split(), key=len).lower()
        return ok(title) or (q in brand and term in title.lower())

    def bing_watch(q):
        b = rss_items(BING.format(q=urllib.parse.quote(q)))
        res = []
        for it in b:
            if keep_watch(q, it['title']) and (not it['pub'] or it['pub'] >= fresh):
                it['url'] = bing_url(it['url'])
                res.append({**it, 'eng': 'bing'})
        return len(b), res
    deadline = time.time() + DECODE_BUDGET
    path = os.path.join(out, 'items.jsonl')
    old = []
    if os.path.exists(path):
        old = [json.loads(l) for l in open(path, encoding='utf-8') if l.strip()]
    lim = iso(NOW - dt.timedelta(days=KEEP_DAYS))
    old = [o for o in old if o.get('v') == VER and o['first_seen'] >= lim and not dom_in(o['url'], excl)
           and (o['kind'] != 'watch' or keep_watch(o['src'][6:], o['title']))]
    known = {o['key'] for o in old}
    known_g = {o['g'] for o in old if o.get('g')}
    fresh = iso(NOW - dt.timedelta(hours=FRESH_H))
    status = {'generated_at': iso(NOW), 'lists': {}, 'watch': {}}
    try:
        prev = json.load(open(os.path.join(out, 'status_prev.json'), encoding='utf-8'))
    except (FileNotFoundError, ValueError):
        prev = {}

    def last_nz(group, name, n):  # 마지막으로 1건 이상 받은 시각(0건이 이어지면 구조 변경·차단 의심)
        return iso(NOW) if n else prev.get(group, {}).get(name, {}).get('last_nonzero')
    new = []

    def add(src, region, kind, it, first_seen, bf=False):
        if not it['url'].startswith('http') or not it['title'] or dom_in(it['url'], excl):
            return False
        if it['pub'] and it['pub'] < fresh:
            return False
        key = hashlib.sha1(nurl(it['url']).encode()).hexdigest()[:12]
        if key in known:
            return False
        known.add(key)
        o = {'v': VER, 'key': key, 'first_seen': first_seen, 'pub': it['pub'], 'src': src, 'region': region,
             'kind': kind, 'title': it['title'][:300], 'url': it['url'], 'bf': bf}
        for f in ('eng', 'g', 'outlet'):
            if it.get(f): o[f] = it[f]
        if dom_in(it['url'], portal): o['portal'] = True
        new.append(o)
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
                    st['new'] += add(f['name'], f['region'], 'list', it, fs, backfill and not it['pub'])
        except Exception as e:  # noqa: BLE001
            st['error'] = f'{type(e).__name__}: {str(e)[:160]}'
        st['last_nonzero'] = last_nz('lists', f['name'], st['fetched'])
        status['lists'][f['name']] = st
    for w in watch:
        q = w['q']
        st = {'ok': False, 'fetched': 0, 'matched': 0, 'new': 0, 'error': '', 'eng': 'google', 'ed': w['ed']}
        items, why = [], ''
        if gnewsdecoder is None:
            why = 'googlenewsdecoder 없음'
        else:
            try:
                g = google_items(q, w['ed'])
                st['fetched'] = len(g)
                if len(g) >= 100: st['cap_hit'] = True  # 구글 상한. 검색어를 나눌 것
                cand = [it for it in g if keep_watch(q, it['title']) and (not it['pub'] or it['pub'] >= fresh)]
                cand.sort(key=lambda it: it['pub'] or '', reverse=True)
                st['matched'] = len(cand)
                todo = [it for it in cand if gkey(it['url']) not in known_g]
                if len(todo) > CAP: st['capped'] = len(todo) - CAP
                todo = todo[:CAP]
                okn = tried = 0
                for i in range(0, len(todo), 10):  # 새 항목만 원주소로 변환
                    if time.time() > deadline:
                        st['decode_later'] = len(todo) - i
                        break
                    chunk = todo[i:i + 10]
                    tried += len(chunk)
                    try:
                        res = gnewsdecoder([it['url'] for it in chunk], interval=1)
                    except Exception as e:  # noqa: BLE001
                        res = [{'success': False, 'message': str(e)}] * len(chunk)
                    for it, d in zip(chunk, res):
                        if d.get('success'):
                            okn += 1
                            items.append({**it, 'g': gkey(it['url']), 'url': d['decoded_url'], 'eng': 'google'})
                    time.sleep(1)
                st['decoded'], st['decode_fail'] = okn, tried - okn
                if not g:
                    why = '구글 0건'
                elif tried >= 2 and okn < tried / 2:
                    why = f'변환 실패 {tried - okn}/{tried}'
                st['ok'] = True
            except Exception as e:  # noqa: BLE001
                why = f'구글 오류 {type(e).__name__}: {str(e)[:120]}'
        if why or w['brand']:  # 예비: Bing. 업체명 검색어는 구글이 적게 잡아 항상 함께 조회
            if why: st['fallback'], st['eng'] = why, 'bing'
            try:
                nb, bi = bing_watch(q)
                st['ok'] = True
                st['bing_fetched'] = nb
                if why: items, st['fetched'], st['matched'] = [], nb, len(bi)
                else: st['eng'] = 'google+bing'
                have = {nurl(it['url']) for it in items}
                items += [it for it in bi if nurl(it['url']) not in have][:CAP]
            except Exception as e:  # noqa: BLE001
                if why: st['error'] = f'{why} / Bing {type(e).__name__}: {str(e)[:120]}'
        for it in items:
            fs = it['pub'] if backfill and it['pub'] and it['pub'] <= iso(NOW) else iso(NOW)
            st['new'] += add('watch:' + q, '', 'watch', it, fs, backfill and not it['pub'])
        known_g.update(it['g'] for it in items if it.get('g'))
        st['last_nonzero'] = last_nz('watch', q, st['fetched'])
        status['watch'][q] = st
        time.sleep(1)
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
