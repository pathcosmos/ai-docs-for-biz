(function () {
  const STORAGE_KEY = 'ai_docs_agent_state_v1';
  const RESULT_KEY = 'ai_docs_agent_last_result_v1';
  const SECTION_CONTEXT_IDS = [
    'GUIDE-COMPANY-PROFILE-§3',
    'GUIDE-PROBLEM-MATRIX-§3',
    'GUIDE-KPI-BREAKDOWN-§3',
    'GUIDE-EXECUTION-ROADMAP-§3',
    'GUIDE-SCENARIO-ROI-§3',
    'GUIDE-DATA-SPEC-§3',
    'GUIDE-MODEL-TRAINING-§3',
    'GUIDE-DEPLOYMENT-PLAN-§3',
    'GUIDE-MLOPS-RITUAL-§3',
  ];

  const app = document.getElementById('agent-app');
  if (!app) return;

  const form = document.getElementById('agent-form');
  const panels = Array.from(app.querySelectorAll('.agent-panel'));
  const indicators = Array.from(app.querySelectorAll('[data-step-indicator]'));
  const prevButton = document.getElementById('agent-prev');
  const nextButton = document.getElementById('agent-next');
  const resetButton = document.getElementById('agent-reset');
  const endpointInput = document.getElementById('agent-endpoint');
  const statusEl = document.getElementById('agent-status');
  const progressEl = document.getElementById('agent-progress');
  const partialsEl = document.getElementById('agent-partials');
  const resultEl = document.getElementById('agent-result');
  const auditMatrixEl = document.getElementById('agent-audit-matrix');
  const auditResultEl = document.getElementById('agent-audit-result');
  const copyButton = document.getElementById('agent-copy');
  const downloadButton = document.getElementById('agent-download');
  const copyAuditButton = document.getElementById('agent-copy-audit');
  const downloadAuditButton = document.getElementById('agent-download-audit');

  let currentStep = 1;
  let finalMarkdown = '';
  let auditMarkdown = '';
  let auditData = null;
  let templateContextPromise = null;

  function defaultEndpoint() {
    return app.dataset.agentEndpoint || '';
  }

  function templateIndexPath() {
    return app.dataset.templateIndexPath || '../data/templates_index.json';
  }

  function setStatus(message, tone) {
    statusEl.textContent = message;
    statusEl.dataset.tone = tone || 'neutral';
  }

  function setStep(step) {
    currentStep = Math.max(1, Math.min(5, step));
    panels.forEach(panel => panel.classList.toggle('is-active', Number(panel.dataset.step) === currentStep));
    indicators.forEach(item => {
      const itemStep = Number(item.dataset.stepIndicator);
      item.classList.toggle('is-active', itemStep === currentStep);
      item.classList.toggle('is-done', itemStep < currentStep);
    });
    prevButton.disabled = currentStep === 1;
    nextButton.style.display = currentStep === 5 ? 'none' : '';
    validateCurrentStep();
    saveState();
  }

  function fieldValue(field) {
    return (field.value || '').trim();
  }

  function requiredFieldsForStep(step) {
    return Array.from(app.querySelectorAll(`[data-step="${step}"] [data-required="true"]`));
  }

  function validateCurrentStep() {
    const missing = requiredFieldsForStep(currentStep).filter(field => !fieldValue(field));
    app.querySelectorAll('.agent-invalid').forEach(field => field.classList.remove('agent-invalid'));
    missing.forEach(field => field.classList.add('agent-invalid'));
    nextButton.disabled = missing.length > 0;
    return missing.length === 0;
  }

  function assignPath(target, path, value) {
    const parts = path.split('.');
    let cursor = target;
    parts.forEach((part, index) => {
      if (index === parts.length - 1) {
        cursor[part] = value;
        return;
      }
      cursor[part] = cursor[part] || {};
      cursor = cursor[part];
    });
  }

  function auditDetail(key, check) {
    if (!check) return '-';
    if (key === 'slot') return check.count ? `잔류 ${check.count}` : '잔류 없음';
    if (key === 'placeholder') return check.count ? `잔류 ${check.count}` : '잔류 없음';
    if (key === 'sectionHeaders') return check.missing && check.missing.length ? check.missing.join(', ') : '§1~§9';
    if (key === 'balance') return `ratio ${check.balance_ratio}`;
    if (key === 'cross') return `누출 ${check.total_leaks || 0}`;
    if (key === 'meta') return check.count ? `누출 ${check.count}` : '누출 없음';
    return check.pass ? '정상' : '점검 필요';
  }

  function renderAuditMatrix(audit) {
    auditMatrixEl.innerHTML = '';
    if (!audit || !audit.checks) return;
    const labels = {
      slot: '슬롯',
      placeholder: '표기',
      sectionHeaders: '섹션',
      balance: '균형',
      cross: '도메인',
      meta: '메타',
    };
    const table = document.createElement('table');
    table.innerHTML = '<thead><tr><th>축</th><th>결과</th><th>상세</th></tr></thead>';
    const tbody = document.createElement('tbody');
    Object.entries(audit.checks).forEach(([key, check]) => {
      const row = document.createElement('tr');
      row.dataset.pass = check.pass ? 'true' : 'false';
      const axis = document.createElement('td');
      axis.textContent = labels[key] || key;
      const result = document.createElement('td');
      result.textContent = check.pass ? 'PASS' : 'FAIL';
      const detail = document.createElement('td');
      detail.textContent = auditDetail(key, check);
      row.append(axis, result, detail);
      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    auditMatrixEl.appendChild(table);
  }

  function collectPayload(templateContext) {
    const profile = {};
    const fields = Array.from(form.querySelectorAll('[name]'));
    fields.forEach(field => {
      const value = fieldValue(field);
      if (!value || field.name === 'settings.endpoint') return;
      assignPath(profile, field.name, value);
    });
    const payload = { profile };
    if (templateContext && Object.keys(templateContext).length > 0) {
      payload.template_context = templateContext;
    }
    return payload;
  }

  async function loadTemplateContext() {
    if (!templateContextPromise) {
      templateContextPromise = fetch(templateIndexPath(), { cache: 'force-cache' })
        .then(response => {
          if (!response.ok) throw new Error(`templates_index.json HTTP ${response.status}`);
          return response.json();
        })
        .then(index => {
          const context = {};
          SECTION_CONTEXT_IDS.forEach(id => {
            if (index && index[id]) context[id] = index[id];
          });
          return context;
        })
        .catch(() => ({}));
    }
    return templateContextPromise;
  }

  function saveState() {
    const state = { currentStep, values: {} };
    Array.from(form.querySelectorAll('[name]')).forEach(field => {
      state.values[field.name] = field.value;
    });
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function restoreState() {
    endpointInput.value = defaultEndpoint();
    try {
      const state = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      Object.entries(state.values || {}).forEach(([name, value]) => {
        const field = form.querySelector(`[name="${CSS.escape(name)}"]`);
        if (field) field.value = value;
      });
      if (!endpointInput.value) endpointInput.value = defaultEndpoint();
      const last = JSON.parse(localStorage.getItem(RESULT_KEY) || '{}');
      if (last.final_md) {
        finalMarkdown = last.final_md;
        auditMarkdown = last.audit_md || '';
        auditData = last.audit || null;
        resultEl.value = finalMarkdown;
        auditResultEl.value = auditMarkdown;
        renderAuditMatrix(auditData);
        copyButton.disabled = false;
        downloadButton.disabled = false;
        copyAuditButton.disabled = !auditMarkdown;
        downloadAuditButton.disabled = !auditMarkdown;
      }
      setStep(Number(state.currentStep || 1));
    } catch {
      endpointInput.value = defaultEndpoint();
      setStep(1);
    }
  }

  function resetOutput() {
    finalMarkdown = '';
    auditMarkdown = '';
    auditData = null;
    progressEl.innerHTML = '';
    partialsEl.innerHTML = '';
    resultEl.value = '';
    auditMatrixEl.innerHTML = '';
    auditResultEl.value = '';
    copyButton.disabled = true;
    downloadButton.disabled = true;
    copyAuditButton.disabled = true;
    downloadAuditButton.disabled = true;
  }

  function upsertProgress(label, state) {
    const id = label.replace(/[^a-zA-Z0-9가-힝§]/g, '-');
    let item = progressEl.querySelector(`[data-progress-id="${CSS.escape(id)}"]`);
    if (!item) {
      item = document.createElement('div');
      item.className = 'agent-progress-item';
      item.dataset.progressId = id;
      progressEl.appendChild(item);
    }
    item.textContent = label;
    item.dataset.state = state;
  }

  function appendPartial(data) {
    const details = document.createElement('details');
    details.className = 'agent-partial';
    const summary = document.createElement('summary');
    summary.textContent = `${data.section} ${data.title || ''}`;
    const pre = document.createElement('pre');
    pre.textContent = data.markdown || '';
    details.append(summary, pre);
    partialsEl.appendChild(details);
  }

  function parseSse(buffer, onEvent) {
    const chunks = buffer.split('\n\n');
    const rest = chunks.pop() || '';
    chunks.forEach(chunk => {
      const event = chunk.split('\n').find(line => line.startsWith('event: '))?.slice(7);
      const data = chunk.split('\n').find(line => line.startsWith('data: '))?.slice(6);
      if (!event || !data) return;
      onEvent(event, JSON.parse(data));
    });
    return rest;
  }

  function handleEvent(event, data) {
    if (event === 'connected') {
      setStatus('연결됨', 'running');
      return;
    }
    if (event === 'stage_start') {
      upsertProgress(data.stage, 'running');
      return;
    }
    if (event === 'stage_done') {
      upsertProgress(data.stage, 'done');
      return;
    }
    if (event === 'section_start') {
      upsertProgress(data.section, 'running');
      return;
    }
    if (event === 'section_fallback') {
      upsertProgress(data.section, 'warning');
      return;
    }
    if (event === 'section_done') {
      upsertProgress(data.section, 'done');
      appendPartial(data);
      return;
    }
    if (event === 'validation') {
      upsertProgress('validation', 'done');
      return;
    }
    if (event === 'complete') {
      finalMarkdown = data.final_md || '';
      auditMarkdown = data.audit_md || '';
      auditData = data.audit || null;
      resultEl.value = finalMarkdown;
      auditResultEl.value = auditMarkdown;
      renderAuditMatrix(auditData);
      copyButton.disabled = !finalMarkdown;
      downloadButton.disabled = !finalMarkdown;
      copyAuditButton.disabled = !auditMarkdown;
      downloadAuditButton.disabled = !auditMarkdown;
      localStorage.setItem(RESULT_KEY, JSON.stringify(data));
      setStatus('완료', 'done');
      return;
    }
    if (event === 'error') {
      setStatus(data.message || '오류', 'error');
    }
  }

  async function streamAgent() {
    if (![1, 2, 3, 4].every(step => requiredFieldsForStep(step).every(field => fieldValue(field)))) {
      setStatus('필수 입력을 확인하세요.', 'error');
      return;
    }
    resetOutput();
    setStatus('컨텍스트 로딩 중', 'running');
    const payload = collectPayload(await loadTemplateContext());
    setStatus('요청 중', 'running');
    const endpoint = fieldValue(endpointInput) || defaultEndpoint();
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: response.statusText }));
      setStatus(error.error || '요청 실패', 'error');
      return;
    }
    if (!response.body) {
      setStatus('브라우저가 스트림 응답을 지원하지 않습니다.', 'error');
      return;
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      buffer = parseSse(buffer, handleEvent);
    }
  }

  form.addEventListener('input', () => {
    validateCurrentStep();
    saveState();
  });

  nextButton.addEventListener('click', () => {
    if (validateCurrentStep()) setStep(currentStep + 1);
  });

  prevButton.addEventListener('click', () => setStep(currentStep - 1));

  form.addEventListener('submit', event => {
    event.preventDefault();
    streamAgent().catch(error => setStatus(error.message, 'error'));
  });

  resetButton.addEventListener('click', () => {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(RESULT_KEY);
    form.reset();
    endpointInput.value = defaultEndpoint();
    resetOutput();
    setStep(1);
    setStatus('대기 중');
  });

  copyButton.addEventListener('click', async () => {
    await navigator.clipboard.writeText(finalMarkdown);
    setStatus('복사됨', 'done');
  });

  copyAuditButton.addEventListener('click', async () => {
    await navigator.clipboard.writeText(auditMarkdown);
    setStatus('검토 리포트 복사됨', 'done');
  });

  downloadButton.addEventListener('click', () => {
    const blob = new Blob([finalMarkdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'agent-business-plan.md';
    a.click();
    URL.revokeObjectURL(url);
  });

  downloadAuditButton.addEventListener('click', () => {
    const blob = new Blob([auditMarkdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'agent-generation-audit.md';
    a.click();
    URL.revokeObjectURL(url);
  });

  restoreState();
})();
