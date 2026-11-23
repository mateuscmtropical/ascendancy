"""Model the plaza props (fountains, lamp post, planter, park bench) and export them to art/town/.

Reuses the geometry helpers and stone textures of build_cathedral.py (run that first: it writes the textures).
Meshes named "Water" get the water shader in Godot; *-colonly boxes become collision.

Usage:
  blender -b --factory-startup -P tools_src/build_plaza_props.py
"""

import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_cathedral import (  # noqa: E402
    GENERATED_TEXTURES,
    OUTPUT_DIR,
    PROJECT_DIR,
    build_robed_figure,
    load_kit_image,
    make_box,
    make_cone,
    make_span,
    make_stair_ramp,
    make_cylinder,
    make_material,
    make_plain_material,
    make_sphere,
    map_uvs_per_face,
    merge_meshes_by_material,
    object_from_bmesh,
    save_generated_image,
)


def build_prop_materials() -> dict:
    stone_image = bpy.data.images.load(str(GENERATED_TEXTURES / "T_CathedralStone_BaseColor.png"))
    trim_image = bpy.data.images.load(str(GENERATED_TEXTURES / "T_CathedralTrim_BaseColor.png"))

    return {
        "stone": make_material("M_CathedralStone", stone_image, load_kit_image("T_Brick_Normal.png", False)),
        "trim": make_material("M_CathedralTrim", trim_image, load_kit_image("T_Plaster_Normal.png", False)),
        "water": make_plain_material("M_Water", (0.25, 0.55, 0.65), 0.0, 0.05),
        "water_basin": make_plain_material("M_WaterBasin", (0.25, 0.55, 0.65), 0.0, 0.05),
        "water_lower": make_plain_material("M_WaterLower", (0.25, 0.55, 0.65), 0.0, 0.05),
        "water_middle": make_plain_material("M_WaterMiddle", (0.25, 0.55, 0.65), 0.0, 0.05),
        "water_upper": make_plain_material("M_WaterUpper", (0.25, 0.55, 0.65), 0.0, 0.05),
        "water_jet": make_plain_material("M_WaterJet", (0.6, 0.85, 0.95), 0.0, 0.05),
        "water_curtain": make_plain_material("M_WaterCurtain", (0.6, 0.85, 0.95), 0.0, 0.05),
        "metal": make_plain_material("M_LampMetal", (0.08, 0.17, 0.13), 0.7, 0.45),
        "roof": make_material("M_CathedralRoof", bpy.data.images.load(str(GENERATED_TEXTURES / "T_CathedralRoof_BaseColor.png")), load_kit_image("T_RoundTiles_Normal.png", False)),
        "lamp_glass": make_lamp_glass_material(),
        "soil": make_plain_material("M_Soil", (0.22, 0.15, 0.10), 0.0, 1.0),
        "palm_trunk": make_plain_material("M_PalmTrunk", (0.3, 0.26, 0.21), 0.0, 0.95),
        "palm_leaf": make_two_sided_material("M_PalmLeaf", (0.07, 0.3, 0.07)),
        "wood": make_plain_material("M_PropWood", (0.2, 0.11, 0.06), 0.0, 0.7),
        "bench_wood": make_material("M_BenchWood", load_kit_image("T_WoodTrim_BaseColor.png", True), load_kit_image("T_WoodTrim_Normal.png", False)),
    }


def make_two_sided_material(name: str, color: tuple):
    material = make_plain_material(name, color, 0.0, 0.8)
    material.use_backface_culling = False

    return material


def make_lamp_glass_material():
    material = make_plain_material("M_LampGlass", (0.95, 0.94, 0.9), 0.0, 0.3)
    shader = material.node_tree.nodes["Principled BSDF"]

    shader.inputs["Emission Color"].default_value = (1.0, 0.93, 0.8, 1.0)
    shader.inputs["Emission Strength"].default_value = 0.6

    return material


def make_frustum(name: str, base_z: float, bottom_radius: float, top_radius: float, height: float, sides: int, material):
    import bmesh

    frustum_bmesh = bmesh.new()
    bmesh.ops.create_cone(frustum_bmesh, cap_ends=True, segments=sides, radius1=bottom_radius, radius2=top_radius, depth=height)
    bmesh.ops.translate(frustum_bmesh, vec=(0, 0, base_z + height / 2.0), verts=frustum_bmesh.verts)

    from build_cathedral import object_from_bmesh

    return object_from_bmesh(name, frustum_bmesh, material)


def make_octagon_ring(name: str, outer_radius: float, inner_radius: float, height: float, material):
    ring = make_cylinder(name, (0, 0, 0), outer_radius, height, 8, material)
    hole = make_cylinder(name + "_hole", (0, 0, -0.1), inner_radius, height + 0.2, 8, None)
    modifier = ring.modifiers.new("hole", "BOOLEAN")

    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = hole
    bpy.context.view_layer.objects.active = ring
    bpy.ops.object.modifier_apply(modifier="hole")
    bpy.data.objects.remove(hole, do_unlink=True)
    ring.rotation_euler.z = math.pi / 8.0

    return ring


NYMPH_SOURCE = PROJECT_DIR / "art" / "characters" / "villager_female.gltf"  # CC0, montada por build_characters.py
NYMPH_PARTS = ("Head_Skin", "Hair_Buns", "Eyebrows", "Female_Peasant_Arms", "Female_Peasant_Body", "Female_Peasant_Feet")
NYMPH_POSE = [("upperarm_l", "Y", 66.0), ("upperarm_r", "Y", -66.0), ("lowerarm_l", "X", -78.0), ("lowerarm_r", "X", -78.0), ("lowerarm_l", "Z", -24.0), ("lowerarm_r", "Z", 24.0), ("Head", "X", 12.0)]
FOUNTAIN_STATUE_RADIUS = 3.45


def make_round_ring(name: str, outer_radius: float, inner_radius: float, base_z: float, height: float, material, segments: int = 40):
    """Round wall: annulus extruded from base_z, smooth all around."""
    import bmesh

    from build_cathedral import object_from_bmesh

    ring_bmesh = bmesh.new()
    loops = [[ring_bmesh.verts.new((radius * math.cos(2.0 * math.pi * index / segments), radius * math.sin(2.0 * math.pi * index / segments), z)) for index in range(segments)] for radius, z in ((outer_radius, base_z), (outer_radius, base_z + height), (inner_radius, base_z + height), (inner_radius, base_z))]

    for lower, upper in zip(loops, loops[1:]):
        for index in range(segments):
            following = (index + 1) % segments
            ring_bmesh.faces.new([lower[index], lower[following], upper[following], upper[index]])

    return object_from_bmesh(name, ring_bmesh, material)


