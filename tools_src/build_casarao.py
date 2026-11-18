"""Model the casarão: one two-storey tiled mansion (sobrado) filling the block in front of the cathedral.

Inside it is five walk-in halls of build_market_shops.py (flagged casarao=True), all connected: the vestibule in
the middle, with the only street portal and the grand stair (casarao_vestibule.py), the library and the school
beside it on the ground floor, the reading room and the seminary over them on the upper floor (andar nobre).
Their shells keep the walls with the real doors and windows, the floors, ceilings and interiors. This model fills
the joints between the halls (cut at the inner doorways), dresses the outside (stone plinth, blue-and-white
azulejo cladding around the openings, pilasters, keystones, iron fanlights, hoods and wrought-iron balconies on
the upper windows, the walkable balcony over the portal) and crowns it: string course, a dentilled cornice, a
balustraded parapet with ceramic urns, the central pediment with a clock, a hipped tile roof and a lookout
(mirante) on the ridge.

Output: art/town/casarao.gltf (+ JSON sidecar), in the coords of the halls: facade on Y = 0, street toward -Y,
u (X) across the facade with 0 at the portal, d (Y) into the block, z up. build_hub_scene.py places it on the
vestibule's lot frame.

Usage:
  blender -b --factory-startup -P tools_src/build_casarao.py
"""

import math
import sys
from pathlib import Path

import bpy
import numpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_market_shops as shops  # noqa: E402
import build_town_houses as town  # noqa: E402
import casarao_vestibule as vestibule  # noqa: E402
from build_hub_scene import CASARAO_FRAME_HALL, CASARAO_HALLS, CASARAO_UPPER_HALLS, town_lots  # noqa: E402
from build_town_houses import STONE, WALL, WHITE, WOOD, Builder, Opening, srgb  # noqa: E402
from shop_props_common import lathe  # noqa: E402

STOREYS = shops.CASARAO_STOREYS
LEVELS = (0.0, STOREYS[0])
BODY_TOP = sum(STOREYS)
WALL_TOP = BODY_TOP - 0.3  # a cimalha cobre os últimos 30 cm
JOINT = 0.3  # parede que este modelo põe entre as cascas de dois salões vizinhos
BALCONY_REACH = 0.6
PORTAL_BALCONY_REACH = 1.5  # a sacada sobre o portal é andável
SHUTTER_MAX_HEIGHT = 2.0  # janelas do fundo até esta altura levam venezianas
CORNICE_TOP = WALL_TOP + 0.55
PARAPET_TOP = CORNICE_TOP + 1.15
CLADDING = 0.03  # espessura do azulejo sobre a parede
PLINTH_HEIGHT = 0.7
OPENING_MARGIN = 0.2  # azulejo para antes da moldura de pedra das aberturas do térreo
PILASTER = 0.62
PILASTER_PROUD = 0.14
CORNER_PILASTER = 0.9
STRING_COURSE = 0.3
DENTIL_PITCH = 0.32
BALUSTER_PITCH = 0.21
PEDESTAL_MAX_GAP = 7.8
ROOF_PITCH = 26.0
ROOF_INSET = 0.35  # o telhado começa atrás da platibanda
BACK_EAVE = 0.7
ATTIC_BAYS = 3  # vãos de cada ponta da fachada sob um frontão curvo (quebra a fileira longa de janelas iguais)
ATTIC_RISE = 1.9
PEDIMENT_HALF = 5.9
PEDIMENT_RISE = 2.7
MIRANTE_HALF = 2.7
MIRANTE_STOREY = 3.6
AZULEJO_TILE_METRES = 1.2  # a textura cobre 4 x 4 azulejos de 30 cm (os de 15 cm cintilavam de longe)
AZULEJO_PIXELS = 1024
AZULEJO_TEXTURE = town.TEXTURE_DIR / "T_Azulejo_BaseColor.png"
OUTPUT = town.PROJECT_DIR / "art" / "town" / "casarao.gltf"

TRIM = srgb("EFE4CC")  # molduras, pilastras e cimalhas em reboco creme (a pedra cinza do atlas apagava a fachada)
CANTARIA = srgb(STONE["clara"])
IRON = srgb(town.IRON)
SHUTTER_GREEN = srgb("2F6B4F")
ROOF_TILE = srgb(town.ROOFS["terracota"])
GOLD = srgb("D9A441")
AZULEJO_BLUE = srgb("2E5AA8")
GLAZE_WHITE = srgb("F4F2EC")


# ---------- azulejo texture ----------

def azulejo_pixels() -> numpy.ndarray:
    """RGBA float pixels of 4 x 4 glazed tiles: corner quarter rings that close into circles across tiles, a
    four-petal flower in the middle of each tile, thin grout lines and a slight glaze variation per tile."""
    tile_pixels = AZULEJO_PIXELS // 4
    coords = (numpy.arange(AZULEJO_PIXELS) + 0.5) / tile_pixels
    x, y = numpy.meshgrid(coords, coords)
    local_x, local_y = x % 1.0, y % 1.0
    corner_distance = numpy.hypot(numpy.minimum(local_x, 1.0 - local_x), numpy.minimum(local_y, 1.0 - local_y))
    angle = numpy.arctan2(local_y - 0.5, local_x - 0.5)
    centre_distance = numpy.hypot(local_x - 0.5, local_y - 0.5)
    petal = 0.2 * (0.45 + 0.55 * numpy.abs(numpy.cos(2.0 * angle)))
    tile_index = numpy.floor(x).astype(int) * 7 + numpy.floor(y).astype(int) * 13
    glaze = 1.0 - 0.035 * ((tile_index * 37) % 5) / 4.0

    background = numpy.array([0.95, 0.94, 0.9])
    deep_blue = numpy.array([0.3, 0.45, 0.72])  # contraste baixo: azul forte sobre branco cintilava de longe
    light_blue = numpy.array([0.64, 0.75, 0.9])
    ochre = numpy.array([0.86, 0.66, 0.28])
    grout = numpy.array([0.82, 0.81, 0.77])

    pixels = numpy.ones((AZULEJO_PIXELS, AZULEJO_PIXELS, 4))
    pixels[..., :3] = background * glaze[..., None]

    layers = [
        (corner_distance < 0.17, light_blue),
        (numpy.abs(corner_distance - 0.3) < 0.035, deep_blue),
        (centre_distance < petal, deep_blue),
        (centre_distance < petal * 0.62, light_blue),
        (centre_distance < 0.05, ochre),
        ((numpy.abs(local_x - 0.5) < 0.012) & (centre_distance > petal) & (centre_distance < 0.42), light_blue),
        ((numpy.abs(local_y - 0.5) < 0.012) & (centre_distance > petal) & (centre_distance < 0.42), light_blue),
        ((local_x < 0.012) | (local_x > 0.988) | (local_y < 0.012) | (local_y > 0.988), grout),
    ]

    for mask, color in layers:
        pixels[mask, :3] = color

    return pixels


