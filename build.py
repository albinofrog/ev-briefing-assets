#!/usr/bin/env python3
"""EV 시장·정책 브리핑 기계 작업.

  python3 build.py prep            자산 받기, 작업 시작 시각·3일 기준 고정
  python3 build.py schema          briefing.json 형식과 예시 출력
  python3 build.py check  FILE     규칙 검사(오류가 있으면 종료 코드 1)
  python3 build.py render FILE     검사 후 HTML·PDF 제작, 장부 줄·푸시·run_log 블록 출력
  python3 build.py trim sent|log   /tmp/ev/sent.md 또는 /tmp/ev/run_log.md 정리본 출력
  python3 build.py failpush 단계   푸시 문구 앞에 [실패] 단계 표시 추가

작업 폴더 /tmp/ev, 산출물 /mnt/user-data/outputs.
"""
import sys, os, re, json, html, glob, base64, subprocess, datetime as dt

W = '/tmp/ev'
FONTS = '/tmp/ev_fonts'
OUT = '/mnt/user-data/outputs'
REPO = 'https://raw.githubusercontent.com/albinofrog/ev-briefing-assets/main/'
KST = dt.timezone(dt.timedelta(hours=9))
FRESH_H = 72
KEEP_DAYS = 10
AX_SHORT = {1: '시장 지표', 2: '정책·규제', 3: '중고·잔존가치', 4: '보험·금융', 5: '데이터·진단'}
AX_LONG = {1: 'EV·배터리 시장 지표', 2: '정책·규제', 3: '중고 EV·리스·잔존가치', 4: '보험·금융', 5: '배터리 데이터·진단'}
REGIONS = ['한국', 'EU', '미국', '중국', '일본']
BLOCKED = ['msn.com', 'naver.com', 'daum.net', 'yahoo.com', 'yahoo.co.jp', 'sina.com.cn', 'sina.cn', '163.com',
           'sohu.com', 'qq.com', 'bing.com', 'news.google.com', 'eletric-vehicles.com']
BANNED = r'시사|전망|기회|위협|보인다|예상|주목|당사(?!자)'
WEEK = '월화수목금토일'

ASSETS = [('template.html', f'{W}/template.html'), ('sources.md', f'{W}/sources.md'),
          ('watchlist.md', f'{W}/watchlist.md'), ('collector.md', f'{W}/collector.md'), ('fonts/archivonarrow.woff2', f'{FONTS}/archivonarrow.woff2'),
          ('fonts/lgsmart.woff2', f'{FONTS}/lgsmart.woff2'), ('serv04_img_01.png', f'{FONTS}/bonce.png')]

SCHEMA = r'''
{
  "items": [                                  // 수록 기사 전부. 없으면 []
    {
      "tier": "core",                         // core(핵심) | ref(참고)
      "top": 1,                               // 오늘의 핵심 순위 1~3, 아니면 생략
      "axis": 5,                              // 1~5
      "region": "한국",                        // 한국 | EU | 미국 | 중국 | 일본
      "headline": "현대차그룹, 중고 EV 배터리 안전지수 개발 착수",   // 한국어, 행위 명사로 끝남
      "followup": false,                      // 장부에 있는 사건의 새 단계면 true
      "orig_title": "원문 제목 그대로",
      "subject": "현대자동차그룹",               // core만
      "figure": "1초 단위",                     // core만. 대표 수치 14자 이내, 없으면 null
      "figure_note": "배터리 상태 산출 주기, 개발 단계",  // 대상·기준 기간·원문 단서, 없으면 null
      "key_line": "…",                         // top 항목만. 대표 수치와 단서를 담은 한 줄
      "summary": ["사실 1", "사실 2", "사실 3"],  // core: 3~4문장 목록 / ref: 문자열 한 줄 또는 "본문 미확인"
      "outlet": "한국경제", "url": "https://…",
      "published": "09-28 17:14 KST",          // 매체 표기 게재 시각(현지 시간대 포함)
      "published_kst": "09-28 17:14",          // "MM-DD HH:MM" 또는 "MM-DD"
      "first_public": "2026-09-28 17:14",      // 사건 최초 공개 KST. 시각을 모르면 "2026-09-28"(기준일 다음 날 이후만 수록 가능)
      "body_read": true,
      "source_kind": "media",                  // url이 발표 주체 자신의 자료(보도자료·공시·정부 발표)면 origin
      "origin": {"url": "https://…", "outlet": "현대자동차그룹", "title": "…", "date": "2026-09-28"},  // 없으면 null
      "event_key": "현대자동차그룹 / 개발 / -"   // 주체 / 행위 명사 1개 / 대표 수치("|" 금지)
    }
  ],
  "calls": {"A": 18, "B": 19, "C": 16, "D": 24, "본세션": 12},   // 웹 호출(WebFetch·WebSearch) 수
  "yield": {"electrive": "14/3/1", "watch:중고 전기차 배터리": "5/2/1"},   // 창 안/후보/수록
  "dropped": ["제목 앞 20자 | 사유", "…"],   // 주요 탈락 5건 이내
  "errors": ["도구 오류 원문 요약"]
}
'''


