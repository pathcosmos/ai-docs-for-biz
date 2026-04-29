"""rotate_mermaid_to_vertical.py — 가로형 mmdc SVG 전면 재작업 (Phase E15)

전략:
1. git history 의 Phase E11-2 직전 commit (Phase E14-A 직전 base) 에서 .md 파일 추출
2. 각 .md 의 mermaid 블록 추출 + 위치 매핑
3. flowchart LR / graph LR → flowchart TD / graph TD 변환 (LR 인 블록만)
4. mmdc 재변환 → 같은 SVG 경로에 덮어쓰기
5. 결과: 가로형 → 세로형 SVG (의미 100% 보존)

대상: aspect_audit.json 의 horizontal 62 SVG 만.
근거 commit: 6b14f5d (E11-1, E11-2 직전 — mermaid 코드 모두 보존)
+ E14-A 추가 변환된 9 블록 (들여쓰기 + bare fence) 은 별도 처리.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path("/Volumes/EXDATA/temp_git/ai-docs-for-biz")
AUDIT_JSON = ROOT / "docs" / "data" / "svg_aspect_audit.json"
SLUG_MAP_FILE = ROOT / "slug_map.yml"

# Phase E11-2 직전 commit (mermaid 코드 모두 보존)
BASE_COMMIT_E11 = "6b14f5d"
# Phase E14-A 직전 commit (5.2 카드 + 모듈 mermaid 포함)
BASE_COMMIT_E14 = "8feb327"

import yaml
with open(SLUG_MAP_FILE) as f:
    SLUG_MAP = yaml.safe_load(f)
REVERSE_SLUG = {v: k for k, v in SLUG_MAP.items()}  # docs slug → root .md


# Mermaid 정규식 (다양한 형식)
MERMAID_RE_NAMED = re.compile(
    r"^([ \t]*)```mermaid\s*\n(.*?)\n[ \t]*```\s*$",
    re.MULTILINE | re.DOTALL,
)
MERMAID_RE_BARE = re.compile(
    r"^([ \t]*)```\s*\n((?:flowchart |graph |sequenceDiagram|gantt|stateDiagram|classDiagram|gitGraph|erDiagram|pie|journey)[\s\S]*?)\n[ \t]*```\s*$",
    re.MULTILINE,
)


def get_md_at_commit(commit: str, md_filename: str) -> str | None:
    """git show <commit>:<filename> — 해당 commit 시점의 .md 내용 반환."""
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{md_filename}"],
            capture_output=True, text=True, cwd=ROOT, timeout=10,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except Exception:
        return None


def extract_mermaid_blocks(content: str) -> list[dict]:
    """.md 내용에서 모든 mermaid 블록 추출. (indent, code, position) 리스트 반환."""
    blocks = []
    for m in MERMAID_RE_NAMED.finditer(content):
        blocks.append({"indent": m.group(1), "code": m.group(2), "start": m.start()})
    for m in MERMAID_RE_BARE.finditer(content):
        if not any(b["start"] == m.start() for b in blocks):
            blocks.append({"indent": m.group(1), "code": m.group(2), "start": m.start()})
    blocks.sort(key=lambda b: b["start"])
    return blocks


def is_horizontal_lr(code: str) -> bool:
    """mermaid 코드의 첫 줄이 LR 흐름인지 확인."""
    first = code.strip().split("\n")[0].strip()
    return first.startswith("flowchart LR") or first.startswith("graph LR")


def rotate_to_td(code: str) -> str:
    """flowchart LR → flowchart TD, graph LR → graph TD."""
    lines = code.split("\n")
    if not lines:
        return code
    first = lines[0].strip()
    if first.startswith("flowchart LR"):
        lines[0] = lines[0].replace("flowchart LR", "flowchart TD", 1)
    elif first.startswith("graph LR"):
        lines[0] = lines[0].replace("graph LR", "graph TD", 1)
    return "\n".join(lines)


def normalize_mermaid_syntax(code: str) -> str:
    """convert_mermaid.py 의 syntax 정규화 일부 (placeholder + <br/> + 노드 라벨 따옴표)."""
    code = code.replace("<br/>", "<br>").replace("<br />", "<br>")
    PLACEHOLDERS = [
        "수치", "기간", "고객사", "공정", "%", "기준", "임계", "비율",
        "LLM모델", "벡터스토어", "단계", "년", "월", "일", "건", "명", "개",
        "도메인", "지역", "지원사업", "기관", "팀", "조", "분", "시간",
        "N", "M", "n", "m", "회", "권", "점", "도", "차", "초", "시",
    ]
    for ph in PLACEHOLDERS:
        code = code.replace(f"[{ph}]", f"({ph})")

    # 라벨 안 inner [xxx] (1~15자)
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

    # 화살표 라벨 |...| 안 [, ] 제거
    code = re.sub(r"\|([^|\n]+)\|", lambda m: f"|{re.sub(r'[\\[\\]]', '', m.group(1))}|", code)

    return code


def mmdc_convert(mermaid_code: str, output_path: Path) -> tuple[bool, str]:
    """mermaid → SVG 변환."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".mmd", mode="w", encoding="utf-8", delete=False) as tmp:
        tmp.write(mermaid_code)
        tmp_path = Path(tmp.name)

    try:
        result = subprocess.run(
            ["mmdc", "-i", str(tmp_path), "-o", str(output_path),
             "-t", "default", "-b", "white", "-w", "800", "-H", "1200"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0 or not output_path.exists():
            return False, result.stderr.strip()[:300]
        return True, ""
    except Exception as e:
        return False, str(e)[:300]
    finally:
        tmp_path.unlink(missing_ok=True)


def process_horizontal_svgs(audit: dict):
    """가로형 SVG 만 LR→TD 변환 후 재 mmdc."""
    horizontal = audit["horizontal"]
    print(f"## 가로형 SVG {len(horizontal)} 종 처리")

    # 파일별 그룹화
    by_slug = {}
    for r in horizontal:
        slug = r["slug"]  # e.g., "pkg2-cold-rolled"
        diagram_n = int(re.search(r"diagram-(\d+)\.svg", r["diagram"]).group(1))
        by_slug.setdefault(slug, []).append(diagram_n)

    # 각 slug → root .md 매핑 + commit 기반 mermaid 추출
    ok_total = 0
    fail_total = 0
    for slug, diagram_ns in sorted(by_slug.items()):
        # slug → docs path → root path
        docs_md_candidates = [
            f"{prefix}/{slug}.md" for prefix in ("track", "pkg", "scenario", "guide", "module", "other", "meta")
        ] + [f"{slug}.md"]
        root_md = None
        for docs_path in docs_md_candidates:
            if docs_path in REVERSE_SLUG:
                root_md = REVERSE_SLUG[docs_path]
                break
        if not root_md:
            # docs/ 직접 작성 (blocks·by-package·start-here·index·graph·filter·catalog)
            root_md = f"docs/{slug}.md"

        # commit 시점별 mermaid 코드 추출 (E11 직전 + E14 직전 둘 다 시도)
        mermaid_blocks = []
        for commit in [BASE_COMMIT_E11, BASE_COMMIT_E14]:
            content = get_md_at_commit(commit, root_md)
            if content:
                blocks = extract_mermaid_blocks(content)
                if blocks:
                    mermaid_blocks = blocks
                    break

        if not mermaid_blocks:
            print(f"  ✗ {slug}: mermaid 코드 복원 실패 ({root_md})")
            fail_total += len(diagram_ns)
            continue

        # 각 가로형 diagram-N → mermaid block N-1 (인덱스 0-based)
        for n in sorted(diagram_ns):
            if n - 1 >= len(mermaid_blocks):
                print(f"  ✗ {slug}/diagram-{n}: 매핑 인덱스 초과 ({len(mermaid_blocks)} blocks)")
                fail_total += 1
                continue

            block = mermaid_blocks[n - 1]
            code = block["code"]

            # LR → TD 변환
            if not is_horizontal_lr(code):
                # 이미 TD 또는 다른 흐름인데 SVG 가 가로 — 뭔가 이상. 일단 skip.
                print(f"  ⚠ {slug}/diagram-{n}: 첫 줄 LR 아님 ({code.split(chr(10))[0]})")
                continue

            rotated = rotate_to_td(code)
            normalized = normalize_mermaid_syntax(rotated)

            # mmdc 재변환
            output_path = ROOT / "docs" / "assets" / "diagrams" / slug / f"diagram-{n}.svg"
            success, err = mmdc_convert(normalized, output_path)
            if success:
                print(f"  ✓ {slug}/diagram-{n}: LR → TD 변환 + mmdc 재생성")
                ok_total += 1
            else:
                # 1차 실패 시 정규화 안 한 코드로 재시도
                success2, err2 = mmdc_convert(rotated, output_path)
                if success2:
                    print(f"  ✓ {slug}/diagram-{n}: LR → TD (정규화 skip)")
                    ok_total += 1
                else:
                    print(f"  ✗ {slug}/diagram-{n}: mmdc 실패 — {err[:100]}")
                    fail_total += 1

    print(f"\n[summary] {ok_total} 성공 / {fail_total} 실패")


def main():
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    process_horizontal_svgs(audit)


if __name__ == "__main__":
    main()