GRAVITY = 9.8
JET_TUBE_SIDES = 6
JET_PATH_STEPS = 22
CURTAIN_SEGMENTS = 72
CURTAIN_ROWS = 14
TANK_WATER_TOP = 0.42
# Os mesmos pontos de impacto vao para os shaders das superficies (art/materials/water_fountain_*.tres:
# curtain_ring_radius, jet_landing_*); se mudar um numero aqui, atualizar o material correspondente.
CROWN_JETS = {"count": 8, "start": (0.05, 5.62), "horizontal_speed": 0.91, "vertical_speed": 2.5, "land_z": 4.91, "radius": 0.028}
BOWL_JETS = {"count": 12, "start": (1.95, 3.29), "horizontal_speed": 1.965, "vertical_speed": 3.5, "land_z": TANK_WATER_TOP + 0.02, "radius": 0.05}
CENTER_JET = {"base": (0.0, 0.0, 5.6), "height": 0.95, "radius": 0.04}
# Cada cortina nasce na borda externa (1.03 * raio) da bacia e cai na superficie da de baixo.
UPPER_CURTAIN = {"radius": 0.9, "top_z": 4.91, "outward_speed": 0.3, "bottom_z": 4.3}
MIDDLE_CURTAIN = {"radius": 1.51, "top_z": 4.31, "outward_speed": 0.4, "bottom_z": 3.27}
LOWER_CURTAIN = {"radius": 2.39, "top_z": 3.28, "outward_speed": 0.45, "bottom_z": TANK_WATER_TOP + 0.02}
# Fonte pequena da rotatória (mesma receita): jato central e 4 arcos do pináculo caindo na taça, véu da taça ao tanque.
SMALL_BASIN_WATER_TOP = 0.47
SMALL_CENTER_JET = {"base": (0.0, 0.0, 2.08), "height": 0.55, "radius": 0.025}
SMALL_FINIAL_JETS = {"count": 4, "start": (0.08, 1.98), "horizontal_speed": 0.5, "vertical_speed": 1.2, "land_z": 1.62, "radius": 0.022}
SMALL_BOWL_CURTAIN = {"radius": 0.82, "top_z": 1.64, "outward_speed": 0.35, "bottom_z": SMALL_BASIN_WATER_TOP + 0.02}


def ballistic_path(azimuth: float, jet: dict) -> list:
    """Points of a thrown-water arc (gravity only) from the nozzle until it reaches land_z."""
    start_radius, start_z = jet["start"]
    drop = start_z - jet["land_z"]
    flight_time = (jet["vertical_speed"] + math.sqrt(jet["vertical_speed"] ** 2 + 2.0 * GRAVITY * drop)) / GRAVITY
    times = [flight_time * step / JET_PATH_STEPS for step in range(JET_PATH_STEPS + 1)]
    direction = Vector((math.cos(azimuth), math.sin(azimuth), 0.0))
    origin = direction * start_radius + Vector((0.0, 0.0, start_z))

    return [
        origin + direction * jet["horizontal_speed"] * time + Vector((0.0, 0.0, jet["vertical_speed"] * time - 0.5 * GRAVITY * time * time))
        for time in times
    ]


def jet_azimuths(jet: dict) -> list:
    return [math.tau * index / jet["count"] for index in range(jet["count"])]


def tube_ring(path: list, point_index: int, radius: float) -> list:
    """Hexagon of vertex positions around one path point, tapering toward the tail."""
    last = len(path) - 1
    tangent = (path[min(point_index + 1, last)] - path[max(point_index - 1, 0)]).normalized()
    side = tangent.cross(Vector((0.0, 0.0, 1.0)))
    side = side.normalized() if side.length > 1e-4 else Vector((1.0, 0.0, 0.0))
    lift = side.cross(tangent)
    ring_radius = radius * (1.0 - 0.45 * point_index / last)

    return [
        path[point_index] + ring_radius * (math.cos(math.tau * corner / JET_TUBE_SIDES) * side + math.sin(math.tau * corner / JET_TUBE_SIDES) * lift)
        for corner in range(JET_TUBE_SIDES)
    ]


def add_quad(target_bmesh, corners: tuple, uvs: tuple, uv_layer) -> None:
    face = target_bmesh.faces.new(corners)

    for loop, uv in zip(face.loops, uvs):
        loop[uv_layer].uv = uv
    face.smooth = True


def add_tube(stream_bmesh, path: list, stream_index: int, radius: float, uv_layer) -> None:
    """Hexagonal tube along path. UV.x = stream_index * 2 + around (0..1); UV.y = 0..1 along the stream."""
    last = len(path) - 1
    rings = [[stream_bmesh.verts.new(position) for position in tube_ring(path, point_index, radius)] for point_index in range(last + 1)]

    for ring_index, side_index in [(ring, side) for ring in range(last) for side in range(JET_TUBE_SIDES)]:
        next_side = (side_index + 1) % JET_TUBE_SIDES
        corners = (rings[ring_index][side_index], rings[ring_index][next_side], rings[ring_index + 1][next_side], rings[ring_index + 1][side_index])
        left = stream_index * 2.0 + side_index / JET_TUBE_SIDES
        right = stream_index * 2.0 + (side_index + 1) / JET_TUBE_SIDES
        uvs = ((left, ring_index / last), (right, ring_index / last), (right, (ring_index + 1) / last), (left, (ring_index + 1) / last))
        add_quad(stream_bmesh, corners, uvs, uv_layer)


def make_jet_mesh(material, center_jet: dict = CENTER_JET, arc_jets: tuple = (CROWN_JETS, BOWL_JETS)):
    """Every jet of a fountain as tapered tubes: the vertical centre jet plus the ballistic arcs."""
    stream_bmesh = bmesh.new()
    uv_layer = stream_bmesh.loops.layers.uv.new("UVMap")
    base = Vector(center_jet["base"])
    center_path = [base + Vector((0.0, 0.0, center_jet["height"] * step / JET_PATH_STEPS)) for step in range(JET_PATH_STEPS + 1)]
    arc_paths = [(ballistic_path(azimuth, jet), jet["radius"]) for jet in arc_jets for azimuth in jet_azimuths(jet)]

    for stream_index, (path, radius) in enumerate([(center_path, center_jet["radius"])] + arc_paths):
        add_tube(stream_bmesh, path, stream_index, radius, uv_layer)

    jet_object = object_from_bmesh("WaterJets", stream_bmesh, material)
    jet_object["keep_uvs"] = True

    return jet_object


