"""Generate the shop houses by seed out of the storeys of the town houses and export them to art/town/shops/.

The town houses (build_houses.py) are stacks of storey rings on a 2 m wall grid, one ring every 3.12 m, with a
roof on top. This script takes those houses apart again (ground storeys, upper storeys, roofs) and, from a fixed
seed, stacks a new house per recipe: which ground floor, how many upper storeys and which ones, mirrored or not,
plaster colour and roof tile colour (vertex colours, multiplied over the kit textures by Godot).

Only houses with the same footprint share storeys, so every variant keeps the footprint of its family and
build_hub_scene.py can swap it in for a town house of that family without moving anything.

Usage (after build_houses.py):
  blender -b --factory-startup -P tools_src/build_shop_houses.py -- [variant_name ...]
"""

import random
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_houses import STOREY_HEIGHT, add_collision_box, merge_duplicate_datablocks  # noqa: E402

PROJECT_DIR = Path(__file__).resolve().parent.parent
TOWN_DIR = PROJECT_DIR / "art" / "town"
SHOP_DIR = TOWN_DIR / "shops"

SEED = 2207
ROOF = "roof"
STOREY_LINE_BAND = 0.35
EAVE_DROP = 1.0
EAVE_CLEARANCE = 0.45
ROOF_TILE_MATERIAL = "MI_RoundTiles"
MIRROR_X = Matrix.Scale(-1.0, 4, (1.0, 0.0, 0.0))

# Family -> houses that share a footprint (half width, half depth) and how many variants to generate.
FAMILIES = {
    "narrow": {"sources": {"house_stone_tall": 2, "house_narrow_three": 3}, "half_size": (3.0, 4.0), "variants": 8},
}
UPPER_STOREY_COUNTS = [1, 1, 2, 2, 2]
# Multiplied over the cream plaster / terracotta tile textures (sRGB); soft tones from the style bible palette.
PLASTER_TINTS = [(1.0, 1.0, 1.0), (0.9, 0.95, 1.0), (1.0, 0.91, 0.88), (0.92, 0.98, 0.9), (1.0, 0.95, 0.82), (0.95, 0.91, 1.0), (1.0, 0.93, 0.86)]
ROOF_TINTS = [(1.0, 1.0, 1.0), (0.78, 0.84, 1.0), (0.82, 1.0, 0.86), (1.0, 0.82, 0.78), (0.9, 0.86, 0.82)]
TINTED_MATERIALS = {"MI_Plaster": "plaster", "MI_RoundTiles": "roof"}


def variant_recipes() -> dict:
    """Variant name -> recipe; a fixed seed keeps the town identical on every run."""
    generator = random.Random(SEED)
    recipes = {}

    for family_name, family in FAMILIES.items():
        grounds = list(family["sources"])
        uppers = [(house_name, storey) for house_name, storey_count in family["sources"].items() for storey in range(1, storey_count)]
        plaster_tints = generator.sample(PLASTER_TINTS, len(PLASTER_TINTS))
        roof_tints = generator.sample(ROOF_TINTS, len(ROOF_TINTS))

        for index in range(family["variants"]):
            upper_count = generator.choice(UPPER_STOREY_COUNTS)
            first_upper = generator.randrange(len(uppers))

            recipes[f"house_shop_{family_name}_{index + 1}"] = {
                "family": family_name,
                "ground": grounds[index % len(grounds)],
                "uppers": [uppers[(first_upper + offset) % len(uppers)] for offset in range(upper_count)],
                "roof": generator.choice(grounds),
                "mirrored": index % 2 == 1,
                "plaster": plaster_tints[index % len(plaster_tints)],
                "roof_tint": roof_tints[index % len(roof_tints)],
            }

    return recipes


def import_house(house_name: str):
    """The visible mesh of a town house, in world space (the collision box is dropped)."""
    bpy.ops.import_scene.gltf(filepath=str(TOWN_DIR / f"{house_name}.gltf"), merge_vertices=True)

    for scene_object in [scene_object for scene_object in bpy.context.selected_objects if scene_object.name.split(".")[0].endswith("-colonly")]:
        bpy.data.objects.remove(scene_object, do_unlink=True)

    house = next(scene_object for scene_object in bpy.context.scene.objects if scene_object.type == "MESH" and scene_object.name.startswith("House") and "part" not in scene_object)
    house["part"] = house_name

    with bpy.context.temp_override(active_object=house, selected_editable_objects=[house]):
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    return house


def face_islands(house_bmesh) -> list:
    """Connected groups of faces: every kit piece (wall, window, roof...) is one or more islands."""
    unvisited = set(house_bmesh.faces)
    islands = []

    while unvisited:
        island = []
        frontier = [unvisited.pop()]

        while frontier:
            face = frontier.pop()
            neighbours = {linked_face for vertex in face.verts for linked_face in vertex.link_faces} & unvisited

            island.append(face)
            unvisited -= neighbours
            frontier += neighbours

        islands.append(island)

    return islands


