"""Inside of the casa-grande (farm_sede.py): hollow outer walls with real window and door gaps, board floor, a
plank ceiling (forro), whitewashed partitions with framed doorways, and the furniture of each room.

Plan, in the house frame (x along the front, -8.4..8.4; y from the front wall 0 to the back wall 9.4):
front band  A1 boy's room | A2 girl's room | B sala de visitas (front door) | C escritório
back band   D cozinha     |                | E sala de jantar (back door)    | F quarto do casal
A spine wall at y 4.6 opens on an arch between the two salas; cross walls at x +-3.6 have a door in each band;
the boys pass through the girls' room (alcova, as in old farmhouses)."""

import importlib
import math

from mathutils import Matrix, Vector

from build_town_houses import WOOD, Builder, srgb
from farm_colonial import CAIADO, CREAM, PLANK_UV, TIMBER, TIMBER_UV

PROP_MODULES = ("shop_props_common", "shop_props_food", "shop_props_manor", "shop_props_orphanage", "shop_props_farm")
WALL = 0.35  # outer walls (taipa de pilão rebocada)
PARTITION = 0.15
FLOOR_RISE = 0.02
FORRO = 0.12
BOARD = 0.28
DOOR_WIDTH = 0.9
DOOR_HEIGHT = 2.2
ARCH = (0.0, 2.0, 2.7)  # (x, width, height) of the opening between the two salas
DOOR_JAMB = 0.08
SPINE_Y = 4.6
CROSS_X = (-3.6, 3.6)
ALCOVE_X = -6.0
FRONT_DOOR_Y = 3.4  # doors in the cross walls, front band
BACK_DOOR_Y = 7.6  # and back band
ALCOVE_DOOR_Y = 3.6
LAMP_TINT = "FFC98A"


def load_props() -> dict:
    props = {}

    for module_name in PROP_MODULES:
        props.update(importlib.import_module(module_name).PROPS)

    return props


PROPS = load_props()


class Rooms:
    """Heights of the house and a placer for props by name (front -y, origin on the floor)."""

    def __init__(self, b: Builder, half: float, depth: float, floor: float, ceiling: float) -> None:
        self.b = b
        self.half, self.depth = half, depth
        self.floor = floor
        self.ceiling = ceiling

    def put(self, name: str, x: float, y: float, degrees: float = 0.0, z: float = None, **options) -> None:
        entry = PROPS[name]
        width, depth, height = entry["size"]
        origin_z = z if z is not None else (self.ceiling if entry.get("hang") else self.floor)
        frame = Matrix.Translation((x, y, origin_z)) @ Matrix.Rotation(math.radians(degrees), 4, "Z")

        entry["build"](self.b, frame, **options)

        if entry.get("solid"):
            self.b.collider((-width / 2.0, -depth / 2.0, 0.0), (width / 2.0, depth / 2.0, min(height, 2.4)), frame)

        if entry.get("light"):
            position, color, energy, light_range = entry["light"]
            self.b.light(tuple(frame @ Vector(position)), color, energy, light_range)

    def against(self, wall: str, name: str, along: float, at: float, **options) -> None:
        """Prop with its back to a wall face: wall is the side the wall is on (north +y, south -y, east +x, west -x)."""
        reach = PROPS[name]["size"][1] / 2.0 + 0.03
        spots = {"north": (along, at - reach, 0.0), "south": (along, at + reach, 180.0), "east": (at - reach, along, -90.0), "west": (at + reach, along, 90.0)}
        x, y, degrees = spots[wall]

        self.put(name, x, y, degrees, **options)


# ---------- shell ----------