def now_state():
    try:
        return json.load(open(f'{W}/state.json'))
    except Exception:
        sys.exit('state.json 없음: 먼저 python3 build.py prep')


def kst(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(KST)


def curl(src, dst):
    for _ in range(2):
        r = subprocess.run(['curl', '-sSfL', '--max-time', '60', '-o', dst, REPO + src], capture_output=True, text=True)
        if r.returncode == 0 and os.path.getsize(dst) > 0:
            return ''
    return (r.stderr or 'empty').strip()


def prep():
    os.makedirs(W, exist_ok=True); os.makedirs(FONTS, exist_ok=True)
    if not os.path.exists(f'{W}/state.json'):
        start = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        json.dump({'start': start.isoformat(), 'cutoff': (start - dt.timedelta(hours=FRESH_H)).isoformat()},
                  open(f'{W}/state.json', 'w'))
    st = now_state()
    s, c = kst(st['start']), kst(st['cutoff'])
    print(f"작업 시작: {st['start']} (KST {s:%Y-%m-%d %H:%M} {WEEK[s.weekday()]})")
    print(f"수록 기준: 최초 공개 {st['cutoff']} 이후 (KST {c:%m-%d %H:%M} ~ {s:%m-%d %H:%M})")
    for src, dst in ASSETS:
        err = curl(src, dst)
        print(f"{'OK  ' if not err else '실패'} {src}" + (f' | {err}' if err else ''))


def tier1():
    txt = open(f'{W}/sources.md').read()
    sec = txt[txt.index('## C.'):]
    return set(re.findall(r'[a-z0-9-]+(?:\.[a-z0-9-]+)+', sec.lower()))


def host(u):
    m = re.match(r'https?://([^/]+)', u or '')
    return m.group(1).lower() if m else ''


def dom_in(h, doms):
    return any(h == d or h.endswith('.' + d) for d in doms)


EXCLUDED = ['tistory.com', 'blog.naver.com', 'brunch.co.kr', 'medium.com', 'substack.com', 'note.com', 'x.com',
            'twitter.com', 'facebook.com', 'linkedin.com', 'youtube.com', 'reddit.com', 'weibo.com', 'zhihu.com',
            'toutiao.com', 'baijiahao.baidu.com', 'wikipedia.org']
WIRE = ['prnewswire.com', 'businesswire.com', 'globenewswire.com', 'accessnewswire.com', 'prnasia.com']
GENERIC_ACT = {'발표', '공개', '밝힘', '언급', '보도', '-'}
END_RE = re.compile(r'(했다|한다|된다|됐다|이다|였다|있다|없다|았다|었다|겠다|했습니다|합니다|됩니다|입니다|습니다|해요|예요|이에요|어요|아요)[.!?]?["”’]?$')


def nurl(u):
    u = (u or '').strip()
    u = re.sub(r'#.*$', '', u)
    u = re.sub(r'([?&])(utm_[^=&]+|fbclid|gclid)=[^&]*', r'\1', u)
    u = re.sub(r'[?&]+$', '', u)
    u = re.sub(r'^https?://(www\.|m\.)?', '', u, flags=re.I)
    return u.rstrip('/').lower()


def read_sent():
    p = f'{W}/sent.md'
    if not os.path.exists(p):
        return None
    t = open(p).read()
    if t.strip() == 'READ_FAILED':
        return 'FAILED'
    rows = []
    for ln in t.splitlines():
        parts = [x.strip() for x in ln.split(' | ')]
        if len(parts) >= 5 and re.match(r'\d{4}-\d{2}-\d{2}$', parts[0]):
            rows.append({'date': parts[0], 'url': parts[2], 'key': parts[4], 'line': ln})
    return rows


def norm(s):
    return re.sub(r'[\s·.,()]', '', s).lower()


def key_sa(k):
    p = [x.strip() for x in k.split('/')]
    return (norm(p[0]), norm(p[1])) if len(p) >= 2 else (norm(k), '')


def parse_fp(s):
    if re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', s or ''):
        return dt.datetime.strptime(s, '%Y-%m-%d %H:%M').replace(tzinfo=KST), True
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s or ''):
        return dt.datetime.strptime(s, '%Y-%m-%d').replace(tzinfo=KST), False
    return None, False


