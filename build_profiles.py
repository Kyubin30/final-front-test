"""마스킹 프로필 데이터 사전의 칼럼 구조로 목업 구성원 프로필 생성 -> profiles.js
값 유형: 정형(code) / 반정형(semi, 표기 변형) / 자유기술(free, 정규화 대상)."""
import json, random, re

random.seed(7)

DOMAINS = ['통신', '제조 대내 Hi-Tech', '유통/물류/서비스', '제조 대내 Process', '제조 대외', '공공', '제1금융', '제2금융', '미디어/콘텐츠', 'Global']
GRADES = [('Associate', 650), ('Specialist', 850), ('Pro', 1050), ('Expert', 1350), ('Master', 1700)]  # (직무등급, 목업 월 단가 기준 만원)
JOBS = {  # 직무 13종 -> 스킬셋
    'AI': ['Generative AI Development', 'AI/Data Development'],
    'Software Development': ['Back-end Development', 'Front-end Development'],
    'Project Management': ['Application PM', 'Infra PM'],
    'Data': ['Data Engineering', 'Data Architecting'],
    'Cloud': ['Cloud Native Development', 'Cloud Infra Engineering'],
    'Infra': ['System Engineering'], 'Security': ['Security Consulting'],
    'Consulting': ['Business Consulting', 'AX Strategy'], 'Architecture': ['Application Architecting'],
    'QA': ['Test Engineering'], 'UX': ['UX Design'], 'Operation': ['Service Operation'], 'Solution Sales': ['Solution Sales'],
}
JOB_W = {'AI': 9, 'Software Development': 9, 'Project Management': 5, 'Data': 6, 'Cloud': 5, 'Infra': 3, 'Security': 2,
         'Consulting': 3, 'Architecture': 3, 'QA': 2, 'UX': 2, 'Operation': 3, 'Solution Sales': 1}
