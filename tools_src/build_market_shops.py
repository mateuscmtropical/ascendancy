"""Model the big walk-in shops of the market squares (docs/research/shops.md): one third to one half of a block each.

Outputs per shop, each with a JSON sidecar (AABB, doors, lights, markers):
  art/town/shops/shop_<type>.gltf            shell: walls with real openings, floor, ceiling, posts, roof, awnings, colliders
  art/town/shops/shop_<type>_interior.gltf   furniture and goods fused in one mesh (hidden from afar by shop_interior.gd)

Same coords as build_town_houses.py: lot front on Y = 0, street toward -Y, u across, d into the lot, z up.
Furniture comes from the prop libraries tools_src/shop_props_*.py (PROPS contract in shop_props_common.py); the
plans of each shop live in shop_layouts.py. A prop named by a plan but not modelled yet is reported and skipped.

Usage:
  blender -b --factory-startup -P tools_src/build_market_shops.py -- [shop_type ...]
"""

import importlib
import itertools
import math
import sys
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_town_houses as town  # noqa: E402
import shop_layouts  # noqa: E402
from build_hub_scene import SHOP_LOTS, town_lots  # noqa: E402
from build_town_houses import STONE, WALL, WOOD, WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, House, Opening, srgb  # noqa: E402

PROP_MODULES = ("shop_props_common", "shop_props_arms", "shop_props_food", "shop_props_arcane")
CEILING_SLAB = 0.4
PIER = 0.6  # parede cheia entre vãos e nos cantos da fachada
VITRINE_PITCH = 3.0  # uma vitrine a cada tantos metros de fachada livre
VITRINE_SILL = 0.7
DOOR_CLEARANCE = 3.0  # faixa livre atrás da porta
BOARD_WIDTH = 0.6
JOIST_SPACING = 1.6
POST = 0.32
LIGHT_SPACING = 9.0
LIGHT_ROWS = (0.28, 0.72)  # frações da profundidade
AWNING_REACH = 1.7
AWNING_STRIPE = 0.5
SIDE_WINDOW_PITCH = 4.0
COLLIDER_MAX_HEIGHT = 2.4
PLINTH_HEIGHT = 0.5
FLOOR_TOP = 0.05  # acima do calçamento da quadra, para o piso do salão não brigar com ele
FILL_PITCH = 2.5  # passo da grade de ilhas com que fill_floor enche o chão livre
FILL_AISLE = 0.55
FILL_LANE = 1.9  # meia largura do corredor que fica livre da porta ao balcão
FILL_BACK = 6.0  # fundo do salão que fica para o balcão e o lojista
ISLAND_AISLE = 0.9  # folga em volta de cada ilha que scatter() põe no meio do salão

