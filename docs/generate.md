---
title: "📝 본문 자동 생성"
description: "업체명·수치 입력 → 사업계획서 paste 가능 본문 자동 생성 (15 BLK 블록 통합)"
hide:
  - toc
---

# 📝 본문 자동 생성

!!! tip "사용법 — 3 단계"
    1. **좌측 ① 업체 정보** 입력 (귀사 명·공정·수치 등)
    2. **하단 ② BLK 블록** 1 개 이상 선택 (Track 1·2·3 핵심 15 종)
    3. **🔄 생성하기** → 우측 결과 → 📋 복사 또는 ⬇ 다운로드 (.md)

미입력 필드는 `[고객사]` 같은 원본 그대로 유지됩니다 (사업계획서에서 추가 치환).

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
</div>

<textarea id="output" readonly placeholder="좌측 BLK 선택 후 [🔄 생성하기] 클릭"></textarea>

<div id="output-meta" class="output-meta"></div>

</div>

</div>

#### ② BLK 블록 선택 (Track 1·2·3 핵심 15)

<div class="blk-controls" markdown="1">
<button id="btn-select-all" type="button">☑ 모두 선택</button>
<button id="btn-clear-all" type="button">☐ 모두 해제</button>
<button id="btn-generate" type="button" class="primary">🔄 단순 치환 생성</button>
<button id="btn-ai-generate" type="button" class="primary ai">🤖 AI 다듬기 (Gemini)</button>
</div>

<div id="blk-checklist" class="blk-checklist"></div>

<div id="error-message" class="error-message"></div>

#### 🤖 AI 다듬기 (선택) — Gemini 1.5 Flash

??? warning "API 키 입력 — 보안 안내 (펼치기)"

    Google Gemini API (무료 1M 토큰/일) 를 사용하여 본문을 사업계획서 어투로 자연스럽게 다듬습니다.

    **API 키 발급 방법**:
    1. https://aistudio.google.com/apikey 접속
    2. **Get API key** → **Create API key** 클릭
    3. 발급된 키 복사 → 아래 입력 필드 붙여넣기

    **보안**:
    - 키는 **귀하의 브라우저 localStorage 에만 저장** (서버 0)
    - 페이지 재로드 시 자동 복원
    - **🔓 키 삭제** 클릭 시 즉시 제거
    - 키 노출 의심 시 즉시 https://aistudio.google.com/apikey 에서 회전 (재발급)

    **사용량**:
    - gemini-1.5-flash: 무료 1,500 RPM · 1M 토큰/일
    - 사업계획서 1 회 생성 ≈ 5,000~20,000 토큰 → 일일 50~200 회 사용 가능

<div class="ai-controls" markdown="1">
<label for="input-api-key">Gemini API 키 (선택)</label>
<input id="input-api-key" type="password" placeholder="AIzaSy..." autocomplete="off" />
<button id="btn-clear-key" type="button">🔓 키 삭제</button>
</div>

<div id="ai-status" class="ai-status"></div>

</div>

---

## paste 위치 가이드

| BLK 블록 | 사업계획서 § | 핵심 |
|---|---|---|
| **BLK-T1-3.1** | §3.1 사업 배경 | 인적 의존성·암묵지 리스크 |
| **BLK-T1-3.2** | §3.2 사업 배경 | 데이터 단절·비정형 한계 |
| **BLK-T1-4.4** | §4.4 기술 설계 | 피쳐 엔지니어링 접근 |
| **BLK-T1-4.5** | §4.5 기술 설계 | 모델·앙상블 선정 기준 |
| **BLK-T1-4.6** | §4.6 기술 설계 | 데이터→피쳐→모델→적용 파이프라인 |
| **BLK-T2-3.2** | §6 MLOps AS-IS | 모니터링 부재·후행 운영 |
| **BLK-T2-4.2** | §7 MLOps TO-BE | 7 종 구성요소 인벤토리 |
| **BLK-T2-4.4** | §7 MLOps 아키텍처 | 엣지·온프레·클라우드 3 단 |
| **BLK-T2-5.5** | §8 운영 | 3 층 모니터링·드리프트 |
| **BLK-T2-6.1** | §8 개선 | 개선 포인트 선정 노하우 |
| **BLK-T3-3.1** | §3.1 사업 배경 | 문서 포맷 이질·검색 불가 |
| **BLK-T3-3.2** | §3.2 사업 배경 | 숙련자 암묵지 의존 |
| **BLK-T3-4.2** | §4.2 RAG 아키텍처 | 5 계층 RAG 기준 |
| **BLK-T3-5.2** | §5.2 청킹 전략 | 계층·섹션·토픽·멀티뷰 |
| **BLK-T3-5.5** | §5.5 응답 생성 | 환각 방지·근거 인용·거부 |

!!! info "더 많은 블록이 필요하면"
    - **6 패키지 통합 파일럿** (Stage 2 예정) — 패키지별 30~50 블록
    - **40 시나리오 카탈로그** (Stage 3 예정) — SCN-XXX-NN 단위 본문
    - 현재는 Track 1·2·3 핵심 5 블록 × 3 = **15 블록** 지원
