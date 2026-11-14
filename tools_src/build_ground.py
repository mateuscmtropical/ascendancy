"""Model the city ground and export it as art/town/ground.gltf.

Streets sit STREET_DROP below every pavement, each pavement slab has a stone curb, and the planted beds
of the squares, the roundabout and the avenue median are raised lawns with their own curb, a gentle swell
and clipped hedges along the street side. The layout (paths, beds, heights) comes from build_hub_scene.py,
so props placed there and the ground modelled here always agree.

Beds are cut out of a regular grid by clipping its triangles against the bed distance field, which gives
smooth curved curbs without boolean operations.

Godot (x, y, z) = Blender (x, -z, y). Meshes named *-colonly / *-convcolonly become collision in Godot:
the slabs get a sloped skirt and the beds a ramped edge, so characters walk up a curb instead of hitting it.

Usage (after build_cathedral.py, which writes the stone textures):
  blender -b --factory-startup -P tools_src/build_ground.py
"""

import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_hub_scene as layout  # noqa: E402
from build_cathedral import (  # noqa: E402
    GENERATED_TEXTURES,
    OUTPUT_DIR,
    load_kit_image,
    make_material,
    make_tinted_image,
    object_from_bmesh,
    save_generated_image,
)

GRID_STEP = 0.5
COLLISION_GRID_STEP = 1.0
SLAB_CURB_WIDTH = 0.32
SKIRT_WIDTH = 0.3  # largura da rampa de colisão do meio-fio
HEDGE_BAND = (0.45, 1.25)  # distância da borda do canteiro (lado da rua) onde fica a sebe
HEDGE_PATH_CLEARANCE = 1.6
HEDGE_HEIGHT = 0.8
METERS_PER_TILE = {"brick": 1.0, "stone": 2.6, "street": 3.2, "curb": 1.5, "grass": 7.0, "hedge": 1.6}


# ---------- textures ----------

def fractal_noise(size: int, octaves: list, seed: int) -> numpy.ndarray:
    """Tileable value noise in 0..1: sum of random grids of the given cell counts, bilinearly upsampled."""
    generator = numpy.random.default_rng(seed)
    total = numpy.zeros((size, size))
    coordinates = numpy.arange(size)

    for cells, weight in octaves:
        grid = generator.random((cells, cells))
        position = coordinates * cells / size
        low = position.astype(int) % cells
        high = (low + 1) % cells
        blend = position - position.astype(int)
        blend = blend * blend * (3.0 - 2.0 * blend)
        rows = grid[low][:, low] * (1 - blend)[None, :] + grid[low][:, high] * blend[None, :]
        rows_high = grid[high][:, low] * (1 - blend)[None, :] + grid[high][:, high] * blend[None, :]
        total += weight * (rows * (1 - blend)[:, None] + rows_high * blend[:, None])

    return total / sum(weight for _, weight in octaves)


def make_ramp_image(name: str, noise: numpy.ndarray, dark: tuple, light: tuple):
    rgb = numpy.array(dark)[None, None, :] + (numpy.array(light) - numpy.array(dark))[None, None, :] * noise[..., None]
    rgba = numpy.concatenate([rgb, numpy.ones((*noise.shape, 1))], axis=2)

    return save_generated_image(name, rgba, noise.shape[0])


def make_normal_image(name: str, height: numpy.ndarray, strength: float):
    """Tangent-space normal map (OpenGL/Godot convention) from a tileable height field."""
    slope_x = (numpy.roll(height, -1, axis=1) - numpy.roll(height, 1, axis=1)) * strength
    slope_y = (numpy.roll(height, -1, axis=0) - numpy.roll(height, 1, axis=0)) * strength
    length = numpy.sqrt(slope_x ** 2 + slope_y ** 2 + 1.0)
    rgb = numpy.stack([-slope_x / length, -slope_y / length, 1.0 / length], axis=2) * 0.5 + 0.5
    rgba = numpy.concatenate([rgb, numpy.ones((*height.shape, 1))], axis=2)
    image = save_generated_image(name, rgba, height.shape[0])

    image.colorspace_settings.name = "Non-Color"

    return image


