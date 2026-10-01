# EV 시장·정책 브리핑 추적 목록

사업 핵심 질문(OEM을 거치지 않는 배터리 데이터 접근, 상태 평가, 잔존가치, 보험, 제도 편입)에 닿는 대상을 매시간 표적 검색합니다. collect.py가 한 줄에 검색어 하나씩 구글 뉴스 RSS(최근 2일)로 조회하고, 조회 실패·0건·원주소 변환 실패가 많으면 Bing 뉴스 RSS로 대신 조회해 items.jsonl에 쌓습니다. 제목에 sources.md B절 단어가 있는 결과만 남기고, `!` 표시 검색어(업체명)는 검색어의 고유 단어만 있어도 남기고 구글과 Bing을 함께 조회합니다. 구매 가이드·해설형 제목은 버립니다.
형식: `- 검색어 | 지역판 | !` (지역판·!는 생략 가능). 지역판은 KR:ko, JP:ja, CN:zh-Hans, DE:de, US:en, GB:en 중 하나이며, 생략하면 검색어 글자로 정합니다.
작성 요령: 따옴표 없는 2~3단어 조합이 가장 잘 잡힙니다. 따옴표는 굳어진 용어·고유명사에만 씁니다. 같은 주제의 다른 표현은 OR로 한 줄에 묶을 수 있습니다(구글 지원). 검색어 하나는 한 번 수집에 새 항목 15건까지만 넣고, 구글 결과가 100건 상한에 닿으면 status에 cap_hit로 남으니 검색어를 나눕니다.
교체 기준: data 브랜치 status.json의 검색어별 새 항목 수와 run_log 수록 출처를 보고, 새 항목은 많은데 수록이 이어서 0인 검색어와 prep이 "48시간 넘게 0건"으로 경고한 검색어부터 바꿉니다.

## 데이터 접근·규제
- "battery passport" OR "digital product passport" battery
- "Data Act" connected car
- EU Data Act 자동차 데이터
- in-vehicle data access
- "right to repair" vehicle
- OBD 접근 제한
- 자동차 사이버보안 OBD
- "UN R155" OBD
- 배터리 이력관리
- 사용후 배터리 성능평가
- 전기차 배터리 성능 인증
- 动力电池 溯源
- 电池 数字护照
- 电池健康度 评估 标准

## 배터리 진단·데이터 기업
- Aviloo battery | | !
- TWAICE battery | | !
- "Recurrent" EV battery | | !
- "Cox Automotive" battery health | | !
- 민테크 배터리 | | !
- EV battery diagnostics
- バッテリー 診断 EV
- Batteriezertifikat Gebrauchtwagen

## 중고·잔존가치
- battery health used EV
- 중고 전기차 배터리
- 전기차 리스 잔존가치
- used EV prices
- gebrauchte Elektroautos Batterie
- Restwert Elektroauto
- 二手新能源车 保值
- 中古EV 価格 | JP:ja
- 中古EV 残価 | JP:ja

## 보험·금융
- 전기차 보험료
- 보험 배터리 데이터 전기차
- electric vehicle insurance
- EV 保険 バッテリー
- 新能源车险

## 재사용·교환
- 사용후 배터리
- 宁德时代 巧克力换电
- 蔚来 换电站
- 换电 标准 政策
