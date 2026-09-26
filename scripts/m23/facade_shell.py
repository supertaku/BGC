"""Compile competing coplanar fronts into one deterministic exterior surface.

Boxes become indexed, material-batched surfaces only in landmark packages.
Opposite-facing construction joints remain separate; no depth-bias is applied.
All source feature records are retained by the caller.
"""
from collections import defaultdict
import math
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles


def box_faces(item):
    x,y,z=item['position'];sx,sy,sz=item['scale'];a=item['yaw'];c,s=math.cos(a),math.sin(a)
    vertices=np.array([[x+dx*sx*c+dz*sz*s,y+dy*sy,z-dx*sx*s+dz*sz*c]
        for dx,dy,dz in [(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),
                         (-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)]])
    for indices in [[3,2,1,0],[4,5,6,7],[0,1,5,4],[2,3,7,6],[0,4,7,3],[1,2,6,5]]:
        yield vertices[indices]


def compile_shell(package):
    groups=defaultdict(lambda:defaultdict(list));planes={}
    def add(material,points):
        normal=np.cross(points[1]-points[0],points[2]-points[0]);length=np.linalg.norm(normal)
        if length<1e-8:return
        normal/=length;axis=int(np.argmax(abs(normal)));d=float(np.dot(normal,points[0]))
        # Plane grouping at export precision. Orientation is deliberately preserved.
        key=(*np.round(normal,5),round(d,3));planes[key]=(normal,d,axis)
        polygon=Polygon(np.delete(points,axis,axis=1)).buffer(0)
        if not polygon.is_empty:groups[key][material].append(polygon)
    for material,mesh in package.meshes.items():
        vertices=np.array(mesh['vertices'],dtype=float).reshape(-1,3)
        for i in range(0,len(mesh['indices']),3):add(material,vertices[mesh['indices'][i:i+3]])
    remaining=[]
    for instance in package.instances:
        if instance['kind']=='box':
            for face in box_faces(instance):add(instance['material'],face)
        else:remaining.append(instance)
    package.instances=remaining;package.meshes=defaultdict(lambda:dict(vertices=[],indices=[]))
    exterior=defaultdict(list)
    for key in sorted(groups,key=lambda key:-planes[key][1]):
        materials=groups[key];normal,d,axis=planes[key];occupied=None
        bucket=tuple(np.round(normal,3))
        # Clip away an occluded front when another parallel exterior front is
        # within the 2 cm diagnostic tolerance. Keep its own original plane;
        # this is surface subtraction, never a polygon-offset workaround.
        nearby=[p for depth,p in exterior[bucket] if abs(depth-d)<.022]
        occluder=unary_union(nearby) if nearby else None
        # Opaque trim takes precedence over glazing where their physical faces meet.
        for material in sorted(materials,key=lambda m:(m.startswith('GLASS'),m)):
            surface=unary_union(materials[material])
            visible=surface if occupied is None else surface.difference(occupied)
            occupied=surface if occupied is None else occupied.union(surface)
            if occluder is not None:visible=visible.difference(occluder)
            for triangle in constrained_delaunay_triangles(visible).geoms:
                points=[]
                for uv in list(triangle.exterior.coords)[:3]:
                    point=np.insert(np.array(uv),axis,0.)
                    point[axis]=(d-np.dot(normal,point))/normal[axis];points.append(point)
                if np.dot(np.cross(points[1]-points[0],points[2]-points[0]),normal)<0:points.reverse()
                package.tri(material,points)
        exterior[bucket].append((d,occupied))
    # Identical opposite-facing faces are internal construction joints. Remove
    # both, including cross-material joins, rather than exporting hidden skins.
    seen={};remove=defaultdict(set)
    for mat,mesh in package.meshes.items():
        v=mesh['vertices']
        for offset in range(0,len(mesh['indices']),3):
            indices=mesh['indices'][offset:offset+3]
            key=tuple(sorted(tuple(round(x,3) for x in v[i*3:i*3+3]) for i in indices))
            if key in seen:
                oldmat,oldoffset=seen[key];remove[oldmat].add(oldoffset);remove[mat].add(offset)
            else:seen[key]=(mat,offset)
    for mat,offsets in remove.items():
        mesh=package.meshes[mat];mesh['indices']=[i for offset in range(0,len(mesh['indices']),3) if offset not in offsets for i in mesh['indices'][offset:offset+3]]