SHOPS = {  # tipo -> casca; door = (u, largura, altura, topo); roof_shape como ARCHETYPE_SPECS; awning = (cor, cor)
    "smith": dict(archetype="pedra", wall="cinza", roof="ardosia", accent="oxido", storeys=(5.2,), roof_shape=("gable_parallel", dict(pitch=30.0, eave_front=0.5, eave_back=0.4)), features=("dormers",), floor="stone", awning=("B5533F", "F2E6CF"), door=(-5.0, 2.6, 3.2, "segment"), open_bays=((7.4, 7.2),), chimney=dict(u=8.2, d=18.3, extra=1.5, pots=0, material="stone"), light="FFC890"),
    "guild": dict(archetype="palacete", wall="clara", roof="ardosia", accent="vinho", storeys=(7.4, 3.4), roof_shape=("hip", dict(pitch=24.0, eave_front=0.9, eave_back=0.5)), floor="stone", awning=("7A2F3A", "D9A441"), door=(0.0, 3.2, 4.2, "round"), features=("eave_brackets",), quoins=True, cornice=True, light="FFD9A0"),
    "tavern": dict(archetype="tudor", wall="creme", roof="velha", accent="vinho", storeys=(5.0, 3.0), roof_shape=("gable_parallel", dict(pitch=38.0, eave_front=0.5, eave_back=0.4)), floor="wood", awning=("7A2F3A", "F2E6CF"), door=(0.0, 2.6, 3.0, "pointed"), features=("half_timber",), jetty=0.35, chimney=dict(u=-7.4, d=9.7, extra=1.2, pots=2), light="FFC27A"),
    "armor": dict(archetype="hanseatica", wall="tijolo", roof="terracota", accent="vinho", storeys=(4.6, 3.2), roof_shape=("gable_street", dict(pitch=36.0, gable="stepped")), floor="stone", awning=("7A2F3A", "D8DCE4"), door=(0.0, 2.4, 3.0, "round"), features=("stone_bands",), light="FFD9A0"),
    "general": dict(archetype="sobrado", wall="creme", roof="terracota", accent="verde", storeys=(4.4, 3.2), roof_shape=("hip", dict(pitch=26.0, eave_front=0.6, eave_back=0.5)), floor="wood", awning=("B5533F", "F4EFE6"), door=(0.0, 2.4, 2.9, "segment"), features=("iron_balcony", "finials"), quoins=True, cornice=True, light="FFD9A0"),
    "magic": dict(archetype="torre", wall="lilas", roof="ardosia", accent="azul", storeys=(5.6, 3.0), roof_shape=("gable_street", dict(pitch=42.0, gable="bell")), floor="wood", awning=("4A3A8E", "C9B6D9"), door=(0.0, 2.2, 3.2, "pointed"), light="C9B0FF"),
    "alchemy": dict(archetype="fachwerk", wall="salvia", roof="velha", accent="verde", storeys=(4.6, 2.9), roof_shape=("gable_street", dict(pitch=40.0, gable="half_hip")), floor="wood", awning=("2F6B4F", "D9E8B0"), door=(0.0, 2.2, 2.9, "round"), features=("half_timber",), jetty=0.3, chimney=dict(u=-6.0, d=15.0, extra=1.2, pots=2), light="C8F0B0"),
    "tailor": dict(archetype="mediterranea", wall="rosa", roof="clara", accent="vinho", storeys=(4.4, 3.0), roof_shape=("gable_parallel", dict(pitch=18.0, eave_front=0.4, eave_back=0.3)), floor="wood", awning=("C0517A", "F4EFE6"), door=(0.0, 2.2, 2.9, "round"), features=("flower_boxes",), light="FFDCC0"),
    "library": dict(archetype="palacete", wall="dourada", roof="cobre", accent="azul", storeys=(7.4, 3.2), roof_shape=("hip", dict(pitch=22.0, eave_front=0.8, eave_back=0.5)), floor="wood", awning=None, sill=1.1, vitrine_top="round", door=(0.0, 3.2, 4.2, "round"), features=("eave_brackets",), quoins=True, cornice=True, light="FFDFA8"),
    "school": dict(archetype="sobrado", wall="amarelo", roof="terracota", accent="verde", storeys=(4.6, 3.6), roof_shape=("hip", dict(pitch=26.0, eave_front=0.6, eave_back=0.5)), floor="wood", awning=None, sill=1.1, door=(0.0, 2.6, 3.2, "segment"), features=("finials",), quoins=True, cornice=True, light="FFE2B0"),
    "seminary": dict(archetype="pedra", wall="caiada", roof="velha", accent="vinho", storeys=(5.2, 3.2), roof_shape=("gable_parallel", dict(pitch=36.0, eave_front=0.4, eave_back=0.4)), floor="stone", awning=None, sill=1.3, vitrine_top="pointed", door=(0.0, 2.6, 3.6, "pointed"), features=("dormers",), light="FFDCB0"),
}


def load_props() -> dict:
    """PROPS of every prop library already written (the libraries land one by one)."""
    props = {}

    for module_name in PROP_MODULES:
        if (Path(__file__).resolve().parent / f"{module_name}.py").exists():
            props.update(importlib.import_module(module_name).PROPS)

    return props


PROPS = load_props()


class Room:
    """Measurements of one shop: body, inner hall bounds and heights (facade coords)."""

    def __init__(self, shop_type: str) -> None:
        spec = SHOPS[shop_type]
        width, depth = SHOP_LOTS[shop_type]

        self.shop_type = shop_type
        self.spec = spec
        self.house = House(width, depth, spec["storeys"], spec["wall"], spec["roof"], spec["accent"], town.hash_seed(shop_type))
        self.house.jetty = spec.get("jetty", 0.0)
        self.half = self.house.half
        self.depth = self.house.depth
        self.storey = spec["storeys"][0]
        self.ceiling = self.storey - CEILING_SLAB
        self.left, self.right = -self.half + WALL, self.half - WALL
        self.front, self.back = WALL, self.depth - WALL
        self.exposed = next(lot["exposed"] for lot in town_lots() if lot.get("shop") == shop_type)
        self.door = spec["door"]
        self.plan = shop_layouts.PLANS.get(shop_type, {})
        self.keeper = self.plan.get("keeper", (spec["door"][0], self.back - 2.4))
        self.posts = self.plan.get("posts", self.default_posts())
        self.partitions = self.plan.get("partitions", ())

    def default_posts(self) -> list:
        """Posts on an odd number of ~6 m bays (the door axis stays free), two rows deep."""
        bays = max(3, 2 * round((2.0 * self.half / 6.0 - 1.0) / 2.0) + 1)
        post_us = [-self.half + 2.0 * self.half * index / bays for index in range(1, bays)]

        return list(itertools.product(post_us, (self.depth / 3.0, 2.0 * self.depth / 3.0)))


