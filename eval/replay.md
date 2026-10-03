# 재현 실행 (판정 문항 채점용)

스냅샷 입력으로 브리핑 회차의 판정 단계만 다시 돌려 `briefing.json`을 만들고, 판정 문항(J)을 채점합니다. 프롬프트 개정안을 비교할 때 쓰며, 개정 전·후 프롬프트로 각각 한 번씩 돌립니다.

## 하는 일과 하지 않는 일

- 합니다: `rules.md`(또는 비교할 개정안) 0·2~6절과 `prompt.md` 다절 2~5번(선별·판정, 검토 마감, briefing.json 작성, check)
- 하지 않습니다: 메모리 읽기·쓰기, render, 파일 전달(SendUserFile), 푸시, 장부 기록. 장부는 스냅샷의 `/tmp/ev/sent.md`만 씁니다.
- "현재 시각"은 스냅샷의 작업 시작 시각입니다. 수록 기준은 prep 출력대로 따릅니다.

## 절차

1. 저장소 루트에서 `python3 eval/score.py --prep-only` → `/tmp/ev/candidates.md`, `/tmp/ev/sent.md` 준비
2. 실행 에이전트에게 아래 지시와 프롬프트 파일을 줍니다.
3. 결과(briefing.json, decisions.tsv)를 `/tmp/ev` 밖(예: 작업 폴더의 `replay_<프롬프트판>.json`)에 복사합니다. 채점기가 `/tmp/ev`를 비우기 때문입니다. decisions.tsv는 실행 간 판정이 갈릴 때 원인을 찾는 데 씁니다.
4. `python3 eval/score.py --briefing replay_<프롬프트판>.json`

## 실행 에이전트 지시문

> 브리핑 판정 규칙(첨부한 rules.md)의 재현 실행입니다. `/tmp/ev`는 이미 준비돼 있습니다(준비 단계는 하지 않음). prep 출력(수록 기준, 수집 실패 목록, 경고)은 `/tmp/ev/prep.txt`에 있으니 먼저 읽습니다. rules.md 0·2~6절을 따르고, 그다음 다음 두 단계만 합니다(`python3 /tmp/ev/build.py schema`, briefing.json 작성, `python3 /tmp/ev/build.py check /tmp/ev/briefing.json`). 메모리 도구, render, SendUserFile, PushNotification은 쓰지 않습니다. 장부는 `/tmp/ev/sent.md`입니다. 웹 호출 예산은 프롬프트대로입니다. 검토한 모든 후보(제목만 보고 넘긴 것 포함)를 `/tmp/ev/decisions.tsv`에 한 줄씩 `후보번호<TAB>본문열람(y/n/실패)<TAB>결정(핵심/참고/제외/이월)<TAB>사유`로 적습니다. 끝나면 `/tmp/ev/briefing.json`과 `decisions.tsv`를 지정 경로에 복사하고, 결과를 요약해 보고합니다.

## 한계

- 기사 본문을 실제로 열므로 회당 웹 호출이 최대 40회 듭니다.
- 원문이 바뀌거나 사라지면 같은 프롬프트도 결과가 달라질 수 있습니다. 비교는 같은 날 연달아 돌린 결과끼리 합니다.
- 에이전트 판정에는 변동이 있으므로, 한 번의 차이가 1~2문항이면 다시 돌려 확인합니다.
