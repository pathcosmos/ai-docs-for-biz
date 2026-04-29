"""linkify_scenario_id.py — Phase E14-B

본문 안 SCN-XXX-NN ID 자동 hyperlink + tooltip (시나리오명).

동작:
- 패턴 매치: `\bSCN-(STL|MET|RUB|UTL|SAF|LLM|MLO|CSEC)-\d+\b`
- 변환: `SCN-STL-04` → `<a href="../scenario/catalog/#scn-stl-04" title="냉간압연 패스 스케줄 표준화·최적화" class="scn-link">SCN-STL-04</a>`
- 매핑: `docs/data/scn_names.json` (extract_scn_names.py 가 사전 생성)
- 제외: code block (` ``` `) / inline code (` ` `) / 이미 link 안 / heading (anchor 자기참조 회피)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# 패턴: SCN-(도메인)-(숫자)
SCN_PATTERN = re.compile(
    r"\bSCN-(STL|MET|RUB|UTL|SAF|LLM|MLO|CSEC)-(\d+)\b"
)

# code block / inline code 분리 정규식
CODE_SPLIT_RE = re.compile(
    r"(```[\s\S]*?```|`[^`\n]+`)",
    re.MULTILINE,
)

_NAMES_CACHE = None


def load_names(docs_dir: Path) -> dict:
    """docs/data/scn_names.json 로드 (캐시)."""
    global _NAMES_CACHE
    if _NAMES_CACHE is not None:
        return _NAMES_CACHE
    json_path = docs_dir / "data" / "scn_names.json"
    if not json_path.exists():
        _NAMES_CACHE = {}
        return _NAMES_CACHE
    _NAMES_CACHE = json.loads(json_path.read_text(encoding="utf-8"))
    return _NAMES_CACHE


def relative_catalog_href(src_path: str) -> str:
    """페이지 디렉토리에서 scenario/catalog 까지 상대 경로."""
    parts = src_path.split("/")
    depth = len(parts) - 1  # 디렉토리 깊이
    if src_path.startswith("scenario/"):
        # 같은 디렉토리 안 — catalog.md 직접 link
        return "catalog/"
    prefix = "../" * depth if depth > 0 else ""
    return prefix + "scenario/catalog/"


def linkify_text(text: str, names: dict, href_base: str) -> str:
    """text 안의 SCN ID 를 hyperlink 로 변환."""
    def replace(m: re.Match[str]) -> str:
        scn_id = m.group(0)
        # 이름 lookup
        name = names.get(scn_id, "")
        anchor = scn_id.lower()  # mkdocs auto anchor (### SCN-STL-04 → #scn-stl-04)
        href = f"{href_base}#{anchor}"
        title_attr = f' title="{name}"' if name else ""
        return f'<a href="{href}"{title_attr} class="scn-link">{scn_id}</a>'

    return SCN_PATTERN.sub(replace, text)


def linkify_markdown(markdown: str, src_path: str, names: dict) -> str:
    """마크다운에서 code block 외부의 SCN ID 만 hyperlink 변환.

    - 같은 페이지 (scenario/catalog.md) 자기 참조 회피
    - heading line 안 SCN ID (heading 자체) 도 회피
    """
    if src_path == "scenario/catalog.md":
        return markdown  # 카탈로그 자체는 anchor 자기 참조 회피

    href_base = relative_catalog_href(src_path)

    # code block / inline code 분리
    parts = CODE_SPLIT_RE.split(markdown)
    for i, part in enumerate(parts):
        if part.startswith("```") or (part.startswith("`") and part.endswith("`")):
            continue
        # heading line (^#) 안 SCN 은 anchor 와 충돌 회피 — heading 자체는 link 안 함
        # 단, heading 안 다른 부분 (예: ### SCN-STL-04 : 이름) 은 그대로 유지
        # 본문 (단락·표·리스트) 의 SCN 만 link
        new_part = []
        for line in part.split("\n"):
            if line.startswith("#"):
                # heading 안 SCN 은 anchor 자체이므로 link 안 함
                new_part.append(line)
            else:
                new_part.append(linkify_text(line, names, href_base))
        parts[i] = "\n".join(new_part)

    return "".join(parts)


def on_page_markdown(markdown: str, page, config, files):  # noqa: ARG001
    docs_dir = Path(config["docs_dir"])
    names = load_names(docs_dir)
    if not names:
        return markdown
    return linkify_markdown(markdown, page.file.src_path, names)
