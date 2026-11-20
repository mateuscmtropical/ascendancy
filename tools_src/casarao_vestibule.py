"""Shell of the casarão's vestibule: the middle hall of the mansion, two storeys high.

Ground floor: the only street portal, a colonnade across the hall and behind it the grand stair in its well (one
wide flight up to a landing against the back wall, under three tall windows, then two return flights up to the
upper floor). Upper floor: the gallery around the stair well, with the three balcony doors of the facade in front.
Doorways in both side walls, on both floors, lead to the four halls of the wings (enfilade along the facade).

build_market_shops.py calls build_shell() for the "vestibule" entry of SHOPS; build_casarao.py reads
facade_openings() to dress the outside; shop_layouts.py reads the measurements to furnish around the stair.
"""

import copy
import math

from mathutils import Matrix

import build_market_shops as shops
import build_town_houses as town
from build_town_houses import STONE, WOOD, WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, Opening, srgb
from shop_props_common import lathe

UPPER = shops.CASARAO_STOREYS[0]  # altura da laje do andar nobre
WELL_SHIFT = shops.SHOP_LOTS["vestibule"][1] - 20.0  # a escada fica encostada no fundo: o salão cresceu para trás, o vão vai junto
TOP = sum(shops.CASARAO_STOREYS)
FLOOR_TOP = shops.FLOOR_TOP
STAIR_HALF = 1.8  # meia largura do lance central
SIDE_FLIGHT = (2.1, 4.5)  # |u| dos dois lances de volta
WELL_HALF = 4.8  # o vão da escada vai até a face de fora das paredes que seguram a galeria
WELL_FRONT = 11.2 + WELL_SHIFT  # d da borda da galeria: pé do lance central e chegada dos lances de volta
LANDING_FRONT = 16.0 + WELL_SHIFT  # d da borda do patamar
RISERS = 16  # espelhos por lance
TREAD = (LANDING_FRONT - WELL_FRONT) / (RISERS - 1)
RISE = UPPER / (2 * RISERS)
LANDING_TOP = FLOOR_TOP + RISERS * RISE
SLOPE = math.atan2(RISE, TREAD)
SOFFIT_DROP = 0.45  # da linha dos focinhos ao forro inclinado dos lances de volta
RAIL_HEIGHT = 1.05
STRINGER_RISE = 0.25  # a mureta ao lado do lance central passa isto da linha dos degraus
STRINGER_RAIL = 0.8  # e o corrimão dela fica mais baixo, para dar a mesma altura sobre o degrau
BAR_PITCH = 0.16
COLUMN_US = (-9.7, -1.95, 1.95, 9.7)  # colunata do térreo na borda da galeria
GALLERY_COLUMN_US = (-4.65, -1.95, 1.95, 4.65)  # colunas do andar nobre: emolduram a chegada dos lances
STAIR_WINDOWS = ((-2.9, 0.0, 2.9), 1.7, 4.3, 5.2)  # (eixos u, largura, peitoril, altura): janelão sobre o patamar
BALCONY_BAYS = 3  # vãos do meio da fachada do andar nobre que são portas para a sacada
LAYLIGHT = (3.3, 12.6 + WELL_SHIFT, 17.7 + WELL_SHIFT, 6, 4)  # (meia largura, d de, d até, colunas, fileiras) da claraboia de vidro colorido do vão
LAYLIGHT_GLASS = ("laylight_warm", "laylight_amber", "laylight_cyan")  # miolo, borda, cantos; vidro de claraboia (features/sky/window_glass.gd): claro de dia, quase apagado de noite
LAYLIGHT_COLORS = {"laylight_warm": ("M_LaylightWarm", "FFD9A0"), "laylight_amber": ("M_LaylightAmber", "FFB347"), "laylight_cyan": ("M_LaylightCyan", "8FD8FF")}
RUNNER_HALF = 0.9  # passadeira do portal ao patamar
FLOOR_TILE = 1.2
FLOOR_TINTS = (srgb("EBD6AC"), srgb("C99A6C"))  # xadrez do piso do térreo
DADO_TOP = 1.5
CORNICE_HEIGHT = 0.2  # the same cornice the wing halls run under their ceilings (build_market_shops.py)
CORNICE_TINT = srgb("EFE6D2")
DADO_REVEAL = 0.32  # o lambri para antes da moldura de cada vão
PANEL_PITCH = 2.6  # largura aproximada de um painel de parede
PANEL_TOP = 4.35
LANDING_DADO = 1.2  # lambri do patamar, sob os janelões
BACK_PANEL_TOP = 3.0  # na parede do fundo os painéis ficam sob as janelas altas
AZULEJO_TEXTURE = town.TEXTURE_DIR / "T_Azulejo_BaseColor.png"  # pintada por build_casarao.py, versionada
GILT = srgb("D9A441")
WALL_FINISHES = (  # por andar: lambri (material, cor, uv), campo e moldura dos painéis
    dict(dado="azulejo", dado_tint=town.WHITE, dado_uv=("world", 1.2), field=srgb("E9BE62"), frame=srgb("F6F0E2")),
    dict(dado="paint", dado_tint=srgb("2F6B5A"), dado_uv=None, field=srgb("7FB894"), frame=GILT),
)
MARBLE = srgb("F1ECE2")
PLASTER = srgb("F4EFE6")
RUNNER = srgb("8E2F3A")


