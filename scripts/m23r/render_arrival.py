"""Blender CLI close-up review of the estimated Shangri-La bridge/arrival work."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts/m23'))
from blender_build import load_package
import bpy
from mathutils import Vector
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
load_package('shangri');scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=900;scene.render.resolution_y=650;scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.72,.8,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
bpy.ops.object.light_add(type='SUN');bpy.context.object.rotation_euler=(.6,-.4,-.6);bpy.context.object.data.energy=3
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.lens=40
for name,position,target in [('BRIDGES',(-435,157,20),(-459,191,16)),('ARRIVAL',(-500,132,23),(-479,170,4))]:
 camera.location=position;camera.rotation_euler=(Vector(target)-Vector(position)).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(ROOT/f'blender/renders/m23/m23r-arrival/{name}.png');Path(scene.render.filepath).parent.mkdir(parents=True,exist_ok=True);bpy.ops.render.render(write_still=True)