# ---------- walls ----------

def close_opening_top(b: Builder, room: Room, frame: Matrix, opening: Opening) -> None:
    house = room.house
    half = opening.width / 2.0

    town.wall_piece(b, (opening.u - half, 0.0, opening.apex), (opening.u + half, WALL, room.storey), house.wall_material, house.wall_tint, frame)

    if opening.top != "flat":
        b.prism(opening.arc() + [(opening.u - half, opening.apex), (opening.u + half, opening.apex)], 0.0, WALL, house.wall_material, house.wall_tint, frame=frame)


def dress_door(b: Builder, room: Room, frame: Matrix, opening: Opening) -> None:
    """Flush stone threshold, moulding and two leaves fixed open into the hall."""
    house = room.house
    half = opening.width / 2.0
    leaf = half - 0.02
    leaf_height = opening.spring - 0.05
    swing = math.radians(100.0)

    b.box((opening.u - half, -0.3, 0.0), (opening.u + half, WALL, FLOOR_TOP + 0.005), "trim", house.trim_tint, frame=frame)
    town.open_frame(b, opening, 0.18, -0.06, 0.0, house.trim_tint, town.TRIM_BLOCK_BAND, frame)

    for side_sign in (-1, 1):
        hinge_u = opening.u + side_sign * half
        tip = (hinge_u - side_sign * leaf * math.cos(swing), WALL + leaf * math.sin(swing))
        b.beam((hinge_u, WALL + 0.03, 0.02 + leaf_height / 2.0), (tip[0], tip[1], 0.02 + leaf_height / 2.0), leaf_height, 0.07, "paint", house.accent, frame=frame)

    house.doors.append({"x": round(opening.u - room.half, 3), "width": opening.width, "enterable": True})


def dress_vitrine(b: Builder, room: Room, frame: Matrix, opening: Opening) -> None:
    """Shop window: low sill wall, glass pane with glazing bars, moulded frame."""
    house = room.house
    half = opening.width / 2.0
    bar_count = max(1, round(opening.width / 0.9)) - 1
    bar_tint = srgb(WOOD["escura"])

    town.wall_piece(b, (opening.u - half, 0.0, 0.0), (opening.u + half, WALL, opening.bottom), house.wall_material, house.wall_tint, frame)
    b.prism(opening.outline(), 0.12, 0.14, "shopfront", frame=frame)
    b.collider((opening.u - half, 0.08, opening.bottom), (opening.u + half, 0.2, opening.apex), frame)
    town.open_frame(b, opening, 0.12, -0.05, 0.0, house.trim_tint, town.TRIM_SMOOTH_BAND, frame)
    b.box((opening.u - half - 0.1, -0.12, opening.bottom - 0.08), (opening.u + half + 0.1, WALL + 0.12, opening.bottom), "trim", house.trim_tint, frame=frame)
    b.box((opening.u - half, 0.1, opening.spring - 0.03), (opening.u + half, 0.16, opening.spring + 0.03), "paint", bar_tint, frame=frame)

    for bar_index in range(bar_count):
        bar_u = opening.u - half + opening.width * (bar_index + 1) / (bar_count + 1)
        b.box((bar_u - 0.025, 0.1, opening.bottom), (bar_u + 0.025, 0.16, opening.spring), "paint", bar_tint, frame=frame)


def dress_open_bay(b: Builder, room: Room, frame: Matrix, opening: Opening) -> None:
    """Open bay (forge yard): a timber lintel on the facade, nothing in the gap."""
    half = opening.width / 2.0

    b.box((opening.u - half - 0.2, -0.1, opening.apex - 0.05), (opening.u + half + 0.2, 0.0, opening.apex + 0.35), "wood", room.house.wood_tint, frame=frame, uv=("band", *WOOD_DARK_BAND, 1.5))


OPENING_DRESSING = {"door": dress_door, "vitrine": dress_vitrine, "open": dress_open_bay}


