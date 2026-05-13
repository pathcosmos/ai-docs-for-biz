import { runAudit } from './audit.js';
import { buildSlots, composeFromLibrary } from './library.js';

const SECTION_IDS = ['§1', '§2', '§3', '§4', '§5', '§6', '§7', '§8', '§9'];
const VALID_DOMAINS = new Set(['STL', 'MET', 'RUB', 'UTL', 'LLM', 'CAS', 'HEA', 'PLT', 'SHP', 'ASM']);
const CATEGORY_PRIORITY = {
  track: 0,
  guide: 1,
  scenario: 2,
  module: 3,
  package: 4,
};

function jsonResponse(payload, status, origin, env, corsHeaders) {
  return Response.json(payload, {
    status,
    headers: corsHeaders(origin, env),
  });
}

export function normalizeSectionId(value) {
  if (!value) return null;
  const match = String(value).match(/§\s*(\d+)/);
  if (!match) return null;
  const number = Number.parseInt(match[1], 10);
  if (number === 0) return '§1';
  if (number === 10) return '§4';
  if (number >= 1 && number <= 9) return `§${number}`;
  return null;
}

function compactPlan(payload) {
  return {
    domain: payload.domain,
    scenarios: Array.isArray(payload.scenarios) ? payload.scenarios : [],
    package: payload.package || '',
  };
}

function normalizedProfile(payload) {
  const profile = payload.slots && typeof payload.slots === 'object' ? { ...payload.slots } : {};
  profile.step1_company = {
    ...(profile.step1_company || {}),
    industry: payload.domain || profile.step1_company?.industry,
  };
  return profile;
}

function blockList(payload) {
  if (Array.isArray(payload.blocks)) return payload.blocks.map(String);
  const context = payload.block_context && typeof payload.block_context === 'object' ? payload.block_context : {};
  return Object.keys(context);
}

function normalizeExplicitAssignment(sectionAssignment, selectedBlocks) {
  const selected = new Set(selectedBlocks);
  const assignment = Object.fromEntries(SECTION_IDS.map(section => [section, []]));
  if (!sectionAssignment || typeof sectionAssignment !== 'object') return null;

  for (const [rawSection, rawIds] of Object.entries(sectionAssignment)) {
    const section = normalizeSectionId(rawSection);
    if (!section || !Array.isArray(rawIds)) continue;
    for (const id of rawIds.map(String)) {
      if (selected.has(id) && !assignment[section].includes(id)) {
        assignment[section].push(id);
      }
    }
  }
  return assignment;
}

export function assignBlocksToSections(selectedBlocks, blockContext, sectionAssignment) {
  const explicit = normalizeExplicitAssignment(sectionAssignment, selectedBlocks);
  if (explicit) return explicit;

  const assignment = Object.fromEntries(SECTION_IDS.map(section => [section, []]));
  for (const id of selectedBlocks) {
    const section = normalizeSectionId(blockContext[id]?.section);
    if (section) assignment[section].push(id);
  }
  return assignment;
}

function stripFrontmatter(text) {
  return text.replace(/^---\n[\s\S]*?\n---\n?/, '');
}

function stripInternalIds(line) {
  return line
    .replace(/\b(?:BLK|TEST)-[A-Z0-9_.§/·-]+\b\s*[—\-–:]?\s*/g, '')
    .replace(/\s{2,}/g, ' ')
    .trimEnd();
}

export function fillText(text, slots) {
  const duration = String(slots.duration_months || '').replace(/\s*개월\s*$/, '');
  return String(text || '')
    .replace(/\{\{(\w+)\}\}/g, (_, key) => (slots[key] !== undefined ? String(slots[key]) : '[확인 필요]'))
    .replace(/\[고객사\]/g, slots.company || '[확인 필요]')
    .replace(/\[공정\]/g, slots.process || '[확인 필요]')
    .replace(/\[기간\]/g, duration ? `${duration} 개월` : '[확인 필요]')
    .replace(/\[수치\]/g, '[확인 필요]')
    .replace(/\[%\]/g, '[확인 필요]');
}

