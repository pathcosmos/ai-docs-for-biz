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
<!-- slaminar:begin:overview -->
## Overview

**ai-docs-for-biz** — 한국어 제조 AI 사업계획서 작성을 위한 누적 콘텐츠 워크스페이스. 부산·경남권 철강·금속·고무·정밀가공 제조업체를 고객사로 하는 정부지원 R&D·스마트공장·CBAM·디지털 경남 사업 신청서·수행계획서·연구개발계획서 작성에 재사용 가능한 모듈형 자산 (44 마크다운 / 17,816 줄 / Mermaid 115 블록 / 인용 출처 274 회) 을 제공한다.

- **Primary content:** 한국어 마크다운 — Track 1·2·3 본문 + 6 패키지 통합 파일럿 + 11 운영 가이드 + 5 cross-cutting 모듈 + 시나리오 카탈로그 (40 시나리오) + 36 방법론.
- **Secondary infrastructure (Phase E9, 2026-04):** Python — MkDocs Material 기반 HTML 문서화 + GitHub Pages 배포 파이프라인 (`build_src.py` + `hooks/` + `mkdocs.yml`).
- **Pattern:** Knowledge base + reusable content modules (콘텐츠 작성 워크스페이스 + 정적 문서 사이트). 단일 정의된 사업계획서를 만들지 않고 재조합 가능한 모듈을 누적.
- **Maturity:** Phase A~E8 완료 (자산 누적·운영 모드 진입) + Phase E9 진행 중 (HTML 시각 문서화).
<!-- slaminar:end:overview -->
<!-- slaminar:begin:commands -->
## Build & Development Commands

**HTML 문서화 (Phase E9 — MkDocs Material)**:

```bash
# 1. 가상환경 + 의존성 설치 (1 회)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 원본 .md 44 종 → docs/ 영문 slug 복사 (mkdocs build 직전 매번)
python build_src.py

# 3. 로컬 빌드 (정적 사이트 site/ 생성)
mkdocs build

# 4. 로컬 프리뷰 (http://127.0.0.1:8000)
mkdocs serve

# 5. GitHub Pages 수동 배포 (CI/CD 미사용 시)
mkdocs gh-deploy --force
```

**자동 배포**: `main` branch 에 push → `.github/workflows/deploy.yml` 가 build_src + mkdocs build + gh-deploy 자동 실행. **단 GitHub Pages 활성화는 repo Settings 1 회 수동 (private repo 는 Pro plan 필요)**.

**git 커밋·푸시 표준 (방법론 4.27)**:

```bash
# 양 원격 (GitHub + Yona) 단일 명령 push 설정 (1 회)
git remote set-url --add --push origin https://github.com/pathcosmos/ai-docs-for-biz.git
git remote set-url --add --push origin http://git.dkpia.com:9000/IoT/ai-docs-for-biz.git

# 이후 push 는 1 명령으로 양 원격 동시 동기화
git push origin main
```

**콘텐츠 작성 워크플로**: 작업로그 #N 엔트리 추가 + 8 필드 양식 (맥락·요청·수행·근거·결정·산출물·배움·다음) → 단일 커밋 → 양 원격 푸시.
<!-- slaminar:end:commands -->
<!-- slaminar:begin:architecture -->
## Architecture

**9 자산 군 + 빌드 인프라** 의 이중 구조 — 콘텐츠 자산 (워크스페이스 root) + HTML 빌드 파이프라인 (Phase E9).

```
ai-docs-for-biz/
├── (워크스페이스 root) — 한글 .md 44 종 운영 자산 + 작업로그·CLAUDE.md
│   ├── track1·2·3_*.md (8) — 3 트랙 본문 (목차·Top5·5.2 카드)
│   ├── 시나리오_*.md (6) — 카탈로그 + 상세 5 (Top5·Phase2·RUB·UTL_SAF·특수강관)
│   ├── 사업계획서_패키지[1-6]_*_파일럿.md (6) — 6 통합 파일럿 (사업 패턴)
│   ├── 가이드_*.md (11) — 운영 가이드 (KPI·재무·외부검증·RAG·도메인지식·sLM·압축·조립·컨설팅·TRL·위험)
│   ├── 모듈_*.md (5) — Cross-cutting (CBAM·중대재해·연합학습·OEM·SaaS)
│   ├── 시너지_ROI_모델·책임_분담_매트릭스·양식검증_DX촉진_R&D·방법론_총론·운영_모드_Quickstart 등 (5)
│   ├── 작업로그.md (#01~#N 엔트리) — 8 필드 진행 연대기
│   └── (참고 PDF 6 종 — verbatim 차용 금지, 패턴 추출용)
│
├── (HTML 인프라 — Phase E9) ─── Python·MkDocs ───
│   ├── mkdocs.yml — Material 테마·ko 검색·Mermaid·9 분류 자동 nav
│   ├── slug_map.yml — 한글 → 영문 slug 매핑 테이블 (44 항목)
│   ├── build_src.py — 원본 → docs/ 복사 스크립트
│   ├── hooks/ — Python 훅 (inject_frontmatter·slug_rewrite + Stage 2·3 추가 예정)
│   ├── docs/ — 빌드 입력 (영문 slug 복사본 + index·graph·filter + stylesheets·javascripts)
│   └── .github/workflows/deploy.yml — Actions 자동 배포 (gh-pages branch)
│
└── (빌드 산출물 — gitignore) site/ + .venv/ + .serena/
```