def azulejo_texture() -> Path:
    """Paint the azulejo atlas once (sRGB PNG next to the other town textures)."""
    if AZULEJO_TEXTURE.exists():
        return AZULEJO_TEXTURE

    image = bpy.data.images.new("T_Azulejo_BaseColor", AZULEJO_PIXELS, AZULEJO_PIXELS, alpha=False)
    image.pixels.foreach_set(azulejo_pixels()[::-1].ravel().astype(numpy.float32))
    image.filepath_raw = str(AZULEJO_TEXTURE)
    image.file_format = "PNG"
    image.save()

    return AZULEJO_TEXTURE


# ---------- plan read from the halls ----------

def hall_rooms() -> dict:
    """hall -> (Room, offset along the casarão facade of the hall's centre, storey), both floors."""
    lots = {lot["shop"]: lot for lot in town_lots() if lot.get("shop") in CASARAO_HALLS}
    centre = lots[CASARAO_FRAME_HALL]["position"]
    offsets = {name: -(lot["position"][2] - centre[2]) for name, lot in lots.items()}
    ground = {name: (shops.Room(name), offset, 0) for name, offset in offsets.items()}
    upper = {name: (shops.Room(name), offsets[below], 1) for name, below in CASARAO_UPPER_HALLS.items()}

    return {**ground, **upper}


class Plan:
    """Body size, the four wall frames (outer face on local Y = 0, outside toward -Y, s along the wall seen from
    outside) and every outside opening per side in s, with z from the ground and its storey in style."""

    def __init__(self) -> None:
        rooms = hall_rooms()
        any_room = rooms[CASARAO_FRAME_HALL][0]

        self.rooms = rooms
        self.vestibule = any_room
        self.half = max(offset + room.half for room, offset, _ in rooms.values())
        self.depth = any_room.depth
        self.frames = {
            "front": Matrix.Translation((-self.half, 0.0, 0.0)),
            "right": Matrix.Translation((self.half, 0.0, 0.0)) @ Matrix.Rotation(math.pi / 2.0, 4, "Z"),
            "back": Matrix.Translation((self.half, self.depth, 0.0)) @ Matrix.Rotation(math.pi, 4, "Z"),
            "left": Matrix.Translation((-self.half, self.depth, 0.0)) @ Matrix.Rotation(-math.pi / 2.0, 4, "Z"),
        }
        self.lengths = {"front": 2.0 * self.half, "back": 2.0 * self.half, "right": self.depth, "left": self.depth}
        self.openings = {side: [] for side in self.frames}
        self.hall_edges = sorted({offset + side_sign * room.half for room, offset, _ in rooms.values() for side_sign in (-1, 1)})
        self.joints = sorted({(first + second) / 2.0 for first, second in zip(self.hall_edges[1::2], self.hall_edges[2::2])})
        self.axes = sorted({offset for _, offset, _ in rooms.values()})

        for name, (room, offset, storey) in rooms.items():
            self.collect(room, offset, self.hall_openings(name, room, storey))

        for side in self.openings:
            self.openings[side].sort(key=lambda opening: opening.u)

        self.doors = [opening.u - self.half for opening in self.openings["front"] if opening.kind == "door"]

    def hall_openings(self, name: str, room, storey: int) -> dict:
        """side -> [(lift, storey, Opening)] of one hall in its own wall coords."""
        if name == CASARAO_FRAME_HALL:
            found = vestibule.facade_openings(room)

            return {side: [(lift, int(lift > 0.0), opening) for lift, opening in openings] for side, openings in found.items()}

        found = {"front": shops.front_openings(room), **shops.wall_windows(room)}

        return {side: [(LEVELS[storey], storey, opening) for opening in openings] for side, openings in found.items()}

    def collect(self, room, offset: float, found: dict) -> None:
        """Openings of one hall moved into the casarão wall frames."""
        along = {
            "front": lambda opening: offset + opening.u - room.half + self.half,
            "back": lambda opening: self.half - (offset + room.half - opening.u),
            "right": lambda opening: WALL + opening.u,
            "left": lambda opening: WALL + opening.u,
        }

        for side, openings in found.items():
            self.openings[side] += [moved(opening, along[side](opening), lift, storey) for lift, storey, opening in openings]

    def on_storey(self, side: str, storey: int) -> list:
        return [opening for opening in self.openings[side] if opening.style["storey"] == storey]


def moved(opening: Opening, s: float, lift: float, storey: int) -> Opening:
    return Opening(s, opening.width, opening.bottom + lift, opening.height, opening.top, kind=opening.kind, storey=storey)


