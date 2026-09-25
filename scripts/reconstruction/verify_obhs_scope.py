"""Measure the One Bonifacio OSM mall polygon against named tower outlines."""

from __future__ import annotations

import json
from pathlib import Path

from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[2]
MALL = "osm:way:1078392706"
NEIGHBORS = {"The Suites": "osm:way:203910666", "PSE Tower": "osm:way:71598335"}


def main() -> None:
    source_path = ROOT / "data/processed/bgc-buildings.geojson"
    data = json.loads(source_path.read_text(encoding="utf-8"))
    wanted = {MALL, *NEIGHBORS.values()}
    features = {item["properties"]["id"]: item for item in data["features"]
                if item["properties"]["id"] in wanted}
    if set(features) != wanted:
        raise ValueError(f"missing OSM features: {sorted(wanted - set(features))}")
    mall = shape(features[MALL]["geometry"])
    overlaps = {}
    for label, source_id in NEIGHBORS.items():
        neighbor = shape(features[source_id]["geometry"])
        intersection = mall.intersection(neighbor)
        overlaps[label] = {"source_id": source_id, "intersection_m2": round(intersection.area, 2),
                           "neighbor_footprint_fraction": round(intersection.area / neighbor.area, 4)}
    payload = {"schema_version": 1, "source_data": str(source_path.relative_to(ROOT)).replace("\\", "/"),
               "source_entity_id": MALL, "mall_tags": features[MALL]["properties"].get("tags", {}),
               "mall_footprint_area_m2": round(mall.area, 2), "overlaps": overlaps,
               "interpretation": "OSM feature is tagged as a mall but spatially includes almost all of two tower outlines; exact retail component boundary is unresolved.",
               "evidence_state": "VERIFIED_GEOGRAPHIC"}
    output = ROOT / "data/reports/m16-obhs-scope.json"
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"OBHS_SCOPE: Suites={overlaps['The Suites']['neighbor_footprint_fraction']:.1%} PSE={overlaps['PSE Tower']['neighbor_footprint_fraction']:.1%} overlap")


if __name__ == "__main__":
    main()
