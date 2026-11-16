"""Model the farm that feeds the town (block 5 behind the cathedral apse and the open fields past the east wall).

Outputs in art/town/farm/, each with a JSON sidecar (AABB in Godot coords, doors, lights, markers):
  farmhouse.gltf    the farmer's house: stone ground storey, half-timbered loft, porch, chimney, woodpile
  barn.gltf         red board barn with stone plinth, big double doors, hayloft door and hoist beam
  farm_yard.gltf    everything else inside the block: dirt yard and lane, kitchen garden, cow pasture with
                    shelter, hay rack and trough, pigsty with mud and hut, well with a little roof, cart,
                    wheelbarrow, haystacks, sacks and barrels, split-rail fences
  farm_fields.gltf  the fields past the wall: wheat, corn, cabbage, carrots, a meadow with haystacks,
                    scarecrows, the lane out of the gate, the stone gate posts and the outer fence
  farm_wagon.gltf   two-wheeled covered wagon pulled by a horse along the streets (features/hub/carriage.gd)
  hay_cart.gltf     open cart heaped with hay, the other wagon of the street loop

The yard and the fields are modelled in world coordinates (origin of the model = origin of the town), so the
scene places them at (0, 0, 0) without rotation; layout numbers come from build_hub_scene.py (FARM_*). Blender
coords: X = Godot X, Y = -Godot Z, Z up. Houses and props reuse the Builder of build_town_houses.py: textured
world-planar UVs tinted by vertex colour. Crops are batched one mesh per colour, so a field of a thousand
plants is a handful of objects.

Ground colliders are named for the footsteps (features/audio/tag_ground_surfaces.gd reads the name without its
number): Yard<n>, Path<n> and Field<n> sound like dirt, Bed<n> like grass.

Usage:
  blender -b --factory-startup -P tools_src/build_farm.py -- [farmhouse barn farm_yard farm_fields farm_wagon hay_cart]
"""

import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
import numpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_hub_scene import (  # noqa: E402  (plano puro em Python)
    BARN,
    FARM_FIELD_PLOTS,
    FARM_FIELDS,
    FARM_GATE_Z,
    FARM_LANE_HALF_WIDTH,
    FARM_PENS,
    FARM_YARD,
    FARMHOUSE,
    KITCHEN_GARDEN,
    STREET_DROP,
)
from build_town_houses import (  # noqa: E402
    STONE,
    TEXTURE_DIR,
    WHITE,
    WOOD,
    WOOD_DARK_BAND,
    WOOD_LIGHT_BAND,
    Builder,
    House,
    draw_chimney,
    draw_door,
    draw_window,
    Opening,
    srgb,
    textured_material,
)
from shop_props_common import barrel, lathe, sack  # noqa: E402

FARM_DIR = Path(__file__).resolve().parent.parent / "art" / "town" / "farm"
CITY_EAST_WALL_X = FARM_YARD[1]
TOWN_GATE_DEPTH = FARM_FIELDS[0] - FARM_YARD[1]  # espessura do muro: o caminho atravessa o vão
ROOF_PITCH = 48.0
OUTSIDE_GROUND = -STREET_DROP  # além do muro o chão é o do campo, na altura das ruas
YARD_TOP = 0.03  # piso de terra da quadra: 3 cm acima do calçamento que ele cobre
FIELD_RAISE = 0.06  # canteiros levemente acima do campo
FENCE_HEIGHT = 1.15
FENCE_POST_SPACING = 2.4
SEED = 5150

# Palette (style bible: clean and bright, warm wood, never dead grey).
SOIL = "A07C55"
SOIL_DARK = "7E5A3A"
SOIL_PATH = "C4A57C"
MUD = "5E4128"
STRAW = "E3C474"
STRAW_DARK = "C49A4C"
WHEAT_STALK = "D9B65A"
WHEAT_EAR = "F2D27A"
CORN_STALK = "7FA44A"
CORN_LEAF = "8DBA55"
CORN_TASSEL = "E8C878"
CORN_COB = "F2C94C"
CABBAGE_OUTER = "5E9E4E"
CABBAGE_HEART = "B8DB8A"
CARROT_LEAF = "6FB45C"
CARROT_ROOT = "E8822E"
MEADOW = "9CC46A"
BARN_RED = "A8473A"
BARN_TRIM = "F2EEE6"
FENCE_WOOD = "9A6B45"
WATER = "5A8FA8"
BURLAP = "C8A878"


def world(x: float, z: float, y: float = 0.0) -> tuple:
    """Godot world point (x, y up, z) -> Blender coords."""
    return x, -z, y


def frame_at_world(x: float, z: float, y: float = 0.0, yaw_degrees: float = 0.0) -> Matrix:
    """Local frame standing at a Godot world point, turned around the vertical (same angle in both programs)."""
    return Matrix.Translation(world(x, z, y)) @ Matrix.Rotation(math.radians(yaw_degrees), 4, "Z")


# ---------- materials and textures ----------

def smooth_noise(size: int, cells: int, generator: numpy.random.Generator) -> numpy.ndarray:
    """Tileable value noise: a cells x cells random grid blown up with smoothstep interpolation."""
    coarse = generator.random((cells, cells))
    coordinates = numpy.arange(size) * cells / size
    low = numpy.floor(coordinates).astype(int)
    high = (low + 1) % cells
    blend = coordinates - low
    blend = blend * blend * (3.0 - 2.0 * blend)
    across, down = blend[None, :], blend[:, None]
    top = coarse[numpy.ix_(low, low)] * (1.0 - across) + coarse[numpy.ix_(low, high)] * across
    bottom = coarse[numpy.ix_(high, low)] * (1.0 - across) + coarse[numpy.ix_(high, high)] * across

    return top * (1.0 - down) + bottom * down


def soil_texture() -> Path:
    """Neutral clod-and-pebble noise for dirt (vertex colour paints soil, path and mud from it)."""
    target = TEXTURE_DIR / "T_FarmSoil_BaseColor.png"

    if target.exists():
        return target

    generator = numpy.random.default_rng(SEED)
    size = 512
    value = sum(weight * smooth_noise(size, cells, generator) for cells, weight in ((6, 0.45), (24, 0.3), (96, 0.25)))
    pebbles = smooth_noise(size, 170, generator) > 0.86
    value = numpy.clip(0.8 + (value - value.mean()) * 0.5 + pebbles * 0.12, 0.0, 1.0)
    rgba = numpy.stack([value, value * 0.98, value * 0.95, numpy.ones_like(value)], axis=-1)
    image = bpy.data.images.new("T_FarmSoil_BaseColor", size, size, alpha=False)

    image.pixels.foreach_set(rgba.astype(numpy.float32).ravel())
    image.filepath_raw = str(target)
    image.file_format = "PNG"
    image.save()

    return target


def farm_builder(name: str) -> Builder:
    """Builder with the town materials plus lawn (pasture, meadow) and soil (yard, fields, mud)."""
    b = Builder(name)

    b.materials["lawn"] = textured_material("M_FarmLawn", TEXTURE_DIR / "T_Lawn_BaseColor.png", roughness=0.95)
    b.materials["soil"] = textured_material("M_FarmSoil", soil_texture(), roughness=0.95)

    return b


# ---------- crop batches: one bmesh per colour ----------