**중요 원칙 — 단방향 빌드**: 원본 .md 자산은 일절 수정 금지. `build_src.py` 가 원본 → `docs/` 영문 slug 복사. 콘텐츠 변경은 항상 root .md 에서, HTML 빌드는 자동 동기화.

**Cross-reference 망**: 274 인용 출처 표기 (`> [출처: 파일명 §섹션]`) 가 자산 간 의존성을 형성. 운영 가이드 11 자산 cross-reference 망이 핵심 (재무 §10 → 컨설팅 §4·6 / KPI §10 → TRL §5 / 책임 §10 → 컨설팅·위험 등).
<!-- slaminar:end:architecture -->
<!-- slaminar:begin:conventions -->
## Conventions

- **본문 언어**: **한국어 formal 문어체** (사업계획서 어투). 영어는 사용자가 명시 요청 시에만.
- **플레이스홀더 관례 (방법론 4.8)**: `[고객사]`·`[공정]`·`[수치]`·`[기간]`·`[%]` — 고객사 변경 시 일괄 치환 가능. 특정 고객사 전용 문구는 파일명·섹션 헤더에 해당 고객사 명시.
- **자산 군 포맷 통일 (방법론 4.26)**: 운영 가이드 11 자산 모두 8 장 구조 + 4 분기 의사결정 + 강도 3 단계 답습. 새 자산 추가 시 첫 자산 포맷 따르기.
- **인용 출처 표기 표준**: `> [출처: 파일명 §섹션]` 매 본문 섹션 말미. 부분 발췌 인용은 "발췌·요약" 명시.
- **자산 명명 규약**: `가이드_X.md` (운영 가이드) / `사업계획서_패키지N_도메인_파일럿.md` (통합 파일럿) / `시나리오_상세_X.md` (시나리오 상세) / `모듈_X.md` (cross-cutting) / `track[1-3]_*.md` (트랙 본문) — 일관 패턴 유지.
- **커밋 스타일**: Conventional Commits (`feat:`·`docs:`·`chore:`·`refactor:`) + Korean body. 양 원격 (GitHub + Yona) 단일 push (방법론 4.27).
- **작업로그 8 필드 엔트리**: 맥락·사용자 요청 원문 요지·AI 수행·판단 근거·사용자 의사결정·산출물·배운 점·다음 단계. 사용자 발언 직접 인용 1 줄 이상.
- **방법론 추출**: 재사용 가치 발견 시 `방법론_총론.md` §3 본문 + `작업로그.md` §4 인덱스 동시 추가 (방법론 4.29).
- **빌드 산출물 gitignore**: `.venv/`·`site/`·`.serena/`·`__pycache__/`·`*.pyc` — 자동 생성물 trace 차단.
<!-- slaminar:end:conventions -->
<!-- slaminar:begin:dependencies -->
## Key Dependencies

**Python (Phase E9 HTML 인프라 — `requirements.txt`)**:
- `mkdocs>=1.6` — 정적 사이트 생성기 (Markdown → HTML)
- `mkdocs-material>=9.5` — Material 테마 (한국어 검색·Mermaid 통합·카드 그리드·tags 플러그인)
- `pymdown-extensions>=10.7` — superfences (Mermaid 커스텀 fence)·details·tabbed·tasklist·highlight 등 마크다운 확장
- `PyYAML>=6.0` — `slug_map.yml` 로딩 (build_src.py + slug_rewrite hook)

**JavaScript CDN (런타임 — 빌드 시 다운로드 안 됨)**:
- `mermaid@11` (CDN unpkg) — Mermaid 다이어그램 렌더링 (115 블록)
- `D3.js@7` (CDN, Stage 3 활성 예정) — Cross-reference 인터랙티브 그래프

**웹폰트 (CDN)**:
- `Pretendard@1.3.9` (jsDelivr) — 한국어 가독성 + dynamic subset (페이지당 사용 글자만 다운로드)

**외부 reference (workspace 내 PDF 6 종)**:
- 6 정부지원 사업 양식 PDF (37·41·67·71·74·150 페이지) — patterns and phrasing 차용 출처. CLAUDE.md §"Working with the reference PDFs" 규약 준수 (verbatim 차용 금지).

**선택 도입 (slaminar 추천 도구 — Step 7 사용자 결정)**:
- `promptfoo` (60 score) — LLM 프롬프트 평가 (Track 3 LLM·RAG 자산과 일부 정합)
- 그 외 `tdd-guard`·`test-kitchen` 등은 본 워크스페이스 (콘텐츠 작성 + 정적 빌드) 에 부합도 낮음.
<!-- slaminar:end:dependencies -->
