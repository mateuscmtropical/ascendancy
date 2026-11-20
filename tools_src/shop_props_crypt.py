"""Props of the hidden crypt and catacombs under the cathedral (build_cathedral_crypt.py). Same contract as the
other prop libraries (see shop_props_common.py).

Drawn after real references: ossuary walls of the old quarry catacombs (femur heads stacked like firewood, two bands
of skulls, loose bones heaped on top, engraved stone plaques on posts, a barrel-shaped column of bones), gilded
baroque glass urns in which incorrupt saints lie in state, confessio altars with a gilded grille, wall lanterns,
long rows of archive presses. The lying saints themselves are the game's character models, posed by
build_cathedral_crypt.py.
"""

import itertools
import math
import random
import sys
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import Builder, srgb  # noqa: E402
from shop_props_arcane import DARK_IRON, GOLD, at, ball, block, box, cyl, gem, hoop, rng, rod  # noqa: E402
from shop_props_common import lathe  # noqa: E402

BONE_SHADES = ("E9DDC0", "DDCDA9", "CDBB93", "BFAA80")
SKULL_SHADES = ("E3D5B5", "D6C49E", "C8B489")
LIMESTONE = "C9B68E"
CRYPT_STONE = "B9AA92"
DARK_STONE = "8E8478"
MARBLE = "EEE8DC"
VELVET = "8E2433"
SOCKET = "2B2236"
GILT = "D9A441"
OSSUARY_LENGTH = 2.0
OSSUARY_HEIGHT = 1.75
FEMUR_STEP = 0.12
SKULL_STEP = 0.24
URN_LENGTH = 2.3
URN_WIDTH = 1.0
URN_BED = 0.86  # top of the cushion bed inside the urn, where the saint lies
LOCULI_LENGTH = 2.0


def skull(b: Builder, frame: Matrix, center: tuple, radius: float = 0.1, tint: str = SKULL_SHADES[0]) -> None:
    """Skull facing -Y: cranium, cheekbones and jaw, dark eye sockets and nose."""
    x, y, z = center

    ball(b, frame, (x, y, z), radius, "paint", tint, scale=(0.82, 0.95, 0.95), segments=6)
    block(b, frame, (x, y - radius * 0.3, z - radius * 0.9), (radius * 1.05, radius * 0.95, radius * 0.5), "paint", tint)

    for side in (-1.0, 1.0):
        block(b, frame, (x + side * radius * 0.36, y - radius * 0.86, z - radius * 0.22), (radius * 0.44, radius * 0.1, radius * 0.4), "paint", SOCKET)

    block(b, frame, (x, y - radius * 0.9, z - radius * 0.48), (radius * 0.2, radius * 0.12, radius * 0.24), "paint", SOCKET)


def femur_band(b: Builder, frame: Matrix, width: float, bottom: float, top: float, generator: random.Random) -> None:
    """Femur and tibia heads stacked like firewood, ends out toward -Y, each a little in or out of the face."""
    columns = int(width / FEMUR_STEP)
    rows = int((top - bottom) / FEMUR_STEP)

    for column, row in itertools.product(range(columns), range(rows)):
        x = -width / 2.0 + FEMUR_STEP * (column + 0.5 + 0.5 * (row % 2)) + generator.uniform(-0.012, 0.012)

        if x > width / 2.0 - 0.04:
            continue

        z = bottom + FEMUR_STEP * (row + 0.5) + generator.uniform(-0.01, 0.01)
        reach = generator.uniform(0.0, 0.06)
        # só a cabeça do osso aparece: o resto do fêmur fica enterrado na pilha
        cyl(b, frame, (x, 0.0 - reach, z), generator.uniform(0.042, 0.052), 0.08, "paint", generator.choice(BONE_SHADES), sides=5, axis="Y")


def skull_band(b: Builder, frame: Matrix, width: float, height: float, generator: random.Random) -> None:
    count = int(width / SKULL_STEP)

    for index in range(count):
        x = -width / 2.0 + SKULL_STEP * (index + 0.5) + generator.uniform(-0.015, 0.015)
        skull(b, frame, (x, -0.04, height + generator.uniform(-0.01, 0.01)), generator.uniform(0.095, 0.105), generator.choice(SKULL_SHADES))


