"""CSV -> data.js (PLAYERS, PROJECTS). 프로젝트는 목업용으로 임의 생성/배정."""
import csv, json, random

random.seed(42)
rows = list(csv.DictReader(open('2019_kbo_for_kaggle_v2.csv', encoding='utf-8')))
f = lambda v: round(float(v), 3) if v else 0

players = {}
for r in rows:
    pid = f"{r['batter_name']}_{r['year_born']}"
    players.setdefault(pid, []).append(r)

PLAYERS = []
for pid, hist in players.items():
    hist.sort(key=lambda r: r['year'])
    last = hist[-1]
    if last['year'] != '2018':
        continue
    PLAYERS.append({
        'id': pid, 'name': last['batter_name'], 'age': int(float(last['age'])),
        'pos': last['cp'], 'hand': last['hand2'], 'salary': int(last['salary'] or 0),
        'war': f(last['war']), 'avg': f(last['avg']), 'obp': f(last['OBP']), 'slg': f(last['SLG']),
        'ops': f(last['OPS']), 'hr': int(float(last['HR'])), 'rbi': int(float(last['RBI'])), 'sb': int(float(last['SB'])),
        'history': [{'year': int(r['year']), 'g': int(float(r['G'])), 'avg': f(r['avg']), 'hr': int(float(r['HR'])),
                     'ops': f(r['OPS']), 'war': f(r['war']), 'salary': int(r['salary'] or 0)} for r in hist],
        'projects': [],
    })

POS = sorted({p['pos'] for p in PLAYERS})
by_pos = {pos: [p for p in PLAYERS if p['pos'] == pos] for pos in POS}

PROJECT_SPECS = [
    ('2016 시즌 리빌딩 TF', '완료'), ('2016 수비 강화 프로젝트', '완료'), ('2017 클린업 재편', '완료'),
    ('2017 퓨처스 육성 프로젝트', '완료'), ('2017 올스타 매칭', '완료'), ('2018 가을야구 프로젝트', '완료'),
    ('2018 국가대표 구성', '완료'), ('2019 시즌 주전 라인업', '진행중'), ('2019 대주자·대수비 풀', '진행중'),
    ('2019 해외 교류전', '진행중'),
]
COMMENTS = {5: '핵심 기여, 재투입 강력 추천', 4: '기대 이상 성과', 3: '무난한 수행', 2: '기복 있음', 1: '기대 이하'}
ongoing = set()
PROJECTS = []
for i, (name, status) in enumerate(PROJECT_SPECS):
    positions = random.sample(POS, random.randint(4, len(POS)))
    members = []
    for pos in positions:
        pool = [p for p in by_pos[pos] if status == '완료' or p['id'] not in ongoing]
        for p in random.sample(pool, min(len(pool), random.randint(1, 3 if status == '진행중' else 2))):
            entry = {'project': f'P{i}', 'pos': pos}
            if status == '완료':
                entry['rating'] = max(1, min(5, round(3 + p['war'] / 2 + random.uniform(-1, 1))))
                entry['comment'] = COMMENTS[entry['rating']]
            else:
                ongoing.add(p['id'])
            p['projects'].append(entry)
            members.append(p['id'])
    PROJECTS.append({'id': f'P{i}', 'name': name, 'status': status, 'positions': positions, 'members': members,
                     'budget': sum(p['salary'] for p in PLAYERS if p['id'] in members) // 1000 * 1000 + 10000})

for p in PLAYERS:
    p['busy'] = p['id'] in ongoing

with open('data.js', 'w', encoding='utf-8') as out:
    out.write('window.PLAYERS = ' + json.dumps(PLAYERS, ensure_ascii=False) + ';\n')
    out.write('window.PROJECTS = ' + json.dumps(PROJECTS, ensure_ascii=False) + ';\n')
    out.write('window.POSITIONS = ' + json.dumps(POS, ensure_ascii=False) + ';\n')

assert len(PLAYERS) > 150 and all(p['salary'] > 0 for p in PLAYERS)
print(f'{len(PLAYERS)} players, {len(PROJECTS)} projects, {len(ongoing)} busy')
