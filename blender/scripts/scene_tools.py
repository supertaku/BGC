"""Reusable bpy primitives for deterministic grounded and synthetic scene builds."""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon


_INSTANCE_PROTOTYPES: dict[str, list[bpy.types.Object]] = {}


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)
    _INSTANCE_PROTOTYPES.clear()


def configure_scene() -> None:
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    else:
        raise RuntimeError("No supported Eevee render engine is available")
    scene.render.resolution_x = 960
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.055, 0.075, 0.11)


def create_material(name: str, color: tuple[float, float, float, float], roughness: float = 0.72, metallic: float = 0.0) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
    material.diffuse_color = color
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = color
        principled.inputs["Roughness"].default_value = roughness
        metallic_input = principled.inputs.get("Metallic") or principled.inputs.get("Metallic IOR Level")
        if metallic_input:
            metallic_input.default_value = metallic
    return material


def create_box(name: str, location: tuple[float, float, float], dimensions: tuple[float, float, float], material: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return obj


def create_building(name: str, x: float, y: float, width: float, depth: float, height: float, material: bpy.types.Material) -> bpy.types.Object:
    if min(width, depth, height) <= 0:
        raise ValueError(f"Building {name} dimensions must be positive")
    obj = create_box(name, (x, y, height / 2.0), (width, depth, height), material)
    obj["classification"] = "procedurally generated filler"
    return obj


def create_footprint_building(name: str, footprint: list[list[float]], height: float, material: bpy.types.Material) -> bpy.types.Object:
    if len(footprint) < 3 or height <= 0:
        raise ValueError(f"Building {name} needs at least three footprint points and positive height")
    count = len(footprint)
    vertices = [(x, y, 0.0) for x, y in footprint] + [(x, y, height) for x, y in footprint]
    faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
    faces.extend((i, (i + 1) % count, (i + 1) % count + count, i + count) for i in range(count))
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(clean_customdata=True)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    obj["classification"] = "procedurally generated filler"
    return obj


def geojson_polygons(geometry: dict) -> list[list[list[float]]]:
    """Return polygons as [exterior, hole, ...] rings from GeoJSON geometry."""
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if geometry_type == "Polygon":
        return [coordinates]
    if geometry_type == "MultiPolygon":
        return list(coordinates)
    raise ValueError(f"Expected Polygon or MultiPolygon, got {geometry_type}")


def create_extruded_polygons(
    name: str,
    polygons: list[list[list[float]]],
    base_z: float,
    height: float,
    material: bpy.types.Material,
    classification: str,
) -> bpy.types.Object:
    """Create one triangulated solid mesh, including polygon holes and parts."""
    if height <= 0:
        raise ValueError(f"{name} extrusion height must be positive")
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for polygon in polygons:
        clean_rings = []
        for ring in polygon:
            clean = [[float(point[0]), float(point[1])] for point in ring]
            if clean and clean[0] == clean[-1]:
                clean.pop()
            if len(clean) >= 3:
                clean_rings.append(clean)
        if not clean_rings:
            continue
        ring_vectors = [[Vector((x, y)) for x, y in ring] for ring in clean_rings]
        triangles = tessellate_polygon(ring_vectors)
        flat_keys = [
            (round(x, 6), round(y, 6))
            for ring in clean_rings
            for x, y in ring
        ]
        lower_lookup: dict[tuple[float, float], int] = {}
        upper_lookup: dict[tuple[float, float], int] = {}
        for ring in clean_rings:
            for x, y in ring:
                key = (round(x, 6), round(y, 6))
                if key in lower_lookup:
                    continue
                lower_lookup[key] = len(vertices)
                vertices.append((x, y, base_z))
                upper_lookup[key] = len(vertices)
                vertices.append((x, y, base_z + height))
        for triangle in triangles:
            if triangle and isinstance(triangle[0], int):
                keys = [flat_keys[index] for index in triangle]
            else:
                keys = [(round(vertex.x, 6), round(vertex.y, 6)) for vertex in triangle]
            top = tuple(upper_lookup[key] for key in keys)
            top_points = [vertices[index] for index in top]
            cross_z = (
                (top_points[1][0] - top_points[0][0]) * (top_points[2][1] - top_points[0][1])
                - (top_points[1][1] - top_points[0][1]) * (top_points[2][0] - top_points[0][0])
            )
            if cross_z < 0:
                top = tuple(reversed(top))
            faces.append(top)
            faces.append(tuple(lower_lookup[key] for key in reversed(keys)))
        for ring in clean_rings:
            for index, (x, y) in enumerate(ring):
                nx, ny = ring[(index + 1) % len(ring)]
                current = (round(x, 6), round(y, 6))
                following = (round(nx, 6), round(ny, 6))
                faces.append((
                    lower_lookup[current], lower_lookup[following],
                    upper_lookup[following], upper_lookup[current],
                ))
    if not vertices or not faces:
        raise ValueError(f"{name} contains no usable polygon geometry")
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(clean_customdata=True)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    obj["classification"] = classification
    return obj


def create_box_cluster(
    name: str,
    points: list[tuple[float, float]],
    dimensions: tuple[float, float, float],
    base_z: float,
    material: bpy.types.Material,
) -> bpy.types.Object | None:
    """Batch many small repeated boxes into one web-efficient mesh."""
    if not points:
        return None
    dx, dy, dz = (component / 2 for component in dimensions)
    cube_faces = ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7))
    vertices = []
    faces = []
    for x, y in points:
        offset = len(vertices)
        z = base_z + dz
        vertices.extend([
            (x - dx, y - dy, z - dz), (x + dx, y - dy, z - dz),
            (x + dx, y + dy, z - dz), (x - dx, y + dy, z - dz),
            (x - dx, y - dy, z + dz), (x + dx, y - dy, z + dz),
            (x + dx, y + dy, z + dz), (x - dx, y + dy, z + dz),
        ])
        faces.extend(tuple(offset + index for index in face) for face in cube_faces)
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    obj["classification"] = "procedurally generated filler at verified geographic points"
    return obj