class CropBatch:
    """Thousands of small plant parts merged into one mesh per colour before they reach the Builder."""

    def __init__(self, b: Builder) -> None:
        self.builder = b
        self.meshes = {}

    def _mesh(self, tint: str):
        return self.meshes.setdefault(tint, bmesh.new())

    def hull(self, points: list, tint: str, frame: Matrix) -> None:
        part = bmesh.new()
        vertices = [part.verts.new(frame @ Vector(point)) for point in points]
        result = bmesh.ops.convex_hull(part, input=vertices)
        bmesh.ops.delete(part, geom=result["geom_interior"] + result["geom_unused"], context="VERTS")
        self._absorb(part, tint)

    def cylinder(self, base: tuple, radius: float, height: float, sides: int, tint: str, frame: Matrix, top_radius: float = None) -> None:
        part = bmesh.new()
        bmesh.ops.create_cone(part, cap_ends=True, segments=sides, radius1=radius, radius2=radius if top_radius is None else top_radius, depth=height)
        bmesh.ops.translate(part, vec=(0.0, 0.0, height / 2.0), verts=part.verts)
        bmesh.ops.transform(part, matrix=frame @ Matrix.Translation(base), verts=part.verts)
        self._absorb(part, tint)

    def ball(self, center: tuple, radius: float, tint: str, frame: Matrix, scale: tuple = (1.0, 1.0, 1.0), segments: int = 6) -> None:
        part = bmesh.new()
        bmesh.ops.create_uvsphere(part, u_segments=segments, v_segments=max(3, segments // 2 + 1), radius=radius)
        bmesh.ops.scale(part, vec=scale, verts=part.verts)
        bmesh.ops.transform(part, matrix=frame @ Matrix.Translation(center), verts=part.verts)
        self._absorb(part, tint)

    def _absorb(self, part, tint: str) -> None:
        mesh_data = bpy.data.meshes.new("CropPart")
        part.to_mesh(mesh_data)
        part.free()
        self._mesh(tint).from_mesh(mesh_data)
        bpy.data.meshes.remove(mesh_data)

    def flush(self, material: str = "paint") -> None:
        for tint, mesh in self.meshes.items():
            self.builder._link(mesh, material, srgb(tint), None, Matrix.Identity(4))

        self.meshes = {}


def blade(batch: CropBatch, frame: Matrix, length: float, width: float, yaw_degrees: float, lean_degrees: float, tint: str) -> None:
    """Thin pointed blade (wheat stalk, corn or carrot leaf): a flat diamond with a little thickness."""
    turn = frame @ Matrix.Rotation(math.radians(yaw_degrees), 4, "Z") @ Matrix.Rotation(math.radians(lean_degrees), 4, "X")
    points = [(-width / 2.0, 0.0, 0.0), (width / 2.0, 0.0, 0.0), (0.0, -0.012, length * 0.45), (0.0, 0.012, length * 0.45), (0.0, 0.0, length)]

    batch.hull(points, tint, turn)


# ---------- generic farm pieces ----------

def ground_patch(b: Builder, rectangle: tuple, top: float, material: str, tint: str, collider: str = None, thickness: float = 0.08) -> None:
    """Flat slab of ground over (min x, max x, min z, max z) in world coords, optionally with its named collider."""
    min_x, max_x, min_z, max_z = rectangle
    low, high = world(min_x, max_z, top - thickness), world(max_x, min_z, top)

    b.box(low, high, material, srgb(tint))

    if collider:
        b.collider(low, high, name=collider)


def rounded_blob(b: Builder, center: tuple, radii: tuple, top: float, tint: str, seed: int, material: str = "soil", points_count: int = 14) -> None:
    """Irregular flat puddle/patch: a lumpy polygon extruded 2 cm (mud, worn earth under the trough)."""
    generator = random.Random(seed)
    outline = [(center[0] + radii[0] * math.cos(angle) * generator.uniform(0.75, 1.1), center[1] + radii[1] * math.sin(angle) * generator.uniform(0.75, 1.1)) for angle in (2.0 * math.pi * index / points_count for index in range(points_count))]
    patch = bmesh.new()
    face = patch.faces.new([patch.verts.new(world(x, z, top)) for x, z in outline])
    extruded = bmesh.ops.extrude_face_region(patch, geom=[face])
    moved = [element for element in extruded["geom"] if isinstance(element, bmesh.types.BMVert)]
    bmesh.ops.translate(patch, vec=(0.0, 0.0, -0.02), verts=moved)

    b._link(patch, material, srgb(tint), None, Matrix.Identity(4))


def fence_run(b: Builder, points: list, ground: float, seed: int, gaps: tuple = ()) -> None:
    """Split-rail fence through world points (x, z): posts every FENCE_POST_SPACING, two rails with a little sag,
    one thin box collider per straight stretch. gaps = (start, end) stretches along the run left open."""
    generator = random.Random(seed)
    stretches = list(zip(points, points[1:]))
    travelled = 0.0

    for start, end in stretches:
        length = math.dist(start, end)
        fence_stretch(b, start, end, ground, generator, [(gap_start - travelled, gap_end - travelled) for gap_start, gap_end in gaps])
        travelled += length


def fence_stretch(b: Builder, start: tuple, end: tuple, ground: float, generator: random.Random, gaps: list) -> None:
    length = math.dist(start, end)
    direction = ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
    post_count = max(1, round(length / FENCE_POST_SPACING))
    stations = [length * index / post_count for index in range(post_count + 1)]
    is_open = [any(gap_start - 0.01 <= (first + second) / 2.0 <= gap_end + 0.01 for gap_start, gap_end in gaps) for first, second in zip(stations, stations[1:])]
    wood = srgb(FENCE_WOOD)

    def at(distance: float) -> tuple:
        return start[0] + direction[0] * distance, start[1] + direction[1] * distance

    for station in stations:
        x, z = at(station)
        lean = generator.uniform(-0.03, 0.03)
        b.box(world(x - 0.07, z + 0.07, ground - 0.1), world(x + 0.07 + lean, z - 0.07, ground + FENCE_HEIGHT + 0.08), "wood", wood, uv=("band", *WOOD_DARK_BAND, 1.5))

    for (first, second), opened in zip(zip(stations, stations[1:]), is_open):
        if opened:
            continue

        a, c = at(first), at(second)
        for rail_height in (0.45, 0.95):
            sag = generator.uniform(0.0, 0.05)
            middle = ((a[0] + c[0]) / 2.0, (a[1] + c[1]) / 2.0)
            b.beam(world(*a, ground + rail_height), world(*middle, ground + rail_height - sag), 0.09, 0.06, "wood", wood, uv=("band", *WOOD_LIGHT_BAND, 1.5))
            b.beam(world(*middle, ground + rail_height - sag), world(*c, ground + rail_height), 0.09, 0.06, "wood", wood, uv=("band", *WOOD_LIGHT_BAND, 1.5))

        fence_collider(b, a, c, ground)


def fence_collider(b: Builder, start: tuple, end: tuple, ground: float) -> None:
    length = math.dist(start, end)
    yaw = math.atan2(-(end[1] - start[1]), end[0] - start[0])
    middle = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
    frame = Matrix.Translation(world(*middle)) @ Matrix.Rotation(yaw, 4, "Z")

    b.collider((-length / 2.0, -0.1, ground), (length / 2.0, 0.1, ground + FENCE_HEIGHT + 0.1), frame=frame, name="Fence")


def rectangle_loop(rectangle: tuple) -> list:
    min_x, max_x, min_z, max_z = rectangle

    return [(min_x, min_z), (max_x, min_z), (max_x, max_z), (min_x, max_z), (min_x, min_z)]


def haystack(b: Builder, frame: Matrix, radius: float, height: float, seed: int) -> None:
    """Round medieval haystack: a straw dome around a pole, with a lighter cap and a few loose wisps."""
    generator = random.Random(seed)
    profile = [(radius, 0.0), (radius * 1.04, height * 0.2), (radius * 0.96, height * 0.45), (radius * 0.72, height * 0.7), (radius * 0.38, height * 0.9), (0.08, height)]

    lathe(b, profile, 12, "paint", STRAW_DARK, frame)
    lathe(b, [(radius * 0.74, height * 0.7), (radius * 0.4, height * 0.9), (0.09, height + 0.04)], 12, "paint", STRAW, frame)
    b.cylinder((0.0, 0.0, height - 0.1), 0.05, 0.6, 6, "wood", srgb(WOOD["escura"]), frame=frame)

    for _ in range(6):
        angle = generator.uniform(0.0, 2.0 * math.pi)
        wisp_base = (math.cos(angle) * radius * 0.95, math.sin(angle) * radius * 0.95, generator.uniform(0.0, height * 0.3))
        b.hull([wisp_base, (wisp_base[0] * 1.08, wisp_base[1] * 1.08, 0.0), (wisp_base[0] * 1.04, wisp_base[1] * 1.04, wisp_base[2] + 0.12), (wisp_base[0] * 1.02, wisp_base[1] * 1.02 + 0.05, 0.02)], "paint", srgb(STRAW), frame=frame)

    b.collider((-radius * 0.8, -radius * 0.8, 0.0), (radius * 0.8, radius * 0.8, height * 0.8), frame=frame)


def hay_pile(b: Builder, frame: Matrix, size: tuple, seed: int) -> None:
    """Loose heap of hay: overlapping squashed lumps."""
    generator = random.Random(seed)

    for _ in range(8):
        center = (generator.uniform(-size[0] / 3.0, size[0] / 3.0), generator.uniform(-size[1] / 3.0, size[1] / 3.0), 0.0)
        scale = (size[0] / 2.0 * generator.uniform(0.45, 0.75), size[1] / 2.0 * generator.uniform(0.45, 0.75), size[2] * generator.uniform(0.6, 1.0))
        b.sphere(center, 1.0, "paint", srgb(STRAW if generator.random() > 0.4 else STRAW_DARK), scale=scale, frame=frame, segments=7)

    for _ in range(int(10 * size[0] * size[1]) + 4):
        root = (generator.uniform(-size[0] / 2.5, size[0] / 2.5), generator.uniform(-size[1] / 2.5, size[1] / 2.5), size[2] * generator.uniform(0.3, 0.7))
        tip = (root[0] + generator.uniform(-0.25, 0.25), root[1] + generator.uniform(-0.25, 0.25), root[2] + generator.uniform(0.1, 0.3))
        b.beam(root, tip, 0.025, 0.012, "paint", srgb(STRAW), frame=frame, uv=None)


def trough(b: Builder, frame: Matrix, length: float) -> None:
    """Plank trough on two trestles with water in it."""
    wood = srgb(WOOD["media"])

    for side in (-1, 1):
        b.box((side * length / 2.0 - 0.08, -0.35, 0.0), (side * length / 2.0 + 0.08, 0.35, 0.3), "wood", wood, frame=frame, uv=("band", *WOOD_DARK_BAND, 1.0))

    b.box((-length / 2.0, -0.32, 0.3), (length / 2.0, 0.32, 0.36), "wood", wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    for side in (-1, 1):
        b.box((-length / 2.0, side * 0.32 - 0.03, 0.36), (length / 2.0, side * 0.32 + 0.03, 0.62), "wood", wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))
        b.box((side * length / 2.0 - 0.03, -0.32, 0.36), (side * length / 2.0 + 0.03, 0.32, 0.62), "wood", wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))

    b.box((-length / 2.0 + 0.03, -0.29, 0.36), (length / 2.0 - 0.03, 0.29, 0.54), "paint", srgb(WATER), frame=frame)
    b.collider((-length / 2.0, -0.35, 0.0), (length / 2.0, 0.35, 0.62), frame=frame)


def wheel(b: Builder, frame: Matrix, center: tuple, radius: float, width: float, spokes: int = 8) -> None:
    """Wooden cart wheel facing local X: iron tyre, felloe, hub and spokes."""
    b.cylinder((center[0] - width / 2.0, center[1], center[2]), radius, width, 16, "metal", srgb("4A4448"), frame=frame, axis="X")
    b.cylinder((center[0] - width / 2.0 - 0.01, center[1], center[2]), radius * 0.92, width + 0.02, 16, "wood", srgb(WOOD["media"]), frame=frame, axis="X")
    b.cylinder((center[0] - width / 2.0 - 0.02, center[1], center[2]), radius * 0.8, width + 0.04, 16, "paint", srgb("2E2422"), frame=frame, axis="X")
    b.cylinder((center[0] - width, center[1], center[2]), 0.1, width * 2.0, 8, "wood", srgb(WOOD["escura"]), frame=frame, axis="X")

    for spoke in range(spokes):
        angle = 2.0 * math.pi * spoke / spokes
        tip = (center[0], center[1] + math.cos(angle) * radius * 0.82, center[2] + math.sin(angle) * radius * 0.82)
        b.beam(center, tip, 0.05, 0.05, "wood", srgb(WOOD["mel"]), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))


