"""Mansion furniture of the casarão's vestibule and salons: paintings, mirrors, console tables, urns on pedestals,
a long-case clock, an upright piano and a gilt chandelier.

Runs inside Blender, imported by build_market_shops.py and build_prop_sheet.py. PROPS contract and local axes in
shop_props_common.py: X width centred on 0, the customer side faces -Y, the back at Y = +size[1] / 2, Z up from
the floor; wall props are built at their mounting height.
"""

import math
import random
import sys
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import WOOD_DARK_BAND, Builder, srgb  # noqa: E402
from shop_props_common import lathe, ring  # noqa: E402

GILT = "D9A441"
GILT_DEEP = "B5822E"
MAHOGANY = "6B3A26"
EBONY = "2B2236"
IVORY = "F2E6CF"
MARBLE = "F1ECE2"
GLAZE_BLUE = "2E5AA8"
WOOD_UV = ("band", *WOOD_DARK_BAND, 1.5)
WALL_Y = 0.04  # a parede fica nesta face dos quadros e espelhos
PAINTING_CENTRE = 2.35
SCENES = {  # variante -> (largura, altura da tela, camadas de baixo para cima: (cor, [(x, z) em fração da tela]))
    "landscape": (1.6, 1.05, [
        ("9CC4E8", [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]),
        ("FFE2B0", [(0.72, 0.7), (0.8, 0.66), (0.86, 0.72), (0.84, 0.8), (0.76, 0.82)]),
        ("7FA8A0", [(0.0, 0.0), (1.0, 0.0), (1.0, 0.5), (0.7, 0.62), (0.45, 0.48), (0.2, 0.6), (0.0, 0.5)]),
        ("5E9A62", [(0.0, 0.0), (1.0, 0.0), (1.0, 0.36), (0.6, 0.44), (0.3, 0.32), (0.0, 0.4)]),
        ("8FBF6A", [(0.0, 0.0), (1.0, 0.0), (1.0, 0.18), (0.5, 0.24), (0.0, 0.16)]),
    ]),
    "seascape": (1.6, 1.05, [
        ("F2C9A0", [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]),
        ("FFE9C4", [(0.2, 0.6), (0.3, 0.56), (0.36, 0.64), (0.3, 0.72), (0.22, 0.7)]),
        ("3E6A9A", [(0.0, 0.0), (1.0, 0.0), (1.0, 0.46), (0.0, 0.46)]),
        ("2E5080", [(0.0, 0.0), (1.0, 0.0), (1.0, 0.2), (0.6, 0.26), (0.25, 0.18), (0.0, 0.24)]),
        ("F4F2EC", [(0.6, 0.38), (0.72, 0.38), (0.66, 0.74)]),
        ("5A3A26", [(0.56, 0.32), (0.78, 0.32), (0.74, 0.38), (0.58, 0.38)]),
    ]),
    "station": (0.5, 0.65, [
        ("3A2E26", [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]),
        ("E2D2AC", [(0.1, 0.08), (0.9, 0.08), (0.9, 0.7), (0.5, 0.92), (0.1, 0.7)]),
        ("7A4A2A", [(0.0, 0.0), (1.0, 0.0), (1.0, 0.34), (0.0, 0.34)]),
        ("B9893A", [(0.45, 0.22), (0.55, 0.22), (0.55, 0.78), (0.45, 0.78)]),
        ("B9893A", [(0.25, 0.54), (0.75, 0.54), (0.75, 0.64), (0.25, 0.64)]),
    ]),
    "portrait": (0.95, 1.3, [
        ("3A2E38", [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]),
        ("5B4658", [(0.1, 0.0), (0.9, 0.0), (0.9, 0.9), (0.5, 1.0), (0.1, 0.9)]),
        ("7A2F3A", [(0.14, 0.0), (0.86, 0.0), (0.78, 0.36), (0.6, 0.46), (0.4, 0.46), (0.22, 0.36)]),
        ("F2E6CF", [(0.42, 0.34), (0.58, 0.34), (0.54, 0.46), (0.46, 0.46)]),
        ("F0C8B0", [(0.38, 0.5), (0.5, 0.44), (0.62, 0.5), (0.64, 0.68), (0.56, 0.78), (0.44, 0.78), (0.36, 0.68)]),
        ("4A2F20", [(0.36, 0.66), (0.4, 0.8), (0.5, 0.86), (0.6, 0.8), (0.64, 0.66), (0.58, 0.76), (0.42, 0.76)]),
    ]),
    "lady": (0.95, 1.3, [
        ("2F4A44", [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]),
        ("47685E", [(0.1, 0.0), (0.9, 0.0), (0.9, 0.9), (0.5, 1.0), (0.1, 0.9)]),
        ("2E5AA8", [(0.1, 0.0), (0.9, 0.0), (0.72, 0.34), (0.58, 0.44), (0.42, 0.44), (0.28, 0.34)]),
        ("F4D8C8", [(0.4, 0.42), (0.6, 0.42), (0.56, 0.5), (0.44, 0.5)]),
        ("F4D8C8", [(0.38, 0.52), (0.5, 0.46), (0.62, 0.52), (0.63, 0.68), (0.56, 0.77), (0.44, 0.77), (0.37, 0.68)]),
        ("8B4A2A", [(0.32, 0.5), (0.36, 0.78), (0.5, 0.88), (0.64, 0.78), (0.68, 0.5), (0.62, 0.74), (0.5, 0.8), (0.38, 0.74)]),
    ]),
}


