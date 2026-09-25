"""Create a separate, fail-closed reference QA audit of current M17 drafts.

The builder cannot grant visual approval. An approved entry needs explicit
reference/render pairs, a recorded reviewer decision, and no open critical or
major discrepancy for evidence-covered aspects.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from evidence_gate import assess


ROOT = Path(__file__).resolve().parents[2]
ASPECTS = ("SILHOUETTE", "HEIGHT", "MAJOR_VOLUME", "SETBACK", "CURVATURE",
           "FACADE_COMPOSITION", "ROOF", "ENTRANCE", "MATERIAL", "GROUND_RELATIONSHIP")
KNOWN_DRAFT_DISCREPANCIES = {
    "bgc_m17_0001": [("MAJOR_VOLUME", "CRITICAL", "OSM mall polygon includes 98.9% of Suites and 99.5% of PSE footprints; retail boundary unresolved")],
    "bgc_m17_0002": [("CURVATURE", "MAJOR", "Generic draft has no architect-described curved tower form")],
    "bgc_m17_0003": [("FACADE_COMPOSITION", "MAJOR", "Generic draft uses horizontal all-edge bands in place of inflected glazing and vertical ribs")],
    "bgc_m17_0004": [("HEIGHT", "MAJOR", "Existing draft GLB uses 114.7 m OSM height; package now decides 136 m from SOM")],
}


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    selection = read(ROOT / "data/reports/m16-selected-buildings.json")
    batch = read(ROOT / "data/batches/m17-batch.json")
    active_ids = {target["entity_id"] for target in batch["targets"]}
    selected_ids = set(selection["final_selected_target_ids"])
    if active_ids != selected_ids:
        raise ValueError(f"M17 active batch differs from M16R final selection: {active_ids ^ selected_ids}")
    generated_at = datetime.now(timezone.utc).isoformat()
    out = ROOT / "data/reports/m17-reference-qa.json"
    previous = {item["entity_id"]: item for item in read(out).get("buildings", [])} if out.exists() else {}
    records = []
    for target in selection["targets"]:
        entity = target["entity_id"]
        package = ROOT / "data/reconstruction_packages" / entity
        evidence = assess(package)
        known = {aspect: (severity, detail) for aspect, severity, detail
                 in KNOWN_DRAFT_DISCREPANCIES.get(entity, [])}
        discrepancies = []
        for aspect in ASPECTS:
            severity, detail = known.get(aspect, ("INFO", "Reference-matched comparison not completed"))
            discrepancies.append({"aspect": aspect, "severity": severity,
                                  "disposition": "OPEN" if aspect in known else "NOT_EVIDENCED",
                                  "description": detail})
        old = previous.get(entity, {})
        record = {"entity_id": entity, "source_entity_id": target["source_entity_id"],
                  "batch_scope": "ACTIVE_BATCH" if entity in active_ids else "DEFERRED_BACKLOG",
                  "disposition": old.get("disposition", target.get("disposition")),
                  "evidence_status": evidence["status"], "builder_status": "DRAFT_ONLY",
                  "glb_structural_status": "PASS_LEGACY_DRAFT",
                  "reference_comparisons": old.get("reference_comparisons", []),
                  "discrepancies": old.get("discrepancies", discrepancies)
                      if old.get("manual_reviewer_signoff") or old.get("reference_comparisons") else discrepancies,
                  "manual_reviewer_signoff": old.get("manual_reviewer_signoff"),
                  "visual_status": "PENDING_VISUAL_QA"}
        for key in ("builder_status", "glb_structural_status"):
            if old.get(key) in {"PASS", "FAIL"}:
                record[key] = old[key]
        open_severe = [d for d in record["discrepancies"] if d.get("disposition") == "OPEN"
                       and d.get("severity") in {"CRITICAL", "MAJOR"}]
        comparisons = record["reference_comparisons"]
        comparison_ok = bool(comparisons) and all(
            c.get("reference_id") and c.get("render_path") and c.get("discrepancy_record")
            and c.get("result") == "PASS" for c in comparisons)
        gates = {
            "evidence": evidence["status"] == "READY_FOR_VISUAL_RECONSTRUCTION",
            "build": record["builder_status"] == "PASS",
            "glb": record["glb_structural_status"] == "PASS",
            "reference_comparison": comparison_ok,
            "discrepancies": not open_severe,
            "independent_signoff": isinstance(record["manual_reviewer_signoff"], dict)
                and record["manual_reviewer_signoff"].get("decision") == "APPROVED"
                and bool(record["manual_reviewer_signoff"].get("reviewer"))
                and bool(record["manual_reviewer_signoff"].get("reviewed_at")),
        }
        record["approval_gates"] = gates
        record["approval_gate"] = "PASS" if all(gates.values()) else "BLOCKED"
        record["visual_status"] = ("APPROVED" if all(gates.values()) else
                                   "DEFERRED_VISUAL_REFINEMENT" if record["disposition"] == "DEFERRED_VISUAL_REFINEMENT" else
                                   "PENDING_VISUAL_QA")
        records.append(record)
    active_records = [record for record in records if record["batch_scope"] == "ACTIVE_BATCH"]
    deferred_records = [record for record in records if record["batch_scope"] == "DEFERRED_BACKLOG"]
    payload = {"schema_version": 1, "generated_at": generated_at,
               "policy": "An APPROVED target requires evidence readiness, reference/render comparisons, separate reviewer signoff, and zero open CRITICAL or MAJOR discrepancies.",
               "research_media_policy": "Research-only source images stay remote; comparison artifacts may contain render and metadata links only until rights permit redistribution.",
               "buildings": records,
               "active_target_ids": sorted(active_ids),
               "deferred_target_ids": [record["entity_id"] for record in deferred_records],
               "active_approved_count": sum(item["visual_status"] == "APPROVED" for item in active_records),
               "approved_count": sum(item["visual_status"] == "APPROVED" for item in active_records)}
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    summary_path = ROOT / "data/reports/m17-summary.json"
    summary = read(summary_path)
    open_critical = sum(d["severity"] == "CRITICAL" and d["disposition"] == "OPEN"
                        for r in active_records for d in r["discrepancies"])
    open_major = sum(d["severity"] == "MAJOR" and d["disposition"] == "OPEN"
                     for r in active_records for d in r["discrepancies"])
    deferred_closure = all(r["visual_status"] == "DEFERRED_VISUAL_REFINEMENT" for r in active_records)
    summary.update(status="CLOSED_WITH_DEFERMENT" if deferred_closure else "FAIL",
                   recovery_state="CLOSED_FOR_V1" if deferred_closure else "IN_PROGRESS",
                   completed_visual_qa=payload["approved_count"],
                   final_evidence_ready_count=len(active_records),
                   active_target_ids=sorted(active_ids), deferred_target_ids=payload["deferred_target_ids"],
                   active_draft_count=len(active_records), deferred_backlog_count=len(deferred_records),
                   draft_count=len(active_records),
                   confirmed_open_critical=open_critical, confirmed_open_major=open_major,
                   critical_discrepancies_confirmed=open_critical,
                   major_discrepancies_confirmed_minimum=open_major,
                   target_specific_builder_modules=1,
                   reference_comparison_passes=sum(bool(r["approval_gates"]["reference_comparison"]) for r in active_records),
                   gate_reason="PSE remained visually discrepant after bounded massing refinement; its draft stays unpublished." if deferred_closure else "No target has passed explicit evidence coverage, camera matching, reference comparison, and independent visual review.")
    summary["generated_at"] = generated_at
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    fidelity_path = ROOT / "data/reports/visual-fidelity-summary.json"
    fidelity = read(fidelity_path)
    m18_accepted = fidelity.get("m18") == "PASS"
    fidelity.update(phase="PASS_WITH_DOCUMENTED_LANDMARK_DEFERMENT" if deferred_closure and m18_accepted else
                    "M17_CLOSED_M18_PENDING" if deferred_closure else "RECOVERY_IN_PROGRESS", m16=selection["evidence_gate"],
                    m17="CLOSED_WITH_DEFERMENT" if deferred_closure else "FAIL",
                    targets_selected=len(selection.get("final_selected_target_ids", [])),
                    candidates_in_review=len(active_records), deferred_backlog_count=len(deferred_records),
                    evidence_ready_with_gaps=0,
                    not_ready=sum(r["evidence_status"] != "READY_FOR_VISUAL_RECONSTRUCTION" for r in active_records), visual_qa="DEFERRED_VISUAL_REFINEMENT" if deferred_closure else "PENDING_VISUAL_QA",
                    lod_qa="NOT_RUN_FOR_NEW_ASSETS")
    fidelity["generated_at"] = generated_at
    fidelity_path.write_text(json.dumps(fidelity, indent=2) + "\n", encoding="utf-8")
    print(f"M17_REFERENCE_QA: {len(records)} candidates, {payload['approved_count']} approved")


if __name__ == "__main__":
    main()
