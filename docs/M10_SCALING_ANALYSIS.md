# M10 scaling analysis

Five new LOD1 assets added 175,532 pilot bytes, 2,700 triangles, and 5 actual overview draw calls relative to M9. The resulting pilot is 1,208,880 bytes, 23,796 triangles, and 76 overview calls. Same-material facade components remain semantic in authoring and merge to one runtime mesh per target.

The observed M10 marginal cost is 35,106 bytes, 540 triangles, and 1 overview call per added building. A linear 31-detailed-building planning extrapolation is roughly 2.05 MB, 36.8k triangles, and 100 overview calls. This is planning evidence only; it assumes similar archetypes and no streaming/culling redesign.

At current scale, runtime geometry is low risk. Evidence fidelity and source coverage dominate. Full spatial streaming remains deferred.
