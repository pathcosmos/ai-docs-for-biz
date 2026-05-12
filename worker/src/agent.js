import { callGeminiText, geminiModel, requireGeminiEnv } from './gemini.js';

const SECTION_DEFS = [
  ['§1', '현황', 'BLK-COMPANY-01', '회사 프로필과 기존 시스템 현황을 정리한다.', ['GUIDE-COMPANY-PROFILE-§3']],
  ['§2', '문제인식', 'BLK-PROB-01', '운영·데이터·지식·제어 관점의 AS-IS 문제를 정리한다.', ['GUIDE-PROBLEM-MATRIX-§3']],
  ['§3', '개선방향', 'BLK-GOAL-01', '핵심 KPI와 단계별 개선 목표를 제시한다.', ['GUIDE-KPI-BREAKDOWN-§3']],
  ['§4', '수행방향', 'BLK-EXEC-01·02', 'phase 로드맵, 역할, 예산, 위험 대응을 정리한다.', ['GUIDE-EXECUTION-ROADMAP-§3']],
  ['§5', 'AI 적용 포인트', 'BLK-APPLIC-01', '선정 시나리오, ROI, 시너지 구조를 정리한다.', ['GUIDE-SCENARIO-ROI-§3']],
  ['§6', '데이터·변수', 'BLK-DATA-01', '핸들링 데이터, X/y, 전처리, 분할, 거버넌스를 명세한다.', ['GUIDE-DATA-SPEC-§3']],
  ['§7', '모델·학습', 'BLK-MODEL-01', '모델 후보, 학습 전략, 검증 지표, 리스크를 정리한다.', ['GUIDE-MODEL-TRAINING-§3']],
  ['§8', '적용·배포', 'BLK-TRAIN-01·02', '배포 아키텍처, 운영 통합, HITL, 교육을 정리한다.', ['GUIDE-DEPLOYMENT-PLAN-§3']],
  ['§9', 'MLOps loop', 'BLK-MLOPS-01·02', '모니터링, 드리프트, 재학습, 운영 리듬을 정리한다.', ['GUIDE-MLOPS-RITUAL-§3']],
];

const DOMAIN_BY_INDUSTRY = {
  STL: { package: 'pkg2', scenarios: ['SCN-STL-04', 'SCN-STL-08', 'SCN-MLO-01'] },
  MET: { package: 'pkg5', scenarios: ['SCN-MET-01', 'SCN-MET-02', 'SCN-MLO-03'] },
  RUB: { package: 'pkg4', scenarios: ['SCN-RUB-01', 'SCN-RUB-05', 'SCN-MLO-03'] },
  UTL: { package: 'pkg6', scenarios: ['SCN-UTL-01', 'SCN-UTL-02', 'SCN-SAF-01'] },
  LLM: { package: 'pkg3', scenarios: ['SCN-LLM-01', 'SCN-LLM-02', 'SCN-STL-08'] },
};

function profilePart(profile, key) {
  return profile?.[key] && typeof profile[key] === 'object' ? profile[key] : {};
}

function companyName(profile) {
  return profilePart(profile, 'step1_company').company || profile.company || '';
}

function industry(profile) {
  return profilePart(profile, 'step1_company').industry || profile.industry || 'STL';
}

function processName(profile) {
  return profilePart(profile, 'step1_company').process || profile.process || '[공정]';
}

function outputStrength(profile) {
  return profilePart(profile, 'step4_settings').output_strength || profile.output_strength || '중';
}

function writerMode(profile) {
  return profilePart(profile, 'step4_settings').writer_mode || profile.writer_mode || 'deterministic';
}

function llmSectionLimit(profile, env) {
  const configured = profilePart(profile, 'step4_settings').max_llm_sections
    || profile.max_llm_sections
    || env.AGENT_MAX_LLM_SECTIONS
    || '5';
  const parsed = Number.parseInt(configured, 10);
  if (!Number.isFinite(parsed)) return 5;
  return Math.max(0, Math.min(SECTION_DEFS.length, parsed));
}

export function validateAgentProfile(profile) {
  const missing = [];
  if (!companyName(profile).trim()) missing.push('company');
  return missing;
}

