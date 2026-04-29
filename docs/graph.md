---
title: "Cross-reference 인터랙티브 그래프"
description: "44 자산 + 274 인용 출처 표기를 force-directed 그래프로 시각화"
hide:
  - toc
---

# Cross-reference 인터랙티브 그래프

> 본 페이지는 **Stage 3** 에서 D3.js force-directed 그래프로 활성화 예정입니다. 현재는 placeholder.

## 진행 예정

- 노드 44 = 자산 1:1 매핑
- 엣지 274 = `> [출처: 파일명]` 표기 파싱 결과
- 노드 클릭 → 해당 자산 페이지 이동
- JS 비활성 환경에서 정적 SVG fallback

## 임시 — 자산 분류 트리

```mermaid
graph TD
  ROOT[44 자산]
  ROOT --> T[Track 본문 8 종]
  ROOT --> S[시나리오 6 종]
  ROOT --> P[6 패키지 파일럿]
  ROOT --> G[11 운영 가이드]
  ROOT --> M[5 모듈]
  ROOT --> O[기타 자산 5]
  ROOT --> META[메타 3]

  T --> T1[Track 1 — 제조 AI]
  T --> T2[Track 2 — MLOps]
  T --> T3[Track 3 — LLM·RAG]

  P --> PKG1[1 대기업 철강 다년 R&D]
  P --> PKG2[2 중견 냉연]
  P --> PKG3[3 특수강관 RAG]
  P --> PKG4[4 고무 양산]
  P --> PKG5[5 정밀가공 SaaS]
  P --> PKG6[6 유틸 ESG]
```

[← 홈으로](index.md)
