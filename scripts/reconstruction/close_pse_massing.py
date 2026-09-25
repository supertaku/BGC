"""Record bounded PSE round 3 and defer the unapproved asset for v1.

Run only after the part-analysis driven PSE build and source-image review.
No asset registry or production manifest is modified.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from review_m17 import main as refresh_review


ROOT = Path(__file__).resolve().parents[2]
ENTITY = "bgc_m17_0003"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    report_path = ROOT / "data/reports/m17-reference-qa.json"
    qa = read(report_path)
    target = next(record for record in qa["buildings"] if record["entity_id"] == ENTITY)
    render_root = ROOT / "blender/renders" / ENTITY
    by_id = {record["reference_id"]: record for record in read(
        ROOT / "data/reconstruction_packages" / ENTITY / "references.json")["records"]}
    pairs = [pair for pair in target["reference_comparisons"] if pair.get("round") != 3]
    for suffix in ("044a", "008a"):
        original = render_root / f"qa-source-{suffix}.png"
        if not original.exists():
            raise FileNotFoundError(original)
        snapshot = render_root / f"qa-source-{suffix}-round3.png"
        if not snapshot.exists():
            shutil.copy2(original, snapshot)
        ref_id = f"ref:m16r:architect-pse:{suffix}"
        pairs.append({
            "round": 3, "reference_id": ref_id,
            "source_url": by_id[ref_id]["url"],
            "render_path": str(snapshot.relative_to(ROOT)).replace("\\", "/"),
            "camera_id": f"qa:{ENTITY}:source:{suffix}",
            "result": "FAIL",
            "discrepancy_record": f"data/reports/m17-reference-qa.json#{ENTITY}",
            "note": "Partitioned OSM masses remove coincident volume, but the flat twin upper silhouette and relative facade widths still differ materially from the architect view; cameras remain approximate.",
        })
    target["reference_comparisons"] = pairs
    descriptions = {
        "SILHOUETTE": "Architect street view shows two pointed, separated upper forms; round 3 flat caps still produce a broad stepped block.",
        "MAJOR_VOLUME": "Polygon partition removes exact nested overlap, but the inferred body/frontpiece proportions remain visually inconsistent with the source views.",
        "ROOF": "Upper geometry remains unsupported beyond the source-visible pointed silhouette; a confident component-specific profile cannot be recovered from current camera matches.",
        "FACADE_COMPOSITION": "Massing-only asset omits the source-described inflected glazing and deep vertical ribs; principal mapped edge is unresolved.",
    }
    for discrepancy in target["discrepancies"]:
        if discrepancy["aspect"] in descriptions:
            discrepancy.update(severity="MAJOR", disposition="OPEN",
                               description=descriptions[discrepancy["aspect"]])
    target.update(disposition="DEFERRED_VISUAL_REFINEMENT", builder_status="PASS",
                  glb_structural_status="PASS", manual_reviewer_signoff=None,
                  visual_status="DEFERRED_VISUAL_REFINEMENT", massing_rounds_added=1,
                  facade_rounds_added=0)
    write(report_path, qa)

    metrics = read(ROOT / "data/reports/buildings" / f"{ENTITY}.json")
    costs_path = ROOT / "data/reports/m17-building-costs.json"
    costs = read(costs_path)
    item = next(asset for asset in costs["assets"] if asset["entity_id"] == ENTITY)
    item.update(glb_bytes=metrics["file_size_bytes"], triangles=metrics["triangle_count"],
                meshes=metrics["mesh_count"], materials=metrics["material_count"],
                draw_calls_approximation=metrics["draw_call_approximation"],
                structural_validation=metrics["validation"],
                visual_qa="DEFERRED_VISUAL_REFINEMENT", draft_phase="MASSING_ROUND_3")
    for key in ("glb_bytes", "triangles", "meshes", "draw_calls_approximation"):
        costs["totals"][key] = sum(asset[key] for asset in costs["assets"])
    costs["generated_at"] = datetime.now(timezone.utc).isoformat()
    write(costs_path, costs)

    batch_path = ROOT / "data/batches/m17-batch.json"
    batch = read(batch_path)
    batch["targets"][0]["disposition"] = "DEFERRED_VISUAL_REFINEMENT"
    write(batch_path, batch)
    refresh_review()


if __name__ == "__main__":
    main()
