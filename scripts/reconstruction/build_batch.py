"""Validate and build a reconstruction batch with isolated target results."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]


def run(command: list[str]) -> tuple[int, str]:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return completed.returncode, (completed.stdout + completed.stderr).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/batches/m10-batch.json")
    parser.add_argument("--wave", choices=("A", "B", "ALL"), default="ALL")
    parser.add_argument("--stage", choices=("validate", "build", "full"), default="full")
    parser.add_argument("--entity-id", action="append", dest="entity_ids", help="Limit a retry to one or more manifest targets")
    parser.add_argument("--retry-count", type=int, default=0)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--fail-fast", action="store_true")
    mode.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    milestone = str(manifest.get("milestone", "M10")).lower()
    targets = [item for item in manifest["targets"] if args.wave == "ALL" or item["wave"] == args.wave]
    if args.entity_ids:
        targets = [item for item in targets if item["entity_id"] in set(args.entity_ids)]
    blender = None
    if args.stage != "validate":
        blender = subprocess.check_output([
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
            str(ROOT / "scripts/setup/find_blender.ps1"),
        ], cwd=ROOT, text=True).strip()
    results = []
    for target in targets:
        started = time.perf_counter()
        entity_id = target["entity_id"]
        package = ROOT / "data/reconstruction_packages" / entity_id
        stages = []
        commands = [("package", [sys.executable, str(ROOT / "scripts/reconstruction/validate_package.py"), str(package)])]
        if args.stage != "validate":
            build_command = [blender, "--background", "--factory-startup", "--python", str(ROOT / "blender/framework/building_builder.py"), "--", "--package", str(package)]
            if args.stage == "full":
                build_command.append("--render")
            commands.extend([
                ("build", build_command),
                ("glb", [blender, "--background", "--factory-startup", "--python", str(ROOT / "blender/scripts/validate_glb.py"), "--", "--path", str(ROOT / f"exports/glb/buildings/{entity_id}_lod1.glb"), "--metrics", str(ROOT / f"data/reports/buildings/{entity_id}.json"), "--entity-id", entity_id]),
                ("registry", [sys.executable, str(ROOT / "scripts/reconstruction/update_asset_registry.py"), entity_id]),
            ])
        status = "PASS"
        for label, command in commands:
            if label == "registry" and manifest.get("approval_policy") != "VISUAL_QA_REQUIRED":
                registry_path = ROOT / "data/assets/buildings.json"
                registry = json.loads(registry_path.read_text(encoding="utf-8"))
                registry["buildings"][entity_id]["available_lods"]["1"]["status"] = "APPROVED"
                registry["buildings"][entity_id]["lifecycle"]["lod1"] = "APPROVED"
                registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
            code, output = run(command)
            stages.append({"stage": label, "status": "PASS" if code == 0 else "FAIL", "diagnostic": output[-4000:]})
            if code:
                status = "FAIL"
                break
        elapsed = round(time.perf_counter() - started, 3)
        results.append({"entity_id": entity_id, "name": target["name"], "wave": target["wave"], "status": status, "elapsed_seconds": elapsed, "retry_count": args.retry_count, "stages": stages})
        print(f"{milestone.upper()}_TARGET {entity_id} {status} elapsed={elapsed}s")
        if status == "FAIL" and args.fail_fast:
            break
    report = {
        "schema_version": 1,
        "milestone": milestone.upper(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "fail-fast" if args.fail_fast else "continue-on-error",
        "wave": args.wave,
        "stage": args.stage,
        "results": results,
        "summary": {"passed": sum(item["status"] == "PASS" for item in results), "failed": sum(item["status"] == "FAIL" for item in results)},
    }
    suffix = f"-retry-{args.retry_count}" if args.entity_ids else ""
    output = ROOT / f"data/reports/{milestone}-batch-{args.wave.lower()}-{args.stage}{suffix}.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{milestone.upper()}_BATCH {'PASS' if not report['summary']['failed'] else 'FAIL'} report={output.relative_to(ROOT)}")
    raise SystemExit(1 if report["summary"]["failed"] else 0)


if __name__ == "__main__":
    main()
