# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project actually is

This is **not a software codebase** — it is a Korean-language **content-authoring workspace** for producing reusable material (본문 문구 + 삽화/도식) that can be pasted into Korean government-funded manufacturing-AI 사업계획서 / 사업신청서 / 수행계획서 / 연구개발계획서.

- No source code, no build system, no tests, no git.
- The working tree contains only **6 reference PDFs** — real filed business plans from other companies (YCP, 코리녹스, 동연에스엔티, 화승알엔에이, 통합형 클라우드화, 전사적 DX 촉진). They are **exemplars**, not templates to copy verbatim.
- The two listed working directories (`/Volumes/EXDATA/temp_git/ai-docs-for-biz` and `/Users/lanco/exdata/temp_git/ai-docs-for-biz`) point at the same content — use either.

## 실무 컨텍스트 — 고객·작성 흐름

- **주요 고객사**: 철강 및 부산·경남권 제조업체. 규모 편차가 크다 (대기업급 ~ 중소).
  - 예: 화승, YCP특수강, 코리녹스, 코렌스, 대한제강, 한국철강 등
  - 업종 범위는 철강·금속가공(연속주조·압연·열처리·표면처리 등)을 중심으로, 고무·폴리머, 정밀가공 등 부산경남 제조업 전반. 예시·공정명은 가급적 이쪽 현장에 실제로 존재하는 것을 고른다.
- 이들 고객사의 사업계획서 작성 업무가 **상시** 발생하며, 최근 **AI 적용 관련 요청이 크게 늘어남** — 본 워크스페이스가 만들어진 직접적 이유.
- **작성 접근 방식 — 공통 자산 + 시나리오 특화**:
  1. AI 관련 **공통 본문·삽화**(아래 3대 트랙 기반)를 먼저 축적,
  2. 고객사·공정·지원사업 성격에 맞춰 **시나리오 몇 가지**를 정의,
  3. 각 시나리오별로 **특화된 문서 내용 + 삽화**를 파생시켜 사업계획서에 투입.
- 따라서 생성물은 "특정 사업계획서용 원고"가 아니라 **재조합 가능한 모듈**로 설계한다.
  - 섹션·문단 단위로 자립적이어야 하고,
  - 고객사명·공정명·수치는 플레이스홀더(`[고객사]`, `[공정]`, `[수치]`) 형태로 남겨 두면 재활용이 쉽다.
  - 특정 고객사 전용 문구는 파일명·섹션 헤더에 해당 고객사를 명시해 공통 자산과 섞이지 않도록 분리한다.

## Production goals (three tracks)

Everything you write should slot into one of three tracks. Outputs in each track must be **self-contained, reusable passages + accompanying 삽화/도식 자료** written in Korean formal 사업계획서 어투.

**Track 1 — 제조 AI 서두/본문 (Manufacturing AI general narrative)**
- 제조업·공장·공정에서 AI 도입 필요성, 기대효과
- 활용 가능한 데이터 유형: 시계열 센서 데이터, 설비/장비 로그, MES/SCADA/PLC 데이터, 비전 이미지 등
- 피쳐 선정·엔지니어링 접근
- 모델·앙상블 선정 기준 (e.g. LSTM/Transformer/XGBoost/이상탐지/앙상블 조합)
- 데이터 수집 → 피쳐 → 모델링 → 현장 적용·운영까지의 일련 과정 서술
- 삽화: 아키텍처 다이어그램, 데이터 파이프라인, 모델 구조도, 현장 적용 플로우

**Track 2 — MLOps 구축 및 지속적 개선**
- MLOps 구성의 일반적 방법·전제 조건 (CI/CD for ML, 모델 레지스트리, 피쳐 스토어, 모니터링 등)
- 지속적 개선 루프에 사업계획서에 넣을 수 있는 문구·도식
- **개선 포인트 선정 노하우** — 성능 저하 탐지, 데이터 드리프트, 재학습 트리거, 피드백 수집 등
- 삽화: MLOps 파이프라인도, 모니터링 대시보드 개념도, 개선 사이클 다이어그램

**Track 3 — LLM + RAG 공정 적용**
- 제조 현장에서 LLM과 RAG을 활용할 수 있는 시나리오 (작업지시서 검색, 장애 대응 지식 검색, 표준 작업 문서 QA, 비정형 공정 지식 활용 등)
- 관련 데이터 수집·구성 방법 (문서 표준화, 청킹 전략, 임베딩·벡터스토어 구성, 권한·보안)
- 삽화: RAG 아키텍처, 데이터 수집·전처리·인덱싱 플로우, 프롬프트/응답 예시 도식