def gilt_frame(b: Builder, frame: Matrix, width: float, bottom: float, height: float, border: float = 0.09) -> None:
    """Moulded gilt frame around a width x height opening standing on z = bottom, against the wall."""
    half = width / 2.0
    bars = [
        ((-half - border, bottom - border), (half + border, bottom)),
        ((-half - border, bottom + height), (half + border, bottom + height + border)),
        ((-half - border, bottom), (-half, bottom + height)),
        ((half, bottom), (half + border, bottom + height)),
    ]

    for (x_from, z_from), (x_to, z_to) in bars:
        b.box((x_from, WALL_Y - 0.07, z_from), (x_to, WALL_Y, z_to), "paint", srgb(GILT), frame=frame)

    b.box((-half - 0.02, WALL_Y - 0.045, bottom - 0.02), (half + 0.02, WALL_Y, bottom + height + 0.02), "paint", srgb(GILT_DEEP), frame=frame)


def painting(b: Builder, frame: Matrix, variant: str = "landscape", **options) -> None:
    """Oil painting in a gilt frame: a landscape, a seascape or a portrait built of flat colour shapes."""
    width, height, layers = SCENES[variant]
    bottom = PAINTING_CENTRE - height / 2.0

    gilt_frame(b, frame, width, bottom, height)

    for index, (color, shape) in enumerate(layers):
        depth = WALL_Y - 0.05 - 0.003 * index
        outline = [(-width / 2.0 + x * width, bottom + z * height) for x, z in shape]
        b.prism(outline, depth - 0.003, depth, "paint", srgb(color), frame=frame)


def wall_mirror(b: Builder, frame: Matrix, **options) -> None:
    """Tall pier glass in a gilt frame with a crest, hung over a console table."""
    width, bottom, height = 0.9, 1.45, 1.5

    gilt_frame(b, frame, width, bottom, height)
    b.box((-width / 2.0, WALL_Y - 0.052, bottom), (width / 2.0, WALL_Y - 0.046, bottom + height), "glass", frame=frame)
    b.prism([(-0.36, bottom + height + 0.09), (0.36, bottom + height + 0.09), (0.2, bottom + height + 0.26), (0.0, bottom + height + 0.4), (-0.2, bottom + height + 0.26)], WALL_Y - 0.06, WALL_Y, "paint", srgb(GILT), frame=frame)
    b.sphere((0.0, WALL_Y - 0.04, bottom + height + 0.22), 0.06, "paint", srgb(GILT_DEEP), frame=frame, segments=8)


