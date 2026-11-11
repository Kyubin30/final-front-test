// standard.yml → graph-data.js (그래프 · 검색 · 노드 상세용)
// 사용법: node scripts/build-graph.mjs [standard.yml] [graph-data.js]
// ponytail: standard.yml은 "최상위 키 아래 평평한 객체 목록"뿐이라 YAML 라이브러리 없이 줄 단위로 읽음.
//           중첩 구조가 생기면 js-yaml로 교체
import { readFileSync, writeFileSync } from 'node:fs';

const [src = 'standard.yml', out = 'graph-data.js'] = process.argv.slice(2);

// ---------- 1. 파싱 ----------
const val = v => {
  v = v.trim();
  if (v === '' || v === '~' || v === 'null') return null;
  if (v === 'true' || v === 'false') return v === 'true';
  if (v.startsWith("'")) return v.slice(1, -1).replaceAll("''", "'");
  if (v.startsWith('"')) return JSON.parse(v);
  return v;
};
const Y = {};
let list = null, obj = null, bad = 0;
for (const line of readFileSync(src, 'utf8').split('\n')) {
  if (!line.trim() || line.startsWith('#') || line === '---') continue;
  let m;
  if ((m = line.match(/^(\w+):\s*(\[\])?\s*$/))) { list = Y[m[1]] = []; obj = null; }
  else if ((m = line.match(/^- (\w+):(.*)$/))) { obj = { [m[1]]: val(m[2]) }; list.push(obj); }
  else if ((m = line.match(/^ {2}(\w+):(.*)$/)) && obj) obj[m[1]] = val(m[2]);
  else bad++;
}
if (bad) console.warn(`읽지 못한 줄 ${bad}개`);

const by = (rows, k) => Object.fromEntries(rows.map(r => [r[k], r]));
const group = (rows, k) => rows.reduce((o, r) => ((o[r[k]] ||= []).push(r), o), {});
const CLIENT = by(Y.client, 'id'), PROJECT = by(Y.project, 'id'), SKILL = by(Y.skill, 'id'), ROLE = by(Y.role, 'id');
const JOB = by(Y.job, 'id'), GRADE = by(Y.job_grade, 'id'), SKILLSET = by(Y.skillset, 'id'), DOMAIN = by(Y.domain, 'id');
const PJ_DOMAIN = Object.fromEntries(Y.project_domain.map(r => [r.project_id, r.domain_id]));
const PJ_CLIENT = Object.fromEntries(Y.project_client.filter(r => r.relationship_kind === 'FINAL_CUSTOMER').map(r => [r.project_id, r.client_id]));
const MP_CLIENT = group(Y.member_project_client, 'project_id'), MP_ROLE = group(Y.member_project_role, 'project_id');
const MP_SKILL = group(Y.member_project_skill, 'project_id'), MP_DOMAIN = group(Y.member_project_domain, 'project_id');
const MJOB = group(Y.member_job, 'member_id'), MSKILL = group(Y.member_skill, 'member_id'), MPROJ = group(Y.member_project, 'member_id');
// 진행 중 = 개인 프로젝트 이력 종료일이 최근(RECENT 이후). assignment.is_current는 현재 소속 발령이라 전원 true여서 못 씀
const RECENT = '2026-10-01', NOW_MONTH = '2026-11';
const live = Y.member_project.filter(h => h.end_date && h.end_date >= RECENT);
const BUSY = new Set(live.map(h => h.member_id)), LIVE_PJ = new Set(live.map(h => h.standard_project_id));

// ---------- 2. 노드 · 링크 ----------
const nodes = [], index = {};
const add = (id, t, l, extra = {}) => index[id] ?? (index[id] = nodes.push({ id, t, l, a: new Set(), g: {}, ...extra }) - 1);
const W = new Map();  // "i,j" → 가중치
const link = (a, b, w = 1) => { if (a == null || b == null || a === b) return; const k = a < b ? `${a},${b}` : `${b},${a}`; W.set(k, (W.get(k) || 0) + w); };

const era = y => !y ? null : y < 2000 ? '~1999' : y < 2010 ? '2000–09' : y < 2018 ? '2010–17' : y < 2022 ? '2018–21' : '2022~';
const cgroup = c => !c ? null : !c.group_name ? '그룹 없음' : ['SK그룹', '카카오', '네이버'].includes(c.group_name) ? c.group_name : '기타 그룹';
Y.domain.forEach(d => add(d.id, 'domain', d.name, { g: { domain: d.name } }));
Y.job.forEach(j => add(j.id, 'job', j.name, { g: { job: j.name } }));

const project = id => {
  const p = PROJECT[id]; if (!p) return null;
  const i = add(id, 'proj', p.name, { s: LIVE_PJ.has(id) || (p.contract_end_month || '') >= NOW_MONTH ? 1 : 0 });
  const n = nodes[i], c = CLIENT[PJ_CLIENT[id]], d = DOMAIN[PJ_DOMAIN[id]];
  Object.assign(n.g, { domain: d?.name, group: cgroup(c), biz: p.business_type, era: era(+p.project_year) });
  if (d) link(i, index[d.id]);
  if (c) { const ci = add(c.id, 'client', c.name, { g: { group: cgroup(c) } }); link(i, ci); [c.legal_name, c.english_abbreviation].forEach(a => a && nodes[ci].a.add(a)); }
  return i;
};
const skill = id => {
  const s = SKILL[id]; if (!s) return null;
  return add(id, 'tech', s.name, { g: { kind: s.kind } });
};

