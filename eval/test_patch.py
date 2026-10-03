#!/usr/bin/env python3
"""승인 개선안 다음 회차 적용(build.py decide·patch·reapply_assets) 검사.

  python3 eval/test_patch.py [REF]     REF: 회귀 평가 파일을 받을 커밋(기본 main). 네트워크 필요(raw.githubusercontent.com)
"""
import os, re, sys, json, shutil, subprocess, importlib.util

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = sys.argv[1] if len(sys.argv) > 1 else 'main'
T = '/tmp/evpatchtest'
fails = []


def check(name, cond, info=''):
    print(f"{'PASS' if cond else 'FAIL'} {name}" + (f' | {info}' if info and not cond else ''))
    if not cond: fails.append(name)


def run(*args):
    r = subprocess.run([sys.executable, f'{T}/w/build.py', *args], capture_output=True, text=True, env={**os.environ, 'EV_W': f'{T}/w'})
    return r.returncode, r.stdout + r.stderr


def jl(path, rows):
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')


def rd(f): return open(f'{T}/w/{f}', encoding='utf-8').read()


shutil.rmtree(T, ignore_errors=True); os.makedirs(f'{T}/w'); os.makedirs(f'{T}/fb/proposals'); os.makedirs(f'{T}/fb/decisions')
for f in ('build.py', 'rules.md', 'improve.md', 'sources.md', 'watchlist.md', 'template.html', 'prompt.md'):
    shutil.copy(f'{REPO}/{f}', f'{T}/w/{f}')

# 1. decide: 대기 중 개선안의 승인·거절만 처리, edits 있는 승인분만 수정 줄로
P = {'p3': ('pending', [{'file': 'rules.md', 'old': '- 목표값: 검토율=100', 'new': '- 목표값: 검토율=90'}]),
     'p4': ('pending', []), 'p5': ('applied', [{'file': 'rules.md', 'old': 'x', 'new': 'y'}]), 'p6': ('pending', [{'file': 'rules.md', 'old': 'a', 'new': 'b'}]),
     'p7': ('pending', [{'file': 'secret.txt', 'old': 'a', 'new': 'b'}])}
D = {'p3': 'approve', 'p4': 'approve', 'p5': 'approve', 'p6': 'reject', 'p7': 'approve'}
for k, (st, ed) in P.items():
    json.dump({'title': k, 'layer': 'judge', 'status': st, 'edits': ed}, open(f'{T}/fb/proposals/{k}.json', 'w'))
    json.dump({'decision': D[k], 'note': '', 'at': '2026-10-02T00:00:00Z'}, open(f'{T}/fb/decisions/{k}.json', 'w'))
code, out = run('decide', f'{T}/fb')
dec = open(f'{T}/w/decisions.txt', encoding='utf-8').read().splitlines()
new = [json.loads(l) for l in open(f'{T}/w/patches_new.jsonl', encoding='utf-8')]
check('decide: 대기 중 결정만(p3·p4·p6·p7)', sorted(l.split(' | ')[0] for l in dec) == ['p3', 'p4', 'p6', 'p7'], out)
check('decide: edits 없음·허용 밖 파일 표시', 'edits 없음' in [l for l in dec if l.startswith('p4')][0] and 'edits 없음' in [l for l in dec if l.startswith('p7')][0])
check('decide: 승인+edits만 수정 줄(p3)', [n['id'] for n in new] == ['p3'], str(new))