function demoteHeading(line) {
  const match = line.match(/^(#{1,6})\s+(.+)$/);
  if (!match) return line;
  const text = stripInternalIds(match[2]).replace(/^\s*[—\-–:]\s*/, '').trim();
  if (!text) return '';
  return `### ${text}`;
}

export function cleanBlockBody(body, slots) {
  return stripFrontmatter(fillText(body, slots))
    .split('\n')
    .filter(line => !line.trim().startsWith('> [출처:'))
    .filter(line => !/^\s*(generator|generated_at|validation_score|model|usage)\s*:/i.test(line))
    .map(line => demoteHeading(line))
    .map(line => stripInternalIds(line))
    .filter(line => !line.includes('본 1차 MVP 초안'))
    .filter(line => !line.includes('후속 Section Writer'))
    .filter(line => !line.includes('generator'))
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function sectionBodyFromLibrary(sectionId, slots) {
  const composed = composeFromLibrary(sectionId, slots);
  if (!composed) return '';
  return composed
    .split('\n')
    .filter((line, index) => index !== 0 || !line.startsWith('## '))
    .join('\n')
    .trim();
}

function sortedSectionBlocks(ids, blockContext) {
  return [...ids].sort((left, right) => {
    const leftCategory = blockContext[left]?.category || '';
    const rightCategory = blockContext[right]?.category || '';
    const leftPriority = CATEGORY_PRIORITY[leftCategory] ?? 99;
    const rightPriority = CATEGORY_PRIORITY[rightCategory] ?? 99;
    if (leftPriority !== rightPriority) return leftPriority - rightPriority;
    return ids.indexOf(left) - ids.indexOf(right);
  });
}

function buildSections(assignment, blockContext, slots) {
  const sections = {};
  for (const sectionId of SECTION_IDS) {
    const bodies = sortedSectionBlocks(assignment[sectionId] || [], blockContext)
      .map(id => cleanBlockBody(blockContext[id]?.body || '', slots))
      .filter(Boolean);
    sections[sectionId] = bodies.length > 0
      ? bodies.join('\n\n')
      : sectionBodyFromLibrary(sectionId, slots);
  }
  return sections;
}

function compileFinalMarkdown(company, sections) {
  const lines = [`# ${company} AI 사업계획서`, ''];
  for (const sectionId of SECTION_IDS) {
    lines.push(`## ${sectionId}`, '', sections[sectionId] || '', '');
  }
  return `${lines.join('\n').replace(/\n{3,}/g, '\n\n').trim()}\n`;
}

function auditMarkdown(audit, meta) {
  const rows = Object.entries(audit.checks || {})
    .map(([key, check]) => `| ${key} | ${check.pass ? 'PASS' : 'FAIL'} |`)
    .join('\n');
  return [
    '# 조립 검토 리포트',
    '',
    `- generator: ${meta.generator}`,
    `- domain: ${meta.domain}`,
    `- section_count: ${meta.section_count}`,
    '',
    '| 축 | 결과 |',
    '|---|---|',
    rows,
    '',
  ].join('\n');
}

function usedBlocks(assignment, blockContext) {
  const rows = [];
  for (const sectionId of SECTION_IDS) {
    for (const id of assignment[sectionId] || []) {
      rows.push({
        id,
        section: sectionId,
        category: blockContext[id]?.category || '',
      });
    }
  }
  return rows;
}

function compactAssignment(assignment) {
  return Object.fromEntries(
    Object.entries(assignment).filter(([, ids]) => ids.length > 0),
  );
}

function compactSlots(slots) {
  return {
    company: slots.company,
    process: slots.process,
    industry: slots.industry,
    duration_months: slots.duration_months,
    total_budget_eok: slots.total_budget_eok,
    govt_ratio_pct: slots.govt_ratio_pct,
  };
}

function validatePayload(payload) {
  const mode = payload.mode || 'deterministic';
  if (mode === 'llm') {
    return {
      status: 501,
      body: { error: 'not_implemented', message: 'mode llm is planned for a later phase' },
    };
  }
  if (mode !== 'deterministic') {
    return { status: 400, body: { error: 'invalid_mode' } };
  }
  if (!VALID_DOMAINS.has(payload.domain)) {
    return { status: 400, body: { error: 'invalid_domain' } };
  }
  if (!Array.isArray(payload.scenarios) || payload.scenarios.length === 0) {
    return { status: 400, body: { error: 'scenarios_required' } };
  }
  return null;
}

export async function handleAssemble(request, env, origin, corsHeaders) {
  let payload;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse({ error: 'invalid_json' }, 400, origin, env, corsHeaders);
  }

  const validation = validatePayload(payload);
  if (validation) {
    return jsonResponse(validation.body, validation.status, origin, env, corsHeaders);
  }

  const profile = normalizedProfile(payload);
  const plan = compactPlan(payload);
  const slots = buildSlots(profile, plan);
  const selectedBlocks = blockList(payload);
  const blockContext = payload.block_context && typeof payload.block_context === 'object'
    ? payload.block_context
    : {};
  const assignment = assignBlocksToSections(selectedBlocks, blockContext, payload.section_assignment);
  const sections = buildSections(assignment, blockContext, slots);
  const finalMd = compileFinalMarkdown(slots.company, sections);
  const audit = runAudit(finalMd, payload.domain);
  const meta = {
    generator: 'assemble-deterministic',
    domain: payload.domain,
    section_count: SECTION_IDS.length,
  };

  return jsonResponse({
    final_md: finalMd,
    audit,
    audit_md: auditMarkdown(audit, meta),
    blocks_used: usedBlocks(assignment, blockContext),
    slots_filled: compactSlots(slots),
    section_assignment: compactAssignment(assignment),
    meta,
  }, 200, origin, env, corsHeaders);
}