def hollow_wall(b: Builder, frame: Matrix, u_from: float, u_to: float, base: float, top: float, openings: list, thickness: float = WALL) -> None:
    """Outer wall in its facade frame (outer face on d = 0, thickness toward +d) with a real gap per opening."""
    plaster = srgb(CAIADO)
    edges = sorted((opening.u - opening.width / 2.0, opening.u + opening.width / 2.0) for opening in openings)
    solid_from = [u_from] + [right for _, right in edges]
    solid_to = [left for left, _ in edges] + [u_to]

    for low, high in zip(solid_from, solid_to):
        wall_block(b, (low, 0.0, base), (high, thickness, top), plaster, frame)

    for opening in openings:
        left, right = opening.u - opening.width / 2.0, opening.u + opening.width / 2.0

        if opening.bottom > base + 1e-3:
            wall_block(b, (left, 0.0, base), (right, thickness, opening.bottom), plaster, frame)

        wall_block(b, (left, 0.0, opening.apex), (right, thickness, top), plaster, frame)

        if opening.top != "flat":
            b.prism(opening.arc() + [(left, opening.apex), (right, opening.apex)], 0.0, thickness, "plaster", plaster, frame=frame)


def wall_block(b: Builder, minimum: tuple, maximum: tuple, tint: tuple, frame: Matrix = None) -> None:
    b.box(minimum, maximum, "plaster", tint, frame=frame)
    b.collider(minimum, maximum, frame)


def floor_and_forro(b: Builder, rooms: Rooms) -> None:
    """Wide boards on the floor (with the plinth's collider under them) and a plank forro with a cornice strip."""
    low_x, high_x, low_y, high_y = -rooms.half + WALL, rooms.half - WALL, WALL, rooms.depth - WALL

    boards(b, (low_x, high_x, low_y, high_y), rooms.floor - FLOOR_RISE, rooms.floor, WOOD["media"])
    b.collider((-rooms.half, 0.0, 0.0), (rooms.half, rooms.depth, rooms.floor))
    boards(b, (low_x, high_x, low_y, high_y), rooms.ceiling, rooms.ceiling + FORRO, WOOD["mel"])


def boards(b: Builder, rectangle: tuple, bottom: float, top: float, tint: str) -> None:
    """Boards running front to back (along y), BOARD wide with a hairline gap: a single slab would stretch the
    plank texture across the whole house."""
    low_x, high_x, low_y, high_y = rectangle
    count = max(1, round((high_x - low_x) / BOARD))
    width = (high_x - low_x) / count

    for index in range(count):
        left = low_x + index * width

        b.box((left + 0.004, low_y, bottom), (left + width - 0.004, high_y, top), "wood", srgb(tint), uv=PLANK_UV)


def partition_x(b: Builder, rooms: Rooms, x: float, y_from: float, y_to: float, doors: tuple) -> None:
    """Partition running along y at x, with framed doorways centred at the given y."""
    gaps = sorted((door_y - DOOR_WIDTH / 2.0, door_y + DOOR_WIDTH / 2.0) for door_y in doors)
    solid = zip([y_from] + [high for _, high in gaps], [low for low, _ in gaps] + [y_to])
    half = PARTITION / 2.0

    for low, high in solid:
        wall_block(b, (x - half, low, rooms.floor), (x + half, high, rooms.ceiling), srgb(CAIADO))

    for low, high in gaps:
        wall_block(b, (x - half, low, rooms.floor + DOOR_HEIGHT), (x + half, high, rooms.ceiling), srgb(CAIADO))
        door_frame(b, Matrix.Translation((x, (low + high) / 2.0, rooms.floor)) @ Matrix.Rotation(math.pi / 2.0, 4, "Z"), DOOR_WIDTH, DOOR_HEIGHT)


def partition_y(b: Builder, rooms: Rooms, y: float, x_from: float, x_to: float, gaps: tuple) -> None:
    """Partition running along x at y; gaps = (x, width, height)."""
    edges = sorted((gap_x - width / 2.0, gap_x + width / 2.0, height) for gap_x, width, height in gaps)
    solid = zip([x_from] + [high for _, high, _ in edges], [low for low, _, _ in edges] + [x_to])
    half = PARTITION / 2.0

    for low, high in solid:
        wall_block(b, (low, y - half, rooms.floor), (high, y + half, rooms.ceiling), srgb(CAIADO))

    for low, high, height in edges:
        wall_block(b, (low, y - half, rooms.floor + height), (high, y + half, rooms.ceiling), srgb(CAIADO))
        door_frame(b, Matrix.Translation(((low + high) / 2.0, y, rooms.floor)), high - low, height)


