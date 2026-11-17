"""Plants of the farm (coffee, corn, sugar cane, cassava, cabbage, carrot, grass and straw tufts) for build_farm.py.

Two pieces keep a field of thousands of plants cheap:
  * one alpha-cut atlas painted here (T_FarmCrops_BaseColor.png): the fine detail of a plant (leaf veins, tassel
    spikelets, lacy carrot fronds) lives in the texture, on a few bent cards;
  * numpy instancing: each plant is modelled once as a Shape (vertices, UVs, triangles) and stamped all over
    the plot with one matrix per plant; a batch becomes one mesh per (material, tint).

Solid parts (stalks, corn husks, cabbage heads, carrot shoulders) are small lathes on the vertex-colour paint
material. Blender coords: X = Godot X, Y = -Godot Z, Z up.
"""

import itertools
import math
import random
from pathlib import Path
from typing import NamedTuple

import bpy
import numpy

ATLAS_SIZE = (1024, 512)  # largura, altura em pixels
SUPERSAMPLE = 2
ATLAS_NAME = "T_FarmCrops_BaseColor"
HAY_NAME = "T_FarmHay_BaseColor"
HAY_SIZE = 512
REGIONS = {  # nome -> (x0, y0, x1, y1) em pixels do atlas, y de baixo para cima
    "tassel": (0, 208, 256, 464),
    "tuft": (256, 208, 512, 464),
    "cabbage": (512, 208, 768, 464),
    "carrot": (768, 208, 1024, 464),
    "corn_leaf": (0, 96, 640, 208),
}
CROP_MATERIAL = "crops"
PAINT_MATERIAL = "paint"
UV_LAYER = "Float2"  # nome que bmesh dá à camada das outras peças do Builder; o join funde as camadas pelo nome

CORN_STALK = "8FAE52"
CORN_HUSK = "B4CF74"
CORN_SILK = "A85A34"
CORN_LEAF_TINTS = ("FFFFFF", "E4F0C8")
CABBAGE_HEAD = "C9E39A"
CABBAGE_OUTER_TINTS = ("7FB094", "8FBF8A")
CABBAGE_INNER = "F4FFD8"
COFFEE_LEAF_TINTS = ("2C6A38", "357642", "265E32")
COFFEE_CHERRY = "C23A2E"
CANE_STALK_TINTS = ("8DB04A", "A58A3C", "7FA43E")
CANE_LEAF_TINTS = ("FFFFFF", "DDEBB0")
CASSAVA_STEM = "A9754E"
CASSAVA_LEAF_TINTS = ("C4E8A0", "A9DB86")
CARROT_ROOT = "E8822E"
CARROT_TINTS = ("FFFFFF", "DDF0C4")
MEADOW_TINTS = ("8FC462", "A9D070", "79B356")
STRAW_TINTS = ("F0D58A", "DDBB62", "F7E4A6")


def rgb(hex_color: str) -> numpy.ndarray:
    return numpy.array([int(hex_color[index:index + 2], 16) / 255.0 for index in (0, 2, 4)], dtype=numpy.float32)


def mix(first: str, second: str, amount: float) -> numpy.ndarray:
    return rgb(first) * (1.0 - amount) + rgb(second) * amount


# ---------- painting: a tiny polygon rasterizer ----------

