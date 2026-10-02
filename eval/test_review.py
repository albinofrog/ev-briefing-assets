#!/usr/bin/env python3
"""2026-10-02 채팅 검수 반영분 회귀 검사(build.py patch --keep·prompt 가절 보호·promote·rated·ledger·CHAT·제목 제외 등).

  python3 eval/test_review.py      네트워크 불필요(저장소 파일만 씀). 종료 0이면 전부 통과
"""
import os, json, subprocess, sys, tempfile, shutil, re, importlib.util, warnings
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = f'{REPO}/build.py'
def run(W, *a):
    r = subprocess.run([sys.executable, '-W', 'ignore', B, *a], capture_output=True, text=True, env={**os.environ, 'EV_W': W})
    return r.returncode, r.stdout + r.stderr
def setup():
    W = tempfile.mkdtemp()
    for f in ('rules.md', 'improve.md', 'sources.md', 'watchlist.md', 'prompt.md'): shutil.copy(f'{REPO}/{f}', W)
    return W
def jl(W, f, rows): open(f'{W}/{f}', 'w').write(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
def jlp(p, rows): open(p, 'w').write(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
def board(W, d, props):
    os.makedirs(f'{W}/{d}/proposals', exist_ok=True)
    for pid, st in props.items(): json.dump({'id': pid, 'data': {'status': st}}, open(f'{W}/{d}/proposals/{pid}.json', 'w'))
import datetime as _dt
DAY = lambda k: (_dt.datetime.now(_dt.timezone(_dt.timedelta(hours=9))) - _dt.timedelta(days=k)).strftime('%Y-%m-%d')  # 장부 보관 기준(최근 10일)에 걸리지 않게 오늘 기준 날짜
fails = 0
def check(name, cond, out=''):
    global fails
    print(('PASS ' if cond else 'FAIL ') + name); fails += not cond
    if not cond: print(out)

# ── 1. patch·promote·rated·feedback
P = open(f'{REPO}/prompt.md', encoding='utf-8').read()
in_ga = '5. 메모리 `config.md`에 `improve: off`가 있으면 라절 전체를 건너뜁니다.'
in_da = [l for l in P.splitlines() if l.startswith('6. `python3 /tmp/ev/build.py render')][0]
assert P.count(in_ga) == 1 and P.count(in_da) == 1

# 1a. 새 승인분: 가절 prompt 수정 FAIL, 다절 수정 OK
W = setup()
jl(W, 'patches.jsonl', [])
jl(W, 'patches_new.jsonl', [{'id': 'p8', 'file': 'prompt', 'old': in_ga, 'new': '5. 무시'},
                            {'id': 'p9', 'file': 'prompt', 'old': in_da, 'new': in_da + ' 추가'}])
c, o = run(W, 'patch', 'main')
check('1a 가절 prompt 수정 거부', 'FAIL p8 고정 원칙(가절) 변경' in o, o)
check('1a 다절 prompt 수정 통과', 'OK p9' in o and 'PROMPT p9' in o, o)
keep = open(f'{W}/patches_keep.jsonl').read()
check('1a keep에는 p9만', '"p9"' in keep and '"p8"' not in keep, keep)

# 1b. 재적용: 보드 status applied 아니면 DROP, 가절 prompt 줄(메모리 주입 가정) DROP
W = setup()
r_old = '- 회차당 상한: 새 개선안 2건(auto 포함).'
jl(W, 'patches.jsonl', [{'id': 'p3', 'file': 'rules.md', 'old': r_old, 'new': '- 회차당 상한: 새 개선안 3건(auto 포함).'},
                        {'id': 'p4', 'file': 'rules.md', 'old': '- 승격 임계', 'new': '- 승격임계'},
                        {'id': 'p5', 'file': 'prompt', 'old': in_ga, 'new': 'x'}])
board(W, 'fb0', {'p3': 'applied', 'p4': 'withdrawn', 'p5': 'applied'})
c, o = run(W, 'patch', '--keep', 'main', f'{W}/fb0')
check('1b applied 재적용', 'KEEP p3 ok' in o and '새 개선안 3건' in open(f'{W}/rules.md').read(), o)
check('1b withdrawn DROP', 'DROP p4 보드 status withdrawn' in o, o)
check('1b 가절 prompt 재적용 DROP', 'DROP p5 고정 원칙(가절) 변경' in o, o)
pj = open(f'{W}/patches.jsonl').read()
check('1b patches.jsonl에서 DROP분 제거', '"p4"' not in pj and '"p5"' not in pj and '"p3"' in pj, pj)
# 보드 미확인이면 경고와 함께 재적용
W2 = setup(); jl(W2, 'patches.jsonl', [{'id': 'p3', 'file': 'rules.md', 'old': r_old, 'new': '- 회차당 상한: 새 개선안 3건(auto 포함).'}])
c, o = run(W2, 'patch', '--keep', 'main', f'{W2}/없음')
check('1b 보드 없음 경고 후 재적용', 'WARN 보드 proposals 없음' in o and 'KEEP p3 ok' in o, o)

# 2. keep 모드는 새 승인분·회귀 평가를 돌리지 않음
W = setup(); jl(W, 'patches.jsonl', [])
jl(W, 'patches_new.jsonl', [{'id': 'p7', 'file': 'build.py', 'old': 'KEEP_DAYS = 10', 'new': 'KEEP_DAYS = 11'}])
shutil.copy(B, W)
c, o = run(W, 'patch', '--keep', 'main')
check('2 keep 모드는 새 승인분 무시(gate 없음)', 'p7' not in o and not os.path.exists('/tmp/evgate/w/marker'), o)

# 3. promote
W = setup()
open(f'{W}/lessons.md', 'w').write(
    'L1 | 제안(p1) | 운영 | code | OPS:장기-수집실패 | 1 | 근거 | 대응 | 1\n'
    'L2 | 관찰 | 운영 | code | OPS:x | 2 | 근거 | 대응 | 1\n'
    'L3 | 관찰 | 관련성 | judge | C5 | 3 | 자기 탐지 | 대응 | 1\n'
    'L4 | 관찰 | 충분성 | judge | MISS-U:C5 | 1 | 제보 | 대응 | 1\n'
    'L5 | 거절 | 관련성 | judge | C6 | 0 | 거절 메모: x | 대응 | 1\n'
    'L6 | 관찰 | 관련성 | judge | FP | 1 | 사용자 평가 | 대응 | 1\n')
open(f'{W}/metrics.md', 'w').write('2026-10-02 | 6 | 핵심 0 참고 1 | 웹 7 | 놓침 0 | 평가 0 유용 0 | 기여 Electrek:1\n')
c, o = run(W, 'promote')
check('3 임계 미달 제안 L1 검출', 'L1 제안(p1) 관찰 1회 < 임계 2' in o, o)
check('3 L2 승격', 'L2 | code | OPS:x' in o, o)
check('3 평가 0이면 자기 탐지 judge L3 대기', 'L3 C5' in o.split('대기:')[1] if '대기:' in o else False, o)
check('3 제보 MISS-U 1회 승격', 'L4 | judge | MISS-U:C5 | 관찰 1회(임계 1)' in o, o)
check('3 FP 1회는 임계 2 미달', 'L6' not in o, o)
check('3 거절 관찰 0은 미승격', 'L5' not in o, o)

# 4. rated는 발행 회차만, 최근 10개
W = setup()
ls = [f'2026-09-{i:02d} | {i} | 핵심 0 참고 {1 if i % 2 else 0} | 웹 1 | 평가 {i} 유용 0 | 기여 -' for i in range(1, 25)]
open(f'{W}/metrics.md', 'w').write('\n'.join(ls) + '\n')
c, o = run(W, 'rated')
exp = sum(i for i in range(1, 25) if i % 2)  # 발행 줄 12개 중 마지막 10개
exp = sum([i for i in range(1, 25) if i % 2][-10:])
check(f'4 rated 발행 회차 10줄 합 {exp}', o.strip() == str(exp), o)

# 4. feedback은 decisions.txt를 만들지 않음, orphan은 계속 출력
W = setup(); d = f'{W}/fb'
for coll in ('items', 'feedback', 'missed', 'proposals', 'decisions'): os.makedirs(f'{d}/{coll}')
json.dump({'id': 'p1', 'data': {'status': 'pending', 'layer': 'code', 'title': 't'}}, open(f'{d}/proposals/p1.json', 'w'))
json.dump({'id': 'p1', 'data': {'decision': 'approve', 'at': '2026-10-02T06:00:00Z'}}, open(f'{d}/decisions/p1.json', 'w'))
json.dump({'id': 'p9', 'data': {'decision': 'approve', 'at': '2026-10-02T06:00:00Z'}}, open(f'{d}/decisions/p9.json', 'w'))
open(f'{W}/decisions.txt', 'w').write('decide가 만든 내용\n')
c, o = run(W, 'feedback', d, '')
check('4 feedback이 decisions.txt를 덮어쓰지 않음', open(f'{W}/decisions.txt').read() == 'decide가 만든 내용\n', o)
check('4 orphan 결정은 출력', '대응 개선안 없는 결정(오류에 적음): p9' in o and '결정: p1' not in o, o)
c, o = run(W, 'decide', d)
check('4 decide가 결정 처리', 'p1 | approve' in open(f'{W}/decisions.txt').read(), o)


# ── 2. 격리·장부·CHAT·수집
# A. 복사본에서 patch → 원본 사본 불변
W = setup(); N = W + '_next'
jlp(f'{W}/patches.jsonl', [])
old = '- 회차당 상한: 새 개선안 2건(auto 포함).'
jlp(f'{W}/patches_new.jsonl', [{'id': 'p9', 'file': 'watchlist.md', 'old': open(f'{W}/watchlist.md').read().splitlines()[0], 'new': open(f'{W}/watchlist.md').read().splitlines()[0]}])
before = {f: open(f'{W}/{f}').read() for f in ('rules.md', 'watchlist.md')}
shutil.copytree(W, N)
jlp(f'{N}/patches_new.jsonl', [{'id': 'p8', 'file': 'prompt', 'old': [l for l in open(f'{W}/prompt.md').read().splitlines() if l.startswith('6. `python3 /tmp/ev/build.py render')][0], 'new': 'x'}])
c, o = run(N, 'patch', 'main')
check('A 복사본 실행 결과는 복사본에만', os.path.exists(f'{N}/patches_keep.jsonl') and not os.path.exists(f'{W}/patches_keep.jsonl')
      and all(open(f'{W}/{f}').read() == t for f, t in before.items()), o)

# C. rules.md·improve.md 새 승인분은 CHAT, 적용 안 됨
W = setup(); jlp(f'{W}/patches.jsonl', [])
jlp(f'{W}/patches_new.jsonl', [{'id': 'p5', 'file': 'rules.md', 'old': old, 'new': old.replace('2건', '3건')},
                              {'id': 'p6', 'file': 'improve.md', 'old': open(f'{W}/improve.md').read().splitlines()[0], 'new': '# x'}])
c, o = run(W, 'patch', 'main')
check('C rules.md 승인분 CHAT', 'CHAT p5' in o and '2건(auto' in open(f'{W}/rules.md').read(), o)
check('C improve.md 승인분 CHAT', 'CHAT p6' in o, o)
check('C keep에 안 들어감', '"p5"' not in open(f'{W}/patches_keep.jsonl').read(), o)
# 재적용(keep)은 rules.md 수정도 그대로 적용(이미 사용자 승인·이전 검사 통과분)
jlp(f'{W}/patches.jsonl', [{'id': 'p3', 'file': 'rules.md', 'old': old, 'new': old.replace('2건', '3건')}])
c, o = run(W, 'patch', '--keep', 'main')
check('C 기존 적용분 재적용은 유지', 'KEEP p3 ok' in o, o)

# B. 장부 합치기
W = setup()
mem = (f'{DAY(4)} | 1 | u:aaa | - | NIO Power / 지분매각 / 30%\n'
       f'{DAY(3)} | 1 | u:bbb | - | -\n'
       'issue 헤더 같은 잡줄\n')
open(f'{W}/sent.md', 'w').write(mem)
os.makedirs(f'{W}/led/ledger')
for i, l in enumerate([f'{DAY(3)} | 1 | u:bbb | - | Stellantis N.V. / 중단 / 1주', f'{DAY(2)} | 3 | u:ccc | - | Carfax / 집계 / -']):
    json.dump({'id': f'l{i}', 'data': {'line': l}}, open(f'{W}/led/ledger/l{i}.json', 'w'), ensure_ascii=False)
c, o = run(W, 'ledger', 'merge', f'{W}/led')
s = open(f'{W}/sent.md').read()
check('B 합집합 3줄', s.count('\n') == 3 and 'u:aaa' in s and 'u:ccc' in s, s + o)
check('B 거부 대체 줄(-)을 보드 줄로 교체', 'Stellantis N.V. / 중단 / 1주' in s and '| u:bbb | - | -\n' not in s, s)
# 메모리 읽기 실패 + 보드 있음 → 보드로 진행
open(f'{W}/sent.md', 'w').write('READ_FAILED\n')
c, o = run(W, 'ledger', 'merge', f'{W}/led')
check('B 메모리 실패 시 보드만으로 장부', open(f'{W}/sent.md').read().count('\n') == 2, o)
# 둘 다 실패 → READ_FAILED 유지
open(f'{W}/sent.md', 'w').write('READ_FAILED\n')
c, o = run(W, 'ledger', 'merge', f'{W}/없음')
check('B 둘 다 실패면 READ_FAILED 유지', open(f'{W}/sent.md').read().strip() == 'READ_FAILED', o)
# 보드 쓰기 목록
open(f'{W}/ledger.txt', 'w').write('2026-10-02 | 1 | u:0b450fe36dfb | - | 현대자동차 / 판매 / 3만1112대\n')
c, o = run(W, 'ledger', 'board')
w = json.load(open(f'{W}/ledger_board.json'))
check('B 보드 쓰기 목록', len(w) == 1 and w[0]['collection'] == 'ledger' and w[0]['data']['line'].startswith('2026-10-02') and re.fullmatch(r'l[0-9a-f]{12}', w[0]['doc_id']), o)
# 같은 키는 같은 doc_id(재기록해도 중복 문서 없음)
c, o = run(W, 'ledger', 'board'); check('B doc_id 결정적', json.load(open(f'{W}/ledger_board.json'))[0]['doc_id'] == w[0]['doc_id'])
# prep의 read_sent가 합친 파일을 읽는지(형식 호환)
os.environ['EV_W'] = W
open(f'{W}/sent.md', 'w').write(mem); run(W, 'ledger', 'merge', f'{W}/led')
import importlib.util
spec = importlib.util.spec_from_file_location('b', B); b = importlib.util.module_from_spec(spec)
import warnings; warnings.simplefilter('ignore'); spec.loader.exec_module(b)
rows = b.read_sent()
check('B read_sent 호환', isinstance(rows, list) and len(rows) == 3, rows)

W = setup()
open(f'{W}/sent.md', 'w').write(f'{DAY(4)} | 1 | - | - | NIO Power / 지분매각 / 30% | x\n{DAY(3)} | 1 | - | - | ACEA / 발표 / 306GWh | y\n')
c, o = run(W, 'ledger', 'merge')
check('B URL 칸이 -인 줄끼리 합쳐지지 않음', open(f'{W}/sent.md').read().count('\n') == 2, o)

W = setup()
open(f'{W}/sent.md', 'w').write(f'{DAY(30)} | 1 | u:old1 | - | Old Corp / 발표 / -\n{DAY(1)} | 1 | u:new1 | - | New Corp / 발표 / -\n')
os.makedirs(f'{W}/led/ledger')
json.dump({'data': {'line': f'{DAY(40)} | 1 | u:old2 | - | Older Corp / 발표 / -'}}, open(f'{W}/led/ledger/a.json', 'w'))
json.dump({'data': {'line': f'{DAY(2)} | 1 | u:new2 | - | Newer Corp / 발표 / -'}}, open(f'{W}/led/ledger/b.json', 'w'))
c, o = run(W, 'ledger', 'merge', f'{W}/led'); s = open(f'{W}/sent.md').read()
check('B 보관 기준(10일) 밖 줄은 메모리·보드 모두 제외', 'u:new1' in s and 'u:new2' in s and 'u:old1' not in s and 'u:old2' not in s and '2줄 제외' in o, s + o)
# 보드 장부가 커져도 합친 장부는 15KB 안내 조건을 넘지 않음(10일 넘은 줄)
W = setup(); os.makedirs(f'{W}/led/ledger'); open(f'{W}/sent.md', 'w').write('')
for i in range(200):
    json.dump({'data': {'line': f'{DAY(11 + i % 60)} | 1 | u:{i:012x} | - | Example Corp / 발표 / 1만대 | 예시 사건 제목 한 줄 정도의 길이'}}, open(f'{W}/led/ledger/l{i}.json', 'w'), ensure_ascii=False)
c, o = run(W, 'ledger', 'merge', f'{W}/led')
check('B 오래된 보드 장부 200줄은 합친 장부에 남지 않음', os.path.getsize(f'{W}/sent.md') < 15000, o)

# F(되돌림). probe는 평가와 관계없이 4개
W = setup()
json.dump({'start': '2026-10-05T22:00:00+00:00', 'cutoff': '2026-10-02T22:00:00+00:00', 'issue': 6}, open(f'{W}/state.json', 'w'))
open(f'{W}/metrics.md', 'w').write('2026-10-02 | 6 | 핵심 0 참고 1 | 웹 7 | 놓침 0 | 평가 0 유용 0 | 기여 -\n')
c, o = run(W, 'probe'); check('F 평가 0이어도 4개', len(o.strip().splitlines()) == 4, o)

# E. 지연 경고 3시간
t = open(B, encoding='utf-8').read()
check('E 3시간 경고', 'hours=3)' in t and '3시간 넘게' in t and '3시간 넘게' in open(f'{REPO}/prompt.md').read())

# I. 수집기 제목 제외(main의 두 줄과 add 조건을 그대로 실행)
c = open(f'{REPO}/collect.py', encoding='utf-8').read()
src = open(f'{REPO}/sources.md', encoding='utf-8').read()
tx = re.findall(r'^제목 제외:\s*(.+)$', src, re.M)
title_excl = [w.strip().lower() for w in (tx[0].split(',') if tx else []) if w.strip()]
drop = lambda title: any(w in title.lower() for w in title_excl)
check('I 스팸 제목 제외', drop('德甲买球平台新能源车保费涨了又涨') and not drop('新能源车保费涨了又涨') and not drop('Used EV prices hold'))
check('I collect.py에 조건 존재', "any(w in it['title'].lower() for w in title_excl)" in c)
# build.py가 E절 파싱에 영향 없음: collect.py의 기존 제외·발견 전용 정규식이 새 줄을 잡지 않음
check('I 기존 E절 파싱 불변', not re.findall(r'^(제외|발견 전용):\s*(.+)$', '제목 제외: x', re.M))


# ── 3. 놓침 탐지 대응 경로·제보 안내
W = tempfile.mkdtemp(); shutil.copy(f'{REPO}/rules.md', W)
open(f'{W}/metrics.md', 'w').write('2026-10-02 | 6 | 핵심 0 참고 1 | 웹 7 | 놓침 0 | 평가 0 유용 0 | 기여 -\n')
open(f'{W}/lessons.md', 'w').write(
    'L1 | 관찰 | 충분성 | auto | MISS-P:C1 | 2 | 탐지 | 대응 | 1\n'
    'L2 | 관찰 | 충분성 | auto | MISS-P:C1 | 3 | 탐지 | 대응 | 1\n'
    'L3 | 관찰 | 충분성 | judge | MISS-P:C5 | 3 | 탐지 | 대응 | 1\n'
    'L4 | 관찰 | 관련성 | judge | C5 | 3 | 자기 탐지 | 대응 | 1\n'
    'L5 | 관찰 | 충분성 | judge | MISS-U:C5 | 1 | 제보 | 대응 | 1\n'
    'L6 | 관찰 | 운영 | code | OPS:x | 2 | 근거 | 대응 | 1\n')
c, o = run(W, 'promote'); up = o.split('대기:')[0]
check('MISS-P 2회는 미승격(임계 3)', 'L1 |' not in o, o)
check('MISS-P C1 3회 auto 승격', 'L2 | auto | MISS-P:C1 | 관찰 3회(임계 3)' in up, o)
check('MISS-P C5 3회는 평가 0이어도 judge 승격', 'L3 | judge | MISS-P:C5' in up, o)
check('자체 판정(C5) judge는 평가 0이면 대기', 'L4 C5' in o.split('대기:')[1] if '대기:' in o else False, o)
check('사용자 제보 1회 승격 유지', 'L5 | judge | MISS-U:C5 | 관찰 1회(임계 1)' in up, o)
open(f'{W}/lessons.md', 'w').write('L7 | 관찰 | 운영 | code | OPS:z | 2회 | 근거 | 대응 | 1\nL6 | 관찰 | 운영 | code | OPS:w | 관찰 3회 | 근거 | 대응 | 1\nL5 | 관찰 | 운영 | code | OPS:v | - | 근거 | 대응 | 1\n')
c, o7 = run(W, 'promote')
check('관찰 수 "2회"·"관찰 3회" 표기도 읽음', 'L7 | code | OPS:z | 관찰 2회' in o7 and 'L6 | code | OPS:w | 관찰 3회' in o7, o7)
check('관찰 수를 못 읽는 줄은 형식 오류로 출력', '형식 오류' in o7 and 'L5 관찰 수 칸' in o7, o7)
check('일반 임계 2 유지', 'L6 | code | OPS:x | 관찰 2회(임계 2)' in up, o)
t = open(B, encoding='utf-8').read(); p = open(f'{REPO}/prompt.md', encoding='utf-8').read()
check('푸시·리포트 제보 안내', "' | 제보·평가 {bu}'" in t and '놓친 기사 URL 제보' in t and '놓친 기사는 보드에 URL 제보' in p and '보드 평가 필요' not in p)
# 푸시 길이 상한: 접미사 길이와 예약분 일치
check('푸시 접미사 예약 길이 일치', len(' | 제보·평가 ') == 9)

print(f'\n{fails} failed'); sys.exit(1 if fails else 0)