def island_part(island: list, storey_count: int, half_width: float, tile_slot: int):
    """Which storey (or the roof) an island belongs to. Whatever sits on a storey line (beams, balcony floors,
    quoin caps) goes with the part above it, and the eaves that hang below the roof line stay with the roof."""
    corners = [vertex.co for face in island for vertex in face.verts]
    heights = [corner.z for corner in corners]
    sides = [abs(corner.x) for corner in corners]
    roof_line = storey_count * STOREY_HEIGHT
    is_tile = island[0].material_index == tile_slot
    is_eave = min(heights) > roof_line - EAVE_DROP and (min(sides) + max(sides)) / 2.0 > half_width + EAVE_CLEARANCE
    storey = int(((min(heights) + max(heights)) / 2.0 + STOREY_LINE_BAND) // STOREY_HEIGHT)

    return ROOF if is_tile or is_eave or storey >= storey_count else max(storey, 0)


def split_house(house_name: str, storey_count: int, half_width: float) -> dict:
    """Take a town house apart: storey index or ROOF -> mesh object holding only that part."""
    house = import_house(house_name)
    house_bmesh = bmesh.new()

    house_bmesh.from_mesh(house.data)

    tile_slot = house.material_slots.find(ROOF_TILE_MATERIAL)

    part_of_face = {face.index: island_part(island, storey_count, half_width, tile_slot) for island in face_islands(house_bmesh) for face in island}
    parts = {}

    house_bmesh.free()

    for part in [*range(storey_count), ROOF]:
        part_object = house.copy()
        part_object.data = house.data.copy()
        part_bmesh = bmesh.new()

        part_bmesh.from_mesh(part_object.data)
        bmesh.ops.delete(part_bmesh, geom=[face for face in part_bmesh.faces if part_of_face[face.index] != part], context="FACES")
        part_bmesh.to_mesh(part_object.data)
        part_bmesh.free()

        parts[part] = part_object

    bpy.data.objects.remove(house, do_unlink=True)

    return parts


def stacked_copy(part_object, lift: float):
    stacked = part_object.copy()
    stacked.data = part_object.data.copy()
    stacked.data.transform(Matrix.Translation((0.0, 0.0, lift)))
    bpy.context.scene.collection.objects.link(stacked)

    return stacked


def tint_house(house, tints: dict) -> None:
    """Vertex colours: white everywhere, the recipe's colour on plaster and roof tiles."""
    color_layer = house.data.color_attributes.new("Color", "FLOAT_COLOR", "CORNER")
    white = (1.0, 1.0, 1.0, 1.0)
    tint_by_slot = [tints.get(TINTED_MATERIALS.get(slot.material.name, ""), white) for slot in house.material_slots]

    for polygon in house.data.polygons:
        for loop_index in polygon.loop_indices:
            color_layer.data[loop_index].color = tint_by_slot[polygon.material_index]

    house.data.color_attributes.active_color = color_layer
    house.data.color_attributes.render_color_index = house.data.color_attributes.find("Color")


def build_variant(variant_name: str, recipe: dict) -> Path:
    family = FAMILIES[recipe["family"]]
    output_path = SHOP_DIR / f"{variant_name}.gltf"
    storey_count = 1 + len(recipe["uppers"])

    bpy.ops.wm.read_factory_settings(use_empty=True)

    parts = {house_name: split_house(house_name, source_storeys, family["half_size"][0]) for house_name, source_storeys in family["sources"].items()}
    merge_duplicate_datablocks()

    roof_lift = (storey_count - family["sources"][recipe["roof"]]) * STOREY_HEIGHT
    stack = [stacked_copy(parts[recipe["ground"]][0], 0.0), stacked_copy(parts[recipe["roof"]][ROOF], roof_lift)]
    stack += [stacked_copy(parts[house_name][storey], (target - storey) * STOREY_HEIGHT) for target, (house_name, storey) in enumerate(recipe["uppers"], start=1)]

    with bpy.context.temp_override(active_object=stack[0], selected_editable_objects=stack):
        bpy.ops.object.join()

    stack[0].name = "House"

    if recipe["mirrored"]:
        stack[0].data.transform(MIRROR_X)
        stack[0].data.flip_normals()

    tint_house(stack[0], {"plaster": (*recipe["plaster"], 1.0), "roof": (*recipe["roof_tint"], 1.0)})
    add_collision_box(Vector((*family["half_size"], 0.0)), storey_count * STOREY_HEIGHT)

    SHOP_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(output_path),
        export_format="GLTF_SEPARATE",
        export_texture_dir="../textures",
        export_yup=True,
        use_visible=True,
        export_vertex_color="ACTIVE",
        export_active_vertex_color_when_no_material=True,
    )

    return output_path


if __name__ == "__main__":
    script_arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    recipes = variant_recipes()

    for requested_variant in script_arguments or list(recipes):
        print(f"BUILT {requested_variant} -> {build_variant(requested_variant, recipes[requested_variant])}")