class Canvas:
    """sRGB picture with alpha, painted with filled polygons at SUPERSAMPLE and averaged down in finish()."""

    def __init__(self, width: int, height: int, base_color: str) -> None:
        self.size = (width * SUPERSAMPLE, height * SUPERSAMPLE)
        self.color = numpy.empty((self.size[1], self.size[0], 3), dtype=numpy.float32)
        self.color[:] = rgb(base_color)
        self.alpha = numpy.zeros((self.size[1], self.size[0]), dtype=numpy.float32)

    def polygon(self, points, color: numpy.ndarray) -> None:
        """Fill by winding number (a stroke folding over itself stays solid)."""
        corners = numpy.asarray(points, dtype=numpy.float32) * SUPERSAMPLE
        low = numpy.clip(numpy.floor(corners.min(axis=0)).astype(int), 0, self.size)
        high = numpy.clip(numpy.ceil(corners.max(axis=0)).astype(int) + 1, 0, self.size)

        if high[0] <= low[0] or high[1] <= low[1]:
            return

        x = (numpy.arange(low[0], high[0]) + 0.5)[None, None, :]
        y = (numpy.arange(low[1], high[1]) + 0.5)[None, :, None]
        start, end = corners[:, :, None, None], numpy.roll(corners, -1, axis=0)[:, :, None, None]
        side = (end[:, 0] - start[:, 0]) * (y - start[:, 1]) - (x - start[:, 0]) * (end[:, 1] - start[:, 1])
        upward = (start[:, 1] <= y) & (end[:, 1] > y) & (side > 0.0)
        downward = (start[:, 1] > y) & (end[:, 1] <= y) & (side < 0.0)
        inside = upward.sum(axis=0) != downward.sum(axis=0)

        self.color[low[1]:high[1], low[0]:high[0]][inside] = color
        self.alpha[low[1]:high[1], low[0]:high[0]][inside] = 1.0

    def stroke(self, points, widths, color: numpy.ndarray) -> None:
        """Polyline with a width per point (tapering blades, stems, veins)."""
        path = numpy.asarray(points, dtype=numpy.float32)
        tangent = numpy.gradient(path, axis=0)
        normal = numpy.stack([-tangent[:, 1], tangent[:, 0]], axis=1)
        normal /= numpy.maximum(numpy.linalg.norm(normal, axis=1, keepdims=True), 1e-6)
        half = (numpy.broadcast_to(numpy.asarray(widths, dtype=numpy.float32), (len(path),)) / 2.0)[:, None]

        self.polygon(numpy.concatenate([path + normal * half, (path - normal * half)[::-1]]), color)

    def ellipse(self, center, radii: tuple, heading: float, color: numpy.ndarray) -> None:
        """Ellipse whose long radius (radii[1]) points along heading (degrees from up, clockwise)."""
        angles = numpy.linspace(0.0, 2.0 * math.pi, 12, endpoint=False)
        local = numpy.stack([numpy.cos(angles) * radii[0], numpy.sin(angles) * radii[1]], axis=1)
        turn = math.radians(-heading)
        rotation = numpy.array([[math.cos(turn), -math.sin(turn)], [math.sin(turn), math.cos(turn)]], dtype=numpy.float32)

        self.polygon(local @ rotation.T + numpy.asarray(center, dtype=numpy.float32), color)

    def finish(self) -> numpy.ndarray:
        """RGBA at the final size; the colour of see-through pixels stays the base colour (no dark fringe)."""
        height, width = self.size[1] // SUPERSAMPLE, self.size[0] // SUPERSAMPLE
        alpha_blocks = self.alpha.reshape(height, SUPERSAMPLE, width, SUPERSAMPLE)
        color_blocks = self.color.reshape(height, SUPERSAMPLE, width, SUPERSAMPLE, 3)
        coverage = alpha_blocks.mean(axis=(1, 3))
        weight = numpy.where(alpha_blocks.sum(axis=(1, 3), keepdims=True) > 0.0, alpha_blocks, 1.0)[..., None]
        color = (color_blocks * weight).sum(axis=(1, 3)) / weight.sum(axis=(1, 3))

        return numpy.concatenate([color, coverage[..., None]], axis=-1)


def arc_points(start, heading: float, length: float, bend: float, steps: int = 8) -> numpy.ndarray:
    """2D curve leaving start at heading (degrees from up, clockwise) and turning bend degrees along its length."""
    headings = numpy.radians(heading + bend * (numpy.arange(steps) + 0.5) / steps)
    deltas = numpy.stack([numpy.sin(headings), numpy.cos(headings)], axis=1) * (length / steps)

    return numpy.concatenate([[start], numpy.asarray(start) + numpy.cumsum(deltas, axis=0)]).astype(numpy.float32)


def heading_at(path: numpy.ndarray, index: int) -> float:
    delta = path[min(index + 1, len(path) - 1)] - path[max(index - 1, 0)]

    return math.degrees(math.atan2(delta[0], delta[1]))


def offset(point, heading: float, distance: float) -> numpy.ndarray:
    return numpy.asarray(point) + numpy.array([math.sin(math.radians(heading)), math.cos(math.radians(heading))]) * distance


def paint_corn_leaf() -> numpy.ndarray:
    """Long corn blade, base at the left: wavy edge, pale midrib, parallel veins, the lower half in shade."""
    width, height = REGIONS["corn_leaf"][2] - REGIONS["corn_leaf"][0], REGIONS["corn_leaf"][3] - REGIONS["corn_leaf"][1]
    canvas = Canvas(width, height, "86B552")
    along = numpy.linspace(0.0, 1.0, 56)
    profile = along ** 0.38 * (1.0 - along) ** 0.72
    half = (height / 2.0 - 7.0) * profile / profile.max()
    x = 4.0 + along * (width - 8.0)
    wave = 3.2 * numpy.sin(along * 34.0) * profile / profile.max()
    middle = numpy.stack([x, numpy.full_like(x, height / 2.0) + wave * 0.4], axis=1)
    upper, lower = middle + numpy.stack([numpy.zeros_like(x), half + wave], axis=1), middle - numpy.stack([numpy.zeros_like(x), half - wave], axis=1)

    canvas.polygon(numpy.concatenate([upper, lower[::-1]]), rgb("8FC258"))
    canvas.polygon(numpy.concatenate([middle, lower[::-1]]), rgb("76AA48"))

    for share in (-0.72, -0.4, 0.4, 0.72):
        canvas.stroke(middle + numpy.stack([numpy.zeros_like(x), half * share], axis=1), 1.6, rgb("5F9140") if share < 0 else rgb("A6D46C"))

    canvas.stroke(middle, numpy.linspace(6.5, 1.6, len(x)), rgb("D8EBA4"))

    return canvas.finish()


