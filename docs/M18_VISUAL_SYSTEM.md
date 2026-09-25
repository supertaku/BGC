# M18A shared visual system

Status: **LOW ACCEPTED; FULL REJECTED for v1**. LOW is the runtime default. LEGACY approximates the pre-M18 background, lighting, material response, exposure, and DPR for matched browser comparison. The normal selector disables FULL; `quality=FULL&benchmark=1` retains a diagnostic path.

`visualSystem.ts` defines 11 shared MeshStandardMaterial families across buildings, ground, roads, and furniture. Original GLB materials are restored in LEGACY. The material mapping is **procedural presentation**, not a surveyed material claim. No environment map or reusable bitmap texture is used. The renderer reports zero textures in LOW; FULL allocates one shadow map.

LOW has sky color, distance fog, hemisphere fill, directional sun, and no shadows. FULL adds a camera-local 1,024² shadow map over a bounded region. Matched p1 results reject FULL for the v1 experience.

The 452 mapped environment instances retain source positions. Three deterministic procedural tree forms vary by tree ID. Trunk and crown use soil and grass material groups. Street lamps, benches, bollards, bins, and shelters retain fixed scale and source rotation; random furniture scale and yaw were removed. This corrects an actual merged-tree geometry failure and avoids arbitrary placement changes.

High Street and South Street saved cameras were moved to estimated visualization positions on verified geographic path/road centerlines, giving clear street views. Their exact camera coordinates are **estimated**, not surveyed. Runtime streaming, LOD switching, and search remain unchanged.