def url_date(u):
    m = re.search(r'/(20\d{2})[/-](\d{2})[/-](\d{2})(?:/|-|$)', u or '')
    if m:
        try: return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError: return None


def style_errs(label, text):
    out = []
    if re.search('[—–]', text):
        out.append(f'{label}: 줄표(—, –) 사용')
    for sent in re.split(r'(?<=[.!?])\s+', text.strip()):
        core = re.sub(r'\s*\([^()]*\)\s*$', '', sent.strip())
        if END_RE.search(core):
            out.append(f'{label}: 서술형 종결 "{core[-12:]}" → 명사형(~함·~됨·~임·~예정)')
    return out


def needed_tops(items):
    per = {}
    for it in items:
        if it.get('tier') == 'core': per[it.get('axis')] = per.get(it.get('axis'), 0) + 1
    return min(3, sum(min(2, n) for n in per.values()))


def check(path, quiet=False):
    st = now_state()
    start, cutoff = kst(st['start']), kst(st['cutoff'])
    d = json.load(open(path))
    items = d.get('items', [])
    E, Wn = [], []
    t1 = tier1()
    sent = read_sent()
    if sent is None:
        E.append('/tmp/ev/sent.md 없음: 메모리 내용을 저장(파일이 없으면 빈 파일, 읽기 실패면 READ_FAILED 한 줄)')
        sent = []
    elif sent == 'FAILED':
        Wn.append('sent.md 읽기 실패: 중복 판정 생략(추정 금지)')
        sent = []
    urls, tops = {}, []
    for i, it in enumerate(items, 1):
        L = f"[{i}] {str(it.get('headline') or '')[:24]}"
        tier = it.get('tier')
        need = ['tier', 'axis', 'region', 'headline', 'orig_title', 'summary', 'outlet', 'url', 'published',
                'published_kst', 'first_public', 'body_read', 'source_kind', 'event_key']
        if tier == 'core':
            need += ['subject', 'figure', 'figure_note']
        miss = [k for k in need if k not in it]
        strs = ['region', 'headline', 'orig_title', 'outlet', 'url', 'published', 'published_kst', 'first_public',
                'source_kind', 'event_key'] + (['subject'] if tier == 'core' else [])
        bad = [k for k in strs if k in it and not (isinstance(it[k], str) and it[k].strip())]
        bad += [k for k in ('figure', 'figure_note', 'key_line') if it.get(k) is not None and not isinstance(it[k], str)]
        summ = it.get('summary')
        if isinstance(summ, list) and not all(isinstance(x, str) and x.strip() for x in summ): bad.append('summary')
        o = it.get('origin')
        if o is not None and not (isinstance(o, dict) and isinstance(o.get('url'), str) and o['url'].startswith('http')):
            bad.append('origin(url 필수, 없으면 null)')
        if miss or bad:
            E.append(f'{L}: 필드 누락 {miss} / 형식 오류 {bad}'); continue
        if tier not in ('core', 'ref'): E.append(f'{L}: tier는 core|ref')
        if it['axis'] not in AX_SHORT: E.append(f'{L}: axis는 1~5')
        if it['region'] not in REGIONS: E.append(f'{L}: region은 {REGIONS}')
        for k in ('url', 'event_key'):
            if re.search(r'\||\n', it[k]): E.append(f'{L}: {k}에 "|"나 줄바꿈 금지')
        if len(it['event_key'].split('/')) != 3: E.append(f'{L}: event_key는 "주체 / 행위 / 수치" 세 칸(칸 안에 "/" 금지)')
        fp, has_t = parse_fp(it['first_public'])
        if not fp:
            E.append(f'{L}: first_public 형식 "YYYY-MM-DD HH:MM" 또는 "YYYY-MM-DD"(KST)')
        else:
            if has_t:
                if fp < cutoff: E.append(f'{L}: 최초 공개가 3일 기준 밖 → 제외(새 단계면 새 단계 시각을 적음)')
            elif fp.date() <= cutoff.date():
                E.append(f'{L}: 날짜만 확인된 기사가 기준일({cutoff:%m-%d}) 이전·당일 → 제외(시각을 확인했으면 시:분까지 적음)')
            if fp > start + dt.timedelta(hours=1): E.append(f'{L}: 최초 공개가 작업 시작 이후')
            m = re.match(r'(\d{2})-(\d{2})(?: (\d{2}):(\d{2}))?$', it['published_kst'].strip())
            if not m:
                E.append(f'{L}: published_kst 형식 "MM-DD HH:MM" 또는 "MM-DD"')
            else:
                pk = dt.datetime(start.year, int(m.group(1)), int(m.group(2)), int(m.group(3) or 23), int(m.group(4) or 59), tzinfo=KST)
                if pk > start + dt.timedelta(days=2): pk = pk.replace(year=start.year - 1)
                if pk < fp: E.append(f'{L}: 게재 시각이 최초 공개보다 이름 → first_public을 게재 시각 이하로')
            if o:
                od = re.match(r'(\d{4})-(\d{2})-(\d{2})', str(o.get('date', '')))
                if not od: E.append(f'{L}: origin.date는 "YYYY-MM-DD"로 시작')
                elif dt.date(*map(int, od.groups())) < fp.date():
                    E.append(f'{L}: 원출처({od.group()})가 최초 공개보다 이름 → first_public을 원출처 기준으로(3일 밖이면 제외)')
            ud = url_date(it['url'])
            if ud and ud < cutoff.date() and not it.get('followup'):
                E.append(f'{L}: URL 날짜 {ud}가 기준일 이전 → 제외')
        for u in [it['url']] + ([o['url']] if o else []):
            if dom_in(host(u), BLOCKED): E.append(f'{L}: 포털·발견 전용 URL 금지 {host(u)} → 원 매체 URL')
            if dom_in(host(u), EXCLUDED): E.append(f'{L}: 제외 출처(블로그·SNS·UGC) {host(u)}')
        nu = nurl(it['url'])
        if nu in urls: E.append(f'{L}: 같은 URL 중복 수록(항목 {urls[nu]})')
        urls[nu] = i
        if tier == 'core':
            if not it['body_read']: E.append(f'{L}: 핵심은 본문 확인 필수 → ref')
            if it['source_kind'] == 'origin':
                if not dom_in(host(it['url']), list(t1) + WIRE):
                    Wn.append(f'{L}: 원출처 표시 도메인 {host(it["url"])} → 발표 주체(기업·기관·배포처)의 공식 도메인인지 확인')
            elif not dom_in(host(it['url']), t1):
                E.append(f'{L}: 핵심 출처 조건 미충족({host(it["url"])}: 원출처도 1등급도 아님) → ref 또는 원출처 URL로 교체')
            if not isinstance(summ, list) or not summ:
                E.append(f'{L}: 핵심 summary는 문장 목록')
            elif not 3 <= len(summ) <= 4:
                Wn.append(f'{L}: 요약 {len(summ)}문장(권장 3~4)')
            if it['figure'] and len(it['figure']) > 14: Wn.append(f'{L}: figure 14자 초과')
        else:
            if not isinstance(summ, str): E.append(f'{L}: 참고 summary는 문자열 한 줄')
            if not it['body_read'] and summ != '본문 미확인': E.append(f'{L}: 본문 미확인이면 summary는 "본문 미확인"')
        if len(it['headline']) > 60: Wn.append(f'{L}: 헤드라인 {len(it["headline"])}자(60자 이내 권장)')
        if it.get('top'):
            if tier != 'core': E.append(f'{L}: top은 핵심만')
            if not it.get('key_line'): E.append(f'{L}: top 항목은 key_line 필요')
            tops.append((it['top'], it['axis']))
        texts = [('headline', it['headline'])]
        texts += [(f'summary{j}', x) for j, x in enumerate(summ if isinstance(summ, list) else [summ], 1)]
        texts += [(k, it.get(k)) for k in ('figure', 'figure_note', 'key_line') if it.get(k)]
        for k, t in texts:
            E += [f'{L} {m}' for m in style_errs(k, t)]
            if re.search(BANNED, t): Wn.append(f'{L} {k}: 금지어 의심 "{re.search(BANNED, t).group()}" → 발언 주체 인용·고유명사가 아니면 고침')
        if not re.search('[가-힣]', it['headline']): E.append(f'{L}: 헤드라인은 한국어')
        for r in sent:
            ks, kn = key_sa(r['key']), key_sa(it['event_key'])
            if nurl(r['url']) == nu:
                E.append(f'{L}: 기수록 URL({r["date"]}) → 제외')
            elif ks == kn and ks[0] not in ('', '-') and not it.get('followup'):
                msg = f'{L}: 장부의 "{r["key"]}"와 주체·행위 일치'
                if ks[1] in GENERIC_ACT: Wn.append(msg + ' → 같은 사건이면 제외, 다른 사건이면 그대로')
                else: E.append(msg + ' → 새 단계면 followup=true, 같은 사건이면 제외')
        if it.get('followup') and not any(key_sa(r['key'])[0] == key_sa(it['event_key'])[0] for r in sent):
            Wn.append(f'{L}: followup=true인데 장부에 같은 주체 없음')
    ncore = sum(1 for it in items if it.get('tier') == 'core')
    need_n = needed_tops(items)
    ranks = sorted(t for t, _ in tops)
    if ranks != list(range(1, need_n + 1)):
        E.append(f'top 순위는 1..{need_n}을 한 번씩(현재 {ranks}, 한 축 2건까지)')
    for a in set(a for _, a in tops):
        if sum(1 for _, b in tops if b == a) > 2: E.append(f'오늘의 핵심에 축 {a}가 3건 이상')
    if not quiet or E or Wn:
        print(f'검사: 항목 {len(items)}(핵심 {ncore}) | 오류 {len(E)} | 확인 {len(Wn)}')
        for m in E: print('오류', m)
        for m in Wn: print('확인', m)
    if os.path.exists(f'{W}/sent.md') and os.path.getsize(f'{W}/sent.md') > 15000:
        print('안내: sent.md 15KB 초과 → python3 build.py trim sent')
    return d, E