def curtain_rows(curtain: dict) -> list:
    """Rim-to-pool vertex rings of a falling sheet: slow outward drift plus gravity."""
    fall_time = math.sqrt(2.0 * (curtain["top_z"] - curtain["bottom_z"]) / GRAVITY)
    rows = []

    for row in range(CURTAIN_ROWS + 1):
        time = fall_time * row / CURTAIN_ROWS
        row_radius = curtain["radius"] + curtain["outward_speed"] * time
        row_height = curtain["top_z"] - 0.5 * GRAVITY * time * time
        angles = [math.tau * column / CURTAIN_SEGMENTS for column in range(CURTAIN_SEGMENTS)]
        rows.append([(row_radius * math.cos(angle), row_radius * math.sin(angle), row_height) for angle in angles])

    return rows


def add_curtain(curtain_bmesh, curtain: dict, uv_layer) -> None:
    """Thin falling sheet around a rim. UV.x = around (0..1); UV.y = 0..1 down the fall."""
    rows = [[curtain_bmesh.verts.new(position) for position in row] for row in curtain_rows(curtain)]

    for row, column in [(row, column) for row in range(CURTAIN_ROWS) for column in range(CURTAIN_SEGMENTS)]:
        next_column = (column + 1) % CURTAIN_SEGMENTS
        corners = (rows[row][column], rows[row][next_column], rows[row + 1][next_column], rows[row + 1][column])
        left = column / CURTAIN_SEGMENTS
        right = (column + 1) / CURTAIN_SEGMENTS
        uvs = ((left, row / CURTAIN_ROWS), (right, row / CURTAIN_ROWS), (right, (row + 1) / CURTAIN_ROWS), (left, (row + 1) / CURTAIN_ROWS))
        add_quad(curtain_bmesh, corners, uvs, uv_layer)


def make_curtain_mesh(material, curtains: tuple = (UPPER_CURTAIN, MIDDLE_CURTAIN, LOWER_CURTAIN)):
    curtain_bmesh = bmesh.new()
    uv_layer = curtain_bmesh.loops.layers.uv.new("UVMap")

    for curtain in curtains:
        add_curtain(curtain_bmesh, curtain, uv_layer)

    curtain_object = object_from_bmesh("WaterCurtains", curtain_bmesh, material)
    curtain_object["keep_uvs"] = True

    return curtain_object


def build_fountain_bowl(name: str, base_z: float, radius: float, materials: dict, lobes: int, water_key: str) -> None:
    """Shallow bowl on a baluster stem, with a rolled rim, a ring of lobes under it and water inside."""
    make_frustum(f"{name}Stem", base_z, radius * 0.2, radius * 0.13, radius * 0.3, 12, materials["trim"])
    make_sphere(f"{name}Knop", (0, 0, base_z + radius * 0.32), radius * 0.17, materials["trim"])
    make_frustum(f"{name}Cup", base_z + radius * 0.4, radius * 0.22, radius, radius * 0.28, 28, materials["trim"])
    make_round_ring(f"{name}Rim", radius * 1.03, radius * 0.92, base_z + radius * 0.68, radius * 0.06 + 0.03, materials["trim"], 28)
    make_cylinder("Water", (0, 0, base_z + radius * 0.6), radius * 0.94, radius * 0.14 + 0.02, 28, materials[water_key])

    for lobe_index in range(lobes):
        angle = 2.0 * math.pi * lobe_index / lobes
        lobe = make_sphere(f"{name}Lobe{lobe_index}", (radius * 0.72 * math.cos(angle), radius * 0.72 * math.sin(angle), base_z + radius * 0.52), radius * 0.16, materials["trim"])
        lobe.scale = (1.0, 1.0, 0.8)


def build_fountain_statues(materials: dict) -> None:
    """Four water bearers on round plinths standing in the tank, facing outward."""
    figure, bones = build_robed_figure("Nymph", NYMPH_SOURCE, NYMPH_PARTS, NYMPH_POSE, materials["trim"])
    hands = (bones["hand_l"] + bones["hand_r"]) / 2.0

    figure.append(make_sphere("NymphJar", (hands.x, hands.y - 0.06, hands.z - 0.02), 0.13, materials["trim"]))
    figure.append(make_frustum("NymphJarNeck", hands.z + 0.07, 0.05, 0.085, 0.12, 10, materials["trim"]))
    figure[-1].data.transform(Matrix.Translation((hands.x, hands.y - 0.06, 0.0)))

    for statue_index in range(4):
        angle = math.pi / 4.0 + statue_index * math.pi / 2.0
        spot = (FOUNTAIN_STATUE_RADIUS * math.cos(angle), FOUNTAIN_STATUE_RADIUS * math.sin(angle))
        placement = Matrix.Translation((spot[0], spot[1], 0.95)) @ Matrix.Rotation(angle + math.pi / 2.0, 4, "Z")

        make_cylinder(f"NymphPlinth{statue_index}", (spot[0], spot[1], 0.0), 0.62, 0.8, 16, materials["stone"])
        make_cylinder(f"NymphPlinthCap{statue_index}", (spot[0], spot[1], 0.8), 0.7, 0.12, 16, materials["trim"])

        for part in figure:
            copy = bpy.data.objects.new(f"{part.name}{statue_index}", part.data.copy())
            copy.data.transform(placement)
            bpy.context.scene.collection.objects.link(copy)

    for part in figure:
        bpy.data.objects.remove(part, do_unlink=True)


