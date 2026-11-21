"""Shell of the adventurers' guild and its bank: a guildhall and a banking hall instead of the open hall.

Ground floor after guild_layout.ROOMS. The great hall panelled to 3 m, plaster and a painted frieze above, a coffered
ceiling of dark beams, the gallery across its far end on turned posts (its underside stops the camera), a red runner
from the door to the dais. The bank with a marble floor and a plain plaster ceiling with a ceiling rose; the
strongroom with stone flags; the guildmaster's office and the trophy room under a lower ceiling. Outside: a
rusticated ground storey, tall arched windows with keystones, the guild's portal with its crest and the bank's own
door with its plaque, banners on poles over the street.

build_market_shops.py calls build_shell() for the "guild" entry of SHOPS (shell="guild_shell").
"""

import math

from mathutils import Matrix

import build_market_shops as shops
import build_town_houses as town
from build_town_houses import WOOD_DARK_BAND, Builder, Opening, srgb
from guild_layout import BANK, BANK_DOOR, BANK_WALL, BANK_WINDOWS, GALLERY, HALF_WALL, HALL_AXIS, HALL_BACK, HALL_WINDOWS, OFFICE, ROOMS, STRONGROOM, TROPHIES

shops.WALL_FINISHES.update({
    BANK: dict(dado="C9C2B0", trim="3F4A44"),
    STRONGROOM: dict(dado="9A968C", trim="4A4A4A"),
    OFFICE: dict(dado="6B4630", trim="3A2418", material="wood", uv=("band", *WOOD_DARK_BAND, 1.5)),
    TROPHIES: dict(dado="7A2F3A", trim="3A2418"),
})
WOOD_UV = ("band", *WOOD_DARK_BAND, 1.5)
OAK = srgb("6B4630")
OAK_DARK = srgb("3A2418")
GILT = srgb("D9A441")
CLARET = srgb("7A2F3A")
PLASTER = srgb("EFE8DA")
STONE_DARK = srgb("B5AC9C")
HALL_WINDOW = (1.8, 1.4, 5.2)  # width, sill, height to the apex
BANK_WINDOW = (1.1, 1.4, 3.6)
SIDE_WINDOWS = {"left": ((2.6, 1.6, 3.4, 3.0), (9.0, 1.6, 3.4, 3.0)), "right": ((3.0, 1.2, 1.6, 3.0), (10.2, 1.2, 1.6, 3.0))}  # d, width, sill, height
BACK_WINDOWS = ((-7.0, 1.2), (1.6, 1.2))  # u, width: office and trophy room (the strongroom has none)
BACK_WINDOW = (1.6, 1.8)  # sill, height
PANEL_TOP, PANEL_RAIL, STILE_PITCH = 3.0, 1.0, 1.2
FRIEZE = (6.3, 6.7)
COFFER = 2.1  # pitch of the ceiling beams of the great hall
COFFER_BEAM = (0.24, 0.34)  # width, drop
GALLERY_POSTS = (-9.8, -6.6, 0.2, 3.6)
GALLERY_RAIL = 1.0  # height of its balustrade
BALUSTER_PITCH = 0.3
LOW_CEILING = 4.4  # office, trophy room and strongroom
RUNNER = (1.6, 0.3, 5.5)  # width, d from, d to: the red carpet from the door to the dais
MARBLE = ("CFC6B4", "3F4A44")
RUSTICATION = 0.5  # course height of the channelled ground storey
BANNERS = ((-7.8, "7A2F3A"), (1.4, "2F3F6B"))  # u of the banner poles, cloth colour
LIGHTS = (((-3.2, 5.0, 5.2), 1.4, 7.5), ((8.6, 5.0, 4.8), 1.3, 7.0), ((8.6, 15.8, 3.6), 1.1, 5.0), ((1.6, 16.4, 3.6), 1.2, 5.5), ((-6.9, 15.0, 3.6), 1.0, 5.0))
LAMP_LIGHT = "FFD9A0"


# ---------- walls and openings ----------

