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
    """MkDocs 훅 — page.meta 직접 set (markdown 변경 0).

    [E12-Fix-2] markdown 에 frontmatter prepend 하던 기존 설계는 mkdocs 의 frontmatter
    파싱이 source 로드 시점에만 작동하므로 hook 이 추가한 frontmatter 는 raw 텍스트로
    렌더링되는 결함. → page.meta 에 직접 set 하여 markdown 본문 변경 0.
    """
    # 이미 frontmatter 가 있는 페이지는 skip
    if page.meta and (page.meta.get("title") or page.meta.get("description")):
        return markdown

    title = extract_title(markdown) or page.file.src_path
    description = first_paragraph(markdown)
    slug_path = page.file.src_path
    tags = derive_tags(slug_path)

    # page.meta 직접 set (markdown 변경 안 함 — raw 노출 0 보장)
    if page.meta is None:
        page.meta = {}
    if not page.meta.get("title"):
        page.meta["title"] = title
    if description and not page.meta.get("description"):
        page.meta["description"] = description
    if tags and not page.meta.get("tags"):
        page.meta["tags"] = tags
    # page.title 도 set (mkdocs 가 navigation·OG 에 사용)
    if hasattr(page, "title") and not page.title:
        page.title = title

    return markdown  # markdown 본문 변경 없음