def front_pilasters(plan: Plan) -> list:
    """s of the pilasters of the front: corners, the joints between halls and both sides of the axis bay of each
    hall (the portal gets a second pair: the three central bays under the pediment)."""
    pilasters = [CORNER_PILASTER / 2.0, plan.lengths["front"] - CORNER_PILASTER / 2.0]
    pilasters += [edge + plan.half for edge in plan.hall_edges[1:-1]]
    openings = plan.on_storey("front", 0)

    for index, opening in enumerate(openings):
        if all(abs(opening.u - plan.half - axis) > 0.5 for axis in plan.axes):
            continue

        pilasters += [between(openings[index - 1], opening), between(opening, openings[index + 1])]

        if opening.kind == "door":
            pilasters += [between(openings[index - 2], openings[index - 1]), between(openings[index + 1], openings[index + 2])]

    return sorted(pilasters)


def between(first: Opening, second: Opening) -> float:
    return (first.u + first.width / 2.0 + second.u - second.width / 2.0) / 2.0


def corner_pilasters(length: float) -> list:
    return [CORNER_PILASTER / 2.0, length - CORNER_PILASTER / 2.0]


# ---------- ground floor dressing ----------

def plinth(b: Builder, plan: Plan, side: str) -> None:
    """Stone base course, cut at the doors."""
    frame = plan.frames[side]
    doors = [(opening.u - opening.width / 2.0 - 0.2, opening.u + opening.width / 2.0 + 0.2) for opening in plan.on_storey(side, 0) if opening.kind == "door"]
    starts = [0.0] + [right for _, right in doors]
    ends = [left for left, _ in doors] + [plan.lengths[side]]

    for start, end in zip(starts, ends):
        b.box((start, -0.1, 0.0), (end, 0.0, PLINTH_HEIGHT), "stone", CANTARIA, frame=frame)
        b.box((start, -0.14, PLINTH_HEIGHT - 0.08), (end, 0.0, PLINTH_HEIGHT), "plaster", TRIM, frame=frame)


def clad(b: Builder, plan: Plan, side: str, storey: int) -> None:
    """Azulejo over one storey of a street wall, around the openings (their stone frames stay clear)."""
    frame = plan.frames[side]
    bottom = (PLINTH_HEIGHT, LEVELS[1] + STRING_COURSE / 2.0)[storey]
    top = (LEVELS[1] - STRING_COURSE / 2.0, WALL_TOP)[storey]
    gaps = [(opening.u - opening.width / 2.0 - OPENING_MARGIN, opening.u + opening.width / 2.0 + OPENING_MARGIN, opening) for opening in plan.on_storey(side, storey)]
    starts = [0.0] + [right for _, right, _ in gaps]
    ends = [left for left, _, _ in gaps] + [plan.lengths[side]]

    for start, end in zip(starts, ends):
        b.box((start, -CLADDING, bottom), (end, 0.0, top), "azulejo", WHITE, frame=frame, uv=("world", AZULEJO_TILE_METRES))

    for left, right, opening in gaps:
        b.box((left, -CLADDING, opening.apex + OPENING_MARGIN), (right, 0.0, top), "azulejo", WHITE, frame=frame, uv=("world", AZULEJO_TILE_METRES))

        if opening.bottom > bottom + 0.2:
            b.box((left, -CLADDING, bottom), (right, 0.0, opening.bottom - 0.1), "azulejo", WHITE, frame=frame, uv=("world", AZULEJO_TILE_METRES))


def keystones_and_fanlights(b: Builder, plan: Plan, side: str) -> None:
    """Carved keystone on every ground arch; the doors get a wrought-iron fanlight in the arch."""
    frame = plan.frames[side]

    for opening in plan.on_storey(side, 0):
        top = opening.apex + 0.12
        b.prism([(opening.u - 0.16, top - 0.28), (opening.u + 0.16, top - 0.28), (opening.u + 0.22, top + 0.12), (opening.u - 0.22, top + 0.12)], -0.12, 0.0, "trim", CANTARIA, frame=frame)

        if opening.kind == "door":
            fanlight(b, frame, opening)


def fanlight(b: Builder, frame: Matrix, opening: Opening) -> None:
    """Sunburst of iron bars filling the arch over the door leaves."""
    spring = opening.spring
    radius = opening.width / 2.0 - 0.04
    spokes = 9

    b.box((opening.u - radius, 0.1, spring - 0.03), (opening.u + radius, 0.14, spring + 0.03), "metal", IRON, frame=frame)

    for spoke in range(spokes):
        angle = math.pi * (spoke + 0.5) / spokes
        end = (opening.u + radius * math.cos(angle), 0.12, spring + radius * math.sin(angle))
        b.beam((opening.u, 0.12, spring), end, 0.03, 0.03, "metal", IRON, frame=frame)

    arc = Opening(opening.u, 2.0 * radius, spring - radius, 2.0 * radius, "round")
    inner = Opening(opening.u, 2.0 * radius - 0.08, spring - radius, 2.0 * radius - 0.04, "round")
    b.prism(arc.arc() + list(reversed(inner.arc())), 0.1, 0.14, "metal", IRON, frame=frame)
    b.cylinder((opening.u, 0.1, spring), 0.08, 0.04, 12, "metal", IRON, frame=frame, axis="Y")


def wall_lantern(b: Builder, frame: Matrix, s: float, height: float) -> None:
    """Iron bracket with a hexagonal lantern (its panes light up at night like the windows)."""
    reach = 0.55

    b.box((s - 0.08, -0.04, height - 0.25), (s + 0.08, 0.0, height + 0.25), "metal", IRON, frame=frame)
    b.beam((s, -0.02, height + 0.1), (s, -reach, height + 0.1), 0.04, 0.04, "metal", IRON, frame=frame)
    b.beam((s, -0.02, height - 0.2), (s, -reach + 0.2, height + 0.08), 0.03, 0.03, "metal", IRON, frame=frame)
    b.cylinder((s, -reach, height - 0.45), 0.13, 0.42, 6, "glass", WHITE, frame=frame)
    b.cylinder((s, -reach, height - 0.5), 0.15, 0.06, 6, "metal", IRON, frame=frame)
    b.cylinder((s, -reach, height - 0.03), 0.17, 0.2, 6, "metal", IRON, top_radius=0.03, frame=frame)
    b.sphere((s, -reach, height + 0.22), 0.04, "metal", IRON, frame=frame)


