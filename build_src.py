#!/usr/bin/env python3
"""build_src.py — 원본 .md 파일을 영문 slug 경로로 docs/ 하위에 복사.

사용처:
- mkdocs build/serve 직전 실행
- GitHub Actions deploy.yml 의 빌드 단계 직전

원본 .md 는 워크스페이스 운영 자산이므로 수정하지 않음.
docs/ 하위는 매번 재생성 (기존 내용 덮어쓰기).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.resolve()
SLUG_MAP_PATH = ROOT / "slug_map.yml"
DOCS_DIR = ROOT / "docs"


def load_slug_map() -> dict[str, str]:
    with SLUG_MAP_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    slug_map = load_slug_map()

    # docs/ 하위의 자동 생성 디렉토리만 정리 (수동 신설 파일 보존)
    auto_dirs = ["track", "pkg", "guide", "scenario", "module", "other", "meta"]
    for d in auto_dirs:
        target = DOCS_DIR / d
        if target.exists():
            shutil.rmtree(target)

    copied = 0
    missing = []
    for src_name, dst_rel in slug_map.items():
        src = ROOT / src_name
        dst = DOCS_DIR / dst_rel

        if not src.exists():
            missing.append(src_name)
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1

    print(f"[build_src] 복사 완료: {copied} 파일")
    if missing:
        print(f"[build_src] 경고 — 부재 원본: {len(missing)} 종")
        for m in missing:
            print(f"  - {m}")


if __name__ == "__main__":
    main()