def door_frame(b: Builder, frame: Matrix, width: float, height: float) -> None:
    """Dark timber jambs and lintel around a doorway, standing proud of both faces of a partition."""
    half = width / 2.0
    reach = PARTITION / 2.0 + 0.03
    timber = srgb(TIMBER)

    for low, high in ((-half - DOOR_JAMB, -half), (half, half + DOOR_JAMB)):
        b.box((low, -reach, 0.0), (high, reach, height), "wood", timber, frame=frame, uv=TIMBER_UV)

    b.box((-half - DOOR_JAMB, -reach, height), (half + DOOR_JAMB, reach, height + DOOR_JAMB * 1.5), "wood", timber, frame=frame, uv=TIMBER_UV)


def partitions(b: Builder, rooms: Rooms) -> None:
    low_x, high_x, low_y, high_y = -rooms.half + WALL, rooms.half - WALL, WALL, rooms.depth - WALL
    half = PARTITION / 2.0

    partition_y(b, rooms, SPINE_Y, low_x, high_x, (ARCH,))

    for x in CROSS_X:
        partition_x(b, rooms, x, low_y, SPINE_Y - half, (FRONT_DOOR_Y,))
        partition_x(b, rooms, x, SPINE_Y + half, high_y, (BACK_DOOR_Y,))

    partition_x(b, rooms, ALCOVE_X, low_y, SPINE_Y - half, (ALCOVE_DOOR_Y,))
    cornice_strips(b, rooms)


def cornice_strips(b: Builder, rooms: Rooms) -> None:
    """Cream moulding where the forro meets the outer walls."""
    low_x, high_x, low_y, high_y = -rooms.half + WALL, rooms.half - WALL, WALL, rooms.depth - WALL
    top, bottom = rooms.ceiling, rooms.ceiling - 0.1
    strips = (((low_x, low_y, bottom), (high_x, low_y + 0.06, top)), ((low_x, high_y - 0.06, bottom), (high_x, high_y, top)), ((low_x, low_y, bottom), (low_x + 0.06, high_y, top)), ((high_x - 0.06, low_y, bottom), (high_x, high_y, top)))

    for minimum, maximum in strips:
        b.box(minimum, maximum, "trim", srgb(CREAM))


# ---------- rooms ----------

def furnish(rooms: Rooms) -> None:
    for room in (boys_room, girls_room, sala_de_visitas, escritorio, cozinha, sala_de_jantar, quarto_do_casal):
        room(rooms)


def inner_faces() -> dict:
    """Face of each wall on the room side, by name."""
    half = PARTITION / 2.0

    return {"front": WALL, "back": 9.4 - WALL, "west": -8.4 + WALL, "east": 8.4 - WALL, "spine_front": SPINE_Y - half, "spine_back": SPINE_Y + half, "cross_west_w": CROSS_X[0] - half, "cross_west_e": CROSS_X[0] + half, "cross_east_w": CROSS_X[1] - half, "cross_east_e": CROSS_X[1] + half, "alcove_w": ALCOVE_X - half, "alcove_e": ALCOVE_X + half}


FACE = inner_faces()


def boys_room(rooms: Rooms) -> None:
    rooms.against("north", "iron_bed", -7.45, FACE["spine_front"], variant="grey_blue")
    rooms.against("north", "night_table", -6.55, FACE["spine_front"])
    rooms.put("bed_trunk", -7.45, 2.35)
    rooms.against("east", "wardrobe", 1.15, FACE["alcove_w"])
    rooms.against("north", "wall_crucifix", -7.45, FACE["spine_front"] - 0.02)
    rooms.put("hanging_oil_lamp", -7.0, 2.4)


