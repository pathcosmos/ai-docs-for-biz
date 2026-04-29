"""inject_frontmatter.py — H1 제목 추출 + Front matter 자동 삽입 (MkDocs 훅).

원본 .md 는 Front matter 가 없으므로 빌드 타임에 H1 (`# 제목`) 을 추출하여
title·description·tags 를 자동 부여.

태그 분류 (4 축):
- 자산 유형: track / scenario / pkg / guide / module / other / meta
- 트랙: track1 / track2 / track3 (해당 시)
- 패키지: pkg1 ~ pkg6 (해당 시)
- 공정: steel / rubber / precision / util / safety (해당 시)
"""

from __future__ import annotations

import re

# 슬러그 경로 패턴 → 자산 유형 매핑
TYPE_TAGS = [
    ("track/", "track"),
    ("pkg/", "package"),
    ("guide/", "guide"),
    ("scenario/", "scenario"),
    ("module/", "module"),
    ("other/", "other"),
    ("meta/", "meta"),
]

# 슬러그 키워드 → 추가 태그 매핑
KEYWORD_TAGS = {
    "track1": ["track1", "manufacturing-ai"],
    "track2": ["track2", "mlops"],
    "track3": ["track3", "llm-rag"],
    "pkg1": ["pkg1", "steel", "enterprise", "multi-year-rd"],
    "pkg2": ["pkg2", "steel", "midsize"],
    "pkg3": ["pkg3", "steel", "rag"],
    "pkg4": ["pkg4", "rubber"],
    "pkg5": ["pkg5", "precision", "saas"],
    "pkg6": ["pkg6", "util", "esg"],
    "cbam": ["cbam", "esg"],
    "safety": ["safety"],
    "kpi": ["kpi"],
    "finance": ["finance"],
    "rag": ["rag"],
}


def extract_title(markdown: str) -> str | None:
    for line in markdown.splitlines():
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip().strip("`")
    return None


def first_paragraph(markdown: str, limit: int = 200) -> str:
    """본문 첫 단락 (H1 다음 첫 단락) 을 description 후보로 추출."""
    after_h1 = False
    buf: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("# "):
            after_h1 = True
            continue
        if not after_h1:
            continue
        stripped = line.strip()
        # blockquote / 빈 줄 / 섹션 헤더는 건너뛰기
        if not stripped or stripped.startswith(("#", ">", "|", "---", "```")):
            if buf:
                break
            continue
        buf.append(stripped)
        if sum(len(b) for b in buf) >= limit:
            break
    text = " ".join(buf)
    text = re.sub(r"\s+", " ", text)
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return text


def derive_tags(slug_path: str) -> list[str]:
    tags: list[str] = []
    for prefix, tag in TYPE_TAGS:
        if slug_path.startswith(prefix):
            tags.append(tag)
            break

    slug_lower = slug_path.lower()
    for kw, kw_tags in KEYWORD_TAGS.items():
        if kw in slug_lower:
            for t in kw_tags:
                if t not in tags:
                    tags.append(t)
    return tags


def on_page_markdown(markdown: str, page, config, files):  # noqa: ARG001
    """MkDocs 훅 — 각 페이지의 markdown 을 변환."""
    # 이미 Front matter 가 있으면 스킵
    if markdown.lstrip().startswith("---"):
        return markdown

    title = extract_title(markdown) or page.file.src_path
    description = first_paragraph(markdown)
    slug_path = page.file.src_path
    tags = derive_tags(slug_path)

    fm_lines = ["---"]
    # YAML 멀티라인 안전을 위해 따옴표 escape
    safe_title = title.replace('"', '\\"')
    fm_lines.append(f'title: "{safe_title}"')
    if description:
        safe_desc = description.replace('"', '\\"')
        fm_lines.append(f'description: "{safe_desc}"')
    if tags:
        fm_lines.append("tags:")
        for t in tags:
            fm_lines.append(f"  - {t}")
    fm_lines.append("---")
    fm_lines.append("")

    return "\n".join(fm_lines) + markdown