def create_tree_cluster(
    name: str,
    points: list[tuple[float, float]],
    trunk_material: bpy.types.Material,
    crown_material: bpy.types.Material,
) -> list[bpy.types.Object]:
    """Batch low-poly tree markers into two meshes to hold draw calls down."""
    if not points:
        return []
    objects = []
    trunk_vertices = []
    trunk_faces = []
    sides = 6
    for x, y in points:
        offset = len(trunk_vertices)
        for z in (0.12, 2.3):
            for index in range(sides):
                angle = index * math.tau / sides
                trunk_vertices.append((x + math.cos(angle) * 0.16, y + math.sin(angle) * 0.16, z))
        trunk_faces.append(tuple(offset + index for index in range(sides - 1, -1, -1)))
        trunk_faces.append(tuple(offset + sides + index for index in range(sides)))
        trunk_faces.extend((offset + index, offset + (index + 1) % sides, offset + sides + (index + 1) % sides, offset + sides + index) for index in range(sides))
    trunk_mesh = bpy.data.meshes.new(f"{name}_trunks_mesh")
    trunk_mesh.from_pydata(trunk_vertices, [], trunk_faces)
    trunk_mesh.update()
    trunk_obj = bpy.data.objects.new(f"{name}_trunks", trunk_mesh)
    bpy.context.scene.collection.objects.link(trunk_obj)
    trunk_obj.data.materials.append(trunk_material)
    objects.append(trunk_obj)

    crown_vertices = []
    crown_faces = []
    crown_template = [(0, 0, 4.5), (1.25, 0, 3.2), (0, 1.25, 3.2), (-1.25, 0, 3.2), (0, -1.25, 3.2), (0, 0, 2.25)]
    crown_template_faces = ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1), (5, 2, 1), (5, 3, 2), (5, 4, 3), (5, 1, 4))
    for x, y in points:
        offset = len(crown_vertices)
        crown_vertices.extend((x + vx, y + vy, vz) for vx, vy, vz in crown_template)
        crown_faces.extend(tuple(offset + index for index in face) for face in crown_template_faces)
    crown_mesh = bpy.data.meshes.new(f"{name}_crowns_mesh")
    crown_mesh.from_pydata(crown_vertices, [], crown_faces)
    crown_mesh.update()
    crown_obj = bpy.data.objects.new(f"{name}_crowns", crown_mesh)
    bpy.context.scene.collection.objects.link(crown_obj)
    crown_obj.data.materials.append(crown_material)
    objects.append(crown_obj)
    for obj in objects:
        obj["classification"] = "procedurally generated filler at verified geographic points"
    return objects


