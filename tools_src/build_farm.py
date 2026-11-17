"""Model the fazenda that feeds the town (block 5 behind the cathedral apse and the open fields past the east wall),
a 19th-century Brazilian coffee farm.

Outputs in art/town/farm/, each with a JSON sidecar (AABB in Godot coords, doors, lights, markers):
  farmhouse.gltf    the casa-grande (farm_sede.py): stone base, whitewashed walls, blue shutters, hipped capa-e-canal
                    roof, front alpendre with turned posts and balustrade, stone stair, chimney
  barn.gltf         the tulha (farm_rural.py): whitewashed walls in a dark timber frame on a stone base, hipped roof,
                    big plank doors, raised loading door with platform and ladder (file name kept)
  farm_yard.gltf    everything else inside the block: lawn and lane, terreiro de cafe (brick paving, white kerbs,
                    coffee drying in beds, rakes, sacks, baskets), horta, curral and pigsty with heavy fences and
                    porteiras, ranchos on round posts, cacimba with sarilho, spring box with bamboo bica and trough
  farm_fields.gltf  the fields past the wall: cafezal, mandioca, sugar cane, milho, a hay field in windrows, a mown
                    meadow, scarecrows, the lane out of the gate, footpaths, gate posts and the outer fence
  farm_wagon.gltf   two-wheeled covered wagon pulled by a horse along the streets (features/hub/carriage.gd):
                    shafts up to the harness rings, driver's bench (sidecar marker driver_seat)
  hay_cart.gltf     open cart heaped with hay, the other wagon of the street loop

The palm alley along the lane is placed by build_hub_scene.py (add_palm_alley). Shared colonial pieces live in
farm_colonial.py, water works in farm_water.py.

The yard and the fields are modelled in world coordinates (origin of the model = origin of the town), so the
scene places them at (0, 0, 0) without rotation; layout numbers come from build_hub_scene.py (FARM_*). Blender
coords: X = Godot X, Y = -Godot Z, Z up. Houses and props reuse the Builder of build_town_houses.py: textured
world-planar UVs tinted by vertex colour. Plants (farm_plants.py) are alpha-cut cards from one painted atlas plus
small solids, stamped with numpy and batched one mesh per (material, tint): a field of thousands of plants is
a handful of objects.

Ground colliders are named for the footsteps (features/audio/tag_ground_surfaces.gd reads the name without its
number): Yard<n>, Path<n> and Field<n> sound like dirt, Bed<n> like grass, Terreiro like stone.

Usage:
  blender -b --factory-startup -P tools_src/build_farm.py -- [farmhouse barn farm_yard farm_fields farm_wagon hay_cart]
"""

import hashlib
import itertools
import json
import math
import random
import sys
from pathlib import Path
from typing import NamedTuple

import bmesh
import bpy
import numpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_hub_scene import (  # noqa: E402  (plano puro em Python)
    BARN,
    FARM_FIELD_PLOTS,
    FARM_FIELDS,
    FARM_GATE_Z,
    FARM_LANE_HALF_WIDTH,
    FARM_PEN_PROPS,
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
    WORLD_TILE,
    Builder,
    load_image,
    plain_material,
    srgb,
    textured_material,
)
from farm_plants import (  # noqa: E402
    CARROT_ROOT,
    MEADOW_TINTS,
    STRAW_TINTS,
    PlantBatch,
    arc_path,
    cabbage_plant,
    cane_plant,
    carrot_plant,
    cassava_plant,
    coffee_plant,
    corn_plant,
    crop_atlas,
    hay_texture,
    lathe_shape,
    rgb,
    ribbon,
    spot_matrices,
    stamp_variants,
    transforms,
    tuft_variants,
    variants_of,
)
from farm_rural import rancho, tulha  # noqa: E402
from farm_sede import casa_grande  # noqa: E402
from farm_water import cacimba, spring_box  # noqa: E402
from shop_props_common import barrel, lathe, sack  # noqa: E402

FARM_DIR = Path(__file__).resolve().parent.parent / "art" / "town" / "farm"
CITY_EAST_WALL_X = FARM_YARD[1]
TOWN_GATE_DEPTH = FARM_FIELDS[0] - FARM_YARD[1]  # espessura do muro: o caminho atravessa o vão
OUTSIDE_GROUND = -STREET_DROP  # além do muro o chão é o do campo, na altura das ruas
YARD_TOP = 0.03  # piso de terra da quadra: 3 cm acima do calçamento que ele cobre
FIELD_RAISE = 0.06  # canteiros levemente acima do campo
SEED = 5150

# Palette (style bible: clean and bright, warm wood, never dead grey).
SOIL = "A07C55"
SOIL_DARK = "7E5A3A"
SOIL_PATH = "C4A57C"
SOIL_RUT = "A08462"
STRAW = "E3C474"
MUD = "5E4128"
WATER = "5A8FA8"
BURLAP = "C8A878"
BRICK_SATURATION = 0.5  # o tijolo do terreiro é o da praça desbotado de sol: metade da saturação,
BRICK_BRIGHTNESS = 1.3  # mais claro
BRICK_DUST = "B08E66"  # e coberto de poeira de barro (#A57C61 de média, entre a madeira e a pedra da paleta)
BRICK_DUST_AMOUNT = 0.5
CROP_CARD_MATERIAL = "M_FarmCrops"
# As plantas de cada canteiro e trilha viram malhas soltas Crops<n> (a cena para de desenhar cada canteiro de longe);
# as dos props ficam na malha principal, que assim traz M_FarmCrops antes: o importador do Godot desliga a cor de
# vértice do material que aparece pela primeira vez como superfície 0 de uma malha.
CROPS_PREFIX = "Crops"
WORLD_TILE["hay"] = 1.1  # metros por repetição da palha
WORLD_TILE["paving"] = 1.0  # a textura de tijolo já traz 10 fiadas por metro
FARM_TEXTURES = {}  # pintadas uma vez por execução


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


def faded_brick_texture() -> Path:
    """The town's red paving brick bleached to the dull clay of an old terreiro: half the saturation gone, lighter, and
    a film of the yard's dust over it (vertex tint only multiplies, it can not take the red out)."""
    target = TEXTURE_DIR / "T_FarmBrick_BaseColor.png"
    source = load_image(TEXTURE_DIR / "T_BrickPaving_BaseColor.png", True)
    width, height = source.size
    rgba = numpy.array(source.pixels[:], dtype=numpy.float32).reshape(height, width, 4)
    color = rgba[..., :3]
    luma = (color @ numpy.array([0.2126, 0.7152, 0.0722], dtype=numpy.float32))[..., None]
    bleached = (luma + (color - luma) * BRICK_SATURATION) * BRICK_BRIGHTNESS
    dust = rgb(BRICK_DUST) * (luma / luma.mean())
    rgba[..., :3] = numpy.clip(bleached * (1.0 - BRICK_DUST_AMOUNT) + dust * BRICK_DUST_AMOUNT, 0.0, 1.0)
    image = bpy.data.images.new("T_FarmBrick_BaseColor", width, height, alpha=False)

    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = str(target)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)

    return target


def farm_textures() -> dict:
    """Crop atlas, hay and the faded terreiro brick, made on the first call (the same seed always writes the same files)."""
    if not FARM_TEXTURES:
        FARM_TEXTURES["crops"] = crop_atlas(TEXTURE_DIR, SEED)
        FARM_TEXTURES["hay"] = hay_texture(TEXTURE_DIR, SEED + 1)
        FARM_TEXTURES["brick"] = faded_brick_texture()

    return FARM_TEXTURES


def crop_material(atlas: Path):
    """Alpha-cut, double-sided card material of the plants (finish_model marks it MASK in the glTF)."""
    material = textured_material(CROP_CARD_MATERIAL, atlas, roughness=0.9)
    nodes = material.node_tree.nodes
    image_node = next(node for node in nodes if node.type == "TEX_IMAGE")

    material.node_tree.links.new(image_node.outputs["Alpha"], nodes["Principled BSDF"].inputs["Alpha"])
    material.use_backface_culling = False

    return material


def farm_builder(name: str) -> Builder:
    """Builder with the town materials plus lawn (pasture, meadow), soil (yard, fields, mud), hay and the crop
    cards; b.plants batches the stamped plants. Farm windows have their own glass: every pane lit at night
    (features/sky/window_glass.gd), not the town's scattering of lit and dark panes."""
    b = Builder(name)
    textures = farm_textures()

    b.materials["lawn"] = textured_material("M_FarmLawn", TEXTURE_DIR / "T_Lawn_BaseColor.png", roughness=0.95)
    b.materials["soil"] = textured_material("M_FarmSoil", soil_texture(), roughness=0.95)
    b.materials["hay"] = textured_material("M_FarmHay", textures["hay"], roughness=0.95)
    b.materials["crops"] = crop_material(textures["crops"])
    b.materials["paving"] = textured_material("M_FarmPaving", textures["brick"], TEXTURE_DIR / "T_BrickPaving_Normal.png", roughness=0.9)
    b.materials["glass"] = plain_material("M_FarmGlass", srgb("3A4E66"), 0.12, 0.4)
    b.materials["lantern"] = plain_material("M_FarmLantern", srgb("C9B48A"), 0.2)
    b.plants = PlantBatch(b, srgb)

    return b


def finish_model(b: Builder, name: str, sidecar: dict) -> dict:
    """Flush the plants, export, and turn the card material into alpha-scissor (Blender writes it as BLEND). The
    hash of the .bin goes into the .gltf: Godot only reimports when the .gltf text changes, and a rebuild that
    moves vertices or UVs (a repainted atlas) changes nothing but the .bin."""
    path = FARM_DIR / f"{name}.gltf"
    b.plants.flush()
    result = b.finish(path, sidecar, separate=(CROPS_PREFIX,))
    document = json.loads(path.read_text(encoding="utf-8"))
    cards = [material for material in document["materials"] if material["name"] == CROP_CARD_MATERIAL]

    for material in cards:
        material.update({"alphaMode": "MASK", "alphaCutoff": 0.5, "doubleSided": True})

    document["asset"]["extras"] = {"buffer_md5": hashlib.md5(path.with_suffix(".bin").read_bytes()).hexdigest()}
    path.write_text(json.dumps(document, indent=1), encoding="utf-8", newline="\n")

    return result


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


class FenceStyle(NamedTuple):
    height: float
    post: float  # thickness of the (square, rough) posts
    rails: tuple  # height of each sawn rail
    rail_width: float  # board height
    spacing: float
    post_wood: str
    rail_wood: str


FENCE_STYLES = {  # heavy Brazilian fences: thick rough posts, sawn boards nailed on, alternating faces
    "curral": FenceStyle(1.5, 0.2, (0.28, 0.64, 1.0, 1.36), 0.15, 2.4, "6B4A32", "A9794C"),
    "horta": FenceStyle(1.0, 0.13, (0.3, 0.62, 0.92), 0.1, 2.0, "7A5438", "B48A58"),
    "campo": FenceStyle(1.35, 0.17, (0.3, 0.7, 1.1), 0.13, 2.6, "6B4A32", "A9794C"),
}
RAIL_THICKNESS = 0.05


