# M23 — High Street Central

A local terraced amphitheater, water center, radial paving, stairs and outer grade apron replace the flat preview. The shared GroundSampler registers triangulated height surfaces while the package is active, and Walk samples these surfaces every frame. Local terrain falls back to the existing city ground when unloaded. Mapped low-detail props intersecting raised terrain are temporarily suppressed; canonical mapped records are retained.

## Evidence and limits

The Crearis reference establishes amphitheater, water, plaza and garden identity. All elevations and detailed arrangement are estimated, including the apron gradient; no accessible-gradient certification is claimed. Constrained triangulation and a boundary tolerance repair the gaps seen in earlier fixed-camera iterations. The intrusive inner ramp wedge was removed.

## Reproduce

Run `scripts/m23/run.ps1 -Render` from the repository. Source geometry is in `scripts/m23/build.py`; runtime packages are in `web/public/world/detail/m23`; fixed cameras and hashes are in `data/reports/m23`. Generated Blender and GLB outputs can be recreated.

## Validation

See `data/reports/m23-validation.json`, `m23-performance.json`, `m23-reference-coverage.json` and `m23-visual-acceptance.json`. Static PASS does not grant appearance approval.
