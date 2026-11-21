"""Props of the apothecary-alchemist (alchemy_layout.py): the Repositorium bays of the Offizin, the dispensing
counter, show globes, the herb drawer cabinet and drying poles, the stamping mortar, the laboratory hearth under its
hood, the copper still and the poison cabinet.

Prop contract of shop_props_common: origin at the middle of the footprint on the floor, front toward -Y, back toward
+Y (the wall side), z up; hanging props grow down from the ceiling mount. Runs inside Blender, imported by
build_market_shops.py.
"""

import math
import random
import sys
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import BRICK, STONE, Builder, srgb  # noqa: E402
from shop_props_arcane import BONE, BRASS, COPPER, DARK_IRON, PARCHMENT, ball, box, cyl, gem, rod, spin  # noqa: E402
from shop_props_food import LIGHT_FIRE, SOOT, WALNUT, fire  # noqa: E402

CABINET_SAGE = "8FA593"  # painted Repositorium, sage green-grey with gilt crowns (museum Offizin)
CABINET_PANEL = "B7C7B0"
GILT = "E8B64A"
FAIENCE = "F4EFE6"
FAIENCE_BLUE = "2F5FA8"
JAR_GLASS = ("8E5A2E", "3F6B55", "C9D3E8", "6A2E6E")
HERB_GREENS = ("6E8A4A", "8FA060", "A08A5A", "7E6A8A", "5E7A44")
DRAWER_PULL = "C9A46A"
GLOBE_LIQUIDS = {"red": "C9304A", "green": "2F9A5A", "blue": "2F5FC9", "amber": "E0952F"}
REPOSITORIUM_SHELVES = (1.45, 1.9, 2.35)  # shelf tops over the drawer bank
REPOSITORIUM_TOP = 2.75


def drawer_bank(b: Builder, frame: Matrix, width: float, height: float, columns: int, rows: int, face_y: float, tint: str, z_from: float = 0.0) -> None:
    """Grid of small drawer fronts with a pull each over a flat cabinet front at face_y (one loop over a flat index)."""
    drawer_width, drawer_height = width / columns, height / rows

    for index in range(columns * rows):
        column, row = index % columns, index // columns
        left = -width / 2.0 + column * drawer_width
        bottom = z_from + row * drawer_height
        box(b, frame, (left + 0.02, face_y - 0.015, bottom + 0.02), (left + drawer_width - 0.02, face_y, bottom + drawer_height - 0.02), "paint", tint)
        box(b, frame, (left + drawer_width / 2.0 - 0.025, face_y - 0.035, bottom + drawer_height / 2.0 - 0.012), (left + drawer_width / 2.0 + 0.025, face_y - 0.015, bottom + drawer_height / 2.0 + 0.012), "metal", DRAWER_PULL)


def apothecary_jar(b: Builder, frame: Matrix, x: float, y: float, z: float, height: float, generator: random.Random) -> None:
    """White faience albarello with a blue band, or a glass jar of dried goods with a stopper."""
    radius = height * 0.33

    if generator.random() < 0.6:
        spin(b, frame, [(radius * 0.85, 0.0), (radius, height * 0.15), (radius * 0.82, height * 0.5), (radius, height * 0.85), (radius * 0.6, height)], "paint", FAIENCE, sides=6, base=(x, y, z))
        cyl(b, frame, (x, y, z + height * 0.42), radius * 0.86, height * 0.18, "paint", FAIENCE_BLUE, sides=6)
        return

    cyl(b, frame, (x, y, z), radius, height * 0.8, "paint", generator.choice(JAR_GLASS), sides=6)
    cyl(b, frame, (x, y, z + height * 0.8), radius * 0.5, height * 0.2, "wood_light", WALNUT, sides=6)