# ---------- vertical and horizontal orders ----------

def pilaster(b: Builder, frame: Matrix, s: float, width: float, bottom: float, top: float) -> None:
    """Stone pilaster with a stepped base and a moulded capital."""
    half = width / 2.0

    b.box((s - half, -PILASTER_PROUD, bottom), (s + half, 0.0, top), "plaster", TRIM, frame=frame, uv=("band", *town.TRIM_SMOOTH_BAND, 1.0))
    b.box((s - half - 0.08, -PILASTER_PROUD - 0.08, bottom), (s + half + 0.08, 0.0, bottom + 0.9), "trim", CANTARIA, frame=frame, uv=("band", *town.TRIM_BLOCK_BAND, 1.0))
    b.box((s - half - 0.05, -PILASTER_PROUD - 0.05, bottom + 0.9), (s + half + 0.05, 0.0, bottom + 1.0), "plaster", TRIM, frame=frame)
    b.box((s - half - 0.07, -PILASTER_PROUD - 0.07, top - 0.35), (s + half + 0.07, 0.0, top - 0.25), "plaster", TRIM, frame=frame)
    b.box((s - half - 0.12, -PILASTER_PROUD - 0.12, top - 0.18), (s + half + 0.12, 0.0, top), "plaster", TRIM, frame=frame)


def string_course(b: Builder, frame: Matrix, length: float, z: float) -> None:
    """Moulded band between storeys (cimalha)."""
    half = STRING_COURSE / 2.0
    profile = [(0.0, z - half), (-0.08, z - half), (-0.08, z - half + 0.08), (-0.2, z), (-0.2, z + half - 0.05), (-0.12, z + half), (0.0, z + half)]

    b.side_prism(profile, -0.1, length + 0.1, "plaster", TRIM, frame=frame)


def azulejo_band(b: Builder, frame: Matrix, length: float, top: float) -> None:
    """Plain deep-blue tile border under a moulding, framing each storey's tile field."""
    b.box((0.0, -CLADDING - 0.008, top - 0.24), (length, 0.0, top), "paint", AZULEJO_BLUE, frame=frame)


def cornice(b: Builder, frame: Matrix, length: float, with_dentils: bool) -> None:
    """Crown cornice with dentils under the drip."""
    profile = [(0.0, WALL_TOP), (-0.12, WALL_TOP), (-0.12, WALL_TOP + 0.1), (-0.2, WALL_TOP + 0.18), (-0.24, WALL_TOP + 0.3), (-0.5, WALL_TOP + 0.38), (-0.56, WALL_TOP + 0.47), (-0.56, CORNICE_TOP), (0.0, CORNICE_TOP)]

    b.side_prism(profile, -0.5, length + 0.5, "plaster", TRIM, frame=frame)

    if not with_dentils:
        return

    for index in range(int(length / DENTIL_PITCH)):
        s = (index + 0.5) * DENTIL_PITCH
        b.box((s - 0.08, -0.24, WALL_TOP + 0.3), (s + 0.08, -0.12, WALL_TOP + 0.42), "plaster", TRIM, frame=frame)


# ---------- upper storeys ----------

def arched_window(b: Builder, frame: Matrix, opening: Opening, front: float, muntins: int) -> None:
    """Moulded stone frame behind, dark glass in front of it with white glazing bars, sill."""
    b.prism(opening.outline(0.14), front - 0.04, front, "plaster", TRIM, frame=frame)
    b.prism(opening.outline(), front - 0.06, front - 0.04, "glass", frame=frame)
    b.box((opening.u - 0.025, front - 0.08, opening.bottom), (opening.u + 0.025, front - 0.06, opening.apex), "paint", WHITE, frame=frame)

    for bar in range(muntins):
        bar_z = opening.bottom + (opening.spring - opening.bottom) * (bar + 1) / (muntins + 1)
        b.box((opening.u - opening.width / 2.0, front - 0.08, bar_z - 0.02), (opening.u + opening.width / 2.0, front - 0.06, bar_z + 0.02), "paint", WHITE, frame=frame)

    b.box((opening.u - opening.width / 2.0, front - 0.08, opening.spring - 0.025), (opening.u + opening.width / 2.0, front - 0.06, opening.spring + 0.025), "paint", WHITE, frame=frame)
    b.box((opening.u - opening.width / 2.0 - 0.2, front - 0.16, opening.bottom - 0.12), (opening.u + opening.width / 2.0 + 0.2, front, opening.bottom), "trim", CANTARIA, frame=frame)


def hood(b: Builder, frame: Matrix, opening: Opening, front: float, shape: str) -> None:
    """Small pediment over a piano nobile window: triangle or segmental arch on a frieze."""
    half = opening.width / 2.0 + 0.32
    base = opening.apex + 0.2
    hoods = {
        "triangle": [(opening.u - half, base), (opening.u + half, base), (opening.u, base + 0.55)],
        "segment": Opening(opening.u, 2.0 * half, base - 0.4, 0.85, "segment").outline()[1:] + [(opening.u - half, base)],
    }

    b.box((opening.u - half + 0.1, front - 0.12, base - 0.22), (opening.u + half - 0.1, front, base), "plaster", TRIM, frame=frame)
    b.prism(hoods[shape], front - 0.2, front, "plaster", TRIM, frame=frame)


