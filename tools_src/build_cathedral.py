"""Model the hub cathedral and export it as art/town/cathedral.gltf.

Art Deco church inspired by the Catedral São José of Campo Mourão (PR): twin stepped towers with
white fins and slit windows, stepped central gable, twin segmental arches over stained glass, round
portal with voussoirs, low aisles with balustrades and rounded front corners. Scaled ~0.8 (20 x 40 m).
The interior is open and walkable: narthex, nave on finned piers, aisles, pews, raised chancel and apse.

Blender coords: facade faces -Y, nave runs toward +Y. Collision boxes are named *-colonly for Godot.
Visible meshes are merged per material at the end (few draw calls).

Usage:
  blender -b --factory-startup -P tools_src/build_cathedral.py
"""

import itertools
import math
from collections import defaultdict
from pathlib import Path

import bmesh
import bpy
import numpy
from mathutils import Matrix, Vector

PROJECT_DIR = Path(__file__).resolve().parent.parent
KIT_DIR = PROJECT_DIR / "tools" / "vendor" / "village" / "Medieval Village MegaKit[Standard]"
KIT_TEXTURES = KIT_DIR / "Textures"
OUTPUT_DIR = PROJECT_DIR / "art" / "town"
GENERATED_TEXTURES = OUTPUT_DIR / "textures"

STEP_COUNT = 7
STEP_RISE = 0.15
STEP_TREAD = 0.45
BASE = STEP_COUNT * STEP_RISE
HALF_WIDTH = 10.0
CENTER_HALF = 2.8
TOWER_OUTER = 7.0
NAVE_HALF = 4.5
WALL = 0.6
FACADE_DEPTH = 1.0
NARTHEX_DEPTH = 5.0
BODY_LENGTH = 34.0
APSE_RADIUS = NAVE_HALF
AISLE_TOP = 11.4
ARCADE_TOP = 9.0
NAVE_CEILING = 14.0
NAVE_WALL_TOP = 15.5
TOWER_BASE_TOP = 17.0
PIER_Y = [10.4, 15.8, 21.2, 26.6]
ARCH_WIDTH = 4.4
ARCH_SPRING = 6.0
BAY_CENTERS = [7.7, 13.1, 18.5, 23.9, 29.3]
CHANCEL_FRONT = 29.0
CHANCEL_HEIGHT = 0.9
PORTAL_WIDTH = 4.0
PORTAL_SPRING = 4.0

GLASS_COLORS = numpy.array([
    [0.12, 0.25, 0.75], [0.10, 0.20, 0.60], [0.95, 0.62, 0.15], [0.98, 0.78, 0.30],
    [0.20, 0.45, 0.85], [0.15, 0.35, 0.70], [0.85, 0.30, 0.15],
])


# ---------- materials ----------

def load_kit_image(file_name: str, is_color: bool):
    godot_normal = KIT_TEXTURES / "Normals Godot-Unity" / file_name
    image = bpy.data.images.load(str(godot_normal if godot_normal.exists() else KIT_TEXTURES / file_name))
    image.colorspace_settings.name = "sRGB" if is_color else "Non-Color"

    return image


def save_generated_image(name: str, pixels_rgba, size: int):
    image = bpy.data.images.new(name, size, size, alpha=False)

    image.pixels.foreach_set(pixels_rgba.astype(numpy.float32).ravel())
    image.filepath_raw = str(GENERATED_TEXTURES / f"{name}.png")
    image.file_format = "PNG"
    GENERATED_TEXTURES.mkdir(parents=True, exist_ok=True)
    image.save()

    return image


def make_tinted_image(source_name: str, name: str, multiply: tuple, add: tuple):
    source = load_kit_image(source_name, True)
    size = source.size[0]
    pixels = numpy.array(source.pixels[:]).reshape(size, size, 4)
    tinted = numpy.clip(pixels[..., :3] * numpy.array(multiply) + numpy.array(add), 0.0, 1.0)
    rgba = numpy.concatenate([tinted, numpy.ones((size, size, 1))], axis=2)

    return save_generated_image(name, rgba, size)


def make_stained_glass_image():
    size = 256
    generator = numpy.random.default_rng(7)
    cell_points = generator.random((45, 2)) * size
    cell_colors = GLASS_COLORS[generator.integers(0, len(GLASS_COLORS), 45)]
    grid = numpy.stack(numpy.meshgrid(numpy.arange(size), numpy.arange(size)), axis=-1).reshape(-1, 1, 2)
    distances = numpy.linalg.norm(grid - cell_points[None, :, :], axis=2)
    nearest_two = numpy.sort(distances, axis=1)[:, :2]
    owner = numpy.argmin(distances, axis=1)
    lead_line = (nearest_two[:, 1] - nearest_two[:, 0]) < 1.6
    shade = 0.88 + 0.12 * numpy.cos(distances[numpy.arange(len(owner)), owner] / 12.0)
    rgb = cell_colors[owner] * shade[:, None]
    rgb[lead_line] = [0.05, 0.05, 0.07]
    rgba = numpy.concatenate([rgb, numpy.ones((len(rgb), 1))], axis=1).reshape(size, size, 4)

    return save_generated_image("T_StainedGlass", rgba, size)


