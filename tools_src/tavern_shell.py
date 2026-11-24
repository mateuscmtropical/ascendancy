"""Shell of the tavern and inn: a timber-framed house of real rooms instead of the open shop hall.

Ground floor after tavern_layout.ROOMS: the tall tavern hall with its L-shaped terrace a chest-height up (stone
faced, plank topped, the inner corner rounded) and the ramp along the right wall from the street door; the inn's hall
behind its own door on the side street, the kitchen, the pantry and the store, all under dark joists and summer beams
on white plaster. Leaded casement windows, no awnings; outside a timber frame on the ground storey, a gabled hood over
the street door, benches and barrels, the jettied upper floor and a second chimney for the kitchen range.

build_market_shops.py calls build_shell() for the "tavern" entry of SHOPS (shell="tavern_shell").
"""

import math

from mathutils import Matrix

import build_market_shops as shops
import build_town_houses as town
from build_town_houses import WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, Opening, srgb
from tavern_layout import BACK_EDGE, FRONT_WINDOWS, HALL, HALL_BACK, INN_BACK, INN_DOOR, PLASTERED, RAMP, ROOMS, SIDE_EDGE, TERRACE_FILLET, TERRACE_PARTS, TERRACE_TOP, WAINSCOT, WINDOW

shops.WALL_FINISHES.update({
    WAINSCOT: dict(dado="8B5A3C", trim="4A2E1E", material="wood", uv=("band", *WOOD_LIGHT_BAND, 1.5)),
    PLASTERED: dict(dado="D9CDB4", trim="6B4A32"),
})
JOIST_PITCH = 0.55
JOIST = (0.12, 0.16)  # width, depth under the plaster
SUMMER = (0.3, 0.32)  # the summer beam down the middle of a room
CEILING_PLASTER = srgb("F2EBDD")
OAK = srgb("5A3A26")
PANEL_BOARDS = srgb("C98B52")
PANEL_RIBS = srgb("7A4A2C")
PANEL_BAND = (TERRACE_TOP, 2.4)  # boarded dado of the terrace walls, up to just under the picture rail
BATTEN_PITCH = 0.6
LEAD = srgb("3A3238")
LEAD_PANE = (0.26, 0.3)  # leaded lights: pane width, height
FRAME_POSTS = (-8.85, -3.0, 2.1, 5.3, 8.85)  # u of the oak posts on the ground storey of the facade
HOOD = dict(half=1.2, reach=0.95, eave=2.95, rise=0.55)  # gabled hood over a street door
STREET_PROPS = (("bench_long", 0.6, -0.3), ("bench_long", -5.9, -0.3), ("barrel_group", 3.6, -0.62), ("barrel_group", -1.6, -0.62))
KITCHEN_CHIMNEY = (-6.8, HALL_BACK)
LIGHTS = ((3.1, 3.0), (4.8, 11.6), (-5.8, 2.6), (-5.8, 9.5), (-5.8, 16.6), (2.8, 16.6))  # one lamp a room, two in the hall
LAMP_DROP = 0.7
STONE_FACE = srgb(town.STONE["dourada"])
DECK = 0.05  # planks on top of the terrace and of the ramp
RAIL = dict(height=0.95, inset=0.06, pitch=0.14, baluster=0.05, newel=0.12, collider=1.0)
ARC_SEGMENTS = 12
RAMP_CLEAT_PITCH = 0.4
INN_SIGN_OFFSET = 0.45  # from the edge of the inn's door to the arm of its sign, as on the facades


# ---------- walls ----------

def front_openings(room) -> list:
    """Street door at the right end, the inn's window and two to the hall (wall-local u = facade u + half)."""
    door_u, door_width, door_height, door_top = room.door
    width, sill, height = WINDOW
    windows = [Opening(u + room.half, width, sill, height, "flat", kind="vitrine") for u in FRONT_WINDOWS]

    return [Opening(door_u + room.half, door_width, 0.0, door_height, door_top, kind="door")] + windows


def wall_local_left(room, d: float) -> float:
    """Wall-local u of the left (side street) wall at hall depth d."""
    return room.depth - town.WALL - d