def paint_spikelets(canvas: Canvas, path: numpy.ndarray, generator: random.Random) -> None:
    for index in range(1, len(path)):
        side = 1.0 if index % 2 else -1.0
        along = heading_at(path, index)
        canvas.ellipse(offset(path[index], along + side * 90.0, 3.0), (3.0, 6.4), along + side * 28.0, mix("B8964A", "EDD68C", generator.random()))


def paint_tassel(generator: random.Random) -> numpy.ndarray:
    """Corn tassel: a central spike and arching side branches strung with golden spikelets."""
    canvas = Canvas(256, 256, "D8C070")
    spike = arc_points((128.0, 0.0), 0.0, 246.0, generator.uniform(-6.0, 6.0), 26)

    for index in range(11):
        side = 1.0 if index % 2 else -1.0
        branch = arc_points(spike[2 + index], side * generator.uniform(28.0, 55.0), generator.uniform(105.0, 165.0), side * generator.uniform(25.0, 65.0), 16)
        canvas.stroke(branch, numpy.linspace(3.0, 1.8, len(branch)), rgb("B9A45E"))
        paint_spikelets(canvas, branch[2:], generator)

    canvas.stroke(spike, numpy.linspace(6.0, 2.0, len(spike)), rgb("B9B062"))
    paint_spikelets(canvas, spike[8:], generator)

    return canvas.finish()


def paint_tuft(generator: random.Random) -> numpy.ndarray:
    """Fan of blades in near-white: the vertex colour makes it meadow grass, straw or corn silk."""
    canvas = Canvas(256, 256, "E6E6E6")

    for _ in range(19):
        lean = generator.uniform(-42.0, 42.0)
        blade = arc_points((128.0 + lean * 0.5 + generator.uniform(-8.0, 8.0), 0.0), lean * 0.6, generator.uniform(140.0, 246.0), lean * generator.uniform(0.3, 1.1), 8)
        canvas.stroke(blade, numpy.linspace(10.0, 1.6, len(blade)), mix("BEBEBE", "FFFFFF", generator.random()))

    return canvas.finish()


def paint_cabbage_leaf(generator: random.Random) -> numpy.ndarray:
    """Round cabbage leaf, stalk at the bottom: frilled rim, thick pale midrib and branching veins."""
    canvas = Canvas(256, 256, "A9D488")
    angles = numpy.linspace(0.0, 2.0 * math.pi, 90, endpoint=False)
    frill = 1.0 + 0.04 * numpy.sin(angles * 11.0) + 0.025 * numpy.sin(angles * 23.0 + 1.0)
    rim = numpy.stack([128.0 + 116.0 * numpy.sin(angles) * frill, 130.0 - 122.0 * numpy.cos(angles) * frill], axis=1)
    midrib = arc_points((128.0, 6.0), 0.0, 222.0, generator.uniform(-5.0, 5.0), 12)

    canvas.polygon(rim, rgb("8CBF6E"))
    canvas.polygon((rim - (128.0, 130.0)) * 0.9 + (128.0, 130.0), rgb("A9D488"))
    canvas.polygon((rim - (128.0, 130.0)) * 0.55 + (128.0, 120.0), rgb("B7DE96"))

    for index, side in itertools.product(range(2, 11, 2), (-1.0, 1.0)):
        vein = arc_points(midrib[index], side * (62.0 - index * 2.5), 96.0 - index * 5.0, -side * 24.0, 6)
        canvas.stroke(vein, numpy.linspace(4.6, 1.4, len(vein)), rgb("E2F2C6"))
        canvas.stroke(arc_points(vein[3], heading_at(vein, 3) + side * 38.0, 30.0, 0.0, 2), (2.4, 1.8, 1.2), rgb("E2F2C6"))
        canvas.stroke(arc_points(vein[4], heading_at(vein, 4) - side * 34.0, 24.0, 0.0, 2), (2.2, 1.6, 1.2), rgb("E2F2C6"))

    canvas.stroke(midrib, numpy.linspace(11.0, 2.4, len(midrib)), rgb("EEF8D8"))

    return canvas.finish()


