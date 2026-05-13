import assert from 'node:assert/strict';
import { beforeEach, describe, it } from 'node:test';

import '../docs/javascripts/assemble-ui.js';

function storageStub(initial = {}) {
  const store = new Map(Object.entries(initial));
  return {
    getItem(key) { return store.get(key) || null; },
    setItem(key, value) { store.set(key, String(value)); },
    removeItem(key) { store.delete(key); },
  };
}

describe('AiDocsAssemble helpers', () => {
  beforeEach(() => {
    globalThis.localStorage = storageStub();
  });

  it('normalizes sections into §1 through §9', () => {
    const { normalizeSection } = globalThis.AiDocsAssemble;

    assert.equal(normalizeSection('§1'), '§1');
    assert.equal(normalizeSection('§1 현황'), '§1');
    assert.equal(normalizeSection('§3.1 개선방향'), '§3');
    assert.equal(normalizeSection('§0 과제 요약'), '§1');
    assert.equal(normalizeSection('§10 재무·예산'), '§4');
    assert.equal(normalizeSection('본문 조립'), null);
    assert.equal(normalizeSection('§12'), null);
  });

  it('builds automatic section assignments from selected blocks and compact index', () => {
    const { assignBlocksToSections } = globalThis.AiDocsAssemble;
    const assignment = assignBlocksToSections(
      ['A', 'B', 'C'],
      {
        A: { section: '§3.1', category: 'scenario' },
        B: { section: '§10 재무', category: 'guide' },
        C: { section: '전체', category: 'guide' },
      },
    );

    assert.deepEqual(assignment, {
      '§3': ['A'],
      '§4': ['B'],
    });
  });

  it('builds canonical assemble payload with selected full block bodies only', () => {
    const { buildPayload } = globalThis.AiDocsAssemble;
    const state = {
      domain: 'STL',
      scenarios: ['SCN-STL-04', 'SCN-MLO-01'],
      selectedBlocks: ['A', 'B'],
      sectionAssignment: { '§1': ['A'], '§2': ['B'] },
      slots: {
        step1_company: { company: '동국산업(주)', industry: 'STL', process: '냉간 압연', scale: '중견' },
        step2_business: { duration_months: '12', total_budget: '600 백만원', gov_pct: '50%' },
      },
    };
    const fullTemplates = {
      A: { title: 'A title', category: 'guide', section: '§1', body: 'A body' },
      B: { title: 'B title', category: 'scenario', section: '§2', body: 'B body' },
      C: { title: 'C title', category: 'track', section: '§3', body: 'C body' },
    };

    assert.deepEqual(buildPayload(state, fullTemplates), {
      domain: 'STL',
      scenarios: ['SCN-STL-04', 'SCN-MLO-01'],
      blocks: ['A', 'B'],
      section_assignment: { '§1': ['A'], '§2': ['B'] },
      slots: state.slots,
      block_context: {
        A: { title: 'A title', category: 'guide', section: '§1', body: 'A body' },
        B: { title: 'B title', category: 'scenario', section: '§2', body: 'B body' },
      },
      mode: 'deterministic',
    });
  });

  it('uses visible placeholder examples as default company and business slots', () => {
    const { collectSlotsFromFields } = globalThis.AiDocsAssemble;
    const fields = [
      { name: 'step1_company.company', value: ' ', placeholder: '동국산업(주)' },
      { name: 'step1_company.industry', value: 'STL', placeholder: '' },
      { name: 'step1_company.process', value: '', placeholder: '냉간 압연' },
      { name: 'step1_company.scale', value: '중견', placeholder: '' },
      { name: 'step2_business.duration_months', value: '', placeholder: '12' },
      { name: 'step2_business.total_budget', value: '650 백만원', placeholder: '600 백만원' },
      { name: 'step2_business.gov_pct', value: '', placeholder: '50%' },
      { name: 'quant.kpi_quality_pct', value: '', placeholder: 'kpi_quality_pct' },
    ];

    assert.deepEqual(collectSlotsFromFields(fields, 'STL'), {
      domain: 'STL',
      slots: {
        step1_company: {
          company: '동국산업(주)',
          industry: 'STL',
          process: '냉간 압연',
          scale: '중견',
        },
        step2_business: {
          duration_months: '12',
          total_budget: '650 백만원',
          gov_pct: '50%',
        },
        quant: {},
      },
    });
  });

  it('keeps internal scenario and block ids out of display labels', () => {
    const { stripInternalIds, scenarioTitle, blockTitle } = globalThis.AiDocsAssemble;

    assert.equal(stripInternalIds('SCN-MLO-01 모델 운영 감시'), '모델 운영 감시');
    assert.equal(scenarioTitle({ id: 'SCN-MLO-01', title: 'SCN-MLO-01 모델 운영 감시·드리프트 탐지' }), '모델 운영 감시·드리프트 탐지');
    assert.equal(blockTitle('GUIDE-COMPANY-PROFILE-§3', {
      'GUIDE-COMPANY-PROFILE-§3': { title: 'GUIDE-COMPANY-PROFILE-§3 회사 프로필 본문', category: 'guide' },
    }), '회사 프로필 본문');
    assert.equal(blockTitle('GUIDE-MISSING', { 'GUIDE-MISSING': { category: 'guide' } }), '가이드 블록');
  });

  it('restores persisted state defensively from localStorage', () => {
    const { restoreState, defaultState, STORAGE_KEY } = globalThis.AiDocsAssemble;
    const saved = {
      domain: 'RUB',
      scenarios: ['SCN-RUB-01'],
      selectedBlocks: ['A'],
      sectionAssignment: { '§3': ['A'] },
      slots: { step1_company: { company: '태광고무' } },
    };
    globalThis.localStorage = storageStub({ [STORAGE_KEY]: JSON.stringify(saved) });

    assert.deepEqual(restoreState(globalThis.localStorage), {
      ...defaultState(),
      ...saved,
    });

    globalThis.localStorage = storageStub({ [STORAGE_KEY]: '{bad json' });
    assert.deepEqual(restoreState(globalThis.localStorage), defaultState());
  });
});
