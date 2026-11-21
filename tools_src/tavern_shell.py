"""Shell of the tavern and inn: a timber-framed house of real rooms instead of the open shop hall.

Ground floor after tavern_layout.ROOMS: hall, taproom, Stube, kitchen, store and music room under a low ceiling of
dark joists and summer beams on white plaster (the Stube under a boarded, ribbed ceiling and panelled to the plate
shelf); leaded casement windows, no awnings; outside a timber frame on the ground storey, a gabled hood over the
door, benches and barrels, the jettied upper floor and a second chimney for the kitchen range.

build_market_shops.py calls build_shell() for the "tavern" entry of SHOPS (shell="tavern_shell").
"""

import math

from mathutils import Matrix

import build_market_shops as shops
import build_town_houses as town
from build_town_houses import WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, Opening, srgb
from tavern_layout import FRONT_WINDOWS, PANELLED, PLASTERED, ROOMS, WAINSCOT, WINDOW

shops.WALL_FINISHES.update({
    WAINSCOT: dict(dado="8B5A3C", trim="4A2E1E", material="wood", uv=("band", *WOOD_LIGHT_BAND, 1.5)),
    PLASTERED: dict(dado="D9CDB4", trim="6B4A32"),
    PANELLED: dict(dado="C98B52", trim="7A4A2C", material="wood", uv=("band", *WOOD_LIGHT_BAND, 1.5)),
})
BEAMED_ROOMS = ("taproom", "kitchen", "hall", "store", "music")
JOIST_PITCH = 0.55
JOIST = (0.12, 0.16)  # width, depth under the plaster
SUMMER = (0.3, 0.32)  # the summer beam down the middle of a room
COFFER_PITCH = 1.5
CEILING_BOARD = 0.25
STUBE_BOARD_SHADES = (1.0, 0.9, 1.06, 0.95)
CEILING_PLASTER = srgb("F2EBDD")
OAK = srgb("5A3A26")
STUBE_BOARDS = srgb("C98B52")
STUBE_RIBS = srgb("8B5A3C")
PANEL_BAND = (shops.DADO_HEIGHT + shops.RAIL_HEIGHT, 2.25)  # the Stube is panelled up to its plate shelf
BATTEN_PITCH = 0.6
LEAD = srgb("3A3238")
LEAD_PANE = (0.26, 0.3)  # leaded lights: pane width, height
FRAME_POSTS = (-8.85, -5.6, -2.6, 2.6, 5.6, 8.85)  # u of the oak posts on the ground storey of the facade
HOOD = dict(half=1.2, reach=0.95, eave=2.95, rise=0.55)  # gabled hood over the street door
STREET_PROPS = (("bench_long", -5.6, -0.3), ("bench_long", 5.6, -0.3), ("barrel_group", -2.6, -0.62), ("barrel_group", 2.6, -0.62))
KITCHEN_CHIMNEY = (-7.1, 18.6)
LIGHTS = ((-5.5, 3.5), (-5.5, 9.5), (0.0, 6.5), (5.5, 13.8), (-5.5, 15.8))  # one or two lamps a room (the Stube has its chandelier)
LAMP_DROP = 0.7


def front_openings(room) -> list:
    """Street door in the middle and two casement windows to each front room (wall-local u = facade u + half)."""
    door_u, door_width, door_height, door_top = room.door
    width, sill, height = WINDOW
    windows = [Opening(u + room.half, width, sill, height, "flat", kind="vitrine") for u in FRONT_WINDOWS]

    return [Opening(door_u + room.half, door_width, 0.0, door_height, door_top, kind="door")] + windows


def leaded_lights(b: Builder, frame: Matrix, opening: Opening) -> None:
    """Lead cames over the glass of a window: a grid of small panes (casements of the period)."""
    columns = max(2, round(opening.width / LEAD_PANE[0]))
    rows = max(2, round((opening.spring - opening.bottom) / LEAD_PANE[1]))
    left = opening.u - opening.width / 2.0
    verticals = [left + opening.width * index / columns for index in range(1, columns)]
    horizontals = [opening.bottom + (opening.spring - opening.bottom) * index / rows for index in range(1, rows)]

    for u in verticals:
        b.box((u - 0.012, 0.1, opening.bottom), (u + 0.012, 0.12, opening.spring), "metal", LEAD, frame=frame)

    for z in horizontals:
        b.box((left, 0.1, z - 0.012), (left + opening.width, 0.12, z + 0.012), "metal", LEAD, frame=frame)


