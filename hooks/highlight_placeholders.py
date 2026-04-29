"""highlight_placeholders.py — `[고객사]`·`[공정]`·`[수치]` 등 플레이스홀더 시각 강조.

MkDocs 훅 — 본문 마크다운에서 표준 플레이스홀더 패턴을 `<span data-placeholder>` 로 감싸서
CSS (`docs/stylesheets/extra.css`) 의 점선 박스 + 앰버 배경이 적용되도록 한다.

대상 패턴 (CLAUDE.md §플레이스홀더 관례 준수):
- [고객사] · [공정] · [수치] · [기간] · [%] · [LLM모델] · [벡터스토어] · [임계]

코드 블록 (```·`...`) 안의 플레이스홀더는 변환 제외 (코드 의미 보존).
"""

from __future__ import annotations

import re

# 표준 플레이스홀더 화이트리스트 (CLAUDE.md 규약)
PLACEHOLDERS = [
    "고객사", "공정", "수치", "기간", "%", "LLM모델", "벡터스토어", "임계",
    "도메인", "기관", "예산", "회차", "ID", "버전", "사이트",
]

PLACEHOLDER_RE = re.compile(
    r"\[(" + "|".join(re.escape(p) for p in PLACEHOLDERS) + r")\]"
)

# 코드 블록 (fenced code) — ``` 또는 ~~~ 로 둘러싸인 영역
CODE_FENCE_RE = re.compile(
    r"(^```[\s\S]*?^```$|^~~~[\s\S]*?^~~~$)",
    re.MULTILINE,
)
# 인라인 코드 — `...`
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")


def wrap_placeholder(match: re.Match[str]) -> str:
    name = match.group(1)
    return f'<span class="placeholder-tag" data-placeholder="{name}">[{name}]</span>'


def highlight(text: str) -> str:
    """본문 텍스트에서 플레이스홀더만 감쌈. 코드 블록 외부에만 적용."""
    parts: list[str] = []
    last_end = 0

    # 코드 펜스 영역 식별 — 그 외 영역만 변환 대상
    for m in CODE_FENCE_RE.finditer(text):
        # 코드 펜스 이전 (변환 대상)
        before = text[last_end : m.start()]
        parts.append(_apply_inline_safe(before))
        # 코드 펜스 자체 (변환 제외)
        parts.append(m.group(0))
        last_end = m.end()

    # 마지막 코드 펜스 이후 (변환 대상)
    parts.append(_apply_inline_safe(text[last_end:]))
    return "".join(parts)


def _apply_inline_safe(text: str) -> str:
    """인라인 코드 외부에만 placeholder 변환 적용."""
    parts: list[str] = []
    last_end = 0
    for m in INLINE_CODE_RE.finditer(text):
        before = text[last_end : m.start()]
        parts.append(PLACEHOLDER_RE.sub(wrap_placeholder, before))
        parts.append(m.group(0))  # 인라인 코드 보존
        last_end = m.end()
    parts.append(PLACEHOLDER_RE.sub(wrap_placeholder, text[last_end:]))
    return "".join(parts)


def on_page_markdown(markdown: str, page, config, files):  # noqa: ARG001
    return highlight(markdown)
