"""build_templates_data.py — Phase E16-1 (Stage 1)

빌드 시점에 Track 1·2·3 top5 페이지의 BLK 본문 추출 → docs/data/templates.json.

generate.md 페이지의 JavaScript 가 fetch 하여 placeholder 치환 + 본문 자동 생성에 사용.

대상:
- docs/track/track1-top5.md (Track 1 BLK 5 종 — BLK-T1-3.1·3.2·4.4·4.5·4.6)
- docs/track/track2-top5.md (Track 2 BLK 5 종 — BLK-T2-3.2·4.2·4.4·5.5·6.1)
- docs/track/track3-top5.md (Track 3 BLK 5 종 — BLK-T3-3.1·3.2·4.2·5.2·5.5)

각 BLK 본문 = H2 부터 다음 H2 또는 ` ### 도식 ` 직전까지의 paragraph (### 본문·### 도식 제외).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# H2 BLK 패턴 2 종:
# Format A (Track 1·3): `## 3.1 제목 (블록명: BLK-T1-3.1)` 또는 `## 3.1 제목 (BLK-T1-3.1)`
# Format B (Track 2):   `## BLK-T2-3.2 — 제목`
H2_BLK_RE = re.compile(
    r"^## (?:"
    r"(?P<sectionA>\d+\.\d+)\s+(?P<titleA>.+?)\s*\((?:블록명:\s*)?(?P<idA>BLK-T\d-\d+\.\d+)\)"
    r"|"
    r"(?P<idB>BLK-T(?P<trackB>\d)-(?P<sectionB>\d+\.\d+))\s*[—\-–]\s*(?P<titleB>.+?)"
    r")\s*$",
    re.MULTILINE,
)

# 본문 추출 대상 H3 (### 본문 — admonition·copy 안의 본문 단락)
H3_BODY_RE = re.compile(r"^###\s+본문\s*$", re.MULTILINE)
# 본문 끝 — ### 도식 또는 다음 H2
H3_END_RE = re.compile(r"^(###\s+(?:삽화|도식)|## )", re.MULTILINE)

# 출처 인용 줄 (`> [출처: ...]`) 도 본문에 포함 (사업계획서 paste 시 출처 명시 가치)
# 단 ### 도식 (Mermaid 또는 SVG) 는 제외


def parse_h2(match: re.Match[str]) -> tuple[str, str]:
    """매치에서 (block_id, title) 추출."""
    if match.group("idA"):
        return match.group("idA"), match.group("titleA").strip()
    return match.group("idB"), match.group("titleB").strip()


def extract_blk_body(content: str, h2_start: int, h2_end: int) -> str:
    """H2 BLK 의 본문 (### 본문 다음 단락) 추출."""
    block_text = content[h2_start:h2_end]
    # ### 본문 위치
    body_match = H3_BODY_RE.search(block_text)
    if not body_match:
        # ### 본문 없으면 H2 다음 첫 단락 (관용)
        body_start = block_text.find("\n", 0) + 1
    else:
        body_start = body_match.end() + 1

    # ### 도식 또는 다음 ### 직전까지
    rest = block_text[body_start:]
    end_match = H3_END_RE.search(rest)
    body = rest[:end_match.start()] if end_match else rest

    return body.strip()


def extract_templates(md_path: Path) -> dict:
    """단일 .md 파일에서 모든 BLK 본문 추출."""
    if not md_path.exists():
        return {}
    content = md_path.read_text(encoding="utf-8")
    matches = list(H2_BLK_RE.finditer(content))
    if not matches:
        return {}

    templates = {}
    for i, m in enumerate(matches):
        blk_id, title = parse_h2(m)
        h2_start = m.end()
        h2_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = extract_blk_body(content, h2_start, h2_end)
        templates[blk_id] = {
            "title": f"{blk_id} — {title}",
            "body": body,
        }
    return templates


def on_pre_build(config):
    """MkDocs 훅 — 빌드 시점 templates.json 자동 생성."""
    docs_dir = Path(config["docs_dir"])
    sources = [
        "track/track1-top5.md",
        "track/track2-top5.md",
        "track/track3-top5.md",
    ]

    all_templates = {}
    for src in sources:
        templates = extract_templates(docs_dir / src)
        all_templates.update(templates)

    output = docs_dir / "data" / "templates.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(all_templates, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[build_templates_data] {len(all_templates)} BLK → {output.relative_to(docs_dir)}")