def shop_openings(room) -> dict:
    """Guild portal, bank door, the arched windows of the hall and the bank; windows to the side streets and the yard."""
    door_u, door_width, door_height, door_top = room.door
    bank_u, bank_width, bank_height = BANK_DOOR
    hall_width, hall_sill, hall_height = HALL_WINDOW
    bank_window_width, bank_sill, bank_height_window = BANK_WINDOW
    back_sill, back_height = BACK_WINDOW
    front = [Opening(door_u + room.half, door_width, 0.0, door_height, door_top, kind="door"), Opening(bank_u + room.half, bank_width, 0.0, bank_height, "round", kind="door")]
    front += [Opening(u + room.half, hall_width, hall_sill, hall_height, "round", kind="window") for u in HALL_WINDOWS]
    front += [Opening(u + room.half, bank_window_width, bank_sill, bank_height_window, "round", kind="window") for u in BANK_WINDOWS]
    wall_u = {"left": lambda d: room.depth - shops.WALL - d, "right": lambda d: d - shops.WALL}
    sides = {side: [Opening(wall_u[side](d), width, sill, height, "round", kind="window") for d, width, sill, height in SIDE_WINDOWS[side]] for side in ("left", "right")}
    back = [Opening(room.half - u, width, back_sill, back_height, "flat", kind="window") for u, width in BACK_WINDOWS]

    return {"front": front, "back": back, **{side: sides[side] if side in room.exposed else [] for side in ("left", "right")}}


def window_bars(b: Builder, frame: Matrix, opening: Opening) -> None:
    """A mullion and transoms: tall leaded lights in three tiers."""
    tiers = (opening.spring - opening.bottom) / 3.0
    transoms = [opening.bottom + tiers * index for index in (1, 2)] + [opening.spring]

    b.box((opening.u - 0.03, 0.1, opening.bottom), (opening.u + 0.03, 0.14, opening.apex - 0.05), "paint", OAK_DARK, frame=frame)

    for z in transoms:
        b.box((opening.u - opening.width / 2.0, 0.1, z - 0.03), (opening.u + opening.width / 2.0, 0.14, z + 0.03), "paint", OAK_DARK, frame=frame)


def build_walls(b: Builder, room) -> dict:
    openings = shop_openings(room)
    frames = shops.wall_frames(room)
    windows = [(side, opening) for side, found in openings.items() for opening in found if opening.kind == "window"]

    shops.build_walls(b, room, openings)

    for side, opening in windows:
        window_bars(b, frames[side], opening)

    return openings


# ---------- floors and ceilings ----------

