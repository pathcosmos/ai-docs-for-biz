// copy-block.js — H2/H3 섹션·blockquote·표 단위로 "이 블록 복사" 버튼 자동 주입
// MkDocs Material 의 instant navigation (document$) 호환

document$.subscribe(function () {
  // 페이지 본문 영역만 대상
  var content = document.querySelector('.md-content article');
  if (!content) return;

  // 이미 처리됐으면 스킵 (instant navigation 중복 회피)
  if (content.dataset.copyBlocksApplied === 'true') return;
  content.dataset.copyBlocksApplied = 'true';

  // 대상 1 — H2/H3 섹션 (헤더부터 다음 헤더 직전까지를 1 블록으로)
  var headers = content.querySelectorAll('h2, h3');
  headers.forEach(function (header) {
    addCopyButton(header, 'header');
  });

  // 대상 2 — 표 (table)
  var tables = content.querySelectorAll('table');
  tables.forEach(function (table) {
    var wrapper = table.closest('.md-typeset__table') || table.parentElement;
    addCopyButtonToBlock(wrapper, table, 'table');
  });

  // 대상 3 — blockquote (출처 표기·인용 박스)
  var blockquotes = content.querySelectorAll('blockquote');
  blockquotes.forEach(function (bq) {
    addCopyButtonToBlock(bq, bq, 'blockquote');
  });
});

function addCopyButton(header, kind) {
  if (header.dataset.copyButtonAdded === 'true') return;
  header.dataset.copyButtonAdded = 'true';

  var btn = document.createElement('button');
  btn.className = 'copy-block-btn';
  btn.title = '이 섹션 본문 복사';
  btn.setAttribute('aria-label', '이 섹션 본문 복사');
  btn.textContent = '📋 복사';

  btn.addEventListener('click', function (e) {
    e.preventDefault();
    var text = collectSectionText(header);
    copyToClipboard(text, btn);
  });

  header.appendChild(btn);
}

function addCopyButtonToBlock(wrapper, source, kind) {
  if (wrapper.dataset.copyButtonAdded === 'true') return;
  wrapper.dataset.copyButtonAdded = 'true';
  wrapper.style.position = wrapper.style.position || 'relative';

  var btn = document.createElement('button');
  btn.className = 'copy-block-btn copy-block-btn--inline';
  btn.title = (kind === 'table' ? '표 ' : '블록 ') + '복사';
  btn.setAttribute('aria-label', '복사');
  btn.textContent = '📋';

  btn.addEventListener('click', function (e) {
    e.preventDefault();
    var text = (kind === 'table') ? tableToText(source) : (source.innerText || source.textContent || '');
    copyToClipboard(text, btn);
  });

  wrapper.appendChild(btn);
}

// 헤더부터 다음 헤더 (동급 또는 상위) 직전까지의 텍스트 수집
function collectSectionText(header) {
  var level = parseInt(header.tagName.substring(1), 10);
  var lines = [header.textContent.replace(/¤$/, '').trim()];

  var node = header.nextElementSibling;
  while (node) {
    if (/^H[1-6]$/.test(node.tagName)) {
      var nodeLevel = parseInt(node.tagName.substring(1), 10);
      if (nodeLevel <= level) break;
    }
    var text = (node.innerText || node.textContent || '').trim();
    if (text) lines.push(text);
    node = node.nextElementSibling;
  }
  return lines.join('\n\n');
}

// 표 → 마크다운 표 텍스트 변환 (paste 시 다른 도구 호환)
function tableToText(table) {
  var rows = table.querySelectorAll('tr');
  var out = [];
  rows.forEach(function (row, idx) {
    var cells = row.querySelectorAll('th, td');
    var cellTexts = Array.from(cells).map(function (c) {
      return (c.innerText || c.textContent || '').trim().replace(/\|/g, '\\|');
    });
    out.push('| ' + cellTexts.join(' | ') + ' |');
    if (idx === 0 && row.querySelectorAll('th').length > 0) {
      out.push('|' + cellTexts.map(function () { return ' --- '; }).join('|') + '|');
    }
  });
  return out.join('\n');
}

function copyToClipboard(text, btn) {
  if (!navigator.clipboard) {
    // fallback (구형 브라우저)
    var textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(textarea);
    flashSuccess(btn);
    return;
  }
  navigator.clipboard.writeText(text).then(function () {
    flashSuccess(btn);
  }).catch(function () {
    btn.textContent = '⚠ 실패';
    setTimeout(function () { btn.textContent = '📋 복사'; }, 1500);
  });
}

function flashSuccess(btn) {
  var original = btn.textContent;
  btn.textContent = '✓ 복사됨';
  btn.classList.add('copy-block-btn--success');
  setTimeout(function () {
    btn.textContent = original;
    btn.classList.remove('copy-block-btn--success');
  }, 1500);
}