def fence_run(b: Builder, points: list, ground: float, seed: int, gaps: tuple = (), style: str = "curral", gates: tuple = ()) -> None:
    """Fence through world points (x, z): posts about every style.spacing, sawn rails, one thin box collider per
    straight stretch. gaps = (start, end) stretches along the run left open; gates = (stretch, segment) pairs where a
    porteira stands between two posts."""
    generator = random.Random(seed)
    stretches = list(zip(points, points[1:]))
    travelled = 0.0

    for index, (start, end) in enumerate(stretches):
        length = math.dist(start, end)
        stretch_gates = [segment for stretch, segment in gates if stretch == index]
        fence_stretch(b, start, end, ground, generator, [(gap_start - travelled, gap_end - travelled) for gap_start, gap_end in gaps], FENCE_STYLES[style], stretch_gates)
        travelled += length


def fence_stretch(b: Builder, start: tuple, end: tuple, ground: float, generator: random.Random, gaps: list, style: FenceStyle, gate_segments: list) -> None:
    length = math.dist(start, end)
    direction = ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
    post_count = max(1, round(length / style.spacing))
    stations = [length * index / post_count for index in range(post_count + 1)]
    segments = list(zip(stations, stations[1:]))
    is_open = [any(gap_start - 0.01 <= (first + second) / 2.0 <= gap_end + 0.01 for gap_start, gap_end in gaps) for first, second in segments]
    wood = srgb(style.post_wood)

    def at(distance: float) -> tuple:
        return start[0] + direction[0] * distance, start[1] + direction[1] * distance

    for station in stations:
        x, z = at(station)
        fence_post(b, world(x, z, ground), style, generator.uniform(-0.025, 0.025))

    for index, ((first, second), opened) in enumerate(zip(segments, is_open)):
        if opened:
            continue

        a, c = at(first), at(second)

        if index in gate_segments:
            porteira(b, a, c, ground, style)
        else:
            fence_rails(b, a, c, ground, style, index, generator)

        fence_collider(b, a, c, ground, style.height)


def segment_frame(start: tuple, end: tuple, ground: float) -> tuple:
    """(frame, length): origin at the middle of a world segment (x, z) on the ground, local X along it, Y across."""
    length = math.dist(start, end)
    yaw = math.atan2(-(end[1] - start[1]), end[0] - start[0])
    middle = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)

    return Matrix.Translation(world(*middle, ground)) @ Matrix.Rotation(yaw, 4, "Z"), length


def fence_post(b: Builder, base: tuple, style: FenceStyle, lean: float) -> None:
    """Thick rough post sunk into the ground with a chamfered cap."""
    half = style.post / 2.0
    top = style.height + 0.08
    wood = srgb(style.post_wood)
    frame = Matrix.Translation(base)

    b.box((-half, -half, -0.12), (half, half, top), "wood", wood, frame=frame @ Matrix.Rotation(lean, 4, "Y"), uv=("band", *WOOD_DARK_BAND, 1.5))
    b.hull([(-half - 0.02, -half - 0.02, top), (half + 0.02, -half - 0.02, top), (-half - 0.02, half + 0.02, top), (half + 0.02, half + 0.02, top), (-half * 0.5, -half * 0.5, top + 0.06), (half * 0.5, -half * 0.5, top + 0.06), (-half * 0.5, half * 0.5, top + 0.06), (half * 0.5, half * 0.5, top + 0.06)], "wood", shade_tint(wood, 0.8), frame=frame @ Matrix.Rotation(lean, 4, "Y"))


def shade_tint(tint: tuple, factor: float) -> tuple:
    return tuple(channel * factor for channel in tint)


def fence_rails(b: Builder, start: tuple, end: tuple, ground: float, style: FenceStyle, index: int, generator: random.Random) -> None:
    """Sawn rails between two posts, nailed on the faces alternately so the ends overlap like hand work."""
    frame, length = segment_frame(start, end, ground)
    rail = srgb(style.rail_wood)
    face = style.post / 2.0 + RAIL_THICKNESS / 2.0

    for number, height in enumerate(style.rails):
        side = 1.0 if (index + number) % 2 == 0 else -1.0
        reach = generator.uniform(0.0, 0.08)
        tint = shade_tint(rail, generator.uniform(0.85, 1.05))

        b.box((-length / 2.0 - reach, side * face - RAIL_THICKNESS / 2.0, height - style.rail_width / 2.0), (length / 2.0 + reach, side * face + RAIL_THICKNESS / 2.0, height + style.rail_width / 2.0), "wood", tint, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.5))


def porteira(b: Builder, start: tuple, end: tuple, ground: float, style: FenceStyle) -> None:
    """Closed farm gate between two posts: stiles, sawn boards, a diagonal brace from the hinge-side bottom to the
    latch-side top, iron hinge straps, a chain and a latch block."""
    frame, length = segment_frame(start, end, ground)
    rail = srgb(style.rail_wood)
    stile = srgb(style.post_wood)
    iron = srgb("3A3438")
    half = length / 2.0 - style.post / 2.0 - 0.04
    top = style.rails[-1] + style.rail_width / 2.0
    face = style.post / 2.0 + RAIL_THICKNESS / 2.0

    for end_side in (-1, 1):
        b.box((end_side * half - 0.07, face - 0.03, 0.12), (end_side * half + 0.07, face + 0.05, top + 0.05), "wood", stile, frame=frame, uv=("band", *WOOD_DARK_BAND, 1.5))

    for height in style.rails:
        b.box((-half, face - 0.025, height - style.rail_width / 2.0), (half, face + 0.025, height + style.rail_width / 2.0), "wood", rail, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.5))

    b.beam((-half + 0.1, face + 0.04, style.rails[0]), (half - 0.1, face + 0.04, style.rails[-1]), 0.13, 0.04, "wood", shade_tint(rail, 0.8), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.5))

    for height in (style.rails[0], style.rails[-1]):
        b.box((-half - 0.1, face + 0.05, height - 0.03), (-half + 0.5, face + 0.07, height + 0.03), "metal", iron, frame=frame)

    b.box((half - 0.12, face + 0.05, style.rails[1] - 0.05), (half + 0.12, face + 0.12, style.rails[1] + 0.05), "metal", iron, frame=frame)
    b.beam((half + 0.04, face + 0.13, style.rails[1]), (half + 0.04, face + 0.13, style.rails[1] - 0.35), 0.03, 0.03, "metal", iron, frame=frame, uv=None)


def fence_collider(b: Builder, start: tuple, end: tuple, ground: float, height: float) -> None:
    frame, length = segment_frame(start, end, ground)

    b.collider((-length / 2.0, -0.1, 0.0), (length / 2.0, 0.1, height + 0.1), frame=frame, name="Fence")


def rectangle_loop(rectangle: tuple) -> list:
    min_x, max_x, min_z, max_z = rectangle

    return [(min_x, min_z), (max_x, min_z), (max_x, max_z), (min_x, max_z), (min_x, min_z)]


# ---------- dirt tracks ----------

def ground_strip(b: Builder, left, right, height: float, material: str, tint: str) -> None:
    """Flat ribbon of ground between two edges given as world (x, z) points."""
    strip = bmesh.new()
    left_vertices = [strip.verts.new(world(x, z, height)) for x, z in left]
    right_vertices = [strip.verts.new(world(x, z, height)) for x, z in right]

    for index in range(len(left_vertices) - 1):
        strip.faces.new((left_vertices[index], right_vertices[index], right_vertices[index + 1], left_vertices[index + 1]))

    b._link(strip, material, srgb(tint), None, Matrix.Identity(4))


def smooth_path(points: list, spacing: float = 1.0) -> tuple:
    """Round the corners of a polyline (corner cutting) and walk it at even steps: (centres, unit normals)."""
    path = numpy.array(points, dtype=float)

    for _ in range(3):
        cut = numpy.stack([path[:-1] * 0.75 + path[1:] * 0.25, path[:-1] * 0.25 + path[1:] * 0.75], axis=1).reshape(-1, 2)
        path = numpy.concatenate([path[:1], cut, path[-1:]])

    travelled = numpy.concatenate([[0.0], numpy.cumsum(numpy.linalg.norm(numpy.diff(path, axis=0), axis=1))])
    stations = numpy.linspace(0.0, travelled[-1], int(travelled[-1] / spacing) + 1)
    centers = numpy.stack([numpy.interp(stations, travelled, path[:, 0]), numpy.interp(stations, travelled, path[:, 1])], axis=1)
    tangent = numpy.gradient(centers, axis=0)
    normals = numpy.stack([-tangent[:, 1], tangent[:, 0]], axis=1)

    return centers, normals / numpy.linalg.norm(normals, axis=1, keepdims=True)


def dirt_track(b: Builder, points: list, ground: float, seed: int, half_width: float = 1.9, cart_ruts: bool = True) -> None:
    """Worn farm track: wandering centre line, ragged edges of uneven width and, for a cart track, two darker
    wheel ruts with a strip of grass surviving between them in stretches. Tufts of grass creep in at the edges."""
    generator = numpy.random.default_rng(seed)
    tuft_generator = random.Random(seed)
    centers, normals = smooth_path(points)
    along = numpy.arange(len(centers), dtype=float)

    def wobble(amplitude: float) -> numpy.ndarray:
        phases = generator.uniform(0.0, 2.0 * math.pi, 3)

        return amplitude * (0.5 * numpy.sin(along * 0.23 + phases[0]) + 0.3 * numpy.sin(along * 0.61 + phases[1]) + 0.2 * numpy.sin(along * 1.37 + phases[2]))

    def edge(distance: numpy.ndarray) -> numpy.ndarray:
        return centers + normals * distance[:, None]

    left = half_width * (1.0 + wobble(0.3)) + generator.normal(0.0, 0.05, len(along))
    right = half_width * (1.0 + wobble(0.3)) + generator.normal(0.0, 0.05, len(along))
    border = numpy.concatenate([edge(left + 0.1)[::3], edge(-right - 0.1)[::3]])

    ground_strip(b, edge(left), edge(-right), ground, "soil", SOIL_PATH)
    stamp_variants(b.plants, tuft_variants(MEADOW_TINTS, 0.42, 0.3), spot_matrices([tuple(spot) for spot in border], ground, tuft_generator, (0.6, 1.2)), tuft_generator)

    if not cart_ruts:
        return

    for side in (-1.0, 1.0):
        middle, half_rut = side * 0.66 + wobble(0.1), 0.17 + wobble(0.06)
        ground_strip(b, edge(middle + half_rut), edge(middle - half_rut), ground + 0.008, "soil", SOIL_RUT)

    is_grassy = wobble(1.0) > -0.12
    runs = numpy.flatnonzero(numpy.diff(numpy.concatenate([[0], is_grassy.astype(int), [0]]))).reshape(-1, 2)
    crown_middle, crown_half = wobble(0.08), 0.24 + wobble(0.1)

    for start, end in runs[(runs[:, 1] - runs[:, 0]) > 3]:
        taper = numpy.pad(numpy.sin(numpy.linspace(0.0, math.pi, end - start)) ** 0.5, (start, len(along) - end))
        crown_spots = [tuple(spot) for spot in edge(crown_middle)[start + 1:end - 1]]

        ground_strip(b, edge(crown_middle + crown_half * taper)[start:end], edge(crown_middle - crown_half * taper)[start:end], ground + 0.01, "lawn", "FFFFFF")
        stamp_variants(b.plants, tuft_variants(MEADOW_TINTS, 0.4, 0.26), spot_matrices(crown_spots, ground, tuft_generator, (0.6, 1.1)), tuft_generator)


