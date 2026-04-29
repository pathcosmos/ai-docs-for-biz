#!/usr/bin/env python3
"""
Phase E12-B — mmdc 변환 SVG style 일괄 patch.

mmdc (mermaid-cli) 가 생성한 91 SVG 의 inline <style> 태그 안에는
mermaid default 폰트 (`trebuchet ms`) + default palette (#ECECFF / #9370DB / #333 등) 가
박혀 있어 시각적으로 mermaid 그대로 보인다.

본 스크립트는 docs/assets/diagrams/**/*.svg 를 순회하며
정규식으로 폰트 + 색상 토큰을 SaaS indigo·violet·slate·emerald 로 일괄 치환한다.

특징
- idempotent: 재실행해도 동일 결과 (이미 patch 된 파일은 변경 0).
- byte size 비교 + XML well-formed 검증.
- inline style="max-width: NNNpx" 등 lightbox 의존 속성은 보존.

사용:
    python scripts/patch_mmdc_svg_style.py
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path("/Volumes/EXDATA/temp_git/ai-docs-for-biz")
SVG_DIR = ROOT / "docs/assets/diagrams"

# 정규식 치환 테이블 — 순서 중요 (앞쪽이 먼저 치환).
# 색상 hex 토큰은 (?![\dA-Fa-f]) lookahead 로 정확 매치 (예: #333 가 #3333 의 일부로
# 잘리지 않도록).
REPLACEMENTS: list[tuple[str, str]] = [
    # ─ 폰트 ─────────────────────────────────────────────
    (r'"trebuchet ms"', '"Pretendard"'),
    (
        r'trebuchet ms,verdana,arial,sans-serif',
        'Pretendard, system-ui, -apple-system, sans-serif',
    ),
    # ─ 색상 (mermaid default → SaaS indigo·violet·slate) ─
    # cluster bg
    (r'#ECECFF', '#EEF2FF'),
    (r'#ececff', '#EEF2FF'),
    # cluster stroke / neo accent
    (r'#9370DB', '#818CF8'),
    (r'#9370db', '#818CF8'),
    # node stroke·text deep
    (r'#333(?![\dA-Fa-f])', '#4338CA'),
    # subtle line
    (r'#ddd(?![\dA-Fa-f])', '#E2E8F0'),
    # text muted
    (r'#888(?![\dA-Fa-f])', '#64748B'),
    # subgraph alt bg
    (r'#f4f4f4', '#F8FAFC'),
    (r'#F4F4F4', '#F8FAFC'),
    # text mid
    (r'#555(?![\dA-Fa-f])', '#334155'),
    # line gray
    (r'#BFBFBF', '#CBD5E1'),
    (r'#bfbfbf', '#CBD5E1'),
    # line alt indigo lavender
    (r'#ABA9CC', '#C7D2FE'),
    (r'#aba9cc', '#C7D2FE'),
    # text deep
    (r'#444(?![\dA-Fa-f])', '#1E293B'),
]


def patch_text(text: str) -> str:
    """REPLACEMENTS 를 순서대로 적용한 새 문자열을 반환."""
    new = text
    for pat, repl in REPLACEMENTS:
        new = re.sub(pat, repl, new)
    return new


def is_valid_xml(p: Path) -> bool:
    """ElementTree 로 parse 가능한지 검증 (SVG 는 XML)."""
    try:
        ET.parse(p)
        return True
    except ET.ParseError:
        return False


def main() -> int:
    if not SVG_DIR.exists():
        print(f"[ERROR] SVG_DIR 없음: {SVG_DIR}", file=sys.stderr)
        return 1

    svgs = sorted(SVG_DIR.rglob("*.svg"))
    if not svgs:
        print(f"[WARN] SVG 0 종 (대상 없음): {SVG_DIR}")
        return 0

    changed = 0
    skipped_invalid = 0
    size_delta_total = 0

    for svg in svgs:
        before = svg.read_text(encoding="utf-8")
        after = patch_text(before)

        if after == before:
            continue

        size_before = len(before.encode("utf-8"))
        size_after = len(after.encode("utf-8"))
        delta = size_after - size_before

        # write 후 XML 유효성 재확인.
        svg.write_text(after, encoding="utf-8")
        if not is_valid_xml(svg):
            # roll back.
            svg.write_text(before, encoding="utf-8")
            print(f"[INVALID-XML 복구] {svg.relative_to(ROOT)}", file=sys.stderr)
            skipped_invalid += 1
            continue

        changed += 1
        size_delta_total += delta

    print(
        f"[patch_mmdc_svg] 변경 {changed}/{len(svgs)} SVG · "
        f"size Δ {size_delta_total:+d} bytes · invalid 롤백 {skipped_invalid}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