def paint_pinna(canvas: Canvas, pinna: numpy.ndarray, side: float, generator: random.Random) -> None:
    canvas.stroke(pinna, numpy.linspace(3.0, 1.4, len(pinna)), rgb("5FA04A"))

    for index, leaflet_side in itertools.product(range(1, len(pinna)), (-1.0, 1.0)):
        reach = (9.0 + 15.0 * (1.0 - index / len(pinna))) * generator.uniform(0.8, 1.2)
        leaflet = arc_points(pinna[index], heading_at(pinna, index) + leaflet_side * 48.0, reach, -leaflet_side * 20.0, 3)
        canvas.stroke(leaflet, (5.4, 6.4, 4.0, 1.2), mix("62AB4E", "92D074", generator.random()))


def paint_carrot_frond(generator: random.Random) -> numpy.ndarray:
    """Feathery carrot leaf: a slender stalk, opposite pinnae getting shorter to the tip, each cut into leaflets."""
    canvas = Canvas(256, 256, "74B85C")
    stalk = arc_points((128.0, 0.0), 0.0, 246.0, generator.uniform(-8.0, 8.0), 13)

    for index, side in itertools.product(range(3, 13), (-1.0, 1.0)):
        reach = 124.0 * (1.0 - (index - 3) / 12.5) * generator.uniform(0.85, 1.1)
        pinna = arc_points(stalk[index], heading_at(stalk, index) + side * generator.uniform(48.0, 62.0), reach, -side * 16.0, max(3, int(reach / 13.0)))
        paint_pinna(canvas, pinna, side, generator)

    paint_pinna(canvas, stalk[10:], 1.0, generator)
    canvas.stroke(stalk, numpy.linspace(4.6, 1.6, len(stalk)), rgb("6CAE52"))

    return canvas.finish()


def paint_hay(generator: random.Random) -> numpy.ndarray:
    """Tileable packed hay: straws lying mostly one way, every straw also drawn wrapped across the borders."""
    canvas = Canvas(HAY_SIZE, HAY_SIZE, "D2AE5C")
    canvas.alpha[:] = 1.0
    shades = ("F2D88E", "C39A4A", "E6C674", "AD8438", "F8E6AA", "D9B868")
    wraps = [numpy.array(shift, dtype=numpy.float32) for shift in itertools.product((0.0, -HAY_SIZE), repeat=2)]

    for _ in range(2600):
        heading = 90.0 + (generator.uniform(-22.0, 22.0) if generator.random() < 0.82 else generator.uniform(-90.0, 90.0))
        straw = arc_points((generator.uniform(0.0, HAY_SIZE), generator.uniform(0.0, HAY_SIZE)), heading, generator.uniform(30.0, 120.0), generator.uniform(-25.0, 25.0), 4)
        shade = rgb(generator.choice(shades))
        thickness = generator.uniform(1.8, 4.2)

        for shift in wraps:
            canvas.stroke(straw + shift, thickness, shade)

    return canvas.finish()


def save_texture(name: str, pixels: numpy.ndarray, directory: Path) -> Path:
    """Write RGBA pixels as a PNG (image.save() stores the float buffer as it is, so the values are sRGB)."""
    target = directory / f"{name}.png"
    height, width = pixels.shape[:2]
    image = bpy.data.images.new(name, width, height, alpha=True)

    image.pixels.foreach_set(pixels.astype(numpy.float32).ravel())
    image.filepath_raw = str(target)
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)

    return target


def crop_atlas(directory: Path, seed: int) -> Path:
    """Paint every region of the crop atlas (deterministic: the same seed writes the same file)."""
    generator = random.Random(seed)
    atlas = numpy.zeros((ATLAS_SIZE[1], ATLAS_SIZE[0], 4), dtype=numpy.float32)
    atlas[..., :3] = rgb("B9C46A")
    painted = {
        "tassel": paint_tassel(generator),
        "tuft": paint_tuft(generator),
        "cabbage": paint_cabbage_leaf(generator),
        "carrot": paint_carrot_frond(generator),
        "corn_leaf": paint_corn_leaf(),
    }

    for name, picture in painted.items():
        x0, y0, x1, y1 = REGIONS[name]
        atlas[y0:y1, x0:x1] = picture

    return save_texture(ATLAS_NAME, atlas, directory)


def hay_texture(directory: Path, seed: int) -> Path:
    return save_texture(HAY_NAME, paint_hay(random.Random(seed)), directory)


# ---------- shapes: a plant modelled once ----------

class Shape(NamedTuple):
    vertices: numpy.ndarray  # (n, 3)
    uvs: numpy.ndarray  # (n, 2)
    triangles: numpy.ndarray  # (t, 3)