# ---------- hay ----------

def lumpy_mound(b: Builder, frame: Matrix, radii: tuple, height: float, seed: int, material: str = "hay", tint: str = "FFFFFF", sides: int = 12) -> None:
    """Irregular heap (loose hay, a load on a cart): rings of uneven radius closing on a peak."""
    generator = numpy.random.default_rng(seed)
    shares, levels = numpy.array([1.0, 1.03, 0.9, 0.68, 0.4]), numpy.array([0.0, 0.2, 0.46, 0.7, 0.9])
    angles = 2.0 * math.pi * numpy.arange(sides) / sides
    reach = shares[:, None] * generator.uniform(0.86, 1.1, (len(shares), sides))
    points = numpy.stack([radii[0] * reach * numpy.cos(angles), radii[1] * reach * numpy.sin(angles), height * levels[:, None] * generator.uniform(0.9, 1.1, (len(shares), sides))], axis=-1)
    points[0, :, 2] = 0.0
    mound = bmesh.new()
    vertices = [mound.verts.new(point) for point in points.reshape(-1, 3)]
    peak = mound.verts.new((0.0, 0.0, height))

    for ring, step in itertools.product(range(len(shares) - 1), range(sides)):
        lower, lower_next = ring * sides + step, ring * sides + (step + 1) % sides
        mound.faces.new((vertices[lower], vertices[lower_next], vertices[lower_next + sides], vertices[lower + sides]))

    for step in range(sides):
        mound.faces.new((vertices[-sides + step], vertices[-sides + (step + 1) % sides], peak))

    for face in mound.faces:
        face.smooth = True

    b._link(mound, material, srgb(tint), None, frame)


def straw_tufts(b: Builder, frame: Matrix, radii: tuple, height: float, count: int, seed: int) -> None:
    """Wisps of straw hanging off a heap: tuft cards laid outward and down over its surface."""
    generator = random.Random(seed)
    angles = [generator.uniform(0.0, 2.0 * math.pi) for _ in range(count)]
    levels = [generator.uniform(0.05, 0.92) for _ in range(count)]
    points = [(radii[0] * (1.0 - level ** 1.7) * math.cos(angle), radii[1] * (1.0 - level ** 1.7) * math.sin(angle), height * level + 0.04) for angle, level in zip(angles, levels)]
    yaws = [math.degrees(angle) + 90.0 + generator.uniform(-35.0, 35.0) for angle in angles]
    tilts = [generator.uniform(60.0, 125.0) for _ in range(count)]
    scales = [generator.uniform(0.6, 1.15) for _ in range(count)]

    stamp_variants(b.plants, tuft_variants(STRAW_TINTS, 0.5, 0.42), transforms(points, yaws, tilts, scales), generator, frame)


def hay_pile(b: Builder, frame: Matrix, size: tuple, seed: int) -> None:
    """Loose heap of hay (width, depth, height) bristling with straw."""
    radii = (size[0] / 2.0, size[1] / 2.0)

    lumpy_mound(b, frame, radii, size[2], seed)
    straw_tufts(b, frame, radii, size[2], int(14 * size[0] * size[1]) + 6, seed)


def pitchfork(b: Builder, frame: Matrix) -> None:
    """Hay fork with the tines at the local origin and the handle up local Z."""
    iron = srgb("4A4448")

    b.cylinder((0.0, 0.0, 0.32), 0.018, 1.25, 6, "wood", srgb(WOOD["mel"]), frame=frame)
    b.cylinder((0.0, 0.0, 0.26), 0.024, 0.1, 6, "metal", iron, frame=frame)
    b.beam((-0.1, 0.0, 0.27), (0.1, 0.0, 0.27), 0.02, 0.02, "metal", iron, frame=frame, uv=None)

    for tine in (-0.1, 0.0, 0.1):
        b.beam((tine, 0.0, 0.27), (tine, 0.03, 0.0), 0.016, 0.016, "metal", iron, frame=frame, uv=None)


def haycock(b: Builder, frame: Matrix, radius: float, height: float, seed: int, fork: bool = False) -> None:
    """Heap of loose hay raked up to dry: lumpy, wider than tall, shaggy with straw; sometimes a fork left in it."""
    hay_pile(b, frame, (radius * 2.0, radius * 1.8, height), seed)
    straw_tufts(b, frame, (radius * 1.15, radius * 1.05), 0.12, int(radius * 16), seed + 1)
    b.collider((-radius * 0.75, -radius * 0.7, 0.0), (radius * 0.75, radius * 0.7, height * 0.75), frame=frame)

    if fork:
        pitchfork(b, frame @ Matrix.Translation((radius * 0.5, -radius * 0.35, height * 0.45)) @ Matrix.Rotation(math.radians(-22.0), 4, "Y"))


BALE_SIZE = (0.95, 0.46, 0.38)  # comprimento, largura, altura de um fardo retangular


def hay_bale(b: Builder, frame: Matrix, seed: int) -> None:
    """Rectangular bale: pressed hay tied with two strings, straw sticking out of the cut ends."""
    generator = random.Random(seed)
    half_length, half_width, height = BALE_SIZE[0] / 2.0, BALE_SIZE[1] / 2.0, BALE_SIZE[2]
    shade = generator.choice(("FFFFFF", "F4EBD0", "FFF6DC"))
    end_points = [(side * half_length, generator.uniform(-half_width, half_width) * 0.8, generator.uniform(0.08, height - 0.06)) for side in (-1.0, 1.0, -1.0, 1.0)]
    end_yaws = [-90.0 if point[0] > 0 else 90.0 for point in end_points]

    b.box((-half_length, -half_width, 0.0), (half_length, half_width, height), "hay", srgb(shade), frame=frame)

    for string in (-0.24, 0.24):
        b.box((string - 0.009, -half_width - 0.006, -0.002), (string + 0.009, half_width + 0.006, height + 0.006), "paint", srgb("8A6A3A"), frame=frame)

    stamp_variants(b.plants, tuft_variants(STRAW_TINTS, 0.3, 0.2), transforms(end_points, end_yaws, 80.0, 1.0), generator, frame)


def bale_stack(b: Builder, frame: Matrix, columns: int, rows: int, layers: int, seed: int) -> None:
    """Bales stacked like bricks, every layer one bale shorter and shifted half a bale; one loose bale beside it."""
    generator = random.Random(seed)
    length, width, height = BALE_SIZE
    slots = [(layer, row, column) for layer, row, column in itertools.product(range(layers), range(rows), range(columns)) if column < columns - layer]

    for index, (layer, row, column) in enumerate(slots):
        position = ((column - (columns - layer - 1) / 2.0) * (length + 0.02), (row - (rows - 1) / 2.0) * (width + 0.02), layer * height)
        hay_bale(b, frame @ Matrix.Translation(position) @ Matrix.Rotation(math.radians(generator.uniform(-3.0, 3.0)), 4, "Z"), seed + index)

    loose = frame @ Matrix.Translation((columns * length / 2.0 + 0.5, generator.uniform(-0.2, 0.2), 0.0)) @ Matrix.Rotation(math.radians(generator.uniform(50.0, 80.0)), 4, "Z")
    hay_bale(b, loose, seed + 99)
    straw_tufts(b, frame, (columns * length / 2.0 + 0.3, rows * width / 2.0 + 0.3), 0.1, 14, seed)
    b.collider((-columns * length / 2.0, -rows * width / 2.0, 0.0), (columns * length / 2.0, rows * width / 2.0, layers * height), frame=frame)


# ---------- produce: sacks, baskets and what goes in them ----------

PRODUCE_SHAPES = {
    "apple": lathe_shape([(0.012, 0.0), (0.05, 0.02), (0.056, 0.055), (0.04, 0.095), (0.01, 0.1)], 7),
    "potato": lathe_shape([(0.01, 0.0), (0.045, 0.02), (0.05, 0.05), (0.03, 0.085), (0.008, 0.09)], 6),
    "carrot": lathe_shape([(0.004, 0.0), (0.016, 0.07), (0.026, 0.2), (0.012, 0.215)], 6),
    "coffee": lathe_shape([(0.006, 0.0), (0.022, 0.012), (0.026, 0.03), (0.016, 0.05), (0.005, 0.055)], 6),
}
PRODUCE_TINTS = {"apple": ("C9302C", "D8452F", "E0B23A"), "potato": ("C9A26A", "B88E58", "D2B07A"), "coffee": ("B8402F", "C9502F", "8F2E24")}
BASKET_LINING = {"apple": "A82A26", "potato": "A88458", "carrot": "C96A22", "cabbage": "7FB094", "coffee": "8F2E24"}


def fill_with_cabbages(b: Builder, frame: Matrix, radius: float, top: float, generator: random.Random) -> None:
    heads = [(math.cos(angle) * radius * 0.42, math.sin(angle) * radius * 0.42, top - 0.06) for angle in (0.3, 2.4, 4.5)]

    stamp_variants(b.plants, variants_of(cabbage_plant, generator, 2), transforms(heads, [generator.uniform(0.0, 360.0) for _ in heads], 0.0, 0.72), generator, frame)


def fill_with_carrots(b: Builder, frame: Matrix, radius: float, top: float, generator: random.Random) -> None:
    """Carrots in a fan, points to the middle, their leaves hanging over the rim."""
    angles = [index * 40.0 + generator.uniform(-12.0, 12.0) for index in range(9)]
    tips = [(math.cos(math.radians(angle)) * radius * 0.15, math.sin(math.radians(angle)) * radius * 0.15, top - 0.03 + 0.012 * (index % 3)) for index, angle in enumerate(angles)]
    crowns = [(math.cos(math.radians(angle)) * radius * 0.85, math.sin(math.radians(angle)) * radius * 0.85, top + 0.03) for angle in angles]
    frond = ribbon(arc_path(0.3, 35.0, 60.0, 2), 0.16, "carrot")

    b.plants.stamp(PRODUCE_SHAPES["carrot"], transforms(tips, [angle - 90.0 for angle in angles], -78.0, 1.0), CARROT_ROOT, "paint", frame)
    b.plants.stamp(frond, transforms(crowns, [angle - 90.0 + generator.uniform(-25.0, 25.0) for angle in angles], 0.0, 1.0), "FFFFFF", "crops", frame)


def fill_with_round(produce: str):
    """Apples or potatoes heaped in two rings and a crown."""
    def fill(b: Builder, frame: Matrix, radius: float, top: float, generator: random.Random) -> None:
        rings = [(radius * 0.62, 7, top - 0.05), (radius * 0.3, 4, top + 0.01), (0.0, 1, top + 0.06)]
        points = [(math.cos(2.0 * math.pi * index / count + reach) * reach, math.sin(2.0 * math.pi * index / count + reach) * reach, level) for reach, count, level in rings for index in range(count)]
        matrices = transforms(points, [generator.uniform(0.0, 360.0) for _ in points], [generator.uniform(-40.0, 40.0) for _ in points], [generator.uniform(0.85, 1.1) for _ in points])
        shade = numpy.array([generator.randrange(3) for _ in points])

        for index, tint in enumerate(PRODUCE_TINTS[produce]):
            b.plants.stamp(PRODUCE_SHAPES[produce], matrices[shade == index], tint, "paint", frame)

    return fill


