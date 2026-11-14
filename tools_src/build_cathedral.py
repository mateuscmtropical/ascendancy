"""Model the hub cathedral (original gothic design) and export it as art/town/cathedral.gltf.

Built from solid volumes; windows and portals are boolean recesses with stained glass at the back.
Textures come from the CC0 Medieval Village MegaKit (stone, plaster) plus two derived here
(slate tiles from the round tiles, procedural stained glass).
Blender coords: facade faces -Y, nave runs toward +Y. Collision boxes are named *-colonly for Godot.

Usage:
  blender -b --factory-startup -P tools_src/build_cathedral.py
"""

import math
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

PLINTH = 0.6
NAVE_HALF_WIDTH = 6.0
NAVE_LENGTH = 34.0
NAVE_HEIGHT = 18.0
NAVE_RIDGE = 9.0
AISLE_OUTER = 11.0
AISLE_HEIGHT = 9.0
BAY_CENTERS = [8.25, 13.75, 19.25, 24.75, 30.25]
PIER_POSITIONS = [5.5, 11.0, 16.5, 22.0, 27.5, 33.0]
TOWER_CENTER_X = 9.5
TOWER_HALF = 3.5
TOWER_FRONT = -1.0
TOWER_HEIGHT = 30.0
SPIRE_TOP = 48.0