def merged(shapes: list) -> Shape:
    offsets = numpy.cumsum([0] + [len(shape.vertices) for shape in shapes[:-1]])

    return Shape(
        numpy.concatenate([shape.vertices for shape in shapes]),
        numpy.concatenate([shape.uvs for shape in shapes]),
        numpy.concatenate([shape.triangles + start for shape, start in zip(shapes, offsets)]),
    )


def moved(shape: Shape, matrix: numpy.ndarray) -> Shape:
    return Shape(shape.vertices @ matrix[:3, :3].T + matrix[:3, 3], shape.uvs, shape.triangles)


def transforms(points, yaws=0.0, tilts=0.0, scales=1.0, heights=None) -> numpy.ndarray:
    """One 4x4 per point: scale (uniform, or `heights` for Z), lean around local X, turn around Z, move. Degrees."""
    points = numpy.atleast_2d(numpy.asarray(points, dtype=numpy.float64))
    count = len(points)
    yaw, tilt = numpy.radians(numpy.broadcast_to(yaws, (count,))), numpy.radians(numpy.broadcast_to(tilts, (count,)))
    scale = numpy.broadcast_to(scales, (count,))
    height = scale if heights is None else numpy.broadcast_to(heights, (count,))
    cos_yaw, sin_yaw, cos_tilt, sin_tilt = numpy.cos(yaw), numpy.sin(yaw), numpy.cos(tilt), numpy.sin(tilt)
    matrices = numpy.zeros((count, 4, 4))

    matrices[:, 0, 0], matrices[:, 0, 1], matrices[:, 0, 2] = cos_yaw * scale, -sin_yaw * cos_tilt * scale, sin_yaw * sin_tilt * height
    matrices[:, 1, 0], matrices[:, 1, 1], matrices[:, 1, 2] = sin_yaw * scale, cos_yaw * cos_tilt * scale, -cos_yaw * sin_tilt * height
    matrices[:, 2, 1], matrices[:, 2, 2] = sin_tilt * scale, cos_tilt * height
    matrices[:, :3, 3] = points
    matrices[:, 3, 3] = 1.0

    return matrices


def transform(point=(0.0, 0.0, 0.0), yaw: float = 0.0, tilt: float = 0.0, scale: float = 1.0) -> numpy.ndarray:
    return transforms([point], yaw, tilt, scale)[0]


def arc_path(length: float, lift: float, droop: float, steps: int) -> numpy.ndarray:
    """3D curve in the local YZ plane: leaves the origin `lift` degrees above the horizon (toward +Y) and
    drops `droop` degrees along its length (negative droop curls it upward and back)."""
    elevations = numpy.radians(lift - droop * (numpy.arange(steps) + 0.5) / steps)
    deltas = numpy.stack([numpy.zeros(steps), numpy.cos(elevations), numpy.sin(elevations)], axis=1) * (length / steps)

    return numpy.concatenate([numpy.zeros((1, 3)), numpy.cumsum(deltas, axis=0)])


def ribbon(path, width, region: str, along: str = "v", cup: float = 0.0, columns: int = 2, side=(1.0, 0.0, 0.0), span: tuple = (0.0, 1.0)) -> Shape:
    """Card following a path, `width` across (along `side`); the atlas region runs base to tip along `along`
    ("v": bottom to top, "u": left to right) and `span` picks a slice of it across. cup lifts the edges."""
    path = numpy.asarray(path, dtype=numpy.float64)
    side = numpy.asarray(side, dtype=numpy.float64)
    rows = len(path)
    across = numpy.linspace(-0.5, 0.5, columns)
    tangent = numpy.gradient(path, axis=0)
    normal = numpy.cross(tangent, side)
    normal /= numpy.maximum(numpy.linalg.norm(normal, axis=1, keepdims=True), 1e-9)
    widths = numpy.broadcast_to(width, (rows,))[:, None, None]
    vertices = path[:, None, :] + side * across[None, :, None] * widths + normal[:, None, :] * (cup * (2.0 * across[None, :, None]) ** 2) * widths
    x0, y0, x1, y1 = [(edge + inset) / ATLAS_SIZE[axis % 2] for axis, (edge, inset) in enumerate(zip(REGIONS[region], (1.5, 1.5, -1.5, -1.5)))]
    lengthwise = numpy.repeat(numpy.linspace(0.0, 1.0, rows), columns)
    crosswise = numpy.tile(span[0] + (across + 0.5) * (span[1] - span[0]), rows)
    uvs = {
        "v": numpy.stack([x0 + crosswise * (x1 - x0), y0 + lengthwise * (y1 - y0)], axis=1),
        "u": numpy.stack([x0 + lengthwise * (x1 - x0), y0 + crosswise * (y1 - y0)], axis=1),
    }[along]
    corner = (numpy.arange(rows - 1)[:, None] * columns + numpy.arange(columns - 1)[None, :]).ravel()
    triangles = numpy.concatenate([numpy.stack([corner, corner + 1, corner + columns + 1], axis=1), numpy.stack([corner, corner + columns + 1, corner + columns], axis=1)])

    return Shape(vertices.reshape(-1, 3), uvs, triangles)


