# EV 시장·정책 브리핑 참조 목록

예약 작업 프롬프트가 실행할 때 내려받아 쓰는 참조 데이터입니다. 판정 규칙은 프롬프트에 있고, 이 파일은 "무엇을 볼지"만 담습니다.

## A. 경로 1 목록 주소

N은 WebFetch로 나열할 최신 항목 수이며, 적혀 있지 않으면 30입니다. "후보 규칙"이 적힌 목록은 그 규칙을 일반 선별 규칙보다 우선합니다.

- 한국: 전기신문 `https://www.electimes.com/rss/allArticle.xml`, 디일렉 `https://www.thelec.kr/rss/allArticle.xml`, 전자신문 `https://rss.etnews.com/Section902.xml` (N=50), 한국경제 `https://www.hankyung.com/feed/economy` (N=50), 모터그래프(2등급) `https://www.motorgraph.com/rss/allArticle.xml`, 보험 전문지 insnews(2등급, ④ 발견용) `https://www.insnews.co.kr/rss/allArticle.xml` (N=50, 후보 규칙: 제목에 전기차·EV·배터리·자동차보험 중 하나가 있을 때만 후보), 보험 전문지 insjournal(2등급, ④ 발견용) `https://www.insjournal.co.kr/rss/allArticle.xml` (N=60, 후보 규칙: insnews와 같음)
- EU: electrive `https://www.electrive.com/feed/`, electrive.net `https://www.electrive.net/feed/`, Handelsblatt 기업 `https://feeds.cms.handelsblatt.com/unternehmen`, Handelsblatt 정치(dpa 기사 포함) `https://feeds.cms.handelsblatt.com/politik`, Just Auto(2등급) `https://www.just-auto.com/feed/`, kfz-betrieb(2등급, 독일 자동차 유통 전문지, ③ 발견용) `https://www.kfz-betrieb.vogel.de/rss/news.xml` (N=50, lastBuildDate가 날짜만 갱신되어 항상 00:00으로 찍히므로 "갱신 지연" 판정에서 제외하고 항목의 pubDate(시간대 포함)로만 판단)
- 미국: Insurance Journal `https://www.insurancejournal.com/rss/news/national/`, Electrek(2등급) `https://electrek.co/feed/`, Repairer Driven News(2등급, 차량 데이터·수리권) `https://www.repairerdrivennews.com/feed/`, Auto Remarketing(2등급, 중고차 리마케팅·오토 파이낸스, ③④ 발견용) `https://www.autoremarketing.com/feed/` (전체 20개), CBT News(2등급, 딜러 업계·중고차·통상 정책, ②③ 발견용) `https://www.cbtnews.com/feed/` (전체 15개)
- 중국: 第一财经 `https://www.yicai.com/news/`, 盖世汽车 `https://auto.gasgoo.com/`(`autodata.gasgoo.com` URL은 본문이 JS로 그려져 비어 있으므로 후보에서 제외), CnEVPost(2등급) `https://cnevpost.com/feed/`
- 일본: Response `https://response.jp/rss/index.rdf`, 日刊工業新聞 `https://www.nikkan.co.jp/rss/nksrdf.rdf` (N=50), 日刊自動車新聞 `https://www.netdenjd.com/`
- 공식 창구: 중국 공업정보화부 `https://www.miit.gov.cn/`, 미국 에너지부 `https://www.energy.gov/newsroom`, 미국 도로교통안전국 `https://www.nhtsa.gov/press-releases`. 한국 부처 발표는 매체 목록과 경로 3으로 발견합니다(korea.kr은 robots 차단).
- 보도자료 배포처(원출처): GlobeNewswire 자동차·부품 `https://www.globenewswire.com/RssFeed/industry/3000-Automobiles%20Parts/feedTitle/GlobeNewswire%20-%20Industry%20News%20on%20Automobiles%20Parts`
- 발견 전용 목록: eletric-vehicles.com `https://eletric-vehicles.com/feed/` (통신사 보도 발견용). 이 사이트의 URL은 리포트에 쓰지 않습니다.

## B. 제목 신호어

관세, 통상, 보조금, 세액공제, 소비세, 규제, 법안, 시행령, 연비, 잔존가치, 중고, 보험, 리스, 배터리, 리튬, 나트륨, 전고체, 재사용, 재제조 / tariff, subsidy, tax credit, regulation, rule, standards, fuel economy, CAFE, emissions, mandate, ban, residual, used EV, insurance, lease, battery, recycling, second-life / 关税, 补贴, 政策, 购置税, 保值, 二手, 车险, 电池, 碳酸锂, 回收 / 関税, 補助金, 規制, 燃費, 残価, 中古, 保険, 電池 / Zoll, Förderung, Steuer, Restwert, gebraucht, Versicherung, Batterie, E-Auto, Elektroauto

EV 전문 매체(질문형·비유형 제목도 후보로 둠): electrive, electrive.net, Electrek, CnEVPost, Just Auto, eletric-vehicles.com

## C. 경로 3 Bing RSS 표적 검색어 (21개)

| 축 | 검색어 |
|---|---|
| ① (3) | 碳酸锂 价格, EV registrations Europe, 전기차 판매 실적 |
| ② (7) | EV tariff China EU UK, fuel economy standards EV, connected vehicle ban China, 전기차 세액공제 보조금, 新能源汽车 关税 补贴, Batterieverordnung Batteriepass, right to repair vehicle data |
| ③ (5) | used EV prices residual value, gebrauchte Elektroautos Preise, 중고 전기차 시세, 二手新能源车 保值率, 中古EV 残価 |
| ④ (3) | EV insurance premiums, 전기차 보험료, 新能源车险 保费 |
| ⑤ (3) | EV battery health certificate, 사용후 배터리 재사용, 换电 电池 合作 |

## D. 1등급 도메인 (허용 목록)

- 글로벌: reuters.com, bloomberg.com, apnews.com, ft.com, wsj.com, asia.nikkei.com
- 한국: yna.co.kr, news1.kr, hankyung.com, mk.co.kr, sedaily.com, edaily.co.kr, etnews.com, thelec.kr, electimes.com
- EU: electrive.com, electrive.net, handelsblatt.com, faz.net, automobilwoche.de, fleetnews.co.uk, autonews.com(Automotive News Europe 포함)
- 미국: insideevs.com, insurancejournal.com, cnbc.com, coxautoinc.com
- 중국: news.cn, yicai.com, caixin.com, 21jingji.com, stcn.com, gasgoo.com
- 일본: nikkei.com, nikkan.co.jp, netdenjd.com, response.jp, kyodonews.jp
