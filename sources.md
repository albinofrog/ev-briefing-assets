# EV 시장·정책 브리핑 수집 목록

GitHub Actions의 collect.py가 매시간 이 파일(A·B·E절)과 watchlist.md를 읽어 data 브랜치의 items.jsonl에 새 항목을 쌓습니다. 주제 검색은 구글 뉴스가 주 경로이고 Bing은 예비입니다. 판정 규칙은 예약 작업 프롬프트에, 표적 검색어는 watchlist.md에 있습니다.

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
옵션이 비어 있는 목록은 제목에 아래 단어 중 하나가 있어야 수집합니다. 영문은 단어 경계로(단어 사이 공백은 하이픈도 허용), 나머지는 포함 여부로 봅니다(대소문자 무시).

전기차, 전기자동차, 배터리, 이차전지, 2차전지, 전고체, 리튬, 니켈, 양극재, 충전, 중고차, 자동차보험, 잔존가치, 잔가, 리스, 보조금, 세액공제, 관세, 연비, 완성차, 현대차, 기아, LG에너지솔루션, 삼성SDI, SK온, 사용후, 재제조, 이력관리, 자동차 데이터, 차량 데이터, 데이터 개방, 손해율, 자보, 차보험, 친환경차, 잔존수명, 성능점검, 중고 전기차
EV, EVs, electric vehicle, electric vehicles, electric car, battery, batteries, lithium, charging, used car, used cars, residual, lease, leasing, auto insurance, tariff, tariffs, subsidy, tax credit, fuel economy, CAFE, emissions, right to repair, vehicle data, recycling, second-life, OBD, telematics, Data Act, connected car, in-vehicle data, data access, BMS, state of health, SOH, used vehicle, used vehicles, pre-owned, depreciation, remarketing, residual values, insurer, insurers
电动, 新能源, 电池, 锂, 充电, 换电, 二手车, 保值, 车险, 关税, 补贴, 购置税, 回收, 溯源, 汽车数据, 车辆数据, 动力电池, 退役电池, 电池健康
電気自動車, 電池, バッテリー, リチウム, 充電, 中古車, 残価, 自動車保険, 関税, 補助金, 燃費, リサイクル, 車両データ, 電池診断
Elektroauto, Elektroautos, E-Auto, E-Autos, Batterie, Akku, Lithium, Gebrauchtwagen, Restwert, Leasing, Kfz-Versicherung, Zoll, Zölle, Förderung, Flottengrenzwert, Datenzugang, Fahrzeugdaten, Data Act, Batteriezustand, Restwerte

## C. 1등급 도메인
같은 사건을 여러 매체가 보도했을 때 실을 URL을 고르는 데만 씁니다.

- 글로벌: reuters.com, bloomberg.com, apnews.com, ft.com, wsj.com, asia.nikkei.com
- 한국: yna.co.kr, news1.kr, hankyung.com, mk.co.kr, sedaily.com, edaily.co.kr, etnews.com, thelec.kr, electimes.com
- EU: electrive.com, electrive.net, handelsblatt.com, faz.net, automobilwoche.de, fleetnews.co.uk, autonews.com
- 미국: insideevs.com, insurancejournal.com, cnbc.com, coxautoinc.com
- 중국: news.cn, yicai.com, caixin.com, 21jingji.com, stcn.com, gasgoo.com
- 일본: nikkei.com, nikkan.co.jp, netdenjd.com, response.jp, kyodonews.jp

## D. 주체 별칭
사건 중복 판정에서 같은 주체로 봅니다. 한 줄에 같은 주체의 여러 표기를 `=`로 잇습니다. 새로 겹치는 주체가 나오면 줄을 추가합니다.

