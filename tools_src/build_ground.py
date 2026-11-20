"""Model the city ground and export it as art/town/ground.gltf.

Streets sit STREET_DROP below every pavement, each pavement slab has a stone curb, and the planted beds
of the squares, the roundabout, the marco and the avenue median are raised lawns with their own curb, a gentle
swell and a knee-high clipped hedge all around, broken by a few gaps with topiary balls. The layout (paths, beds, heights) comes from build_hub_scene.py,
so props placed there and the ground modelled here always agree.

Beds are cut out of a regular grid by clipping its triangles against the bed distance field, which gives
smooth curved curbs without boolean operations.

Godot (x, y, z) = Blender (x, -z, y). Meshes named *-colonly / *-convcolonly become collision in Godot:
the slabs get a sloped skirt and the beds a ramped edge, so characters walk up a curb instead of hitting it.

Usage (after build_cathedral.py, which writes the stone textures):
  blender -b --factory-startup -P tools_src/build_ground.py
"""

import math
import random
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
    make_plain_material,
    make_tinted_image,
    object_from_bmesh,
    save_generated_image,
)

GRID_STEP = 0.5
COLLISION_GRID_STEP = 1.0
SLAB_CURB_WIDTH = 0.32
SKIRT_WIDTH = 0.3  # largura da rampa de colisão do meio-fio
HEDGE_HEIGHT = 0.50  # acima da grama da borda: altura do joelho
HEDGE_CHAMFER = 0.08
TOPIARY_RADIUS = 0.35
WINDOW_GRID_STEP = 0.5
ROUNDABOUT_INLAY_RADII = (7.55, 7.85)  # faixa de pedra clara na pista em anel
MARCO_BASE = 1.2
MARCO_HEIGHT = 5.0
HEDGE_GAPS = layout.hedge_gaps()
METERS_PER_TILE = {"brick": 1.0, "stone": 1.7, "street": 1.8, "curb": 1.5, "grass": 7.0, "hedge": 1.6}
FLOWER_LEAF_COLOR = "3F8A50"
FLOWER_HEADS = (3, 5)  # cabeças por tufo
FLOWER_HEAD_RADIUS = (0.045, 0.07)


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
    grass_image = make_ramp_image("T_Lawn_BaseColor", grass_noise, (0.07, 0.2, 0.06), (0.3, 0.52, 0.19))
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
        "flower_leaf": make_plain_material("M_GroundFlowerLeaf", linear_color(FLOWER_LEAF_COLOR), 0.0, 0.85),
        **{f"flower_{name}": make_plain_material(f"M_GroundFlower{name.title()}", linear_color(hex_value), 0.0, 0.7) for name, hex_value in layout.FLOWER_COLORS.items()},
    }


def linear_color(hex_value: str) -> tuple:
    return tuple((int(hex_value[offset:offset + 2], 16) / 255.0) ** 2.2 for offset in (0, 2, 4))


# ---------- clipped grid meshes ----------

def bed_fields(point: tuple) -> tuple:
    """(bed distance, gap distance): the hedge runs along every bed edge except within HEDGE_GAP_HALF_WIDTH of a gap."""
    gap = min(math.hypot(point[0] - center[0], point[1] - center[1]) for center in HEDGE_GAPS) - layout.HEDGE_GAP_HALF_WIDTH

    return layout.bed_field(point), gap


