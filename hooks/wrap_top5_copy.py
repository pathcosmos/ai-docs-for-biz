"""wrap_top5_copy.py — Track 1·2·3 본문 공통 Top5 페이지의 각 BLK 블록을 자동으로
'📋 paste-ready copy admonition' 으로 wrap.

대상 페이지:
- track/track1-top5.md (BLK-T1-3.1·3.2·4.4·4.5·4.6 — 5 블록)
- track/track2-top5.md (BLK-T2-3.2·4.2·4.4·5.5·6.1 — 5 블록)
- track/track3-top5.md (BLK-T3-3.1·3.2·4.2·5.2·5.5 — 5 블록)

각 블록의 H2 (예: `## 3.1 ... (BLK-T1-3.1)`) 부터 다음 H2 직전까지를
`<div markdown="1" class="admonition copy">...</div>` 으로 wrap.

CSS (`extra.css` `.admonition.copy`) 가 앰버 좌측 보더 + 📋 아이콘 적용.

또한 페이지 상단에 "📋 paste-ready 블록 일람" 안내 admonition 자동 주입.
"""

from __future__ import annotations

import re

TARGET_PAGES = {
    "track/track1-top5.md": "Track 1 — 제조 AI",
    "track/track2-top5.md": "Track 2 — MLOps",
    "track/track3-top5.md": "Track 3 — LLM·RAG",
}

# 사업계획서 paste 위치 매핑 (§ 번호 → 사업계획서 섹션 명)
SECTION_NAMES = {
    "3.1": "사업 배경",
    "3.2": "사업 배경 — 데이터·운영 한계",
    "4.2": "기술 설계 — 핵심 모듈",
    "4.4": "기술 설계 — 아키텍처",
    "4.5": "기술 설계 — 모델 선정",
    "4.6": "기술 설계 — 전체 파이프라인",
    "5.2": "운영 — 데이터·청킹 전략",
    "5.5": "운영 — 모니터링·환각 방지",
    "6.1": "운영 — 개선 포인트 선정",
}

# H2 패턴 2 종 (Track 1·3 형식 + Track 2 형식 통합):
#   Format A (Track 1·3): `## 3.1 제목 (블록명: BLK-T1-3.1)` 또는 `## 3.1 제목 (BLK-T1-3.1)`
#   Format B (Track 2):   `## BLK-T2-3.2 — 제목` 또는 `## BLK-T2-3.2 - 제목`
H2_BLOCK_RE = re.compile(
    r"^## (?:"
    r"(?P<sectionA>\d+\.\d+)\s+(?P<titleA>.+?)\s*\((?:블록명:\s*)?(?P<idA>BLK-T\d-\d+\.\d+)\)"
    r"|"
    r"(?P<idB>BLK-T(?P<trackB>\d)-(?P<sectionB>\d+\.\d+))\s*[—\-–]\s*(?P<titleB>.+?)"
    r")\s*$",
    re.MULTILINE,
)


def parse_block_match(m: re.Match[str]) -> tuple[str, str, str]:
    """매치에서 (section, title, block_id) 추출 — 두 형식 통합."""
    if m.group("sectionA"):
        return m.group("sectionA"), m.group("titleA").strip(), m.group("idA")
    return m.group("sectionB"), m.group("titleB").strip(), m.group("idB")


def wrap_blocks(markdown: str, track_name: str) -> str:
    """각 BLK 블록의 H2 + 본문 + 삽화 까지를 div admonition.copy 으로 wrap."""
    matches = list(H2_BLOCK_RE.finditer(markdown))
    if not matches:
        return markdown

    # 각 블록의 시작 위치 + 끝 위치 계산
    # 블록 끝: 다음 H2 직전 또는 다음 `---` 직전
    blocks = []
    for i, m in enumerate(matches):
        section, title, block_id = parse_block_match(m)

        block_start = m.start()
        # 다음 블록 시작 또는 파일 끝
        block_end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)

        # 끝 직전에 `---\n` 이 있으면 그 직전까지
        sub_text = markdown[block_start:block_end]
        sep_match = re.search(r"\n---\n", sub_text)
        if sep_match:
            block_end = block_start + sep_match.start()
            block_text = markdown[block_start:block_end]
        else:
            block_text = sub_text

        blocks.append({
            "section": section,
            "title": title,
            "id": block_id,
            "start": block_start,
            "end": block_end,
            "text": block_text,
        })

    # 역순 처리 (앞쪽 먼저 처리하면 인덱스 변화)
    new_markdown = markdown
    for block in reversed(blocks):
        section = block["section"]
        title = block["title"]
        block_id = block["id"]
        original = block["text"]

        # 본문에서 H2 자체는 제거하고 admonition title 로 치환
        body_after_h2 = re.sub(
            H2_BLOCK_RE, "", original, count=1
        ).lstrip()

        section_label = SECTION_NAMES.get(section, "")
        admon_title = f"📋 {block_id} — 사업계획서 §{section} {section_label} paste 가능"

        # admonition (collapsible details, 기본 펼침)
        wrapped = (
            f'<div markdown="1" class="admonition copy" data-block-id="{block_id}">\n'
            f'<p class="admonition-title">{admon_title}</p>\n'
            f'\n'
            f'<details markdown="1" open>\n'
            f'<summary>{title}</summary>\n'
            f'\n'
            f'{body_after_h2.rstrip()}\n'
            f'</details>\n'
            f'</div>\n'
        )

        new_markdown = (
            new_markdown[:block["start"]]
            + wrapped
            + new_markdown[block["end"]:]
        )

    # 페이지 상단에 안내 admonition 주입 (H1 직후)
    intro_admon = (
        f'\n!!! tip "📋 본 페이지 5 블록은 paste-ready 본문입니다"\n'
        f'    각 블록은 한국어 사업계획서 어투 완성 문장으로, 아래 앰버 박스 안의 본문을 그대로 복사 + `[고객사]·[공정]·[수치]` 등 플레이스홀더만 귀사 정보로 치환하면 사업계획서 §3·4·5·6 에 즉시 paste 가능합니다.\n\n'
        f'    🔍 모든 블록을 한눈에 보려면 [📋 공통 블록 모음](../blocks.md) 페이지 참조 (Track 1·2·3 의 15 블록 통합).\n\n'
    )

    h1_pattern = re.compile(r"(^#\s+.+?\n)", re.MULTILINE)
    if h1_pattern.search(new_markdown):
        new_markdown = h1_pattern.sub(r"\1" + intro_admon, new_markdown, count=1)

    return new_markdown


def on_page_markdown(markdown: str, page, config, files):  # noqa: ARG001
    src_path = page.file.src_path
    if src_path not in TARGET_PAGES:
        return markdown
    track_name = TARGET_PAGES[src_path]
    return wrap_blocks(markdown, track_name)