TECH = {  # 정형 기술명: (분류, 자유기술 표기 변형)
    'Python': ('언어_개발', ['python', '파이썬', 'Python3']), 'Java': ('언어_개발', ['JAVA', 'java', '자바']),
    'TypeScript': ('프론트엔드 개발_언어', ['typescript', 'TS']), 'React': ('프론트엔드 개발_프레임워크', ['ReactJS', 'react.js', '리액트']),
    'Spring Boot': ('백엔드 개발_프레임워크', ['SpringBoot', 'spring boot', '스프링부트']), 'Node.js': ('백엔드 개발_프레임워크', ['NodeJS', 'node']),
    'Kafka': ('데이터_개발', ['kafka', '카프카']), 'Spark': ('데이터_개발', ['pyspark', 'spark']), 'Airflow': ('데이터_개발', ['airflow']),
    'MariaDB': ('백엔드 개발_데이터베이스', ['mariadb', '마리아DB']), 'Oracle': ('백엔드 개발_데이터베이스', ['오라클', 'ORACLE', 'Oracle DB']),
    'PostgreSQL': ('백엔드 개발_데이터베이스', ['postgres', 'PostgresQL']), 'Redis': ('백엔드 개발_데이터베이스', ['redis']),
    'Kubernetes': ('클라우드_인프라', ['k8s', 'K8S', '쿠버네티스']), 'Docker': ('클라우드_인프라', ['docker', '도커']),
    'AWS': ('클라우드_인프라', ['aws', '아마존웹서비스']), 'Azure': ('클라우드_인프라', ['MS Azure', 'azure']),
    'Terraform': ('클라우드_인프라', ['terraform']), 'Linux': ('인프라_OS', ['linux', '리눅스']),
    'LangChain': ('AI_프레임워크', ['langchain', '랭체인']), 'PyTorch': ('AI_프레임워크', ['pytorch', 'torch']),
    'RAG': ('AI_아키텍처', ['rag', '검색증강생성']), 'Elasticsearch': ('데이터_검색', ['elastic', 'ES']), 'SAP': ('ERP_솔루션', ['SAP ERP', 'sap']),
    'Selenium': ('테스트_자동화', ['selenium', '셀레니움']), 'Figma': ('디자인_도구', ['figma', '피그마']),
}
JOB_TECH = {
    'AI': ['Python', 'PyTorch', 'LangChain', 'RAG', 'Elasticsearch', 'Docker'],
    'Software Development': ['Java', 'Spring Boot', 'React', 'TypeScript', 'Node.js', 'MariaDB', 'Oracle', 'Redis'],
    'Project Management': ['Oracle', 'Java', 'SAP', 'AWS'], 'Data': ['Python', 'Kafka', 'Spark', 'Airflow', 'PostgreSQL', 'Oracle'],
    'Cloud': ['Kubernetes', 'Docker', 'AWS', 'Azure', 'Terraform', 'Linux'], 'Infra': ['Linux', 'Oracle', 'Docker', 'AWS'],
    'Security': ['Linux', 'AWS', 'Kubernetes'], 'Consulting': ['SAP', 'Python'], 'Architecture': ['Java', 'Spring Boot', 'Kubernetes', 'Kafka', 'AWS'],
    'QA': ['Selenium', 'Java', 'Python'], 'UX': ['Figma', 'React', 'TypeScript'], 'Operation': ['Linux', 'Oracle', 'Redis', 'Elasticsearch'],
    'Solution Sales': ['SAP', 'AWS'],
}
JUNK = ['N/A', '.', '-', '해당없음', '사업제안', '컨설팅', '비대상']
CLIENTS = {  # 고객사 표준(법인 기준): 반정형 표기 변형. SK(주)는 계약 주체가 최종 고객 자리에 들어간 경우
    '에스케이텔레콤(주)': ['에스케이텔레콤(주)', 'SKT', 'SK텔레콤', 'SK(주)'], '(주)신한은행': ['(주)신한은행', '신한은행', 'Shinhan Bank'],
    'KB손해보험(주)': ['KB손해보험(주)', 'KB손보', '케이비손해보험'], '국민연금공단': ['국민연금공단', 'NPS'],
    '에스케이하이닉스(주)': ['에스케이하이닉스(주)', 'SK하이닉스', 'SK hynix'], '현대자동차(주)': ['현대자동차(주)', '현대차'],
    '롯데쇼핑(주)': ['롯데쇼핑(주)', '롯데쇼핑'], '한국전력공사': ['한국전력공사', '한전', 'KEPCO'],
    '(주)씨제이이엔엠': ['(주)씨제이이엔엠', 'CJ ENM'], '삼성생명보험(주)': ['삼성생명보험(주)', '삼성생명'],
}
# PMS 공식 프로젝트(정규화 표준): (공식명, 고객사, 도메인, 시작, 종료, 기술, 자유기술 표기 변형)
PMS = [
    ('SKT 에이닷 비즈 멤버사 확산 Product 개발', '에스케이텔레콤(주)', '통신', '2025-03-01', '현재', ['Python', 'LangChain', 'RAG', 'Kubernetes'],
     ['SKT 25년 에이닷 비즈(A. Biz) 멤버사 확산 Product 개발-WF1팀', 'A.Biz 멤버사 확산', '에이닷비즈 확산 PJT']),
    ('SKT 에이닷 비즈 DevOps 운영', '에스케이텔레콤(주)', '통신', '2024-07-01', '현재', ['Kubernetes', 'Docker', 'AWS', 'Linux'],
     ['SKT 25년 에이닷 비즈 DevOps 운영-WF1', '에이닷 DevOps 운영', 'A. Biz 운영']),
    ('SKT 차세대 빌링 시스템 구축', '에스케이텔레콤(주)', '통신', '2021-02-01', '2022-12-31', ['Java', 'Spring Boot', 'Oracle', 'Kafka'],
     ['SKT 차세대 빌링 구축', 'T 빌링 차세대 PJT', '차세대 Billing 시스템 구축 2단계']),
    ('SKT 고객센터 AICC 구축', '에스케이텔레콤(주)', '통신', '2023-03-01', '2024-02-29', ['Python', 'PyTorch', 'Elasticsearch', 'Kafka'],
     ['SKT AICC 구축', 'T고객센터 AI 컨택센터', 'AICC 1차']),
    ('신한은행 차세대 계정계 구축', '(주)신한은행', '제1금융', '2020-05-01', '2022-04-30', ['Java', 'Spring Boot', 'Oracle'],
     ['신한은행 차세대 구축', '신한 차세대 PJT', '(주)신한은행 차세대 계정계']),
    ('신한은행 마이데이터 플랫폼 구축', '(주)신한은행', '제1금융', '2022-06-01', '2023-05-31', ['Java', 'Kafka', 'Redis', 'AWS'],
     ['신한 마이데이터', '신한은행 MyData 플랫폼', '마이데이터 구축 PJT']),
    ('KB손보 차세대 시스템 구축', 'KB손해보험(주)', '제2금융', '2019-03-01', '2021-02-28', ['Java', 'Oracle', 'Spring Boot'],
     ['KB손보 차세대', 'KB손해보험 차세대 구축사업', 'KB 차세대 PJT']),
    ('국민연금공단 지능형 연금복지 통합플랫폼 구축', '국민연금공단', '공공', '2023-01-01', '2024-12-31', ['Java', 'Python', 'PostgreSQL', 'RAG'],
     ['국민연금 지능형 플랫폼', 'NPS 연금복지 통합플랫폼', '지능형 연금복지 플랫폼 구축']),
    ('SK하이닉스 FAB 데이터 레이크 구축', '에스케이하이닉스(주)', '제조 대내 Hi-Tech', '2022-01-01', '2023-06-30', ['Python', 'Spark', 'Airflow', 'Kafka'],
     ['하이닉스 Data Lake', 'SK hynix FAB 데이터레이크', 'FAB DL 구축']),
    ('SK하이닉스 수율 예측 AI 고도화', '에스케이하이닉스(주)', '제조 대내 Hi-Tech', '2024-03-01', '현재', ['Python', 'PyTorch', 'Spark'],
     ['하이닉스 수율예측 AI', '수율 예측 모델 고도화', 'Yield AI 고도화']),
    ('현대차 커넥티드카 서비스 플랫폼 구축', '현대자동차(주)', '제조 대외', '2021-09-01', '2023-02-28', ['Java', 'Kafka', 'Kubernetes', 'AWS'],
     ['현대차 커넥티드카', '커넥티드 카 플랫폼 구축', 'CCS 플랫폼']),
    ('롯데쇼핑 통합 커머스 플랫폼 구축', '롯데쇼핑(주)', '유통/물류/서비스', '2020-01-01', '2021-06-30', ['Java', 'React', 'Node.js', 'MariaDB'],
     ['롯데ON 통합 커머스', '롯데쇼핑 커머스 플랫폼', '통합몰 구축']),
    ('한국전력공사 전력 데이터 분석 플랫폼', '한국전력공사', '공공', '2019-06-01', '2020-12-31', ['Python', 'Spark', 'PostgreSQL'],
     ['한전 전력데이터 플랫폼', 'KEPCO 데이터 분석', '전력 빅데이터 플랫폼']),
    ('CJ ENM 콘텐츠 추천 시스템 고도화', '(주)씨제이이엔엠', '미디어/콘텐츠', '2022-04-01', '2023-03-31', ['Python', 'PyTorch', 'Redis', 'AWS'],
     ['CJ ENM 추천 고도화', '티빙 콘텐츠 추천', '콘텐츠 추천엔진 고도화']),
    ('삼성생명 보험 심사 자동화', '삼성생명보험(주)', '제2금융', '2023-07-01', '2024-06-30', ['Python', 'LangChain', 'RAG', 'Azure'],
     ['삼성생명 언더라이팅 자동화', '보험심사 AI 자동화', '삼성생명 심사자동화 PJT']),
    ('Talent AX 구축', '에스케이텔레콤(주)', '통신', '2025-09-01', '현재', ['Python', 'LangChain', 'PostgreSQL', 'React'],
     ['Talent AX', '인재 AX 플랫폼 구축', 'TalentAX 구축 PJT']),
    ('사내 OSS 클라우드 전환', '에스케이텔레콤(주)', '통신', '2023-05-01', '2024-04-30', ['Kubernetes', 'Terraform', 'Docker', 'Linux'],
     ['OSS 클라우드 전환', 'OSS Cloud Migration', 'OSS 전환 PJT']),
    ('신한은행 디지털 창구 UX 개선', '(주)신한은행', '제1금융', '2024-02-01', '2024-11-30', ['React', 'TypeScript', 'Figma'],
     ['신한 디지털창구 UX', '디지털 창구 개선', '신한 UX 개선 PJT']),
]
ROLES = {
    'Project Management': ['Project Leader', '프로젝트 PM', 'PM, PL, TA', 'PM; 일정·리스크·이해관계자 관리'],
    'AI': ['AI 모델 개발', 'LLM Engineer; RAG 파이프라인 구축', 'AI 개발 PL', 'Data Scientist'],
    'Data': ['데이터 엔지니어', 'DA; 데이터 모델링', '데이터 파이프라인 개발', 'Data Engineer'],
    'Software Development': ['개발자', 'Back-end 개발; API 개발', '단위업무 PL', 'Developer', 'FE 개발'],
    'Cloud': ['클라우드 엔지니어', 'DevOps; CI/CD 구축', 'TA', 'Infra 구축'],
    'Architecture': ['AA', '아키텍트; 표준 프레임워크 설계', 'TA, AA'], 'QA': ['QA', '테스트 자동화; 회귀 테스트'],
    'UX': ['UX 디자이너', 'UI/UX 설계'], 'Operation': ['운영', '서비스 운영; 장애 대응'],
}
DONE = ['구현 및 안정화', '설계·구축', '성능 개선(응답시간 40% 단축)', '운영 이관 완료', '고도화 및 확산']
THING = ['데이터 파이프라인', 'API 서버', 'RAG 검색 서비스', '모니터링 체계', '배치 처리', '추천 모델', '화면 프레임워크', 'CI/CD 파이프라인']
TEAMS = ['Talent AX추진팀', 'Data Engineering2팀', '전문 개발그룹', '전문 개발 그룹', 'AI Platform팀', 'Cloud Native팀', '금융사업1팀', '통신DT팀', '제조AX팀', 'PMO팀']
CERTS = [('정보처리기사', '국가인증', '한국산업인력공단'), ('Certified Kubernetes Administrator (CKA)', 'Vendor인증', 'The Linux Foundation'),
         ('AWS Certified Solutions Architect - Associate', 'Vendor인증', 'Amazon Web Services'), ('PMP', '국제인증', 'PMI'),
         ('SQLD', '국가인증', '한국데이터산업진흥원'), ('Azure AI Engineer Associate', 'Vendor인증', 'Microsoft'),
         ('OCJP (=SCJP)', 'Vendor인증', 'Oracle'), ('ADsP', '국가인증', '한국데이터산업진흥원')]
