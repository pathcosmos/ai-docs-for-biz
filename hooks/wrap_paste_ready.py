"""wrap_paste_ready.py — Phase E13-2 (Sprint 2)

paste-ready 블록 시각 demarcation 자동 wrap (admonition.copy 박스 = 앰버 좌측 보더 + 📋).

대상:
1. 시나리오 상세 5 파일 (`scenario/detail-*.md`)
   - SCN-XXX-NN 마다 안의 ### 4 sub (적용 맥락·AS-IS·AI 해결·기대효과) wrap
2. 6 통합 파일럿 (`pkg/pkg*.md`)
   - §3.X (AS-IS) 모든 ### 항목 wrap
   - §4.X (TO-BE) 모든 ### 항목 wrap
3. 운영 가이드 11 (`guide/*.md`)
   - 본문 ### 섹션 중 "실 사용 예시"·"표준 양식"·"본문 인용" 패턴 wrap

wrap 대상 H3 (`### 제목`) 의 본문 (~ 다음 H2/H3 직전까지) 을 admonition.copy 로 감쌈.
"""

from __future__ import annotations

import re
from pathlib import Path

# 대상 패턴 매핑 — slug → 처리 모드
TARGET_PATTERNS = {
    # 시나리오 상세 — SCN-XXX-NN 안 sub-### wrap (4 종)
    "scenario/detail-top5.md": "scenario_sub",
    "scenario/detail-rub.md": "scenario_sub",
    "scenario/detail-phase2.md": "scenario_sub",
    "scenario/detail-utl-saf.md": "scenario_sub",
    "scenario/detail-special-pipe.md": "scenario_sub",
    # 패키지 1~6 — §3·§4 ### wrap
    "pkg/pkg1-steel-enterprise.md": "pkg_section",
    "pkg/pkg2-cold-rolled.md": "pkg_section",
    "pkg/pkg3-special-pipe.md": "pkg_section",
    "pkg/pkg4-rubber.md": "pkg_section",
    "pkg/pkg5-precision.md": "pkg_section",
    "pkg/pkg6-util-esg.md": "pkg_section",
}

# 시나리오 sub-섹션 — wrap 대상 (적용 맥락·AS-IS·AI 해결·기대효과·삽화)
SCENARIO_SUB_HEADERS = (
    "적용 맥락",
    "AS-IS",
    "AI 해결",
    "기대효과",
)

# 패키지 §3·§4 wrap 대상 (§3 = AS-IS / §4 = TO-BE)
PKG_SECTION_PREFIX = ("3.", "4.")


def wrap_scenario_subs(markdown: str) -> str:
    """시나리오 상세 — SCN-XXX-NN 안의 ### sub-section 4 종 wrap.

    구조:
      ## SCN-RUB-01 — 제목
      ### 적용 맥락
      본문...
      ### AS-IS — 현재의 공백
      본문...
      ### AI 해결 — 도입 후 운영 모습
      본문...
      ### 기대효과
      본문...
      ### 삽화 (Mermaid)
      이미지

    각 ### sub-section (적용 맥락·AS-IS·AI 해결·기대효과) 다음 본문을
    admonition.copy 로 wrap. 삽화는 wrap 안 함.
    """
    lines = markdown.split("\n")
    result: list[str] = []
    i = 0
    current_scn = None
    wrap_count = 0

    while i < len(lines):
        line = lines[i]

        # SCN 시작 — 현재 SCN 기록
        m_scn = re.match(r"^## (SCN-[A-Z]+-\d+)\s*[—\-–]?\s*(.*)$", line)
        if m_scn:
            current_scn = m_scn.group(1)
            result.append(line)
            i += 1
            continue

        # ### sub-section
        m_sub = re.match(r"^### (.+?)\s*$", line)
        if m_sub and current_scn:
            sub_title = m_sub.group(1).strip()
            # wrap 대상 확인
            should_wrap = any(sub_title.startswith(h) for h in SCENARIO_SUB_HEADERS)

            if should_wrap:
                # 본문 끝 찾기 (다음 ### 또는 ## 직전)
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if next_line.startswith("### ") or next_line.startswith("## "):
                        break
                    j += 1

                # 본문 = lines[i+1:j]
                body = "\n".join(lines[i + 1:j]).strip()

                # admonition.copy wrap
                admon_title = f"📋 {current_scn} — {sub_title} (paste 가능)"
                wrapped = (
                    f'<div markdown="1" class="admonition copy" data-scn="{current_scn}">\n'
                    f'<p class="admonition-title">{admon_title}</p>\n\n'
                    f'{body}\n'
                    f'</div>\n'
                )
                result.append(wrapped)
                wrap_count += 1
                i = j
                continue

        result.append(line)
        i += 1

    return "\n".join(result)


def wrap_pkg_sections(markdown: str) -> str:
    """패키지 1~6 — §3.X·§4.X 의 ### 항목 wrap.

    구조 예 (사업계획서_패키지2):
      ## 3. 사업의 필요성 (AS-IS — 현재의 공백)
      ### 3.1 공정 운영의 인적 의존성·암묵지 리스크
      본문...
      ### 3.2 데이터 단절·비정형 관리 한계
      본문...

    §3.X·§4.X 시작 ### 항목 본문 (~ 다음 ### 또는 ## 직전까지) admonition.copy wrap.
    """
    lines = markdown.split("\n")
    result: list[str] = []
    i = 0
    current_section = None  # "3" 또는 "4"
    wrap_count = 0

    while i < len(lines):
        line = lines[i]

        # ## 3. 또는 ## 4. 감지
        m_h2 = re.match(r"^## (\d+)\.\s+(.*)$", line)
        if m_h2:
            section_num = m_h2.group(1)
            current_section = section_num if section_num in ("3", "4") else None
            result.append(line)
            i += 1
            continue

        # ### N.M 항목
        m_h3 = re.match(r"^### (\d+\.\d+)\s+(.+?)\s*$", line)
        if m_h3 and current_section:
            sub_num = m_h3.group(1)
            sub_title = m_h3.group(2).strip()

            # §3 또는 §4 의 sub 만 wrap
            if sub_num.startswith(PKG_SECTION_PREFIX):
                # 본문 끝 찾기
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if next_line.startswith("### ") or next_line.startswith("## "):
                        break
                    j += 1

                body = "\n".join(lines[i + 1:j]).strip()

                admon_title = f"📋 §{sub_num} {sub_title} (사업계획서 paste 가능)"
                wrapped = (
                    f'<div markdown="1" class="admonition copy" data-section="{sub_num}">\n'
                    f'<p class="admonition-title">{admon_title}</p>\n\n'
                    f'{body}\n'
                    f'</div>\n'
                )
                result.append(wrapped)
                wrap_count += 1
                i = j
                continue

        result.append(line)
        i += 1

    return "\n".join(result)


def on_page_markdown(markdown: str, page, config, files):  # noqa: ARG001
    """MkDocs 훅 — 대상 페이지의 paste-ready 블록 자동 wrap."""
    src = page.file.src_path
    mode = TARGET_PATTERNS.get(src)
    if not mode:
        return markdown

    if mode == "scenario_sub":
        return wrap_scenario_subs(markdown)
    elif mode == "pkg_section":
        return wrap_pkg_sections(markdown)
    return markdown
