# EV 시장·정책 브리핑 수집 목록

GitHub Actions의 collect.py가 매시간 이 파일(A·B절)과 watchlist.md를 읽어 data 브랜치의 items.jsonl에 새 항목을 쌓습니다. 판정 규칙은 예약 작업 프롬프트에, 표적 검색어는 watchlist.md에 있습니다.

## A. 목록
형식: `- 이름 | 권역 | 방식 | URL | 옵션`
- 방식: `rss` 또는 `html:<기사 링크 정규식>`(목록 페이지의 기사 링크를 뽑음)
- 옵션: `전체`는 제목 필터 없이 모두 수집, 비우면 B절 단어가 제목에 있는 항목만 수집

- 전기신문 | 한국 | rss | https://www.electimes.com/rss/allArticle.xml |
- 디일렉 | 한국 | rss | https://www.thelec.kr/rss/allArticle.xml |
- 전자신문 | 한국 | rss | https://rss.etnews.com/Section902.xml |
- 한국경제 | 한국 | rss | https://www.hankyung.com/feed/economy |
- 모터그래프 | 한국 | rss | https://www.motorgraph.com/rss/allArticle.xml | 전체
- 한국보험신문 | 한국 | rss | https://www.insnews.co.kr/rss/allArticle.xml |
- 보험저널 | 한국 | rss | https://www.insjournal.co.kr/rss/allArticle.xml |
- electrive | EU | rss | https://www.electrive.com/feed/ | 전체
- electrive.net | EU | rss | https://www.electrive.net/feed/ | 전체
- Handelsblatt 기업 | EU | rss | https://feeds.cms.handelsblatt.com/unternehmen |
- Handelsblatt 정치 | EU | rss | https://feeds.cms.handelsblatt.com/politik |
- Just Auto | EU | rss | https://www.just-auto.com/feed/ |
- kfz-betrieb | EU | rss | https://www.kfz-betrieb.vogel.de/rss/news.xml |
- Insurance Journal | 미국 | rss | https://www.insurancejournal.com/rss/news/national/ |
- Electrek | 미국 | rss | https://electrek.co/feed/ | 전체
- Repairer Driven News | 미국 | rss | https://www.repairerdrivennews.com/feed/ |
- Auto Remarketing | 미국 | rss | https://www.autoremarketing.com/feed/ |
- CBT News | 미국 | rss | https://www.cbtnews.com/feed/ |
- GlobeNewswire 자동차 | 미국 | rss | https://www.globenewswire.com/RssFeed/industry/3000-Automobiles%20Parts/feedTitle/GlobeNewswire%20-%20Industry%20News%20on%20Automobiles%20Parts |
- 미국 에너지부 | 미국 | html:/articles/ | https://www.energy.gov/newsroom |
- NHTSA | 미국 | html:/press-releases/ | https://www.nhtsa.gov/press-releases |
- 第一财经 | 중국 | html:/news/\d+\.html | https://www.yicai.com/news/ |
- 盖世汽车 | 중국 | html:/news/\d{6}/ | https://auto.gasgoo.com/ | 전체
- CnEVPost | 중국 | rss | https://cnevpost.com/feed/ | 전체
- 중국 공업정보화부 | 중국 | html:/art/20\d\d/ | https://www.miit.gov.cn/ |
- Response | 일본 | rss | https://response.jp/rss/index.rdf |
- 日刊工業新聞 | 일본 | rss | https://www.nikkan.co.jp/rss/nksrdf.rdf |
- 日刊自動車新聞 | 일본 | html:/archives/\d+ | https://www.netdenjd.com/ | 전체
- eletric-vehicles.com(발견 전용, 리포트 URL로 쓰지 않음) | 미국 | rss | https://eletric-vehicles.com/feed/ | 전체

## B. 제목 필터 단어
옵션이 비어 있는 목록은 제목에 아래 단어 중 하나가 있어야 수집합니다. 영문은 단어 경계로, 나머지는 포함 여부로 봅니다(대소문자 무시).

전기차, 전기자동차, 배터리, 이차전지, 2차전지, 전고체, 리튬, 니켈, 양극재, 충전, 중고차, 자동차보험, 잔존가치, 잔가, 리스, 보조금, 세액공제, 관세, 연비, 완성차, 현대차, 기아, LG에너지솔루션, 삼성SDI, SK온, 사용후, 재제조, 이력관리
EV, EVs, electric vehicle, electric vehicles, electric car, battery, batteries, lithium, charging, used car, used cars, residual, lease, leasing, auto insurance, tariff, tariffs, subsidy, tax credit, fuel economy, CAFE, emissions, right to repair, vehicle data, recycling, second-life, OBD, telematics
电动, 新能源, 电池, 锂, 充电, 换电, 二手车, 保值, 车险, 关税, 补贴, 购置税, 回收, 溯源
電気自動車, 電池, バッテリー, リチウム, 充電, 中古車, 残価, 自動車保険, 関税, 補助金, 燃費, リサイクル
Elektroauto, Elektroautos, E-Auto, E-Autos, Batterie, Akku, Lithium, Gebrauchtwagen, Restwert, Leasing, Kfz-Versicherung, Zoll, Zölle, Förderung, Flottengrenzwert

## C. 1등급 도메인
같은 사건을 여러 매체가 보도했을 때 실을 URL을 고르는 데만 씁니다.

- 글로벌: reuters.com, bloomberg.com, apnews.com, ft.com, wsj.com, asia.nikkei.com
- 한국: yna.co.kr, news1.kr, hankyung.com, mk.co.kr, sedaily.com, edaily.co.kr, etnews.com, thelec.kr, electimes.com
- EU: electrive.com, electrive.net, handelsblatt.com, faz.net, automobilwoche.de, fleetnews.co.uk, autonews.com
- 미국: insideevs.com, insurancejournal.com, cnbc.com, coxautoinc.com
- 중국: news.cn, yicai.com, caixin.com, 21jingji.com, stcn.com, gasgoo.com
- 일본: nikkei.com, nikkan.co.jp, netdenjd.com, response.jp, kyodonews.jp