ACTS = [('사내 전문가 활동', '강의', '25년 10월 사내강의'), ('사내 전문가 활동', '심사활동 ', '사내 기술 심사'),
        ('대외 전문가 활동', '심사/자문', '공공 SW 사업 기술평가 자문'), ('프로보노 활동', '기타', '비영리 단체 IT 멘토링')]
AWARDS = ['부문장 Recognition', '2018년 부문장 Recognition', 'CEO 표창', '우수 PJT 포상']

rand_date = lambda y0, y1: f'{random.randint(y0, y1)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}'


def months(a, b):
    b = '2026-11-01' if b == '현재' else b
    (y0, m0), (y1, m1) = [map(int, d.split('-')[:2]) for d in (a, b)]
    return (y1 - y0) * 12 + m1 - m0


def norm_tech(raw):  # 자유기술 보유기술 -> 정형 기술명 (목업 정규화 결과)
    alias = {v.lower(): k for k, (_, vs) in TECH.items() for v in vs + [k]}
    return [{'raw': t, 'std': alias.get(t.lower())} for t in (x.strip() for x in re.split(r'[/,]', raw)) if t]


def conf():  # Jev 확신도 목업: 구간별 처리 경로
    c = round(random.choice([random.uniform(.9, .995)] * 6 + [random.uniform(.7, .9)] * 3 + [random.uniform(.5, .7)]), 2)
    return c, '자동 반영' if c >= .9 else '재검토' if c >= .7 else '사람 확인'


