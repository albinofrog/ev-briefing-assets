#!/usr/bin/env python3
"""수집·점수 건강 검사(build.py collect_collapse·score_selftest·selftest) 검사. 네트워크 없음.

  python3 eval/test_health.py
"""
import os, sys, json, shutil, subprocess, importlib.util, datetime as dt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = '/tmp/evhealthtest'
fails = []


def check(name, cond, info=''):
    print(f"{'PASS' if cond else 'FAIL'} {name}" + (f' | {info}' if info and not cond else ''))
    if not cond: fails.append(name)


shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
shutil.copy(f'{REPO}/sources.md', T)
os.environ['EV_W'] = T
spec = importlib.util.spec_from_file_location('b', f'{REPO}/build.py'); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

U = dt.timezone.utc
start = dt.datetime(2026, 11, 20, 22, 10, tzinfo=U)
def write(rows):
    with open(f'{T}/items.jsonl', 'w') as f:
        for k, t in rows: f.write(json.dumps({'key': 'x', 'first_seen': t.isoformat().replace('+00:00', 'Z'), 'kind': k}) + '\n')
hours = lambda days: [start - dt.timedelta(hours=h) for h in range(1, 24 * days)]
normal = [(k, t) for k in ('list', 'watch') for t in hours(16) for _ in range(2)]  # 시간당 2건씩 16일
write(normal)
c, msg = b.collect_collapse(start)
check('수집량: 평소와 같으면 경보 없음', c is False and msg == '', msg)
write([(k, t) for k, t in normal if not (k == 'watch' and t >= start - dt.timedelta(hours=60))])  # 검색 경로만 60시간 끊김
c, msg = b.collect_collapse(start)
check('수집량: 한 경로가 끊기면 그 경로 경보(watch)', c is True and 'watch' in msg and 'list' not in msg, msg)
write([(k, t) for k, t in normal if t < start - dt.timedelta(hours=72) or t.hour % 12 == 0])  # 72시간 동안 1/12로 줄어듦(8%)
c, msg = b.collect_collapse(start)
check('수집량: 평소의 15% 미만이면 경보', c is True, msg)
write([(k, t) for k, t in normal if t >= start - dt.timedelta(days=3)])  # 이력이 3일뿐
c, msg = b.collect_collapse(start)
check('수집량: 이력이 짧으면 판단 안 함', c is False, msg)

check('점수 자체 검사: 현재 규칙 통과', b.score_selftest() == [], str(b.score_selftest()))
import re
b.R1 = re.compile(r'\\bSOH\\b')  # raw 문자열이 아닌 \b 같은 고장(11-03 L41)
bad = b.score_selftest()
check('점수 자체 검사: 정규식 고장은 실패로 잡음', len(bad) >= 5 and any('SOH' in x or 'residual' in x.lower() for x in bad), str(bad))

r = subprocess.run([sys.executable, f'{REPO}/build.py', 'selftest'], capture_output=True, text=True, env={**os.environ, 'EV_W': T})
check('selftest(gate가 code 개선안 반영 전에 돌림): 중복 대조·점수 규칙 모두 통과', r.returncode == 0 and '점수 규칙: 통과' in r.stdout, r.stdout + r.stderr)

shutil.copy(f'{REPO}/build.py', f'{T}/build.py')
src = open(f'{T}/build.py', encoding='utf-8').read()
fx = [l for l in src.splitlines() if 'Fed raises' in l][0]
check('건강 검사 기준(SCORE_FIXTURE)은 개선안으로 못 고침(measure_touch)', b.measure_touch([{'file': 'build.py', 'old': fx, 'new': '    ]'}]) is True)
cl = [l for l in src.splitlines() if l.startswith('COLLAPSE = ')][0]
check('건강 검사 기준(COLLAPSE)은 개선안으로 못 고침', b.measure_touch([{'file': 'build.py', 'old': cl, 'new': cl.replace('0.15', '0.01')}]) is True)

print(f'\n{"전부 통과" if not fails else "실패 " + ", ".join(fails)}')
sys.exit(1 if fails else 0)