def loose_bones(b: Builder, frame: Matrix, width: float, bottom: float, generator: random.Random) -> None:
    """The heap on top of the facade: bones lying every way and a few skulls half buried."""
    for index in range(int(width * 9)):
        x = generator.uniform(-width / 2.0 + 0.05, width / 2.0 - 0.05)
        angle = generator.uniform(0.0, math.pi)
        length = generator.uniform(0.25, 0.42)
        start = (x - 0.5 * length * math.cos(angle), 0.1 + 0.2 * length * math.sin(angle), bottom + generator.uniform(0.0, 0.12))
        end = (x + 0.5 * length * math.cos(angle), 0.1 - 0.2 * length * math.sin(angle), bottom + generator.uniform(0.0, 0.16))
        rod(b, frame, start, end, 0.045, "paint", generator.choice(BONE_SHADES))

    for index in range(int(width * 2)):
        skull(b, frame, (generator.uniform(-width / 2.0 + 0.1, width / 2.0 - 0.1), 0.02, bottom + 0.12), 0.09, generator.choice(SKULL_SHADES))


def ossuary_wall(b: Builder, frame: Matrix, **options) -> None:
    """2 m of ossuary facade against the rock: femur band, skull band, femur band, skull band, loose heap on top.
    Variant "cross" sets a cross of skulls into the upper femur band, "heart" a heart."""
    generator = rng(options)
    width = OSSUARY_LENGTH
    pattern = options.get("variant", "plain")

    box(b, frame, (-width / 2.0, 0.12, 0.0), (width / 2.0, 0.3, OSSUARY_HEIGHT), "paint", "6E6250")
    femur_band(b, frame, width, 0.0, 0.62, generator)
    skull_band(b, frame, width, 0.72, generator)
    femur_band(b, frame, width, 0.84, 1.44, generator)
    skull_band(b, frame, width, 1.54, generator)
    loose_bones(b, frame, width, 1.64, generator)
    pattern_builders[pattern](b, frame, generator)


def no_pattern(b: Builder, frame: Matrix, generator: random.Random) -> None:
    return


def skull_cross(b: Builder, frame: Matrix, generator: random.Random) -> None:
    for z in (0.9, 1.1, 1.3):
        skull(b, frame, (0.0, -0.1, z), 0.085, SKULL_SHADES[0])

    for x in (-0.2, 0.2):
        skull(b, frame, (x, -0.1, 1.1), 0.085, SKULL_SHADES[0])


def skull_heart(b: Builder, frame: Matrix, generator: random.Random) -> None:
    for step in range(12):
        angle = 2.0 * math.pi * step / 12.0
        x = 0.16 * math.sin(angle) ** 3
        z = 0.16 * (13.0 * math.cos(angle) - 5.0 * math.cos(2 * angle) - 2.0 * math.cos(3 * angle) - math.cos(4 * angle)) / 16.0
        skull(b, frame, (x * 1.6, -0.1, 1.14 + z * 1.6), 0.07, SKULL_SHADES[0])


pattern_builders = {"plain": no_pattern, "cross": skull_cross, "heart": skull_heart}


def bone_barrel(b: Builder, frame: Matrix, **options) -> None:
    """The barrel: a round column of bones bulging at the middle, femur heads out, two skull bands, a stone cap."""
    generator = rng(options)
    rings = [(0.0, 1.0), (0.3, 1.08), (0.6, 1.14), (0.9, 1.16), (1.2, 1.12), (1.5, 1.04)]

    for ring_index, ((ring_z, radius), skull_ring) in enumerate(zip(rings, (False, False, True, False, True, False))):
        count = int(2.0 * math.pi * radius / (SKULL_STEP if skull_ring else FEMUR_STEP))

        for index in range(count):
            angle = 2.0 * math.pi * (index + 0.5 * (ring_index % 2)) / count
            spot = at(frame, (radius * math.cos(angle), radius * math.sin(angle), ring_z + 0.15), math.degrees(angle) - 90.0)

            if skull_ring:
                skull(b, spot, (0.0, 0.0, 0.0), 0.095, generator.choice(SKULL_SHADES))
                continue

            for lift in (-0.06, 0.06):
                cyl(b, spot, (0.0, 0.08, lift), 0.045, 0.2, "paint", generator.choice(BONE_SHADES), sides=5, axis="Y")

    cyl(b, frame, (0.0, 0.0, 0.0), 0.95, 1.7, "paint", "6E6250", sides=12)
    cyl(b, frame, (0.0, 0.0, 1.7), 1.12, 0.12, "stone", LIMESTONE, sides=16)


def catacomb_plaque(b: Builder, frame: Matrix, **options) -> None:
    """Engraved stone tablet on a squared post, the kind that names where the bones came from."""
    generator = rng(options)

    box(b, frame, (-0.09, -0.08, 0.0), (0.09, 0.08, 1.1), "stone", MARBLE)
    box(b, frame, (-0.45, -0.1, 1.05), (0.45, -0.02, 1.55), "stone", MARBLE)

    for line in range(5):
        line_width = generator.uniform(0.35, 0.7) if line else 0.6
        box(b, frame, (-line_width / 2.0, -0.11, 1.45 - line * 0.08), (line_width / 2.0, -0.1, 1.47 - line * 0.08), "paint", "4A4038")


