"""dim_workspace_meta.py — 워크스페이스 메타데이터 시각 약화 (사용자 피드백 #1).

본 사이트의 외부 사용자 (사업계획서 작성용 참고·복사) 에게 의미 0 인 워크스페이스
내부 메타데이터 (Phase·엔트리·방법론·에이전트 ID) 를 정규식으로 인식하여
`<span class="meta-marker">` 으로 wrap. CSS (`extra.css` `.meta-marker`) 가
gray + smaller font + opacity 적용으로 시각 분리.

대상 패턴 (외부 사용자에게 의미 없는 내부 ID 만):
- Phase 표기 — `Phase E1`·`Phase E10-1`·`Phase A`·`Phase G` 등
- 엔트리 표기 — `엔트리 #1` ~ `엔트리 #99`
- 방법론 표기 — `방법론 4.1` ~ `방법론 4.99`
- 에이전트 표기 — `G15·G16 에이전트`·`G31 에이전트`

본문 일반 텍스트 (예: 4.1 GHz·G15 모델 등) 와 충돌 회피를 위해 정밀 정규식 사용.
코드 블록 (```·`) 안의 패턴은 보존.
"""

from __future__ import annotations

import re

# 메타데이터 정규식 (정밀 매칭 — 본문 일반 텍스트와 충돌 회피)
META_PATTERNS = [
    # Phase E1·E10·E10-1 등 (E + 숫자 + 선택적 -숫자)
    re.compile(r"(?<!\w)(Phase\s+E\d+(?:-\d+)?)(?!\w)"),
    # Phase A·Phase B·Phase G 등 (영문자 1 자)
    re.compile(r"(?<!\w)(Phase\s+[A-G])(?!\w)"),
    # 엔트리 #N (숫자 1~3 자리)
    re.compile(r"(엔트리\s*#\s*\d{1,3})"),
    # 방법론 4.N (4. 으로 시작 — 본 워크스페이스 표준)
    re.compile(r"(?<!\w)(방법론\s+4\.\d{1,3})(?!\w)"),
    # G\d+ 에이전트 (단일 또는 복수)
    re.compile(r"(?<!\w)(G\d{1,3}(?:[·,\s]+G\d{1,3})*\s*에이전트)"),
]

# 코드 블록 (fenced)
CODE_FENCE_RE = re.compile(
    r"(^```[\s\S]*?^```$|^~~~[\s\S]*?^~~~$)",
    re.MULTILINE,
)
# 인라인 코드
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
# 이미 wrap 된 영역 (재처리 방지)
ALREADY_WRAPPED_RE = re.compile(
    r'<span class="meta-marker"[^>]*>[^<]*</span>'
)


def wrap_meta(text: str) -> str:
    """메타 패턴을 <span class="meta-marker"> 으로 wrap."""
    for pattern in META_PATTERNS:
        def replacer(m: re.Match[str]) -> str:
            content = m.group(1)
            return f'<span class="meta-marker">{content}</span>'
        text = pattern.sub(replacer, text)
    return text


def apply_safely(text: str) -> str:
    """본문 텍스트에서만 메타 wrap (코드 블록·인라인 코드 외부에만 적용)."""
    parts: list[str] = []
    last_end = 0

    for m in CODE_FENCE_RE.finditer(text):
        before = text[last_end : m.start()]
        parts.append(_apply_inline_safe(before))
        parts.append(m.group(0))  # 코드 블록 보존
        last_end = m.end()

    parts.append(_apply_inline_safe(text[last_end:]))
    return "".join(parts)


def _apply_inline_safe(text: str) -> str:
    """인라인 코드 외부에만 메타 wrap."""
    parts: list[str] = []
    last_end = 0
    for m in INLINE_CODE_RE.finditer(text):
        before = text[last_end : m.start()]
        parts.append(wrap_meta(before))
        parts.append(m.group(0))  # 인라인 코드 보존
        last_end = m.end()
    parts.append(wrap_meta(text[last_end:]))
    return "".join(parts)


def on_page_markdown(markdown: str, page, config, files):  # noqa: ARG001
    return apply_safely(markdown)
