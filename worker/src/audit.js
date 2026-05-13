const EXPECTED_SECTION_HEADERS = ['§1', '§2', '§3', '§4', '§5', '§6', '§7', '§8', '§9'];
const SLOT_PATTERN = /\{\{(\w+)\}\}/g;
const PLACEHOLDER_PATTERN = /\[(고객사|공정|수치|기간|%)(?=\]|[^\w가-힣])[^\]]*\]/g;
const PLACEHOLDER_WHITELIST = /\[고객사 — [^\]]+\]/g;
const META_LEAKAGE_PATTERNS = [
  /\bTODO\b/g,
  /\bFIXME\b/g,
  /\bsample_\w+/g,
  /\bDEFAULTS\b/g,
  /\bDOMAIN_PROFILE\b/g,
  /\bbuildSlots\b/g,
];

const DOMAIN_VOCAB = {
  STL: ['1ZHM', '2ZHM', 'BAF', '압연유', '스테인리스'],
  MET: ['CNC', '머시닝센터', '절삭 토크', '공구 마모'],
  RUB: ['밴버리', '가황', '압출', '고무 배합'],
  UTL: ['보일러', '압축기', '냉동기', '폐수 처리', 'SOx', 'NOx'],
  LLM: ['RAG', '환각률', '임베딩', 'BGE', 'KoAlpaca'],
  CAS: ['턴디시', '몰드', '연주', '용강', '슬라브'],
  HEA: ['가열로', 'QT', '퀜칭', '템퍼링', '결정립'],
  PLT: ['도금조', '전기도금', 'QUALICOAT', '분체도장', '정류기'],
  SHP: ['선각', '블록', '선급', 'DNV', 'ABS', '용접 비드'],
  ASM: ['체결력', '산업로봇', '토크 건', '비전 검사'],
};

function unique(matches) {
  return Array.from(new Set(matches)).sort();
}

function allMatches(text, pattern, group = 0) {
  pattern.lastIndex = 0;
  return Array.from(text.matchAll(pattern)).map(match => match[group]);
}

export function checkSlotResidual(text) {
  const matches = allMatches(text, SLOT_PATTERN, 1);
  return {
    label: 'slot',
    count: matches.length,
    unique: unique(matches),
    pass: matches.length === 0,
  };
}

export function checkPlaceholderResidual(text) {
  const cleaned = text.replace(PLACEHOLDER_WHITELIST, '');
  const matches = allMatches(cleaned, PLACEHOLDER_PATTERN, 1);
  return {
    label: 'placeholder',
    count: matches.length,
    unique: unique(matches),
    pass: matches.length === 0,
  };
}

export function checkSectionHeaders(text) {
  const missing = EXPECTED_SECTION_HEADERS.filter(section => {
    const pattern = new RegExp(`^## ${section}\\b`, 'm');
    return !pattern.test(text);
  });
  return {
    label: 'sectionHeaders',
    missing,
    pass: missing.length === 0,
  };
}

export function checkSectionBalance(text) {
  const sections = {};
  let current = null;
  let count = 0;
  for (const line of text.split('\n')) {
    const match = line.match(/^## (§\d)\b/);
    if (match) {
      if (current) sections[current] = count;
      current = match[1];
      count = 0;
    } else if (current) {
      count += 1;
    }
  }
  if (current) sections[current] = count;
  const counts = Object.values(sections);
  if (counts.length === 0 || Math.max(...counts) === 0) {
    return { label: 'balance', sections, balance_ratio: 0, pass: false };
  }
  const ratio = Math.min(...counts) / Math.max(...counts);
  return {
    label: 'balance',
    sections,
    balance_ratio: Math.round(ratio * 100) / 100,
    pass: ratio >= 0.10,
  };
}

export function checkDomainCrossPollution(text, domain) {
  if (!domain || !DOMAIN_VOCAB[domain]) {
    return { label: 'cross', my_domain: domain || null, leaks: {}, total_leaks: 0, pass: true };
  }
  const leaks = {};
  for (const [otherDomain, vocab] of Object.entries(DOMAIN_VOCAB)) {
    if (otherDomain === domain) continue;
    const hits = vocab.filter(word => text.includes(word));
    if (hits.length > 0) leaks[otherDomain] = hits;
  }
  const totalLeaks = Object.values(leaks).reduce((sum, hits) => sum + hits.length, 0);
  return {
    label: 'cross',
    my_domain: domain,
    leaks,
    total_leaks: totalLeaks,
    pass: totalLeaks < 4,
  };
}

export function checkMetaLeakage(text) {
  const hits = [];
  for (const pattern of META_LEAKAGE_PATTERNS) {
    hits.push(...allMatches(text, pattern));
  }
  return {
    label: 'meta',
    count: hits.length,
    samples: hits.slice(0, 5),
    pass: hits.length === 0,
  };
}

export function runAudit(markdown, domain) {
  const checks = {
    slot: checkSlotResidual(markdown),
    placeholder: checkPlaceholderResidual(markdown),
    sectionHeaders: checkSectionHeaders(markdown),
    balance: checkSectionBalance(markdown),
    cross: checkDomainCrossPollution(markdown, domain),
    meta: checkMetaLeakage(markdown),
  };
  const passed = Object.values(checks).every(check => check.pass);
  const failed = Object.entries(checks)
    .filter(([, check]) => !check.pass)
    .map(([key]) => key);
  return {
    passed,
    checks,
    summary: {
      pass_count: Object.values(checks).filter(check => check.pass).length,
      fail_count: failed.length,
      failed,
    },
  };
}