def create_road(name: str, x: float, y: float, width: float, length: float, orientation: str, material: bpy.types.Material) -> bpy.types.Object:
    dims = (length, width, 0.12) if orientation == "x" else (width, length, 0.12)
    return create_box(name, (x, y, 0.06), dims, material)


def create_sidewalk(name: str, x: float, y: float, width: float, length: float, orientation: str, material: bpy.types.Material) -> bpy.types.Object:
    dims = (length, width, 0.24) if orientation == "x" else (width, length, 0.24)
    return create_box(name, (x, y, 0.12), dims, material)


def _linked_instance(prototype_key: str, name: str, location: tuple[float, float, float], factory) -> list[bpy.types.Object]:
    if prototype_key not in _INSTANCE_PROTOTYPES:
        created = factory(name, location)
        _INSTANCE_PROTOTYPES[prototype_key] = created
        return created
    instances = []
    base_location = _INSTANCE_PROTOTYPES[prototype_key][0].location.copy()
    offset = Vector(location) - base_location
    for index, source in enumerate(_INSTANCE_PROTOTYPES[prototype_key]):
        obj = source.copy()
        obj.data = source.data
        obj.name = f"{name}_{index}"
        obj.location = source.location + offset
        bpy.context.scene.collection.objects.link(obj)
        instances.append(obj)
    return instances


def create_tree(name: str, x: float, y: float, trunk_material: bpy.types.Material, leaf_material: bpy.types.Material) -> list[bpy.types.Object]:
    def factory(base_name: str, location: tuple[float, float, float]) -> list[bpy.types.Object]:
        px, py, _ = location
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.22, depth=2.4, location=(px, py, 1.32))
        trunk = bpy.context.object
        trunk.name = f"{base_name}_trunk"
        trunk.data.materials.append(trunk_material)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.45, location=(px, py, 3.25))
        crown = bpy.context.object
        crown.name = f"{base_name}_crown"
        crown.scale = (1.0, 1.0, 1.2)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        crown.data.materials.append(leaf_material)
        return [trunk, crown]
    return _linked_instance("tree_standard", name, (x, y, 0.0), factory)


def create_streetlight(name: str, x: float, y: float, pole_material: bpy.types.Material, lamp_material: bpy.types.Material) -> list[bpy.types.Object]:
    def factory(base_name: str, location: tuple[float, float, float]) -> list[bpy.types.Object]:
        px, py, _ = location
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.09, depth=4.6, location=(px, py, 2.42))
        pole = bpy.context.object
        pole.name = f"{base_name}_pole"
        pole.data.materials.append(pole_material)
        lamp = create_box(f"{base_name}_lamp", (px + 0.42, py, 4.65), (0.85, 0.24, 0.18), lamp_material)
        return [pole, lamp]
    return _linked_instance("streetlight_standard", name, (x, y, 0.0), factory)


def add_daylight() -> None:
    bpy.ops.object.light_add(type="SUN", location=(20, -25, 50))
    sun = bpy.context.object
    sun.name = "Sun"
    sun.data.energy = 2.4
    sun.rotation_euler = (math.radians(24), math.radians(-28), math.radians(-28))
    bpy.ops.object.light_add(type="AREA", location=(-24, -16, 34))
    area = bpy.context.object
    area.name = "SkyFill"
    area.data.energy = 850
    area.data.shape = "DISK"
    area.data.size = 28
    point_camera(area, (0, 0, 0))


def add_camera(name: str, location: tuple[float, float, float], target: tuple[float, float, float], lens: float = 48.0) -> bpy.types.Object:
    bpy.ops.object.camera_add(location=location)
    camera = bpy.context.object
    camera.name = name
    camera.data.lens = lens
    camera.data.clip_end = 1200
    point_camera(camera, target)
    bpy.context.scene.camera = camera
    return camera


def point_camera(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_png(path: Path) -> None:
    ensure_directory(path.parent)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def save_blend(path: Path) -> None:
    ensure_directory(path.parent)
    bpy.ops.wm.save_as_mainfile(filepath=str(path))


def export_glb(path: Path) -> None:
    ensure_directory(path.parent)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_yup=True, export_extras=True,
    )
