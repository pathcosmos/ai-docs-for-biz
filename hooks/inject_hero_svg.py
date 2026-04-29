"""inject_hero_svg.py — 페이지 slug 기반 hero SVG 자동 주입.

각 페이지 (예: `docs/pkg/pkg1-steel-enterprise.md`) 가 빌드될 때, 동일 slug 의 SVG
(`docs/assets/svg/pkg/pkg1-steel-enterprise.svg`) 가 존재하면 H1 직후에 figure 임베딩.

규칙:
- slug `track/track1-index.md` → `assets/svg/track/track1-index.svg` 검색
- SVG 가 있으면 `<figure markdown="span">![](상대경로)<figcaption>...</figcaption></figure>` 삽입
- SVG 가 없으면 변경 없음
- 이미 첫 H1 직후에 `<figure>` 가 있으면 중복 회피
- 홈 페이지 (index.md) 는 수동 임베딩 우선 (excluded)

기준 디렉토리:
- docs/track/, docs/pkg/, docs/guide/, docs/scenario/, docs/module/, docs/other/, docs/meta/
- 매칭 SVG 위치: docs/assets/svg/{group}/{slug}.svg
"""

from __future__ import annotations

import re
from pathlib import Path

# 자동 주입 제외 페이지 (수동 임베딩 또는 hero 부적합)
EXCLUDE_SLUGS = {
    "index.md",      # 수동 hero 이미 있음
    "graph.md",      # D3 그래프 컨테이너
    "filter.md",     # 태그 필터 페이지
}

# 자동 figcaption 패턴 (자산 군별 안내 문구)
GROUP_CAPTIONS = {
    "track": "Track 본문 시각 — 클릭하여 확대·SVG 다운로드 (벡터, 해상도 무제한)",
    "pkg": "통합 파일럿 인포그래픽 — 클릭하여 확대·SVG 다운로드",
    "guide": "운영 가이드 인포그래픽 — 8 장 + 4 분기 + 강도 3 단계 시각",
    "scenario": "시나리오 인포그래픽 — 도메인·시나리오 ID·5.2 카드 매핑",
    "module": "Cross-cutting 모듈 인포그래픽 — 결합 영역 시각",
    "other": "기타 자산 인포그래픽 — 핵심 도식",
    "meta": "메타 자산 인포그래픽",
}


def derive_group(src_path: str) -> str | None:
    parts = src_path.split("/")
    if len(parts) >= 2 and parts[0] in GROUP_CAPTIONS:
        return parts[0]
    return None


def find_svg_for_page(docs_dir: Path, src_path: str) -> Path | None:
    """페이지 src_path 에 대응하는 SVG 파일 경로 반환."""
    # src_path: e.g., 'pkg/pkg1-steel-enterprise.md'
    svg_rel = src_path.replace(".md", ".svg")
    svg_path = docs_dir / "assets" / "svg" / svg_rel
    return svg_path if svg_path.exists() else None


def has_figure_at_top(markdown: str) -> bool:
    """페이지 H1 직후에 이미 <figure> 가 있는지 확인."""
    fm_match = re.match(r"^---\n.*?\n---\n", markdown, re.DOTALL)
    body_start = markdown[fm_match.end():] if fm_match else markdown

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
        # <figure 또는 ![ 로 시작하면 이미 이미지 있음
        return stripped.startswith("<figure") or stripped.startswith("![") or "<figure" in stripped[:50]
    return False


def relative_svg_path(src_path: str) -> str:
    """페이지 디렉토리에서 SVG 까지의 상대 경로.
    src_path = 'pkg/pkg1-steel-enterprise.md' → '../assets/svg/pkg/pkg1-steel-enterprise.svg'
    """
    parts = src_path.split("/")
    depth = len(parts) - 1  # 디렉토리 깊이
    prefix = "../" * depth if depth > 0 else ""
    svg_rel = src_path.replace(".md", ".svg")
    return prefix + "assets/svg/" + svg_rel


def inject_hero(markdown: str, page, config) -> str:
    src_path = page.file.src_path
    if src_path in EXCLUDE_SLUGS:
        return markdown

    group = derive_group(src_path)
    if not group:
        return markdown

    config_dir = Path(config["config_file_path"]).parent
    docs_dir = config_dir / "docs"
    svg_file = find_svg_for_page(docs_dir, src_path)
    if not svg_file:
        return markdown

    if has_figure_at_top(markdown):
        return markdown  # 이미 figure 있음

    rel_path = relative_svg_path(src_path)
    caption = GROUP_CAPTIONS.get(group, "인포그래픽 — 클릭하여 확대·다운로드")
    page_title_match = re.search(r"^#\s+(.+?)\s*$", markdown, re.MULTILINE)
    page_title = page_title_match.group(1).strip() if page_title_match else "인포그래픽"

    figure_block = (
        f'\n<figure markdown="span">\n'
        f'  ![{page_title}]({rel_path})\n'
        f'  <figcaption>{caption}</figcaption>\n'
        f'</figure>\n'
    )

    # H1 직후에 figure_block 삽입
    pattern = re.compile(r"(^#\s+.+?\n)", re.MULTILINE)
    new_markdown, count = pattern.subn(r"\1" + figure_block, markdown, count=1)
    return new_markdown if count > 0 else markdown


def on_page_markdown(markdown: str, page, config, files):  # noqa: ARG001
    return inject_hero(markdown, page, config)
