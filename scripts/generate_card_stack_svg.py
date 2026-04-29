"""generate_card_stack_svg.py — Phase E15-2 — 8 SVG 600×800 세로형 카드 stack 일괄 생성.

극단 가로형 mmdc SVG 8 종을 디자인 SVG (assets/svg/ 패턴) 으로 재작성.
viewBox 600×800 portrait + 헤더 100px + 카드 stack + 하단 cross-ref.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path("/Volumes/EXDATA/temp_git/ai-docs-for-biz")
OUT_DIR = ROOT / "docs" / "assets" / "diagrams"


def render_svg(spec: dict) -> str:
    """단일 SVG 생성 — 카드 stack."""
    nodes = spec["nodes"]  # [{main, sub}]
    n = len(nodes)
    grad_id = f"g_{spec['slug']}"

    # 카드 layout 계산
    avail_h = 580  # 중간 영역
    card_gap = 8
    card_h = (avail_h - card_gap * (n - 1)) // n
    card_h = min(card_h, 70)  # 최대 70px
    card_h = max(card_h, 48)  # 최소 48px

    card_x = 80
    card_w = 440  # 600 - 80*2 + 좌측 ① 원형 공간 = 80 + 24 + 8 + 408
    circle_r = 14
    circle_cx = 56
    text_x = 90  # circle 우측

    # cards 위치 계산
    start_y = 110  # 헤더 100 + 10 여백
    cards_xml = []
    for i, node in enumerate(nodes):
        cy = start_y + i * (card_h + card_gap)
        circle_y = cy + card_h // 2
        # 카드 box
        cards_xml.append(f'''  <g class="card" transform="translate(0, {cy})">
    <rect x="{card_x - 32}" y="0" width="{card_w + 32}" height="{card_h}" rx="8" fill="url(#{grad_id}_card)" stroke="{spec['stroke']}" stroke-width="0.8" filter="url(#shadow)"/>
    <circle cx="{circle_cx}" cy="{card_h // 2}" r="{circle_r}" fill="url(#{grad_id})"/>
    <text x="{circle_cx}" y="{card_h // 2 + 4}" text-anchor="middle" fill="white" font-size="11" font-weight="700">{i + 1}</text>
    <text x="{text_x}" y="{card_h // 2 - 4}" font-size="11" font-weight="700" fill="{spec['text_main']}">{node["main"]}</text>
    <text x="{text_x}" y="{card_h // 2 + 12}" font-size="9" font-weight="500" fill="{spec['text_sub']}">{node["sub"]}</text>
  </g>''')
        # 화살표 ▼ (마지막 카드 제외)
        if i < n - 1:
            arrow_y = cy + card_h + card_gap // 2 + 2
            cards_xml.append(f'  <text x="300" y="{arrow_y}" text-anchor="middle" font-size="10" fill="{spec["stroke"]}" opacity="0.6">▼</text>')

    cards_str = "\n".join(cards_xml)

    # 헤더 그라데이션 stops
    if "grad_3stop" in spec:
        grad_stops = f'''<stop offset="0%" stop-color="{spec["grad_3stop"][0]}"/><stop offset="50%" stop-color="{spec["grad_3stop"][1]}"/><stop offset="100%" stop-color="{spec["grad_3stop"][2]}"/>'''
    else:
        grad_stops = f'''<stop offset="0%" stop-color="{spec["grad"][0]}"/><stop offset="100%" stop-color="{spec["grad"][1]}"/>'''

    # SVG 출력
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" role="img"
     aria-label="{spec['title']} — {spec['subtitle']}">
  <title>{spec['title']}</title>
  <desc>{spec['desc']}</desc>
  <defs>
    <linearGradient id="{grad_id}" x1="0%" y1="0%" x2="100%" y2="100%">
      {grad_stops}
    </linearGradient>
    <linearGradient id="{grad_id}_card" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{spec['card_fill_top']}"/>
      <stop offset="100%" stop-color="{spec['card_fill_bot']}"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0F172A" flood-opacity="0.08"/>
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0F172A" flood-opacity="0.06"/>
    </filter>
  </defs>
  <style>
    text {{ font-family: "Pretendard", system-ui, -apple-system, sans-serif; }}
  </style>
  <rect width="600" height="800" fill="{spec['bg']}"/>
  <!-- 헤더 100px -->
  <rect x="0" y="0" width="600" height="100" fill="url(#{grad_id})"/>
  <text x="40" y="40" font-size="11" font-weight="600" fill="rgba(255,255,255,0.85)" letter-spacing="2">{spec['en_label']}</text>
  <text x="40" y="68" font-size="20" font-weight="800" fill="white">{spec['title']}</text>
  <text x="40" y="88" font-size="11" font-weight="500" fill="rgba(255,255,255,0.85)">{spec['subtitle']}</text>
  <!-- 카드 stack {n} 개 -->
{cards_str}
  <!-- 하단 cross-reference 120px -->
  <rect x="40" y="690" width="520" height="80" rx="8" fill="#EEF2FF" stroke="#C7D2FE" stroke-width="1"/>
  <text x="60" y="715" font-size="11" font-weight="700" fill="#4338CA">📌 {spec['cross_ref_label']}</text>
  <text x="60" y="735" font-size="10" font-weight="500" fill="#475569">{spec['cross_ref_1']}</text>
  <text x="60" y="752" font-size="10" font-weight="500" fill="#475569">{spec['cross_ref_2']}</text>
</svg>
'''


SPECS = [
    # === 그룹 A: pkg2 (3) + graph (1) ===
    {
        "slug": "pkg2_d1",
        "path": "pkg2-cold-rolled/diagram-1.svg",
        "title": "사양 → 추천 → HITL → 플라이휠",
        "subtitle": "9 단계 데이터 플라이휠",
        "en_label": "PKG 2 · DIAGRAM 1 · DATA FLYWHEEL",
        "desc": "주문 사양 입력부터 LLM 근거 추천, 숙련자 HITL 승인, 신규 사례 자동 편입까지 9 단계 데이터 플라이휠 흐름",
        "bg": "#EEF2FF",
        "grad": ["#3730A3", "#4F46E5"],
        "card_fill_top": "#FFFFFF",
        "card_fill_bot": "#F1F5F9",
        "stroke": "#818CF8",
        "text_main": "#1E1B4B",
        "text_sub": "#475569",
        "cross_ref_label": "사업계획서 §SCN-STL-04 패스 스케줄 표준화 paste 가능",
        "cross_ref_1": "결합 5.2 카드: 5.2-a (유사 사례) + 5.2-f (LLM·RAG)",
        "cross_ref_2": "Track 2 SCN-MLO-01 데이터 플라이휠 환류 루프 결합",
        "nodes": [
            {"main": "주문·사양 입력", "sub": "재질·치수·형상 → 시작점"},
            {"main": "피쳐 인코딩·임베딩", "sub": "수치·범주 dense vector"},
            {"main": "벡터 유사도 검색", "sub": "Top-N 후보 추출"},
            {"main": "과거 이력 KB 조회", "sub": "사양·설정·결과 매칭"},
            {"main": "규칙 검증", "sub": "물리·설비 제약 체크"},
            {"main": "LLM 요약·근거", "sub": "Citation 포함 추천 근거"},
            {"main": "추천 UI 표시", "sub": "Top-N 레시피 카드"},
            {"main": "숙련자 HITL", "sub": "승인·미세조정"},
            {"main": "신규 사례 자동 편입", "sub": "데이터 플라이휠 환류"},
        ],
    },
    {
        "slug": "pkg2_d2",
        "path": "pkg2-cold-rolled/diagram-2.svg",
        "title": "실시간 두께 조기경보",
        "subtitle": "8 단계 ICS Tag → HMI 경보",
        "en_label": "PKG 2 · DIAGRAM 2 · REAL-TIME EARLY WARNING",
        "desc": "PLC/Historian 의 10~100Hz 태그를 Edge 스트림으로 처리, 1D-CNN/LSTM 으로 두께 이탈 예측, HMI 경보 → 드리프트 → 재학습",
        "bg": "#EEF2FF",
        "grad": ["#3730A3", "#4F46E5"],
        "card_fill_top": "#FFFFFF",
        "card_fill_bot": "#F1F5F9",
        "stroke": "#818CF8",
        "text_main": "#1E1B4B",
        "text_sub": "#475569",
        "cross_ref_label": "사업계획서 §SCN-STL-05 두께 조기경보 paste 가능",
        "cross_ref_1": "결합 5.2 카드: 5.2-b (시계열 예측)",
        "cross_ref_2": "Track 2 SCN-MLO-01 드리프트 모니터링·재학습 결합",
        "nodes": [
            {"main": "PLC/Historian", "sub": "10~100Hz 태그 수집"},
            {"main": "Edge 스트림 버퍼", "sub": "NTP 동기화"},
            {"main": "슬라이딩 윈도우 피쳐", "sub": "통계·재질 메타 추출"},
            {"main": "예측 모델", "sub": "1D-CNN/LSTM/Transformer"},
            {"main": "이탈 판정", "sub": "σ 임계·추세 검출"},
            {"main": "HMI 경보 + 조작변수", "sub": "텐션·속도·온도 제안"},
            {"main": "드리프트 모니터링", "sub": "PSI/KS 분포 측정"},
            {"main": "재학습 트리거", "sub": "Track 2 SCN-MLO-01"},
        ],
    },
    {
        "slug": "pkg2_d5",
        "path": "pkg2-cold-rolled/diagram-5.svg",
        "title": "RAG 장애 대응 검색",
        "subtitle": "12 단계 SOP·CMMS 지식 검색 + sLM 라우팅",
        "en_label": "PKG 2 · DIAGRAM 5 · RAG TROUBLESHOOTING",
        "desc": "SOP·도면·CMMS 문서를 청킹·임베딩 후 벡터스토어 적재, 하이브리드 검색·Re-rank·민감도 라우팅 후 sLM 또는 외부 LLM 응답",
        "bg": "#EEF2FF",
        "grad": ["#3730A3", "#4F46E5"],
        "card_fill_top": "#FFFFFF",
        "card_fill_bot": "#F1F5F9",
        "stroke": "#818CF8",
        "text_main": "#1E1B4B",
        "text_sub": "#475569",
        "cross_ref_label": "사업계획서 §SCN-LLM-02 장애대응 RAG paste 가능",
        "cross_ref_1": "결합 5.2 카드: 5.2-f (LLM·RAG) + sLM 가이드 §1·§5",
        "cross_ref_2": "RAG 인프라 가이드 §3 통합 5 계층 + BLK-CSEC-F 라우팅",
        "nodes": [
            {"main": "문서 소스", "sub": "SOP·도면·CMMS·MSDS"},
            {"main": "파서·OCR", "sub": "PDF/HWP/DWG 처리"},
            {"main": "청킹·임베딩", "sub": "멀티뷰 (원문·요약·키워드)"},
            {"main": "벡터스토어", "sub": "Pinecone / Weaviate"},
            {"main": "사용자 질의", "sub": "현장 HMI / 태블릿"},
            {"main": "하이브리드 검색", "sub": "Dense + BM25 + 메타"},
            {"main": "Re-ranker", "sub": "Top-N 정밀 정렬"},
            {"main": "민감도 라우팅", "sub": "BLK-CSEC-F ①~⑤ 게이트"},
            {"main": "온프레 sLM", "sub": "EXAONE / HyperCLOVA"},
            {"main": "외부 LLM API", "sub": "GPT / Claude (민감도 ①·②)"},
            {"main": "응답 + Citation", "sub": "근거 강제·환각 방지"},
            {"main": "피드백·감사 로그", "sub": "문서 보강 환류 루프"},
        ],
    },
    {
        "slug": "graph_d1",
        "path": "graph/diagram-1.svg",
        "title": "44 자산 분류 트리",
        "subtitle": "Cross-reference 그래프 — 정적 fallback",
        "en_label": "GRAPH · 44 ASSETS · CLASSIFICATION TREE",
        "desc": "44 자산을 7 분류 (Track 본문·시나리오·6 패키지·11 운영가이드·5 모듈·기타·메타) 로 분류한 트리 구조 — D3 force-directed 그래프의 정적 fallback",
        "bg": "#FAF5FF",
        "grad_3stop": ["#6366F1", "#8B5CF6", "#EC4899"],
        "grad": ["#6366F1", "#EC4899"],
        "card_fill_top": "#FFFFFF",
        "card_fill_bot": "#FAF5FF",
        "stroke": "#A78BFA",
        "text_main": "#3B0764",
        "text_sub": "#6B21A8",
        "cross_ref_label": "Cross-reference 그래프 — D3 force-directed 인터랙티브",
        "cross_ref_1": "44 자산 + 109 인용 출처 표기 (build_crossref.py)",
        "cross_ref_2": "graph.md 페이지 D3 인터랙티브 + 본 정적 fallback",
        "nodes": [
            {"main": "44 자산 ROOT", "sub": "워크스페이스 전체"},
            {"main": "Track 본문 8 종", "sub": "Track 1·2·3 + 핵심 5 블록"},
            {"main": "시나리오 6 종", "sub": "카탈로그 + 상세 5 (Top5·Phase2·RUB·UTL·SAF·특수강관)"},
            {"main": "6 패키지 파일럿", "sub": "대기업 철강·중견 냉연·특수강관·고무·정밀가공·유틸 ESG"},
            {"main": "11 운영 가이드", "sub": "조립·재무·압축·KPI·외부검증·RAG·도메인·sLM·컨설팅·TRL·위험"},
            {"main": "5 Cross-cutting 모듈", "sub": "CBAM·중대재해·연합학습·OEM·SaaS 보안"},
            {"main": "기타 자산 5 종", "sub": "시너지 ROI·RACI·지원사업·양식검증·방법론"},
            {"main": "메타 3 종", "sub": "작업로그·CLAUDE.md·검토 리포트"},
            {"main": "Track 1 — 제조 AI", "sub": "생산·품질·예지보전"},
            {"main": "Track 2 — MLOps", "sub": "모니터링·재학습·거버넌스"},
        ],
    },
    # === 그룹 B: pkg4 (2) + pkg5 (2) ===
    {
        "slug": "pkg4_d1",
        "path": "pkg4-rubber/diagram-1.svg",
        "title": "압출 공정 시계열 예측·재학습",
        "subtitle": "8 단계 PLC → HMI 경보 → Drift 환류",
        "en_label": "PKG 4 · DIAGRAM 1 · EXTRUSION TIME-SERIES",
        "desc": "고무 압출 공정의 PLC/Historian 태그를 슬라이딩 윈도우 피쳐로 변환, 1D-CNN/LSTM/Transformer 예측, HMI 경보·드리프트·재학습 환류",
        "bg": "#FFFBEB",
        "grad": ["#F59E0B", "#FB923C"],
        "card_fill_top": "#FFFFFF",
        "card_fill_bot": "#FEF3C7",
        "stroke": "#FBBF24",
        "text_main": "#78350F",
        "text_sub": "#92400E",
        "cross_ref_label": "사업계획서 §SCN-RUB-02 압출 라인 치수·표면 paste 가능",
        "cross_ref_1": "결합 5.2 카드: 5.2-b (시계열 예측)",
        "cross_ref_2": "Track 2 SCN-MLO-01 드리프트·재학습 1차 적용",
        "nodes": [
            {"main": "PLC/Historian", "sub": "10~100Hz 태그 수집"},
            {"main": "Edge 스트림 버퍼", "sub": "NTP 동기화"},
            {"main": "슬라이딩 윈도우 피쳐", "sub": "통계·재질 메타 추출"},
            {"main": "예측 모델", "sub": "1D-CNN / LSTM / Transformer"},
            {"main": "이탈 판정", "sub": "σ 임계·추세 검출"},
            {"main": "HMI 경보 + 조작변수", "sub": "스크류 회전수·다이 온도"},
            {"main": "드리프트 모니터링", "sub": "PSI / KS 분포 측정"},
            {"main": "재학습 트리거", "sub": "Track 2 SCN-MLO-01"},
        ],
    },
    {
        "slug": "pkg4_d2",
        "path": "pkg4-rubber/diagram-2.svg",
        "title": "외관 비전 검사·이벤트 트리거",
        "subtitle": "8 단계 라인스캔 → CMMS 처분 기록",
        "en_label": "PKG 4 · DIAGRAM 2 · VISION QC HITL",
        "desc": "라인스캔/다각도 카메라 + 균일 조명, EfficientNet/ViT/YOLO 비전 모델, 결함 등급 매핑 + 라인 분기·정지 이벤트, CMMS/MES 처분 기록 + Active Learning",
        "bg": "#FFFBEB",
        "grad": ["#F59E0B", "#FB923C"],
        "card_fill_top": "#FFFFFF",
        "card_fill_bot": "#FEF3C7",
        "stroke": "#FBBF24",
        "text_main": "#78350F",
        "text_sub": "#92400E",
        "cross_ref_label": "사업계획서 §SCN-RUB-05 외관 비전 검사 paste 가능",
        "cross_ref_1": "결합 5.2 카드: 5.2-c (비전 검사)",
        "cross_ref_2": "Active Learning 환류 + CMMS/MES 처분 기록",
        "nodes": [
            {"main": "카메라 입력", "sub": "라인스캔 / 다각도"},
            {"main": "전처리", "sub": "왜곡 보정·정규화"},
            {"main": "조명 균일도", "sub": "균일 조도 보정"},
            {"main": "비전 모델", "sub": "EfficientNet / ViT / YOLO"},
            {"main": "결함 등급 매핑", "sub": "설계 허용치 대비 분류"},
            {"main": "이벤트 트리거", "sub": "라인 분기 / 정지"},
            {"main": "CMMS/MES 연동", "sub": "처분 기록 자동 적재"},
            {"main": "검사원 라벨링", "sub": "Active Learning 환류"},
        ],
    },
    {
        "slug": "pkg5_d1",
        "path": "pkg5-precision/diagram-1.svg",
        "title": "CNC 공구 마모·RUL 예지",
        "subtitle": "8 단계 OPC-UA → 모바일 알람 → 환류",
        "en_label": "PKG 5 · DIAGRAM 1 · CNC TOOL WEAR · RUL FORECAST",
        "desc": "CNC 컨트롤러 1~10Hz 태그를 OPC-UA 게이트웨이로 클라우드 TSDB 적재, LSTM+XGBoost 스태킹 RUL 예측, 모바일 알람 + 드리프트·재학습",
        "bg": "#F0F9FF",
        "grad": ["#0EA5E9", "#38BDF8"],
        "card_fill_top": "#FFFFFF",
        "card_fill_bot": "#E0F2FE",
        "stroke": "#7DD3FC",
        "text_main": "#0C4A6E",
        "text_sub": "#075985",
        "cross_ref_label": "사업계획서 §SCN-MET-01 CNC 공구 마모 paste 가능",
        "cross_ref_1": "결합 5.2 카드: 5.2-b (시계열) + 5.2-d (예지보전)",
        "cross_ref_2": "Track 2 SCN-MLO-01 압축 모드 (단일 텐넌트)",
        "nodes": [
            {"main": "CNC 컨트롤러", "sub": "1~10Hz 태그 수집"},
            {"main": "OPC-UA 게이트웨이", "sub": "NTP 동기·표준 프로토콜"},
            {"main": "클라우드 TSDB", "sub": "슬라이딩 윈도우 피쳐"},
            {"main": "예측 모델", "sub": "LSTM + XGBoost Stacking"},
            {"main": "마모 단계 분류", "sub": "+ 파손 임박 조기경보"},
            {"main": "작업자 모바일 알람", "sub": "+ 공구 교체 권고"},
            {"main": "드리프트 모니터링", "sub": "PSI / KS 분포 측정"},
            {"main": "재학습 트리거", "sub": "Track 2 압축 모드"},
        ],
    },
    {
        "slug": "pkg5_d2",
        "path": "pkg5-precision/diagram-2.svg",
        "title": "3D 스캔 치수 검사·SPC 조기경보",
        "subtitle": "9 단계 포인트클라우드 → ERP 적재",
        "en_label": "PKG 5 · DIAGRAM 2 · 3D SCAN INSPECTION · SPC",
        "desc": "3D 스캐너 포인트클라우드 + CMM + CAD 도면 정합, EfficientNet+PointNet+ICP 비전 모델 치수 편차 자동 산출, ERP 처분 + Active Learning",
        "bg": "#F0F9FF",
        "grad": ["#0EA5E9", "#38BDF8"],
        "card_fill_top": "#FFFFFF",
        "card_fill_bot": "#E0F2FE",
        "stroke": "#7DD3FC",
        "text_main": "#0C4A6E",
        "text_sub": "#075985",
        "cross_ref_label": "사업계획서 §SCN-MET-03 치수 검사 자동화 paste 가능",
        "cross_ref_1": "결합 5.2 카드: 5.2-c (비전 검사) + 5.2-g (CAD 임베딩)",
        "cross_ref_2": "Active Learning 환류 + ERP 처분 기록",
        "nodes": [
            {"main": "3D 스캐너", "sub": "포인트클라우드 입력"},
            {"main": "클라우드 적재·정합", "sub": "CAD 도면 매칭"},
            {"main": "CMM 측정 결과", "sub": "정밀 좌표 측정"},
            {"main": "CAD 설계 도면", "sub": "기준 형상 비교"},
            {"main": "비전 모델", "sub": "EfficientNet + PointNet + ICP"},
            {"main": "치수 편차 산출", "sub": "설계 허용치 대비 자동"},
            {"main": "합격·재검사·불량", "sub": "이벤트 트리거 분류"},
            {"main": "ERP 검사 결과 적재", "sub": "처분 기록 자동"},
            {"main": "검사원 검토 라벨링", "sub": "Active Learning · 클라우드"},
        ],
    },
]


def render_tree_branching(spec: dict) -> str:
    """tree_branching template — 3 입력 → 합류 → 분기 → 결과 합류 (BLK-T1-3.1 같은 인적 의존성·리스크 다이어그램).

    레이아웃:
      ┌── input1 ──┐  ┌── input2 ──┐  ┌── input3 ──┐  (3 입력 row, y=130)
      └────────────┘  └────────────┘  └────────────┘
              ↘            ↓            ↙
                  ┌── 합류 (현장 판단) ──┐  (y=240)
                          ↓
                  ┌── 결정 (변수 동시) ──┐  (y=330)
                          ↓ (점선 분기)  ↘
                  ┌── 편차 ─────┐   ┌── 좌측 점선 분기 (이탈) ──┐  (y=440)
                          ↓               ↓
                  ┌── 재작업 ───┐   ┌── 즉각 마비 ──┐
                          ↘            ↓
                              ┌── 구조적 리스크 (합류) ──┐  (y=590)
    """
    grad_id = f"g_{spec['slug']}"
    inputs = spec.get("inputs", [])      # 3 입력
    pivot1 = spec.get("pivot1", {})       # 1차 합류
    pivot2 = spec.get("pivot2", {})       # 2차 결정
    branches = spec.get("branches", [])   # 분기 (좌·우)
    leaves = spec.get("leaves", [])       # 잎 노드
    final = spec.get("final", {})         # 최종 합류

    # input row (3 boxes, y=130)
    input_xml = []
    for i, node in enumerate(inputs):
        x = 40 + i * 175  # 40, 215, 390
        input_xml.append(f'''  <g transform="translate({x}, 120)">
    <rect width="160" height="56" rx="8" fill="url(#{grad_id}_card)" stroke="{spec['stroke']}" stroke-width="0.8" filter="url(#shadow)"/>
    <text x="80" y="24" text-anchor="middle" font-size="11" font-weight="700" fill="{spec['text_main']}">{node["main"]}</text>
    <text x="80" y="42" text-anchor="middle" font-size="9" font-weight="500" fill="{spec['text_sub']}">{node["sub"]}</text>
  </g>''')

    # 화살표 input → pivot1 (3 → 1)
    for i in range(3):
        x_start = 120 + i * 175
        input_xml.append(f'  <path d="M {x_start} 176 Q {x_start} 215 300 230" fill="none" stroke="{spec["stroke"]}" stroke-width="1.5" marker-end="url(#arrow_{grad_id})"/>')

    # pivot1 (y=240, 합류)
    pivot1_xml = f'''  <g transform="translate(180, 230)">
    <rect width="240" height="60" rx="10" fill="url(#{grad_id})" stroke="{spec['stroke']}" stroke-width="1" filter="url(#shadow)"/>
    <text x="120" y="28" text-anchor="middle" font-size="13" font-weight="700" fill="white">{pivot1.get("main", "")}</text>
    <text x="120" y="46" text-anchor="middle" font-size="10" font-weight="500" fill="rgba(255,255,255,0.9)">{pivot1.get("sub", "")}</text>
  </g>
  <text x="300" y="305" text-anchor="middle" font-size="14" fill="{spec['stroke']}">▼</text>'''

    # pivot2 (y=320, 결정)
    pivot2_xml = f'''  <g transform="translate(180, 315)">
    <rect width="240" height="60" rx="10" fill="url(#{grad_id}_card)" stroke="{spec['stroke']}" stroke-width="1" filter="url(#shadow)"/>
    <text x="120" y="28" text-anchor="middle" font-size="13" font-weight="700" fill="{spec['text_main']}">{pivot2.get("main", "")}</text>
    <text x="120" y="46" text-anchor="middle" font-size="10" font-weight="500" fill="{spec['text_sub']}">{pivot2.get("sub", "")}</text>
  </g>'''

    # branches (좌·우 분기, y=410)
    branches_xml = []
    if len(branches) >= 2:
        for i, b in enumerate(branches[:2]):
            x = 60 + i * 280  # 60, 340
            dash = ' stroke-dasharray="4 3"' if b.get("dashed") else ""
            label = b.get("label", "")
            label_x = 200 + i * 280  # 200, 480
            branches_xml.append(f'''  <path d="M 300 375 Q {x + 80} 390 {x + 80} 410" fill="none" stroke="{spec["stroke"]}" stroke-width="1.4"{dash} marker-end="url(#arrow_{grad_id})"/>
  <rect x="{label_x - 40}" y="380" width="80" height="18" rx="4" fill="{spec['bg']}" stroke="{spec['stroke']}" stroke-width="0.5"/>
  <text x="{label_x}" y="392" text-anchor="middle" font-size="9" font-weight="600" fill="{spec['stroke']}">{label}</text>
  <g transform="translate({x}, 410)">
    <rect width="160" height="48" rx="8" fill="url(#{grad_id}_card)" stroke="{spec['stroke']}" stroke-width="0.8" filter="url(#shadow)"/>
    <text x="80" y="22" text-anchor="middle" font-size="11" font-weight="700" fill="{spec['text_main']}">{b["main"]}</text>
    <text x="80" y="38" text-anchor="middle" font-size="9" font-weight="500" fill="{spec['text_sub']}">{b["sub"]}</text>
  </g>''')

    # leaves (y=490, 4 box)
    leaves_xml = []
    if len(leaves) >= 4:
        for i, l in enumerate(leaves[:4]):
            x = 30 + i * 140  # 4 boxes
            leaves_xml.append(f'''  <g transform="translate({x}, 490)">
    <rect width="125" height="50" rx="8" fill="white" stroke="{spec['stroke']}" stroke-width="0.8" filter="url(#shadow)"/>
    <text x="62.5" y="22" text-anchor="middle" font-size="10" font-weight="700" fill="{spec['text_main']}">{l["main"]}</text>
    <text x="62.5" y="38" text-anchor="middle" font-size="8" font-weight="500" fill="{spec['text_sub']}">{l.get("sub", "")}</text>
  </g>''')

    # final (y=590, 합류)
    final_xml = f'''  <text x="300" y="565" text-anchor="middle" font-size="14" fill="{spec['stroke']}">▼</text>
  <g transform="translate(150, 575)">
    <rect width="300" height="62" rx="10" fill="url(#{grad_id})" stroke="{spec['stroke']}" stroke-width="1.5" filter="url(#shadow)"/>
    <text x="150" y="32" text-anchor="middle" font-size="14" font-weight="800" fill="white">⚠ {final.get("main", "")}</text>
    <text x="150" y="50" text-anchor="middle" font-size="10" font-weight="500" fill="rgba(255,255,255,0.9)">{final.get("sub", "")}</text>
  </g>'''

    if "grad_3stop" in spec:
        grad_stops = f'''<stop offset="0%" stop-color="{spec["grad_3stop"][0]}"/><stop offset="50%" stop-color="{spec["grad_3stop"][1]}"/><stop offset="100%" stop-color="{spec["grad_3stop"][2]}"/>'''
    else:
        grad_stops = f'''<stop offset="0%" stop-color="{spec["grad"][0]}"/><stop offset="100%" stop-color="{spec["grad"][1]}"/>'''

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" role="img"
     aria-label="{spec['title']} — {spec['subtitle']}">
  <title>{spec['title']}</title>
  <desc>{spec['desc']}</desc>
  <defs>
    <linearGradient id="{grad_id}" x1="0%" y1="0%" x2="100%" y2="100%">
      {grad_stops}
    </linearGradient>
    <linearGradient id="{grad_id}_card" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{spec['card_fill_top']}"/>
      <stop offset="100%" stop-color="{spec['card_fill_bot']}"/>
    </linearGradient>
    <marker id="arrow_{grad_id}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="{spec['stroke']}"/>
    </marker>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0F172A" flood-opacity="0.08"/>
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0F172A" flood-opacity="0.06"/>
    </filter>
  </defs>
  <style>
    text {{ font-family: "Pretendard", system-ui, -apple-system, sans-serif; }}
  </style>
  <rect width="600" height="800" fill="{spec['bg']}"/>
  <rect x="0" y="0" width="600" height="100" fill="url(#{grad_id})"/>
  <text x="40" y="40" font-size="11" font-weight="600" fill="rgba(255,255,255,0.85)" letter-spacing="2">{spec['en_label']}</text>
  <text x="40" y="68" font-size="20" font-weight="800" fill="white">{spec['title']}</text>
  <text x="40" y="88" font-size="11" font-weight="500" fill="rgba(255,255,255,0.85)">{spec['subtitle']}</text>
{chr(10).join(input_xml)}
{pivot1_xml}
{pivot2_xml}
{chr(10).join(branches_xml)}
{chr(10).join(leaves_xml)}
{final_xml}
  <rect x="40" y="690" width="520" height="80" rx="8" fill="#EEF2FF" stroke="#C7D2FE" stroke-width="1"/>
  <text x="60" y="715" font-size="11" font-weight="700" fill="#4338CA">📌 {spec['cross_ref_label']}</text>
  <text x="60" y="735" font-size="10" font-weight="500" fill="#475569">{spec['cross_ref_1']}</text>
  <text x="60" y="752" font-size="10" font-weight="500" fill="#475569">{spec['cross_ref_2']}</text>
</svg>
'''


def render_matrix_2x2(spec: dict) -> str:
    """matrix_2x2 template — 2×2 매트릭스 + 의사결정 트리.

    레이아웃:
      ┌── 질문 1 (큰 박스) ──┐  (y=130)
      └────────────────────┘
              ↓ 예 / 아니오
      ┌── 질문 2 ──────────┐  (y=240)
      └────────────────────┘
              ↓
      ┌── 4 도메인 카드 grid 2×2 ──┐  (y=350)
      └────────────────────────────┘
              ↓
      ┌── 4 결과 권고 ──┐  (y=560)
    """
    grad_id = f"g_{spec['slug']}"
    questions = spec.get("questions", [])
    domains = spec.get("domains", [])
    results = spec.get("results", [])

    parts = []
    # 2 questions row (y=120, 230)
    for i, q in enumerate(questions[:2]):
        y = 120 + i * 95
        parts.append(f'''  <g transform="translate(120, {y})">
    <rect width="360" height="64" rx="10" fill="url(#{grad_id})" stroke="{spec['stroke']}" stroke-width="1" filter="url(#shadow)"/>
    <text x="180" y="32" text-anchor="middle" font-size="14" font-weight="700" fill="white">{q.get("main", "")}</text>
    <text x="180" y="50" text-anchor="middle" font-size="10" font-weight="500" fill="rgba(255,255,255,0.9)">{q.get("sub", "")}</text>
  </g>
  <text x="300" y="{y + 80}" text-anchor="middle" font-size="14" fill="{spec['stroke']}">▼</text>''')

    # 2x2 grid (y=320~ 440)
    for i, d in enumerate(domains[:4]):
        col = i % 2
        row = i // 2
        x = 60 + col * 250
        y = 330 + row * 90
        parts.append(f'''  <g transform="translate({x}, {y})">
    <rect width="230" height="76" rx="10" fill="url(#{grad_id}_card)" stroke="{spec['stroke']}" stroke-width="0.8" filter="url(#shadow)"/>
    <text x="115" y="28" text-anchor="middle" font-size="12" font-weight="700" fill="{spec['text_main']}">{d.get("main", "")}</text>
    <text x="115" y="48" text-anchor="middle" font-size="9" font-weight="500" fill="{spec['text_sub']}">{d.get("sub", "")}</text>
    <text x="115" y="64" text-anchor="middle" font-size="9" font-weight="600" fill="{spec['stroke']}">→ {d.get("rec", "")}</text>
  </g>''')

    # results row (y=540~590)
    parts.append('  <text x="300" y="525" text-anchor="middle" font-size="14" fill="' + spec['stroke'] + '">▼</text>')
    for i, r in enumerate(results[:4]):
        x = 30 + i * 140
        parts.append(f'''  <g transform="translate({x}, 540)">
    <rect width="125" height="56" rx="8" fill="white" stroke="{spec['stroke']}" stroke-width="0.8" filter="url(#shadow)"/>
    <text x="62.5" y="22" text-anchor="middle" font-size="10" font-weight="700" fill="{spec['text_main']}">{r.get("main", "")}</text>
    <text x="62.5" y="38" text-anchor="middle" font-size="9" font-weight="500" fill="{spec['text_sub']}">{r.get("sub", "")}</text>
    <text x="62.5" y="50" text-anchor="middle" font-size="9" font-weight="600" fill="{spec['stroke']}">{r.get("rec", "")}</text>
  </g>''')

    if "grad_3stop" in spec:
        grad_stops = f'''<stop offset="0%" stop-color="{spec["grad_3stop"][0]}"/><stop offset="50%" stop-color="{spec["grad_3stop"][1]}"/><stop offset="100%" stop-color="{spec["grad_3stop"][2]}"/>'''
    else:
        grad_stops = f'''<stop offset="0%" stop-color="{spec["grad"][0]}"/><stop offset="100%" stop-color="{spec["grad"][1]}"/>'''

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" role="img"
     aria-label="{spec['title']} — {spec['subtitle']}">
  <title>{spec['title']}</title>
  <desc>{spec['desc']}</desc>
  <defs>
    <linearGradient id="{grad_id}" x1="0%" y1="0%" x2="100%" y2="100%">
      {grad_stops}
    </linearGradient>
    <linearGradient id="{grad_id}_card" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{spec['card_fill_top']}"/>
      <stop offset="100%" stop-color="{spec['card_fill_bot']}"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0F172A" flood-opacity="0.08"/>
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0F172A" flood-opacity="0.06"/>
    </filter>
  </defs>
  <style>
    text {{ font-family: "Pretendard", system-ui, -apple-system, sans-serif; }}
  </style>
  <rect width="600" height="800" fill="{spec['bg']}"/>
  <rect x="0" y="0" width="600" height="100" fill="url(#{grad_id})"/>
  <text x="40" y="40" font-size="11" font-weight="600" fill="rgba(255,255,255,0.85)" letter-spacing="2">{spec['en_label']}</text>
  <text x="40" y="68" font-size="20" font-weight="800" fill="white">{spec['title']}</text>
  <text x="40" y="88" font-size="11" font-weight="500" fill="rgba(255,255,255,0.85)">{spec['subtitle']}</text>
{chr(10).join(parts)}
  <rect x="40" y="690" width="520" height="80" rx="8" fill="#EEF2FF" stroke="#C7D2FE" stroke-width="1"/>
  <text x="60" y="715" font-size="11" font-weight="700" fill="#4338CA">📌 {spec['cross_ref_label']}</text>
  <text x="60" y="735" font-size="10" font-weight="500" fill="#475569">{spec['cross_ref_1']}</text>
  <text x="60" y="752" font-size="10" font-weight="500" fill="#475569">{spec['cross_ref_2']}</text>
</svg>
'''


# === 시범 SPECS (Phase E15-3 — 다양한 template 검증) ===
DEMO_SPECS = [
    {
        "template": "tree_branching",
        "slug": "demo_t1_31",
        "path": "track1-top5/diagram-1.svg",
        "title": "인적 의존성·암묵지 리스크",
        "subtitle": "BLK-T1-3.1 — 3 입력 → 합류 → 분기 → 구조적 리스크",
        "en_label": "TRACK 1 · BLK-T1-3.1 · TACIT KNOWLEDGE RISK",
        "desc": "베테랑 숙련공·Excel 메모·작업자 경험 3 입력이 현장 운영 판단으로 합류, 공정 설정값 결정 후 작업자 편차로 분기, 표준 미정립·즉각 마비·재작업·후속 산포가 구조적 리스크로 합류",
        "bg": "#EEF2FF",
        "grad": ["#3730A3", "#6366F1"],
        "card_fill_top": "#FFFFFF",
        "card_fill_bot": "#F1F5F9",
        "stroke": "#818CF8",
        "text_main": "#1E1B4B",
        "text_sub": "#475569",
        "cross_ref_label": "사업계획서 §3.1 사업 배경 paste 가능 (Track 1)",
        "cross_ref_1": "결합 5.2 카드: 5.2-f (LLM·RAG 지식 검색) — 암묵지 형식지화",
        "cross_ref_2": "BLK-T1-3.2 데이터 단절 + BLK-T2-3.2 모니터링 부재 결합",
        "inputs": [
            {"main": "베테랑 숙련공", "sub": "(수치)명 · 경력 (기간)+"},
            {"main": "Excel·수기 메모", "sub": "분산·미관리"},
            {"main": "작업자별 경험", "sub": "암묵지 의존"},
        ],
        "pivot1": {"main": "현장 운영 판단", "sub": "암묵지 전수 (3 입력 합류)"},
        "pivot2": {"main": "공정 설정값 결정", "sub": "변수 (수치)종 동시 조작"},
        "branches": [
            {"main": "표준 미정립", "sub": "문서화 부재", "label": "문서화 부재", "dashed": True},
            {"main": "작업자 간 편차", "sub": "±(수치)% 차이", "label": "이탈·퇴직", "dashed": False},
        ],
        "leaves": [
            {"main": "즉각적 공정 마비", "sub": "베테랑 이탈 시"},
            {"main": "표준 미정립", "sub": "후임 학습 ↓"},
            {"main": "재작업률", "sub": "(수치)% 발생"},
            {"main": "후속 공정 산포", "sub": "품질 악화"},
        ],
        "final": {"main": "구조적 리스크", "sub": "4 결과 합류 — 사업 위협"},
    },
    {
        "template": "matrix_2x2",
        "slug": "demo_by_pkg",
        "path": "by-package/diagram-1.svg",
        "title": "6 패키지 매칭 의사결정",
        "subtitle": "규모 × 도메인 × 사업기간 → 적정 패키지",
        "en_label": "BY-PACKAGE · DECISION TREE",
        "desc": "귀사 규모 (대기업·중견·중소) × 다년 R&D 여부 × 주력 도메인 (철강·고무·정밀가공·유틸 ESG) 의 3 분기로 6 통합 파일럿 패키지 (1~6) 중 적정 매칭",
        "bg": "#FAF5FF",
        "grad_3stop": ["#6366F1", "#8B5CF6", "#EC4899"],
        "grad": ["#6366F1", "#EC4899"],
        "card_fill_top": "#FFFFFF",
        "card_fill_bot": "#FAF5FF",
        "stroke": "#A78BFA",
        "text_main": "#3B0764",
        "text_sub": "#6B21A8",
        "cross_ref_label": "by-package.md — 6 패키지 비교 매트릭스 본문",
        "cross_ref_1": "사업 매칭 후 해당 패키지의 §3·§4·§5 본문 paste",
        "cross_ref_2": "패키지 1 (대기업 R&D) ~ 패키지 6 (유틸·ESG·CBAM)",
        "questions": [
            {"main": "Q1. 귀사 규모는?", "sub": "대기업 5조+ / 중견 1~5천억 / 중소 수백억"},
            {"main": "Q2. 다년 R&D? 주력 도메인?", "sub": "예 33개월+ / 아니오 단년"},
        ],
        "domains": [
            {"main": "철강 냉연·압연", "sub": "대기업·중견 다년", "rec": "패키지 1·2"},
            {"main": "특수강관 + 암묵지", "sub": "중견 RAG 중심", "rec": "패키지 3"},
            {"main": "고무·폴리머 양산", "sub": "OEM 공급", "rec": "패키지 4"},
            {"main": "유틸·환경·ESG", "sub": "CBAM·중대재해", "rec": "패키지 6"},
        ],
        "results": [
            {"main": "전사적 DX R&D", "sub": "다년·대기업", "rec": "패키지 1"},
            {"main": "스마트공장 고도화", "sub": "중견·12 개월", "rec": "패키지 2·5"},
            {"main": "디지털 경남", "sub": "중견·9 개월", "rec": "패키지 3·6"},
            {"main": "정밀가공 SaaS", "sub": "중소·9 개월", "rec": "패키지 5"},
        ],
    },
]


def main():
    for spec in SPECS:
        svg = render_svg(spec)
        out_path = OUT_DIR / spec["path"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(svg, encoding="utf-8")
        n_lines = svg.count("\n")
        print(f"  ✓ {spec['path']} ({n_lines} 줄, {len(spec['nodes'])} 노드, card_stack)")

    # === Phase E15-3 demo (template 다양화 시범) ===
    print("\n## Phase E15-3 시범 (5 templates 다양화)")
    for spec in DEMO_SPECS:
        if spec["template"] == "tree_branching":
            svg = render_tree_branching(spec)
        elif spec["template"] == "matrix_2x2":
            svg = render_matrix_2x2(spec)
        else:
            continue
        out_path = OUT_DIR / spec["path"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(svg, encoding="utf-8")
        n_lines = svg.count("\n")
        print(f"  ✓ {spec['path']} ({n_lines} 줄, {spec['template']})")


if __name__ == "__main__":
    main()