def storey_room(room, storey: int):
    """The hall as one of its storeys sees it: the upper one has the facade windows of the andar nobre."""
    if storey == 0:
        return room

    upper = copy.copy(room)
    upper.spec = dict(room.spec, **{key: shops.CASARAO_UPPER[key] for key in ("sill", "vitrine_apex", "vitrine_width")})
    upper.has_street_door = False

    return upper


def front_openings(room, storey: int) -> list:
    """Portal and windows of the ground floor; upstairs the middle bays are doors to the balcony."""
    openings = sorted(shops.front_openings(storey_room(room, storey)), key=lambda opening: opening.u)

    if storey == 0:
        return openings

    first_door = (len(openings) - BALCONY_BAYS) // 2
    doors = openings[first_door:first_door + BALCONY_BAYS]
    windows = [opening for opening in openings if opening not in doors]

    return windows + [Opening(door.u, door.width, 0.0, door.apex, door.top, kind="balcony") for door in doors]


def back_openings(room, storey: int) -> list:
    """High windows of the back wall on both sides of the stair well (wall-local u of the whole back wall)."""
    return [opening for opening in shops.back_windows(room) if abs(room.half - opening.u) > WELL_HALF + 0.9]


def stair_windows(room) -> list:
    """The tall windows over the landing, in the coords of the whole back wall with z from the ground."""
    axes, width, sill, height = STAIR_WINDOWS

    return [Opening(room.half - u, width, sill, height, "round", kind="vitrine") for u in axes]


def facade_openings(room) -> dict:
    """side -> [(lift, Opening)] of the street and back walls, both storeys, for the outside dressing."""
    lifts = (0.0, UPPER)
    front = [(lifts[storey], opening) for storey in (0, 1) for opening in front_openings(room, storey)]
    back = [(lifts[storey], opening) for storey in (0, 1) for opening in back_openings(room, storey)]

    return {"front": front, "back": back + [(0.0, opening) for opening in stair_windows(room)]}


# ---------- walls ----------

def build_walls(b: Builder, room) -> None:
    """Front and side walls storey by storey; the back wall is whole behind the stair well (the tall windows
    cross the level of the upper floor)."""
    lengths = shops.wall_lengths(room)
    inner = shops.inner_door_openings(room)
    well_wall = copy.copy(room)
    well_wall.storey = TOP

    for storey, lift in enumerate((0.0, UPPER)):
        frames = shops.wall_frames(room, lift)
        back_side = room.half - WELL_HALF
        back = back_openings(room, storey)

        shops.pierced_wall(b, storey_room(room, storey), frames["front"], lengths["front"], front_openings(room, storey))
        shops.pierced_wall(b, room, frames["left"], lengths["left"], inner["left"])
        shops.pierced_wall(b, room, frames["right"], lengths["right"], inner["right"])
        shops.pierced_wall(b, room, frames["back"], back_side, [opening for opening in back if opening.u < back_side])
        shops.pierced_wall(b, room, frames["back"] @ Matrix.Translation((room.half + WELL_HALF, 0.0, 0.0)), back_side, [shifted(opening, -(room.half + WELL_HALF)) for opening in back if opening.u > back_side])

    well_frame = shops.wall_frames(room)["back"] @ Matrix.Translation((room.half - WELL_HALF, 0.0, 0.0))
    shops.pierced_wall(b, well_wall, well_frame, 2.0 * WELL_HALF, [shifted(opening, -(room.half - WELL_HALF)) for opening in stair_windows(room)])


