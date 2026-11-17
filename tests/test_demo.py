from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_offline_demo_loads_fixture_and_exports_report(tmp_path: Path) -> None:
    output = tmp_path / "demo-report.md"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_demo.py"), "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "OFFLINE FIXTURE DEMO" in result.stdout
    assert "OFFLINE KEYWORD SEARCH" in result.stdout
    assert "does not call Whisper" in result.stdout
    assert output.is_file()
    assert "Mobile app launch planning" in output.read_text(encoding="utf-8")
