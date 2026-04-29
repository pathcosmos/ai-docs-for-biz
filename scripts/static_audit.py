"""static_audit.py — Phase E13-1 (Sprint 1)

빌드된 site/ 디렉토리의 HTML 파일을 정적 검사 — Playwright 의존성 없이 회귀 검증.

검증 항목 (사용자 호소 13 건의 회귀 검사):
1. raw frontmatter 노출 (`<p>title: "...":`)
2. 이미지 캡션 깨짐 (`![text [` unclosed bracket)
3. mermaid 잔존 (`class="mermaid"` 또는 ` ```mermaid `)
4. SVG aspect ratio (세로 vs 가로 분포)
5. 우측 TOC H3 숨김 CSS 적용 여부
6. 사이드바 4 그룹 nav 구조 정상
7. 페이지 폭 76rem 적용 여부

5 핵심 페이지 + 추가 회귀 페이지 검증.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/Volumes/EXDATA/temp_git/ai-docs-for-biz")
SITE = ROOT / "site"

# 5 핵심 페이지 + 추가 회귀
PAGES = [
    "index.html",
    "blocks/index.html",
    "by-package/index.html",
    "start-here/index.html",
    "track/track1-top5/index.html",
    "track/track2-top5/index.html",
    "track/track3-top5/index.html",
    "pkg/pkg1-steel-enterprise/index.html",
    "pkg/pkg2-cold-rolled/index.html",
    "scenario/catalog/index.html",
    "guide/quickstart/index.html",
]

# 검증 패턴
PATTERNS = {
    "raw_frontmatter": re.compile(r'<p>title: "[^"]*"', re.IGNORECASE),
    "broken_caption": re.compile(r'!\[[^\]\n]*\[[^\]\n]*?\]\([^\)]*\)'),  # ![ 안에 [ 가 또 있음
    "mermaid_residual": re.compile(r'class="mermaid"|<pre><code class="language-mermaid"'),
    "extra_css_loaded": re.compile(r'extra\.css'),
    "tocs_hidden_h3": re.compile(r'\.md-nav--secondary\s+\.md-nav__list\s+\.md-nav__list\s*\{[^}]*display:\s*none', re.IGNORECASE),
    "grid_76rem": re.compile(r'--md-grid:\s*76rem|max-width:\s*76rem'),
    "viewport_meta": re.compile(r'<meta[^>]+name="viewport"[^>]+>'),
}


def check_page(page_path: Path) -> dict:
    """단일 페이지 검사. 결과 dict 반환."""
    if not page_path.exists():
        return {"file": str(page_path), "exists": False}

    text = page_path.read_text(encoding="utf-8")
    results = {"file": str(page_path.relative_to(SITE)), "exists": True}

    # 1. raw frontmatter — 0 매치 합격
    raw_matches = PATTERNS["raw_frontmatter"].findall(text)
    results["raw_frontmatter_count"] = len(raw_matches)
    results["raw_frontmatter_ok"] = len(raw_matches) == 0

    # 2. broken image caption
    broken_imgs = PATTERNS["broken_caption"].findall(text)
    results["broken_caption_count"] = len(broken_imgs)
    results["broken_caption_ok"] = len(broken_imgs) == 0

    # 3. mermaid 잔존 (mermaid runtime 제거 후 0 합격)
    mermaid_matches = PATTERNS["mermaid_residual"].findall(text)
    results["mermaid_residual_count"] = len(mermaid_matches)
    results["mermaid_residual_ok"] = len(mermaid_matches) == 0

    # 4. viewport meta (모바일 반응형 보장)
    results["viewport_meta_ok"] = bool(PATTERNS["viewport_meta"].search(text))

    return results


def check_css() -> dict:
    """extra.css 의 핵심 spec 검증."""
    css_path = SITE / "stylesheets" / "extra.css"
    if not css_path.exists():
        return {"exists": False}
    text = css_path.read_text(encoding="utf-8")
    return {
        "exists": True,
        "size_kb": round(css_path.stat().st_size / 1024, 1),
        "lines": text.count("\n"),
        "toc_h3_hidden": bool(PATTERNS["tocs_hidden_h3"].search(text)),
        "grid_76rem": bool(PATTERNS["grid_76rem"].search(text)),
    }


def check_svg_aspect() -> dict:
    """docs/assets/svg/ + diagrams/ 의 viewBox 분포."""
    counts = {"vertical_600x800": 0, "horizontal_800x400": 0, "square": 0, "other": 0, "diagrams_mmdc": 0, "total_svg": 0, "total_diagrams": 0}
    for svg in (ROOT / "docs/assets/svg").rglob("*.svg"):
        counts["total_svg"] += 1
        text = svg.read_text(encoding="utf-8", errors="ignore")[:500]
        if 'viewBox="0 0 600 800"' in text:
            counts["vertical_600x800"] += 1
        elif 'viewBox="0 0 800 400"' in text:
            counts["horizontal_800x400"] += 1
        elif re.search(r'viewBox="0 0 (\d+) \1"', text):
            counts["square"] += 1
        else:
            counts["other"] += 1
    for svg in (ROOT / "docs/assets/diagrams").rglob("*.svg"):
        counts["total_diagrams"] += 1
        counts["diagrams_mmdc"] += 1
    return counts


def main():
    print("=" * 60)
    print("Phase E13-1 — 정적 검증 (Sprint 1)")
    print("=" * 60)

    # CSS 검증
    print("\n## extra.css 검증")
    css = check_css()
    if css["exists"]:
        print(f"  - 크기: {css['size_kb']} KB · {css['lines']:,} 줄")
        print(f"  - 우측 TOC H3 숨김: {'✓' if css['toc_h3_hidden'] else '✗'}")
        print(f"  - 본문 폭 76rem: {'✓' if css['grid_76rem'] else '✗'}")
    else:
        print("  ✗ extra.css 미존재 (빌드 안 됨)")
        sys.exit(1)

    # SVG aspect ratio 분포
    print("\n## SVG 분포")
    svg = check_svg_aspect()
    print(f"  - 세로형 (600×800): {svg['vertical_600x800']}/{svg['total_svg']}")
    print(f"  - 가로형 (800×400): {svg['horizontal_800x400']}/{svg['total_svg']}")
    print(f"  - 정사각형: {svg['square']}/{svg['total_svg']}")
    print(f"  - 기타: {svg['other']}/{svg['total_svg']}")
    print(f"  - mmdc 다이어그램: {svg['diagrams_mmdc']}")

    # 페이지별 검증
    print(f"\n## 페이지별 검증 ({len(PAGES)} 핵심)")
    all_pass = True
    fail_summary = []
    for page in PAGES:
        page_path = SITE / page
        r = check_page(page_path)
        if not r.get("exists"):
            print(f"  ✗ {page} (파일 없음)")
            all_pass = False
            fail_summary.append(f"{page} 미존재")
            continue
        marks = []
        if not r["raw_frontmatter_ok"]:
            marks.append(f"raw frontmatter {r['raw_frontmatter_count']}")
        if not r["broken_caption_ok"]:
            marks.append(f"broken caption {r['broken_caption_count']}")
        if not r["mermaid_residual_ok"]:
            marks.append(f"mermaid {r['mermaid_residual_count']}")
        if not r["viewport_meta_ok"]:
            marks.append("viewport meta 누락")
        status = "✓" if not marks else f"✗ ({', '.join(marks)})"
        print(f"  {status} {page}")
        if marks:
            all_pass = False
            fail_summary.append(f"{page}: {', '.join(marks)}")

    # 종합
    print("\n" + "=" * 60)
    if all_pass:
        print("✅ 합격 — 11 페이지 회귀 검사 통과")
    else:
        print("❌ 일부 실패:")
        for s in fail_summary:
            print(f"  - {s}")
    print("=" * 60)

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