def shifted(opening: Opening, offset: float) -> Opening:
    return Opening(opening.u + offset, opening.width, opening.bottom, opening.height, opening.top, kind=opening.kind)


def build_well_walls(b: Builder, room) -> None:
    """The two walls that carry the gallery beside the stair, whole: the rooms behind them open on the crossing."""
    wall = copy.copy(room)
    wall.storey = UPPER
    length = room.back - WELL_FRONT
    right = Matrix.Translation((WELL_HALF, WELL_FRONT, 0.0)) @ Matrix.Rotation(math.pi / 2.0, 4, "Z")
    left = Matrix.Translation((-WELL_HALF, room.back, 0.0)) @ Matrix.Rotation(-math.pi / 2.0, 4, "Z")

    shops.pierced_wall(b, wall, right, length, [])
    shops.pierced_wall(b, wall, left, length, [])


# ---------- floors and ceilings ----------

def gallery_pieces(room) -> list:
    """(u from, u to, d from, d to) of the upper floor: everything but the stair well."""
    return [
        (room.left, room.right, room.front, WELL_FRONT),
        (room.left, -WELL_HALF, WELL_FRONT, room.back),
        (WELL_HALF, room.right, WELL_FRONT, room.back),
    ]


def build_ground_floor(b: Builder, room) -> None:
    """Checkered stone floor with a carpet runner from the portal to the foot of the stair."""
    columns = round((room.right - room.left) / FLOOR_TILE)
    rows = round((room.back - room.front) / FLOOR_TILE)
    tile_u, tile_d = (room.right - room.left) / columns, (room.back - room.front) / rows

    b.collider((room.left, room.front, 0.0), (room.right, room.back, FLOOR_TOP))

    for index in range(columns * rows):
        column, row = index % columns, index // columns
        corner = (room.left + column * tile_u, room.front + row * tile_d)

        b.box((corner[0], corner[1], 0.0), (corner[0] + tile_u, corner[1] + tile_d, FLOOR_TOP), "plaster", FLOOR_TINTS[(column + row) % 2])

    b.box((-RUNNER_HALF, room.front + 0.5, FLOOR_TOP), (RUNNER_HALF, WELL_FRONT, FLOOR_TOP + 0.012), "paint", RUNNER)

    for side_sign in (-1, 1):
        edge = side_sign * (RUNNER_HALF - 0.1)
        b.box((edge - 0.03, room.front + 0.5, FLOOR_TOP), (edge + 0.03, WELL_FRONT, FLOOR_TOP + 0.014), "paint", GILT)


# ---------- wall finishes ----------

def free_spans(span_from: float, span_to: float, gaps: list) -> list:
    """Stretches (from, to) of a wall left between its openings [(from, to)]."""
    edges = sorted(gaps)
    starts = [span_from] + [gap_to for _, gap_to in edges]
    ends = [gap_from for gap_from, _ in edges] + [span_to]

    return [(start, end) for start, end in zip(starts, ends) if end - start > 0.3]


