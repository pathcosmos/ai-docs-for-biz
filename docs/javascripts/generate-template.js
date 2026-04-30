// generate-template.js — Phase E16 Stage 1+2
// 본문 자동 생성 — 단순 치환 + AI 다듬기 (Gemini API, localStorage 키)

document$.subscribe(function () {
  const form = document.getElementById('generate-form');
  if (!form) return;
  if (form.dataset.initialized === 'true') return;
  form.dataset.initialized = 'true';

  const PLACEHOLDERS = ['고객사', '공정', '수치', '기간', '%', 'LLM모델', '벡터스토어', '임계'];
  const STORAGE_KEY = 'gemini_api_key';
  const GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent';

  // 1. templates.json 로드
  const dataPath = form.dataset.templatesPath || '../data/templates.json';
  let templates = {};

  fetch(dataPath)
    .then(r => {
      if (!r.ok) throw new Error('templates.json HTTP ' + r.status);
      return r.json();
    })
    .then(data => {
      templates = data;
      renderBlockList(templates);
      const errEl = document.getElementById('error-message');
      if (errEl) errEl.textContent = '';
    })
    .catch(err => {
      const errEl = document.getElementById('error-message');
      if (errEl) errEl.textContent = '⚠ 템플릿 데이터 로드 실패: ' + err.message + ' (' + dataPath + ')';
    });

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

  function getCheckedBlocks() {
    const cbs = document.querySelectorAll('input[name="blk"]:checked');
    return Array.from(cbs).map(cb => cb.value);
  }

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
      warn.textContent = ` · ⚠ 미치환 placeholder ${remainingMatches.length} 개 (${remainingPh.join('·')})`;
      meta.appendChild(warn);
    }
  }

  // 2. 단순 치환 모드
  document.getElementById('btn-generate').addEventListener('click', () => {
    const inputs = collectInputs();
    const selected = getCheckedBlocks();
    const output = document.getElementById('output');

    if (selected.length === 0) {
      output.value = '⚠ 좌측에서 BLK 블록을 1 개 이상 선택하세요.';
      const meta = document.getElementById('output-meta');
      if (meta) while (meta.firstChild) meta.removeChild(meta.firstChild);
      return;
    }

    const result = buildOutput(selected, inputs);
    output.value = result;
    updateMeta(result, selected, inputs);
  });

  // 3. API 키 localStorage 관리
  const apiKeyInput = document.getElementById('input-api-key');
  if (apiKeyInput) {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) apiKeyInput.value = saved;
    apiKeyInput.addEventListener('change', () => {
      const v = apiKeyInput.value.trim();
      if (v) {
        localStorage.setItem(STORAGE_KEY, v);
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    });
  }

  document.getElementById('btn-clear-key').addEventListener('click', () => {
    if (apiKeyInput) apiKeyInput.value = '';
    localStorage.removeItem(STORAGE_KEY);
    const status = document.getElementById('ai-status');
    if (status) status.textContent = '🔓 API 키 삭제됨';
  });

  // 4. Gemini API 호출
  async function callGemini(apiKey, prompt) {
    const url = `${GEMINI_URL}?key=${encodeURIComponent(apiKey)}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: {
          temperature: 0.6,
          maxOutputTokens: 4096,
          topP: 0.9,
        },
      }),
    });
    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Gemini API ${response.status}: ${errText.slice(0, 200)}`);
    }
    const data = await response.json();
    if (data.error) throw new Error(`Gemini API: ${data.error.message}`);
    const candidate = data.candidates && data.candidates[0];
    if (!candidate) throw new Error('Gemini 응답 candidates 0');
    if (candidate.finishReason === 'SAFETY') throw new Error('Gemini SAFETY 필터 차단');
    const parts = candidate.content && candidate.content.parts;
    if (!parts || parts.length === 0) throw new Error('Gemini 응답 parts 0');
    return parts[0].text;
  }

  function buildAIPrompt(rawText, inputs) {
    const inputDesc = Object.entries(inputs)
      .map(([k, v]) => `- [${k}] = ${v}`)
      .join('\n') || '(입력 정보 없음 — 플레이스홀더 그대로 유지)';
    return `당신은 한국어 정부지원 R&D 사업계획서 작성 전문가입니다. 아래 사업계획서 본문 초안을 다음 작업으로 다듬어 주세요:

【작업 지침】
1. 본문의 \`[고객사]·[공정]·[수치]\` 등 플레이스홀더 중 아래 입력 정보가 있는 것은 자연스럽게 치환
2. 한국어 사업계획서 formal 문어체 (~한다·~된다 종결, 명사형 표현 적극 활용) 일관 적용
3. 단락 간 논리 흐름 자연스럽게 (현황 → 문제 → 해결 → 기대효과)
4. 의미 보존 — 원본 내용 추가·삭제 0, 표현·문체만 정렬
5. 제목 (## 헤딩) 그대로 유지
6. 출력은 다듬어진 마크다운 본문만 (해설·주석 X)

【사용자 입력 정보】
${inputDesc}

【본문 초안】
${rawText}

【다듬어진 본문】
`;
  }

  // 5. AI 다듬기 모드
  document.getElementById('btn-ai-generate').addEventListener('click', async () => {
    const apiKey = (apiKeyInput && apiKeyInput.value.trim()) || localStorage.getItem(STORAGE_KEY);
    const status = document.getElementById('ai-status');
    const output = document.getElementById('output');

    if (!apiKey) {
      if (status) status.textContent = '⚠ API 키를 입력하세요.';
      return;
    }

    const inputs = collectInputs();
    const selected = getCheckedBlocks();
    if (selected.length === 0) {
      if (status) status.textContent = '⚠ BLK 블록을 1 개 이상 선택하세요.';
      return;
    }

    const rawText = buildOutput(selected, inputs);
    if (status) status.textContent = '🤖 Gemini AI 호출 중... (10~30초 소요)';
    output.value = rawText + '\n\n---\n\n[AI 다듬기 진행 중...]';

    try {
      const prompt = buildAIPrompt(rawText, inputs);
      const ai = await callGemini(apiKey, prompt);
      output.value = ai.trim();
      updateMeta(output.value, selected, inputs);
      if (status) status.textContent = '✅ Gemini AI 다듬기 완료';
    } catch (err) {
      if (status) status.textContent = '❌ ' + err.message;
      output.value = rawText + '\n\n---\n\n[AI 호출 실패: ' + err.message + ']';
    }
  });

  // 6. 복사
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

  // 7. 다운로드 (.md)
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

  // 8. 모두 선택·해제
  document.getElementById('btn-select-all').addEventListener('click', () => {
    document.querySelectorAll('input[name="blk"]').forEach(cb => { cb.checked = true; });
  });
  document.getElementById('btn-clear-all').addEventListener('click', () => {
    document.querySelectorAll('input[name="blk"]').forEach(cb => { cb.checked = false; });
    document.getElementById('output').value = '';
    const meta = document.getElementById('output-meta');
    if (meta) while (meta.firstChild) meta.removeChild(meta.firstChild);
  });
});
