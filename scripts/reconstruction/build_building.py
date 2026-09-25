"""One-command staged reconstruction entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def run(command: list[str], label: str) -> None:
    print(f"{label} START")
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode:
        raise SystemExit(f"{label}_ERROR: exit {completed.returncode}")
    print(f"{label} PASS")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--stage", choices=("validate", "build", "render", "full"), default="full")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    package = args.package.resolve()
    entity_id = package.name
    if args.clean:
        for generated in (
            ROOT / "blender" / "scenes" / f"{entity_id}-lod1.blend",
            ROOT / "exports" / "glb" / "buildings" / f"{entity_id}_lod1.glb",
            ROOT / "data" / "reports" / "buildings" / f"{entity_id}-dry-run.json",
        ):
            if generated.is_file():
                generated.unlink()
        print("CLEAN PASS generated_outputs_only=true")
    if args.stage in {"validate", "full", "build", "render"}:
        run([sys.executable, str(ROOT / "scripts" / "reconstruction" / "validate_package.py"), str(package)], "PACKAGE")
    if entity_id.startswith("bgc_m17_"):
        from evidence_gate import assess
        result = assess(package)
        if result["status"] != "READY_FOR_VISUAL_RECONSTRUCTION":
            raise SystemExit("EVIDENCE_GATE_ERROR: " + json.dumps(result["reasons"]))
    if args.stage == "validate":
        return
    blender = subprocess.check_output([
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        str(ROOT / "scripts" / "setup" / "find_blender.ps1")
    ], cwd=ROOT, text=True).strip()
    command = [blender, "--background", "--factory-startup", "--python", str(ROOT / "blender" / "framework" / "building_builder.py"), "--", "--package", str(package)]
    if args.stage in {"render", "full"}:
        command.append("--render")
    run(command, "BUILD")
    if args.stage == "full":
        run([blender, "--background", "--factory-startup", "--python",
             str(ROOT / "blender/scripts/validate_glb.py"), "--",
             "--path", str(ROOT / "exports/glb/buildings" / f"{entity_id}_lod1.glb"),
             "--metrics", str(ROOT / "data/reports/buildings" / f"{entity_id}.json"),
             "--entity-id", entity_id], "GLB")


if __name__ == "__main__":
    main()