def slab(b: Builder, run: tuple, span: tuple, heights: tuple, thickness: float, material: str, tint: tuple, uv: tuple = None) -> None:
    """Thin cladding on a wall. run = (axis, fixed, inward): axis "u" is a wall along the facade at d = fixed,
    "d" a wall into the lot at u = fixed; inward (1 or -1) points into the room."""
    axis, fixed, inward = run
    low, high = sorted((fixed, fixed + inward * thickness))
    corners = {"u": ((span[0], low), (span[1], high)), "d": ((low, span[0]), (high, span[1]))}[axis]

    b.box((*corners[0], heights[0]), (*corners[1], heights[1]), material, tint, uv=uv)


def wall_panel(b: Builder, run: tuple, span: tuple, heights: tuple, finish: dict) -> None:
    """One framed field of colour on a wall."""
    bottom, top = heights
    bars = [((span[0], span[1]), (bottom, bottom + 0.07)), ((span[0], span[1]), (top - 0.07, top)), ((span[0], span[0] + 0.07), heights), ((span[1] - 0.07, span[1]), heights)]

    slab(b, run, span, heights, 0.012, "paint", finish["field"])

    for bar_span, bar_heights in bars:
        slab(b, run, bar_span, bar_heights, 0.03, "paint", finish["frame"])


def dress_wall(b: Builder, run: tuple, span: tuple, lift: float, finish: dict, dado_top: float = DADO_TOP, panel_top: float = PANEL_TOP) -> None:
    """Skirting, dado and chair rail on a stretch of wall and, above them, framed panels up to panel_top."""
    floor = lift + FLOOR_TOP
    count = max(1, round((span[1] - span[0]) / PANEL_PITCH))
    width = (span[1] - span[0]) / count

    slab(b, run, span, (floor, floor + 0.14), 0.05, "plaster", srgb(STONE["clara"]))
    slab(b, run, span, (floor + 0.14, lift + dado_top), 0.03, finish["dado"], finish["dado_tint"], finish["dado_uv"])
    slab(b, run, span, (lift + dado_top, lift + dado_top + 0.08), 0.06, "paint", finish["frame"])

    if panel_top <= dado_top or span[1] - span[0] < 1.0:
        return

    for index in range(count):
        panel_span = (span[0] + index * width + 0.2, span[0] + (index + 1) * width - 0.2)
        wall_panel(b, run, panel_span, (lift + dado_top + 0.3, lift + panel_top), finish)


def build_wall_finishes(b: Builder, room, storey: int) -> None:
    """Dado and coloured panels on the walls of one storey: azulejo and ochre on the ground floor, green and gilt
    in the salon upstairs. The stretches stop short of the mouldings of every opening."""
    lift = (0.0, UPPER)[storey]
    finish = WALL_FINISHES[storey]
    door_d, door_width = shops.INNER_DOOR[:2]
    door_gap = [(door_d - door_width / 2.0 - DADO_REVEAL, door_d + door_width / 2.0 + DADO_REVEAL)]
    front = [(opening.u - room.half, opening) for opening in front_openings(room, storey)]
    front_gaps = [(u - opening.width / 2.0 - DADO_REVEAL, u + opening.width / 2.0 + DADO_REVEAL) for u, opening in front]
    sills = [(u, opening) for u, opening in front if opening.bottom > 0.5]
    side_spans = free_spans(room.front, room.back, door_gap)
    well_spans = [(WELL_FRONT, room.back)] if storey == 0 else []
    runs = [(("d", room.left, 1), span) for span in side_spans] + [(("d", room.right, -1), span) for span in side_spans]
    runs += [(("u", room.front, 1), span) for span in free_spans(room.left, room.right, front_gaps)]
    runs += [(("d", -WELL_HALF, -1), span) for span in well_spans] + [(("d", WELL_HALF, 1), span) for span in well_spans]

    for run, span in runs:
        dress_wall(b, run, span, lift, finish)

    for span in ((room.left, -WELL_HALF), (WELL_HALF, room.right)):
        dress_wall(b, ("u", room.back, -1), span, lift, finish, panel_top=BACK_PANEL_TOP)

    if storey == 0:
        dress_wall(b, ("u", room.back, -1), (-SIDE_FLIGHT[1], SIDE_FLIGHT[1]), LANDING_TOP - FLOOR_TOP, finish, dado_top=LANDING_DADO, panel_top=0.0)

    for u, opening in sills:
        dress_wall(b, ("u", room.front, 1), (u - opening.width / 2.0 - DADO_REVEAL, u + opening.width / 2.0 + DADO_REVEAL), lift, finish, dado_top=opening.bottom - 0.2, panel_top=0.0)

    ceiling = lift + room.ceiling
    cornice_runs = [(("d", room.left, 1), (room.front, room.back)), (("d", room.right, -1), (room.front, room.back)), (("u", room.front, 1), (room.left, room.right)), (("u", room.back, -1), (room.left, room.right))]

    for run, span in cornice_runs:
        slab(b, run, span, (ceiling - CORNICE_HEIGHT, ceiling - CORNICE_HEIGHT * 0.6), 0.05, "plaster", CORNICE_TINT)
        slab(b, run, span, (ceiling - CORNICE_HEIGHT * 0.6, ceiling), 0.1, "plaster", CORNICE_TINT)


