(function initAiDocsLLM(global) {
  const ENDPOINT_STORAGE_KEY = 'ai_docs_llm_endpoint';

  function storage() {
    try {
      return global.localStorage || null;
    } catch {
      return null;
    }
  }

  function normalizeEndpoint(endpoint) {
    return (endpoint || '').trim().replace(/\/+$/, '');
  }

  function getEndpoint(form) {
    const saved = storage()?.getItem(ENDPOINT_STORAGE_KEY) || '';
    const configured = form?.dataset?.llmEndpoint || global.AI_DOCS_LLM_ENDPOINT || '';
    return normalizeEndpoint(saved || configured);
  }

  function saveEndpoint(endpoint) {
    const normalized = normalizeEndpoint(endpoint);
    if (normalized) storage()?.setItem(ENDPOINT_STORAGE_KEY, normalized);
    else storage()?.removeItem(ENDPOINT_STORAGE_KEY);
    return normalized;
  }

  async function call({ endpoint, mode, text, inputs = {}, metadata = {}, fetchImpl = global.fetch }) {
    const target = normalizeEndpoint(endpoint);
    if (!target) throw new Error('LLM Worker endpoint is not configured');
    if (!fetchImpl) throw new Error('fetch is not available');

    const response = await fetchImpl(target, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode, text, inputs, metadata }),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = data.message || data.detail || data.error || response.statusText || `HTTP ${response.status}`;
      throw new Error(detail);
    }
    if (!data.text) throw new Error('LLM Worker response did not include text');
    return {
      text: data.text,
      model: data.model || '',
      usage: data.usage || null,
    };
  }

  global.AiDocsLLM = {
    getEndpoint,
    saveEndpoint,
    call,
  };
})(globalThis);
