"""build_crossref.py — 274 인용 출처 표기 파싱 → docs/data/crossref.json 생성.

MkDocs 빌드 시점에 모든 페이지의 markdown 을 스캔하여 `> [출처: 파일명.md §섹션]` 패턴을
추출하고 노드·엣지 형태로 정규화. graph.js (D3 force-directed) 의 입력으로 사용.

출력 포맷 (`docs/data/crossref.json`):
{
  "nodes": [
    {"id": "track/track1-index", "label": "Track 1 목차", "group": "track", "url": "/track/track1-index/"},
    ...
  ],
  "edges": [
    {"source": "pkg/pkg1-steel-enterprise", "target": "track/track1-index", "weight": 1},
    ...
  ]
}

본 hook 은 `on_files` 또는 `on_pre_build` 에서 동작 — 빌드 직전 1 회 실행.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import yaml

SOURCE_RE = re.compile(r"\[출처:\s*([^\s\]]+\.md)")

# 자산 군별 그룹 매핑 (slug 디렉토리 기준)
GROUP_LABELS = {
    "track": "Track 본문",
    "pkg": "통합 파일럿",
    "guide": "운영 가이드",
    "scenario": "시나리오",
    "module": "Cross-cutting 모듈",
    "other": "기타 자산",
    "meta": "메타",
}


def load_slug_map(config_dir: Path) -> dict[str, str]:
    slug_path = config_dir / "slug_map.yml"
    with slug_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def slug_to_id(slug_path: str) -> str:
    """docs/track/track1-index.md → track/track1-index"""
    return slug_path.removesuffix(".md")


def slug_to_url(slug_path: str) -> str:
    """track/track1-index.md → /track/track1-index/"""
    return "/" + slug_path.removesuffix(".md") + "/"


def derive_group(slug_path: str) -> str:
    parts = slug_path.split("/")
    if len(parts) >= 2 and parts[0] in GROUP_LABELS:
        return parts[0]
    return "other"


def extract_label_from_md(file_path: Path) -> str:
    """원본 .md 의 첫 H1 추출."""
    try:
        text = file_path.read_text(encoding="utf-8")
        m = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
        if m:
            label = m.group(1).strip().strip("`")
            # 너무 긴 라벨 단축 (그래프 노드 라벨용)
            if len(label) > 30:
                label = label[:28] + "…"
            return label
    except Exception:
        pass
    return slug_to_id(str(file_path))


def build_crossref(config) -> None:
    """slug_map 의 모든 자산을 노드로, > [출처: ...] 표기를 엣지로 변환."""
    config_dir = Path(config["config_file_path"]).parent
    docs_dir = config_dir / "docs"
    data_dir = docs_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / "crossref.json"

    slug_map = load_slug_map(config_dir)

    # 노드 생성 — slug_map 기반
    nodes: list[dict] = []
    slug_to_filename: dict[str, str] = {}  # slug_path → 원본 한글 filename
    filename_to_slug: dict[str, str] = {}  # 원본 한글 filename → slug_path
    for orig_filename, slug_path in slug_map.items():
        node_id = slug_to_id(slug_path)
        group = derive_group(slug_path)
        # 원본 .md 의 H1 을 라벨로 사용 (디렉토리 root 의 .md)
        label = extract_label_from_md(config_dir / orig_filename)
        nodes.append({
            "id": node_id,
            "label": label,
            "group": group,
            "group_label": GROUP_LABELS.get(group, "기타"),
            "url": slug_to_url(slug_path),
            "filename": orig_filename,
        })
        slug_to_filename[node_id] = orig_filename
        filename_to_slug[orig_filename] = node_id

    # 엣지 생성 — 모든 docs/ 하위 .md 의 > [출처: ...] 표기 파싱
    edge_count: dict[tuple[str, str], int] = defaultdict(int)
    for orig_filename, slug_path in slug_map.items():
        source_node = slug_to_id(slug_path)
        md_file = docs_dir / slug_path
        if not md_file.exists():
            continue
        try:
            text = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in SOURCE_RE.finditer(text):
            referenced = m.group(1)
            target_slug = filename_to_slug.get(referenced)
            if not target_slug:
                continue
            if target_slug == source_node:
                continue  # self-reference 회피
            edge_count[(source_node, target_slug)] += 1

    edges = [
        {"source": s, "target": t, "weight": w}
        for (s, t), w in edge_count.items()
    ]

    output = {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "total_citations": sum(edge_count.values()),
        },
    }

    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[build_crossref] 노드 {len(nodes)} · 엣지 {len(edges)} · 인용 {sum(edge_count.values())} → {output_path}")


def on_pre_build(config):  # noqa: ARG001
    """MkDocs hook — 빌드 직전 crossref.json 생성."""
    build_crossref(config)
