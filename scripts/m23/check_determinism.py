"""Regenerate packages and assert byte-for-byte reproducibility."""
import hashlib,subprocess,sys
from prepare import ROOT,write

def hashes():
 return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'web/public/world/detail/m23').glob('*.json')) if p.name!='tile-variants.json'}

if __name__=='__main__':
 before=hashes()
 subprocess.run([sys.executable,str(ROOT/'scripts/m23/build.py')],cwd=ROOT,check=True)
 after=hashes();changed=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)]
 write('data/reports/m23/determinism.json',dict(status='PASS' if not changed else 'FAIL',files=len(after),changed=changed,sha256=after))
 print('M23 determinism:',len(after),'files;',len(changed),'changed')
 if changed:raise SystemExit(1)