people = []
for i in range(1, 61):
    job = random.choices(list(JOB_W), weights=list(JOB_W.values()))[0]
    gi = random.choices(range(5), weights=[2, 4, 5, 3, 1])[0]
    lvl = min(5, max(1, gi + random.choice([0, 0, 1, -1])))
    career = round(random.uniform(2 + gi * 3, 6 + gi * 4), 1)
    pool = JOB_TECH[job]
    people.append({
        'id': f'P{i:02d}', 'job': job, 'grade': GRADES[gi][0], 'skillset': random.choice(JOBS[job]), 'level': lvl,
        'career': career, 'tenure': round(career * random.uniform(.5, 1), 1),
        'jobCareer': f'{int(career * .8)}년 {random.randint(0, 11)}개월', 'grantDate': rand_date(2023, 2025),
        'rate': GRADES[gi][1] + lvl * 40,  # 목업 내부단가(월, 만원) = 등급 기준 + 스킬셋 수준 가산
        'techs': [{'name': t, 'clas': TECH[t][0], 'lev': random.choice('상중중하')} for t in random.sample(pool, min(len(pool), random.randint(3, 5)))],
        'projects': [], 'careers': [],
        'certs': [dict(zip(['name', 'div', 'inst'], c), date=rand_date(2012, 2025)) for c in random.sample(CERTS, random.randint(0, 3))],
        'acts': [dict(zip(['div', 'type', 'name'], a), date=rand_date(2020, 2025)) for a in random.sample(ACTS, random.randint(0, 2))],
        'awards': [{'name': a, 'date': rand_date(2016, 2025), 'inst': 'SK㈜ C&C CEO' if 'CEO' in a else '부문장'} for a in random.sample(AWARDS, random.randint(0, 2))],
    })

