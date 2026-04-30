---
title: "📝 본문 자동 생성"
description: "업체 정보 입력 → 276 블록 (Track·패키지·시나리오·가이드·모듈) → 사업계획서 paste-ready 본문"
hide:
  - toc
---

# 📝 본문 자동 생성

!!! tip "사용법 — 4 모드"
    1. **⚡ 빠른** — 패키지 1 클릭으로 ~45 블록 자동 묶음
    2. **🎯 § 매핑** — 사업계획서 §별 자산 그룹 selector
    3. **📋 Track** — Track 1·2·3 핵심 15 BLK (기존)
    4. **🔍 검색** — 자유 텍스트로 본문 검색

미입력 placeholder (`[고객사]` 등) 는 원본 그대로 유지 — 사업계획서 paste 후 일괄 치환 가능.

<div id="asset-stats" class="asset-stats">데이터 로딩 중...</div>

---

<div id="generate-form" data-templates-path="../data/templates.json" markdown="1">

<div class="generate-grid" markdown="1">

<div class="generate-form-col" markdown="1">

#### ① 업체 정보 입력

<div class="form-fields" markdown="1">
<label for="input-고객사">고객사명</label>
<input id="input-고객사" type="text" placeholder="예: 동국제강(주)" />

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
<button id="btn-ai-generate" type="button" class="primary ai">🤖 AI 다듬기 (Gemini)</button>
</div>

<div id="error-message" class="error-message"></div>

#### 🤖 AI 다듬기 (선택) — Gemini 1.5 Flash

??? warning "API 키 입력 — 보안 안내 (펼치기)"

    Google Gemini API (무료 1M 토큰/일) 를 사용하여 본문을 사업계획서 어투로 자연스럽게 다듬습니다.

    **API 키 발급**: https://aistudio.google.com/apikey → **Get API key** → **Create API key**

    **보안**:
    - 키는 **귀하의 브라우저 localStorage 에만 저장** (서버 0)
    - 페이지 재로드 시 자동 복원
    - **🔓 키 삭제** 클릭 시 즉시 제거
    - 노출 의심 시 즉시 https://aistudio.google.com/apikey 에서 회전

    **사용량**:
    - gemini-1.5-flash: 1,500 RPM · 1M 토큰/일 무료
    - 사업계획서 1 회 ≈ 5,000~50,000 토큰 → 일일 20~200 회 사용 가능
    - 본문 100,000 자 초과 시 자동 차단 (에러 회피)

<div class="ai-controls" markdown="1">
<label for="input-api-key">Gemini API 키</label>
<input id="input-api-key" type="password" placeholder="AIzaSy..." autocomplete="off" />
<button id="btn-clear-key" type="button">🔓 키 삭제</button>
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
