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


def build_coreto(materials: dict) -> None:
    """Octagonal bandstand on a raised platform with railing, red tile roof and front steps (Blender -Y)."""
    platform_height = 1.2
    column_radius = 3.25
    column_top = 4.0
    step_count = 6
    step_tread = 0.35
    sides = [(math.pi / 8.0 + side_index * math.pi / 4.0, math.pi / 8.0 + (side_index + 1) * math.pi / 4.0) for side_index in range(8)]
    stair_side = 5

    make_cylinder("Platform", (0, 0, 0), 3.6, platform_height - 0.12, 8, materials["stone"]).rotation_euler.z = math.pi / 8.0
    make_cylinder("PlatformRim", (0, 0, platform_height - 0.12), 3.72, 0.12, 8, materials["trim"]).rotation_euler.z = math.pi / 8.0
    make_cone("Roof", (0, 0, column_top + 0.1), 4.4, 1.9, 8, materials["roof"], math.pi / 8.0)
    make_cylinder("Eave", (0, 0, column_top), 4.45, 0.16, 8, materials["trim"]).rotation_euler.z = math.pi / 8.0
    make_cone("Finial", (0, 0, column_top + 1.95), 0.12, 0.7, 8, materials["metal"])

    for step_index in range(step_count):
        step_top = platform_height * (step_index + 1) / step_count
        step_front = -3.3 - (step_count - step_index) * step_tread
        make_box(f"Step{step_index}", (0, (step_front - 3.0) / 2.0, step_top / 2.0), (2.2, -3.0 - step_front, step_top), materials["stone"])

    stairs = make_box("Stairs-colonly", (0, -3.3 - step_count * step_tread / 2.0, platform_height / 2.0 - 0.06), (2.2, math.hypot(step_count * step_tread, platform_height), 0.1), None)
    stairs.rotation_euler.x = math.atan2(platform_height, step_count * step_tread)
    make_cylinder("Platform-colonly", (0, 0, 0), 3.72, platform_height, 8, None).rotation_euler.z = math.pi / 8.0

    for side_index, (start_angle, end_angle) in enumerate(sides):
        start = (column_radius * math.cos(start_angle), column_radius * math.sin(start_angle))
        end = (column_radius * math.cos(end_angle), column_radius * math.sin(end_angle))
        middle = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
        length = math.hypot(end[0] - start[0], end[1] - start[1])
        side_angle = math.atan2(end[1] - start[1], end[0] - start[0])
        make_cylinder(f"Column{side_index}", (start[0], start[1], platform_height), 0.09, column_top - platform_height, 10, materials["trim"])
        make_box(f"Lintel{side_index}", (middle[0], middle[1], column_top - 0.15), (length, 0.14, 0.3), materials["trim"]).rotation_euler.z = side_angle

        if side_index == stair_side:
            continue

        make_box(f"Rail{side_index}", (middle[0], middle[1], platform_height + 0.9), (length, 0.08, 0.08), materials["metal"]).rotation_euler.z = side_angle
        make_box(f"RailLow{side_index}", (middle[0], middle[1], platform_height + 0.12), (length, 0.06, 0.06), materials["metal"]).rotation_euler.z = side_angle
        make_box(f"RailGrille{side_index}", (middle[0], middle[1], platform_height + 0.5), (length - 0.2, 0.02, 0.7), materials["metal"]).rotation_euler.z = side_angle
        make_box(f"Rail{side_index}-colonly", (middle[0], middle[1], platform_height + 0.5), (length, 0.2, 1.0), None).rotation_euler.z = side_angle


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
