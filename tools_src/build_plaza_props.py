"""Model the plaza props (fountains, lamp post, planter) and export them to art/town/.

Reuses the geometry helpers and stone textures of build_cathedral.py (run that first: it writes the textures).
Meshes named "Water" get the water shader in Godot; *-colonly boxes become collision.

Usage:
  blender -b --factory-startup -P tools_src/build_plaza_props.py
"""

import math
import sys
from pathlib import Path

import bpy
import numpy

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_cathedral import (  # noqa: E402
    GENERATED_TEXTURES,
    OUTPUT_DIR,
    load_kit_image,
    make_box,
    make_cone,
    make_span,
    make_cylinder,
    make_material,
    make_plain_material,
    make_sphere,
    map_uvs_per_face,
    merge_meshes_by_material,
    save_generated_image,
)


def build_prop_materials() -> dict:
    stone_image = bpy.data.images.load(str(GENERATED_TEXTURES / "T_CathedralStone_BaseColor.png"))
    trim_image = bpy.data.images.load(str(GENERATED_TEXTURES / "T_CathedralTrim_BaseColor.png"))

    return {
        "stone": make_material("M_CathedralStone", stone_image, load_kit_image("T_Brick_Normal.png", False)),
        "trim": make_material("M_CathedralTrim", trim_image, load_kit_image("T_Plaster_Normal.png", False)),
        "water": make_plain_material("M_Water", (0.25, 0.55, 0.65), 0.0, 0.05),
        "metal": make_plain_material("M_LampMetal", (0.08, 0.17, 0.13), 0.7, 0.45),
        "roof": make_material("M_CathedralRoof", bpy.data.images.load(str(GENERATED_TEXTURES / "T_CathedralRoof_BaseColor.png")), load_kit_image("T_RoundTiles_Normal.png", False)),
        "lamp_glass": make_lamp_glass_material(),
        "soil": make_plain_material("M_Soil", (0.22, 0.15, 0.10), 0.0, 1.0),
        "wood": make_plain_material("M_PropWood", (0.2, 0.11, 0.06), 0.0, 0.7),
    }


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


def build_large_fountain(materials: dict) -> None:
    make_octagon_ring("BasinStep", 5.7, 4.0, 0.18, materials["trim"])
    make_octagon_ring("BasinWall", 5.0, 4.55, 0.75, materials["stone"])
    make_octagon_ring("BasinRim", 5.12, 4.45, 0.12, materials["trim"]).location.z = 0.75
    make_cylinder("BasinFloor", (0, 0, 0), 4.6, 0.3, 8, materials["stone"]).rotation_euler.z = math.pi / 8.0
    make_cylinder("Water", (0, 0, 0.3), 4.58, 0.28, 32, materials["water"])
    make_frustum("Pedestal", 0.3, 0.9, 0.55, 0.5, 8, materials["trim"])
    make_cylinder("Column", (0, 0, 0.8), 0.42, 1.0, 12, materials["trim"])
    make_frustum("LowerBowl", 1.8, 0.45, 2.1, 0.5, 24, materials["trim"])
    make_cylinder("LowerBowlRim", (0, 0, 2.3), 2.12, 0.08, 24, materials["trim"])
    make_cylinder("Water", (0, 0, 2.2), 1.95, 0.16, 24, materials["water"])
    make_cylinder("UpperColumn", (0, 0, 2.38), 0.24, 0.9, 12, materials["trim"])
    make_frustum("UpperBowl", 3.28, 0.25, 1.05, 0.35, 20, materials["trim"])
    make_cylinder("Water", (0, 0, 3.5), 0.95, 0.1, 20, materials["water"])
    make_frustum("FinialBase", 3.6, 0.22, 0.14, 0.35, 12, materials["trim"])
    make_cone("Finial", (0, 0, 3.95), 0.16, 0.6, 12, materials["trim"])
    make_cylinder("Fountain-colonly", (0, 0, 0), 5.1, 1.2, 8, None).rotation_euler.z = math.pi / 8.0


def build_small_fountain(materials: dict) -> None:
    make_octagon_ring("BasinWall", 2.0, 1.7, 0.6, materials["stone"])
    make_octagon_ring("BasinRim", 2.08, 1.62, 0.1, materials["trim"]).location.z = 0.6
    make_cylinder("BasinFloor", (0, 0, 0), 1.75, 0.25, 8, materials["stone"]).rotation_euler.z = math.pi / 8.0
    make_cylinder("Water", (0, 0, 0.25), 1.72, 0.22, 24, materials["water"])
    make_cylinder("Column", (0, 0, 0.25), 0.22, 1.1, 10, materials["trim"])
    make_frustum("Bowl", 1.35, 0.22, 0.8, 0.3, 16, materials["trim"])
    make_cylinder("Water", (0, 0, 1.55), 0.72, 0.08, 16, materials["water"])
    make_cone("Finial", (0, 0, 1.65), 0.12, 0.45, 10, materials["trim"])
    make_cylinder("Fountain-colonly", (0, 0, 0), 2.1, 1.0, 8, None).rotation_euler.z = math.pi / 8.0


def build_lamp_post(materials: dict) -> None:
    """Cast-iron post with four curled arms and a crown globe: five white globes, as in the Campo Mourão squares."""
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

    stairs = make_box("Stairs-colonly", (0, 0, 0), (stair_width, math.hypot(run, platform_height), 0.1), None)
    stairs.location = (0, -apothem - run / 2.0, platform_height / 2.0 - 0.05)
    stairs.rotation_euler.x = math.atan2(platform_height, run)


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

    for corner_index, corner in enumerate(corners):
        rib_angle = eighth + corner_index * math.pi / 4.0
        rib = make_oriented_box(f"RoofRib{corner_index}", (3.02 * math.cos(rib_angle), 3.02 * math.sin(rib_angle), beam_top + 0.76), (3.75, 0.14, 0.1), rib_angle, materials["trim"])
        rib.rotation_euler.y = math.atan2(1.25, 3.55)
        build_coreto_post(corner_index, corner, platform_height, beam_top - 0.2, materials)

        if corner_index != stair_side:
            build_coreto_balustrade(corner_index, corner, corners[(corner_index + 1) % 8], platform_height, materials)

    build_coreto_stairs(platform_height, apothem, materials)


def build_planter(materials: dict) -> None:
    make_octagon_ring("PlanterWall", 1.3, 1.08, 0.5, materials["stone"])
    make_octagon_ring("PlanterRim", 1.36, 1.02, 0.08, materials["trim"]).location.z = 0.5
    make_cylinder("Soil", (0, 0, 0), 1.1, 0.42, 8, materials["soil"]).rotation_euler.z = math.pi / 8.0
    make_cylinder("Planter-colonly", (0, 0, 0), 1.3, 1.0, 8, None).rotation_euler.z = math.pi / 8.0


PROPS = {
    "fountain_large": build_large_fountain,
    "fountain_small": build_small_fountain,
    "lamp_post": build_lamp_post,
    "coreto": build_coreto,
    "planter": build_planter,
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

    for mesh_object in [scene_object for scene_object in bpy.data.objects if scene_object.type == "MESH" and scene_object.data.materials]:
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
