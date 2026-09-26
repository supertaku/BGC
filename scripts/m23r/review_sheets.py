"""Create deterministic six-camera review sheets without re-rendering assets."""
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
VIEWS=['AERIAL','STREET_FRONT','STREET_REAR','LEFT','RIGHT','ROOF_OBLIQUE']
def main():
 folders=sorted((ROOT/'blender/renders/m23/m23r').iterdir())
 out=ROOT/'data/reports/m23r-review';out.mkdir(exist_ok=True)
 for start in range(0,len(folders),4):
  sheet=Image.new('RGB',(1440,4*210),'#e8edef');draw=ImageDraw.Draw(sheet)
  for row,folder in enumerate(folders[start:start+4]):
   for col,view in enumerate(VIEWS):
    path=folder/(view+'.png')
    if not path.exists():raise RuntimeError(f'Missing camera {path}')
    image=Image.open(path).convert('RGB');image.thumbnail((240,180))
    sheet.paste(image,(col*240,row*210+24));draw.text((col*240+4,row*210+4),folder.name+' / '+view,fill='black')
  sheet.save(out/f'sheet-{start//4+1:02}.jpg',quality=90)
 print(f'{len(folders)} landmarks, {len(folders)*6} views, {(len(folders)+3)//4} review sheets')
if __name__=='__main__':main()
