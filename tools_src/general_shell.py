"""Shell of the general store and bakery: two shops behind one painted wooden shopfront instead of the open hall.

Ground floor after general_layout.ROOMS: the grocer's under a pale boarded ceiling, its storeroom, the baker's shop
with tiled walls and the bakehouse with a chequered floor. Outside: a shopfront of pilasters, a fascia with name
panels and a cornice, stall boards under small-paned shop windows, two street doors with transom lights, crates of
produce on the pavement; side and back windows where the house has them.

build_market_shops.py calls build_shell() for the "general" entry of SHOPS (shell="general_shell").
"""

from mathutils import Matrix

import build_market_shops as shops
import build_town_houses as town
from build_town_houses import WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, Opening, srgb
from general_layout import BACK_WINDOW, BACK_WINDOWS, BAKEHOUSE, BAKERY, BAKERY_DOOR, FRONT_WINDOWS, GROCER, ROOMS, SIDE_WINDOW, SIDE_WINDOWS, STOREROOM, WINDOW_SILL, WINDOW_TOP

shops.WALL_FINISHES.update({
    GROCER: dict(dado="8B5A3C", trim="4A2E1E", material="wood", uv=("band", *WOOD_LIGHT_BAND, 1.5)),
    STOREROOM: dict(dado="B9AA92", trim="5A4636"),
    BAKERY: dict(dado="FFFFFF", trim="2F5FA8", material="azulejo"),
    BAKEHOUSE: dict(dado="D9CDB4", trim="6B4A32"),
})
SHOPFRONT = srgb("2F4A3F")  # painted wood of the shopfront, the grocer's green
SHOPFRONT_PANEL = srgb("3F6B55")
GILT = srgb("E8B64A")
NAME_PANEL = srgb("F2E6CF")
PILASTERS = (-8.65, -4.85, -2.45, 1.2, 4.1, 6.0, 8.65)  # u of the shopfront pilasters
FASCIA = (3.3, 3.9)  # z of the fascia board
NAME_PANELS = ((-8.2, 0.7), (1.7, 8.2))
TRANSOM = 2.55  # z of the transom bar of the shop windows
BOARDS = srgb("E8DCC0")  # the grocer's painted board ceiling: one slab, thin grooves draw the boards
BOARD_GROOVE = srgb("9C8C70")
BOARD_PITCH = 0.16
CEILING_PLASTER = srgb("F2EBDD")
BAKERY_TILES = ("EFE6D2", "D9B48A")  # cream and buff tiles in the baker's shop
BAKEHOUSE_TILES = ("EFE6D2", "4A4540")  # black and white in the bakehouse
STREET_PROPS = (("crate_open", -7.3, -0.5, "apples"), ("crate_open", -5.9, -0.5, "roots"), ("barrel_group", -1.6, -0.6, None), ("wicker_basket", 3.0, -0.45, "bread"))
LIGHTS = ((-4.6, 4.0), (-4.6, 9.4), (-4.0, 15.9), (4.9, 2.6), (4.9, 11.0))
LAMP_LIGHT = "FFD9A0"
LAMP_DROP = 0.9
LAMP_RANGE = 5.5  # each lamp lights its own room: the walls do not stop a shadowless light, the range does


# ---------- walls and openings ----------

def shop_openings(room) -> dict:
    """Both street doors and the four shop windows; side windows to the side street, back windows (wall-local u)."""
    door_u, door_width, door_height, door_top = room.door
    bakery_u, bakery_width, bakery_height = BAKERY_DOOR
    side_width, side_sill, side_height = SIDE_WINDOW
    back_width, back_sill, back_height = BACK_WINDOW
    front = [Opening(door_u + room.half, door_width, 0.0, door_height, door_top, kind="door"), Opening(bakery_u + room.half, bakery_width, 0.0, bakery_height, "flat", kind="door")]
    front += [Opening(u + room.half, width, WINDOW_SILL, WINDOW_TOP - WINDOW_SILL, "flat", kind="vitrine") for u, width in FRONT_WINDOWS]
    side = [Opening(d - shops.WALL, side_width, side_sill, side_height, "flat", kind="vitrine") for d in SIDE_WINDOWS]
    back = [Opening(room.half - u, back_width, back_sill, back_height, "flat", kind="vitrine") for u in BACK_WINDOWS]

    return {"front": front, "back": back, "left": [], "right": side if "right" in room.exposed else []}