BASKET_FILLS = {"cabbage": fill_with_cabbages, "carrot": fill_with_carrots, "apple": fill_with_round("apple"), "potato": fill_with_round("potato"), "coffee": fill_with_round("coffee")}


def basket(b: Builder, frame: Matrix, produce: str, seed: int, radius: float = 0.27, height: float = 0.3) -> None:
    """Round wicker basket with thick walls, woven bands, two handles, filled to the brim."""
    wicker, band = "C49A5E", srgb("96703E")
    grip = [(radius, -0.07, height), (radius + 0.03, -0.04, height + 0.07), (radius + 0.03, 0.04, height + 0.07), (radius, 0.07, height)]

    lathe(b, [(radius * 0.72, 0.0), (radius, height), (radius * 0.9, height), (radius * 0.64, 0.04)], 12, "paint", wicker, frame, closed=True)
    b.cylinder((0.0, 0.0, 0.03), radius * 0.68, 0.02, 12, "paint", srgb(wicker), frame=frame)
    b.cylinder((0.0, 0.0, height * 0.6), radius * 0.86, 0.02, 12, "paint", srgb(BASKET_LINING[produce]), frame=frame)

    for level in (0.25, 0.55, 0.97):
        b.cylinder((0.0, 0.0, height * level - 0.012), radius * (0.72 + 0.28 * level) + 0.008, 0.024, 12, "paint", band, frame=frame)

    for side, (start, end) in itertools.product((-1.0, 1.0), zip(grip, grip[1:])):
        b.beam((side * start[0], start[1], start[2]), (side * end[0], end[1], end[2]), 0.022, 0.022, "paint", band, frame=frame, uv=None)

    BASKET_FILLS[produce](b, frame, radius, height, random.Random(seed))


def open_sack(b: Builder, frame: Matrix, radius: float, height: float, tint: str, grain: str) -> None:
    """Sack standing open with its mouth rolled down, heaped with grain."""
    lathe(b, [(0.75 * radius, 0.0), (radius, 0.2 * height), (radius, 0.6 * height), (0.9 * radius, 0.86 * height), (1.02 * radius, 0.93 * height), (0.94 * radius, height), (0.82 * radius, 0.94 * height)], 9, "paint", tint, frame)
    lathe(b, [(0.84 * radius, 0.9 * height), (0.5 * radius, 0.99 * height), (0.02, 1.04 * height)], 9, "paint", grain, frame)


def lying_sack(b: Builder, frame: Matrix, position: tuple, yaw: float, radius: float, length: float, tint: str) -> None:
    """Full sack laid on its side (stacked on a cart or against a wall)."""
    lying = Matrix.Translation((position[0], position[1], position[2] + radius * 0.82)) @ Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Diagonal((1.0, 1.0, 0.82, 1.0)) @ Matrix.Rotation(math.radians(90.0), 4, "X")

    sack(b, frame @ lying, 0.0, 0.0, -length / 2.0, radius, length, tint)


def produce_stand(b: Builder, frame: Matrix, seed: int) -> None:
    """The day's harvest set out in the yard: baskets of cabbages, carrots, apples and potatoes, an open sack of
    grain, full sacks leaning on each other."""
    baskets = (("cabbage", (-0.85, 0.1)), ("carrot", (-0.2, -0.25)), ("apple", (0.45, 0.15)), ("potato", (0.15, 0.75)))

    for index, (produce, (x, y)) in enumerate(baskets):
        basket(b, frame @ Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(index * 1.1, 4, "Z"), produce, seed + index)

    open_sack(b, frame @ Matrix.Translation((1.15, 0.2, 0.0)), 0.25, 0.5, "DDC9A0", "E3B95A")
    sack(b, frame, 1.2, 0.85, 0.0, 0.26, 0.5, "E8D7B0")
    lying_sack(b, frame, (0.75, 1.4, 0.0), 20.0, 0.22, 0.62, "DDAE62")
    b.collider((-1.2, -0.6, 0.0), (1.5, 1.6, 0.5), frame=frame)


# ---------- carts ----------

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
    """Open spoked wheel turning around local X: wooden felloe inside an iron tyre, hub and spokes you can see
    through."""
    around_x = frame @ Matrix.Translation(center) @ Matrix.Rotation(math.radians(90.0), 4, "Y")
    half = width / 2.0

    lathe(b, [(radius * 0.84, -half), (radius * 0.975, -half), (radius * 0.975, half), (radius * 0.84, half)], 18, "wood", WOOD["media"], around_x, closed=True, uv=("band", *WOOD_LIGHT_BAND, 1.0))
    lathe(b, [(radius * 0.975, -half - 0.004), (radius, -half - 0.004), (radius, half + 0.004), (radius * 0.975, half + 0.004)], 18, "metal", "4A4448", around_x, closed=True)
    b.cylinder((center[0] - width, center[1], center[2]), radius * 0.15 + 0.02, width * 2.0, 8, "wood", srgb(WOOD["escura"]), frame=frame, axis="X")
    b.cylinder((center[0] - width - 0.02, center[1], center[2]), 0.03, width * 2.0 + 0.04, 6, "metal", srgb("4A4448"), frame=frame, axis="X")

    for spoke in range(spokes):
        angle = 2.0 * math.pi * spoke / spokes
        tip = (center[0], center[1] + math.cos(angle) * radius * 0.86, center[2] + math.sin(angle) * radius * 0.86)
        b.beam(center, tip, 0.045, 0.04, "wood", srgb(WOOD["mel"]), frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))


def slab(b: Builder, frame: Matrix, lower: tuple, upper: tuple, thickness: tuple, tint: tuple) -> None:
    """Board between a lower and an upper edge (each a pair of points), given a thickness vector: the leaning
    sides of a wheelbarrow tray or a footboard."""
    edge_points = [*lower, *upper]
    points = edge_points + [tuple(coordinate + offset for coordinate, offset in zip(point, thickness)) for point in edge_points]

    b.hull(points, "wood", tint, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))


CART_HALF_WIDTH = 0.78
CART_HALF_LENGTH = 1.2
CART_FLOOR = 0.8
CART_SIDE_HEIGHT = 0.5
CART_WHEEL_RADIUS = 0.64
SEAT_HEIGHT = 1.46
SEAT_Y = -1.3  # centro do assento, além da parede da frente (as canelas do condutor descem livres): Blender -Y é a frente (+Z no Godot)
FOOTBOARD_REACH = 0.62  # da parede da frente até a ponta do estribo, onde os pés do condutor apoiam
HORSE_OFFSET = 3.9  # Carriage.horse_offset: do eixo às patas do cavalo
HARNESS_SIDECAR = FARM_DIR / "animals" / "horse_harness.json"
HARNESS_RING = (0.275, 1.149, 0.241)  # argola direita do arreio no cavalo (Godot: x lado, y altura, z à frente)
SHAFT_CLEARANCE = 0.07  # o varal passa por fora da argola, encostado no flanco
HORSE_RUMP_BEHIND = 0.95  # da origem do cavalo até a garupa: ali os varais já correm na altura dos flancos


def harness_ring() -> tuple:
    """Right harness ring of the horse (x out, height, ahead of the hooves), from the converted harness sidecar
    (convert_farm_animals.py) when it exists: the shaft tips always meet the rings the horse really wears."""
    if not HARNESS_SIDECAR.exists():
        return HARNESS_RING

    rings = json.loads(HARNESS_SIDECAR.read_text(encoding="utf-8")).get("harness_rings", [HARNESS_RING])

    return tuple(max(rings, key=lambda ring: ring[0]))


def cart_body(b: Builder, frame: Matrix) -> None:
    """Bed of five floor planks on two sills, slatted sides on stakes, headboard and tailboard."""
    wood, dark = srgb(WOOD["mel"]), srgb(WOOD["media"])
    plank = 2.0 * CART_HALF_WIDTH / 5.0
    top = CART_FLOOR + 0.05

    for index in range(5):
        x = -CART_HALF_WIDTH + index * plank
        b.box((x + 0.006, -CART_HALF_LENGTH, CART_FLOOR), (x + plank - 0.006, CART_HALF_LENGTH, top), "wood", wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.5))

    for side in (-1, 1):
        b.box((side * 0.5 - 0.05, -CART_HALF_LENGTH, CART_FLOOR - 0.1), (side * 0.5 + 0.05, CART_HALF_LENGTH, CART_FLOOR), "wood", dark, frame=frame, uv=("band", *WOOD_DARK_BAND, 1.5))
        b.box((side * 0.5 - 0.05, 0.02, CART_WHEEL_RADIUS - 0.02), (side * 0.5 + 0.05, 0.18, CART_FLOOR - 0.1), "wood", dark, frame=frame)
        wheel(b, frame, (side * (CART_HALF_WIDTH + 0.16), 0.1, CART_WHEEL_RADIUS), CART_WHEEL_RADIUS, 0.08, spokes=10)

    for side, stake_y in itertools.product((-1, 1), (-1.14, -0.38, 0.38, 1.14)):
        b.box((side * CART_HALF_WIDTH - 0.035, stake_y - 0.035, CART_FLOOR - 0.06), (side * CART_HALF_WIDTH + 0.035, stake_y + 0.035, top + CART_SIDE_HEIGHT + 0.06), "wood", dark, frame=frame, uv=("band", *WOOD_DARK_BAND, 1.5))

    for side, board in itertools.product((-1, 1), range(3)):
        inner = side * (CART_HALF_WIDTH - 0.06)
        b.box((min(inner, inner + side * 0.03), -CART_HALF_LENGTH, top + 0.02 + board * 0.165), (max(inner, inner + side * 0.03), CART_HALF_LENGTH, top + 0.16 + board * 0.165), "wood", wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.5))

    for end, board in itertools.product((-1, 1), range(3)):
        y = end * (CART_HALF_LENGTH - 0.03)
        b.box((-CART_HALF_WIDTH + 0.06, min(y, y + end * 0.03), top + 0.02 + board * 0.165), (CART_HALF_WIDTH - 0.06, max(y, y + end * 0.03), top + 0.16 + board * 0.165), "wood", wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.5))

    b.cylinder((-CART_HALF_WIDTH - 0.2, 0.1, CART_WHEEL_RADIUS), 0.04, 2.0 * CART_HALF_WIDTH + 0.4, 6, "metal", srgb("4A4448"), frame=frame, axis="X")