def build_large_fountain(materials: dict) -> None:
    """Chafariz: wide round tank with a sitting rim, four water bearers and a three-tier fountain on a panelled drum."""
    tank_radius = 5.5

    make_round_ring("TankStep", tank_radius + 0.45, tank_radius - 0.1, 0.0, 0.14, materials["trim"])
    make_round_ring("TankWall", tank_radius, tank_radius - 0.42, 0.0, 0.52, materials["stone"])
    make_round_ring("TankRim", tank_radius + 0.08, tank_radius - 0.52, 0.52, 0.1, materials["trim"])
    make_cylinder("TankFloor", (0, 0, 0), tank_radius - 0.4, 0.12, 40, materials["stone"])
    make_cylinder("Water", (0, 0, 0.12), tank_radius - 0.42, 0.3, 40, materials["water_basin"])

    make_cylinder("DrumBase", (0, 0, 0.1), 1.55, 0.45, 8, materials["trim"]).rotation_euler.z = math.pi / 8.0
    make_cylinder("Drum", (0, 0, 0.55), 1.15, 0.85, 8, materials["stone"]).rotation_euler.z = math.pi / 8.0
    make_cylinder("DrumCornice", (0, 0, 1.4), 1.35, 0.14, 8, materials["trim"]).rotation_euler.z = math.pi / 8.0

    for panel_index in range(8):
        angle = panel_index * math.pi / 4.0
        apothem = 1.15 * math.cos(math.pi / 8.0)
        panel = make_box(f"DrumPanel{panel_index}", (0, 0, 0), (0.56, 0.06, 0.56), materials["trim"])
        panel.location = (apothem * math.cos(angle), apothem * math.sin(angle), 0.98)
        panel.rotation_euler.z = angle + math.pi / 2.0
        boss = make_sphere(f"DrumBoss{panel_index}", ((apothem + 0.04) * math.cos(angle), (apothem + 0.04) * math.sin(angle), 0.98), 0.12, materials["trim"])
        boss.scale = (1.0, 1.0, 1.0)

    build_fountain_bowl("LowerBowl", 1.54, 2.3, materials, 12, "water_lower")
    build_fountain_bowl("MiddleBowl", 3.2, 1.45, materials, 10, "water_middle")
    build_fountain_bowl("UpperBowl", 4.25, 0.85, materials, 8, "water_upper")
    make_frustum("FinialUrn", 4.85, 0.1, 0.2, 0.25, 12, materials["trim"])
    make_sphere("FinialBud", (0, 0, 5.22), 0.16, materials["trim"])
    make_cone("FinialSpout", (0, 0, 5.3), 0.07, 0.3, 10, materials["trim"])
    build_fountain_statues(materials)
    make_jet_mesh(materials["water_jet"])
    make_curtain_mesh(materials["water_curtain"])
    make_cylinder("Fountain-colonly", (0, 0, 0), tank_radius + 0.5, 3.0, 24, None)


def build_small_fountain(materials: dict) -> None:
    make_octagon_ring("BasinWall", 2.0, 1.7, 0.6, materials["stone"])
    make_octagon_ring("BasinRim", 2.08, 1.62, 0.1, materials["trim"]).location.z = 0.6
    make_cylinder("BasinFloor", (0, 0, 0), 1.75, 0.25, 8, materials["stone"]).rotation_euler.z = math.pi / 8.0
    make_cylinder("Water", (0, 0, 0.25), 1.72, SMALL_BASIN_WATER_TOP - 0.25, 24, materials["water"])
    make_cylinder("Column", (0, 0, 0.25), 0.22, 1.1, 10, materials["trim"])
    make_frustum("Bowl", 1.35, 0.22, 0.8, 0.3, 16, materials["trim"])
    make_cylinder("Water", (0, 0, 1.55), 0.72, 0.08, 16, materials["water"])
    make_cone("Finial", (0, 0, 1.65), 0.12, 0.45, 10, materials["trim"])
    make_jet_mesh(materials["water_jet"], SMALL_CENTER_JET, (SMALL_FINIAL_JETS,))
    make_curtain_mesh(materials["water_curtain"], (SMALL_BOWL_CURTAIN,))
    # Taller than a jump so nobody ends up standing in the jets.
    make_cylinder("Fountain-colonly", (0, 0, 0), 2.1, 2.6, 8, None).rotation_euler.z = math.pi / 8.0


def build_lamp_post(materials: dict) -> None:
    """Cast-iron post with four curled arms and a crown globe: five white globes."""
    arm_height = 3.3
    arm_reach = 0.55

    make_frustum("Base", 0.0, 0.3, 0.16, 0.6, 8, materials["metal"])
    make_cylinder("Post", (0, 0, 0.6), 0.07, 3.1, 10, materials["metal"])
    make_cylinder("Collar", (0, 0, arm_height - 0.05), 0.12, 0.12, 10, materials["metal"])
    make_cylinder("CrownCup", (0, 0, 3.7), 0.09, 0.12, 10, materials["metal"])
    make_sphere("CrownGlobe", (0, 0, 4.03), 0.22, materials["lamp_glass"])

    for arm_index in range(4):
        angle = math.pi / 4.0 + arm_index * math.pi / 2.0
        direction = (math.cos(angle), math.sin(angle))
        tip = (direction[0] * arm_reach, direction[1] * arm_reach)
        arm = make_box(f"Arm{arm_index}", (0, 0, 0), (arm_reach, 0.05, 0.05), materials["metal"])
        arm.location = (tip[0] / 2.0, tip[1] / 2.0, arm_height)
        arm.rotation_euler.z = angle
        make_cylinder(f"ArmCup{arm_index}", (tip[0], tip[1], arm_height), 0.08, 0.14, 10, materials["metal"])
        make_sphere(f"Globe{arm_index}", (tip[0], tip[1], arm_height + 0.33), 0.2, materials["lamp_glass"])

    make_cylinder("LampPost-colonly", (0, 0, 0), 0.25, 2.5, 8, None)