def iron_railing(b: Builder, frame: Matrix, start: float, end: float, front: float, back: float, z: float, height: float = 1.0) -> None:
    """Wrought-iron railing on three sides of a balcony slab: rails, bars and a ring in the middle of the front."""
    bar_count = max(2, int((end - start) / 0.12))

    b.box((start, front, z + height - 0.05), (end, front + 0.05, z + height), "metal", IRON, frame=frame)
    b.box((start, front, z + 0.08), (end, front + 0.04, z + 0.12), "metal", IRON, frame=frame)

    for bar in range(bar_count + 1):
        s = start + (end - start) * bar / bar_count
        b.box((s - 0.012, front, z), (s + 0.012, front + 0.03, z + height), "metal", IRON, frame=frame)

    for edge in (start, end):
        b.box((edge - 0.02, front, z + height - 0.05), (edge + 0.02, back, z + height), "metal", IRON, frame=frame)
        b.box((edge - 0.012, (front + back) / 2.0, z), (edge + 0.012, (front + back) / 2.0 + 0.03, z + height), "metal", IRON, frame=frame)

    middle = (start + end) / 2.0
    centre_z = z + height / 2.0 + 0.05
    diamond = [(middle, centre_z + 0.2), (middle + 0.16, centre_z), (middle, centre_z - 0.2), (middle - 0.16, centre_z)]

    for corner, next_corner in zip(diamond, diamond[1:] + diamond[:1]):
        b.beam((corner[0], front + 0.015, corner[1]), (next_corner[0], front + 0.015, next_corner[1]), 0.025, 0.025, "metal", IRON, frame=frame)


def balcony(b: Builder, frame: Matrix, start: float, end: float, z: float, reach: float = BALCONY_REACH, walkable: bool = False) -> None:
    """Stone slab on carved consoles with an iron railing (sacada); a walkable one gets colliders."""
    rail = 1.1 if walkable else 1.0

    b.box((start, -reach, z - 0.16), (end, 0.0, z), "trim", CANTARIA, frame=frame)
    b.box((start - 0.03, -reach - 0.03, z - 0.2), (end + 0.03, -reach + 0.06, z - 0.16), "plaster", TRIM, frame=frame)
    iron_railing(b, frame, start + 0.04, end - 0.04, -reach + 0.04, -0.02, z, rail)

    if not walkable:
        return

    b.collider((start, -reach, z - 0.16), (end, 0.0, z), frame)
    b.collider((start, -reach, z), (end, -reach + 0.1, z + rail), frame)
    b.collider((start, -reach, z), (start + 0.1, 0.0, z + rail), frame)
    b.collider((end - 0.1, -reach, z), (end, 0.0, z + rail), frame)


def console(b: Builder, frame: Matrix, s: float, z: float, reach: float) -> None:
    """Scrolled stone bracket under a balcony slab (profile in the t-z plane)."""
    profile = [(0.0, z), (-reach + 0.06, z), (-reach + 0.1, z - 0.12), (-0.18, z - 0.35), (-0.08, z - 0.6), (0.0, z - 0.6)]
    b.side_prism(profile, s - 0.08, s + 0.08, "trim", CANTARIA, frame=frame)


def dress_upper_storey(b: Builder, plan: Plan, side: str) -> None:
    """Andar nobre: the real windows of the upper halls get alternating hoods; the French windows (janelas de
    sacada) a balcony each; the doors over the portal share one long balcony the player can walk on."""
    frame = plan.frames[side]
    front = -CLADDING
    openings = plan.on_storey(side, 1)
    doors = [opening for opening in openings if opening.kind == "balcony"]

    for index, opening in enumerate(openings):
        is_door = opening in doors
        is_french = opening.bottom - LEVELS[1] < 0.3

        hood(b, frame, opening, front, "triangle" if index % 2 == 0 or is_door else "segment")

        if is_door or not is_french:
            continue

        balcony(b, frame, opening.u - 0.95, opening.u + 0.95, opening.bottom)

        for s in (opening.u - 0.7, opening.u + 0.7):
            console(b, frame, s, LEVELS[1] - 0.04, BALCONY_REACH - 0.05)

    if doors:
        start, end = doors[0].u - 1.25, doors[-1].u + 1.25
        balcony(b, frame, start, end, LEVELS[1] + shops.FLOOR_TOP, reach=PORTAL_BALCONY_REACH, walkable=True)

        for opening in doors:
            for s in (opening.u - 0.9, opening.u + 0.9):
                console(b, frame, s, LEVELS[1] - 0.1, PORTAL_BALCONY_REACH - 0.1)


def back_shutters(b: Builder, plan: Plan) -> None:
    """Plain whitewashed back: green shutters beside the small windows of both floors."""
    frame = plan.frames["back"]
    small = [opening for opening in plan.openings["back"] if opening.height <= SHUTTER_MAX_HEIGHT]

    for opening in small:
        for side_sign in (-1, 1):
            shutter = opening.u + side_sign * (opening.width / 2.0 + 0.33)
            b.box((shutter - 0.27, -0.1, opening.bottom), (shutter + 0.27, -0.04, opening.spring), "paint", SHUTTER_GREEN, frame=frame)


# ---------- joints between the halls ----------

def dress_joint_doorway(b: Builder, room, frame: Matrix, opening: Opening) -> None:
    """Threshold of an inner doorway through the joint wall."""
    half = opening.width / 2.0

    b.box((opening.u - half, 0.0, 0.0), (opening.u + half, JOINT, shops.FLOOR_TOP + 0.005), "trim", room.house.trim_tint, frame=frame)
    b.collider((opening.u - half, 0.0, 0.0), (opening.u + half, JOINT, shops.FLOOR_TOP), frame)


shops.OPENING_DRESSING["joint"] = dress_joint_doorway


