"""build_templates_data.py — Phase E16 Stage 3-A (대폭 확장)

빌드 시점에 워크스페이스 자산 → docs/data/templates.json 자동 생성.

추출 대상 (15 → ~280 블록):
- Track 1·2·3 top5 (15 BLK) — H2 단위
- 6 패키지 (~54 블록) — H2 §0~§8 단위
- 시나리오 상세 5 (~80 블록) — SCN + 4 sub (적용맥락·AS-IS·AI 해결·기대효과)
- 운영 가이드 11 (~80 블록) — H2 §1~§8 단위
- 5 모듈 (~35 블록) — H3 BLK-XXX-A~G 단위

각 블록 메타: category·section·package·domain·tags·preview
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# ============================================================================
# 정규식 패턴
# ============================================================================

# Track top5 — H2 BLK 패턴 2 종 (Track 1·3 vs Track 2)
TRACK_BLK_RE = re.compile(
    r"^## (?:"
    r"(?P<sectionA>\d+\.\d+)\s+(?P<titleA>.+?)\s*\((?:블록명:\s*)?(?P<idA>BLK-T\d-\d+\.\d+)\)"
    r"|"
    r"(?P<idB>BLK-T(?P<trackB>\d)-(?P<sectionB>\d+\.\d+))\s*[—\-–]\s*(?P<titleB>.+?)"
    r")\s*$",
    re.MULTILINE,
)

# 패키지 H2 — `## 0. 과제 요약` / `## 1. 사업 개요` ... / `## 8. 부록`
PKG_H2_RE = re.compile(r"^## (\d+)\.\s+(.+?)\s*$", re.MULTILINE)

# 시나리오 SCN — `## SCN-XXX-NN — 제목` (또는 `:`)
SCN_RE = re.compile(r"^## (SCN-[A-Z]+-\d+)\s*[—\-–:]\s*(.+?)\s*$", re.MULTILINE)
# 시나리오 sub-section — `### 적용 맥락` / `### AS-IS` / `### AI 해결` / `### 기대효과` / `### 도식` / `### 삽화`
SCN_SUB_HEADERS = ("적용 맥락", "AS-IS", "AI 해결", "기대효과")
SCN_SUB_RE = re.compile(r"^### (.+?)\s*$", re.MULTILINE)

# 가이드 H2 — `## 1. ... / ## 2. ...`
GUIDE_H2_RE = re.compile(r"^## (\d+)\.\s+(.+?)\s*$", re.MULTILINE)

# 모듈 H3 BLK — `### BLK-CBAM-A — 배경·시의성`
MODULE_BLK_RE = re.compile(
    r"^### (BLK-[A-Z]+-[A-Z])\s*[—\-–]\s*(.+?)\s*$",
    re.MULTILINE,
)

# 본문 끝 — 다음 H2/H3 또는 `### 도식·삽화`
BODY_END_HEADERS = ("도식", "삽화 (Mermaid)", "삽화(Mermaid)")

# ============================================================================
# 메타데이터 매핑
# ============================================================================

# 패키지 H2 → 사업계획서 § 매핑
PKG_SECTION_MAP = {
    "0": "§0 과제 요약",
    "1": "§1 사업 개요·추진 배경",
    "2": "§2 기업 현황·대상 공정",
    "3": "§3 현황·문제점 (AS-IS)",
    "4": "§4 목표 모습 (TO-BE)·도입 전략",
    "5": "§5 구축 상세",
    "6": "§6 기대효과·성과 지표",
    "7": "§7 Track 2·3 연계",
    "8": "§8 부록·별첨",
}

# 가이드 slug → 사업계획서 § 매핑
GUIDE_SECTION_MAP = {
    "assembly": "§ 본문 조립 (전체)",
    "finance-budget": "§10 재무·예산",
    "duration-compress": "§ 사업기간 (1·5)",
    "kpi-measurement": "§6 KPI 측정",
    "external-validation": "§ 외부 검증·RACI",
    "rag-infra": "§4·5 RAG 인프라",
    "domain-knowledge": "§ 도메인 지식추출",
    "korean-slm": "§4·5 한국 sLM",
    "consulting-outsource": "§ 컨설팅 위탁",
    "trl-progress": "§ TRL 진척",
    "risk-matrix": "§ 위험 매트릭스",
    "quickstart": "§ Quick-Start",
}

# 모듈 → 사업계획서 § 매핑
MODULE_SECTION_MAP = {
    "cbam": "§3.5 ESG·CBAM·§7 성과",
    "safety": "§1.2 추진 배경 (중대재해)",
    "federated-learning": "§3.4 성과공유 (연합학습)",
    "oem-supply": "§1.1 외부 환경 (OEM)",
    "saas-security": "§3.5 보안 (SaaS)",
}

# 시나리오 sub → 사업계획서 § 매핑
SCN_SUB_SECTION_MAP = {
    "적용 맥락": "§3.1·4.1 사업 배경·도입 맥락",
    "AS-IS": "§3 현황·문제점 (AS-IS)",
    "AI 해결": "§4 TO-BE·AI 도입 전략",
    "기대효과": "§6 기대효과·성과 지표",
}

# 패키지별 도메인
PKG_DOMAIN = {
    "pkg1-steel-enterprise": "STL",
    "pkg2-cold-rolled": "STL",
    "pkg3-special-pipe": "STL·LLM",
    "pkg4-rubber": "RUB",
    "pkg5-precision": "MET",
    "pkg6-util-esg": "UTL·SAF",
}

# 시나리오 SCN-XXX 도메인 prefix → 도메인
SCN_DOMAIN_MAP = {
    "STL": "철강",
    "MET": "정밀가공",
    "RUB": "고무·폴리머",
    "UTL": "유틸·환경",
    "SAF": "안전",
    "LLM": "LLM·RAG",
    "MLO": "MLOps",
    "CSEC": "보안",
}

# ============================================================================
# 본문 추출 유틸
# ============================================================================


def trim_body(text: str) -> str:
    """본문 끝 — `### 도식` / `### 삽화` 직전까지 자름. 빈 줄 다듬기."""
    for header in BODY_END_HEADERS:
        idx = text.find(f"### {header}")
        if idx > 0:
            text = text[:idx]
        idx2 = text.find(f"### 삽화")
        if idx2 > 0:
            text = text[:idx2]
    # 한 줄 이상 빈 줄 정규화
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def make_preview(body: str, n: int = 80) -> str:
    """본문 처음 N 자 (마크다운 stripped) preview."""
    # 마크다운 강조 제거
    plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", body)
    plain = re.sub(r"`([^`]+)`", r"\1", plain)
    plain = re.sub(r"\n+", " ", plain)
    plain = plain.strip()
    return plain[:n] + ("…" if len(plain) > n else "")


# ============================================================================
# 자산별 추출 함수
# ============================================================================


def extract_track_top5(md_path: Path, track_n: int) -> dict:
    """Track 1·2·3 top5 BLK 5 종 추출."""
    if not md_path.exists():
        return {}
    content = md_path.read_text(encoding="utf-8")
    matches = list(TRACK_BLK_RE.finditer(content))
    if not matches:
        return {}

    templates = {}
    for i, m in enumerate(matches):
        if m.group("idA"):
            blk_id = m.group("idA")
            title = m.group("titleA").strip()
            section = m.group("sectionA")
        else:
            blk_id = m.group("idB")
            title = m.group("titleB").strip()
            section = m.group("sectionB")

        h2_end = m.end()
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = trim_body(content[h2_end:next_start])

        section_label = f"§{section}"
        templates[blk_id] = {
            "title": f"{blk_id} — {title}",
            "body": body,
            "category": "track",
            "section": section_label,
            "package": None,
            "domain": f"track{track_n}",
            "tags": [f"track{track_n}", "core-blk"],
            "preview": make_preview(body),
        }
    return templates


def extract_package(md_path: Path, pkg_slug: str) -> dict:
    """패키지 .md 의 H2 §0~§8 추출."""
    if not md_path.exists():
        return {}
    content = md_path.read_text(encoding="utf-8")
    matches = list(PKG_H2_RE.finditer(content))
    if not matches:
        return {}

    pkg_id = pkg_slug.split("-")[0]  # pkg1 / pkg2 ...
    domain = PKG_DOMAIN.get(pkg_slug, "")

    templates = {}
    for i, m in enumerate(matches):
        section_num = m.group(1)
        title = m.group(2).strip()
        # 본문
        h2_end = m.end()
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = trim_body(content[h2_end:next_start])
        if not body or len(body) < 50:
            continue  # 너무 짧은 헤더 skip

        block_id = f"PKG-{pkg_id.upper()}-§{section_num}"
        templates[block_id] = {
            "title": f"{pkg_slug} §{section_num}. {title}",
            "body": body,
            "category": "package",
            "section": PKG_SECTION_MAP.get(section_num, f"§{section_num}"),
            "package": pkg_id,
            "domain": domain,
            "tags": [pkg_id, "package", domain.lower().replace("·", "-")],
            "preview": make_preview(body),
        }
    return templates


def extract_scenarios(md_path: Path, scn_file: str) -> dict:
    """시나리오 상세 .md 의 SCN × 4 sub 추출."""
    if not md_path.exists():
        return {}
    content = md_path.read_text(encoding="utf-8")
    scn_matches = list(SCN_RE.finditer(content))
    if not scn_matches:
        return {}

    templates = {}
    for i, scn_m in enumerate(scn_matches):
        scn_id = scn_m.group(1)
        scn_title = scn_m.group(2).strip()
        scn_start = scn_m.end()
        scn_end = scn_matches[i + 1].start() if i + 1 < len(scn_matches) else len(content)
        scn_block = content[scn_start:scn_end]

        # 도메인 (SCN-XXX-NN → XXX)
        domain_prefix = scn_id.split("-")[1]
        domain = SCN_DOMAIN_MAP.get(domain_prefix, domain_prefix)

        # 4 sub-section 추출
        sub_matches = list(SCN_SUB_RE.finditer(scn_block))
        for j, sub_m in enumerate(sub_matches):
            sub_title = sub_m.group(1).strip()
            # SCN_SUB_HEADERS 중 하나로 시작?
            matched_header = None
            for h in SCN_SUB_HEADERS:
                if sub_title.startswith(h):
                    matched_header = h
                    break
            if not matched_header:
                continue

            sub_start = sub_m.end()
            sub_end = sub_matches[j + 1].start() if j + 1 < len(sub_matches) else len(scn_block)
            sub_body = trim_body(scn_block[sub_start:sub_end])
            if not sub_body or len(sub_body) < 30:
                continue

            block_id = f"{scn_id}/{matched_header.replace(' ', '_')}"
            templates[block_id] = {
                "title": f"{scn_id} {matched_header} — {scn_title}",
                "body": sub_body,
                "category": "scenario",
                "section": SCN_SUB_SECTION_MAP.get(matched_header, matched_header),
                "package": None,
                "domain": domain,
                "tags": [scn_id, domain_prefix, "scenario", matched_header.replace(" ", "_")],
                "preview": make_preview(sub_body),
            }
    return templates


def extract_guide(md_path: Path, guide_slug: str) -> dict:
    """운영 가이드 .md 의 H2 §1~§8 추출."""
    if not md_path.exists():
        return {}
    content = md_path.read_text(encoding="utf-8")
    matches = list(GUIDE_H2_RE.finditer(content))
    if not matches:
        return {}

    section_label = GUIDE_SECTION_MAP.get(guide_slug, guide_slug)

    templates = {}
    for i, m in enumerate(matches):
        h2_num = m.group(1)
        title = m.group(2).strip()
        h2_end = m.end()
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = trim_body(content[h2_end:next_start])
        if not body or len(body) < 50:
            continue

        block_id = f"GUIDE-{guide_slug.upper()}-§{h2_num}"
        templates[block_id] = {
            "title": f"가이드 {guide_slug} §{h2_num}. {title}",
            "body": body,
            "category": "guide",
            "section": section_label,
            "package": None,
            "domain": "guide",
            "tags": ["guide", guide_slug, f"§{h2_num}"],
            "preview": make_preview(body),
        }
    return templates


def extract_module(md_path: Path, module_slug: str) -> dict:
    """모듈 .md 의 BLK-XXX-A~G 추출."""
    if not md_path.exists():
        return {}
    content = md_path.read_text(encoding="utf-8")
    matches = list(MODULE_BLK_RE.finditer(content))
    if not matches:
        return {}

    section_label = MODULE_SECTION_MAP.get(module_slug, "")

    templates = {}
    for i, m in enumerate(matches):
        blk_id = m.group(1)
        title = m.group(2).strip()
        h3_end = m.end()
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = trim_body(content[h3_end:next_start])
        if not body or len(body) < 30:
            continue

        templates[blk_id] = {
            "title": f"{blk_id} — {title}",
            "body": body,
            "category": "module",
            "section": section_label,
            "package": None,
            "domain": module_slug,
            "tags": ["module", module_slug, blk_id.split("-")[1]],
            "preview": make_preview(body),
        }
    return templates


# ============================================================================
# MkDocs hook
# ============================================================================


def on_pre_build(config):
    """MkDocs 훅 — 빌드 시점 templates.json 자동 생성."""
    docs_dir = Path(config["docs_dir"])
    all_templates = {}

    # 1. Track 1·2·3 top5 (15 BLK)
    for n, slug in enumerate(["track1-top5", "track2-top5", "track3-top5"], start=1):
        all_templates.update(extract_track_top5(docs_dir / "track" / f"{slug}.md", n))

    # 2. 6 패키지
    for pkg_slug in ["pkg1-steel-enterprise", "pkg2-cold-rolled", "pkg3-special-pipe",
                     "pkg4-rubber", "pkg5-precision", "pkg6-util-esg"]:
        all_templates.update(extract_package(docs_dir / "pkg" / f"{pkg_slug}.md", pkg_slug))

    # 3. 시나리오 상세 5
    for scn_slug in ["detail-top5", "detail-phase2", "detail-rub", "detail-utl-saf", "detail-special-pipe"]:
        all_templates.update(extract_scenarios(docs_dir / "scenario" / f"{scn_slug}.md", scn_slug))

    # 4. 운영 가이드 11
    for guide_slug in ["assembly", "finance-budget", "duration-compress", "kpi-measurement",
                       "external-validation", "rag-infra", "domain-knowledge", "korean-slm",
                       "consulting-outsource", "trl-progress", "risk-matrix", "quickstart"]:
        all_templates.update(extract_guide(docs_dir / "guide" / f"{guide_slug}.md", guide_slug))

    # 5. 5 모듈
    for module_slug in ["cbam", "safety", "federated-learning", "oem-supply", "saas-security"]:
        all_templates.update(extract_module(docs_dir / "module" / f"{module_slug}.md", module_slug))

    # 출력
    output = docs_dir / "data" / "templates.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(all_templates, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 통계
    by_cat = {}
    for blk in all_templates.values():
        by_cat[blk["category"]] = by_cat.get(blk["category"], 0) + 1

    cat_summary = " · ".join(f"{k}: {v}" for k, v in sorted(by_cat.items()))
    print(f"[build_templates_data] {len(all_templates)} 블록 → data/templates.json ({cat_summary})")
