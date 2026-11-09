#!/usr/bin/env python3
"""주간 놓침 감사(build.py audit)와 감사 판정의 개선 신호 연결(build.py feedback) 검사. 네트워크 없음.

  python3 eval/test_audit.py
"""
import os, sys, json, shutil, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = '/tmp/evaudittest'
fails = []


def check(name, cond, info=''):
    print(f"{'PASS' if cond else 'FAIL'} {name}" + (f' | {info}' if info and not cond else ''))
    if not cond: fails.append(name)


def run(*args):
    r = subprocess.run([sys.executable, f'{REPO}/build.py', *args], capture_output=True, text=True, env={**os.environ, 'EV_W': T})
    return r.returncode, r.stdout + r.stderr


def doc(coll, i, data, root=f'{T}/fb'):
    os.makedirs(f'{root}/{coll}', exist_ok=True)
    json.dump({'id': i, 'data': data, 'version': 1}, open(f'{root}/{coll}/{i}.json', 'w', encoding='utf-8'), ensure_ascii=False)


shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
U1, U2, U3, U4 = ('https://example.com/news/a-carried', 'https://example.org/ledger-only', 'https://example.net/same-event', 'https://example.jp/missed')
open(f'{T}/sent.md', 'w', encoding='utf-8').write(f'2026-11-10 | 3 | {U2} | - | Cox / 집계 / 3%\n')
doc('items', 'i033-01', {'issue': 33, 'n': 1, 'tier': 'core', 'url': U1, 'headline': '기사 A', 'date': '2026-11-10', 'key': ''})
doc('items', 'i034-02', {'issue': 34, 'n': 2, 'tier': 'ref', 'url': 'https://other.example/x', 'headline': '같은 사건 다른 매체', 'date': '2026-11-11'})
AUD = [{'url': U1, 'title': 'A', 'date': '2026-11-09', 'topic': '배터리 데이터 평가', 'why': 'SOH 인증'},
       {'url': U2, 'title': 'B', 'date': '2026-11-09', 'topic': '전기중고차·리스', 'why': '잔존가치'},
       {'url': U3, 'title': 'C', 'date': '2026-11-10', 'topic': '정책', 'why': '규제'},
       {'url': U4, 'title': 'D', 'date': '2026-11-11', 'topic': '보험', 'why': '배터리 보험'}]
json.dump(AUD, open(f'{T}/audit_in.json', 'w', encoding='utf-8'), ensure_ascii=False)

code, out = run('audit', 'check', f'{T}/audit_in.json', f'{T}/fb')
auto = json.load(open(f'{T}/audit_auto.json', encoding='utf-8')) if code == 0 else {}
check('check: 보드 items URL 자동 일치', auto.get(U1) == 'item:i033-01', out)
check('check: 장부 URL 자동 일치', auto.get(U2) == 'ledger', out)
check('check: 못 맞춘 것은 대조 필요, 기간 안 수록 기사 목록 출력', auto.get(U3) == '' and 'i034-02' in out, out)

json.dump([{**x, 'title': ''} if i == 0 else x for i, x in enumerate(AUD)], open(f'{T}/bad.json', 'w', encoding='utf-8'), ensure_ascii=False)
code, out = run('audit', 'check', f'{T}/bad.json', f'{T}/fb')
check('check: 빈 칸 형식 오류', code != 0 and '형식 오류' in out, out)

code, out = run('audit', 'board', f'{T}/audit_in.json', '2026-11-13')
check('board: 수동 대조(match) 없으면 거부', code != 0 and 'match 없음' in out, out)
AUD[2]['match'] = 'i034-02'; AUD[3]['match'] = 'none'
json.dump(AUD, open(f'{T}/audit_in.json', 'w', encoding='utf-8'), ensure_ascii=False)
code, out = run('audit', 'board', f'{T}/audit_in.json', '2026-11-13')
w = json.load(open(f'{T}/audit_board.json', encoding='utf-8')) if code == 0 else []
by = {x['data']['url']: x for x in w}
check('board: 4건, 실림 3·판정 필요 1', len(w) == 4 and [by[u]['data']['carried'] for u in (U1, U2, U3, U4)] == [True, True, True, False] and '판정 필요 1' in out, out)
check('board: 수동 대조 id는 item: 접두어로', by.get(U3, {}).get('data', {}).get('match') == 'item:i034-02')
code, out2 = run('audit', 'board', f'{T}/audit_in.json', '2026-11-13')
w2 = json.load(open(f'{T}/audit_board.json', encoding='utf-8'))
check('board: 같은 주·URL은 같은 문서 id(다시 돌려도 덮어씀)', sorted(x['doc_id'] for x in w) == sorted(x['doc_id'] for x in w2))

for x in w: doc('audit', x['doc_id'], x['data'])
miss_id = by[U4]['doc_id']
doc('audit_fb', miss_id, {'verdict': 'miss', 'note': '', 'at': '2026-11-14T01:00:00Z'})
code, out = run('audit', 'score', f'{T}/fb')
check('score: 놓침률 = 놓침 ÷ (실림 + 놓침)', '2026-11-13 | 후보 4 실림 3 놓침 1 불필요 0 판정 대기 0 | 놓침률 25%' in out, out)

code, out = run('feedback', f'{T}/fb', '2026-11-13T00:00:00Z')
mt = open(f'{T}/missed.txt', encoding='utf-8').read()
check('feedback: 감사에서 놓침 확인한 기사는 놓침 제보(MISS-U)로', U4 in mt and '감사 놓침 확인: 배터리 보험' in mt, out + mt)
check('feedback: fb_seen 다음 값에 감사 판정 시각 포함', 'fb_seen 다음 값: 2026-11-14T01:00:00Z' in out, out)
code, out = run('feedback', f'{T}/fb', '2026-11-14T01:00:00Z')
check('feedback: 이미 본 감사 판정은 다시 안 셈', U4 not in open(f'{T}/missed.txt', encoding='utf-8').read(), out)
doc('audit_fb', by[U3]['doc_id'], {'verdict': 'ok', 'note': '', 'at': '2026-11-15T00:00:00Z'})
code, out = run('feedback', f'{T}/fb', '2026-11-14T01:00:00Z')
check('feedback: 불필요 판정은 놓침 신호 아님', open(f'{T}/missed.txt', encoding='utf-8').read() == '', out)

print(f'\n{"전부 통과" if not fails else "실패 " + ", ".join(fails)}')
sys.exit(1 if fails else 0)