def repositorium(b: Builder, frame: Matrix, **options) -> None:
    """One bay of the built-in Offizin cabinet: a drawer bank under a counter ledge, three shelves of faience and glass
    jars between pilasters, and a moulded crown with a gilt cartouche."""
    tint = options.get("tint", CABINET_SAGE)
    generator = random.Random(options.get("seed", 7))
    jar_xs = (-0.52, -0.18, 0.18, 0.52)

    box(b, frame, (-0.8, -0.3, 0.0), (0.8, 0.3, 0.1), "wood", SOOT)
    box(b, frame, (-0.8, -0.28, 0.1), (0.8, 0.3, 0.95), "paint", tint)
    drawer_bank(b, frame, 1.5, 0.8, 4, 4, -0.28, CABINET_PANEL, 0.12)
    box(b, frame, (-0.82, -0.34, 0.95), (0.82, 0.32, 1.0), "wood_light", WALNUT)
    box(b, frame, (-0.8, 0.2, 1.0), (0.8, 0.3, REPOSITORIUM_TOP), "paint", tint)

    for side_x in (-0.8, 0.72):
        box(b, frame, (side_x, -0.12, 1.0), (side_x + 0.08, 0.3, REPOSITORIUM_TOP), "paint", tint)
        box(b, frame, (side_x + 0.015, -0.14, 1.6), (side_x + 0.065, -0.12, 2.5), "metal", GILT)

    for shelf_z in REPOSITORIUM_SHELVES:
        box(b, frame, (-0.72, -0.1, shelf_z - 0.03), (0.72, 0.2, shelf_z), "paint", tint)

    for row_z in (1.0, *REPOSITORIUM_SHELVES):
        for jar_x in jar_xs:
            apothecary_jar(b, frame, jar_x, 0.05, row_z, generator.uniform(0.28, 0.36), generator)

    box(b, frame, (-0.84, -0.18, REPOSITORIUM_TOP), (0.84, 0.32, REPOSITORIUM_TOP + 0.08), "paint", tint)
    box(b, frame, (-0.86, -0.22, REPOSITORIUM_TOP + 0.08), (0.86, 0.32, REPOSITORIUM_TOP + 0.13), "metal", GILT)
    ball(b, frame, (0.0, -0.16, REPOSITORIUM_TOP + 0.26), 0.16, "metal", GILT, scale=(1.0, 0.25, 0.8))
    ball(b, frame, (0.0, -0.2, REPOSITORIUM_TOP + 0.26), 0.11, "paint", tint, scale=(1.0, 0.2, 0.75))


def balance_scale(b: Builder, frame: Matrix, x: float, y: float, z: float) -> None:
    """Brass apothecary balance: a column on a foot, the beam and two hanging pans."""
    cyl(b, frame, (x, y, z), 0.09, 0.03, "metal", BRASS, sides=8)
    rod(b, frame, (x, y, z + 0.03), (x, y, z + 0.45), 0.02, "metal", BRASS)
    rod(b, frame, (x - 0.22, y, z + 0.44), (x + 0.22, y, z + 0.44), 0.015, "metal", BRASS)

    for pan_x in (x - 0.2, x + 0.2):
        rod(b, frame, (pan_x, y, z + 0.44), (pan_x, y, z + 0.2), 0.006, "metal", BRASS)
        cyl(b, frame, (pan_x, y, z + 0.18), 0.08, 0.02, "metal", BRASS, sides=8, top=0.09)


def rezeptur(b: Builder, frame: Matrix, **options) -> None:
    """Dispensing counter (Rezeptur) in the middle of the Offizin: raised panels toward the customers, a wall of
    drawers on the apothecary's side, a walnut top with the balance, a brass mortar, sample jars and the ledger."""
    tint = options.get("tint", CABINET_SAGE)
    generator = random.Random(options.get("seed", 11))

    box(b, frame, (-1.6, -0.42, 0.0), (1.6, 0.42, 0.1), "wood", SOOT)
    box(b, frame, (-1.58, -0.4, 0.1), (1.58, 0.4, 0.95), "paint", tint)

    for panel_x in (-1.05, 0.0, 1.05):
        box(b, frame, (panel_x - 0.42, -0.43, 0.22), (panel_x + 0.42, -0.4, 0.82), "paint", CABINET_PANEL)
        box(b, frame, (panel_x - 0.1, -0.45, 0.44), (panel_x + 0.1, -0.43, 0.6), "metal", GILT)

    drawer_bank(b, frame, 3.0, 0.72, 8, 3, 0.43, CABINET_PANEL, 0.14)
    box(b, frame, (-1.66, -0.48, 0.95), (1.66, 0.48, 1.01), "wood_light", WALNUT)
    balance_scale(b, frame, 0.85, 0.05, 1.01)
    spin(b, frame, [(0.08, 0.0), (0.12, 0.04), (0.13, 0.16), (0.11, 0.18)], "metal", BRASS, sides=8, base=(-0.9, 0.0, 1.01))
    rod(b, frame, (-0.9, 0.0, 1.1), (-0.82, 0.07, 1.33), 0.03, "metal", BRASS)
    box(b, frame, (-0.35, 0.05, 1.01), (0.15, 0.4, 1.05), "paint", PARCHMENT)
    box(b, frame, (-0.35, 0.05, 1.05), (-0.1, 0.4, 1.07), "paint", PARCHMENT)

    for jar_x in (-1.45, -1.25, 1.3, 1.5):
        apothecary_jar(b, frame, jar_x, -0.15, 1.01, generator.uniform(0.2, 0.26), generator)