def build_gallery(b: Builder, room) -> None:
    """Slab of the upper floor around the well: plaster underneath on timber joists, boards on top."""
    house = room.house
    board = shops.BOARD_WIDTH
    wood = srgb(WOOD["mel"])

    for u_from, u_to, d_from, d_to in gallery_pieces(room):
        board_count = round((u_to - u_from) / board)
        board_width = (u_to - u_from) / board_count
        joist_count = int((d_to - d_from) / shops.JOIST_SPACING)

        town.wall_piece(b, (u_from, d_from, room.ceiling), (u_to, d_to, UPPER), "plaster", PLASTER)
        b.collider((u_from, d_from, UPPER), (u_to, d_to, UPPER + FLOOR_TOP), name="WoodFloor")

        for index in range(board_count):
            shade = 1.0 if index % 3 else 0.9
            board_left = u_from + index * board_width
            b.box((board_left, d_from, UPPER), (board_left + board_width, d_to, UPPER + FLOOR_TOP), "wood", tuple(shade * channel for channel in wood), uv=("band", *WOOD_LIGHT_BAND, 2.0))

        for index in range(joist_count):
            d = d_from + (d_to - d_from) * (index + 0.5) / joist_count
            b.box((u_from, d - 0.08, room.ceiling - 0.2), (u_to, d + 0.08, room.ceiling), "wood", house.wood_tint, uv=("band", *WOOD_DARK_BAND, 1.5))

    b.box((room.left, WELL_FRONT - 0.2, room.ceiling - 0.45), (room.right, WELL_FRONT + 0.2, room.ceiling), "plaster", PLASTER)
    b.box((-SIDE_FLIGHT[0], WELL_FRONT - 0.03, room.ceiling), (SIDE_FLIGHT[0], WELL_FRONT + 0.2, UPPER + FLOOR_TOP), "plaster", PLASTER)


def build_top_ceiling(b: Builder, room) -> None:
    """Plaster ceiling of the upper floor with a grid of beams; over the well, a coloured-glass laylight and the
    boss of the chandelier."""
    ceiling = UPPER + room.ceiling
    beam_ds = [room.front + (room.back - room.front) * index / 4.0 for index in range(1, 4)]
    beam_us = [room.left + (room.right - room.left) * index / 6.0 for index in range(1, 6)]
    rose = Matrix.Translation((0.0, (WELL_FRONT + room.back) / 2.0, ceiling))

    town.wall_piece(b, (room.left, room.front, ceiling), (room.right, room.back, TOP), "plaster", PLASTER)

    for d in beam_ds:
        b.box((room.left, d - 0.14, ceiling - 0.28), (room.right, d + 0.14, ceiling), "plaster", srgb(STONE["clara"]))

    for u in beam_us:
        b.box((u - 0.14, room.front, ceiling - 0.24), (u + 0.14, room.back, ceiling), "plaster", srgb(STONE["clara"]))

    lathe(b, [(0.15, -0.34), (0.38, -0.32), (0.45, -0.24), (0.65, -0.22), (0.75, -0.12)], 16, "plaster", STONE["clara"], rose)
    build_laylight(b, ceiling)