def lintel_inscription(b: Builder, frame: Matrix, **options) -> None:
    """Black stone tablet with a carved warning, set into the rock over a doorway (built at its height)."""
    generator = rng(options)

    box(b, frame, (-0.9, -0.06, 0.0), (0.9, 0.0, 0.42), "stone", "2E2A2C")

    for line in range(3):
        line_width = generator.uniform(1.0, 1.5)
        box(b, frame, (-line_width / 2.0, -0.07, 0.3 - line * 0.1), (line_width / 2.0, -0.06, 0.32 - line * 0.1), "paint", "D8CDB0")


def wall_lantern(b: Builder, frame: Matrix, **options) -> None:
    """Iron lantern on a wall bracket, amber panes (back against the wall at +Y, built at its mounting height)."""
    rod(b, frame, (0.0, 0.18, 0.0), (0.0, -0.12, 0.0), 0.03, "metal", DARK_IRON)
    rod(b, frame, (0.0, 0.18, -0.18), (0.0, -0.02, 0.0), 0.02, "metal", DARK_IRON)
    box(b, frame, (-0.11, -0.23, -0.34), (0.11, -0.01, -0.31), "metal", DARK_IRON)
    box(b, frame, (-0.09, -0.21, -0.31), (0.09, -0.03, -0.08), "glow_amber")
    b.hull([(x, y, -0.08) for x, y in itertools.product((-0.12, 0.12), (-0.24, 0.0))] + [(0.0, -0.12, 0.04)], "metal", srgb(DARK_IRON), frame=frame)


def candle_stand(b: Builder, frame: Matrix, **options) -> None:
    """Tall gilt church candlestick on a three-footed base, one thick candle."""
    for leg in range(3):
        angle = 2.0 * math.pi * leg / 3.0
        rod(b, frame, (0.0, 0.0, 0.18), (0.16 * math.cos(angle), 0.16 * math.sin(angle), 0.0), 0.03, "metal", GILT)

    lathe(b, [(0.07, 0.0), (0.03, 0.06), (0.025, 0.5), (0.05, 0.56), (0.025, 0.62), (0.025, 1.1), (0.08, 1.16), (0.08, 1.2)], 8, "metal", GILT, frame, base=(0.0, 0.0, 0.15))
    cyl(b, frame, (0.0, 0.0, 1.35), 0.035, 0.28, "paint", "F2EAD6", sides=8)
    gem(b, frame, (0.0, 0.0, 1.67), 0.024, "glow_warm")


def flower_vase(b: Builder, frame: Matrix, **options) -> None:
    """Brass vase of red and white flowers, as laid before the saints."""
    generator = rng(options)

    lathe(b, [(0.07, 0.0), (0.1, 0.12), (0.06, 0.28), (0.09, 0.34)], 10, "metal", GOLD, frame)

    for index in range(9):
        angle = generator.uniform(0.0, 2.0 * math.pi)
        reach = generator.uniform(0.04, 0.16)
        top = (reach * math.cos(angle), reach * math.sin(angle), 0.48 + generator.uniform(0.0, 0.18))
        rod(b, frame, (0.0, 0.0, 0.3), top, 0.01, "paint", "4E7A3A")
        ball(b, frame, top, 0.045, "paint", generator.choice(("C2283A", "F4F0E8", "D8405A")), segments=6)


def kneeler(b: Builder, frame: Matrix, **options) -> None:
    """Prie-dieu: padded kneeling step and an arm rest, dark wood (the person kneels on the -Y side)."""
    box(b, frame, (-0.5, -0.25, 0.0), (0.5, 0.1, 0.16), "wood", "4A3226")
    box(b, frame, (-0.48, -0.22, 0.16), (0.48, 0.05, 0.2), "paint", VELVET)
    box(b, frame, (-0.5, 0.1, 0.0), (0.5, 0.2, 0.8), "wood", "4A3226")
    box(b, frame, (-0.55, 0.04, 0.8), (0.55, 0.26, 0.86), "wood", "4A3226")


