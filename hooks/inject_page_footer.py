"""inject_page_footer.py — 페이지 상단 읽기 시간 배지 + 페이지 하단 메타 정보 details.

본 hook 은 2 가지 작업을 동시 수행:

1. **상단 — 읽기 시간 배지** (`📖 약 N 분`):
   - 한국어 본문 기준 분당 약 500 자 (한자·영문 혼합 평균)
   - 페이지 본문 글자 수 / 500 = 분 단위 (최소 1 분)
   - H1 직후에 작은 배지로 삽입

2. **하단 — 페이지 메타 정보 details** (개발자용):
   - 원본 한글 파일명 + slug + 자산 군 + 마지막 갱신
   - <details class="meta-footer"> 으로 collapsible (기본 닫힘)

홈·필터·그래프 등 특수 페이지는 제외.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

EXCLUDE_PAGES = {"index.md", "graph.md", "filter.md", "start-here.md", "by-package.md"}

# 자산 군별 라벨
GROUP_LABELS = {
    "track": "🔧 기술 트랙",
    "pkg": "📦 통합 파일럿",
    "guide": "📋 운영 가이드",
    "scenario": "🎯 시나리오",
    "module": "🧩 Cross-cutting 모듈",
    "other": "📚 참고 자산",
    "meta": "📌 메타",
}

_SLUG_REVERSE: dict[str, str] | None = None


def load_reverse_slug_map(config_dir: Path) -> dict[str, str]:
    """slug 경로 → 원본 한글 파일명 reverse 매핑."""
    global _SLUG_REVERSE
    if _SLUG_REVERSE is not None:
        return _SLUG_REVERSE

    slug_path = config_dir / "slug_map.yml"
    with slug_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    _SLUG_REVERSE = {v: k for k, v in raw.items()}
    return _SLUG_REVERSE


def calculate_reading_time(text: str) -> int:
    """한국어 본문 기준 분당 약 500 자. 최소 1 분."""
    # 마크다운 마크업·코드 블록·HTML 태그 제거 후 글자 수 카운트
    cleaned = re.sub(r"```[\s\S]*?```", "", text)  # fenced code
    cleaned = re.sub(r"<[^>]+>", "", cleaned)  # HTML tags
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)  # markdown links
    cleaned = re.sub(r"[#*`>|\-=]", "", cleaned)  # markdown markup
    cleaned = re.sub(r"\s+", "", cleaned)  # whitespace

    char_count = len(cleaned)
    minutes = max(1, char_count // 500)
    return minutes


def derive_group(src_path: str) -> str | None:
    parts = src_path.split("/")
    if len(parts) >= 2 and parts[0] in GROUP_LABELS:
        return parts[0]
    return None


def inject_top_reading_time(markdown: str, page) -> str:
    """H1 직후에 읽기 시간 배지 삽입."""
    minutes = calculate_reading_time(markdown)
    if minutes < 2:
        # 짧은 페이지는 배지 skip
        return markdown

    badge = f'\n<span class="reading-time-badge">📖 약 {minutes} 분 읽기</span>\n\n'

    # H1 직후에 삽입 (Front matter 보존)
    pattern = re.compile(r"(^#\s+.+?\n)", re.MULTILINE)
    new_markdown, count = pattern.subn(r"\1" + badge, markdown, count=1)
    return new_markdown if count > 0 else markdown


def inject_meta_footer(markdown: str, page, config) -> str:
    """페이지 하단에 메타 정보 details 추가."""
    src_path = page.file.src_path
    group = derive_group(src_path)
    if not group:
        return markdown

    config_dir = Path(config["config_file_path"]).parent
    reverse_map = load_reverse_slug_map(config_dir)
    original_filename = reverse_map.get(src_path, src_path)
    group_label = GROUP_LABELS.get(group, "기타")

    footer_block = (
        '\n\n??? note "📌 이 페이지 정보 (개발자용)"\n'
        f'    - **원본 파일**: `{original_filename}`\n'
        f'    - **자산 군**: {group_label}\n'
        f'    - **slug 경로**: `{src_path}`\n'
        '    - **워크스페이스 정책**: 원본 .md 수정 0 — hooks 로만 시각 변환\n'
        '    - **자산 자족성 정상화**: Phase E7 완료 (잔여 외부 갭 4)\n'
    )

    # 페이지 끝에 추가 (이미 footer 가 있으면 중복 회피)
    if "📌 이 페이지 정보" in markdown:
        return markdown

    return markdown.rstrip() + footer_block + "\n"


def on_page_markdown(markdown: str, page, config, files):  # noqa: ARG001
    if page.file.src_path in EXCLUDE_PAGES:
        return markdown

    markdown = inject_top_reading_time(markdown, page)
    markdown = inject_meta_footer(markdown, page, config)
    return markdown