def pierced_wall(b: Builder, room: Room, frame: Matrix, length: float, openings: list) -> None:
    """Wall in its own frame: u from 0 to length seen from outside, outer face on d = 0, WALL thick toward +d."""
    house = room.house
    edges = sorted((opening.u - opening.width / 2.0, opening.u + opening.width / 2.0) for opening in openings)
    solid_from = [0.0] + [right for _, right in edges]
    solid_to = [left for left, _ in edges] + [length]

    for u_from, u_to in zip(solid_from, solid_to):
        if u_to - u_from > 1e-3:
            town.wall_piece(b, (u_from, 0.0, 0.0), (u_to, WALL, room.storey), house.wall_material, house.wall_tint, frame)

    for opening in openings:
        close_opening_top(b, room, frame, opening)
        OPENING_DRESSING[opening.kind](b, room, frame, opening)


def evenly(span_from: float, span_to: float, pitch: float) -> list:
    """(centre, room) of the openings that fit a wall span, one every pitch metres."""
    count = int((span_to - span_from) // pitch)

    return [(span_from + (span_to - span_from) * (index + 0.5) / count, (span_to - span_from) / count) for index in range(count)]


def front_openings(room: Room) -> list:
    """Door, open bays and as many shop windows as fit the free stretches of the facade (wall-local u = facade u + half)."""
    door_u, door_width, door_height, door_top = room.door
    vitrine_top = min(room.ceiling - 0.6, 3.4)
    bays = [(u, width, "open") for u, width in room.spec.get("open_bays", ())]
    taken = sorted([(door_u - door_width / 2.0, door_u + door_width / 2.0)] + [(u - width / 2.0, u + width / 2.0) for u, width, _ in bays])
    free_from = [-room.half] + [right for _, right in taken]
    free_to = [left for left, _ in taken] + [room.half]
    spots = [spot for span_from, span_to in zip(free_from, free_to) for spot in evenly(span_from + PIER, span_to - PIER, VITRINE_PITCH)]
    sill = room.spec.get("sill", VITRINE_SILL)
    vitrines = [Opening(u + room.half, space - 0.9, sill, vitrine_top - sill, room.spec.get("vitrine_top", "segment"), kind="vitrine") for u, space in spots]
    door = Opening(door_u + room.half, door_width, 0.0, door_height, door_top, kind="door")
    open_bays = [Opening(u + room.half, width, 0.0, min(room.ceiling - 0.5, 3.8), "flat", kind="open") for u, width, _ in bays]

    return [door] + open_bays + vitrines


def side_windows(room: Room, length: float, sill: float, height: float) -> list:
    return [Opening(u, 1.5, sill, height, "segment", kind="vitrine") for u, _ in evenly(1.0, length - 1.0, SIDE_WINDOW_PITCH)]


def flat_window(b: Builder, room: Room, frame: Matrix, opening: Opening) -> None:
    """Window painted on a solid wall (upper storeys of the exposed sides)."""
    b.prism(opening.outline(0.1), -0.05, 0.0, "trim", room.house.trim_tint, frame=frame, uv=("band", *town.TRIM_SMOOTH_BAND, 1.0))
    b.prism(opening.outline(), -0.07, -0.05, "glass", frame=frame)
    b.box((opening.u - 0.02, -0.085, opening.bottom), (opening.u + 0.02, -0.07, opening.spring), "paint", town.WHITE, frame=frame)


def dress_street_wall(b: Builder, room: Room, frame: Matrix, length: float, openings: list) -> None:
    """What makes a street wall read as a facade: stone plinth between the doors, a string course under the upper
    storey, and on tall halls a second tier of arched windows over the shop windows."""
    house = room.house
    gaps = sorted((opening.u - opening.width / 2.0 - 0.18, opening.u + opening.width / 2.0 + 0.18) for opening in openings if opening.kind != "vitrine")
    plinth_from = [0.0] + [right for _, right in gaps]
    plinth_to = [left for left, _ in gaps] + [length]
    vitrines = [opening for opening in openings if opening.kind == "vitrine"]
    tier_bottom = max((opening.apex for opening in vitrines), default=0.0) + 1.3
    tier_height = room.storey - 0.7 - tier_bottom

    for u_from, u_to in zip(plinth_from, plinth_to):
        b.box((u_from, -0.07, 0.0), (u_to, 0.0, PLINTH_HEIGHT), "trim", house.trim_tint, frame=frame, uv=("band", *town.TRIM_BLOCK_BAND, 1.0))

    if len(house.storeys) > 1:
        b.box((0.0, -0.1, room.storey - 0.22), (length, 0.0, room.storey), "trim", house.trim_tint, frame=frame, uv=("band", *town.TRIM_SMOOTH_BAND, 1.0))

    if tier_height < 1.2:
        return

    for opening in vitrines:
        flat_window(b, room, frame, Opening(opening.u, min(1.5, opening.width * 0.6), tier_bottom, tier_height, "round"))


def build_walls(b: Builder, room: Room) -> list:
    """Four walls of the ground storey; the sides that face a street get real windows. Returns the front openings."""
    side_length = room.depth - 2.0 * WALL
    frames = {
        "front": Matrix.Translation((-room.half, 0.0, 0.0)),
        "back": Matrix.Translation((room.half, room.depth, 0.0)) @ Matrix.Rotation(math.pi, 4, "Z"),
        "right": Matrix.Translation((room.half, WALL, 0.0)) @ Matrix.Rotation(math.pi / 2.0, 4, "Z"),
        "left": Matrix.Translation((-room.half, room.depth - WALL, 0.0)) @ Matrix.Rotation(-math.pi / 2.0, 4, "Z"),
    }
    front = front_openings(room)
    high_sill = room.ceiling - 1.9
    openings = {
        "front": front,
        "back": [Opening(u, 1.6, high_sill, 1.4, "segment", kind="vitrine") for u, _ in evenly(1.0, 2.0 * room.half - 1.0, 5.0)],
        "left": side_windows(room, side_length, 1.2, min(2.2, room.ceiling - 1.8)) if "left" in room.exposed else [],
        "right": side_windows(room, side_length, 1.2, min(2.2, room.ceiling - 1.8)) if "right" in room.exposed else [],
    }
    lengths = {"front": 2.0 * room.half, "back": 2.0 * room.half, "left": side_length, "right": side_length}

    for side, frame in frames.items():
        pierced_wall(b, room, frame, lengths[side], openings[side])

    for side in ("front", *room.exposed):
        dress_street_wall(b, room, frames[side], lengths[side], openings[side])

    for side, storey in itertools.product(room.exposed, range(1, len(room.house.storeys))):
        upper_frame = frames[side] @ Matrix.Translation((0.0, 0.0, room.house.levels[storey]))

        for u, _ in evenly(1.0, side_length - 1.0, SIDE_WINDOW_PITCH):
            flat_window(b, room, upper_frame, Opening(u, 1.1, 0.8, 1.7, "segment"))

    return front


# ---------- shell ----------

def build_floor(b: Builder, room: Room) -> None:
    """Planked or flagged floor flush with the pavement."""
    if room.spec["floor"] == "stone":
        b.box((room.left, room.front, 0.0), (room.right, room.back, FLOOR_TOP), "stone", srgb(STONE["dourada"]), uv=("world", 1.2))
        return

    board_count = round((room.right - room.left) / BOARD_WIDTH)
    board_width = (room.right - room.left) / board_count

    for board_index in range(board_count):
        board_left = room.left + board_index * board_width
        shade = 1.0 if board_index % 3 else 0.9
        b.box((board_left, room.front, 0.0), (board_left + board_width, room.back, FLOOR_TOP), "wood", tuple(shade * channel for channel in srgb(WOOD["mel"])), uv=("band", *WOOD_LIGHT_BAND, 2.0))

    b.collider((room.left, room.front, 0.0), (room.right, room.back, FLOOR_TOP), name="WoodFloor")  # passos com som de madeira


def build_ceiling(b: Builder, room: Room) -> None:
    """Board ceiling (its collider stops the camera arm), joists, and a girder over each row of posts."""
    house = room.house
    joist_count = int((room.back - room.front) / JOIST_SPACING)
    post_us = sorted({u for u, _ in room.posts})

    town.wall_piece(b, (room.left, room.front, room.ceiling), (room.right, room.back, room.storey), "wood", srgb(WOOD["mel"]))

    for joist_index in range(joist_count):
        d = room.front + (room.back - room.front) * (joist_index + 0.5) / joist_count
        b.box((room.left, d - 0.08, room.ceiling - 0.2), (room.right, d + 0.08, room.ceiling), "wood", house.wood_tint, uv=("band", *WOOD_DARK_BAND, 1.5))

    for u in post_us:
        b.box((u - 0.15, room.front, room.ceiling - 0.42), (u + 0.15, room.back, room.ceiling - 0.2), "wood", house.wood_tint, uv=("band", *WOOD_DARK_BAND, 1.5))

    for u, d in room.posts:
        town.wall_piece(b, (u - POST / 2.0, d - POST / 2.0, 0.0), (u + POST / 2.0, d + POST / 2.0, room.ceiling - 0.42), "wood", house.wood_tint)
        b.box((u - POST / 2.0 - 0.06, d - POST / 2.0 - 0.06, 0.0), (u + POST / 2.0 + 0.06, d + POST / 2.0 + 0.06, 0.35), "stone", srgb(STONE["media"]))

        for brace_sign in (-1, 1):
            b.beam((u, d + brace_sign * 0.1, room.ceiling - 1.4), (u, d + brace_sign * 1.0, room.ceiling - 0.42), 0.14, 0.14, "wood", house.wood_tint)


def partition_box(room: Room, partition: tuple) -> tuple:
    axis, fixed, span_from, span_to = partition
    boxes = {
        "u": ((fixed - WALL / 2.0, span_from, 0.0), (fixed + WALL / 2.0, span_to, room.ceiling)),
        "d": ((span_from, fixed - WALL / 2.0, 0.0), (span_to, fixed + WALL / 2.0, room.ceiling)),
    }

    return boxes[axis]


def build_awnings(b: Builder, room: Room, front: list) -> None:
    """Striped cloth awning over every shop window of the facade."""
    colors = [srgb(hex_value) for hex_value in room.spec["awning"] or ()]
    vitrines = [opening for opening in front if opening.kind == "vitrine" and colors]

    for opening in vitrines:
        left = opening.u - room.half - opening.width / 2.0 - 0.25
        stripe_count = max(2, round((opening.width + 0.5) / AWNING_STRIPE))
        stripe_width = (opening.width + 0.5) / stripe_count
        top = opening.apex + 0.45
        slab = [(0.0, top), (-AWNING_REACH, top - 0.6), (-AWNING_REACH, top - 0.55), (0.0, top + 0.05)]
        valance = [(-AWNING_REACH, top - 0.58), (-AWNING_REACH, top - 0.85), (-AWNING_REACH + 0.03, top - 0.85), (-AWNING_REACH + 0.03, top - 0.58)]

        for stripe_index in range(stripe_count):
            stripe_left = left + stripe_index * stripe_width
            b.side_prism(slab, stripe_left, stripe_left + stripe_width, "paint", colors[stripe_index % 2])
            b.side_prism(valance, stripe_left, stripe_left + stripe_width, "paint", colors[(stripe_index + 1) % 2])

        for arm_u in (left + 0.05, left + opening.width + 0.45):
            b.beam((arm_u, 0.0, top - 0.75), (arm_u, -AWNING_REACH, top - 0.6), 0.04, 0.04, "metal", room.house.iron_tint)


def build_roof(b: Builder, room: Room) -> None:
    """Upper storeys, roof and signature details of the archetype the shop is dressed after."""
    spec = dict(town.ARCHETYPE_SPECS[room.spec["archetype"]])
    house = room.house

    spec.update(storeys=room.spec["storeys"], roof=room.spec["roof_shape"], features=room.spec.get("features", ()), chimney=room.spec.get("chimney"), loggia_top=False, quoins=room.spec.get("quoins", False), cornice=room.spec.get("cornice", False))
    town.build_house(b, house, spec, ground="shop")

    if room.spec["roof_shape"][0] != "gable_parallel":
        return

    options = room.spec["roof_shape"][1]
    eave_front, eave_back = -options["eave_front"], house.depth + options["eave_back"]
    rise = (eave_back - eave_front) / 2.0 * math.tan(math.radians(options["pitch"]))
    gable = [(eave_front + 0.3, house.top - 0.12), (eave_back - 0.3, house.top - 0.12), ((eave_front + eave_back) / 2.0, house.top - 0.12 + rise - 0.3 * rise / ((eave_back - eave_front) / 2.0))]

    for side in room.exposed:
        side_sign = {"left": -1.0, "right": 1.0}[side]
        b.side_prism(gable, side_sign * house.limit, side_sign * (house.limit + 0.01), house.wall_material, house.wall_tint)


def build_shell(shop_type: str) -> dict:
    room = Room(shop_type)
    b = Builder(f"shop_{shop_type}")
    house = room.house
    light_columns = max(2, round(2.0 * room.half / LIGHT_SPACING))
    light_us = [room.left + (room.right - room.left) * (index + 0.5) / light_columns for index in range(light_columns)]

    front = build_walls(b, room)
    build_floor(b, room)
    build_ceiling(b, room)
    build_awnings(b, room, front)
    build_roof(b, room)

    for partition in room.partitions:
        town.wall_piece(b, *partition_box(room, partition), house.wall_material, house.wall_tint)

    for u, row in itertools.product(light_us, LIGHT_ROWS):
        b.light((u, room.front + (room.back - room.front) * row, room.ceiling - 0.9), room.spec["light"], 1.3, 10.0)

    b.marker("shopkeeper", (*room.keeper, 0.0))

    return b.finish(town.SHOP_DIR / f"shop_{shop_type}.gltf", {"lot_width": SHOP_LOTS[shop_type][0], "lot_depth": SHOP_LOTS[shop_type][1], "shop": shop_type, "doors": house.doors})


# ---------- furniture ----------

class Furnisher:
    """Places props of the libraries in a room and keeps their footprints to report overlaps."""

    def __init__(self, b: Builder, room: Room) -> None:
        door_u, door_width, _, _ = room.door

        self.b = b
        self.room = room
        self.left, self.right, self.front, self.back, self.ceiling = room.left, room.right, room.front, room.back, room.ceiling
        self.door_u = door_u
        self.keeper = room.keeper
        self.placed = 0
        self.missing = set()
        self.lights = []
        self.footprints = [("porta", (door_u - door_width / 2.0 - 0.2, door_u + door_width / 2.0 + 0.2, room.front, room.front + DOOR_CLEARANCE)), ("lojista", (self.keeper[0] - 0.35, self.keeper[0] + 0.35, self.keeper[1] - 0.35, self.keeper[1] + 0.35))]
        self.footprints += [("pilar", (u - POST / 2.0, u + POST / 2.0, d - POST / 2.0, d + POST / 2.0)) for u, d in room.posts]
        self.footprints += [("parede", (box[0][0], box[1][0], box[0][1], box[1][1])) for box in (partition_box(room, partition) for partition in room.partitions)]

    def put(self, name: str, u: float, d: float, degrees: float = 0.0, z: float = None, **options) -> None:
        """One prop with its local origin at (u, d); degrees turns its front (-Y) counter-clockwise seen from above.
        Hanging props go to the ceiling unless z is given."""
        entry = PROPS.get(name)

        if entry is None:
            self.missing.add(name)
            return

        width, depth, height = entry["size"]
        height_origin = (self.ceiling if entry.get("hang") else FLOOR_TOP) if z is None else z
        frame = Matrix.Translation((u, d, height_origin)) @ Matrix.Rotation(math.radians(degrees), 4, "Z")
        cos_turn, sin_turn = abs(math.cos(math.radians(degrees))), abs(math.sin(math.radians(degrees)))
        half_u, half_d = (width * cos_turn + depth * sin_turn) / 2.0, (width * sin_turn + depth * cos_turn) / 2.0

        entry["build"](self.b, frame, **options)
        self.placed += 1

        if entry.get("solid"):
            self.b.collider((-width / 2.0, -depth / 2.0, 0.0), (width / 2.0, depth / 2.0, min(height, COLLIDER_MAX_HEIGHT)), frame)
            self.footprints.append((name, (u - half_u, u + half_u, d - half_d, d + half_d)))

        if entry.get("light"):
            position, color, energy, light_range = entry["light"]
            self.lights.append((frame, position, color, energy, light_range))

    def wall(self, side: str, items: list, start: float = None, gap: float = 0.25) -> None:
        """Props in a row with their backs to a wall, from start along it (u for back/front, d for left/right).
        items: prop name, (name, options) or a number of metres to skip."""
        cursor = start if start is not None else {"back": self.left, "front": self.left, "left": self.front, "right": self.front}[side] + 0.4

        for item in items:
            if isinstance(item, (int, float)):
                cursor += item
                continue

            name, options = (item, {}) if isinstance(item, str) else item
            width = PROPS.get(name, {"size": (1.0, 0.5, 1.0)})["size"][0]

            self.on_wall(side, name, cursor + width / 2.0, **options)
            cursor += width + gap

    def on_wall(self, side: str, name: str, along: float, z: float = None, **options) -> None:
        """One prop with its back to a wall, centred at along (u for back/front, d for left/right)."""
        turns = {"back": 0.0, "front": 180.0, "left": 90.0, "right": -90.0}
        across = PROPS.get(name, {"size": (1.0, 0.5, 1.0)})["size"][1] / 2.0 + 0.03
        spots = {"back": (along, self.back - across), "front": (along, self.front + across), "left": (self.left + across, along), "right": (self.right - across, along)}

        self.put(name, *spots[side], turns[side], z, **options)

    def is_free(self, name: str, u: float, d: float, degrees: float, aisle: float) -> bool:
        """True when the prop would stand inside the hall with an aisle to everything already placed."""
        width, depth, _ = PROPS.get(name, {"size": (1.0, 1.0, 1.0)})["size"]
        cos_turn, sin_turn = abs(math.cos(math.radians(degrees))), abs(math.sin(math.radians(degrees)))
        half_u, half_d = (width * cos_turn + depth * sin_turn) / 2.0 + aisle, (width * sin_turn + depth * cos_turn) / 2.0 + aisle
        inside = self.left < u - half_u and u + half_u < self.right and self.front < d - half_d and d + half_d < self.back

        return inside and not any(u - half_u < taken[1] and taken[0] < u + half_u and d - half_d < taken[3] and taken[2] < d + half_d for _, taken in self.footprints)

    def scatter(self, items: list, u_range: tuple, d_range: tuple, columns: int, rows: int, aisle: float = ISLAND_AISLE) -> None:
        """Islands for the open floor: walks a columns x rows grid and stands the next item of the cycle on every
        cell that is still free (aisle kept to walls, posts, the door lane and earlier props).
        items: prop name or (name, degrees, options)."""
        cycle = itertools.cycle(items)

        for row, column in itertools.product(range(rows), range(columns)):
            u = u_range[0] + (u_range[1] - u_range[0]) * column / max(1, columns - 1)
            d = d_range[0] + (d_range[1] - d_range[0]) * row / max(1, rows - 1)
            name, degrees, options = next(cycle)

            if self.is_free(name, u, d, degrees, aisle):
                self.put(name, u, d, degrees, **options)

    def grid(self, name: str, u_range: tuple, d_range: tuple, columns: int, rows: int, degrees: float = 0.0, **options) -> None:
        """columns x rows copies spread over a rectangle (ranges are the centres of the outer ones)."""
        for column, row in itertools.product(range(columns), range(rows)):
            u = u_range[0] + (u_range[1] - u_range[0]) * column / max(1, columns - 1)
            d = d_range[0] + (d_range[1] - d_range[0]) * row / max(1, rows - 1)
            self.put(name, u, d, degrees, **options)

    def report(self) -> None:
        """Print solid props that overlap each other, a post, a partition, the door lane, or leave the room."""
        pairs = itertools.combinations(self.footprints, 2)
        overlapping = [(first[0], second[0], tuple(round(value, 1) for value in second[1])) for first, second in pairs if first[1][0] < second[1][1] - 0.02 and second[1][0] < first[1][1] - 0.02 and first[1][2] < second[1][3] - 0.02 and second[1][2] < first[1][3] - 0.02]
        outside = [name for name, (u_from, u_to, d_from, d_to) in self.footprints if u_from < self.left - 0.02 or u_to > self.right + 0.02 or d_from < self.front - 0.02 or d_to > self.back + 0.02]

        for first, second, where in overlapping:
            print(f"AVISO {self.room.shop_type}: {first} x {second} em {where}")

        for name in outside:
            print(f"AVISO {self.room.shop_type}: {name} fora do salão")

        if self.missing:
            print(f"AVISO {self.room.shop_type}: props ainda não modelados: {sorted(self.missing)}")


def fill_floor(furnisher: Furnisher, items: list) -> None:
    """Loose islands of goods on whatever floor the plan left free, on both sides of the lane from the door."""
    if not items:
        return

    d_range = (furnisher.front + 2.2, furnisher.back - FILL_BACK)
    rows = round((d_range[1] - d_range[0]) / FILL_PITCH) + 1

    for u_range in ((furnisher.left + 1.2, furnisher.door_u - FILL_LANE), (furnisher.door_u + FILL_LANE, furnisher.right - 1.2)):
        columns = max(1, round((u_range[1] - u_range[0]) / FILL_PITCH) + 1)
        furnisher.scatter(items, u_range, d_range, columns, rows, aisle=FILL_AISLE)


def build_interior(shop_type: str) -> dict:
    """Furniture model of one shop; nothing is written while its plan or its props do not exist yet."""
    room = Room(shop_type)
    b = Builder(f"shop_{shop_type}_interior")
    furnisher = Furnisher(b, room)
    output_path = town.SHOP_DIR / f"shop_{shop_type}_interior.gltf"
    feature_light_limit = 3

    room.plan.get("furnish", shop_layouts.furnish_generic)(furnisher)
    fill_floor(furnisher, shop_layouts.FILL.get(shop_type, []))
    furnisher.report()

    if furnisher.placed == 0:
        return {}

    for frame, position, color, energy, light_range in furnisher.lights[:feature_light_limit]:
        b.light(position, color, energy, light_range, frame)

    return b.finish(output_path, {"shop": shop_type, "props": furnisher.placed})


if __name__ == "__main__":
    requested = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    only_interiors = "--interiors" in requested
    shop_types = [name for name in requested if not name.startswith("--")] or sorted(SHOPS)

    for shop_type in shop_types:
        sidecar = {} if only_interiors else build_shell(shop_type)
        interior = build_interior(shop_type)
        print(f"BUILT shop_{shop_type}: aabb {sidecar.get('aabb_min')} .. {sidecar.get('aabb_max')}, interior props {interior.get('props', 0)}")
