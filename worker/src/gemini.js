export const DEFAULT_MODEL = 'gemini-2.5-flash';

export function geminiModel(env) {
  return env.GEMINI_MODEL || DEFAULT_MODEL;
}

export function requireGeminiEnv(env) {
  const missing = ['GEMINI_API_KEY', 'CF_ACCOUNT_ID', 'CF_GATEWAY_ID']
    .filter(key => !env[key]);
  if (missing.length > 0) {
    return `Missing Worker env: ${missing.join(', ')}`;
  }
  return '';
}

export function buildGatewayUrl(env) {
  const accountId = encodeURIComponent(env.CF_ACCOUNT_ID);
  const gatewayId = encodeURIComponent(env.CF_GATEWAY_ID);
  const model = encodeURIComponent(geminiModel(env));
  return `https://gateway.ai.cloudflare.com/v1/${accountId}/${gatewayId}/google-ai-studio/v1/models/${model}:generateContent`;
}

export function parseGeminiText(data) {
  const parts = data?.candidates?.[0]?.content?.parts || [];
  const text = parts.map(part => part.text || '').join('').trim();
  if (!text) {
    throw new Error('Gemini response did not include text');
  }
  return text;
}

export async function callGeminiText({ prompt, env, fetchImpl, generationConfig = {} }) {
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
        ...generationConfig,
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