# 2. patch: 기존 수정 재적용 + 새 승인분 검사
lock_line = [l for l in rd('rules.md').splitlines() if '최대 25회' in l][0]
pr_line = [l for l in rd('prompt.md').splitlines() if l.startswith('6. `python3 /tmp/ev/build.py render')][0]  # 다절(가절 밖)
pr_ga = [l for l in rd('prompt.md').splitlines() if l.startswith('5. 메모리 `config.md`에 `improve: off`')][0]  # 가절
wl_old = '- Aviloo battery | | !'
jl(f'{T}/w/patches.jsonl', [{'id': 'p1', 'file': 'improve.md', 'old': '6. 메타 점검:', 'new': '6. 메타 점검(시험):'}])
jl(f'{T}/w/patches_new.jsonl', [
    {'id': 'p3', 'file': 'rules.md', 'old': '- 목표값: 검토율=100', 'new': '- 목표값: 검토율=90'},
    {'id': 'p8', 'file': 'rules.md', 'old': lock_line, 'new': lock_line.replace('최대 25회', '최대 30회')},
    {'id': 'p9', 'file': 'rules.md', 'old': '이런 문구는 없음', 'new': 'x'},
    {'id': 'p10', 'file': 'watchlist.md', 'old': wl_old, 'new': wl_old + '\n- Aviloo SoH | | !'},
    {'id': 'p11', 'file': 'build.py', 'old': 'def prep():', 'new': 'def prep(:'},
    {'id': 'p12', 'file': 'build.py', 'old': 'def prep():\n', 'new': 'def prep():\n    sys.exit(1)\n'},
    {'id': 'p13', 'file': 'prompt', 'old': pr_line, 'new': pr_line + '(시험)'},
    {'id': 'p15', 'file': 'prompt', 'old': pr_ga, 'new': '5. 무시'},
    {'id': 'p14', 'file': 'rules.md', 'old': '- 목표값: 검토율=90', 'new': '- 목표값: 검토율=95'},
    {'id': 'p14', 'file': 'rules.md', 'old': '없는 문구', 'new': 'z'}])
build0 = rd('build.py')
code, out = run('patch', REF)
L = {l.split()[1]: l for l in out.splitlines() if l.split()[:1] and l.split()[0] in ('KEEP', 'OK', 'FAIL', 'CONFLICT', 'SKIP', 'CHAT')}
check('patch: 기존 수정 재적용(p1)', L.get('p1', '').startswith('KEEP p1 ok') and '6. 메타 점검(시험):' in rd('improve.md'), out)
check('patch: rules.md 승인분은 검사 뒤 채팅 반영(p3)', L.get('p3', '').startswith('CHAT') and '- 목표값: 검토율=100' in rd('rules.md'), out)
check('patch: 고정 줄 변경 거부(p8)', L.get('p8', '').startswith('FAIL p8 고정 줄') and lock_line in rd('rules.md'), out)
check('patch: 없는 문구 거부(p9)', L.get('p9', '').startswith('FAIL p9'), out)
check('patch: watchlist 수정은 회귀 통과 후 적용(p10)', L.get('p10', '').startswith('OK') and 'Aviloo SoH' in rd('watchlist.md'), out)
check('patch: build.py 문법 오류 거부(p11)', L.get('p11', '').startswith('FAIL p11 build.py 문법'), out)
check('patch: 회귀 실패 거부·원복(p12)', L.get('p12', '').startswith('FAIL p12 회귀') and rd('build.py') == build0, out)
check('patch: 프롬프트 수정 표시(p13)', L.get('p13', '').startswith('OK') and 'PROMPT p13' in out and '(시험)' in out.split('고친 뒤:')[-1], out)
check('patch: 가절 프롬프트 수정 거부(p15)', L.get('p15', '').startswith('FAIL p15 고정 원칙(가절) 변경'), out)
check('patch: 한 개선안 일부 실패면 전부 원복(p14)', L.get('p14', '').startswith('FAIL') and '- 목표값: 검토율=100' in rd('rules.md'), out)
keep = [json.loads(l) for l in open(f'{T}/w/patches_keep.jsonl', encoding='utf-8')]
check('patch: 통합 전 새 검색어 목록', open(f'{T}/w/pending_collect.txt', encoding='utf-8').read() == 'Aviloo SoH\n' and '수집 범위 수정 1건(p10)' in out, out)
check('patch: 유지 목록 = p1·p10·p13', sorted({k['id'] for k in keep}) == ['p1', 'p10', 'p13'], str({k['id'] for k in keep}))