def build_lamp_candelabra(materials: dict) -> None:
    """Tall centre lamp of a round plaza: stone plinth, cast-iron post, four arms on scroll brackets and a crown globe."""
    arm_height = 3.6
    arm_reach = 0.8

    make_cylinder("Plinth", (0, 0, 0), 0.55, 0.5, 8, materials["stone"]).rotation_euler.z = math.pi / 8.0
    make_cylinder("PlinthCap", (0, 0, 0.5), 0.6, 0.08, 8, materials["trim"]).rotation_euler.z = math.pi / 8.0
    make_frustum("Base", 0.58, 0.32, 0.15, 0.7, 8, materials["metal"])
    make_cylinder("Post", (0, 0, 1.28), 0.085, 3.3, 10, materials["metal"])

    for ring_height in (1.3, 2.4, arm_height - 0.08):
        make_cylinder(f"Collar{ring_height}", (0, 0, ring_height), 0.13, 0.12, 10, materials["metal"])

    make_cylinder("CrownCup", (0, 0, 4.55), 0.1, 0.14, 10, materials["metal"])
    make_sphere("CrownGlobe", (0, 0, 4.9), 0.25, materials["lamp_glass"])

    for arm_index in range(4):
        angle = arm_index * math.pi / 2.0
        direction = (math.cos(angle), math.sin(angle))
        tip = (direction[0] * arm_reach, direction[1] * arm_reach)
        arm = make_box(f"Arm{arm_index}", (0, 0, 0), (arm_reach, 0.06, 0.06), materials["metal"])
        arm.location = (tip[0] / 2.0, tip[1] / 2.0, arm_height)
        arm.rotation_euler.z = angle
        bracket = make_box(f"Bracket{arm_index}", (0, 0, 0), (0.62, 0.04, 0.04), materials["metal"])
        bracket.location = (direction[0] * 0.3, direction[1] * 0.3, arm_height - 0.3)
        bracket.rotation_euler = (0.0, -math.radians(52.0), angle)
        make_cylinder(f"ArmCup{arm_index}", (tip[0], tip[1], arm_height), 0.09, 0.15, 10, materials["metal"])
        make_sphere(f"Globe{arm_index}", (tip[0], tip[1], arm_height + 0.36), 0.22, materials["lamp_glass"])

    make_cylinder("LampCandelabra-colonly", (0, 0, 0), 0.6, 2.5, 8, None)


def make_oriented_box(name: str, center: tuple, size: tuple, angle: float, material):
    """Box of the given size centred at center and turned by angle around its own vertical axis."""
    box = make_box(name, (0, 0, 0), size, material)

    box.location = center
    box.rotation_euler.z = angle

    return box


def make_baluster(name: str, position: tuple, base_z: float, height: float, material) -> None:
    """Turned stone baluster: square foot, belly, neck and square head."""
    belly_height = height * 0.42
    profile = [(0.0, 0.05, 0.075, belly_height * 0.5), (belly_height * 0.5, 0.075, 0.045, belly_height * 0.5), (belly_height, 0.045, 0.035, height - belly_height - 0.14), (height - 0.14, 0.035, 0.06, 0.06)]

    make_box(f"{name}Foot", (position[0], position[1], base_z + 0.03), (0.15, 0.15, 0.06), material)
    make_box(f"{name}Head", (position[0], position[1], base_z + height - 0.03), (0.14, 0.14, 0.06), material)

    for part_index, (offset, bottom_radius, top_radius, part_height) in enumerate(profile):
        part = make_frustum(f"{name}Part{part_index}", base_z + 0.06 + offset * (height - 0.12) / height, bottom_radius, top_radius, part_height * (height - 0.12) / height, 8, material)
        part.location.x, part.location.y = position


def build_coreto_balustrade(side_index: int, start: tuple, end: tuple, floor: float, materials: dict) -> None:
    """Stone balustrade between two posts: plinth rail, turned balusters and a moulded handrail."""
    rail_height = 0.95
    middle = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
    length = math.hypot(end[0] - start[0], end[1] - start[1]) - 0.3
    side_angle = math.atan2(end[1] - start[1], end[0] - start[0])
    direction = (math.cos(side_angle), math.sin(side_angle))
    baluster_count = max(2, round(length / 0.3))

    make_oriented_box(f"RailPlinth{side_index}", (middle[0], middle[1], floor + 0.06), (length, 0.2, 0.12), side_angle, materials["trim"])
    make_oriented_box(f"Handrail{side_index}", (middle[0], middle[1], floor + rail_height - 0.05), (length, 0.24, 0.1), side_angle, materials["trim"])
    make_oriented_box(f"HandrailBead{side_index}", (middle[0], middle[1], floor + rail_height - 0.13), (length, 0.17, 0.06), side_angle, materials["trim"])
    make_oriented_box(f"Rail{side_index}-colonly", (middle[0], middle[1], floor + 0.55), (length + 0.3, 0.3, 1.1), side_angle, None)

    for baluster_index in range(baluster_count):
        along = (baluster_index + 0.5) / baluster_count * length - length / 2.0
        make_baluster(f"Baluster{side_index}_{baluster_index}", (middle[0] + direction[0] * along, middle[1] + direction[1] * along), floor + 0.12, rail_height - 0.28, materials["trim"])


def build_coreto_post(post_index: int, position: tuple, floor: float, top: float, materials: dict) -> None:
    """Square timber post on a stone pedestal, with a capital and two curved-looking braces under the beam."""
    angle = math.atan2(position[1], position[0])
    pedestal_height = 0.95

    make_oriented_box(f"PostPedestal{post_index}", (position[0], position[1], floor + pedestal_height / 2.0), (0.34, 0.34, pedestal_height), angle, materials["stone"])
    make_oriented_box(f"PostPedestalCap{post_index}", (position[0], position[1], floor + pedestal_height + 0.04), (0.42, 0.42, 0.08), angle, materials["trim"])
    make_oriented_box(f"Post{post_index}", (position[0], position[1], (floor + pedestal_height + top) / 2.0), (0.2, 0.2, top - floor - pedestal_height), angle, materials["wood"])
    make_oriented_box(f"PostCapital{post_index}", (position[0], position[1], top - 0.07), (0.32, 0.32, 0.14), angle, materials["wood"])

    for brace_sign in (-1, 1):
        brace_angle = angle + brace_sign * (math.pi / 2.0 + math.pi / 8.0)
        offset = (math.cos(brace_angle) * 0.3, math.sin(brace_angle) * 0.3)
        brace = make_oriented_box(f"Brace{post_index}{brace_sign:+d}", (position[0] + offset[0], position[1] + offset[1], top - 0.42), (0.85, 0.1, 0.1), brace_angle, materials["wood"])
        brace.rotation_euler.y = -math.pi / 4.0

    post_collider = make_cylinder(f"Post{post_index}-colonly", (position[0], position[1], floor), 0.2, top - floor, 6, None)
    post_collider.rotation_euler.z = 0.0


