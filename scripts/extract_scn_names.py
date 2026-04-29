"""extract_scn_names.py — Phase E14-B

시나리오_카탈로그.md 에서 `### SCN-XXX-NN : 이름` 패턴 추출 → docs/data/scn_names.json.

linkify_scenario_id.py hook 의 입력 데이터.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path("/Volumes/EXDATA/temp_git/ai-docs-for-biz")
CATALOG = ROOT / "시나리오_카탈로그.md"
OUTPUT = ROOT / "docs" / "data" / "scn_names.json"

# 패턴: `### SCN-XXX-NN : 이름` 또는 `## SCN-XXX-NN — 이름`
PATTERN = re.compile(
    r"^###?\s+(SCN-[A-Z]+-\d+)\s*[:—\-–]?\s*(.+?)\s*$",
    re.MULTILINE,
)


def main():
    text = CATALOG.read_text(encoding="utf-8")
    names = {}
    for m in PATTERN.finditer(text):
        scn_id = m.group(1)
        name = m.group(2).strip()
        # 더 짧은 이름 우선 (catalog 의 ### 가 가장 정제됨)
        if scn_id not in names or len(name) < len(names[scn_id]):
            names[scn_id] = name

    # 보조 — 시나리오 상세 5 + 패키지 6 도 fallback 으로 파싱
    for fname in [
        "시나리오_상세_Top5.md",
        "시나리오_상세_Phase2.md",
        "시나리오_상세_RUB.md",
        "시나리오_상세_UTL_SAF.md",
        "시나리오_상세_특수강관.md",
    ]:
        fp = ROOT / fname
        if fp.exists():
            for m in PATTERN.finditer(fp.read_text(encoding="utf-8")):
                scn_id = m.group(1)
                name = m.group(2).strip()
                if scn_id not in names:
                    names[scn_id] = name

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(names, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[extract_scn_names] {len(names)} SCN → {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