def chapel_altar(b: Builder, frame: Matrix, **options) -> None:
    """Small stone altar of the bone chapel (back against +Y, 1.3 m wide): a limestone block on a plinth, a marble
    slab, a white altar cloth hanging over the front with a red band and gilt hem, two candlesticks and a crucifix
    standing in the middle. The candles only glow (no real light), the chapel is lit by its candle stands."""
    half_width, half_depth, mensa = 0.65, 0.3, 0.95

    box(b, frame, (-half_width - 0.08, -half_depth - 0.08, 0.0), (half_width + 0.08, half_depth + 0.08, 0.1), "stone", DARK_STONE)
    box(b, frame, (-half_width, -half_depth, 0.1), (half_width, half_depth, mensa - 0.08), "stone", LIMESTONE)
    box(b, frame, (-half_width - 0.05, -half_depth - 0.05, mensa - 0.08), (half_width + 0.05, half_depth + 0.05, mensa), "stone", MARBLE)

    box(b, frame, (-half_width - 0.03, -half_depth - 0.06, mensa - 0.42), (half_width + 0.03, half_depth + 0.04, mensa + 0.01), "paint", "F4F0E8")
    box(b, frame, (-half_width - 0.035, -half_depth - 0.065, mensa - 0.3), (half_width + 0.035, -half_depth - 0.055, mensa - 0.22), "paint", VELVET)
    box(b, frame, (-half_width - 0.035, -half_depth - 0.065, mensa - 0.42), (half_width + 0.035, -half_depth - 0.055, mensa - 0.4), "metal", GILT)

    for side in (-1.0, 1.0):
        x = side * 0.4
        lathe(b, [(0.06, 0.0), (0.02, 0.04), (0.02, 0.2), (0.045, 0.24)], 8, "metal", GILT, frame, base=(x, 0.0, mensa))
        cyl(b, frame, (x, 0.0, mensa + 0.24), 0.02, 0.2, "paint", "F2EAD6", sides=6)
        gem(b, frame, (x, 0.0, mensa + 0.47), 0.02, "glow_warm")

    lathe(b, [(0.1, 0.0), (0.07, 0.05), (0.03, 0.12)], 8, "metal", GILT, frame, base=(0.0, 0.1, mensa))
    box(b, frame, (-0.025, 0.08, mensa + 0.12), (0.025, 0.14, mensa + 0.62), "metal", GILT)
    box(b, frame, (-0.17, 0.08, mensa + 0.4), (0.17, 0.14, mensa + 0.45), "metal", GILT)


def railing(b: Builder, frame: Matrix, **options) -> None:
    """2 m of gilded iron railing on a marble kerb: balusters, top rail, two rings at mid height."""
    box(b, frame, (-1.0, -0.08, 0.0), (1.0, 0.08, 0.1), "stone", MARBLE)
    box(b, frame, (-1.0, -0.03, 0.92), (1.0, 0.03, 0.97), "metal", GILT)

    for bar in range(13):
        x = -0.96 + bar * 0.16
        box(b, frame, (x - 0.01, -0.01, 0.1), (x + 0.01, 0.01, 0.92), "metal", DARK_IRON)

    for x in (-0.5, 0.5):
        hoop(b, at(frame, (x, 0.0, 0.52), 90.0, "X"), (0.0, 0.0, 0.0), 0.16, 0.012, "metal", GILT, axis="Z")


