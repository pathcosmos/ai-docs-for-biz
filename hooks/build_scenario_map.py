"""Build docs/data/scenario_block_map.json from scenario and template indexes."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DATA = ROOT / "docs" / "data"

CORE_GUIDES = [
    "GUIDE-COMPANY-PROFILE-§3",
    "GUIDE-PROBLEM-MATRIX-§3",
    "GUIDE-KPI-BREAKDOWN-§3",
    "GUIDE-EXECUTION-ROADMAP-§3",
    "GUIDE-SCENARIO-ROI-§3",
    "GUIDE-DATA-SPEC-§3",
    "GUIDE-MODEL-TRAINING-§3",
    "GUIDE-DEPLOYMENT-PLAN-§3",
    "GUIDE-MLOPS-RITUAL-§3",
]

DOMAIN_HINTS = {
    "STL": ["철강", "압연", "스테인리스", "steel", "stl"],
    "MET": ["정밀가공", "CNC", "금속", "met"],
    "RUB": ["고무", "폴리머", "가황", "rub"],
    "UTL": ["유틸", "환경", "에너지", "utl"],
    "MLO": ["MLOps", "드리프트", "재학습", "mlo", "track2"],
    "LLM": ["LLM", "RAG", "문서", "llm", "track3"],
    "SAF": ["안전", "중대재해", "saf"],
    "CAS": ["주조", "연주", "턴디시", "cas"],
    "HEA": ["열처리", "소둔", "QT", "hea"],
    "PLT": ["도금", "도장", "표면", "plt"],
    "SHP": ["조선", "해양", "용접", "shp"],
    "ASM": ["자동차", "조립", "체결", "asm"],
}

CATEGORY_SCORE = {
    "scenario": 14,
    "track": 12,
    "guide": 9,
    "module": 6,
    "package": 4,
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_section(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"§\s*(\d+)", str(value))
    if not match:
        return None
    number = int(match.group(1))
    if number == 0:
        return "§1"
    if number == 10:
        return "§4"
    if 1 <= number <= 9:
        return f"§{number}"
    return None


def track_numbers(track_text: str) -> set[str]:
    numbers = set(re.findall(r"Track\s*(\d)", track_text or "", flags=re.IGNORECASE))
    numbers.update(re.findall(r"\bT(\d)\b", track_text or "", flags=re.IGNORECASE))
    return numbers


def searchable_block(block_id: str, block: dict) -> str:
    fields = [
        block_id,
        block.get("title", ""),
        block.get("category", ""),
        block.get("section", ""),
        block.get("domain", ""),
        block.get("preview", ""),
        " ".join(block.get("tags") or []),
    ]
    return " ".join(str(item) for item in fields)


def scenario_text(scenario: dict) -> str:
    card = scenario.get("card") or {}
    fields = [
        scenario.get("id", ""),
        scenario.get("title", ""),
        scenario.get("domain", ""),
        scenario.get("domain_label", ""),
        *card.values(),
    ]
    return " ".join(str(item) for item in fields)


def keyword_hits(scenario: dict, block_text: str) -> int:
    text = scenario_text(scenario)
    tokens = [
        token
        for token in re.split(r"[\s·,()\-+/]+", text)
        if len(token) >= 3 and not token.startswith("SCN")
    ]
    unique = []
    for token in tokens:
        if token not in unique:
            unique.append(token)
    return sum(1 for token in unique[:40] if token and token in block_text)


def score_block(scenario: dict, block_id: str, block: dict) -> int:
    block_text = searchable_block(block_id, block)
    block_lower = block_text.lower()
    scenario_id = scenario["id"]
    prefix = scenario["domain"]
    card = scenario.get("card") or {}
    score = 0

    if scenario_id in block_text:
        score += 100
    if prefix.lower() in block_lower:
        score += 22
    for hint in DOMAIN_HINTS.get(prefix, []):
        if hint.lower() in block_lower:
            score += 8

    for number in track_numbers(card.get("트랙 매핑", "")):
        if block.get("category") == "track" and (block.get("domain") == f"track{number}" or f"track{number}" in block_lower):
            score += 28
        if f"track{number}" in block_lower:
            score += 12

    score += CATEGORY_SCORE.get(block.get("category", ""), 0)
    if normalize_section(block.get("section")) in {"§3", "§4", "§5", "§6"}:
        score += 4
    if block_id in CORE_GUIDES:
        score += 5
    score += min(keyword_hits(scenario, block_text), 10)
    return score


def make_entry(block_id: str, block: dict, score: int) -> dict:
    return {
        "id": block_id,
        "score": score,
        "title": block.get("title", ""),
        "section": normalize_section(block.get("section")),
        "category": block.get("category", ""),
    }


def build_map() -> dict[str, list[dict]]:
    scenarios = load_json(DOCS_DATA / "scenario_index.json")
    templates = load_json(DOCS_DATA / "templates_index.json")
    result: dict[str, list[dict]] = {}

    for scenario in scenarios:
        scored = []
        for block_id, block in templates.items():
            score = score_block(scenario, block_id, block)
            if score > 0:
                scored.append(make_entry(block_id, block, score))
        scored.sort(key=lambda item: (-item["score"], item["category"], item["id"]))

        chosen = []
        seen = set()
        for item in scored:
            if item["id"] in seen:
                continue
            chosen.append(item)
            seen.add(item["id"])
            if len(chosen) >= 14:
                break

        for guide_id in CORE_GUIDES:
            if len(chosen) >= 5:
                break
            if guide_id in templates and guide_id not in seen:
                chosen.append(make_entry(guide_id, templates[guide_id], 1))
                seen.add(guide_id)

        if len(chosen) < 5:
            raise RuntimeError(f"{scenario['id']} mapped block count below 5: {len(chosen)}")
        result[scenario["id"]] = chosen

    return result


def write_map() -> None:
    scenario_map = build_map()
    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    (DOCS_DATA / "scenario_block_map.json").write_text(
        json.dumps(scenario_map, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    min_count = min(len(items) for items in scenario_map.values()) if scenario_map else 0
    print(f"[build_scenario_map] {len(scenario_map)} scenarios · min {min_count} blocks → data/scenario_block_map.json")


def on_pre_build(config):  # noqa: ARG001
    write_map()


if __name__ == "__main__":
    write_map()
