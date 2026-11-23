#!/usr/bin/env python3
"""브리핑 직전 현장 수집(build.py local_collect·read_local·prep의 local: 처리, c15) 검사. 네트워크 없음(수집기는 가짜 스크립트).

  python3 eval/test_localcollect.py
"""
import os, sys, json, shutil, importlib.util, datetime as dt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = '/tmp/evlocaltest'
fails = []


def check(name, cond, info=''):
    print(f"{'PASS' if cond else 'FAIL'} {name}" + (f' | {info}' if info and not cond else ''))
    if not cond: fails.append(name)


shutil.rmtree(T, ignore_errors=True); os.makedirs(f'{T}/w'); os.makedirs(f'{T}/data')
os.environ['EV_W'] = f'{T}/w'
spec = importlib.util.spec_from_file_location('b', f'{REPO}/build.py'); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
W = f'{T}/w'
U = dt.timezone.utc
now = dt.datetime.now(U).replace(microsecond=0)
iso = lambda t: t.isoformat().replace('+00:00', 'Z')
item = lambda k, fs, title: {'v': 3, 'key': k, 'first_seen': iso(fs), 'pub': iso(fs), 'src': 'Electrek', 'region': '미국', 'kind': 'list',
                             'title': title, 'url': f'https://electrek.co/{k}', 'bf': False}
OLD = item('aaaaaaaaaaa1', now - dt.timedelta(hours=30), 'Used EV battery health report shows SOH data')
status = lambda ok, n: {'generated_at': iso(now - dt.timedelta(hours=7)), 'total': 1, 'added': 0,
                        'lists': {f'l{i}': {'ok': i < ok, 'fetched': 3, 'error': '' if i < ok else '403', 'last_nonzero': iso(now)} for i in range(n)},
                        'watch': {}}


def seed():
    for f in ('sources.md', 'watchlist.md'): shutil.copy(f'{REPO}/{f}', W)
    with open(f'{W}/items.jsonl', 'w') as f: f.write(json.dumps(OLD) + '\n')
    json.dump(status(10, 10), open(f'{W}/status.json', 'w'))


def fake(name, body):
    p = f'{T}/{name}.py'
    open(p, 'w').write('import sys, os, json, datetime as dt\nout = sys.argv[1]\n' + body)
    return p


NEW_KEY = 'bbbbbbbbbbb2'
NEW = item(NEW_KEY, now - dt.timedelta(minutes=5), 'Battery health certificate for used EV leases launched')
ok_py = fake('ok', f'''
rows = [json.loads(l) for l in open(os.path.join(out, 'items.jsonl')) if l.strip()] + [{json.dumps(NEW)!r}]
rows = [r if isinstance(r, dict) else json.loads(r) for r in rows]
open(os.path.join(out, 'items.jsonl'), 'w').write(''.join(json.dumps(r) + '\\n' for r in rows))
s = json.load(open(os.path.join(out, 'status_prev.json'))); s['generated_at'] = {iso(now)!r}; s['total'] = len(rows)
json.dump(s, open(os.path.join(out, 'status.json'), 'w'))
''')
blocked_py = fake('blocked', f'''
import shutil; shutil.copy(os.path.join(out, 'items.jsonl'), os.path.join(out, 'items.jsonl.bak'))
json.dump(json.loads({json.dumps(status(2, 10))!r}), open(os.path.join(out, 'status.json'), 'w'))
''')
crash_py = fake('crash', 'sys.exit(1)\n')

# 1) 성공: 새 항목이 W에 들어가고 키가 반환됨
seed(); os.environ['EV_COLLECT_PY'] = ok_py
added, msg = b.local_collect('')
rows = [json.loads(l) for l in open(f'{W}/items.jsonl') if l.strip()]
check('성공: 새 항목 키 반환', added == [NEW_KEY], f'{added} {msg}')
check('성공: items.jsonl에 이력+새 항목', [r['key'] for r in rows] == [OLD['key'], NEW_KEY], str([r['key'] for r in rows]))
check('성공: status.json 생성 시각 갱신', json.load(open(f'{W}/status.json'))['generated_at'] == iso(now))
check('성공: 요약 줄', msg.startswith('현장 수집: 새 항목 1건, 성공 10/10'), msg)

# 2) 접속 차단(성공 2/10): data 브랜치 그대로
seed(); os.environ['EV_COLLECT_PY'] = blocked_py
before = open(f'{W}/items.jsonl').read(), open(f'{W}/status.json').read()
added, msg = b.local_collect('')
check('차단: None 반환·경고', added is None and '접속 차단' in msg and 'data 브랜치 사용' in msg, msg)
check('차단: W 파일 그대로', (open(f'{W}/items.jsonl').read(), open(f'{W}/status.json').read()) == before)