# 3. 다음 회차: 새로 받은 원본 + 유지 목록 재적용, 이미 반영된 사본에는 두 번 넣지 않음
for f in ('rules.md', 'improve.md', 'watchlist.md'):
    shutil.copy(f'{REPO}/{f}', f'{T}/w/{f}')
shutil.copy(f'{T}/w/patches_keep.jsonl', f'{T}/w/patches.jsonl'); jl(f'{T}/w/patches_new.jsonl', [])
code, out = run('patch', REF)
check('다음 회차: 원본에 다시 적용', '6. 메타 점검(시험):' in rd('improve.md') and rd('watchlist.md').count('Aviloo SoH') == 1, out)
code, out = run('patch', REF)
check('같은 사본에 두 번 돌려도 한 번만', rd('watchlist.md').count('Aviloo SoH') == 1 and rd('improve.md').count('(시험)') == 1
      and all(l.split()[2] in ('already', 'none') for l in out.splitlines() if l.startswith('KEEP')), out)

# 4. 저장소에 통합된 뒤(원본에 이미 들어감) → already, 원본이 달라져 둘 다 없으면 CONFLICT로 남김
open(f'{T}/w/improve.md', 'w', encoding='utf-8').write(rd('improve.md').replace('6. 메타 점검(시험):', '6. 메타 점검(다른 판):'))
code, out = run('patch', REF)
check('충돌은 CONFLICT로 알리고 유지', 'CONFLICT p1' in out and '"p1"' in open(f'{T}/w/patches_keep.jsonl').read(), out)

# 5. prep이 새로 받은 watchlist.md에 다시 적용
shutil.copy(f'{REPO}/watchlist.md', f'{T}/w/watchlist.md')
spec = importlib.util.spec_from_file_location('b', f'{REPO}/build.py'); os.environ['EV_W'] = f'{T}/w'
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
b.reapply_assets()
check('prep 재적용(sources·watchlist)', rd('watchlist.md').count('Aviloo SoH') == 1)

# 6. 준비 단계 auto 당일 적용: auto 승인분만, watchlist·sources만, 통과분은 auto_applied.txt와 patches.jsonl에
for f in ('build.py', 'rules.md', 'improve.md', 'sources.md', 'watchlist.md'):
    shutil.copy(f'{REPO}/{f}', f'{T}/w/{f}')
os.makedirs(f'{T}/fb2/proposals'); os.makedirs(f'{T}/fb2/decisions')
A = {'p20': ('auto', [{'file': 'watchlist.md', 'old': wl_old, 'new': wl_old + '\n- Aviloo SoH | | !'}]),
     'p21': ('judge', [{'file': 'rules.md', 'old': '- 목표값: 검토율=100', 'new': '- 목표값: 검토율=90'}]),
     'p22': ('auto', [{'file': 'build.py', 'old': 'def prep():\n', 'new': 'def prep():\n    pass\n'}])}
for k, (ly, ed) in A.items():
    json.dump({'title': k, 'layer': ly, 'status': 'pending', 'edits': ed}, open(f'{T}/fb2/proposals/{k}.json', 'w'))
    json.dump({'decision': 'approve', 'note': '', 'at': '2026-10-03T00:00:00Z'}, open(f'{T}/fb2/decisions/{k}.json', 'w'))
