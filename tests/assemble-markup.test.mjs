import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

test('assemble page keeps app markup as raw HTML instead of markdown-parsed blocks', () => {
  const markup = fs.readFileSync(new URL('../docs/assemble.md', import.meta.url), 'utf8');

  assert.match(markup, /<div id="assemble-app" class="assemble-app"/);
  assert.equal(markup.includes('markdown="1"'), false);
  assert.match(markup, /<button id="assemble-copy" type="button" disabled>복사<\/button>/);
  assert.match(markup, /<button id="assemble-download" type="button" disabled>다운로드<\/button>/);
});
