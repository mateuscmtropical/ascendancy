"""Props of the general store and bakery (general_layout.py): the grocer's wall of drawers and shelves, the shop
counter, the coffee mill, the baker's slanted bread shelves, the bakehouse oven, the kneading trough and the peel
rack.

Prop contract of shop_props_common: origin at the middle of the footprint on the floor, front toward -Y, back toward
+Y (the wall side), z up. Runs inside Blender, imported by build_market_shops.py.
"""

import random
import sys
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import BRICK, STONE, Builder, srgb  # noqa: E402
from shop_props_alchemy import balance_scale, drawer_bank  # noqa: E402
from shop_props_arcane import BRASS, DARK_IRON, PARCHMENT, ball, box, cyl, rod, spin  # noqa: E402
from shop_props_food import LIGHT_FIRE, SOOT, WALNUT, fire  # noqa: E402

GROCER_WOOD = "8B5A3C"
DRAWER_FRONT = "C08A55"
TIN_COLOURS = ("C9483B", "2F5FA8", "E8B64A", "3F8A50", "F2E6CF", "6A2E6E", "D9A441")
PACKET_COLOURS = ("E0884A", "F2E6CF", "4F8FC9", "C9483B", "8FAE5A")
LOAF = ("C98B52", "B0703A", "D9A46A", "8E5A2E")
MILL_RED = "B5333F"
GROCER_SHELVES = (1.45, 1.95, 2.45, 2.95)
GROCER_TOP = 3.35


def goods_row(b: Builder, frame: Matrix, z: float, generator: random.Random) -> None:
    """One shelf of tins, packets and jars across a 1.4 m bay."""
    xs = [-0.6 + 0.2 * index for index in range(7)]

    for x in xs:
        kind = generator.random()

        if kind < 0.45:
            cyl(b, frame, (x, 0.05, z), 0.07, generator.uniform(0.16, 0.26), "paint", generator.choice(TIN_COLOURS), sides=6)
        elif kind < 0.8:
            box(b, frame, (x - 0.08, -0.04, z), (x + 0.08, 0.14, z + generator.uniform(0.2, 0.32)), "paint", generator.choice(PACKET_COLOURS))
        else:
            cyl(b, frame, (x, 0.05, z), 0.08, 0.24, "paint", "C9D3E8", sides=6)
            cyl(b, frame, (x, 0.05, z + 0.24), 0.05, 0.03, "wood_light", WALNUT, sides=6)


def grocer_wall(b: Builder, frame: Matrix, **options) -> None:
    """One bay of the grocer's wall: a bank of labelled spice and coffee drawers under a ledge, four shelves of tins,
    packets and jars between uprights, a cornice with a name board."""
    generator = random.Random(options.get("seed", 3))

    box(b, frame, (-0.75, -0.27, 0.0), (0.75, 0.3, 0.1), "wood", SOOT)
    box(b, frame, (-0.75, -0.25, 0.1), (0.75, 0.3, 1.0), "wood_light", GROCER_WOOD)
    drawer_bank(b, frame, 1.42, 0.84, 5, 4, -0.25, DRAWER_FRONT, 0.13)
    box(b, frame, (-0.77, -0.3, 1.0), (0.77, 0.3, 1.05), "wood_light", WALNUT)
    box(b, frame, (-0.75, 0.22, 1.05), (0.75, 0.3, GROCER_TOP), "wood_light", GROCER_WOOD)

    for side_x in (-0.75, 0.69):
        box(b, frame, (side_x, -0.12, 1.05), (side_x + 0.06, 0.3, GROCER_TOP), "wood_light", GROCER_WOOD)

    for shelf_z in GROCER_SHELVES:
        box(b, frame, (-0.69, -0.12, shelf_z - 0.03), (0.69, 0.22, shelf_z), "wood_light", GROCER_WOOD)

    for row_z in (1.05, *GROCER_SHELVES):
        goods_row(b, frame, row_z, generator)

    box(b, frame, (-0.78, -0.18, GROCER_TOP), (0.78, 0.3, GROCER_TOP + 0.08), "wood", WALNUT)
    box(b, frame, (-0.6, -0.2, GROCER_TOP - 0.32), (0.6, -0.12, GROCER_TOP - 0.06), "paint", "2F4A3F")
    box(b, frame, (-0.5, -0.21, GROCER_TOP - 0.24), (0.5, -0.2, GROCER_TOP - 0.14), "metal", "E8B64A")