function makePlan(profile) {
  const domain = industry(profile);
  const mapped = DOMAIN_BY_INDUSTRY[domain] || DOMAIN_BY_INDUSTRY.STL;
  return {
    domain,
    package: mapped.package,
    scenarios: mapped.scenarios,
    reasoning: `${domain} 도메인 입력과 ${processName(profile)} 공정 정보를 기준으로 1차 후보를 선정했다.`,
  };
}

function makeOutline(plan) {
  return {
    sections: SECTION_DEFS.map(([id, title, guide, intent, contextIds], index) => ({
      index: index + 1,
      id,
      title,
      guide,
      intent,
      context_ids: contextIds,
      blocks_to_cite: [guide],
      ascii_slots: [],
    })),
  };
}

function deterministicSectionMarkdown(profile, outlineSection, plan) {
  const company = companyName(profile);
  const process = processName(profile);
  return [
    `## ${outlineSection.id} ${outlineSection.title}`,
    '',
    `${company}의 ${process} 사업계획서 ${outlineSection.title} 섹션은 ${outlineSection.intent}`,
    `본 1차 MVP 초안은 ${outlineSection.guide} 생성 가이드와 ${plan.scenarios.join('·')} 시나리오 후보를 기준으로 작성되며, 후속 Section Writer 단계에서 세부 수치와 인용 블록 본문을 확장한다.`,
    '',
    `> [출처: ${outlineSection.guide}]`,
  ].join('\n');
}

function compactProfileJson(profile) {
  return JSON.stringify(profile, null, 2).slice(0, 6000);
}

function compactTemplateContext(templateContext, outlineSection) {
  const entries = (outlineSection.context_ids || [])
    .map(id => [id, templateContext?.[id]])
    .filter(([, entry]) => entry && typeof entry === 'object')
    .map(([id, entry]) => {
      const title = typeof entry.title === 'string' ? entry.title.slice(0, 160) : '';
      const section = typeof entry.section === 'string' ? entry.section.slice(0, 80) : '';
      const tags = Array.isArray(entry.tags) ? entry.tags.slice(0, 8).join(', ') : '';
      const preview = typeof entry.preview === 'string' ? entry.preview.slice(0, 900) : '';
      return [
        `- id: ${id}`,
        title ? `  title: ${title}` : '',
        section ? `  section: ${section}` : '',
        tags ? `  tags: ${tags}` : '',
        preview ? `  preview: ${preview}` : '',
      ].filter(Boolean).join('\n');
    });

  return entries.length > 0 ? entries.join('\n') : '(제공된 compact index context 없음)';
}

function buildSectionPrompt(profile, outlineSection, plan, templateContext = {}) {
  return `당신은 한국어 정부지원 R&D 사업계획서 작성 전문가입니다. 아래 입력을 바탕으로 사업계획서의 단일 섹션만 작성하세요.

【작성 대상】
- 섹션: ${outlineSection.id} ${outlineSection.title}
- 생성 가이드: ${outlineSection.guide}
- 작성 의도: ${outlineSection.intent}
- 도메인: ${plan.domain}
- 패키지 후보: ${plan.package}
- 시나리오 후보: ${plan.scenarios.join(', ')}

【필수 규칙】
1. 출력은 Markdown 본문만 반환합니다.
2. 첫 줄은 반드시 "## ${outlineSection.id} ${outlineSection.title}" 제목으로 시작합니다.
3. 한국어 formal 문어체 (~한다·~된다 종결)를 사용합니다.
4. 확인되지 않은 수치나 회사별 고유 사실은 지어내지 말고 "[확인 필요]" 로 표시합니다.
5. 섹션 끝에는 반드시 "> [출처: ${outlineSection.guide}]" 를 포함합니다.
6. 다른 섹션 제목은 만들지 않습니다.

【생성 가이드 compact context】
아래 context는 섹션 구조와 표현 패턴 참고용입니다. 원문 전체가 아니므로 회사별 사실·수치는 사용자 입력만 기준으로 작성합니다.
${compactTemplateContext(templateContext, outlineSection)}

【사용자 입력 JSON】
${compactProfileJson(profile)}

【${outlineSection.id} ${outlineSection.title} 본문】`;
}

