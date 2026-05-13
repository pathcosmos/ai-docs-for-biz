import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { handleRequest } from '../src/index.js';

const env = {
  ALLOWED_ORIGINS: 'https://pathcosmos.github.io,http://127.0.0.1:8000,http://localhost:8000',
};

const VALID_SLOTS = {
  step1_company: {
    company: '동국산업(주)',
    industry: 'STL',
    process: '냉간 압연',
    scale: '중견',
  },
  step2_business: {
    duration_months: '12',
    total_budget: '600 백만원',
    gov_pct: '50%',
  },
};

const DOMAIN_SCENARIOS = {
  STL: ['SCN-STL-04', 'SCN-STL-05', 'SCN-MLO-01'],
  MET: ['SCN-MET-01', 'SCN-MET-05', 'SCN-MLO-03'],
  RUB: ['SCN-RUB-01', 'SCN-RUB-02', 'SCN-MLO-03'],
  UTL: ['SCN-UTL-01', 'SCN-UTL-02', 'SCN-SAF-01'],
  LLM: ['SCN-LLM-01', 'SCN-LLM-02', 'SCN-MLO-02'],
  CAS: ['SCN-CAS-01', 'SCN-CAS-02', 'SCN-MLO-01'],
  HEA: ['SCN-HEA-01', 'SCN-HEA-02', 'SCN-MLO-02'],
  PLT: ['SCN-PLT-01', 'SCN-PLT-02', 'SCN-MLO-03'],
  SHP: ['SCN-SHP-01', 'SCN-SHP-02', 'SCN-MLO-01'],
  ASM: ['SCN-ASM-01', 'SCN-ASM-02', 'SCN-MLO-03'],
};

function assembleRequest(body, init = {}) {
  const requestInit = {
    method: init.method || 'POST',
    headers: {
      'content-type': 'application/json',
      origin: 'https://pathcosmos.github.io',
      ...(init.headers || {}),
    },
  };
  if ('rawBody' in init) {
    requestInit.body = init.rawBody;
  } else if (requestInit.method !== 'GET') {
    requestInit.body = JSON.stringify(body);
  }
  return new Request('https://worker.example.com/api/assemble', requestInit);
}

async function postAssemble(body, init) {
  return handleRequest(assembleRequest(body, init), env, async () => {
    throw new Error('assemble must not call fetch');
  });
}