def window_bars(b: Builder, frame: Matrix, opening: Opening, is_shop_window: bool) -> None:
    """Glazing bars: a transom with small panes over the big lower light of a shop window, a cross elsewhere."""
    left = opening.u - opening.width / 2.0
    transom = TRANSOM if is_shop_window else opening.bottom + (opening.apex - opening.bottom) / 2.0
    upper_panes = max(2, round(opening.width / 0.32)) if is_shop_window else 2
    verticals = [left + opening.width * index / upper_panes for index in range(1, upper_panes)]

    b.box((left, 0.1, transom - 0.03), (left + opening.width, 0.13, transom + 0.03), "paint", SHOPFRONT, frame=frame)

    for u in verticals:
        b.box((u - 0.02, 0.1, transom), (u + 0.02, 0.13, opening.apex), "paint", SHOPFRONT, frame=frame)

    if not is_shop_window:
        b.box((opening.u - 0.025, 0.1, opening.bottom), (opening.u + 0.025, 0.13, transom), "paint", SHOPFRONT, frame=frame)


def build_walls(b: Builder, room) -> dict:
    openings = shop_openings(room)
    frames = shops.wall_frames(room)
    windows = [(side, opening) for side, found in openings.items() for opening in found if opening.kind == "vitrine"]

    shops.build_walls(b, room, openings)

    for side, opening in windows:
        window_bars(b, frames[side], opening, side == "front")

    return openings


# ---------- floors and ceilings ----------

def build_floors(b: Builder, room) -> None:
    """Plank floors, small chequered tiles in the baker's shop, black and white tiles in the bakehouse."""
    board_count = round((room.right - room.left) / shops.BOARD_WIDTH)
    top = shops.FLOOR_TOP + shops.STONE_PATCH_LIFT
    patches = (("bakery", BAKERY_TILES[0]), ("bakehouse", BAKEHOUSE_TILES[0]))

    shops.build_plank_floor(b, room, board_count, (room.right - room.left) / board_count)
    b.collider((room.left, room.front, 0.0), (room.right, room.back, shops.FLOOR_TOP), name="WoodFloor")

    for name, tint in patches:
        u_from, u_to, d_from, d_to = ROOMS[name]
        b.box((u_from, d_from, shops.FLOOR_TOP), (u_to, d_to, top), "paint", srgb(tint))
        b.collider((u_from, d_from, shops.FLOOR_TOP), (u_to, d_to, top), name="StoneFloor")

    chequer(b, ROOMS["bakery"], top, 0.3, BAKERY_TILES[1])
    chequer(b, ROOMS["bakehouse"], top, 0.4, BAKEHOUSE_TILES[1])


