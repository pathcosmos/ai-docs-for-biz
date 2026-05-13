import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

test('assemble page keeps app markup as raw HTML instead of markdown-parsed blocks', () => {
  const markup = fs.readFileSync(new URL('../docs/assemble.md', import.meta.url), 'utf8');

  assert.match(markup, /<div id="assemble-app" class="assemble-app"/);
  assert.equal(markup.includes('markdown="1"'), false);
  assert.equal(markup.includes('<ol class="assemble-stepper"'), false);
  assert.match(markup, /<div class="assemble-stepper" role="list"/);
  assert.match(markup, /class="assemble-mark" width="96" height="56"/);
  assert.match(markup, /hide:\s*\n(?:\s+- .+\n)*\s+- navigation\n(?:\s+- .+\n)*\s+- path/m);
  assert.match(markup, /<button id="assemble-copy" type="button" disabled>복사<\/button>/);
  assert.match(markup, /<button id="assemble-download" type="button" disabled>다운로드<\/button>/);
});

test('assemble stylesheet does not size the app from viewport while inside docs chrome', () => {
  const css = fs.readFileSync(new URL('../docs/stylesheets/assemble.css', import.meta.url), 'utf8');

  assert.doesNotMatch(css, /\.assemble-app\s*\{[^}]*100vw/s);
  assert.match(css, /body:has\(#assemble-app\)\s+\.md-tabs__list\s*\{[^}]*justify-content:\s*center/s);
  assert.match(css, /\.md-typeset\s+\.assemble-stepper\s*\{[^}]*display:\s*grid/s);
  assert.match(css, /\.md-typeset\s+\.assemble-stepper\s+\[data-assemble-step\]\s*\{[^}]*display:\s*grid/s);
  assert.match(css, /\.md-typeset\s+\.assemble-mark\s*\{[^}]*width:/s);
  assert.match(css, /\.md-typeset\s+img\.assemble-mark\[src\$="\.svg"\]\s*\{[^}]*width:[^;]+!important/s);
  assert.match(css, /\.md-typeset\s+img\.assemble-mark\[src\$="\.svg"\]\s*\{[^}]*max-width:[^;]+!important/s);
});

test('assemble block catalog uses page scrolling and makes click-to-selection mapping visible', () => {
  const css = fs.readFileSync(new URL('../docs/stylesheets/assemble.css', import.meta.url), 'utf8');
  const js = fs.readFileSync(new URL('../docs/javascripts/assemble-ui.js', import.meta.url), 'utf8');

  const catalogRule = css.match(/\.assemble-catalog\s*\{(?<body>[^}]*)\}/s)?.groups.body || '';
  assert.doesNotMatch(catalogRule, /max-height\s*:/);
  assert.doesNotMatch(catalogRule, /overflow\s*:\s*auto/);
  assert.match(catalogRule, /overflow\s*:\s*visible/);
  assert.match(css, /\.assemble-active-map\s*\{/);
  assert.match(css, /\.assemble-cart-item\[data-active="true"\]/);
  assert.match(css, /\.assemble-section-slot\[data-active="true"\]/);
  assert.match(js, /function\s+toggleBlock\(id\)/);
  assert.match(js, /title\.addEventListener\('click',\s*\(\)\s*=>\s*toggleBlock\(id\)\);/);
  assert.match(js, /state\.selectedBlocks\.includes\(id\)\s*\?\s*'해제'\s*:\s*'담기'/);
});