def cart_bench(b: Builder, frame: Matrix) -> None:
    """Driver's bench across the front of the bed: seat plank on two brackets, backrest and a sloping footboard."""
    wood, dark = srgb(WOOD["mel"]), srgb(WOOD["media"])
    side_top = CART_FLOOR + 0.05 + CART_SIDE_HEIGHT
    foot_low = ((-CART_HALF_WIDTH, -CART_HALF_LENGTH, CART_FLOOR + 0.02), (CART_HALF_WIDTH, -CART_HALF_LENGTH, CART_FLOOR + 0.02))
    foot_high = ((-CART_HALF_WIDTH, -CART_HALF_LENGTH - FOOTBOARD_REACH, CART_FLOOR + 0.26), (CART_HALF_WIDTH, -CART_HALF_LENGTH - FOOTBOARD_REACH, CART_FLOOR + 0.26))

    b.box((-CART_HALF_WIDTH - 0.04, SEAT_Y - 0.2, SEAT_HEIGHT - 0.05), (CART_HALF_WIDTH + 0.04, SEAT_Y + 0.2, SEAT_HEIGHT), "wood", wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.5))
    b.box((-CART_HALF_WIDTH, SEAT_Y + 0.2, SEAT_HEIGHT + 0.12), (CART_HALF_WIDTH, SEAT_Y + 0.24, SEAT_HEIGHT + 0.36), "wood", wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.5))
    slab(b, frame, foot_low, foot_high, (0.0, 0.0, 0.04), wood)

    for side in (-1, 1):
        b.box((side * CART_HALF_WIDTH - 0.04, -CART_HALF_LENGTH, side_top), (side * CART_HALF_WIDTH + 0.04, SEAT_Y + 0.17, SEAT_HEIGHT - 0.05), "wood", dark, frame=frame)
        b.box((side * CART_HALF_WIDTH - 0.03, SEAT_Y + 0.2, side_top), (side * CART_HALF_WIDTH + 0.03, SEAT_Y + 0.25, SEAT_HEIGHT + 0.36), "wood", dark, frame=frame)
        b.beam((side * 0.5, -CART_HALF_LENGTH - FOOTBOARD_REACH + 0.02, CART_FLOOR + 0.26), (side * 0.5, -CART_HALF_LENGTH, CART_FLOOR - 0.06), 0.05, 0.05, "wood", dark, frame=frame)


def cart_shafts(b: Builder, frame: Matrix, hitched: bool) -> None:
    """The pair of shafts. Hitched: they rise from the bed to the harness rings on the horse's flanks, one each
    side of the horse standing HORSE_OFFSET ahead, with a cross bar behind its tail. Parked: level, on a trestle."""
    dark, iron = srgb(WOOD["media"]), srgb("4A4448")
    ring_x, ring_height, ring_ahead = harness_ring()
    tip_x = ring_x + SHAFT_CLEARANCE
    rump_y = -(HORSE_OFFSET - HORSE_RUMP_BEHIND)
    lines = {
        True: [(0.56, -CART_HALF_LENGTH + 0.3, CART_FLOOR - 0.05), (0.54, -2.1, CART_FLOOR + 0.1), (tip_x + 0.1, rump_y, ring_height - 0.06), (tip_x, -(HORSE_OFFSET + ring_ahead) - 0.12, ring_height)],
        False: [(0.56, -CART_HALF_LENGTH + 0.3, CART_FLOOR - 0.05), (0.52, -2.1, CART_FLOOR - 0.08), (0.48, -3.5, CART_FLOOR - 0.1)],
    }[hitched]
    tip = lines[-1]
    trestle_y = -3.3

    for side, (start, end) in itertools.product((-1, 1), zip(lines, lines[1:])):
        b.beam((side * start[0], start[1], start[2]), (side * end[0], end[1], end[2]), 0.075, 0.075, "wood", dark, frame=frame)

    for side in (-1, 1):
        b.cylinder((side * tip[0], tip[1] - 0.06, tip[2]), 0.05, 0.12, 6, "metal", iron, frame=frame, axis="Y")

    b.beam((-0.58, -2.1, lines[1][2]), (0.58, -2.1, lines[1][2]), 0.07, 0.07, "wood", dark, frame=frame)

    if hitched:
        return

    b.beam((-0.62, trestle_y, CART_FLOOR - 0.18), (0.62, trestle_y, CART_FLOOR - 0.18), 0.08, 0.08, "wood", dark, frame=frame)

    for side, lean in itertools.product((-1, 1), (-0.22, 0.22)):
        b.beam((side * 0.5, trestle_y, CART_FLOOR - 0.2), (side * 0.6, trestle_y + lean, 0.0), 0.06, 0.06, "wood", dark, frame=frame)


def load_hay(b: Builder, frame: Matrix, seed: int) -> None:
    """Hay piled above the sides behind the bench, spilling over the boards, the fork stuck in the top."""
    bed = frame @ Matrix.Translation((0.0, 0.3, CART_FLOOR + 0.05))

    hay_pile(b, bed, (1.5, 1.75, 1.05), seed)
    straw_tufts(b, bed @ Matrix.Translation((0.0, 0.0, 0.42)), (0.86, 0.95), 0.3, 26, seed + 5)
    pitchfork(b, bed @ Matrix.Translation((0.2, 0.35, 0.7)) @ Matrix.Rotation(math.radians(14.0), 4, "X"))


def load_sacks(b: Builder, frame: Matrix, seed: int) -> None:
    """Grain sacks standing and lying two deep, one open, and a basket of apples by the tailboard."""
    bed = frame @ Matrix.Translation((0.0, 0.0, CART_FLOOR + 0.05))
    tints = ("E8D7B0", "DDAE62", "C98F4F", "E8D7B0")

    for (x, y), tint in zip(((-0.42, -0.45), (0.08, -0.5), (0.45, -0.1), (-0.4, 0.05)), tints):
        sack(b, bed, x, y, 0.0, 0.25, 0.5, tint)

    lying_sack(b, bed, (-0.3, 0.6, 0.0), 8.0, 0.21, 0.6, tints[2])
    lying_sack(b, bed, (0.25, 0.42, 0.0), 95.0, 0.21, 0.6, tints[0])
    lying_sack(b, bed, (-0.1, -0.2, 0.44), 60.0, 0.2, 0.56, tints[1])
    open_sack(b, bed @ Matrix.Translation((0.45, 0.9, 0.0)), 0.22, 0.44, "DDC9A0", "E3B95A")
    basket(b, bed @ Matrix.Translation((-0.42, 0.95, 0.0)), "apple", seed, radius=0.22, height=0.26)


def load_produce(b: Builder, frame: Matrix, seed: int) -> None:
    """Harvest going to market: baskets of every vegetable."""
    bed = frame @ Matrix.Translation((0.0, 0.0, CART_FLOOR + 0.05))
    baskets = (("cabbage", -0.4, -0.3), ("carrot", 0.38, -0.4), ("potato", -0.4, 0.3), ("cabbage", 0.38, 0.2), ("apple", -0.38, 0.88), ("carrot", 0.35, 0.82))

    for index, (produce, x, y) in enumerate(baskets):
        basket(b, bed @ Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(index * 0.9, 4, "Z"), produce, seed + index, radius=0.25)


CART_LOADS = {"hay": load_hay, "sacks": load_sacks, "produce": load_produce}


def farm_cart(b: Builder, frame: Matrix, load: str = "hay", seed: int = 1, hitched: bool = False) -> None:
    """Two-wheeled farm cart: slatted bed, spoked wheels, driver's bench, shafts and a load."""
    cart_body(b, frame)
    cart_bench(b, frame)
    cart_shafts(b, frame, hitched)
    CART_LOADS[load](b, frame, seed)
    b.collider((-0.98, -CART_HALF_LENGTH - 0.45, 0.0), (0.98, CART_HALF_LENGTH + 0.05, 1.4), frame=frame)


def wheelbarrow(b: Builder, frame: Matrix, seed: int = 7) -> None:
    """Wooden wheelbarrow: an open tray of boards flaring upward (floor and four leaning sides, all with
    thickness), spoked wheel between the shafts, two legs, handles; a few cabbages riding in it."""
    wood, dark = srgb(WOOD["mel"]), srgb(WOOD["media"])
    generator = random.Random(seed)
    floor, rim = 0.4, 0.7
    low_x, low_front, low_back = 0.24, -0.36, 0.36
    high_x, high_front, high_back = 0.38, -0.56, 0.5
    heads = [(-0.1, -0.12, floor), (0.12, 0.14, floor), (0.0, -0.02, floor + 0.17)]

    b.box((-low_x, low_front, floor - 0.035), (low_x, low_back, floor), "wood", wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))
    slab(b, frame, ((-low_x, low_front, floor - 0.03), (low_x, low_front, floor - 0.03)), ((-high_x, high_front, rim), (high_x, high_front, rim)), (0.0, -0.03, 0.0), wood)
    slab(b, frame, ((-low_x, low_back, floor - 0.03), (low_x, low_back, floor - 0.03)), ((-high_x, high_back, rim), (high_x, high_back, rim)), (0.0, 0.03, 0.0), wood)

    for side in (-1, 1):
        slab(b, frame, ((side * low_x, low_front, floor - 0.03), (side * low_x, low_back, floor - 0.03)), ((side * high_x, high_front, rim), (side * high_x, high_back, rim)), (side * 0.03, 0.0, 0.0), wood)
        b.beam((side * 0.12, -0.98, 0.25), (side * 0.3, 0.2, floor - 0.07), 0.055, 0.05, "wood", dark, frame=frame)
        b.beam((side * 0.3, 0.2, floor - 0.07), (side * 0.36, 1.25, 0.62), 0.055, 0.05, "wood", dark, frame=frame)
        b.cylinder((side * 0.36, 1.2, 0.62), 0.032, 0.16, 6, "wood", srgb(WOOD["escura"]), frame=frame, axis="Y")
        b.beam((side * 0.31, 0.32, floor - 0.06), (side * 0.34, 0.42, 0.0), 0.05, 0.05, "wood", dark, frame=frame)
        b.beam((side * 0.33, 0.4, 0.14), (side * 0.3, 0.05, floor - 0.08), 0.035, 0.035, "wood", dark, frame=frame)

    b.beam((-0.33, 0.4, 0.12), (0.33, 0.4, 0.12), 0.04, 0.04, "wood", dark, frame=frame)
    wheel(b, frame, (0.0, -0.9, 0.25), 0.25, 0.05, spokes=6)
    b.cylinder((-0.15, -0.9, 0.25), 0.02, 0.3, 6, "metal", srgb("4A4448"), frame=frame, axis="X")
    stamp_variants(b.plants, variants_of(cabbage_plant, generator, 2), transforms(heads, [generator.uniform(0.0, 360.0) for _ in heads], 0.0, 0.8), generator, frame)
    b.collider((-0.45, -1.1, 0.0), (0.45, 1.3, 0.7), frame=frame)


# ---------- shelters and feeders ----------

def farm_rancho(b: Builder, frame: Matrix, width: float, depth: float, eave: float) -> None:
    """Rancho on round posts (farm_rural.py) with straw bedding on its floor."""
    half = width / 2.0

    rancho(b, frame, width, depth, eave)
    lumpy_mound(b, frame @ Matrix.Translation((0.0, depth * 0.55, 0.0)), (half * 0.86, depth * 0.4), 0.09, int(width * 100))
    straw_tufts(b, frame @ Matrix.Translation((0.0, depth * 0.5, 0.0)), (half * 0.95, depth * 0.48), 0.08, int(width * depth), int(width * 10))


