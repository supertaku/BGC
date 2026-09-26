"""Recover retained-snapshot transport tags omitted by the older normalizer."""
from prepare import read
def enrich_road_evidence(roads):
    raw=read('data/raw/osm/bgc-2026-09-14T162150Z.json')
    tags={f'osm:{e["type"]}:{e["id"]}':e.get('tags',{}) for e in raw['elements']}
    return [dict(road,properties=dict(road['properties'],tags=dict(road['properties'].get('tags',{}),**tags.get(road['properties']['id'],{})))) for road in roads]