def build_floors(b: Builder, room) -> None:
    """Oak boards; a marble floor with a dark border and a star in the bank, stone flags in the strongroom; the red
    runner from the guild door to the dais."""
    board_count = round((room.right - room.left) / shops.BOARD_WIDTH)
    top = shops.FLOOR_TOP + shops.STONE_PATCH_LIFT
    bank_from, bank_to, bank_front, bank_back = ROOMS["bank"]
    strong_from, strong_to, strong_front, strong_back = ROOMS["strongroom"]
    runner_width, runner_from, runner_to = RUNNER
    star = Matrix.Translation(((bank_from + bank_to) / 2.0, 3.2, top))

    shops.build_plank_floor(b, room, board_count, (room.right - room.left) / board_count)
    b.collider((room.left, room.front, 0.0), (room.right, room.back, shops.FLOOR_TOP), name="WoodFloor")
    b.box((bank_from, bank_front, shops.FLOOR_TOP), (bank_to, bank_back, top), "paint", srgb(MARBLE[0]))
    b.box((strong_from, strong_front, shops.FLOOR_TOP), (strong_to, strong_back, top), "stone", STONE_DARK, uv=("world", 1.0))
    b.collider((bank_from, bank_front, shops.FLOOR_TOP), (strong_to, strong_back, top), name="StoneFloor")

    for inset in (0.35, 0.55):
        frame_from, frame_to, frame_front, frame_back = bank_from + inset, bank_to - inset, bank_front + inset, bank_back - inset
        border = [((frame_from, frame_front), (frame_to, frame_front + 0.08)), ((frame_from, frame_back - 0.08), (frame_to, frame_back)), ((frame_from, frame_front), (frame_from + 0.08, frame_back)), ((frame_to - 0.08, frame_front), (frame_to, frame_back))]

        for (u_from, d_from), (u_to, d_to) in border:
            b.box((u_from, d_from, top), (u_to, d_to, top + 0.004), "paint", srgb(MARBLE[1]))

    for angle in (0.0, 45.0):
        b.box((-1.1, -0.12, 0.0), (1.1, 0.12, 0.005), "paint", srgb(MARBLE[1]), frame=star @ Matrix.Rotation(math.radians(angle), 4, "Z"))
        b.box((-0.12, -1.1, 0.0), (0.12, 1.1, 0.005), "paint", srgb(MARBLE[1]), frame=star @ Matrix.Rotation(math.radians(angle), 4, "Z"))

    b.box((HALL_AXIS - runner_width / 2.0, runner_from, shops.FLOOR_TOP), (HALL_AXIS + runner_width / 2.0, runner_to, shops.FLOOR_TOP + 0.01), "paint", CLARET)
    b.box((HALL_AXIS - runner_width / 2.0 + 0.1, runner_from, shops.FLOOR_TOP + 0.01), (HALL_AXIS - runner_width / 2.0 + 0.16, runner_to, shops.FLOOR_TOP + 0.012), "paint", GILT)
    b.box((HALL_AXIS + runner_width / 2.0 - 0.16, runner_from, shops.FLOOR_TOP + 0.01), (HALL_AXIS + runner_width / 2.0 - 0.1, runner_to, shops.FLOOR_TOP + 0.012), "paint", GILT)


def build_ceilings(b: Builder, room) -> None:
    """Plaster under the upper floor; dark coffering beams across the great hall, a ceiling rose in the bank, a lower
    ceiling over the back rooms. Colliders at the beams and at the low ceiling."""
    hall_from, hall_to, hall_front, hall_back = ROOMS["hall"]
    bank_from, bank_to, _, bank_back = ROOMS["bank"]
    beam_width, beam_drop = COFFER_BEAM
    across = [hall_from + COFFER * index for index in range(1, int((hall_to - hall_from) / COFFER) + 1)]
    along = [hall_front + COFFER * index for index in range(1, int((hall_back - hall_front) / COFFER) + 1)]
    beam_bottom = room.ceiling - beam_drop

    b.box((room.left, room.front, room.ceiling), (room.right, room.back, room.storey), "plaster", PLASTER)
    b.collider((room.left, room.front, beam_bottom), (room.right, room.back, room.storey))

    for u in across:
        b.box((u - beam_width / 2.0, hall_front, beam_bottom), (u + beam_width / 2.0, hall_back, room.ceiling), "wood", OAK, uv=WOOD_UV)

    for d in along:
        b.box((hall_from, d - beam_width / 2.0, beam_bottom + 0.06), (hall_to, d + beam_width / 2.0, room.ceiling), "wood", OAK, uv=WOOD_UV)

    for name in ("hall",):
        u_from, u_to, d_from, d_to = ROOMS[name]
        b.box((u_from, d_from, beam_bottom), (u_to, d_from + 0.3, room.ceiling), "wood", OAK_DARK, uv=WOOD_UV)
        b.box((u_from, d_to - 0.3, beam_bottom), (u_to, d_to, room.ceiling), "wood", OAK_DARK, uv=WOOD_UV)

    b.cylinder(((bank_from + bank_to) / 2.0, bank_back / 2.0, room.ceiling - 0.08), 0.7, 0.08, 12, "plaster", PLASTER)

    for name in ("office", "trophies", "strongroom"):
        u_from, u_to, d_from, d_to = ROOMS[name]
        b.box((u_from, d_from, LOW_CEILING), (u_to, d_to, LOW_CEILING + 0.2), "plaster", PLASTER)
        b.collider((u_from, d_from, LOW_CEILING - 0.05), (u_to, d_to, LOW_CEILING + 0.2))


# ---------- the great hall ----------

