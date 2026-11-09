#!/usr/bin/env python3
"""회차 절차 점검(checklist·정상 종료 기록)과 그림자 판정(shadowrules·shadow·shadowscore·feedback 정답) 검사. 네트워크 없음.

  python3 eval/test_shadow.py
"""
import os, sys, json, shutil, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = '/tmp/evshadowtest'
fails = []


def check(name, cond, info=''):
    print(f"{'PASS' if cond else 'FAIL'} {name}" + (f' | {info}' if info and not cond else ''))
    if not cond: fails.append(name)


def run(*a):
    r = subprocess.run([sys.executable, f'{REPO}/build.py', *a], capture_output=True, text=True, env={**os.environ, 'EV_W': T})
    return r.returncode, r.stdout + r.stderr


def doc(coll, i, data):
    os.makedirs(f'{T}/fb/{coll}', exist_ok=True)
    json.dump({'id': i, 'data': data}, open(f'{T}/fb/{coll}/{i}.json', 'w', encoding='utf-8'), ensure_ascii=False)


shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
shutil.copy(f'{REPO}/rules.md', T)
json.dump({'issue': 40, 'start': '2026-12-01T22:10:00+00:00', 'cutoff': '2026-11-28T22:10:00+00:00'}, open(f'{T}/state.json', 'w'))

# 1. 정상 종료 기록과 절차 점검
code, out = run('nextid', f'{T}/fb')
check('정상 종료한 명령은 .done에 기록', code == 0 and 'nextid' in open(f'{T}/.done').read(), out)
code, out = run('trace')  # 인자 부족으로 실패
check('실패한 명령은 기록 안 함', 'trace' not in open(f'{T}/.done').read(), out)
code, out = run('checklist')
check('checklist: 누락 있으면 종료 1, 단계 위치 표시', code == 1 and 'prep(나.5)' in out and 'promote(improve 4)' in out, out)
open(f'{T}/.done', 'w').write('\n'.join(['ledger-merge', 'prep', 'snapcap', 'coverage', 'check', 'render', 'board', 'probe', 'scorecard']) + '\n')
code, out = run('checklist', 'noboard', 'nodeliver')
check('checklist: 끈 조건(보드 못 읽음·전달 없음)의 단계는 빼고 다 했으면 종료 0', code == 0 and '누락 없음' in out, out)
code, out = run('checklist', 'nodeliver')
check('checklist: 보드를 읽었으면 lessons·promote 누락을 잡음', code == 1 and 'lessons-attach(improve 2)' in out and 'promote(improve 4)' in out, out)

# 2. 그림자 판정
line = [l for l in open(f'{T}/rules.md', encoding='utf-8').read().splitlines() if l.startswith('  - 3: 나머지.')][0]
doc('proposals', 'p50', {'title': '교환 제휴 관련도 2', 'layer': 'judge', 'status': 'pending', 'edits': [{'file': 'rules.md', 'old': line, 'new': line + ' (시험)'}]})
doc('proposals', 'p51', {'title': '없는 문구', 'layer': 'judge', 'status': 'pending', 'edits': [{'file': 'rules.md', 'old': '없는 문구', 'new': 'x'}]})
code, out = run('shadowrules', 'p50', f'{T}/fb')
check('shadowrules: 개선안 edits를 rules.md 사본에 적용', code == 0 and '(시험)' in open(f'{T}/rules_shadow_p50.md', encoding='utf-8').read() and '(시험)' not in open(f'{T}/rules.md', encoding='utf-8').read(), out)
code, out = run('shadowrules', 'p51', f'{T}/fb')
check('shadowrules: 적용 안 되는 개선안은 실패', code != 0 and '0곳' in out, out)
open(f'{T}/candidates.md', 'w', encoding='utf-8').write('## 점수 2 (2)\nc1 | 점수 2 | 11-30 | 교환 제휴 A | x.com | https://x.example/a\nc2 | 점수 2 | 11-30 | 교환 제휴 B | y.com | https://y.example/b\n   ↳ c2-1 | 11-30 | 교환 제휴 B 다른 보도 | z.com | https://z.example/b\n')
open(f'{T}/decisions.tsv', 'w', encoding='utf-8').write('c1\ty\t참고\t관련도 3\nc2\ty\t제외\t축 밖\nc2-1\tn\t제외\t같은 사건\n')
open(f'{T}/shadow_p50.tsv', 'w', encoding='utf-8').write('c1\t핵심\t새 규칙에서 관련도 2\nc2\t제외\t같음\nc9\t참고\t없는 후보\n')
code, out = run('shadow', 'p50', f'{T}/fb')
w = json.load(open(f'{T}/shadow_board.json', encoding='utf-8')) if code == 0 else [{}]
cs = w[0].get('data', {}).get('cases', [])
check('shadow: 결정이 달라진 후보만 사례로(제목·URL·기존·새 결정)', code == 0 and len(cs) == 1 and cs[0]['cand'] == 'c1' and cs[0]['url'] == 'https://x.example/a' and (cs[0]['base'], cs[0]['new']) == ('참고', '핵심')
      and w[0]['doc_id'] == 'sh041-p50', out + json.dumps(w, ensure_ascii=False))
check('shadow: 같은 결정·없는 후보는 버림', '버림 c2' in out and '버림 c9' in out, out)
doc('shadow', 'sh039-p50', {'proposal': 'p50', 'issue': 39, 'n': 5, 'cases': [{'k': i, 'cand': f'c{i}', 'url': f'https://o.example/{i}', 'base': '참고', 'new': '핵심'} for i in range(1, 6)]})
code, out = run('shadow', 'p50', f'{T}/fb')
check(f'shadow: 사례가 상한(5)만큼 모이면 더 안 모음', json.load(open(f'{T}/shadow_board.json'))[0]['data']['n'] == 0, out)
for i, v in ((1, 'new'), (2, 'new'), (3, 'base')):
    doc('shadow_fb', f'sh039-p50-{i}', {'verdict': v, 'at': '2026-12-02T00:00:00Z'})
code, out = run('shadowscore', f'{T}/fb')
check('shadowscore: 개선안별 사례 판정 집계', 'p50 | 새 규칙이 맞음 2 · 지금 규칙이 맞음 1 · 판정 대기 2 | 새 규칙 우세' in out, out)
doc('items', 'i039-01', {'issue': 39, 'n': 1, 'tier': 'ref', 'url': 'https://q.example', 'headline': 'q', 'date': '2026-11-30'})
code, out = run('feedback', f'{T}/fb', '2026-12-01T00:00:00Z')
g = open(f'{T}/gold.txt', encoding='utf-8').read()
check('feedback: 사례 판정은 고른 쪽 결정으로 평가 세트 정답 줄', '39 | ' in g and 'https://o.example/1 | 핵심 | 사례 판정(p50)' in g and 'https://o.example/3 | 참고 | 사례 판정(p50)' in g, g)

print(f'\n{"전부 통과" if not fails else "실패 " + ", ".join(fails)}')
sys.exit(1 if fails else 0)
