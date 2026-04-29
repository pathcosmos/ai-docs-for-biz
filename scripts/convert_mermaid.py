"""convert_mermaid.py — Phase E11-2

Root 의 한국어 .md 파일 + docs/ 직접 작성 .md 파일에서 ` ```mermaid ... ``` ` 블록을 추출,
mmdc (mermaid-cli) 로 정적 SVG 변환, 마크다운에서 ![](svg path) 로 교체.

배경: 사용자 호소 #4 (mermaid syntax error 깨짐). Phase 1 Explore 결과 119 블록 전수 위험 패턴.
결정 (사용자): 전수 정적 SVG 변환 + mermaid.js CDN 제거.

기준 동작:
1. root 의 19 .md (slug_map.yml 매핑된 파일 중 mermaid 함유) + docs/ 직접 작성 (blocks.md, by-package.md, start-here.md)
2. 각 mermaid 블록 → 임시 .mmd → mmdc → docs/assets/diagrams/{slug}/diagram-N.svg
3. 마크다운에서 블록 → `![캡션](../assets/diagrams/{slug}/diagram-N.svg)` 교체
4. root .md 직접 수정 (workspace .md 정책 — Phase E11 plan §H 명시)

mmdc 설치 (이미 됨): npm install -g @mermaid-js/mermaid-cli

mmdc 옵션:
  -i input.mmd
  -o output.svg
  -t default (테마 default — 'forest', 'dark', 'neutral' 중 default)
  -w 800 -H 600 (배경 사이즈, 한국어 노드 가독성)
  --backgroundColor white

출력: SVG 인라인 텍스트 + path 교체. 실패 블록은 stderr 보고 (수동 처리).
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

with open(SLUG_MAP_FILE, encoding="utf-8") as f:
    SLUG_MAP = yaml.safe_load(f)

# Reverse slug map: { "pkg/pkg2-cold-rolled.md": "사업계획서_패키지2_..." }
REVERSE_SLUG = {v: k for k, v in SLUG_MAP.items()}

# Mermaid 블록 정규식 — 3 패턴 통합 (Phase E14-A 보강)
# 1. ```mermaid ... ```  (top-level)
# 2. {indent}```mermaid ... ```  (들여쓰기 — list item content 안)
# 3. {indent}``` + mermaid syntax 시작 (bare fence — flowchart·graph·sequenceDiagram 등)
MERMAID_RE = re.compile(
    # Pattern 1+2 통합: 들여쓰기 0 또는 N 모두 매치
    r"^([ \t]*)```mermaid\s*\n(.*?)\n[ \t]*```\s*$",
    re.MULTILINE | re.DOTALL,
)

# Bare fence + mermaid syntax 시작 (flowchart·graph·sequenceDiagram·gantt·stateDiagram 등)
MERMAID_BARE_RE = re.compile(
    r"^([ \t]*)```\s*\n((?:flowchart |graph |sequenceDiagram|gantt|stateDiagram|classDiagram|gitGraph|erDiagram|pie|journey)[\s\S]*?)\n[ \t]*```\s*$",
    re.MULTILINE,
)


def slug_for_file(md_path: Path) -> str:
    """Root .md 또는 docs/ 직접 작성 파일의 slug stem 반환.

    예: 사업계획서_패키지2_중견냉연_파일럿.md → "pkg2-cold-rolled"
        docs/blocks.md → "blocks"
    """
    name = md_path.name
    if name in SLUG_MAP:
        # root 한국어 파일 → docs/ slug
        slug_path = SLUG_MAP[name]  # "pkg/pkg2-cold-rolled.md"
        return Path(slug_path).stem  # "pkg2-cold-rolled"
    elif md_path.parent == ROOT / "docs":
        # docs/ 직접 작성 파일
        return md_path.stem
    else:
        return md_path.stem


def relative_svg_path(md_path: Path, slug: str, n: int) -> str:
    """마크다운 안에서 사용할 상대 경로 — docs/assets/diagrams/{slug}/diagram-N.svg.

    Root .md → docs/ 의 영문 slug 디렉토리에서 보면 ../assets/diagrams/{slug}/diagram-N.svg
    docs/ 직접 작성 (예 docs/blocks.md) → assets/diagrams/{slug}/diagram-N.svg
    """
    if md_path.parent == ROOT:
        # Root 파일 — docs/ 의 슬러그 디렉토리에서 보면 한 단계 상위
        slug_dir = SLUG_MAP.get(md_path.name, "")  # "pkg/pkg2-cold-rolled.md"
        depth = len(Path(slug_dir).parent.parts)  # "pkg" → 1
        prefix = "../" * depth if depth > 0 else ""
        return f"{prefix}assets/diagrams/{slug}/diagram-{n}.svg"
    elif md_path.parent == ROOT / "docs":
        return f"assets/diagrams/{slug}/diagram-{n}.svg"
    else:
        # docs/ 의 sub-dir
        depth = len(md_path.relative_to(ROOT / "docs").parent.parts)
        prefix = "../" * depth if depth > 0 else ""
        return f"{prefix}assets/diagrams/{slug}/diagram-{n}.svg"


def normalize_mermaid_syntax(code: str) -> str:
    """mermaid syntax 자동 정규화 — 노드 라벨 따옴표 wrap + `<br/>` → `<br>`.

    Phase 1 진단 결과 119 블록 전수 위험 패턴: `<br/>` 65+ · 한글+하이픈 50+ · 라벨 안 [수치]·(년) 등.
    가장 흔한 깨짐 원인: 노드 라벨 안의 [수치]·[기간] 이 mermaid 가 노드 종결 brackets 로 오인.
    해결: 노드 라벨을 따옴표로 강제 wrap.
    """
    # 1. <br/> → <br>
    code = code.replace("<br/>", "<br>").replace("<br />", "<br>")

    # 1a. 플레이스홀더 [수치]·[기간]·[고객사] 등 → 전각 대괄호 『xxx』 변환
    # 라벨 안에서 mermaid 가 노드 종결 brackets 로 오인하는 가장 큰 원인 제거.
    # 본 변환은 mermaid 블록 안에서만 적용 (본문 텍스트 placeholder 는 보존).
    PLACEHOLDERS = [
        "수치", "기간", "고객사", "공정", "%", "기준", "임계", "비율",
        "LLM모델", "벡터스토어", "단계", "년", "월", "일", "건", "명", "개",
        "도메인", "지역", "지원사업", "기관", "팀", "조", "분", "시간",
        "N", "M", "n", "m", "회", "권", "점", "도", "차", "초", "시",
        "거리", "온도", "압력", "속도", "주파수", "용량", "두께", "길이",
    ]
    for ph in PLACEHOLDERS:
        code = code.replace(f"[{ph}]", f"({ph})")

    # 1c. 노드 라벨 안의 inner [xxx] (1~15자 짧은 단어) → (xxx) 강제 변환
    # mermaid 노드 정의 outer [...] 안에 또 [...] 가 있으면 mermaid 가 깨짐.
    # line by line + bracket depth 추적.
    new_lines = []
    for line in code.split("\n"):
        # 노드 정의 패턴 검출 (\w+\[ 또는 [( 또는 (( 등)
        # 단순 휴리스틱: line 안에서 첫 [ 부터 그 깊이의 마지막 ] 까지가 outer label
        if "[" in line and "]" in line and not line.lstrip().startswith("subgraph"):
            # 첫 [ 의 위치
            first = line.find("[")
            # 마지막 ] 의 위치
            last = line.rfind("]")
            if first < last:
                outer_label = line[first + 1 : last]
                # 라벨 안의 inner [xxx] (짧은 단어) 변환
                inner_normalized = re.sub(
                    r"\[([^\]\[\n]{1,15})\]",
                    r"(\1)",
                    outer_label,
                )
                line = line[: first + 1] + inner_normalized + line[last:]
        new_lines.append(line)
    code = "\n".join(new_lines)

    # 1b. 라벨 안의 일반 대괄호 — 화살표·노드 정의 외부의 [숫자]·[A1] 등도 위험
    # 다만 mermaid 자체 노드 정의 [라벨] 은 보존해야 함.
    # 안전한 방법: 라벨 패턴 (노드ID[...]) 안의 [xxx] 를 (xxx) 로 변환.

    # 2. 노드 라벨 따옴표 wrap — [...], ((...)),  등 mermaid 노드 패턴
    # 패턴: 노드ID[라벨], 노드ID(라벨), 노드ID{라벨}, 노드ID[(라벨)], 노드ID((라벨)), 노드ID{{라벨}}
    # 라벨에 이미 따옴표 있으면 skip

    def quote_label(match: re.Match[str]) -> str:
        prefix = match.group(1)  # 노드ID + 여는 bracket
        body = match.group(2)
        suffix = match.group(3)  # 닫는 bracket
        if body.startswith('"') and body.endswith('"'):
            return match.group(0)  # 이미 따옴표
        # 라벨 안의 따옴표 escape
        body_escaped = body.replace('"', '#quot;')
        return f'{prefix}"{body_escaped}"{suffix}'

    # [...] (단일 대괄호) — 가장 흔함
    code = re.sub(
        r"(\w+\[)([^\]\[\n][^\]\n]*?)(\])",
        quote_label,
        code,
    )
    # ((...)) (이중 괄호 — circle)
    code = re.sub(
        r"(\w+\(\()([^)\n]+?)(\)\))",
        quote_label,
        code,
    )
    # {{...}} (이중 중괄호 — hexagon)
    code = re.sub(
        r"(\w+\{\{)([^}\n]+?)(\}\})",
        quote_label,
        code,
    )
    # [(...)] (cylinder)
    code = re.sub(
        r"(\w+\[\()([^)\n]+?)(\)\])",
        quote_label,
        code,
    )

    # 3. 화살표 라벨 |라벨| 안의 특수문자 — 그대로 두되 [], () escape
    # |곱 ≥ 임계 [수치]| → |곱 ≥ 임계 수치| (간단 escape)
    def escape_arrow_label(match: re.Match[str]) -> str:
        body = match.group(1)
        # [, ] 제거
        body_clean = re.sub(r"[\[\]]", "", body)
        return f"|{body_clean}|"

    code = re.sub(r"\|([^|\n]+)\|", escape_arrow_label, code)

    return code


def convert_mermaid_to_svg(mermaid_code: str, output_path: Path) -> tuple[bool, str]:
    """mermaid 코드 → SVG 파일. (success, error_msg) 반환.

    1차 시도: 원본 그대로
    2차 시도: syntax 정규화 후
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1차: 원본
    success, err = _try_mmdc(mermaid_code, output_path)
    if success:
        return True, ""

    # 2차: syntax 정규화
    normalized = normalize_mermaid_syntax(mermaid_code)
    if normalized != mermaid_code:
        success, err2 = _try_mmdc(normalized, output_path)
        if success:
            return True, ""
        # 디버그: 정규화된 코드 첫 5 줄 + 정규화 err 전체
        norm_preview = "\n      ".join(normalized.split("\n")[:8])
        return False, (
            f"원본 err: {err[:80]}\n      정규화 err: {err2[:200]}\n"
            f"      정규화 코드 미리보기:\n      {norm_preview}"
        )

    return False, err


