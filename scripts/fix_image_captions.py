"""fix_image_captions.py — Phase E12-Fix-3

문제: convert_mermaid.py 의 extract_caption() 이 mermaid 첫 노드 라벨에서 [수치]·[기간]
같은 placeholder 를 포함한 채 [:50] 슬라이스 → unclosed bracket 으로 markdown image 깨짐.

예 (깨진 마크다운):
  ![베테랑 숙련공 [수치 (다이어그램 1)](path.svg)
  →  ! 다음 [...] 안에 또 [...] 가 있어서 markdown image 파싱 실패

수정: 모든 .md 의 `![caption](path)` 패턴에서 caption 안의 `[`,`]` 제거 + placeholder 정리.

idempotent: 재실행 시 0 변경.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("/Volumes/EXDATA/temp_git/ai-docs-for-biz")

# `![caption](path)` 패턴 — caption 안의 [·] 제거
# 단순 정규식: ![ + caption + ]( + path + )
# caption 안에 닫는 ] 가 또 있으면 markdown 도 깨짐 → 안전한 처리: 첫 ]( 까지를 caption 으로 간주
IMAGE_RE = re.compile(r"!\[([^\n]*?)\]\(([^\)\n]+?)\)")

# caption 깨짐 패턴 — caption 안에 [ 가 있으면 unclosed
BROKEN_PATTERN = re.compile(r"!\[([^\]\n]*?\[[^\]\n]*?)\(([^\)\n]+?)\)")


def clean_caption(caption: str) -> str:
    """caption 안의 [, ] 제거 + placeholder 정리."""
    # [수치], [기간] 등 placeholder → 단순 텍스트
    cleaned = caption.replace("[", "").replace("]", "")
    # 다중 공백 정리
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def fix_file(md_path: Path) -> tuple[int, int]:
    """파일 안 깨진 image markdown 수정. (changed, total) 반환."""
    text = md_path.read_text(encoding="utf-8")
    original = text

    # 깨진 패턴: ![text [placeholder text (path)
    # 즉 ! 다음 첫 [ 부터 다음 ]( 까지 caption 으로 보고 안의 [, ] 제거
    def fix_one(m: re.Match[str]) -> str:
        caption = m.group(1)
        path = m.group(2)
        new_caption = clean_caption(caption)
        return f"![{new_caption}]({path})"

    # 패턴 1: 정상 image (caption 에 [ 없음) — 변경 없음
    # 패턴 2: 깨진 image (caption 에 [ 있음) — 정리
    # 안전한 정규식: ! 다음 [ 부터 다음 ]( 까지 lazy match
    new_text = re.sub(
        r"!\[([^\n]*?)\]\(([^\n\)]+?)\)",
        fix_one,
        text,
    )

    # 추가: caption 안에 [ 만 있고 ] 없는 깨진 패턴 (사용자 스크린샷 케이스)
    # `![text [placeholder (다이어그램 N)](path)` 처럼 [ 가 추가된 경우
    # 위 정규식이 lazy 이므로 첫 ]( 만나면 잘림 → caption = "text [placeholder (다이어그램 N"
    # 그 안의 [ 도 clean_caption 에서 제거됨 → fix 됨

    if new_text != original:
        md_path.write_text(new_text, encoding="utf-8")
        # 변경된 image 카운트
        original_imgs = len(re.findall(r"!\[", original))
        return (1, original_imgs)
    return (0, 0)


def main():
    """root + docs/ 전 .md 파일 처리."""
    files = []
    files.extend(ROOT.glob("*.md"))
    for sub in ["docs", "docs/track", "docs/pkg", "docs/scenario", "docs/guide", "docs/module", "docs/other", "docs/meta"]:
        files.extend((ROOT / sub).glob("*.md"))

    changed_files = 0
    for f in files:
        if not f.is_file():
            continue
        changed, total = fix_file(f)
        if changed:
            changed_files += 1
            print(f"  ✓ {f.relative_to(ROOT)}")

    print(f"\n[fix_image_captions] {changed_files} 파일 수정")


if __name__ == "__main__":
    main()
