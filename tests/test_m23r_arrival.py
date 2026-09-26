import json,sys
from pathlib import Path
from shapely.geometry import shape
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/m23'))
from shangri_completion import arrival_void
def test_arrival_court_does_not_intersect_retained_towers():
    targets=json.loads((ROOT/'data/visual_reference/targets.json').read_text(encoding='utf-8'))['targets']
    target=next(t for t in targets if t['id']=='shangri')
    for volume in target['volumes']:
        if volume['properties']['height_m']>35:
            assert arrival_void().distance(shape(volume['geometry']))>.8