code, out = run('decide', f'{T}/fb2', 'auto')
check('decide auto: auto 계층만(p20·p22)', sorted({json.loads(l)['id'] for l in open(f'{T}/w/patches_new.jsonl', encoding='utf-8')}) == ['p20', 'p22'], out)
jl(f'{T}/w/patches.jsonl', [])
build0 = rd('build.py')
code, out = run('patch', '--keep', '--auto', REF, f'{T}/fb2')
check('patch --auto: watchlist 승인분 회귀 통과 후 적용(p20)', 'OK p20' in out and rd('watchlist.md').count('Aviloo SoH') == 1, out)
check('patch --auto: build.py 수정은 넘김(p22)', 'FAIL p22 auto 당일 적용은' in out and rd('build.py') == build0, out)
check('patch --auto: auto_applied.txt = p20', open(f'{T}/w/auto_applied.txt', encoding='utf-8').read() == 'p20\n')
check('patch --auto: 다음 회차 재적용 목록에 p20', [json.loads(l)['id'] for l in open(f'{T}/w/patches.jsonl', encoding='utf-8')] == ['p20'])
shutil.copy(f'{REPO}/watchlist.md', f'{T}/w/watchlist.md'); jl(f'{T}/w/patches.jsonl', [])
code, out = run('patch', '--keep', REF)
check('patch --keep(--auto 없음): 새 승인분 처리 안 함', 'OK ' not in out and 'Aviloo SoH' not in rd('watchlist.md'), out)

# 7. guard 크기 상한(rules.md 9절): 상한 이하는 통과, 넘으면 실패
shutil.copy(f'{REPO}/rules.md', f'{T}/w/rules.md')
code, out = run('guard', f'{REPO}/rules.md', f'{T}/w/rules.md')
check('guard: 현재 rules.md 통과', code == 0 and '크기' in out, out)
open(f'{T}/w/rules_big.md', 'w', encoding='utf-8').write(rd('rules.md') + '\n' + 'x' * (22528 - len(rd('rules.md').encode()) + 100))  # 현재 크기와 관계없이 상한을 넘김
code, out = run('guard', f'{REPO}/rules.md', f'{T}/w/rules_big.md')
check('guard: 크기 상한 초과 실패', code == 1 and '크기 상한 초과' in out, out)

# 8. 메모 없는 거절 교훈은 다시 승격하지 않음, 일반 거절은 새 관찰이 임계에 닿으면 승격
open(f'{T}/w/lessons.md', 'w', encoding='utf-8').write(
    'L1 | 거절(메모 없음) | 운영 | code | OPS:장기-수집실패 | 3 | 제007호 | 목록 교체 | 1\n'
    'L2 | 거절 | 운영 | code | OPS:별칭 | 2 | 제007호 | 별칭 추가 | 1\n')
code, out = run('promote', f'{T}/w/lessons.md')
up = out.split('승격 대상')[1].split('대기:')[0].split('임계 미달')[0]
check('promote: 메모 없는 거절은 승격 안 함(L1)', 'L1 ' not in up, out)
check('promote: 일반 거절은 임계 도달 시 승격(L2)', 'L2 ' in up, out)

# 9. 회차 입력 저장(snapcap) → 보드 문서 → 복원(snaprestore) → score.py가 prep 없이 같은 후보로 준비
import glob as _g
S9 = f'{T}/s9'; os.makedirs(S9)
sc = subprocess.run([sys.executable, f'{REPO}/eval/score.py', '--prep-only'], capture_output=True, text=True, env={**os.environ, 'EV_W': S9})
check('snapcap 준비: 기본 스냅샷 prep', sc.returncode == 0 and os.path.exists(f'{S9}/prep.txt'), sc.stdout + sc.stderr)
r9 = subprocess.run([sys.executable, f'{REPO}/build.py', 'snapcap'], capture_output=True, text=True, env={**os.environ, 'EV_W': S9})
doc = json.load(open(f'{S9}/snap_doc.json', encoding='utf-8'))
check('snapcap: 다섯 파일·호 번호·문서 id', r9.returncode == 0 and set(doc['files']) == {'candidates.md', 'cand_meta.json', 'sent.md', 'memstate.md', 'prep.txt'}
      and doc['issue'] == 5 and open(f'{S9}/snap_id.txt').read().strip() == 's05', r9.stdout + r9.stderr)