def crossed_cards(region: str, width: float, height: float, count: int = 2, lean: float = 0.0) -> Shape:
    """`count` upright cards through the same axis, turned evenly (a tuft seen from any side)."""
    path = [(0.0, 0.0, 0.0), (0.0, lean, height)]

    return merged([moved(ribbon(path, width, region), transform(yaw=180.0 * index / count)) for index in range(count)])


def lathe_shape(profile: list, sides: int) -> Shape:
    """Solid of revolution around Z from [(radius, z), ...] bottom to top, open at both ends (tips close on a
    tiny radius). Faces wind outward; UVs are unused by the paint material."""
    angles = 2.0 * math.pi * numpy.arange(sides) / sides
    radii, heights = numpy.array(profile, dtype=numpy.float64).T
    rings = len(profile)
    vertices = numpy.stack([radii[:, None] * numpy.cos(angles), radii[:, None] * numpy.sin(angles), numpy.broadcast_to(heights[:, None], (rings, sides))], axis=-1)
    ring, step = numpy.meshgrid(numpy.arange(rings - 1), numpy.arange(sides), indexing="ij")
    lower, lower_next = (ring * sides + step).ravel(), (ring * sides + (step + 1) % sides).ravel()
    triangles = numpy.concatenate([numpy.stack([lower, lower_next, lower_next + sides], axis=1), numpy.stack([lower, lower_next + sides, lower + sides], axis=1)])

    return Shape(vertices.reshape(-1, 3), numpy.zeros((rings * sides, 2)), triangles)


# ---------- batch: one mesh per (material, tint) ----------

class PlantBatch:
    """Collects stamped shapes and hands the Builder one object per (material, tint)."""

    def __init__(self, builder, to_linear) -> None:
        self.builder = builder
        self.to_linear = to_linear  # hex sRGB -> tinta linear do Builder
        self.parts = {}

    def stamp(self, shape: Shape, matrices: numpy.ndarray, tint: str, material: str = CROP_MATERIAL, frame=None) -> None:
        """Copy the shape once per matrix; frame (a mathutils Matrix) places the whole lot."""
        matrices = numpy.asarray(matrices, dtype=numpy.float64).reshape(-1, 4, 4)

        if len(matrices) == 0:
            return

        if frame is not None:
            matrices = numpy.array(frame) @ matrices

        vertices = numpy.einsum("kij,nj->kni", matrices[:, :3, :3], shape.vertices) + matrices[:, None, :3, 3]
        triangles = shape.triangles[None, :, :] + (numpy.arange(len(matrices)) * len(shape.vertices))[:, None, None]

        self.parts.setdefault((material, tint), []).append(Shape(vertices.reshape(-1, 3), numpy.tile(shape.uvs, (len(matrices), 1)), triangles.reshape(-1, 3)))

    def triangle_count(self) -> int:
        return sum(len(shape.triangles) for shapes in self.parts.values() for shape in shapes)

    def flush(self, name_prefix: str = "Plants") -> None:
        """Turn what was stamped so far into objects named name_prefix<n> (one per material and tint)."""
        for (material, tint), shapes in self.parts.items():
            self._link(merged(shapes), material, tint, name_prefix)

        self.parts = {}

    def _link(self, shape: Shape, material: str, tint: str, name_prefix: str) -> None:
        builder = self.builder
        builder.count += 1
        mesh = bpy.data.meshes.new(f"{name_prefix}{builder.count}")
        corner_vertices = shape.triangles.ravel()

        mesh.vertices.add(len(shape.vertices))
        mesh.vertices.foreach_set("co", shape.vertices.astype(numpy.float32).ravel())
        mesh.loops.add(len(corner_vertices))
        mesh.loops.foreach_set("vertex_index", corner_vertices.astype(numpy.int32))
        mesh.polygons.add(len(shape.triangles))
        mesh.polygons.foreach_set("loop_start", numpy.arange(len(shape.triangles), dtype=numpy.int32) * 3)
        mesh.polygons.foreach_set("loop_total", numpy.full(len(shape.triangles), 3, dtype=numpy.int32))
        mesh.update(calc_edges=True)
        mesh.polygons.foreach_set("use_smooth", numpy.ones(len(shape.triangles), dtype=bool))
        mesh.uv_layers.new(name=UV_LAYER).data.foreach_set("uv", shape.uvs[corner_vertices].astype(numpy.float32).ravel())

        plants = bpy.data.objects.new(mesh.name, mesh)
        bpy.context.scene.collection.objects.link(plants)
        mesh.materials.append(builder.materials[material])
        plants["tint"] = self.to_linear(tint)
        plants["uv"] = '["keep"]'


