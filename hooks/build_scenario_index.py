"""Build docs/data/scenario_index.json from scenario catalog assets."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DATA = ROOT / "docs" / "data"
CATALOG_PATH = ROOT / "시나리오_카탈로그.md"
SLOTS_PATH = ROOT / "사전_슬롯과_도메인_10종.md"

CARD_RE = re.compile(r"^### (SCN-[A-Z]+-\d+)\s*[:—\-–]\s*(.+?)\s*$", re.MULTILINE)
FIELD_RE = re.compile(r"^- \*\*(대상 공정|고통점|AI 해결|데이터 소스|트랙 매핑|적합 규모|기대효과|삽화)\*\*:\s*(.+?)\s*$", re.MULTILINE)
OTHER_FIELD_RE = re.compile(r"^- \*\*(목적|대상)\*\*:\s*(.+?)\s*$", re.MULTILINE)
TABLE_ROW_RE = re.compile(r"^\|\s*`?(SCN-(CAS|HEA|PLT|SHP|ASM)-\d+)`?\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$", re.MULTILINE)

FIELD_KEYS = ["대상 공정", "고통점", "AI 해결", "데이터 소스", "트랙 매핑", "적합 규모", "기대효과", "삽화"]

DOMAIN_LABELS = {
    "STL": "철강·제강",
    "MET": "금속·정밀가공",
    "RUB": "고무·폴리머",
    "UTL": "유틸리티·환경",
    "MLO": "MLOps 공통",
    "LLM": "LLM·RAG 공통",
    "SAF": "안전·ESG",
    "CAS": "연속주조·중력주조",
    "HEA": "열처리·소둔·QT",
    "PLT": "도금·표면처리·도장",
    "SHP": "조선·해양기자재",
    "ASM": "자동차부품 조립",
}

DOMAIN_DATA = {
    "CAS": "턴디시 온도·몰드 진동·주조 속도·2 차 냉각수 유량·용강 성분",
    "HEA": "노 내 온도·분위기 가스·냉각 속도·열전대 응답·진공도",
    "PLT": "도금조 온도·전류 밀도·pH·전도도·도금 시간",
    "SHP": "용접 전류·전압·아크 시간·구조해석 응답·환경 온습도",
    "ASM": "토크·체결력·로봇 관절 위치·비전 검사 좌표·라인 속도",
}


def domain_prefix(scenario_id: str) -> str:
    return scenario_id.split("-")[1]


def normalize_track(value: str) -> str:
    return (
        value.replace("T1", "Track 1")
        .replace("T2", "Track 2")
        .replace("T3", "Track 3")
        .replace("  ", " ")
        .strip()
    )


def make_entry(scenario_id: str, title: str, card: dict[str, str], source: str) -> dict:
    prefix = domain_prefix(scenario_id)
    normalized_card = {key: card.get(key, "").strip() for key in FIELD_KEYS}
    return {
        "id": scenario_id,
        "title": title.strip(),
        "domain": prefix,
        "domain_label": DOMAIN_LABELS.get(prefix, prefix),
        "source": source,
        "card": normalized_card,
    }


def parse_catalog() -> list[dict]:
    content = CATALOG_PATH.read_text(encoding="utf-8")
    matches = list(CARD_RE.finditer(content))
    scenarios = []
    for index, match in enumerate(matches):
        scenario_id = match.group(1)
        title = match.group(2)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        block = content[start:end]
        fields = {field: value.strip() for field, value in FIELD_RE.findall(block)}
        other_fields = {field: value.strip() for field, value in OTHER_FIELD_RE.findall(block)}
        prefix = domain_prefix(scenario_id)
        target = fields.get("대상 공정") or other_fields.get("대상") or other_fields.get("목적") or DOMAIN_LABELS.get(prefix, prefix)
        fields.setdefault("대상 공정", target)
        fields.setdefault("고통점", f"{title} 관련 운영 기준이 분산되어 판단 재현성과 대응 속도가 제한된다.")
        fields.setdefault("AI 해결", f"{title} 를 AI 기반 분석·검색·추천 워크플로로 구현한다.")
        fields.setdefault("데이터 소스", DOMAIN_DATA.get(prefix, f"{target} 관련 운영 로그·작업 이력·검증 결과"))
        fields.setdefault("트랙 매핑", "Track 1" if prefix not in {"MLO", "LLM"} else ("Track 2" if prefix == "MLO" else "Track 3"))
        fields.setdefault("적합 규모", "전 규모")
        fields.setdefault("기대효과", f"{title} 의 운영 재현성·대응 속도·품질 안정성을 높인다.")
        fields.setdefault("삽화", f"{title} 데이터 흐름도, 운영 화면, KPI 전후 비교")
        scenarios.append(make_entry(scenario_id, title, fields, "시나리오_카탈로그.md"))
    return scenarios


def parse_candidate_rows() -> list[dict]:
    content = SLOTS_PATH.read_text(encoding="utf-8")
    scenarios = []
    for scenario_id, prefix, title, track, scale in TABLE_ROW_RE.findall(content):
        track_label = normalize_track(track)
        domain_label = DOMAIN_LABELS.get(prefix, prefix)
        data_sources = DOMAIN_DATA.get(prefix, f"{domain_label} 공정 데이터·작업 이력·품질 검사 결과")
        card = {
            "대상 공정": domain_label,
            "고통점": f"{title} 관련 판단이 작업자 경험, 분산 문서, 사후 검사에 의존하여 재현성과 대응 속도가 제한된다.",
            "AI 해결": f"{title} 를 {track_label} 기반 모델·검색·추천 워크플로로 구현하고, 작업자 검수 루프와 운영 기준을 함께 둔다.",
            "데이터 소스": data_sources,
            "트랙 매핑": track_label,
            "적합 규모": scale.strip(),
            "기대효과": f"{title} 의 품질 편차·대응 시간·재작업 부담을 낮추고 표준 운영 재현성을 높인다.",
            "삽화": f"{title} 데이터 흐름도, 추천·탐지 화면, KPI 전후 비교 차트",
        }
        scenarios.append(make_entry(scenario_id, title, card, "사전_슬롯과_도메인_10종.md §3"))
    return scenarios


def build_index() -> list[dict]:
    scenarios = parse_catalog() + parse_candidate_rows()
    seen = set()
    duplicates = []
    for item in scenarios:
        if item["id"] in seen:
            duplicates.append(item["id"])
        seen.add(item["id"])
    if duplicates:
        raise RuntimeError(f"duplicate scenarios: {', '.join(sorted(duplicates))}")
    if len(scenarios) < 65:
        raise RuntimeError(f"scenario_index requires at least 65 scenarios, got {len(scenarios)}")
    return sorted(scenarios, key=lambda item: (item["domain"], item["id"]))


def write_index() -> None:
    scenarios = build_index()
    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    (DOCS_DATA / "scenario_index.json").write_text(
        json.dumps(scenarios, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[build_scenario_index] {len(scenarios)} scenarios → data/scenario_index.json")


def on_pre_build(config):  # noqa: ARG001
    write_index()


if __name__ == "__main__":
    write_index()