def esc(s):
    return html.escape(str(s or ''), quote=True)


def render(path):
    d, E = check(path)
    if E:
        sys.exit('오류를 고친 뒤 다시 render')
    st = now_state()
    s, c = kst(st['start']), kst(st['cutoff'])
    items = d['items']
    date = f'{s:%Y-%m-%d}'
    try:
        nums = [l.strip() for l in open(f'{W}/issue_no.txt').read().splitlines() if re.fullmatch(r'\s*\d+\s*', l)]
    except FileNotFoundError:
        nums = []
    if len(nums) != 1:
        sys.exit('/tmp/ev/issue_no.txt에 직전 호수 숫자 한 줄만 저장(메모리 파일이 없으면 0)')
    issue = int(nums[0]) + 1
    nnn = f'{issue:03d}'
    fails = []
    core = [i for i in items if i['tier'] == 'core']
    refs = [i for i in items if i['tier'] == 'ref']
    ledger = [f"{i['first_public'][:10]} | {i['axis']} | {i['url']} | {(i.get('origin') or {}).get('url') or '-'} | {i['event_key']}"
              for i in items]
    top1 = sorted([i for i in core if i.get('top')], key=lambda x: x['top'])
    if items:
        push = f"EV 시장·정책 제{nnn}호 | 핵심 {len(core)}·참고 {len(refs)} | " + (
            f"1) {top1[0]['headline'][:40]}" if top1 else '핵심 없음')
    else:
        push = 'EV 시장·정책 | 3일 내 조건에 맞는 새 소식 없음'
    files = []
    if items:
        html_path, pdf_path = build_html(d, s, c, nnn, date, fails)
        files = [html_path]
        pdf_ok = make_pdf(html_path, pdf_path, fails)
        if pdf_ok: files.insert(0, pdf_path)
    if fails:
        push = '[실패] ' + ','.join(sorted(set(f.split(':')[0] for f in fails))) + ' ' + push
    push = push[:200]
    calls = d.get('calls', {})
    total = sum(v for v in calls.values() if isinstance(v, int))
    head = f"## {'제' + nnn + '호' if items else '발행 없음'} | 시작 {st['start']} | 기준 {c:%m-%d %H:%M}~{s:%m-%d %H:%M} KST | 핵심 {len(core)}·참고 {len(refs)} | 파일 {'PDF·HTML' if len(files) == 2 else ('HTML' if files else '없음')}"
    log = [head, '호출: ' + ' / '.join(f'{k} {v}' for k, v in calls.items()) + f' / 합계 {total}',
           '수확: ' + ', '.join(f'{k} {v}' for k, v in d.get('yield', {}).items()),
           '수록: ' + ' ; '.join(f"{i['headline'][:20]} | {'핵심' if i['tier'] == 'core' else '참고'}" for i in items),
           '탈락: ' + ' ; '.join(d.get('dropped', [])[:5]),
           '오류: ' + ' ; '.join(d.get('errors', []) + fails)]
    block = '\n'.join(log)
    for k in (4, 2, 3):
        while len(block.encode()) > 1500 and len(log[k]) > 30:
            log[k] = log[k][:int(len(log[k]) * .8)] + '…'; block = '\n'.join(log)
    open(f'{W}/runlog_block.md', 'w').write(block + '\n')
    open(f'{W}/ledger.txt', 'w').write('\n'.join(ledger) + ('\n' if ledger else ''))
    open(f'{W}/push.txt', 'w').write(push)
    print('\n== 파일(전달 순서) ==\n' + ('\n'.join(files) or '없음'))
    print('== 장부 줄(5줄씩 추가) ==\n' + ('\n'.join(ledger) or '없음'))
    print('== 푸시 ==\n' + push)
    print('== run_log 블록 ==\n' + block)
    if fails: print('== 실패 ==\n' + '\n'.join(fails))


