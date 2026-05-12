import assert from 'node:assert/strict';
import { beforeEach, describe, it } from 'node:test';

import '../docs/javascripts/llm-client.js';

describe('AiDocsLLM client', () => {
  beforeEach(() => {
    globalThis.localStorage = {
      store: new Map(),
      getItem(key) { return this.store.get(key) || null; },
      setItem(key, value) { this.store.set(key, String(value)); },
      removeItem(key) { this.store.delete(key); },
    };
  });

  it('prefers endpoint from the form dataset', () => {
    const form = { dataset: { llmEndpoint: 'https://worker.example/api/llm' } };

    assert.equal(globalThis.AiDocsLLM.getEndpoint(form), 'https://worker.example/api/llm');
  });

  it('saves and reloads an endpoint from localStorage', () => {
    globalThis.AiDocsLLM.saveEndpoint(' https://worker.example/api/llm ');

    assert.equal(globalThis.AiDocsLLM.getEndpoint({ dataset: {} }), 'https://worker.example/api/llm');
  });

  it('throws a clear error when endpoint is missing', async () => {
    await assert.rejects(
      globalThis.AiDocsLLM.call({ endpoint: '', mode: 'polish', text: '본문' }),
      /LLM Worker endpoint is not configured/,
    );
  });

  it('posts polish requests to the Worker and returns text/model/usage', async () => {
    let fetchUrl = '';
    let fetchInit = {};
    const result = await globalThis.AiDocsLLM.call({
      endpoint: 'https://worker.example/api/llm',
      mode: 'polish',
      text: '본문',
      inputs: { 고객사: '동국제강' },
      metadata: { selectedIds: ['BLK-T1-3.1'] },
      fetchImpl: async (url, init) => {
        fetchUrl = url;
        fetchInit = init;
        return Response.json({
          text: '다듬어진 본문',
          model: 'gemini-2.5-flash',
          usage: { promptTokenCount: 1 },
        });
      },
    });

    assert.equal(fetchUrl, 'https://worker.example/api/llm');
    assert.equal(fetchInit.method, 'POST');
    assert.equal(fetchInit.headers['Content-Type'], 'application/json');
    assert.deepEqual(JSON.parse(fetchInit.body), {
      mode: 'polish',
      text: '본문',
      inputs: { 고객사: '동국제강' },
      metadata: { selectedIds: ['BLK-T1-3.1'] },
    });
    assert.deepEqual(result, {
      text: '다듬어진 본문',
      model: 'gemini-2.5-flash',
      usage: { promptTokenCount: 1 },
    });
  });

  it('throws Worker error details when the response is not ok', async () => {
    await assert.rejects(
      globalThis.AiDocsLLM.call({
        endpoint: 'https://worker.example/api/llm',
        mode: 'polish',
        text: '본문',
        fetchImpl: async () => Response.json({ error: 'payload_too_large', maxChars: 12000 }, { status: 413 }),
      }),
      /payload_too_large/,
    );
  });
});