def build_coreto_stairs(platform_height: float, apothem: float, materials: dict) -> None:
    """Front steps (Blender -Y) between two stepped cheek walls with a newel block each."""
    step_count = 7
    step_tread = 0.34
    stair_width = 2.3
    run = step_count * step_tread
    step_rise = platform_height / step_count

    for step_index in range(step_count):
        step_top = step_rise * (step_index + 1)
        step_front = -apothem - (step_count - step_index) * step_tread
        make_span(f"Step{step_index}", (-stair_width / 2.0, step_front, 0.0), (stair_width / 2.0, -apothem + 0.2, step_top - 0.05), materials["stone"])
        make_span(f"StepTread{step_index}", (-stair_width / 2.0 - 0.02, step_front - 0.03, step_top - 0.05), (stair_width / 2.0 + 0.02, step_front + step_tread + 0.02, step_top), materials["trim"])

    for side_sign in (-1, 1):
        cheek_x = side_sign * (stair_width / 2.0 + 0.2)
        make_span(f"CheekLow{side_sign:+d}", (cheek_x - 0.2, -apothem - run - 0.25, 0.0), (cheek_x + 0.2, -apothem - run / 2.0, platform_height * 0.55), materials["stone"])
        make_span(f"CheekHigh{side_sign:+d}", (cheek_x - 0.2, -apothem - run / 2.0, 0.0), (cheek_x + 0.2, -apothem + 0.2, platform_height + 0.05), materials["stone"])
        make_span(f"CheekLowCap{side_sign:+d}", (cheek_x - 0.26, -apothem - run - 0.31, platform_height * 0.55), (cheek_x + 0.26, -apothem - run / 2.0 + 0.06, platform_height * 0.55 + 0.08), materials["trim"])
        make_span(f"CheekHighCap{side_sign:+d}", (cheek_x - 0.26, -apothem - run / 2.0, platform_height + 0.05), (cheek_x + 0.26, -apothem + 0.26, platform_height + 0.13), materials["trim"])
        make_sphere(f"CheekFinial{side_sign:+d}", (cheek_x, -apothem - run + 0.05, platform_height * 0.55 + 0.26), 0.2, materials["trim"])
        make_span(f"Cheek{side_sign:+d}-colonly", (cheek_x - 0.26, -apothem - run - 0.3, 0.0), (cheek_x + 0.26, -apothem + 0.2, platform_height + 0.1), None)

    # Landing runs past the platform collider's edge so the top step joins the floor without a lip.
    make_stair_ramp("Stairs", stair_width, -apothem - run, step_count, step_tread, step_rise, 0.0, landing_length=step_tread + 0.5)


def build_coreto(materials: dict) -> None:
    """Octagonal bandstand: stone base with plinth and frieze, stone balustrade between timber posts,
    two-tier tiled roof with a lantern. The stairs face Blender -Y; that side stays open."""
    platform_height = 1.2
    platform_radius = 3.7
    post_radius = 3.35
    beam_top = 4.15
    eighth = math.pi / 8.0
    apothem = platform_radius * math.cos(eighth)
    corners = [(post_radius * math.cos(eighth + index * math.pi / 4.0), post_radius * math.sin(eighth + index * math.pi / 4.0)) for index in range(8)]
    stair_side = next(index for index in range(8) if abs(corners[index][1] + corners[(index + 1) % 8][1]) / 2.0 > post_radius * 0.9 and corners[index][1] < 0)
    octagon = lambda name, base_z, radius, height, material: setattr(make_cylinder(name, (0, 0, base_z), radius, height, 8, material).rotation_euler, "z", eighth)

    octagon("Plinth", 0.0, platform_radius + 0.18, 0.22, materials["trim"])
    octagon("Platform", 0.22, platform_radius, platform_height - 0.5, materials["stone"])
    octagon("Frieze", platform_height - 0.28, platform_radius + 0.05, 0.16, materials["trim"])
    octagon("PlatformRim", platform_height - 0.12, platform_radius + 0.16, 0.12, materials["trim"])
    octagon("Floor", platform_height - 0.02, platform_radius - 0.2, 0.03, materials["wood"])
    octagon("Platform-colonly", 0.0, platform_radius + 0.1, platform_height, None)

    octagon("RingBeam", beam_top - 0.22, post_radius + 0.22, 0.22, materials["wood"])
    octagon("Ceiling", beam_top - 0.02, post_radius + 0.1, 0.04, materials["wood"])
    octagon("Eave", beam_top, 4.75, 0.1, materials["wood"])
    make_cone("Roof", (0, 0, beam_top + 0.1), 4.8, 1.25, 8, materials["roof"], eighth, top_radius=1.25)
    octagon("LanternWall", beam_top + 1.3, 1.1, 0.45, materials["trim"])
    octagon("LanternEave", beam_top + 1.75, 1.6, 0.07, materials["wood"])
    make_cone("LanternRoof", (0, 0, beam_top + 1.82), 1.62, 1.0, 8, materials["roof"], eighth)
    make_sphere("FinialBall", (0, 0, beam_top + 2.9), 0.14, materials["metal"])
    make_cone("Finial", (0, 0, beam_top + 2.98), 0.06, 0.6, 8, materials["metal"])
    # Só a câmera enxerga (o import põe CameraStop* na camada "camera"): olhando para baixo ela para sob o forro e o beiral.
    octagon("CameraStopCeiling-colonly", beam_top - 0.22, post_radius + 0.22, 0.22, None)
    octagon("CameraStopEave-colonly", beam_top, 4.75, 0.1, None)
    make_cone("CameraStopRoof-colonly", (0, 0, beam_top + 0.1), 4.8, 1.25, 8, None, eighth, top_radius=1.25)

    for corner_index, corner in enumerate(corners):
        rib_angle = eighth + corner_index * math.pi / 4.0
        rib = make_oriented_box(f"RoofRib{corner_index}", (3.02 * math.cos(rib_angle), 3.02 * math.sin(rib_angle), beam_top + 0.76), (3.75, 0.14, 0.1), rib_angle, materials["trim"])
        rib.rotation_euler.y = math.atan2(1.25, 3.55)
        build_coreto_post(corner_index, corner, platform_height, beam_top - 0.2, materials)

        if corner_index != stair_side:
            build_coreto_balustrade(corner_index, corner, corners[(corner_index + 1) % 8], platform_height, materials)

    build_coreto_stairs(platform_height, apothem, materials)