def build_html(d, s, c, nnn, date, fails):
    tpl = open(f'{W}/template.html').read()
    head = tpl[tpl.index('<head>'):tpl.index('</head>') + 7]
    script = tpl[tpl.index('<script>'):tpl.index('</script>') + 9]
    head = re.sub(r'<!--.*?-->', '', head, flags=re.S)
    head = head.replace('{{NNN}}', nnn).replace('{{YYYY-MM-DD}}', date)
    ff = [f'{FONTS}/archivonarrow.woff2', f'{FONTS}/lgsmart.woff2']
    if not all(os.path.exists(f) and os.path.getsize(f) > 0 for f in ff):
        head = re.sub(r'@font-face\{[^}]*\}\n?', '', head); fails.append('글꼴: 로컬 파일 없음, 기본 글꼴 사용')
    else:
        head = re.sub(r',url\("https://[^"]+"\) format\("woff2"\)', '', head)  # 원격 글꼴 주소 제거
    logo = f'{FONTS}/bonce.png'
    if os.path.exists(logo) and os.path.getsize(logo) > 0:
        uri = 'data:image/png;base64,' + base64.b64encode(open(logo, 'rb').read()).decode()
    else:
        uri = None; fails.append('로고: 파일 없음')
    items = d['items']
    notes, srcs = {}, []

    def fn(url, outlet, title, when):
        if url not in notes:
            notes[url] = len(notes) + 1
            srcs.append(f'<li>{esc(outlet)}, 「{esc(title)}」, {esc(when)}. <a href="{esc(url)}">{esc(url)}</a></li>')
        return f'<sup><a href="{esc(url)}">[{notes[url]}]</a></sup>'

    B = []
    B.append('<header class="mast">\n  <div>\n' + (f'    <img class="logo" src="{uri}" alt="B.once">\n' if uri else '') +
             '    <h1>EV 시장·정책 브리핑</h1><div class="sub">배터리 데이터 신사업을 위한 국내외 시장·정책 일간 동향</div></div>\n'
             f'  <dl><dt>이슈</dt><dd>제{nnn}호</dd><dt>발행일</dt><dd>{date} ({WEEK[s.weekday()]})</dd><dt>작성</dt><dd>{s:%H:%M} KST</dd>'
             f'<dt>조사 창</dt><dd>{c:%m-%d %H:%M} ~ {s:%m-%d %H:%M} KST</dd></dl>\n</header>')
    core = [i for i in items if i['tier'] == 'core']
    tops = sorted([i for i in core if i.get('top')], key=lambda x: x['top'])
    for i in tops: i['_id'] = f"k{i['top']}"
    K = ['<div class="box">\n  <h2>오늘의 핵심</h2>']
    for i in tops:
        fpk = i['first_public'][5:16]
        K.append(f'  <div class="key"><span class="n">{i["top"]}</span><span class="h"><a href="#{i["_id"]}">{esc(hl(i))}</a></span>'
                 f'<span class="s"><span class="axn">{i["axis"]}</span>{AX_SHORT[i["axis"]]} · {i["region"]} · {fpk}</span>'
                 f'<span class="g">{esc(i["key_line"])}</span></div>')
    if not tops: K.append('  <p class="none">핵심 기준을 충족한 기사 없음</p>')
    K.append('  <table class="counts">\n    <thead><tr><th>축별 건수</th>' +
             ''.join(f'<th><span class="axn">{a}</span>{AX_SHORT[a]}</th>' for a in AX_SHORT) + '<th class="sum">합계</th></tr></thead>\n    <tbody>')
    for name, t in (('핵심', 'core'), ('참고', 'ref')):
        ns = [sum(1 for i in items if i['tier'] == t and i['axis'] == a) for a in AX_SHORT]
        K.append(f'      <tr><th>{name}</th>' + ''.join(f'<td class="z">0</td>' if n == 0 else f'<td>{n}</td>' for n in ns) +
                 f'<td class="sum">{sum(ns)}</td></tr>')
    K.append('    </tbody>\n  </table>\n</div>')
    B.append('\n'.join(K))
    empty_run = []

    def flush():
        if empty_run:
            B.append('<section class="empty"><h2>' + ''.join(f'<span class="ax">{a}</span>' for a in empty_run) +
                     ' · '.join(AX_LONG[a] for a in empty_run) + '<span class="cnt">해당 없음</span></h2></section>')
            empty_run.clear()

    for a in AX_SHORT:
        cs = [i for i in items if i['axis'] == a and i['tier'] == 'core']
        rs = [i for i in items if i['axis'] == a and i['tier'] == 'ref']
        if not cs and not rs:
            empty_run.append(a); continue
        flush()
        S = [f'<section>\n  <h2><span class="ax">{a}</span>{AX_LONG[a]}<span class="cnt">핵심 {len(cs)} · 참고 {len(rs)}</span></h2>']
        if not cs: S.append('  <p class="none">핵심 항목 없음</p>')
        for i in cs:
            idattr = f' id="{i["_id"]}"' if i.get('_id') else ''
            if i['figure']:
                fig = f'<dt class="figl">대표 수치</dt><dd class="fig">{esc(i["figure"])}</dd>' + (
                    f'<dd class="q">{esc(i["figure_note"])}</dd>' if i['figure_note'] else '')
            else:
                fig = '<dt class="figl">대표 수치</dt><dd class="fig nil">수치 없음</dd>'
            note = fn(i['url'], i['outlet'], i['orig_title'], i['published'])
            lis = ''.join(f'<li>{esc(x)}{note if j == len(i["summary"]) - 1 else ""}</li>' for j, x in enumerate(i['summary']))
            pub = i['published'] if 'KST' in i['published'] else f"{i['published']} ({i['published_kst']} KST)"
            o = i.get('origin')
            osrc = f', 원출처 자료{fn(o["url"], o.get("outlet", ""), o.get("title", ""), o.get("date", ""))}' if o and o.get('url') else ''
            S.append(f'  <article class="item"{idattr}>\n    <dl class="meta"><dt>주체</dt><dd>{esc(i["subject"])}</dd>{fig}</dl>\n'
                     f'    <h3>{esc(hl(i))}</h3>\n    <p class="orig">{esc(i["orig_title"])}</p>\n    <ul class="sum">{lis}</ul>\n'
                     f'    <div class="src">{esc(i["outlet"])}({i["region"]}), 게재 {esc(pub)}{osrc}</div>\n  </article>')
        if rs:
            S.append(f'  <h4 class="tier">참고 {len(rs)}건</h4>')
            for i in rs:
                note = fn(i['url'], i['outlet'], i['orig_title'], i['published'])
                when = i['first_public'][5:16] + (' KST' if len(i['first_public']) > 10 else '')
                S.append(f'  <div class="ref"><span class="t">{esc(hl(i))}</span>{esc(i["summary"])}'
                         f'<div class="m">{esc(i["outlet"])}, {i["region"]}, {when} {note}</div></div>')
        S.append('</section>')
        B.append('\n'.join(S))
    flush()
    B.append('<section class="srcs">\n  <h2>출처 목록</h2>\n  <ol class="sources">\n    ' + '\n    '.join(srcs) + '\n  </ol>\n</section>')
    doc = (f'<!DOCTYPE html>\n<html lang="ko">\n{head}\n<body>\n' + '\n\n'.join(B) + f'\n{script}\n</body>\n</html>\n')
    doc = doc.replace('file:///tmp/ev_fonts/bonce.png', uri or '')
    if not uri:
        doc = re.sub(r'<link rel="preload"[^>]*>\n?', '', doc)
    left = re.findall(r'\{\{[^}]*\}\}', doc)
    if left: fails.append(f'템플릿: 남은 자리표시자 {left[:3]}')
    os.makedirs(OUT, exist_ok=True)
    hp = f'{OUT}/EV시장정책브리핑_{date}.html'
    open(hp, 'w').write(doc)
    return hp, hp[:-5] + '.pdf'


