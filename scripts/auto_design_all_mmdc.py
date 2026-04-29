"""auto_design_all_mmdc.py — Phase E15-7

모든 잔존 mmdc SVG → 디자인 card_stack SVG 자동 일괄 변환.

전략:
1. docs/assets/diagrams/ 의 모든 SVG 식별
2. mmdc 생성물 vs 디자인 SVG 분리 (`#my-svg` 마커)
3. mmdc 만 처리:
   - 노드 텍스트 자동 추출 (`<p>` 태그)
   - slug 기반 도메인 색상 매핑
   - generate_card_stack_svg.py 의 render_svg() 호출
   - 같은 path 에 덮어쓰기
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/Volumes/EXDATA/temp_git/ai-docs-for-biz")
DIAGRAMS_BASE = ROOT / "docs" / "assets" / "diagrams"

# generate_card_stack_svg.py 의 render_svg 임포트
sys.path.insert(0, str(ROOT / "scripts"))
from generate_card_stack_svg import render_svg


# slug prefix → 도메인 메타 (색상·title 패턴·cross-ref)
DOMAIN_META = {
    "track1-top5": {
        "title_prefix": "Track 1 — 제조 AI",
        "en_label_prefix": "TRACK 1 · MANUFACTURING AI",
        "bg": "#EEF2FF",
        "grad": ["#3730A3", "#6366F1"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#E0E7FF", "stroke": "#A5B4FC",
        "text_main": "#312E81", "text_sub": "#3730A3",
        "cross_ref_label": "사업계획서 §3·§4 본문 5 블록 paste 가능 (Track 1)",
    },
    "track1-engine-cards": {
        "title_prefix": "Track 1 — AI 엔진 카드 (5.2)",
        "en_label_prefix": "TRACK 1 · 5.2 AI ENGINE CARDS",
        "bg": "#EEF2FF",
        "grad": ["#3730A3", "#6366F1"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#E0E7FF", "stroke": "#A5B4FC",
        "text_main": "#312E81", "text_sub": "#3730A3",
        "cross_ref_label": "5.2 AI 엔진 6 종 카드 (시계열·비전·이상탐지·강화·RAG·CAD)",
    },
    "track2-top5": {
        "title_prefix": "Track 2 — MLOps",
        "en_label_prefix": "TRACK 2 · MLOPS",
        "bg": "#F5F3FF",
        "grad": ["#6D28D9", "#8B5CF6"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#EDE9FE", "stroke": "#C4B5FD",
        "text_main": "#4C1D95", "text_sub": "#5B21B6",
        "cross_ref_label": "사업계획서 §6·§7·§8 본문 5 블록 paste 가능 (Track 2)",
    },
    "track3-top5": {
        "title_prefix": "Track 3 — LLM·RAG",
        "en_label_prefix": "TRACK 3 · LLM·RAG",
        "bg": "#F0FDFA",
        "grad": ["#0F766E", "#14B8A6"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#CCFBF1", "stroke": "#5EEAD4",
        "text_main": "#134E4A", "text_sub": "#115E59",
        "cross_ref_label": "사업계획서 §4·§5 본문 5 블록 paste 가능 (Track 3)",
    },
    "pkg2-cold-rolled": {
        "title_prefix": "패키지 2 — 중견 냉연 12 개월",
        "en_label_prefix": "PKG 2 · COLD-ROLLED",
        "bg": "#EEF2FF",
        "grad": ["#3730A3", "#4F46E5"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#F1F5F9", "stroke": "#818CF8",
        "text_main": "#1E1B4B", "text_sub": "#475569",
        "cross_ref_label": "패키지 2 통합 파일럿 §3·§4 paste 가능",
    },
    "pkg3-special-pipe": {
        "title_prefix": "패키지 3 — 특수강관 RAG 9 개월",
        "en_label_prefix": "PKG 3 · SPECIALTY PIPE RAG",
        "bg": "#F0FDFA",
        "grad": ["#0F766E", "#14B8A6"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#CCFBF1", "stroke": "#5EEAD4",
        "text_main": "#134E4A", "text_sub": "#115E59",
        "cross_ref_label": "패키지 3 통합 파일럿 paste 가능",
    },
    "pkg4-rubber": {
        "title_prefix": "패키지 4 — 고무 양산 OEM",
        "en_label_prefix": "PKG 4 · RUBBER OEM",
        "bg": "#FFFBEB",
        "grad": ["#F59E0B", "#FB923C"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#FEF3C7", "stroke": "#FBBF24",
        "text_main": "#78350F", "text_sub": "#92400E",
        "cross_ref_label": "패키지 4 통합 파일럿 paste 가능",
    },
    "pkg5-precision": {
        "title_prefix": "패키지 5 — 정밀가공 SaaS",
        "en_label_prefix": "PKG 5 · PRECISION SAAS",
        "bg": "#F0F9FF",
        "grad": ["#0EA5E9", "#38BDF8"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#E0F2FE", "stroke": "#7DD3FC",
        "text_main": "#0C4A6E", "text_sub": "#075985",
        "cross_ref_label": "패키지 5 통합 파일럿 paste 가능",
    },
    "pkg6-util-esg": {
        "title_prefix": "패키지 6 — 유틸·ESG·CBAM",
        "en_label_prefix": "PKG 6 · UTILITY · ESG",
        "bg": "#F0FDF4",
        "grad": ["#15803D", "#22C55E"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#DCFCE7", "stroke": "#86EFAC",
        "text_main": "#14532D", "text_sub": "#166534",
        "cross_ref_label": "패키지 6 통합 파일럿 paste 가능",
    },
    "detail-top5": {
        "title_prefix": "시나리오 상세 — 철강 Top 5",
        "en_label_prefix": "SCN · STEEL TOP 5",
        "bg": "#EEF2FF",
        "grad": ["#3730A3", "#6366F1"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#E0E7FF", "stroke": "#A5B4FC",
        "text_main": "#312E81", "text_sub": "#3730A3",
        "cross_ref_label": "시나리오 상세 paste 가능",
    },
    "detail-phase2": {
        "title_prefix": "시나리오 — 압연·소둔 Phase 2",
        "en_label_prefix": "SCN · PHASE 2",
        "bg": "#EEF2FF",
        "grad": ["#3730A3", "#6366F1"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#E0E7FF", "stroke": "#A5B4FC",
        "text_main": "#312E81", "text_sub": "#3730A3",
        "cross_ref_label": "Phase 2 시나리오 paste 가능",
    },
    "detail-rub": {
        "title_prefix": "시나리오 — 고무·폴리머",
        "en_label_prefix": "SCN · RUBBER",
        "bg": "#FFFBEB",
        "grad": ["#F59E0B", "#FB923C"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#FEF3C7", "stroke": "#FBBF24",
        "text_main": "#78350F", "text_sub": "#92400E",
        "cross_ref_label": "고무 시나리오 paste 가능",
    },
    "detail-utl-saf": {
        "title_prefix": "시나리오 — 유틸·안전",
        "en_label_prefix": "SCN · UTL · SAF",
        "bg": "#F0FDF4",
        "grad": ["#15803D", "#22C55E"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#DCFCE7", "stroke": "#86EFAC",
        "text_main": "#14532D", "text_sub": "#166534",
        "cross_ref_label": "UTL·SAF 시나리오 paste 가능",
    },
    "detail-special-pipe": {
        "title_prefix": "시나리오 — 특수강관 RAG",
        "en_label_prefix": "SCN · SPECIAL PIPE",
        "bg": "#F0FDFA",
        "grad": ["#0F766E", "#14B8A6"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#CCFBF1", "stroke": "#5EEAD4",
        "text_main": "#134E4A", "text_sub": "#115E59",
        "cross_ref_label": "특수강관 RAG 시나리오 paste 가능",
    },
    # 운영 가이드
    "duration-compress": {
        "title_prefix": "사업기간 압축",
        "en_label_prefix": "GUIDE · DURATION COMPRESS",
        "bg": "#EEF2FF",
        "grad": ["#3730A3", "#6366F1"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#E0E7FF", "stroke": "#A5B4FC",
        "text_main": "#312E81", "text_sub": "#3730A3",
        "cross_ref_label": "사업기간 압축 가이드 본문",
    },
    "external-validation": {
        "title_prefix": "외부검증 운영",
        "en_label_prefix": "GUIDE · EXTERNAL VALIDATION",
        "bg": "#EEF2FF",
        "grad": ["#3730A3", "#6366F1"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#E0E7FF", "stroke": "#A5B4FC",
        "text_main": "#312E81", "text_sub": "#3730A3",
        "cross_ref_label": "외부검증 가이드 본문",
    },
    # 모듈
    "saas-security": {
        "title_prefix": "SaaS·클라우드 보안",
        "en_label_prefix": "MODULE · SAAS SECURITY",
        "bg": "#FAF5FF",
        "grad": ["#6D28D9", "#8B5CF6"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#F3E8FF", "stroke": "#C4B5FD",
        "text_main": "#4C1D95", "text_sub": "#5B21B6",
        "cross_ref_label": "SaaS 보안 모듈 본문",
    },
    "oem-supply": {
        "title_prefix": "OEM 공급망 정합",
        "en_label_prefix": "MODULE · OEM SUPPLY",
        "bg": "#FFFBEB",
        "grad": ["#F59E0B", "#FB923C"],
        "card_fill_top": "#FFFFFF", "card_fill_bot": "#FEF3C7", "stroke": "#FBBF24",
        "text_main": "#78350F", "text_sub": "#92400E",
        "cross_ref_label": "OEM 공급망 모듈 본문",
    },
}

# fallback (slug 미매핑 시)
DEFAULT_META = {
    "title_prefix": "도식",
    "en_label_prefix": "DIAGRAM",
    "bg": "#F8FAFC",
    "grad": ["#475569", "#64748B"],
    "card_fill_top": "#FFFFFF", "card_fill_bot": "#F1F5F9", "stroke": "#94A3B8",
    "text_main": "#0F172A", "text_sub": "#334155",
    "cross_ref_label": "본문 paste 가능",
}


def is_mmdc_svg(svg_path: Path) -> bool:
    try:
        text = svg_path.read_text(encoding="utf-8", errors="ignore")[:500]
        return ('id="my-svg"' in text or 'class="flowchart"' in text or 'aria-roledescription="flowchart' in text)
    except Exception:
        return False


def extract_nodes(svg_path: Path) -> list[dict]:
    """SVG 안 노드 텍스트 추출 — flowchart·gantt·sequence 모두 fallback."""
    text = svg_path.read_text(encoding="utf-8", errors="ignore")
    # 1차: flowchart nodeLabel 의 <p>
    raw = re.findall(r'class="nodeLabel"[^>]*><p[^>]*>(.*?)</p>', text, re.DOTALL)
    # 2차: gantt taskText
    if not raw:
        raw = re.findall(r'class="taskText[^"]*"[^>]*>([^<]+?)</text>', text)
        # gantt section title
        if not raw:
            raw = re.findall(r'class="[^"]*sectionTitle[^"]*"[^>]*>([^<]+?)</text>', text)
        if raw:
            return [{"main": t.strip(), "sub": ""} for t in raw[:8] if t.strip() and len(t.strip()) >= 2]
    # 3차: sequenceDiagram actor / message
    if not raw:
        actors = re.findall(r'class="actor[^"]*"[^>]*>([^<]+?)</text>', text)
        messages = re.findall(r'class="messageText[^"]*"[^>]*>([^<]+?)</text>', text)
        combined = actors + messages
        if combined:
            return [{"main": t.strip(), "sub": ""} for t in combined[:8] if t.strip() and len(t.strip()) >= 2]
    # 4차: 모든 <text> 태그 (최후 fallback)
    if not raw:
        raw = re.findall(r"<text[^>]*>([^<]{2,80})</text>", text)
        if raw:
            return [{"main": t.strip(), "sub": ""} for t in raw[:8] if t.strip()]
    if not raw:
        # 5차: 모든 <p> 태그
        raw = re.findall(r"<p[^>]*>(.*?)</p>", text, re.DOTALL)

    nodes = []
    seen = set()
    for n_raw in raw:
        # <br /> 또는 <br/> 또는 <br> 를 sep 로 메인/부속 분리
        parts = re.split(r"<br\s*/?>", n_raw)
        main = parts[0].strip()
        sub = parts[1].strip() if len(parts) > 1 else ""
        # HTML entity decode (&amp; · &lt; · &gt;)
        main = main.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        sub = sub.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        # XML 태그 제거 (잔존 HTML)
        main = re.sub(r"<[^>]+>", "", main).strip()
        sub = re.sub(r"<[^>]+>", "", sub).strip()
        if not main or main in seen:
            continue
        if len(main) < 2:
            continue
        seen.add(main)

        # sub 가 없는 경우 — 메인에서 자동 분리 시도
        if not sub:
            m = re.match(r"^(.+?)\s*[(\[]([^)\]]+)[)\]]\s*$", main)
            if m:
                main = m.group(1).strip()
                sub = m.group(2).strip()
            else:
                for sep in (" — ", " · ", ": "):
                    if sep in main and len(main) > 8:
                        p = main.split(sep, 1)
                        main = p[0].strip()
                        sub = p[1].strip()
                        break

        nodes.append({"main": main, "sub": sub})
        if len(nodes) >= 8:
            break
    return nodes


def auto_spec(svg_path: Path) -> dict | None:
    """mmdc SVG 에서 자동 SPEC 생성. 노드 < 3 이면 None (skip)."""
    nodes = extract_nodes(svg_path)
    if len(nodes) < 3:
        return None

    slug = svg_path.parent.name
    diagram = svg_path.name
    n = re.search(r"diagram-(\d+)\.svg", diagram)
    diagram_n = n.group(1) if n else "?"

    meta = DOMAIN_META.get(slug, DEFAULT_META)

    return {
        "slug": f"auto_{slug}_{diagram_n}",
        "path": f"{slug}/{diagram}",
        "title": f"{meta['title_prefix']} (도식 {diagram_n})",
        "subtitle": " · ".join([n["main"] for n in nodes[:3]]),
        "en_label": f"{meta['en_label_prefix']} · DIAGRAM {diagram_n}",
        "desc": f"{meta['title_prefix']} 의 {diagram_n}번 도식 — {len(nodes)} 단계",
        "bg": meta["bg"],
        "grad": meta["grad"],
        "card_fill_top": meta["card_fill_top"],
        "card_fill_bot": meta["card_fill_bot"],
        "stroke": meta["stroke"],
        "text_main": meta["text_main"],
        "text_sub": meta["text_sub"],
        "cross_ref_label": meta["cross_ref_label"],
        "cross_ref_1": f"노드 {len(nodes)} 단계 — 직각 화살표 흐름",
        "cross_ref_2": f"디자인 SVG (Phase E15 정책) · 600×800 portrait",
        "nodes": nodes,
    }


def main():
    svgs = sorted(DIAGRAMS_BASE.rglob("diagram-*.svg"))
    mmdc_svgs = [s for s in svgs if is_mmdc_svg(s)]
    print(f"## 대상 mmdc SVG: {len(mmdc_svgs)} (전체 {len(svgs)})")

    converted = 0
    skipped = 0
    for svg in mmdc_svgs:
        spec = auto_spec(svg)
        if spec is None:
            print(f"  ⚠ skip (노드 < 3): {svg.parent.name}/{svg.name}")
            skipped += 1
            continue
        new_svg = render_svg(spec)
        svg.write_text(new_svg, encoding="utf-8")
        converted += 1
        print(f"  ✓ {svg.parent.name}/{svg.name} ({len(spec['nodes'])} 노드)")

    print(f"\n## 변환: {converted} · 스킵: {skipped}")


if __name__ == "__main__":
    main()