def brick_paving_height(size: int = 500) -> numpy.ndarray:
    """Height of the running-bond paving written by build_plaza_props.make_brick_paving_image (same joints)."""
    rows, bricks_per_row = 10, 5
    pixel_rows, pixel_columns = numpy.meshgrid(numpy.arange(size), numpy.arange(size), indexing="ij")
    brick_height = size // rows
    brick_width = size / bricks_per_row
    shifted_columns = pixel_columns + ((pixel_rows // brick_height) % 2) * brick_width / 2.0
    joint_distance = numpy.minimum(numpy.minimum(pixel_rows % brick_height, brick_height - pixel_rows % brick_height), numpy.minimum(shifted_columns % brick_width, brick_width - shifted_columns % brick_width))

    return numpy.clip(joint_distance / 5.0, 0.0, 1.0)


def build_ground_materials() -> dict:
    grass_noise = 0.55 * fractal_noise(512, [(4, 1.0), (9, 0.6), (21, 0.3)], 5) + 0.45 * fractal_noise(512, [(128, 1.0), (256, 0.8)], 6)
    hedge_noise = fractal_noise(256, [(24, 1.0), (64, 1.0), (128, 0.6)], 8)
    grass_image = make_ramp_image("T_Lawn_BaseColor", grass_noise, (0.15, 0.34, 0.13), (0.4, 0.62, 0.27))
    hedge_image = make_ramp_image("T_Hedge_BaseColor", hedge_noise, (0.08, 0.26, 0.13), (0.3, 0.56, 0.24))
    hedge_normal = make_normal_image("T_Hedge_Normal", hedge_noise, 6.0)
    street_image = make_tinted_image("T_UnevenBrick_BaseColor.png", "T_Street_BaseColor", (0.6, 0.6, 0.66), (0.02, 0.02, 0.04))
    stone_image = make_tinted_image("T_UnevenBrick_BaseColor.png", "T_Pavement_BaseColor", (0.92, 0.88, 0.82), (0.05, 0.05, 0.04))
    curb_image = make_tinted_image("T_RockTrim_BaseColor.png", "T_Curb_BaseColor", (0.95, 0.93, 0.9), (0.1, 0.1, 0.1))
    brick_image = bpy.data.images.load(str(GENERATED_TEXTURES / "T_BrickPaving_BaseColor.png"))
    brick_normal = make_normal_image("T_BrickPaving_Normal", brick_paving_height(), 1.6)
    uneven_normal = load_kit_image("T_UnevenBrick_Normal.png", False)
    uneven_roughness = load_kit_image("T_UnevenBrick_Roughness.png", False)

    return {
        "brick": make_material("M_GroundBrick", brick_image, brick_normal),
        "stone": make_material("M_GroundStone", stone_image, uneven_normal, uneven_roughness),
        "street": make_material("M_GroundStreet", street_image, uneven_normal, uneven_roughness),
        "curb": make_material("M_GroundCurb", curb_image, load_kit_image("T_RockTrim_Normal.png", False)),
        "grass": make_material("M_GroundLawn", grass_image),
        "hedge": make_material("M_GroundHedge", hedge_image, hedge_normal),
    }


# ---------- clipped grid meshes ----------

def bed_fields(point: tuple) -> tuple:
    """(bed distance, hedge distance): the hedge follows the street edge of a square and keeps clear of every path."""
    bed = layout.bed_field(point)
    street_edge = layout.square_edge_distance(point)
    path_clearance = min(layout.path_distance(point, path) for path in layout.SQUARE_PATHS)
    hedge = min(street_edge - HEDGE_BAND[0], HEDGE_BAND[1] - street_edge, path_clearance - HEDGE_PATH_CLEARANCE)

    return bed, hedge


def grid_triangles(minimum: tuple, maximum: tuple, step: float) -> list:
    """Triangles of a regular grid over a Godot (x, z) rectangle; each vertex is (x, z, bed, hedge)."""
    columns = int(round((maximum[0] - minimum[0]) / step))
    rows = int(round((maximum[1] - minimum[1]) / step))
    vertices = {}

    for row in range(rows + 1):
        for column in range(columns + 1):
            point = (minimum[0] + column * step, minimum[1] + row * step)
            vertices[(column, row)] = (*point, *bed_fields(point))

    triangles = []

    for row in range(rows):
        for column in range(columns):
            corners = [vertices[(column, row)], vertices[(column + 1, row)], vertices[(column + 1, row + 1)], vertices[(column, row + 1)]]

            if max(corner[2] for corner in corners) <= 0.0:
                continue

            triangles.append([corners[0], corners[1], corners[2]])
            triangles.append([corners[0], corners[2], corners[3]])

    return triangles


def clip_polygon(polygon: list, field_index: int, level: float, keep_above: bool) -> list:
    """Sutherland-Hodgman against an iso-line of one per-vertex field (linear along edges)."""
    sign = 1.0 if keep_above else -1.0
    clipped = []

    for index, current in enumerate(polygon):
        following = polygon[(index + 1) % len(polygon)]
        current_value = sign * (current[field_index] - level)
        following_value = sign * (following[field_index] - level)

        if current_value >= 0.0:
            clipped.append(current)

        if (current_value >= 0.0) != (following_value >= 0.0):
            blend = current_value / (current_value - following_value)
            clipped.append(tuple(a + (b - a) * blend for a, b in zip(current, following)))

    return clipped if len(clipped) >= 3 else []


def clip_region(polygons: list, limits: list) -> list:
    """Keep the part of every polygon inside all limits: (field index, level, keep_above)."""
    for field_index, level, keep_above in limits:
        polygons = [clipped for clipped in (clip_polygon(polygon, field_index, level, keep_above) for polygon in polygons) if clipped]

    return polygons


def region_mesh(name: str, polygons: list, height_of, material, wall_bottom: float = None) -> bpy.types.Object:
    """Mesh of clipped polygons at height_of(vertex); wall_bottom adds a skirt down from every open edge."""
    region_bmesh = bmesh.new()
    vertices = {}

    def vertex_for(corner: tuple):
        key = (round(corner[0], 3), round(corner[1], 3))

        if key not in vertices:
            vertices[key] = region_bmesh.verts.new((corner[0], -corner[1], height_of(corner)))

        return vertices[key]

    for polygon in polygons:
        face_vertices = []

        for corner in polygon:
            vertex = vertex_for(corner)

            if vertex not in face_vertices:
                face_vertices.append(vertex)

        if len(face_vertices) >= 3:
            try:
                region_bmesh.faces.new(list(reversed(face_vertices)))
            except ValueError:
                pass

    if wall_bottom is not None:
        open_loops = [(loop.vert, loop.link_loop_next.vert) for face in region_bmesh.faces for loop in face.loops if loop.edge.is_boundary]

        for first, second in open_loops:
            first_base = region_bmesh.verts.new((first.co.x, first.co.y, wall_bottom))
            second_base = region_bmesh.verts.new((second.co.x, second.co.y, wall_bottom))
            region_bmesh.faces.new([second, first, first_base, second_base])

        bmesh.ops.remove_doubles(region_bmesh, verts=region_bmesh.verts, dist=0.0005)

    bmesh.ops.recalc_face_normals(region_bmesh, faces=region_bmesh.faces)

    return object_from_bmesh(name, region_bmesh, material)


def hedge_top(corner: tuple) -> float:
    """Clipped hedge with a softly uneven top."""
    return layout.bed_height(corner[2]) + HEDGE_HEIGHT + 0.05 * math.sin(corner[0] * 1.7) * math.cos(corner[1] * 1.3)


def collision_height(corner: tuple) -> float:
    """Bed height with the curb turned into a short ramp."""
    return min(layout.bed_height(max(corner[2], layout.CURB_WIDTH)), layout.CURB_HEIGHT * max(corner[2], 0.0) / SKIRT_WIDTH + 0.02)


def bed_domains() -> list:
    """Godot (x, z) rectangles that contain planted beds."""
    radius = layout.ROUNDABOUT_LAWN_RADII[1] + 1.0
    roundabout = ((layout.ROUNDABOUT[0] - radius, layout.ROUNDABOUT[1] - radius), (layout.ROUNDABOUT[0] + radius, layout.ROUNDABOUT[1] + radius))
    padded_medians = [((minimum[0] - 1.0, minimum[1] - 1.0), (maximum[0] + 1.0, maximum[1] + 1.0)) for minimum, maximum in layout.MEDIAN_BEDS]

    return list(layout.LAWN_RECTS.values()) + [roundabout] + padded_medians


def build_beds(materials: dict) -> None:
    curb_width = layout.CURB_WIDTH

    for index, (minimum, maximum) in enumerate(bed_domains()):
        triangles = grid_triangles(minimum, maximum, GRID_STEP)
        collision_triangles = grid_triangles(minimum, maximum, COLLISION_GRID_STEP)
        hedge_polygons = clip_region(triangles, [(2, HEDGE_BAND[0], True), (3, 0.0, True)])

        region_mesh(f"BedCurb{index}", clip_region(triangles, [(2, 0.0, True), (2, curb_width, False)]), lambda corner: layout.CURB_HEIGHT, materials["curb"], wall_bottom=0.0)
        region_mesh(f"BedLawn{index}", clip_region(triangles, [(2, curb_width, True)]), lambda corner: layout.bed_height(max(corner[2], curb_width)), materials["grass"])
        region_mesh(f"Bed{index}-colonly", clip_region(collision_triangles, [(2, 0.0, True)]), collision_height, None)

        if hedge_polygons:
            region_mesh(f"BedHedge{index}", hedge_polygons, hedge_top, materials["hedge"], wall_bottom=layout.LAWN_EDGE_HEIGHT)
            region_mesh(f"Hedge{index}-colonly", hedge_polygons, hedge_top, None, wall_bottom=layout.LAWN_EDGE_HEIGHT)


# ---------- slabs ----------

def make_flat_quad(name: str, minimum: tuple, maximum: tuple, height: float, material) -> bpy.types.Object:
    quad_bmesh = bmesh.new()
    corners = [(minimum[0], -minimum[1]), (minimum[0], -maximum[1]), (maximum[0], -maximum[1]), (maximum[0], -minimum[1])]

    quad_bmesh.faces.new([quad_bmesh.verts.new((x, y, height)) for x, y in corners])

    return object_from_bmesh(name, quad_bmesh, material)


def make_curb_frame(name: str, minimum: tuple, maximum: tuple, material) -> None:
    """Stone curb around a slab: flat top band plus the vertical face down to the street."""
    inner_minimum = (minimum[0] + SLAB_CURB_WIDTH, minimum[1] + SLAB_CURB_WIDTH)
    inner_maximum = (maximum[0] - SLAB_CURB_WIDTH, maximum[1] - SLAB_CURB_WIDTH)
    frame_bmesh = bmesh.new()
    outer = [(minimum[0], -minimum[1]), (minimum[0], -maximum[1]), (maximum[0], -maximum[1]), (maximum[0], -minimum[1])]
    inner = [(inner_minimum[0], -inner_minimum[1]), (inner_minimum[0], -inner_maximum[1]), (inner_maximum[0], -inner_maximum[1]), (inner_maximum[0], -inner_minimum[1])]
    top_outer = [frame_bmesh.verts.new((x, y, 0.0)) for x, y in outer]
    top_inner = [frame_bmesh.verts.new((x, y, 0.0)) for x, y in inner]
    base_outer = [frame_bmesh.verts.new((x, y, -layout.STREET_DROP)) for x, y in outer]

    for corner in range(4):
        following = (corner + 1) % 4
        frame_bmesh.faces.new([top_outer[corner], top_outer[following], top_inner[following], top_inner[corner]])
        frame_bmesh.faces.new([top_outer[following], top_outer[corner], base_outer[corner], base_outer[following]])

    bmesh.ops.recalc_face_normals(frame_bmesh, faces=frame_bmesh.faces)
    object_from_bmesh(name, frame_bmesh, material)


def make_slab_collider(name: str, minimum: tuple, maximum: tuple) -> None:
    """Convex frustum: slab top at 0 with a sloped skirt down to the street."""
    center = ((minimum[0] + maximum[0]) / 2.0, -(minimum[1] + maximum[1]) / 2.0)
    half = ((maximum[0] - minimum[0]) / 2.0, (maximum[1] - minimum[1]) / 2.0)
    collider_bmesh = bmesh.new()

    bmesh.ops.create_cube(collider_bmesh, size=1.0)

    for vertex in collider_bmesh.verts:
        is_top = vertex.co.z > 0.0
        spread = 0.0 if is_top else SKIRT_WIDTH
        vertex.co = (center[0] + math.copysign(half[0] + spread, vertex.co.x), center[1] + math.copysign(half[1] + spread, vertex.co.y), 0.0 if is_top else -layout.STREET_DROP - 0.02)

    object_from_bmesh(name, collider_bmesh, None)


def slab_rectangles() -> list:
    """(name, min, max, [(surface min, surface max, material key)]) for every raised pavement, Godot (x, z)."""
    half_x, half_z = layout.SQUARE_HALF
    west = layout.GETULIO_VARGAS[0] - half_x
    east = layout.SAO_JOSE[0] + half_x
    calcadao = (layout.GETULIO_VARGAS[0] + half_x, layout.SAO_JOSE[0] - half_x)
    squares = [
        ((west, -half_z), (calcadao[0], half_z), "brick"),
        ((calcadao[0], -half_z), (calcadao[1], half_z), "stone"),
        ((calcadao[1], -half_z), (east, half_z), "brick"),
    ]
    blocks = [(f"Block{index}", (block[0], block[2]), (block[1], block[3]), [((block[0], block[2]), (block[1], block[3]), "stone")]) for index, block in enumerate(layout.BLOCKS)]
    median = ("Median", (layout.CITY_MIN[0], layout.MEDIAN_Z[0]), (layout.CITY_MAX[0], layout.MEDIAN_Z[1]), [((layout.CITY_MIN[0], layout.MEDIAN_Z[0]), (layout.CITY_MAX[0], layout.MEDIAN_Z[1]), "brick")])

    return blocks + [median, ("Squares", (west, -half_z), (east, half_z), squares)]


def build_slabs(materials: dict) -> None:
    for name, minimum, maximum, surfaces in slab_rectangles():
        make_curb_frame(f"{name}Curb", minimum, maximum, materials["curb"])
        make_slab_collider(f"{name}-convcolonly", minimum, maximum)

        for surface_index, (surface_minimum, surface_maximum, material_key) in enumerate(surfaces):
            inset_minimum = (max(surface_minimum[0], minimum[0] + SLAB_CURB_WIDTH), max(surface_minimum[1], minimum[1] + SLAB_CURB_WIDTH))
            inset_maximum = (min(surface_maximum[0], maximum[0] - SLAB_CURB_WIDTH), min(surface_maximum[1], maximum[1] - SLAB_CURB_WIDTH))
            make_flat_quad(f"{name}Surface{surface_index}", inset_minimum, inset_maximum, 0.0, materials[material_key])


def make_disc(name: str, center: tuple, inner_radius: float, outer_radius: float, height: float, material, wall_bottom: float = None) -> None:
    disc_bmesh = bmesh.new()
    segments = 64
    ring = lambda radius, z: [disc_bmesh.verts.new((center[0] + radius * math.cos(2 * math.pi * index / segments), -center[1] + radius * math.sin(2 * math.pi * index / segments), z)) for index in range(segments)]
    outer = ring(outer_radius, height)
    inner = ring(inner_radius, height) if inner_radius > 0.0 else None
    base = ring(outer_radius, wall_bottom) if wall_bottom is not None else None

    if inner is None:
        disc_bmesh.faces.new(outer)

    for index in range(segments):
        following = (index + 1) % segments

        if inner is not None:
            disc_bmesh.faces.new([outer[index], outer[following], inner[following], inner[index]])

        if base is not None:
            disc_bmesh.faces.new([outer[following], outer[index], base[index], base[following]])

    bmesh.ops.recalc_face_normals(disc_bmesh, faces=disc_bmesh.faces)
    object_from_bmesh(name, disc_bmesh, material)


def build_roundabout(materials: dict) -> None:
    radius = layout.ROUNDABOUT_RADIUS
    collider_bmesh = bmesh.new()

    make_disc("RoundaboutCurb", layout.ROUNDABOUT, radius - SLAB_CURB_WIDTH, radius, 0.001, materials["curb"], wall_bottom=-layout.STREET_DROP)
    make_disc("RoundaboutPaving", layout.ROUNDABOUT, 0.0, radius - SLAB_CURB_WIDTH, 0.001, materials["brick"])
    bmesh.ops.create_cone(collider_bmesh, cap_ends=True, segments=24, radius1=radius + SKIRT_WIDTH, radius2=radius, depth=layout.STREET_DROP + 0.02)
    bmesh.ops.translate(collider_bmesh, vec=(layout.ROUNDABOUT[0], -layout.ROUNDABOUT[1], -(layout.STREET_DROP + 0.02) / 2.0), verts=collider_bmesh.verts)
    object_from_bmesh("Roundabout-convcolonly", collider_bmesh, None)


def build_inlays(materials: dict) -> None:
    """Stone inlays that break up the brick: the chafariz plaza, the coreto plaza and the rondels."""
    discs = [("ChafarizPlaza", layout.GETULIO_VARGAS, layout.PLAZA_RADIUS - 0.6), ("CoretoPlaza", layout.COREO_POSITION, layout.COREO_PLAZA_RADIUS - 0.6)]
    discs += [(f"Rondel{index}", rondel, layout.RONDEL_RADIUS - 0.5) for index, rondel in enumerate(layout.rondel_centers())]

    for name, center, radius in discs:
        make_disc(f"{name}Stone", center, 0.0, radius - 0.3, 0.012, materials["stone"])
        make_disc(f"{name}Border", center, radius - 0.3, radius, 0.012, materials["curb"])


def build_streets(materials: dict) -> None:
    make_flat_quad("Streets", layout.CITY_MIN, layout.CITY_MAX, -layout.STREET_DROP, materials["street"])


# ---------- export ----------

def map_world_uvs(mesh_object: bpy.types.Object, meters_per_tile: float) -> None:
    """Top-down UVs for flat faces, side-on UVs for curb and hedge walls, all in world metres (seamless across meshes)."""
    uv_bmesh = bmesh.new()
    uv_bmesh.from_mesh(mesh_object.data)
    uv_layer = uv_bmesh.loops.layers.uv.verify()

    for face in uv_bmesh.faces:
        is_wall = abs(face.normal.z) < 0.5

        for loop in face.loops:
            position = loop.vert.co
            loop[uv_layer].uv = ((position.x + position.y) / meters_per_tile, position.z / meters_per_tile) if is_wall else (position.x / meters_per_tile, position.y / meters_per_tile)

    uv_bmesh.to_mesh(mesh_object.data)
    uv_bmesh.free()


def merge_by_material(materials: dict) -> None:
    for key, material in materials.items():
        mesh_objects = [scene_object for scene_object in bpy.data.objects if scene_object.type == "MESH" and scene_object.data.materials and scene_object.data.materials[0] == material]

        for mesh_object in mesh_objects:
            map_world_uvs(mesh_object, METERS_PER_TILE[key])

        with bpy.context.temp_override(active_object=mesh_objects[0], selected_editable_objects=mesh_objects):
            bpy.ops.object.join()

        mesh_objects[0].name = "Ground" + material.name.removeprefix("M_Ground")

        for polygon in mesh_objects[0].data.polygons:
            polygon.use_smooth = key in ("grass", "hedge")


def build_ground() -> Path:
    output_path = OUTPUT_DIR / "ground.gltf"

    bpy.ops.wm.read_factory_settings(use_empty=True)

    materials = build_ground_materials()
    build_streets(materials)
    build_slabs(materials)
    build_roundabout(materials)
    build_inlays(materials)
    build_beds(materials)
    merge_by_material(materials)

    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_texture_dir="textures", export_yup=True)

    return output_path


if __name__ == "__main__":
    print(f"BUILT ground -> {build_ground()}")
