// generate-template.js — Phase E16 Stage 3 (계층 selector + § 매핑 + 패키지·검색)

document$.subscribe(function () {
  const form = document.getElementById('generate-form');
  if (!form) return;
  if (form.dataset.initialized === 'true') return;
  form.dataset.initialized = 'true';

  const PLACEHOLDERS = ['고객사', '공정', '수치', '기간', '%', 'LLM모델', '벡터스토어', '임계'];
  const STORAGE_KEY = 'gemini_api_key';
  const GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent';

  // 패키지별 권장 묶음 (도메인별 시나리오 + Track + 가이드 자동 묶음)
  const PKG_BUNDLES = {
    pkg1: { label: '패키지 1 — 대기업 철강 다년 R&D', domain: 'STL', subtitle: '9 시나리오 · 다년 (33+ 개월)' },
    pkg2: { label: '패키지 2 — 중견 냉연 12 개월', domain: 'STL', subtitle: '6 시나리오 · 12 개월' },
    pkg3: { label: '패키지 3 — 특수강관 RAG 9 개월', domain: 'STL·LLM', subtitle: '4 시나리오 · 9 개월' },
    pkg4: { label: '패키지 4 — 고무 양산 OEM', domain: 'RUB', subtitle: '5 시나리오 · 12 개월' },
    pkg5: { label: '패키지 5 — 정밀가공 SaaS', domain: 'MET', subtitle: '5 시나리오 · 9 개월' },
    pkg6: { label: '패키지 6 — 유틸·ESG·CBAM', domain: 'UTL·SAF', subtitle: '5 시나리오 · 12 개월' },
  };

  // 사업계획서 § 그룹 (관련 카테고리·키워드)
  const SECTION_GROUPS = [
    { id: '§0', label: '§0 과제 요약', keys: ['§0'] },
    { id: '§1', label: '§1 사업 개요·추진 배경', keys: ['§1'] },
    { id: '§2', label: '§2 기업 현황·대상 공정', keys: ['§2'] },
    { id: '§3', label: '§3 사업 배경·AS-IS', keys: ['§3', 'AS-IS', '적용 맥락'] },
    { id: '§4', label: '§4 기술 설계·TO-BE', keys: ['§4', 'TO-BE', 'AI 해결'] },
    { id: '§5', label: '§5 구현 상세·청킹·RAG', keys: ['§5', 'RAG', '청킹'] },
    { id: '§6', label: '§6 기대효과·KPI', keys: ['§6', '기대효과', 'KPI'] },
    { id: '§7', label: '§7 Track 2·3 연계·MLOps', keys: ['§7', 'MLOps'] },
    { id: '§8', label: '§8 부록·별첨', keys: ['§8'] },
    { id: '§10', label: '§10 재무·예산', keys: ['§10', '재무'] },
  ];

  let templates = {};

  // 1. templates.json 로드
  const dataPath = form.dataset.templatesPath || '../data/templates.json';
  fetch(dataPath)
    .then(r => {
      if (!r.ok) throw new Error('templates.json HTTP ' + r.status);
      return r.json();
    })
    .then(data => {
      templates = data;
      const errEl = document.getElementById('error-message');
      if (errEl) errEl.textContent = '';
      // 통계 업데이트
      const stat = document.getElementById('asset-stats');
      if (stat) {
        const byCat = {};
        Object.values(data).forEach(b => { byCat[b.category] = (byCat[b.category] || 0) + 1; });
        stat.textContent = `총 ${Object.keys(data).length} 블록 (track ${byCat.track||0}·package ${byCat.package||0}·scenario ${byCat.scenario||0}·guide ${byCat.guide||0}·module ${byCat.module||0})`;
      }
      // 모드별 렌더
      renderQuickMode();
      renderSectionMode();
      renderTrackMode();
    })
    .catch(err => {
      const errEl = document.getElementById('error-message');
      if (errEl) errEl.textContent = '⚠ 템플릿 데이터 로드 실패: ' + err.message;
    });

  // 2. 모드 탭 전환
  document.querySelectorAll('.generate-tabs button').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.generate-tabs button').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.generate-mode').forEach(m => m.style.display = 'none');
      btn.classList.add('active');
      const mode = btn.dataset.mode;
      const target = document.getElementById('mode-' + mode);
      if (target) target.style.display = 'block';
    });
  });

  // 3. ⚡ 빠른 모드 — 패키지 카드
  function renderQuickMode() {
    const container = document.getElementById('pkg-cards');
    if (!container) return;
    while (container.firstChild) container.removeChild(container.firstChild);
    Object.entries(PKG_BUNDLES).forEach(([pkgId, info]) => {
      const blocksInPkg = Object.entries(templates)
        .filter(([id, t]) => t.package === pkgId).length;
      const card = document.createElement('div');
      card.className = 'pkg-card';
      card.dataset.pkg = pkgId;
      const h = document.createElement('div'); h.className = 'pkg-card-header';
      h.textContent = info.label; card.appendChild(h);
      const s = document.createElement('div'); s.className = 'pkg-card-sub';
      s.textContent = info.subtitle + ' · ' + info.domain; card.appendChild(s);
      const c = document.createElement('div'); c.className = 'pkg-card-count';
      c.textContent = blocksInPkg + ' 블록'; card.appendChild(c);
      card.addEventListener('click', () => selectPackage(pkgId, card));
      container.appendChild(card);
    });
  }

  function selectPackage(pkgId, card) {
    document.querySelectorAll('.pkg-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    // 패키지 본문 + 도메인 시나리오 + Track 자동 묶음
    const info = PKG_BUNDLES[pkgId];
    const domainPrefixes = info.domain.split('·');
    const ids = Object.entries(templates)
      .filter(([id, t]) => {
        if (t.package === pkgId) return true;
        // 시나리오: 같은 도메인
        if (t.category === 'scenario' && domainPrefixes.some(d => t.domain.includes(d) || (t.tags || []).includes(d))) return true;
        // Track: 모두 포함 (사업계획서 §3·§4·§6 공통)
        if (t.category === 'track') return true;
        return false;
      })
      .map(([id]) => id);
    setSelectedBlocks(ids);
    updateSelectedCount();
  }

  // 4. 🎯 § 매핑 모드
  function renderSectionMode() {
    const container = document.getElementById('section-tree');
    if (!container) return;
    while (container.firstChild) container.removeChild(container.firstChild);
    SECTION_GROUPS.forEach(group => {
      const matchingBlocks = Object.entries(templates).filter(([id, t]) =>
        group.keys.some(k => (t.section || '').includes(k))
      );
      if (matchingBlocks.length === 0) return;

      const details = document.createElement('details');
      details.className = 'section-group';
      const summary = document.createElement('summary');
      summary.textContent = `${group.label} [${matchingBlocks.length} 블록]`;
      details.appendChild(summary);

      const list = document.createElement('div');
      list.className = 'section-block-list';
      matchingBlocks.forEach(([id, t]) => {
        const label = document.createElement('label');
        label.className = 'blk-item';
        const cb = document.createElement('input');
        cb.type = 'checkbox'; cb.value = id; cb.name = 'blk-section';
        cb.addEventListener('change', updateSelectedCount);
        label.appendChild(cb);
        const span = document.createElement('span');
        const catBadge = document.createElement('span');
        catBadge.className = 'cat-badge cat-' + t.category;
        catBadge.textContent = t.category;
        span.appendChild(catBadge);
        const text = document.createTextNode(' ' + t.title);
        span.appendChild(text);
        if (t.preview) {
          const prev = document.createElement('div');
          prev.className = 'blk-preview';
          prev.textContent = t.preview;
          span.appendChild(prev);
        }
        label.appendChild(span);
        list.appendChild(label);
      });
      details.appendChild(list);
      container.appendChild(details);
    });
  }

  // 5. 📋 Track 모드 — 기존 15 BLK
  function renderTrackMode() {
    const container = document.getElementById('blk-checklist');
    if (!container) return;
    while (container.firstChild) container.removeChild(container.firstChild);
    Object.entries(templates).filter(([id]) => id.startsWith('BLK-T')).sort().forEach(([id, t]) => {
      const label = document.createElement('label');
      label.className = 'blk-item';
      const cb = document.createElement('input');
      cb.type = 'checkbox'; cb.value = id; cb.name = 'blk-track';
      cb.addEventListener('change', updateSelectedCount);
      label.appendChild(cb);
      const span = document.createElement('span'); span.textContent = t.title;
      label.appendChild(span);
      container.appendChild(label);
    });
  }

  // 6. 🔍 자유 검색
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const q = searchInput.value.trim().toLowerCase();
      const results = document.getElementById('search-results');
      while (results.firstChild) results.removeChild(results.firstChild);
      if (q.length < 2) return;
      const matches = Object.entries(templates)
        .filter(([id, t]) => (t.body + ' ' + t.title).toLowerCase().includes(q))
        .slice(0, 50);
      const hint = document.createElement('div');
      hint.className = 'search-hint';
      hint.textContent = `결과 ${matches.length} 블록 (최대 50)`;
      results.appendChild(hint);
      matches.forEach(([id, t]) => {
        const label = document.createElement('label');
        label.className = 'blk-item';
        const cb = document.createElement('input');
        cb.type = 'checkbox'; cb.value = id; cb.name = 'blk-search';
        cb.addEventListener('change', updateSelectedCount);
        label.appendChild(cb);
        const span = document.createElement('span');
        const cat = document.createElement('span');
        cat.className = 'cat-badge cat-' + t.category;
        cat.textContent = t.category;
        span.appendChild(cat);
        span.appendChild(document.createTextNode(' ' + t.title));
        const prev = document.createElement('div');
        prev.className = 'blk-preview';
        prev.textContent = t.preview || '';
        span.appendChild(prev);
        label.appendChild(span);
        results.appendChild(label);
      });
    });
  }

  // 7. 공통 — 선택된 블록 (모든 모드 합산)
  function getCheckedBlocks() {
    const cbs = document.querySelectorAll('input[name^="blk"]:checked');
    return Array.from(new Set(Array.from(cbs).map(cb => cb.value)));
  }

  function setSelectedBlocks(ids) {
    document.querySelectorAll('input[name^="blk"]').forEach(cb => {
      cb.checked = ids.includes(cb.value);
    });
  }

  function updateSelectedCount() {
    const n = getCheckedBlocks().length;
    const counter = document.getElementById('selected-count');
    if (counter) counter.textContent = `선택 ${n} 블록`;
  }

  // 8. 입력
  function collectInputs() {
    const inputs = {};
    PLACEHOLDERS.forEach(key => {
      const el = document.getElementById('input-' + slugify(key));
      if (el && el.value.trim()) inputs[key] = el.value.trim();
    });
    return inputs;
  }
  function slugify(key) { return key.replace('%', 'percent'); }

  function applyPlaceholders(text, inputs) {
    let result = text;
    Object.entries(inputs).forEach(([key, val]) => {
      const safeKey = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      result = result.replace(new RegExp('\\[' + safeKey + '\\]', 'g'), val);
    });
    return result;
  }

  function buildOutput(selected, inputs) {
    return selected.map(id => {
      const tpl = templates[id];
      if (!tpl) return '';
      const body = applyPlaceholders(tpl.body, inputs);
      return `## ${tpl.title}\n\n${body}`;
    }).join('\n\n---\n\n');
  }

  function updateMeta(text, selected, inputs) {
    const meta = document.getElementById('output-meta');
    if (!meta) return;
    while (meta.firstChild) meta.removeChild(meta.firstChild);
    const remainingPh = PLACEHOLDERS.filter(k => !inputs[k]);
    const remainingMatches = text.match(/\[(?:고객사|공정|수치|기간|%|LLM모델|벡터스토어|임계)\]/g) || [];
    const lines = text.split('\n').length;
    const chars = text.length;

    const stats = document.createElement('span');
    stats.textContent = `📊 ${selected.length} 블록 · ${lines} 줄 · ${chars.toLocaleString()} 자`;
    meta.appendChild(stats);

    if (remainingMatches.length > 0) {
      const warn = document.createElement('span');
      warn.className = 'warn';
      warn.textContent = ` · ⚠ 미치환 ${remainingMatches.length} 개 (${remainingPh.join('·')})`;
      meta.appendChild(warn);
    }
  }

  // 9. 단순 치환
  document.getElementById('btn-generate').addEventListener('click', () => {
    const inputs = collectInputs();
    const selected = getCheckedBlocks();
    const output = document.getElementById('output');

    if (selected.length === 0) {
      output.value = '⚠ 1 개 이상 블록을 선택하세요.';
      const meta = document.getElementById('output-meta');
      if (meta) while (meta.firstChild) meta.removeChild(meta.firstChild);
      return;
    }

    const result = buildOutput(selected, inputs);
    output.value = result;
    updateMeta(result, selected, inputs);
  });

  // 10. API 키 localStorage
  const apiKeyInput = document.getElementById('input-api-key');
  if (apiKeyInput) {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) apiKeyInput.value = saved;
    apiKeyInput.addEventListener('change', () => {
      const v = apiKeyInput.value.trim();
      if (v) localStorage.setItem(STORAGE_KEY, v);
      else localStorage.removeItem(STORAGE_KEY);
    });
  }

  document.getElementById('btn-clear-key').addEventListener('click', () => {
    if (apiKeyInput) apiKeyInput.value = '';
    localStorage.removeItem(STORAGE_KEY);
    const status = document.getElementById('ai-status');
    if (status) status.textContent = '🔓 API 키 삭제됨';
  });

  async function callGemini(apiKey, prompt) {
    const url = `${GEMINI_URL}?key=${encodeURIComponent(apiKey)}`;
    const response = await fetch(url, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: { temperature: 0.6, maxOutputTokens: 8192, topP: 0.9 },
      }),
    });
    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Gemini ${response.status}: ${errText.slice(0, 200)}`);
    }
    const data = await response.json();
    if (data.error) throw new Error('Gemini: ' + data.error.message);
    const candidate = data.candidates && data.candidates[0];
    if (!candidate) throw new Error('Gemini candidates 0');
    if (candidate.finishReason === 'SAFETY') throw new Error('Gemini SAFETY 차단');
    const parts = candidate.content && candidate.content.parts;
    if (!parts || parts.length === 0) throw new Error('Gemini parts 0');
    return parts[0].text;
  }

  function buildAIPrompt(rawText, inputs) {
    const inputDesc = Object.entries(inputs)
      .map(([k, v]) => `- [${k}] = ${v}`)
      .join('\n') || '(입력 정보 없음 — 플레이스홀더 그대로 유지)';
    return `당신은 한국어 정부지원 R&D 사업계획서 작성 전문가입니다. 아래 본문 초안을 다듬어 주세요:

