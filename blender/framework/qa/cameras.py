"""Deterministic diagnostic camera creation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class QACameraSpec:
    camera_id: str
    kind: str
    location: tuple[float, float, float]
    target: tuple[float, float, float]
    lens_mm: float
    filename: str
    match: str
    reference_ids: tuple[str, ...] = ()


def create_qa_cameras(scene_tools, specs: list[QACameraSpec], render_dir: Path | None = None) -> list[dict]:
    records = []
    for spec in specs:
        camera = scene_tools.add_camera(spec.camera_id, spec.location, spec.target, lens=spec.lens_mm)
        camera["qa_kind"] = spec.kind
        camera["camera_match"] = spec.match
        camera["deterministic"] = True
        camera["exportable"] = False
        if render_dir is not None:
            scene_tools.render_png(render_dir / spec.filename)
        record = asdict(spec)
        record["render"] = str((render_dir / spec.filename) if render_dir else spec.filename)
        records.append(record)
    return records

