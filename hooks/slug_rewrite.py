"""slug_rewrite.py — 본문 내 한글 .md 참조를 영문 slug 경로로 치환 (MkDocs 훅).

대상 패턴:
1. 백틱 인용 — `track1_공통본문_목차.md` → `track/track1-index.md`
2. 마크다운 링크 — [텍스트](track1_공통본문_목차.md) → [텍스트](track/track1-index.md)
3. 인용 출처 — `> [출처: track1_공통본문_목차.md §3.1]` → 동일 패턴 + slug 치환

slug_map.yml 은 워크스페이스 루트 (mkdocs.yml 과 동일 디렉토리) 에 위치.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

_SLUG_MAP: dict[str, str] | None = None


def load_slug_map(config) -> dict[str, str]:
    global _SLUG_MAP
    if _SLUG_MAP is not None:
        return _SLUG_MAP

    config_path = Path(config["config_file_path"]).parent
    slug_path = config_path / "slug_map.yml"
    with slug_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # 정렬: 긴 파일명부터 치환 (부분 매칭 회피)
    sorted_map = dict(sorted(raw.items(), key=lambda kv: len(kv[0]), reverse=True))
    _SLUG_MAP = sorted_map
    return sorted_map


def slug_for(filename: str, slug_map: dict[str, str]) -> str | None:
    return slug_map.get(filename)


def rewrite(text: str, slug_map: dict[str, str]) -> str:
    """본문 내 한글 .md 참조를 slug 경로로 치환."""

    def replace_one(match: re.Match[str]) -> str:
        original = match.group(0)
        filename = match.group(1) + ".md"
        target = slug_for(filename, slug_map)
        if not target:
            return original
        # 원본 패턴 유지하되 .md 부분만 치환
        return original.replace(filename, target)

    # 한글·숫자·영문·언더스코어·하이픈·점 조합 + .md
    pattern = re.compile(r"([\wㄱ-힝\.\-]+?)\.md")
    return pattern.sub(replace_one, text)


def on_page_markdown(markdown: str, page, config, files):  # noqa: ARG001
    slug_map = load_slug_map(config)
    return rewrite(markdown, slug_map)