def build_walls(b: Builder, room) -> dict:
    """The four outer walls with the street door and casements, lead cames on every window; returns the openings."""
    openings = {"front": front_openings(room), **shops.wall_windows(room)}
    frames = shops.wall_frames(room)
    windows = [(side, opening) for side, found in openings.items() for opening in found if opening.kind == "vitrine"]

    shops.build_walls(b, room, openings)

    for side, opening in windows:
        leaded_lights(b, frames[side], opening)

    return openings


def build_floor(b: Builder, room) -> None:
    """Staggered plank floor, flagstones in the hall, the kitchen and the store."""
    board_count = round((room.right - room.left) / shops.BOARD_WIDTH)

    shops.build_plank_floor(b, room, board_count, (room.right - room.left) / board_count)
    b.collider((room.left, room.front, 0.0), (room.right, room.back, shops.FLOOR_TOP), name="WoodFloor")

    for u_from, u_to, d_from, d_to in room.plan["stone_floors"]:
        top = shops.FLOOR_TOP + shops.STONE_PATCH_LIFT
        b.box((u_from, d_from, shops.FLOOR_TOP), (u_to, d_to, top), "stone", srgb(town.STONE["dourada"]), uv=("world", 1.2))
        b.collider((u_from, d_from, shops.FLOOR_TOP), (u_to, d_to, top), name="StoneFloor")


def build_ceiling(b: Builder, room) -> None:
    """Plaster under the upper floor, joists and a summer beam in the working rooms, boards and ribs in the Stube.
    Its collider comes down to the underside of the summer beams: the camera arm stops under them."""
    b.box((room.left, room.front, room.ceiling), (room.right, room.back, room.storey), "plaster", CEILING_PLASTER)
    b.collider((room.left, room.front, room.ceiling - SUMMER[1]), (room.right, room.back, room.storey))

    for name in BEAMED_ROOMS:
        beamed_ceiling(b, room, ROOMS[name])

    coffered_ceiling(b, room, ROOMS["stube"])


def beamed_ceiling(b: Builder, room, bounds: tuple) -> None:
    u_from, u_to, d_from, d_to = bounds
    joist_count = int((d_to - d_from) / JOIST_PITCH)
    middle = (u_from + u_to) / 2.0
    beam_uv = ("band", *WOOD_DARK_BAND, 1.5)

    for index in range(joist_count):
        d = d_from + (d_to - d_from) * (index + 0.5) / joist_count
        b.box((u_from, d - JOIST[0] / 2.0, room.ceiling - JOIST[1]), (u_to, d + JOIST[0] / 2.0, room.ceiling), "wood", OAK, uv=beam_uv)

    b.box((middle - SUMMER[0] / 2.0, d_from, room.ceiling - SUMMER[1]), (middle + SUMMER[0] / 2.0, d_to, room.ceiling), "wood", OAK, uv=beam_uv)


def coffered_ceiling(b: Builder, room, bounds: tuple) -> None:
    u_from, u_to, d_from, d_to = bounds
    u_ribs = [u_from + (u_to - u_from) * index / round((u_to - u_from) / COFFER_PITCH) for index in range(1, round((u_to - u_from) / COFFER_PITCH))]
    d_ribs = [d_from + (d_to - d_from) * index / round((d_to - d_from) / COFFER_PITCH) for index in range(1, round((d_to - d_from) / COFFER_PITCH))]
    rib_uv = ("band", *WOOD_DARK_BAND, 1.0)

    board_count = round((u_to - u_from) / CEILING_BOARD)
    board_width = (u_to - u_from) / board_count

    for board in range(board_count):
        shade = STUBE_BOARD_SHADES[board % len(STUBE_BOARD_SHADES)]
        tint = tuple(shade * channel for channel in STUBE_BOARDS)
        b.box((u_from + board * board_width, d_from, room.ceiling - 0.04), (u_from + (board + 1) * board_width - 0.01, d_to, room.ceiling), "wood", tint, uv=("band", *WOOD_LIGHT_BAND, 2.0))

    for u in u_ribs:
        b.box((u - 0.06, d_from, room.ceiling - 0.14), (u + 0.06, d_to, room.ceiling - 0.04), "wood", STUBE_RIBS, uv=rib_uv)

    for d in d_ribs:
        b.box((u_from, d - 0.06, room.ceiling - 0.14), (u_to, d + 0.06, room.ceiling - 0.04), "wood", STUBE_RIBS, uv=rib_uv)