def build_laylight(b: Builder, ceiling: float) -> None:
    """Coloured-glass laylight under the ceiling of the stair well: warm field, amber border, cyan corners, in
    plaster bars."""
    half, d_from, d_to, columns, rows = LAYLIGHT
    pane_u, pane_d = 2.0 * half / columns, (d_to - d_from) / rows
    bar = srgb(STONE["clara"])

    for index in range(columns * rows):
        column, row = index % columns, index // columns
        edges = (column in (0, columns - 1)) + (row in (0, rows - 1))
        corner = (-half + column * pane_u, d_from + row * pane_d)

        b.box((corner[0], corner[1], ceiling - 0.03), (corner[0] + pane_u, corner[1] + pane_d, ceiling - 0.01), LAYLIGHT_GLASS[edges])

    for column in range(columns + 1):
        u = -half + column * pane_u
        b.box((u - 0.05, d_from, ceiling - 0.12), (u + 0.05, d_to, ceiling), "plaster", bar)

    for row in range(rows + 1):
        d = d_from + row * pane_d
        b.box((-half - 0.05, d - 0.05, ceiling - 0.12), (half + 0.05, d + 0.05, ceiling), "plaster", bar)


def column(b: Builder, u: float, d: float, bottom: float, top: float) -> None:
    """Stone column with a moulded base and capital; a square collider."""
    height = top - bottom
    profile = [(0.36, 0.0), (0.36, 0.22), (0.3, 0.28), (0.3, 0.36), (0.25, 0.46), (0.21, height - 0.5), (0.26, height - 0.42), (0.26, height - 0.34), (0.33, height - 0.2), (0.38, height - 0.12), (0.38, height)]

    lathe(b, profile, 14, "plaster", STONE["clara"], Matrix.Translation((u, d, bottom)))
    b.collider((u - 0.26, d - 0.26, bottom), (u + 0.26, d + 0.26, top))


def build_columns(b: Builder, room) -> None:
    for u in COLUMN_US:
        column(b, u, WELL_FRONT, FLOOR_TOP, room.ceiling - 0.45)

    for u in GALLERY_COLUMN_US:
        column(b, u, WELL_FRONT, UPPER + FLOOR_TOP, UPPER + room.ceiling)


# ---------- stair ----------

def flight_profile(start_d: float, start_z: float, direction: float) -> list:
    """Stepped top of one flight in (d, z): RISERS risers from start_d, climbing toward direction (+1 or -1)."""
    risers = [(start_d + direction * index * TREAD, start_z + index * RISE) for index in range(RISERS)]

    return [point for d, z in risers for point in ((d, z), (d, z + RISE))]


def build_stair(b: Builder, room) -> None:
    """The three flights and the landing: solid marble under the first flight, a sloped soffit under the others."""
    central = flight_profile(WELL_FRONT, FLOOR_TOP, 1.0)
    side = flight_profile(LANDING_FRONT, LANDING_TOP, -1.0)
    soffit = [(WELL_FRONT, UPPER + FLOOR_TOP - RISE - SOFFIT_DROP), (LANDING_FRONT, LANDING_TOP - SOFFIT_DROP)]
    side_edges = [side_sign * edge for side_sign in (-1, 1) for edge in SIDE_FLIGHT]

    b.side_prism([(WELL_FRONT, 0.0)] + central + [(LANDING_FRONT, 0.0)], -STAIR_HALF, STAIR_HALF, "plaster", MARBLE)
    town.wall_piece(b, (-SIDE_FLIGHT[1], LANDING_FRONT, 0.0), (SIDE_FLIGHT[1], room.back, LANDING_TOP), "plaster", MARBLE)
    ramp(b, 0.0, 2.0 * STAIR_HALF, WELL_FRONT - TREAD, FLOOR_TOP, 1.0)

    for u_from, u_to in zip(side_edges[::2], side_edges[1::2]):
        b.side_prism(side + soffit, min(u_from, u_to), max(u_from, u_to), "plaster", MARBLE)
        ramp(b, (u_from + u_to) / 2.0, abs(u_to - u_from), LANDING_FRONT + TREAD, LANDING_TOP, -1.0)

    build_runner(b)