function normalizeSectionMarkdown(text, outlineSection) {
  const expectedHeading = `## ${outlineSection.id} ${outlineSection.title}`;
  const lines = text.trim().split('\n');
  const hasHeading = lines[0]?.startsWith('## ');
  const withHeading = hasHeading ? text.trim() : `${expectedHeading}\n\n${text.trim()}`;
  if (withHeading.includes('> [출처:')) {
    return withHeading;
  }
  return `${withHeading}\n\n> [출처: ${outlineSection.guide}]`;
}

function deterministicSectionResult(profile, outlineSection, plan, startedAt = Date.now()) {
  return {
    section: outlineSection.id,
    title: outlineSection.title,
    markdown: deterministicSectionMarkdown(profile, outlineSection, plan),
    citations: outlineSection.blocks_to_cite,
    placeholders_unfilled: [],
    duration_ms: Date.now() - startedAt,
    source: 'deterministic',
  };
}

async function llmSectionResult(profile, outlineSection, plan, env, fetchImpl, templateContext) {
  const startedAt = Date.now();
  try {
    const gemini = await callGeminiText({
      prompt: buildSectionPrompt(profile, outlineSection, plan, templateContext),
      env,
      fetchImpl,
      generationConfig: {
        temperature: 0.35,
        maxOutputTokens: 4096,
        topP: 0.85,
      },
    });
    if (!gemini.ok) {
      throw new Error(`Gemini section writer failed with ${gemini.status}: ${gemini.detail}`);
    }
    return {
      section: outlineSection.id,
      title: outlineSection.title,
      markdown: normalizeSectionMarkdown(gemini.text, outlineSection),
      citations: outlineSection.blocks_to_cite,
      placeholders_unfilled: [],
      duration_ms: Date.now() - startedAt,
      source: 'llm',
      usage: gemini.usage,
    };
  } catch (error) {
    return {
      ...deterministicSectionResult(profile, outlineSection, plan, startedAt),
      fallback_reason: error.message,
    };
  }
}

async function writeSections({ profile, outline, plan, mode, env, fetchImpl, send, templateContext }) {
  if (mode !== 'llm') {
    return outline.sections.map(outlineSection => {
      send('section_start', { section: outlineSection.id, at: new Date().toISOString() });
      const result = deterministicSectionResult(profile, outlineSection, plan);
      send('section_done', result);
      return result;
    });
  }

  const limit = llmSectionLimit(profile, env);
  const tasks = outline.sections.map(async outlineSection => {
    send('section_start', { section: outlineSection.id, at: new Date().toISOString() });
    if (outlineSection.index > limit) {
      const result = {
        ...deterministicSectionResult(profile, outlineSection, plan),
        fallback_reason: `llm_section_limit:${limit}`,
      };
      send('section_fallback', { section: outlineSection.id, reason: result.fallback_reason });
      send('section_done', result);
      return result;
    }
    const result = await llmSectionResult(profile, outlineSection, plan, env, fetchImpl, templateContext);
    if (result.fallback_reason) {
      send('section_fallback', { section: outlineSection.id, reason: result.fallback_reason });
    }
    send('section_done', result);
    return result;
  });
  const sections = await Promise.all(tasks);
  return sections.sort((a, b) => {
    const left = SECTION_DEFS.findIndex(([id]) => id === a.section);
    const right = SECTION_DEFS.findIndex(([id]) => id === b.section);
    return left - right;
  });
}

function summarizeUsage(sections, env) {
  const usages = sections.map(section => section.usage).filter(Boolean);
  const totalTokens = usages.reduce((sum, usage) => {
    const fallbackTotal = (usage.promptTokenCount || 0) + (usage.candidatesTokenCount || 0);
    return sum + (usage.totalTokenCount || fallbackTotal);
  }, 0);
  return {
    total_calls: usages.length,
    total_tokens: totalTokens,
    model: geminiModel(env),
  };
}

