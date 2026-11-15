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
HALF_WIDTH = 13.0
CENTER_HALF = 3.6
TOWER_OUTER = 9.1
NAVE_HALF = 7.0
WALL = 0.6
FACADE_DEPTH = 1.0
NARTHEX_DEPTH = 5.0
BODY_LENGTH = 40.0
APSE_RADIUS = NAVE_HALF
AISLE_TOP = 13.5
ARCADE_TOP = 11.2
NAVE_CEILING = 17.5
NAVE_WALL_TOP = 19.5
TOWER_BASE_TOP = 22.0
PIER_Y = [10.6, 16.2, 21.8, 27.4, 33.0]
ARCH_WIDTH = 4.6
ARCH_SPRING = 7.6
BAY_CENTERS = [7.8, 13.4, 19.0, 24.6, 30.2]
CHANCEL_BAY = 36.5
CHANCEL_FRONT = 33.0
CHANCEL_HEIGHT = 0.9
CHANCEL_FLOOR = BASE + CHANCEL_HEIGHT
PORTAL_WIDTH = 4.6
PORTAL_SPRING = 4.8
AISLE_WINDOW = (1.7, 7.6)  # vitral alto em arco de cada tramo (largura, altura)
LOW_WINDOW = (1.4, 2.2)  # janela baixa, sob a faixa ocre
OCHRE_BAND = (4.8, 5.6)  # altura absoluta da faixa ocre (multiplo de 0,8: a textura repete a cada 0,8 m)
NAVE_FRIEZE = (12.0, 12.8)
CHANDELIER_Y = [8.0, 14.0, 20.0, 26.0]
CAPITAL_LEAVES = 8
CAPITAL_LEAF_ROWS = [(0.0, 0.4, 0.34), (0.24, 0.47, 0.36)]  # (altura, raio, tamanho) de cada fileira de folhas do capitel
COLUMN_SCALE = 1.2
SCONCE_HEIGHT = 3.4
PEW_ROWS = (8.0, 31.0)  # primeira e ultima fileira de bancos ao longo da nave
PEW_PITCH = 1.15
PEW_GAP_ROW = 10  # fileira omitida: corredor transversal entre as portas laterais
PEW_BLOCKS = ((1.3, 3.6), (4.6, 6.3), (8.8, 11.2))  # x (do eixo para fora) de cada bloco: nave interna, nave externa, nave lateral
SIDE_DOOR_Y = 19.0
LOFT_HEIGHT = 7.4  # laje do coro alto sobre o nartex
RETABLE_Y = BODY_LENGTH + APSE_RADIUS - 1.3
LANCET_ANGLES = (30.0, 55.0, 78.0)  # graus do eixo da abside, de cada lado
LANCET_SIZE = (1.5, 8.5)

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


def make_figure_glass_image():
    """Leaded stained glass with a haloed, robed figure under a pointed canopy: one window = one texture (256 x 512)."""
    width, height = 256, 512
    generator = numpy.random.default_rng(23)
    cell_count = 520
    cell_points = generator.random((cell_count, 2)) * (width, height)
    grid_y, grid_x = numpy.meshgrid(numpy.arange(height), numpy.arange(width), indexing="ij")
    pixels = numpy.stack([grid_x, grid_y], axis=-1).reshape(-1, 1, 2)
    distances = numpy.linalg.norm(pixels - cell_points[None, :, :], axis=2)
    nearest_two = numpy.sort(distances, axis=1)[:, :2]
    owner = numpy.argmin(distances, axis=1)
    cell_u = cell_points[:, 0] / width - 0.5
    cell_v = cell_points[:, 1] / height
    robe_half = 0.1 + 0.2 * numpy.clip((0.66 - cell_v) / 0.56, 0.0, 1.0)
    in_robe = (cell_v > 0.1) & (cell_v < 0.66) & (numpy.abs(cell_u) < robe_half)
    in_mantle = in_robe & (cell_u * (1.0 + cell_v) > 0.02)
    head_distance = numpy.hypot(cell_u, (cell_v - 0.72) * 2.0)
    in_border = (numpy.abs(cell_u) > 0.41) | (cell_v < 0.045) | (cell_v > 0.955)
    in_ground = cell_v < 0.12
    palette = numpy.where(cell_v[:, None] > 0.5, [[0.1, 0.22, 0.72]], [[0.14, 0.34, 0.8]]) * numpy.ones((cell_count, 3))
    palette[in_ground] = [0.16, 0.5, 0.24]
    palette[in_robe] = [0.9, 0.86, 0.74]
    palette[in_mantle] = [0.7, 0.14, 0.14]
    palette[head_distance < 0.2] = [0.98, 0.8, 0.26]
    palette[head_distance < 0.11] = [0.93, 0.72, 0.58]
    palette[in_border] = numpy.where((numpy.floor(cell_v[in_border] * 14.0) % 2 == 0)[:, None], [[0.75, 0.16, 0.12]], [[0.95, 0.7, 0.2]])
    shade = 0.8 + 0.25 * generator.random((cell_count, 1))
    rgb = (palette * shade)[owner]
    rgb[(nearest_two[:, 1] - nearest_two[:, 0]) < 1.5] = [0.04, 0.04, 0.06]
    rgba = numpy.concatenate([numpy.clip(rgb, 0.0, 1.0), numpy.ones((len(rgb), 1))], axis=1)
    image = bpy.data.images.new("T_StainedGlassFigure", width, height, alpha=False)

    image.pixels.foreach_set(rgba.astype(numpy.float32).ravel())
    image.filepath_raw = str(GENERATED_TEXTURES / "T_StainedGlassFigure.png")
    image.file_format = "PNG"
    image.save()

    return image


def save_rgb_image(name: str, rgb) -> bpy.types.Image:
    """Save a (height, width, 3) float array (row 0 = bottom, as Blender stores pixels) as a PNG texture."""
    height, width = rgb.shape[:2]
    rgba = numpy.concatenate([numpy.clip(rgb, 0.0, 1.0), numpy.ones((height, width, 1))], axis=2)
    image = bpy.data.images.new(name, width, height, alpha=False)

    image.pixels.foreach_set(rgba.astype(numpy.float32).ravel())
    image.filepath_raw = str(GENERATED_TEXTURES / f"{name}.png")
    image.file_format = "PNG"
    GENERATED_TEXTURES.mkdir(parents=True, exist_ok=True)
    image.save()

    return image


def voronoi_cells(width: int, height: int, cell_count: int, seed: int) -> tuple:
    """Cell centers, owner cell of every pixel (height, width) and the gap between the two nearest centers (lead line where small)."""
    generator = numpy.random.default_rng(seed)
    points = (generator.random((cell_count, 2)) * (width, height)).astype(numpy.float32)
    grid_y, grid_x = numpy.meshgrid(numpy.arange(height), numpy.arange(width), indexing="ij")
    pixels = numpy.stack([grid_x, grid_y], axis=-1).reshape(-1, 2).astype(numpy.float32)
    owner = numpy.empty(len(pixels), dtype=numpy.int32)
    gap = numpy.empty(len(pixels), dtype=numpy.float32)

    for start in range(0, len(pixels), 8192):
        block = pixels[start:start + 8192]
        distances = numpy.sqrt(((block[:, None, :] - points[None, :, :]) ** 2).sum(axis=2))
        nearest = numpy.partition(distances, 1, axis=1)[:, :2]
        owner[start:start + 8192] = distances.argmin(axis=1)
        gap[start:start + 8192] = nearest.max(axis=1) - nearest.min(axis=1)

    return points, owner.reshape(height, width), gap.reshape(height, width)


def ellipse_mask(x, y, center_x: float, center_y: float, semi_major: float, semi_minor: float, degrees: float):
    angle = math.radians(degrees)
    along = (x - center_x) * math.cos(angle) + (y - center_y) * math.sin(angle)
    across = -(x - center_x) * math.sin(angle) + (y - center_y) * math.cos(angle)

    return (along / semi_major) ** 2 + (across / semi_minor) ** 2 <= 1.0


def feather_fan(label, color, x, y, shoulder: tuple, angles: list, lengths: list, width: float, first_id: int, tint) -> None:
    """Dove wing or tail: overlapping elliptical feathers fanning out of one shoulder, drawn from the last to the first."""
    for feather_index in reversed(range(len(angles))):
        direction = (math.cos(math.radians(angles[feather_index])), math.sin(math.radians(angles[feather_index])))
        center = (shoulder[0] + direction[0] * lengths[feather_index] / 2.0, shoulder[1] + direction[1] * lengths[feather_index] / 2.0)
        mask = ellipse_mask(x, y, center[0], center[1], lengths[feather_index] / 2.0, width, angles[feather_index])
        label[mask] = first_id + feather_index
        color[mask] = tint * (0.93 + 0.07 * (feather_index % 2))


def make_leaded_glass(name: str, width: int, height: int, window_size: tuple, painter, cell_count: int, seed: int):
    """Stained glass: painter(x_m, y_m, cell_x_m, cell_y_m, cell_random) -> (shape label, rgb); lead where cells or shapes meet."""
    points, owner, gap = voronoi_cells(width, height, cell_count, seed)
    grid_y, grid_x = numpy.meshgrid(numpy.arange(height), numpy.arange(width), indexing="ij")
    meters_x = (grid_x + 0.5) / width * window_size[0] - window_size[0] / 2.0
    meters_y = (grid_y + 0.5) / height * window_size[1]
    cell_x = points[:, 0][owner] / width * window_size[0] - window_size[0] / 2.0
    cell_y = points[:, 1][owner] / height * window_size[1]
    generator = numpy.random.default_rng(seed + 1)
    cell_random = generator.random(cell_count)
    label, color = painter(meters_x, meters_y, cell_x, cell_y, cell_random[owner])
    shade = (0.9 + 0.16 * generator.random(cell_count))[owner][..., None]
    rgb = color * shade
    edge = (label != numpy.roll(label, 1, axis=0)) | (label != numpy.roll(label, 1, axis=1))
    edge |= numpy.roll(edge, 1, axis=0) | numpy.roll(edge, 1, axis=1)
    rgb[(gap < 1.5) | edge] = [0.04, 0.04, 0.06]

    return save_rgb_image(name, rgb)