def left_openings(room) -> list:
    """The side street wall: its windows (the plan keeps the stretch round the inn's door blind) and that door."""
    door = Opening(wall_local_left(room, INN_DOOR["d"]), INN_DOOR["width"], 0.0, INN_DOOR["height"], "flat", kind="side_door")

    return shops.wall_windows(room)["left"] + [door]


def dress_side_door(b: Builder, room, frame: Matrix, opening: Opening) -> None:
    """The inn's door: stone threshold, moulding and one plank leaf fixed open into its hall."""
    house = room.house
    half = opening.width / 2.0
    leaf = opening.width - 0.04
    swing = math.radians(100.0)
    hinge_u = opening.u - half
    tip = (hinge_u + leaf * math.cos(swing), town.WALL + leaf * math.sin(swing))

    b.box((opening.u - half, -0.1, 0.0), (opening.u + half, town.WALL, shops.FLOOR_TOP + 0.005), "trim", house.trim_tint, frame=frame)  # flush: the lot ends at this wall
    town.open_frame(b, opening, 0.18, -0.06, 0.0, house.trim_tint, town.TRIM_BLOCK_BAND, frame)
    b.beam((hinge_u, town.WALL + 0.03, opening.spring / 2.0), (tip[0], tip[1], opening.spring / 2.0), opening.spring - 0.05, 0.07, "paint", house.accent, frame=frame)


shops.OPENING_DRESSING["side_door"] = dress_side_door


def tavern_openings(room) -> dict:
    return {**shops.wall_windows(room), "front": front_openings(room), "left": left_openings(room) if "left" in room.exposed else []}


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
    """The four outer walls with both doors and the casements, lead cames on every window; returns the openings."""
    openings = tavern_openings(room)
    frames = shops.wall_frames(room)
    windows = [(side, opening) for side, found in openings.items() for opening in found if opening.kind == "vitrine"]

    shops.build_walls(b, room, openings)

    for side, opening in windows:
        leaded_lights(b, frames[side], opening)

    return openings


# ---------- floors and ceilings ----------

def build_floor(b: Builder, room) -> None:
    """Staggered plank floor, flagstones in the inn's hall, the kitchen, the pantry and the store."""
    board_count = round((room.right - room.left) / shops.BOARD_WIDTH)

    shops.build_plank_floor(b, room, board_count, (room.right - room.left) / board_count)
    b.collider((room.left, room.front, 0.0), (room.right, room.back, shops.FLOOR_TOP), name="WoodFloor")

    for u_from, u_to, d_from, d_to in room.plan["stone_floors"]:
        top = shops.FLOOR_TOP + shops.STONE_PATCH_LIFT
        b.box((u_from, d_from, shops.FLOOR_TOP), (u_to, d_to, top), "stone", STONE_FACE, uv=("world", 1.2))
        b.collider((u_from, d_from, shops.FLOOR_TOP), (u_to, d_to, top), name="StoneFloor")


def build_ceiling(b: Builder, room) -> None:
    """Plaster under the upper floor, joists and a summer beam in every room. Its collider comes down to the underside
    of the summer beams: the camera arm stops under them."""
    b.box((room.left, room.front, room.ceiling), (room.right, room.back, room.storey), "plaster", CEILING_PLASTER)
    b.collider((room.left, room.front, room.ceiling - SUMMER[1]), (room.right, room.back, room.storey))

    for bounds in ROOMS.values():
        beamed_ceiling(b, room, bounds)


def beamed_ceiling(b: Builder, room, bounds: tuple) -> None:
    u_from, u_to, d_from, d_to = bounds
    joist_count = int((d_to - d_from) / JOIST_PITCH)
    middle = (u_from + u_to) / 2.0
    beam_uv = ("band", *WOOD_DARK_BAND, 1.5)

    for index in range(joist_count):
        d = d_from + (d_to - d_from) * (index + 0.5) / joist_count
        b.box((u_from, d - JOIST[0] / 2.0, room.ceiling - JOIST[1]), (u_to, d + JOIST[0] / 2.0, room.ceiling), "wood", OAK, uv=beam_uv)

    b.box((middle - SUMMER[0] / 2.0, d_from, room.ceiling - SUMMER[1]), (middle + SUMMER[0] / 2.0, d_to, room.ceiling), "wood", OAK, uv=beam_uv)