def baroque_urn(b: Builder, frame: Matrix, **options) -> None:
    """Gilded glass urn on scrolled legs (the saint is added by the crypt generator on the bed at URN_BED):
    carved base with a velvet panel, glass on every side, gilt posts, a curved lid with a cross on top."""
    length, width = URN_LENGTH, URN_WIDTH
    base_bottom, base_top = 0.4, 0.72
    glass_top = 1.5

    for x_side, y_side in itertools.product((-1.0, 1.0), (-1.0, 1.0)):
        corner = (x_side * (length / 2.0 - 0.18), y_side * (width / 2.0 - 0.14))
        rod(b, frame, (corner[0], corner[1], base_bottom), (corner[0] * 1.08, corner[1] * 1.25, 0.08), 0.07, "metal", GILT)
        ball(b, frame, (corner[0] * 1.08, corner[1] * 1.25, 0.06), 0.07, "metal", GILT, segments=6)

    box(b, frame, (-length / 2.0, -width / 2.0, base_bottom), (length / 2.0, width / 2.0, base_top), "metal", GILT)
    box(b, frame, (-length / 2.0 + 0.2, -width / 2.0 - 0.01, base_bottom + 0.06), (length / 2.0 - 0.2, width / 2.0 + 0.01, base_top - 0.06), "paint", VELVET)
    box(b, frame, (-length / 2.0 + 0.04, -width / 2.0 + 0.04, base_top), (length / 2.0 - 0.04, width / 2.0 - 0.04, URN_BED), "paint", VELVET)

    for x_side, y_side in itertools.product((-1.0, 1.0), (-1.0, 1.0)):
        post = (x_side * (length / 2.0 - 0.03), y_side * (width / 2.0 - 0.03))
        box(b, frame, (post[0] - 0.035, post[1] - 0.035, base_top), (post[0] + 0.035, post[1] + 0.035, glass_top), "metal", GILT)

    for side in (-1.0, 1.0):
        box(b, frame, (-length / 2.0, side * (width / 2.0 - 0.03) - 0.005, base_top), (length / 2.0, side * (width / 2.0 - 0.03) + 0.005, glass_top), "vitrine")
        box(b, frame, (side * (length / 2.0 - 0.03) - 0.005, -width / 2.0, base_top), (side * (length / 2.0 - 0.03) + 0.005, width / 2.0, glass_top), "vitrine")
        box(b, frame, (-length / 2.0, side * (width / 2.0) - 0.04, glass_top - 0.06), (length / 2.0, side * (width / 2.0) + 0.04, glass_top), "metal", GILT)

    lid = [(x, y * (width / 2.0 + 0.05), glass_top) for x, y in itertools.product((-length / 2.0 - 0.05, length / 2.0 + 0.05), (-1.0, 1.0))]
    lid += [(x, y * width * 0.3, glass_top + 0.18) for x, y in itertools.product((-length / 2.0 + 0.1, length / 2.0 - 0.1), (-1.0, 1.0))]
    b.hull(lid, "metal", srgb(GILT), frame=frame)
    box(b, frame, (-0.02, -0.02, glass_top + 0.18), (0.02, 0.02, glass_top + 0.5), "metal", GILT)
    box(b, frame, (-0.1, -0.02, glass_top + 0.38), (0.1, 0.02, glass_top + 0.42), "metal", GILT)


def sarcophagus(b: Builder, frame: Matrix, **options) -> None:
    """Stone tomb chest on a plinth with carved panels; the recumbent effigy on its lid is added by the generator."""
    length, width = 2.3, 1.0

    box(b, frame, (-length / 2.0 - 0.08, -width / 2.0 - 0.08, 0.0), (length / 2.0 + 0.08, width / 2.0 + 0.08, 0.16), "stone", DARK_STONE)
    box(b, frame, (-length / 2.0, -width / 2.0, 0.16), (length / 2.0, width / 2.0, 0.9), "stone", CRYPT_STONE)
    box(b, frame, (-length / 2.0 - 0.04, -width / 2.0 - 0.04, 0.9), (length / 2.0 + 0.04, width / 2.0 + 0.04, 1.0), "stone", CRYPT_STONE)

    for panel in range(3):
        center = -length / 3.0 + panel * length / 3.0
        box(b, frame, (center - 0.3, -width / 2.0 - 0.02, 0.3), (center + 0.3, -width / 2.0, 0.76), "stone", "A89A82")
        box(b, frame, (center - 0.02, -width / 2.0 - 0.03, 0.38), (center + 0.02, -width / 2.0 - 0.01, 0.68), "stone", "8E8070")
        box(b, frame, (center - 0.12, -width / 2.0 - 0.03, 0.56), (center + 0.12, -width / 2.0 - 0.01, 0.6), "stone", "8E8070")


def loculi_wall(b: Builder, frame: Matrix, **options) -> None:
    """2 m of burial niches: marble plaques with carved lines and a bronze cross, four rows in a stone frame."""
    generator = rng(options)
    rows, columns = 4, 2
    cell_width, cell_height = LOCULI_LENGTH / columns, 0.7

    box(b, frame, (-LOCULI_LENGTH / 2.0, -0.02, 0.0), (LOCULI_LENGTH / 2.0, 0.3, rows * cell_height + 0.3), "stone", CRYPT_STONE)

    for row, column in itertools.product(range(rows), range(columns)):
        left = -LOCULI_LENGTH / 2.0 + column * cell_width + 0.07
        bottom = 0.15 + row * cell_height + 0.05
        middle = left + cell_width / 2.0 - 0.07
        box(b, frame, (left, -0.05, bottom), (left + cell_width - 0.14, -0.02, bottom + cell_height - 0.1), "paint", generator.choice((MARBLE, "E2DBCB", "D9D1C0")))

        for line in range(3):
            line_width = generator.uniform(0.25, 0.55)
            box(b, frame, (middle - line_width / 2.0, -0.06, bottom + 0.14 + line * 0.1), (middle + line_width / 2.0, -0.05, bottom + 0.16 + line * 0.1), "paint", "6E6458")

        box(b, frame, (middle - 0.012, -0.07, bottom + 0.42), (middle + 0.012, -0.05, bottom + 0.56), "metal", "A8783A")
        box(b, frame, (middle - 0.04, -0.07, bottom + 0.5), (middle + 0.04, -0.05, bottom + 0.522), "metal", "A8783A")

    box(b, frame, (-LOCULI_LENGTH / 2.0 - 0.04, -0.1, rows * cell_height + 0.3), (LOCULI_LENGTH / 2.0 + 0.04, 0.3, rows * cell_height + 0.42), "stone", MARBLE)


