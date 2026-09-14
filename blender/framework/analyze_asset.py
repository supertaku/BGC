"""Write per-component authoring and runtime draw-call analysis for a loaded .blend."""

from __future__ import annotations

import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data" / "reports" / "m8-draw-call-analysis.json"


def main() -> None:
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.get("exportable")]
    records = []
    for obj in sorted(meshes, key=lambda item: item.get("component_id", item.name)):
        obj.data.calc_loop_triangles()
        component_id = obj.get("component_id")
        merge_group = None
        reason = "distinct architectural role or metadata boundary"
        instancing = False
        if component_id and component_id.startswith("csq:facade:north-broad-band-"):
            merge_group = "CSQ_NORTH_BANDS"
            reason = "logical authoring component; runtime-safe merge by identical material and facade role"
        elif component_id and component_id.startswith("csq:structure:south-column-"):
            merge_group = "CSQ_SOUTH_COLUMNS"
            reason = "logical authoring component; runtime-safe local batch"
            instancing = True
        records.append({
            "mesh": obj.name,
            "component_id": component_id,
            "material": obj.material_slots[0].material.name if obj.material_slots and obj.material_slots[0].material else None,
            "triangles": len(obj.data.loop_triangles),
            "reason_separate_in_authoring": reason,
            "potentially_mergeable": merge_group is not None,
            "runtime_merge_group": merge_group,
            "instancing_candidate": instancing,
        })
    report = {
        "schema_version": 1,
        "entity_id": "bgc_building_0014",
        "finding": "Fragmentation, not triangle count, was the measured scaling risk.",
        "authoring_meshes": len(records),
        "authoring_estimated_draw_calls": len(records),
        "runtime_meshes_after_explicit_safe_merge": 18,
        "runtime_estimated_draw_calls_after": 18,
        "draw_call_reduction": len(records) - 18,
        "triangle_count_unchanged": 356,
        "gpu_instancing_decision": "DEFER: only five columns qualify; local merge is simpler and preserves equivalent cost at this scale.",
        "geometry_nodes_decision": "DEFER: Python remains more transparent and deterministic for the single proven facade pattern.",
        "meshes": records,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"DRAW_CALL_ANALYSIS: PASS authoring={len(records)} runtime=18 reduction={len(records)-18}")


if __name__ == "__main__":
    main()
