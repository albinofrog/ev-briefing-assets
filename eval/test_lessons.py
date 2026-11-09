#!/usr/bin/env python3
"""교훈 장부 자동 갱신(build.py lessons attach) 검사. 네트워크 없음.

  python3 eval/test_lessons.py
"""
import os, sys, json, shutil, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = '/tmp/evlessontest'
fails = []


def check(name, cond, info=''):
    print(f"{'PASS' if cond else 'FAIL'} {name}" + (f' | {info}' if info and not cond else ''))
    if not cond: fails.append(name)


def run(*a):
    r = subprocess.run([sys.executable, f'{REPO}/build.py', *a], capture_output=True, text=True, env={**os.environ, 'EV_W': T})
    return r.returncode, r.stdout + r.stderr


def les(): return {l.split(' | ')[0]: l.split(' | ') for l in open(f'{T}/lessons.md', encoding='utf-8').read().splitlines() if l.strip()}


def setup(lessons, signals, attach=None):
    shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
    json.dump({'issue': 39, 'start': '2026-12-01T22:10:00+00:00', 'cutoff': '2026-11-28T22:10:00+00:00'}, open(f'{T}/state.json', 'w'))
    pub = lambda d, i: f'{d} | {i} | 핵심 1 참고 2 | 웹 10 | 평가 0 유용 0'
    open(f'{T}/metrics.md', 'w').write('\n'.join(pub(f'2026-11-{d:02d}', d) for d in range(1, 30)) + '\n')  # 발행 29회차(호 1~29)
    open(f'{T}/lessons.md', 'w', encoding='utf-8').write('\n'.join(lessons) + '\n')
    open(f'{T}/signals.md', 'w', encoding='utf-8').write('\n'.join(signals) + '\n')
    if attach is not None: open(f'{T}/attach.tsv', 'w').write('\n'.join(attach) + '\n')


BASE = ['L1 | 관찰 | 관련성 | judge | FP | 2 | 제039호 https://a.example/1 x | 관찰 지표: FP | 5',
        'L2 | 관찰 | 운영 | meta | OPS:본문차단 | 3 | 제039호 fleetnews robots | 관련12본문 | 3',
        'L3 | 거절(메모 없음) | 운영 | code | OPS:장기-수집실패 | 0 | 제006호 https://old.example/feed 장기 실패 | 수집실패; 거절 제007호 | 1',
        'L4 | 관찰 | 충분성 | auto | MISS-P:C1 | 1 | 제030호 https://p.example/z | 놓침 | 20',
        'L5 | 관찰 | 충분성 | auto | MISS-P:C1 | 1 | 제031호 https://q.example/z | 놓침 | 21']
SIG = ['FP | 제040호 | 기사 A | https://a.example/2 | R3 참고 | ',          # 1 L1에 붙음
       'FP | 제040호 | 기사 A 다시 | https://a.example/1 | R3 참고 | ',      # 2 이미 센 URL
       'OPS:본문차단 | - | motortradenews client_error | - | - | c14',     # 3 L2 +1
       'OPS:본문차단 | - | am-online robots | - | - | c20',                # 4 같은 회차 URL 없는 신호는 한 번
       'MISS-U:C7 | - | 수록됨 | https://r.example/1 | - | 이번 호 수록 묶음',  # 5 버림
       'OVER | 제040호 | 기사 B | https://b.example/1 | R1 핵심 | 메모',     # 6 새 교훈(관련성·judge)
       'OPS:장기-수집실패 | - | 같은 장기 실패 | - | - | -',                # 7 메모 없는 거절, URL 없는 같은 근거 → 버림(발행 29회차 지남 → 재상정)
       'MISS-P:C1 | - | 새 놓침 | https://s.example/1 | - | 목록 밖']     # 8 후보 L4·L5 둘 → 선택 필요
setup(BASE, SIG)
code, out = run('lessons', 'attach')
check('attach: 같은 원인 코드 교훈이 여럿이면 선택 필요(종료 3, 아무것도 안 씀)', code == 3 and '8\t?' in out and les()['L1'][5] == '2', out)
setup(BASE, SIG, ['8\tL5'])
code, out = run('lessons', 'attach')
d = les()
check('attach: 새 URL은 관찰 +1, 근거 맨 앞에 이번 호', code == 0 and d['L1'][5] == '3' and d['L1'][6].startswith('제040호 https://a.example/2'), out)
check('attach: 이미 센 URL은 다시 안 셈', out.count('이미 센 근거') >= 1 and d['L1'][5] == '3', out)
check('attach: URL 없는 OPS 신호는 회차당 한 번', d['L2'][5] == '4', out)
check('attach: 수록됨(C7)은 버림', '수록됨이라 버림' in out, out)
check('attach: 새 교훈은 다음 번호·관찰 1회·코드별 목표·계층·시작 회차(metrics 줄 수+1)', 'L6' in d and d['L6'][1:6] == ['관찰', '관련성', 'judge', 'OVER', '1'] and d['L6'][-1] == '30', str(d.get('L6')))
check('attach: 메모 없는 거절은 거절 뒤 발행 10회차 넘게 재발하면 한 번 재상정', d['L3'][1] == '관찰' and d['L3'][5] == '1' and '재상정' in d['L3'][6], str(d['L3']))
check('attach: 선택(attach.tsv)대로 붙임', d['L5'][5] == '2' and d['L4'][5] == '1', out)
code, out = run('lessons', 'attach')
d2 = les()
check('attach: 같은 신호로 다시 돌려도 더 세지 않음(재상정 한 번만)', code == 0 and d2['L1'][5] == '3' and d2['L2'][5] == '4' and d2['L3'][5] == '1' and d2['L5'][5] == '2', out)

