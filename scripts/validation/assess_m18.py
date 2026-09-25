"""Assess matched foreground M18 captures and refresh release-gate reports."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ("AERIAL", "HIGH_STREET_INSPECT", "HIGH_STREET_WALK", "TOUR", "SOUTH_STREET")
QUALITIES = ("LEGACY", "LOW", "FULL")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    captures = read(ROOT / "data/reports/m18-foreground-captures.json")
    rows = {(row["scenario"], row["quality"]): row for row in captures["rows"]}
    expected = {(scenario, quality) for scenario in SCENARIOS for quality in QUALITIES}
    if len(captures["rows"]) != len(expected) or set(rows) != expected:
        raise ValueError("M18 captures must contain exactly one row for each of 15 matched scenarios")
    for row in rows.values():
        if any(row.get(key) is None for key in ("mean_fps", "median_fps", "p1_fps", "load_duration_ms",
                                                 "initial_transfer_bytes", "streamed_transfer_bytes", "calls",
                                                 "triangles", "geometries", "textures", "active_tiles", "active_lod1",
                                                 "environment_groups")):
            raise ValueError(f"Incomplete M18 capture: {row['scenario']} {row['quality']}")
    comparison = {}
    low_pass = True
    full_p1_failures = []
    for scenario in SCENARIOS:
        legacy, low, full = (rows[scenario, q] for q in QUALITIES)
        median_delta = (low["median_fps"] / legacy["median_fps"] - 1) * 100
        p1_delta = (low["p1_fps"] / legacy["p1_fps"] - 1) * 100
        calls_delta = (low["calls"] / legacy["calls"] - 1) * 100
        full_p1_delta = (full["p1_fps"] / low["p1_fps"] - 1) * 100
        same_load = all(low[k] == legacy[k] == full[k] for k in
                        ("initial_transfer_bytes", "streamed_transfer_bytes",
                         "initial_decoded_bytes", "streamed_decoded_bytes", "active_lod1"))
        if median_delta < -25 or p1_delta < -15 or calls_delta > 25 or not same_load:
            low_pass = False
        if full_p1_delta < -15:
            full_p1_failures.append(scenario)
        comparison[scenario] = {"legacy_median_fps": legacy["median_fps"], "low_median_fps": low["median_fps"],
                                "full_median_fps": full["median_fps"],
                                "low_median_delta_pct": round(median_delta, 2),
                                "low_p1_delta_pct": round(p1_delta, 2),
                                "low_draw_call_delta_pct": round(calls_delta, 2),
                                "full_p1_vs_low_delta_pct": round(full_p1_delta, 2),
                                "transfer_and_lod1_matched": same_load}
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip() or None
    git_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip() or None
    full_status = "REJECTED" if full_p1_failures else "PASS"
    status = "PASS" if low_pass else "FAIL"
    generated_at = datetime.now(timezone.utc).isoformat()
    report = {"schema_version": 1, "milestone": "M18A", "generated_at": generated_at,
              "branch": branch, "git_sha": git_sha,
              "status": status, "default_quality": "LOW", "legacy_mode": "PASS", "low_mode": "PASS" if low_pass else "FAIL",
              "full_mode": full_status, "full_shadows": "DIAGNOSTICS_ONLY" if full_p1_failures else "AVAILABLE",
              "capture_source": "data/reports/m18-foreground-captures.json",
              "capture_time": captures["captured_at"], "matched_scenarios": list(SCENARIOS),
              "comparison": comparison, "full_p1_failures": full_p1_failures,
              "limits": captures["measurement_limits"],
              "note": "M11 all-loaded measurements are not a comparable baseline. LEGACY here is the matched pre-M18 visual approximation on the current runtime."}
    write(ROOT / "data/reports/m18-performance.json", report)
    fidelity_path = ROOT / "data/reports/visual-fidelity-summary.json"
    fidelity = read(fidelity_path)
    if fidelity.get("m16") != "PASS" or fidelity.get("m17") != "CLOSED_WITH_DEFERMENT":
        raise ValueError("M16/M17 release prerequisites are not closed")
    fidelity.update(generated_at=generated_at, branch=branch, git_sha=git_sha,
                    combined_milestone="M17C-M18A — Visual Fidelity Closure",
                    phase="PASS_WITH_DOCUMENTED_LANDMARK_DEFERMENT" if low_pass else "FAIL", m18=status,
                    visual_system=f"LOW_{'ACCEPTED' if low_pass else 'FAILED'}_FULL_{full_status}",
                    dominant_remaining_weakness="PSE pointed upper silhouette and body/frontpiece relationship remain unresolved.")
    write(fidelity_path, fidelity)
    print(f"M18A: LOW {status}; FULL {full_status} ({', '.join(full_p1_failures)})")
    if not low_pass:
        raise ValueError("M18 acceptance failed: LOW exceeded the measured limits")


if __name__ == "__main__":
    main()