# 프로젝트마다 기술이 맞는 구성원을 우선 배정 -> 함께 일한 관계(겹치는 프로젝트)가 생김
fit = lambda p, techs: len(set(techs) & set(JOB_TECH[p['job']])) + random.random() * 2
team = [sorted(people, key=lambda p: -fit(p, v[5]))[:random.randint(4, 7)] for v in PMS]
for p in people:  # 이력 없는 구성원은 가장 맞는 프로젝트에 추가
    if not any(p in m for m in team):
        team[max(range(len(PMS)), key=lambda i: fit(p, PMS[i][5]))].append(p)
projects = []
for pi, (name, client, dom, s, e, techs, variants) in enumerate(PMS):
    pid = f'J{pi:02d}'
    members = team[pi]
    for p in members:
        c1, s1 = conf()
        c2, s2 = conf()
        raw_tech = random.choice(['/', ', ', ' / ', ',']).join(
            random.choice(TECH[t][1] + [t]) for t in random.sample(techs, random.randint(1, len(techs))))
        if random.random() < .15:
            raw_tech = random.choice(JUNK) if random.random() < .5 else raw_tech + ', ' + random.choice(JUNK)
        role = random.choice(ROLES.get(p['job'], ['수행인력', 'TA', '설계/개발']))
        merged = random.random() < .1
        p['projects'].append({
            'raw': random.choice(variants), 'std': pid, 'conf': c1, 'route': s1,
            'domain': dom if random.random() > .1 else f'{dom} / {random.choice(DOMAINS)}',
            'clientRaw': random.choice(CLIENTS[client]), 'client': client, 'clientConf': c2, 'clientRoute': s2,
            'role': role, 'perf': ('[동일 기간 병합 프로젝트] ' if merged else '') + f'{random.choice(techs)} 기반 {random.choice(THING)} {random.choice(DONE)}',
            'cov': random.choice(['-', '-', '-', '2개 이상 시스템간']), 'techRaw': raw_tech, 'techNorm': norm_tech(raw_tech),
            'start': s, 'end': e,
        })
    projects.append({'id': pid, 'name': name, 'client': client, 'domain': dom, 'start': s, 'end': e, 'techs': techs,
                     'status': '진행중' if e == '현재' else '완료', 'members': [p['id'] for p in members]})

