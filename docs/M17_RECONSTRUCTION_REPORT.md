# M17C bounded reconstruction

Status: **CLOSED_WITH_DEFERMENT; zero new LOD1 approvals**. The generic builder, per-landmark override, QA cameras, and structural GLB validator remain in use. Only the unpublished PSE draft was rebuilt.

The [part analysis](../data/reports/pse-part-analysis.json) computes area, perimeter, centroid, orientation, and pairwise overlap from source polygons. The 131 m part lies wholly inside the 119.2 m part; the latter's residual footprint is 938.6468 m². The builder now partitions those mapped masses, avoiding coincident full volumes. The 15.6 m and 12 m low parts are disjoint from the tower parts. Polygon boundaries and mapped heights are **verified geographic data**; component identities and floor stacking are **inferred**.

The old universal 4 m slope has been removed. The body and frontpiece currently have separate explicit `FLAT` top parameters labeled **INFERRED**. This is a placeholder because the photos show pointed twin forms but do not give enough independent geometry to place a trustworthy profile. The principal facade edge remains unresolved and a facade-phase build now fails clearly if it lacks an index. No vertical ribs were added.

One additional MASSING round rendered the two approximate southeast source cameras. Both comparisons still fail on upper silhouette and body/frontpiece relationship. Four major issues remain, so the conditional FACADE phase was not entered. The draft GLB passes structural validation at 9,960 bytes, 120 triangles, 3 meshes, 2 materials, and approximately 3 draws. The PSE LOD2 fallback stays in production; the draft's foreground LOD transition is NOT_RUN.

The seven original approved LOD1 assets remain published; no failed draft entered the runtime registry. Later PSE work should first obtain stronger side/upper-form evidence and resolve the principal facade edge. The other nine M17 candidates remain deferred, outside this closure.