## Working with the reference PDFs

- **All 6 PDFs exceed 10 pages** (37, 41, 67, 71, 74, 150). The `Read` tool requires the `pages` parameter for any of them — reading without it will fail. Start with a small range (e.g. `pages: "1-10"`) and expand.
- Filenames are Korean and contain spaces/brackets — always quote paths in Bash.
- Each PDF represents a different government/대기업 지원사업 format (스마트공장, 디지털 경남, 대중소상생, 전사적 DX, 클라우드 지원사업). Structure, depth, and emphasis differ; do not assume one layout.
- Treat them as **source material for patterns and phrasing**, not text to reproduce. Avoid copying sentences verbatim — extract patterns (목차 구성, 논리 전개, 표·도식 종류, 수치 제시 방식) and write fresh prose.

## Output expectations

- **Language: Korean.** The target deliverable is Korean business-plan copy. Write body text in formal 국문 (문어체), not conversational Korean and not English unless the user explicitly asks.
- Prefer producing **drafts as Markdown files in this directory** so the user can review/edit before transplanting into their .hwp / .docx / .pptx. Do not create files unless asked, but when asked, put them at the repo root (flat structure matches what's here).
- 삽화/도식: describe them as Markdown diagrams (Mermaid where appropriate), ASCII sketches, or structured tables. The user will re-draw in their real document — clarity of structure and labels matters more than rendering.
- When the user's request maps clearly to one of the three tracks, name the track you're writing for so reuse across plans is easier.

## 작업 로그 유지 규약 (필독 · 필수 준수)

본 워크스페이스에는 **`작업로그.md`** 파일이 존재한다. 이 파일은 프로젝트 전 기간에 걸친 작업 과정·판단 근거·사용자 의사결정을 상세히 기록하여, (1) 다른 프로젝트에 방법론을 응용하고, (2) 다른 작업자(사람 또는 다른 세션의 AI)가 이어받아 수행할 수 있도록 한다.

**모든 세션·모든 작업자는 다음 규약을 반드시 준수한다.**

1. **갱신 의무**: 아래에 해당하는 작업을 수행한 경우 **같은 턴 안에서** `작업로그.md` 섹션 3(진행 연대기) 에 엔트리를 추가한다.
   - 새 파일 생성·삭제
   - 기존 파일의 의미 있는 수정 (오탈자 수정 제외)
   - 사용자 의사결정 수신
   - 계획·방향 전환 또는 Phase 전환
   - 스킬·에이전트 호출을 수반한 작업
   - 사용자가 중요 맥락·고객 정보·용어 정의를 제공한 경우
2. **엔트리 형식**: `작업로그.md` 섹션 1.2 의 8 필드 템플릿을 따른다 — 맥락 / 사용자 요청 원문 요지 / AI 수행 / 판단 근거 / 사용자 의사결정 / 산출물 / 배운 점·재사용 포인트 / 다음 단계.
3. **원문 인용**: 사용자 발언은 **짧은 직접 인용** 한 줄 이상 포함 (요약은 의도 왜곡의 주범).
4. **"왜" 기재**: "무엇을 했다" 보다 "왜 그렇게 했다" 를 더 정성 있게. 이 문서의 가치는 이식성에 있고, 이식성의 원천은 판단 근거다.
5. **파일 목록·미결 항목 동기화**: 파일이 추가·삭제되면 `작업로그.md` 섹션 2.7 (파일 목록) 과 섹션 5 (미결 항목) 를 함께 갱신한다.
6. **방법론 추출**: 재사용 가치가 있는 패턴을 발견하면 `작업로그.md` 섹션 4 (방법론 추출) 에도 추가한다.
7. **프로젝트 종료 시까지 유지**: 작업 종료 · 인계 · 재개 시에도 본 규약은 불변.

본 로그가 없거나 양식이 바뀐 상태로 발견되면, 먼저 `작업로그.md` 를 복구·표준화한 뒤에야 다른 작업을 진행한다.

## What NOT to do

- Do not treat this as a code project — there is nothing to build, lint, or test.
- Do not initialize git, create package manifests, or scaffold directories unless the user asks.
- Do not invent statistics, company names, or specific project outcomes from the reference PDFs without first reading the relevant pages.
- Do not default to English. The user's deliverable is Korean.
- **Do not skip the `작업로그.md` update** when the criteria above apply — skipping breaks handoff for the next worker/session.