SLATE_DARK = numpy.array([0.21, 0.23, 0.29])
SLATE_LIGHT = numpy.array([0.50, 0.54, 0.62])
GLASS_COLORS = numpy.array([
    [0.12, 0.25, 0.75], [0.10, 0.20, 0.60], [0.75, 0.12, 0.15], [0.95, 0.70, 0.15],
    [0.15, 0.55, 0.30], [0.45, 0.20, 0.65], [0.20, 0.45, 0.85],
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


def make_slate_image():
    source = load_kit_image("T_RoundTiles_BaseColor.png", True)
    size = source.size[0]
    pixels = numpy.array(source.pixels[:]).reshape(size, size, 4)
    luminance = (pixels[..., :3] @ numpy.array([0.3, 0.59, 0.11]))[..., None]
    normalized = numpy.clip((luminance - 0.15) / 0.5, 0.0, 1.0)
    slate = SLATE_DARK + (SLATE_LIGHT - SLATE_DARK) * normalized
    rgba = numpy.concatenate([slate, numpy.ones((size, size, 1))], axis=2)

    return save_generated_image("T_SlateTiles_BaseColor", rgba, size)


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
    stone_image = make_tinted_image("T_Brick_BaseColor.png", "T_CathedralStone_BaseColor", (1.08, 1.06, 1.0), (0.09, 0.08, 0.06))
    trim_image = make_tinted_image("T_Plaster_BaseColor.png", "T_CathedralTrim_BaseColor", (1.0, 1.0, 1.0), (0.08, 0.08, 0.08))

    return {
        "stone": make_material("M_CathedralStone", stone_image, load_kit_image("T_Brick_Normal.png", False), load_kit_image("T_Brick_Roughness.png", False)),
        "trim": make_material("M_CathedralTrim", trim_image, load_kit_image("T_Plaster_Normal.png", False)),
        "slate": make_material("M_CathedralSlate", make_slate_image(), load_kit_image("T_RoundTiles_Normal.png", False)),
        "glass": make_material("M_StainedGlass", make_stained_glass_image(), emission=1.5),
        "gold": make_plain_material("M_Gold", (0.95, 0.72, 0.28), 1.0, 0.3),
        "wood": make_material("M_DoorWood", load_kit_image("T_WoodTrim_BaseColor.png", True), load_kit_image("T_WoodTrim_Normal.png", False)),
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


def pointed_arch_profile(width: float, spring_height: float, segments: int = 10) -> list:
    """Equilateral gothic arch: each side is an arc of radius = width centered on the opposite springer."""
    half = width / 2.0
    angles = [math.radians(180.0 - 60.0 * step / segments) for step in range(segments + 1)]
    left_arc = [(half + width * math.cos(angle), spring_height + width * math.sin(angle)) for angle in angles]
    right_arc = [(-x, z) for x, z in reversed(left_arc[:-1])]

    return [(-half, 0.0)] + left_arc + right_arc + [(half, 0.0)]


def arch_spring(width: float, height: float) -> float:
    return height - width * math.sin(math.radians(60.0))


def circle_profile(radius: float, segments: int = 32) -> list:
    return [(radius * math.cos(2 * math.pi * step / segments), radius * math.sin(2 * math.pi * step / segments)) for step in range(segments)]


def make_cone(name: str, base_center: tuple, radius: float, height: float, sides: int, material, rotation: float = 0.0) -> bpy.types.Object:
    cone_bmesh = bmesh.new()
    bmesh.ops.create_cone(cone_bmesh, cap_ends=True, segments=sides, radius1=radius, radius2=0.0, depth=height)
    bmesh.ops.rotate(cone_bmesh, verts=cone_bmesh.verts, matrix=Matrix.Rotation(rotation, 3, "Z"))
    bmesh.ops.translate(cone_bmesh, vec=(base_center[0], base_center[1], base_center[2] + height / 2.0), verts=cone_bmesh.verts)

    return object_from_bmesh(name, cone_bmesh, material)


def make_cylinder(name: str, base_center: tuple, radius: float, height: float, sides: int, material) -> bpy.types.Object:
    cylinder_bmesh = bmesh.new()
    bmesh.ops.create_cone(cylinder_bmesh, cap_ends=True, segments=sides, radius1=radius, radius2=radius, depth=height)
    bmesh.ops.translate(cylinder_bmesh, vec=(base_center[0], base_center[1], base_center[2] + height / 2.0), verts=cylinder_bmesh.verts)

    return object_from_bmesh(name, cylinder_bmesh, material)


def make_torus(name: str, center: Vector, major_radius: float, minor_radius: float, material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius, major_segments=40, minor_segments=8, location=center, rotation=(math.pi / 2.0, 0, 0))
    torus = bpy.context.active_object
    torus.name = name
    torus.data.materials.append(material)

    return torus


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


# ---------- cathedral parts ----------

def window_opening(name: str, position: tuple, facing: str, width: float, height: float, wall_depth: float, materials: dict, cutters: list) -> None:
    """Recessed pointed window: a cutter for the wall plus a stained glass pane at the back of the recess."""
    spring = arch_spring(width, height)
    profile = pointed_arch_profile(width, spring)
    transform = facing_transform(position, facing)
    cutters.append(make_profile_prism(name + "_cut", profile, wall_depth * 2.0, transform @ Matrix.Translation((0, -wall_depth, 0)), None))
    make_profile_prism(name + "_glass", profile, 0.05, transform @ Matrix.Translation((0, wall_depth * 0.85, 0)), materials["glass"])
    make_box(name + "_mullion", (0, 0, 0), (0.12, 0.12, spring), materials["trim"]).matrix_world = transform @ Matrix.Translation((0, wall_depth * 0.78, spring / 2.0))


def build_plinth_and_steps(materials: dict) -> None:
    make_box("Plinth", (0, 20.0, PLINTH / 2.0), (30.0, 44.0, PLINTH), materials["trim"])

    for step_index in range(3):
        step_height = PLINTH * (step_index + 1) / 3.0
        step_front = -3.5 + step_index * 0.5
        make_box(f"Step{step_index}", (0, (step_front - 2.0) / 2.0, step_height / 2.0), (18.0 - step_index, -2.0 - step_front, step_height), materials["trim"])

    make_box("Plinth-colonly", (0, 20.0, PLINTH / 2.0), (30.0, 44.0, PLINTH), None)
    ramp = make_box("Steps-colonly", (0, -2.75, PLINTH / 2.0 - 0.05), (18.0, 1.62, 0.1), None)
    ramp.rotation_euler.x = math.atan2(PLINTH, 1.5)


def build_nave(materials: dict) -> None:
    base = PLINTH
    nave = make_box("Nave", (0, (NAVE_LENGTH + 1.4) / 2.0, base + NAVE_HEIGHT / 2.0), (NAVE_HALF_WIDTH * 2, NAVE_LENGTH - 1.4, NAVE_HEIGHT), materials["stone"])
    cutters = []
    clerestory_bottom = base + AISLE_HEIGHT + 3.4

    for bay_index, bay_y in enumerate(BAY_CENTERS):
        window_opening(f"ClerestoryL{bay_index}", (-NAVE_HALF_WIDTH, bay_y, clerestory_bottom), "-X", 2.2, 4.6, 0.8, materials, cutters)
        window_opening(f"ClerestoryR{bay_index}", (NAVE_HALF_WIDTH, bay_y, clerestory_bottom), "+X", 2.2, 4.6, 0.8, materials, cutters)

    carve(nave, cutters)

    roof_profile = [(-NAVE_HALF_WIDTH - 0.5, base + NAVE_HEIGHT - 0.3), (0.0, base + NAVE_HEIGHT + NAVE_RIDGE), (NAVE_HALF_WIDTH + 0.5, base + NAVE_HEIGHT - 0.3)]
    make_profile_prism("NaveRoof", roof_profile, NAVE_LENGTH - 0.7, Matrix.Translation((0, 1.0, 0)), materials["slate"])
    make_box("NaveCornice", (0, (NAVE_LENGTH + 1.4) / 2.0, base + NAVE_HEIGHT - 0.25), (NAVE_HALF_WIDTH * 2 + 0.8, NAVE_LENGTH - 1.4, 0.5), materials["trim"])
    make_box("Nave-colonly", (0, 19.0, base + NAVE_HEIGHT / 2.0), (AISLE_OUTER * 2 + 4, 40.0, NAVE_HEIGHT), None)


def build_aisles(materials: dict) -> None:
    base = PLINTH
    aisle_center_x = (NAVE_HALF_WIDTH + AISLE_OUTER) / 2.0
    aisle_width = AISLE_OUTER - NAVE_HALF_WIDTH + 0.2
    aisle_length = NAVE_LENGTH - 6.0
    aisle_center_y = 6.0 + aisle_length / 2.0

    for side_sign, side_name, facing in ((-1, "L", "-X"), (1, "R", "+X")):
        aisle = make_box(f"Aisle{side_name}", (side_sign * aisle_center_x, aisle_center_y, base + AISLE_HEIGHT / 2.0), (aisle_width, aisle_length, AISLE_HEIGHT), materials["stone"])
        cutters = []

        for bay_index, bay_y in enumerate(BAY_CENTERS):
            window_opening(f"AisleWindow{side_name}{bay_index}", (side_sign * AISLE_OUTER, bay_y, base + 2.2), facing, 1.9, 5.2, 0.7, materials, cutters)

        carve(aisle, cutters)

        roof_profile = [(side_sign * (NAVE_HALF_WIDTH - 0.1), base + AISLE_HEIGHT + 3.0), (side_sign * (AISLE_OUTER + 0.6), base + AISLE_HEIGHT - 0.3), (side_sign * (NAVE_HALF_WIDTH - 0.1), base + AISLE_HEIGHT - 0.3)]
        make_profile_prism(f"AisleRoof{side_name}", roof_profile, aisle_length + 0.6, Matrix.Translation((0, 6.0 - 0.3, 0)), materials["slate"])


def build_flying_buttresses(materials: dict) -> None:
    base = PLINTH
    pier_x = AISLE_OUTER + 1.8
    pier_top = base + AISLE_HEIGHT + 4.0
    piers = [(side_sign, pier_y) for side_sign in (-1, 1) for pier_y in PIER_POSITIONS]

    for side_sign, pier_y in piers:
        tag = f"{'L' if side_sign < 0 else 'R'}{pier_y:.0f}"
        make_box(f"Pier{tag}", (side_sign * pier_x, pier_y, base + pier_top / 2.0 - base / 2.0), (1.4, 1.6, pier_top - base), materials["stone"])
        make_box(f"PierCap{tag}", (side_sign * pier_x, pier_y, pier_top + 0.2), (1.7, 1.9, 0.4), materials["trim"])
        make_cone(f"Pinnacle{tag}", (side_sign * pier_x, pier_y, pier_top + 0.4), 0.85, 4.2, 4, materials["trim"], math.pi / 4.0)
        make_box(f"Pilaster{tag}", (side_sign * (NAVE_HALF_WIDTH + 0.25), pier_y, base + NAVE_HEIGHT / 2.0 + 2.0), (0.6, 1.0, NAVE_HEIGHT - 4.0), materials["stone"])
        flyer_start = Vector((side_sign * (pier_x - 0.7), pier_y, pier_top - 0.6))
        flyer_end = Vector((side_sign * (NAVE_HALF_WIDTH + 0.5), pier_y, base + NAVE_HEIGHT - 2.0))
        flyer_vector = flyer_end - flyer_start
        flyer = make_box(f"Flyer{tag}", (0, 0, 0), (flyer_vector.length, 0.7, 0.55), materials["trim"])
        flyer.matrix_world = Matrix.Translation((flyer_start + flyer_end) / 2.0) @ Matrix.Rotation(side_sign * math.atan2(flyer_vector.z, abs(flyer_vector.x)), 4, "Y")


def build_apse(materials: dict) -> None:
    base = PLINTH
    apse = make_cylinder("Apse", (0, NAVE_LENGTH, base), NAVE_HALF_WIDTH, NAVE_HEIGHT - 2.0, 20, materials["stone"])
    cutters = []
    window_angles = [-60, -30, 0, 30, 60]

    for window_index, angle_degrees in enumerate(window_angles):
        angle = math.radians(angle_degrees)
        direction = Vector((math.sin(angle), math.cos(angle), 0))
        position = Vector((0, NAVE_LENGTH, base + 5.0)) + direction * NAVE_HALF_WIDTH
        rotation = Matrix.Translation(position) @ Matrix.Rotation(math.pi - angle, 4, "Z")
        profile = pointed_arch_profile(1.8, 7.0)
        cutters.append(make_profile_prism(f"ApseCut{window_index}", profile, 1.6, rotation @ Matrix.Translation((0, -0.8, 0)), None))
        make_profile_prism(f"ApseGlass{window_index}", profile, 0.05, rotation @ Matrix.Translation((0, 0.45, 0)), materials["glass"])

    carve(apse, cutters)
    make_cone("ApseRoof", (0, NAVE_LENGTH, base + NAVE_HEIGHT - 2.3), NAVE_HALF_WIDTH + 0.5, 7.5, 20, materials["slate"])


def build_facade(materials: dict) -> None:
    base = PLINTH
    facade = make_box("Facade", (0, 0.6, base + NAVE_HEIGHT / 2.0 + 1.0), (NAVE_HALF_WIDTH * 2, 1.6, NAVE_HEIGHT + 2.0), materials["stone"])
    cutters = []
    portal_layers = [(5.6, 9.6), (4.8, 8.8), (4.0, 8.0)]

    for layer_index, (width, height) in enumerate(portal_layers):
        layer_back = -0.2 + 0.45 * (layer_index + 1)
        cutters.append(make_profile_prism(f"PortalCut{layer_index}", pointed_arch_profile(width, arch_spring(width, height)), layer_back + 0.3, Matrix.Translation((0, -0.3, base)), None))

    make_profile_prism("PortalBack", pointed_arch_profile(4.0, arch_spring(4.0, 8.0)), 0.2, Matrix.Translation((0, 1.15, base)), materials["trim"])
    make_box("PortalDoors", (0, 1.1, base + 2.6), (3.6, 0.1, 5.2), materials["wood"])
    make_box("PortalLintel", (0, 1.05, base + 5.35), (4.0, 0.2, 0.3), materials["trim"])

    gallery_bottom = base + 11.0
    gallery_positions = [-4.0, -2.0, 0.0, 2.0, 4.0]

    for gallery_index, gallery_x in enumerate(gallery_positions):
        window_opening(f"Gallery{gallery_index}", (gallery_x, -0.2, gallery_bottom), "-Y", 1.3, 3.0, 0.6, materials, cutters)

    rose_center = Vector((0, -0.2, base + 18.3))
    cutters.append(make_profile_prism("RoseCut", circle_profile(3.4), 1.2, Matrix.Translation(rose_center + Vector((0, -0.6, 0))), None))
    make_profile_prism("RoseGlass", circle_profile(3.4), 0.05, Matrix.Translation(rose_center + Vector((0, 0.5, 0))), materials["glass"])
    make_torus("RoseRing", rose_center + Vector((0, 0.15, 0)), 3.35, 0.2, materials["trim"])
    make_torus("RoseInnerRing", rose_center + Vector((0, 0.3, 0)), 1.7, 0.12, materials["trim"])

    for spoke_index in range(8):
        spoke = make_box(f"RoseSpoke{spoke_index}", (0, 0, 0), (0.18, 0.2, 6.8), materials["trim"])
        spoke.matrix_world = Matrix.Translation(rose_center + Vector((0, 0.35, 0))) @ Matrix.Rotation(math.pi * spoke_index / 8.0, 4, "Y")

    make_cylinder("RoseHub", (0, 0, 0), 0.7, 0.3, 16, materials["trim"]).matrix_world = Matrix.Translation(rose_center + Vector((0, 0.35, 0))) @ Matrix.Rotation(math.pi / 2.0, 4, "X")
    carve(facade, cutters)

    gable_profile = [(-NAVE_HALF_WIDTH, base + NAVE_HEIGHT + 2.0), (0.0, base + NAVE_HEIGHT + NAVE_RIDGE + 2.5), (NAVE_HALF_WIDTH, base + NAVE_HEIGHT + 2.0)]
    make_profile_prism("FacadeGable", gable_profile, 1.4, Matrix.Translation((0, -0.1, 0)), materials["stone"])
    make_box("FacadeCornice", (0, 0.5, base + NAVE_HEIGHT + 2.1), (NAVE_HALF_WIDTH * 2 + 0.4, 1.9, 0.4), materials["trim"])
    make_cone("GablePinnacle", (0, 0.6, base + NAVE_HEIGHT + NAVE_RIDGE + 2.3), 0.6, 3.0, 4, materials["trim"], math.pi / 4.0)


def build_tower(side_sign: int, materials: dict) -> None:
    base = PLINTH
    tag = "L" if side_sign < 0 else "R"
    center = Vector((side_sign * TOWER_CENTER_X, TOWER_FRONT + TOWER_HALF, base))
    tower = make_box(f"Tower{tag}", (center.x, center.y, base + TOWER_HEIGHT / 2.0), (TOWER_HALF * 2, TOWER_HALF * 2, TOWER_HEIGHT), materials["stone"])
    cutters = []
    front_y = TOWER_FRONT
    side_x = center.x + side_sign * TOWER_HALF
    side_facing = "+X" if side_sign > 0 else "-X"

    spring = arch_spring(2.6, 4.6)
    cutters.append(make_profile_prism(f"SidePortalCut{tag}", pointed_arch_profile(2.6, spring), 1.6, Matrix.Translation((center.x, front_y - 0.4, base)), None))
    make_box(f"SidePortalDoor{tag}", (center.x, front_y + 1.05, base + 1.7), (2.4, 0.1, 3.4), materials["wood"])
    make_profile_prism(f"SidePortalBack{tag}", pointed_arch_profile(2.6, spring), 0.1, Matrix.Translation((center.x, front_y + 1.1, base)), materials["trim"])
    window_opening(f"TowerWindow{tag}", (center.x, front_y, base + 12.0), "-Y", 1.8, 5.0, 0.7, materials, cutters)
    window_opening(f"TowerSideWindow{tag}", (side_x, center.y, base + 12.0), side_facing, 1.8, 5.0, 0.7, materials, cutters)

    for belfry_offset in (-1.3, 1.3):
        window_opening(f"BelfryFront{tag}{belfry_offset:+.0f}", (center.x + belfry_offset, front_y, base + 21.0), "-Y", 1.6, 6.5, 0.8, materials, cutters)
        window_opening(f"BelfrySide{tag}{belfry_offset:+.0f}", (side_x, center.y + belfry_offset, base + 21.0), side_facing, 1.6, 6.5, 0.8, materials, cutters)

    carve(tower, cutters)

    corner_offsets = [(-1, -1), (1, -1), (1, 1), (-1, 1)]

    for corner_index, (corner_x, corner_y) in enumerate(corner_offsets):
        corner_position = (center.x + corner_x * (TOWER_HALF + 0.1), center.y + corner_y * (TOWER_HALF + 0.1))
        make_box(f"TowerButtress{tag}{corner_index}", (corner_position[0], corner_position[1], base + 13.0), (1.3, 1.3, 26.0), materials["stone"])
        make_box(f"TowerButtressCap{tag}{corner_index}", (corner_position[0], corner_position[1], base + 26.2), (1.5, 1.5, 0.4), materials["trim"])
        make_cone(f"TowerPinnacle{tag}{corner_index}", (corner_position[0], corner_position[1], base + TOWER_HEIGHT + 0.6), 0.75, 4.5, 4, materials["trim"], math.pi / 4.0)
        make_box(f"TowerPinnacleBase{tag}{corner_index}", (corner_position[0], corner_position[1], base + TOWER_HEIGHT + 0.3), (1.2, 1.2, 0.6), materials["trim"])

    make_box(f"TowerCornice{tag}", (center.x, center.y, base + TOWER_HEIGHT + 0.3), (TOWER_HALF * 2 + 0.8, TOWER_HALF * 2 + 0.8, 0.6), materials["trim"])
    make_cylinder(f"SpireDrum{tag}", (center.x, center.y, base + TOWER_HEIGHT + 0.6), TOWER_HALF - 0.4, 2.0, 8, materials["stone"])
    make_cone(f"Spire{tag}", (center.x, center.y, base + TOWER_HEIGHT + 2.6), TOWER_HALF - 0.2, SPIRE_TOP - TOWER_HEIGHT - 2.6, 8, materials["slate"], math.pi / 8.0)
    make_cylinder(f"FinialRod{tag}", (center.x, center.y, base + SPIRE_TOP - 0.5), 0.08, 2.2, 8, materials["gold"])
    make_cylinder(f"FinialBall{tag}", (center.x, center.y, base + SPIRE_TOP + 0.4), 0.35, 0.7, 12, materials["gold"])
    make_box(f"Tower{tag}-colonly", (center.x, center.y, base + TOWER_HEIGHT / 2.0), (TOWER_HALF * 2 + 1.4, TOWER_HALF * 2 + 1.4, TOWER_HEIGHT), None)


def build_crossing_spire(materials: dict) -> None:
    base = PLINTH
    crossing = (0, 24.0, base + NAVE_HEIGHT + NAVE_RIDGE - 2.0)

    make_cylinder("FlecheDrum", crossing, 1.3, 4.0, 8, materials["trim"])
    make_cone("Fleche", (crossing[0], crossing[1], crossing[2] + 4.0), 1.5, 8.0, 8, materials["slate"], math.pi / 8.0)
    make_cylinder("FlecheFinial", (crossing[0], crossing[1], crossing[2] + 11.5), 0.07, 1.6, 8, materials["gold"])


def build_string_courses(materials: dict) -> None:
    """Horizontal moulding bands that break the facade into storeys."""
    base = PLINTH
    facade_band_heights = [10.4, 14.45]
    tower_band_heights = [10.4, 19.6]

    for band_height in facade_band_heights:
        make_box(f"FacadeBand{band_height}", (0, -0.32, base + band_height), (NAVE_HALF_WIDTH * 2, 0.3, 0.35), materials["trim"])

    for band_height in tower_band_heights:
        for side_sign in (-1, 1):
            make_box(f"TowerBand{side_sign}{band_height}", (side_sign * TOWER_CENTER_X, TOWER_FRONT + TOWER_HALF, base + band_height), (TOWER_HALF * 2 + 0.3, TOWER_HALF * 2 + 0.3, 0.35), materials["trim"])


def finalize_objects(materials: dict) -> None:
    tile_sizes = {materials["stone"].name: 4.5, materials["trim"].name: 2.5, materials["slate"].name: 3.0, materials["glass"].name: 4.0}
    visible_meshes = [scene_object for scene_object in bpy.data.objects if scene_object.type == "MESH" and not scene_object.name.endswith("-colonly")]

    bpy.context.view_layer.update()

    for mesh_object in visible_meshes:
        material_name = mesh_object.data.materials[0].name if mesh_object.data.materials else ""
        map_uvs_per_face(mesh_object, tile_sizes.get(material_name, 2.0))


def build_cathedral() -> Path:
    output_path = OUTPUT_DIR / "cathedral.gltf"

    bpy.ops.wm.read_factory_settings(use_empty=True)

    materials = build_materials()
    build_plinth_and_steps(materials)
    build_nave(materials)
    build_aisles(materials)
    build_flying_buttresses(materials)
    build_apse(materials)
    build_facade(materials)
    build_tower(-1, materials)
    build_tower(1, materials)
    build_crossing_spire(materials)
    build_string_courses(materials)
    finalize_objects(materials)

    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_texture_dir="textures", export_yup=True)

    return output_path


if __name__ == "__main__":
    print(f"BUILT cathedral -> {build_cathedral()}")