def joint_walls(b: Builder, plan: Plan) -> None:
    """The wall between the shells of two neighbour halls, on both floors, cut where their doorways meet."""
    door_d, width, height, top = shops.INNER_DOOR

    for joint in plan.joints:
        for level in LEVELS:
            frame = Matrix.Translation((joint + JOINT / 2.0, 0.0, level)) @ Matrix.Rotation(math.pi / 2.0, 4, "Z")
            shops.pierced_wall(b, plan.vestibule, frame, plan.depth, [Opening(door_d, width, 0.0, height, top, kind="joint")])


# ---------- crown: parapet, pediment, roof, lookout ----------

def parapet(b: Builder, plan: Plan, side: str, posts: list) -> None:
    """Balustrade with pedestals over the pilasters (and in between where they are far apart), urns on top."""
    frame = plan.frames[side]
    length = plan.lengths[side]
    bottom = CORNICE_TOP
    rail = PARAPET_TOP - 0.16
    gaps = closed_spans(plan) if side == "front" else []  # frontão e áticos interrompem a balaustrada
    edges = [edge for gap in gaps for edge in (gap[0] - 0.3, gap[1] + 0.3) if 0.5 < edge < length - 0.5]
    pedestals = sorted([s for s in fill_gaps(posts, PEDESTAL_MAX_GAP) if not any(gap[0] - 0.8 < s < gap[1] + 0.8 for gap in gaps)] + edges)
    cuts = [0.0] + [edge for gap in gaps for edge in gap] + [length]
    runs = [(start, end) for start, end in zip(cuts[::2], cuts[1::2]) if end - start > 0.05]

    for start, end in runs:
        b.box((start, -0.3, bottom), (end, 0.05, bottom + 0.25), "plaster", TRIM, frame=frame)
        b.box((start, -0.34, rail), (end, 0.08, PARAPET_TOP), "plaster", TRIM, frame=frame)

    for index in range(int(length / BALUSTER_PITCH)):
        s = (index + 0.5) * BALUSTER_PITCH

        if any(gap[0] < s < gap[1] for gap in gaps):
            continue

        if all(abs(s - pedestal) > 0.45 for pedestal in pedestals):
            baluster(b, frame @ Matrix.Translation((s, -0.12, bottom + 0.25)), rail - bottom - 0.25)

    for s in pedestals:
        b.box((s - 0.32, -0.36, bottom), (s + 0.32, 0.1, PARAPET_TOP + 0.08), "plaster", TRIM, frame=frame)
        b.box((s - 0.38, -0.42, PARAPET_TOP + 0.08), (s + 0.38, 0.16, PARAPET_TOP + 0.18), "plaster", TRIM, frame=frame)
        urn(b, frame @ Matrix.Translation((s, -0.13, PARAPET_TOP + 0.18)))


def attic_spans(plan: Plan) -> list:
    """(start, end) in s of the end attics: from each corner over its first ATTIC_BAYS bays."""
    openings = plan.on_storey("front", 0)
    left = between(openings[ATTIC_BAYS - 1], openings[ATTIC_BAYS])
    right = between(openings[-ATTIC_BAYS - 1], openings[-ATTIC_BAYS])

    return [(0.0, left), (right, plan.lengths["front"])]


def closed_spans(plan: Plan) -> list:
    """Spans of the front parapet with no balustrade, left to right: the attics and the central pediment."""
    pediment = (plan.half - PEDIMENT_HALF - 0.2, plan.half + PEDIMENT_HALF + 0.2)
    attics = attic_spans(plan)

    return [attics[0], pediment, attics[1]]


def attic(b: Builder, plan: Plan, span: tuple) -> None:
    """Curved-top attic over the end bays: solid parapet with a segmental crown, cream frame around an azulejo
    panel, a moulded coping and an urn at the crown."""
    frame = plan.frames["front"]
    centre = (span[0] + span[1]) / 2.0
    width = span[1] - span[0]
    body = Opening(centre, width, CORNICE_TOP, PARAPET_TOP - CORNICE_TOP + ATTIC_RISE, "segment")
    panel = Opening(centre, width - 2.2, CORNICE_TOP + 0.35, body.height - 0.85, "segment")

    b.prism(body.outline(), -0.3, 0.3, "plaster", TRIM, frame=frame)
    b.prism(body.arc(0.12) + list(reversed(body.arc())), -0.42, 0.36, "plaster", TRIM, frame=frame)
    b.prism(panel.outline(0.14), -0.36, -0.3, "plaster", TRIM, frame=frame)
    b.prism(panel.outline(), -0.38, -0.36, "azulejo", WHITE, frame=frame, uv=("world", AZULEJO_TILE_METRES))
    b.box((centre - 0.32, -0.36, body.apex + 0.05), (centre + 0.32, 0.1, body.apex + 0.25), "plaster", TRIM, frame=frame)
    urn(b, frame @ Matrix.Translation((centre, -0.13, body.apex + 0.25)))


def fill_gaps(posts: list, max_gap: float) -> list:
    """posts plus evenly spaced extra ones wherever two neighbours are more than max_gap apart."""
    filled = []

    for first, second in zip(posts, posts[1:]):
        extra = int((second - first) / max_gap)
        filled += [first + (second - first) * step / (extra + 1) for step in range(extra + 1)]

    return filled + posts[-1:]


BALUSTER_PROFILE = [(0.07, 0.0), (0.07, 0.07), (0.045, 0.12), (0.06, 0.22), (0.085, 0.33), (0.05, 0.44), (0.035, 0.49), (0.065, 0.53), (0.065, 0.58)]
URN_PROFILE = [(0.17, 0.0), (0.17, 0.06), (0.1, 0.1), (0.08, 0.16), (0.2, 0.3), (0.24, 0.42), (0.2, 0.55), (0.12, 0.6), (0.15, 0.64), (0.13, 0.68), (0.02, 0.7)]