def hl(i):
    return ('[후속] ' if i.get('followup') else '') + i['headline']


def chrome():
    for p in glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome') + ['/usr/bin/chromium', '/usr/bin/chromium-browser']:
        if os.path.exists(p): return p


def make_pdf(hp, pp, fails):
    exe = chrome()
    if not exe:
        fails.append('PDF: chromium 없음'); return False

    def run(src):
        if os.path.exists(pp): os.remove(pp)
        try:
            subprocess.run([exe, '--headless', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer',
                            '--virtual-time-budget=10000', f'--print-to-pdf={pp}', f'file://{src}#pdf'],
                           capture_output=True, timeout=240)
        except subprocess.TimeoutExpired:
            return False
        return os.path.exists(pp) and os.path.getsize(pp) >= 10000

    ok = run(hp)
    if not ok:
        alt = f'{W}/nofont.html'
        open(alt, 'w').write(re.sub(r'@font-face\{[^}]*\}\n?', '', open(hp).read()))
        ok = run(alt)
        if ok: fails.append('글꼴: PDF 10KB 미만, 기본 글꼴로 재변환')
    if not ok:
        fails.append('PDF: 변환 실패'); return False
    info = subprocess.run(['pdfinfo', pp], capture_output=True, text=True).stdout
    size = re.search(r'Page size:\s+([\d.]+) x ([\d.]+)', info)
    pages = re.search(r'Pages:\s+(\d+)', info)
    if not size or abs(float(size.group(1)) - 595) > 2 or abs(float(size.group(2)) - 842) > 2:
        fails.append(f'PDF: A4 아님 {size.group(0) if size else info[:80]}')
    fonts = subprocess.run(['pdffonts', pp], capture_output=True, text=True).stdout
    if not any(x.startswith('글꼴') for x in fails):
        for f in ('ArchivoNarrow', 'LGSm'):
            if f not in fonts: fails.append(f'글꼴: PDF에 {f} 없음')
    subprocess.run(['pdftoppm', '-png', '-r', '60', '-f', '1', '-l', '1', pp, f'{W}/page1'])
    print(f'PDF: {pp} | {pages.group(1) if pages else "?"}쪽 | {os.path.getsize(pp) // 1024}KB | 1쪽 미리보기 {W}/page1-1.png')
    return True


