const DEFAULT_MODEL = 'gemini-2.5-flash';
const MODE_LIMITS = {
  polish: 12000,
  map: 4000,
  ascii: 8000,
};

const PLANNED_MODES = new Set(['map', 'ascii']);

function splitCsv(value = '') {
  return value
    .split(',')
    .map(item => item.trim())
    .filter(Boolean);
}

function isAllowedOrigin(origin, env) {
  if (!origin) return true;
  return splitCsv(env.ALLOWED_ORIGINS).includes(origin);
}

function corsHeaders(origin, env) {
  const headers = {
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Vary': 'Origin',
  };
  if (origin && isAllowedOrigin(origin, env)) {
    headers['Access-Control-Allow-Origin'] = origin;
  }
  return headers;
}

function jsonResponse(payload, status, origin, env) {
  return Response.json(payload, {
    status,
    headers: corsHeaders(origin, env),
  });
}

function requireEnv(env) {
  const missing = ['GEMINI_API_KEY', 'CF_ACCOUNT_ID', 'CF_GATEWAY_ID']
    .filter(key => !env[key]);
  if (missing.length > 0) {
    return `Missing Worker env: ${missing.join(', ')}`;
  }
  return '';
}

function buildGatewayUrl(env) {
  const accountId = encodeURIComponent(env.CF_ACCOUNT_ID);
  const gatewayId = encodeURIComponent(env.CF_GATEWAY_ID);
  const model = encodeURIComponent(env.GEMINI_MODEL || DEFAULT_MODEL);
  return `https://gateway.ai.cloudflare.com/v1/${accountId}/${gatewayId}/google-ai-studio/v1/models/${model}:generateContent`;
}

function buildPolishPrompt({ text, inputs = {}, metadata = {} }) {
  const inputLines = Object.entries(inputs)
    .map(([key, value]) => `- [${key}] = ${value}`)
    .join('\n') || '(입력 정보 없음 — 플레이스홀더 그대로 유지)';
  const selectedIds = Array.isArray(metadata.selectedIds) && metadata.selectedIds.length > 0
    ? metadata.selectedIds.join(', ')
    : '(선택 블록 ID 없음)';

  return `당신은 한국어 정부지원 R&D 사업계획서 작성 전문가입니다. 아래 본문 초안을 다듬어 주세요.

【작업 지침】
1. 한국어 formal 문어체 (~한다·~된다 종결, 명사형 표현)를 유지합니다.
2. 의미를 추가하거나 삭제하지 말고 표현·문체만 정리합니다.
3. Markdown 제목과 표 구조를 유지합니다.
4. 출처 표기 \`> [출처: ...]\` 는 한 글자도 바꾸지 않습니다.
5. 아래 입력 정보가 있는 플레이스홀더는 자연스럽게 치환합니다.
6. 출력은 다듬어진 Markdown 본문만 반환합니다.

【사용자 입력 정보】
${inputLines}

【선택 블록 ID】
${selectedIds}

【본문 초안】
${text}

【다듬어진 본문】`;
}

function parseGeminiText(data) {
  const parts = data?.candidates?.[0]?.content?.parts || [];
  const text = parts.map(part => part.text || '').join('').trim();
  if (!text) {
    throw new Error('Gemini response did not include text');
  }
  return text;
}

async function callGeminiViaGateway(payload, env, fetchImpl) {
  const prompt = buildPolishPrompt(payload);
  const headers = {
    'Content-Type': 'application/json',
    'x-goog-api-key': env.GEMINI_API_KEY,
    'cf-aig-collect-log-payload': 'false',
  };
  if (env.CF_AIG_TOKEN) {
    headers['cf-aig-authorization'] = `Bearer ${env.CF_AIG_TOKEN}`;
  }

  const response = await fetchImpl(buildGatewayUrl(env), {
    method: 'POST',
    headers,
    body: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: {
        temperature: 0.4,
        maxOutputTokens: 8192,
        topP: 0.9,
      },
    }),
  });

  if (!response.ok) {
    const detail = await response.text();
    return {
      ok: false,
      status: response.status,
      detail: detail.slice(0, 500),
    };
  }

  const data = await response.json();
  return {
    ok: true,
    text: parseGeminiText(data),
    usage: data.usageMetadata || null,
  };
}

export async function handleRequest(request, env, fetchImpl = fetch) {
  const origin = request.headers.get('Origin') || '';

  if (!isAllowedOrigin(origin, env)) {
    return new Response('Origin not allowed', {
      status: 403,
      headers: corsHeaders(origin, env),
    });
  }

  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: corsHeaders(origin, env),
    });
  }

  const url = new URL(request.url);
  if (url.pathname !== '/api/llm') {
    return jsonResponse({ error: 'not_found' }, 404, origin, env);
  }

  if (request.method !== 'POST') {
    return jsonResponse({ error: 'method_not_allowed' }, 405, origin, env);
  }

  const configError = requireEnv(env);
  if (configError) {
    return jsonResponse({ error: 'worker_misconfigured', message: configError }, 500, origin, env);
  }

  let payload;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse({ error: 'invalid_json' }, 400, origin, env);
  }

  const mode = payload.mode || 'polish';
  if (PLANNED_MODES.has(mode)) {
    return jsonResponse(
      { error: 'not_implemented', message: `mode ${mode} is planned for a later phase` },
      501,
      origin,
      env,
    );
  }
  if (mode !== 'polish') {
    return jsonResponse({ error: 'invalid_mode' }, 400, origin, env);
  }

  const text = typeof payload.text === 'string' ? payload.text : '';
  if (!text.trim()) {
    return jsonResponse({ error: 'text_required' }, 400, origin, env);
  }

  const maxChars = MODE_LIMITS[mode];
  if (text.length > maxChars) {
    return jsonResponse({ error: 'payload_too_large', maxChars }, 413, origin, env);
  }

  try {
    const gemini = await callGeminiViaGateway(payload, env, fetchImpl);
    if (!gemini.ok) {
      return jsonResponse(
        { error: 'gemini_error', status: gemini.status, detail: gemini.detail },
        502,
        origin,
        env,
      );
    }
    return jsonResponse(
      {
        text: gemini.text,
        model: env.GEMINI_MODEL || DEFAULT_MODEL,
        usage: gemini.usage,
      },
      200,
      origin,
      env,
    );
  } catch (error) {
    return jsonResponse({ error: 'worker_error', message: error.message }, 500, origin, env);
  }
}

export default {
  fetch(request, env) {
    return handleRequest(request, env);
  },
};
