"""Summarize M16–M18 gate state from committed registry and validation data.

This report deliberately distinguishes structural GLB validation from visual approval.
It never promotes draft assets or claims an unrun browser benchmark.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "data/reports"


def read(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write(name: str, value: dict) -> None:
    (REPORTS / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    selection = read("data/reports/m16-selected-buildings.json")
    selected = selection["targets"]
    ranking = read("data/reports/m16-priority-ranking.json")["candidates"]
    registry = read("data/assets/buildings.json")["buildings"]
    world = read("web/public/world/bgc-world.json")
    tiers = Counter(item["tier"] for item in ranking)
    costs = []
    for target in selected:
        entity_id = target["entity_id"]
        metric = read(f"data/reports/buildings/{entity_id}.json")
        status = registry[entity_id]["available_lods"]["1"]["status"]
        costs.append({
            "entity_id": entity_id,
            "name": target["name"],
            "wave": target["wave"],
            "asset": f"exports/glb/buildings/{entity_id}_lod1.glb",
            "glb_bytes": metric["file_size_bytes"],
            "triangles": metric["triangle_count"],
            "meshes": metric["mesh_count"],
            "materials": metric["material_count"],
            "draw_calls_approximation": metric["draw_call_approximation"],
            "structural_validation": metric["validation"],
            "visual_qa": status,
        })
    totals = {key: sum(item[key] for item in costs) for key in
              ("glb_bytes", "triangles", "meshes", "draw_calls_approximation")}
    now = datetime.now(timezone.utc).isoformat()
    write("m17-building-costs.json", {
        "schema_version": 1, "milestone": "M17", "generated_at": now,
        "scope": "Ten draft assets; not a simultaneous active-scene cost or browser measurement",
        "assets": costs, "totals": totals,
    })
    approved = [item for item in costs if item["visual_qa"] == "APPROVED"]
    pending = [item for item in costs if item["visual_qa"] != "APPROVED"]
    write("m17-summary.json", {
        "schema_version": 1, "milestone": "M17", "generated_at": now,
        "status": "FAIL" if pending else "PASS", "attempted": len(costs),
        "structurally_valid": sum(item["structural_validation"] == "PASS" for item in costs),
        "completed_visual_qa": len(approved), "deferred": len(pending),
        "approved_lod1_before": 7, "approved_lod1_after": len(world["detailed_assets"]),
        "lod0_count": 0, "wave_a_targets": 4, "wave_b_targets": 6,
        "critical_discrepancies_confirmed": 0,
        "major_discrepancies_confirmed_minimum": 2,
        "major_discrepancy_count_complete_audit": None,
        "qa_render_rounds": 12,
        "reference_comparison_passes": 0,
        "new_shared_geometry_primitives": 0,
        "target_specific_builder_modules": 0,
        "astra_tasks": 0,
        "gate_reason": "Architecture-level silhouette/facade mismatches remain; no reference-matched signoff or foreground LOD regression run.",
    })
    write("m18-performance.json", {
        "schema_version": 1, "milestone": "M18", "generated_at": now,
        "status": "NOT_GATED", "default_quality": "LOW", "full_shadows": "OPT_IN_UNBENCHMARKED",
        "before": {"source": "M15 foreground validation (not captured as a comparable machine-readable report)",
                   "initial_bytes": None, "walk_mean_fps": None, "walk_p1_fps": None,
                   "peak_draw_calls": None, "textures": None},
        "after": {"scenarios_measured": [], "initial_bytes": None, "walk_mean_fps": None,
                  "walk_p1_fps": None, "peak_draw_calls": None, "textures": None},
        "legacy_m11_all_loaded_reference": "data/reports/m11-browser-benchmark.json",
        "note": "M11 Chrome results are a different runtime/scenario and must not be presented as M15-to-M18 deltas.",
    })
    write("visual-fidelity-summary.json", {
        "schema_version": 1, "combined_milestone": "M16-M18 — Visual Fidelity Expansion",
        "generated_at": now, "phase": "PARTIAL", "m16": selection["evidence_gate"], "m17": "FAIL", "m18": "NOT_GATED",
        "candidates_evaluated": len(ranking), "tier_counts": dict(tiers),
        "targets_selected": len(selected),
        "evidence_ready_with_gaps": sum(item["evidence_readiness"] == "READY_WITH_GAPS" for item in selected),
        "not_ready": sum(item["evidence_readiness"] == "NOT_READY" for item in selected),
        "lod1_published": len(world["detailed_assets"]),
        "drafts_excluded_from_runtime": len(pending),
        "grounding_audit": "PARTIAL",
        "visual_qa": "FAIL", "lod_qa": "NOT_RUN_FOR_NEW_ASSETS",
        "dominant_remaining_weakness": "Priority landmarks lack reference-matched massing and facade reconstruction.",
    })
    print(f"VISUAL_REPORT: M16={len(ranking)} candidates, M17={len(pending)} deferred, published LOD1={len(world['detailed_assets'])}, draft bytes={totals['glb_bytes']}")


if __name__ == "__main__":
    main()