def make_palm_frond(name: str, yaw: float, pitch: float, length: float, material):
    """Arching frond: a V-shaped blade of ragged leaflets that droops toward the tip."""
    import bmesh

    from build_cathedral import object_from_bmesh

    frond_bmesh = bmesh.new()
    segments = 9
    spine, left, right = [], [], []

    for segment in range(segments + 1):
        along = segment / segments
        reach = length * along
        droop = math.sin(pitch) * reach - 0.42 * length * along * along
        out = math.cos(pitch) * reach
        half_width = 0.42 * math.sin(math.pi * min(1.0, along * 1.15 + 0.08)) * (1.0 if segment % 2 == 0 else 0.72) + 0.02
        spine.append(frond_bmesh.verts.new((out, 0.0, droop)))
        left.append(frond_bmesh.verts.new((out - 0.08, half_width, droop - 0.5 * half_width)))
        right.append(frond_bmesh.verts.new((out - 0.08, -half_width, droop - 0.5 * half_width)))

    for segment in range(segments):
        frond_bmesh.faces.new([spine[segment], spine[segment + 1], left[segment + 1], left[segment]])
        frond_bmesh.faces.new([spine[segment + 1], spine[segment], right[segment], right[segment + 1]])

    frond = object_from_bmesh(name, frond_bmesh, material)
    frond.rotation_euler.z = yaw

    return frond


def build_palm(materials: dict) -> None:
    """Royal palm: ringed trunk with a slight lean, green crownshaft and a crown of arching fronds."""
    trunk_height = 7.2
    ring_count = 12
    lean = lambda rise: (0.35 * rise * rise, 0.12 * math.sin(rise * 2.4))
    crown = (*lean(1.0), trunk_height)

    for ring_index in range(ring_count):
        rise = ring_index / ring_count
        radius = 0.3 - 0.11 * rise + (0.07 if ring_index == 0 else 0.0)
        segment = make_frustum(f"Trunk{ring_index}", trunk_height * rise, radius, radius - 0.025, trunk_height / ring_count, 10, materials["palm_trunk"])
        segment.location.x, segment.location.y = lean(rise)
        ring = make_cylinder(f"TrunkRing{ring_index}", (*lean(rise), trunk_height * rise), radius + 0.012, 0.05, 10, materials["palm_trunk"])
        ring.scale = (1.0, 1.0, 1.0)

    shaft = make_frustum("Crownshaft", trunk_height, 0.2, 0.13, 0.9, 10, materials["palm_leaf"])
    shaft.location.x, shaft.location.y = crown[0], crown[1]

    for frond_index in range(16):
        tier = frond_index % 3
        frond = make_palm_frond(f"Frond{frond_index}", frond_index * math.radians(137.5), math.radians(58.0 - 30.0 * tier), 3.1 - 0.25 * tier, materials["palm_leaf"])
        frond.location = (crown[0], crown[1], trunk_height + 0.75 - 0.12 * tier)


BENCH_SLAT_LENGTH = 1.9
BENCH_END_X = 0.84  # the two cast-iron ends, one near each end of the slats
BENCH_SEAT_TOP = 0.46  # height the UAL Sitting_* clips sit at
BENCH_BACK_TILT = math.radians(15.0)  # backrest leaning back from upright
BENCH_SEAT_SLATS = (-0.30, -0.218, -0.136, -0.054, 0.028)  # y of each seat slat (front is -Y)
BENCH_BACK_SLATS = (0.14, 0.235, 0.33)  # metres up the backrest line, from the back of the seat
BENCH_BACK_FOOT = (0.105, 0.50)  # (y, z) where the backrest line starts, just above the back seat slat
BENCH_BAR_FOOT = (0.135, 0.41)  # (y, z) where the iron back bar leaves the seat rail, behind the backrest slats
BENCH_IRON = (0.03, 0.036)  # cross-section of the cast-iron bars: across the bench, along the side
WOOD_GRAIN_BAND = (0.72, 0.96)  # V range of the plank band at the top of the kit's wood-trim atlas
WOOD_METRES_PER_TILE = 2.0  # the atlas spans 2 m of plank in both directions


def make_slat(name: str, center: tuple, width: float, thickness: float, tilt: float, grain_offset: float, material):
    """One plank across the bench: its UVs follow the grain of the atlas's plank band along its length."""
    slat_bmesh = bmesh.new()
    uv_layer = slat_bmesh.loops.layers.uv.new()
    band_low, band_high = WOOD_GRAIN_BAND
    across_span = (width + thickness) / WOOD_METRES_PER_TILE  # same texel size across the grain as along it
    band_start = band_low + (band_high - band_low - across_span) * (grain_offset % 1.0)

    bmesh.ops.create_cube(slat_bmesh, size=1.0)
    bmesh.ops.scale(slat_bmesh, vec=(BENCH_SLAT_LENGTH, width, thickness), verts=slat_bmesh.verts)

    for face in slat_bmesh.faces:
        for loop in face.loops:
            across = (loop.vert.co.y / width + loop.vert.co.z / thickness) * 0.5 + 0.5
            loop[uv_layer].uv = (loop.vert.co.x / WOOD_METRES_PER_TILE + grain_offset, band_start + across_span * across)

    bmesh.ops.transform(slat_bmesh, matrix=Matrix.Translation(center) @ Matrix.Rotation(tilt, 4, "X"), verts=slat_bmesh.verts)
    slat = object_from_bmesh(name, slat_bmesh, material)
    slat["keep_uvs"] = True

    return slat


