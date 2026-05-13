#!/usr/bin/env python3
"""Generate a paste-ready 9-section business plan from the local Layer A library.

The script intentionally uses only Python's standard library. It reads the
human-readable Markdown library/dictionary files, fills slots, writes one clean
Markdown document, and runs tools/lint_plan.py unless --no-lint is supplied.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
LIBRARY_PATH = ROOT / "라이브러리_공통문구_9섹션.md"
DICTIONARY_PATH = ROOT / "사전_슬롯과_도메인_10종.md"
LINT_PATH = ROOT / "tools" / "lint_plan.py"

SECTION_TITLES = {
    "§1": "현황",
    "§2": "문제인식",
    "§3": "개선방향",
    "§4": "수행방향",
    "§5": "AI 적용 포인트",
    "§6": "데이터·변수",
    "§7": "모델·학습",
    "§8": "적용·배포",
    "§9": "MLOps loop",
}

DEFAULTS = {
    "veteran_count": "3~5",
    "variable_count": "10~15",
    "experience_years": "10 년",
    "spec_variance_pct": "8~12",
    "pdf_form_count": "10~20",
    "human_entry_minutes": "5~10",
    "human_error_pct": "2~5",
    "retention_period": "3 년",
    "kpi_quality_pct": "15~25",
    "kpi_productivity_pct": "10~20",
    "kpi_anomaly_accuracy_pct": "90",
    "kpi_fp_pct": "5",
    "kpi_fn_pct": "3",
    "total_budget_eok": "6",
    "govt_ratio_pct": "50",
    "private_ratio_pct": "50",
    "trl_start": "5",
    "trl_target": "6",
    "duration_months": "9",
    "ml_drift_psi_warn": "0.10",
    "ml_drift_psi_retrain": "0.25",
    "edge_latency_ms": "100",
    "hmi_latency_s": "2",
    "rag_latency_s": "5",
    "service_sla_pct": "99.5",
}

SCALE_PROFILE = {
    "중소": {
        "total_budget_eok": "3",
        "govt_ratio_pct": "70",
        "private_ratio_pct": "30",
        "duration_months": "9",
        "trl_start": "4",
        "trl_target": "5",
        "veteran_count": "2~3",
        "spec_variance_pct": "10~15",
        "pdf_form_count": "8~15",
        "retention_period": "2 년",
    },
    "중견": {
        "total_budget_eok": "7",
        "govt_ratio_pct": "50",
        "private_ratio_pct": "50",
        "duration_months": "12",
        "trl_start": "5",
        "trl_target": "6",
        "veteran_count": "3~5",
        "spec_variance_pct": "8~12",
        "pdf_form_count": "10~20",
        "retention_period": "3 년",
    },
    "대기업": {
        "total_budget_eok": "22",
        "govt_ratio_pct": "40",
        "private_ratio_pct": "60",
        "duration_months": "24",
        "trl_start": "5",
        "trl_target": "7",
        "veteran_count": "10~15",
        "spec_variance_pct": "5~8",
        "pdf_form_count": "25~40",
        "retention_period": "5 년",
    },
}

PACKAGE_BY_DOMAIN = {
    "STL": "pkg2",
    "MET": "pkg5",
    "RUB": "pkg4",
    "UTL": "pkg6",
    "LLM": "pkg3",
    "CAS": "pkg1",
    "HEA": "pkg3",
    "PLT": "pkg5",
    "SHP": "pkg1",
    "ASM": "pkg5",
}

DOMAIN_SLOT_MAP = {
    "process_default": "domain_label",
    "sample_facility": "facility",
    "sample_product": "product",
    "sample_quality_target": "quality_target",
    "sample_kpi_label": "kpi_label",
    "sensor_examples": "sensor_examples",
    "image_examples": "image_examples",
    "cert_examples": "cert_examples",
    "risk_examples": "risk_examples",
    "model_examples": "model_examples",
    "scenario_focus": "scenario_focus",
    "veteran_areas": "veteran_areas",
}


def clean_cell(value: str) -> str:
    return (
        value.strip()
        .strip("|")
        .replace("`", "")
        .replace("**", "")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )


def split_table_row(line: str) -> List[str]:
    return [clean_cell(cell) for cell in line.strip().strip("|").split("|")]


def parse_domain_profiles(text: str) -> Dict[str, Dict[str, str]]:
    profiles: Dict[str, Dict[str, str]] = {}
    domains: List[str] = []
    for line in text.splitlines():
        if line.startswith("| 슬롯 |") and "**" in line:
            domains = re.findall(r"\*\*([A-Z]{3})\*\*", line)
            for domain in domains:
                profiles.setdefault(domain, {})
            continue
        if not domains or not line.startswith("| `"):
            continue
        cells = split_table_row(line)
        if len(cells) < len(domains) + 1:
            continue
        key = cells[0]
        for domain, value in zip(domains, cells[1:]):
            profiles.setdefault(domain, {})[key] = value
    return profiles


def strip_source_blocks(section: str) -> str:
    lines = []
    skipping_source = False
    for line in section.splitlines():
        if line.startswith("> [출처"):
            skipping_source = True
            continue
        if skipping_source and line.startswith(">"):
            continue
        if skipping_source and not line.strip():
            skipping_source = False
            continue
        if line.strip() == "---":
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def parse_library_sections(text: str) -> Dict[str, str]:
    sections: Dict[str, str] = {}
    matches = list(re.finditer(r"^## (§\d)\b[^\n]*\n", text, flags=re.MULTILINE))
    for index, match in enumerate(matches):
        section_id = match.group(1)
        start = match.end()
        next_section = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        next_non_section = re.search(r"\n## (?!§)", text[start:next_section])
        end = start + next_non_section.start() if next_non_section else next_section
        body = strip_source_blocks(text[start:end])
        sections[section_id] = f"## {section_id} {SECTION_TITLES[section_id]}\n\n{body}".strip()
    return sections


def split_scenarios(value: str) -> List[str]:
    return [item.strip() for item in re.split(r"[,·\s]+", value) if item.strip()]


def build_slots(args: argparse.Namespace, profiles: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    if args.domain not in profiles:
        raise SystemExit(f"unknown domain: {args.domain}")
    domain_profile = profiles[args.domain]
    slots = dict(DEFAULTS)
    slots.update(SCALE_PROFILE.get(args.scale, {}))
    slots.update(
        {
            "company": args.company,
            "industry": args.domain,
            "process": args.process or domain_profile.get("process_default", ""),
            "package_label": args.package or PACKAGE_BY_DOMAIN.get(args.domain, "pkg2"),
            "scenarios_label": "·".join(split_scenarios(args.scenarios)),
        }
    )
    for source_key, slot_key in DOMAIN_SLOT_MAP.items():
        slots[slot_key] = domain_profile.get(source_key, "")
    if not slots["process"]:
        slots["process"] = slots["domain_label"]
    return slots


def fill_slots(text: str, slots: Dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return slots.get(key, match.group(0))

    filled = re.sub(r"\{\{(\w+)\}\}", replace, text)
    return polish_korean_spacing(filled)


def polish_korean_spacing(text: str) -> str:
    text = re.sub(
        r"([가-힣A-Za-z0-9\]\)])\s+(은|는|이|가|을|를|의|에|에서|으로|로|와|과)(?=\s)",
        r"\1\2",
        text,
    )
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def compose(args: argparse.Namespace) -> str:
    profiles = parse_domain_profiles(DICTIONARY_PATH.read_text(encoding="utf-8"))
    sections = parse_library_sections(LIBRARY_PATH.read_text(encoding="utf-8"))
    slots = build_slots(args, profiles)
    body = "\n\n".join(fill_slots(sections[f"§{idx}"], slots) for idx in range(1, 10))
    return f"# {args.company} AI 사업계획서\n\n{body}\n"


def run_lint(path: Path) -> int:
    result = subprocess.run(
        [sys.executable, str(LINT_PATH), str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", required=True, choices=sorted(PACKAGE_BY_DOMAIN))
    parser.add_argument("--scale", required=True, choices=sorted(SCALE_PROFILE))
    parser.add_argument("--company", required=True)
    parser.add_argument("--process", default="")
    parser.add_argument("--scenarios", required=True)
    parser.add_argument("--package", default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--no-lint", action="store_true")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(compose(args), encoding="utf-8")
    if args.no_lint:
        return 0
    return run_lint(output)


if __name__ == "__main__":
    raise SystemExit(main())