def hay_rack(b: Builder, frame: Matrix, length: float) -> None:
    """Slatted V-shaped hay manger on legs, full of hay."""
    wood = srgb(WOOD["media"])
    slats = max(4, int(length / 0.25))

    for side in (-1, 1):
        b.beam((side * length / 2.0, 0.0, 0.0), (side * length / 2.0, 0.0, 1.0), 0.1, 0.1, "wood", wood, frame=frame)
        b.beam((-length / 2.0, side * 0.45, 1.3), (length / 2.0, side * 0.45, 1.3), 0.07, 0.07, "wood", wood, frame=frame)

    b.beam((-length / 2.0, 0.0, 0.6), (length / 2.0, 0.0, 0.6), 0.08, 0.08, "wood", wood, frame=frame)

    for slat, side in itertools.product(range(slats), (-1, 1)):
        x = -length / 2.0 + length * (slat + 0.5) / slats
        b.beam((x, 0.0, 0.62), (x, side * 0.45, 1.3), 0.04, 0.04, "wood", srgb(WOOD["mel"]), frame=frame)

    hay_pile(b, frame @ Matrix.Translation((0.0, 0.0, 0.95)), (length * 0.9, 0.8, 0.5), 41)
    b.collider((-length / 2.0, -0.5, 0.0), (length / 2.0, 0.5, 1.3), frame=frame)


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
    """Soil of a plot with a low ridge under every row (the walkable collider is the flat bed); no ridges when
    ridge_spacing is None."""
    _crop, min_x, max_x, min_z, max_z = plot

    ground_patch(b, (min_x, max_x, min_z, max_z), ground + FIELD_RAISE, "soil", tint, collider="Field", thickness=FIELD_RAISE + 0.02)

    for row_z in crop_rows(plot, ridge_spacing) if ridge_spacing else []:
        b.side_prism([(row_z - 0.22, ground + FIELD_RAISE), (row_z + 0.22, ground + FIELD_RAISE), (row_z, ground + FIELD_RAISE + 0.1)], min_x + 0.2, max_x - 0.2, "soil", srgb(SOIL_DARK), frame=row_frame())


def row_frame() -> Matrix:
    """side_prism draws (d, z) profiles extruded along u = Blender X; d is Blender Y. World z = -Y, so a profile
    written in world z is mirrored back by this frame."""
    return Matrix.Diagonal((1.0, -1.0, 1.0, 1.0))


CROPS = {  # cultura -> (planta, entre fileiras, entre plantas, desvio, tamanho, inclinação em graus)
    "coffee": (coffee_plant, 2.4, 1.7, 0.12, (0.9, 1.15), 1.5),
    "cane": (cane_plant, 1.5, 1.0, 0.1, (0.85, 1.15), 3.0),
    "cassava": (cassava_plant, 1.2, 1.0, 0.08, (0.9, 1.15), 2.0),
    "corn": (corn_plant, 0.9, 0.6, 0.07, (0.88, 1.1), 4.0),
    "cabbage": (cabbage_plant, 0.8, 0.8, 0.06, (0.85, 1.15), 0.0),
    "carrot": (carrot_plant, 0.6, 0.4, 0.05, (0.8, 1.15), 0.0),
}
RIDGE_SPACING = {"coffee": 2.4, "cane": 1.5, "cassava": 1.2, "corn": 0.9, "cabbage": 0.8, "carrot": 0.6}
BED_TINT = {"coffee": SOIL_DARK, "cane": SOIL, "cassava": SOIL, "corn": SOIL, "cabbage": SOIL, "carrot": SOIL}


def plant_crop(b: Builder, crop: str, plot: tuple, ground: float, seed: int) -> None:
    """Rows of one crop: a handful of plant variants stamped along the ridges, each turned and sized at random."""
    plant, across, along, jitter, sizes, lean = CROPS[crop]
    generator = random.Random(seed)
    spots = plant_spots(plot, across, along, seed, jitter)

    stamp_variants(b.plants, variants_of(plant, generator, 5), spot_matrices(spots, ground + FIELD_RAISE + 0.08, generator, sizes, lean), generator)


def grass_tufts(b: Builder, plot: tuple, ground: float, count: int, generator: random.Random) -> None:
    _crop, min_x, max_x, min_z, max_z = plot
    spots = [(generator.uniform(min_x + 0.4, max_x - 0.4), generator.uniform(min_z + 0.4, max_z - 0.4)) for _ in range(count)]

    stamp_variants(b.plants, tuft_variants(MEADOW_TINTS, 0.55, 0.4), spot_matrices(spots, ground, generator, (0.6, 1.3)), generator)


def meadow_field(b: Builder, plot: tuple, ground: float, seed: int) -> None:
    """Mown meadow: grass with tufts, heaps of hay drying and the bales already tied, stacked by the fence."""
    generator = random.Random(seed)
    _crop, min_x, max_x, min_z, max_z = plot

    ground_patch(b, (min_x, max_x, min_z, max_z), ground + 0.03, "lawn", "FFFFFF", collider="Bed", thickness=0.05)
    grass_tufts(b, plot, ground + 0.03, 520, generator)

    for index, (x, z) in enumerate(((113.0, 29.0), (121.5, 38.0), (131.0, 30.5), (139.5, 38.5))):
        haycock(b, frame_at_world(x, z, ground + 0.03, index * 47.0), generator.uniform(1.2, 1.5), generator.uniform(1.0, 1.3), seed + index, fork=index == 1)

    bale_stack(b, frame_at_world(144.5, 28.0, ground + 0.03, 90.0), 3, 2, 2, seed + 10)


def hay_field(b: Builder, plot: tuple, ground: float, seed: int) -> None:
    """Hay just cut, raked into long windrows across the field to dry."""
    generator = random.Random(seed)
    _crop, min_x, max_x, min_z, max_z = plot
    heaps = itertools.product(numpy.arange(min_z + 2.2, max_z - 1.5, 3.1), numpy.arange(min_x + 2.6, max_x - 2.0, 3.3))

    ground_patch(b, (min_x, max_x, min_z, max_z), ground + 0.03, "lawn", "FFFFFF", collider="Bed", thickness=0.05)
    grass_tufts(b, plot, ground + 0.03, 160, generator)

    for index, (z, x) in enumerate(heaps):
        hay_pile(b, frame_at_world(x + generator.uniform(-0.3, 0.3), z + generator.uniform(-0.25, 0.25), ground + 0.03, generator.uniform(-9.0, 9.0)), (3.3, generator.uniform(0.8, 1.1), generator.uniform(0.28, 0.4)), seed + index)


def build_plot(b: Builder, name: str, plot: tuple) -> None:
    """One plot; its plants are flushed into meshes of their own (Crops<n>), so the scene can stop drawing a plot
    from afar (visibility range) without the whole farm's batch going with it."""
    crop = plot[0]
    seed = SEED + len(name) * 7
    pastures = {"meadow": meadow_field, "hayfield": hay_field}

    if crop in pastures:
        pastures[crop](b, plot, OUTSIDE_GROUND, seed)
        b.plants.flush(CROPS_PREFIX)
        return

    plot_bed(b, plot, OUTSIDE_GROUND, RIDGE_SPACING[crop], BED_TINT[crop])
    plant_crop(b, crop, plot, OUTSIDE_GROUND, seed)
    b.plants.flush(CROPS_PREFIX)


# ---------- buildings ----------

def build_farmhouse() -> dict:
    """The sede (casa-grande): see farm_sede.py."""
    b = farm_builder("farmhouse")
    sidecar = casa_grande(b, FARMHOUSE["width"] / 2.0, FARMHOUSE["depth"])

    return finish_model(b, "farmhouse", sidecar)


def build_barn() -> dict:
    """The tulha (file name kept: barn.gltf): see farm_rural.py. Sacks and barrels by the doors."""
    b = farm_builder("barn")
    width, depth = BARN["width"], BARN["depth"]
    sidecar = tulha(b, width / 2.0, depth)

    return finish_model(b, "barn", sidecar)


# ---------- the yard (block 5) ----------

YARD_LANE = [(75.0, 0.3), (80.0, -0.5), (86.0, 0.6), (92.0, -0.4), (97.0, 0.4), (102.0, 0.0)]  # da rua ao portão do muro
YARD_VERGE = 5.0  # a terra batida vai da pista até aqui; ao norte é gramado
YARD_GRASS_PATCHES = (  # (x, z, raio x, raio z): grama que resiste nas beiradas da terra batida do sul
    (80.5, 43.4, 3.0, 1.2),
    (99.6, 8.0, 1.6, 2.4),
)
TERREIRO = (76.5, 94.1, -29.4, -5.0)  # terreiro de tijolo em frente da casa-grande, até o limiar da tulha
TERREIRO_TOP = YARD_TOP + 0.05
TERREIRO_BORDER = 0.5
TERREIRO_PATH = (83.9, 87.1)  # lajedo da escada da casa até a pista
KERB_TINT = "F4F0E6"
BRICK_TINT = "FFF8F0"  # quase branco: a cor já vem da textura desbotada (faded_brick_texture)
COFFEE_TINTS = {"cereja": "B8402F", "passa": "7A3A28", "seco": "4E3A2A", "verde": "9A8A3E"}
COFFEE_BEDS = {  # leito -> (min x, max x, estado de cada retângulo, do norte para o sul)
    "west": (77.5, 83.1, ("seco", "passa", "cereja", "cereja", "passa", "seco")),
    "east": (88.2, 91.4, ("cereja", None, "passa", "seco", "cereja", None)),
}
COFFEE_BED_DEPTH = 2.6
COFFEE_BED_START = -28.2
COFFEE_BED_PITCH = 3.8
BURLAP_TINTS = ("C8A878", "B8955F", "D4B88A")


