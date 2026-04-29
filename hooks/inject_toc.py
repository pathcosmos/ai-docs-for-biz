"""inject_toc.py — 본문 길이가 긴 페이지에 자동 TOC + 진입 navigation 박스 주입.

긴 페이지 (300 줄 이상) 의 경우 페이지 상단에 "이 페이지 둘러보기" admonition
박스를 자동으로 주입하여 사용자가 페이지 구조를 빠르게 파악하도록 한다.

이미 Front matter 가 있고 첫 H1 직후 콘텐츠가 시작되는 페이지를 대상으로 한다.
홈 페이지 (index.md) + 그래프·필터 등 특수 페이지는 제외.
"""

from __future__ import annotations

import re

# 자동 TOC 박스 제외 페이지 (이미 카드 그리드·plain 구조)
EXCLUDE_SLUGS = {"index.md", "graph.md", "filter.md"}

# 자동 TOC 박스 주입 임계 (줄 수)
LINE_THRESHOLD = 300


def count_h2(markdown: str) -> int:
    """H2 헤딩 수 — TOC 박스의 의미 있는 항목 수."""
    return len(re.findall(r"^##\s+", markdown, re.MULTILINE))


def has_admonition_at_top(markdown: str) -> bool:
    """페이지 상단에 이미 admonition (!!!) 또는 blockquote 가 있는지."""
    body_start = markdown
    # Front matter 제거
    fm_match = re.match(r"^---\n.*?\n---\n", markdown, re.DOTALL)
    if fm_match:
        body_start = markdown[fm_match.end():]

    # H1 다음 첫 비-빈줄 찾기
    after_h1 = False
    for line in body_start.splitlines():
        if line.startswith("# "):
            after_h1 = True
            continue
        if not after_h1:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        # 이미 admonition 또는 blockquote 가 있으면 스킵
        if stripped.startswith("!!!") or stripped.startswith("???") or stripped.startswith(">"):
            return True
        return False
    return False


def inject_navigation_box(markdown: str, page) -> str:
    """긴 페이지 상단에 'TOC 빠른 진입' admonition 주입."""
    line_count = markdown.count("\n")
    if line_count < LINE_THRESHOLD:
        return markdown

    if count_h2(markdown) < 4:
        # H2 가 적으면 TOC 가치 낮음
        return markdown

    if has_admonition_at_top(markdown):
        # 이미 안내 박스가 있으면 중복 회피
        return markdown

    # H1 직후에 navigation 박스 삽입
    nav_box = (
        '\n!!! tip "이 페이지 둘러보기"\n'
        f'    본 페이지는 약 {line_count:,} 줄 / H2 섹션 {count_h2(markdown)} 개 입니다.\n'
        '    우측 목차 (TOC) 를 활용하여 원하는 섹션으로 빠르게 이동할 수 있습니다.\n'
    )

    # H1 (`# 제목`) 다음에 빈 줄 + nav_box 삽입
    pattern = re.compile(r"(^#\s+.+?\n)", re.MULTILINE)
    new_markdown, count = pattern.subn(r"\1" + nav_box, markdown, count=1)
    return new_markdown if count > 0 else markdown


def on_page_markdown(markdown: str, page, config, files):  # noqa: ARG001
    if page.file.src_path in EXCLUDE_SLUGS:
        return markdown
    return inject_navigation_box(markdown, page)