def failpush(stage):
    p = f'{W}/push.txt'
    t = open(p).read().strip()
    t = re.sub(r'^\[실패\] ', f'[실패] {stage},', t) if t.startswith('[실패] ') else f'[실패] {stage} {t}'
    open(p, 'w').write(t[:200]); print(t[:200])


def trim(what):
    st = now_state()
    if what == 'sent':
        lim = (kst(st['start']) - dt.timedelta(days=KEEP_DAYS)).strftime('%Y-%m-%d')
        lines = [l for l in open(f'{W}/sent.md').read().splitlines()
                 if re.match(r'\d{4}-\d{2}-\d{2} \| ', l) and l[:10] >= lim]
        open(f'{W}/sent_trimmed.md', 'w').write('\n'.join(lines) + '\n')
        print(f'{W}/sent_trimmed.md ({len(lines)}줄, {lim} 이후) → memory_write로 덮어씀')
    else:
        t = open(f'{W}/run_log.md').read()
        blocks = [b for b in re.split(r'\n(?=## )', t) if b.strip()]
        keep = '\n'.join(blocks[-15:]).strip() + '\n'
        open(f'{W}/run_log_trimmed.md', 'w').write(keep)
        print(f'{W}/run_log_trimmed.md (최근 {min(15, len(blocks))}회) → memory_write로 덮어씀')


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if a[0] == 'prep': prep()
    elif a[0] == 'schema': print(SCHEMA)
    elif a[0] == 'check': sys.exit(1 if check(a[1])[1] else 0)
    elif a[0] == 'render': render(a[1])
    elif a[0] == 'trim': trim(a[1])
    elif a[0] == 'failpush': failpush(a[1])
    else: sys.exit(__doc__)