def grid_triangles(minimum: tuple, maximum: tuple, step: float, fields_of=bed_fields, band: tuple = (0.0, math.inf)) -> list:
    """Triangles of a regular grid over a Godot (x, z) rectangle; each vertex is (x, z, *fields_of(point)).

    Only cells whose first field reaches into band are kept.
    """
    columns = int(round((maximum[0] - minimum[0]) / step))
    rows = int(round((maximum[1] - minimum[1]) / step))
    vertices = {}

    for row in range(rows + 1):
        for column in range(columns + 1):
            point = (minimum[0] + column * step, minimum[1] + row * step)
            vertices[(column, row)] = (*point, *fields_of(point))

    triangles = []

    for row in range(rows):
        for column in range(columns):
            corners = [vertices[(column, row)], vertices[(column + 1, row)], vertices[(column + 1, row + 1)], vertices[(column, row + 1)]]
            values = [corner[2] for corner in corners]

            if max(values) < band[0] or min(values) > band[1]:
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
    """Flat knee-high top at a fixed height, chamfered on both edges, with a soft clipped ripple."""
    inner, outer = layout.HEDGE_BAND
    depth_into_band = min(corner[2] - inner, outer - corner[2])
    chamfer = HEDGE_CHAMFER - min(max(depth_into_band, 0.0), HEDGE_CHAMFER)
    ripple = 0.03 * math.sin(corner[0] * 1.7) * math.cos(corner[1] * 1.3)

    return layout.LAWN_EDGE_HEIGHT + HEDGE_HEIGHT - chamfer + ripple


def collision_height(corner: tuple) -> float:
    """Bed height with the curb turned into a short ramp."""
    return min(layout.bed_height(max(corner[2], layout.CURB_WIDTH)), layout.CURB_HEIGHT * max(corner[2], 0.0) / SKIRT_WIDTH + 0.02)


def build_beds(materials: dict) -> None:
    curb_width = layout.CURB_WIDTH
    inner, outer = layout.HEDGE_BAND

    for index, (minimum, maximum) in enumerate(layout.bed_domains()):
        triangles = grid_triangles(minimum, maximum, GRID_STEP)
        collision_triangles = grid_triangles(minimum, maximum, COLLISION_GRID_STEP)
        hedge_polygons = clip_region(triangles, [(2, inner, True), (2, outer, False), (3, 0.0, True)])

        region_mesh(f"BedCurb{index}", clip_region(triangles, [(2, 0.0, True), (2, curb_width, False)]), lambda corner: layout.CURB_HEIGHT, materials["curb"], wall_bottom=0.0)
        region_mesh(f"BedLawn{index}", clip_region(triangles, [(2, curb_width, True)]), lambda corner: layout.bed_height(max(corner[2], curb_width)), materials["grass"])
        region_mesh(f"Bed{index}-colonly", clip_region(collision_triangles, [(2, 0.0, True)]), collision_height, None)

        if hedge_polygons:
            region_mesh(f"BedHedge{index}", hedge_polygons, hedge_top, materials["hedge"], wall_bottom=layout.LAWN_EDGE_HEIGHT)
            region_mesh(f"Hedge{index}-colonly", hedge_polygons, hedge_top, None, wall_bottom=layout.LAWN_EDGE_HEIGHT)


def build_topiary(materials: dict) -> None:
    """A clipped ball on the hedge at both ends of every gap."""
    reach = layout.HEDGE_GAP_HALF_WIDTH + TOPIARY_RADIUS * 0.6
    height = layout.LAWN_EDGE_HEIGHT + HEDGE_HEIGHT + TOPIARY_RADIUS * 0.55
    ends = [(gap[0] + side * reach * layout.hedge_tangent(gap)[0], gap[1] + side * reach * layout.hedge_tangent(gap)[1]) for gap in HEDGE_GAPS for side in (-1.0, 1.0)]

    for index, (x, z) in enumerate(ends):
        ball_bmesh = bmesh.new()
        bmesh.ops.create_icosphere(ball_bmesh, subdivisions=2, radius=TOPIARY_RADIUS)
        bmesh.ops.translate(ball_bmesh, vec=(x, -z, height), verts=ball_bmesh.verts)
        object_from_bmesh(f"Topiary{index}", ball_bmesh, materials["hedge"])


# ---------- flowers (L.1) ----------