def iron_gate(b: Builder, frame: Matrix, **options) -> None:
    """One leaf of a wrought-iron grille gate (0.8 x 2.3), standing open against the jamb; spear tips on top."""
    width = 0.8

    for rail_z in (0.1, 1.15, 2.2):
        box(b, frame, (-width / 2.0, -0.02, rail_z), (width / 2.0, 0.02, rail_z + 0.05), "metal", DARK_IRON)

    for bar in range(7):
        x = -width / 2.0 + 0.05 + bar * (width - 0.1) / 6.0
        box(b, frame, (x - 0.012, -0.012, 0.05), (x + 0.012, 0.012, 2.3), "metal", DARK_IRON)
        gem(b, frame, (x, 0.0, 2.36), 0.03, "metal", DARK_IRON, scale=(0.6, 0.6, 2.0))


def confessio_altar(b: Builder, frame: Matrix, **options) -> None:
    """Crypt altar (back against +Y): marble mensa on a base whose front is a gilded scroll grille over glass, the
    saint lying behind it (added by the generator at z 0.42); six candlesticks, a crucifix and an altar cloth."""
    length, depth, mensa = 2.8, 1.2, 1.05

    box(b, frame, (-length / 2.0 - 0.3, -depth / 2.0 - 0.6, 0.0), (length / 2.0 + 0.3, depth / 2.0, 0.15), "stone", MARBLE)
    box(b, frame, (-length / 2.0, -depth / 2.0, 0.15), (length / 2.0, depth / 2.0, 0.42), "stone", "D9D1C0")
    box(b, frame, (-length / 2.0, depth / 2.0 - 0.1, 0.42), (length / 2.0, depth / 2.0, mensa), "stone", "D9D1C0")

    for side in (-1.0, 1.0):
        pier_x = side * (length / 2.0 - 0.09)
        box(b, frame, (pier_x - 0.09, -depth / 2.0, 0.42), (pier_x + 0.09, depth / 2.0, mensa), "stone", MARBLE)

    box(b, frame, (-length / 2.0 - 0.08, -depth / 2.0 - 0.08, mensa), (length / 2.0 + 0.08, depth / 2.0 + 0.04, mensa + 0.1), "stone", MARBLE)
    box(b, frame, (-length / 2.0 + 0.15, -depth / 2.0 - 0.09, mensa + 0.02), (length / 2.0 - 0.15, -depth / 2.0 - 0.08, mensa + 0.1), "paint", "F4F0E8")
    box(b, frame, (-length / 2.0 + 0.18, -depth / 2.0 + 0.02, 0.42), (length / 2.0 - 0.18, -depth / 2.0 + 0.03, mensa - 0.04), "vitrine")
    box(b, frame, (-length / 2.0 + 0.18, -depth / 2.0, 0.42), (length / 2.0 - 0.18, -depth / 2.0 + 0.02, 0.46), "metal", GILT)
    box(b, frame, (-length / 2.0 + 0.18, -depth / 2.0, mensa - 0.08), (length / 2.0 - 0.18, -depth / 2.0 + 0.02, mensa - 0.04), "metal", GILT)

    for scroll in range(7):
        x = -1.05 + scroll * 0.35
        hoop(b, at(frame, (x, -depth / 2.0 + 0.01, 0.74), 90.0, "X"), (0.0, 0.0, 0.0), 0.14, 0.014, "metal", GILT, axis="Z")

    for index, x in enumerate((-1.2, -0.85, -0.5, 0.5, 0.85, 1.2)):
        height = 0.34 - 0.05 * abs(index - 2.5)
        lathe(b, [(0.06, 0.0), (0.02, 0.04), (0.02, height), (0.05, height + 0.03)], 8, "metal", GILT, frame, base=(x, 0.35, mensa + 0.1))
        cyl(b, frame, (x, 0.35, mensa + 0.13 + height), 0.02, 0.26, "paint", "F2EAD6", sides=6)
        gem(b, frame, (x, 0.35, mensa + 0.43 + height), 0.02, "glow_warm")

    box(b, frame, (-0.03, 0.42, mensa + 0.1), (0.03, 0.48, mensa + 1.25), "metal", GILT)
    box(b, frame, (-0.26, 0.42, mensa + 0.88), (0.26, 0.48, mensa + 0.94), "metal", GILT)


