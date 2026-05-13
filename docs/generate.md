---
title: "📝 본문 자동 생성"
description: "업체 정보 입력 → 276 블록 (Track·패키지·시나리오·가이드·모듈) → 사업계획서 paste-ready 본문"
hide:
  - toc
---

# 📝 본문 자동 생성

!!! warning "새 작성 흐름 안내"
    신규 작성은 [조립형 작성기](/assemble/) 를 우선 사용하세요. 이 페이지는 기존 블록 선택·AI 다듬기 호환용으로 유지됩니다.

!!! tip "사용법 — 4 모드"
    1. **⚡ 빠른** — 패키지 1 클릭으로 ~45 블록 자동 묶음
    2. **🎯 § 매핑** — 사업계획서 §별 자산 그룹 selector
    3. **📋 Track** — Track 1·2·3 핵심 15 BLK (기존)
    4. **🔍 검색** — 자유 텍스트로 본문 검색

미입력 placeholder (`[고객사]` 등) 는 원본 그대로 유지 — 사업계획서 paste 후 일괄 치환 가능.

<div id="asset-stats" class="asset-stats">데이터 로딩 중...</div>

---

<div id="generate-form" data-templates-path="../data/templates.json" data-llm-endpoint="https://ai-docs-for-biz-llm.pathcosmos.workers.dev/api/llm" markdown="1">

<div class="generate-grid" markdown="1">

<div class="generate-form-col" markdown="1">

#### ① 업체 정보 입력

<div class="form-fields" markdown="1">
<label for="input-고객사">고객사명</label>
<input id="input-고객사" type="text" placeholder="예: 동국산업(주)" />

<label for="input-공정">대상 공정</label>
<input id="input-공정" type="text" placeholder="예: 후판 압연·소둔" />

<label for="input-수치">수치 (정량 데이터)</label>
<input id="input-수치" type="text" placeholder="예: 87" />

<label for="input-기간">기간</label>
<input id="input-기간" type="text" placeholder="예: 12 개월" />

<label for="input-percent">% (비율)</label>
<input id="input-percent" type="text" placeholder="예: 30%" />

<label for="input-LLM모델">LLM 모델</label>
<input id="input-LLM모델" type="text" placeholder="예: HyperCLOVA-X" />

<label for="input-벡터스토어">벡터스토어</label>
<input id="input-벡터스토어" type="text" placeholder="예: Pinecone·Weaviate" />

<label for="input-임계">임계값</label>
<input id="input-임계" type="text" placeholder="예: PSI 0.25" />
</div>

</div>

<div class="generate-result-col" markdown="1">

#### ③ 생성 결과

<div class="output-controls" markdown="1">
<button id="btn-copy" type="button">📋 복사</button>
<button id="btn-download" type="button">⬇ 다운로드 (.md)</button>
<span id="selected-count" class="selected-count">선택 0 블록</span>
</div>

<textarea id="output" readonly placeholder="우측 모드에서 블록 선택 후 [🔄 단순 치환] 또는 [🤖 AI 다듬기]"></textarea>

<div id="output-meta" class="output-meta"></div>

</div>

</div>

#### ② 블록 선택 — 4 모드

<div class="generate-tabs" markdown="1">
<button type="button" data-mode="quick" class="active">⚡ 빠른</button>
<button type="button" data-mode="section">🎯 § 매핑</button>
<button type="button" data-mode="track">📋 Track</button>
<button type="button" data-mode="search">🔍 검색</button>
</div>

<div id="mode-quick" class="generate-mode" style="display:block" markdown="1">

**패키지 1 클릭** → 도메인 시나리오 + Track 본문 자동 묶음

<div id="pkg-cards" class="pkg-cards"></div>

</div>

<div id="mode-section" class="generate-mode" style="display:none" markdown="1">

**사업계획서 § 별 자산** (펼치기)

<div id="section-tree" class="section-tree"></div>

</div>

<div id="mode-track" class="generate-mode" style="display:none" markdown="1">

**Track 1·2·3 핵심 15 BLK** (기본)

<div id="blk-checklist" class="blk-checklist"></div>

</div>

<div id="mode-search" class="generate-mode" style="display:none" markdown="1">

**자유 텍스트 검색** — 모든 블록 본문에서

<input id="search-input" type="text" class="search-input" placeholder="예: 압연·암묵지·CBAM·드리프트·청킹" />

<div id="search-results" class="search-results"></div>

</div>

<div class="blk-controls" markdown="1">
<button id="btn-select-all" type="button">☑ 모두 선택</button>
<button id="btn-clear-all" type="button">☐ 모두 해제</button>
<button id="btn-generate" type="button" class="primary">🔄 단순 치환</button>
<button id="btn-ai-generate" type="button" class="primary ai">🤖 AI 다듬기 (Worker)</button>
</div>

<div id="error-message" class="error-message"></div>

#### 🤖 AI 다듬기 (선택) — Gemini + Cloudflare Worker

??? warning "Worker endpoint 설정 — 보안 안내 (펼치기)"

    Cloudflare Worker 가 Gemini API 키를 서버 측 secret 으로 보관하고, 브라우저는 Worker 의 `/api/llm` endpoint 만 호출합니다.

    **배포 준비**:
    - `worker/wrangler.toml` 기준으로 Worker 를 배포합니다.
    - `GEMINI_API_KEY`, `CF_ACCOUNT_ID`, `CF_GATEWAY_ID` 는 Cloudflare Worker secret 으로 등록합니다.
    - 선택적으로 authenticated AI Gateway 를 쓰는 경우 `CF_AIG_TOKEN` 도 secret 으로 등록합니다.

    **보안**:
    - Gemini API 키는 브라우저에 입력하거나 저장하지 않습니다.
    - 이 페이지에는 Worker endpoint URL 만 저장됩니다.
    - endpoint 는 브라우저 `localStorage` 에 저장되어 페이지 재로드 시 복원됩니다.
    - **🔓 endpoint 삭제** 클릭 시 저장값을 제거합니다.

    **사용량**:
    - 기본 모델은 `gemini-2.5-flash` 입니다.
    - Phase 1 은 단일 polish 호출만 지원합니다.
    - 본문 12,000 자 초과 시 차단합니다. 블록 단위 chunking 은 후속 단계에서 구현합니다.

<div class="ai-controls" markdown="1">
<label for="input-llm-endpoint">Cloudflare Worker endpoint</label>
<input id="input-llm-endpoint" type="url" placeholder="https://ai-docs-for-biz-llm.pathcosmos.workers.dev/api/llm" autocomplete="off" />
<button id="btn-clear-endpoint" type="button">🔓 endpoint 삭제</button>
</div>

<div id="ai-status" class="ai-status"></div>

</div>

---

## 📊 자산 분포 (276 블록)

| 카테고리 | 블록 수 | 사업계획서 § |
|---|---|---|
| **track** | 15 | §3·§4·§6 (핵심 5 BLK × Track 1·2·3) |
| **package** | 45 | §0~§8 (6 패키지 × 평균 7.5 H2) |
| **scenario** | 79 | §3·§4·§6 (40 SCN × 4 sub) |
| **guide** | 102 | §1·§4·§5·§6·§10 (12 가이드 × 평균 8 장) |
| **module** | 35 | §3.5·§1.2·§3.4 (5 모듈 × 7 BLK-A~G) |