for (const m of Y.member) {
  const id = m.member_id, jobs = (MJOB[id] || []).slice().sort((a, b) => (+b.level || 0) - (+a.level || 0));
  const mi = add(id, 'person', id, { s: BUSY.has(id) ? 1 : 0 });
  if (jobs[0]) Object.assign(nodes[mi].g, { job: JOB[jobs[0].job_id]?.name, grade: GRADE[jobs[0].job_grade_id]?.name });
  jobs.forEach(j => link(mi, index[j.job_id], 2));
  for (const h of MPROJ[id] || []) {
    const pi = project(h.standard_project_id);
    if (pi != null) link(mi, pi, 3);
    for (const c of MP_CLIENT[h.id] || []) if (c.client_id && index[c.client_id] != null && c.client) nodes[index[c.client_id]].a.add(c.client);
    for (const s of MP_SKILL[h.id] || []) {
      const si = skill(s.skill_id); if (si == null) continue;
      if (s.skill) nodes[si].a.add(s.skill);
      link(mi, si); if (pi != null) link(pi, si, .5);
    }
  }
}

// ---------- 3. 묶음 값: 자기 속성 → 비어 있으면 이웃 다수결 (2회) ----------
const GROUPS = [['domain', '도메인'], ['job', '직무'], ['grade', '직무등급'], ['group', '고객사 그룹'], ['biz', '사업 유형'], ['kind', '기술 분류'], ['era', '프로젝트 시기']];
const adj = nodes.map(() => []);
for (const k of W.keys()) { const [a, b] = k.split(',').map(Number); adj[a].push(b); adj[b].push(a); }
for (let pass = 0; pass < 2; pass++) {
  const fill = nodes.map(n => ({ ...n.g }));
  nodes.forEach((n, i) => {
    for (const [k] of GROUPS) {
      if (n.g[k]) continue;
      const cnt = {};
      for (const j of adj[i]) { const v = nodes[j].g[k]; if (v) cnt[v] = (cnt[v] || 0) + 1; }
      const best = Object.entries(cnt).sort((a, b) => b[1] - a[1])[0];
      if (best) fill[i][k] = best[0];
    }
  });
  nodes.forEach((n, i) => n.g = fill[i]);
}
// 무리 이름 순서: 도메인 · 직무 · 등급은 표준 목록 순서, 시기는 시간순, 나머지는 크기순
const ORDER = { domain: Y.domain.map(d => d.name), job: Y.job.map(j => j.name), grade: Y.job_grade.map(g => g.name), era: ['~1999', '2000–09', '2010–17', '2018–21', '2022~'] };
const groups = GROUPS.map(([key, name]) => {
  const cnt = {};
  nodes.forEach(n => { const v = n.g[key]; if (v) cnt[v] = (cnt[v] || 0) + 1; });
  const labels = (ORDER[key] || Object.keys(cnt).sort((a, b) => cnt[b] - cnt[a])).filter(l => cnt[l]);
  return { key, name, labels };
});

// ---------- 4. 상세 데이터 ----------
const proj = {};
for (const n of nodes) if (n.t === 'proj') {
  const p = PROJECT[n.id];
  proj[n.id] = [p.business_type, p.contract_start_month, p.contract_end_month, PJ_CLIENT[n.id] || null, PJ_DOMAIN[n.id] || null, p.program_key];
}
const member = {};
for (const m of Y.member) {
  const id = m.member_id;
  member[id] = {
    jobs: (MJOB[id] || []).map(j => [JOB[j.job_id]?.name, GRADE[j.job_grade_id]?.name, SKILLSET[j.skillset_id]?.name, +j.level || null, j.career]),
    skills: (MSKILL[id] || []).map(s => [s.skill, s.proficiency, s.category]),
    hist: (MPROJ[id] || []).map(h => [h.name, h.standard_project_id, h.start_date, h.end_date,
      (MP_CLIENT[h.id] || []).map(c => [c.client, c.client_id]),
      (MP_ROLE[h.id] || []).map(r => [r.role, ROLE[r.role_id]?.name || null]),
      (MP_SKILL[h.id] || []).map(s => [s.skill, s.skill_id]),
      (MP_DOMAIN[h.id] || []).map(d => DOMAIN[d.domain_id]?.name)]),
  };
}

const data = {
  groups,
  nodes: nodes.map(n => {
    const o = { id: n.id, t: n.t, l: n.l, g: groups.map(gr => gr.labels.indexOf(n.g[gr.key])) };
    if (n.s) o.s = 1;
    const a = [...n.a].filter(x => x !== n.l).slice(0, 10);
    if (a.length) o.a = a;
    return o;
  }),
  links: [...W].flatMap(([k, w]) => [...k.split(',').map(Number), +w.toFixed(1)]),
  proj, member,
  client: Object.fromEntries(nodes.filter(n => n.t === 'client').map(n => [n.id, [CLIENT[n.id].legal_name, CLIENT[n.id].group_name]])),
  kind: Object.fromEntries(nodes.filter(n => n.t === 'tech').map(n => [n.id, SKILL[n.id].kind])),
};
const js = `// 생성 파일: node scripts/build-graph.mjs (원본 standard.yml). 직접 고치지 말 것\nwindow.STD = ${JSON.stringify(data)};\n`;
writeFileSync(out, js);

const types = nodes.reduce((o, n) => (o[n.t] = (o[n.t] || 0) + 1, o), {});
console.log('노드', nodes.length, types, '링크', W.size);
console.log('무리', groups.map(g => `${g.name} ${g.labels.length}`).join(' · '));
console.log('미분류', groups.map(g => `${g.name} ${data.nodes.filter(n => n.g[groups.indexOf(g)] < 0).length}`).join(' · '));
console.log('파일', (js.length / 2 ** 20).toFixed(2), 'MB');