def turned_leg(b: Builder, frame: Matrix, x: float, y: float, height: float, tint: str = MAHOGANY) -> None:
    profile = [(0.02, 0.0), (0.035, 0.04), (0.022, 0.1), (0.03, height * 0.5), (0.02, height - 0.16), (0.04, height - 0.1), (0.04, height)]

    lathe(b, profile, 8, "wood", tint, frame @ Matrix.Translation((x, y, 0.0)))


def vase(b: Builder, frame: Matrix, x: float, y: float, z: float, seed: int) -> None:
    """Glazed white-and-blue vase with a bunch of flowers."""
    generator = random.Random(seed)
    at = frame @ Matrix.Translation((x, y, z))

    lathe(b, [(0.05, 0.0), (0.06, 0.02), (0.1, 0.12), (0.11, 0.2), (0.06, 0.3), (0.05, 0.34), (0.07, 0.37)], 10, "paint", MARBLE, at)
    lathe(b, [(0.112, 0.15), (0.112, 0.22)], 10, "paint", GLAZE_BLUE, at)

    for index in range(7):
        angle = math.tau * index / 7.0
        reach = 0.06 + 0.06 * generator.random()
        head = (reach * math.cos(angle), reach * math.sin(angle), 0.46 + 0.12 * generator.random())
        b.beam((0.0, 0.0, 0.34), head, 0.012, 0.012, "paint", srgb("3F8A50"), frame=at)
        b.sphere(head, 0.045, "paint", srgb(generator.choice(("E8C14F", "C9483B", "F2E6CF", "C46AA8"))), frame=at, segments=6)


def candlestick(b: Builder, frame: Matrix, x: float, y: float, z: float) -> None:
    at = frame @ Matrix.Translation((x, y, z))

    lathe(b, [(0.06, 0.0), (0.06, 0.015), (0.02, 0.04), (0.015, 0.2), (0.035, 0.22), (0.035, 0.24)], 8, "metal", GILT, at)
    b.cylinder((0.0, 0.0, 0.24), 0.014, 0.14, 6, "paint", srgb(IVORY), frame=at)
    b.sphere((0.0, 0.0, 0.4), 0.018, "glow_warm", frame=at, segments=6)


def console_table(b: Builder, frame: Matrix, seed: int = 1, **options) -> None:
    """Marble-topped console against a wall with a vase of flowers between two candlesticks."""
    top = 0.88

    b.box((-0.65, -0.22, top - 0.04), (0.65, 0.22, top), "paint", srgb(MARBLE), frame=frame)
    b.box((-0.6, -0.17, top - 0.16), (0.6, 0.2, top - 0.04), "wood", srgb(MAHOGANY), frame=frame, uv=WOOD_UV)
    b.box((-0.56, -0.12, 0.14), (0.56, 0.16, 0.17), "wood", srgb(MAHOGANY), frame=frame, uv=WOOD_UV)

    for x, y in ((-0.56, -0.14), (0.56, -0.14), (-0.56, 0.16), (0.56, 0.16)):
        turned_leg(b, frame, x, y, top - 0.16)

    vase(b, frame, 0.0, 0.02, top, seed)
    candlestick(b, frame, -0.46, 0.0, top)
    candlestick(b, frame, 0.46, 0.0, top)


def pedestal_urn(b: Builder, frame: Matrix, **options) -> None:
    """Glazed urn with a gold finial on a panelled stone pedestal."""
    stone = srgb("E9DCC6")
    urn = frame @ Matrix.Translation((0.0, 0.0, 0.95))

    b.box((-0.28, -0.28, 0.0), (0.28, 0.28, 0.12), "plaster", stone, frame=frame)
    b.box((-0.22, -0.22, 0.12), (0.22, 0.22, 0.82), "plaster", stone, frame=frame)
    b.box((-0.27, -0.27, 0.82), (0.27, 0.27, 0.95), "plaster", stone, frame=frame)
    b.box((-0.15, -0.225, 0.24), (0.15, -0.22, 0.7), "paint", srgb(GLAZE_BLUE), frame=frame)
    lathe(b, [(0.15, 0.0), (0.15, 0.05), (0.09, 0.09), (0.07, 0.14), (0.18, 0.27), (0.21, 0.38), (0.18, 0.5), (0.11, 0.55), (0.13, 0.58), (0.12, 0.62), (0.02, 0.64)], 10, "paint", MARBLE, urn)
    lathe(b, [(0.215, 0.33), (0.215, 0.42)], 10, "paint", GLAZE_BLUE, urn)
    b.sphere((0.0, 0.0, 0.7), 0.05, "paint", srgb(GILT), scale=(1.0, 1.0, 1.4), frame=urn)