def baluster(b: Builder, frame: Matrix, height: float) -> None:
    scale = height / BALUSTER_PROFILE[-1][1]
    lathe(b, [(radius, z * scale) for radius, z in BALUSTER_PROFILE], 6, "trim", "F2EEE6", frame)


def urn(b: Builder, frame: Matrix) -> None:
    """Glazed ceramic urn (compoteira) with a pine-cone finial: white body, blue band, gold knob."""
    lathe(b, URN_PROFILE, 10, "paint", "F2F0EA", frame)
    lathe(b, [(0.245, 0.36), (0.245, 0.46)], 10, "paint", "2E5AA8", frame)
    b.sphere((0.0, 0.0, 0.82), 0.09, "paint", GOLD, scale=(1.0, 1.0, 1.5), frame=frame)


def pediment(b: Builder, plan: Plan) -> None:
    """Triangular pediment over the central bays: azulejo tympanum, raking cornices, a clock in a stone ring and
    urns on the three corners."""
    frame = plan.frames["front"]
    centre = plan.half
    base = CORNICE_TOP
    apex = base + PEDIMENT_RISE
    triangle = [(centre - PEDIMENT_HALF, base), (centre + PEDIMENT_HALF, base), (centre, apex)]
    clock = Opening(centre, 1.3, base + 0.45, 1.3, "circle")

    b.prism(triangle, -0.02, 0.4, "azulejo", WHITE, frame=frame, uv=("world", AZULEJO_TILE_METRES))
    b.box((centre - PEDIMENT_HALF - 0.2, -0.45, base - 0.05), (centre + PEDIMENT_HALF + 0.2, 0.4, base + 0.2), "plaster", TRIM, frame=frame)

    for side_sign in (-1, 1):
        corner = (centre - side_sign * PEDIMENT_HALF, -0.2, base + 0.1)
        b.beam((corner[0] - side_sign * 0.25, corner[1], corner[2] - 0.05), (centre + side_sign * 0.12, -0.2, apex + 0.22), 0.36, 0.5, "plaster", TRIM, frame=frame)

    b.box((centre - 0.3, -0.3, apex + 0.1), (centre + 0.3, 0.3, apex + 0.4), "plaster", TRIM, frame=frame)
    urn(b, frame @ Matrix.Translation((centre, 0.0, apex + 0.4)))
    b.prism(clock.outline(0.16), -0.12, -0.02, "trim", CANTARIA, frame=frame)
    b.prism(clock.outline(), -0.14, -0.12, "paint", srgb("F6F1E2"), frame=frame)
    clock_hands(b, frame, centre, clock.bottom + clock.height / 2.0)


def clock_hands(b: Builder, frame: Matrix, s: float, z: float) -> None:
    """Hour marks and two hands (ten past ten, the classic clock-face pose)."""
    for hour in range(12):
        angle = math.tau * hour / 12.0
        mark = (s + 0.53 * math.sin(angle), z + 0.53 * math.cos(angle))
        b.box((mark[0] - 0.025, -0.16, mark[1] - 0.025), (mark[0] + 0.025, -0.14, mark[1] + 0.025), "paint", srgb("2A2228"), frame=frame)

    for length, angle in ((0.32, math.radians(-60.0)), (0.48, math.radians(60.0))):
        b.beam((s, -0.17, z), (s + length * math.sin(angle), -0.17, z + length * math.cos(angle)), 0.04, 0.02, "paint", srgb("2A2228"), frame=frame)

    b.cylinder((s, -0.18, z), 0.05, 0.03, 8, "paint", GOLD, frame=frame, axis="Y")


def hip(b: Builder, minimum: tuple, maximum: tuple, base: float, pitch: float, material: str, tint: tuple) -> float:
    """Four-slope roof over a rectangle (u, d); returns the ridge height."""
    half_short = min(maximum[0] - minimum[0], maximum[1] - minimum[1]) / 2.0
    rise = half_short * math.tan(math.radians(pitch))
    centre = ((minimum[0] + maximum[0]) / 2.0, (minimum[1] + maximum[1]) / 2.0)
    along_u = maximum[0] - minimum[0] >= maximum[1] - minimum[1]
    ridge_half = (maximum[0] - minimum[0] if along_u else maximum[1] - minimum[1]) / 2.0 - half_short
    ridge = [(centre[0] - ridge_half, centre[1]), (centre[0] + ridge_half, centre[1])] if along_u else [(centre[0], centre[1] - ridge_half), (centre[0], centre[1] + ridge_half)]
    corners = [(u, d, base) for u in (minimum[0], maximum[0]) for d in (minimum[1], maximum[1])]

    peaks = sorted({(round(u, 4), round(d, 4)) for u, d in ridge})  # planta quadrada: as duas pontas viram um vértice só

    b.hull(corners + [(u, d, base + rise) for u, d in peaks], material, tint)

    return base + rise


def roof(b: Builder, plan: Plan) -> float:
    """Main hipped roof behind the parapet with an eave over the plain back, ridge tiles and chimneys."""
    minimum = (-plan.half + ROOF_INSET, ROOF_INSET)
    maximum = (plan.half - ROOF_INSET, plan.depth + BACK_EAVE)
    ridge = hip(b, minimum, maximum, CORNICE_TOP - 0.15, ROOF_PITCH, "tiles", ROOF_TILE)
    ridge_half = (maximum[0] - minimum[0]) / 2.0 - (maximum[1] - minimum[1]) / 2.0
    middle = (minimum[1] + maximum[1]) / 2.0

    b.cylinder((-ridge_half, middle, ridge), 0.14, 2.0 * ridge_half, 8, "tiles", srgb(town.ROOFS["velha"]), axis="X")

    for u in (-plan.half * 0.62, plan.half * 0.62, -plan.half * 0.2):
        chimney_base = CORNICE_TOP
        b.box((u - 0.45, plan.depth - 4.2, chimney_base), (u + 0.45, plan.depth - 3.4, ridge - 0.6), "plaster", srgb("F4EFE6"))
        b.box((u - 0.55, plan.depth - 4.3, ridge - 0.6), (u + 0.55, plan.depth - 3.3, ridge - 0.45), "plaster", TRIM)
        b.box((u - 0.4, plan.depth - 4.15, ridge - 0.45), (u + 0.4, plan.depth - 3.45, ridge - 0.3), "tiles", ROOF_TILE)

    return ridge


