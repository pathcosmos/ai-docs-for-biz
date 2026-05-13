(function () {
  const STORAGE_KEY = 'ai_docs_assemble_state_v1';
  const FAVORITES_KEY = 'ai_docs_assemble_favorites_v1';
  const RESULT_KEY = 'ai_docs_assemble_last_result_v1';
  const SECTION_IDS = ['§1', '§2', '§3', '§4', '§5', '§6', '§7', '§8', '§9'];
  const QUANT_SLOT_KEYS = [
    'veteran_count',
    'variable_count',
    'experience_years',
    'spec_variance_pct',
    'pdf_form_count',
    'human_entry_minutes',
    'human_error_pct',
    'retention_period',
    'kpi_quality_pct',
    'kpi_productivity_pct',
    'kpi_anomaly_accuracy_pct',
    'kpi_fp_pct',
    'kpi_fn_pct',
    'total_budget_eok',
    'govt_ratio_pct',
    'private_ratio_pct',
    'trl_start',
    'trl_target',
    'duration_months',
    'ml_drift_psi_warn',
    'ml_drift_psi_retrain',
    'edge_latency_ms',
    'hmi_latency_s',
    'rag_latency_s',
    'service_sla_pct',
  ];
  const PLACEHOLDER_DEFAULT_FIELDS = new Set([
    'step1_company.company',
    'step1_company.process',
    'step2_business.duration_months',
    'step2_business.total_budget',
    'step2_business.gov_pct',
  ]);
  const CATEGORY_LABELS = {
    track: '트랙',
    guide: '가이드',
    scenario: '시나리오',
    module: '모듈',
    package: '패키지',
    block: '블록',
  };

  const DOMAINS = [
    { id: 'STL', label: '철강·냉연', process: '냉간압연·연속소둔', scale: '중견' },
    { id: 'MET', label: '정밀가공', process: '정밀가공·절삭', scale: '중소' },
    { id: 'RUB', label: '고무·폴리머', process: '고무 배합·가황', scale: '중견' },
    { id: 'UTL', label: '유틸·환경', process: '에너지·환경 관리', scale: '중견' },
    { id: 'LLM', label: 'LLM·RAG', process: '작업표준 RAG', scale: '중견' },
    { id: 'CAS', label: '연속주조', process: '연속주조·중력주조', scale: '대기업' },
    { id: 'HEA', label: '열처리', process: '가열로·QT', scale: '중견' },
    { id: 'PLT', label: '도금·표면', process: '도금·도장', scale: '중소' },
    { id: 'SHP', label: '조선·해양', process: '블록·의장·용접', scale: '대기업' },
    { id: 'ASM', label: '자동차 조립', process: '체결·검사 라인', scale: '중견' },
  ];

  function defaultState() {
    return {
      currentStep: 1,
      domain: '',
      scenarios: [],
      selectedBlocks: [],
      sectionAssignment: {},
      slots: {
        step1_company: {},
        step2_business: {},
        quant: {},
      },
      activeBlock: '',
    };
  }

  function normalizeSection(value) {
    if (!value) return null;
    const match = String(value).match(/§\s*(\d+)/);
    if (!match) return null;
    const number = Number.parseInt(match[1], 10);
    if (number === 0) return '§1';
    if (number === 10) return '§4';
    if (number >= 1 && number <= 9) return `§${number}`;
    return null;
  }

  function assignBlocksToSections(blockIds, templateIndex, existingAssignment) {
    const selected = new Set(blockIds || []);
    const result = {};
    if (existingAssignment && typeof existingAssignment === 'object') {
      Object.entries(existingAssignment).forEach(([rawSection, ids]) => {
        const section = normalizeSection(rawSection);
        if (!section || !Array.isArray(ids)) return;
        ids.forEach(id => {
          if (!selected.has(id)) return;
          result[section] = result[section] || [];
          if (!result[section].includes(id)) result[section].push(id);
        });
      });
    }
    (blockIds || []).forEach(id => {
      if (Object.values(result).some(ids => ids.includes(id))) return;
      const section = normalizeSection(templateIndex && templateIndex[id] && templateIndex[id].section);
      if (!section) return;
      result[section] = result[section] || [];
      result[section].push(id);
    });
    return result;
  }

  function buildPayload(state, fullTemplates) {
    const blockContext = {};
    (state.selectedBlocks || []).forEach(id => {
      const source = fullTemplates && fullTemplates[id];
      if (!source) return;
      blockContext[id] = {
        title: source.title || '',
        category: source.category || '',
        section: source.section || '',
        body: source.body || '',
      };
    });
    return {
      domain: state.domain,
      scenarios: state.scenarios || [],
      blocks: state.selectedBlocks || [],
      section_assignment: state.sectionAssignment || {},
      slots: state.slots || {},
      block_context: blockContext,
      mode: 'deterministic',
    };
  }

  function trimValue(value) {
    return value == null ? '' : String(value).trim();
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

  function fieldSlotValue(field) {
    const explicitValue = trimValue(field && field.value);
    if (explicitValue) return explicitValue;
    if (field && PLACEHOLDER_DEFAULT_FIELDS.has(field.name)) return trimValue(field.placeholder);
    return '';
  }

  function collectSlotsFromFields(fields, currentDomain) {
    const slots = {
      step1_company: {},
      step2_business: {},
      quant: {},
    };
    Array.from(fields || []).forEach(field => {
      if (!field || !field.name) return;
      const value = fieldSlotValue(field);
      if (!value) return;
      if (field.name.startsWith('quant.')) {
        slots.quant[field.name.replace('quant.', '')] = value;
        return;
      }
      assignPath(slots, field.name, value);
    });
    if (!slots.step1_company.industry && currentDomain) slots.step1_company.industry = currentDomain;
    return {
      domain: slots.step1_company.industry || currentDomain || '',
      slots,
    };
  }

  function restoreState(storage) {
    const target = storage || (typeof localStorage !== 'undefined' ? localStorage : null);
    if (!target) return defaultState();
    try {
      const parsed = JSON.parse(target.getItem(STORAGE_KEY) || '{}');
      return { ...defaultState(), ...parsed };
    } catch {
      return defaultState();
    }
  }

  function loadFavorites(storage) {
    const target = storage || (typeof localStorage !== 'undefined' ? localStorage : null);
    if (!target) return [];
    try {
      const parsed = JSON.parse(target.getItem(FAVORITES_KEY) || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function saveJson(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* localStorage can be unavailable in private contexts. */
    }
  }

  function text(value) {
    return value === undefined || value === null ? '' : String(value);
  }

  function clear(node) {
    if (!node) return;
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function button(label, className, onClick) {
    const item = document.createElement('button');
    item.type = 'button';
    item.textContent = label;
    if (className) item.className = className;
    item.addEventListener('click', onClick);
    return item;
  }

  function badge(label) {
    const item = document.createElement('span');
    item.className = 'assemble-badge';
    item.textContent = label;
    return item;
  }

  function categoryLabel(value) {
    return CATEGORY_LABELS[value] || value || '블록';
  }

  function scenarioDomain(id) {
    const match = String(id || '').match(/^SCN-([A-Z]+)-/);
    return match ? match[1] : '';
  }

  function stripInternalIds(value) {
    return text(value)
      .replace(/\b(?:SCN|BLK|TEST)-[A-Z0-9_.§-]+/g, '')
      .replace(/\b(?:GUIDE|MODULE|PKG|TRACK)-[A-Z0-9_.§-]+/g, '')
      .replace(/\s{2,}/g, ' ')
      .replace(/^[\s:·—-]+|[\s:·—-]+$/g, '')
      .trim();
  }

  function scenarioTitle(item) {
    const cleanTitle = stripInternalIds(item && (item.title || item.name));
    if (cleanTitle) return cleanTitle;
    const card = (item && item.card) || {};
    return stripInternalIds(card['AI 해결'] || card['대상 공정']) || '시나리오';
  }

  function scenarioCardsForDomain(scenarios, domain) {
    const cross = new Set(['MLO', 'LLM', 'SAF']);
    return (scenarios || []).filter(item => {
      const prefix = scenarioDomain(item.id);
      return prefix === domain || cross.has(prefix);
    });
  }

  function blockTitle(id, index) {
    const entry = index && index[id];
    const cleanTitle = stripInternalIds(entry && entry.title);
    if (cleanTitle) return cleanTitle;
    return entry && entry.category ? `${categoryLabel(entry.category)} 블록` : '선택 블록';
  }

  function recommendedBlockIds(state, scenarioMap) {
    const ids = [];
    (state.scenarios || []).forEach(scenarioId => {
      const mapped = scenarioMap && scenarioMap[scenarioId];
      if (!Array.isArray(mapped)) return;
      mapped.forEach(item => {
        const id = typeof item === 'string' ? item : item.id;
        if (id && !ids.includes(id)) ids.push(id);
      });
    });
    return ids;
  }

  function initApp() {
    const app = document.getElementById('assemble-app');
    if (!app || app.dataset.initialized === 'true') return;
    app.dataset.initialized = 'true';

    const els = {
      panels: Array.from(app.querySelectorAll('[data-assemble-step-panel]')),
      indicators: Array.from(app.querySelectorAll('[data-assemble-step]')),
      domainGrid: document.getElementById('assemble-domain-grid'),
      scenarioList: document.getElementById('assemble-scenario-list'),
      catalog: document.getElementById('assemble-catalog'),
      cart: document.getElementById('assemble-cart'),
      sections: document.getElementById('assemble-sections'),
      search: document.getElementById('assemble-search'),
      status: document.getElementById('assemble-status'),
      result: document.getElementById('assemble-result'),
      audit: document.getElementById('assemble-audit'),
      auditMatrix: document.getElementById('assemble-audit-matrix'),
      prev: document.getElementById('assemble-prev'),
      next: document.getElementById('assemble-next'),
      submit: document.getElementById('assemble-submit'),
      reset: document.getElementById('assemble-reset'),
      copy: document.getElementById('assemble-copy'),
      download: document.getElementById('assemble-download'),
      endpoint: document.getElementById('assemble-endpoint'),
      form: document.getElementById('assemble-fields'),
      quant: document.getElementById('assemble-quant-fields'),
    };

    const requiredElements = [
      'domainGrid',
      'scenarioList',
      'catalog',
      'cart',
      'sections',
      'search',
      'status',
      'result',
      'audit',
      'auditMatrix',
      'prev',
      'next',
      'submit',
      'reset',
      'copy',
      'download',
      'endpoint',
      'form',
      'quant',
    ];
    const missingElements = requiredElements.filter(key => !els[key]);
    if (missingElements.length > 0) {
      const message = `조립형 작성기 DOM 오류: ${missingElements.join(', ')}`;
      app.dataset.assembleError = 'missing-elements';
      app.replaceChildren();
      const error = document.createElement('div');
      error.className = 'assemble-status';
      error.dataset.tone = 'error';
      error.textContent = message;
      app.appendChild(error);
      return;
    }

    let state = restoreState();
    let favorites = loadFavorites();
    let scenarioIndex = [];
    let scenarioMap = {};
    let templatesIndex = {};
    let fullTemplatesPromise = null;
    let finalMarkdown = '';
    let highlightedBlock = '';
    let highlightTimer = null;

    function scenarioIndexPath() {
      return app.dataset.scenarioIndexPath || '../data/scenario_index.json';
    }

    function scenarioMapPath() {
      return app.dataset.scenarioMapPath || '../data/scenario_block_map.json';
    }

    function templateIndexPath() {
      return app.dataset.templateIndexPath || '../data/templates_index.json';
    }

    function templatesPath() {
      return app.dataset.templatesPath || '../data/templates.json';
    }

    function endpoint() {
      return (els.endpoint && els.endpoint.value.trim()) || app.dataset.assembleEndpoint || '';
    }

    function setStatus(message, tone) {
      if (!els.status) return;
      els.status.textContent = message;
      els.status.dataset.tone = tone || 'neutral';
    }

    function saveState() {
      saveJson(STORAGE_KEY, state);
      saveJson(FAVORITES_KEY, favorites);
    }

    function setStep(step) {
      state.currentStep = Math.max(1, Math.min(4, step));
      els.panels.forEach(panel => {
        panel.hidden = Number(panel.dataset.assembleStepPanel) !== state.currentStep;
      });
      els.indicators.forEach(item => {
        const itemStep = Number(item.dataset.assembleStep);
        item.classList.toggle('is-active', itemStep === state.currentStep);
        item.classList.toggle('is-done', itemStep < state.currentStep);
      });
      if (els.prev) els.prev.disabled = state.currentStep === 1;
      if (els.next) els.next.hidden = state.currentStep === 4;
      if (els.submit) els.submit.hidden = state.currentStep !== 4;
      saveState();
    }

    function syncCompanyDefaults(domain) {
      const info = DOMAINS.find(item => item.id === domain);
      state.slots.step1_company = {
        ...(state.slots.step1_company || {}),
        industry: domain,
        process: state.slots.step1_company?.process || (info && info.process) || '',
        scale: state.slots.step1_company?.scale || (info && info.scale) || '중견',
      };
    }

    function renderDomains() {
      clear(els.domainGrid);
      DOMAINS.forEach(info => {
        const card = document.createElement('button');
        card.type = 'button';
        card.className = 'assemble-domain-card';
        card.dataset.selected = state.domain === info.id ? 'true' : 'false';
        const code = document.createElement('span');
        code.className = 'assemble-domain-code';
        code.textContent = info.id;
        const label = document.createElement('strong');
        label.textContent = info.label;
        const process = document.createElement('span');
        process.textContent = info.process;
        card.append(code, label, process);
        card.addEventListener('click', () => {
          state.domain = info.id;
          state.scenarios = [];
          syncCompanyDefaults(info.id);
          saveState();
          render();
          setStep(2);
        });
        els.domainGrid.appendChild(card);
      });
    }

    function renderScenarios() {
      clear(els.scenarioList);
      const list = scenarioCardsForDomain(scenarioIndex, state.domain);
      list.forEach(item => {
        const id = item.id;
        const card = document.createElement('label');
        card.className = 'assemble-scenario-card';
        card.dataset.selected = state.scenarios.includes(id) ? 'true' : 'false';
        const input = document.createElement('input');
        input.type = 'checkbox';
        input.checked = state.scenarios.includes(id);
        input.addEventListener('change', () => {
          if (input.checked && !state.scenarios.includes(id)) state.scenarios.push(id);
          if (!input.checked) state.scenarios = state.scenarios.filter(value => value !== id);
          const autoBlocks = recommendedBlockIds(state, scenarioMap).slice(0, 12);
          autoBlocks.forEach(blockId => {
            if (!state.selectedBlocks.includes(blockId)) state.selectedBlocks.push(blockId);
          });
          state.sectionAssignment = assignBlocksToSections(state.selectedBlocks, templatesIndex, state.sectionAssignment);
          saveState();
          render();
        });
        const body = document.createElement('span');
        body.className = 'assemble-scenario-body';
        const title = document.createElement('strong');
        title.textContent = scenarioTitle(item);
        const meta = document.createElement('span');
        const cardData = item.card || {};
        meta.textContent = [cardData['대상 공정'], cardData['트랙 매핑'], cardData['적합 규모']]
          .filter(Boolean)
          .join(' · ');
        body.append(title, meta);
        card.append(input, body);
        els.scenarioList.appendChild(card);
      });
    }

    function addBlock(id, section) {
      if (!id) return;
      if (!state.selectedBlocks.includes(id)) state.selectedBlocks.push(id);
      const targetSection = section || normalizeSection(templatesIndex[id]?.section);
      state.sectionAssignment = assignBlocksToSections(state.selectedBlocks, templatesIndex, state.sectionAssignment);
      if (targetSection) {
        Object.keys(state.sectionAssignment).forEach(key => {
          state.sectionAssignment[key] = state.sectionAssignment[key].filter(value => value !== id);
          if (state.sectionAssignment[key].length === 0) delete state.sectionAssignment[key];
        });
        state.sectionAssignment[targetSection] = state.sectionAssignment[targetSection] || [];
        state.sectionAssignment[targetSection].push(id);
      }
      state.activeBlock = id;
      highlightedBlock = id;
      saveState();
      renderStepThree();
      if (highlightTimer) clearTimeout(highlightTimer);
      highlightTimer = setTimeout(() => {
        if (highlightedBlock !== id) return;
        highlightedBlock = '';
        renderStepThree();
      }, 1600);
    }

    function removeBlock(id) {
      state.selectedBlocks = state.selectedBlocks.filter(value => value !== id);
      Object.keys(state.sectionAssignment).forEach(section => {
        state.sectionAssignment[section] = state.sectionAssignment[section].filter(value => value !== id);
        if (state.sectionAssignment[section].length === 0) delete state.sectionAssignment[section];
      });
      if (state.activeBlock === id) state.activeBlock = '';
      if (highlightedBlock === id) highlightedBlock = '';
      saveState();
      renderStepThree();
    }

    function toggleFavorite(id) {
      if (favorites.includes(id)) {
        favorites = favorites.filter(value => value !== id);
      } else {
        favorites.push(id);
      }
      saveState();
      renderStepThree();
    }

    function renderCatalog() {
      clear(els.catalog);
      const recommended = recommendedBlockIds(state, scenarioMap);
      const sourceIds = recommended.length > 0 ? recommended : Object.keys(templatesIndex);
      const query = (els.search && els.search.value.trim().toLowerCase()) || '';
      sourceIds
        .filter(id => templatesIndex[id])
        .filter(id => {
          if (!query) return true;
          const item = templatesIndex[id];
          return `${id} ${item.title || ''} ${item.preview || ''} ${(item.tags || []).join(' ')}`.toLowerCase().includes(query);
        })
        .slice(0, 80)
        .forEach(id => {
          const item = templatesIndex[id];
          const row = document.createElement('article');
          row.className = 'assemble-block-row';
          row.draggable = true;
          row.dataset.active = state.activeBlock === id ? 'true' : 'false';
          row.dataset.selected = state.selectedBlocks.includes(id) ? 'true' : 'false';
          row.dataset.flash = highlightedBlock === id ? 'true' : 'false';
          row.addEventListener('dragstart', event => event.dataTransfer.setData('text/plain', id));
          row.addEventListener('click', event => {
            if (event.target.closest('button')) return;
            addBlock(id);
          });
          const title = document.createElement('button');
          title.type = 'button';
          title.className = 'assemble-block-title';
          title.textContent = blockTitle(id, templatesIndex);
          title.addEventListener('click', () => addBlock(id));
          const meta = document.createElement('div');
          meta.className = 'assemble-block-meta';
          meta.append(badge(categoryLabel(item.category || 'block')), badge(normalizeSection(item.section) || '미배치'));
          if (favorites.includes(id)) meta.append(badge('즐겨찾기'));
          const preview = document.createElement('p');
          preview.textContent = stripInternalIds(item.preview || '');
          const actions = document.createElement('div');
          actions.className = 'assemble-inline-actions';
          actions.append(
            button(state.selectedBlocks.includes(id) ? '선택됨' : '담기', '', () => addBlock(id)),
            button(favorites.includes(id) ? '즐겨찾기 해제' : '즐겨찾기', '', () => toggleFavorite(id)),
          );
          row.append(title, meta, preview, actions);
          els.catalog.appendChild(row);
        });
    }

    function renderCart() {
      clear(els.cart);
      if (state.activeBlock) {
        const active = document.createElement('div');
        active.className = 'assemble-active-map';
        active.dataset.selected = state.selectedBlocks.includes(state.activeBlock) ? 'true' : 'false';
        active.dataset.flash = highlightedBlock === state.activeBlock ? 'true' : 'false';
        active.append(
          badge('현재 선택'),
          badge(normalizeSection(templatesIndex[state.activeBlock]?.section) || '미배치'),
        );
        const title = document.createElement('strong');
        title.textContent = blockTitle(state.activeBlock, templatesIndex);
        active.appendChild(title);
        els.cart.appendChild(active);
      }
      state.selectedBlocks.forEach(id => {
        const item = document.createElement('div');
        item.className = 'assemble-cart-item';
        item.dataset.active = state.activeBlock === id ? 'true' : 'false';
        item.dataset.flash = highlightedBlock === id ? 'true' : 'false';
        item.append(badge(normalizeSection(templatesIndex[id]?.section) || '미배치'));
        const title = document.createElement('span');
        title.textContent = blockTitle(id, templatesIndex);
        item.append(title, button('제거', '', () => removeBlock(id)));
        els.cart.appendChild(item);
      });
    }

    function moveBlockToSection(id, section) {
      if (!id) return;
      addBlock(id, section);
    }

    function renderSections() {
      clear(els.sections);
      SECTION_IDS.forEach(section => {
        const box = document.createElement('section');
        box.className = 'assemble-section-slot';
        box.dataset.active = (state.sectionAssignment[section] || []).includes(state.activeBlock) ? 'true' : 'false';
        box.addEventListener('dragover', event => event.preventDefault());
        box.addEventListener('drop', event => {
          event.preventDefault();
          moveBlockToSection(event.dataTransfer.getData('text/plain'), section);
        });
        const header = document.createElement('header');
        const title = document.createElement('strong');
        title.textContent = section;
        header.append(title);
        if (state.activeBlock) {
          header.append(button('선택 블록 추가', '', () => moveBlockToSection(state.activeBlock, section)));
        }
        const list = document.createElement('div');
        list.className = 'assemble-section-blocks';
        (state.sectionAssignment[section] || []).forEach(id => {
          const pill = document.createElement('span');
          pill.className = 'assemble-section-pill';
          pill.dataset.active = state.activeBlock === id ? 'true' : 'false';
          pill.dataset.flash = highlightedBlock === id ? 'true' : 'false';
          pill.textContent = blockTitle(id, templatesIndex);
          pill.append(button('×', 'assemble-icon-button', () => removeBlock(id)));
          list.appendChild(pill);
        });
        box.append(header, list);
        els.sections.appendChild(box);
      });
    }

    function renderStepThree() {
      renderCatalog();
      renderCart();
      renderSections();
    }

    function renderQuantFields() {
      if (!els.quant || els.quant.dataset.rendered === 'true') return;
      els.quant.dataset.rendered = 'true';
      QUANT_SLOT_KEYS.forEach(key => {
        const label = document.createElement('label');
        label.textContent = key;
        const input = document.createElement('input');
        input.name = `quant.${key}`;
        input.placeholder = key;
        label.appendChild(input);
        els.quant.appendChild(label);
      });
    }

    function restoreFormValues() {
      if (!els.form) return;
      const flat = {
        'step1_company.company': state.slots.step1_company?.company || '',
        'step1_company.industry': state.domain || state.slots.step1_company?.industry || '',
        'step1_company.process': state.slots.step1_company?.process || '',
        'step1_company.scale': state.slots.step1_company?.scale || '',
        'step2_business.duration_months': state.slots.step2_business?.duration_months || '',
        'step2_business.total_budget': state.slots.step2_business?.total_budget || '',
        'step2_business.gov_pct': state.slots.step2_business?.gov_pct || '',
      };
      Object.entries(state.slots.quant || {}).forEach(([key, value]) => {
        flat[`quant.${key}`] = value;
      });
      Array.from(els.form.querySelectorAll('[name]')).forEach(field => {
        if (flat[field.name] !== undefined) field.value = flat[field.name];
      });
      if (els.endpoint) els.endpoint.value = app.dataset.assembleEndpoint || '';
    }

    function collectFormSlots() {
      const collected = collectSlotsFromFields(els.form ? els.form.querySelectorAll('[name]') : [], state.domain);
      state.domain = collected.domain || state.domain;
      state.slots = collected.slots;
      Object.assign(state.slots, collected.slots.quant);
      saveState();
    }

    function renderAudit(audit) {
      clear(els.auditMatrix);
      if (!audit || !audit.checks) return;
      const table = document.createElement('table');
      table.innerHTML = '<thead><tr><th>축</th><th>결과</th></tr></thead>';
      const tbody = document.createElement('tbody');
      Object.entries(audit.checks).forEach(([key, check]) => {
        const row = document.createElement('tr');
        row.dataset.pass = check.pass ? 'true' : 'false';
        const axis = document.createElement('td');
        axis.textContent = key;
        const result = document.createElement('td');
        result.textContent = check.pass ? 'PASS' : 'FAIL';
        row.append(axis, result);
        tbody.appendChild(row);
      });
      table.appendChild(tbody);
      els.auditMatrix.appendChild(table);
    }

    async function loadFullTemplates() {
      if (!fullTemplatesPromise) {
        fullTemplatesPromise = fetch(templatesPath(), { cache: 'force-cache' }).then(response => {
          if (!response.ok) throw new Error(`templates.json HTTP ${response.status}`);
          return response.json();
        });
      }
      return fullTemplatesPromise;
    }

    async function assemble() {
      collectFormSlots();
      if (!state.domain || state.scenarios.length === 0) {
        setStatus('도메인과 시나리오를 확인하세요.', 'error');
        return;
      }
      if (!endpoint()) {
        setStatus('Worker endpoint 를 확인하세요.', 'error');
        return;
      }
      setStatus('본문 조립 중', 'running');
      const fullTemplates = await loadFullTemplates();
      const payload = buildPayload(state, fullTemplates);
      const response = await fetch(endpoint(), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setStatus(data.error || '요청 실패', 'error');
        return;
      }
      finalMarkdown = data.final_md || '';
      if (els.result) els.result.value = finalMarkdown;
      if (els.audit) els.audit.value = data.audit_md || '';
      renderAudit(data.audit);
      saveJson(RESULT_KEY, data);
      if (els.copy) els.copy.disabled = !finalMarkdown;
      if (els.download) els.download.disabled = !finalMarkdown;
      setStatus(data.audit && data.audit.passed ? 'Audit PASS' : 'Audit 확인 필요', data.audit && data.audit.passed ? 'done' : 'warning');
    }

    function restoreLastResult() {
      try {
        const data = JSON.parse(localStorage.getItem(RESULT_KEY) || '{}');
        if (!data.final_md) return;
        finalMarkdown = data.final_md;
        if (els.result) els.result.value = data.final_md;
        if (els.audit) els.audit.value = data.audit_md || '';
        renderAudit(data.audit);
        if (els.copy) els.copy.disabled = false;
        if (els.download) els.download.disabled = false;
      } catch {
        /* Ignore stale result state. */
      }
    }

    function render() {
      renderDomains();
      renderScenarios();
      renderStepThree();
      renderQuantFields();
      restoreFormValues();
      setStep(state.currentStep || 1);
    }

    async function loadData() {
      setStatus('데이터 로딩 중', 'running');
      const [scenarios, mapped, index] = await Promise.all([
        fetch(scenarioIndexPath(), { cache: 'force-cache' }).then(response => response.json()),
        fetch(scenarioMapPath(), { cache: 'force-cache' }).then(response => response.json()),
        fetch(templateIndexPath(), { cache: 'force-cache' }).then(response => response.json()),
      ]);
      scenarioIndex = Array.isArray(scenarios) ? scenarios : scenarios.scenarios || [];
      scenarioMap = mapped || {};
      templatesIndex = index || {};
      state.sectionAssignment = assignBlocksToSections(state.selectedBlocks, templatesIndex, state.sectionAssignment);
      render();
      restoreLastResult();
      setStatus('대기 중', 'neutral');
    }

    if (els.search) els.search.addEventListener('input', renderCatalog);
    if (els.prev) els.prev.addEventListener('click', () => setStep(state.currentStep - 1));
    if (els.next) els.next.addEventListener('click', () => setStep(state.currentStep + 1));
    if (els.submit) els.submit.addEventListener('click', () => assemble().catch(error => setStatus(error.message, 'error')));
    if (els.form) els.form.addEventListener('input', () => {
      collectFormSlots();
      restoreFormValues();
    });
    if (els.reset) els.reset.addEventListener('click', () => {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(RESULT_KEY);
      state = defaultState();
      finalMarkdown = '';
      if (els.form) els.form.reset();
      if (els.result) els.result.value = '';
      if (els.audit) els.audit.value = '';
      clear(els.auditMatrix);
      render();
      setStatus('초기화됨', 'neutral');
    });
    if (els.copy) els.copy.addEventListener('click', async () => {
      await navigator.clipboard.writeText(finalMarkdown);
      setStatus('복사됨', 'done');
    });
    if (els.download) els.download.addEventListener('click', () => {
      const blob = new Blob([finalMarkdown], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'assembled-business-plan.md';
      a.click();
      URL.revokeObjectURL(url);
    });

    loadData().catch(error => setStatus(error.message, 'error'));
  }

  globalThis.AiDocsAssemble = {
    STORAGE_KEY,
    FAVORITES_KEY,
    QUANT_SLOT_KEYS,
    SECTION_IDS,
    DOMAINS,
    defaultState,
    normalizeSection,
    assignBlocksToSections,
    buildPayload,
    collectSlotsFromFields,
    restoreState,
    loadFavorites,
    stripInternalIds,
    scenarioTitle,
    blockTitle,
  };

  if (typeof document$ !== 'undefined' && document$ && typeof document$.subscribe === 'function') {
    document$.subscribe(initApp);
  } else if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initApp);
    } else {
      initApp();
    }
  }
})();
