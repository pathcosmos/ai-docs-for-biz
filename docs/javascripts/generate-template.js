// generate-template.js — Phase E16-2 (Stage 1)
// 본문 자동 생성 페이지 (docs/generate.md) 의 폼 처리·placeholder 치환·복사·다운로드.

document$.subscribe(function () {
  const form = document.getElementById('generate-form');
  if (!form) return;
  if (form.dataset.initialized === 'true') return;
  form.dataset.initialized = 'true';

  const PLACEHOLDERS = ['고객사', '공정', '수치', '기간', '%', 'LLM모델', '벡터스토어', '임계'];

  // 1. templates.json 로드
  const dataPath = form.dataset.templatesPath || 'data/templates.json';
  let templates = {};

  fetch(dataPath)
    .then(r => {
      if (!r.ok) throw new Error('templates.json 로드 실패');
      return r.json();
    })
    .then(data => {
      templates = data;
      renderBlockList(templates);
    })
    .catch(err => {
      const errEl = document.getElementById('error-message');
      if (errEl) errEl.textContent = '⚠ 템플릿 데이터 로드 실패: ' + err.message;
    });

  // 2. 블록 체크박스 렌더링 (DOM API only)
  function renderBlockList(tpls) {
    const container = document.getElementById('blk-checklist');
    if (!container) return;
    while (container.firstChild) container.removeChild(container.firstChild);
    const ids = Object.keys(tpls).sort();
    ids.forEach(id => {
      const label = document.createElement('label');
      label.className = 'blk-item';
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.value = id;
      cb.name = 'blk';
      label.appendChild(cb);
      const span = document.createElement('span');
      span.textContent = tpls[id].title;
      label.appendChild(span);
      container.appendChild(label);
    });
  }

  // 3. 입력 폼 → 키-값 dict
  function collectInputs() {
    const inputs = {};
    PLACEHOLDERS.forEach(key => {
      const el = document.getElementById('input-' + slugify(key));
      if (el && el.value.trim()) inputs[key] = el.value.trim();
    });
    return inputs;
  }

  function slugify(key) {
    return key.replace('%', 'percent');
  }

  // 4. 선택된 블록 배열
  function getCheckedBlocks() {
    const cbs = document.querySelectorAll('input[name="blk"]:checked');
    return Array.from(cbs).map(cb => cb.value);
  }

  // 5. placeholder 치환 (모든 [key] → value)
  function applyPlaceholders(text, inputs) {
    let result = text;
    Object.entries(inputs).forEach(([key, val]) => {
      const safeKey = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      result = result.replace(new RegExp('\\[' + safeKey + '\\]', 'g'), val);
    });
    return result;
  }

  // 6. 생성하기
  document.getElementById('btn-generate').addEventListener('click', () => {
    const inputs = collectInputs();
    const selected = getCheckedBlocks();
    const output = document.getElementById('output');
    const meta = document.getElementById('output-meta');

    if (selected.length === 0) {
      output.value = '⚠ 좌측에서 BLK 블록을 1 개 이상 선택하세요.';
      if (meta) {
        while (meta.firstChild) meta.removeChild(meta.firstChild);
      }
      return;
    }

    const parts = selected.map(id => {
      const tpl = templates[id];
      if (!tpl) return '';
      const body = applyPlaceholders(tpl.body, inputs);
      return `## ${tpl.title}\n\n${body}`;
    });
    output.value = parts.join('\n\n---\n\n');

    // 메타 — DOM API 로 안전 구성
    if (meta) {
      while (meta.firstChild) meta.removeChild(meta.firstChild);
      const remainingPh = PLACEHOLDERS.filter(k => !inputs[k]);
      const remainingMatches = output.value.match(/\[(?:고객사|공정|수치|기간|%|LLM모델|벡터스토어|임계)\]/g) || [];
      const lines = output.value.split('\n').length;
      const chars = output.value.length;

      const stats = document.createElement('span');
      stats.textContent = `📊 ${selected.length} 블록 · ${lines} 줄 · ${chars.toLocaleString()} 자`;
      meta.appendChild(stats);

      if (remainingMatches.length > 0) {
        const warn = document.createElement('span');
        warn.className = 'warn';
        warn.textContent = ` · ⚠ 미치환 placeholder ${remainingMatches.length} 개 (${remainingPh.join('·')})`;
        meta.appendChild(warn);
      }
    }
  });

  // 7. 복사
  document.getElementById('btn-copy').addEventListener('click', async () => {
    const output = document.getElementById('output');
    if (!output.value) return;
    try {
      await navigator.clipboard.writeText(output.value);
      const btn = document.getElementById('btn-copy');
      const orig = btn.textContent;
      btn.textContent = '✅ 복사됨';
      setTimeout(() => { btn.textContent = orig; }, 1500);
    } catch (e) {
      alert('복사 실패: ' + e.message);
    }
  });

  // 8. 다운로드 (.md)
  document.getElementById('btn-download').addEventListener('click', () => {
    const output = document.getElementById('output');
    if (!output.value) return;
    const blob = new Blob([output.value], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const today = new Date().toISOString().slice(0, 10);
    a.download = `사업계획서_본문_${today}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // 9. 모두 선택·해제
  document.getElementById('btn-select-all').addEventListener('click', () => {
    document.querySelectorAll('input[name="blk"]').forEach(cb => { cb.checked = true; });
  });
  document.getElementById('btn-clear-all').addEventListener('click', () => {
    document.querySelectorAll('input[name="blk"]').forEach(cb => { cb.checked = false; });
    document.getElementById('output').value = '';
    const meta = document.getElementById('output-meta');
    if (meta) {
      while (meta.firstChild) meta.removeChild(meta.firstChild);
    }
  });
});
