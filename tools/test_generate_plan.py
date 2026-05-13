#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_generate_plan_cli() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "generated_STL_중견.md"
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "generate_plan.py"),
                "--domain",
                "STL",
                "--scale",
                "중견",
                "--company",
                "동국산업",
                "--process",
                "냉간 압연",
                "--scenarios",
                "SCN-STL-04,SCN-STL-08,SCN-MLO-01",
                "--package",
                "pkg2",
                "--output",
                str(output),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        text = output.read_text(encoding="utf-8")
        assert text.startswith("# 동국산업 AI 사업계획서")
        for section in range(1, 10):
            assert f"## §{section}" in text
        assert "{{" not in text
        assert "[출처:" not in text
        assert "BLK-" not in text
        assert "[수치]" not in text


def main() -> int:
    try:
        test_generate_plan_cli()
    except AssertionError as error:
        print(error, file=sys.stderr)
        return 1
    print("tools/test_generate_plan.py PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