def farm_cart(b: Builder, frame: Matrix, load: str = "hay", seed: int = 1) -> None:
    """Two-wheeled farm cart with plank sides and shafts resting on a prop; loaded with hay or sacks."""
    generator = random.Random(seed)
    wood = srgb(WOOD["mel"])
    side_wood = srgb(WOOD["media"])

    b.box((-0.75, -1.2, 0.7), (0.75, 1.2, 0.8), "wood", wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.5))

    for side in (-1, 1):
        b.box((side * 0.75 - 0.04, -1.2, 0.8), (side * 0.75 + 0.04, 1.2, 1.2), "wood", side_wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.5))
        b.box((-0.75, side * 1.2 - 0.04, 0.8), (0.75, side * 1.2 + 0.04, 1.15), "wood", side_wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.5))
        wheel(b, frame, (side * 0.9, 0.1, 0.62), 0.62, 0.08)
        b.beam((side * 0.5, -1.2, 0.72), (side * 0.45, -3.1, 0.12), 0.08, 0.08, "wood", side_wood, frame=frame)

    b.beam((0.0, -2.9, 0.0), (0.0, -2.9, 0.26), 0.12, 0.12, "wood", srgb(WOOD["escura"]), frame=frame)
    b.cylinder((-1.0, 0.1, 0.62), 0.05, 2.0, 6, "metal", srgb("4A4448"), frame=frame, axis="X")

    if load == "hay":
        hay_pile(b, frame @ Matrix.Translation((0.0, 0.0, 0.85)), (1.4, 2.3, 0.75), seed)

    if load == "sacks":
        for index in range(5):
            sack(b, frame, generator.uniform(-0.45, 0.45), -0.8 + index * 0.4, 0.8, 0.24, 0.42, "E8D7B0" if index % 2 else "DDAE62")

    b.collider((-0.95, -1.25, 0.0), (0.95, 1.25, 1.2), frame=frame)


def wheelbarrow(b: Builder, frame: Matrix) -> None:
    """Wooden wheelbarrow: tapered tray, front wheel, two handles and legs."""
    wood = srgb(WOOD["mel"])

    b.hull([(-0.32, -0.35, 0.35), (0.32, -0.35, 0.35), (-0.4, 0.45, 0.4), (0.4, 0.45, 0.4), (-0.42, -0.5, 0.68), (0.42, -0.5, 0.68), (-0.5, 0.55, 0.7), (0.5, 0.55, 0.7)], "wood", wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))
    b.hull([(-0.36, -0.42, 0.66), (0.36, -0.42, 0.66), (-0.44, 0.48, 0.68), (0.44, 0.48, 0.68), (-0.3, -0.3, 0.6), (0.3, -0.3, 0.6)], "soil", srgb(SOIL), frame=frame)
    wheel(b, frame, (0.0, -0.75, 0.24), 0.24, 0.07, spokes=6)

    for side in (-1, 1):
        b.beam((side * 0.12, -0.8, 0.26), (side * 0.32, 1.3, 0.6), 0.06, 0.06, "wood", srgb(WOOD["media"]), frame=frame)
        b.beam((side * 0.3, 0.45, 0.4), (side * 0.3, 0.5, 0.0), 0.05, 0.05, "wood", srgb(WOOD["media"]), frame=frame)

    b.collider((-0.5, -1.0, 0.0), (0.5, 1.3, 0.7), frame=frame)


def well(b: Builder, frame: Matrix) -> None:
    """Round stone well with a little tiled roof on two posts, windlass, rope and bucket."""
    wood = srgb(WOOD["escura"])

    lathe(b, [(0.95, 0.0), (0.95, 0.85), (0.72, 0.85), (0.72, 0.1)], 16, "stone", STONE["media"], frame, closed=True)
    b.cylinder((0.0, 0.0, 0.85), 1.0, 0.1, 16, "trim", srgb(STONE["clara"]), frame=frame)
    b.cylinder((0.0, 0.0, 0.25), 0.72, 0.02, 16, "paint", srgb("2E4A5A"), frame=frame)

    for side in (-1, 1):
        b.box((side * 0.85 - 0.08, -0.08, 0.85), (side * 0.85 + 0.08, 0.08, 2.5), "wood", wood, frame=frame, uv=("band", *WOOD_DARK_BAND, 1.5))
        b.hull([(-1.25, 0.0, 2.85), (1.25, 0.0, 2.85), (-1.25, side * 1.05, 2.25), (1.25, side * 1.05, 2.25), (-1.25, 0.0, 2.93), (1.25, 0.0, 2.93), (-1.25, side * 1.05, 2.33), (1.25, side * 1.05, 2.33)], "tiles", srgb("C9674E"), frame=frame)

    b.beam((-0.85, 0.0, 2.45), (0.85, 0.0, 2.45), 0.12, 0.12, "wood", wood, frame=frame)
    b.cylinder((-0.6, 0.0, 1.75), 0.12, 1.2, 8, "wood", srgb(WOOD["mel"]), frame=frame, axis="X")
    b.beam((0.85, 0.0, 1.75), (1.05, 0.0, 1.55), 0.05, 0.05, "wood", wood, frame=frame)
    b.cylinder((0.0, 0.0, 1.05), 0.015, 0.7, 4, "paint", srgb(BURLAP), frame=frame)
    lathe(b, [(0.14, 0.0), (0.17, 0.25), (0.15, 0.25), (0.12, 0.02)], 8, "wood", WOOD["media"], frame, base=(0.0, 0.0, 0.8), closed=True)
    b.collider((-1.0, -1.0, 0.0), (1.0, 1.0, 0.95), frame=frame)


def scarecrow(b: Builder, frame: Matrix, shirt: str) -> None:
    """Scarecrow on a post: patched shirt, straw hands and feet, burlap head with a floppy hat."""
    wood = srgb(WOOD["media"])

    b.box((-0.05, -0.05, 0.0), (0.05, 0.05, 2.3), "wood", wood, frame=frame)
    b.box((-0.85, -0.04, 1.6), (0.85, 0.04, 1.68), "wood", wood, frame=frame)
    b.hull([(-0.32, -0.16, 1.05), (0.32, -0.16, 1.05), (-0.32, 0.16, 1.05), (0.32, 0.16, 1.05), (-0.42, -0.14, 1.72), (0.42, -0.14, 1.72), (-0.42, 0.14, 1.72), (0.42, 0.14, 1.72)], "paint", srgb(shirt), frame=frame)
    b.box((-0.85, -0.12, 1.52), (-0.4, 0.12, 1.74), "paint", srgb(shirt), frame=frame)
    b.box((0.4, -0.12, 1.52), (0.85, 0.12, 1.74), "paint", srgb(shirt), frame=frame)
    b.box((-0.12, -0.17, 1.3), (0.08, -0.16, 1.48), "paint", srgb("E8C14F"), frame=frame)
    b.sphere((0.0, 0.0, 1.98), 0.24, "paint", srgb(BURLAP), scale=(1.0, 0.95, 1.1), frame=frame, segments=10)
    b.cylinder((0.0, 0.0, 2.14), 0.42, 0.05, 12, "paint", srgb("B58A4A"), frame=frame)
    b.cylinder((0.0, 0.0, 2.18), 0.2, 0.26, 10, "paint", srgb("B58A4A"), top_radius=0.13, frame=frame)

    for side in (-1, 1):
        b.hull([(side * 0.85, -0.08, 1.56), (side * 0.85, 0.08, 1.7), (side * 1.05, -0.1, 1.48), (side * 1.05, 0.1, 1.62), (side * 1.02, 0.0, 1.76)], "paint", srgb(STRAW), frame=frame)
        b.sphere((side * 0.09, -0.21, 2.02), 0.03, "paint", srgb("2E2422"), frame=frame, segments=6)

    b.hull([(-0.3, -0.12, 1.05), (0.3, -0.12, 1.05), (0.0, 0.0, 0.8), (-0.2, 0.1, 1.05), (0.2, 0.1, 1.05)], "paint", srgb(STRAW), frame=frame)
    b.collider((-0.15, -0.15, 0.0), (0.15, 0.15, 2.3), frame=frame)