# ---------- terrace and ramp ----------

def fillet_points(radius: float) -> list:
    """(u, d) along the rounded inner corner of the L, from the back arm's edge round to the right arm's edge."""
    centre = (SIDE_EDGE - TERRACE_FILLET, BACK_EDGE - TERRACE_FILLET)
    angles = [math.pi / 2.0 * (1.0 - index / ARC_SEGMENTS) for index in range(ARC_SEGMENTS + 1)]

    return [(centre[0] + radius * math.cos(angle), centre[1] + radius * math.sin(angle)) for angle in angles]


def build_terrace(b: Builder) -> None:
    """The two arms of the L as stone blocks under a plank deck, and the rounded corner as wedges fanned from the
    corner of the arms; every piece is walkable (wood footsteps)."""
    plank_uv = ("band", *WOOD_LIGHT_BAND, 2.0)
    deck_from = TERRACE_TOP - DECK
    arc = fillet_points(TERRACE_FILLET)
    corner = (SIDE_EDGE, BACK_EDGE)

    for u_from, u_to, d_from, d_to in TERRACE_PARTS:
        b.box((u_from, d_from, 0.0), (u_to, d_to, deck_from), "stone", STONE_FACE, uv=("world", 1.2))
        b.box((u_from, d_from, deck_from), (u_to, d_to, TERRACE_TOP), "wood", PANEL_BOARDS, uv=plank_uv)
        b.collider((u_from, d_from, 0.0), (u_to, d_to, TERRACE_TOP), name="WoodFloor")

    for start, end in zip(arc, arc[1:]):
        wedge = [corner, start, end]
        body = b.hull([(u, d, 0.0) for u, d in wedge] + [(u, d, deck_from) for u, d in wedge], "stone", STONE_FACE, uv=("world", 1.2))
        deck = b.hull([(u, d, deck_from) for u, d in wedge] + [(u, d, TERRACE_TOP) for u, d in wedge], "wood", PANEL_BOARDS, uv=plank_uv)
        b.solid(body, name="WoodFloor")
        b.solid(deck, name="WoodFloor")


def ramp_frame() -> tuple:
    """Frame on the foot of the ramp's deck (y up the slope), and the sloped length."""
    rise = TERRACE_TOP - shops.FLOOR_TOP
    run = RAMP["d_to"] - RAMP["d_from"]
    middle = (RAMP["u_from"] + RAMP["u_to"]) / 2.0

    return Matrix.Translation((middle, RAMP["d_from"], shops.FLOOR_TOP)) @ Matrix.Rotation(math.atan2(rise, run), 4, "X"), math.hypot(rise, run)


def build_ramp(b: Builder, room) -> None:
    """Stone wedge under a plank deck with cleats every RAMP_CLEAT_PITCH, from the door landing up to the right arm;
    a handrail on brackets along the wall. The sloped collider follows the deck."""
    frame, length = ramp_frame()
    half = (RAMP["u_to"] - RAMP["u_from"]) / 2.0
    cleats = [RAMP_CLEAT_PITCH * index for index in range(1, int(length / RAMP_CLEAT_PITCH))]
    wall_rail_u = RAMP["u_to"] - 0.08
    wood_uv = ("band", *WOOD_DARK_BAND, 1.5)

    b.side_prism([(RAMP["d_from"], 0.0), (RAMP["d_to"], 0.0), (RAMP["d_to"], TERRACE_TOP - DECK), (RAMP["d_from"], shops.FLOOR_TOP - DECK)], RAMP["u_from"], RAMP["u_to"], "stone", STONE_FACE, uv=("world", 1.2))
    b.box((-half, 0.0, -DECK), (half, length, 0.0), "wood", PANEL_BOARDS, frame=frame, uv=("band", *WOOD_LIGHT_BAND, 2.0))
    b.collider((-half, 0.0, -0.12), (half, length, 0.0), frame, name="WoodFloor")

    for along in cleats:
        b.box((-half + 0.05, along - 0.03, 0.0), (half - 0.05, along + 0.03, 0.025), "wood", room.house.wood_tint, frame=frame, uv=wood_uv)

    b.beam((wall_rail_u, RAMP["d_from"], shops.FLOOR_TOP + 0.9), (wall_rail_u, RAMP["d_to"], TERRACE_TOP + 0.9), 0.07, 0.07, "wood", room.house.wood_tint, uv=wood_uv)

    for step in range(4):
        d = RAMP["d_from"] + 0.3 + (RAMP["d_to"] - RAMP["d_from"] - 0.6) * step / 3.0
        z = shops.FLOOR_TOP + (TERRACE_TOP - shops.FLOOR_TOP) * (d - RAMP["d_from"]) / (RAMP["d_to"] - RAMP["d_from"]) + 0.9
        b.box((wall_rail_u + 0.03, d - 0.02, z - 0.12), (RAMP["u_to"], d + 0.02, z - 0.03), "metal", room.house.iron_tint)