def make_iron_bar(name: str, x: float, start: tuple, end: tuple, material) -> None:
    """Square cast-iron bar in the side plane x, from (y, z) start to end (lapped a little at both joints)."""
    width, depth = BENCH_IRON
    run = Vector((0.0, end[0] - start[0], end[1] - start[1]))
    bar = make_box(name, (0, 0, 0), (width, run.length + depth, depth), material)

    bar.location = (x, (start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
    bar.rotation_euler.x = math.atan2(run.z, run.y)


def back_line(foot: tuple, distance: float) -> tuple:
    return foot[0] + distance * math.sin(BENCH_BACK_TILT), foot[1] + distance * math.cos(BENCH_BACK_TILT)


def build_bench_end(side: str, x: float, material) -> None:
    """One cast-iron end: front leg up to the armrest, rear leg, seat rail, the back bar that carries the backrest,
    a curved armrest and a low brace between the legs."""
    seat_rail_z = BENCH_SEAT_TOP - 0.05
    back_top = back_line(BENCH_BAR_FOOT, 0.48)
    arm_back = back_line(BENCH_BAR_FOOT, (0.66 - BENCH_BAR_FOOT[1]) / math.cos(BENCH_BACK_TILT))
    armrest = [(-0.36, 0.63), (-0.33, 0.66), (-0.2, 0.675), (0.0, 0.67), arm_back]
    brace = [(-0.30, 0.13), (-0.1, 0.18), (0.08, 0.18), (0.17, 0.12)]

    make_iron_bar(f"FrontLeg{side}", x, (-0.31, 0.0), (-0.33, 0.655), material)
    make_iron_bar(f"RearLeg{side}", x, (0.2, 0.0), (BENCH_BAR_FOOT[0], seat_rail_z), material)
    make_iron_bar(f"SeatRail{side}", x, (-0.34, seat_rail_z), (BENCH_BAR_FOOT[0], seat_rail_z), material)
    make_iron_bar(f"BackBar{side}", x, BENCH_BAR_FOOT, back_top, material)

    for index, (start, end) in enumerate(zip(armrest, armrest[1:])):
        make_iron_bar(f"Armrest{side}{index}", x, start, end, material)

    for index, (start, end) in enumerate(zip(brace, brace[1:])):
        make_iron_bar(f"Brace{side}{index}", x, start, end, material)

    for index, foot_y in enumerate((-0.31, 0.2)):
        make_box(f"Foot{side}{index}", (x, foot_y, 0.012), (0.06, 0.09, 0.024), material)


def build_park_bench(materials: dict) -> None:
    """Praça bench: wooden slats for seat and backrest, held at each end by a cast-iron side frame that joins the
    seat to the backrest. The front faces -Y (+Z in Godot); a sitter goes 0.15 m in front of the origin."""
    slat_thickness = 0.035

    for index, slat_y in enumerate(BENCH_SEAT_SLATS):
        make_slat(f"SeatSlat{index}", (0.0, slat_y, BENCH_SEAT_TOP - slat_thickness / 2.0), 0.07, slat_thickness, 0.0, index * 0.37, materials["bench_wood"])

    for index, distance in enumerate(BENCH_BACK_SLATS):
        y, z = back_line(BENCH_BACK_FOOT, distance)
        behind = slat_thickness / 2.0
        center = (0.0, y + behind * math.cos(BENCH_BACK_TILT), z - behind * math.sin(BENCH_BACK_TILT))
        make_slat(f"BackSlat{index}", center, 0.085, slat_thickness, math.pi / 2.0 - BENCH_BACK_TILT, 0.2 + index * 0.41, materials["bench_wood"])

    for side, x in (("L", BENCH_END_X), ("R", -BENCH_END_X)):
        build_bench_end(side, x, materials["metal"])

    make_box("ParkBench-colonly", (0.0, -0.06, 0.27), (BENCH_SLAT_LENGTH, 0.62, 0.54), None)


def build_planter(materials: dict) -> None:
    make_octagon_ring("PlanterWall", 1.3, 1.08, 0.5, materials["stone"])
    make_octagon_ring("PlanterRim", 1.36, 1.02, 0.08, materials["trim"]).location.z = 0.5
    make_cylinder("Soil", (0, 0, 0), 1.1, 0.42, 8, materials["soil"]).rotation_euler.z = math.pi / 8.0
    make_cylinder("Planter-colonly", (0, 0, 0), 1.3, 1.0, 8, None).rotation_euler.z = math.pi / 8.0


PROPS = {
    "fountain_large": build_large_fountain,
    "fountain_small": build_small_fountain,
    "lamp_post": build_lamp_post,
    "lamp_candelabra": build_lamp_candelabra,
    "coreto": build_coreto,
    "planter": build_planter,
    "palm": build_palm,
    "park_bench": build_park_bench,
}


def make_brick_paving_image() -> None:
    """Terracotta running-bond paving of the squares: one texture = 1 x 1 m, bricks 20 x 10 cm."""
    size = 500
    bricks_per_row = 5
    rows = 10
    generator = numpy.random.default_rng(3)
    brick_colors = numpy.array([0.62, 0.31, 0.21]) * (0.85 + 0.25 * generator.random((rows, bricks_per_row + 1, 1)))
    pixel_rows, pixel_columns = numpy.meshgrid(numpy.arange(size), numpy.arange(size), indexing="ij")
    brick_height = size // rows
    brick_width = size / bricks_per_row
    row_index = pixel_rows // brick_height
    shifted_columns = pixel_columns + (row_index % 2) * brick_width / 2.0
    column_index = (shifted_columns // brick_width).astype(int)
    is_mortar = (pixel_rows % brick_height < 3) | (shifted_columns % brick_width < 3)
    rgb = brick_colors[row_index, column_index, :] * (0.94 + 0.06 * generator.random((size, size, 1)))
    rgb[is_mortar] = [0.5, 0.36, 0.3]
    rgba = numpy.concatenate([rgb, numpy.ones((size, size, 1))], axis=2)

    save_generated_image("T_BrickPaving_BaseColor", rgba, size)


def build_prop(prop_name: str) -> Path:
    output_path = OUTPUT_DIR / f"{prop_name}.gltf"
    tile_sizes = {"M_CathedralStone": 3.0, "M_CathedralTrim": 1.5, "M_CathedralRoof": 2.0}

    bpy.ops.wm.read_factory_settings(use_empty=True)

    materials = build_prop_materials()
    PROPS[prop_name](materials)
    bpy.context.view_layer.update()

    for mesh_object in [scene_object for scene_object in bpy.data.objects if scene_object.type == "MESH" and scene_object.data.materials and not scene_object.get("keep_uvs")]:
        map_uvs_per_face(mesh_object, tile_sizes.get(mesh_object.data.materials[0].name, 2.0))

    merge_meshes_by_material(prop_name.title().replace("_", ""))

    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_texture_dir="textures", export_yup=True)

    return output_path


if __name__ == "__main__":
    script_arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    bpy.ops.wm.read_factory_settings(use_empty=True)
    make_brick_paving_image()

    for requested_prop in script_arguments or list(PROPS):
        print(f"BUILT {requested_prop} -> {build_prop(requested_prop)}")
