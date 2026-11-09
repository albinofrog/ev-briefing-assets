#!/usr/bin/env python3
"""build.py coverage 주제 배정·공백 검사(watchlist `주제어:` 줄). 네트워크 없음.

  python3 eval/test_coverage.py
"""
import os, sys, json, shutil, io, contextlib, importlib.util

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = '/tmp/evcovtest'
fails = []


def check(name, cond, info=''):
    print(f"{'PASS' if cond else 'FAIL'} {name}" + (f' | {info}' if info and not cond else ''))
    if not cond: fails.append(name)


shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
shutil.copy(f'{REPO}/sources.md', T)
open(f'{T}/watchlist.md', 'w', encoding='utf-8').write(
    '# 시험\n\n## 중고·리스\n주제어: 중고 전기차, lease\n- used EV prices\n- 전기차 리스 잔존가치\n\n'
    '## 보험\n주제어: 보험, insurance\n- 보험 배터리 데이터 전기차\n- EV insurance claims\n\n'
    '## 정책·시장 | 참고\n- 전기차 신규 등록\n- BEV registrations | GB:en\n')
items = [  # (번호, 제목, 출처, url)
    ('c1', '배터리 데이터까지 공개…현대차, 인증중고차 신뢰 높인다', 'watch:보험 배터리 데이터 전기차', 'https://www.edaily.co.kr/a1'),
    ('c2', 'EV insurance premiums rise 12% as repair costs climb', 'watch:EV insurance claims', 'https://www.insurancejournal.com/a2'),
    ('c3', '중고 전기차 거래 54% 늘어', '모터그래프', 'https://www.motorgraph.com/a3'),
    ('c4', 'Tesla release notes new battery software', 'watch:used EV prices', 'https://electrek.co/a4'),
    ('c5', '10월 전기차 신규 등록 2만대', 'watch:전기차 신규 등록', 'https://www.hankyung.com/a5'),
]
with open(f'{T}/items.jsonl', 'w', encoding='utf-8') as f:
    for cid, t, s, u in items: f.write(json.dumps({'url': u, 'title': t, 'src': s}, ensure_ascii=False) + '\n')
with open(f'{T}/candidates.md', 'w', encoding='utf-8') as f:
    f.write('## 점수 3 이상\n')
    for cid, t, s, u in items: f.write(f'{cid} | 3 | 11-08 09:00 | {s} | {t} | {u}\n')
json.dump({'lists': {}, 'watch': {}}, open(f'{T}/status.json', 'w'))
os.environ['EV_W'] = T
spec = importlib.util.spec_from_file_location('b', f'{REPO}/build.py'); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

out = io.StringIO()
with contextlib.redirect_stdout(out): b.coverage()
cov = json.load(open(f'{T}/coverage.json', encoding='utf-8'))
rows = {r['topic']: r for r in cov['topics']}
gaps = {g['topic'] for g in cov['gaps']}
check('검색어 출처만 있고 주제 단어가 없는 기사(c1)는 보험 국내 칸을 채우지 않음', rows['보험']['국내']['cand_hi'] == 0, out.getvalue())
check('보험·국내 공백 보고', '보험·국내' in gaps, str(gaps))
check('주제 단어가 있는 기사(c2)는 보험 국외 칸을 채움', rows['보험']['국외']['cand_hi'] == 1, str(rows['보험']))
check('검색어 출처가 아닌 목록 기사(c3)도 주제어로 중고·리스 국내에 셈', rows['중고·리스']['국내']['cand_hi'] == 1, str(rows['중고·리스']))
check('영문 주제어는 단어 앞 경계(lease가 release에 걸리지 않음, c4)', rows['중고·리스']['국외']['cand_hi'] == 0, str(rows['중고·리스']))
check('`| 참고` 대주제는 검색어 출처로 셈(c5)', rows['정책·시장']['국내']['cand_hi'] == 1, str(rows['정책·시장']))

print(f"\n{'모두 통과' if not fails else f'실패 {len(fails)}건'}")
sys.exit(1 if fails else 0)