for p in people:
    p['projects'].sort(key=lambda x: x['start'], reverse=True)
    p['busy'] = any(x['end'] == '현재' for x in p['projects'])
    top = [t['name'] for t in p['techs'][:3]]
    p['core'] = f"{p['job']} 분야 {p['career']}년 경력을 바탕으로 {p['skillset']} 및 {', '.join(top)} 기반 시스템 설계·구축 역량을 보유하고 있습니다."
    p['desc'] = f"{p['skillset']} 관련 개발/설계/리딩 역량을 가지고 있습니다."
    p['levelReason'] = f"{random.choice(['다수 프로젝트', '대형 차세대 사업', '신규 플랫폼 구축'])}에서 {p['skillset']} 경험을 보유."
    for k, x in enumerate(p['projects'][:random.randint(1, 3)]):  # 주요 경력: 발령 이력 + 꼬리표 붙은 맥락
        pj = projects[int(x['std'][1:])]
        ctx = [f"[공식 PMS 투입이력]\n- {pj['name']} — {x['role'].split(';')[0]}",
               f"[본인 작성 · 프로젝트 수행이력]\n- {x['raw']} — {x['role']}"]
        if random.random() < .3:
            ctx.append(f"[당시 조직 업무 · 동료 근거 기반 추정 · 본인 수행 미확인]\n- {random.choice(PMS)[0]}")
        p['careers'].append({'team': random.choice(TEAMS), 'start': x['start'], 'end': x['end'], 'ctx': '\n'.join(ctx)})
    p['monthsTotal'] = sum(months(x['start'], x['end']) for x in p['projects'])

with open('profiles.js', 'w', encoding='utf-8') as out:
    for k, v in [('PEOPLE', people), ('PROJECTS', projects), ('DOMAINS', DOMAINS), ('JOBS', list(JOBS)),
                 ('TECHS', {k: {'clas': c, 'alias': a} for k, (c, a) in TECH.items()}), ('CLIENTS', CLIENTS),
                 ('PMS_ALIAS', {f'J{i:02d}': v[6] for i, v in enumerate(PMS)})]:
        out.write(f'window.{k} = {json.dumps(v, ensure_ascii=False)};\n')

# 셀프체크: 정규화 결과가 표준 목록 안에 있고, 함께 일한 관계가 존재
assert all(n['std'] in TECH or n['std'] is None for p in people for x in p['projects'] for n in x['techNorm'])
assert all(len(pj['members']) >= 4 for pj in projects) and all(p['projects'] for p in people)
assert norm_tech('k8s, 자바 / 사업제안') == [{'raw': 'k8s', 'std': 'Kubernetes'}, {'raw': '자바', 'std': 'Java'}, {'raw': '사업제안', 'std': None}]
print(f"{len(people)}명, 프로젝트 {len(projects)}개, 참여중 {sum(p['busy'] for p in people)}명, 이력 {sum(len(p['projects']) for p in people)}행")