def stamp_variants(batch: PlantBatch, variants: list, matrices: numpy.ndarray, generator: random.Random, frame=None) -> None:
    """Give every matrix one of the variants (each a list of (shape, material, tint) parts)."""
    choice = numpy.array([generator.randrange(len(variants)) for _ in range(len(matrices))])
    parts = [(index, part) for index, variant in enumerate(variants) for part in variant]

    for index, (shape, material, tint) in parts:
        batch.stamp(shape, matrices[choice == index], tint, material, frame)


# ---------- the plants ----------

def corn_ear(generator: random.Random, height: float, yaw: float) -> list:
    """Cob wrapped in its husk leaning off the stalk, silk spilling from the tip."""
    place = transform((0.0, 0.0, height), yaw, generator.uniform(-32.0, -22.0))
    husk = lathe_shape([(0.012, 0.0), (0.042, 0.07), (0.04, 0.17), (0.006, 0.28)], 5)
    silk = moved(crossed_cards("tuft", 0.13, 0.13), transform((0.0, 0.0, 0.26), 0.0, -35.0))

    return [(moved(husk, place), PAINT_MATERIAL, CORN_HUSK), (moved(silk, place), CROP_MATERIAL, CORN_SILK)]


def corn_plant(generator: random.Random) -> list:
    """Stalk, long arching leaves on alternate sides, one or two ears with silk and the tassel on top."""
    height = generator.uniform(2.0, 2.4)
    twist = generator.uniform(0.0, 360.0)
    leaves = [
        moved(
            ribbon(arc_path(generator.uniform(0.75, 1.0), generator.uniform(52.0, 68.0), generator.uniform(95.0, 135.0), 3), 0.13, "corn_leaf", along="u"),
            transform((0.0, 0.0, height * (0.2 + 0.11 * index)), twist + index * 180.0 + generator.uniform(-28.0, 28.0)),
        )
        for index in range(6)
    ]
    stalk = lathe_shape([(0.03, 0.0), (0.024, height * 0.5), (0.01, height - 0.05)], 4)
    tassel = moved(crossed_cards("tassel", 0.36, 0.4), transform((0.0, 0.0, height - 0.12)))
    ears = [part for index in range(generator.choice((1, 1, 2))) for part in corn_ear(generator, height * (0.4 + 0.12 * index), twist + 90.0 + index * 170.0)]

    return [(merged(leaves), CROP_MATERIAL, generator.choice(CORN_LEAF_TINTS)), (stalk, PAINT_MATERIAL, CORN_STALK), (tassel, CROP_MATERIAL, "FFFFFF"), *ears]


def cabbage_plant(generator: random.Random) -> list:
    """Tight pale head hugged by three cupped leaves, in a rosette of big open outer leaves."""
    radius = generator.uniform(0.12, 0.15)
    head = lathe_shape([(radius * 0.45, 0.03), (radius, radius * 0.75), (radius * 0.92, radius * 1.5), (radius * 0.2, radius * 2.0)], 5)
    hugging = [
        moved(ribbon(arc_path(radius * 3.3, 12.0, -128.0, 3), radius * 2.5, "cabbage", cup=0.3, columns=3), transform((0.0, 0.0, 0.02), index * 120.0 + generator.uniform(-15.0, 15.0)))
        for index in range(3)
    ]
    outer = [
        moved(
            ribbon(arc_path(generator.uniform(0.3, 0.38), generator.uniform(18.0, 42.0), generator.uniform(-20.0, 30.0), 2), generator.uniform(0.3, 0.36), "cabbage", cup=0.22, columns=3),
            transform((0.0, 0.0, 0.03), index * 72.0 + generator.uniform(-18.0, 18.0)),
        )
        for index in range(5)
    ]

    return [(head, PAINT_MATERIAL, CABBAGE_HEAD), (merged(hugging), CROP_MATERIAL, CABBAGE_INNER), (merged(outer), CROP_MATERIAL, generator.choice(CABBAGE_OUTER_TINTS))]


