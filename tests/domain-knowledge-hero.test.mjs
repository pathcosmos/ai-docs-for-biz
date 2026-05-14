import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const svg = fs.readFileSync(
  new URL('../docs/assets/svg/guide/domain-knowledge.svg', import.meta.url),
  'utf8',
);
const css = fs.readFileSync(new URL('../docs/stylesheets/extra.css', import.meta.url), 'utf8');
const page = fs.readFileSync(new URL('../docs/guide/domain-knowledge.md', import.meta.url), 'utf8');
const hook = fs.readFileSync(new URL('../hooks/inject_hero_svg.py', import.meta.url), 'utf8');

test('domain knowledge hero is a wide, plain-language overview', () => {
  const viewBox = svg.match(/viewBox="0 0 (?<width>\d+) (?<height>\d+)"/)?.groups;
  assert.ok(viewBox, 'SVG should declare a numeric viewBox');
  assert.ok(Number(viewBox.width) > Number(viewBox.height), 'hero should be wider than it is tall');

  for (const phrase of ['현장 지식 모으기', '묻기', '정리', '문답 만들기', '확인', '남는 결과']) {
    assert.match(svg, new RegExp(phrase), `${phrase} should appear in the hero copy`);
  }

  assert.doesNotMatch(svg, /암묵지|형식지|골드셋|QA 프로토타입|RAG|sLM|cross-reference|100 문항|운영 회귀/);
});

test('domain knowledge hero has page-specific sizing and a simple intro', () => {
  assert.match(css, /domain-knowledge\.svg/);
  assert.match(css, /domain-knowledge\.svg[^{]+\{[^}]*max-height:\s*none\s*!important/s);
  assert.match(css, /domain-knowledge\.svg[^{]+\{[^}]*width:\s*100%\s*!important/s);
  assert.match(css, /domain-knowledge\.svg[^{]+\{[^}]*max-width:\s*900px\s*!important/s);
  assert.match(css, /max-width:\s*40em[\s\S]*domain-knowledge\.svg[\s\S]*min\(calc\(100vw - 2rem\),\s*340px\)/);
  assert.match(css, /max-width:\s*40em[\s\S]*margin-left:\s*0/);
  assert.match(page, /쉽게 말하면/);
  assert.match(hook, /guide\/domain-knowledge\.md/);
  assert.match(hook, /현장 지식을 질문·답·검증 기준으로 정리하는 흐름/);
});