def add_leaf_cross(leaf_bmesh, x: float, y: float, base: float, height: float, yaw: float) -> None:
    """Two crossed upright quads of foliage (the material is double-sided)."""
    half = 0.14

    for turn in (0.0, math.pi / 2.0):
        dx, dy = half * math.cos(yaw + turn), half * math.sin(yaw + turn)
        corners = [(x - dx, y - dy, base), (x + dx, y + dy, base), (x + dx * 0.6, y + dy * 0.6, base + height), (x - dx * 0.6, y - dy * 0.6, base + height)]
        leaf_bmesh.faces.new([leaf_bmesh.verts.new(corner) for corner in corners])


def add_flower_head(head_bmesh, center: tuple, radius: float) -> None:
    """Flattened four-sided pyramid: a blossom seen from above and the side."""
    apex = head_bmesh.verts.new((center[0], center[1], center[2] + radius * 0.6))
    rim = [head_bmesh.verts.new((center[0] + radius * math.cos(side * math.pi / 2.0), center[1] + radius * math.sin(side * math.pi / 2.0), center[2])) for side in range(4)]

    for side in range(4):
        head_bmesh.faces.new([rim[side], rim[(side + 1) % 4], apex])


def build_flowers(materials: dict) -> None:
    """Low flower patches inside the hedges: one mesh of leaf crosses and one of blossoms per colour (layout.flower_tufts)."""
    generator = random.Random(layout.FLOWER_SEED + 1)
    leaf_bmesh = bmesh.new()
    head_bmeshes = {name: bmesh.new() for name in layout.FLOWER_COLORS}

    for x, z, color, height, yaw in layout.flower_tufts():
        base = layout.ground_height((x, z))
        add_leaf_cross(leaf_bmesh, x, -z, base, height * 0.85, yaw)

        for _ in range(generator.randint(*FLOWER_HEADS)):
            angle = generator.uniform(0.0, 2.0 * math.pi)
            reach = generator.uniform(0.0, 0.1)
            head = (x + reach * math.cos(angle), -z + reach * math.sin(angle), base + height * generator.uniform(0.8, 1.0))
            add_flower_head(head_bmeshes[color], head, generator.uniform(*FLOWER_HEAD_RADIUS))

    object_from_bmesh("FlowerLeaves", leaf_bmesh, materials["flower_leaf"])

    for name, head_bmesh in head_bmeshes.items():
        object_from_bmesh(f"FlowerHeads{name.title()}", head_bmesh, materials[f"flower_{name}"])


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
    west = layout.WEST_SQUARE[0] - half_x
    east = layout.EAST_SQUARE[0] + half_x
    calcadao = (layout.WEST_SQUARE[0] + half_x, layout.EAST_SQUARE[0] - half_x)
    squares = [
        ((west, -half_z), (calcadao[0], half_z), "brick"),
        ((calcadao[0], -half_z), (calcadao[1], half_z), "stone"),
        ((calcadao[1], -half_z), (east, half_z), "brick"),
    ]
    blocks = [(f"Block{index}", (block[0], block[2]), (block[1], block[3]), [((block[0], block[2]), (block[1], block[3]), "stone")]) for index, block in enumerate(layout.BLOCKS)]

    return blocks + [("Squares", (west, -half_z), (east, half_z), squares)]


def roundabout_cut(point: tuple) -> float:
    """Distance outside the roundabout ring road (negative = on the ring road)."""
    return math.hypot(point[0] - layout.ROUNDABOUT[0], point[1] - layout.ROUNDABOUT[1]) - layout.ROUNDABOUT_OUTER_RADIUS


def median_field(sign: float):
    """Signed distance into one half of the avenue median: a long strip whose end toward the roundabout is a round nose."""
    center_z = sum(layout.MEDIAN_Z) / 2.0

    return lambda point: (layout.MEDIAN_HALF_WIDTH - math.hypot(max(layout.MEDIAN_NOSE_X - sign * point[0], 0.0), point[1] - center_z),)


def rectangle_overlap(first: tuple, second: tuple) -> tuple:
    """Overlap of two (min, max) rectangles, or None."""
    minimum = (max(first[0][0], second[0][0]), max(first[0][1], second[0][1]))
    maximum = (min(first[1][0], second[1][0]), min(first[1][1], second[1][1]))

    return (minimum, maximum) if minimum[0] < maximum[0] and minimum[1] < maximum[1] else None