def rail_line() -> list:
    """(u, d, z) of the balustrade over the open edges, inset onto the deck: the back arm's edge from the left wall,
    round the rounded corner, down the right arm's edge, across its front and down the open side of the ramp."""
    inset = RAIL["inset"]
    top = [(HALL[0] + inset, BACK_EDGE + inset)] + fillet_points(TERRACE_FILLET + inset) + [(SIDE_EDGE + inset, RAMP["d_to"] + inset), (RAMP["u_from"] + inset, RAMP["d_to"] + inset)]
    foot = (RAMP["u_from"] + inset, RAMP["d_from"] + 0.1, shops.FLOOR_TOP + (TERRACE_TOP - shops.FLOOR_TOP) * 0.1 / (RAMP["d_to"] - RAMP["d_from"]))

    return [(u, d, TERRACE_TOP) for u, d in top] + [foot]


def build_balustrade(b: Builder, room) -> None:
    """Oak handrail and foot rail on square balusters, a newel at every bend, along rail_line(); each run has a
    collider up to RAIL["collider"] so nobody walks off the edge."""
    points = rail_line()
    tint = room.house.wood_tint
    wood_uv = ("band", *WOOD_DARK_BAND, 1.5)
    lift = lambda point, height: (point[0], point[1], point[2] + height)

    for start, end in zip(points, points[1:]):
        balustrade_run(b, start, end, tint)
        rail_collider(b, start, end)

    for point in points:
        newel = RAIL["newel"] / 2.0
        b.box((point[0] - newel, point[1] - newel, point[2]), (point[0] + newel, point[1] + newel, point[2] + RAIL["height"] + 0.1), "wood", tint, uv=wood_uv)

    for start, end in zip(points, points[1:]):
        b.beam(lift(start, RAIL["height"]), lift(end, RAIL["height"]), 0.09, 0.07, "wood", tint, uv=wood_uv)
        b.beam(lift(start, 0.08), lift(end, 0.08), 0.06, 0.05, "wood", tint, uv=wood_uv)


def balustrade_run(b: Builder, start: tuple, end: tuple, tint: tuple) -> None:
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    count = max(1, round(length / RAIL["pitch"]))
    half = RAIL["baluster"] / 2.0
    feet = [tuple(start[axis] + (end[axis] - start[axis]) * index / count for axis in range(3)) for index in range(1, count)]

    for u, d, z in feet:
        b.box((u - half, d - half, z + 0.1), (u + half, d + half, z + RAIL["height"] - 0.03), "wood", tint, uv=("band", *WOOD_DARK_BAND, 1.0))


def rail_collider(b: Builder, start: tuple, end: tuple) -> None:
    """Thin wall from start to end (y along the run, tilted with it), RAIL["collider"] high."""
    run = math.hypot(end[0] - start[0], end[1] - start[1])
    heading = math.atan2(-(end[0] - start[0]), end[1] - start[1])
    slope = math.atan2(end[2] - start[2], run)
    frame = Matrix.Translation(start) @ Matrix.Rotation(heading, 4, "Z") @ Matrix.Rotation(slope, 4, "X")

    b.collider((-0.06, 0.0, 0.0), (0.06, math.hypot(run, end[2] - start[2]), RAIL["collider"]), frame)


# ---------- wall finishes ----------