def panelling(b: Builder, axis: str, face_at: float, normal: int, span: tuple, cuts: list) -> None:
    """Oak wainscot to PANEL_TOP: boards, stiles, a middle and a top rail, the skirting."""
    for span_from, span_to in shops.free_spans(span[0], span[1], cuts):
        stiles = [span_from + STILE_PITCH * index for index in range(1, int((span_to - span_from) / STILE_PITCH) + 1)]

        b.box(*shops.wall_slab(axis, face_at, normal, (span_from, span_to), 0.0, 0.03, (0.0, PANEL_TOP)), "wood", OAK, uv=WOOD_UV)
        b.box(*shops.wall_slab(axis, face_at, normal, (span_from, span_to), 0.0, 0.07, (0.0, 0.2)), "wood", OAK_DARK, uv=WOOD_UV)

        for z in (PANEL_RAIL, PANEL_TOP - 0.12):
            b.box(*shops.wall_slab(axis, face_at, normal, (span_from, span_to), 0.0, 0.06, (z, z + 0.12)), "wood", OAK_DARK, uv=WOOD_UV)

        for stile in stiles:
            b.box(*shops.wall_slab(axis, face_at, normal, (stile - 0.05, min(stile + 0.05, span_to)), 0.0, 0.05, (0.2, PANEL_TOP)), "wood", OAK_DARK, uv=WOOD_UV)


def hall_faces(room, openings: dict) -> list:
    """(axis, face, normal, span, cuts) of the four faces of the great hall, doorways and low windows cut."""
    hall_from, hall_to, hall_front, hall_back = ROOMS["hall"]
    front_cuts = [(opening.u - room.half - opening.width / 2.0 - 0.1, opening.u - room.half + opening.width / 2.0 + 0.1) for opening in openings["front"] if opening.bottom < PANEL_TOP]
    side_cuts = [(4.6 - 1.0, 4.6 + 1.0)]  # the doorway to the bank
    back_cuts = [(-9.0 - 0.75, -9.0 + 0.75), (2.6 - 0.9, 2.6 + 0.9)]

    return [
        ("d", hall_front, 1, (hall_from, hall_to), front_cuts),
        ("u", hall_from, 1, (hall_front, hall_back), []),
        ("u", hall_to, -1, (hall_front, hall_back), side_cuts),
        ("d", hall_back, -1, (hall_from, hall_to), back_cuts),
    ]


def build_hall(b: Builder, room, openings: dict) -> None:
    for axis, face_at, normal, span, cuts in hall_faces(room, openings):
        panelling(b, axis, face_at, normal, span, cuts)
        b.box(*shops.wall_slab(axis, face_at, normal, span, 0.0, 0.02, FRIEZE), "paint", CLARET)
        b.box(*shops.wall_slab(axis, face_at, normal, span, 0.0, 0.04, (FRIEZE[1], FRIEZE[1] + 0.05)), "metal", GILT)

    build_gallery(b, room)