【작업 지침】
1. 본문의 \`[고객사]·[공정]·[수치]\` 등 플레이스홀더 중 아래 입력 정보가 있는 것은 자연스럽게 치환
2. 한국어 사업계획서 formal 문어체 (~한다·~된다 종결, 명사형 표현 적극 활용) 일관 적용
3. 단락 간 논리 흐름 자연스럽게 (현황 → 문제 → 해결 → 기대효과)
4. 의미 보존 — 원본 내용 추가·삭제 0, 표현·문체만 정렬
5. 제목 (## 헤딩) 그대로 유지
6. 출력은 다듬어진 마크다운 본문만

【사용자 입력 정보】
${inputDesc}

【본문 초안】
${rawText}

【다듬어진 본문】
`;
  }

  // 11. AI 다듬기
  document.getElementById('btn-ai-generate').addEventListener('click', async () => {
    const apiKey = (apiKeyInput && apiKeyInput.value.trim()) || localStorage.getItem(STORAGE_KEY);
    const status = document.getElementById('ai-status');
    const output = document.getElementById('output');
    if (!apiKey) { if (status) status.textContent = '⚠ API 키를 입력하세요.'; return; }
    const inputs = collectInputs();
    const selected = getCheckedBlocks();
    if (selected.length === 0) { if (status) status.textContent = '⚠ 블록을 1 개 이상 선택하세요.'; return; }

    const rawText = buildOutput(selected, inputs);
    if (rawText.length > 100000) {
      if (status) status.textContent = '⚠ 본문 너무 큼 (' + rawText.length + ' 자) — 블록 줄이세요.';
      return;
    }
    if (status) status.textContent = '🤖 Gemini 호출 중... (' + rawText.length.toLocaleString() + ' 자)';
    output.value = rawText + '\n\n---\n\n[AI 다듬기 진행 중...]';

    try {
      const ai = await callGemini(apiKey, buildAIPrompt(rawText, inputs));
      output.value = ai.trim();
      updateMeta(output.value, selected, inputs);
      if (status) status.textContent = '✅ Gemini AI 완료';
    } catch (err) {
      if (status) status.textContent = '❌ ' + err.message;
      output.value = rawText + '\n\n---\n\n[AI 실패: ' + err.message + ']';
    }
  });

  // 12. 복사·다운로드
  document.getElementById('btn-copy').addEventListener('click', async () => {
    const output = document.getElementById('output');
    if (!output.value) return;
    try {
      await navigator.clipboard.writeText(output.value);
      const btn = document.getElementById('btn-copy');
      const orig = btn.textContent;
      btn.textContent = '✅ 복사됨';
      setTimeout(() => { btn.textContent = orig; }, 1500);
    } catch (e) { alert('복사 실패: ' + e.message); }
  });

  document.getElementById('btn-download').addEventListener('click', () => {
    const output = document.getElementById('output');
    if (!output.value) return;
    const blob = new Blob([output.value], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const today = new Date().toISOString().slice(0, 10);
    a.download = `사업계획서_본문_${today}.md`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // 13. 모두 선택·해제
  document.getElementById('btn-select-all').addEventListener('click', () => {
    document.querySelectorAll('input[name^="blk"]').forEach(cb => { cb.checked = true; });
    updateSelectedCount();
  });
  document.getElementById('btn-clear-all').addEventListener('click', () => {
    document.querySelectorAll('input[name^="blk"]').forEach(cb => { cb.checked = false; });
    document.getElementById('output').value = '';
    const meta = document.getElementById('output-meta');
    if (meta) while (meta.firstChild) meta.removeChild(meta.firstChild);
    updateSelectedCount();
  });
});
