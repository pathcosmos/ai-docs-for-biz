"""regenerate_all_mmdc.py — 모든 mmdc SVG 재생성 with stepBefore (직각 화살표 정책).

정책: **모든 다이어그램 화살표는 직각 (orthogonal)**.

전략:
- docs/assets/diagrams/ 의 모든 SVG 식별
- mmdc 생성물 vs 직접 작성 디자인 SVG 분리 (`<g class="root">` 또는 `#my-svg` 마커)
- mmdc 만 git history 의 원본 mermaid 코드 복원 + stepBefore directive prepend + 재변환
- 직접 작성 디자인 SVG 는 skip (이미 직각)
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT = Path("/Volumes/EXDATA/temp_git/ai-docs-for-biz")
SLUG_MAP_FILE = ROOT / "slug_map.yml"
DIAGRAMS_BASE = ROOT / "docs" / "assets" / "diagrams"

# Mermaid 코드 보존된 commit 후보 (시간 역순)
COMMIT_CANDIDATES = ["8feb327", "6b14f5d"]

with open(SLUG_MAP_FILE) as f:
    SLUG_MAP = yaml.safe_load(f)
REVERSE_SLUG = {v: k for k, v in SLUG_MAP.items()}

MERMAID_RE_NAMED = re.compile(
    r"^([ \t]*)```mermaid\s*\n(.*?)\n[ \t]*```\s*$",
    re.MULTILINE | re.DOTALL,
)
MERMAID_RE_BARE = re.compile(
    r"^([ \t]*)```\s*\n((?:flowchart |graph |sequenceDiagram|gantt|stateDiagram|classDiagram|gitGraph|erDiagram|pie|journey)[\s\S]*?)\n[ \t]*```\s*$",
    re.MULTILINE,
)


def is_mmdc_svg(svg_path: Path) -> bool:
    """mmdc 생성 SVG 인지 식별."""
    try:
        text = svg_path.read_text(encoding="utf-8", errors="ignore")[:500]
        return ('id="my-svg"' in text or 'class="flowchart"' in text or 'aria-roledescription="flowchart' in text)
    except Exception:
        return False


def get_md_at_commit(commit: str, md_filename: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{md_filename}"],
            capture_output=True, text=True, cwd=ROOT, timeout=10,
        )
        return result.stdout if result.returncode == 0 else None
    except Exception:
        return None


def extract_mermaid_blocks(content: str) -> list[dict]:
    blocks = []
    for m in MERMAID_RE_NAMED.finditer(content):
        blocks.append({"indent": m.group(1), "code": m.group(2), "start": m.start()})
    for m in MERMAID_RE_BARE.finditer(content):
        if not any(b["start"] == m.start() for b in blocks):
            blocks.append({"indent": m.group(1), "code": m.group(2), "start": m.start()})
    blocks.sort(key=lambda b: b["start"])
    return blocks


def rotate_lr_to_td(code: str) -> str:
    lines = code.split("\n")
    if lines and lines[0].strip().startswith("flowchart LR"):
        lines[0] = lines[0].replace("flowchart LR", "flowchart TD", 1)
    elif lines and lines[0].strip().startswith("graph LR"):
        lines[0] = lines[0].replace("graph LR", "graph TD", 1)
    return "\n".join(lines)


def normalize_syntax(code: str) -> str:
    code = code.replace("<br/>", "<br>").replace("<br />", "<br>")
    PLACEHOLDERS = ["수치", "기간", "고객사", "공정", "%", "기준", "임계", "비율", "LLM모델", "벡터스토어",
                    "단계", "년", "월", "일", "건", "명", "개", "도메인", "지역", "지원사업", "기관",
                    "팀", "조", "분", "시간", "N", "M", "n", "m", "회", "권", "점", "도", "차", "초", "시"]
    for ph in PLACEHOLDERS:
        code = code.replace(f"[{ph}]", f"({ph})")
    new_lines = []
    for line in code.split("\n"):
        if "[" in line and "]" in line and not line.lstrip().startswith("subgraph"):
            first = line.find("[")
            last = line.rfind("]")
            if first < last:
                outer_label = line[first + 1: last]
                inner_normalized = re.sub(r"\[([^\]\[\n]{1,15})\]", r"(\1)", outer_label)
                line = line[:first + 1] + inner_normalized + line[last:]
        new_lines.append(line)
    code = "\n".join(new_lines)
    code = re.sub(r"\|([^|\n]+)\|", lambda m: f"|{re.sub(r'[\\[\\]]', '', m.group(1))}|", code)
    return code


def mmdc_with_stepbefore(code: str, output_path: Path) -> tuple[bool, str]:
    """stepBefore directive 자동 prepend + mmdc 변환."""
    if not code.lstrip().startswith("%%{init"):
        code = '%%{init: {"flowchart": {"curve": "stepBefore"}}}%%\n' + code

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".mmd", mode="w", encoding="utf-8", delete=False) as tmp:
        tmp.write(code)
        tmp_path = Path(tmp.name)
    try:
        result = subprocess.run(
            ["mmdc", "-i", str(tmp_path), "-o", str(output_path),
             "-t", "default", "-b", "white", "-w", "800", "-H", "1200"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0 or not output_path.exists():
            return False, result.stderr.strip()[:200]
        return True, ""
    except Exception as e:
        return False, str(e)[:200]
    finally:
        tmp_path.unlink(missing_ok=True)


def regenerate_slug(slug: str):
    """단일 slug (디렉토리) 의 모든 mmdc SVG 재생성."""
    slug_dir = DIAGRAMS_BASE / slug
    if not slug_dir.exists():
        return
    svgs = sorted(slug_dir.glob("diagram-*.svg"))
    mmdc_svgs = [s for s in svgs if is_mmdc_svg(s)]
    if not mmdc_svgs:
        return  # 모두 직접 작성 디자인 SVG (skip)

    # slug → root .md
    docs_md_candidates = [f"{prefix}/{slug}.md" for prefix in
                          ("track", "pkg", "scenario", "guide", "module", "other", "meta")] + [f"{slug}.md"]
    root_md = None
    for docs_path in docs_md_candidates:
        if docs_path in REVERSE_SLUG:
            root_md = REVERSE_SLUG[docs_path]
            break
    if not root_md:
        root_md = f"docs/{slug}.md"

    # commit 시점별 mermaid 코드 추출
    mermaid_blocks = []
    for commit in COMMIT_CANDIDATES:
        content = get_md_at_commit(commit, root_md)
        if content:
            blocks = extract_mermaid_blocks(content)
            if len(blocks) >= len(svgs):
                mermaid_blocks = blocks
                break
            if blocks and not mermaid_blocks:
                mermaid_blocks = blocks

    if not mermaid_blocks:
        print(f"  ✗ {slug}: mermaid 코드 복원 실패 ({root_md})")
        return

    # 각 mmdc SVG 의 diagram-N → mermaid block N-1
    for svg in mmdc_svgs:
        m = re.search(r"diagram-(\d+)\.svg", svg.name)
        if not m:
            continue
        n = int(m.group(1))
        if n - 1 >= len(mermaid_blocks):
            continue
        block = mermaid_blocks[n - 1]
        code = block["code"]
        # LR → TD (가로형 회피)
        code = rotate_lr_to_td(code)
        # syntax 정규화
        code = normalize_syntax(code)
        success, err = mmdc_with_stepbefore(code, svg)
        if success:
            print(f"  ✓ {slug}/{svg.name}: stepBefore 적용")
        else:
            print(f"  ✗ {slug}/{svg.name}: {err[:80]}")


def main():
    slugs = sorted([d.name for d in DIAGRAMS_BASE.iterdir() if d.is_dir()])
    print(f"## 대상 slug: {len(slugs)}")
    for slug in slugs:
        regenerate_slug(slug)


if __name__ == "__main__":
    main()
