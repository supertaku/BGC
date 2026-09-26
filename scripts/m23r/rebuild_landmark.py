"""Rebuild one changed landmark without regenerating validated city assets."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts/m23'))
from build import landmark
from prepare import read,write
def main():
 key=sys.argv[1];target=next(t for t in read('data/visual_reference/targets.json')['targets'] if t['id']==key)
 entry=landmark(target).save();catalog=read('web/public/world/detail/m23/catalog.json')
 old=next(e for e in catalog['packages'] if e['id']==key);old.update(entry)
 write('web/public/world/detail/m23/catalog.json',catalog)
 print('Rebuilt',key)
if __name__=='__main__':main()