def outer_faces(room, openings: dict) -> list:
    """(axis, face, normal, span, finish, windows) of every room's stretch of the outer walls; windows as
    (from, to, bottom, top) along it."""
    to_d = lambda opening: wall_local_left(room, opening.u)
    front = [(opening.u - room.half - opening.width / 2.0 - 0.1, opening.u - room.half + opening.width / 2.0 + 0.1, opening.bottom, opening.apex) for opening in openings["front"]]
    left = [(to_d(opening) - opening.width / 2.0 - 0.1, to_d(opening) + opening.width / 2.0 + 0.1, opening.bottom, opening.apex) for opening in openings["left"]]
    back = [(start - 0.1, end + 0.1, bottom, bottom + 1.4) for start, end, bottom in shops.window_spans(room)["back"]]
    walls = {"front": ("d", room.front, 1, front), "back": ("d", room.back, -1, back), "left": ("u", room.left, 1, left), "right": ("u", room.right, -1, [])}
    stretches = (
        ("hall", "front", WAINSCOT), ("hall", "right", WAINSCOT), ("inn", "front", WAINSCOT), ("inn", "left", WAINSCOT),
        ("kitchen", "left", PLASTERED), ("pantry", "left", PLASTERED), ("pantry", "back", PLASTERED), ("store", "back", PLASTERED), ("store", "right", PLASTERED),
    )
    along = lambda name, side: ROOMS[name][:2] if side in ("front", "back") else ROOMS[name][2:]

    return [(walls[side][0], walls[side][1], walls[side][2], along(name, side), finish, walls[side][3]) for name, side, finish in stretches]


def cuts_at(windows: list, height: float) -> list:
    return [(start, end) for start, end, bottom, top in windows if bottom < height < top + 0.1]


def terrace_faces() -> list:
    """(axis, face, normal, span, cuts) of the walls round the terrace, boarded above its deck (the inglenook cut out)."""
    inglenook = (0.2, 3.4)

    return [
        ("u", HALL[1], -1, (RAMP["d_to"], HALL[3]), []),
        ("d", HALL[3], -1, (HALL[0], HALL[1]), [inglenook]),
        ("u", HALL[0], 1, (BACK_EDGE, HALL[3]), []),
    ]


def build_finishes(b: Builder, room, openings: dict) -> None:
    """Dado, rails and cornice on the outer walls room by room; the walls round the terrace boarded above its deck."""
    for axis, face_at, normal, span, finish, windows in outer_faces(room, openings):
        shops.dress_wall_face(b, room, axis, face_at, normal, span, finish, cuts_at(windows, shops.DADO_HEIGHT), cuts_at(windows, shops.PICTURE_RAIL_HEIGHT))

    for axis, face_at, normal, span, cuts in terrace_faces():
        for piece in shops.free_spans(*span, cuts):
            panel_stretch(b, axis, face_at, normal, piece)


def panel_stretch(b: Builder, axis: str, face_at: float, normal: int, piece: tuple) -> None:
    """Boarding of one stretch: boards up PANEL_BAND, battens every BATTEN_PITCH and a capping board."""
    batten_count = max(1, round((piece[1] - piece[0]) / BATTEN_PITCH))
    battens = [piece[0] + (piece[1] - piece[0]) * index / batten_count for index in range(1, batten_count)]
    wood_uv = ("band", *WOOD_LIGHT_BAND, 1.5)

    b.box(*shops.wall_slab(axis, face_at, normal, piece, 0.0, 0.02, PANEL_BAND), "wood", PANEL_BOARDS, uv=wood_uv)
    b.box(*shops.wall_slab(axis, face_at, normal, piece, 0.0, 0.06, (PANEL_BAND[1], PANEL_BAND[1] + 0.05)), "wood", PANEL_RIBS, uv=wood_uv)

    for batten in battens:
        b.box(*shops.wall_slab(axis, face_at, normal, (batten - 0.03, batten + 0.03), 0.02, 0.02, (PANEL_BAND[0] + 0.1, PANEL_BAND[1])), "wood", PANEL_RIBS, uv=wood_uv)


# ---------- outside ----------

