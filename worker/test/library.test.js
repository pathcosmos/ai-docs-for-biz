import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  buildSlots,
  composeFromLibrary,
  libraryHasSection,
  librarySectionTitle,
} from '../src/library.js';

const DOMAINS = ['STL', 'MET', 'RUB', 'UTL', 'LLM', 'CAS', 'HEA', 'PLT', 'SHP', 'ASM'];
const SCALES = ['중소', '중견', '대기업'];
const SECTIONS = ['§1', '§2', '§3', '§4', '§5', '§6', '§7', '§8', '§9'];

const SCALE_BUDGET = {
  '중소': '3',
  '중견': '7',
  '대기업': '22',
};
const SCALE_DURATION = {
  '중소': '9',
  '중견': '12',
  '대기업': '24',
};
const SCALE_VETERAN = {
  '중소': '2~3',
  '중견': '3~5',
  '대기업': '10~15',
};

describe('library buildSlots — 10 도메인 × 3 규모 = 30 케이스', () => {
  for (const industry of DOMAINS) {
    for (const scale of SCALES) {
      it(`${industry} × ${scale} 가 13 도메인 어휘 + 10 규모 정량 슬롯을 채운다`, () => {
        const profile = {
          step1_company: {
            company: `[고객사 — 가상 ${scale} ${industry} 사]`,
            industry,
            scale,
          },
        };
        const plan = { domain: industry, scenarios: [`SCN-${industry}-01`] };
        const slots = buildSlots(profile, plan);

        // 식별 슬롯
        assert.equal(slots.industry, industry);
        assert.equal(slots.company, `[고객사 — 가상 ${scale} ${industry} 사]`);
        assert.ok(slots.process, 'process 슬롯이 빈 값이면 안 됨');

        // 도메인 어휘 슬롯 12 종 (process_default + 11 sample/examples)
        for (const key of [
          'domain_label', 'facility', 'product', 'quality_target', 'kpi_label',
          'sensor_examples', 'image_examples', 'cert_examples', 'risk_examples',
          'model_examples', 'scenario_focus', 'veteran_areas',
        ]) {
          assert.ok(slots[key], `${industry} 의 ${key} 가 비어 있다`);
        }

        // 규모 fallback 정량 슬롯
        assert.equal(slots.total_budget_eok, SCALE_BUDGET[scale],
          `${scale} 의 total_budget_eok 가 SCALE_PROFILE 과 다르다`);
        assert.equal(slots.duration_months, SCALE_DURATION[scale],
          `${scale} 의 duration_months 가 SCALE_PROFILE 과 다르다`);
        assert.equal(slots.veteran_count, SCALE_VETERAN[scale],
          `${scale} 의 veteran_count 가 SCALE_PROFILE 과 다르다`);
      });
    }
  }
});

describe('library buildSlots — scale fallback 동작', () => {
  it('scale 미지정 시 DEFAULTS 가 그대로 적용', () => {
    const slots = buildSlots({ step1_company: { company: 'X', industry: 'STL' } }, {});
    assert.equal(slots.total_budget_eok, '6'); // DEFAULTS 값 (중견 7 과 다름)
    assert.equal(slots.duration_months, '9');  // DEFAULTS 값
  });

  it('영문 alias (small/mid/large) 도 한글 키로 정규화된다', () => {
    const small = buildSlots({ step1_company: { company: 'X', industry: 'STL', scale: 'small' } }, {});
    assert.equal(small.total_budget_eok, '3');
    const mid = buildSlots({ step1_company: { company: 'X', industry: 'STL', scale: 'mid' } }, {});
    assert.equal(mid.total_budget_eok, '7');
    const large = buildSlots({ step1_company: { company: 'X', industry: 'STL', scale: 'large' } }, {});
    assert.equal(large.total_budget_eok, '22');
  });

  it('사용자 명시 입력이 scale fallback 보다 우선', () => {
    const slots = buildSlots({
      step1_company: { company: 'X', industry: 'STL', scale: '대기업' },
      total_budget_eok: '50',  // 명시 입력
    }, {});
    assert.equal(slots.total_budget_eok, '50');
    assert.equal(slots.duration_months, '24'); // 명시 없으니 scale 적용
  });

  it('UI step2_business alias 도 정량 슬롯으로 반영된다', () => {
    const slots = buildSlots({
      step1_company: { company: 'X', industry: 'STL', scale: '중견' },
      step2_business: {
        total_budget: '800 백만원',
        gov_pct: '70%',
        trl: '4 → 6',
        duration_months: '18 개월',
      },
    }, {});
    assert.equal(slots.total_budget_eok, '8');
    assert.equal(slots.govt_ratio_pct, '70');
    assert.equal(slots.private_ratio_pct, '30');
    assert.equal(slots.trl_start, '4');
    assert.equal(slots.trl_target, '6');
    assert.equal(slots.duration_months, '18');
  });

  it('알 수 없는 scale 값은 DEFAULTS 만 적용 (오류 던지지 않음)', () => {
    const slots = buildSlots({ step1_company: { company: 'X', industry: 'STL', scale: 'unknown' } }, {});
    assert.equal(slots.total_budget_eok, '6'); // DEFAULTS
  });
});