def girls_room(rooms: Rooms) -> None:
    rooms.against("north", "iron_bed", -4.75, FACE["spine_front"], variant="dull_red")
    rooms.against("north", "night_table", -3.95, FACE["spine_front"])
    rooms.put("bed_trunk", -4.75, 2.35)
    rooms.against("east", "washstand", 1.3, FACE["cross_west_w"])
    rooms.against("west", "dollhouse", 1.25, FACE["alcove_e"])
    rooms.put("hanging_oil_lamp", -4.8, 2.4)


def sala_de_visitas(rooms: Rooms) -> None:
    rooms.against("west", "cane_settee", 1.75, FACE["cross_west_e"])
    rooms.put("rug", -2.35, 1.75, 90.0, variant="red")
    rooms.put("armchair", -1.55, 1.15, -90.0)
    rooms.put("armchair", -1.55, 2.35, -90.0)
    rooms.against("north", "home_oratory", -2.4, FACE["spine_front"])
    rooms.against("east", "piano", 1.65, FACE["cross_east_w"])
    rooms.against("north", "console_table", 2.55, FACE["spine_front"])
    rooms.against("north", "wall_mirror", 2.55, FACE["spine_front"] - 0.02)
    rooms.against("north", "long_case_clock", 1.45, FACE["spine_front"])

    for window_x in (-2.4, 2.4):
        rooms.against("south", "curtain_pair", window_x, FACE["front"], variant="wine")

    rooms.put("hanging_oil_lamp", 0.0, 2.3)


def escritorio(rooms: Rooms) -> None:
    rooms.put("director_desk", 6.3, 2.2, -90.0)
    rooms.against("east", "filing_cabinet", 3.75, FACE["east"])
    rooms.against("north", "wall_map", 5.6, FACE["spine_front"])
    rooms.against("north", "chest_gold", 4.4, FACE["spine_front"])
    rooms.put("bentwood_chair", 4.9, 2.2, 90.0)
    rooms.put("hanging_oil_lamp", 5.9, 2.4)


def cozinha(rooms: Rooms) -> None:
    rooms.against("south", "masonry_range", -5.9, FACE["spine_back"])
    rooms.against("west", "stone_sink", 6.0, FACE["west"])
    rooms.against("west", "water_filter", 8.5, FACE["west"])
    rooms.against("east", "pantry_shelf", 5.95, FACE["cross_west_w"])
    rooms.put("kitchen_worktable", -5.8, 7.05)
    rooms.put("pilao", -4.15, 8.55)
    rooms.put("hanging_oil_lamp", -5.8, 7.0)


def sala_de_jantar(rooms: Rooms) -> None:
    rooms.put("long_table_set", 0.0, 6.85)

    for chair_x in (-1.25, -0.42, 0.42, 1.25):
        rooms.put("bentwood_chair", chair_x, 7.6, 0.0)
        rooms.put("bentwood_chair", chair_x, 6.1, 180.0)
    rooms.against("west", "crockery_dresser", 5.85, FACE["cross_west_e"])
    rooms.against("east", "console_table", 5.85, FACE["cross_east_w"])
    rooms.put("hanging_oil_lamp", -0.9, 6.85)
    rooms.put("hanging_oil_lamp", 0.9, 6.85)


def quarto_do_casal(rooms: Rooms) -> None:
    rooms.against("south", "bed_canopy", 5.95, FACE["spine_back"])
    rooms.against("south", "night_table", 4.75, FACE["spine_back"])
    rooms.against("east", "wardrobe", 5.35, FACE["east"])
    rooms.against("west", "washstand", 6.2, FACE["cross_east_e"])
    rooms.put("bed_trunk", 5.95, 7.25)
    rooms.put("hanging_oil_lamp", 5.9, 6.9)


def build_rooms(b: Builder, half: float, depth: float, base: float, wall_top: float) -> None:
    rooms = Rooms(b, half, depth, base + FLOOR_RISE, wall_top - FORRO)

    floor_and_forro(b, rooms)
    partitions(b, rooms)
    furnish(rooms)