def build_street_front(b: Builder, room) -> None:
    """Oak posts, sill and head beam on the ground storey of the facade, the door hood, benches and barrels (the inn's
    side door has none: the lot ends at that wall)."""
    house = room.house
    door_u = room.door[0]
    beam_uv = ("band", *WOOD_DARK_BAND, 1.5)
    gaps = [(u - WINDOW[0] / 2.0 - 0.12, u + WINDOW[0] / 2.0 + 0.12) for u in FRONT_WINDOWS] + [(door_u - room.door[1] / 2.0 - 0.3, door_u + room.door[1] / 2.0 + 0.3)]
    rails = shops.free_spans(-house.half, house.half, gaps)

    for u in FRAME_POSTS:
        b.box((u - 0.09, -0.09, shops.PLINTH_HEIGHT), (u + 0.09, 0.0, room.storey - 0.22), "wood", house.wood_tint, uv=beam_uv)

    b.box((-house.half, -0.1, room.storey - 0.42), (house.half, 0.0, room.storey - 0.22), "wood", house.wood_tint, uv=beam_uv)

    for rail_from, rail_to in rails:
        b.box((rail_from, -0.09, shops.PLINTH_HEIGHT + 0.85), (rail_to, 0.0, shops.PLINTH_HEIGHT + 0.97), "wood", house.wood_tint, uv=beam_uv)

    build_door_hood(b, room, Matrix.Translation((door_u, 0.0, 0.0)))

    for name, u, d in STREET_PROPS:
        width, depth, height = shops.PROPS[name]["size"]
        frame = Matrix.Translation((u, d, 0.0))

        shops.PROPS[name]["build"](b, frame)
        b.collider((-width / 2.0, -depth / 2.0, 0.0), (width / 2.0, depth / 2.0, height), frame)


def build_door_hood(b: Builder, room, frame: Matrix) -> None:
    """Small gabled hood on two carved brackets over the street door (frame on the door's axis); the camera stops
    under it."""
    house = room.house
    half, reach, eave, rise = HOOD["half"], HOOD["reach"], HOOD["eave"], HOOD["rise"]
    slopes = ([(-half - 0.1, eave), (0.0, eave + rise), (0.0, eave + rise + 0.1), (-half - 0.1, eave + 0.1)], [(half + 0.1, eave), (half + 0.1, eave + 0.1), (0.0, eave + rise + 0.1), (0.0, eave + rise)])

    for slope in slopes:
        b.camera_stop(b.prism(slope, -reach, 0.0, house.roof_material, house.roof_tint, frame=frame))

    b.prism([(-half, eave), (half, eave), (0.0, eave + rise)], -reach + 0.04, -reach + 0.08, house.wall_material, house.wall_tint, frame=frame)
    b.box((-half, -reach + 0.02, eave - 0.14), (half, -reach + 0.12, eave), "wood", house.wood_tint, frame=frame, uv=("band", *WOOD_DARK_BAND, 1.5))

    for side_sign in (-1, 1):
        u = side_sign * (half - 0.08)
        b.side_prism([(0.0, eave - 0.9), (0.0, eave), (-reach + 0.05, eave)], u - 0.06, u + 0.06, "wood", house.wood_tint, frame=frame)


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

    openings = build_walls(b, room)
    build_floor(b, room)
    build_ceiling(b, room)
    build_terrace(b)
    build_ramp(b, room)
    build_balustrade(b, room)

    for partition in room.partitions:
        shops.build_partition(b, room, partition)

    build_finishes(b, room, openings)
    shops.build_roof(b, room)
    build_street_front(b, room)
    build_kitchen_chimney(b, room)

    for u, d in LIGHTS:
        b.light((u, d, room.ceiling - LAMP_DROP), room.spec["light"], 1.3, 7.0)

    b.marker("shopkeeper", (*room.keeper, 0.0))

    return b.finish(town.SHOP_DIR / f"shop_{room.shop_type}.gltf", {**shops.shell_sidecar(room), "side_signs": side_signs(room)})


def side_signs(room) -> list:
    """The inn's hanging sign beside its door on the side street (model-local Godot coords, turned to face the street)."""
    if "left" not in room.exposed:
        return []

    d = INN_DOOR["d"] - INN_DOOR["width"] / 2.0 - INN_SIGN_OFFSET

    return [{"sign": "inn", "position": town.blender_to_godot((-room.half, d, 0.0)), "yaw": -math.pi / 2.0}]
