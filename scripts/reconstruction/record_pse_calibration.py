"""Record the first PSE massing comparison without granting visual approval."""

from __future__ import annotations

import html
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
ENTITY = "bgc_m17_0003"
RENDERS = ROOT / "blender/renders" / ENTITY
QA_PATH = ROOT / "data/reports/m17-reference-qa.json"


def main() -> None:
    references = json.loads((ROOT / "data/reconstruction_packages" / ENTITY / "references.json").read_text(encoding="utf-8"))
    by_id = {item["reference_id"]: item for item in references["records"]}
    pairs = []
    for suffix in ("044a", "008a"):
        ref_id = f"ref:m16r:architect-pse:{suffix}"
        render = RENDERS / f"qa-source-{suffix}.png"
        if not render.exists():
            raise FileNotFoundError(render)
        snapshot = RENDERS / f"qa-source-{suffix}-round1.png"
        if not snapshot.exists():
            shutil.copy2(render, snapshot)
        pairs.append({"round": 1, "reference_id": ref_id, "source_url": by_id[ref_id]["url"],
                      "render_path": str(snapshot.relative_to(ROOT)).replace("\\", "/"),
                      "camera_id": f"qa:{ENTITY}:source:{suffix}",
                      "result": "FAIL", "discrepancy_record": f"data/reports/m17-reference-qa.json#{ENTITY}",
                      "note": "Coarse massing render lacks source-visible upper roof shaping and principal facade articulation. Camera positions are approximate."})
        spec = json.loads((ROOT / "data/reconstruction_packages" / ENTITY / "reconstruction_spec.json").read_text(encoding="utf-8"))
        if spec.get("landmark_parameters", {}).get("roof_slope_m", 0) > 0:
            refined = RENDERS / f"qa-source-{suffix}-round2.png"
            if not refined.exists():
                shutil.copy2(render, refined)
            pairs.append({"round": 2, "reference_id": ref_id, "source_url": by_id[ref_id]["url"],
                          "render_path": str(refined.relative_to(ROOT)).replace("\\", "/"),
                          "camera_id": f"qa:{ENTITY}:source:{suffix}",
                          "result": "FAIL", "discrepancy_record": f"data/reports/m17-reference-qa.json#{ENTITY}",
                          "note": "Estimated 4 m roof slope improved the near roof edge but the source-visible twin upper shaping and volume articulation still differ."})
    html_path = RENDERS / "comparison.html"
    cards = []
    for pair in pairs:
        suffix = pair["reference_id"].split(":")[-1]
        round_number = pair["round"]
        render_name = Path(pair["render_path"]).name
        cards.append(f'<section><h2>{suffix} — round {round_number}, approximate camera</h2><div class="pair">'
                     f'<figure><img src="{html.escape(pair["source_url"])}" alt="Research-only architect reference"><figcaption>Architect reference, research only</figcaption></figure>'
                     f'<figure><img src="{html.escape(render_name)}" alt="PSE massing render"><figcaption>Generated massing render, round {round_number}</figcaption></figure>'
                     f'</div></section>')
    html_path.write_text("<!doctype html><meta charset='utf-8'><title>PSE massing QA</title>"
                         "<style>body{font:16px system-ui;background:#15202a;color:white;margin:24px}"
                         ".pair{display:flex;gap:16px;align-items:flex-start}figure{width:49%;margin:0}"
                         "img{width:100%;height:600px;object-fit:contain;background:#26343e}"
                         "figcaption{padding:8px}h2{margin-top:40px}</style>"
                         "<h1>PSE Tower — massing round 1</h1><p>Remote architect images are research-only and are not stored here. Camera matches are approximate; this is not signoff.</p>"
                         + "".join(cards), encoding="utf-8")
    qa = json.loads(QA_PATH.read_text(encoding="utf-8"))
    record = next(item for item in qa["buildings"] if item["entity_id"] == ENTITY)
    record["builder_status"] = "PASS"
    record["glb_structural_status"] = "PASS"
    record["reference_comparisons"] = pairs
    for item in record["discrepancies"]:
        if item["aspect"] == "SILHOUETTE":
            item.update(severity="MAJOR", disposition="OPEN",
                        description="Second massing render adds a 4 m estimated slope, but both architect views still show more distinct twin upper shapes.")
        elif item["aspect"] == "MAJOR_VOLUME":
            item.update(severity="MAJOR", disposition="OPEN",
                        description="OSM overlapping tower parts render as a thick continuous block; frontpiece and body separation need refinement.")
        elif item["aspect"] == "ROOF":
            item.update(severity="MAJOR", disposition="OPEN",
                        description="Estimated roof slope does not yet match the upper silhouette in source photographs.")
        elif item["aspect"] == "FACADE_COMPOSITION":
            item.update(severity="MAJOR", disposition="OPEN",
                        description="Massing-only draft intentionally omits the architect-documented inflected glazing and vertical ribs.")
    record["visual_status"] = "PENDING_VISUAL_QA"
    record["manual_reviewer_signoff"] = None
    QA_PATH.write_text(json.dumps(qa, indent=2) + "\n", encoding="utf-8")
    metrics = json.loads((ROOT / "data/reports/buildings" / f"{ENTITY}.json").read_text(encoding="utf-8"))
    costs_path = ROOT / "data/reports/m17-building-costs.json"
    costs = json.loads(costs_path.read_text(encoding="utf-8"))
    item = next(asset for asset in costs["assets"] if asset["entity_id"] == ENTITY)
    item.update(glb_bytes=metrics["file_size_bytes"], triangles=metrics["triangle_count"],
                meshes=metrics["mesh_count"], materials=metrics["material_count"],
                draw_calls_approximation=metrics["draw_call_approximation"],
                structural_validation=metrics["validation"], visual_qa="PENDING_VISUAL_QA",
                draft_phase="MASSING_CALIBRATION_ROUND_2")
    for key in ("glb_bytes", "triangles", "meshes", "draw_calls_approximation"):
        costs["totals"][key] = sum(asset[key] for asset in costs["assets"])
    costs_path.write_text(json.dumps(costs, indent=2) + "\n", encoding="utf-8")
    print(f"PSE_CALIBRATION: FAIL_MASSING rounds={max(pair['round'] for pair in pairs)} comparison={html_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
