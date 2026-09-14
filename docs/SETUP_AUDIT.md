# Setup audit

## Environment

- Operating system: Windows 10 Home Single Language 25H2, build 26200.9445 (64-bit runtime)
- Blender version: 5.2.1 LTS
- Blender executable access: PASS via `scripts/setup/find_blender.ps1`; executable is installed but not on `PATH`
- Blender Python version: 3.13.13 (64-bit)
- Node version: 22.20.0
- npm version: 11.18.0
- Git version: 2.41.0.windows.1
- Disk space during audit: approximately 75.6 GB free on `C:`

## Blender automation

| Capability | Result | Evidence |
| --- | --- | --- |
| Launching Blender from CLI | PASS | Blender 5.2.1 LTS started and exited in background mode |
| Executing `bpy` | PASS | `bpy.app.version_string` returned 5.2.1 LTS |
| Generating geometry | PASS | Minimal and procedural scenes generated from scripts |
| Saving `.blend` | PASS | Three non-empty scene files validated |
| Rendering PNG | PASS | Three non-empty 960 × 640 PNGs rendered and visually inspected |
| Exporting GLB | PASS | 38,844-byte GLB exported and re-imported successfully |

GLB re-import validation reported 49 mesh objects, 1,636 polygons, 10 materials, and a maximum object dimension of 100 m. Materials and geometry survived the round trip. Blender Z-up is converted by the exporter to glTF Y-up, matching Three.js; no viewer-side corrective rotation is used.

## Web pipeline

| Capability | Result | Evidence |
| --- | --- | --- |
| Creating web project | PASS | Minimal Next.js/TypeScript project and lockfile created |
| Loading GLB | PASS | `/models/integration-test.glb` loaded in a real browser session |
| Rendering scene | PASS | Synthetic block and materials visibly rendered; FPS display active |
| Camera interaction | PASS | OrbitControls drag visibly changed the camera viewpoint |
| Development build | PASS | Next.js dev server served the viewer with no final console errors or warnings |
| Production build | PASS | `next build` compiled, type-checked, and prerendered `/` successfully |

`npm run lint` passed and the installed dependency audit reported zero known vulnerabilities.

## Procedural pipeline

| Capability | Result | Evidence |
| --- | --- | --- |
| Structured data input | PASS | Three footprint records read from `data/entities/synthetic-buildings.json` |
| Procedural geometry creation | PASS | Synthetic 100 × 100 m block generated with varied buildings, roads, sidewalks, vegetation, and street furniture |
| Reusable asset functions | PASS | Shared functions cover materials, buildings, footprint extrusion, roads, sidewalks, trees, streetlights, cameras, rendering, saving, and export; repeated assets share mesh data |
| Deterministic regeneration | PASS | Full pipeline ran successfully twice from scripts without manual Blender state |

## Problems

### Blender is not on `PATH`

```text
severity: low
cause: the Blender installer did not add its executable directory to the process PATH
impact: typing `blender` directly fails, but repository scripts discover the standard installation and the full pipeline passes
recommended fix: keep using scripts/setup/find_blender.ps1; optionally add Blender to PATH later if direct shell use becomes important
```

### Git safe-directory check under the automation account

```text
severity: low
cause: the workspace owner SID differs from the sandbox process SID
impact: plain Git commands from this automation account reject the repository as dubious; a repository-specific one-command safe.directory override successfully reads status
recommended fix: use `git -c safe.directory=C:/Users/joshu/Documents/BGC <command>` in this sandbox, or explicitly add only this repository to the user's global safe.directory list if persistent Git automation is desired
```

## Readiness

READY FOR BGC PLANNING
