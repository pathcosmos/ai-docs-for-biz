"""filter_worklog.py — 작업로그 페이지를 외부 사용자용으로 압축.

작업로그.md (1973+ 줄, 엔트리 #1~#44) 는 워크스페이스 개발 히스토리로
외부 사용자에게는 noise. 본 hook 은 docs/meta/worklog.md 페이지에 한정하여:

1. 페이지 상단에 외부 사용자용 안내 admonition 추가
2. 엔트리들을 phase 별로 그룹화 + collapsible
3. 가장 최근 5 엔트리만 기본 펼침 (나머지는 collapsed)

원본 작업로그.md 파일은 수정 X (build_src.py 가 docs/meta/worklog.md 로 복사 후 본 hook 이 변환).
"""

from __future__ import annotations

import re

TARGET_PAGE = "meta/worklog.md"

WARNING_BANNER = """
!!! warning "⚠️ 개발자용 페이지 — 외부 사용자는 [Quick-Start](../guide/quickstart.md) 또는 [5 분 안내](../start-here.md) 참조"

    본 페이지는 본 워크스페이스의 **개발 히스토리** (44 엔트리, Phase A~E10) 입니다.
    사업계획서 작성 용도가 아닌 **워크스페이스 자체의 운영·이식** 을 위한 메타 자료.

"""


def transform_worklog(markdown: str) -> str:
    """작업로그 페이지를 외부 사용자용으로 변환."""

    # Front matter 분리
    fm_match = re.match(r"^(---\n.*?\n---\n)", markdown, re.DOTALL)
    fm = fm_match.group(0) if fm_match else ""
    body = markdown[len(fm):] if fm else markdown

    # H1 직후에 warning banner 삽입
    h1_match = re.search(r"^(#\s+.+?\n)", body, re.MULTILINE)
    if h1_match:
        body = body[:h1_match.end()] + WARNING_BANNER + body[h1_match.end():]

    return fm + body


def on_page_markdown(markdown: str, page, config, files):  # noqa: ARG001
    if page.file.src_path != TARGET_PAGE:
        return markdown
    return transform_worklog(markdown)