describe('library composeFromLibrary — 10 도메인 9 섹션 조립', () => {
  for (const industry of DOMAINS) {
    it(`${industry} 의 9 섹션이 모두 ## §N 헤더로 시작한다`, () => {
      const profile = {
        step1_company: {
          company: `[고객사 — 가상 ${industry} 사]`,
          industry,
          scale: '중견',
        },
      };
      const plan = { domain: industry, scenarios: [`SCN-${industry}-01`] };
      const slots = buildSlots(profile, plan);
      for (const sectionId of SECTIONS) {
        assert.ok(libraryHasSection(sectionId), `${sectionId} 가 LIBRARY 에 없다`);
        const md = composeFromLibrary(sectionId, slots);
        assert.ok(md, `${industry} ${sectionId} 조립 실패`);
        const expectedHeader = `## ${sectionId} ${librarySectionTitle(sectionId)}`;
        assert.ok(md.startsWith(expectedHeader),
          `${industry} ${sectionId} 가 ${expectedHeader} 로 시작하지 않음`);
        // 슬롯 잔존 0
        assert.doesNotMatch(md, /\{\{\w+\}\}/,
          `${industry} ${sectionId} 에 슬롯 잔존: ${md.match(/\{\{\w+\}\}/g)?.join(', ')}`);
      }
    });
  }
});

describe('library composeFromLibrary — STL 회귀 (사업계획서_샘플_철강 견본 결 정합)', () => {
  it('STL 도메인 §1 첫 단락에 1ZHM·2ZHM·정밀압연·APL·BAF facility 포함', () => {
    const profile = {
      step1_company: {
        company: '[고객사 — 부산·경남 가상 중견 스테인리스 정밀박판 제조사 A]',
        industry: 'STL',
        scale: '중견',
      },
    };
    const slots = buildSlots(profile, { domain: 'STL', scenarios: ['SCN-STL-04'] });
    const md = composeFromLibrary('§1', slots);
    assert.match(md, /1ZHM·2ZHM·정밀압연·APL·BAF/);
    assert.match(md, /스테인리스 SUS304·SUS316L 0\.1~2\.0 mm 박판/);
  });

  it('CAS 도메인 §1 첫 단락에 신규 어휘 (전기로·LF·VD·턴디시·몰드) 포함', () => {
    const profile = {
      step1_company: {
        company: '[고객사 — 가상 대기업 일관제철 연주·압연 통합사 F]',
        industry: 'CAS',
        scale: '대기업',
      },
    };
    const slots = buildSlots(profile, { domain: 'CAS', scenarios: ['SCN-CAS-01'] });
    const md = composeFromLibrary('§1', slots);
    assert.match(md, /전기로·LF·VD·턴디시·몰드·연주기·주형/);
    assert.match(md, /자동차·조선용 슬라브·블룸·빌렛·중력주조 부품/);
  });
});