def lean_to(b: Builder, frame: Matrix, width: float, depth: float, front_height: float, back_height: float, walls: str = "three") -> None:
    """Open plank shed: posts, board walls on the back and sides, shingled mono-pitch roof sloping to the back."""
    wood = srgb(WOOD["media"])
    boards = srgb("8C6448")

    for x, y in ((-width / 2.0, 0.0), (width / 2.0, 0.0), (-width / 2.0, depth), (width / 2.0, depth)):
        height = front_height if y == 0.0 else back_height
        b.box((x - 0.08, y - 0.08, 0.0), (x + 0.08, y + 0.08, height), "wood", wood, frame=frame, uv=("band", *WOOD_DARK_BAND, 1.5))

    b.box((-width / 2.0, depth - 0.05, 0.0), (width / 2.0, depth + 0.05, back_height - 0.05), "wood", boards, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 2.0))
    b.collider((-width / 2.0, depth - 0.1, 0.0), (width / 2.0, depth + 0.1, back_height), frame=frame)

    if walls == "three":
        for side in (-1, 1):
            b.side_prism([(0.0, 0.0), (depth, 0.0), (depth, back_height - 0.05), (0.0, front_height - 0.05)], side * width / 2.0 - 0.05, side * width / 2.0 + 0.05, "wood", boards, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 2.0))
            b.collider((side * width / 2.0 - 0.1, 0.0, 0.0), (side * width / 2.0 + 0.1, depth, front_height), frame=frame)

    b.hull([(-width / 2.0 - 0.3, -0.4, front_height + 0.12), (width / 2.0 + 0.3, -0.4, front_height + 0.12), (-width / 2.0 - 0.3, depth + 0.3, back_height + 0.02), (width / 2.0 + 0.3, depth + 0.3, back_height + 0.02), (-width / 2.0 - 0.3, -0.4, front_height), (width / 2.0 + 0.3, -0.4, front_height), (-width / 2.0 - 0.3, depth + 0.3, back_height - 0.1), (width / 2.0 + 0.3, depth + 0.3, back_height - 0.1)], "slate", srgb("9A948A"), frame=frame)


def hay_rack(b: Builder, frame: Matrix, length: float) -> None:
    """Slatted V-shaped hay manger on legs, full of hay."""
    wood = srgb(WOOD["media"])
    slats = max(4, int(length / 0.25))

    for side in (-1, 1):
        b.beam((side * length / 2.0, 0.0, 0.0), (side * length / 2.0, 0.0, 1.0), 0.1, 0.1, "wood", wood, frame=frame)
        b.beam((-length / 2.0, side * 0.45, 1.3), (length / 2.0, side * 0.45, 1.3), 0.07, 0.07, "wood", wood, frame=frame)

    b.beam((-length / 2.0, 0.0, 0.6), (length / 2.0, 0.0, 0.6), 0.08, 0.08, "wood", wood, frame=frame)

    for slat, side in ((index, sign) for index in range(slats) for sign in (-1, 1)):
        x = -length / 2.0 + length * (slat + 0.5) / slats
        b.beam((x, 0.0, 0.62), (x, side * 0.45, 1.3), 0.04, 0.04, "wood", srgb(WOOD["mel"]), frame=frame)

    hay_pile(b, frame @ Matrix.Translation((0.0, 0.0, 0.95)), (length * 0.9, 0.8, 0.4), 41)
    b.collider((-length / 2.0, -0.5, 0.0), (length / 2.0, 0.5, 1.3), frame=frame)


def log_pile(b: Builder, frame: Matrix, length: float, rows: int) -> None:
    """Firewood stacked against a wall: rows of split logs with pale cut ends, a chopping block with an axe."""
    for row in range(rows):
        logs = rows - row + 3
        for log in range(logs):
            y = -logs * 0.11 + log * 0.22 + 0.11
            b.cylinder((-length / 2.0, y, 0.11 + row * 0.19), 0.11, length, 6, "wood", srgb(WOOD["media"]), frame=frame, axis="X")
            b.cylinder((length / 2.0, y, 0.11 + row * 0.19), 0.09, 0.02, 6, "paint", srgb("E0B678"), frame=frame, axis="X")

    b.cylinder((length / 2.0 + 0.8, -0.2, 0.0), 0.3, 0.5, 10, "wood", srgb(WOOD["mel"]), frame=frame)
    b.beam((length / 2.0 + 0.8, -0.2, 0.5), (length / 2.0 + 1.0, -0.4, 1.05), 0.04, 0.04, "wood", srgb(WOOD["media"]), frame=frame)
    b.box((length / 2.0 + 0.72, -0.24, 0.46), (length / 2.0 + 0.9, -0.12, 0.6), "metal", srgb("9BB0CE"), frame=frame)
    b.collider((-length / 2.0, -0.6, 0.0), (length / 2.0, 0.6, 0.2 + rows * 0.19), frame=frame)


# ---------- crops ----------

def crop_rows(plot: tuple, spacing_across: float) -> list:
    """z of each row of a plot (rows run along x)."""
    _crop, _min_x, _max_x, min_z, max_z = plot
    count = int((max_z - min_z - 0.6) / spacing_across)
    margin = (max_z - min_z - (count - 1) * spacing_across) / 2.0

    return [min_z + margin + row * spacing_across for row in range(count)]


