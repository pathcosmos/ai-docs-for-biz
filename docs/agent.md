---
title: "Agent 자동 작성"
description: "5 단계 입력으로 9 섹션 사업계획서 초안을 생성"
hide:
  - toc
---

# Agent 자동 작성

<div id="agent-app" class="agent-app" data-agent-endpoint="https://ai-docs-for-biz-llm.pathcosmos.workers.dev/api/agent/generate" data-template-index-path="../data/templates_index.json" markdown="1">

<div class="agent-layout" markdown="1">

<section class="agent-workspace" markdown="1">

<ol class="agent-stepper" aria-label="작성 단계">
  <li class="agent-step is-active" data-step-indicator="1">회사</li>
  <li class="agent-step" data-step-indicator="2">사업</li>
  <li class="agent-step" data-step-indicator="3">데이터·모델</li>
  <li class="agent-step" data-step-indicator="4">설정</li>
  <li class="agent-step" data-step-indicator="5">제출</li>
</ol>

<form id="agent-form" class="agent-form">

<section class="agent-panel is-active" data-step="1" aria-labelledby="agent-step-1">
<h2 id="agent-step-1">회사</h2>
<div class="agent-fields">
  <label>고객사명 <input name="step1_company.company" data-required="true" autocomplete="organization" placeholder="동국제강" /></label>
  <label>업종 <select name="step1_company.industry" data-required="true">
    <option value="">선택</option>
    <option value="STL">철강</option>
    <option value="RUB">고무·폴리머</option>
    <option value="MET">정밀가공</option>
    <option value="UTL">유틸·ESG</option>
    <option value="LLM">LLM·RAG</option>
  </select></label>
  <label>대상 공정 <input name="step1_company.process" data-required="true" placeholder="후판 압연" /></label>
  <label>기업 규모 <select name="step1_company.scale" data-required="true">
    <option value="">선택</option>
    <option>중소</option>
    <option>중견</option>
    <option>대기업</option>
  </select></label>
  <label>핵심 보유 시스템 <input name="step1_company.systems" placeholder="MES, SCADA, QMS" /></label>
  <label>인증·표준 <input name="step1_company.certifications" placeholder="IATF 16949, ISO 9001" /></label>
</div>
</section>

<section class="agent-panel" data-step="2" aria-labelledby="agent-step-2">
<h2 id="agent-step-2">사업</h2>
<div class="agent-fields">
  <label>사업 기간 <select name="step2_business.duration_months" data-required="true">
    <option value="">선택</option>
    <option value="6">6 개월</option>
    <option value="9">9 개월</option>
    <option value="12">12 개월</option>
    <option value="18">18 개월</option>
    <option value="24">24 개월</option>
    <option value="33">33 개월</option>
  </select></label>
  <label>양식 유형 <select name="step2_business.form_type" data-required="true">
    <option value="">선택</option>
    <option>단년</option>
    <option>다년 단계+연차</option>
  </select></label>
  <label>총 사업비 <input name="step2_business.total_budget" inputmode="numeric" placeholder="800 백만원" /></label>
  <label>정부지원 비율 <input name="step2_business.gov_pct" inputmode="numeric" placeholder="70%" /></label>
  <label>TRL 시작·도달 <input name="step2_business.trl" placeholder="5 → 6" /></label>
  <label>위험 상위 항목 <input name="step2_business.risks" placeholder="데이터 수집 지연, 모델 성능 미달" /></label>
</div>
</section>

<section class="agent-panel" data-step="3" aria-labelledby="agent-step-3">
<h2 id="agent-step-3">데이터·모델</h2>
<div class="agent-fields">
  <label>raw 데이터 출처 <textarea name="step3_data_model.raw_sources" data-required="true" rows="3" placeholder="MES 작업 이력, PLC 센서, QMS 검사 결과"></textarea></label>
  <label>독립변수 X <textarea name="step3_data_model.x_candidates" data-required="true" rows="3" placeholder="온도, 속도, 압력, 롤갭"></textarea></label>
  <label>종속변수 y <input name="step3_data_model.y_target" data-required="true" placeholder="두께 편차, 결함 분류" /></label>
  <label>문제 유형 <select name="step3_data_model.problem_type" data-required="true">
    <option value="">선택</option>
    <option>분류</option>
    <option>회귀</option>
    <option>이상탐지</option>
    <option>검색·생성</option>
  </select></label>
  <label>모델 후보 <input name="step3_data_model.model_candidates" placeholder="XGBoost, LSTM, CNN, LLM+RAG" /></label>
  <label>검증 지표 <input name="step3_data_model.evaluation" placeholder="F1, MAPE, RAGAS, P95 latency" /></label>
</div>
</section>

<section class="agent-panel" data-step="4" aria-labelledby="agent-step-4">
<h2 id="agent-step-4">설정</h2>
<div class="agent-fields">
  <label>작성 강도 <select name="step4_settings.output_strength">
    <option>중</option>
    <option>강</option>
    <option>약</option>
  </select></label>
  <label>작성 엔진 <select name="step4_settings.writer_mode">
    <option value="llm" selected>Gemini</option>
    <option value="deterministic">빠른 골격</option>
  </select></label>
  <label>Worker endpoint <input id="agent-endpoint" name="settings.endpoint" type="url" autocomplete="off" /></label>
  <label>생성 모델 <input name="step4_settings.gemini_model" placeholder="gemini-2.5-flash" /></label>
  <label>ASCII 도식 <select name="step4_settings.include_ascii" disabled>
    <option value="false">사용 안 함</option>
  </select></label>
</div>
</section>

<section class="agent-panel" data-step="5" aria-labelledby="agent-step-5">
<h2 id="agent-step-5">제출</h2>
<div class="agent-submit">
  <button id="agent-submit" type="submit" class="agent-primary">초안 생성</button>
  <button id="agent-reset" type="button">입력 초기화</button>
</div>
<div id="agent-status" class="agent-status" role="status">대기 중</div>
</section>

<div class="agent-actions">
  <button id="agent-prev" type="button">이전</button>
  <button id="agent-next" type="button" class="agent-primary">다음</button>
</div>

</form>

</section>

<aside class="agent-output" aria-label="생성 상태" markdown="1">
<h2>진행</h2>
<div id="agent-progress" class="agent-progress"></div>
<div id="agent-partials" class="agent-partials"></div>
<h2>결과</h2>
<div class="agent-result-actions">
  <button id="agent-copy" type="button" disabled>복사</button>
  <button id="agent-download" type="button" disabled>다운로드</button>
</div>
<textarea id="agent-result" readonly placeholder="결과 없음"></textarea>
</aside>

</div>

</div>