def outer_faces(room) -> list:
    """(axis, face, normal, span, finish, windows) of every room's stretch of the outer walls; windows as
    (from, to, bottom, top) along it."""
    spans = shops.window_spans(room)
    width, sill, height = WINDOW
    door_half = room.door[1] / 2.0 + town.FRAME_DEPTH + 0.18
    front = [(u - width / 2.0 - 0.1, u + width / 2.0 + 0.1, sill, sill + height) for u in FRONT_WINDOWS] + [(room.door[0] - door_half, room.door[0] + door_half, 0.0, room.door[2])]
    walls = {
        "front": ("d", room.front, 1, front),
        "back": ("d", room.back, -1, [(start - 0.1, end + 0.1, bottom, bottom + 1.4) for start, end, bottom in spans["back"]]),
        "left": ("u", room.left, 1, [(start - 0.1, end + 0.1, bottom, bottom + WINDOW[2]) for start, end, bottom in spans["left"]]),
        "right": ("u", room.right, -1, []),
    }
    stretches = (
        ("taproom", "front", WAINSCOT), ("taproom", "left", WAINSCOT), ("hall", "front", WAINSCOT), ("stube", "front", PANELLED), ("stube", "right", PANELLED),
        ("kitchen", "left", PLASTERED), ("kitchen", "back", PLASTERED), ("store", "back", PLASTERED), ("music", "right", WAINSCOT), ("music", "back", WAINSCOT),
    )
    along = lambda name, side: ROOMS[name][:2] if side in ("front", "back") else ROOMS[name][2:]

    return [(walls[side][0], walls[side][1], walls[side][2], along(name, side), finish, walls[side][3]) for name, side, finish in stretches]


def cuts_at(windows: list, height: float) -> list:
    return [(start, end) for start, end, bottom, top in windows if bottom < height < top + 0.1]


def build_finishes(b: Builder, room) -> None:
    """Dado, rails and cornice on the outer walls room by room; the Stube panelled up to its plate shelf."""
    for axis, face_at, normal, span, finish, windows in outer_faces(room):
        shops.dress_wall_face(b, room, axis, face_at, normal, span, finish, cuts_at(windows, shops.DADO_HEIGHT), cuts_at(windows, shops.PICTURE_RAIL_HEIGHT))

    stube_faces = [face for face in outer_faces(room) if face[4] == PANELLED] + stube_partition_faces()
    pieces = [(axis, face_at, normal, piece) for axis, face_at, normal, span, _, windows in stube_faces for piece in shops.free_spans(*span, cuts_at(windows, PANEL_BAND[1] - 0.1))]

    for axis, face_at, normal, piece in pieces:
        panel_stretch(b, axis, face_at, normal, piece)


def stube_partition_faces() -> list:
    """The Stube's faces of its two inner walls, the door to the hall cut out."""
    u_from, u_to, d_from, d_to = ROOMS["stube"]

    return [("u", u_from, 1, (d_from, d_to), PANELLED, [(5.2, 6.8, 0.0, 2.4)]), ("d", d_to, -1, (u_from, u_to), PANELLED, [])]


def panel_stretch(b: Builder, axis: str, face_at: float, normal: int, piece: tuple) -> None:
    """Upper panelling of one stretch: boards over the dado rail, battens every BATTEN_PITCH and a capping board."""
    battens = [piece[0] + (piece[1] - piece[0]) * index / max(1, round((piece[1] - piece[0]) / BATTEN_PITCH)) for index in range(1, max(1, round((piece[1] - piece[0]) / BATTEN_PITCH)))]
    wood_uv = ("band", *WOOD_LIGHT_BAND, 1.5)

    b.box(*shops.wall_slab(axis, face_at, normal, piece, 0.0, 0.02, PANEL_BAND), "wood", STUBE_BOARDS, uv=wood_uv)
    b.box(*shops.wall_slab(axis, face_at, normal, piece, 0.0, 0.06, (PANEL_BAND[1], PANEL_BAND[1] + 0.05)), "wood", STUBE_RIBS, uv=wood_uv)

    for batten in battens:
        b.box(*shops.wall_slab(axis, face_at, normal, (batten - 0.03, batten + 0.03), 0.02, 0.02, (0.14, PANEL_BAND[1])), "wood", STUBE_RIBS, uv=wood_uv)