def show_globe(b: Builder, frame: Matrix, **options) -> None:
    """Show globe of the apothecary's window: a pear-shaped glass carboy of coloured liquid on a wrought-iron tripod."""
    liquid = GLOBE_LIQUIDS.get(options.get("variant"), GLOBE_LIQUIDS["green"])

    for angle in (90.0, 210.0, 330.0):
        foot = (0.22 * math.cos(math.radians(angle)), 0.22 * math.sin(math.radians(angle)), 0.0)
        rod(b, frame, foot, (foot[0] * 0.4, foot[1] * 0.4, 0.95), 0.025, "metal", DARK_IRON)

    cyl(b, frame, (0.0, 0.0, 0.92), 0.14, 0.04, "metal", DARK_IRON, sides=8)
    ball(b, frame, (0.0, 0.0, 1.22), 0.2, "paint", liquid, scale=(1.0, 1.0, 1.15), segments=8)
    spin(b, frame, [(0.05, 0.96), (0.23, 1.15), (0.22, 1.36), (0.07, 1.52), (0.04, 1.62), (0.06, 1.66)], "vitrine", sides=8)
    gem(b, frame, (0.0, 0.0, 1.7), 0.04, "metal", BRASS, scale=(1.0, 1.0, 1.6))


def herb_cabinet(b: Builder, frame: Matrix, **options) -> None:
    """Herb room drawer cabinet: six columns of labelled oak drawers on a plinth, a cornice, baskets on top."""
    box(b, frame, (-1.0, -0.25, 0.0), (1.0, 0.27, 0.12), "wood", SOOT)
    box(b, frame, (-1.0, -0.22, 0.12), (1.0, 0.27, 2.1), "wood_light", WALNUT)
    drawer_bank(b, frame, 1.9, 1.9, 6, 8, -0.22, "C08A55", 0.16)
    box(b, frame, (-1.05, -0.28, 2.1), (1.05, 0.3, 2.2), "wood", WALNUT)

    for basket_x, green in ((-0.6, HERB_GREENS[0]), (0.1, HERB_GREENS[2]), (0.65, HERB_GREENS[3])):
        cyl(b, frame, (basket_x, 0.0, 2.2), 0.17, 0.14, "wood_light", "D9B57A", sides=8, top=0.2)
        ball(b, frame, (basket_x, 0.0, 2.34), 0.15, "paint", green, scale=(1.0, 1.0, 0.45), segments=6)


def herb_poles(b: Builder, frame: Matrix, **options) -> None:
    """Two drying poles hung on cords under the ceiling, bundles of herbs tied head down along them."""
    generator = random.Random(options.get("seed", 5))
    width = options.get("width", 3.0)
    bundle_xs = [-width / 2.0 + 0.2 + 0.3 * index for index in range(int((width - 0.3) / 0.3))]

    for pole_y in (-0.45, 0.45):
        rod(b, frame, (-width / 2.0, pole_y, -0.35), (width / 2.0, pole_y, -0.35), 0.05, "wood_light", "C08A55")

        for cord_x in (-width / 2.0 + 0.15, width / 2.0 - 0.15):
            rod(b, frame, (cord_x, pole_y, -0.33), (cord_x, pole_y, 0.0), 0.012, "paint", "C9A46A")

        for bundle_x in bundle_xs:
            drop = generator.uniform(0.35, 0.6)
            rod(b, frame, (bundle_x, pole_y, -0.37), (bundle_x, pole_y, -0.45), 0.012, "paint", "C9A46A")
            cyl(b, frame, (bundle_x, pole_y, -0.45 - drop), 0.02, drop, "paint", generator.choice(HERB_GREENS), sides=5, top=0.07)