# 3) 수집기 오류 종료: data 브랜치 그대로
seed(); os.environ['EV_COLLECT_PY'] = crash_py
added, msg = b.local_collect('')
check('오류 종료: None 반환·경고', added is None and '종료 1' in msg, msg)
check('오류 종료: W 파일 그대로', open(f'{W}/status.json').read() == before[1])

# 4) 꺼짐
os.environ['EV_LOCAL_COLLECT'] = 'off'
added, msg = b.local_collect('')
check('꺼짐: 실행하지 않음', added is None and '꺼짐' in msg, msg)
del os.environ['EV_LOCAL_COLLECT']

# 5) read_local: 형식 맞는 키만
open(f'{W}/memstate.md', 'w').write(f'issue: 43\nwatermark: {iso(now)}\nrunning: -\ndeferred: -\nlocal: {NEW_KEY},xyz,ccccccccccc3\n')
check('read_local: 12자 16진 키만', b.read_local() == {NEW_KEY, 'ccccccccccc3'}, str(b.read_local()))

# 6) prep 전체(오프라인): 회차 1은 현장 수집으로 NEW를 후보로 보고 local:에 남김,
#    회차 2는 Actions가 나중에 같은 항목을 늦은 first_seen으로 넣어도 후보에서 뺌
def fake_curl(src, dst):
    name = src.split('/')[-1]
    if '/data/' in src: shutil.copy(f'{T}/data/{name}', dst); return ''
    p = f'{REPO}/{name}' if os.path.exists(f'{REPO}/{name}') else next((os.path.join(r, name) for r, _, fs in os.walk(REPO) if name in fs), '')
    if not p: return 'not found'
    shutil.copy(p, dst); return ''
b.curl = fake_curl


def run_prep(wm, data_rows, collect_py):
    for f in os.listdir(W):
        if f != 'fonts': (shutil.rmtree if os.path.isdir(f'{W}/{f}') else os.remove)(f'{W}/{f}')
    open(f'{W}/memstate.md', 'w').write(MEM.format(wm=wm))
    open(f'{W}/sent.md', 'w').write('')
    with open(f'{T}/data/items.jsonl', 'w') as f: f.write(''.join(json.dumps(r) + '\n' for r in data_rows))
    json.dump(status(10, 10), open(f'{T}/data/status.json', 'w'))
    os.environ['EV_COLLECT_PY'] = collect_py
    import contextlib, io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try: b.prep()
        except SystemExit as e: print(f'EXIT {e.code}')
    return buf.getvalue(), open(f'{W}/candidates.md').read() if os.path.exists(f'{W}/candidates.md') else ''


MEM = 'issue: 43\nwatermark: {wm}\nrunning: -\ndeferred: -\n'
out1, cand1 = run_prep(iso(now - dt.timedelta(hours=24)), [OLD], ok_py)
st1 = json.load(open(f'{W}/state.json'))
check('prep 1회차: 현장 수집 요약 출력', '현장 수집: 새 항목 1건' in out1, out1[-400:])
check('prep 1회차: 새 항목이 후보', NEW['url'] in cand1, cand1[:300])
check('prep 1회차: local_next에 새 키', st1.get('local_next') == [NEW_KEY], str(st1.get('local_next')))
check('prep 1회차: 수집 지연 경고 없음', '3시간 넘게' not in out1)

MEM = 'issue: 44\nwatermark: {wm}\nrunning: -\ndeferred: -\nlocal: ' + NEW_KEY + '\n'
late = dict(NEW, first_seen=iso(now + dt.timedelta(minutes=30)))  # Actions가 1회차 뒤에 넣음
out2, cand2 = run_prep(iso(now - dt.timedelta(minutes=1)), [OLD, late], crash_py)
st2 = json.load(open(f'{W}/state.json'))
check('prep 2회차: 현장 수집 실패 시 경고하고 계속', '현장 수집 실패' in out2 and 'EXIT' not in out2, out2[-400:])
check('prep 2회차: local:에 있던 항목은 후보에서 빠짐', NEW['url'] not in cand2, cand2[:300])
check('prep 2회차: data 브랜치에 들어온 키는 local_next에서 빠짐', st2.get('local_next') == [], str(st2.get('local_next')))

MEM = 'issue: 44\nwatermark: {wm}\nrunning: -\ndeferred: -\nlocal: ' + NEW_KEY + '\n'
out3, _ = run_prep(iso(now - dt.timedelta(minutes=1)), [OLD], crash_py)
check('prep: 아직 data 브랜치에 없는 local 키는 유지', json.load(open(f'{W}/state.json')).get('local_next') == [NEW_KEY])

print(f'\n{len(fails)}건 실패' if fails else '\n모두 통과')
sys.exit(1 if fails else 0)
