"""Incrementally regenerate tile-owned streets from original transport evidence."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts/m23'))
from build import street_packages
from road_evidence import enrich_road_evidence
from prepare import read,write
from shapely.geometry import shape
from shapely.ops import unary_union
def main():
 paths=read('data/processed/bgc-paths.geojson')['features'];roads=enrich_road_evidence(read('data/processed/bgc-roads.geojson')['features']);buildings=read('data/processed/bgc-buildings.geojson')['features'];pois=read('data/processed/bgc-pois.geojson')['features']
 entries=street_packages(paths,roads,buildings,pois,unary_union([shape(f['geometry']) for f in buildings]),unary_union([shape(f['geometry']) for f in roads]))
 catalog=read('web/public/world/detail/m23/catalog.json');catalog['packages']=sorted([e for e in catalog['packages'] if not e['id'].startswith('street_')]+entries,key=lambda e:e['id'])
 write('web/public/world/detail/m23/catalog.json',catalog);print('Rebuilt',len(entries),'street packages')
if __name__=='__main__':main()
