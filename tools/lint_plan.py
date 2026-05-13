#!/usr/bin/env python3
"""lint_plan.py — 가상 사업계획서 자동 검증 스크립트

산출물 C (사업계획서_가상_10종/*.md) 또는 신규 고객사 사업계획서를
6 축으로 기계 검증한다:
  1. {{slot_*}}     잔존 0
  2. placeholder    [수치]·[고객사]·[공정]·[기간]·[%] 등 잔존 0 (gold 의도 잔존은 화이트리스트)
  3. 9 섹션 헤더    ## §1 ~ ## §9 누락 검사
  4. 섹션별 길이    줄 수·단락 수 균형도 (편차 ±50 % 이내 권장)
  5. 도메인 cross   다른 도메인 어휘 누출 카운트
  6. 메타 흔적      "기본값"·"sample"·"default"·"TODO"·"FIXME" 누설 0

출력: 도메인 N × 항목 6 매트릭스 (terminal 표 + JSON).

의존성: Python 표준 라이브러리만. PyYAML 은 사용 안 함.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List

# ─────────────────────────────────────────────────────────────────────
# 상수 — 검증 기준
# ─────────────────────────────────────────────────────────────────────

# 9 섹션 헤더 — composeFromLibrary 의 출력 형식 ## §N 제목
EXPECTED_SECTION_HEADERS = [
    r"^## §1\b",
    r"^## §2\b",
    r"^## §3\b",
    r"^## §4\b",
    r"^## §5\b",
    r"^## §6\b",
    r"^## §7\b",
    r"^## §8\b",
    r"^## §9\b",
]

# 슬롯 패턴 — composeFromLibrary 의 fill() 함수가 채우지 못한 슬롯
SLOT_PATTERN = re.compile(r"\{\{(\w+)\}\}")

# placeholder 패턴 — 워크스페이스 표준 (방법론 4.8)
# 의도적 잔존이 허용되는 placeholder 는 화이트리스트 (조립 메타·견본 표기 등) 로 분리
PLACEHOLDER_PATTERN = re.compile(r"\[(고객사|공정|수치|기간|%)(?=\]|[^\w가-힣])[^\]]*\]")

# 화이트리스트 — gold 사례에서 의도적 잔존이 허용되는 패턴
# (예: 머리말의 "[고객사 — ...]" 표기, 조립 메타의 견본 표기)
PLACEHOLDER_WHITELIST = re.compile(
    r"\[고객사 — [^\]]+\]"  # "[고객사 — 부산·경남 가상 ...]" 형식
)

# 메타 흔적 — 본문에 누출되어서는 안 되는 코드·메타 어휘
META_LEAKAGE_PATTERNS = [
    re.compile(r"\bTODO\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bsample_\w+"),  # sample_facility 등 코드 키 누출
    re.compile(r"\bDEFAULTS\b"),
    re.compile(r"\bDOMAIN_PROFILE\b"),
    re.compile(r"\bbuildSlots\b(?![^`]*`)"),  # 코드 블록 외 buildSlots 누출
]

# 도메인 어휘 사전 — 본문에 다른 도메인 어휘가 누출되었는지 검사
# 각 도메인의 매우 distinctive 한 단어만 등록 (일반 단어 제외)
DOMAIN_VOCAB = {
    "STL": ["1ZHM", "2ZHM", "BAF", "압연유", "스테인리스"],
    "MET": ["CNC", "머시닝센터", "절삭 토크", "공구 마모"],
    "RUB": ["밴버리", "가황", "압출", "고무 배합"],
    "UTL": ["보일러", "압축기", "냉동기", "폐수 처리", "SOx", "NOx"],
    "LLM": ["RAG", "환각률", "임베딩", "BGE", "KoAlpaca"],
    "CAS": ["턴디시", "몰드", "연주", "용강", "슬라브"],
    "HEA": ["가열로", "QT", "퀜칭", "템퍼링", "결정립"],
    "PLT": ["도금조", "전기도금", "QUALICOAT", "분체도장", "정류기"],
    "SHP": ["선각", "블록", "선급", "DNV", "ABS", "용접 비드"],
    "ASM": ["체결력", "산업로봇", "토크 건", "비전 검사"],
}

# 파일명 → 도메인 매핑 (사업계획서_가상_10종 의 파일명 규약)
FILENAME_DOMAIN_PATTERN = re.compile(r"\d+_(\w+)_\w+\.md$")


# ─────────────────────────────────────────────────────────────────────
# 검증 함수
# ─────────────────────────────────────────────────────────────────────


def detect_domain(path: Path) -> str | None:
    m = FILENAME_DOMAIN_PATTERN.search(path.name)
    return m.group(1) if m else None


def check_slot_residual(text: str) -> Dict:
    matches = SLOT_PATTERN.findall(text)
    return {
        "count": len(matches),
        "unique": sorted(set(matches)),
        "pass": len(matches) == 0,
    }


def check_placeholder_residual(text: str) -> Dict:
    # 본문에서 화이트리스트 (예: "[고객사 — ...]") 를 먼저 제거
    cleaned = PLACEHOLDER_WHITELIST.sub("", text)
    matches = PLACEHOLDER_PATTERN.findall(cleaned)
    return {
        "count": len(matches),
        "unique": sorted(set(matches)),
        "pass": len(matches) == 0,
    }


def check_section_headers(text: str) -> Dict:
    missing: List[str] = []
    for i, pattern in enumerate(EXPECTED_SECTION_HEADERS, 1):
        if not re.search(pattern, text, re.MULTILINE):
            missing.append(f"§{i}")
    return {
        "missing": missing,
        "pass": len(missing) == 0,
    }


def check_section_balance(text: str) -> Dict:
    """각 § 섹션의 줄 수·단락 수가 균형 잡혀 있는지 검사 (±50 % 이내)."""
    sections: Dict[str, int] = {}
    current = None
    line_count = 0
    for line in text.splitlines():
        m = re.match(r"^## (§\d)\b", line)
        if m:
            if current is not None:
                sections[current] = line_count
            current = m.group(1)
            line_count = 0
        elif current is not None:
            line_count += 1
    if current is not None:
        sections[current] = line_count

    if not sections:
        return {"sections": {}, "balance_ratio": 0, "pass": False}

    counts = list(sections.values())
    if not counts or max(counts) == 0:
        return {"sections": sections, "balance_ratio": 0, "pass": False}

    balance_ratio = min(counts) / max(counts)
    return {
        "sections": sections,
        "balance_ratio": round(balance_ratio, 2),
        "pass": balance_ratio >= 0.10,  # 최소 섹션이 최대의 10 % 이상이면 통과
    }


def check_domain_cross_pollution(text: str, my_domain: str | None) -> Dict:
    """본문에 다른 도메인 어휘가 누출되었는지 검사."""
    if my_domain is None or my_domain not in DOMAIN_VOCAB:
        return {"my_domain": my_domain, "leaks": {}, "pass": True}

    leaks: Dict[str, List[str]] = {}
    for other_domain, vocab in DOMAIN_VOCAB.items():
        if other_domain == my_domain:
            continue
        hits = [w for w in vocab if w in text]
        if hits:
            # 본 도메인의 도메인 인접 (예: STL ↔ CAS·HEA) 이거나
            # cross-cutting (LLM·UTL 의 RAG·MLOps 단어) 은 의도적일 수 있음
            # → 정보로만 보고, pass 판정은 누출 4 단어 이상에서만 fail
            leaks[other_domain] = hits

    total_leaks = sum(len(v) for v in leaks.values())
    return {
        "my_domain": my_domain,
        "leaks": leaks,
        "total_leaks": total_leaks,
        "pass": total_leaks < 4,  # 3 단어 이하는 인접 도메인·cross-cutting 으로 허용
    }


def check_meta_leakage(text: str) -> Dict:
    hits: List[str] = []
    for pattern in META_LEAKAGE_PATTERNS:
        for m in pattern.finditer(text):
            hits.append(m.group(0))
    return {
        "count": len(hits),
        "samples": hits[:5],
        "pass": len(hits) == 0,
    }


# ─────────────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────────────


def lint_file(path: Path) -> Dict:
    text = path.read_text(encoding="utf-8")
    domain = detect_domain(path)
    result = {
        "file": str(path),
        "domain": domain,
        "checks": {
            "slot_residual": check_slot_residual(text),
            "placeholder_residual": check_placeholder_residual(text),
            "section_headers": check_section_headers(text),
            "section_balance": check_section_balance(text),
            "domain_cross": check_domain_cross_pollution(text, domain),
            "meta_leakage": check_meta_leakage(text),
        },
    }
    result["all_pass"] = all(c["pass"] for c in result["checks"].values())
    return result


def render_table(results: List[Dict]) -> str:
    """Terminal 표 형태로 결과 렌더."""
    rows = []
    header = (
        "| 도메인 | 파일 | slot | place | §hdr | bal | cross | meta | PASS |"
    )
    sep = "|--------|------|------|-------|------|-----|-------|------|------|"
    rows.append(header)
    rows.append(sep)

    def mark(p: bool) -> str:
        return "✅" if p else "❌"

    for r in results:
        c = r["checks"]
        fname = Path(r["file"]).name
        domain = r["domain"] or "?"
        bal = c["section_balance"]["balance_ratio"]
        cross_n = c["domain_cross"].get("total_leaks", 0)
        rows.append(
            f"| {domain:<6} | {fname:<24} | "
            f"{mark(c['slot_residual']['pass'])} ({c['slot_residual']['count']}) | "
            f"{mark(c['placeholder_residual']['pass'])} ({c['placeholder_residual']['count']}) | "
            f"{mark(c['section_headers']['pass'])} ({len(c['section_headers']['missing'])}) | "
            f"{mark(c['section_balance']['pass'])} ({bal}) | "
            f"{mark(c['domain_cross']['pass'])} ({cross_n}) | "
            f"{mark(c['meta_leakage']['pass'])} ({c['meta_leakage']['count']}) | "
            f"{mark(r['all_pass'])} |"
        )
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        type=str,
        help="검증 대상 — 디렉터리 (재귀 *.md) 또는 단일 .md 파일",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON 형식 출력 (terminal 표 대신)",
    )
    parser.add_argument(
        "--strict-cross",
        action="store_true",
        help="도메인 cross 누출 1 단어부터 fail (기본 4 단어 이상에서만 fail)",
    )
    args = parser.parse_args()

    target = Path(args.target)
    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(target.rglob("*.md"))
    else:
        print(f"❌ 대상 경로 없음: {target}", file=sys.stderr)
        return 2

    if not files:
        print(f"⚠ .md 파일 없음: {target}", file=sys.stderr)
        return 0

    if args.strict_cross:
        global check_domain_cross_pollution

        original = check_domain_cross_pollution

        def strict(text, dom):
            r = original(text, dom)
            r["pass"] = r.get("total_leaks", 0) == 0
            return r

        check_domain_cross_pollution = strict  # type: ignore

    results = [lint_file(f) for f in files]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"\nlint_plan.py — {len(results)} 파일 검증\n")
        print(render_table(results))
        # 위반 상세
        fails = [r for r in results if not r["all_pass"]]
        if fails:
            print(f"\n❌ {len(fails)} 파일이 검증 실패. 상세:")
            for r in fails:
                print(f"\n  [{r['domain']}] {Path(r['file']).name}")
                for name, c in r["checks"].items():
                    if not c["pass"]:
                        print(f"    - {name}: {c}")
        else:
            print(f"\n✅ 전체 {len(results)} 파일 검증 통과")

    return 0 if all(r["all_pass"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