def rectangle_minus(rectangle: tuple, hole: tuple) -> list:
    """Up to four rectangles covering rectangle outside hole (hole lies inside rectangle)."""
    (min_x, min_z), (max_x, max_z) = rectangle
    (hole_min_x, hole_min_z), (hole_max_x, hole_max_z) = hole
    pieces = [
        ((min_x, min_z), (hole_min_x, max_z)),
        ((hole_max_x, min_z), (max_x, max_z)),
        ((hole_min_x, min_z), (hole_max_x, hole_min_z)),
        ((hole_min_x, hole_max_z), (hole_max_x, max_z)),
    ]

    return [piece for piece in pieces if piece[0][0] < piece[1][0] and piece[0][1] < piece[1][1]]


def slab_collision_height(corner: tuple) -> float:
    """Slab top at 0 with the curb turned into a ramp down to the street."""
    return -(layout.STREET_DROP + 0.02) * min(1.0, max(-corner[2], 0.0) / SKIRT_WIDTH)


def build_field_slab(name: str, domain: tuple, fields_of, surfaces: list, window: tuple, materials: dict) -> None:
    """Pavement shaped by a distance field: curb and collision follow the field inside window, plain quads elsewhere."""
    padded_window = ((window[0][0] - SKIRT_WIDTH, window[0][1] - SKIRT_WIDTH), (window[1][0] + SKIRT_WIDTH, window[1][1] + SKIRT_WIDTH))
    curb_triangles = grid_triangles(*domain, WINDOW_GRID_STEP, fields_of, (0.0, SLAB_CURB_WIDTH))
    collision_triangles = grid_triangles(*padded_window, WINDOW_GRID_STEP, fields_of, (-SKIRT_WIDTH, math.inf))
    window_surfaces = [(overlap, key) for overlap, key in ((rectangle_overlap((minimum, maximum), window), key) for minimum, maximum, key in surfaces) if overlap]
    pieces = rectangle_minus(domain, window) if rectangle_overlap(domain, window) != domain else []

    region_mesh(f"{name}Curb", clip_region(curb_triangles, [(2, 0.0, True), (2, SLAB_CURB_WIDTH, False)]), lambda corner: 0.0, materials["curb"], wall_bottom=-layout.STREET_DROP)
    region_mesh(f"{name}Window-colonly", clip_region(collision_triangles, [(2, -SKIRT_WIDTH, True)]), slab_collision_height, None)

    for surface_index, ((minimum, maximum), key) in enumerate(window_surfaces):
        surface_triangles = grid_triangles(minimum, maximum, WINDOW_GRID_STEP, fields_of, (SLAB_CURB_WIDTH, math.inf))
        region_mesh(f"{name}WindowSurface{surface_index}", clip_region(surface_triangles, [(2, SLAB_CURB_WIDTH, True)]), lambda corner: 0.0, materials[key])

    for piece_index, piece in enumerate(pieces):
        add_holed_slab(f"{name}Piece{piece_index}", piece, [((minimum, maximum), key) for minimum, maximum, key in surfaces], materials, domain)


def add_inset_surfaces(name: str, slab: tuple, surfaces: list, materials: dict) -> None:
    """Flat surface quads kept clear of the curb band along the slab edges."""
    (minimum, maximum) = slab

    for surface_index, ((surface_minimum, surface_maximum), key) in enumerate(surfaces):
        inset_minimum = (max(surface_minimum[0], minimum[0] + SLAB_CURB_WIDTH), max(surface_minimum[1], minimum[1] + SLAB_CURB_WIDTH))
        inset_maximum = (min(surface_maximum[0], maximum[0] - SLAB_CURB_WIDTH), min(surface_maximum[1], maximum[1] - SLAB_CURB_WIDTH))
        make_flat_quad(f"{name}Surface{surface_index}", inset_minimum, inset_maximum, 0.0, materials[key])