def relic_shelf(b: Builder, frame: Matrix, **options) -> None:
    """Dark wooden cabinet of relics: gilded reliquaries, a jewelled skull on a cushion, old crowns, chalices, a codex."""
    generator = rng(options)
    width, depth = 2.0, 0.45
    shelves = (0.9, 1.55)

    box(b, frame, (-width / 2.0, -depth / 2.0, 0.0), (width / 2.0, depth / 2.0, 0.85), "wood", "4A3226")
    box(b, frame, (-width / 2.0, depth / 2.0 - 0.04, 0.85), (width / 2.0, depth / 2.0, 2.3), "wood", "4A3226")
    box(b, frame, (-width / 2.0 - 0.03, -depth / 2.0 - 0.03, 2.3), (width / 2.0 + 0.03, depth / 2.0 + 0.03, 2.4), "wood", "4A3226")

    for side in (-1.0, 1.0):
        box(b, frame, (side * width / 2.0 - 0.04, -depth / 2.0, 0.85), (side * width / 2.0 + 0.04, depth / 2.0, 2.3), "wood", "4A3226")

    box(b, frame, (-width / 2.0, -depth / 2.0, shelves[1] - 0.03), (width / 2.0, depth / 2.0, shelves[1]), "wood", "4A3226")

    for index, x in enumerate((-0.7, -0.25, 0.25, 0.7)):
        relic_builders[("reliquary", "crown", "chalice", "reliquary")[index]](b, at(frame, (x, 0.0, shelves[0])), generator)

    box(b, frame, (-0.3, -0.12, shelves[1]), (0.3, 0.12, shelves[1] + 0.06), "paint", VELVET)
    skull(b, frame, (0.0, -0.02, shelves[1] + 0.16), 0.1, "D8C8A4")
    gem(b, frame, (0.0, -0.11, shelves[1] + 0.25), 0.02, "glow_pink")

    for side in (-1.0, 1.0):
        relic_builders["codex" if side < 0 else "crown"](b, at(frame, (side * 0.7, 0.0, shelves[1])), generator)


def reliquary(b: Builder, frame: Matrix, generator: random.Random) -> None:
    lathe(b, [(0.08, 0.0), (0.06, 0.04), (0.03, 0.08), (0.07, 0.12), (0.07, 0.3), (0.0, 0.42)], 8, "metal", GOLD, frame)
    box(b, frame, (-0.045, -0.072, 0.15), (0.045, -0.06, 0.27), "vitrine")
    gem(b, frame, (0.0, 0.0, 0.45), 0.03, "glow_pink")


def crown(b: Builder, frame: Matrix, generator: random.Random) -> None:
    box(b, frame, (-0.16, -0.12, 0.0), (0.16, 0.12, 0.05), "paint", VELVET)
    hoop(b, frame, (0.0, 0.0, 0.1), 0.1, 0.02, "metal", GOLD, sides=12)

    for point in range(6):
        angle = 2.0 * math.pi * point / 6.0
        gem(b, frame, (0.1 * math.cos(angle), 0.1 * math.sin(angle), 0.16), 0.03, "metal", GOLD, scale=(0.7, 0.7, 1.8))

    gem(b, frame, (0.0, -0.1, 0.1), 0.025, "glow_pink")


def chalice(b: Builder, frame: Matrix, generator: random.Random) -> None:
    lathe(b, [(0.07, 0.0), (0.02, 0.03), (0.015, 0.14), (0.03, 0.16), (0.07, 0.25), (0.075, 0.27)], 10, "metal", GOLD, frame)


def codex(b: Builder, frame: Matrix, generator: random.Random) -> None:
    box(b, frame, (-0.16, -0.12, 0.0), (0.16, 0.12, 0.07), "paint", "5A2A20")
    box(b, frame, (-0.14, -0.121, 0.015), (0.14, 0.121, 0.055), "paint", "E8DCC0")
    box(b, frame, (-0.05, -0.125, 0.0), (0.05, -0.12, 0.07), "metal", GOLD)


relic_builders = {"reliquary": reliquary, "crown": crown, "chalice": chalice, "codex": codex}