DOVE_RAY_PALETTES = [
    (numpy.array([0.95, 0.77, 0.27]), numpy.array([0.91, 0.59, 0.18])),
    (numpy.array([0.97, 0.82, 0.35]), numpy.array([0.88, 0.40, 0.28])),
    (numpy.array([1.00, 0.90, 0.55]), numpy.array([0.93, 0.62, 0.20])),
]
WHITE_PEARL = numpy.array([0.97, 0.96, 0.92])
RUBY = numpy.array([0.66, 0.14, 0.17])
GOLD = numpy.array([0.95, 0.77, 0.26])
LEAF_GREEN = numpy.array([0.25, 0.54, 0.31])
COBALT = numpy.array([0.12, 0.25, 0.66])
SKY_BLUE = numpy.array([0.44, 0.70, 0.95])
TURQUOISE = numpy.array([0.10, 0.62, 0.72])


def sky_gradient(vertical):
    """Cobalt at the base of the window to sky blue at the top (vertical 0..1)."""
    amount = numpy.clip(vertical, 0.0, 1.0)[..., None]

    return COBALT + (SKY_BLUE - COBALT) * amount


def paint_dove_window(variant: int, mirror: bool, dove_height: float):
    """Painter for one apse lancet (1.5 x 9 m): white dove with an olive branch under golden rays, lilies and a medallion below."""
    ray_colors = DOVE_RAY_PALETTES[variant]
    scale = 0.72

    def painter(x, y, cell_x, cell_y, cell_random):
        x_flipped = -x if mirror else x
        label = numpy.zeros(x.shape, dtype=numpy.int32)
        color = sky_gradient(cell_y / 9.0)
        turquoise = (cell_random < 0.15)[..., None]
        color = numpy.where(turquoise, TURQUOISE, color)
        dove_x, dove_y = -0.05, dove_height
        angle = numpy.degrees(numpy.arctan2(y - dove_y, x_flipped - dove_x))
        wedge = numpy.floor((angle + 160.0) / (140.0 / 18.0)).astype(numpy.int32)
        in_rays = (angle > -160.0) & (angle < -20.0) & (wedge % 2 == 0) & (y > 4.05)
        label[in_rays] = 10 + wedge[in_rays]
        color[in_rays] = numpy.where(((wedge // 2) % 2 == 0)[in_rays][:, None], ray_colors[0], ray_colors[1])
        halo_distance = numpy.hypot(x_flipped - dove_x, y - dove_y)
        label[halo_distance < 0.72] = 3
        color[halo_distance < 0.72] = GOLD
        label[halo_distance < 0.68] = 4
        color[halo_distance < 0.68] = [0.10, 0.20, 0.56]

        local_x = (x_flipped - dove_x) / scale
        local_y = (y - dove_y) / scale
        feather_fan(label, color, local_x, local_y, (0.0, 0.02), [215.0, 228.0, 242.0, 256.0], [0.55, 0.58, 0.55, 0.48], 0.075, 70, WHITE_PEARL * 0.94)
        feather_fan(label, color, local_x, local_y, (0.02, 0.10), [48.0, 64.0, 80.0, 96.0, 112.0], [0.80, 0.82, 0.78, 0.70, 0.60], 0.085, 60, WHITE_PEARL)
        feather_fan(label, color, local_x, local_y, (-0.30, 0.0), [186.0, 172.0, 160.0], [0.30, 0.32, 0.28], 0.06, 54, WHITE_PEARL * 0.96)
        body = ellipse_mask(local_x, local_y, 0.0, 0.0, 0.36, 0.14, -8.0)
        label[body] = 50
        color[body] = WHITE_PEARL
        head = numpy.hypot(local_x - 0.42, local_y - 0.11) < 0.095
        label[head] = 51
        color[head] = WHITE_PEARL
        beak = ellipse_mask(local_x, local_y, 0.55, 0.10, 0.07, 0.028, 0.0)
        label[beak] = 52
        color[beak] = GOLD
        eye = numpy.hypot(local_x - 0.44, local_y - 0.13) < 0.016
        label[eye] = 53
        color[eye] = [0.05, 0.05, 0.08]

        for sample in numpy.linspace(0.0, 1.0, 40):
            stem_x, stem_y = 0.62 + 0.30 * sample, 0.09 - 0.07 * sample - 0.15 * sample * sample
            stem = numpy.hypot(local_x - stem_x, local_y - stem_y) < 0.018
            label[stem] = 90
            color[stem] = LEAF_GREEN * 0.8

        for leaf_index, sample in enumerate(numpy.linspace(0.18, 1.0, 5)):
            side = 1.0 if leaf_index % 2 == 0 else -1.0
            stem_x, stem_y = 0.62 + 0.30 * sample, 0.09 - 0.07 * sample - 0.15 * sample * sample
            leaf = ellipse_mask(local_x, local_y, stem_x + 0.03, stem_y + side * 0.06, 0.09, 0.035, -25.0 + side * 40.0)
            label[leaf] = 91 + leaf_index
            color[leaf] = LEAF_GREEN

        lower = y < 2.7
        label[lower] = 70
        color[lower] = RUBY

        for lily_x, lily_y in ((-0.38, 1.95), (0.38, 2.05), (0.0, 2.3)):
            lily_id = 120 + int(lily_x * 10 + 5)
            stem = (numpy.abs(x - lily_x) < 0.018) & (y < lily_y) & (y > 1.55)
            label[stem] = lily_id
            color[stem] = LEAF_GREEN
            leaf = ellipse_mask(x, y, lily_x + 0.11, lily_y - 0.28, 0.14, 0.04, 35.0) | ellipse_mask(x, y, lily_x - 0.11, lily_y - 0.28, 0.14, 0.04, 145.0)
            label[leaf] = lily_id + 1
            color[leaf] = LEAF_GREEN

            for petal_index, petal_angle in enumerate((90.0, 52.0, 128.0)):
                direction = (math.cos(math.radians(petal_angle)), math.sin(math.radians(petal_angle)))
                petal = ellipse_mask(x, y, lily_x + direction[0] * 0.12, lily_y + direction[1] * 0.12, 0.15, 0.055, petal_angle)
                label[petal] = lily_id + 2 + petal_index
                color[petal] = WHITE_PEARL

        medallion_distance = numpy.hypot(x, y - 1.0)
        ring = (medallion_distance < 0.5) & (medallion_distance > 0.4)
        inside = medallion_distance <= 0.4
        label[ring] = 130
        color[ring] = GOLD
        label[inside] = 131
        color[inside] = [0.96, 0.9, 0.78]
        cross = inside & (((numpy.abs(x) < 0.05) & (numpy.abs(y - 1.0) < 0.3)) | ((numpy.abs(y - 1.05) < 0.05) & (numpy.abs(x) < 0.2)))
        label[cross] = 132
        color[cross] = GOLD

        side_border = numpy.abs(x) > 0.63
        end_border = (y < 0.27) | (y > 8.73)
        border = side_border | end_border
        side_patch = 200 + numpy.floor(y / 0.3).astype(numpy.int32) * 2 + (x > 0)
        end_patch = 400 + numpy.floor((x + 0.75) / 0.3).astype(numpy.int32) + 10 * (y > 4.0)
        patch = numpy.where(side_border, side_patch, end_patch)
        diamond_gold = (numpy.floor(y / 0.3).astype(numpy.int32) + (x > 0)) % 2 == 0
        end_gold = numpy.floor((x + 0.75) / 0.3).astype(numpy.int32) % 2 == 0
        label[border] = patch[border]
        color[border] = numpy.where(numpy.where(side_border, diamond_gold, end_gold)[border][:, None], GOLD, RUBY)

        return label, color

    return painter


def make_dove_glass_images() -> list:
    """Three apse lancets: doves flying toward the centre (mirrored on the other side), higher near the axis, three ray palettes."""
    specs = [(0, False, 6.9), (1, True, 6.5), (2, False, 6.1)]

    return [make_leaded_glass(f"T_DoveGlass{index}", 256, 1536, (1.5, 9.0), paint_dove_window(variant, mirror, dove_height), 1300, 41 + index) for index, (variant, mirror, dove_height) in enumerate(specs)]


def paint_oculus(x, y, cell_x, cell_y, cell_random):
    """Holy Spirit: a white dove seen from the front, wings spread, head down, inside golden rays in twelve gores."""
    radius = numpy.hypot(x, y)
    angle = numpy.degrees(numpy.arctan2(y, x)) % 360.0
    sector = numpy.floor(angle / 30.0).astype(numpy.int32)
    label = numpy.zeros(x.shape, dtype=numpy.int32)
    color = numpy.where((cell_random < 0.2)[..., None], TURQUOISE, SKY_BLUE * 0.85)
    in_rays = (radius < 1.0) & (sector % 2 == 0)
    label[in_rays] = 10 + sector[in_rays]
    color[in_rays] = numpy.where(((sector // 2) % 2 == 0)[in_rays][:, None], DOVE_RAY_PALETTES[0][0], DOVE_RAY_PALETTES[0][1])
    label[radius < 0.72] = 3
    color[radius < 0.72] = GOLD
    label[radius < 0.68] = 4
    color[radius < 0.68] = [0.10, 0.20, 0.56]

    for side in (-1.0, 1.0):
        angles = [180.0 - 62.0, 180.0 - 44.0, 180.0 - 28.0, 180.0 - 12.0, 180.0 + 4.0, 180.0 + 18.0] if side < 0 else [62.0, 44.0, 28.0, 12.0, -4.0, -18.0]
        feather_fan(label, color, x, y, (side * 0.08, 0.15), angles, [0.55, 0.62, 0.66, 0.64, 0.58, 0.5], 0.085, 60 if side < 0 else 80, WHITE_PEARL)

    feather_fan(label, color, x, y, (0.0, 0.30), [90.0, 76.0, 104.0], [0.32, 0.28, 0.28], 0.06, 100, WHITE_PEARL * 0.96)
    body = ellipse_mask(x, y, 0.0, 0.02, 0.30, 0.13, 90.0)
    label[body] = 50
    color[body] = WHITE_PEARL
    head = numpy.hypot(x, y + 0.30) < 0.10
    label[head] = 51
    color[head] = WHITE_PEARL
    beak = ellipse_mask(x, y, 0.0, -0.43, 0.07, 0.035, 90.0)
    label[beak] = 52
    color[beak] = GOLD

    for eye_x in (-0.04, 0.04):
        eye = numpy.hypot(x - eye_x, y + 0.28) < 0.014
        label[eye] = 53
        color[eye] = [0.05, 0.05, 0.08]

    ring = (radius > 1.0) & (radius < 1.08)
    label[ring] = 130
    color[ring] = GOLD
    outer = radius >= 1.08
    outer_patch = 300 + numpy.floor(angle / 15.0).astype(numpy.int32)
    label[outer] = outer_patch[outer]
    color[outer] = numpy.where((numpy.floor(angle / 15.0).astype(numpy.int32) % 2 == 0)[outer][:, None], RUBY, GOLD)

    return label, color


def make_oculus_glass_image():
    return make_leaded_glass("T_OculusGlass", 512, 512, (2.4, 2.4), lambda x, y, cx, cy, cr: paint_oculus(x, y - 1.2, cx, cy - 1.2, cr), 420, 77)


def make_ochre_band_image():
    """Ochre frieze (3.2 x 0.8 m per tile): a row of small brown arches between pinstripes, as on the aisle walls of the real cathedral."""
    width, height = 512, 128
    grid_y, grid_x = numpy.meshgrid(numpy.arange(height), numpy.arange(width), indexing="ij")
    x = (grid_x + 0.5) / width * 3.2
    y = (grid_y + 0.5) / height * 0.8
    rgb = numpy.broadcast_to(numpy.array([0.84, 0.62, 0.24]), (height, width, 3)).copy()
    stripe = (y < 0.05) | (y > 0.75) | ((y > 0.08) & (y < 0.1)) | ((y > 0.70) & (y < 0.72))
    rgb[stripe] = [0.52, 0.30, 0.13]
    local_x = (x % 0.4) - 0.2
    arch_height = 0.34
    in_arch = (numpy.abs(local_x) < 0.1) & (y > 0.18) & ((y < 0.18 + arch_height - 0.1) | (numpy.hypot(local_x, y - (0.18 + arch_height - 0.1)) < 0.1))
    rgb[in_arch] = [0.46, 0.27, 0.12]
    inner = (numpy.abs(local_x) < 0.07) & (y > 0.2) & ((y < 0.18 + arch_height - 0.1) | (numpy.hypot(local_x, y - (0.18 + arch_height - 0.1)) < 0.07))
    rgb[inner] = [0.93, 0.78, 0.45]
    rgb[(numpy.abs(local_x) < 0.012) & (y > 0.24) & (y < 0.40)] = [0.46, 0.27, 0.12]
    rgb[(numpy.abs(local_x + 0.2) < 0.012) | (numpy.abs(local_x - 0.2) < 0.012)] *= 0.9

    return save_rgb_image("T_OchreBand", rgb)


def make_starry_image(name: str, top_color: tuple, base_color: tuple, star_count: int, seed: int, rib_period: int = 0):
    """Blue vault or niche back with scattered gold stars; with rib_period, gold ribs every that many pixels (apse dome gores)."""
    width, height = (768, 256) if rib_period else (256, 256)
    generator = numpy.random.default_rng(seed)
    grid_y = numpy.arange(height)[:, None] * numpy.ones((1, width))
    blend = (grid_y / height)[..., None]
    rgb = numpy.array(base_color) + (numpy.array(top_color) - numpy.array(base_color)) * blend

    for star_index in range(star_count):
        star_x, star_y = int(generator.integers(4, width - 4)), int(generator.integers(8, height - 4))
        size = int(generator.integers(2, 5))
        rows, columns = numpy.ogrid[:height, :width]
        diamond = (numpy.abs(rows - star_y) + numpy.abs(columns - star_x) <= size) | ((numpy.abs(rows - star_y) <= 0) & (numpy.abs(columns - star_x) <= size + 2)) | ((numpy.abs(columns - star_x) <= 0) & (numpy.abs(rows - star_y) <= size + 2))
        rgb[diamond] = [0.98, 0.84, 0.38]

    if rib_period:
        columns = numpy.arange(width)[None, :] * numpy.ones((height, 1))
        rib = (columns % rib_period < 3) | (columns % rib_period > rib_period - 2)
        rgb[rib] = [0.93, 0.72, 0.28]
        rgb[:6, :, :] = [0.93, 0.72, 0.28]

    return save_rgb_image(name, rgb)


def make_colored_plaster(name: str, color: tuple):
    """Kit plaster re-colored: its brightness pattern around the given average color."""
    source = load_kit_image("T_Plaster_BaseColor.png", True)
    size = source.size[0]
    pixels = numpy.array(source.pixels[:]).reshape(size, size, 4)
    luminance = pixels[..., :3] @ numpy.array([0.3, 0.59, 0.11])
    relative = (luminance / luminance.mean())[..., None] ** 0.8
    rgba = numpy.concatenate([numpy.clip(numpy.array(color) * relative, 0.0, 1.0), numpy.ones((size, size, 1))], axis=2)

    return save_generated_image(name, rgba, size)


def make_floor_image():
    """Polished granite laid on the diagonal: cream and grey diamonds, thin grout, slight per-tile shade noise."""
    size = 256
    generator = numpy.random.default_rng(11)
    cream = numpy.array([0.92, 0.88, 0.80])
    grey = numpy.array([0.62, 0.62, 0.63])
    coordinates = numpy.arange(size)
    grid_y, grid_x = numpy.meshgrid(coordinates, coordinates, indexing="ij")
    diagonal_a = (grid_x + grid_y) // (size // 2)
    diagonal_b = (grid_x - grid_y + size) // (size // 2)
    is_cream = ((diagonal_a + diagonal_b) % 2 == 0)[..., None]
    rgb = numpy.where(is_cream, cream, grey) * (0.96 + 0.04 * generator.random((size, size, 1)))
    grout = ((grid_x + grid_y) % (size // 2) < 2) | ((grid_x - grid_y + size) % (size // 2) < 2)
    rgb[grout] = 0.5
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


def make_glow(name: str, color: tuple, strength: float):
    material = make_plain_material(name, color, 0.0, 0.4)
    shader = material.node_tree.nodes["Principled BSDF"]

    shader.inputs["Emission Color"].default_value = (*color, 1.0)
    shader.inputs["Emission Strength"].default_value = strength

    return material


def build_materials() -> dict:
    # Stone and trim textures are also loaded by build_plaza_props.py.
    stone_image = make_tinted_image("T_Brick_BaseColor.png", "T_CathedralStone_BaseColor", (1.08, 1.06, 1.0), (0.09, 0.08, 0.06))
    trim_image = make_tinted_image("T_Plaster_BaseColor.png", "T_CathedralTrim_BaseColor", (1.04, 1.0, 0.9), (0.1, 0.09, 0.06))
    wall_image = make_tinted_image("T_Plaster_BaseColor.png", "T_CathedralWall_BaseColor", (1.0, 0.97, 0.9), (0.17, 0.16, 0.14))
    salmon_image = make_colored_plaster("T_CathedralSalmon_BaseColor", (0.93, 0.66, 0.55))
    roof_image = make_tinted_image("T_RoundTiles_BaseColor.png", "T_CathedralRoof_BaseColor", (1.15, 0.62, 0.48), (0.08, 0.02, 0.0))
    plaster_normal = load_kit_image("T_Plaster_Normal.png", False)
    figure_image = make_figure_glass_image()
    figure_glass = make_material("M_FigureGlass", figure_image, emission=1.1)
    dove_glass = [make_material(f"M_DoveGlass{index}", image, emission=1.8) for index, image in enumerate(make_dove_glass_images())]
    oculus_glass = make_material("M_OculusGlass", make_oculus_glass_image(), emission=2.4)
    ochre_band = make_material("M_OchreBand", make_ochre_band_image())
    dome_sky = make_material("M_DomeSky", make_starry_image("T_DomeSky", (0.72, 0.84, 0.95), (0.45, 0.62, 0.84), 80, 5, rib_period=64), emission=0.25)
    retable_blue = make_material("M_RetableBlue", make_starry_image("T_RetableBlue", (0.16, 0.30, 0.55), (0.10, 0.20, 0.42), 40, 6), emission=0.35)
    floor = make_material("M_CathedralFloor", make_floor_image())

    floor.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.28

    return {
        "figure_glass": figure_glass,
        "figure_painting": make_material("M_SaintPainting", figure_image),
        "dove_glass": dove_glass,
        "oculus_glass": oculus_glass,
        "ochre_band": ochre_band,
        "dome_sky": dome_sky,
        "retable_blue": retable_blue,
        "lamp_glow": make_glow("M_ChandelierGlow", (1.0, 0.86, 0.6), 2.5),
        "flame": make_glow("M_CandleFlame", (1.0, 0.7, 0.3), 4.0),
        "ruby_glow": make_glow("M_SanctuaryLamp", (1.0, 0.18, 0.12), 3.5),
        "pew_wood": make_plain_material("M_PewWood", (0.3, 0.16, 0.08), 0.0, 0.55),
        "stone": make_material("M_CathedralStone", stone_image, load_kit_image("T_Brick_Normal.png", False), load_kit_image("T_Brick_Roughness.png", False)),
        "wall": make_material("M_CathedralWall", wall_image, plaster_normal),
        "salmon": make_material("M_CathedralSalmon", salmon_image, plaster_normal),
        "trim": make_material("M_CathedralTrim", trim_image, plaster_normal),
        "roof": make_material("M_CathedralRoof", roof_image, load_kit_image("T_RoundTiles_Normal.png", False)),
        "floor": floor,
        "glass": make_material("M_StainedGlass", make_stained_glass_image(), emission=1.2),
        "gold": make_plain_material("M_Gold", (0.92, 0.68, 0.26), 0.3, 0.4),
        "marble": make_plain_material("M_Marble", (0.66, 0.62, 0.55), 0.0, 0.6),
        "marble_white": make_plain_material("M_MarbleWhite", (0.86, 0.83, 0.78), 0.0, 0.35),
        "marble_pink": make_plain_material("M_MarblePink", (0.89, 0.72, 0.66), 0.0, 0.4),
        "marble_grey": make_plain_material("M_MarbleGrey", (0.55, 0.56, 0.58), 0.0, 0.4),
        "marble_green": make_plain_material("M_MarbleGreen", (0.12, 0.27, 0.2), 0.0, 0.35),
        "carpet": make_plain_material("M_Carpet", (0.6, 0.17, 0.17), 0.0, 0.95),
        "blue_robe": make_plain_material("M_MaryRobe", (0.62, 0.76, 0.91), 0.0, 0.7),
        "brown_robe": make_plain_material("M_JosephRobe", (0.55, 0.35, 0.24), 0.0, 0.7),
        "paint_red": make_plain_material("M_PaintRed", (0.6, 0.18, 0.14), 0.0, 0.8),
        "paint_ochre": make_plain_material("M_PaintOchre", (0.82, 0.6, 0.28), 0.0, 0.8),
        "slit_glass": make_plain_material("M_SlitGlass", (0.08, 0.12, 0.25), 0.2, 0.15),
        "wood": make_plain_material("M_DoorWood", (0.26, 0.14, 0.08), 0.0, 0.6),
        "wood_dark": make_plain_material("M_CrossWood", (0.29, 0.18, 0.13), 0.0, 0.55),
        "iron": make_plain_material("M_WroughtIron", (0.07, 0.07, 0.09), 0.8, 0.45),
        "copper": make_plain_material("M_Verdigris", (0.37, 0.63, 0.54), 0.4, 0.5),
        "ivory": make_plain_material("M_CarvedIvory", (0.91, 0.82, 0.69), 0.0, 0.6),
        "linen": make_plain_material("M_Linen", (0.94, 0.91, 0.85), 0.0, 0.85),
        "thorn": make_plain_material("M_Thorns", (0.35, 0.23, 0.16), 0.0, 0.8),
        "candle": make_plain_material("M_Candle", (0.95, 0.9, 0.78), 0.0, 0.6),
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


def carve(targets, cutters: list) -> None:
    """Subtract the cutters from one object or a list of objects (a wall and its skins), then delete the cutters."""
    for target in targets if isinstance(targets, list) else [targets]:
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


def map_uvs_per_face(mesh_object: bpy.types.Object, meters_per_tile) -> None:
    """Planar UVs in each face's own frame: U horizontal, V up the face (walls) or down the slope (roofs).
    meters_per_tile is one size or a (horizontal, vertical) pair for textures that are not square."""
    tile_u, tile_v = meters_per_tile if isinstance(meters_per_tile, tuple) else (meters_per_tile, meters_per_tile)
    uv_bmesh = bmesh.new()
    uv_bmesh.from_mesh(mesh_object.data)
    uv_layer = uv_bmesh.loops.layers.uv.verify()

    for face in uv_bmesh.faces:
        horizontal = face.normal.cross(Vector((0, 0, 1)))
        u_axis = horizontal.normalized() if horizontal.length > 0.01 else Vector((1, 0, 0))
        v_axis = face.normal.cross(u_axis).normalized() if horizontal.length > 0.01 else Vector((0, 1, 0))

        for loop in face.loops:
            world = mesh_object.matrix_world @ loop.vert.co
            loop[uv_layer].uv = (world.dot(u_axis) / tile_u, world.dot(v_axis) / tile_v)

    uv_bmesh.to_mesh(mesh_object.data)
    uv_bmesh.free()


def make_image_panel(name: str, profile: list, size: tuple, transform: Matrix, material) -> bpy.types.Object:
    """Flat XZ polygon showing a whole image once (UV 0..1 across size); finalize_objects keeps these UVs."""
    panel_bmesh = bmesh.new()
    uv_layer = panel_bmesh.loops.layers.uv.verify()
    face = panel_bmesh.faces.new([panel_bmesh.verts.new((x, 0.0, z)) for x, z in profile])

    for loop in face.loops:
        loop[uv_layer].uv = (loop.vert.co.x / size[0] + 0.5, loop.vert.co.z / size[1])

    bmesh.ops.transform(panel_bmesh, matrix=transform, verts=panel_bmesh.verts)
    panel = object_from_bmesh(name, panel_bmesh, material)
    panel["keep_uvs"] = True

    return panel


# ---------- aggregated meshes and curved parts ----------

def bm_box(mesh_bmesh, center: tuple, size: tuple) -> None:
    """Add an axis-aligned box to a bmesh (many small parts of one material become one object)."""
    made = bmesh.ops.create_cube(mesh_bmesh, size=1.0)

    bmesh.ops.scale(mesh_bmesh, vec=size, verts=made["verts"])
    bmesh.ops.translate(mesh_bmesh, vec=center, verts=made["verts"])


def bm_cylinder(mesh_bmesh, base_center: tuple, radius: float, height: float, sides: int, top_radius: float = None) -> None:
    made = bmesh.ops.create_cone(mesh_bmesh, cap_ends=True, segments=sides, radius1=radius, radius2=radius if top_radius is None else top_radius, depth=height)

    bmesh.ops.translate(mesh_bmesh, vec=(base_center[0], base_center[1], base_center[2] + height / 2.0), verts=made["verts"])


def bm_prism_yz(mesh_bmesh, x_center: float, thickness: float, points_yz: list) -> None:
    """Add a prism whose outline is drawn in the YZ plane, extruded along X by thickness."""
    face_vertices = [mesh_bmesh.verts.new((x_center - thickness / 2.0, y, z)) for y, z in points_yz]
    face = mesh_bmesh.faces.new(face_vertices)
    extruded = bmesh.ops.extrude_face_region(mesh_bmesh, geom=[face])
    moved = [element for element in extruded["geom"] if isinstance(element, bmesh.types.BMVert)]

    bmesh.ops.translate(mesh_bmesh, vec=(thickness, 0.0, 0.0), verts=moved)
    bmesh.ops.recalc_face_normals(mesh_bmesh, faces=mesh_bmesh.faces)


def make_lathe(name: str, center: tuple, profile_rz: list, sides: int, material, smooth: bool = True) -> bpy.types.Object:
    """Solid of revolution about a vertical axis from a (radius, height) profile listed bottom to top; the ends are capped."""
    lathe_bmesh = bmesh.new()
    rings = []

    for radius, height in profile_rz:
        rings.append([lathe_bmesh.verts.new((center[0] + radius * math.cos(2.0 * math.pi * segment / sides), center[1] + radius * math.sin(2.0 * math.pi * segment / sides), center[2] + height)) for segment in range(sides)])

    for lower, upper in zip(rings, rings[1:]):
        for segment in range(sides):
            following = (segment + 1) % sides
            lathe_bmesh.faces.new([lower[segment], lower[following], upper[following], upper[segment]])

    lathe_bmesh.faces.new(list(reversed(rings[0])))
    lathe_bmesh.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(lathe_bmesh, faces=lathe_bmesh.faces)

    for face in lathe_bmesh.faces:
        face.smooth = smooth

    return object_from_bmesh(name, lathe_bmesh, material)


def apse_point(radius: float, angle: float) -> tuple:
    """Plan point on the apse semicircle: angle 0 = +X side, pi/2 = on the axis (toward the apse back), pi = -X side."""
    return (radius * math.cos(angle), BODY_LENGTH + radius * math.sin(angle))


def make_arc_band(name: str, inner_radius: float, outer_radius: float, bottom: float, top: float, material, segments: int = 24) -> bpy.types.Object:
    """Half-ring wall band around the apse (a moulding, a painted frieze or a skin over the wall)."""
    angles = [math.pi * step / segments for step in range(segments + 1)]
    outline = [apse_point(outer_radius, angle) for angle in angles] + [apse_point(inner_radius, angle) for angle in reversed(angles)]

    return make_vertical_prism(name, outline, bottom, top - bottom, material)


def make_dome_shell(name: str, radius: float, bottom: float, rise: float, material, rings: int = 8, segments: int = 24) -> bpy.types.Object:
    """Half dome (flattened) over the apse; UV u runs across the half circle, v from the springing to the crown."""
    dome_bmesh = bmesh.new()
    uv_layer = dome_bmesh.loops.layers.uv.verify()
    grid = []
    vertex_uv = {}

    for ring_index in range(rings):
        elevation = (math.pi / 2.0) * ring_index / rings
        ring = []

        for segment in range(segments + 1):
            vertex = dome_bmesh.verts.new((*apse_point(radius * math.cos(elevation), math.pi * segment / segments), bottom + rise * math.sin(elevation)))
            vertex_uv[vertex] = (segment / segments, ring_index / rings)
            ring.append(vertex)

        grid.append(ring)

    crown = dome_bmesh.verts.new((0.0, BODY_LENGTH, bottom + rise))
    faces = []

    for ring_index in range(rings - 1):
        for segment in range(segments):
            faces.append(dome_bmesh.faces.new([grid[ring_index][segment], grid[ring_index][segment + 1], grid[ring_index + 1][segment + 1], grid[ring_index + 1][segment]]))

    for segment in range(segments):
        faces.append(dome_bmesh.faces.new([grid[-1][segment], grid[-1][segment + 1], crown]))
        vertex_uv[crown] = ((segment + 0.5) / segments, 1.0)

        for loop in faces[-1].loops:
            loop[uv_layer].uv = vertex_uv[loop.vert] if loop.vert is not crown else ((segment + 0.5) / segments, 1.0)

    for face in faces[: (rings - 1) * segments]:
        for loop in face.loops:
            loop[uv_layer].uv = vertex_uv[loop.vert]

    for face in dome_bmesh.faces:
        face.smooth = True

    bmesh.ops.recalc_face_normals(dome_bmesh, faces=dome_bmesh.faces)
    dome = object_from_bmesh(name, dome_bmesh, material)
    dome["keep_uvs"] = True

    return dome


def make_slope(name: str, start: tuple, end: tuple, width: float, thickness: float, material) -> bpy.types.Object:
    """Inclined slab between two (x, y, z) points on its top surface; the slab hangs below that line."""
    direction = Vector(end) - Vector(start)
    horizontal = math.hypot(direction.x, direction.y)
    pitch = math.atan2(direction.z, horizontal)
    yaw = math.atan2(direction.y, direction.x)
    slab = make_box(name, (0, 0, 0), (direction.length, width, thickness), material)

    slab.matrix_world = Matrix.Translation((Vector(start) + Vector(end)) / 2.0) @ Matrix.Rotation(yaw, 4, "Z") @ Matrix.Rotation(-pitch, 4, "Y") @ Matrix.Translation((0, 0, -thickness / 2.0))

    return slab


# ---------- reusable pieces ----------

def wall_opening(name: str, profile: list, position: tuple, facing: str, wall_depth: float, pane_material, cutters: list, pane_depth: float = 0.5) -> None:
    """Cut an opening through (or into) a wall and set a pane at pane_depth (0 = outer face, 1 = inner face)."""
    transform = facing_transform(position, facing)

    cutters.append(make_profile_prism(name + "_cut", profile, wall_depth + 0.4, transform @ Matrix.Translation((0, -0.2, 0)), None))

    if pane_material:
        make_profile_prism(name + "_pane", profile, 0.05, transform @ Matrix.Translation((0, wall_depth * pane_depth, 0)), pane_material)


def make_voussoirs(name: str, center: Vector, radius: float, start_angle: float, end_angle: float, count: int, radial_size: float, front_y: float, depth: float, material, frame: Matrix = None, ornament_material=None) -> None:
    """Ring of blocks around an arch in the local XZ plane, protruding toward local -Y.

    material may be a list to alternate colours; frame places the ring on a wall that is not the facade.
    ornament_material adds a small leaf (pointed lozenge with a midrib) on every block of the first colour.
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

        if ornament_material and block_index % len(block_materials) == 0:
            leaf_frame = frame @ Matrix.Translation(position - Vector((0.0, depth / 2.0, 0.0))) @ Matrix.Rotation(math.pi / 2.0 - angle, 4, "Y")
            leaf = make_box(f"{name}Leaf{block_index}", (0, 0, 0), (radial_size * 0.5, 0.03, radial_size * 0.5), ornament_material)
            leaf.matrix_world = leaf_frame @ Matrix.Diagonal((0.55, 1.0, 1.0, 1.0)) @ Matrix.Rotation(math.pi / 4.0, 4, "Y")
            midrib = make_box(f"{name}LeafRib{block_index}", (0, 0, 0), (0.035, 0.05, radial_size * 0.78), ornament_material)
            midrib.matrix_world = leaf_frame


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

    window_profile = round_arch_profile(AISLE_WINDOW[0], AISLE_WINDOW[1] - AISLE_WINDOW[0] / 2.0)

    for bay_y in BAY_CENTERS:
        window_position = (side_sign * HALF_WIDTH, bay_y, BASE + 2.2)
        wall_opening(f"AisleWindow{tag}{bay_y}", window_profile, window_position, facing, WALL, None, cutters)
        make_image_panel(f"AisleGlass{tag}{bay_y}", window_profile, AISLE_WINDOW, facing_transform(window_position, facing) @ Matrix.Translation((0, WALL / 2.0, 0)), materials["figure_glass"])
        make_span(f"AisleSill{tag}{bay_y}", (min(side_sign * (inner_x - 0.12), side_sign * inner_x), bay_y - AISLE_WINDOW[0] / 2.0 - 0.15, BASE + 2.05), (max(side_sign * (inner_x - 0.12), side_sign * inner_x), bay_y + AISLE_WINDOW[0] / 2.0 + 0.15, BASE + 2.2), materials["trim"])

    carve(wall, cutters)
    make_span(f"Wainscot{tag}", (min(side_sign * (inner_x - 0.05), side_sign * inner_x), NARTHEX_DEPTH, BASE), (max(side_sign * (inner_x - 0.05), side_sign * inner_x), BODY_LENGTH - WALL, BASE + 1.35), materials["pew_wood"])
    make_span(f"WainscotCap{tag}", (min(side_sign * (inner_x - 0.1), side_sign * inner_x), NARTHEX_DEPTH, BASE + 1.35), (max(side_sign * (inner_x - 0.1), side_sign * inner_x), BODY_LENGTH - WALL, BASE + 1.43), materials["gold"])
    build_side_altar(side_sign, materials)

    for fin_y in fin_positions:
        make_span(f"SideFin{tag}{fin_y}", (min(side_sign * HALF_WIDTH, side_sign * (HALF_WIDTH + 0.3)), fin_y - 0.4, BASE), (max(side_sign * HALF_WIDTH, side_sign * (HALF_WIDTH + 0.3)), fin_y + 0.4, BASE + AISLE_TOP + 0.25), materials["trim"])

    make_span(f"SideParapet{tag}", (min(side_sign * inner_x, side_sign * HALF_WIDTH), 2.0, BASE + AISLE_TOP), (max(side_sign * inner_x, side_sign * HALF_WIDTH), BODY_LENGTH, BASE + AISLE_TOP + 1.0), materials["wall"])
    make_span(f"SideCoping{tag}", (min(side_sign * (inner_x - 0.05), side_sign * (HALF_WIDTH + 0.1)), 2.0, BASE + AISLE_TOP + 1.0), (max(side_sign * (inner_x - 0.05), side_sign * (HALF_WIDTH + 0.1)), BODY_LENGTH + 0.1, BASE + AISLE_TOP + 1.15), materials["trim"])
    make_span(f"AisleRoof{tag}", (min(side_sign * NAVE_HALF, side_sign * inner_x), 1.0, BASE + AISLE_TOP), (max(side_sign * NAVE_HALF, side_sign * inner_x), BODY_LENGTH, BASE + AISLE_TOP + 0.4), materials["trim"])
    make_span(f"AisleBackWall{tag}", (min(side_sign * NAVE_HALF, side_sign * HALF_WIDTH), BODY_LENGTH - WALL, BASE), (max(side_sign * NAVE_HALF, side_sign * HALF_WIDTH), BODY_LENGTH, BASE + AISLE_TOP), materials["wall"])


def build_nave(materials: dict) -> None:
    """Arcade walls with round arches on round columns, clerestory slits, coffered ceiling and the tiled roof."""
    nave_roof_profile = [(-NAVE_HALF - 0.9, BASE + NAVE_WALL_TOP - 0.1), (0.0, BASE + NAVE_WALL_TOP + 2.2), (NAVE_HALF + 0.9, BASE + NAVE_WALL_TOP - 0.1)]
    coffer_ribs_y = [NARTHEX_DEPTH - 2.7 + 5.4 * rib_index for rib_index in range(7)]

    for side_sign, facing in ((-1, "-X"), (1, "+X")):
        build_arcade_wall(side_sign, facing, materials)

    for rib_y in coffer_ribs_y:
        make_span(f"CofferRibAcross{rib_y:.1f}", (-NAVE_HALF, rib_y - 0.25, BASE + NAVE_CEILING - 0.6), (NAVE_HALF, rib_y + 0.25, BASE + NAVE_CEILING), materials["trim"])

    for rib_x in (-2.25, 2.25):
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

    # The wall between two arches is cut away below the springing: the arcade stands on the free columns.
    cutters += [make_box(f"PierVoid{tag}{pier_y}", (side_sign * (NAVE_HALF + WALL / 2.0), pier_y, BASE + ARCH_SPRING / 2.0 - 0.1), (WALL + 0.4, PIER_Y[1] - PIER_Y[0] - ARCH_WIDTH + 0.04, ARCH_SPRING + 0.2), None) for pier_y in PIER_Y]

    carve(wall, cutters)

    for bay_y in BAY_CENTERS:
        frame = facing_transform((nave_face_x, bay_y, 0.0), nave_side_facing)
        make_voussoirs(f"ArchVoussoir{tag}{bay_y}", Vector((0, 0, BASE + ARCH_SPRING)), ARCH_WIDTH / 2.0, 0.0, math.pi, 11, 0.5, -0.12, 0.14, [materials["paint_red"], materials["trim"]], frame, materials["gold"])

    for pier_y in PIER_Y:
        build_column(side_sign * (NAVE_HALF + WALL / 2.0), pier_y, f"{tag}{pier_y}", materials)

    make_span(f"Frieze{tag}", (min(nave_face_x, nave_face_x - side_sign * 0.06), NARTHEX_DEPTH, BASE + 9.2), (max(nave_face_x, nave_face_x - side_sign * 0.06), BODY_LENGTH - WALL, BASE + 9.7), materials["paint_ochre"])


def build_side_altar(side_sign: int, materials: dict) -> None:
    """Small altar at the end of an aisle: marble table, gilded frontal and an arched niche with the saint painted in it."""
    tag = "L" if side_sign < 0 else "R"
    altar_x = side_sign * (NAVE_HALF + HALF_WIDTH) / 2.0
    wall_y = BODY_LENGTH - WALL
    niche_profile = round_arch_profile(1.3, 2.2)

    make_span(f"SideAltarStep{tag}", (altar_x - 1.3, wall_y - 1.5, BASE), (altar_x + 1.3, wall_y, BASE + 0.15), materials["marble"])
    make_span(f"SideAltarTable{tag}", (altar_x - 0.9, wall_y - 0.8, BASE + 0.15), (altar_x + 0.9, wall_y, BASE + 1.15), materials["marble"])
    make_span(f"SideAltarTop{tag}", (altar_x - 1.0, wall_y - 0.88, BASE + 1.15), (altar_x + 1.0, wall_y, BASE + 1.23), materials["trim"])
    make_span(f"SideAltarFrontal{tag}", (altar_x - 0.6, wall_y - 0.83, BASE + 0.35), (altar_x + 0.6, wall_y - 0.8, BASE + 0.95), materials["gold"])
    make_profile_prism(f"SideAltarNicheFrame{tag}", round_arch_profile(1.6, 2.3), 0.1, Matrix.Translation((altar_x, wall_y - 0.1, BASE + 1.5)), materials["gold"])
    make_image_panel(f"SideAltarPainting{tag}", niche_profile, (1.3, 2.85), Matrix.Translation((altar_x, wall_y - 0.12, BASE + 1.6)), materials["figure_painting"])

    for candle_sign in (-1, 1):
        make_cylinder(f"SideAltarCandle{tag}{candle_sign:+d}", (altar_x + candle_sign * 0.7, wall_y - 0.4, BASE + 1.23), 0.04, 0.45, 8, materials["gold"])
        make_cone(f"SideAltarFlame{tag}{candle_sign:+d}", (altar_x + candle_sign * 0.7, wall_y - 0.4, BASE + 1.68), 0.03, 0.09, 6, materials["lamp_glow"])


def make_fluted_shaft(name: str, center: tuple, bottom: float, height: float, radius: float, flutes: int, material) -> bpy.types.Object:
    """Column shaft with concave flutes and a slight taper toward the top."""
    shaft_bmesh = bmesh.new()
    segments = flutes * 4
    rings = []

    for rise, taper in ((0.0, 1.0), (0.5, 0.97), (1.0, 0.9)):
        ring = []

        for segment in range(segments):
            angle = 2.0 * math.pi * segment / segments
            fluted = radius * taper * (1.0 - 0.07 * (0.5 - 0.5 * math.cos(flutes * angle)))
            ring.append(shaft_bmesh.verts.new((center[0] + fluted * math.cos(angle), center[1] + fluted * math.sin(angle), bottom + height * rise)))

        rings.append(ring)

    for lower, upper in zip(rings, rings[1:]):
        for segment in range(segments):
            following = (segment + 1) % segments
            shaft_bmesh.faces.new([lower[segment], lower[following], upper[following], upper[segment]])

    return object_from_bmesh(name, shaft_bmesh, material)


def build_column(column_x: float, column_y: float, tag: str, materials: dict) -> None:
    """Fluted cream column on a moulded base, with a gilded capital of two rows of leaves under a square abacus."""
    capital_bottom = BASE + ARCH_SPRING - 0.75

    make_box(f"ColumnPlinth{tag}", (column_x, column_y, BASE + 0.15), (1.15, 1.15, 0.3), materials["trim"])
    make_cylinder(f"ColumnTorus{tag}", (column_x, column_y, BASE + 0.3), 0.54, 0.14, 20, materials["trim"])
    make_cylinder(f"ColumnScotia{tag}", (column_x, column_y, BASE + 0.44), 0.47, 0.08, 20, materials["trim"])
    make_fluted_shaft(f"ColumnShaft{tag}", (column_x, column_y), BASE + 0.52, capital_bottom - BASE - 0.52, 0.43, 14, materials["trim"])
    make_cylinder(f"ColumnNecking{tag}", (column_x, column_y, capital_bottom - 0.06), 0.43, 0.08, 20, materials["gold"])
    make_cone(f"ColumnBell{tag}", (column_x, column_y, capital_bottom), 0.4, 0.62, 16, materials["gold"], top_radius=0.6)
    make_box(f"ColumnAbacus{tag}", (column_x, column_y, BASE + ARCH_SPRING - 0.07), (1.25, 1.25, 0.14), materials["gold"])

    for leaf_row, leaf_index in itertools.product(range(len(CAPITAL_LEAF_ROWS)), range(CAPITAL_LEAVES)):
        row_height, row_radius, leaf_height = CAPITAL_LEAF_ROWS[leaf_row]
        angle = 2.0 * math.pi * (leaf_index + 0.5 * leaf_row) / CAPITAL_LEAVES
        make_acanthus_leaf(f"ColumnLeaf{tag}{leaf_row}{leaf_index}", (column_x, column_y, capital_bottom + row_height), angle, row_radius, leaf_height, materials["gold"])

    for corner_x, corner_y in itertools.product((-1, 1), (-1, 1)):
        volute = make_cylinder(f"ColumnVolute{tag}{corner_x:+d}{corner_y:+d}", (0, 0, -0.07), 0.13, 0.14, 12, materials["gold"])
        volute.matrix_world = Matrix.Translation((column_x + corner_x * 0.53, column_y + corner_y * 0.53, BASE + ARCH_SPRING - 0.25)) @ Matrix.Rotation(math.atan2(corner_y, corner_x) + math.pi / 2.0, 4, "Z") @ Matrix.Rotation(math.pi / 2.0, 4, "Y")

    build_sconce(tag, (column_x, column_y), materials)


def make_acanthus_leaf(name: str, capital_center: tuple, angle: float, radius: float, height: float, material) -> bpy.types.Object:
    """Leaf of a capital: a pointed blade standing against the bell, leaning out and curling over at the tip."""
    leaf_bmesh = bmesh.new()
    half_width = height * 0.36
    thickness = 0.035
    outline = [(0.55, 0.0, 0.0), (1.0, 0.45, 0.04), (0.7, 0.8, 0.14), (0.0, 1.0, 0.3)]  # (width, rise, lean outward), base to tip
    rows = []

    for width, rise, lean in outline:
        offsets = (-1.0, 0.0, 1.0) if width else (0.0,)
        rows.append([leaf_bmesh.verts.new((lean * height + (thickness if offset == 0.0 else 0.0), offset * width * half_width, rise * height - (0.12 * height if rise == 1.0 else 0.0))) for offset in offsets])

    for lower, upper in zip(rows, rows[1:]):
        for side in range(len(lower) - 1):
            upper_pair = [upper[min(side + 1, len(upper) - 1)], upper[min(side, len(upper) - 1)]]
            leaf_bmesh.faces.new(list(dict.fromkeys([lower[side], lower[side + 1], *upper_pair])))

    leaf = object_from_bmesh(name, leaf_bmesh, material)
    leaf.matrix_world = Matrix.Translation(capital_center) @ Matrix.Rotation(angle, 4, "Z") @ Matrix.Translation((radius, 0.0, 0.0))

    return leaf


def build_sconce(tag: str, column: tuple, materials: dict) -> None:
    """Lamp on a column, facing the nave: gilded band, arm and cup with a glowing globe."""
    toward_nave = -math.copysign(1.0, column[0])
    lamp_x = column[0] + toward_nave * 0.72

    make_cylinder(f"SconceBand{tag}", (column[0], column[1], BASE + SCONCE_HEIGHT - 0.05), 0.46, 0.1, 20, materials["gold"])
    make_box(f"SconceArm{tag}", (column[0] + toward_nave * 0.55, column[1], BASE + SCONCE_HEIGHT), (0.4, 0.05, 0.05), materials["gold"])
    make_cone(f"SconceCup{tag}", (lamp_x, column[1], BASE + SCONCE_HEIGHT), 0.05, 0.12, 10, materials["gold"], top_radius=0.12)
    make_sphere(f"SconceGlobe{tag}", (lamp_x, column[1], BASE + SCONCE_HEIGHT + 0.22), 0.13, materials["lamp_glow"])


def build_chandeliers(materials: dict) -> None:
    """Gilded ring chandeliers hanging on chains along the nave, eight glowing globes each."""
    ring_height = BASE + 8.2

    for chandelier_index, chandelier_y in enumerate(CHANDELIER_Y):
        tag = f"Chandelier{chandelier_index}"
        make_cylinder(f"{tag}Chain", (0, chandelier_y, ring_height + 0.5), 0.025, NAVE_CEILING - 8.7, 6, materials["gold"])
        make_cone(f"{tag}Crown", (0, chandelier_y, ring_height), 0.75, 0.5, 8, materials["gold"], top_radius=0.06)
        make_cylinder(f"{tag}Ring", (0, chandelier_y, ring_height - 0.08), 0.8, 0.08, 16, materials["gold"])
        make_sphere(f"{tag}Drop", (0, chandelier_y, ring_height - 0.25), 0.12, materials["gold"])

        for globe_index in range(8):
            angle = 2.0 * math.pi * globe_index / 8.0
            globe_spot = (0.8 * math.cos(angle), chandelier_y + 0.8 * math.sin(angle))
            make_cylinder(f"{tag}Cup{globe_index}", (*globe_spot, ring_height), 0.06, 0.06, 8, materials["gold"])
            make_sphere(f"{tag}Globe{globe_index}", (*globe_spot, ring_height + 0.17), 0.12, materials["lamp_glow"])


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
        make_image_panel(f"Painting{panel_x:+.1f}", rectangle_profile(panel_width, panel_height), (panel_width, panel_height), Matrix.Translation((panel_x, reredos_y - 0.09, floor_top + 1.6)), materials["figure_painting"])


def build_pews(materials: dict) -> None:
    """Two blocks of dark pews facing the altar (+Y), each with a kneeler behind its back for the next row."""
    rows = [PEW_ROWS[0] + row_index * 1.05 for row_index in range(int((PEW_ROWS[1] - PEW_ROWS[0]) / 1.05) + 1)]
    blocks = (-2.3, 2.3)
    pew_length = 2.6

    for block_x, row_y in itertools.product(blocks, rows):
        tag = f"{block_x:+.0f}_{row_y:.1f}"
        make_box(f"PewSeat{tag}", (block_x, row_y, BASE + 0.45), (pew_length, 0.45, 0.07), materials["pew_wood"])
        make_box(f"PewBack{tag}", (block_x, row_y - 0.24, BASE + 0.75), (pew_length, 0.07, 0.6), materials["pew_wood"])
        make_box(f"PewRail{tag}", (block_x, row_y - 0.24, BASE + 1.07), (pew_length + 0.1, 0.11, 0.05), materials["pew_wood"])
        make_box(f"PewKneeler{tag}", (block_x, row_y - 0.42, BASE + 0.14), (pew_length - 0.2, 0.16, 0.05), materials["pew_wood"])

        for end_sign in (-1, 1):
            end_x = block_x + end_sign * pew_length / 2.0
            make_box(f"PewEnd{tag}{end_sign:+d}", (end_x, row_y - 0.05, BASE + 0.5), (0.09, 0.62, 1.0), materials["pew_wood"])
            make_cylinder(f"PewEndKnob{tag}{end_sign:+d}", (end_x, row_y - 0.24, BASE + 1.0), 0.07, 0.12, 8, materials["pew_wood"])


STATUE_SOURCE = PROJECT_DIR / "art" / "characters" / "villager_male.gltf"  # CC0, montado por build_characters.py
STATUE_PARTS = ("Head", "Hair_Beard", "Hair_Buzzed", "Eyebrows", "Male_Peasant_Arms", "Male_Peasant_Body", "Male_Peasant_Feet")
MARY_SOURCE = PROJECT_DIR / "art" / "characters" / "villager_female.gltf"
MARY_PARTS = ("Head", "Eyebrows", "Female_Peasant_Arms", "Female_Peasant_Body", "Female_Peasant_Feet")
CHRIST_SOURCE = PROJECT_DIR / "tools" / "vendor" / "ubc" / "Universal Base Characters[Standard]" / "Base Characters" / "Godot - UE" / "Superhero_Male_FullBody.gltf"
CHRIST_HAIR_DIR = PROJECT_DIR / "tools" / "vendor" / "ubc" / "Universal Base Characters[Standard]" / "Hairstyles" / "Rigged to Head Bone" / "glTF (Godot -Unreal)"
CHRIST_HAIR = ("Hair_Long", "Hair_Beard", "Eyebrows_Regular")
STATUE_SCALE = 1.45
STATUE_SPOTS = [(-12.2, -2.4), (12.2, -2.4)]
PEDESTAL_HEIGHT = 2.8
STATUE_POSE = [  # (bone, world axis, degrees), applied in order: arms lowered, right hand to the chest, left hand forward on the staff
    ("upperarm_l", "Y", 74.0),
    ("upperarm_r", "Y", -70.0),
    ("lowerarm_r", "X", -118.0),
    ("lowerarm_r", "Z", 38.0),
    ("lowerarm_l", "X", -52.0),
    ("Head", "X", 9.0),
]
PRAYER_POSE = [  # hands joined at the chest, head slightly bowed
    ("upperarm_l", "Y", 74.0),
    ("upperarm_r", "Y", -70.0),
    ("lowerarm_r", "X", -118.0),
    ("lowerarm_r", "Z", 38.0),
    ("lowerarm_l", "X", -118.0),
    ("lowerarm_l", "Z", -38.0),
    ("Head", "X", 10.0),
]
CHRIST_POSE = [  # arms open a little above the horizontal, head fallen to the right shoulder, knees slightly bent
    ("upperarm_l", "Y", 14.0),
    ("upperarm_r", "Y", -14.0),
    ("lowerarm_l", "X", -8.0),
    ("lowerarm_r", "X", -8.0),
    ("thigh_l", "X", -10.0),
    ("thigh_r", "X", -10.0),
    ("calf_l", "X", 20.0),
    ("calf_r", "X", 20.0),
    ("Head", "X", 22.0),
    ("Head", "Z", 14.0),
]


def pose_bone_about_world_axis(armature, bone_name: str, axis: str, degrees: float) -> None:
    pose_bone = armature.pose.bones[bone_name]
    pivot = (armature.matrix_world @ pose_bone.matrix).to_translation()
    turn = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(degrees), 4, axis) @ Matrix.Translation(-pivot)

    pose_bone.matrix = armature.matrix_world.inverted() @ turn @ armature.matrix_world @ pose_bone.matrix
    bpy.context.view_layer.update()


def make_draped_cone(name: str, bottom: float, top: float, bottom_radius: float, top_radius: float, folds: int, fold_depth: float, material) -> bpy.types.Object:
    """Robe as a fluted, slightly flattened cone: the folds deepen toward the hem."""
    drape_bmesh = bmesh.new()
    segments = folds * 6
    ring_count = 7
    rings = []

    for ring_index in range(ring_count):
        rise = ring_index / (ring_count - 1)
        radius = bottom_radius + (top_radius - bottom_radius) * rise ** 0.8
        depth = fold_depth * (1.0 - rise) ** 1.5
        ring = []

        for segment in range(segments):
            angle = 2.0 * math.pi * segment / segments
            folded = radius + depth * math.cos(folds * angle + 0.6 * math.sin(3.0 * angle))
            ring.append(drape_bmesh.verts.new((folded * math.cos(angle), 0.72 * folded * math.sin(angle), bottom + (top - bottom) * rise)))

        rings.append(ring)

    for lower, upper in zip(rings, rings[1:]):
        for segment in range(segments):
            following = (segment + 1) % segments
            drape_bmesh.faces.new([lower[segment], lower[following], upper[following], upper[segment]])

    drape_bmesh.faces.new(rings[-1])

    for face in drape_bmesh.faces:
        face.smooth = True

    return object_from_bmesh(name, drape_bmesh, material)


def import_posed_meshes(source: Path, part_names: tuple, pose: list, name: str, material) -> tuple:
    """Import a rigged CC0 character, bend it into the pose, and return (carved copies of the named parts in one material,
    {bone name: posed world position}, {bone name: posed bone matrix (world)}, rest bone matrices (world))."""
    objects_before = set(bpy.data.objects)

    bpy.ops.import_scene.gltf(filepath=str(source))

    imported = list(set(bpy.data.objects) - objects_before)
    armature = next(scene_object for scene_object in imported if scene_object.type == "ARMATURE")
    rest_matrices = {bone.name: armature.matrix_world @ bone.matrix_local for bone in armature.data.bones}

    bpy.context.view_layer.update()

    for bone_name, axis, degrees in pose:
        pose_bone_about_world_axis(armature, bone_name, axis, degrees)

    depsgraph = bpy.context.evaluated_depsgraph_get()
    posed_matrices = {pose_bone.name: armature.matrix_world @ pose_bone.matrix for pose_bone in armature.pose.bones}
    bone_positions = {bone_name: matrix.to_translation() for bone_name, matrix in posed_matrices.items()}
    parts = []

    for part_name in part_names:
        posed = bpy.data.objects[part_name].evaluated_get(depsgraph)
        carved_mesh = bpy.data.meshes.new_from_object(posed)
        carved_mesh.transform(posed.matrix_world)
        carved_mesh.materials.clear()
        carved_mesh.materials.append(material)
        carved = bpy.data.objects.new(f"{name}{part_name}", carved_mesh)
        bpy.context.scene.collection.objects.link(carved)
        parts.append(carved)

    for scene_object in imported:
        bpy.data.objects.remove(scene_object, do_unlink=True)

    return parts, bone_positions, posed_matrices, rest_matrices


def build_robed_figure(name: str, source: Path, part_names: tuple, pose: list, material, tunic: bool = True, tunic_material=None) -> tuple:
    """Stone figure from a CC0 character: fixed pose, carved in one material and dressed in a fluted tunic.
    Returns (meshes standing at the origin facing -Y, {bone name: posed world position})."""
    figure, bone_positions, _, _ = import_posed_meshes(source, part_names, pose, name, material)

    if tunic:
        figure.append(make_draped_cone(f"{name}Tunic", 0.03, 1.4, 0.36, 0.17, 9, 0.035, tunic_material or material))

    return figure, bone_positions


def build_saint_figure(materials: dict, robe_key: str = "marble", staff: bool = True) -> list:
    """Robed saint carved in marble, with mantle, staff and halo. Meshes stand at the origin facing -Y, unscaled (1.8 m)."""
    figure, bones = build_robed_figure("Saint", STATUE_SOURCE, STATUE_PARTS, STATUE_POSE, materials["marble"], tunic_material=materials[robe_key])
    staff_hand = bones["hand_l"]
    head_top = bones["Head"]
    mantle = make_draped_cone("SaintMantle", 0.55, 1.52, 0.34, 0.19, 7, 0.03, materials[robe_key])

    mantle.data.transform(Matrix.Translation((0.0, 0.035, 0.0)))
    figure.append(mantle)

    if staff:
        figure.append(make_cylinder("SaintStaff", (staff_hand.x, staff_hand.y - 0.02, 0.0), 0.022, 1.95, 8, materials["marble"]))
        figure.append(make_sphere("SaintStaffBloom", (staff_hand.x, staff_hand.y - 0.02, 2.0), 0.075, materials["marble"]))

    figure.append(make_cylinder("SaintBase", (0, 0, -0.14), 0.5, 0.16, 20, materials["marble"]))
    figure.append(make_halo("SaintHalo", (0.0, head_top.y + 0.1, head_top.z + 0.14), 0.19, materials["gold"]))

    return figure


def build_mary_figure(materials: dict) -> list:
    """Our Lady: veiled head, blue mantle, hands joined at the chest. Meshes at the origin facing -Y, unscaled."""
    figure, bones = build_robed_figure("Mary", MARY_SOURCE, MARY_PARTS, PRAYER_POSE, materials["marble_white"], tunic_material=materials["marble_white"])
    head_top = bones["Head"]
    mantle = make_draped_cone("MaryMantle", 0.05, 1.5, 0.38, 0.2, 8, 0.035, materials["blue_robe"])
    veil = make_draped_cone("MaryVeil", 1.18, 1.76, 0.2, 0.125, 6, 0.012, materials["blue_robe"])

    mantle.data.transform(Matrix.Translation((0.0, 0.04, 0.0)))
    veil.data.transform(Matrix.Translation((0.0, 0.055, 0.0)))
    figure += [mantle, veil, make_cylinder("MaryBase", (0, 0, -0.14), 0.5, 0.16, 20, materials["marble_white"])]
    figure.append(make_halo("MaryHalo", (0.0, head_top.y + 0.1, head_top.z + 0.12), 0.19, materials["gold"]))

    return figure


def make_halo(name: str, center: tuple, radius: float, material) -> bpy.types.Object:
    """Thin golden ring tilted back like a halo."""
    halo_bmesh = bmesh.new()

    bmesh.ops.create_cone(halo_bmesh, cap_ends=False, segments=24, radius1=radius, radius2=radius, depth=0.02)
    halo = object_from_bmesh(name, halo_bmesh, material)
    halo.data.transform(Matrix.Translation(center) @ Matrix.Rotation(math.radians(80.0), 4, "X"))

    return halo


def make_torus(name: str, center: tuple, major_radius: float, minor_radius: float, material, major_segments: int = 24, minor_segments: int = 6) -> bpy.types.Object:
    """Horizontal torus (ring) around the given center."""
    torus_bmesh = bmesh.new()
    rings = []

    for major in range(major_segments):
        major_angle = 2.0 * math.pi * major / major_segments
        ring = []

        for minor in range(minor_segments):
            minor_angle = 2.0 * math.pi * minor / minor_segments
            radius = major_radius + minor_radius * math.cos(minor_angle)
            ring.append(torus_bmesh.verts.new((center[0] + radius * math.cos(major_angle), center[1] + radius * math.sin(major_angle), center[2] + minor_radius * math.sin(minor_angle))))

        rings.append(ring)

    for major in range(major_segments):
        following = (major + 1) % major_segments

        for minor in range(minor_segments):
            next_minor = (minor + 1) % minor_segments
            torus_bmesh.faces.new([rings[major][minor], rings[following][minor], rings[following][next_minor], rings[major][next_minor]])

    bmesh.ops.recalc_face_normals(torus_bmesh, faces=torus_bmesh.faces)

    return object_from_bmesh(name, torus_bmesh, material)


def build_christ_figure(materials: dict) -> tuple:
    """The crucified Christ carved in painted ivory: the base body of the CC0 characters posed with open arms, long hair and beard,
    loincloth, crown of thorns and halo. Meshes stand at the origin (soles at z = 0) facing -Y, unscaled (1.8 m).
    Returns (meshes, {bone name: posed world position})."""
    ivory = materials["ivory"]
    figure, bones, posed_matrices, rest_matrices = import_posed_meshes(CHRIST_SOURCE, ("SuperHero_Male",), CHRIST_POSE, "Christ", ivory)
    head_delta = posed_matrices["Head"] @ rest_matrices["Head"].inverted()

    for hair_name in CHRIST_HAIR:
        objects_before = set(bpy.data.objects)

        bpy.ops.import_scene.gltf(filepath=str(CHRIST_HAIR_DIR / f"{hair_name}.gltf"))

        imported = list(set(bpy.data.objects) - objects_before)
        depsgraph = bpy.context.evaluated_depsgraph_get()

        for hair_source in [scene_object for scene_object in imported if scene_object.type == "MESH" and scene_object.name.startswith(hair_name.split("_")[0])]:
            posed = hair_source.evaluated_get(depsgraph)
            hair_mesh = bpy.data.meshes.new_from_object(posed)

            hair_mesh.transform(head_delta @ posed.matrix_world)
            hair_mesh.materials.clear()
            hair_mesh.materials.append(materials["thorn"] if hair_name != "Eyebrows_Regular" else ivory)
            hair_object = bpy.data.objects.new(f"Christ{hair_name}", hair_mesh)
            bpy.context.scene.collection.objects.link(hair_object)
            figure.append(hair_object)

        for scene_object in imported:
            bpy.data.objects.remove(scene_object, do_unlink=True)

    head = bones["Head"]
    loincloth = make_draped_cone("ChristLoincloth", 0.80, 1.08, 0.235, 0.19, 9, 0.03, materials["linen"])
    knot = make_box("ChristLoinKnot", (0.2, -0.17, 0.99), (0.1, 0.07, 0.3), materials["linen"])
    crown = make_torus("ChristCrown", (head.x, head.y - 0.015, head.z + 0.17), 0.1, 0.014, materials["thorn"], 16, 5)
    aureole = make_halo("ChristAureole", (head.x, head.y + 0.13, head.z + 0.13), 0.21, materials["gold"])

    knot.rotation_euler.y = math.radians(-12.0)
    figure += [loincloth, knot, crown, aureole]

    for ray_index in range(3):
        ray = make_box(f"ChristRay{ray_index}", (0, 0, 0), (0.035, 0.012, 0.19), materials["gold"])
        ray.matrix_world = Matrix.Translation((head.x, head.y + 0.115, head.z + 0.13)) @ Matrix.Rotation(math.radians(ray_index * 120.0), 4, "Y") @ Matrix.Translation((0, 0, 0.09))
        figure.append(ray)

    for thorn_index in range(10):
        angle = 2.0 * math.pi * thorn_index / 10.0
        thorn = make_cone(f"ChristThorn{thorn_index}", (0, 0, 0), 0.012, 0.04, 5, materials["thorn"])
        thorn.matrix_world = Matrix.Translation((head.x + 0.105 * math.cos(angle), head.y - 0.015 + 0.105 * math.sin(angle), head.z + 0.17)) @ Matrix.Rotation(math.radians(55.0), 4, "Y") @ Matrix.Rotation(angle, 4, "Z")
        figure.append(thorn)

    for hand_name in ("hand_l", "hand_r"):
        nail = make_cylinder(f"ChristNail{hand_name}", (bones[hand_name].x, bones[hand_name].y + 0.0, bones[hand_name].z - 0.015), 0.012, 0.05, 6, materials["iron"])
        nail.data.transform(Matrix.Translation((0, 0, 0)))
        figure.append(nail)

    return figure, bones


def place_figure(parts: list, placement: Matrix, tag: str) -> list:
    """Copy the figure meshes to a place in the scene (placement may mirror: normals are flipped back)."""
    copies = []

    for part in parts:
        copy = bpy.data.objects.new(f"{part.name}{tag}", part.data.copy())

        copy.data.transform(placement)

        if placement.determinant() < 0.0:
            copy.data.flip_normals()

        bpy.context.scene.collection.objects.link(copy)
        copies.append(copy)

    return copies


def discard_figure(parts: list) -> None:
    for part in parts:
        bpy.data.objects.remove(part, do_unlink=True)


def build_pedestal(tag: str, center: tuple, materials: dict) -> None:
    """Tall pedestal: stepped base, plinth, dado with a framed bronze plaque on the front (-Y), cornice and cap."""
    x, y = center
    dado_bottom, dado_top = 0.5, PEDESTAL_HEIGHT - 0.35
    courses = [
        ("Step", 1.9, 0.0, 0.22, "stone"),
        ("Plinth", 1.55, 0.22, 0.5, "trim"),
        ("Dado", 1.2, dado_bottom, dado_top, "salmon"),
        ("Necking", 1.3, dado_top, dado_top + 0.08, "trim"),
        ("Cornice", 1.55, dado_top + 0.08, dado_top + 0.22, "trim"),
        ("Cap", 1.3, dado_top + 0.22, PEDESTAL_HEIGHT, "stone"),
    ]
    frame_bars = [((0.0, dado_top - 0.2), (0.86, 0.07)), ((0.0, dado_bottom + 0.2), (0.86, 0.07)), ((-0.4, (dado_bottom + dado_top) / 2.0), (0.07, dado_top - dado_bottom - 0.4)), ((0.4, (dado_bottom + dado_top) / 2.0), (0.07, dado_top - dado_bottom - 0.4))]

    for name, width, bottom, top, material_key in courses:
        make_span(f"Pedestal{name}{tag}", (x - width / 2.0, y - width / 2.0, bottom), (x + width / 2.0, y + width / 2.0, top), materials[material_key])

    for bar_index, ((offset_x, height), (size_x, size_z)) in enumerate(frame_bars):
        make_box(f"PedestalFrame{tag}{bar_index}", (x + offset_x, y - 0.62, height), (size_x, 0.05, size_z), materials["trim"])

    make_box(f"PedestalPlaque{tag}", (x, y - 0.61, (dado_bottom + dado_top) / 2.0 + 0.1), (0.52, 0.03, 0.36), materials["gold"])


def build_statues(materials: dict, saint: list) -> None:
    """Two robed saints on tall pedestals flanking the stairs, facing the forecourt."""
    for spot_index, (statue_x, statue_y) in enumerate(STATUE_SPOTS):
        tag = "LR"[spot_index]
        mirror = Matrix.Scale(-1.0 if spot_index else 1.0, 4, (1, 0, 0))
        placement = Matrix.Translation((statue_x, statue_y, PEDESTAL_HEIGHT + 0.14 * STATUE_SCALE)) @ mirror @ Matrix.Scale(STATUE_SCALE, 4)

        build_pedestal(tag, (statue_x, statue_y), materials)
        place_figure(saint, placement, f"Facade{tag}")


# ---------- collision ----------

def make_stair_ramp(name: str, width: float, first_step_front: float, step_count: int, tread: float, rise: float, bottom: float, landing_length: float = 0.0) -> None:
    """Ramp collider touching every step nosing (feet never sink into a tread), from the floor one tread
    before the first step up to the last nosing, plus a flat landing over the top tread. The box is built
    at the origin and then placed, so its rotation turns about its own center."""
    ramp_start = first_step_front - tread
    ramp_end = first_step_front + (step_count - 1) * tread
    ramp_top = bottom + step_count * rise
    slope = math.atan2(ramp_top - bottom, ramp_end - ramp_start)
    thickness = 0.1
    ramp = make_box(f"{name}-colonly", (0, 0, 0), (width, math.hypot(ramp_end - ramp_start, ramp_top - bottom), thickness), None)

    ramp.location = (0, (ramp_start + ramp_end) / 2.0 + math.sin(slope) * thickness / 2.0, (bottom + ramp_top) / 2.0 - math.cos(slope) * thickness / 2.0)
    ramp.rotation_euler.x = slope
    make_span(f"{name}Landing-colonly", (-width / 2.0, ramp_end, ramp_top - thickness), (width / 2.0, ramp_end + (landing_length or tread), ramp_top), None)


def build_colliders() -> None:
    """Simple boxes for the player and the navmesh; names ending in -colonly become static bodies in Godot."""
    make_stair_ramp("Stairs", 18.0, -STEP_COUNT * STEP_TREAD, STEP_COUNT, STEP_TREAD, STEP_RISE, 0.0)
    make_stair_ramp("ChancelSteps", 7.2, CHANCEL_FRONT - 5 * 0.4, 5, 0.4, CHANCEL_HEIGHT / 5, BASE)

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
    make_mirrored_span("Pews-colonly", (1.0, PEW_ROWS[0] - 0.5, BASE), (3.6, PEW_ROWS[1] + 0.5, BASE + 1.0), None)
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
        make_box(f"Statue{side_sign:+d}-colonly", (side_sign * 9.6, -2.0, 2.4), (1.6, 1.6, 4.8), None)


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

    for mesh_object in [mesh_object for mesh_object in visible_meshes if not mesh_object.get("keep_uvs")]:
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
    build_chandeliers(materials)
    build_statues(materials)
    build_colliders()
    finalize_objects(materials)

    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_texture_dir="textures", export_yup=True)

    return output_path


if __name__ == "__main__":
    print(f"BUILT cathedral -> {build_cathedral()}")