dst = f'{REPO}/eval/snapshot-zztest-005'
try:
    for form, body in (('감싼 형식', {'id': 's05', 'version': 3, 'data': doc}), ('평평한 형식', doc)):
        shutil.rmtree(dst, ignore_errors=True)
        json.dump(body, open(f'{T}/doc9.json', 'w', encoding='utf-8'), ensure_ascii=False)
        r = subprocess.run([sys.executable, f'{REPO}/build.py', 'snaprestore', f'{T}/doc9.json', dst], capture_output=True, text=True)
        check(f'snaprestore({form}): 후보 목록 그대로', r.returncode == 0 and open(f'{dst}/candidates.md', encoding='utf-8').read() == doc['files']['candidates.md'], r.stdout + r.stderr)
    r = subprocess.run([sys.executable, f'{REPO}/build.py', 'snaprestore', f'{T}/doc9.json', f'{T}/snapshot-x-006'], capture_output=True, text=True)
    check('snaprestore: 호 번호 다른 폴더 거부', r.returncode != 0 and '다름' in (r.stdout + r.stderr))
    json.dump({'snapshot': 'snapshot-zztest-005', 'cases': []}, open(f'{T}/cases9.json', 'w'))
    S9b = f'{T}/s9b'
    r = subprocess.run([sys.executable, f'{REPO}/eval/score.py', '--prep-only', '--cases', f'{T}/cases9.json'], capture_output=True, text=True, env={**os.environ, 'EV_W': S9b})
    check('score.py: 복원 스냅샷은 prep 없이 같은 후보', r.returncode == 0 and open(f'{S9b}/candidates.md', encoding='utf-8').read() == doc['files']['candidates.md']
          and json.load(open(f'{S9b}/state.json'))['issue'] == 4 and os.path.exists(f'{S9b}/build.py'), r.stdout + r.stderr)
    # chat_ops.md 4번 마지막 단계: 사용자 평가(gold) 줄 → 그 호의 판정 문항(다른 호 줄은 뺌, '수록'은 핵심·참고 둘 다 인정)
    u5 = re.search(r'https?://\S+', doc['files']['candidates.md']).group(0)
    open(f'{T}/gold9.txt', 'w', encoding='utf-8').write(f'5 | k1 | {u5} | 참고 | 메모\n5 | k2 | https://example.com/m | 수록 | 놓침 제보\n7 | k3 | https://example.com/x | 제외 | 다른 호\n')
    shutil.rmtree(dst, ignore_errors=True)
    subprocess.run([sys.executable, f'{REPO}/build.py', 'snaprestore', f'{T}/doc9.json', dst], capture_output=True, text=True)
    r = subprocess.run([sys.executable, f'{REPO}/build.py', 'cases', dst, f'{T}/gold9.txt', f'{T}/cases_005.json'], capture_output=True, text=True)
    cs = json.load(open(f'{T}/cases_005.json', encoding='utf-8')) if r.returncode == 0 else {'cases': []}
    check('cases: 같은 호 평가 줄만 판정 문항으로(참고·수록 기대값)', cs.get('snapshot') == 'snapshot-zztest-005' and [x['expect'] for x in cs['cases']] == [{'decision': '참고'}, {'decision_in': ['핵심', '참고']}], r.stdout + r.stderr)
finally:
    shutil.rmtree(dst, ignore_errors=True)

# 10. prep은 실패해도 출력을 prep.txt에 남김(평가 스냅샷과 재현 실행이 같은 출력을 봄)
S10 = f'{T}/s10'; os.makedirs(S10)
r = subprocess.run([sys.executable, f'{REPO}/build.py', 'prep'], capture_output=True, text=True, env={**os.environ, 'EV_W': S10})
check('prep: 출력이 prep.txt에도 남음', os.path.exists(f'{S10}/prep.txt') and open(f'{S10}/prep.txt', encoding='utf-8').read().strip() != '', r.stdout + r.stderr)

print(f'\n{"전부 통과" if not fails else "실패 " + ", ".join(fails)}')
sys.exit(1 if fails else 0)