def chequer(b: Builder, bounds: tuple, top: float, size: float, dark: str) -> None:
    """Second-colour tiles on every other cell of a tiled floor."""
    u_from, u_to, d_from, d_to = bounds
    columns, rows = int((u_to - u_from) / size), int((d_to - d_from) / size)
    dark_cells = [index for index in range(columns * rows) if (index % columns + index // columns) % 2]
    tint = srgb(dark)

    for index in dark_cells:
        u, d = u_from + (index % columns) * size, d_from + (index // columns) * size
        b.box((u, d, top), (u + size, d + size, top + 0.004), "paint", tint)


def build_ceiling(b: Builder, room) -> None:
    """Plaster under the upper floor; pale painted boards under it in the grocer's. Collider at the boards."""
    u_from, u_to, d_from, d_to = ROOMS["store"]

    b.box((room.left, room.front, room.ceiling), (room.right, room.back, room.storey), "plaster", CEILING_PLASTER)
    b.collider((room.left, room.front, room.ceiling - 0.05), (room.right, room.back, room.storey))
    b.box((u_from, d_from, room.ceiling - 0.03), (u_to, d_to, room.ceiling), "paint", BOARDS)

    for groove in range(1, round((u_to - u_from) / BOARD_PITCH)):
        u = u_from + groove * BOARD_PITCH
        b.box((u - 0.006, d_from, room.ceiling - 0.034), (u + 0.006, d_to, room.ceiling - 0.03), "paint", BOARD_GROOVE)


# ---------- finishes ----------

def outer_faces(room, openings: dict) -> list:
    """(axis, face, normal, span, finish, cuts) of each room's stretch of the outer walls, doors and low windows cut."""
    front_cuts = [(opening.u - room.half - opening.width / 2.0 - 0.15, opening.u - room.half + opening.width / 2.0 + 0.15) for opening in openings["front"]]
    walls = {"front": ("d", room.front, 1, front_cuts), "back": ("d", room.back, -1, []), "left": ("u", room.left, 1, []), "right": ("u", room.right, -1, [])}
    stretches = (
        ("store", "front", GROCER), ("storeroom", "left", STOREROOM), ("storeroom", "back", STOREROOM),
        ("bakery", "front", BAKERY), ("bakery", "right", BAKERY), ("bakehouse", "right", BAKEHOUSE), ("bakehouse", "back", BAKEHOUSE),
    )
    along = lambda name, side: ROOMS[name][:2] if side in ("front", "back") else ROOMS[name][2:]

    return [(walls[side][0], walls[side][1], walls[side][2], along(name, side), finish, walls[side][3]) for name, side, finish in stretches]


def build_finishes(b: Builder, room, openings: dict) -> None:
    for axis, face_at, normal, span, finish, cuts in outer_faces(room, openings):
        shops.dress_wall_face(b, room, axis, face_at, normal, span, finish, cuts, cuts)


# ---------- shopfront ----------

def build_shopfront(b: Builder, room, openings: dict) -> None:
    """Pilasters on plinth blocks, the fascia with its name panels and gilt beading, a moulded cornice (the camera
    stops under it), stall boards under the windows and transom lights over the doors."""
    wood_uv = ("band", *WOOD_DARK_BAND, 1.5)
    windows = [opening for opening in openings["front"] if opening.kind == "vitrine"]
    doors = [opening for opening in openings["front"] if opening.kind == "door"]

    for u in PILASTERS:
        b.box((u - 0.17, -0.14, 0.0), (u + 0.17, 0.0, FASCIA[0]), "paint", SHOPFRONT)
        b.box((u - 0.2, -0.18, 0.0), (u + 0.2, 0.0, 0.4), "paint", SHOPFRONT_PANEL)
        b.box((u - 0.2, -0.18, FASCIA[0] - 0.25), (u + 0.2, 0.0, FASCIA[0]), "paint", SHOPFRONT_PANEL)

    b.box((-room.house.half, -0.12, FASCIA[0]), (room.house.half, 0.0, FASCIA[1]), "wood", SHOPFRONT, uv=wood_uv)

    for u_from, u_to in NAME_PANELS:
        b.box((u_from, -0.14, FASCIA[0] + 0.1), (u_to, -0.12, FASCIA[1] - 0.1), "paint", NAME_PANEL)
        b.box((u_from - 0.04, -0.15, FASCIA[0] + 0.06), (u_to + 0.04, -0.14, FASCIA[0] + 0.1), "metal", GILT)
        b.box((u_from - 0.04, -0.15, FASCIA[1] - 0.1), (u_to + 0.04, -0.14, FASCIA[1] - 0.06), "metal", GILT)

    b.camera_stop(b.box((-room.house.half - 0.05, -0.32, FASCIA[1]), (room.house.half + 0.05, 0.0, FASCIA[1] + 0.16), "paint", SHOPFRONT))

    for opening in windows:
        u = opening.u - room.half
        b.box((u - opening.width / 2.0, -0.1, shops.FLOOR_TOP), (u + opening.width / 2.0, 0.0, opening.bottom), "paint", SHOPFRONT)
        b.box((u - opening.width / 2.0 + 0.12, -0.12, 0.14), (u + opening.width / 2.0 - 0.12, -0.1, opening.bottom - 0.1), "paint", SHOPFRONT_PANEL)

    for opening in doors:
        u = opening.u - room.half
        b.box((u - opening.width / 2.0, -0.06, opening.apex), (u + opening.width / 2.0, 0.0, FASCIA[0]), "glass", srgb("3A4E66"))
        b.box((u - opening.width / 2.0 - 0.06, -0.1, opening.apex - 0.04), (u + opening.width / 2.0 + 0.06, 0.0, opening.apex + 0.06), "paint", SHOPFRONT)


def build_street_goods(b: Builder) -> None:
    """Produce crates under the grocer's window, a barrel by its door, bread in a basket by the baker's."""
    for name, u, d, variant in STREET_PROPS:
        width, depth, height = shops.PROPS[name]["size"]
        frame = Matrix.Translation((u, d, 0.0))
        options = dict(variant=variant) if variant else {}

        shops.PROPS[name]["build"](b, frame, **options)
        b.collider((-width / 2.0, -depth / 2.0, 0.0), (width / 2.0, depth / 2.0, height), frame)


# ---------- assembly ----------

def build_shell(room) -> dict:
    b = Builder(f"shop_{room.shop_type}")
    b.materials["azulejo"] = town.textured_material("M_TownAzulejo", shops.AZULEJO_TEXTURE, roughness=0.35)
    openings = build_walls(b, room)

    build_floors(b, room)
    build_ceiling(b, room)

    for partition in room.partitions:
        shops.build_partition(b, room, partition)

    build_finishes(b, room, openings)
    shops.build_roof(b, room)
    build_shopfront(b, room, openings)
    build_street_goods(b)

    for u, d in LIGHTS:
        b.light((u, d, room.ceiling - LAMP_DROP), LAMP_LIGHT, 1.4, LAMP_RANGE)

    b.marker("shopkeeper", (*room.keeper, 0.0))

    return b.finish(town.SHOP_DIR / f"shop_{room.shop_type}.gltf", shops.shell_sidecar(room))