def ramp(b: Builder, u: float, width: float, start_d: float, start_z: float, direction: float) -> None:
    """Sloped collider through the step edges of one flight, from the floor one tread before its first riser."""
    length = math.hypot(RISERS * TREAD, RISERS * RISE)
    turn = Matrix.Identity(4) if direction > 0.0 else Matrix.Rotation(math.pi, 4, "Z")
    frame = Matrix.Translation((u, start_d, start_z)) @ turn @ Matrix.Rotation(SLOPE, 4, "X")

    b.collider((-width / 2.0, 0.0, -0.12), (width / 2.0, length, 0.0), frame, name="Stairs")


def build_runner(b: Builder) -> None:
    """Red carpet runner on the treads of the first flight and across the landing."""
    for index in range(RISERS - 1):
        d = WELL_FRONT + index * TREAD
        z = FLOOR_TOP + (index + 1) * RISE
        b.box((-RUNNER_HALF, d - 0.012, z - RISE), (RUNNER_HALF, d + TREAD, z + 0.012), "paint", RUNNER)

    b.box((-RUNNER_HALF, LANDING_FRONT - 0.012, LANDING_TOP - RISE), (RUNNER_HALF, LANDING_FRONT + 2.2, LANDING_TOP + 0.012), "paint", RUNNER)


# ---------- railings ----------

def rail_run(b: Builder, room, start: tuple, end: tuple, thickness: float = 0.1, bottom=None, height: float = RAIL_HEIGHT) -> None:
    """Iron bars under a timber handrail from start to end (u, d, z of the floor line), newel posts at both ends
    and a collider in level steps under the rail (down to bottom(d) when the run stands over open floor)."""
    house = room.house
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    bar_count = max(2, round(length / BAR_PITCH))
    pieces = max(1, round(abs(end[2] - start[2]) / 0.7))
    along = lambda step: tuple(start[axis] + (end[axis] - start[axis]) * step for axis in range(3))
    lift = lambda point, height: (point[0], point[1], point[2] + height)

    b.beam(lift(start, height), lift(end, height), 0.07, 0.1, "wood", house.wood_tint)
    b.beam(lift(start, 0.1), lift(end, 0.1), 0.04, 0.03, "metal", house.iron_tint)

    for index in range(1, bar_count):
        foot = along(index / bar_count)
        b.box((foot[0] - 0.012, foot[1] - 0.012, foot[2]), (foot[0] + 0.012, foot[1] + 0.012, foot[2] + height), "metal", house.iron_tint)

    for post in (start, end):
        newel(b, post, height)

    for index in range(pieces):
        first, second = along(index / pieces), along((index + 1) / pieces)
        low = min(first[2], second[2]) if bottom is None else bottom(max(first[1], second[1]))
        minimum = (min(first[0], second[0]) - thickness / 2.0, min(first[1], second[1]) - thickness / 2.0, low)
        maximum = (max(first[0], second[0]) + thickness / 2.0, max(first[1], second[1]) + thickness / 2.0, max(first[2], second[2]) + height)
        b.collider(minimum, maximum)


def newel(b: Builder, foot: tuple, height: float) -> None:
    """Turned timber newel post with a ball on top."""
    profile = [(0.09, 0.0), (0.09, 0.12), (0.065, 0.18), (0.065, height - 0.1), (0.1, height), (0.1, height + 0.08), (0.05, height + 0.12)]

    lathe(b, profile, 8, "wood", WOOD["escura"], Matrix.Translation(foot))
    b.sphere((foot[0], foot[1], foot[2] + height + 0.2), 0.09, "wood", srgb(WOOD["escura"]))