def stamp_mortar(b: Builder, frame: Matrix, **options) -> None:
    """Stamping room mortar: a bronze mortar on an oak stump, the iron pestle hung from a springy pole on a post."""
    cyl(b, frame, (0.0, -0.1, 0.0), 0.36, 0.55, "wood", WALNUT, sides=8)
    spin(b, frame, [(0.24, 0.55), (0.3, 0.62), (0.32, 0.98), (0.36, 1.02), (0.3, 1.04)], "metal", "B07A3A", sides=10)
    cyl(b, frame, (0.0, -0.1, 0.98), 0.27, 0.01, "paint", "3A2A20", sides=10)
    rod(b, frame, (0.0, -0.1, 0.8), (0.0, -0.1, 1.75), 0.06, "metal", DARK_IRON)
    rod(b, frame, (-0.28, -0.1, 1.6), (0.28, -0.1, 1.6), 0.04, "wood_light", "C08A55")
    rod(b, frame, (0.0, -0.1, 1.75), (0.0, -0.1, 2.45), 0.012, "paint", "C9A46A")
    rod(b, frame, (0.0, 0.42, 0.0), (0.0, 0.42, 2.65), 0.14, "wood", WALNUT)
    rod(b, frame, (0.0, 0.42, 2.55), (0.0, -0.45, 2.45), 0.06, "wood_light", "C08A55")


def lab_hearth(b: Builder, frame: Matrix, **options) -> None:
    """Laboratory hearth (Laborherd): a long brick bench with three fire holes, a stone top with a sand bath, a
    water bath and a retort, a small round furnace at one end, under a plastered smoke hood."""
    width = 4.2
    brick, dark = BRICK["tudor"], BRICK["escuro"]
    hood = [(-0.48, 1.95), (0.65, 1.95), (0.65, 2.85), (0.15, 2.85)]  # (y, z) section, extruded along the bench

    box(b, frame, (-width / 2.0, -0.4, 0.0), (width / 2.0, 0.65, 0.85), "brick", brick)
    box(b, frame, (-width / 2.0 - 0.04, -0.45, 0.85), (width / 2.0 + 0.04, 0.65, 0.93), "stone", STONE["media"])

    for hole_x in (-1.3, 0.0, 1.3):
        box(b, frame, (hole_x - 0.22, -0.42, 0.12), (hole_x + 0.22, -0.38, 0.48), "brick", dark)
        fire(b, frame, hole_x, -0.3, 0.12, 0.34, int(hole_x * 10) + 20)

    box(b, frame, (-1.65, -0.25, 0.93), (-0.95, 0.35, 1.03), "metal", DARK_IRON)
    box(b, frame, (-1.6, -0.2, 1.0), (-1.0, 0.3, 1.04), "paint", "E3C99A")
    spin(b, frame, [(0.12, 0.0), (0.12, 0.08), (0.07, 0.2), (0.02, 0.24)], "vitrine", sides=8, base=(-1.3, 0.05, 1.04))
    rod(b, frame, (-1.3, 0.05, 1.27), (-0.75, -0.2, 1.12), 0.025, "vitrine")
    cyl(b, frame, (0.0, 0.05, 0.93), 0.3, 0.32, "metal", COPPER, sides=10)
    cyl(b, frame, (0.0, 0.05, 1.25), 0.32, 0.03, "metal", COPPER, sides=10)
    cyl(b, frame, (1.55, 0.15, 0.93), 0.32, 0.75, "brick", brick, sides=8, top=0.26)
    cyl(b, frame, (1.55, 0.15, 1.68), 0.12, 0.25, "metal", DARK_IRON, sides=6)
    box(b, frame, (1.43, -0.18, 1.1), (1.67, -0.14, 1.3), "glow_ember")

    b.side_prism(hood, -width / 2.0 - 0.1, width / 2.0 + 0.1, "brick", srgb(dark), frame=frame)
    box(b, frame, (-width / 2.0 - 0.12, -0.52, 1.88), (width / 2.0 + 0.12, -0.46, 1.97), "wood", SOOT)


