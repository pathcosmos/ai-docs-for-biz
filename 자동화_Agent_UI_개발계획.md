# Manufacturing AI 사업계획서 Agent + 전용 UI — 상세 개발 계획서 (Phase 1·2·3)

> 작성일: 2026-05-12 · 관련 작업로그: 엔트리 #70 · 분류: 메타 (개발 계획서) · 코드 작성 진입 직전 기준선
>
> 본 문서는 `자동화_시스템_구현_가능성_진단.md` v2 (#58·#60) 의 Phase 1·2·3 (Agent 오케스트레이터 + 전용 UI + Section Writers × 9) 의 **구현 직전 상세 사양**. Phase 0 (콘텐츠 갭 9 종, #66~#69, commit `99a60ee`) 완료 후 사용자 명시 — *"실제 개발 말고 계획까지만 세워 줘 별도 md 파일로 저장해주면 돼"*. 사용자 결정 3 항 (Section Writer 완전 병렬·UI Stepper 5 단계·ASCII Phase 4 분리) 반영판.

> 플레이스홀더 범례 — `[기간]` 일·주 단위 일정, `[수치]` 라인 수·필드 수, `[기관]` 외부 의존성. **(확인 필요)** — Cloudflare Worker 의 SSE 호환성·subrequest 한도·CPU time 한도, Gemini 모델 응답 평균 지연, 한국어 압축 후 실측 토큰 등은 Phase 1 착수 시 실측 후 §10 보정.

> 본 문서의 직접 근거 — `자동화_시스템_구현_가능성_진단.md` §3·§4·§5 (9 섹션 매핑·Agent 아키텍처·신규 파일 목록); 9 가이드 (BLK-COMPANY-01·EXEC-01·02·DATA-01·MODEL-01·PROB-01·GOAL-01·APPLIC-01·TRAIN-01·02·MLOPS-01·02) §3 본문 절 템플릿 (Section Writer 9 prompt 의 직접 입력); `worker/src/index.js` 236 줄 (현재 가동 중 `/api/llm` polish 모드 + `/api/agent/generate` SSE 라우트); `docs/javascripts/llm-client.js` 58 줄 (현재 Worker 프록시 클라이언트); `docs/data/templates.json` 1.46 MB / 348 블록 (Section Writer 의 블록 풀); CLAUDE.md "Conventions" (한국어 문어체·플레이스홀더·인용 출처).

> 구현 반영 현황 (2026-05-12, 엔트리 #72·#73) — 본 계획의 첫 실행 단위로 `/agent` Stepper UI, `worker/src/agent.js` SSE Agent MVP, `docs/data/templates_index.json` compact index 생성, Gemini Section Writer × 9 병렬 호출을 구현했다. API 기본은 deterministic fallback 이고, UI 기본은 Gemini 작성이다. 현재 남은 큰 범위는 9 가이드 본문/compact index 를 prompt context 로 더 깊게 주입하는 품질 보강, Validator 운영 보강, ASCII Phase 4 분리 구현이다. `templates.json` 은 현재 348 블록 / 1.46 MB, `templates_index.json` 은 348 블록 / 141,866 bytes / body 제외 상태로 갱신됐다.

---

## 1. Context — 위치·결정·기존 자산

### 1.1 Phase E19 단계 위치

- **완료**: Phase 0 (콘텐츠 갭 9 종 가이드 신설) — commit `99a60ee` / 작업로그 #66~#69
- **본 문서 대상**: Phase 1 (Worker Agent 골격) + Phase 2 (전용 UI + SSE) + Phase 3 (Section Writers × 9 완비) = **MVP 구현 직전 사양**
- **본 문서 외**: Phase 4 (ASCII deterministic 4 타입 + LLM 폴백) · Phase 5 (Validator 운영 보강) — 별도 사이클

### 1.2 사용자 결정 3 항 (본 문서의 1 차 입력)

| 결정 | 선택 | 근거 |
|---|---|---|
| Section Writer × 9 호출 방식 | **완전 병렬** (Promise.all, ~30 초) | Cloudflare Worker subrequest 한도 50 내 안전 · 스트림 UX 와 정합 (사용자 인내 한계 30 초~1 분) · 결합 맥락은 Stage 2 Outline 이 사전 결정 |
| UI 폼 구조 | **Stepper 5 단계** | Step 1 회사 → 2 사업 → 3 데이터·모델 → 4 설정 → 5 제출. 단계별 유효성 검증으로 외울·충돌 조기 차단. Tier 1 미입력 거부 (4.92) 적용 용이 |
| ASCII 모듈 포함 시점 | **Phase 4 분리 유지** | Phase 1·2·3 MVP = 본문만. ASCII 는 Phase 4 별도 사이클. 4.30 (에이전트 안전 영역) 정합 |

### 1.3 기존 자산 활용 매트릭스

| 자산 | 현재 줄수 | 본 개발에서의 처리 |
|---|---|---|
| `worker/src/index.js` | 236 | **EXTENDED** — `/api/llm` (polish) 보존 + `/api/agent/generate` (SSE) 신규 라우트 추가. `handleRequest()` 함수 분기 확장 완료 |
| `worker/src/index.js` 의 `callGeminiViaGateway()` (L96-135) | (함수) | **REUSE AS-IS** — agent.js 각 stage 가 공유 호출 |
| `docs/javascripts/llm-client.js` | 58 | **EXTEND** — `AiDocsLLM.call()` 단순 POST → `AiDocsLLM.stream()` SSE 수신 추가. 기존 polish 호출은 보존 |
| `docs/data/templates.json` | 1.46 MB / 348 블록 | **REUSE** — Worker 내부에서 본문 조회 (LLM 에 전체 전송 금지). compact index 별도 |
| `docs/data/templates_index.json` | 141 KB / 348 블록 | **CREATED** — `body` 제외 compact index. AI 매핑·Section Writer 후보 선정 입력으로 사용 |
| `hooks/build_templates_data.py` | 434 | **EXTENDED** — 신규 가이드 9 종 패턴 추가 후 compact index 생성 로직 신설 완료 |
| 9 가이드 (BLK-COMPANY·PROB·GOAL·EXEC·APPLIC·DATA·MODEL·TRAIN·MLOPS) | 약 2,360 (9 합산) | **READ-ONLY** — Section Writer 9 의 system prompt 컨텍스트로 1:1 주입 |
| `docs/generate.md` + `generate-template.js` | 170 + 403 | **KEEP DURING MVP** — `/agent` 검증 전까지 기존 수동 조립 UI 병행. 폐기는 Agent 품질·운영 검증 후 별도 결정 |

### 1.4 본 개발의 명시적 비목표 (Out of Scope)

- ❌ Phase 4 ASCII 모듈 (deterministic 4 generator + LLM 폴백) — 별도 사이클
- ❌ Phase 5 운영 보강 (rate limit·CORS·payload off·chunking·평가 데이터셋) — 별도 사이클
- ❌ 양식 스키마 5 종 (DX촉진 외) 확충 — 별도 사이클
- ❌ 사업계획서 결과의 PDF/HWP 변환 — 사용자가 .md 받아 자체 변환

> [출처: `자동화_시스템_구현_가능성_진단.md` §4·§5·§6 + 사용자 결정 3 항 (AskUserQuestion 응답, 2026-05-12) + `worker/src/index.js`·`docs/javascripts/llm-client.js` 현재 코드 실측]

---

## 2. Worker Agent Orchestrator — `worker/src/agent.js`

### 2.1 모듈 골격

```
worker/src/
├── index.js              (수정 — 라우트 분기)
├── agent.js              (신규 — 오케스트레이터·SSE)
├── stages/
│   ├── plan.js           (신규 — Stage 1 Planner)
│   ├── outline.js        (신규 — Stage 2 Outline)
│   ├── section.js        (신규 — Stage 3 Section Writer × 9)
│   ├── validate.js       (신규 — Stage 5 Validator)
│   ├── compile.js        (신규 — Stage 6 Compiler)
│   └── ascii.js          (신규, Phase 4 — placeholder 만)
├── prompts/              (신규)
│   ├── planner.md
│   ├── outline.md
│   ├── section_01.md ~ section_09.md  (9 종)
│   ├── ascii.md          (Phase 4)
│   └── validator.md
└── lib/
    ├── sse.js            (신규 — SSE 응답 빌더)
    ├── templates.js      (신규 — Worker 내 templates.json 조회)
    └── gemini.js         (신규 — callGeminiViaGateway 의 다중 prompt 지원 확장)
```

### 2.2 `/api/agent/generate` SSE 라우트 사양

- **HTTP method**: POST
- **Content-Type (request)**: `application/json`
- **Content-Type (response)**: `text/event-stream`
- **Origin allowlist**: 기존 `worker/src/index.js` 의 `isAllowedOrigin()` 재사용 (GitHub Pages·Cloudflare Pages 도메인만 허용)
- **응답 형식**: SSE (Server-Sent Events) — `event:` 필드 + `data:` JSON payload + `\n\n` 종결
- **연결 종료**: `event: complete` 또는 `event: error` 이벤트 송신 후 `controller.close()`

### 2.3 ReadableStream 기반 응답 빌더 (사양)

```text
async function buildSSEResponse(profile, settings, env, fetchImpl) {
    const stream = new ReadableStream({
        async start(controller) {
            const send = (event, data) => {
                controller.enqueue(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
            };
            try {
                send('connected', { at: new Date().toISOString() });
                const plan = await runPlanner(send, profile, settings, env, fetchImpl);
                const outline = await runOutline(send, plan, profile, env, fetchImpl);
                const sections = await runSectionWriters(send, outline, profile, env, fetchImpl);
                const validation = await runValidator(send, sections, profile, env, fetchImpl);
                const finalMd = await runCompiler(send, sections, validation, profile, env);
                send('complete', { final_md: finalMd, usage: { ... }, meta: { ... } });
            } catch (error) {
                send('error', { stage: error.stage, code: error.code, message: error.message });
            }
            controller.close();
        }
    });
    return new Response(stream, {
        headers: { ...corsHeaders, 'Content-Type': 'text/event-stream' }
    });
}
```

> ⚠ Cloudflare Worker 의 SSE 동작 (확인 필요) — Workers Free 의 CPU time 30 초 한도가 SSE 장기 유지에 영향. Workers Paid (CPU 30 분) 또는 Cloudflare Workers Streams API 사용 필수.

### 2.4 Cloudflare Worker 한도 정합

| 한도 | 무료 | Paid (Bundled / Unbound) | 본 개발 정합 |
|---|---|---|---|
| Subrequest | 50 | 50 / 1000 | 9 Section + 1 Planner + 1 Outline + 1 Validator = 12-14, 안전 마진 큼 |
| CPU time | 10 ms (start) / 30 s (request) | 30 s / 30 분 | SSE 1 회 생성 ~30 초~2 분 → **Paid Unbound 권장** |
| Request size | 100 MB | 동일 | 입력 ~ 50 KB (95 fields 분류 + templates_index.json compact) → 안전 |
| Response size | 100 MB | 동일 | 출력 ~ 200 KB (9 섹션 .md + 메타) → 안전 |
| KV·Durable Objects | 사용 (선택) | 동일 | **본 MVP 미사용** — stateless 처리 |

> [출처: Cloudflare Workers Limits — `https://developers.cloudflare.com/workers/platform/limits/` (확인 필요 — 2026-05 기준 갱신 점검 필수)]

---

## 3. 6 Stages 상세 명세

### 3.1 Stage 1 — Planner (`stages/plan.js`)

| 항목 | 명세 |
|---|---|
| 목적 | 사용자 프로필 → 시나리오·패키지·도메인 매칭 결정 |
| 입력 schema | `{ profile: { company, industry, scale, ... 95 fields }, templates_index: { 348 entries × 7 fields } }` |
| LLM prompt | `prompts/planner.md` — "사용자 입력을 기반으로 적합한 시나리오 ID 1-9 개·패키지 후보·도메인 태그 (STL·MET·RUB·UTL·MLO·LLM·SAF) 결정" |
| LLM 호출 | Gemini Flash 1 회 (~ 8 K 입력 / ~ 2 K 출력) |
| 출력 schema | `{ scenarios: ["SCN-STL-01", ...], package: "pkg2", domain: "STL", reasoning: "..." }` |
| Timeout | 15 초 |
| 오류 처리 | Gemini 응답 schema 위반 시 → fallback (사용자 프로필 의 `[업종]` 직접 매핑) |
| SSE 이벤트 | `stage_start { stage: "planner" }` → `stage_done { stage: "planner", duration_ms, partial: { scenarios, package } }` |

### 3.2 Stage 2 — Outline (`stages/outline.js`)

| 항목 | 명세 |
|---|---|
| 목적 | 9 섹션 outline (절별 키워드·요구 표 수·인용 블록 목록) + ASCII 삽입 지점 명세 (Phase 4 입력) |
| 입력 schema | `{ profile, plan: Stage 1 결과 }` |
| LLM prompt | `prompts/outline.md` — "9 섹션 (§1·2·3·4·5·6·7·8·9) 의 절별 outline + 각 절의 인용 블록 ID 추천 + ASCII 삽입 지점 N 개 명세" |
| LLM 호출 | Gemini Flash 1 회 (~ 6 K 입력 / ~ 4 K 출력) |
| 출력 schema | `{ sections: [{ id: "§1", subsections: [...], blocks_to_cite: [...], ascii_slots: [...] }, ... × 9] }` |
| Timeout | 20 초 |
| SSE 이벤트 | `stage_done { stage: "outline", partial: { section_count, ascii_slot_count } }` |

### 3.3 Stage 3 — Section Writers × 9 (`stages/section.js`) — **완전 병렬**

| 항목 | 명세 |
|---|---|
| 목적 | 9 섹션 본문 동시 생성 — Promise.all 9 호출 |
| 입력 schema (각 Writer) | `{ section_id: "§N", outline_subsections: [...], blocks: [{ id, title, body }], guide: "BLK-XXX-01 본문", profile }` |
| LLM prompt (각) | `prompts/section_0N.md` — 가이드 §3 본문 절 템플릿을 그대로 시스템 prompt 컨텍스트 + 사용자 프로필 치환 지침 |
| LLM 호출 | Gemini Flash × 9 병렬 (각 ~ 12 K 입력 / ~ 3 K 출력) |
| 출력 schema | `{ section: "§N", markdown: "...", citations: ["block_id1", ...], placeholders_unfilled: [], domain_examples_used: [] }` |
| Timeout | 각 Writer 30 초, 전체 30 초 (가장 느린 1 회) |
| 오류 처리 | 1 Writer 실패 시 → 그 섹션만 fallback (가이드 §3 템플릿 그대로 + placeholder 치환만, LLM 적응 생략) |
| SSE 이벤트 | 9 회 `section_start { section, at }` + 9 회 `section_done { section, markdown, citations }` (병렬 도착 순) |

#### 3.3.1 Promise.all 완전 병렬 설계

```text
const writers = [1,2,3,4,5,6,7,8,9].map(i => 
    runSectionWriter(i, outline.sections[i-1], profile, env, fetchImpl)
        .then(result => { send('section_done', result); return result; })
        .catch(error => { send('section_error', { section: i, error }); return fallback(i); })
);
const sections = await Promise.all(writers);
```

#### 3.3.2 9 Writer 의 결합 맥락 — Outline 이 사전 결정

각 Writer 는 독립 호출이지만, 결합 일관성 (예: §6 X 정의 ↔ §7 모델 후보) 은 **Stage 2 Outline 이 사전에 키워드·블록 ID·placeholder 수치 합의** 로 보장. 9 Writer 는 outline 의 합의된 컨텍스트를 받아 본문 작성만 수행.

### 3.4 Stage 4 — ASCII Generator (`stages/ascii.js`, Phase 4 까지 placeholder 만)

| 항목 | Phase 1·2·3 MVP 명세 |
|---|---|
| 목적 | Phase 4 까지 — Outline 의 ascii_slots 위치에 `<!-- ASCII placeholder: [도식설명] -->` 주석 삽입만 |
| 입력 | sections[1..9] + outline.ascii_slots |
| 처리 | placeholder 텍스트로 치환, LLM 호출 없음 |
| 출력 schema | sections[1..9] (ASCII slot 자리에 주석 텍스트 삽입) |
| SSE 이벤트 | `stage_skipped { stage: "ascii", reason: "phase4_separate" }` |

### 3.5 Stage 5 — Validator (`stages/validate.js`)

| 항목 | 명세 |
|---|---|
| 목적 | 인용 보존·플레이스홀더·수치 일관성 자동 그렙 + 톤·논리 LLM 채점 |
| 입력 schema | `{ sections: [{ markdown, citations }], outline, profile }` |
| 처리 | (a) 자동 그렙 — `> [출처: ...]` 매칭 vs Outline blocks_to_cite 의 100 % 보존 검사 (b) 미치환 placeholder `[변수]` 카운트 (c) 수치 일관성 (profile.[수치] vs 본문 수치) (d) LLM 1 회 — 톤 일관성·논리 정합 채점 (0-100) |
| LLM 호출 | Gemini Flash 1 회 (~ 20 K 입력 / ~ 1 K 출력 채점 보고) |
| 출력 schema | `{ citation_preservation: %, placeholder_unfilled: [...], numeric_inconsistencies: [...], tone_score: 0-100, sections_to_rewrite: [] }` |
| Timeout | 30 초 |
| SSE 이벤트 | `validation { report }` |

### 3.6 Stage 6 — Compiler (`stages/compile.js`)

| 항목 | 명세 |
|---|---|
| 목적 | sections × ASCII placeholder → 단일 .md 조립 + YAML frontmatter |
| 입력 schema | `{ sections, validation, profile, plan, outline }` |
| 처리 | (a) §1·2·...·9 본문 H1 정렬 조립 (b) YAML frontmatter — 메타 (`generated_at`, `model`, `scenarios`, `package`, `domain`, `citations_count`, `placeholders_count`, `validation_score`) (c) 사용자 친화 부록 (어떤 가이드 인용했는지 목록) |
| LLM 호출 | 0 회 (deterministic) |
| 출력 schema | `{ final_md: "...", meta: { ... } }` |
| Timeout | 5 초 |
| SSE 이벤트 | `complete { final_md, meta }` |

### 3.7 6 Stage 호출 순서·타이밍 추정

```
Stage 1 (Planner)     :  0s ─────  15s   [Gemini 1 회]
Stage 2 (Outline)     : 15s ─────  35s   [Gemini 1 회]
Stage 3 (Sections × 9): 35s ─── ~65s    [Gemini 9 회 병렬, 가장 느린 1 회]
Stage 4 (ASCII)       : 65s ───  66s   [Phase 4 까지 skip]
Stage 5 (Validator)   : 66s ─── ~95s   [그렙 + Gemini 1 회]
Stage 6 (Compiler)    : 95s ─── 100s   [deterministic]
총 ~ 100 초 (~ 1.5 분)
```

> ⚠ **Cloudflare Worker Free CPU 30 초 한도 초과 — Paid Unbound 필수**.

> [출처: 사용자 결정 3 항 + 본 개발의 사양 추정 + Cloudflare Workers Streams API 문서 (확인 필요)]

---

## 4. 9 Section Writers 매핑 표

각 Writer 의 system prompt 컨텍스트로 Phase 0 의 가이드 1 종을 1:1 주입. 가이드 §3 본문 절 템플릿이 직접 system prompt 본문이 됨.

| § | 섹션명 | system prompt 파일 | 주입 가이드 (BLK) | 블록 검색 키워드 | 입력 변수 (profile 부분집합) |
|---|---|---|---|---|---|
| 1 | 현황 | `prompts/section_01.md` | `가이드_회사_프로필_템플릿.md` (BLK-COMPANY-01) | "현황·인적 의존성·데이터 단절·기존 시스템" | company·industry·scale·revenue·employees·systems·certifications |
| 2 | 문제인식 | `prompts/section_02.md` | `가이드_문제_식별_매트릭스.md` (BLK-PROB-01) | "4 축·심각도·pain point·AS-IS" | operational_pain·data_pain·knowledge_pain·control_pain·external_pressure |
| 3 | 개선방향 | `prompts/section_03.md` | `가이드_개선_KPI_분해.md` (BLK-GOAL-01) | "KPI·목표·AI 기여도·단계별 도달" | primary_kpi·baseline·target·ai_contribution_pct·secondary_kpi |
| 4 | 수행방향 | `prompts/section_04.md` | `가이드_사업_수행_로드맵.md` (BLK-EXEC-01·02) | "phase·RACI·예산·M/M·외부 위탁·위험" | duration_months·form_type·trl_start·trl_end·total_budget·gov_pct·total_mm·track_mix·專_org·consulting·outsourcing·collaborators·risks |
| 5 | AI 적용 포인트 | `prompts/section_05.md` | `가이드_시나리오_ROI_분석.md` (BLK-APPLIC-01) | "시나리오 선정·5.2 카드·ROI·시너지" | selected_scenarios·investment_per_scn·effect_per_scn·payback·synergies |
| 6 | 데이터·변수 | `prompts/section_06.md` | `가이드_데이터_명세_변수_구조.md` (BLK-DATA-01) | "X·y·전처리·라벨링·분할·거버넌스" | raw_sources·X_candidates·X_format·y_target·y_problem_type·preprocessing·labeling·split·governance |
| 7 | 모델·학습 | `prompts/section_07.md` | `가이드_모델_선정_학습_기법.md` (BLK-MODEL-01) | "모델 후보·학습 전략·HPO·검증·baseline·리스크" | model_candidates·training_strategy·hpo·evaluation·baselines·model_risks |
| 8 | 적용·배포 | `prompts/section_08.md` | `가이드_적용_배포_방안.md` (BLK-TRAIN-01·02) | "배포 아키텍처·통합·HITL·교육·변화관리" | deployment_location·integration_systems·hitl_scenarios·training_curriculum·change_management |
| 9 | MLOps loop | `prompts/section_09.md` | `가이드_MLOps_거버넌스_리츄얼.md` (BLK-MLOPS-01·02) | "모니터링·드리프트·재학습·챔피언챌린저·리츄얼" | monitoring·drift_threshold·retraining_trigger·champion_challenger·governance_ritual |

### 4.1 system prompt 의 구조 표준 (9 종 모두 동일 골격)

```
당신은 한국 정부 R&D 사업계획서 §N (섹션명) 작성 전문가입니다.

[가이드 컨텍스트 — system prompt 의 직접 인용]
{guide_md_body}  ← 약 200-300 줄

[Outline 컨텍스트]
{outline.sections[N-1]}

[사용자 프로필]
{profile_subset for §N}

[관련 블록 본문 (Worker 내 templates.json 조회 결과)]
{blocks[5-15 개]}

[작업 지침]
1. 가이드 §3 본문 절 템플릿을 답습 (8 장 구조 중 §3)
2. [플레이스홀더] 를 사용자 프로필 입력으로 치환
3. 인용 출처 표기 (> [출처: ...]) 100 % 보존
4. 6 도메인 적용 예시 (가이드 §4) 중 사용자 [업종] 행 만 답습
5. 인용 강도 (가이드 §5) — 사용자 [기간]·[양식유형] 기반 강·중·약 자동 선택
6. 한국어 formal 문어체 (~한다·~된다 종결)

[출력 형식]
{ markdown: "...", citations: [...], placeholders_unfilled: [] }
```

> [출처: 9 가이드 §3 본문 절 템플릿 + `가이드_회사_프로필_템플릿.md` §5 인용 강도 3 단계 표준]

---

## 5. SSE Wire Protocol — 7 이벤트

### 5.1 이벤트 종류

| event | 시점 | data schema |
|---|---|---|
| `connected` | 연결 직후 | `{ at: ISO8601 }` |
| `stage_start` | 각 stage 호출 시작 | `{ stage: "planner"\|"outline"\|"validate"\|"compile", at }` |
| `stage_done` | 각 stage 호출 완료 | `{ stage, duration_ms, partial: {...} }` |
| `section_start` | 9 Section Writer 시작 (병렬, 9 회) | `{ section: "§N", at }` |
| `section_done` | 9 Section Writer 완료 (병렬 도착 순) | `{ section, markdown, citations, placeholders_unfilled, duration_ms }` |
| `validation` | Stage 5 완료 | `{ report: { citation_preservation, placeholder_unfilled, tone_score, ... } }` |
| `complete` | Stage 6 완료 + 종료 | `{ final_md, meta: { ... }, usage: { total_tokens, model } }` |
| `error` | 단계 실패 | `{ stage, code, message, recoverable: bool }` |

### 5.2 이벤트 시퀀스 (정상 흐름)

```
connected
stage_start { planner }
stage_done { planner, partial: { scenarios, package, domain } }
stage_start { outline }
stage_done { outline, partial: { section_count: 9, ascii_slot_count: N } }
section_start × 9 (동시)
section_done × 9 (병렬 도착 순)
stage_start { validate }
stage_done { validate }
validation { report }
stage_start { compile }
complete { final_md, meta, usage }
```

### 5.3 클라이언트 reconnect·재시도 정책

| 시나리오 | 정책 |
|---|---|
| SSE 연결 끊김 (네트워크) | UI 측 자동 reconnect — 단, 진행 상태는 server-side stateless 라 처음부터 재시작 |
| `error { recoverable: true }` | UI 측 retry 버튼 노출 + 자동 재시도 1 회 |
| `error { recoverable: false }` | UI 측 오류 화면 + 사용자에 입력 수정 권유 |
| Worker timeout (CPU 한도) | `error { stage, code: "worker_timeout" }` 송신 후 종료 |

> [출처: 본 개발의 SSE wire protocol 사양 — Phase 1 착수 시 첫 구현 + Cloudflare Workers Streams API (확인 필요)]

---

## 6. Compact Index 빌더 — `hooks/build_templates_data.py`

### 6.1 사양

| 항목 | 명세 |
|---|---|
| 입력 | `docs/data/templates.json` (1.46 MB / 348 블록) |
| 출력 | `docs/data/templates_index.json` (141,866 bytes / 348 블록, body 제외) |
| 추출 필드 | id·title·category·section·package·domain·tags·preview (body 제외) |
| 빌드 시점 | `build_src.py` 후속 자동 실행 — mkdocs build 매 회 갱신 |
| 사용처 | Stage 1 Planner LLM prompt 의 컨텍스트 (전체 본문 전송 차단) |

### 6.2 처리 흐름 (엔트리 #72 에서 구현 완료)

```
1. templates.json 로드
2. 각 블록에서 body 필드 제거
3. preview 필드 = 기존 80 자 그대로 유지
4. id·title·category·section·package·domain·tags 7 필드만 보존
5. templates_index.json 으로 저장
6. 크기 검증 — 결과 ≤ 100 KB 안전 (LLM 호출 시 8 K 토큰 내)
```

### 6.3 hooks/build_templates_data.py 확장 옵션

별도 신설 (`build_templates_index.py`) vs 기존 확장. 권장 — **기존 확장**. 이유: build pipeline 1 곳 유지·hook 등록 단순.

> [출처: `hooks/build_templates_data.py` 407 줄 (현재) + `자동화_시스템_구현_가능성_진단.md` §3.0 ④ "AI 매핑 compact index 기반"]

---

## 7. Stepper 5 단계 UI 사양

### 7.1 HTML 구조 — `docs/agent.md`

```
[hero] AI 사업계획서 자동 작성 Agent
[stepper bar] (1) 회사  (2) 사업  (3) 데이터·모델  (4) 설정  (5) 제출
[step 1 panel] (active by default)
    Tier 1 9 필드 (필수)
    Tier 2 9 필드 (권장)
    Tier 3 6 필드 (선택, 접힘)
    [Next →] (Tier 1 미입력 시 disabled)
[step 2 panel] (hidden)
    ...
...
[step 5 panel] (hidden — 제출 시 활성화)
    [Submit] → SSE 진행 표시
    [Progress bar] 6 stage / 9 section / 검증 / 완료
    [Partial preview] section_done 도착 순 부분 표시
    [Final result] complete 시 .md 다운로드 + frontmatter 메타
```

### 7.2 agent-ui.js 모듈 분해

| 모듈 | 책임 |
|---|---|
| `StepperController` | 5 step 간 전환·current step 추적·Tier 1 검증 통과 시만 next 허용 |
| `FormValidator` | 각 step 의 Tier 1·2·3 필드 유효성 (필수 누락·형식·범위) |
| `SSEReceiver` | EventSource 또는 fetch + ReadableStream 으로 SSE 수신·이벤트 dispatcher |
| `ProgressBar` | 6 stage × 9 section 의 시각적 진행 (현재 stage·각 section 도착 시 체크) |
| `PartialPreview` | section_done 도착 순 markdown 부분 표시 (collapsible) |
| `Downloader` | complete 시 final_md → Blob → .md 다운로드 + 클립보드 복사 + 메타 표시 |
| `LocalStorage` | 각 step 의 form input 자동 저장 (key: `agent_step_N`) + 재방문 시 복원 |

### 7.3 agent.css 스타일 클래스

| 클래스 | 용도 |
|---|---|
| `.agent-stepper` | 상단 stepper bar (5 단계 표시) |
| `.agent-step--active` / `.agent-step--done` / `.agent-step--pending` | 단계별 상태 |
| `.agent-form-section` | 각 step 의 폼 컨테이너 |
| `.agent-tier1` / `.agent-tier2` / `.agent-tier3` | Tier 별 시각적 분리 |
| `.agent-progress` | 진행 bar 컨테이너 |
| `.agent-progress-stage` / `.agent-progress-section` | stage·section 별 인디케이터 |
| `.agent-partial` | section_done 부분 결과 collapsible |
| `.agent-final` | complete 시 최종 결과 영역 |
| `.agent-error` | error 시 오류 메시지 |

### 7.4 localStorage 자동 저장·복원

| key | value | 갱신 시점 |
|---|---|---|
| `agent_step_1` | Step 1 폼 입력 (JSON) | onBlur each field |
| `agent_step_2` | Step 2 폼 입력 | 동일 |
| `agent_step_3` | Step 3 폼 입력 | 동일 |
| `agent_step_4` | Step 4 폼 입력 | 동일 |
| `agent_current_step` | 현재 step 번호 | step 전환 시 |
| `agent_last_result` | complete 시 final_md + meta | complete 도착 시 |

**재방문 시**: localStorage 의 step 1-4 복원 + current_step 로 이동 + last_result 있으면 결과 영역 표시.

### 7.5 Tier 1 미입력 거부 정책 (4.92 답습)

각 step 의 Tier 1 필드 미입력 시 `[Next →]` 버튼 disabled + 누락 필드 빨간 테두리. step 5 제출 전 5 step Tier 1 전수 통과 검증.

> [출처: 9 가이드 §2 입력 스키마 3 Tier · CLAUDE.md "Conventions" · `방법론_총론.md` §3 4.92 (Tier 1 미입력 거부 정책)]

---

## 8. POST /api/agent/generate API 스키마

### 8.1 Request Body — 5 Step 합산 약 95 필드

| Step | 출처 가이드 | Tier 1 | Tier 2 | Tier 3 | 합 |
|---|---|---|---|---|---|
| Step 1 회사 | COMPANY-01 | 9 | 9 | 6 | 24 |
| Step 2 사업 | EXEC-01·02 | 8 | 8 | 6 | 22 |
| Step 3 데이터 | DATA-01 | 9 | 12 | 4 | 25 |
| Step 3 모델 | MODEL-01 | 9 | 11 | 4 | 24 |
| Step 4 설정 (LLM 모델·생성 옵션) | — | 2 | 2 | 0 | 4 |
| **합계** | | **37** | **42** | **20** | **99** |

> Step 4 의 4 필드는 본 개발에서 신설 — `gemini_model` (default `gemini-2.5-flash`), `output_strength` (강·중·약), `include_ascii` (false MVP), `language` (ko default).

### 8.2 Request body 예시 (개념)

```json
{
  "profile": {
    "step1_company": { "company": "...", "industry": "STL", ... 24 fields ... },
    "step2_business": { "duration_months": 12, "form_type": "단년", ... 22 fields ... },
    "step3_data_model": { "raw_sources": [...], "X_candidates": [...], ... 49 fields ... },
    "step4_settings": { "gemini_model": "gemini-2.5-flash", "output_strength": "중", ... }
  }
}
```

### 8.3 Response — SSE Stream (위 §5)

### 8.4 Error Code 표

| code | HTTP | 의미 | 사용자 대응 |
|---|---|---|---|
| `tier1_missing` | 400 | Tier 1 필드 미입력 | 폼 수정 |
| `payload_too_large` | 413 | profile size ≥ 100 KB | 필드 축소 |
| `origin_forbidden` | 403 | Origin allowlist 위반 | (개발자 설정 점검) |
| `gemini_error` | 502 | Gemini API 실패 | 자동 재시도 1 회 후 사용자 알림 |
| `worker_timeout` | 504 | Cloudflare CPU 한도 초과 | Workers Paid 전환 검토 |
| `validator_failed` | 200 (SSE error event) | 검증 점수 임계 미달 (재작성 필요 섹션 ≥ 3) | UI 측 재시도 or 사람 검수 권유 |

> [출처: `worker/src/index.js` 현재 error 처리 패턴 + 본 개발 신규 사양]

---

## 9. 개발 일정 분해 (Day 단위)

### 9.1 Phase 1 — Worker Agent 골격 (2 주, Day 1-10)

| Day | 작업 | 산출물 | 검증 |
|---|---|---|---|
| 1 | `worker/src/agent.js` 골격 + SSE 응답 빌더 | `agent.js` 100 줄 (controller·send 함수만) | curl 로 SSE 응답 헤더 확인 |
| 2 | `worker/src/index.js` 라우트 분기 (`/api/llm` + `/api/agent/generate`) | `index.js` 50 줄 추가 | OPTIONS + POST 모두 응답 |
| 3-4 | `stages/plan.js` — Planner LLM 호출 + 응답 schema 검증 | `plan.js` 80 줄 + `prompts/planner.md` 50 줄 | 더미 profile 로 plan 응답 정상 |
| 5-6 | `stages/outline.js` — Outline LLM 호출 + 9 섹션 outline 출력 | `outline.js` 80 줄 + `prompts/outline.md` 60 줄 | plan → outline 연결 정상 |
| 7 | `lib/gemini.js` — callGeminiViaGateway 다중 prompt 지원 | `gemini.js` 60 줄 (기존 함수 확장) | 단위 테스트 (모킹) |
| 8 | `lib/templates.js` — Worker 내 templates.json 조회 | `templates.js` 40 줄 | 9 섹션 블록 ID 매핑 정상 |
| 9 | `hooks/build_templates_data.py` 기존 확장 | `templates_index.json` 141 KB / 348 블록 | `body` 제외 + 7 필드 보존 완료. 100 KB 이하 축소는 후속 최적화 |
| 10 | Stage 1·2 + 6 (Compiler) end-to-end | `agent.js` orchestrator 완성 + `stages/compile.js` 80 줄 | curl SSE → connected·stage_start·stage_done × 3·complete 정상 수신 |

**Phase 1 마일스톤**: Planner·Outline·Compiler 만으로 dummy 9 섹션 outline + frontmatter 산출. Section Writer 와 Validator 는 미구현 (Phase 3).

### 9.2 Phase 2 — 전용 UI + SSE 통합 (2 주, Day 11-20)

| Day | 작업 | 산출물 | 검증 |
|---|---|---|---|
| 11-12 | `docs/agent.md` HTML 구조 + Stepper 5 단계 골격 | `agent.md` 200 줄 | 5 step 간 전환 동작 |
| 13 | `agent.css` — Stepper·폼·진행·결과 영역 스타일 | `agent.css` 400 줄 | Material Design 정합 시각 검증 |
| 14-15 | `agent-ui.js` — StepperController + FormValidator | 200 줄 | Tier 1 미입력 시 Next disabled |
| 16 | `agent-ui.js` — LocalStorage 자동 저장·복원 | 80 줄 추가 | 새로고침 시 입력 복원 |
| 17-18 | `agent-ui.js` — SSEReceiver + ProgressBar + PartialPreview | 200 줄 추가 | Phase 1 SSE 응답 수신·표시 |
| 19 | `agent-ui.js` — Downloader (최종 .md + 클립보드 + 메타) | 80 줄 추가 | complete 도착 → 다운로드 동작 |
| 20 | 레거시 폐기 (`docs/generate.md`·`generate-template.js` 삭제) + `mkdocs.yml`·`slug_map.yml` 갱신 | 4 파일 변경 | 빌드 정상·`/generate` 404 |

**Phase 2 마일스톤**: Stepper UI 완성 + Phase 1 의 dummy 9 outline 까지 SSE 정상 수신·표시. Section Writer 까지 가는 흐름은 placeholder.

### 9.3 Phase 3 — Section Writers × 9 완비 (2 주, Day 21-30)

| Day | 작업 | 산출물 | 검증 |
|---|---|---|---|
| 21-22 | `stages/section.js` 골격 + Promise.all × 9 + section_start·section_done 이벤트 | `section.js` 150 줄 | 9 회 병렬 호출 + 도착 순 이벤트 송신 |
| 23-25 | `prompts/section_01.md` ~ `section_09.md` 9 종 작성 (가이드 §3 본문 절 직접 인용) | 9 prompt 총 ~ 1200 줄 | 각 §N 본문 정상 출력 |
| 26 | `stages/validate.js` — 그렙 (인용·placeholder·수치) + LLM 채점 | `validate.js` 150 줄 + `prompts/validator.md` 40 줄 | 인용 보존율·placeholder 미치환 검증 정상 |
| 27 | `stages/compile.js` — sections × ASCII placeholder → 단일 .md + YAML frontmatter | `compile.js` 80 줄 | 9 섹션 합쳐서 최종 .md 산출 |
| 28-29 | 6 도메인 end-to-end 시나리오 검증 (철강 대기업·중견 냉연·특수강관·고무·정밀가공·유틸) — 각 1 회 SSE 호출 → .md 산출 → 사람 수정율 측정 | 6 결과 .md + 검증 리포트 | 사용자 수정율 ≤ 40 % |
| 30 | 튜닝 (prompt 조정·블록 검색 매핑 보정·placeholder 채움 정책) + MVP 종료 | 9 prompt 조정 + section.js 미세 보정 | end-to-end 정상 동작 |

**Phase 3 마일스톤**: 6 도메인 모두 9 섹션 .md 완성. MVP 사용 가능. 사용자 수정율 ≤ 40 %.

### 9.4 총 일정 요약

| Phase | 기간 | 핵심 산출물 |
|---|---|---|
| Phase 1 | 2 주 (Day 1-10) | Worker `/api/agent/generate` SSE + Planner·Outline·Compiler |
| Phase 2 | 2 주 (Day 11-20) | Stepper 5 단계 UI + SSE 수신 + 레거시 폐기 |
| Phase 3 | 2 주 (Day 21-30) | Section Writers × 9 (병렬) + Validator + 6 도메인 end-to-end |
| **MVP 완료** | **6 주** | **사용자 첫 사용 가능** |

> Phase 4 (ASCII) + Phase 5 (운영 보강) 는 별도 사이클 — 본 문서 외.

---

## 10. 검증·위험·한계

### 10.1 단위·통합 테스트

| 테스트 | 대상 | 방법 |
|---|---|---|
| 단위 (Worker) | 각 stage 함수 — 입력 schema 정상·출력 schema 정상 | Vitest (모킹 fetch) — `worker/test/` 별도 |
| 단위 (UI) | StepperController·FormValidator·SSEReceiver | Vitest jsdom |
| 통합 (Worker) | `/api/agent/generate` end-to-end with stubbed Gemini | wrangler dev + curl |
| 통합 (UI ↔ Worker) | Stepper 5 step 입력 → SSE 진행 → 다운로드 | Playwright (Chrome) |
| 도메인 검증 | 6 도메인 시나리오 각 1 회 | 사람 검토 (사용자 수정율 측정) |

### 10.2 Cloudflare Worker 한계 위험

| 한계 | 영향 | 완화 |
|---|---|---|
| CPU time 30 초 (Free) | SSE 1 회 ~ 100 초 → 초과 | **Paid Unbound (CPU 30 분) 필수** — 비용 ~ $5/월 + 사용량 |
| Subrequest 50 | 9 + 4 = 13 회 안전 | 사용량 ↑ 시 모니터 |
| Response size 100 MB | 출력 ~ 200 KB 안전 | 무관 |
| KV·Durable Objects 미사용 | stateless 처리 | 재시도·복원 한계 — UI localStorage 로 대체 |

### 10.3 한국어 압축 (4.34) 토큰 비용

- 9 가이드 system prompt 합산 ~ 2,360 줄 → 1 Section Writer 호출당 본인 가이드 1 종 ~ 250 줄 ≈ 5 K 토큰 + Outline + 블록 본문 5-10 K + profile 1 K = **호당 ~ 12-16 K 입력**
- 출력 ~ 3 K (한국어 압축)
- 1 사업계획서 = 9 Section + 1 Planner + 1 Outline + 1 Validator = 12 호출 × 평균 입력 12 K + 출력 3 K = **~ 180 K 입력 + 36 K 출력 = ~ 약 $0.5-1.5 / 건** (Gemini Flash 기준)

### 10.4 fallback·롤백 정책

| 시나리오 | 정책 |
|---|---|
| 1 Section Writer 실패 | 그 섹션만 가이드 §3 템플릿 + placeholder 치환 fallback |
| Planner·Outline 실패 | 사용자에 입력 수정 권유 (재시도 자동 1 회) |
| Validator 점수 미달 (재작성 권유 ≥ 3 섹션) | UI 측 "사람 검수 권유" 화면 + 재시도 옵션 |
| Compiler 실패 | 9 섹션 markdown 그대로 다운로드 (frontmatter·메타 제외) |
| 전체 Worker timeout | UI 측 오류 + 입력 복원 (localStorage) |

### 10.5 (확인 필요) 항목

- Cloudflare Workers Streams API 의 SSE 정확한 동작 패턴 — 1 차 구현 후 실측
- Gemini Flash 의 9 병렬 호출 시 rate limit (개별 토큰·동시 처리)
- 한국어 압축 후 실측 토큰 (현 추정 4.34 → 0.5)
- Cloudflare Workers Paid Unbound 의 9 Section 병렬 시 CPU time 측정
- 9 가이드 의 system prompt 컨텍스트 캐싱 가능 여부 (Gemini context caching API)

---

## 부록. 관련 작업로그·자산 cross-reference

- `작업로그.md` 엔트리 #58·#60·#61·#62·#63·#64·#65·#66·#67·#68·#69·#70·#72 — Phase E19 전체 흐름
- `자동화_시스템_구현_가능성_진단.md` v2 — 본 개발의 high-level 진단·전체 Phase 1-5 계획
- `방법론_총론.md` §3 — 4.30·4.34·4.82~4.99 — 본 개발의 운영 원칙
- 9 가이드 (BLK-COMPANY·PROB·GOAL·EXEC·APPLIC·DATA·MODEL·TRAIN·MLOPS) — Section Writer 9 의 system prompt 직접 입력
- `worker/src/index.js` + `worker/src/agent.js` + `wrangler.toml` — Phase 1 MVP 구현 대상
- `docs/agent.md` + `docs/javascripts/agent-ui.js` + `docs/stylesheets/agent.css` — Phase 2 Stepper UI MVP 구현 대상

> [본 문서 = Phase E19 / Phase 1·2·3 의 구현 직전 상세 사양. 엔트리 #72 에서 `/agent` UI + Worker SSE + compact index 의 Phase 1 MVP 를 구현했다. 남은 핵심 범위는 Gemini 기반 Section Writer × 9 병렬화, Validator 운영 보강, ASCII Phase 4 분리 구현이다.]