def build_farm_yard() -> dict:
    """Ground, fences and props of the farm block, in world coordinates."""
    b = farm_builder("farm_yard")
    min_x, max_x, min_z, max_z = FARM_YARD
    cows = FARM_PENS["cows"]

    ground_patch(b, (cows[0] - 1.0, max_x, cows[2] - 1.0, cows[3] + 1.0), YARD_TOP, "lawn", "FFFFFF", collider="Bed")
    ground_patch(b, (min_x, max_x, FARM_LANE_HALF_WIDTH, cows[2] - 1.0), YARD_TOP, "soil", SOIL, collider="Yard")
    ground_patch(b, (min_x, cows[0] - 1.0, cows[2] - 1.0, max_z), YARD_TOP, "lawn", "FFFFFF", collider="Bed")
    ground_patch(b, (cows[0] - 1.0, max_x, cows[3] + 1.0, max_z), YARD_TOP, "soil", SOIL, collider="Yard")
    ground_patch(b, (min_x, max_x, -FARM_LANE_HALF_WIDTH, FARM_LANE_HALF_WIDTH), YARD_TOP, "soil", SOIL, collider="Path")
    ground_patch(b, (min_x, max_x, -YARD_VERGE, -FARM_LANE_HALF_WIDTH), YARD_TOP, "soil", SOIL, collider="Yard")
    ground_patch(b, (min_x, max_x, min_z, -YARD_VERGE), YARD_TOP, "lawn", "FFFFFF", collider="Bed")
    dirt_track(b, YARD_LANE, YARD_TOP + 0.012, SEED + 70)

    for index, (x, z, rx, rz) in enumerate(((92.5, 35.8, 2.6, 1.8), (96.5, 33.8, 1.8, 1.3), (88.5, 41.0, 1.6, 1.2))):
        rounded_blob(b, (x, z), (rx, rz), YARD_TOP + 0.012, MUD, SEED + index)

    for index, (x, z, rx, rz) in enumerate(((88.0, 6.6, 2.0, 1.1), (93.5, 19.6, 3.4, 1.2))):
        rounded_blob(b, (x, z), (rx, rz), YARD_TOP + 0.012, SOIL, SEED + 10 + index)

    for index, (x, z, rx, rz) in enumerate(YARD_GRASS_PATCHES):
        rounded_blob(b, (x, z), (rx, rz), YARD_TOP + 0.008, "FFFFFF", SEED + 50 + index, material="lawn")

    scatter_tufts(b, YARD_GRASS_PATCHES, SEED + 60)
    terreiro(b)
    build_kitchen_garden(b, KITCHEN_GARDEN[1:])
    build_curral(b)
    build_water_corner(b)

    farm_cart(b, frame_at_world(98.0, -5.0, YARD_TOP, 20.0), load="hay", seed=3)
    haycock(b, frame_at_world(80.5, -3.6, YARD_TOP, 10.0), 1.1, 1.0, 71, fork=True)
    bale_stack(b, frame_at_world(79.0, 40.0, YARD_TOP, 0.0), 4, 2, 3, 81)
    haycock(b, frame_at_world(78.6, 32.6, YARD_TOP, 30.0), 1.2, 1.05, 82)
    haycock(b, frame_at_world(81.8, 35.4, YARD_TOP, 80.0), 1.0, 0.9, 83)

    return finish_model(b, "farm_yard", {"origin": "world", "doors": []})


RANCHO_EAVE = {"cows": 2.7, "pigs": 2.4}
PEN_PROPS = [(pen, prop) for pen, props in FARM_PEN_PROPS.items() for prop in props]
PEN_PROP_BUILDERS = {  # tipo de FARM_PEN_PROPS -> (builder, frame, cercado, largura, fundo)
    "rancho": lambda b, frame, pen, width, depth: farm_rancho(b, frame, width, depth, RANCHO_EAVE[pen]),
    "hay_rack": lambda b, frame, pen, width, depth: hay_rack(b, frame, width),
    "trough": lambda b, frame, pen, width, depth: trough(b, frame, width),
    "hay_pile": lambda b, frame, pen, width, depth: hay_pile(b, frame, (width, depth, 0.5), 61),
}


def build_curral(b: Builder) -> None:
    """The pens: heavy fences with a porteira each, ranchos on round posts, troughs, hay rack."""
    cows, pigs = FARM_PENS["cows"], FARM_PENS["pigs"]

    fence_run(b, rectangle_loop(cows), YARD_TOP, SEED + 20, gates=((0, 6),))
    fence_run(b, rectangle_loop(pigs), YARD_TOP, SEED + 21, gates=((0, 1),))

    # Ranchos inteiros dentro do cercado: fundo e beiral a mais de 1,3 m da cerca.
    for pen, (kind, x, z, yaw, width, depth) in PEN_PROPS:
        PEN_PROP_BUILDERS[kind](b, frame_at_world(x, z, YARD_TOP, yaw), pen, width, depth)


def terreiro(b: Builder) -> None:
    """Paved drying yard in front of the casa-grande: brick field inside a border of cut stone and a white kerb, a stone
    path from the stair to the lane, drying beds of coffee in rectangles raked into ridges, rakes, sacks, baskets,
    sieves. The whole slab is one walkable collider named Terreiro (it sounds like stone)."""
    min_x, max_x, min_z, max_z = TERREIRO
    inner = (min_x + TERREIRO_BORDER, max_x - TERREIRO_BORDER, min_z + TERREIRO_BORDER, max_z - TERREIRO_BORDER)
    border_rectangles = (
        (min_x, max_x, min_z, min_z + TERREIRO_BORDER),
        (min_x, max_x, max_z - TERREIRO_BORDER, max_z),
        (min_x, min_x + TERREIRO_BORDER, min_z + TERREIRO_BORDER, max_z - TERREIRO_BORDER),
        (max_x - TERREIRO_BORDER, max_x, min_z + TERREIRO_BORDER, max_z - TERREIRO_BORDER),
    )

    b.collider(world(min_x, max_z, YARD_TOP - 0.05), world(max_x, min_z, TERREIRO_TOP), name="Terreiro")
    ground_patch(b, inner, TERREIRO_TOP, "paving", BRICK_TINT, thickness=0.1)

    for rectangle in border_rectangles:
        ground_patch(b, rectangle, TERREIRO_TOP, "stone", STONE["clara"], thickness=0.1)

    ground_patch(b, (TERREIRO_PATH[0], TERREIRO_PATH[1], min_z + TERREIRO_BORDER, max_z - TERREIRO_BORDER), TERREIRO_TOP + 0.012, "stone", STONE["clara"], thickness=0.02)
    kerb_loop(b, (min_x - 0.12, max_x + 0.12, min_z - 0.12, max_z + 0.12), YARD_TOP + 0.02, 0.2, 0.14)

    for index, (bed_min, bed_max, states) in enumerate(COFFEE_BEDS.values()):
        for row, state in enumerate(states):
            z_low = COFFEE_BED_START + row * COFFEE_BED_PITCH
            coffee_bed(b, (bed_min, bed_max, z_low, z_low + COFFEE_BED_DEPTH), state, SEED + 100 * index + row)

    terreiro_props(b)


def kerb_loop(b: Builder, rectangle: tuple, ground: float, height: float, width: float, tint: str = KERB_TINT) -> None:
    """White kerb (guia caiada) around a rectangle: four low boxes standing on the ground, no collider."""
    min_x, max_x, min_z, max_z = rectangle
    sides = (
        (min_x, max_x, min_z, min_z + width),
        (min_x, max_x, max_z - width, max_z),
        (min_x, min_x + width, min_z + width, max_z - width),
        (max_x - width, max_x, min_z + width, max_z - width),
    )

    for side in sides:
        ground_patch(b, side, ground + height, "plaster", tint, thickness=height)


def coffee_bed(b: Builder, rectangle: tuple, state: str, seed: int) -> None:
    """One drying bed: white kerb, a layer of coffee (state picks the stage: ripe cherry, half dried, dry) and the
    furrows the rodo leaves in it. state None leaves bare brick."""
    min_x, max_x, min_z, max_z = rectangle

    kerb_loop(b, rectangle, TERREIRO_TOP, 0.07, 0.1)

    if state is None:
        return

    generator = random.Random(seed)
    tint = COFFEE_TINTS[state]
    fill_top = TERREIRO_TOP + 0.035

    ground_patch(b, (min_x + 0.1, max_x - 0.1, min_z + 0.1, max_z - 0.1), fill_top, "soil", tint, thickness=0.04)

    for ridge_z in [min_z + 0.35 + index * 0.37 for index in range(int((max_z - min_z - 0.5) / 0.37) + 1)]:
        ridge_tint = shade_tint(srgb(tint), generator.uniform(0.82, 1.06))
        ridge_row(b, min_x + 0.2, max_x - 0.2, ridge_z, fill_top, ridge_tint)


def ridge_row(b: Builder, x_from: float, x_to: float, z: float, ground: float, tint: tuple) -> None:
    """Furrow ridge left by the rake: a long low triangular prism along x."""
    along = Matrix.Translation(world(x_from, z, ground))

    b.side_prism([(-0.15, 0.0), (0.15, 0.0), (0.0, 0.07)], 0.0, x_to - x_from, "soil", tint, frame=along @ Matrix.Rotation(math.pi / 2.0, 4, "Z"))


def rodo(b: Builder, frame: Matrix) -> None:
    """Coffee rake lying on the ground: long pole, wide board head with a lip."""
    wood = srgb(WOOD["mel"])

    b.cylinder((0.0, 0.0, 0.05), 0.022, 2.3, 6, "wood", wood, frame=frame @ Matrix.Rotation(math.pi / 2.0, 4, "Y"), uv=("band", *WOOD_LIGHT_BAND, 1.0))
    b.box((2.28, -0.36, 0.0), (2.36, 0.36, 0.13), "wood", srgb(WOOD["media"]), frame=frame, uv=("band", *WOOD_DARK_BAND, 1.0))
    b.box((2.2, -0.36, 0.0), (2.28, 0.36, 0.04), "wood", wood, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 1.0))


def peneira(b: Builder, frame: Matrix) -> None:
    """Round wicker sieve lying flat with a handful of cherries on it."""
    b.cylinder((0.0, 0.0, 0.0), 0.5, 0.05, 14, "paint", srgb("C49A5E"), frame=frame)
    b.cylinder((0.0, 0.0, 0.05), 0.5, 0.04, 14, "paint", srgb("96703E"), top_radius=0.46, frame=frame)
    b.cylinder((0.0, 0.0, 0.05), 0.42, 0.03, 14, "soil", srgb(COFFEE_TINTS["cereja"]), frame=frame)


def burlap_pile(b: Builder, frame: Matrix) -> None:
    """Sacks of coffee (sacas de juta) piled three, two and one, standing, a lying one in front."""
    rows = ((0.0, 0.0, 0.0), (0.55, 0.0, 0.0), (1.1, 0.0, 0.0), (0.27, 0.0, 0.42), (0.82, 0.0, 0.42), (0.55, 0.0, 0.84))

    for index, (x, y, z) in enumerate(rows):
        sack(b, frame, x, y, z, 0.27, 0.5, BURLAP_TINTS[index % 3])

    lying_sack(b, frame, (0.55, -0.62, 0.0), 80.0, 0.22, 0.62, BURLAP_TINTS[1])
    b.collider((-0.3, -0.3, 0.0), (1.4, 0.3, 1.3), frame=frame)


def terreiro_props(b: Builder) -> None:
    """Rakes on the beds, sacks of coffee by the tulha door, balaios of cherries, sieves, a wheelbarrow."""
    top = TERREIRO_TOP

    rodo(b, frame_at_world(79.0, -26.4, top + 0.1, 8.0))
    rodo(b, frame_at_world(88.6, -13.2, top + 0.1, -170.0))
    rodo(b, frame_at_world(80.2, -10.0, top + 0.1, 188.0))
    peneira(b, frame_at_world(84.6, -9.0, top + 0.012, 0.0))
    peneira(b, frame_at_world(85.9, -7.6, top + 0.012, 30.0))
    burlap_pile(b, frame_at_world(91.6, -25.2, top, 90.0))
    burlap_pile(b, frame_at_world(91.6, -9.6, top, 90.0))
    basket(b, frame_at_world(87.8, -21.0, top, 20.0), "coffee", 301, radius=0.3, height=0.34)
    basket(b, frame_at_world(88.3, -20.3, top, 80.0), "coffee", 302, radius=0.27, height=0.3)
    basket(b, frame_at_world(83.5, -28.6, top, 0.0), "coffee", 303, radius=0.3, height=0.34)
    wheelbarrow(b, frame_at_world(90.0, -6.2, top, -60.0))