def long_case_clock(b: Builder, frame: Matrix, **options) -> None:
    """Long-case clock in mahogany: plinth, trunk with a glazed door and a brass pendulum, hood with the dial."""
    wood = srgb(MAHOGANY)
    dial = 1.9

    b.box((-0.27, -0.16, 0.0), (0.27, 0.16, 0.5), "wood", wood, frame=frame, uv=WOOD_UV)
    b.box((-0.19, -0.12, 0.5), (0.19, 0.13, 1.6), "wood", wood, frame=frame, uv=WOOD_UV)
    b.box((-0.27, -0.16, 1.6), (0.27, 0.16, 2.2), "wood", wood, frame=frame, uv=WOOD_UV)
    b.prism([(-0.3, 2.2), (0.3, 2.2), (0.2, 2.3), (0.0, 2.38), (-0.2, 2.3)], -0.18, 0.16, "wood", srgb(EBONY), frame=frame)
    b.box((-0.12, -0.125, 0.62), (0.12, -0.12, 1.5), "glass", frame=frame)
    b.box((-0.008, -0.11, 0.9), (0.008, -0.1, 1.5), "metal", srgb(GILT), frame=frame)
    b.cylinder((0.0, -0.1, 0.86), 0.07, 0.012, 10, "metal", srgb(GILT), frame=frame, axis="Y")
    b.cylinder((0.0, -0.165, dial), 0.19, 0.01, 14, "paint", srgb(IVORY), frame=frame, axis="Y")

    for hour in range(12):
        angle = math.tau * hour / 12.0
        b.box((0.15 * math.sin(angle) - 0.012, -0.175, dial + 0.15 * math.cos(angle) - 0.012), (0.15 * math.sin(angle) + 0.012, -0.165, dial + 0.15 * math.cos(angle) + 0.012), "paint", srgb(EBONY), frame=frame)

    for length, angle in ((0.09, math.radians(-60.0)), (0.14, math.radians(60.0))):
        b.beam((0.0, -0.18, dial), (length * math.sin(angle), -0.18, dial + length * math.cos(angle)), 0.016, 0.008, "paint", srgb(EBONY), frame=frame)


def piano(b: Builder, frame: Matrix, **options) -> None:
    """Upright piano in ebony with brass candle arms, an open keyboard, a music sheet and a round stool."""
    wood = srgb(EBONY)
    key_count = 28
    key_width = 1.3 / key_count

    b.box((-0.75, 0.0, 0.0), (0.75, 0.36, 1.25), "wood", wood, frame=frame, uv=WOOD_UV)
    b.box((-0.79, -0.02, 1.25), (0.79, 0.38, 1.29), "wood", srgb(MAHOGANY), frame=frame, uv=WOOD_UV)
    b.box((-0.75, -0.3, 0.62), (0.75, 0.0, 0.72), "wood", wood, frame=frame, uv=WOOD_UV)
    b.box((-0.65, -0.28, 0.72), (0.65, -0.02, 0.735), "paint", srgb(IVORY), frame=frame)
    b.box((-0.3, -0.04, 0.86), (0.3, -0.01, 1.12), "paint", srgb(IVORY), frame=frame)

    for index in range(key_count):
        if index % 7 in (2, 6):
            continue

        key_x = -0.65 + (index + 1) * key_width
        b.box((key_x - 0.014, -0.18, 0.735), (key_x + 0.014, -0.02, 0.75), "paint", srgb(EBONY), frame=frame)

    for side_sign in (-1, 1):
        b.box((side_sign * 0.75 - 0.04, -0.3, 0.0), (side_sign * 0.75 + 0.04, -0.22, 0.62), "wood", wood, frame=frame, uv=WOOD_UV)
        candlestick(b, frame, side_sign * 0.52, -0.1, 0.98)
        b.box((side_sign * 0.52 - 0.012, -0.1, 0.96), (side_sign * 0.52 + 0.012, 0.0, 0.98), "metal", srgb(GILT), frame=frame)

    lathe(b, [(0.16, 0.0), (0.16, 0.03), (0.035, 0.08), (0.03, 0.4), (0.17, 0.44), (0.17, 0.5)], 10, "wood", MAHOGANY, frame @ Matrix.Translation((0.0, -0.72, 0.0)))
    lathe(b, [(0.165, 0.5), (0.165, 0.54), (0.12, 0.56)], 10, "paint", "7A2F3A", frame @ Matrix.Translation((0.0, -0.72, 0.0)))