def _try_mmdc(mermaid_code: str, output_path: Path) -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile(
        suffix=".mmd", mode="w", encoding="utf-8", delete=False
    ) as tmp:
        tmp.write(mermaid_code)
        tmp_path = Path(tmp.name)

    try:
        result = subprocess.run(
            [
                "mmdc",
                "-i", str(tmp_path),
                "-o", str(output_path),
                "-t", "default",
                "-b", "white",
                "-w", "800",
                "-H", "1000",  # 세로형 (Phase E11-3 정합)
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return False, result.stderr.strip()
        if not output_path.exists():
            return False, "SVG 파일 생성 안 됨"
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "mmdc 타임아웃 (30초)"
    except Exception as e:
        return False, str(e)
    finally:
        tmp_path.unlink(missing_ok=True)


def extract_caption(mermaid_code: str) -> str:
    """mermaid 코드에서 첫 의미 있는 라벨 추출 (alt 텍스트용)."""
    # 첫 줄: flowchart LR / graph TD / sequenceDiagram 등
    lines = mermaid_code.strip().split("\n")
    diagram_type = lines[0].strip() if lines else "다이어그램"

    # 노드 이름 첫 발견
    label_match = re.search(r'\["?([^"\]]+)"?\]|\("([^"]+)"\)', mermaid_code)
    if label_match:
        label = (label_match.group(1) or label_match.group(2)).strip()
        # `<br/>` 제거, 앞 50자
        label = re.sub(r"<br\s*/?>\s*", " ", label)[:50]
        return label or diagram_type
    return diagram_type


def process_file(md_path: Path, dry_run: bool = False) -> dict:
    """단일 .md 파일 처리. 변환 카운트 + 실패 목록 반환."""
    if not md_path.exists():
        return {"file": str(md_path), "blocks": 0, "ok": 0, "failed": []}

    content = md_path.read_text(encoding="utf-8")

    # [E14-A] 3 패턴 통합 매치: 들여쓰기 mermaid + bare fence
    matches_named = list(MERMAID_RE.finditer(content))    # group: (indent, code)
    matches_bare = list(MERMAID_BARE_RE.finditer(content))  # group: (indent, code)

    # 두 정규식 매치 결합 (위치 기준 정렬)
    all_matches = []
    for m in matches_named:
        all_matches.append({"start": m.start(), "end": m.end(), "indent": m.group(1), "code": m.group(2), "match": m})
    for m in matches_bare:
        # named 와 중복 회피
        if not any(am["start"] == m.start() for am in all_matches):
            all_matches.append({"start": m.start(), "end": m.end(), "indent": m.group(1), "code": m.group(2), "match": m})
    all_matches.sort(key=lambda x: x["start"])

    if not all_matches:
        return {"file": str(md_path), "blocks": 0, "ok": 0, "failed": []}

    slug = slug_for_file(md_path)
    diagram_dir = DIAGRAMS_BASE / slug

    ok_count = 0
    failed = []

    # 역순으로 교체 (인덱스 변동 방지)
    new_content = content
    for idx, am in enumerate(reversed(all_matches), start=1):
        n = len(all_matches) - idx + 1  # 정방향 번호
        mermaid_code = am["code"]
        indent = am["indent"]
        svg_path = diagram_dir / f"diagram-{n}.svg"
        rel_path = relative_svg_path(md_path, slug, n)
        caption = extract_caption(mermaid_code)

        if dry_run:
            ok_count += 1
            continue

        success, err = convert_mermaid_to_svg(mermaid_code, svg_path)
        if not success:
            failed.append({"n": n, "error": err[:200], "code_first_line": mermaid_code.split("\n")[0]})
            continue

        # 마크다운 교체 (들여쓰기 보존 — list item content 안 mermaid 대응)
        replacement = f'{indent}![{caption} (다이어그램 {n})]({rel_path})'
        new_content = new_content[:am["start"]] + replacement + new_content[am["end"]:]
        ok_count += 1

    if not dry_run and ok_count > 0:
        md_path.write_text(new_content, encoding="utf-8")

    return {
        "file": str(md_path.name),
        "slug": slug,
        "blocks": len(all_matches),
        "ok": ok_count,
        "failed": failed,
    }


def main():
    """전체 .md 처리 — root 의 mermaid 함유 19 종 + docs/ 직접 작성."""
    targets = []

    # Root 의 mermaid 함유 .md (slug_map 에 있는 것만)
    # [E14-A] mermaid 검출 키워드 — 명시적 ```mermaid 또는 bare fence + flowchart 등 syntax
    def has_mermaid(text: str) -> bool:
        if "```mermaid" in text:
            return True
        # bare fence + mermaid syntax 시작 (flowchart·graph·sequenceDiagram 등)
        return bool(re.search(
            r"^[ \t]*```\s*\n[ \t]*(?:flowchart |graph |sequenceDiagram|gantt|stateDiagram|classDiagram|gitGraph|erDiagram|pie|journey)",
            text, re.MULTILINE
        ))

    for md_name in SLUG_MAP.keys():
        md_path = ROOT / md_name
        if md_path.exists() and has_mermaid(md_path.read_text(encoding="utf-8")):
            targets.append(md_path)

    # docs/ 직접 작성 파일 (slug_map 에 없음)
    for direct in [
        "docs/blocks.md", "docs/by-package.md", "docs/start-here.md",
        "docs/index.md", "docs/graph.md", "docs/filter.md",
    ]:
        p = ROOT / direct
        if p.exists() and has_mermaid(p.read_text(encoding="utf-8")):
            targets.append(p)

    print(f"[convert_mermaid] 대상 파일: {len(targets)}")

    total_blocks = 0
    total_ok = 0
    all_failed = []

    for md_path in targets:
        result = process_file(md_path)
        total_blocks += result["blocks"]
        total_ok += result["ok"]
        if result["failed"]:
            all_failed.append(result)
        status = "✓" if not result["failed"] else "✗"
        print(f"  {status} {result['file']:50} {result['ok']:3}/{result['blocks']:3} 변환")

    print(f"\n[convert_mermaid] 요약: {total_ok}/{total_blocks} 변환 성공")

    if all_failed:
        print(f"\n[실패 상세]")
        for r in all_failed:
            print(f"\n  파일: {r['file']}")
            for f in r["failed"]:
                print(f"    블록 {f['n']}: {f['code_first_line']}")
                print(f"      → {f['error'][:150]}")


if __name__ == "__main__":
    main()