# ---------- outside ----------

def build_street_front(b: Builder, room) -> None:
    """Oak posts, sill and head beam on the ground storey of the facade, the door hood, benches and barrels."""
    house = room.house
    beam_uv = ("band", *WOOD_DARK_BAND, 1.5)
    gaps = [(u - WINDOW[0] / 2.0 - 0.12, u + WINDOW[0] / 2.0 + 0.12) for u in FRONT_WINDOWS] + [(-room.door[1] / 2.0 - 0.3, room.door[1] / 2.0 + 0.3)]
    rails = shops.free_spans(-house.half, house.half, gaps)

    for u in FRAME_POSTS:
        b.box((u - 0.09, -0.09, shops.PLINTH_HEIGHT), (u + 0.09, 0.0, room.storey - 0.22), "wood", house.wood_tint, uv=beam_uv)

    b.box((-house.half, -0.1, room.storey - 0.42), (house.half, 0.0, room.storey - 0.22), "wood", house.wood_tint, uv=beam_uv)

    for rail_from, rail_to in rails:
        b.box((rail_from, -0.09, shops.PLINTH_HEIGHT + 0.85), (rail_to, 0.0, shops.PLINTH_HEIGHT + 0.97), "wood", house.wood_tint, uv=beam_uv)

    build_door_hood(b, room)

    for name, u, d in STREET_PROPS:
        width, depth, height = shops.PROPS[name]["size"]
        frame = Matrix.Translation((u, d, 0.0))

        shops.PROPS[name]["build"](b, frame)
        b.collider((-width / 2.0, -depth / 2.0, 0.0), (width / 2.0, depth / 2.0, height), frame)


def build_door_hood(b: Builder, room) -> None:
    """Small gabled hood on two carved brackets over the street door; the camera stops under it."""
    house = room.house
    half, reach, eave, rise = HOOD["half"], HOOD["reach"], HOOD["eave"], HOOD["rise"]
    slopes = ([(-half - 0.1, eave), (0.0, eave + rise), (0.0, eave + rise + 0.1), (-half - 0.1, eave + 0.1)], [(half + 0.1, eave), (half + 0.1, eave + 0.1), (0.0, eave + rise + 0.1), (0.0, eave + rise)])

    for slope in slopes:
        b.camera_stop(b.prism(slope, -reach, 0.0, house.roof_material, house.roof_tint))

    b.prism([(-half, eave), (half, eave), (0.0, eave + rise)], -reach + 0.04, -reach + 0.08, house.wall_material, house.wall_tint)
    b.box((-half, -reach + 0.02, eave - 0.14), (half, -reach + 0.12, eave), "wood", house.wood_tint, uv=("band", *WOOD_DARK_BAND, 1.5))

    for side_sign in (-1, 1):
        u = side_sign * (half - 0.08)
        b.side_prism([(0.0, eave - 0.9), (0.0, eave), (-reach + 0.05, eave)], u - 0.06, u + 0.06, "wood", house.wood_tint)


def build_kitchen_chimney(b: Builder, room) -> None:
    """Second stack for the kitchen range, rising through the back slope of the roof."""
    house = room.house
    options = room.spec["roof_shape"][1]
    back_eave = house.depth + options["eave_back"]
    roof_there = house.top - 0.12 + (back_eave - KITCHEN_CHIMNEY[1]) * math.tan(math.radians(options["pitch"]))

    town.draw_chimney(b, house, KITCHEN_CHIMNEY[0], KITCHEN_CHIMNEY[1], roof_there + 1.1, material="brick", pots=1)


# ---------- assembly ----------

def build_shell(room) -> dict:
    b = Builder(f"shop_{room.shop_type}")

    build_walls(b, room)
    build_floor(b, room)
    build_ceiling(b, room)

    for partition in room.partitions:
        shops.build_partition(b, room, partition)

    build_finishes(b, room)
    shops.build_roof(b, room)
    build_street_front(b, room)
    build_kitchen_chimney(b, room)

    for u, d in LIGHTS:
        b.light((u, d, room.ceiling - LAMP_DROP), room.spec["light"], 1.3, 7.0)

    b.marker("shopkeeper", (*room.keeper, 0.0))

    return b.finish(town.SHOP_DIR / f"shop_{room.shop_type}.gltf", shops.shell_sidecar(room))