def shop_counter(b: Builder, frame: Matrix, **options) -> None:
    """Long panelled shop counter: the balance, a paper roll and twine, sweet jars, a cash box; drawers behind."""
    generator = random.Random(options.get("seed", 9))
    goods = options.get("variant", "grocer")

    box(b, frame, (-1.5, -0.38, 0.0), (1.5, 0.38, 0.1), "wood", SOOT)
    box(b, frame, (-1.48, -0.36, 0.1), (1.48, 0.38, 0.95), "wood_light", GROCER_WOOD)

    for panel_x in (-1.0, 0.0, 1.0):
        box(b, frame, (panel_x - 0.42, -0.39, 0.22), (panel_x + 0.42, -0.36, 0.82), "wood_light", WALNUT)

    drawer_bank(b, frame, 2.8, 0.3, 6, 1, 0.39, DRAWER_FRONT, 0.6)
    box(b, frame, (-1.55, -0.44, 0.95), (1.55, 0.44, 1.0), "wood_light", WALNUT)

    if goods == "bakery":
        bread_baskets(b, frame, generator)
        return

    balance_scale(b, frame, -1.0, 0.0, 1.0)
    cyl(b, frame, (0.2, 0.25, 1.0), 0.03, 0.4, "metal", DARK_IRON, sides=6)
    cyl(b, frame, (0.2, 0.25, 1.2), 0.09, 0.32, "paint", PARCHMENT, sides=8, axis="X")
    box(b, frame, (0.85, 0.05, 1.0), (1.3, 0.35, 1.2), "wood", SOOT)

    for jar_x in (-0.45, -0.2, 0.5):
        spin(b, frame, [(0.07, 0.0), (0.1, 0.05), (0.1, 0.24), (0.06, 0.3), (0.08, 0.33)], "vitrine", sides=8, base=(jar_x, -0.2, 1.0))
        cyl(b, frame, (jar_x, -0.2, 1.01), 0.085, 0.14, "paint", generator.choice(TIN_COLOURS), sides=8)


def bread_baskets(b: Builder, frame: Matrix, generator: random.Random) -> None:
    for basket_x in (-1.1, -0.35, 0.4):
        cyl(b, frame, (basket_x, 0.0, 1.0), 0.28, 0.12, "wood_light", "D9B57A", sides=8, top=0.32)

        for loaf in range(3):
            ball(b, frame, (basket_x + 0.13 * (loaf - 1), 0.0, 1.14), 0.1, "paint", generator.choice(LOAF), scale=(1.4, 0.8, 0.6), segments=6)

    box(b, frame, (0.85, 0.05, 1.0), (1.3, 0.35, 1.2), "wood", SOOT)


def coffee_mill(b: Builder, frame: Matrix, **options) -> None:
    """Standing coffee mill with two big red flywheels, a brass hopper and a drawer, on a box stand."""
    box(b, frame, (-0.3, -0.22, 0.0), (0.3, 0.22, 0.75), "wood_light", WALNUT)
    box(b, frame, (-0.2, -0.16, 0.75), (0.2, 0.16, 1.1), "paint", MILL_RED)
    spin(b, frame, [(0.06, 1.1), (0.16, 1.3), (0.18, 1.34)], "metal", BRASS, sides=8)

    for wheel_x in (-0.25, 0.25):
        cyl(b, frame, (wheel_x, 0.0, 1.0), 0.32, 0.04, "paint", MILL_RED, sides=12, axis="X")
        cyl(b, frame, (wheel_x + (0.03 if wheel_x > 0 else -0.03), 0.0, 1.0), 0.06, 0.04, "metal", BRASS, sides=8, axis="X")

    rod(b, frame, (0.3, 0.0, 1.2), (0.3, -0.12, 1.36), 0.03, "wood_light", "D9B57A")


def bread_wall(b: Builder, frame: Matrix, **options) -> None:
    """Baker's bread wall: slanted shelves of loaves over a cupboard, rolls in a row of baskets on top."""
    generator = random.Random(options.get("seed", 4))
    rows = (0.95, 1.35, 1.75)

    box(b, frame, (-1.0, -0.2, 0.0), (1.0, 0.25, 0.9), "wood_light", "C08A55")
    box(b, frame, (-1.0, 0.18, 0.9), (1.0, 0.25, 2.25), "wood_light", "C08A55")

    for side_x in (-1.0, 0.95):
        box(b, frame, (side_x, -0.2, 0.9), (side_x + 0.05, 0.25, 2.25), "wood_light", WALNUT)

    for row_z in rows:
        b.side_prism([(-0.2, row_z), (0.18, row_z + 0.16), (0.18, row_z + 0.19), (-0.2, row_z + 0.03)], -0.95, 0.95, "wood", srgb("9A6A42"), frame=frame)
        loaves = [-0.8 + 0.27 * index for index in range(7)]

        for loaf_x in loaves:
            ball(b, frame, (loaf_x, 0.0, row_z + 0.14), 0.12, "paint", generator.choice(LOAF), scale=(1.0, 1.5, 0.6), segments=6)

    box(b, frame, (-1.02, -0.22, 2.25), (1.02, 0.27, 2.32), "wood", WALNUT)


