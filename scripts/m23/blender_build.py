"""Blender CLI: isolate M23 LOD2 fallbacks and render reproducible QA assets.

blender -b --python scripts/m23/blender_build.py -- --tiles
blender -b --python scripts/m23/blender_build.py -- --render pse mind_museum
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
from collections import defaultdict
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'blender/scripts'))
import generate_bgc_tiles as tile_builder
from scene_tools import clear_scene,configure_scene,create_material,export_glb

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,d):
 p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def tiles():
 cat=read('web/public/world/detail/m23/catalog.json');mapping={sid:'m23:'+p['id'] for p in cat['packages'] for sid in p.get('replaces',[])}
 tile_builder.OUTPUT_DIR=ROOT/'web/public/models/m23/tiles';tile_builder.SCENE_DIR=ROOT/'blender/scenes/m23/tiles';tile_builder.METRICS_DIR=ROOT/'data/reports/m23/tiles'
 manifest={};version=hashlib.sha256((Path(__file__).read_bytes()+(ROOT/'blender/scripts/generate_bgc_tiles.py').read_bytes()+json.dumps(mapping,sort_keys=True).encode())).hexdigest()
 for source in sorted((ROOT/'data/processed/bgc-tiles').glob('*.json')):
  d=json.loads(source.read_text(encoding='utf-8'));changed=False
  for f in d['buildings']:
   sid=f['properties']['id']
   if sid in mapping:f['properties']['detailed_asset_id']=mapping[sid];changed=True
  if not changed:continue
  key=d['tile_id'];inputhash=hashlib.sha256(source.read_bytes()+version.encode()).hexdigest();metric=tile_builder.METRICS_DIR/f'{key}.json';output=tile_builder.OUTPUT_DIR/f'{key}.glb'
  if metric.exists() and output.exists() and json.loads(metric.read_text()).get('input_sha256')==inputhash:r=json.loads(metric.read_text())
  else:
   d['input_sha256']=inputhash;p=ROOT/f'data/visual_reference/compiled_tiles/{key}.json';write(str(p.relative_to(ROOT)),d);r=tile_builder.build_tile(p,False)
  manifest[key]=dict(url=f'/models/m23/tiles/{key}.glb',size_bytes=r['bytes'],triangles=r['triangle_count'],meshes=r['mesh_count'])
 write('web/public/world/detail/m23/tile-variants.json',dict(schema_version=1,tiles=manifest));print('M23_TILE_VARIANTS',len(manifest))

def prototype(kind):
 if kind=='box':bpy.ops.mesh.primitive_cube_add(size=1)
 elif kind=='sphere':bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=5,radius=1)
 elif kind=='cone':bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=1,radius2=0,depth=1)
 else:bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=1,depth=1)
 ob=bpy.context.object;verts=[tuple(v.co) for v in ob.data.vertices];faces=[tuple(p.vertices) for p in ob.data.polygons];bpy.data.objects.remove(ob,do_unlink=True);return verts,faces

def load_package(key):
 d=read(f'web/public/world/detail/m23/{key}.json');buffers=defaultdict(lambda:[[],[]]);protos={k:prototype(k) for k in ['box','sphere','cylinder','cone']}
 for mat,m in d['meshes'].items():
  vs,fs=buffers[mat];offset=len(vs);v=m['vertices'];vs.extend((v[i],-v[i+2],v[i+1]) for i in range(0,len(v),3));ind=m['indices'];fs.extend(tuple(offset+n for n in ind[i:i+3]) for i in range(0,len(ind),3))
 for inst in d['instances']:
  vs,fs=buffers[inst['material']];offset=len(vs);pv,pf=protos[inst['kind']];x,h,z=inst['position'];sx,sh,sz=inst['scale'];a=inst['yaw'];c,s=math.cos(a),math.sin(a)
  # Blender prototype axes x/north/up correspond to runtime x/-z/y.
  for vx,vy,vz in pv:
   xx,yy=vx*sx,vy*sz;vs.append((x+xx*c-yy*s,-z+xx*s+yy*c,h+vz*sh))
  fs.extend(tuple(offset+n for n in face) for face in pf)
 for mat,(vs,fs) in buffers.items():
  color,rough,metal=d['materials'][mat];rgb=tuple(int(color[i:i+2],16)/255 for i in [1,3,5]);m=create_material('M23_'+mat,(*rgb,1),rough,metal)
  mesh=bpy.data.meshes.new(key+'_'+mat);mesh.from_pydata(vs,[],fs);mesh.validate();mesh.update();ob=bpy.data.objects.new(key+'_'+mat,mesh);bpy.context.collection.objects.link(ob);ob.data.materials.append(m);ob['grounding']='INFERRED';ob['source_package']=f'/world/detail/m23/{key}.json'
 return d

def render(key,iteration):
 clear_scene();configure_scene()
 ensembles={'mitsukoshi_ensemble':['mitsukoshi','seasons'],'one_bonifacio_ensemble':['pse','suites','shangri','one_bonifacio','one_bonifacio_realm']}
 members=[load_package(k) for k in ensembles.get(key,[key])];d=members[0];scene=bpy.context.scene
 # Save unlit runtime export before adding QA-only stage/camera/lights.
 out=ROOT/f'exports/glb/m23/{key}.glb';out.parent.mkdir(parents=True,exist_ok=True);export_glb(out)
 meshes=[o for o in scene.objects if o.type=='MESH'];coords=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box];xmin=min(v.x for v in coords);xmax=max(v.x for v in coords);ymin=min(v.y for v in coords);ymax=max(v.y for v in coords);h=max(v.z for v in coords);cx=(xmin+xmax)/2;cy=(ymin+ymax)/2;extent=max(xmax-xmin,ymax-ymin,h)
 bpy.ops.mesh.primitive_plane_add(size=extent*4,location=(cx,cy,-.02));floor=bpy.context.object;floor.name='QA_ONLY_GROUND';floor.data.materials.append(create_material('QA_ground',(.22,.25,.22,1)))
 bpy.ops.object.light_add(type='SUN',location=(cx-100,cy-200,300));bpy.context.object.rotation_euler=(.45,-.5,-.5);bpy.context.object.data.energy=2
 scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.72,.8,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
 scene.render.resolution_x=900;scene.render.resolution_y=700;scene.render.resolution_percentage=100
 scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
 bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.lens=45;camera.data.clip_end=10000
 views={'AERIAL':(1,-1,1.2),'STREET_FRONT':(0,-1.5,.12),'STREET_REAR':(0,1.5,.12),'LEFT_OBLIQUE':(-1,-1,.65),'RIGHT_OBLIQUE':(1,-1,.65),'ROOF_OBLIQUE':(.3,.3,1.9)}
 qa=[]
 for name,offset in views.items():
  target=Vector((cx,cy,h*.5));radius=math.sqrt((xmax-xmin)**2+(ymax-ymin)**2+h*h)/2;distance=radius/math.sin(camera.data.angle_y/2)*1.12
  direction=Vector(offset).normalized();loc=target+direction*distance
  if name.startswith('STREET') and h<20:loc.z=4;target.z=3
  camera.location=loc;camera.rotation_euler=(target-loc).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(ROOT/f'blender/renders/m23/{iteration}/{key}/{name}.png');Path(scene.render.filepath).parent.mkdir(parents=True,exist_ok=True);bpy.ops.render.render(write_still=True);qa.append(dict(camera_id=name,position=list(loc),target=list(target),image=str(Path(scene.render.filepath).relative_to(ROOT))))
 scene_path=ROOT/f'blender/scenes/m23/{key}.blend';scene_path.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(scene_path));write(f'data/reports/m23/cameras/{key}.json',dict(entity_id=key,iteration=iteration,cameras=qa,source_sha256=[m['content_sha256'] for m in members],status='AWAITING_USER_TEST'))

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--tiles',action='store_true');parser.add_argument('--render',nargs='*');parser.add_argument('--iteration',default='v1');a=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
 if a.tiles:tiles()
 for key in a.render or []:render(key,a.iteration)
if __name__=='__main__':main()