def build_gallery(b: Builder, room) -> None:
    """Across the far end of the hall on turned posts: joists, floor, fascia, a balustrade with a handrail, the door
    to the stair painted on the wall behind it, banners hanging from the fascia."""
    hall_from, hall_to, _, hall_back = ROOMS["hall"]
    edge, underside = GALLERY
    floor_top = underside + 0.3
    balusters = [hall_from + 0.12 + BALUSTER_PITCH * index for index in range(int((hall_to - hall_from - 0.24) / BALUSTER_PITCH) + 1)]
    joists = [hall_from + 0.8 * index for index in range(1, int((hall_to - hall_from) / 0.8))]

    b.camera_stop(b.box((hall_from, edge, underside + 0.12), (hall_to, hall_back, floor_top), "wood", OAK, uv=WOOD_UV))
    b.box((hall_from, edge - 0.06, underside - 0.06), (hall_to, edge + 0.08, floor_top + 0.04), "wood", OAK_DARK, uv=WOOD_UV)
    b.collider((hall_from, edge, underside), (hall_to, hall_back, floor_top + GALLERY_RAIL))

    for u in joists:
        b.box((u - 0.07, edge, underside), (u + 0.07, hall_back, underside + 0.12), "wood", OAK_DARK, uv=WOOD_UV)

    for u in balusters:
        b.box((u - 0.035, edge - 0.02, floor_top), (u + 0.035, edge + 0.05, floor_top + GALLERY_RAIL - 0.08), "wood", OAK_DARK, uv=WOOD_UV)

    b.box((hall_from, edge - 0.05, floor_top + GALLERY_RAIL - 0.08), (hall_to, edge + 0.09, floor_top + GALLERY_RAIL), "wood", OAK, uv=WOOD_UV)

    for u in GALLERY_POSTS:
        b.cylinder((u, edge + 0.02, 0.0), 0.16, underside - 0.06, 8, "wood", OAK_DARK, uv=WOOD_UV)
        b.box((u - 0.24, edge - 0.22, 0.0), (u + 0.24, edge + 0.26, 0.35), "wood", OAK_DARK, uv=WOOD_UV)
        b.box((u - 0.3, edge - 0.25, underside - 0.3), (u + 0.3, edge + 0.29, underside - 0.06), "wood", OAK, uv=WOOD_UV)
        b.collider((u - 0.24, edge - 0.22, 0.0), (u + 0.24, edge + 0.26, underside))

    b.box((HALL_AXIS - 0.6, hall_back - 0.04, floor_top), (HALL_AXIS + 0.6, hall_back, floor_top + 2.2), "wood", OAK_DARK, uv=WOOD_UV)

    for u, colour in ((-9.4, CLARET), (2.9, srgb("2F3F6B"))):
        b.box((u - 0.45, edge - 0.1, floor_top - 1.4), (u + 0.45, edge - 0.07, floor_top + GALLERY_RAIL - 0.1), "paint", colour)
        b.box((u - 0.18, edge - 0.11, floor_top - 0.6), (u + 0.18, edge - 0.1, floor_top - 0.1), "metal", GILT)


# ---------- finishes of the other rooms ----------

def outer_faces(room, openings: dict) -> list:
    """(axis, face, normal, span, finish, cuts) of each back room's or the bank's stretch of the outer walls."""
    bank_cuts = [(opening.u - room.half - opening.width / 2.0 - 0.15, opening.u - room.half + opening.width / 2.0 + 0.15) for opening in openings["front"] if opening.u - room.half > BANK_WALL]
    walls = {"front": ("d", room.front, 1, bank_cuts), "back": ("d", room.back, -1, []), "left": ("u", room.left, 1, []), "right": ("u", room.right, -1, [])}
    stretches = (
        ("bank", "front", BANK), ("bank", "right", BANK), ("strongroom", "right", STRONGROOM), ("strongroom", "back", STRONGROOM),
        ("office", "left", OFFICE), ("office", "back", OFFICE), ("trophies", "back", TROPHIES),
    )
    along = lambda name, side: ROOMS[name][:2] if side in ("front", "back") else ROOMS[name][2:]

    return [(walls[side][0], walls[side][1], walls[side][2], along(name, side), finish, walls[side][3]) for name, side, finish in stretches]


def build_finishes(b: Builder, room, openings: dict) -> None:
    for axis, face_at, normal, span, finish, cuts in outer_faces(room, openings):
        shops.dress_wall_face(b, room, axis, face_at, normal, span, finish, cuts, cuts)


# ---------- facade ----------