def build_railings(b: Builder, room) -> None:
    """Rails of the three flights, of the gallery around the well and the low wall beside the first flight."""
    gallery = UPPER + FLOOR_TOP
    stringer_foot = WELL_FRONT - 0.1
    stringer_top = lambda d: FLOOR_TOP + STRINGER_RISE + (d - stringer_foot) * (LANDING_TOP - FLOOR_TOP) / (LANDING_FRONT - stringer_foot)
    soffit = lambda d: LANDING_TOP - SOFFIT_DROP + (LANDING_FRONT - d) * RISE / TREAD
    stringer = [(stringer_foot, 0.0), (stringer_foot, stringer_top(stringer_foot)), (LANDING_FRONT, stringer_top(LANDING_FRONT)), (LANDING_FRONT, 0.0)]
    strip_ends = (WELL_FRONT + 0.15, LANDING_FRONT - 0.15)

    for side_sign in (-1, 1):
        strip = sorted((side_sign * STAIR_HALF, side_sign * SIDE_FLIGHT[0]))
        strip_u = side_sign * (STAIR_HALF + SIDE_FLIGHT[0]) / 2.0
        inner_u = side_sign * (SIDE_FLIGHT[0] + 0.07)

        b.side_prism(stringer, *strip, "plaster", MARBLE)
        rail_run(b, room, (strip_u, strip_ends[0], stringer_top(strip_ends[0])), (strip_u, strip_ends[1], stringer_top(strip_ends[1])), thickness=0.3, bottom=lambda d: 0.0, height=STRINGER_RAIL)
        rail_run(b, room, (inner_u, LANDING_FRONT - 0.15, LANDING_TOP + RISE), (inner_u, WELL_FRONT + 0.15, gallery), bottom=soffit)
        rail_run(b, room, (side_sign * (WELL_HALF - 0.08), WELL_FRONT + 0.4, gallery), (side_sign * (WELL_HALF - 0.08), room.back - 0.1, gallery))
        b.box((side_sign * WELL_HALF - 0.3 * (side_sign > 0), WELL_FRONT, UPPER), (side_sign * WELL_HALF + 0.3 * (side_sign < 0), room.back, gallery + 0.06), "plaster", PLASTER)

    rail_run(b, room, (-GALLERY_COLUMN_US[2] + 0.3, WELL_FRONT + 0.05, gallery), (GALLERY_COLUMN_US[2] - 0.3, WELL_FRONT + 0.05, gallery))


# ---------- assembly ----------

def build_lights(b: Builder, room) -> None:
    """Day lamps under the gallery and under the top ceiling (daylight bouncing round the hall, see shops.day_lamp); at
    night the chandeliers of the furniture light the hall."""
    spots = [(-9.7, 5.5), (0.0, 5.5), (9.7, 5.5), (0.0, 12.2), (-9.7, 15.2 + WELL_SHIFT), (9.7, 15.2 + WELL_SHIFT)]

    for u, d in spots:
        b.light((u, d, room.ceiling - 0.9), *shops.day_lamp(room))
        b.light((u, d, UPPER + room.ceiling - 0.9), *shops.day_lamp(room))

    b.light((0.0, 15.0 + WELL_SHIFT, UPPER + 2.4), room.spec["day_light"], 1.6, 12.0, None, "day_lights")


def build_shell(room) -> dict:
    b = Builder(f"shop_{room.shop_type}")
    b.materials["azulejo"] = town.textured_material("M_TownAzulejo", AZULEJO_TEXTURE, roughness=0.35)

    for key, (material_name, hex_color) in LAYLIGHT_COLORS.items():
        b.materials[key] = town.plain_material(material_name, srgb(hex_color), 0.4)

    build_walls(b, room)
    build_well_walls(b, room)
    build_wall_finishes(b, room, 0)
    build_wall_finishes(b, room, 1)

    for partition in room.partitions:  # cômodos do térreo em volta do saguão (locutório, portaria, madre, costura, latrinas)
        shops.build_partition(b, room, partition)

    build_ground_floor(b, room)
    build_gallery(b, room)
    build_top_ceiling(b, room)
    build_columns(b, room)
    build_stair(b, room)
    build_railings(b, room)
    build_lights(b, room)
    b.marker("shopkeeper", (*room.keeper, 0.0))

    return b.finish(town.SHOP_DIR / f"shop_{room.shop_type}.gltf", shops.shell_sidecar(room))
