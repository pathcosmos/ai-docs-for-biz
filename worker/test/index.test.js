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

function agentRequest(body, init = {}) {
  return new Request('https://worker.example.com/api/agent/generate', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      origin: 'https://pathcosmos.github.io',
      ...(init.headers || {}),
    },
    body: JSON.stringify(body),
  });
}

async function readSseEvents(response) {
  const text = await response.text();
  return text
    .trim()
    .split('\n\n')
    .filter(Boolean)
    .map(chunk => {
      const lines = chunk.split('\n');
      const event = lines.find(line => line.startsWith('event: '))?.slice(7);
      const dataLine = lines.find(line => line.startsWith('data: '))?.slice(6);
      return { event, data: JSON.parse(dataLine || '{}') };
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

  it('rejects agent generation when required company fields are missing', async () => {
    const response = await handleRequest(
      agentRequest({ profile: { step1_company: { industry: 'STL' } } }),
      env,
      async () => {
        throw new Error('fetch should not be called');
      },
    );

    assert.equal(response.status, 400);
    assert.deepEqual(await response.json(), {
      error: 'tier1_missing',
      fields: ['company'],
    });
  });

  it('streams a phase-one agent generation document with nine sections', async () => {
    const response = await handleRequest(
      agentRequest({
        profile: {
          step1_company: {
            company: '동국제강',
            industry: 'STL',
            process: '후판 압연',
            scale: '중견',
          },
          step2_business: {
            duration_months: 12,
            form_type: '단년',
          },
          step4_settings: {
            output_strength: '중',
          },
        },
      }),
      env,
      async () => {
        throw new Error('fetch should not be called in phase-one deterministic mode');
      },
    );

    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-type'), /text\/event-stream/);
    assert.equal(response.headers.get('access-control-allow-origin'), 'https://pathcosmos.github.io');

    const events = await readSseEvents(response);
    assert.equal(events[0].event, 'connected');
    assert.equal(events.filter(item => item.event === 'section_done').length, 9);

    const complete = events.find(item => item.event === 'complete');
    assert.ok(complete);
    assert.match(complete.data.final_md, /# 동국제강 AI 사업계획서/);
    assert.equal(complete.data.meta.section_count, 9);
    assert.equal(complete.data.meta.domain, 'STL');
  });

  it('uses Gemini section writers when requested and keeps AI Gateway payload logging disabled', async () => {
    const fetchCalls = [];
    const response = await handleRequest(
      agentRequest({
        profile: {
          step1_company: {
            company: '동국제강',
            industry: 'STL',
            process: '후판 압연',
            scale: '중견',
          },
          step2_business: {
            duration_months: 12,
            form_type: '단년',
          },
          step3_data_model: {
            raw_sources: 'MES 작업 이력, PLC 센서',
            x_candidates: '온도, 속도, 압력',
            y_target: '두께 편차',
            problem_type: '회귀',
          },
          step4_settings: {
            output_strength: '중',
            writer_mode: 'llm',
          },
        },
      }),
      { ...env, AGENT_MAX_LLM_SECTIONS: '9' },
      async (url, init) => {
        const body = JSON.parse(init.body);
        fetchCalls.push({ url, init, prompt: body.contents[0].parts[0].text });
        const sectionNo = fetchCalls.length;
        return Response.json({
          candidates: [
            {
              content: {
                parts: [{
                  text: `## §${sectionNo} LLM 섹션\n\nGemini section ${sectionNo}\n\n> [출처: TEST-${sectionNo}]`,
                }],
              },
            },
          ],
          usageMetadata: {
            promptTokenCount: 100 + sectionNo,
            candidatesTokenCount: 20 + sectionNo,
            totalTokenCount: 120 + (sectionNo * 2),
          },
        });
      },
    );

    assert.equal(response.status, 200);
    const events = await readSseEvents(response);
    assert.equal(fetchCalls.length, 9);
    assert.equal(events.filter(item => item.event === 'section_done').length, 9);
    assert.equal(fetchCalls[0].url, 'https://gateway.ai.cloudflare.com/v1/account-123/gateway-abc/google-ai-studio/v1/models/gemini-2.5-flash:generateContent');
    assert.equal(fetchCalls[0].init.headers['x-goog-api-key'], 'test-gemini-key');
    assert.equal(fetchCalls[0].init.headers['cf-aig-collect-log-payload'], 'false');
    assert.match(fetchCalls[0].prompt, /BLK-COMPANY-01/);
    assert.match(fetchCalls[5].prompt, /BLK-DATA-01/);

    const complete = events.find(item => item.event === 'complete');
    assert.ok(complete);
    assert.equal(complete.data.meta.mode, 'phase-two-llm-sections');
    assert.equal(complete.data.usage.total_calls, 9);
    assert.equal(complete.data.usage.total_tokens, 1170);
    assert.match(complete.data.final_md, /Gemini section 1/);
    assert.match(complete.data.final_md, /Gemini section 9/);
  });

  it('caps Gemini section writers by environment limit and falls back for the rest', async () => {
    const fetchCalls = [];
    const response = await handleRequest(
      agentRequest({
        profile: {
          step1_company: {
            company: '동국제강',
            industry: 'STL',
            process: '후판 압연',
            scale: '중견',
          },
          step2_business: { duration_months: 12, form_type: '단년' },
          step3_data_model: {
            raw_sources: 'MES 작업 이력',
            x_candidates: '온도, 속도',
            y_target: '두께 편차',
            problem_type: '회귀',
          },
          step4_settings: {
            output_strength: '중',
            writer_mode: 'llm',
          },
        },
      }),
      { ...env, AGENT_MAX_LLM_SECTIONS: '5' },
      async (_url, init) => {
        fetchCalls.push(JSON.parse(init.body).contents[0].parts[0].text);
        return Response.json({
          candidates: [{ content: { parts: [{ text: `Gemini section ${fetchCalls.length}` }] } }],
          usageMetadata: { totalTokenCount: 10 },
        });
      },
    );

    assert.equal(response.status, 200);
    const events = await readSseEvents(response);
    assert.equal(fetchCalls.length, 5);
    assert.equal(events.filter(item => item.event === 'section_fallback').length, 4);

    const complete = events.find(item => item.event === 'complete');
    assert.ok(complete);
    assert.equal(complete.data.meta.fallback_count, 4);
    assert.equal(complete.data.usage.total_calls, 5);
    assert.equal(complete.data.usage.total_tokens, 50);
  });
});