def build_facade(b: Builder, room, openings: dict) -> None:
    """Channelled courses over the ground storey, a plinth, keystones over the arches, the guild's crest over its
    door, the bank's plaque, banners on poles."""
    front = openings["front"]
    doors = [opening for opening in front if opening.kind == "door"]
    courses = [RUSTICATION * index for index in range(1, int(room.storey / RUSTICATION))]
    plinth_cuts = [(opening.u - room.half - opening.width / 2.0, opening.u - room.half + opening.width / 2.0) for opening in doors]

    for z in courses:
        cuts = [(opening.u - room.half - opening.width / 2.0 - 0.05, opening.u - room.half + opening.width / 2.0 + 0.05) for opening in front if opening.bottom - 0.05 < z < opening.apex + 0.35]

        for span_from, span_to in shops.free_spans(-room.half, room.half, cuts):
            b.box((span_from, -0.02, z - 0.025), (span_to, 0.0, z + 0.025), "paint", STONE_DARK)

    for span_from, span_to in shops.free_spans(-room.half, room.half, plinth_cuts):
        b.box((span_from, -0.12, 0.0), (span_to, 0.0, 0.6), "stone", STONE_DARK, uv=("world", 1.0))

    for opening in front:
        u = opening.u - room.half
        b.prism([(u - 0.18, opening.apex - 0.05), (u + 0.18, opening.apex - 0.05), (u + 0.24, opening.apex + 0.45), (u - 0.24, opening.apex + 0.45)], -0.1, 0.0, "plaster", PLASTER)

    guild_u, bank_u = room.door[0], BANK_DOOR[0]
    portal_top = doors[0].apex + 0.5
    crest = [(guild_u - 0.55, portal_top + 0.2), (guild_u + 0.55, portal_top + 0.2), (guild_u + 0.55, portal_top + 1.0), (guild_u, portal_top + 1.35), (guild_u - 0.55, portal_top + 1.0)]

    for side in (-1, 1):
        u = guild_u + side * (doors[0].width / 2.0 + 0.3)
        b.box((u - 0.2, -0.2, 0.0), (u + 0.2, 0.0, portal_top), "plaster", PLASTER)

    b.box((guild_u - doors[0].width / 2.0 - 0.6, -0.26, portal_top), (guild_u + doors[0].width / 2.0 + 0.6, 0.0, portal_top + 0.2), "plaster", PLASTER)
    b.prism(list(reversed(crest)), -0.3, -0.26, "paint", CLARET)
    b.prism([(guild_u - 0.06, portal_top + 0.3), (guild_u + 0.06, portal_top + 0.3), (guild_u + 0.06, portal_top + 1.2), (guild_u - 0.06, portal_top + 1.2)], -0.32, -0.3, "metal", GILT)
    b.prism([(guild_u - 0.4, portal_top + 0.75), (guild_u + 0.4, portal_top + 0.75), (guild_u + 0.4, portal_top + 0.85), (guild_u - 0.4, portal_top + 0.85)], -0.32, -0.3, "metal", GILT)
    b.box((bank_u - 0.7, -0.06, doors[1].apex + 0.55), (bank_u + 0.7, 0.0, doors[1].apex + 0.95), "metal", GILT)
    b.cylinder((bank_u, -0.06, doors[1].apex + 0.75), 0.16, 0.04, 12, "metal", GILT, axis="Y")

    for u, colour in BANNERS:
        pole = Matrix.Translation((u, 0.0, 5.6)) @ Matrix.Rotation(math.radians(-35.0), 4, "X")
        b.beam((u, 0.0, 5.6), (u, -1.7, 6.8), 0.05, 0.05, "metal", srgb("2A2A2A"))
        b.box((-0.5, -0.03, -1.9), (0.5, 0.0, 0.0), "paint", srgb(colour), frame=Matrix.Translation((u, -1.45, 6.6)))
        b.box((-0.2, -0.04, -1.2), (0.2, -0.03, -0.6), "metal", GILT, frame=Matrix.Translation((u, -1.45, 6.6)))


# ---------- assembly ----------

def build_shell(room) -> dict:
    b = Builder(f"shop_{room.shop_type}")
    openings = build_walls(b, room)

    build_floors(b, room)
    build_ceilings(b, room)

    for partition in room.partitions:
        shops.build_partition(b, room, partition)

    build_hall(b, room, openings)
    build_finishes(b, room, openings)
    shops.build_roof(b, room)
    build_facade(b, room, openings)

    for position, energy, light_range in LIGHTS:
        b.light(position, LAMP_LIGHT, energy, light_range)

    b.marker("shopkeeper", (*room.keeper, 0.0))

    return b.finish(town.SHOP_DIR / f"shop_{room.shop_type}.gltf", shops.shell_sidecar(room))
