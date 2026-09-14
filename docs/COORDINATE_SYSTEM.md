# Coordinate system

## Contract

```text
GeoJSON longitude/latitude (EPSG:4326)
  -> pyproj Transformer(always_xy=True)
EPSG:32651 easting/northing metres
  -> subtract fixed projected origin
local X east / Y north / Z up metres
  -> Blender glTF exporter
Three.js right-handed Y-up scene (no corrective rotation)
```

The EPSG registry defines EPSG:32651 as WGS 84 / UTM zone 51N, covering 120°E–126°E in the northern hemisphere with easting/northing axes in metres. BGC lies within that longitude band.

## Fixed origin

| Field | Value | Classification |
| --- | --- | --- |
| Longitude | 121.050972°E | chosen engineering datum |
| Latitude | 14.550806°N | chosen engineering datum |
| EPSG:32651 easting | 289,998.296851 m | derived by pyproj 3.7.2 |
| EPSG:32651 northing | 1,609,541.741597 m | derived by pyproj 3.7.2 |
| Transform version | `bgc-local-frame-v1` | project contract |
| Horizontal units | metres | verified CRS definition |
| Vertical datum | unknown | not used in this pilot |

Ground is local `Z=0`; building heights are relative to that diagnostic ground. Absolute terrain/elevation is not claimed.

## Verification

`scripts/validation/test_coordinates.py` checks the UTM central-meridian invariant, origin round trip, east/north direction, three geodesic-versus-projected distance comparisons (within 0.25 m), pilot dimensions/area, polygon winding, validity, and local coordinate magnitudes. The measured pilot is approximately **494.0 × 419.2 m**, **20.35 ha**.

Sources: [EPSG:32651](https://epsg.org/crs_32651/WGS-84-UTM-zone-51N.html) and [pyproj Transformer](https://pyproj4.github.io/pyproj/stable/api/transformer.html).
