"""linkify_sources.py — `> [출처: 파일명 §섹션]` 인용 표기를 자동 링크화.

본문에 274 회 사용된 출처 인용 표기 패턴 (CLAUDE.md §인용 출처 표기 표준) 을
slug_map.yml 기반 내부 링크로 변환하여 페이지 간 cross-reference 망을 시각화한다.

대상 패턴:
  > [출처: track1_공통본문_목차.md §3.1 발췌·요약]
변환 결과:
  > [출처: [track1_공통본문_목차.md](../track/track1-index.md) §3.1 발췌·요약]

slug_map 의 키 (한글 파일명) 을 인식해 영문 slug 경로로 링크 변환한다.
slug_map 에 없는 파일명은 변환하지 않고 보존.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

_SLUG_MAP: dict[str, str] | None = None

# 출처 인용 패턴 — `> [출처: 파일명.md §섹션 ...]`
SOURCE_RE = re.compile(
    r"(\[출처:\s*)([^\s\]]+\.md)(\s*[^\]]*\])"
)


def load_slug_map(config) -> dict[str, str]:
    global _SLUG_MAP
    if _SLUG_MAP is not None:
        return _SLUG_MAP

    config_dir = Path(config["config_file_path"]).parent
    slug_path = config_dir / "slug_map.yml"
    with slug_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    _SLUG_MAP = raw
    return raw


def linkify(text: str, slug_map: dict[str, str], current_dir: Path) -> str:
    """본문 내 출처 표기를 slug 경로 링크로 변환."""

    def replace_one(match: re.Match[str]) -> str:
        prefix = match.group(1)  # `[출처: `
        filename = match.group(2)  # `track1_공통본문_목차.md`
        suffix = match.group(3)  # ` §3.1 발췌·요약]`

        target_slug = slug_map.get(filename)
        if not target_slug:
            return match.group(0)

        # 현재 페이지 디렉토리에서 target_slug 까지의 상대 경로
        try:
            current_path = Path("docs") / current_dir
            target_path = Path("docs") / target_slug
            # 상대 경로 계산
            rel = "/".join([".."] * len(current_path.parts[1:])) + "/" + target_slug
            rel = rel.lstrip("/")
            if not rel.startswith(".."):
                rel = "./" + rel
        except Exception:
            rel = target_slug

        return f"{prefix}[{filename}]({rel}){suffix}"

    return SOURCE_RE.sub(replace_one, text)


def on_page_markdown(markdown: str, page, config, files):  # noqa: ARG001
    slug_map = load_slug_map(config)
    src_path = page.file.src_path
    current_dir = Path(src_path).parent
    return linkify(markdown, slug_map, current_dir)