- NIO Inc. = NIO = NIO Power = 蔚来 = 니오
- Geely Holding Group = Geely = 吉利 = 지리
- Contemporary Amperex Technology Co., Limited = CATL = 宁德时代 = 닝더스다이
- BYD Company Limited = BYD = 比亚迪 = 비야디 = BYD Auto Japan = BYD오토재팬
- Toyota Motor Corporation = Toyota = 토요타 = トヨタ
- Honda Motor Co., Ltd. = Honda = 혼다 = ホンダ
- Nissan Motor Co., Ltd. = Nissan = 닛산 = 日産
- 현대자동차그룹 = 현대자동차 = 현대차 = 현대차그룹 = Hyundai Motor Group = Hyundai Motor Company = Hyundai
- 기아 = Kia
- LG에너지솔루션 = LG엔솔 = LG Energy Solution
- 삼성SDI = Samsung SDI
- SK온 = SK On
- Volkswagen AG = Volkswagen = VW = 폭스바겐
- PowerCo SE = PowerCo = 파워코
- Tesla, Inc. = Tesla = 테슬라
- General Motors = GM = 제너럴모터스
- Ford Motor Company = Ford = 포드
- Stellantis N.V. = Stellantis = 스텔란티스
- Renault Group = Renault = 르노
- Mercedes-Benz Group = Mercedes-Benz = 메르세데스벤츠 = 벤츠
- BMW AG = BMW
- ACEA = European Automobile Manufacturers' Association = 유럽자동차제조협회
- Ministry of Industry and Information Technology = MIIT = 工业和信息化部 = 工信部 = 중국 공업정보화부 = 공업정보화부
- European Commission = EU 집행위원회 = 유럽연합 집행위원회 = EC
- U.S. Department of Transportation = USDOT = 미국 교통부
- National Highway Traffic Safety Administration = NHTSA = 미국 도로교통안전국
- 산업통상자원부 = 산업부 = MOTIE
- 국토교통부 = 국토부
- Transport & Environment = T&E = 유럽교통환경연합
- 宁德时代巧克力换电 = 巧克力换电 = Chocolate Swap = 초콜릿 배터리교환

## E. 수집 제외·발견 전용 도메인
`제외`는 수집 단계에서 버립니다(자체 매체·집계·SNS·유료 보도자료 면). `/`가 들어간 항목(도메인/경로)은 URL에 그 문자열이 있으면 버립니다. `발견 전용`은 남기되 후보 점수를 낮추고, 리포트에는 원 매체 URL을 찾아 씁니다.

제외: chejiahao.autohome.com.cn, k.sina.com.cn, aikahao.xcar.com.cn, user.guancha.cn, thecooldown.com, usatoday.com/press-release/, timeline.sohu.com, baijiahao.baidu.com, toutiao.com, tradingview.com, zhihu.com, weibo.com, tistory.com, blog.naver.com, post.naver.com, brunch.co.kr, medium.com, substack.com, note.com, x.com, twitter.com, facebook.com, linkedin.com, youtube.com, reddit.com, wikipedia.org, marketbeat.com
발견 전용: sina.com.cn, sina.cn, sohu.com, 163.com, qq.com, msn.com, naver.com, daum.net, yahoo.com, yahoo.co.jp, news.google.com, bing.com, eletric-vehicles.com

## F. 관련도 주체
제목에 이 주체가 나오면 핵심어가 없어도 해당 관련도로 보고 후보 점수를 매깁니다(정렬용, 판정은 프롬프트 5절). 대소문자를 구분합니다.

- Aviloo | R1
- TWAICE | R1
- Recurrent | R1
- 민테크 = Mintech | R1
- 피엠그로우 = PMGROW | R1
- Geotab | R1
- Volytica | R1
- ACCURE | R1
- Altelium | R1
- Smartcar | R1
- High Mobility | R1
- Mobilisights | R1
- cap hpi = Cap HPI | R1
- NIO Power = 蔚来能源 = 니오파워 | R2
- 巧克力换电 = Chocolate Swap = 초콜릿 배터리교환 | R2
- DEKRA | R2
- TÜV SÜD = TÜV Rheinland = TÜV | R2
- Autovista = Autovista24 | R2
- Black Book | R2
- Manheim | R2
- Cox Automotive | R2
- J.D. Power | R2
- 中国汽车流通协会 = CADA | R2
- Ayvens = Arval = LeasePlan | R2
- 현대캐피탈 = SK렌터카 = 롯데렌탈 | R2
- 케이카 = 엔카 = Encar | R2
- Carvana = CarMax | R2
- 瓜子二手车 = 优信 | R2
- 삼성화재 = 현대해상 = DB손해보험 = DB손보 = KB손해보험 | R2