describe('POST /api/assemble', () => {
  it('rejects unsupported methods', async () => {
    const response = await postAssemble({}, { method: 'GET' });

    assert.equal(response.status, 405);
    assert.deepEqual(await response.json(), { error: 'method_not_allowed' });
  });

  it('rejects invalid JSON', async () => {
    const response = await postAssemble(null, { rawBody: '{not json' });

    assert.equal(response.status, 400);
    assert.deepEqual(await response.json(), { error: 'invalid_json' });
  });

  it('returns not_implemented for llm mode', async () => {
    const response = await postAssemble({
      domain: 'STL',
      scenarios: ['SCN-STL-04'],
      slots: VALID_SLOTS,
      mode: 'llm',
    });

    assert.equal(response.status, 501);
    assert.deepEqual(await response.json(), {
      error: 'not_implemented',
      message: 'mode llm is planned for a later phase',
    });
  });

  it('rejects invalid mode, domain, and empty scenarios', async () => {
    const invalidMode = await postAssemble({
      domain: 'STL',
      scenarios: ['SCN-STL-04'],
      slots: VALID_SLOTS,
      mode: 'draft',
    });
    assert.equal(invalidMode.status, 400);
    assert.deepEqual(await invalidMode.json(), { error: 'invalid_mode' });

    const invalidDomain = await postAssemble({
      domain: 'BAD',
      scenarios: ['SCN-STL-04'],
      slots: VALID_SLOTS,
    });
    assert.equal(invalidDomain.status, 400);
    assert.deepEqual(await invalidDomain.json(), { error: 'invalid_domain' });

    const emptyScenarios = await postAssemble({
      domain: 'STL',
      scenarios: [],
      slots: VALID_SLOTS,
    });
    assert.equal(emptyScenarios.status, 400);
    assert.deepEqual(await emptyScenarios.json(), { error: 'scenarios_required' });
  });

  it('auto maps block sections, fills placeholders, and removes source markers', async () => {
    const response = await postAssemble({
      domain: 'STL',
      scenarios: ['SCN-STL-04', 'SCN-MLO-01'],
      blocks: ['BLK-CUSTOM-1'],
      slots: VALID_SLOTS,
      block_context: {
        'BLK-CUSTOM-1': {
          title: 'BLK-CUSTOM-1 — 회사 프로필 본문 템플릿',
          category: 'guide',
          section: '§3.1 개선방향',
          body: [
            '---',
            'generator: test',
            '---',
            '## BLK-CUSTOM-1 — [고객사] [공정]',
            '',
            '> [출처: 테스트 §3]',
            '',
            '{{company}} 는 [공정] 기준으로 [기간] 동안 패스 스케줄을 표준화한다.',
            '정량 목표는 [수치] 및 [%] 개선으로 두되 검증 전까지 보수적으로 표시한다.',
          ].join('\n'),
        },
      },
      mode: 'deterministic',
    });

    assert.equal(response.status, 200);
    const data = await response.json();
    assert.equal(data.section_assignment['§3'][0], 'BLK-CUSTOM-1');
    assert.equal(data.audit.passed, true);
    assert.equal(data.meta.generator, 'assemble-deterministic');
    assert.equal(data.meta.domain, 'STL');
    assert.equal(data.meta.section_count, 9);
    assert.match(data.final_md, /^# 동국산업\(주\) AI 사업계획서/);
    assert.equal((data.final_md.match(/^## §\d$/gm) || []).length, 9);
    assert.match(data.final_md, /동국산업\(주\) 는 냉간 압연 기준으로 12 개월 동안/);
    assert.doesNotMatch(data.final_md, /\[고객사\]|\[공정\]|\[기간\]|\[수치\]|\[%\]/);
    assert.doesNotMatch(data.final_md, /\[출처:/);
    assert.doesNotMatch(data.final_md, /BLK-/);
    assert.doesNotMatch(data.final_md, /generator/);
    assert.deepEqual(data.blocks_used, [
      { id: 'BLK-CUSTOM-1', section: '§3', category: 'guide' },
    ]);
    assert.deepEqual(data.slots_filled.company, '동국산업(주)');
    assert.deepEqual(data.slots_filled.process, '냉간 압연');
  });

  it('honors explicit section_assignment over block context sections', async () => {
    const response = await postAssemble({
      domain: 'STL',
      scenarios: ['SCN-STL-04'],
      blocks: ['GUIDE-COMPANY-PROFILE-§3'],
      section_assignment: {
        '§1': ['GUIDE-COMPANY-PROFILE-§3'],
      },
      slots: VALID_SLOTS,
      block_context: {
        'GUIDE-COMPANY-PROFILE-§3': {
          title: '회사 프로필 본문 템플릿',
          category: 'guide',
          section: '§3.1',
          body: '### 회사 프로필\n\n[고객사] 의 [공정] 현황을 정리한다.',
        },
      },
    });

    assert.equal(response.status, 200);
    const data = await response.json();
    assert.deepEqual(data.section_assignment['§1'], ['GUIDE-COMPANY-PROFILE-§3']);
    assert.equal(data.blocks_used[0].section, '§1');
    assert.match(data.final_md, /## §1\n\n### 회사 프로필\n\n동국산업\(주\) 의 냉간 압연 현황/);
  });

  it('generates audit-passing fallback plans for all ten domains', async () => {
    for (const [domain, scenarios] of Object.entries(DOMAIN_SCENARIOS)) {
      const response = await postAssemble({
        domain,
        scenarios,
        blocks: [],
        slots: {
          ...VALID_SLOTS,
          step1_company: {
            ...VALID_SLOTS.step1_company,
            industry: domain,
          },
        },
      });

      assert.equal(response.status, 200, domain);
      const data = await response.json();
      assert.equal(data.audit.passed, true, domain);
      assert.equal(data.meta.domain, domain);
      assert.equal((data.final_md.match(/^## §\d$/gm) || []).length, 9, domain);
    }
  });
});