def make_floor_image():
    """Two-tone stone checker (one 2x2 tile per texture), slight per-tile shade noise."""
    size = 256
    generator = numpy.random.default_rng(11)
    cream = numpy.array([0.9, 0.87, 0.81])
    slate = numpy.array([0.7, 0.69, 0.68])
    coordinates = numpy.arange(size)
    tile_x, tile_y = numpy.meshgrid(coordinates // (size // 2), coordinates // (size // 2))
    is_cream = ((tile_x + tile_y) % 2 == 0)[..., None]
    rgb = numpy.where(is_cream, cream, slate) * (0.96 + 0.04 * generator.random((size, size, 1)))
    grout = (coordinates % (size // 2) < 2)
    rgb[grout, :] = 0.55
    rgb[:, grout] = 0.55
    rgba = numpy.concatenate([rgb, numpy.ones((size, size, 1))], axis=2)

    return save_generated_image("T_CathedralFloor_BaseColor", rgba, size)


def make_material(name: str, base_image, normal_image=None, roughness_image=None, emission=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes["Principled BSDF"]
    base_node = nodes.new("ShaderNodeTexImage")

    base_node.image = base_image
    links.new(base_node.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 0.9

    if normal_image:
        normal_texture = nodes.new("ShaderNodeTexImage")
        normal_map = nodes.new("ShaderNodeNormalMap")
        normal_texture.image = normal_image
        links.new(normal_texture.outputs["Color"], normal_map.inputs["Color"])
        links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])

    if roughness_image:
        roughness_texture = nodes.new("ShaderNodeTexImage")
        roughness_texture.image = roughness_image
        links.new(roughness_texture.outputs["Color"], shader.inputs["Roughness"])

    if emission > 0.0:
        links.new(base_node.outputs["Color"], shader.inputs["Emission Color"])
        shader.inputs["Emission Strength"].default_value = emission

    return material


def make_plain_material(name: str, color: tuple, metallic: float, roughness: float):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness

    return material


def build_materials() -> dict:
    # Stone and trim textures are also loaded by build_plaza_props.py.
    stone_image = make_tinted_image("T_Brick_BaseColor.png", "T_CathedralStone_BaseColor", (1.08, 1.06, 1.0), (0.09, 0.08, 0.06))
    trim_image = make_tinted_image("T_Plaster_BaseColor.png", "T_CathedralTrim_BaseColor", (1.0, 1.0, 1.0), (0.08, 0.08, 0.08))
    wall_image = make_tinted_image("T_Plaster_BaseColor.png", "T_CathedralWall_BaseColor", (0.98, 0.93, 0.82), (0.12, 0.11, 0.09))
    roof_image = make_tinted_image("T_RoundTiles_BaseColor.png", "T_CathedralRoof_BaseColor", (1.15, 0.62, 0.48), (0.08, 0.02, 0.0))
    plaster_normal = load_kit_image("T_Plaster_Normal.png", False)

    return {
        "stone": make_material("M_CathedralStone", stone_image, load_kit_image("T_Brick_Normal.png", False), load_kit_image("T_Brick_Roughness.png", False)),
        "wall": make_material("M_CathedralWall", wall_image, plaster_normal),
        "trim": make_material("M_CathedralTrim", trim_image, plaster_normal),
        "roof": make_material("M_CathedralRoof", roof_image, load_kit_image("T_RoundTiles_Normal.png", False)),
        "floor": make_material("M_CathedralFloor", make_floor_image()),
        "glass": make_material("M_StainedGlass", make_stained_glass_image(), emission=1.2),
        "gold": make_plain_material("M_Gold", (0.95, 0.72, 0.28), 1.0, 0.3),
        "marble": make_plain_material("M_Marble", (0.93, 0.91, 0.88), 0.0, 0.35),
        "paint_red": make_plain_material("M_PaintRed", (0.6, 0.18, 0.14), 0.0, 0.8),
        "paint_ochre": make_plain_material("M_PaintOchre", (0.82, 0.6, 0.28), 0.0, 0.8),
        "painting": make_plain_material("M_Painting", (0.16, 0.22, 0.48), 0.0, 0.6),
        "slit_glass": make_plain_material("M_SlitGlass", (0.08, 0.12, 0.25), 0.2, 0.15),
        "wood": make_plain_material("M_DoorWood", (0.26, 0.14, 0.08), 0.0, 0.6),
        "dark": make_plain_material("M_RecessShadow", (0.06, 0.05, 0.07), 0.0, 1.0),
    }


# ---------- geometry helpers ----------

def object_from_bmesh(name: str, mesh_bmesh, material) -> bpy.types.Object:
    mesh_data = bpy.data.meshes.new(name)
    mesh_bmesh.to_mesh(mesh_data)
    mesh_bmesh.free()
    mesh_object = bpy.data.objects.new(name, mesh_data)
    bpy.context.scene.collection.objects.link(mesh_object)

    if material:
        mesh_data.materials.append(material)

    return mesh_object


def make_box(name: str, center: tuple, size: tuple, material) -> bpy.types.Object:
    box_bmesh = bmesh.new()
    bmesh.ops.create_cube(box_bmesh, size=1.0)
    bmesh.ops.scale(box_bmesh, vec=size, verts=box_bmesh.verts)
    bmesh.ops.translate(box_bmesh, vec=center, verts=box_bmesh.verts)

    return object_from_bmesh(name, box_bmesh, material)


def make_span(name: str, minimum: tuple, maximum: tuple, material) -> bpy.types.Object:
    """Axis-aligned box from its min and max corners."""
    center = tuple((low + high) / 2.0 for low, high in zip(minimum, maximum))
    size = tuple(high - low for low, high in zip(minimum, maximum))

    return make_box(name, center, size, material)


def make_mirrored_span(name: str, minimum: tuple, maximum: tuple, material) -> None:
    """Span on the +X side plus its mirror on -X (minimum.x and maximum.x given for the +X side)."""
    stem, separator, suffix = name.partition("-")

    make_span(f"{stem}R{separator}{suffix}", minimum, maximum, material)
    make_span(f"{stem}L{separator}{suffix}", (-maximum[0], minimum[1], minimum[2]), (-minimum[0], maximum[1], maximum[2]), material)


def make_profile_prism(name: str, profile_xz: list, depth: float, transform: Matrix, material) -> bpy.types.Object:
    """Extrude a closed XZ polygon along +Y by depth, then place it with transform."""
    prism_bmesh = bmesh.new()
    front_vertices = [prism_bmesh.verts.new((x, 0.0, z)) for x, z in profile_xz]
    front_face = prism_bmesh.faces.new(front_vertices)
    extruded = bmesh.ops.extrude_face_region(prism_bmesh, geom=[front_face])
    moved_vertices = [element for element in extruded["geom"] if isinstance(element, bmesh.types.BMVert)]

    bmesh.ops.translate(prism_bmesh, vec=(0.0, depth, 0.0), verts=moved_vertices)
    bmesh.ops.recalc_face_normals(prism_bmesh, faces=prism_bmesh.faces)
    bmesh.ops.transform(prism_bmesh, matrix=transform, verts=prism_bmesh.verts)

    return object_from_bmesh(name, prism_bmesh, material)


def make_vertical_prism(name: str, profile_xy: list, bottom: float, height: float, material) -> bpy.types.Object:
    """Extrude a closed XY polygon (plan view) upward from bottom by height."""
    prism_bmesh = bmesh.new()
    floor_vertices = [prism_bmesh.verts.new((x, y, bottom)) for x, y in profile_xy]
    floor_face = prism_bmesh.faces.new(floor_vertices)
    extruded = bmesh.ops.extrude_face_region(prism_bmesh, geom=[floor_face])
    moved_vertices = [element for element in extruded["geom"] if isinstance(element, bmesh.types.BMVert)]

    bmesh.ops.translate(prism_bmesh, vec=(0.0, 0.0, height), verts=moved_vertices)
    bmesh.ops.recalc_face_normals(prism_bmesh, faces=prism_bmesh.faces)

    return object_from_bmesh(name, prism_bmesh, material)


def rectangle_profile(width: float, height: float) -> list:
    half = width / 2.0

    return [(-half, 0.0), (half, 0.0), (half, height), (-half, height)]


def round_arch_profile(width: float, spring_height: float, segments: int = 16) -> list:
    half = width / 2.0
    arc = [(half * math.cos(math.pi * step / segments), spring_height + half * math.sin(math.pi * step / segments)) for step in range(segments + 1)]

    return [(-half, 0.0), (half, 0.0)] + arc


def segmental_arc(width: float, spring_height: float, rise: float) -> tuple:
    """Circle center height, radius and half-angle of a segmental arch."""
    half = width / 2.0
    radius = (half * half + rise * rise) / (2.0 * rise)
    center_height = spring_height + rise - radius
    half_angle = math.asin(half / radius)

    return center_height, radius, half_angle


def segmental_arch_profile(width: float, spring_height: float, rise: float, segments: int = 12) -> list:
    center_height, radius, half_angle = segmental_arc(width, spring_height, rise)
    angles = [math.pi / 2.0 - half_angle + 2.0 * half_angle * step / segments for step in range(segments + 1)]
    arc = [(radius * math.cos(angle), center_height + radius * math.sin(angle)) for angle in angles]

    return [(-width / 2.0, 0.0), (width / 2.0, 0.0)] + arc


def make_cone(name: str, base_center: tuple, radius: float, height: float, sides: int, material, rotation: float = 0.0, top_radius: float = 0.0) -> bpy.types.Object:
    cone_bmesh = bmesh.new()
    bmesh.ops.create_cone(cone_bmesh, cap_ends=True, segments=sides, radius1=radius, radius2=top_radius, depth=height)
    bmesh.ops.rotate(cone_bmesh, verts=cone_bmesh.verts, matrix=Matrix.Rotation(rotation, 3, "Z"))
    bmesh.ops.translate(cone_bmesh, vec=(base_center[0], base_center[1], base_center[2] + height / 2.0), verts=cone_bmesh.verts)

    return object_from_bmesh(name, cone_bmesh, material)


def make_cylinder(name: str, base_center: tuple, radius: float, height: float, sides: int, material) -> bpy.types.Object:
    cylinder_bmesh = bmesh.new()
    bmesh.ops.create_cone(cylinder_bmesh, cap_ends=True, segments=sides, radius1=radius, radius2=radius, depth=height)
    bmesh.ops.translate(cylinder_bmesh, vec=(base_center[0], base_center[1], base_center[2] + height / 2.0), verts=cylinder_bmesh.verts)

    return object_from_bmesh(name, cylinder_bmesh, material)


def make_sphere(name: str, center: tuple, radius: float, material) -> bpy.types.Object:
    sphere_bmesh = bmesh.new()
    bmesh.ops.create_uvsphere(sphere_bmesh, u_segments=16, v_segments=10, radius=radius)
    bmesh.ops.translate(sphere_bmesh, vec=center, verts=sphere_bmesh.verts)

    return object_from_bmesh(name, sphere_bmesh, material)


def facing_transform(position: tuple, facing: str) -> Matrix:
    """Opening profile is drawn facing -Y; rotate it to face the wall direction."""
    rotations = {"-Y": 0.0, "+Y": math.pi, "+X": math.pi / 2.0, "-X": -math.pi / 2.0}

    return Matrix.Translation(position) @ Matrix.Rotation(rotations[facing], 4, "Z")


def carve(target: bpy.types.Object, cutters: list) -> None:
    for cutter in cutters:
        modifier = target.modifiers.new(cutter.name, "BOOLEAN")
        modifier.operation = "DIFFERENCE"
        modifier.solver = "EXACT"
        modifier.object = cutter

    bpy.context.view_layer.objects.active = target

    for modifier in list(target.modifiers):
        bpy.ops.object.modifier_apply(modifier=modifier.name)

    for cutter in cutters:
        bpy.data.objects.remove(cutter, do_unlink=True)


def map_uvs_per_face(mesh_object: bpy.types.Object, meters_per_tile: float) -> None:
    """Planar UVs in each face's own frame: U horizontal, V up the face (walls) or down the slope (roofs)."""
    uv_bmesh = bmesh.new()
    uv_bmesh.from_mesh(mesh_object.data)
    uv_layer = uv_bmesh.loops.layers.uv.verify()

    for face in uv_bmesh.faces:
        horizontal = face.normal.cross(Vector((0, 0, 1)))
        u_axis = horizontal.normalized() if horizontal.length > 0.01 else Vector((1, 0, 0))
        v_axis = face.normal.cross(u_axis).normalized() if horizontal.length > 0.01 else Vector((0, 1, 0))

        for loop in face.loops:
            world = mesh_object.matrix_world @ loop.vert.co
            loop[uv_layer].uv = (world.dot(u_axis) / meters_per_tile, world.dot(v_axis) / meters_per_tile)

    uv_bmesh.to_mesh(mesh_object.data)
    uv_bmesh.free()


# ---------- reusable pieces ----------

def wall_opening(name: str, profile: list, position: tuple, facing: str, wall_depth: float, pane_material, cutters: list, pane_depth: float = 0.5) -> None:
    """Cut an opening through (or into) a wall and set a pane at pane_depth (0 = outer face, 1 = inner face)."""
    transform = facing_transform(position, facing)

    cutters.append(make_profile_prism(name + "_cut", profile, wall_depth + 0.4, transform @ Matrix.Translation((0, -0.2, 0)), None))

    if pane_material:
        make_profile_prism(name + "_pane", profile, 0.05, transform @ Matrix.Translation((0, wall_depth * pane_depth, 0)), pane_material)


def make_voussoirs(name: str, center: Vector, radius: float, start_angle: float, end_angle: float, count: int, radial_size: float, front_y: float, depth: float, material, frame: Matrix = None) -> None:
    """Ring of blocks around an arch in the local XZ plane, protruding toward local -Y.

    material may be a list to alternate colours; frame places the ring on a wall that is not the facade.
    """
    block_materials = material if isinstance(material, list) else [material]
    frame = frame or Matrix.Identity(4)
    arc_step = (end_angle - start_angle) / count
    block_length = (radius + radial_size / 2.0) * arc_step * 0.86

    for block_index in range(count):
        angle = start_angle + arc_step * (block_index + 0.5)
        radial_center = radius + radial_size / 2.0
        position = Vector((center.x + radial_center * math.cos(angle), front_y + depth / 2.0, center.z + radial_center * math.sin(angle)))
        block = make_box(f"{name}{block_index}", (0, 0, 0), (block_length, depth, radial_size), block_materials[block_index % len(block_materials)])
        block.matrix_world = frame @ Matrix.Translation(position) @ Matrix.Rotation(math.pi / 2.0 - angle, 4, "Y")


def make_balustrade(name: str, start: tuple, end: tuple, bottom: float, materials: dict) -> None:
    """Plinth rail, turned balusters and a top rail between two plan points."""
    start_vector = Vector((start[0], start[1], 0.0))
    direction = Vector((end[0], end[1], 0.0)) - start_vector
    length = direction.length
    rotation = Matrix.Rotation(math.atan2(direction.y, direction.x), 4, "Z")
    middle = start_vector + direction / 2.0
    baluster_count = max(2, int(length / 0.32))

    make_box(name + "Plinth", (0, 0, 0), (length, 0.36, 0.16), materials["trim"]).matrix_world = Matrix.Translation(middle + Vector((0, 0, bottom + 0.08))) @ rotation
    make_box(name + "Rail", (0, 0, 0), (length + 0.1, 0.42, 0.14), materials["trim"]).matrix_world = Matrix.Translation(middle + Vector((0, 0, bottom + 0.88))) @ rotation

    for baluster_index in range(baluster_count):
        position = start_vector + direction * ((baluster_index + 0.5) / baluster_count)
        make_cone(f"{name}Baluster{baluster_index}", (position.x, position.y, bottom + 0.16), 0.09, 0.65, 8, materials["trim"], top_radius=0.06)


def make_cross(name: str, base: tuple, height: float, thickness: float, material, front_offset: float = 0.0) -> None:
    arm_length = height * 0.48

    make_box(name + "Upright", (base[0], base[1] + front_offset, base[2] + height / 2.0), (thickness, thickness, height), material)
    make_box(name + "Arm", (base[0], base[1] + front_offset, base[2] + height * 0.7), (arm_length, thickness, thickness), material)


# ---------- cathedral parts ----------

def build_podium(materials: dict) -> None:
    make_span("Plinth", (-HALF_WIDTH, 0.0, 0.0), (HALF_WIDTH, BODY_LENGTH, BASE), materials["stone"])
    make_cylinder("ApsePlinth", (0, BODY_LENGTH, 0), APSE_RADIUS + WALL, BASE, 32, materials["stone"])
    make_span("NaveFloor", (-HALF_WIDTH + WALL, FACADE_DEPTH - 0.1, BASE), (HALF_WIDTH - WALL, BODY_LENGTH, BASE + 0.02), materials["floor"])

    for step_index in range(STEP_COUNT):
        step_front = -(STEP_COUNT - step_index) * STEP_TREAD
        make_span(f"Step{step_index}", (-9.0, step_front, 0.0), (9.0, 0.0, (step_index + 1) * STEP_RISE), materials["stone"])


def build_facade_center(materials: dict) -> None:
    """Portal, balustrade band, twin segmental windows and the stepped gable between the towers."""
    window_bottom = BASE + 8.2
    window_spring = BASE + 12.4
    window_width = 2.3
    window_rise = 0.6
    window_centers = (-1.35, 1.35)
    facade = make_span("FacadeCenter", (-CENTER_HALF, 0.0, BASE), (CENTER_HALF, FACADE_DEPTH, BASE + NAVE_WALL_TOP), materials["wall"])
    cutters = []
    portal_center = Vector((0.0, 0.0, BASE + PORTAL_SPRING))

    wall_opening("Portal", round_arch_profile(PORTAL_WIDTH, PORTAL_SPRING), (0, 0, BASE), "-Y", FACADE_DEPTH, None, cutters)

    for window_index, window_x in enumerate(window_centers):
        profile = segmental_arch_profile(window_width, window_spring - window_bottom, window_rise)
        center_height, radius, half_angle = segmental_arc(window_width, window_spring, window_rise)
        wall_opening(f"ArchWindow{window_index}", profile, (window_x, 0, window_bottom), "-Y", FACADE_DEPTH, materials["glass"], cutters)
        make_voussoirs(f"ArchVoussoir{window_index}", Vector((window_x, 0, center_height)), radius, math.pi / 2.0 - half_angle - 0.12, math.pi / 2.0 + half_angle + 0.12, 9, 0.45, -0.2, 0.3, materials["trim"])

        for fin_offset in (-0.58, 0.0, 0.58):
            make_span(f"ArchFin{window_index}{fin_offset:+.1f}", (window_x + fin_offset - 0.09, 0.15, window_bottom), (window_x + fin_offset + 0.09, 0.45, window_spring), materials["trim"])

    carve(facade, cutters)

    make_voussoirs("PortalVoussoir", portal_center, PORTAL_WIDTH / 2.0, 0.0, math.pi, 13, 0.7, -0.3, 0.35, materials["trim"])
    make_mirrored_span("PortalJamb", (PORTAL_WIDTH / 2.0, -0.3, BASE), (PORTAL_WIDTH / 2.0 + 0.7, 0.05, BASE + PORTAL_SPRING), materials["trim"])
    make_balustrade("ArchBalustrade", (-CENTER_HALF, -0.25), (CENTER_HALF, -0.25), BASE + 7.2, materials)
    make_span("ArchSill", (-CENTER_HALF, -0.5, BASE + 7.05), (CENTER_HALF, 0.1, BASE + 7.2), materials["trim"])

    for column_x in (-0.3, 0.3):
        make_cylinder(f"ArchColumn{column_x:+.1f}", (column_x, -0.3, window_bottom), 0.17, window_spring - window_bottom + 0.3, 12, materials["trim"])

    gable_steps = [(5.6, NAVE_WALL_TOP, 16.3), (3.8, 16.3, 17.1), (1.8, 17.1, 18.8)]

    for step_index, (width, bottom, top) in enumerate(gable_steps):
        make_span(f"GableStep{step_index}", (-width / 2.0, -0.1, BASE + bottom), (width / 2.0, FACADE_DEPTH, BASE + top), materials["wall"])
        make_span(f"GableCoping{step_index}", (-width / 2.0 - 0.1, -0.2, BASE + top), (width / 2.0 + 0.1, FACADE_DEPTH + 0.1, BASE + top + 0.12), materials["trim"])

    make_cross("GableRelief", (0, -0.1, BASE + 17.3), 1.4, 0.18, materials["trim"], front_offset=-0.05)


def build_portal_doors(materials: dict) -> None:
    """Carved double doors, both leaves swung open against the narthex walls."""
    leaf_width = PORTAL_WIDTH / 2.0 - 0.05
    leaf_height = PORTAL_SPRING

    for side_sign in (-1, 1):
        leaf_x = side_sign * (PORTAL_WIDTH / 2.0 - 0.08)
        make_span(f"DoorLeaf{side_sign:+d}", (leaf_x - 0.06, FACADE_DEPTH, BASE + 0.02), (leaf_x + 0.06, FACADE_DEPTH + leaf_width, BASE + leaf_height), materials["wood"])

        for panel_index in range(3):
            panel_bottom = BASE + 0.4 + panel_index * 1.2
            make_span(f"DoorPanel{side_sign:+d}{panel_index}", (leaf_x - side_sign * 0.1 - 0.03, FACADE_DEPTH + 0.3, panel_bottom), (leaf_x - side_sign * 0.1 + 0.03, FACADE_DEPTH + leaf_width - 0.3, panel_bottom + 0.9), materials["wood"])


def build_tower(side_sign: int, materials: dict) -> None:
    tag = "L" if side_sign < 0 else "R"
    inner_x = CENTER_HALF
    outer_x = TOWER_OUTER
    middle_x = side_sign * (inner_x + outer_x) / 2.0
    center_y = NARTHEX_DEPTH / 2.0
    side_facing = "+X" if side_sign > 0 else "-X"
    tower_base = make_span(f"TowerBase{tag}", (min(side_sign * inner_x, side_sign * outer_x), 0.0, BASE), (max(side_sign * inner_x, side_sign * outer_x), NARTHEX_DEPTH, BASE + TOWER_BASE_TOP), materials["wall"])
    cutters = []

    for slit_offset in (-0.65, 0.0, 0.65):
        wall_opening(f"TowerSlit{tag}{slit_offset:+.1f}", rectangle_profile(0.36, 13.5), (middle_x + slit_offset, 0, BASE + 1.5), "-Y", 0.5, materials["slit_glass"], cutters, pane_depth=1.0)

    for slit_offset in (-0.5, 0.5):
        wall_opening(f"TowerSideSlit{tag}{slit_offset:+.1f}", rectangle_profile(0.36, 3.6), (side_sign * outer_x, center_y + slit_offset, BASE + AISLE_TOP + 1.4), side_facing, 0.5, materials["slit_glass"], cutters, pane_depth=1.0)

    carve(tower_base, cutters)

    make_span(f"TowerPierInner{tag}", (middle_x - 2.1, -0.3, BASE), (middle_x - 1.2, 0.0, BASE + 15.8), materials["trim"])
    make_span(f"TowerPierOuter{tag}", (middle_x + 1.2, -0.3, BASE), (middle_x + 2.1, 0.0, BASE + 15.8), materials["trim"])

    for fin_offset in (-0.325, 0.325):
        make_span(f"TowerFin{tag}{fin_offset:+.1f}", (middle_x + fin_offset - 0.11, -0.22, BASE + 1.2), (middle_x + fin_offset + 0.11, 0.0, BASE + TOWER_BASE_TOP + 0.6), materials["trim"])

    make_span(f"TowerBaseCornice{tag}", (middle_x - 2.3, -0.4, BASE + TOWER_BASE_TOP), (middle_x + 2.3, NARTHEX_DEPTH + 0.2, BASE + TOWER_BASE_TOP + 0.35), materials["trim"])
    build_tower_upper(tag, Vector((middle_x, center_y, BASE + TOWER_BASE_TOP + 0.35)), materials)


def build_tower_upper(tag: str, base_center: Vector, materials: dict) -> None:
    """Belfry stage with overshooting corner fins, clock stage, stepped crown and cross."""
    belfry_half = 1.7
    belfry_top = 8.65
    belfry = make_span(f"Belfry{tag}", (base_center.x - belfry_half, base_center.y - belfry_half, base_center.z), (base_center.x + belfry_half, base_center.y + belfry_half, base_center.z + belfry_top), materials["wall"])
    cutters = []
    faces = {
        "-Y": Vector((0, -belfry_half, 0)),
        "+Y": Vector((0, belfry_half, 0)),
        "-X": Vector((-belfry_half, 0, 0)),
        "+X": Vector((belfry_half, 0, 0)),
    }
    corner_offsets = [(-1, -1), (1, -1), (1, 1), (-1, 1)]

    for (facing, face_offset), slit_offset in itertools.product(faces.items(), (-0.42, 0.42)):
        lateral = Vector((slit_offset, 0, 0)) if facing in ("-Y", "+Y") else Vector((0, slit_offset, 0))
        position = base_center + face_offset + lateral + Vector((0, 0, 1.1))
        wall_opening(f"BelfrySlit{tag}{facing}{slit_offset:+.1f}", rectangle_profile(0.34, 6.4), tuple(position), facing, 0.5, materials["dark"], cutters, pane_depth=1.0)

    carve(belfry, cutters)

    for corner_index, (corner_x, corner_y) in enumerate(corner_offsets):
        corner = (base_center.x + corner_x * belfry_half, base_center.y + corner_y * belfry_half)
        make_span(f"BelfryCornerFin{tag}{corner_index}", (corner[0] - 0.3, corner[1] - 0.3, base_center.z), (corner[0] + 0.3, corner[1] + 0.3, base_center.z + belfry_top + 0.6), materials["trim"])

    clock_half = 1.5
    clock_bottom = base_center.z + belfry_top
    clock_top = clock_bottom + 3.4
    make_span(f"ClockStage{tag}", (base_center.x - clock_half, base_center.y - clock_half, clock_bottom), (base_center.x + clock_half, base_center.y + clock_half, clock_top), materials["wall"])
    make_span(f"ClockCornice{tag}", (base_center.x - 1.75, base_center.y - 1.75, clock_top), (base_center.x + 1.75, base_center.y + 1.75, clock_top + 0.3), materials["trim"])

    for facing_index, facing_angle in enumerate((0.0, math.pi / 2.0, math.pi, -math.pi / 2.0)):
        build_clock(f"Clock{tag}{facing_index}", base_center, clock_half, clock_bottom + 1.8, facing_angle, materials)

    crown_steps = [(2.4, 0.6, "wall"), (1.5, 0.6, "trim"), (0.7, 0.4, "trim")]
    crown_bottom = clock_top + 0.3

    for step_index, (width, height, material_key) in enumerate(crown_steps):
        make_span(f"Crown{tag}{step_index}", (base_center.x - width / 2.0, base_center.y - width / 2.0, crown_bottom), (base_center.x + width / 2.0, base_center.y + width / 2.0, crown_bottom + height), materials[material_key])
        crown_bottom += height

    make_cross(f"TowerCross{tag}", (base_center.x, base_center.y, crown_bottom), 3.4, 0.28, materials["trim"])


def build_clock(name: str, tower_center: Vector, half_size: float, height: float, facing_angle: float, materials: dict) -> None:
    """White dial with dark rim and hands on one tower face; facing_angle 0 = facing -Y."""
    rotation = Matrix.Rotation(facing_angle, 4, "Z")
    face_center = tower_center.copy()
    face_center.z = height
    outward = rotation @ Vector((0, -1, 0))
    dial_transform = Matrix.Translation(face_center + outward * (half_size + 0.04)) @ rotation @ Matrix.Rotation(math.pi / 2.0, 4, "X")

    make_cylinder(name + "Rim", (0, 0, -0.06), 0.8, 0.08, 24, materials["dark"]).matrix_world = dial_transform
    make_cylinder(name + "Dial", (0, 0, -0.04), 0.7, 0.1, 24, materials["marble"]).matrix_world = dial_transform
    make_box(name + "HourHand", (0, 0, 0), (0.06, 0.04, 0.42), materials["dark"]).matrix_world = Matrix.Translation(face_center + outward * (half_size + 0.12)) @ rotation @ Matrix.Rotation(0.5, 4, "Y") @ Matrix.Translation((0, 0, 0.17))
    make_box(name + "MinuteHand", (0, 0, 0), (0.05, 0.04, 0.6), materials["dark"]).matrix_world = Matrix.Translation(face_center + outward * (half_size + 0.14)) @ rotation @ Matrix.Rotation(-1.9, 4, "Y") @ Matrix.Translation((0, 0, 0.26))


def build_aisle_front(side_sign: int, materials: dict) -> None:
    """Low aisle front with a rounded outer corner, stacked slit pairs and a balustrade on top."""
    tag = "L" if side_sign < 0 else "R"
    corner_radius = 1.0
    front = make_span(f"AisleFront{tag}", (min(side_sign * TOWER_OUTER, side_sign * (HALF_WIDTH - corner_radius)), 0.0, BASE), (max(side_sign * TOWER_OUTER, side_sign * (HALF_WIDTH - corner_radius)), FACADE_DEPTH, BASE + AISLE_TOP), materials["wall"])
    cutters = []
    slit_rows = (1.5, 4.2, 6.9, 9.6)
    slit_columns = (7.55, 8.35)

    for row_height, column_x in itertools.product(slit_rows, slit_columns):
        wall_opening(f"AisleFrontSlit{tag}{row_height}{column_x}", rectangle_profile(0.3, 1.6), (side_sign * column_x, 0, BASE + row_height), "-Y", 0.5, materials["slit_glass"], cutters)

    carve(front, cutters)

    make_cylinder(f"AisleCorner{tag}", (side_sign * (HALF_WIDTH - corner_radius), corner_radius, BASE), corner_radius, AISLE_TOP, 20, materials["wall"])
    make_span(f"AisleFrontCornice{tag}", (min(side_sign * TOWER_OUTER, side_sign * (HALF_WIDTH - 1.0)), -0.15, BASE + AISLE_TOP), (max(side_sign * TOWER_OUTER, side_sign * (HALF_WIDTH - 1.0)), FACADE_DEPTH, BASE + AISLE_TOP + 0.25), materials["trim"])
    make_cylinder(f"AisleCornerCornice{tag}", (side_sign * (HALF_WIDTH - corner_radius), corner_radius, BASE + AISLE_TOP), corner_radius + 0.15, 0.25, 20, materials["trim"])
    make_balustrade(f"AisleBalustrade{tag}", (side_sign * TOWER_OUTER, 0.05), (side_sign * (HALF_WIDTH - corner_radius), 0.05), BASE + AISLE_TOP + 0.25, materials)


def build_side_wall(side_sign: int, materials: dict) -> None:
    tag = "L" if side_sign < 0 else "R"
    facing = "+X" if side_sign > 0 else "-X"
    inner_x = HALF_WIDTH - WALL
    wall = make_span(f"SideWall{tag}", (min(side_sign * inner_x, side_sign * HALF_WIDTH), 1.0, BASE), (max(side_sign * inner_x, side_sign * HALF_WIDTH), BODY_LENGTH, BASE + AISLE_TOP), materials["wall"])
    cutters = []
    fin_positions = [NARTHEX_DEPTH] + PIER_Y + [BODY_LENGTH - 0.5]

    for bay_y, slit_offset in itertools.product(BAY_CENTERS, (-0.4, 0.4)):
        wall_opening(f"AisleWindow{tag}{bay_y}{slit_offset:+.1f}", rectangle_profile(0.38, 7.6), (side_sign * HALF_WIDTH, bay_y + slit_offset, BASE + 1.8), facing, WALL, materials["glass"], cutters)

    carve(wall, cutters)

    for fin_y in fin_positions:
        make_span(f"SideFin{tag}{fin_y}", (min(side_sign * HALF_WIDTH, side_sign * (HALF_WIDTH + 0.3)), fin_y - 0.4, BASE), (max(side_sign * HALF_WIDTH, side_sign * (HALF_WIDTH + 0.3)), fin_y + 0.4, BASE + AISLE_TOP + 0.25), materials["trim"])

    make_span(f"SideParapet{tag}", (min(side_sign * inner_x, side_sign * HALF_WIDTH), 2.0, BASE + AISLE_TOP), (max(side_sign * inner_x, side_sign * HALF_WIDTH), BODY_LENGTH, BASE + AISLE_TOP + 1.0), materials["wall"])
    make_span(f"SideCoping{tag}", (min(side_sign * (inner_x - 0.05), side_sign * (HALF_WIDTH + 0.1)), 2.0, BASE + AISLE_TOP + 1.0), (max(side_sign * (inner_x - 0.05), side_sign * (HALF_WIDTH + 0.1)), BODY_LENGTH + 0.1, BASE + AISLE_TOP + 1.15), materials["trim"])
    make_span(f"AisleRoof{tag}", (min(side_sign * NAVE_HALF, side_sign * inner_x), 1.0, BASE + AISLE_TOP), (max(side_sign * NAVE_HALF, side_sign * inner_x), BODY_LENGTH, BASE + AISLE_TOP + 0.4), materials["trim"])
    make_span(f"AisleBackWall{tag}", (min(side_sign * NAVE_HALF, side_sign * HALF_WIDTH), BODY_LENGTH - WALL, BASE), (max(side_sign * NAVE_HALF, side_sign * HALF_WIDTH), BODY_LENGTH, BASE + AISLE_TOP), materials["wall"])


def build_nave(materials: dict) -> None:
    """Arcade walls with round arches on round columns, clerestory slits, coffered ceiling and the tiled roof."""
    nave_roof_profile = [(-NAVE_HALF - 0.9, BASE + NAVE_WALL_TOP - 0.1), (0.0, BASE + NAVE_WALL_TOP + 2.2), (NAVE_HALF + 0.9, BASE + NAVE_WALL_TOP - 0.1)]
    coffer_ribs_y = [NARTHEX_DEPTH - 2.7 + 2.7 * rib_index for rib_index in range(12)]

    for side_sign, facing in ((-1, "-X"), (1, "+X")):
        build_arcade_wall(side_sign, facing, materials)

    for rib_y in coffer_ribs_y:
        make_span(f"CofferRibAcross{rib_y:.1f}", (-NAVE_HALF, rib_y - 0.15, BASE + NAVE_CEILING - 0.35), (NAVE_HALF, rib_y + 0.15, BASE + NAVE_CEILING), materials["trim"])

    for rib_x in (-3.0, -1.5, 0.0, 1.5, 3.0):
        make_span(f"CofferRibAlong{rib_x:+.1f}", (rib_x - 0.15, 1.0, BASE + NAVE_CEILING - 0.35), (rib_x + 0.15, BODY_LENGTH, BASE + NAVE_CEILING), materials["trim"])

    make_span("NaveCeiling", (-NAVE_HALF - WALL, 1.0, BASE + NAVE_CEILING), (NAVE_HALF + WALL, BODY_LENGTH, BASE + NAVE_CEILING + 0.4), materials["trim"])
    make_span("NarthexRoof", (-CENTER_HALF, FACADE_DEPTH, BASE + NAVE_WALL_TOP - 0.2), (CENTER_HALF, NARTHEX_DEPTH, BASE + NAVE_WALL_TOP + 0.2), materials["trim"])
    make_profile_prism("NaveRoof", nave_roof_profile, BODY_LENGTH - NARTHEX_DEPTH + 0.6, Matrix.Translation((0, NARTHEX_DEPTH, 0)), materials["roof"])
    make_span("NaveCornice", (-NAVE_HALF - WALL - 0.25, NARTHEX_DEPTH, BASE + NAVE_WALL_TOP - 0.3), (NAVE_HALF + WALL + 0.25, BODY_LENGTH + 0.2, BASE + NAVE_WALL_TOP), materials["trim"])
    make_span("NaveBackUpper", (-NAVE_HALF - WALL, BODY_LENGTH - WALL, BASE + NAVE_CEILING), (NAVE_HALF + WALL, BODY_LENGTH, BASE + NAVE_WALL_TOP), materials["wall"])


def build_arcade_wall(side_sign: int, facing: str, materials: dict) -> None:
    """One nave side wall: round arches into the aisle, painted voussoirs, columns with gilded capitals."""
    tag = "L" if side_sign < 0 else "R"
    nave_face_x = side_sign * NAVE_HALF
    wall = make_span(f"ArcadeWall{tag}", (min(nave_face_x, side_sign * (NAVE_HALF + WALL)), NARTHEX_DEPTH, BASE), (max(nave_face_x, side_sign * (NAVE_HALF + WALL)), BODY_LENGTH, BASE + NAVE_WALL_TOP), materials["wall"])
    nave_side_facing = "+X" if side_sign < 0 else "-X"
    cutters = []

    for bay_y in BAY_CENTERS:
        wall_opening(f"Arch{tag}{bay_y}", round_arch_profile(ARCH_WIDTH, ARCH_SPRING), (side_sign * (NAVE_HALF + WALL), bay_y, BASE), facing, WALL, None, cutters)

    for bay_y, slit_offset in itertools.product(BAY_CENTERS, (-0.35, 0.35)):
        wall_opening(f"Clerestory{tag}{bay_y}{slit_offset:+.1f}", rectangle_profile(0.32, 1.9), (side_sign * (NAVE_HALF + WALL), bay_y + slit_offset, BASE + AISLE_TOP + 0.6), facing, WALL, materials["glass"], cutters)

    carve(wall, cutters)

    for bay_y in BAY_CENTERS:
        frame = facing_transform((nave_face_x, bay_y, 0.0), nave_side_facing)
        make_voussoirs(f"ArchVoussoir{tag}{bay_y}", Vector((0, 0, BASE + ARCH_SPRING)), ARCH_WIDTH / 2.0, 0.0, math.pi, 11, 0.5, -0.12, 0.14, [materials["paint_red"], materials["paint_ochre"]], frame)

    for pier_y in PIER_Y:
        build_column(side_sign * (NAVE_HALF + WALL / 2.0), pier_y, f"{tag}{pier_y}", materials)

    make_span(f"Frieze{tag}", (min(nave_face_x, nave_face_x - side_sign * 0.06), NARTHEX_DEPTH, BASE + 9.2), (max(nave_face_x, nave_face_x - side_sign * 0.06), BODY_LENGTH - WALL, BASE + 9.7), materials["paint_ochre"])


def build_column(column_x: float, column_y: float, tag: str, materials: dict) -> None:
    capital_bottom = BASE + ARCH_SPRING - 0.55

    make_box(f"ColumnPlinth{tag}", (column_x, column_y, BASE + 0.2), (1.1, 1.1, 0.4), materials["trim"])
    make_cylinder(f"ColumnShaft{tag}", (column_x, column_y, BASE + 0.4), 0.42, capital_bottom - BASE - 0.4, 16, materials["trim"])
    make_cone(f"ColumnCapital{tag}", (column_x, column_y, capital_bottom), 0.44, 0.45, 16, materials["gold"], top_radius=0.62)
    make_box(f"ColumnAbacus{tag}", (column_x, column_y, BASE + ARCH_SPRING - 0.05), (1.2, 1.2, 0.1), materials["gold"])


def build_apse(materials: dict) -> None:
    """Half-round apse wall with three tall slits, closing the nave behind the chancel."""
    segments = 24
    apse_top = NAVE_CEILING + 0.4
    outer_arc = [((APSE_RADIUS + WALL) * math.cos(math.pi * step / segments), BODY_LENGTH + (APSE_RADIUS + WALL) * math.sin(math.pi * step / segments)) for step in range(segments + 1)]
    inner_arc = [(APSE_RADIUS * math.cos(math.pi * step / segments), BODY_LENGTH + APSE_RADIUS * math.sin(math.pi * step / segments)) for step in reversed(range(segments + 1))]
    apse = make_vertical_prism("Apse", outer_arc + inner_arc, BASE, apse_top, materials["wall"])
    cutters = []

    for window_index, angle_degrees in enumerate((-40, 0, 40)):
        angle = math.radians(angle_degrees)
        direction = Vector((math.sin(angle), math.cos(angle), 0))
        position = Vector((0, BODY_LENGTH, BASE + 3.0)) + direction * (APSE_RADIUS + WALL)
        transform = Matrix.Translation(position) @ Matrix.Rotation(math.pi - angle, 4, "Z")
        cutters.append(make_profile_prism(f"ApseCut{window_index}", rectangle_profile(0.45, 8.5), WALL + 0.6, transform @ Matrix.Translation((0, -0.3, 0)), None))
        make_profile_prism(f"ApseGlass{window_index}", rectangle_profile(0.45, 8.5), 0.05, transform @ Matrix.Translation((0, WALL / 2.0, 0)), materials["glass"])

    carve(apse, cutters)

    make_cylinder("ApseRoof", (0, BODY_LENGTH, BASE + apse_top), APSE_RADIUS + WALL + 0.2, 0.4, 32, materials["trim"])


def build_chancel(materials: dict) -> None:
    """Raised chancel with altar and a stepped reredos that repeats the facade gable."""
    floor_top = BASE + CHANCEL_HEIGHT
    step_count = 5
    reredos_y = BODY_LENGTH + APSE_RADIUS - 0.9
    reredos_steps = [(4.4, 5.6), (3.0, 7.4), (1.4, 9.7)]

    make_span("ChancelFloor", (-NAVE_HALF, CHANCEL_FRONT, BASE), (NAVE_HALF, BODY_LENGTH, floor_top), materials["marble"])
    make_cylinder("ChancelApseFloor", (0, BODY_LENGTH, BASE), APSE_RADIUS, CHANCEL_HEIGHT, 32, materials["marble"])

    for step_index in range(step_count):
        step_front = CHANCEL_FRONT - (step_count - step_index) * 0.4
        make_span(f"ChancelStep{step_index}", (-3.6, step_front, BASE), (3.6, CHANCEL_FRONT, BASE + (step_index + 1) * CHANCEL_HEIGHT / step_count), materials["marble"])

    make_box("Altar", (0, BODY_LENGTH - 1.4, floor_top + 0.5), (2.6, 1.0, 1.0), materials["marble"])
    make_box("AltarFrontal", (0, BODY_LENGTH - 1.92, floor_top + 0.5), (1.8, 0.06, 0.7), materials["gold"])

    for candle_x in (-1.0, 1.0):
        make_cylinder(f"Candlestick{candle_x:+.0f}", (candle_x, BODY_LENGTH - 1.4, floor_top + 1.0), 0.05, 0.55, 8, materials["gold"])

    for step_index, (width, height) in enumerate(reredos_steps):
        make_span(f"Reredos{step_index}", (-width / 2.0, reredos_y, floor_top), (width / 2.0, reredos_y + 0.6, floor_top + height), materials["marble"])
        make_span(f"ReredosCoping{step_index}", (-width / 2.0 - 0.08, reredos_y - 0.08, floor_top + height), (width / 2.0 + 0.08, reredos_y + 0.6, floor_top + height + 0.12), materials["gold"])

    make_cross("ReredosCross", (0, reredos_y, floor_top + 6.2), 3.0, 0.2, materials["gold"], front_offset=-0.12)

    for panel_x, panel_width, panel_height in ((0.0, 1.0, 3.0), (-1.65, 0.8, 2.2), (1.65, 0.8, 2.2)):
        make_span(f"PaintingFrame{panel_x:+.1f}", (panel_x - panel_width / 2.0 - 0.1, reredos_y - 0.06, floor_top + 1.5), (panel_x + panel_width / 2.0 + 0.1, reredos_y, floor_top + 1.7 + panel_height), materials["gold"])
        make_span(f"Painting{panel_x:+.1f}", (panel_x - panel_width / 2.0, reredos_y - 0.09, floor_top + 1.6), (panel_x + panel_width / 2.0, reredos_y - 0.06, floor_top + 1.6 + panel_height), materials["painting"])


def build_pews(materials: dict) -> None:
    rows = [13.0 + row_index * 1.0 for row_index in range(12)]
    blocks = (-2.3, 2.3)
    pew_length = 2.6

    for block_x, row_y in itertools.product(blocks, rows):
        tag = f"{block_x:+.0f}_{row_y:.0f}"
        make_box(f"PewSeat{tag}", (block_x, row_y, BASE + 0.45), (pew_length, 0.45, 0.07), materials["wood"])
        make_box(f"PewBack{tag}", (block_x, row_y + 0.24, BASE + 0.75), (pew_length, 0.07, 0.55), materials["wood"])
        make_box(f"PewEndA{tag}", (block_x - pew_length / 2.0, row_y + 0.05, BASE + 0.47), (0.08, 0.6, 0.94), materials["wood"])
        make_box(f"PewEndB{tag}", (block_x + pew_length / 2.0, row_y + 0.05, BASE + 0.47), (0.08, 0.6, 0.94), materials["wood"])


def build_statues(materials: dict) -> None:
    """Two robed figures on pedestals flanking the stairs."""
    for side_sign in (-1, 1):
        statue_x = side_sign * 9.6
        statue_y = -2.0
        tag = "L" if side_sign < 0 else "R"
        make_box(f"Pedestal{tag}", (statue_x, statue_y, 0.7), (1.1, 1.1, 1.4), materials["stone"])
        make_box(f"PedestalCap{tag}", (statue_x, statue_y, 1.45), (1.3, 1.3, 0.1), materials["trim"])
        make_cone(f"StatueRobe{tag}", (statue_x, statue_y, 1.5), 0.42, 1.45, 16, materials["marble"], top_radius=0.2)
        make_cone(f"StatueShoulders{tag}", (statue_x, statue_y, 2.85), 0.26, 0.22, 16, materials["marble"], top_radius=0.12)
        make_sphere(f"StatueHead{tag}", (statue_x, statue_y, 3.2), 0.15, materials["marble"])


# ---------- collision ----------

def build_colliders() -> None:
    """Simple boxes for the player and the navmesh; names ending in -colonly become static bodies in Godot."""
    stairs_length = math.hypot(STEP_COUNT * STEP_TREAD, BASE)
    stairs = make_box("Stairs-colonly", (0, -STEP_COUNT * STEP_TREAD / 2.0, BASE / 2.0 - 0.06), (18.0, stairs_length, 0.1), None)
    stairs.rotation_euler.x = math.atan2(BASE, STEP_COUNT * STEP_TREAD)
    chancel_steps = make_box("ChancelSteps-colonly", (0, CHANCEL_FRONT - 1.0, BASE + CHANCEL_HEIGHT / 2.0 - 0.06), (7.2, math.hypot(2.0, CHANCEL_HEIGHT), 0.1), None)
    chancel_steps.rotation_euler.x = math.atan2(CHANCEL_HEIGHT, 2.0)

    make_span("Plinth-colonly", (-HALF_WIDTH, 0.0, 0.0), (HALF_WIDTH, BODY_LENGTH, BASE), None)
    make_span("ApsePlinth-colonly", (-APSE_RADIUS - WALL, BODY_LENGTH, 0.0), (APSE_RADIUS + WALL, BODY_LENGTH + APSE_RADIUS + WALL, BASE), None)
    make_span("Chancel-colonly", (-NAVE_HALF, CHANCEL_FRONT, BASE), (NAVE_HALF, BODY_LENGTH + APSE_RADIUS, BASE + CHANCEL_HEIGHT), None)
    make_span("Altar-colonly", (-1.3, BODY_LENGTH - 1.9, BASE + CHANCEL_HEIGHT), (1.3, BODY_LENGTH - 0.9, BASE + CHANCEL_HEIGHT + 1.0), None)
    make_span("Reredos-colonly", (-2.2, BODY_LENGTH + APSE_RADIUS - 0.9, BASE + CHANCEL_HEIGHT), (2.2, BODY_LENGTH + APSE_RADIUS, BASE + 7.0), None)
    make_span("Lintel-colonly", (-PORTAL_WIDTH / 2.0, 0.0, BASE + PORTAL_SPRING), (PORTAL_WIDTH / 2.0, FACADE_DEPTH, BASE + NAVE_WALL_TOP), None)
    make_mirrored_span("Jamb-colonly", (PORTAL_WIDTH / 2.0, -0.3, BASE), (CENTER_HALF, FACADE_DEPTH, BASE + NAVE_WALL_TOP), None)
    make_mirrored_span("Tower-colonly", (CENTER_HALF, -0.3, 0.0), (TOWER_OUTER, NARTHEX_DEPTH, BASE + TOWER_BASE_TOP), None)
    make_mirrored_span("AisleFront-colonly", (TOWER_OUTER, 0.0, 0.0), (HALF_WIDTH, FACADE_DEPTH, BASE + AISLE_TOP), None)
    make_mirrored_span("SideWall-colonly", (HALF_WIDTH - WALL, 0.0, 0.0), (HALF_WIDTH + 0.3, BODY_LENGTH, BASE + AISLE_TOP), None)
    make_mirrored_span("BackWall-colonly", (NAVE_HALF, BODY_LENGTH - WALL, 0.0), (HALF_WIDTH, BODY_LENGTH, BASE + AISLE_TOP), None)
    make_mirrored_span("Pews-colonly", (1.0, 12.7, BASE), (3.6, 24.5, BASE + 1.0), None)
    make_mirrored_span("DoorLeaf-colonly", (PORTAL_WIDTH / 2.0 - 0.15, FACADE_DEPTH, BASE), (PORTAL_WIDTH / 2.0, FACADE_DEPTH + PORTAL_WIDTH / 2.0, BASE + PORTAL_SPRING), None)

    make_mirrored_span("ArcadeEndFront-colonly", (NAVE_HALF, NARTHEX_DEPTH, BASE), (NAVE_HALF + WALL, BAY_CENTERS[0] - ARCH_WIDTH / 2.0, BASE + ARCH_SPRING), None)
    make_mirrored_span("ArcadeEndBack-colonly", (NAVE_HALF, BAY_CENTERS[-1] + ARCH_WIDTH / 2.0, BASE), (NAVE_HALF + WALL, BODY_LENGTH, BASE + ARCH_SPRING), None)

    for side_sign, pier_y in itertools.product((-1, 1), PIER_Y):
        make_box(f"Pier{side_sign:+d}{pier_y}-colonly", (side_sign * (NAVE_HALF + WALL / 2.0), pier_y, BASE + ARCH_SPRING / 2.0), (1.1, 1.1, ARCH_SPRING), None)

    for segment_index in range(8):
        angle = math.pi * (segment_index + 0.5) / 8.0
        radius = APSE_RADIUS + WALL / 2.0
        segment = make_box(f"ApseWall{segment_index}-colonly", (0, 0, 0), (2.0 * radius * math.sin(math.pi / 16.0) + 0.2, WALL, NAVE_CEILING), None)
        segment.matrix_world = Matrix.Translation((radius * math.cos(angle), BODY_LENGTH + radius * math.sin(angle), BASE + NAVE_CEILING / 2.0)) @ Matrix.Rotation(angle - math.pi / 2.0, 4, "Z")

    for side_sign in (-1, 1):
        make_box(f"Statue{side_sign:+d}-colonly", (side_sign * 9.6, -2.0, 1.6), (1.1, 1.1, 3.2), None)


# ---------- export ----------

def merge_meshes_by_material(name_prefix: str) -> None:
    """Join all visible meshes that share a material into one object (one draw call per material)."""
    visible_meshes = [scene_object for scene_object in bpy.data.objects if scene_object.type == "MESH" and not scene_object.name.endswith("-colonly")]
    meshes_by_material = defaultdict(list)

    for mesh_object in visible_meshes:
        meshes_by_material[mesh_object.data.materials[0].name].append(mesh_object)

    for material_name, mesh_objects in meshes_by_material.items():
        with bpy.context.temp_override(active_object=mesh_objects[0], selected_editable_objects=mesh_objects):
            bpy.ops.object.join()

        mesh_objects[0].name = name_prefix + material_name.removeprefix("M_")


def finalize_objects(materials: dict) -> None:
    """World-space UVs per material, then merge per material."""
    tile_sizes = {"stone": 4.5, "wall": 4.0, "trim": 2.5, "roof": 3.0, "floor": 2.4, "glass": 3.0, "wood": 2.0}
    meters_per_tile = {materials[key].name: size for key, size in tile_sizes.items()}
    visible_meshes = [scene_object for scene_object in bpy.data.objects if scene_object.type == "MESH" and not scene_object.name.endswith("-colonly")]

    bpy.context.view_layer.update()

    for mesh_object in visible_meshes:
        map_uvs_per_face(mesh_object, meters_per_tile.get(mesh_object.data.materials[0].name, 2.0))

    merge_meshes_by_material("Cathedral")


def build_cathedral() -> Path:
    output_path = OUTPUT_DIR / "cathedral.gltf"

    bpy.ops.wm.read_factory_settings(use_empty=True)

    materials = build_materials()
    build_podium(materials)
    build_facade_center(materials)
    build_portal_doors(materials)
    build_tower(-1, materials)
    build_tower(1, materials)
    build_aisle_front(-1, materials)
    build_aisle_front(1, materials)
    build_side_wall(-1, materials)
    build_side_wall(1, materials)
    build_nave(materials)
    build_apse(materials)
    build_chancel(materials)
    build_pews(materials)
    build_statues(materials)
    build_colliders()
    finalize_objects(materials)

    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_texture_dir="textures", export_yup=True)

    return output_path


if __name__ == "__main__":
    print(f"BUILT cathedral -> {build_cathedral()}")