def back_eave(b: Builder, plan: Plan) -> None:
    """Simple cornice and wooden rafter tails (cachorros) under the back eave."""
    frame = plan.frames["back"]

    cornice(b, frame, plan.lengths["back"], with_dentils=False)

    for index in range(int(plan.lengths["back"] / 0.7)):
        s = (index + 0.5) * 0.7
        b.box((s - 0.06, -BACK_EAVE + 0.05, CORNICE_TOP - 0.2), (s + 0.06, -0.5, CORNICE_TOP - 0.05), "wood", srgb(WOOD["escura"]), frame=frame)


def mirante(b: Builder, plan: Plan, ridge: float) -> None:
    """Lookout room on the ridge over the pediment: arched windows all round, corner pilasters, cornice and a
    small hipped roof with a finial."""
    centre_d = plan.depth / 2.0
    bottom = ridge - 1.2
    top = ridge + MIRANTE_STOREY
    half = MIRANTE_HALF
    sides = {
        "front": Matrix.Translation((-half, centre_d - half, 0.0)),
        "right": Matrix.Translation((half, centre_d - half, 0.0)) @ Matrix.Rotation(math.pi / 2.0, 4, "Z"),
        "back": Matrix.Translation((half, centre_d + half, 0.0)) @ Matrix.Rotation(math.pi, 4, "Z"),
        "left": Matrix.Translation((-half, centre_d + half, 0.0)) @ Matrix.Rotation(-math.pi / 2.0, 4, "Z"),
    }

    b.box((-half, centre_d - half, bottom), (half, centre_d + half, top), "plaster", srgb("F4EFE6"))

    for frame in sides.values():
        for s in (half - 1.2, half + 1.2):
            arched_window(b, frame, Opening(s, 0.9, ridge + 0.6, 2.1, "round"), 0.0, 2)

        for s in (0.25, 2.0 * half - 0.25):
            b.box((s - 0.25, -0.1, bottom), (s + 0.25, 0.0, top), "plaster", TRIM, frame=frame)

        profile = [(0.0, top - 0.25), (-0.2, top - 0.15), (-0.32, top), (0.0, top)]
        b.side_prism(profile, -0.3, 2.0 * half + 0.3, "plaster", TRIM, frame=frame)

    roof_top = hip(b, (-half - 0.35, centre_d - half - 0.35), (half + 0.35, centre_d + half + 0.35), top, 32.0, "tiles", ROOF_TILE)
    b.cylinder((0.0, centre_d, roof_top - 0.05), 0.08, 0.5, 8, "metal", IRON)
    b.sphere((0.0, centre_d, roof_top + 0.55), 0.12, "paint", GOLD)


# ---------- assembly ----------

def build_casarao() -> dict:
    plan = Plan()
    b = Builder("casarao")
    b.materials["azulejo"] = town.textured_material("M_TownAzulejo", azulejo_texture(), roughness=0.35)
    street_sides = ("front", "right", "left")
    posts = {"front": front_pilasters(plan), "right": corner_pilasters(plan.depth), "left": corner_pilasters(plan.depth)}

    b.collider((-plan.half, 0.0, BODY_TOP), (plan.half, plan.depth, CORNICE_TOP))
    joint_walls(b, plan)

    for side in street_sides:
        frame = plan.frames[side]
        length = plan.lengths[side]

        plinth(b, plan, side)
        clad(b, plan, side, 0)
        clad(b, plan, side, 1)
        keystones_and_fanlights(b, plan, side)
        dress_upper_storey(b, plan, side)
        string_course(b, frame, length, LEVELS[1])
        cornice(b, frame, length, with_dentils=True)

        for moulding_bottom in (LEVELS[1] - STRING_COURSE / 2.0, WALL_TOP):
            azulejo_band(b, frame, length, moulding_bottom)
        parapet(b, plan, side, posts[side])

        for s in posts[side]:
            width = CORNER_PILASTER if s in corner_pilasters(length) else PILASTER
            pilaster(b, frame, s, width, 0.0, WALL_TOP)

    for s in front_pilasters(plan)[1:-1]:
        if any(abs(s - plan.half - door) < 3.0 for door in plan.doors):
            wall_lantern(b, plan.frames["front"], s, 3.6)

    back = plan.frames["back"]
    plinth(b, plan, "back")
    back_shutters(b, plan)
    string_course(b, back, plan.lengths["back"], LEVELS[1])
    back_eave(b, plan)

    for s in corner_pilasters(plan.lengths["back"]) + [plan.half - edge for edge in plan.hall_edges[1:-1]]:
        pilaster(b, back, s, PILASTER, 0.0, WALL_TOP)

    pediment(b, plan)

    for span in attic_spans(plan):
        attic(b, plan, span)
    ridge = roof(b, plan)
    mirante(b, plan, ridge)

    return b.finish(OUTPUT, {"halls": list(plan.rooms), "half": round(plan.half, 3), "depth": round(plan.depth, 3)})


if __name__ == "__main__":
    sidecar = build_casarao()
    print(f"BUILT casarao: aabb {sidecar['aabb_min']} .. {sidecar['aabb_max']}")
