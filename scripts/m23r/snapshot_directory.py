"""Snapshot current official BGC directory pages; retain provenance locally."""
import hashlib,json,re,sys,time
from html import unescape
from urllib.request import urlopen,Request
from urllib.parse import urljoin
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'data/visual_reference/m23r/directory'
def fetch(url):
    CACHE.mkdir(parents=True,exist_ok=True);path=CACHE/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.html')
    if path.exists():return path.read_text(encoding='utf-8')
    with urlopen(Request(url,headers={'User-Agent':'BGC-reconstruction-reference-audit/1.0'}),timeout=45) as response:body=response.read().decode('utf-8')
    path.write_text(body,encoding='utf-8');return body
def text(value):return unescape(re.sub('<[^>]+>',' ',value)).strip()
def links(body):return [(unescape(url),text(label)) for url,label in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',body,re.S)]
def snapshot():
    records={};pages=[];counts={}
    for category in ['shop','dine','see']:
        queue=[f'https://bgc.com.ph/go/{category}/'];seen=set();category_ids=set()
        while queue:
            url=queue.pop(0)
            if url in seen:continue
            seen.add(url);body=fetch(url)
            pages.append(dict(url=url,sha256=hashlib.sha256(body.encode()).hexdigest(),local_file=str((CACHE/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.html')).relative_to(ROOT)),current_as_of='2026-09-26'))
            for target,label in links(body):
                target=urljoin(url,target)
                if re.fullmatch(f'https://bgc.com.ph/go/{category}/page/[0-9]+/',target) and target not in seen:queue.append(target)
            for card in re.findall(r'<li class="product\s.*?</li>',body,re.S):
                targets=links(card)
                if not targets:continue
                source=targets[0][0];title=re.search(r'<h2 class="woocommerce-loop-product__title">(.*?)</h2>',card,re.S)
                location=re.search(r'<p class="product-location">(.*?)</p>',card,re.S)
                image=re.search(r'<img[^>]+src="([^"]+)"',card)
                if not title:continue
                record=records.setdefault(source,dict(id=source.rstrip('/').split('/')[-1],name=text(title[1]),venue=' '.join(text(location[1]).split()) if location else None,floor=None,current_as_of='2026-09-26',source_url=source,source_type='OFFICIAL_BGC_DIRECTORY',exterior_visibility='UNKNOWN',image_url=unescape(image[1]) if image else None,categories=[]))
                if category not in record['categories']:record['categories'].append(category)
                category_ids.add(source)
                if category=='see':
                    title,sep,artist=record['name'].partition(' by ');record.update(title=title,artist=artist if sep else None,representation='DOCUMENTED_PENDING_LOCATION',rights_status='NO_REPRODUCTION_LICENSE_ESTABLISHED')
                else:
                    floor=re.search(r'\b(?:LG|UG|GF|Ground Floor|[1-9](?:st|nd|rd|th) (?:Floor|Level)|Level [1-9])\b',record['venue'] or '',re.I)
                    if floor:record['floor']=floor[0]
        counts[category]=len(category_ids)
    result=dict(schema_version=1,current_as_of='2026-09-26',counts=counts,pages=pages,records=sorted(records.values(),key=lambda r:r['id']),policy='Directory listing proves current listed presence, not exterior sign visibility. Facade placement requires photographic evidence; unknown locations remain pending.')
    destination=ROOT/'data/visual_reference/m23r/directory-snapshot.json';destination.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(counts=counts,pages=len(pages),records=len(records))))
if __name__=='__main__':
    if '--all' in sys.argv:snapshot();raise SystemExit()
    if '--asset' in sys.argv:
        url=sys.argv[2];name=sys.argv[3]
        if not re.fullmatch(r'[a-zA-Z0-9_.-]+',name):raise ValueError('Expected a simple asset filename')
        path=ROOT/'data/visual_reference/m23r/assets'/name;path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():
            with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=45) as response:content=response.read(20_000_000)
            path.write_bytes(content)
        path.with_suffix(path.suffix+'.source.json').write_text(json.dumps(dict(url=url,current_as_of='2026-09-26',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),rights_status='REFERENCE_ONLY_UNLESS_SEPARATELY_DOCUMENTED'),indent=2)+'\n',encoding='utf-8')
        print(path);raise SystemExit()
    if '--images' in sys.argv or '--all-images' in sys.argv:
        body=fetch(sys.argv[2]);print(json.dumps([unescape(s) for s in re.findall(r'(?:src|data-src|href)=["\']([^"\']+)["\']',body) if any(k in s.lower() for k in ['logo','brand']) or '--all-images' in sys.argv and any(k in s.lower() for k in ['.jpg','.png','.webp','.svg'])],indent=2));raise SystemExit()
    url=sys.argv[1] if len(sys.argv)>1 else 'https://bgc.com.ph/go/see/'
    body=fetch(url)
    print(json.dumps([(u,t) for u,t in links(body) if '/go/' in u or '/directory/' in u],ensure_ascii=True,indent=2))
    point=body.find('Ang Supremo');print(body[max(0,point-1200):point+1000])
