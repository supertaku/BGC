"""Retain the four user-supplied photographs with provenance and hashes."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FILES=[('cf8ca6f8-7d52-4ccc-bcdd-18bca47bd015','high-street-terraces'),('6f3eb4f8-b665-4f26-9b70-b2b295c4420c','road-crossing'),('dbbb1236-9d06-4377-9a59-4b9412c7d03a','retail-ramp'),('3d9b1547-65bd-4bcc-9ffa-c088facca219','sm-aura')]
def main():
 target=ROOT/'data/visual_reference/m23r/references';target.mkdir(parents=True,exist_ok=True);records=[]
 for key,name in FILES:
  path=target/(name+'.png')
  if not path.exists():shutil.copyfile(Path.home()/'AppData/Local/Temp'/f'codex-clipboard-{key}.png',path)
  records.append(dict(id=name,path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source_type='USER_SUPPLIED_PHOTOGRAPH',grounding='VERIFIED_PHOTOGRAPHIC_EVIDENCE',capture_date=None,rights='REFERENCE_ONLY',notes='Supports visible form, materials and street furniture; geographic dimensions and reconstruction placement remain estimated.'))
 (target/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
 print('Retained',len(records),'photographs')
if __name__=='__main__':main()
