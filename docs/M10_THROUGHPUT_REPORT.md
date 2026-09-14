# M10 throughput report

M10 completed 5/5 targets in two waves. Average automated build plus five-camera render and GLB validation time was **26.99 s/building**. The batch reused one schema and one generic builder; all target variation is configuration.

Wave A passed after three QA framing iterations on its unusually tall/mid-rise pair. Wave B isolated one package failure: UNIQLO's OSM level-derived height omitted its source link. The corrected package passed on retry 1 without rebuilding the other two targets.

Average authoritative sources were **1.4 per target**, with **2.4 usable references per target**; all visual media stayed research-only and no images were copied. Evidence wall-clock time was not instrumented and is explicitly null in the machine report rather than estimated.

The dominant bottleneck is rights-safe visual coverage, especially weak/rear sides. Modeling cost is low once the evidence package exists; QA camera framing is the main deterministic nuisance across height extremes. See `data/reports/m10-building-costs.json`.
