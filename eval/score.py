#!/usr/bin/env python3
"""EV 브리핑 평가 세트 채점.

  python3 eval/score.py                       # prep 단계 문항 채점(현재 저장소의 build.py)
  python3 eval/score.py --build 경로/build.py  # 다른 버전의 build.py로 채점(수정 전후 비교)
  python3 eval/score.py --briefing 경로/briefing.json  # 판정 문항도 채점(스냅샷으로 돌린 회차의 결과)

스냅샷(eval/snapshot-*)의 수집 데이터·장부·기준 시각을 고정해 prep을 돌리므로 언제 실행해도 같은 후보 목록이 나옵니다.
작업 폴더로 /tmp/ev를 비우고 쓰므로 실제 회차와 같은 환경에서 동시에 돌리지 않습니다.
종료 코드: 일반 prep 문항(known_gap 제외)이 하나라도 틀리면 1(회귀).
"""
import sys, os, re, json, shutil, argparse, importlib.util, contextlib, io, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def load_build(path):
    spec = importlib.util.spec_from_file_location('build_eval', path)
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    return b


def run_prep(b, snap, src):
    W = b.W
    shutil.rmtree(W, ignore_errors=True); os.makedirs(W)
    shutil.copy(f'{snap}/memstate.md', W); shutil.copy(f'{snap}/sent.md', W)
    start = open(f'{snap}/start.txt').read().strip()
    cutoff = (dt.datetime.fromisoformat(start) - dt.timedelta(hours=b.FRESH_H)).isoformat()
    json.dump({'start': start, 'cutoff': cutoff}, open(f'{W}/state.json', 'w'))
    # 자산(sources.md 등)은 build.py와 같은 폴더, 수집 데이터는 스냅샷에서 받음(curl은 http가 아닌 경로 앞에 REPO를 붙이므로 file:/// + 절대경로)
    b.REPO = 'file:///'
    b.ASSETS = [((snap + '/' + s[len(b.DATA):]) if s.startswith(b.DATA) else (src + '/' + s), d) for s, d in b.ASSETS]
    b.ASSETS = [(s.lstrip('/'), d) for s, d in b.ASSETS]
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        try:
            b.prep()
        except SystemExit as e:
            if e.code: sys.exit('prep 실패:\n' + out.getvalue())
    return W


def parse_candidates(path):
    groups, band = [], None
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('## '):
            band = 3 if '3 이상' in ln else 2 if '점수 2' in ln else 1
        elif re.match(r'c\d+ \|', ln):
            groups.append({'band': band, 'head': ln.rstrip(), 'lines': [ln.rstrip()]})
        elif ln.startswith('   ↳') and groups:
            groups[-1]['lines'].append(ln.rstrip())
    return groups


def full_url(text, match):
    m = re.search(r'https?://\S*' + re.escape(match) + r'\S*', text)
    return m.group(0) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', default=os.path.join(REPO, 'build.py'))
    ap.add_argument('--briefing')
    ap.add_argument('--cases', default=os.path.join(HERE, 'cases.json'))
    ap.add_argument('--prep-only', action='store_true', help='스냅샷으로 prep만 돌려 /tmp/ev를 재현 실행용으로 준비하고 끝냄(eval/replay.md)')
    a = ap.parse_args()
    spec = json.load(open(a.cases, encoding='utf-8'))
    snap = os.path.join(HERE, spec['snapshot'])
    b = load_build(os.path.abspath(a.build))
    W = run_prep(b, snap, os.path.dirname(os.path.abspath(a.build)))
    if a.prep_only:
        shutil.copy(os.path.abspath(a.build), f'{W}/build.py')  # 재현 에이전트가 schema·check에 씀
        print(f'준비 완료: {W}/candidates.md, 장부 {W}/sent.md (스냅샷 {spec["snapshot"]})')
        return
    groups = parse_candidates(f'{W}/candidates.md')
    meta = json.load(open(f'{W}/cand_meta.json'))
    find = lambda m: next((g for g in groups if any(m in l for l in g['lines'])), None)

    res = []
    for c in spec['cases']:
        g = find(c['match'])
        e = c['expect']
        if c['layer'] == 'prep':
            if not g:
                ok, why = False, '후보 목록에 없음'
            elif 'tag' in e:
                ok, why = e['tag'] in g['head'], f"표시 {e['tag']} {'있음' if e['tag'] in g['head'] else '없음'}"
            elif 'no_tag' in e:
                ok, why = e['no_tag'] not in g['head'], f"표시 {e['no_tag']} {'없음' if e['no_tag'] not in g['head'] else '있음'}"
            elif 'band_max' in e:
                ok, why = g['band'] <= e['band_max'], f"점수 구간 {g['band']}"
            else:
                ok, why = g['band'] >= e['band_min'], f"점수 구간 {g['band']}"
        else:
            if not a.briefing:
                continue
            d = json.load(open(a.briefing, encoding='utf-8'))
            url = full_url('\n'.join(g['lines']), c['match']) if g else None
            grp = set(meta.get(b.uhash(url), {}).get('grp', [])) if url else set()
            hit = next((i for i in d['items'] if b.uhash(i['url']) in grp
                        or (i.get('origin') and i['origin'].get('url') and b.uhash(i['origin']['url']) in grp)
                        or any(h in i['url'] for h in c.get('accept_hosts', []))), None)
            got = {'decision': {'core': '핵심', 'ref': '참고'}[hit['tier']] if hit else '제외'}
            if hit:
                got['relevance'] = hit.get('relevance'); got['trust_fail'] = hit.get('trust_fail')
            bad = [f'{k} 기대 {v} / 결과 {got.get(k)}' for k, v in e.items() if k != 'decision_in' and got.get(k) != v]
            if 'decision_in' in e and got['decision'] not in e['decision_in']:
                bad.append(f"decision 기대 {'·'.join(e['decision_in'])} / 결과 {got['decision']}")
            ok, why = not bad, '; '.join(bad) or got['decision']
        res.append((c, ok, why))

    for c, ok, why in res:
        flag = ' (알려진 공백)' if c.get('known_gap') else ''
        print(f"{'PASS' if ok else 'FAIL'} {c['id']} {c.get('type', c['layer'])}{flag} | {why}")
    reg = [(c, ok) for c, ok, _ in res if c['layer'] == 'prep' and not c.get('known_gap')]
    gap = [(c, ok) for c, ok, _ in res if c['layer'] == 'prep' and c.get('known_gap')]
    jud = [(c, ok) for c, ok, _ in res if c['layer'] == 'judge']
    print(f"\nprep 회귀 {sum(o for _, o in reg)}/{len(reg)} · 알려진 공백 해결 {sum(o for _, o in gap)}/{len(gap)}"
          + (f" · 판정 {sum(o for _, o in jud)}/{len(jud)}" if jud else ' · 판정 문항은 --briefing 필요'))
    sys.exit(0 if all(o for _, o in reg) else 1)


if __name__ == '__main__':
    main()