def archive_cabinet(b: Builder, frame: Matrix, **options) -> None:
    """Tall archive press (2 x 0.6 x 3): numbered doors below, open shelves of bound registers and tied document
    bundles above, a cornice; the presses stand in long rows like the stacks of a real archive."""
    generator = rng(options)
    width, depth, height = 2.0, 0.6, 3.0

    box(b, frame, (-width / 2.0, -depth / 2.0, 0.0), (width / 2.0, depth / 2.0, 0.08), "wood", "3E2A1E")
    box(b, frame, (-width / 2.0, depth / 2.0 - 0.04, 0.08), (width / 2.0, depth / 2.0, height), "wood", "5A3C28")
    box(b, frame, (-width / 2.0 - 0.05, -depth / 2.0 - 0.05, height), (width / 2.0 + 0.05, depth / 2.0 + 0.02, height + 0.12), "wood", "3E2A1E")

    for side in (-1.0, 0.0, 1.0):
        box(b, frame, (side * (width / 2.0 - 0.03) - 0.03, -depth / 2.0, 0.08), (side * (width / 2.0 - 0.03) + 0.03, depth / 2.0, height), "wood", "4A3226")

    for door in range(4):
        left = -width / 2.0 + 0.06 + door * (width - 0.12) / 4.0
        box(b, frame, (left + 0.01, -depth / 2.0 - 0.01, 0.1), (left + (width - 0.12) / 4.0 - 0.01, -depth / 2.0 + 0.02, 1.0), "wood", "6B4A32")
        box(b, frame, (left + 0.12, -depth / 2.0 - 0.025, 0.86), (left + 0.2, -depth / 2.0 - 0.01, 0.92), "paint", "F2EAD6")
        ball(b, frame, (left + (width - 0.12) / 8.0, -depth / 2.0 - 0.03, 0.6), 0.015, "metal", GOLD, segments=5)

    for shelf_z in (1.02, 1.5, 1.98, 2.46):
        box(b, frame, (-width / 2.0, -depth / 2.0, shelf_z - 0.03), (width / 2.0, depth / 2.0, shelf_z), "wood", "4A3226")
        x = -width / 2.0 + 0.08

        while x < width / 2.0 - 0.12:
            is_register = generator.random() < 0.7
            thickness = generator.uniform(0.05, 0.11) if is_register else generator.uniform(0.18, 0.26)
            tall = generator.uniform(0.28, 0.4) if is_register else generator.uniform(0.12, 0.2)
            tint = generator.choice(("6E3A2A", "8A5A3A", "A9876A", "5A3A2A", "C8B08A")) if is_register else "D8C8A4"
            box(b, frame, (x, -depth / 2.0 + 0.05, shelf_z), (x + thickness, depth / 2.0 - 0.06, shelf_z + tall), "paint", tint)
            x += thickness + generator.uniform(0.003, 0.02)


PROPS = {
    "ossuary_wall": {"build": ossuary_wall, "size": (OSSUARY_LENGTH, 0.42, OSSUARY_HEIGHT + 0.1), "solid": True, "variants": list(pattern_builders)},
    "bone_barrel": {"build": bone_barrel, "size": (2.4, 2.4, 1.85), "solid": True},
    "catacomb_plaque": {"build": catacomb_plaque, "size": (0.9, 0.22, 1.55), "solid": True},
    "lintel_inscription": {"build": lintel_inscription, "size": (1.8, 0.08, 0.42), "solid": False},
    "wall_lantern": {"build": wall_lantern, "size": (0.26, 0.42, 0.4), "solid": False, "light": ((0.0, -0.12, -0.2), "FFB060", 1.3, 7.0)},
    "candle_stand": {"build": candle_stand, "size": (0.36, 0.36, 1.7), "solid": True, "light": ((0.0, 0.0, 1.72), "FFB060", 1.2, 5.5)},
    "flower_vase": {"build": flower_vase, "size": (0.36, 0.36, 0.7), "solid": False},
    "kneeler": {"build": kneeler, "size": (1.1, 0.51, 0.86), "solid": True},
    "chapel_altar": {"build": chapel_altar, "size": (1.46, 0.76, 1.6), "solid": True},
    "railing": {"build": railing, "size": (2.0, 0.16, 0.97), "solid": True},
    "baroque_urn": {"build": baroque_urn, "size": (URN_LENGTH + 0.2, URN_WIDTH + 0.3, 2.0), "solid": True},
    "sarcophagus": {"build": sarcophagus, "size": (2.46, 1.16, 1.1), "solid": True},
    "loculi_wall": {"build": loculi_wall, "size": (LOCULI_LENGTH, 0.4, 3.2), "solid": True},
    "iron_gate": {"build": iron_gate, "size": (0.8, 0.06, 2.4), "solid": False},
    "confessio_altar": {"build": confessio_altar, "size": (3.4, 1.8, 2.4), "solid": True},
    "relic_shelf": {"build": relic_shelf, "size": (2.06, 0.5, 2.4), "solid": True},
    "archive_cabinet": {"build": archive_cabinet, "size": (2.1, 0.62, 3.12), "solid": True},
}
