import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import { handleRequest } from '../src/index.js';

const env = {
  GEMINI_API_KEY: 'test-gemini-key',
  CF_ACCOUNT_ID: 'account-123',
  CF_GATEWAY_ID: 'gateway-abc',
  GEMINI_MODEL: 'gemini-2.5-flash',
  ALLOWED_ORIGINS: 'https://pathcosmos.github.io,http://127.0.0.1:8000,http://localhost:8000',
};

function request(body, init = {}) {
  return new Request('https://worker.example.com/api/llm', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      origin: 'https://pathcosmos.github.io',
      ...(init.headers || {}),
    },
    body: JSON.stringify(body),
  });
}

describe('handleRequest', () => {
  it('rejects requests from origins outside the allowlist', async () => {
    const response = await handleRequest(
      request({ mode: 'polish', text: '본문' }, { headers: { origin: 'https://evil.example' } }),
      env,
      async () => {
        throw new Error('fetch should not be called');
      },
    );

    assert.equal(response.status, 403);
    assert.equal(await response.text(), 'Origin not allowed');
  });

  it('returns a CORS preflight response for allowed origins', async () => {
    const response = await handleRequest(
      new Request('https://worker.example.com/api/llm', {
        method: 'OPTIONS',
        headers: { origin: 'https://pathcosmos.github.io' },
      }),
      env,
      async () => {
        throw new Error('fetch should not be called');
      },
    );

    assert.equal(response.status, 204);
    assert.equal(response.headers.get('access-control-allow-origin'), 'https://pathcosmos.github.io');
    assert.match(response.headers.get('access-control-allow-methods'), /POST/);
  });

  it('rejects unsupported modes before calling Gemini', async () => {
    const response = await handleRequest(
      request({ mode: 'map', text: '부산 중견 철강사' }),
      env,
      async () => {
        throw new Error('fetch should not be called');
      },
    );

    assert.equal(response.status, 501);
    assert.deepEqual(await response.json(), {
      error: 'not_implemented',
      message: 'mode map is planned for a later phase',
    });
  });

  it('rejects polish input above the phase-one size limit', async () => {
    const response = await handleRequest(
      request({ mode: 'polish', text: '가'.repeat(12001) }),
      env,
      async () => {
        throw new Error('fetch should not be called');
      },
    );

    assert.equal(response.status, 413);
    assert.deepEqual(await response.json(), {
      error: 'payload_too_large',
      maxChars: 12000,
    });
  });

  it('calls AI Gateway with payload logging disabled and parses Gemini text', async () => {
    let fetchUrl = '';
    let fetchInit = {};
    const response = await handleRequest(
      request({
        mode: 'polish',
        text: '## 제목\n\n[고객사]의 [공정] 개선',
        inputs: { 고객사: '동국제강', 공정: '후판 압연' },
        metadata: { selectedIds: ['BLK-T1-3.1'] },
      }),
      env,
      async (url, init) => {
        fetchUrl = url;
        fetchInit = init;
        return Response.json({
          candidates: [
            {
              content: {
                parts: [{ text: '## 제목\n\n동국제강의 후판 압연 개선' }],
              },
            },
          ],
          usageMetadata: { promptTokenCount: 10, candidatesTokenCount: 5 },
        });
      },
    );

    assert.equal(response.status, 200);
    assert.equal(response.headers.get('access-control-allow-origin'), 'https://pathcosmos.github.io');
    assert.equal(fetchUrl, 'https://gateway.ai.cloudflare.com/v1/account-123/gateway-abc/google-ai-studio/v1/models/gemini-2.5-flash:generateContent');
    assert.equal(fetchInit.headers['x-goog-api-key'], 'test-gemini-key');
    assert.equal(fetchInit.headers['cf-aig-collect-log-payload'], 'false');
    assert.deepEqual(await response.json(), {
      text: '## 제목\n\n동국제강의 후판 압연 개선',
      model: 'gemini-2.5-flash',
      usage: { promptTokenCount: 10, candidatesTokenCount: 5 },
    });
  });

  it('adds the authenticated gateway token when configured', async () => {
    let headers = {};
    const response = await handleRequest(
      request({ mode: 'polish', text: '본문' }),
      { ...env, CF_AIG_TOKEN: 'gateway-token' },
      async (_url, init) => {
        headers = init.headers;
        return Response.json({
          candidates: [{ content: { parts: [{ text: '다듬어진 본문' }] } }],
        });
      },
    );

    assert.equal(response.status, 200);
    assert.equal(headers['cf-aig-authorization'], 'Bearer gateway-token');
  });
});
