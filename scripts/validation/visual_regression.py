"""Generate tolerant image-difference metrics and side-by-side QA contact sheets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageStat


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--warning-threshold", type=float, default=0.08)
    args = parser.parse_args()
    pairs = []
    args.output.mkdir(parents=True, exist_ok=True)
    for baseline_path in sorted(args.baseline.glob("*.png")):
        current_path = args.current / baseline_path.name
        if not current_path.is_file():
            pairs.append({"camera": baseline_path.stem, "status": "FAIL", "reason": "missing current render"})
            continue
        baseline = Image.open(baseline_path).convert("RGB")
        current = Image.open(current_path).convert("RGB")
        if baseline.size != current.size:
            pairs.append({"camera": baseline_path.stem, "status": "FAIL", "reason": "dimension mismatch"})
            continue
        difference = ImageChops.difference(baseline, current)
        mean = sum(ImageStat.Stat(difference).mean) / (3 * 255)
        sheet = Image.new("RGB", (baseline.width * 2, baseline.height))
        sheet.paste(baseline, (0, 0))
        sheet.paste(current, (baseline.width, 0))
        sheet.save(args.output / f"{baseline_path.stem}-pair.png")
        pairs.append({"camera": baseline_path.stem, "mean_absolute_difference": round(mean, 6), "status": "WARNING" if mean > args.warning_threshold else "PASS"})
    status = "FAIL" if any(item["status"] == "FAIL" for item in pairs) else ("WARNING" if any(item["status"] == "WARNING" for item in pairs) else "PASS")
    report = {"schema_version": 1, "status": status, "interpretation": "Change detector only; architectural correctness requires evidence-grounded visual review.", "pairs": pairs}
    (args.output / "visual-regression.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"VISUAL_REGRESSION: {status} pairs={len(pairs)}")
    raise SystemExit(1 if status == "FAIL" else 0)


if __name__ == "__main__":
    main()
