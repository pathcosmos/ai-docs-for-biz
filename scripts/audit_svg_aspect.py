"""audit_svg_aspect.py — 91 mmdc SVG aspect ratio 전수 인벤토리 (Phase E15)

각 SVG 의 viewBox·width·height 추출 + aspect ratio 계산.
가로형 (ratio > 1.5) 식별 → 세로형 재작업 대상 목록 출력.
"""

from __future__ import annotations

import re
import json
from pathlib import Path

ROOT = Path("/Volumes/EXDATA/temp_git/ai-docs-for-biz")
DIAGRAMS = ROOT / "docs" / "assets" / "diagrams"

VIEWBOX_RE = re.compile(r'viewBox="0 0 ([\d.]+) ([\d.]+)"')


def main():
    results = []
    for svg in sorted(DIAGRAMS.rglob("*.svg")):
        text = svg.read_text(encoding="utf-8", errors="ignore")[:500]
        m = VIEWBOX_RE.search(text)
        if not m:
            continue
        w = float(m.group(1))
        h = float(m.group(2))
        ratio = w / h if h > 0 else 0
        # 노드 텍스트 추출 (mermaid syntax 노드 이름 첫 5 개)
        node_texts = re.findall(r'<span[^>]*class="nodeLabel[^"]*">([^<]+)</span>', svg.read_text(encoding="utf-8", errors="ignore"))[:5]
        results.append({
            "path": str(svg.relative_to(ROOT)),
            "slug": svg.parent.name,
            "diagram": svg.name,
            "width": w,
            "height": h,
            "ratio": round(ratio, 2),
            "orientation": "horizontal" if ratio > 1.5 else "vertical" if ratio < 0.7 else "square",
            "first_nodes": node_texts,
        })

    # 분류
    horizontal = [r for r in results if r["orientation"] == "horizontal"]
    vertical = [r for r in results if r["orientation"] == "vertical"]
    square = [r for r in results if r["orientation"] == "square"]

    print(f"## Total: {len(results)} SVG")
    print(f"  - 가로형 (ratio > 1.5): {len(horizontal)}")
    print(f"  - 세로형 (ratio < 0.7): {len(vertical)}")
    print(f"  - 정사각형: {len(square)}")
    print()
    print(f"## 가로형 분포 (ratio 큰 순):")
    for r in sorted(horizontal, key=lambda x: -x["ratio"])[:30]:
        print(f"  {r['ratio']:6.2f} {int(r['width']):>5}×{int(r['height']):<5} {r['path']}")
        if r["first_nodes"]:
            print(f"        nodes: {' | '.join(r['first_nodes'][:3])}")

    # JSON 출력
    output = ROOT / "docs" / "data" / "svg_aspect_audit.json"
    output.write_text(
        json.dumps({"horizontal": horizontal, "vertical": vertical, "square": square}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[output] {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