def bakehouse_oven(b: Builder, frame: Matrix, **options) -> None:
    """Brick bakehouse oven: a deep masonry block with two cast-iron doors over an ash door, the fire glowing in
    the upper one, an iron rail and the flue breast up to the ceiling."""
    brick = BRICK["vermelho"]
    height = options.get("height", 3.95)

    box(b, frame, (-1.7, -0.9, 0.0), (1.7, 0.95, 1.95), "brick", brick)
    box(b, frame, (-1.3, -0.4, 1.95), (1.3, 0.95, height), "brick", brick)
    box(b, frame, (-1.75, -0.95, 1.95), (1.75, 0.95, 2.05), "stone", STONE["media"])

    for door_x, glow in ((-0.65, True), (0.65, False)):
        box(b, frame, (door_x - 0.42, -0.95, 0.9), (door_x + 0.42, -0.9, 1.5), "metal", DARK_IRON)
        box(b, frame, (door_x - 0.3, -0.97, 1.05), (door_x + 0.3, -0.95, 1.38), "glow_ember" if glow else "metal", None if glow else "2B2236")
        box(b, frame, (door_x - 0.25, -0.95, 0.35), (door_x + 0.25, -0.9, 0.65), "metal", DARK_IRON)

    rod(b, frame, (-1.6, -1.0, 1.7), (1.6, -1.0, 1.7), 0.03, "metal", BRASS)
    fire(b, frame, -0.65, -0.7, 0.92, 0.5, 12)


def kneading_trough(b: Builder, frame: Matrix, **options) -> None:
    """Kneading trough on splayed legs, a lump of dough and the scraper, the lid leant against it."""
    box(b, frame, (-0.95, -0.32, 0.6), (0.95, 0.32, 0.95), "wood_light", "C08A55")
    box(b, frame, (-0.88, -0.26, 0.9), (0.88, 0.26, 0.96), "paint", "F2E6CF")
    ball(b, frame, (-0.3, 0.0, 0.96), 0.22, "paint", "F4E4C0", scale=(1.6, 1.0, 0.45), segments=8)

    for leg_x, leg_y in ((-0.8, -0.25), (0.8, -0.25), (-0.8, 0.25), (0.8, 0.25)):
        rod(b, frame, (leg_x * 1.08, leg_y * 1.3, 0.0), (leg_x, leg_y, 0.6), 0.07, "wood_light", WALNUT)

    box(b, frame, (0.4, -0.05, 0.96), (0.55, 0.05, 0.98), "metal", "C9D3E8")


def peel_rack(b: Builder, frame: Matrix, **options) -> None:
    """Wall rack of long-handled oven peels and a rake."""
    rod(b, frame, (-0.6, 0.0, 2.2), (0.6, 0.0, 2.2), 0.06, "wood_light", WALNUT)

    for peel_x in (-0.45, -0.15, 0.15, 0.45):
        rod(b, frame, (peel_x, -0.04, 0.2), (peel_x, -0.04, 2.3), 0.035, "wood_light", "D9B57A")
        box(b, frame, (peel_x - 0.12, -0.06, 0.02), (peel_x + 0.12, -0.03, 0.3), "wood_light", "D9B57A")


PROPS = {
    "grocer_wall": {"build": grocer_wall, "size": (1.56, 0.6, 3.45), "solid": True, "clearance": 0.35},
    "shop_counter": {"build": shop_counter, "size": (3.1, 0.88, 1.45), "solid": True},
    "coffee_mill": {"build": coffee_mill, "size": (0.7, 0.5, 1.4), "solid": True},
    "bread_wall": {"build": bread_wall, "size": (2.04, 0.5, 2.32), "solid": True, "clearance": 0.8},
    "bakehouse_oven": {"build": bakehouse_oven, "size": (3.5, 1.95, 3.95), "solid": True, "light": ((-0.65, -1.2, 1.2), LIGHT_FIRE, 2.0, 6.0), "clearance": 1.5},
    "kneading_trough": {"build": kneading_trough, "size": (2.1, 0.85, 0.98), "solid": True},
    "peel_rack": {"build": peel_rack, "size": (1.3, 0.15, 2.35), "solid": False},
}