def build_slabs(materials: dict) -> None:
    """Pavements: plain rectangles, except where the roundabout ring road cuts an arc out of them, and the median halves."""
    reach = layout.ROUNDABOUT_OUTER_RADIUS + 1.0
    roundabout_box = ((layout.ROUNDABOUT[0] - reach, layout.ROUNDABOUT[1] - reach), (layout.ROUNDABOUT[0] + reach, layout.ROUNDABOUT[1] + reach))
    median_reach = layout.MEDIAN_NOSE_X - layout.MEDIAN_HALF_WIDTH

    for name, minimum, maximum, surfaces in slab_rectangles():
        window = rectangle_overlap((minimum, maximum), roundabout_box)

        if window is None:
            make_curb_frame(f"{name}Curb", minimum, maximum, materials["curb"])
            add_holed_slab(name, (minimum, maximum), [((surface_minimum, surface_maximum), key) for surface_minimum, surface_maximum, key in surfaces], materials, (minimum, maximum))

            continue

        fields_of = lambda point, minimum=minimum, maximum=maximum: (min(layout.inside_distance(point, minimum, maximum), roundabout_cut(point)),)
        build_field_slab(name, (minimum, maximum), fields_of, [(surface_minimum, surface_maximum, key) for surface_minimum, surface_maximum, key in surfaces], window, materials)

    for sign, name in ((-1.0, "MedianWest"), (1.0, "MedianEast")):
        far_x = layout.CITY_MIN[0] if sign < 0.0 else layout.CITY_MAX[0]
        domain = ((min(sign * median_reach, far_x), layout.MEDIAN_Z[0]), (max(sign * median_reach, far_x), layout.MEDIAN_Z[1]))
        median = median_field(sign)
        fields_of = lambda point, median=median, domain=domain: (min(median(point)[0], layout.inside_distance(point, *domain) + SLAB_CURB_WIDTH),)
        build_field_slab(name, domain, fields_of, [(*domain, "brick")], domain, materials)


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
    """Raised island with the small fountain, a light inlay on the ring road around it."""
    radius = layout.ROUNDABOUT_ISLAND_RADIUS
    collider_bmesh = bmesh.new()

    make_disc("RoundaboutCurb", layout.ROUNDABOUT, radius - SLAB_CURB_WIDTH, radius, 0.001, materials["curb"], wall_bottom=-layout.STREET_DROP)
    make_disc("RoundaboutPaving", layout.ROUNDABOUT, 0.0, radius - SLAB_CURB_WIDTH, 0.001, materials["stone"])
    make_disc("RoundaboutInlay", layout.ROUNDABOUT, *ROUNDABOUT_INLAY_RADII, -layout.STREET_DROP + 0.004, materials["curb"])
    bmesh.ops.create_cone(collider_bmesh, cap_ends=True, segments=32, radius1=radius + SKIRT_WIDTH, radius2=radius, depth=layout.STREET_DROP + 0.02)
    bmesh.ops.translate(collider_bmesh, vec=(layout.ROUNDABOUT[0], -layout.ROUNDABOUT[1], -(layout.STREET_DROP + 0.02) / 2.0), verts=collider_bmesh.verts)
    object_from_bmesh("Roundabout-convcolonly", collider_bmesh, None)