CHANDELIER_TIERS = ((0.95, -1.0, 10), (0.55, -0.55, 6))  # (raio, altura sob o fim da corrente, velas)


def chandelier_tier(b: Builder, frame: Matrix, radius: float, height: float, candles: int) -> None:
    ring(b, (0.0, 0.0, height), radius, 0.022, "metal", GILT, frame, sides=20, tube_sides=4)

    for index in range(candles):
        angle = math.tau * index / candles
        arm = (radius * math.cos(angle), radius * math.sin(angle), height)
        drop = (0.6 * arm[0], 0.6 * arm[1], height - 0.16)

        b.beam((0.0, 0.0, height + 0.12), arm, 0.022, 0.022, "metal", srgb(GILT), frame=frame)
        b.cylinder((arm[0], arm[1], height), 0.05, 0.03, 8, "metal", srgb(GILT), top_radius=0.035, frame=frame)
        b.cylinder((arm[0], arm[1], height + 0.03), 0.02, 0.14, 6, "paint", srgb(IVORY), frame=frame)
        b.cylinder((arm[0], arm[1], height + 0.17), 0.022, 0.08, 4, "glow_warm", top_radius=0.003, frame=frame)
        b.sphere(drop, 0.035, "paint", srgb("CFE6F2"), scale=(1.0, 1.0, 1.6), frame=frame, segments=6)


def grand_chandelier(b: Builder, frame: Matrix, drop: float = 0.8, **options) -> None:
    """Gilt chandelier of two candle tiers with glass drops, on a chain `drop` metres long under a ceiling boss."""
    body = frame @ Matrix.Translation((0.0, 0.0, -drop))
    stem = [(0.001, -1.3), (0.07, -1.26), (0.11, -1.16), (0.05, -1.06), (0.04, -0.7), (0.12, -0.6), (0.05, -0.5), (0.035, -0.1), (0.09, -0.04), (0.02, 0.0)]

    lathe(b, [(0.14, -0.06), (0.1, -0.02), (0.1, 0.0)], 10, "metal", GILT, frame)
    b.cylinder((0.0, 0.0, -drop), 0.015, drop, 6, "metal", srgb(GILT_DEEP), frame=frame)
    lathe(b, stem, 10, "metal", GILT, body)

    for radius, height, candles in CHANDELIER_TIERS:
        chandelier_tier(b, body, radius, height, candles)


PROPS = {
    "grand_chandelier": {"build": grand_chandelier, "size": (2.0, 2.0, 2.2), "solid": False, "hang": True, "light": ((0.0, 0.0, -1.6), "FFC873", 2.2, 11.0)},
    "painting": {"build": painting, "size": (1.8, 0.08, 3.0), "solid": False, "variants": list(SCENES)},
    "wall_mirror": {"build": wall_mirror, "size": (1.1, 0.08, 3.4), "solid": False},
    "console_table": {"build": console_table, "size": (1.3, 0.44, 1.4), "solid": True, "clearance": 0.6},
    "pedestal_urn": {"build": pedestal_urn, "size": (0.56, 0.56, 1.7), "solid": True},
    "long_case_clock": {"build": long_case_clock, "size": (0.6, 0.36, 2.4), "solid": True},
    "piano": {"build": piano, "size": (1.6, 1.3, 1.3), "solid": True, "clearance": 0.8},
}
