# EV 시장·정책 브리핑 추적 목록

사업 핵심 질문(OEM을 거치지 않는 배터리 데이터 접근, 상태 평가, 잔존가치, 보험, 제도 편입)에 닿는 대상을 수집 때마다 표적 검색합니다. collect.py가 한 줄에 검색어 하나씩 구글 뉴스 RSS(최근 2일)로 조회하고, 조회 실패·0건·원주소 변환 실패가 많으면 Bing 뉴스 RSS로 대신 조회해 items.jsonl에 쌓습니다. 제목에 sources.md B절 단어가 있는 결과만 남기고, `!` 표시 검색어(업체명)는 검색어의 고유 단어만 있어도 남기고 구글과 Bing을 함께 조회합니다. 구매 가이드·해설형 제목은 버립니다.
형식: `- 검색어 | 지역판 | !` (지역판·!는 생략 가능). 지역판은 KR:ko, JP:ja, CN:zh-Hans, DE:de, US:en, GB:en 중 하나이며, 생략하면 검색어 글자로 정합니다.
작성 요령: 따옴표 없는 2~3단어 조합이 가장 잘 잡힙니다. 따옴표는 굳어진 용어·고유명사에만 씁니다. 같은 주제의 다른 표현은 OR로 한 줄에 묶을 수 있습니다(구글 지원). 검색어 하나는 한 번 수집에 새 항목 15건까지만 넣고, 구글 결과가 100건 상한에 닿으면 status에 cap_hit로 남으니 검색어를 나눕니다.
교체 기준: data 브랜치 status.json의 검색어별 새 항목 수와 run_log 수록 출처를 보고, 새 항목은 많은데 수록이 이어서 0인 검색어와 prep이 "48시간 넘게 0건"으로 경고한 검색어부터 바꿉니다.
대주제 4개(배터리 데이터 평가 / 중고·리스 / 보험 / 정책·시장)로 나누며, `build.py coverage`가 대주제마다 국내(한국어 기사·한국 매체)·국외 칸의 공백을 따로 봅니다. 칸에 검색어가 없거나 0건이 이어지면 그 칸 검색어를 추가합니다. `주제어:` 줄은 `build.py coverage`가 기사를 그 대주제로 셀 때 쓰는 제목 단어입니다(쉼표로 구분, 수집에는 쓰지 않음). 주제어 줄이 있는 대주제는 제목에 그 단어나 검색어 고유어가 있어야 그 주제로 셉니다. 제목 줄 끝의 `| 참고`는 관련도 3(EV 판매·등록·점유율 등) 중심 대주제라 점수와 관계없이 후보가 있으면 공백으로 보지 않는다는 표시입니다.

## 배터리 데이터 평가
주제어: SOH, state of health, battery health, 배터리 상태, 배터리 데이터, 성능평가, 성능점검, 진단, 배터리 인증, 상태 인증, 이력관리, 여권, passport, Batteriepass, Batteriezustand, 차량 데이터, vehicle data, data access, Data Act, right to repair, repair act, OBD, BMS, Fahrzeugdaten, 電池劣化, 診断, スキャンツール, 电池健康, 溯源, 检测, 护照, 사용후, second-life, 재사용, 재제조
- "battery passport" OR "digital product passport" battery
- "Data Act" vehicle data | GB:en
- 차량 데이터 개방
- in-vehicle data access
- "right to repair" vehicle
- OBD検査 | JP:ja
- スキャンツール 整備 | JP:ja
- Zugang Fahrzeugdaten | DE:de
- 배터리 이력관리
- 사용후 배터리 성능평가
- 배터리 안전성 인증제
- 动力电池 溯源
- 电池 数字护照
- 电池健康度 评估 标准
- EU battery regulation state of health | GB:en
- vehicle data access repair
- "REPAIR Act" vehicle
- 자동차관리법 배터리
- 중고차 성능점검 배터리
- Aviloo battery | | !
- TWAICE battery | | !
- "Recurrent" EV battery | | !
- "Cox Automotive" battery health | | !
- 민테크 배터리 | | !
- EV battery diagnostics
- EV 電池劣化 | JP:ja
- Batteriezertifikat Gebrauchtwagen
- 사용후 배터리
- second-life EV battery | GB:en
- 蔚来 换电 合作 OR 投资 OR 协议
- 换电 标准 政策
- 二手车 电池检测
- 动力电池 在役检测
- 电池 国家标准 发布
- battery passport implementing act | GB:en
- Batteriepass | DE:de

## 중고·리스
주제어: 중고 전기차, 중고 ev, 중고차, 인증중고, 잔존가치, 잔가, 감가, 시세, 리스사, 리스 반납, 장기렌트, used ev, used electric, used car, pre-owned, residual, depreciation, lease, leasing, remarketing, gebraucht, restwert, rückläufer, 中古, 残価, リース, 二手, 保值, 残值, 租赁
- battery health used EV
- 중고 전기차 배터리
- 전기차 리스 잔존가치
- used EV prices
- gebrauchte Elektroautos Batterie
- Restwert Elektroauto
- used EV values | GB:en
- EV battery health check | GB:en
- 二手新能源车 保值
- 中古EV 価格 | JP:ja
- 中古EV 残価 | JP:ja
- 전기차 리스 반납
- EV lease residual values | GB:en
- EV lease returns | US:en
- Elektroauto Leasing Rückläufer | DE:de
- EV リース 残価 | JP:ja
- 新能源汽车 租赁 残值

## 보험
주제어: 보험, 손해율, insurance, insurer, premium, underwriting, versicherung, 保険, 保险, 车险
- 전기차 보험료
- 보험 배터리 데이터 전기차
- EV insurance claims
- EV 保険 バッテリー
- 新能源车险
- Kfz-Versicherung Elektroauto | DE:de
- EV insurance premiums | GB:en
- EV insurance repair costs | US:en
- EV 保険料 | JP:ja

## 정책·시장 | 참고
- 전기차 신규 등록
- BEV registrations | GB:en
- Neuzulassungen Elektroautos | DE:de
- EV sales quarter | US:en
- 新能源汽车 渗透率
- EV 販売台数 | JP:ja