def copper_still(b: Builder, frame: Matrix, **options) -> None:
    """Copper still: a pot on a small brick furnace, the domed head and its swan neck running into the worm of a
    cooling tub, a tap and a receiving flask."""
    brick = BRICK["tudor"]

    box(b, frame, (-0.75, -0.35, 0.0), (0.05, 0.4, 0.7), "brick", brick)
    box(b, frame, (-0.5, -0.37, 0.12), (-0.2, -0.35, 0.4), "glow_ember")
    spin(b, frame, [(0.3, 0.0), (0.38, 0.12), (0.38, 0.4), (0.24, 0.55), (0.12, 0.6)], "metal", COPPER, sides=10, base=(-0.35, 0.02, 0.7))
    spin(b, frame, [(0.12, 0.0), (0.2, 0.1), (0.18, 0.28), (0.05, 0.4)], "metal", COPPER, sides=10, base=(-0.35, 0.02, 1.3))
    rod(b, frame, (-0.35, 0.02, 1.68), (0.45, 0.02, 1.5), 0.05, "metal", COPPER)
    cyl(b, frame, (0.45, 0.02, 0.0), 0.3, 1.45, "wood_light", "C08A55", sides=10)

    for hoop_z in (0.2, 0.75, 1.3):
        cyl(b, frame, (0.45, 0.02, hoop_z), 0.31, 0.04, "metal", DARK_IRON, sides=10)

    rod(b, frame, (0.45, -0.28, 0.3), (0.45, -0.38, 0.3), 0.03, "metal", COPPER)
    spin(b, frame, [(0.05, 0.0), (0.09, 0.06), (0.06, 0.16), (0.02, 0.22)], "vitrine", sides=8, base=(0.45, -0.42, 0.0))


def poison_cabinet(b: Builder, frame: Matrix, **options) -> None:
    """Locked poison cabinet: a dark cupboard with iron straps and a padlock, a painted skull on the door."""
    box(b, frame, (-0.55, -0.22, 0.0), (0.55, 0.25, 2.0), "wood", "4A2E2A")
    box(b, frame, (-0.58, -0.26, 2.0), (0.58, 0.27, 2.1), "wood", SOOT)
    box(b, frame, (-0.01, -0.235, 0.1), (0.01, -0.22, 1.9), "wood", SOOT)

    for strap_z in (0.4, 1.0, 1.6):
        box(b, frame, (-0.52, -0.24, strap_z), (0.52, -0.22, strap_z + 0.06), "metal", DARK_IRON)

    box(b, frame, (-0.07, -0.27, 0.86), (0.07, -0.24, 0.98), "metal", BRASS)
    ball(b, frame, (0.0, -0.24, 1.3), 0.11, "paint", BONE, scale=(1.0, 0.3, 1.05), segments=8)

    for eye_x in (-0.04, 0.04):
        box(b, frame, (eye_x - 0.022, -0.28, 1.3), (eye_x + 0.022, -0.27, 1.34), "paint", SOOT)

    rod(b, frame, (-0.14, -0.25, 1.06), (0.14, -0.25, 1.2), 0.03, "paint", BONE)
    rod(b, frame, (-0.14, -0.25, 1.2), (0.14, -0.25, 1.06), 0.03, "paint", BONE)
    box(b, frame, (-0.3, -0.24, 1.72), (0.3, -0.22, 1.86), "paint", PARCHMENT)


PROPS = {
    "repositorium": {"build": repositorium, "size": (1.6, 0.62, 3.1), "solid": True, "clearance": 1.0},
    "rezeptur": {"build": rezeptur, "size": (3.32, 0.96, 1.5), "solid": True},
    "show_globe": {"build": show_globe, "size": (0.5, 0.5, 1.74), "solid": True},
    "herb_cabinet": {"build": herb_cabinet, "size": (2.1, 0.58, 2.5), "solid": True, "clearance": 0.8},
    "herb_poles": {"build": herb_poles, "size": (3.0, 1.0, 1.1), "solid": False, "hang": True},
    "stamp_mortar": {"build": stamp_mortar, "size": (0.8, 1.0, 2.65), "solid": True},
    "lab_hearth": {"build": lab_hearth, "size": (4.4, 1.1, 2.85), "solid": True, "light": ((0.0, -0.6, 0.6), LIGHT_FIRE, 2.2, 6.5), "clearance": 1.2},
    "copper_still": {"build": copper_still, "size": (1.55, 0.8, 1.75), "solid": True},
    "poison_cabinet": {"build": poison_cabinet, "size": (1.16, 0.53, 2.1), "solid": True},
}
