"""wrap_meta_blockquote.py — 페이지 H1 직후 메타 인용을 <details> collapsible 로 wrap.

본 워크스페이스의 .md 파일은 H1 직후에 메타 정보 blockquote 가 관습적으로 위치한다.
예시: `> Phase E6 Cycle 2 통합 파일럿 산출물. **통합 파일럿 군 6 번째 자산**...`

이러한 메타 blockquote 는 외부 사용자에게는 noise — 페이지 상단을 차지하여 본문
viewport 가 가려진다. 본 hook 은 H1 직후의 첫 blockquote 만 자동으로
`<details><summary>ℹ️ 페이지 정보</summary>...</details>` 로 wrap.

규칙:
- H1 직후 첫 blockquote 만 대상 (본문 중간 인용은 보존)
- 출처 인용 (`> [출처: ...]`) 패턴이 1 줄짜리면 보존 (메타 인용 X)
- 이미 details 로 wrap 되어 있으면 중복 회피
- 홈·필터·그래프 페이지 제외 (본문 적은 페이지)
"""

from __future__ import annotations

import re

EXCLUDE_PAGES = {"index.md", "graph.md", "filter.md", "start-here.md", "by-package.md"}


def is_meta_blockquote(blockquote_text: str) -> bool:
    """blockquote 가 메타 정보인지 판단 — 출처 인용 단일 줄이 아닐 때 메타로 본다."""
    stripped = blockquote_text.strip()
    # 단일 출처 인용 (1 줄, [출처: ...] 패턴) 은 메타 아님
    lines = [ln for ln in stripped.splitlines() if ln.strip()]
    if len(lines) <= 1 and "[출처:" in stripped:
        return False
    # 메타 키워드 포함 여부
    meta_keywords = [
        "Phase", "엔트리", "방법론", "산출물", "통합 파일럿",
        "선행 자산", "플레이스홀더", "신규 자산", "보강", "Cycle",
        "Stage", "G\\d+", "에이전트",
    ]
    return any(kw in stripped for kw in meta_keywords if not kw.startswith("G"))


def wrap_h1_meta_blockquote(markdown: str) -> str:
    """H1 직후 첫 blockquote 가 메타이면 <details> 로 wrap."""

    # Front matter 분리
    fm_match = re.match(r"^(---\n.*?\n---\n)", markdown, re.DOTALL)
    fm = fm_match.group(0) if fm_match else ""
    body = markdown[len(fm):] if fm else markdown

    # H1 패턴
    h1_match = re.search(r"^(#\s+.+?)\n", body, re.MULTILINE)
    if not h1_match:
        return markdown

    h1_end = h1_match.end()
    after_h1 = body[h1_end:]

    # H1 다음 첫 blockquote 시작 위치 찾기 (빈 줄 + > 패턴)
    # 빈 줄 이후 > 으로 시작하는 연속 라인을 blockquote 로 인식
    bq_start_match = re.search(r"\n*(>(?:[^\n]*\n)+)", after_h1)
    if not bq_start_match:
        return markdown

    # blockquote 의 시작/끝 (연속된 > 라인들)
    bq_start_offset = bq_start_match.start(1)
    bq_lines: list[str] = []
    cursor = bq_start_offset
    remaining = after_h1[cursor:]

    bq_pattern = re.compile(r"(>(?:[^\n]*)\n?)+")
    bq_match = bq_pattern.match(remaining)
    if not bq_match:
        return markdown

    bq_text_full = bq_match.group(0)

    # 메타 판단
    bq_inner = re.sub(r"^>\s?", "", bq_text_full, flags=re.MULTILINE)
    if not is_meta_blockquote(bq_inner):
        return markdown

    # 이미 details 로 wrap 되어 있는지 확인 (직전에 <details 가 있는지)
    if "<details" in body[:h1_end + bq_start_offset + bq_match.end()]:
        return markdown

    # wrap 적용
    bq_inner_clean = bq_inner.strip()
    details_block = (
        '\n\n??? info "ℹ️ 페이지 정보 (워크스페이스 메타)"\n'
        + "\n".join("    " + line for line in bq_inner_clean.splitlines())
        + "\n\n"
    )

    new_after_h1 = (
        after_h1[:bq_start_offset]
        + details_block
        + after_h1[bq_start_offset + bq_match.end():]
    )

    return fm + body[:h1_end] + new_after_h1


def on_page_markdown(markdown: str, page, config, files):  # noqa: ARG001
    if page.file.src_path in EXCLUDE_PAGES:
        return markdown
    return wrap_h1_meta_blockquote(markdown)