setup(BASE, ['GOAL:핵심원출처 | - | 핵심원출처 값 0%(목표 50) | - | - | 이번 회차'])
code, out = run('lessons', 'attach')
check('attach: 맞는 교훈 없는 GOAL 신호는 목표·계층 선택 필요', code == 3 and 'new\t<목표>' in out, out)
setup(BASE, ['GOAL:핵심원출처 | - | 핵심원출처 값 0%(목표 50) | - | - | 이번 회차'], ['1\tnew\t신뢰성\tjudge'])
code, out = run('lessons', 'attach')
check('attach: 선택한 목표·계층으로 새 교훈', code == 0 and les()['L6'][1:5] == ['관찰', '신뢰성', 'judge', 'GOAL:핵심원출처'], out)
setup(['L1 | 관찰 | 관련성 | judge | FP | 1 | ' + '; '.join(f'제0{i:02d}호 https://e.example/{i} 긴 근거 문장입니다' * 3 for i in range(40)) + ' | 관찰 지표: FP | 5'],
      ['FP | 제040호 | 새 | https://e.example/new | R3 | '])
code, out = run('lessons', 'attach')
ev = les()['L1'][6]
check('attach: 근거 칸이 길면 오래된 근거부터 생략', code == 0 and len(ev) <= 1500 + 20 and ev.endswith('이전 근거 생략') and ev.startswith('제040호'), str(len(ev)))
# 왕복 방지(propcheck): p3 적용 → p19 되돌림 → p22 재적용 같은 세 번째 전환은 마지막 전환 뒤 발행 20회차 안이면 사용자 근거 없이는 막음
E1 = [{'file': 'rules.md', 'old': 'WebSearch 1회와', 'new': 'WebSearch 1회(site:공식 도메인)와'}]
INV = [{'file': 'rules.md', 'old': 'WebSearch 1회(site:공식 도메인)와', 'new': 'WebSearch 1회와'}]
def prop(i, st, at, ed, ev='', title=''):
    os.makedirs(f'{T}/fb/proposals', exist_ok=True)
    json.dump({'id': i, 'data': {'status': st, 'applied_at': at, 'edits': ed, 'evidence': ev, 'title': title or i}}, open(f'{T}/fb/proposals/{i}.json', 'w'), ensure_ascii=False)
setup(BASE, [])
prop('p3', 'applied', '2026-11-01T00:00:00Z', E1); prop('p19', 'applied', '2026-11-20T00:00:00Z', INV)
prop('p30', 'pending', None, [{'file': 'rules.md', 'old': '- 3: 나머지. 관세', 'new': '- 3: 나머지(수정). 관세'}])
json.dump([{'id': 'p40', 'title': 'p3 재상정', 'evidence': 'effect 재판정', 'edits': E1},
           {'id': 'p41', 'title': 'p3 재상정(사용자)', 'evidence': '사용자 보드 평가 과소 2건', 'edits': E1},
           {'id': 'p42', 'title': '같은 줄', 'evidence': 'x', 'edits': [{'file': 'rules.md', 'old': '- 3: 나머지. 관세', 'new': 'y'}]},
           {'id': 'p43', 'title': '다른 줄', 'evidence': 'x', 'edits': [{'file': 'rules.md', 'old': '전혀 다른 줄', 'new': 'z'}]}],
          open(f'{T}/proposals_new.json', 'w'), ensure_ascii=False)
code, out = run('propcheck', f'{T}/fb')
left = [x['id'] for x in json.load(open(f'{T}/proposals_new.json'))]
check('propcheck: 두 번 오간 수정을 사용자 근거 없이 또 바꾸면 제외(p40)', 'p40' not in left and '2번 오감' in out, out)
check('propcheck: 사용자 근거가 있으면 통과(p41)', 'p41' in left, out)
check('propcheck: 대기 중 개선안과 같은 줄이면 제외(p42)', 'p42' not in left and 'p30(대기 중)' in out, out)
check('propcheck: 다른 줄은 통과(p43)', 'p43' in left, out)
json.dump([{'id': 'p44', 'title': 'p3 되돌림', 'evidence': 'effect 악화', 'edits': INV}], open(f'{T}/proposals_new.json', 'w'), ensure_ascii=False)
os.remove(f'{T}/fb/proposals/p19.json')
code, out = run('propcheck', f'{T}/fb')
check('propcheck: 처음 되돌림(한 번 반영된 수정)은 통과', [x['id'] for x in json.load(open(f'{T}/proposals_new.json'))] == ['p44'], out)

code, out = run('lessons', 'push') if os.path.exists(f'{T}/lessons_base.json') else (0, '')
print(f'\n{"전부 통과" if not fails else "실패 " + ", ".join(fails)}')
sys.exit(1 if fails else 0)
