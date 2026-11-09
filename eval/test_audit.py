#!/usr/bin/env python3
"""주간 놓침 감사(build.py audit)·감사 판정의 개선 신호 연결(feedback)·필수 문항(cases·score.py) 검사. 네트워크 없음.

  python3 eval/test_audit.py      (score.py 필수 문항 검사에 기본 스냅샷 prep을 씀)
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

# 감사 놓침 → 정답 줄의 호는 기사 공개일 뒤 첫 회차(그 회차 스냅샷이 평가 세트가 됨)
doc('items', 'i035-01', {'issue': 35, 'n': 1, 'tier': 'ref', 'url': 'https://z.example/1', 'headline': 'z', 'date': '2026-11-12'})
code, out = run('feedback', f'{T}/fb', '2026-11-13T00:00:00Z')
g = [l for l in open(f'{T}/gold.txt', encoding='utf-8').read().splitlines() if U4 in l]
check('feedback: 감사 놓침 정답 줄은 공개일(11-11) 뒤 첫 회차 제035호', g and g[0].startswith('35 | '), str(g) + out)

# cases: 감사 놓침은 스냅샷 후보에 있으면 필수(must) 판정 문항, 없으면 수집 공백(known_gap, 게이트 제외)
S = f'{T}/snapshot-x-035'; os.makedirs(S)
open(f'{S}/candidates.md', 'w', encoding='utf-8').write(f'c1 | 3 | 제목 | {U4}\n')
open(f'{T}/gold_c.txt', 'w', encoding='utf-8').write(
    f'35 | k | {U4} | 수록 | 감사 놓침 확인: 배터리 보험\n35 | k2 | https://example.kr/not-collected | 수록 | 감사 놓침 확인: 미수집\n35 | k3 | https://example.com/u | 제외 | 사용자 평가\n')
code, out = run('cases', S, f'{T}/gold_c.txt', f'{T}/cases_035.json')
cs = json.load(open(f'{T}/cases_035.json', encoding='utf-8'))['cases'] if code == 0 else []
check('cases: 후보에 있는 감사 놓침은 필수 문항', len(cs) == 3 and cs[0].get('must') is True and not cs[0].get('known_gap'), out + json.dumps(cs, ensure_ascii=False))
check('cases: 후보에 없는 감사 놓침은 수집 공백(게이트 제외)', len(cs) == 3 and cs[1].get('known_gap') is True and not cs[1].get('must'), json.dumps(cs, ensure_ascii=False))
check('cases: 일반 평가 문항은 그대로', len(cs) == 3 and not cs[2].get('must') and not cs[2].get('known_gap') and cs[2]['expect'] == {'decision': '제외'})

# score.py: 필수 문항이 과반 실행에서 틀리면 종료 2, 과반 통과면 0
SNAP = 'snapshot-20261001'
cand = subprocess.run([sys.executable, f'{REPO}/eval/score.py', '--prep-only'], capture_output=True, text=True, env={**os.environ, 'EV_W': f'{T}/sp'})
import re as _re
u = _re.search(r'https?://\S+', open(f'{T}/sp/candidates.md', encoding='utf-8').read().split('## ')[1]).group(0) if cand.returncode == 0 else ''
m = _re.sub(r'^https?://(www\.|m\.)?', '', u).rstrip('/')[:120]
json.dump({'snapshot': SNAP, 'cases': [{'id': 'M01', 'layer': 'judge', 'must': True, 'match': m, 'expect': {'decision_in': ['핵심', '참고']}}]},
          open(f'{T}/cases_must.json', 'w', encoding='utf-8'), ensure_ascii=False)
item = {'tier': 'ref', 'url': u, 'relevance': 1}
for name, items in (('hit', [item]), ('miss', [])):
    json.dump({'items': items}, open(f'{T}/br_{name}.json', 'w', encoding='utf-8'))
sc = lambda *bs: subprocess.run([sys.executable, f'{REPO}/eval/score.py', '--cases', f'{T}/cases_must.json'] + [x for b_ in bs for x in ('--briefing', f'{T}/br_{b_}.json')],
                                capture_output=True, text=True, env={**os.environ, 'EV_W': f'{T}/sp'})
r1, r2, r3 = sc('hit'), sc('miss'), sc('hit', 'miss', 'miss')
check('score.py: 필수 문항 통과 종료 0', bool(u) and r1.returncode == 0 and '필수 1/1' in r1.stdout, r1.stdout + r1.stderr)
check('score.py: 필수 문항 실패 종료 2', r2.returncode == 2 and '필수 문항 실패: M01' in r2.stdout, r2.stdout + r2.stderr)
check('score.py: 여러 실행은 과반으로(1/3 통과면 실패)', r3.returncode == 2 and '1/3회 통과' in r3.stdout, r3.stdout + r3.stderr)
r4 = sc('hit', 'hit', 'miss')
check('score.py: 2/3 통과면 통과', r4.returncode == 0 and '(3회 과반)' in r4.stdout, r4.stdout + r4.stderr)

print(f'\n{"전부 통과" if not fails else "실패 " + ", ".join(fails)}')
sys.exit(1 if fails else 0)