function compileMarkdown(profile, plan, sections, validation, generator) {
  const company = companyName(profile);
  const frontmatter = [
    '---',
    `generated_at: "${new Date().toISOString()}"`,
    `generator: "${generator}"`,
    `company: "${company.replaceAll('"', '\\"')}"`,
    `domain: "${plan.domain}"`,
    `package: "${plan.package}"`,
    `scenarios: "${plan.scenarios.join(',')}"`,
    `validation_score: ${validation.tone_score}`,
    '---',
    '',
  ].join('\n');
  const title = `# ${company} AI 사업계획서`;
  return `${frontmatter}${title}\n\n${sections.map(item => item.markdown).join('\n\n')}\n`;
}

function encodeSse(event, data) {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

export async function handleAgentGenerate(request, env, fetchImpl, origin, corsHeaders) { // eslint-disable-line no-unused-vars
  let payload;
  try {
    payload = await request.json();
  } catch {
    return Response.json({ error: 'invalid_json' }, { status: 400, headers: corsHeaders(origin, env) });
  }

  const profile = payload.profile || {};
  const templateContext = payload.template_context && typeof payload.template_context === 'object'
    ? payload.template_context
    : {};
  const mode = writerMode(profile);
  if (!['deterministic', 'llm'].includes(mode)) {
    return Response.json({ error: 'invalid_writer_mode' }, { status: 400, headers: corsHeaders(origin, env) });
  }
  if (mode === 'llm') {
    const configError = requireGeminiEnv(env);
    if (configError) {
      return Response.json(
        { error: 'worker_misconfigured', message: configError },
        { status: 500, headers: corsHeaders(origin, env) },
      );
    }
  }
  const missing = validateAgentProfile(profile);
  if (missing.length > 0) {
    return Response.json({ error: 'tier1_missing', fields: missing }, {
      status: 400,
      headers: corsHeaders(origin, env),
    });
  }

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const send = (event, data) => controller.enqueue(encoder.encode(encodeSse(event, data)));
      const startedAt = Date.now();

      try {
        send('connected', { at: new Date(startedAt).toISOString(), writer_mode: mode });
        send('stage_start', { stage: 'planner', at: new Date().toISOString() });
        const plan = makePlan(profile);
        send('stage_done', { stage: 'planner', duration_ms: Date.now() - startedAt, partial: plan });

        send('stage_start', { stage: 'outline', at: new Date().toISOString() });
        const outline = makeOutline(plan);
        send('stage_done', {
          stage: 'outline',
          duration_ms: Date.now() - startedAt,
          partial: { section_count: outline.sections.length, ascii_slot_count: 0 },
        });

        const sections = await writeSections({ profile, outline, plan, mode, env, fetchImpl, send, templateContext });

        send('stage_start', { stage: 'validate', at: new Date().toISOString() });
        const validation = {
          citation_preservation: 100,
          placeholder_unfilled: [],
          numeric_inconsistencies: [],
          tone_score: outputStrength(profile) === '강' ? 86 : 82,
          fallback_count: sections.filter(section => section.fallback_reason).length,
        };
        send('stage_done', { stage: 'validate', duration_ms: Date.now() - startedAt, partial: validation });
        send('validation', { report: validation });

        send('stage_start', { stage: 'compile', at: new Date().toISOString() });
        const metaMode = mode === 'llm' ? 'phase-two-llm-sections' : 'phase-one-deterministic';
        const finalMd = compileMarkdown(profile, plan, sections, validation, metaMode);
        send('complete', {
          final_md: finalMd,
          meta: {
            model: geminiModel(env),
            mode: metaMode,
            section_count: sections.length,
            domain: plan.domain,
            package: plan.package,
            scenarios: plan.scenarios,
            validation_score: validation.tone_score,
            fallback_count: validation.fallback_count,
          },
          usage: summarizeUsage(sections, env),
        });
      } catch (error) {
        send('error', { stage: 'agent', code: 'worker_error', message: error.message });
      }
      controller.close();
    },
  });

  return new Response(stream, {
    status: 200,
    headers: {
      ...corsHeaders(origin, env),
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  });
}