def carrot_plant(generator: random.Random) -> list:
    """Orange shoulder just out of the soil under a spray of feathery fronds."""
    shoulder = lathe_shape([(0.02, -0.03), (0.03, 0.012), (0.012, 0.03)], 4)
    fronds = [
        moved(
            ribbon(arc_path(generator.uniform(0.3, 0.44), generator.uniform(55.0, 82.0), generator.uniform(25.0, 70.0), 2), 0.17, "carrot"),
            transform((0.0, 0.0, 0.02), index * 72.0 + generator.uniform(-25.0, 25.0)),
        )
        for index in range(5)
    ]

    return [(shoulder, PAINT_MATERIAL, CARROT_ROOT), (merged(fronds), CROP_MATERIAL, generator.choice(CARROT_TINTS))]


def coffee_plant(generator: random.Random) -> list:
    """Coffee shrub (cafeeiro): a tiered dark-green dome of leaves with ripe cherries studding the lower tiers."""
    scale = generator.uniform(0.7, 0.9)
    dome = lathe_shape([(0.06, 0.0), (0.42 * scale, 0.28), (0.55 * scale, 0.6), (0.45 * scale, 0.95), (0.2 * scale, 1.22), (0.03, 1.32)], 7)
    cherries = [
        moved(lathe_shape([(0.004, 0.0), (0.03, 0.025), (0.004, 0.055)], 5), transform((math.cos(angle) * 0.5 * scale, math.sin(angle) * 0.5 * scale, height), 0.0, 0.0))
        for angle, height in ((generator.uniform(0.0, 6.28), generator.uniform(0.3, 0.75)) for _ in range(7))
    ]

    return [(dome, PAINT_MATERIAL, generator.choice(COFFEE_LEAF_TINTS)), (merged(cherries), PAINT_MATERIAL, COFFEE_CHERRY)]


def cane_plant(generator: random.Random) -> list:
    """Sugar cane clump: tall jointed stalks leaning apart, long blades arching from the crown."""
    twist = generator.uniform(0.0, 360.0)
    stalks = [
        moved(lathe_shape([(0.028, 0.0), (0.024, 1.4), (0.014, generator.uniform(2.5, 3.1))], 5), transform((0.0, 0.0, 0.0), twist + index * 90.0, generator.uniform(4.0, 11.0)))
        for index in range(4)
    ]
    blades = [
        moved(
            ribbon(arc_path(generator.uniform(0.9, 1.2), generator.uniform(42.0, 62.0), generator.uniform(90.0, 130.0), 3), 0.1, "corn_leaf", along="u"),
            transform((0.0, 0.0, generator.uniform(2.1, 2.8)), twist + index * 51.0 + generator.uniform(-20.0, 20.0)),
        )
        for index in range(7)
    ]

    return [(merged(stalks), PAINT_MATERIAL, generator.choice(CANE_STALK_TINTS)), (merged(blades), CROP_MATERIAL, generator.choice(CANE_LEAF_TINTS))]


def cassava_plant(generator: random.Random) -> list:
    """Cassava (mandioca): a few woody stems crowned by hands of long-fingered leaves."""
    twist = generator.uniform(0.0, 360.0)
    stems = [moved(lathe_shape([(0.022, 0.0), (0.016, 0.6), (0.01, generator.uniform(0.95, 1.2))], 4), transform((0.0, 0.0, 0.0), twist + index * 120.0, generator.uniform(6.0, 14.0))) for index in range(3)]
    leaves = [
        moved(ribbon(arc_path(generator.uniform(0.35, 0.5), generator.uniform(20.0, 55.0), generator.uniform(10.0, 50.0), 2), 0.3, "carrot"), transform((0.0, 0.0, generator.uniform(0.9, 1.5)), twist + index * 47.0))
        for index in range(8)
    ]

    return [(merged(stems), PAINT_MATERIAL, CASSAVA_STEM), (merged(leaves), CROP_MATERIAL, generator.choice(CASSAVA_LEAF_TINTS))]


def tuft_variants(tints: tuple, width: float = 0.5, height: float = 0.45) -> list:
    return [[(crossed_cards("tuft", width, height), CROP_MATERIAL, tint)] for tint in tints]


def variants_of(plant, generator: random.Random, count: int = 4) -> list:
    return [plant(generator) for _ in range(count)]


def spot_matrices(spots: list, ground: float, generator: random.Random, scale_range: tuple = (0.9, 1.1), tilt: float = 0.0) -> numpy.ndarray:
    """Matrices standing at Godot ground points (x, z) with a random turn, a size and a small lean."""
    points = [(x, -z, ground) for x, z in spots]
    yaws = [generator.uniform(0.0, 360.0) for _ in spots]
    scales = [generator.uniform(*scale_range) for _ in spots]
    tilts = [generator.uniform(-tilt, tilt) for _ in spots]

    return transforms(points, yaws, tilts, scales) if spots else numpy.zeros((0, 4, 4))