def plant_spots(plot: tuple, spacing_across: float, spacing_along: float, seed: int, jitter: float = 0.08) -> list:
    """(x, z) of every plant in a plot, slightly irregular, rows along x."""
    generator = random.Random(seed)
    _crop, min_x, max_x, _min_z, _max_z = plot
    along_count = int((max_x - min_x - 0.6) / spacing_along)
    rows = crop_rows(plot, spacing_across)

    return [(min_x + 0.3 + spacing_along * (index % along_count + 0.5) + generator.uniform(-jitter, jitter), rows[index // along_count] + generator.uniform(-jitter, jitter)) for index in range(along_count * len(rows))]


def plot_bed(b: Builder, plot: tuple, ground: float, ridge_spacing: float, tint: str = SOIL) -> None:
    """Soil of a plot with a low ridge under every row (the walkable collider is the flat bed)."""
    _crop, min_x, max_x, min_z, max_z = plot

    ground_patch(b, (min_x, max_x, min_z, max_z), ground + FIELD_RAISE, "soil", tint, collider="Field", thickness=FIELD_RAISE + 0.02)

    for row_z in crop_rows(plot, ridge_spacing):
        b.side_prism([(row_z - 0.22, ground + FIELD_RAISE), (row_z + 0.22, ground + FIELD_RAISE), (row_z, ground + FIELD_RAISE + 0.1)], min_x + 0.2, max_x - 0.2, "soil", srgb(SOIL_DARK), frame=row_frame())


def row_frame() -> Matrix:
    """side_prism draws (d, z) profiles extruded along u = Blender X; d is Blender Y. World z = -Y, so a profile
    written in world z is mirrored back by this frame."""
    return Matrix.Diagonal((1.0, -1.0, 1.0, 1.0))


def wheat_field(batch: CropBatch, plot: tuple, ground: float, seed: int) -> None:
    """Ripe wheat: a dense golden band over every row and nodding ears on top of it."""
    generator = random.Random(seed)
    top = ground + FIELD_RAISE
    _crop, min_x, max_x, _min_z, _max_z = plot
    segment_length = 1.2

    for row_z in crop_rows(plot, 0.55):
        segment_count = int((max_x - min_x - 0.4) / segment_length)
        for segment in range(segment_count):
            x0 = min_x + 0.2 + segment * segment_length
            height = generator.uniform(0.85, 1.05)
            batch.hull([world(x0, row_z - 0.18, top), world(x0 + segment_length, row_z - 0.18, top), world(x0, row_z + 0.18, top), world(x0 + segment_length, row_z + 0.18, top), world(x0, row_z - 0.1, top + height), world(x0 + segment_length, row_z - 0.1, top + height * generator.uniform(0.92, 1.06)), world(x0, row_z + 0.1, top + height), world(x0 + segment_length, row_z + 0.1, top + height * generator.uniform(0.92, 1.06))], WHEAT_STALK, Matrix.Identity(4))

    for x, z in plant_spots(plot, 0.55, 0.45, seed + 1, jitter=0.12):
        ear_frame = frame_at_world(x, z, top + generator.uniform(0.85, 1.02), generator.uniform(0.0, 360.0)) @ Matrix.Rotation(math.radians(generator.uniform(10.0, 30.0)), 4, "X")
        batch.hull([(-0.03, 0.0, 0.0), (0.03, 0.0, 0.0), (0.0, -0.035, 0.1), (0.0, 0.035, 0.1), (0.0, 0.0, 0.22)], WHEAT_EAR, ear_frame)


def corn_field(batch: CropBatch, plot: tuple, ground: float, seed: int) -> None:
    """Tall corn: stalk, three arching leaves, a tassel of thin spikes and a cob in its husk."""
    generator = random.Random(seed)
    top = ground + FIELD_RAISE

    for x, z in plant_spots(plot, 0.95, 0.9, seed):
        height = generator.uniform(1.9, 2.4)
        frame = frame_at_world(x, z, top, generator.uniform(0.0, 360.0))
        batch.cylinder((0.0, 0.0, 0.0), 0.04, height, 5, CORN_STALK, frame, top_radius=0.02)

        for leaf_index in range(3):
            blade(batch, frame @ Matrix.Translation((0.0, 0.0, height * (0.28 + 0.2 * leaf_index))), generator.uniform(0.7, 0.95), 0.1, leaf_index * 125.0 + generator.uniform(-20, 20), generator.uniform(50.0, 70.0), CORN_LEAF)

        for spike in range(4):
            blade(batch, frame @ Matrix.Translation((0.0, 0.0, height - 0.02)), generator.uniform(0.28, 0.4), 0.035, spike * 90.0 + generator.uniform(-15, 15), 12.0 + 14.0 * (spike % 2), CORN_TASSEL)
        batch.hull([(0.05, 0.0, height * 0.45), (0.12, -0.05, height * 0.5), (0.12, 0.05, height * 0.5), (0.17, 0.0, height * 0.68), (0.09, 0.0, height * 0.62)], CORN_COB, frame)


def cabbage_field(batch: CropBatch, plot: tuple, ground: float, seed: int) -> None:
    """Round cabbages: a pale heart in three loose outer leaves."""
    generator = random.Random(seed)
    top = ground + FIELD_RAISE

    for x, z in plant_spots(plot, 0.8, 0.75, seed):
        radius = generator.uniform(0.17, 0.23)
        frame = frame_at_world(x, z, top, generator.uniform(0.0, 360.0))
        batch.ball((0.0, 0.0, radius * 0.85), radius, CABBAGE_HEART, frame, scale=(1.0, 1.0, 0.9), segments=5)

        for leaf_index in range(3):
            turn = frame @ Matrix.Rotation(math.radians(leaf_index * 120.0), 4, "Z")
            batch.hull([(-0.05, 0.0, 0.02), (0.05, 0.0, 0.02), (-radius * 1.2, radius * 1.6, radius * 1.3), (radius * 1.2, radius * 1.6, radius * 1.3), (0.0, radius * 2.0, radius * 0.9), (0.0, radius * 0.8, radius * 0.4)], CABBAGE_OUTER, turn)


def carrot_field(batch: CropBatch, plot: tuple, ground: float, seed: int) -> None:
    """Carrots: feathery leaf tufts with the orange shoulder of the root showing above the ridge."""
    generator = random.Random(seed)
    top = ground + FIELD_RAISE + 0.08

    for x, z in plant_spots(plot, 0.6, 0.5, seed):
        frame = frame_at_world(x, z, top, generator.uniform(0.0, 360.0))
        batch.hull([(-0.045, -0.04, -0.03), (0.045, -0.04, -0.03), (0.0, 0.05, -0.03), (0.0, 0.0, 0.04)], CARROT_ROOT, frame)

        for leaf_index in range(2):
            blade(batch, frame @ Matrix.Translation((0.0, 0.0, 0.02)), generator.uniform(0.3, 0.42), 0.12, leaf_index * 180.0 + generator.uniform(-25, 25), generator.uniform(15.0, 35.0), CARROT_LEAF)


def meadow_field(b: Builder, batch: CropBatch, plot: tuple, ground: float, seed: int) -> None:
    """Mown meadow: lawn with tufts and a few round haystacks drying."""
    generator = random.Random(seed)
    _crop, min_x, max_x, min_z, max_z = plot

    ground_patch(b, (min_x, max_x, min_z, max_z), ground + 0.03, "lawn", "FFFFFF", collider="Bed", thickness=0.05)

    for _ in range(160):
        x, z = generator.uniform(min_x + 0.5, max_x - 0.5), generator.uniform(min_z + 0.5, max_z - 0.5)
        blade(batch, frame_at_world(x, z, ground + 0.03), generator.uniform(0.25, 0.45), 0.12, generator.uniform(0, 360), generator.uniform(10, 30), MEADOW)

    for index, (x, z) in enumerate(((112.0, 30.0), (118.5, 37.5), (126.0, 29.0), (134.0, 38.0), (141.0, 31.0))):
        haystack(b, frame_at_world(x, z, ground + 0.03, index * 47.0), generator.uniform(1.4, 1.8), generator.uniform(2.6, 3.2), seed + index)


CROP_BUILDERS = {"wheat": wheat_field, "corn": corn_field, "cabbage": cabbage_field, "carrot": carrot_field}
RIDGE_SPACING = {"wheat": 0.55, "corn": 0.95, "cabbage": 0.8, "carrot": 0.6, "garden": 0.8}


# ---------- buildings ----------

def build_farmhouse() -> dict:
    """Rustic farmer's house: whitewashed stone ground floor, half-timbered loft under a steep tiled roof, wooden
    porch over the door, chimney, flower boxes and a woodpile against the side wall."""
    b = farm_builder("farmhouse")
    house = House(FARMHOUSE["width"], FARMHOUSE["depth"], (3.2, 2.6), "caiada", "velha", "verde", 77)
    wood = srgb(WOOD["escura"])
    timber_rows = (house.levels[1], house.top)

    b.box((-house.half, 0.0, 0.0), (house.half, house.depth, house.levels[1]), "stone", srgb(STONE["clara"]))
    b.box((-house.half, 0.0, house.levels[1]), (house.half, house.depth, house.top), "plaster", srgb("F4EEDF"))
    b.collider((-house.half, 0.0, 0.0), (house.half, house.depth, house.top))

    for u in (-house.half, -house.half / 3.0, house.half / 3.0, house.half):
        b.box((u - 0.12, -0.06, timber_rows[0]), (u + 0.12, 0.0, timber_rows[1]), "wood", wood, uv=("band", *WOOD_DARK_BAND, 1.5))

    for z in timber_rows:
        b.box((-house.half, -0.07, z - 0.1), (house.half, 0.0, z + 0.1), "wood", wood, uv=("band", *WOOD_DARK_BAND, 1.5))

    for left, right in ((-house.half, -house.half / 3.0), (house.half / 3.0, house.half)):
        b.beam((left, -0.04, timber_rows[0] + 0.1), (right, -0.04, timber_rows[1] - 0.1), 0.14, 0.05, "wood", wood)

    rise = house.depth / 2.0 * math.tan(math.radians(ROOF_PITCH))
    ridge = house.top + rise

    b.side_prism([(0.0, house.top), (house.depth, house.top), (house.depth / 2.0, ridge)], -house.half, house.half, "plaster", srgb("F4EEDF"))
    roof_slabs(b, (-house.half - 0.45, house.half + 0.45), (-0.55, house.depth + 0.55), house.top, ridge, srgb("A85F4A"))

    for u in (-3.6, 3.6):
        draw_window(b, house, Opening(u, 1.0, 1.0, 1.2, "flat"), shutters=True, bars=1, frame_tint=srgb(STONE["clara"]))

    for u in (-2.4, 2.4):
        draw_window(b, house, Opening(u, 0.8, house.levels[1] + 0.6, 1.0, "flat"), shutters=True, bars=1, frame_tint=srgb(WOOD["mel"]))

    draw_door(b, house, 0.0, 1.2, 2.3, "flat")

    for side in (-1, 1):
        dress_gable_side(b, house, side, ridge)

    for side in (-1, 1):
        b.box((side * 1.25 - 0.08, -1.8, 0.0), (side * 1.25 + 0.08, -1.64, 2.7), "wood", wood, uv=("band", *WOOD_DARK_BAND, 1.5))
        b.beam((side * 1.25, -1.72, 2.4), (side * 1.25, -0.2, 2.9), 0.1, 0.1, "wood", wood)

    b.hull([(-1.6, -2.1, 2.7), (1.6, -2.1, 2.7), (-1.6, 0.0, 3.25), (1.6, 0.0, 3.25), (-1.6, -2.1, 2.82), (1.6, -2.1, 2.82), (-1.6, 0.0, 3.37), (1.6, 0.0, 3.37)], "tiles", srgb("A85F4A"))
    b.box((-1.5, -1.9, 0.0), (1.5, 0.0, 0.12), "wood", srgb(WOOD["media"]), uv=("band", *WOOD_LIGHT_BAND, 1.0))
    b.collider((-1.5, -1.9, 0.0), (1.5, 0.0, 0.12), name="WoodFloor")

    for u in (-3.6, 3.6):
        b.box((u - 0.6, -0.3, 0.86), (u + 0.6, 0.0, 1.0), "wood", srgb(WOOD["media"]))
        for flower in range(5):
            b.sphere((u - 0.45 + flower * 0.22, -0.15, 1.08), 0.1, "paint", srgb(("D9483B", "F2C544", "E9A6C0", "F4EFE6", "D9483B")[flower]), segments=6)

    draw_chimney(b, house, 3.5, house.depth / 2.0 + 1.0, ridge + 0.6, material="stone", pots=1)
    log_pile(b, Matrix.Translation((house.half + 0.6, house.depth / 2.0, 0.0)) @ Matrix.Rotation(math.pi / 2.0, 4, "Z"), 2.4, 3)
    b.marker("door", (0.0, -2.4, 0.0))

    return b.finish(FARM_DIR / "farmhouse.gltf", {"lot_width": FARMHOUSE["width"], "lot_depth": FARMHOUSE["depth"], "doors": house.doors})


def roof_slabs(b: Builder, across: tuple, depth: tuple, eave: float, ridge: float, tint: tuple, material: str = "tiles", thickness: float = 0.14) -> None:
    """Gable roof as two sloped slabs meeting at the ridge (ridge parallel to Blender X), with eave overhang."""
    middle = (depth[0] + depth[1]) / 2.0
    slope = (ridge - eave) / (middle - depth[0] + 0.55)
    eave_drop = 0.55 * slope

    for edge in depth:
        points = [(u, edge, eave - eave_drop + offset) for u in across for offset in (0.0, thickness)]
        points += [(u, middle, ridge + offset) for u in across for offset in (0.0, thickness)]
        b.hull(points, material, tint)


def dress_gable_side(b: Builder, house: House, side: int, ridge: float) -> None:
    """Gable wall of the farmhouse: a shuttered window downstairs, timber frame and a small loft window above."""
    wall = side * house.half
    outward = (wall, wall + side * 0.07)
    low, high = min(outward), max(outward)
    timber = srgb(WOOD["escura"])
    middle = house.depth / 2.0

    for d in (0.0, middle - 1.6, middle + 1.6, house.depth):
        b.box((low, d - 0.12, house.levels[1]), (high, d + 0.12, house.top), "wood", timber, uv=("band", *WOOD_DARK_BAND, 1.5))

    b.box((low, 0.0, house.levels[1] - 0.1), (high, house.depth, house.levels[1] + 0.1), "wood", timber, uv=("band", *WOOD_DARK_BAND, 1.5))
    b.box((low, 0.0, house.top - 0.1), (high, house.depth, house.top + 0.08), "wood", timber, uv=("band", *WOOD_DARK_BAND, 1.5))
    b.beam((wall + side * 0.035, 0.3, house.top + 0.05), (wall + side * 0.035, middle - 0.1, ridge - 0.25), 0.16, 0.07, "wood", timber)
    b.beam((wall + side * 0.035, house.depth - 0.3, house.top + 0.05), (wall + side * 0.035, middle + 0.1, ridge - 0.25), 0.16, 0.07, "wood", timber)
    gable_window(b, wall, side, middle, 1.0, 1.0, 1.2, srgb(STONE["clara"]), shutters=True, accent=house.accent)
    gable_window(b, wall, side, middle, house.levels[1] + 0.5, 0.8, 1.0, srgb(WOOD["mel"]), shutters=True, accent=house.accent)
    gable_window(b, wall, side, middle, house.top + 0.5, 0.6, 0.7, srgb(WOOD["mel"]))


def gable_window(b: Builder, wall: float, side: int, d: float, bottom: float, width: float, height: float, frame_tint: tuple, shutters: bool = False, accent: tuple = WHITE) -> None:
    """Window in a side wall (facing +-X): frame, dark glass, sill and optional shutters."""
    def span(offset_from: float, offset_to: float) -> tuple:
        first, second = wall + side * offset_from, wall + side * offset_to

        return min(first, second), max(first, second)

    frame_low, frame_high = span(0.0, 0.07)
    glass_low, glass_high = span(0.0, 0.03)
    sill_low, sill_high = span(0.0, 0.16)

    b.box((frame_low, d - width / 2.0 - 0.1, bottom - 0.1), (frame_high, d + width / 2.0 + 0.1, bottom + height + 0.1), "trim", frame_tint, uv=("band", 0.44, 0.66, 1.0))
    b.box((glass_low - 0.001 * side, d - width / 2.0, bottom), (glass_high + 0.05, d + width / 2.0, bottom + height), "glass", WHITE)
    b.box((sill_low, d - width / 2.0 - 0.14, bottom - 0.12), (sill_high, d + width / 2.0 + 0.14, bottom - 0.04), "trim", frame_tint)

    if not shutters:
        return

    shutter_low, shutter_high = span(0.04, 0.1)

    for shutter_side in (-1, 1):
        middle = d + shutter_side * (width * 0.75 + 0.12)
        b.box((shutter_low, middle - width / 4.0, bottom), (shutter_high, middle + width / 4.0, bottom + height), "paint", accent)


def build_barn() -> dict:
    """Red board-and-batten barn on a stone plinth, gable to the yard: double doors with white braces, hayloft door
    with a hoist beam, a small window each side and a vent cupola on the ridge."""
    b = farm_builder("barn")
    width, depth = BARN["width"], BARN["depth"]
    half = width / 2.0
    eave = 4.6
    rise = half * math.tan(math.radians(42.0))
    red, trim = srgb(BARN_RED), srgb(BARN_TRIM)
    door_half = 2.0

    b.box((-half, 0.0, 0.0), (half, depth, 0.7), "stone", srgb(STONE["media"]))
    b.box((-half + 0.05, 0.05, 0.7), (half - 0.05, depth - 0.05, eave), "wood", red, uv=("band", *WOOD_LIGHT_BAND, 2.0))
    b.prism([(-half + 0.05, eave), (half - 0.05, eave), (0.0, eave + rise - 0.1)], 0.05, depth - 0.05, "wood", red, uv=("band", *WOOD_LIGHT_BAND, 2.0))
    b.collider((-half, 0.0, 0.0), (half, depth, eave))

    for batten in range(int(width / 0.6) + 1):
        u = -half + 0.3 + batten * 0.6
        if abs(u) < door_half + 0.1:
            continue
        b.box((u - 0.03, -0.02, 0.7), (u + 0.03, 0.05, eave), "wood", srgb("8E3A2F"), uv=("band", *WOOD_DARK_BAND, 1.5))

    for side in (-1, 1):
        b.hull([(side * (half + 0.6), -0.6, eave - 0.15), (side * (half + 0.6), depth + 0.6, eave - 0.15), (0.0, -0.6, eave + rise + 0.15), (0.0, depth + 0.6, eave + rise + 0.15), (side * (half + 0.6), -0.6, eave - 0.02), (side * (half + 0.6), depth + 0.6, eave - 0.02), (0.0, -0.6, eave + rise + 0.28), (0.0, depth + 0.6, eave + rise + 0.28)], "slate", srgb("7E7A82"))

    for side in (-1, 1):
        leaf_from, leaf_to = sorted((0.0, side * door_half))
        b.box((leaf_from, -0.1, 0.0), (leaf_to, 0.02, 3.4), "wood", red, uv=("band", *WOOD_LIGHT_BAND, 2.0))
        b.box((leaf_from, -0.14, 0.0), (leaf_to, -0.1, 0.14), "wood", trim)
        b.box((leaf_from, -0.14, 3.26), (leaf_to, -0.1, 3.4), "wood", trim)
        b.box((side * door_half - 0.07, -0.14, 0.0), (side * door_half + 0.07, -0.1, 3.4), "wood", trim)
        b.beam((leaf_from + 0.08, -0.13, 0.14), (leaf_to - 0.08, -0.13, 3.26), 0.12, 0.04, "wood", trim)
        b.beam((leaf_to - 0.08, -0.13, 0.14), (leaf_from + 0.08, -0.13, 3.26), 0.12, 0.04, "wood", trim)

    b.box((-0.04, -0.15, 0.0), (0.04, -0.1, 3.4), "wood", trim)
    b.box((-door_half - 0.15, -0.15, 3.4), (door_half + 0.15, -0.0, 3.55), "wood", trim)
    b.box((-0.8, -0.1, 5.1), (0.8, 0.02, 6.6), "wood", srgb("8E3A2F"), uv=("band", *WOOD_LIGHT_BAND, 1.5))
    b.box((-0.9, -0.14, 5.0), (0.9, -0.1, 5.1), "wood", trim)
    b.box((-0.9, -0.14, 6.6), (0.9, -0.1, 6.7), "wood", trim)
    hay_pile(b, Matrix.Translation((0.0, -0.05, 5.1)), (1.4, 0.3, 0.35), 17)
    b.beam((0.0, 0.0, 7.0), (0.0, -1.5, 7.0), 0.2, 0.2, "wood", srgb(WOOD["escura"]))
    b.cylinder((0.0, -1.35, 6.2), 0.012, 0.8, 4, "paint", srgb(BURLAP))
    b.sphere((0.0, -1.35, 6.15), 0.08, "metal", srgb("4A4448"), segments=6)

    for side in (-1, 1):
        draw_side_window(b, side * half, depth * 0.5, trim)

    b.box((-0.5, depth / 2.0 - 0.5, eave + rise - 0.2), (0.5, depth / 2.0 + 0.5, eave + rise + 0.8), "wood", trim)
    b.hull([(-0.75, depth / 2.0 - 0.75, eave + rise + 0.75), (0.75, depth / 2.0 - 0.75, eave + rise + 0.75), (-0.75, depth / 2.0 + 0.75, eave + rise + 0.75), (0.75, depth / 2.0 + 0.75, eave + rise + 0.75), (0.0, depth / 2.0, eave + rise + 1.4)], "slate", srgb("7E7A82"))
    b.cylinder((0.0, depth / 2.0, eave + rise + 1.35), 0.02, 0.6, 4, "metal", srgb("4A4448"))
    weather_vane(b, (0.0, depth / 2.0, eave + rise + 1.95))

    sack(b, Matrix.Identity(4), 2.7, -0.6, 0.0, 0.27, 0.45, "E8D7B0")
    sack(b, Matrix.Identity(4), 3.15, -0.45, 0.0, 0.27, 0.45, "DDAE62")
    sack(b, Matrix.Identity(4), 2.9, -0.55, 0.42, 0.25, 0.4, "C98F4F")
    barrel(b, Matrix.Translation((-3.0, -0.6, 0.0)), 0.0, 0.0, 0.32, 0.95)
    barrel(b, Matrix.Translation((-3.6, -0.5, 0.0)), 0.0, 0.0, 0.3, 0.9, WOOD["mel"])
    b.collider((2.4, -0.9, 0.0), (3.5, -0.1, 0.9))
    b.collider((-4.0, -0.95, 0.0), (-2.6, -0.2, 0.95))

    return b.finish(FARM_DIR / "barn.gltf", {"lot_width": width, "lot_depth": depth, "doors": [{"x": 0.0, "width": 2.0 * door_half, "enterable": False}]})


def weather_vane(b: Builder, top: tuple) -> None:
    """Arrow vane on the cupola: a ball on the rod, the arrow along the ridge with a fletched tail."""
    x, y, z = top
    iron = srgb("4A4448")

    b.sphere((x, y, z - 0.03), 0.06, "metal", srgb("C9A24A"), segments=6)
    b.box((x - 0.015, y - 0.4, z + 0.04), (x + 0.015, y + 0.35, z + 0.07), "metal", iron)
    b.hull([(x, y - 0.55, z + 0.055), (x - 0.015, y - 0.4, z - 0.03), (x + 0.015, y - 0.4, z - 0.03), (x - 0.015, y - 0.4, z + 0.14), (x + 0.015, y - 0.4, z + 0.14)], "metal", iron)
    b.hull([(x - 0.01, y + 0.2, z + 0.055), (x + 0.01, y + 0.2, z + 0.055), (x - 0.01, y + 0.42, z - 0.07), (x + 0.01, y + 0.42, z - 0.07), (x - 0.01, y + 0.42, z + 0.18), (x + 0.01, y + 0.42, z + 0.18)], "metal", iron)


def draw_side_window(b: Builder, u: float, d: float, trim: tuple) -> None:
    outward = 1.0 if u > 0 else -1.0

    b.box((u - 0.02 * outward if outward > 0 else u - 0.1, d - 0.5, 2.0), (u + 0.1 if outward > 0 else u + 0.02, d + 0.5, 3.0), "glass", WHITE)
    b.box((u if outward > 0 else u - 0.14, d - 0.62, 1.9), (u + 0.14 if outward > 0 else u, d + 0.62, 2.0), "wood", trim)
    b.box((u if outward > 0 else u - 0.14, d - 0.62, 3.0), (u + 0.14 if outward > 0 else u, d + 0.62, 3.1), "wood", trim)


# ---------- the yard (block 5) ----------

def build_farm_yard() -> dict:
    """Ground, fences and props of the farm block, in world coordinates."""
    b = farm_builder("farm_yard")
    min_x, max_x, min_z, max_z = FARM_YARD
    cows, pigs = FARM_PENS["cows"], FARM_PENS["pigs"]
    lane = (min_x, max_x, -FARM_LANE_HALF_WIDTH, FARM_LANE_HALF_WIDTH)
    yard = (min_x, max_x, -26.0, -FARM_LANE_HALF_WIDTH)
    garden = KITCHEN_GARDEN[1:]
    batch = CropBatch(b)

    ground_patch(b, (cows[0] - 1.0, max_x, cows[2] - 1.0, cows[3] + 1.0), YARD_TOP, "lawn", "FFFFFF", collider="Bed")
    ground_patch(b, (min_x, max_x, FARM_LANE_HALF_WIDTH, cows[2] - 1.0), YARD_TOP, "soil", SOIL, collider="Yard")
    ground_patch(b, (min_x, cows[0] - 1.0, cows[2] - 1.0, max_z), YARD_TOP, "lawn", "FFFFFF", collider="Bed")
    ground_patch(b, (cows[0] - 1.0, max_x, cows[3] + 1.0, max_z), YARD_TOP, "soil", SOIL, collider="Yard")
    ground_patch(b, lane, YARD_TOP + 0.005, "soil", SOIL_PATH, collider="Path")
    ground_patch(b, yard, YARD_TOP, "soil", SOIL, collider="Yard")
    ground_patch(b, (min_x, max_x, min_z, -26.0), YARD_TOP, "soil", SOIL, collider="Yard")

    for index, (x, z, rx, rz) in enumerate(((92.0, 38.0, 3.2, 2.2), (96.5, 34.5, 2.0, 1.5), (88.5, 41.0, 1.6, 1.2))):
        rounded_blob(b, (x, z), (rx, rz), YARD_TOP + 0.012, MUD, SEED + index)

    for index, (x, z, rx, rz) in enumerate(((93.5, 9.0, 1.8, 1.1), (80.0, 24.0, 2.2, 1.4))):
        rounded_blob(b, (x, z), (rx, rz), YARD_TOP + 0.012, SOIL, SEED + 10 + index)

    for index, (x, z, rx, rz) in enumerate(YARD_GRASS_PATCHES):
        rounded_blob(b, (x, z), (rx, rz), YARD_TOP + 0.008, "FFFFFF", SEED + 50 + index, material="lawn")

    scatter_tufts(batch, YARD_GRASS_PATCHES, SEED + 60)
    build_kitchen_garden(b, batch, garden)
    fence_run(b, rectangle_loop((cows[0], cows[1], cows[2], cows[3])), YARD_TOP, SEED + 20)
    fence_run(b, rectangle_loop((pigs[0], pigs[1], pigs[2], pigs[3])), YARD_TOP, SEED + 21)

    hay_rack(b, frame_at_world(96.0, 25.5, YARD_TOP, 0.0), 3.0)
    lean_to(b, frame_at_world(94.0, 23.0, YARD_TOP, 180.0), 6.0, 3.6, 2.6, 2.1)
    trough(b, frame_at_world(88.0, 5.6, YARD_TOP, 0.0), 2.6)
    trough(b, frame_at_world(94.0, 32.2, YARD_TOP, 0.0), 2.0)
    lean_to(b, frame_at_world(97.5, 40.0, YARD_TOP, 180.0), 4.2, 2.6, 1.9, 1.5)
    hay_pile(b, frame_at_world(88.0, 42.4, YARD_TOP), (2.2, 1.0, 0.45), 61)

    well(b, frame_at_world(88.0, -15.0, YARD_TOP))
    farm_cart(b, frame_at_world(97.5, -16.0, YARD_TOP, 20.0), load="hay", seed=3)
    wheelbarrow(b, frame_at_world(84.5, -11.0, YARD_TOP, -60.0))
    haystack(b, frame_at_world(80.5, -6.5, YARD_TOP, 10.0), 1.5, 2.8, 71)
    trough(b, frame_at_world(91.5, -8.5, YARD_TOP, 90.0), 2.0)

    for index, (x, z) in enumerate(((78.0, 35.0), (81.0, 40.5), (79.5, 30.5))):
        haystack(b, frame_at_world(x, z, YARD_TOP, index * 50.0), 1.4, 2.6, 80 + index)

    for index, (x, z) in enumerate(((84.0, -24.5), (84.7, -24.0))):
        sack(b, frame_at_world(x, z, YARD_TOP), 0.0, 0.0, 0.0, 0.26, 0.44, ("E8D7B0", "DDAE62")[index])

    batch.flush()

    return b.finish(FARM_DIR / "farm_yard.gltf", {"origin": "world", "doors": []})


YARD_GRASS_PATCHES = (  # (x, z, raio x, raio z): grama que resiste nas beiradas do terreiro pisado
    (77.6, -4.6, 2.4, 1.4),
    (99.6, -11.0, 1.8, 3.2),
    (90.5, -3.6, 3.2, 1.0),
    (99.8, -21.5, 1.4, 2.2),
    (80.5, 43.4, 3.0, 1.2),
    (77.2, -44.0, 1.6, 0.8),
)


def scatter_tufts(batch: CropBatch, patches: tuple, seed: int) -> None:
    """A few blades of grass on every patch so the edges read as grass, not paint."""
    generator = random.Random(seed)

    for x, z, radius_x, radius_z in patches:
        for _ in range(int(6 * radius_x * radius_z)):
            angle, reach = generator.uniform(0.0, 2.0 * math.pi), math.sqrt(generator.random()) * 0.8
            spot = (x + math.cos(angle) * radius_x * reach, z + math.sin(angle) * radius_z * reach)
            blade(batch, frame_at_world(*spot, YARD_TOP), generator.uniform(0.18, 0.32), 0.1, generator.uniform(0, 360), generator.uniform(10, 30), MEADOW)


def build_kitchen_garden(b: Builder, batch: CropBatch, rectangle: tuple) -> None:
    """Farmhouse vegetable patch: cabbage and carrot rows in a low wattle fence with a gap toward the lane."""
    min_x, max_x, min_z, max_z = rectangle
    half_z = (min_z + max_z) / 2.0
    cabbages = ("cabbage", min_x + 0.5, max_x - 0.5, min_z + 0.4, half_z - 0.2)
    carrots = ("carrot", min_x + 0.5, max_x - 0.5, half_z + 0.2, max_z - 0.4)

    ground_patch(b, rectangle, YARD_TOP + 0.04, "soil", SOIL_DARK, collider="Field", thickness=0.06)
    cabbage_field(batch, cabbages, YARD_TOP + 0.04 - FIELD_RAISE, SEED + 30)
    carrot_field(batch, carrots, YARD_TOP + 0.04 - FIELD_RAISE, SEED + 31)
    fence_run(b, [(max_x - 2.0, max_z), (min_x, max_z), (min_x, min_z), (max_x, min_z), (max_x, max_z)], YARD_TOP, SEED + 32)


# ---------- the fields past the wall ----------

def build_farm_fields() -> dict:
    """Crop plots, meadow, the lane out of the town gate, the gate posts and the outer fence, in world coordinates."""
    b = farm_builder("farm_fields")
    min_x, max_x, min_z, max_z = FARM_FIELDS
    batch = CropBatch(b)
    gate_x = min_x - TOWN_GATE_DEPTH

    ground_patch(b, (gate_x, max_x, -FARM_LANE_HALF_WIDTH, FARM_LANE_HALF_WIDTH), OUTSIDE_GROUND + 0.03, "soil", SOIL_PATH, collider="Path", thickness=0.06)
    ground_patch(b, (min_x + 1.0, min_x + 3.0, min_z + 1.0, max_z - 1.0), OUTSIDE_GROUND + 0.03, "soil", SOIL_PATH, collider="Path", thickness=0.06)

    for name, plot in FARM_FIELD_PLOTS.items():
        build_plot(b, batch, name, plot)

    for index, (x, z, shirt) in enumerate(((126.0, -35.0, "4F8FC9"), (136.0, 12.0, "C9483B"))):
        scarecrow(b, frame_at_world(x, z, OUTSIDE_GROUND + FIELD_RAISE, index * 140.0 + 20.0), shirt)

    for side in (-1, 1):
        gate_post(b, (CITY_EAST_WALL_X + 0.6, (FARM_GATE_Z[0] if side < 0 else FARM_GATE_Z[1]) + side * 0.5))

    fence_run(b, [(min_x + 0.2, min_z), (max_x, min_z), (max_x, max_z), (min_x + 0.2, max_z)], OUTSIDE_GROUND, SEED + 40, gaps=())
    farm_cart(b, frame_at_world(128.0, 2.8, OUTSIDE_GROUND + 0.03, 95.0), load="sacks", seed=9)
    batch.flush()

    return b.finish(FARM_DIR / "farm_fields.gltf", {"origin": "world", "doors": []})


def build_plot(b: Builder, batch: CropBatch, name: str, plot: tuple) -> None:
    crop = plot[0]

    if crop == "meadow":
        meadow_field(b, batch, plot, OUTSIDE_GROUND, SEED + len(name))
        return

    plot_bed(b, plot, OUTSIDE_GROUND, RIDGE_SPACING[crop])
    CROP_BUILDERS[crop](batch, plot, OUTSIDE_GROUND, SEED + len(name) * 7)


def gate_post(b: Builder, position: tuple) -> None:
    """Stone pillar with a cap and a lantern bracket at each side of the gap in the town wall."""
    frame = frame_at_world(position[0], position[1], OUTSIDE_GROUND)

    b.box((-0.6, -0.5, 0.0), (0.6, 0.5, 4.9), "stone", srgb(STONE["media"]), frame=frame)
    b.box((-0.7, -0.6, 4.9), (0.7, 0.6, 5.15), "trim", srgb(STONE["clara"]), frame=frame)
    b.hull([(-0.55, -0.45, 5.15), (0.55, -0.45, 5.15), (-0.55, 0.45, 5.15), (0.55, 0.45, 5.15), (0.0, 0.0, 5.75)], "trim", srgb(STONE["clara"]), frame=frame)
    b.collider((-0.6, -0.5, 0.0), (0.6, 0.5, 4.9), frame=frame)


# ---------- the wagon of the street carriages ----------

def build_farm_wagon() -> dict:
    """Covered two-wheeled wagon with shafts for one horse (origin under the axle; the horse walks ahead, -Y)."""
    b = farm_builder("farm_wagon")
    frame = Matrix.Identity(4)
    cloth = srgb("F2E6CF")

    farm_cart(b, frame, load="sacks", seed=5)

    for hoop in (-1.0, 0.0, 1.0):
        b.beam((-0.78, hoop, 1.15), (-0.55, hoop, 2.05), 0.05, 0.05, "wood", srgb(WOOD["media"]), frame=frame)
        b.beam((0.78, hoop, 1.15), (0.55, hoop, 2.05), 0.05, 0.05, "wood", srgb(WOOD["media"]), frame=frame)
        b.beam((-0.55, hoop, 2.05), (0.55, hoop, 2.05), 0.05, 0.05, "wood", srgb(WOOD["media"]), frame=frame)

    b.hull([(-0.82, -1.15, 1.15), (0.82, -1.15, 1.15), (-0.82, 1.15, 1.15), (0.82, 1.15, 1.15), (-0.6, -1.15, 2.1), (0.6, -1.15, 2.1), (-0.6, 1.15, 2.1), (0.6, 1.15, 2.1)], "paint", cloth, frame=frame)
    b.box((-0.4, -1.4, 0.95), (0.4, -1.15, 1.25), "wood", srgb(WOOD["mel"]), frame=frame)
    wagon_lantern(b, frame)
    b.marker("horse", (0.0, -3.9, 0.0))

    return b.finish(FARM_DIR / "farm_wagon.gltf", {"origin": "axle", "doors": []})


def build_hay_cart() -> dict:
    """Open two-wheeled cart heaped with hay, the second wagon of the street loop."""
    b = farm_builder("hay_cart")

    farm_cart(b, Matrix.Identity(4), load="hay", seed=11)
    wagon_lantern(b, Matrix.Identity(4))
    b.marker("horse", (0.0, -3.9, 0.0))

    return b.finish(FARM_DIR / "hay_cart.gltf", {"origin": "axle", "doors": []})


def wagon_lantern(b: Builder, frame: Matrix) -> None:
    """Small lantern hanging from a hook at the front of a wagon (its glow is the untinted lead material)."""
    b.beam((0.7, -1.2, 1.1), (0.7, -1.45, 1.55), 0.04, 0.04, "metal", srgb("4A4448"), frame=frame)
    b.box((0.62, -1.53, 1.2), (0.78, -1.37, 1.42), "glow_warm", WHITE, frame=frame)
    b.box((0.6, -1.55, 1.42), (0.8, -1.35, 1.47), "metal", srgb("4A4448"), frame=frame)


MODELS = {
    "farmhouse": build_farmhouse,
    "barn": build_barn,
    "farm_yard": build_farm_yard,
    "farm_fields": build_farm_fields,
    "farm_wagon": build_farm_wagon,
    "hay_cart": build_hay_cart,
}


if __name__ == "__main__":
    requested = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    for model_name in requested or list(MODELS):
        sidecar = MODELS[model_name]()
        print(f"BUILT {model_name}: aabb {sidecar['aabb_min']} .. {sidecar['aabb_max']}")
