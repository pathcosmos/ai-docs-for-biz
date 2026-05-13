import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { runAudit } from '../src/audit.js';
import { buildSlots, composeFromLibrary } from '../src/library.js';

function fullDocument(domain = 'STL') {
  const profile = {
    step1_company: {
      company: '동국산업(주)',
      industry: domain,
      scale: '중견',
    },
  };
  const plan = { domain, package: 'pkg2', scenarios: [`SCN-${domain}-01`, 'SCN-MLO-01'] };
  const slots = buildSlots(profile, plan);
  const sections = ['§1', '§2', '§3', '§4', '§5', '§6', '§7', '§8', '§9']
    .map(section => composeFromLibrary(section, slots));
  return `# 동국산업(주) AI 사업계획서\n\n${sections.join('\n\n')}\n`;
}

describe('runAudit', () => {
  it('완성형 9 섹션 문서를 6축 PASS 처리한다', () => {
    const audit = runAudit(fullDocument('STL'), 'STL');
    assert.equal(audit.passed, true);
    assert.equal(audit.summary.pass_count, 6);
    assert.equal(audit.summary.fail_count, 0);
  });

  it('슬롯·플레이스홀더·섹션 누락·도메인 오염·메타 누출을 잡아낸다', () => {
    const broken = [
      '# 테스트',
      '',
      '## §1 현황',
      '',
      '{{company}} 의 [수치] 목표 TODO',
      '',
      '## §2 문제인식',
      '',
      'RUB 본문에 1ZHM 2ZHM BAF 압연유 스테인리스가 섞였다.',
    ].join('\n');
    const audit = runAudit(broken, 'RUB');
    assert.equal(audit.passed, false);
    assert.equal(audit.checks.slot.pass, false);
    assert.equal(audit.checks.placeholder.pass, false);
    assert.equal(audit.checks.sectionHeaders.pass, false);
    assert.equal(audit.checks.cross.pass, false);
    assert.equal(audit.checks.meta.pass, false);
  });
});