def build_marco(materials: dict) -> None:
    """White obelisk in the middle of its round bed on the calçadão: square base, tapering shaft, pyramid tip."""
    x, y = layout.MARCO[0], -layout.MARCO[1]
    base_height = 0.6
    shaft_height = MARCO_HEIGHT - base_height - 0.5
    marco_bmesh = bmesh.new()
    collider_bmesh = bmesh.new()
    levels = [(MARCO_BASE / 2.0, 0.0), (MARCO_BASE / 2.0, base_height), (0.35, base_height), (0.35, base_height + shaft_height * 0.02), (0.175, MARCO_HEIGHT - 0.5)]
    rings = [[marco_bmesh.verts.new((x + sign_x * half, y + sign_y * half, height)) for sign_x, sign_y in ((-1, -1), (1, -1), (1, 1), (-1, 1))] for half, height in levels]
    tip = marco_bmesh.verts.new((x, y, MARCO_HEIGHT))

    for lower, upper in zip(rings, rings[1:]):
        for corner in range(4):
            following = (corner + 1) % 4
            marco_bmesh.faces.new([lower[corner], lower[following], upper[following], upper[corner]])

    for corner in range(4):
        marco_bmesh.faces.new([rings[-1][corner], rings[-1][(corner + 1) % 4], tip])

    bmesh.ops.recalc_face_normals(marco_bmesh, faces=marco_bmesh.faces)
    object_from_bmesh("Marco", marco_bmesh, materials["curb"])
    bmesh.ops.create_cube(collider_bmesh, size=1.0)
    bmesh.ops.scale(collider_bmesh, vec=(MARCO_BASE, MARCO_BASE, MARCO_HEIGHT), verts=collider_bmesh.verts)
    bmesh.ops.translate(collider_bmesh, vec=(x, y, MARCO_HEIGHT / 2.0), verts=collider_bmesh.verts)
    object_from_bmesh("Marco-convcolonly", collider_bmesh, None)


def build_inlays(materials: dict) -> None:
    """Stone inlays that break up the brick: the chafariz plaza, the coreto apron and the secondary plazas."""
    discs = [("ChafarizPlaza", layout.WEST_SQUARE, layout.PLAZA_RADIUS - 0.6), ("CoretoPlaza", layout.COREO_POSITION, layout.COREO_APRON_RADIUS - 0.4)]
    discs += [(f"Plaza{index}", center, radius - 0.5) for index, (center, radius) in enumerate(layout.secondary_plazas())]

    for name, center, radius in discs:
        make_disc(f"{name}Stone", center, 0.0, radius - 0.3, 0.012, materials["stone"])
        make_disc(f"{name}Border", center, radius - 0.3, radius, 0.012, materials["curb"])


def build_streets(materials: dict) -> None:
    """Asphalt under the whole city, open where the crypt stair goes down (layout.CRYPT_SHAFT_HOLE)."""
    city = (layout.CITY_MIN, layout.CITY_MAX)

    for piece_index, (minimum, maximum) in enumerate(rectangle_minus(city, rectangle_overlap(city, layout.CRYPT_SHAFT_HOLE))):
        make_flat_quad(f"Streets{piece_index}", minimum, maximum, -layout.STREET_DROP, materials["street"])


def add_holed_slab(name: str, slab: tuple, surfaces: list, materials: dict, domain: tuple) -> None:
    """Collider and surfaces of a plain stretch of a slab (domain is the whole slab, whose edges keep the curb band);
    a stretch that holds the crypt stair is split around its hole, which lies under the cathedral, far from edges."""
    hole = rectangle_overlap(slab, layout.CRYPT_SHAFT_HOLE)
    pieces = rectangle_minus(slab, hole) if hole else [slab]

    for piece_index, piece in enumerate(pieces):
        suffix = f"Piece{piece_index}" if len(pieces) > 1 else ""
        make_slab_collider(f"{name}{suffix}-convcolonly", *piece)
        add_inset_surfaces(f"{name}{suffix}", domain, [(overlap, key) for overlap, key in ((rectangle_overlap(piece, surface), key) for surface, key in surfaces) if overlap], materials)


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

        if not mesh_objects:
            continue

        for mesh_object in mesh_objects:
            map_world_uvs(mesh_object, METERS_PER_TILE.get(key, 1.0))

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
    build_marco(materials)
    build_beds(materials)
    build_topiary(materials)
    build_flowers(materials)
    merge_by_material(materials)

    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_texture_dir="textures", export_yup=True)

    return output_path


if __name__ == "__main__":
    print(f"BUILT ground -> {build_ground()}")