def build_water_corner(b: Builder) -> None:
    """East end of the sede's garden: cacimba with sarilho, and the spring box with its bamboo bica over a stone trough."""
    cacimba(b, frame_at_world(96.6, -29.0, YARD_TOP, 0.0))
    spring_box(b, frame_at_world(99.9, -32.2, YARD_TOP, 180.0))


def scatter_tufts(b: Builder, patches: tuple, seed: int) -> None:
    """Tufts of grass on every patch so the edges read as grass, not paint."""
    generator = random.Random(seed)
    spots = [
        (x + math.cos(angle) * radius_x * reach, z + math.sin(angle) * radius_z * reach)
        for x, z, radius_x, radius_z in patches
        for angle, reach in ((generator.uniform(0.0, 2.0 * math.pi), math.sqrt(generator.random()) * 0.85) for _ in range(int(5 * radius_x * radius_z)))
    ]

    stamp_variants(b.plants, tuft_variants(MEADOW_TINTS, 0.45, 0.3), spot_matrices(spots, YARD_TOP, generator, (0.6, 1.2)), generator)


def build_kitchen_garden(b: Builder, rectangle: tuple) -> None:
    """Sede's vegetable patch: cabbage and carrot rows in a low fence with a gap toward the sede."""
    min_x, max_x, min_z, max_z = rectangle
    half_z = (min_z + max_z) / 2.0
    ground = YARD_TOP + 0.04 - FIELD_RAISE

    ground_patch(b, rectangle, YARD_TOP + 0.04, "soil", SOIL_DARK, collider="Field", thickness=0.06)
    plant_crop(b, "cabbage", ("cabbage", min_x + 0.5, max_x - 0.5, min_z + 0.4, half_z - 0.2), ground - 0.08, SEED + 30)
    plant_crop(b, "carrot", ("carrot", min_x + 0.5, max_x - 0.5, half_z + 0.2, max_z - 0.4), ground - 0.08, SEED + 31)
    fence_run(b, [(min_x, max_z), (min_x, min_z), (max_x, min_z), (max_x, max_z), (min_x + 1.6, max_z)], YARD_TOP, SEED + 32, style="horta")


# ---------- the fields past the wall ----------

FIELD_LANE = [(102.0, 0.0), (107.0, 0.5), (113.0, -0.7), (120.0, 0.6), (127.0, -0.5), (134.0, 0.8), (141.0, -0.3), (148.5, 0.4)]
FIELD_FOOTPATHS = (  # trilhas de pé: ao longo do muro (norte e sul) e a cabeceira entre o cafezal e a mandioca e o milho
    [(105.2, -44.0), (104.8, -32.0), (105.7, -18.0), (105.1, -2.6)],
    [(105.2, 2.6), (105.7, 14.0), (104.8, 30.0), (105.3, 44.0)],
    [(106.0, -21.8), (118.0, -21.3), (131.0, -22.2), (147.5, -21.6)],
)


TRACK_EDGE_SHARE = 1.4  # bordas onduladas do dirt_track chegam a ~1,35 x meia largura do centro


def rectangle_gap(point: tuple, rectangle: tuple) -> float:
    """Distance from a world point (x, z) to a rectangle (min x, max x, min z, max z); 0 inside."""
    min_x, max_x, min_z, max_z = rectangle

    return math.hypot(max(min_x - point[0], 0.0, point[0] - max_x), max(min_z - point[1], 0.0, point[1] - max_z))


def check_plots_clear_of_tracks() -> None:
    """No crop plot reaches a lane or footpath, wobbling edges included (the carrots once grew on the path)."""
    tracks = [(FIELD_LANE, 1.9)] + [(footpath, 0.85) for footpath in FIELD_FOOTPATHS]
    samples = [(tuple(center), half_width) for points, half_width in tracks for center in smooth_path(points, 0.5)[0]]
    plots = {name: plot[1:] for name, plot in FARM_FIELD_PLOTS.items()}
    plots["KitchenGarden"] = KITCHEN_GARDEN[1:]
    crossing = sorted({name for name, rectangle in plots.items() for center, half_width in samples if rectangle_gap(center, rectangle) < half_width * TRACK_EDGE_SHARE})

    if crossing:
        raise SystemExit(f"canteiros sobre caminho: {crossing}")


def build_farm_fields() -> dict:
    """Crop plots, meadows, the lane out of the town gate, footpaths, gate posts and the outer fence, in world
    coordinates. No plot touches a track: the lane keeps 1.8 m of verge each side, the footpaths 1.4 m."""
    b = farm_builder("farm_fields")
    min_x, max_x, min_z, max_z = FARM_FIELDS
    gate_x = min_x - TOWN_GATE_DEPTH
    track_top = OUTSIDE_GROUND + 0.02

    check_plots_clear_of_tracks()

    b.collider(world(gate_x, 3.0, track_top - 0.08), world(max_x, -3.0, track_top), name="Path")
    b.collider(world(min_x + 0.6, max_z - 1.0, track_top - 0.08), world(min_x + 3.6, min_z + 1.0, track_top), name="Path")
    dirt_track(b, FIELD_LANE, track_top, SEED + 72)

    for index, footpath in enumerate(FIELD_FOOTPATHS):
        dirt_track(b, footpath, track_top, SEED + 73 + index, half_width=0.85, cart_ruts=False)
        b.plants.flush(CROPS_PREFIX)

    for name, plot in FARM_FIELD_PLOTS.items():
        build_plot(b, name, plot)

    for index, (x, z, shirt) in enumerate(((126.0, -34.0, "4F8FC9"), (116.0, -12.0, "C9483B"))):
        scarecrow(b, frame_at_world(x, z, OUTSIDE_GROUND + FIELD_RAISE, index * 140.0 + 20.0), shirt)

    for side in (-1, 1):
        gate_post(b, (CITY_EAST_WALL_X + 0.6, (FARM_GATE_Z[0] if side < 0 else FARM_GATE_Z[1]) + side * 0.5))

    fence_run(b, [(min_x + 0.2, min_z), (max_x, min_z), (max_x, max_z), (min_x + 0.2, max_z)], OUTSIDE_GROUND, SEED + 40, gaps=())
    farm_cart(b, frame_at_world(113.0, -21.4, track_top, 90.0), load="produce", seed=9)

    return finish_model(b, "farm_fields", {"origin": "world", "doors": []})


def gate_post(b: Builder, position: tuple) -> None:
    """Stone pillar with a cap and a lantern bracket at each side of the gap in the town wall."""
    frame = frame_at_world(position[0], position[1], OUTSIDE_GROUND)

    b.box((-0.6, -0.5, 0.0), (0.6, 0.5, 4.9), "stone", srgb(STONE["media"]), frame=frame)
    b.box((-0.7, -0.6, 4.9), (0.7, 0.6, 5.15), "trim", srgb(STONE["clara"]), frame=frame)
    b.hull([(-0.55, -0.45, 5.15), (0.55, -0.45, 5.15), (-0.55, 0.45, 5.15), (0.55, 0.45, 5.15), (0.0, 0.0, 5.75)], "trim", srgb(STONE["clara"]), frame=frame)
    b.collider((-0.6, -0.5, 0.0), (0.6, 0.5, 4.9), frame=frame)


# ---------- the wagons of the street carriages ----------

def arched_cover(b: Builder, frame: Matrix, half_width: float, base: float, rise: float, span: tuple, tint: tuple, thickness: float = 0.03) -> None:
    """Canvas tilt over the bed: a barrel vault open at both ends, with thickness (you see the load through it)."""
    steps = 12
    angles = [math.pi * step / steps for step in range(steps + 1)]
    cover = bmesh.new()
    arches = [
        [cover.verts.new(((half_width - inset) * math.cos(angle), y, base + (rise - inset) * math.sin(angle))) for angle in angles]
        for y, inset in itertools.product(span, (0.0, thickness))
    ]
    outer_front, inner_front, outer_back, inner_back = arches
    strips = ((outer_front, outer_back), (inner_back, inner_front), (inner_front, outer_front), (outer_back, inner_back))

    for (first, second), step in itertools.product(strips, range(steps)):
        cover.faces.new((first[step], first[step + 1], second[step + 1], second[step]))

    for face in cover.faces:
        face.smooth = True

    b._link(cover, "paint", tint, None, frame)


def wagon_marks(b: Builder) -> None:
    """Where carriage.gd puts the horse and where a driver sits (sidecar markers, Godot coords: +Z ahead)."""
    b.marker("horse", (0.0, -HORSE_OFFSET, 0.0))
    b.marker("driver_seat", (0.0, SEAT_Y, SEAT_HEIGHT))


def build_farm_wagon() -> dict:
    """Covered two-wheeled wagon hitched to one horse (origin under the axle; the horse walks ahead, -Y)."""
    b = farm_builder("farm_wagon")
    frame = Matrix.Identity(4)
    side_top = CART_FLOOR + 0.05 + CART_SIDE_HEIGHT
    cover_span = (SEAT_Y + 0.42, CART_HALF_LENGTH + 0.05)

    farm_cart(b, frame, load="sacks", seed=5, hitched=True)
    arched_cover(b, frame, CART_HALF_WIDTH + 0.06, side_top, 0.95, cover_span, srgb("F2E6CF"))

    for hoop_y in (cover_span[0] + 0.02, sum(cover_span) / 2.0, cover_span[1] - 0.02):
        arched_cover(b, frame, CART_HALF_WIDTH + 0.075, side_top, 0.965, (hoop_y - 0.025, hoop_y + 0.025), srgb(WOOD["media"]), thickness=0.07)

    wagon_lantern(b, frame)
    wagon_marks(b)

    return finish_model(b, "farm_wagon", {"origin": "axle", "doors": []})


def build_hay_cart() -> dict:
    """Open two-wheeled cart heaped with hay, the second wagon of the street loop."""
    b = farm_builder("hay_cart")

    farm_cart(b, Matrix.Identity(4), load="hay", seed=11, hitched=True)
    wagon_lantern(b, Matrix.Identity(4))
    wagon_marks(b)

    return finish_model(b, "hay_cart", {"origin": "axle", "doors": []})


def wagon_lantern(b: Builder, frame: Matrix) -> None:
    """Small lantern on an iron arm beside the driver (smoky glass that lights up at night, features/sky/window_glass.gd)."""
    side = CART_HALF_WIDTH + 0.04

    b.beam((side, SEAT_Y - 0.1, SEAT_HEIGHT - 0.1), (side + 0.16, SEAT_Y - 0.3, SEAT_HEIGHT + 0.42), 0.035, 0.035, "metal", srgb("4A4448"), frame=frame)
    b.box((side + 0.08, SEAT_Y - 0.38, SEAT_HEIGHT + 0.14), (side + 0.24, SEAT_Y - 0.22, SEAT_HEIGHT + 0.36), "lantern", WHITE, frame=frame)
    b.box((side + 0.06, SEAT_Y - 0.4, SEAT_HEIGHT + 0.36), (side + 0.26, SEAT_Y - 0.2, SEAT_HEIGHT + 0.41), "metal", srgb("4A4448"), frame=frame)
    b.box((side + 0.06, SEAT_Y - 0.4, SEAT_HEIGHT + 0.1), (side + 0.26, SEAT_Y - 0.2, SEAT_HEIGHT + 0.14), "metal", srgb("4A4448"), frame=frame)


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
