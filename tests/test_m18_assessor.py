"""The M18 assessor must not encode a required FULL rejection."""

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("assess_m18", ROOT / "scripts/validation/assess_m18.py")
assert SPEC and SPEC.loader
ASSESSOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ASSESSOR)


def fixture_root(tmp_path, monkeypatch):
    reports = tmp_path / "data/reports"
    reports.mkdir(parents=True)
    for name in ("m18-foreground-captures.json", "visual-fidelity-summary.json"):
        (reports / name).write_bytes((ROOT / "data/reports" / name).read_bytes())
    monkeypatch.setattr(ASSESSOR, "ROOT", tmp_path)
    return reports


def test_full_pass_is_allowed(tmp_path, monkeypatch):
    reports = fixture_root(tmp_path, monkeypatch)
    path = reports / "m18-foreground-captures.json"
    captures = json.loads(path.read_text())
    low = {row["scenario"]: row for row in captures["rows"] if row["quality"] == "LOW"}
    for row in captures["rows"]:
        if row["quality"] == "FULL":
            row["p1_fps"] = low[row["scenario"]]["p1_fps"]
    path.write_text(json.dumps(captures))
    ASSESSOR.main()
    assert json.loads((reports / "m18-performance.json").read_text())["full_mode"] == "PASS"


def test_low_failure_fails_acceptance(tmp_path, monkeypatch):
    reports = fixture_root(tmp_path, monkeypatch)
    path = reports / "m18-foreground-captures.json"
    captures = json.loads(path.read_text())
    low = next(row for row in captures["rows"] if row["quality"] == "LOW")
    low["median_fps"] = 1
    path.write_text(json.dumps(captures))
    with pytest.raises(ValueError, match="LOW exceeded"):
        ASSESSOR.main()
    assert json.loads((reports / "m18-performance.json").read_text())["status"] == "FAIL"
