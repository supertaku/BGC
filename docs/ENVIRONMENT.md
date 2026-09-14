# Local environment

Audited 2026-09-10 in `C:\Users\joshu\Documents\BGC`.

| Component | Result |
| --- | --- |
| Operating system | Windows 10 Home Single Language, display version 25H2, build 26200.9445, 64-bit runtime |
| Blender | 5.2.1 LTS |
| Blender executable | `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` |
| Blender on `PATH` | No; `scripts/setup/find_blender.ps1` resolves it from standard install locations |
| Blender Python | 3.13.13, 64-bit |
| `bpy` | 5.2.1 LTS, verified inside headless Blender |
| Git | 2.41.0.windows.1 |
| Node.js | 22.20.0 |
| npm | 11.18.0 |
| Free space at audit | approximately 75.6 GB on `C:` |
| Git repository | Yes; initialized during bootstrap |

Run `scripts/setup/check_environment.ps1` to repeat the executable and version checks. No system-level changes were made and no missing prerequisite blocks the project.

## Viewer dependency baseline

- Next.js 16.3.4
- React / React DOM 19.2.0
- Three.js 0.180.0
- React Three Fiber 9.7.0
- Drei 10.7.8
- TypeScript 6.0.3

The exact resolved graph is retained in `web/package-lock.json`.
