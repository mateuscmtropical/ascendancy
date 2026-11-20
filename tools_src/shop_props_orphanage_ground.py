"""Extra furniture of the ground-floor wings of the orphanage (library wing and school wing): a wall clock, a
cast-iron stove, a brass hand bell and a small side table.

Runs inside Blender, imported by build_market_shops.py. Same contract as shop_props_orphanage.py: X width centred on 0,
the front faces -Y, the back at Y = +size[1] / 2, Z up from the floor; wall props are built at their mounting height.
"""

import math
import sys
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import Builder, srgb  # noqa: E402
from shop_props_common import WOOD_DARK_UV, WOOD_LIGHT_UV, bevel_box, lathe, ring  # noqa: E402

WALNUT = "6B452C"
WALNUT_DARK = "4A2D1C"
CAST_IRON = "3A363C"
IRON_WORN = "55515A"
BRASS = "C89B45"
DIAL_CREAM = "EFE6D2"
INK = "2A2118"
CLOCK_CENTRE = 2.3
STOVE_PIPE_TOP = 2.85
HOUR_MARKS = 12


def wall_clock(b: Builder, frame: Matrix, **options) -> None:
    """Round school clock in a walnut bezel with a cream dial, hour ticks and two hands (reads ten past ten)."""
    face_y = -0.012

    b.cylinder((0.0, 0.0, CLOCK_CENTRE), 0.31, 0.05, 20, "wood", srgb(WALNUT_DARK), frame=frame, axis="Y", uv=WOOD_DARK_UV)
    ring(b, (0.0, face_y + 0.004, CLOCK_CENTRE), 0.285, 0.026, "wood", WALNUT, frame, sides=20, tube_sides=6, axis="Y")
    b.cylinder((0.0, face_y, CLOCK_CENTRE), 0.27, 0.012, 20, "paint", srgb(DIAL_CREAM), frame=frame, axis="Y")

    for mark in range(HOUR_MARKS):
        angle = math.tau * mark / HOUR_MARKS
        reach, width = (0.215, 0.014) if mark % 3 else (0.205, 0.022)
        x, z = reach * math.sin(angle), CLOCK_CENTRE + reach * math.cos(angle)

        b.box((x - width, face_y - 0.008, z - width), (x + width, face_y, z + width), "paint", srgb(INK), frame=frame)

    for length, angle, thickness in ((0.15, math.radians(-60.0), 0.016), (0.22, math.radians(60.0), 0.011)):
        tip = (length * math.sin(angle), face_y - 0.012, CLOCK_CENTRE + length * math.cos(angle))

        b.beam((0.0, face_y - 0.012, CLOCK_CENTRE), tip, thickness, 0.006, "paint", srgb(INK), frame=frame)

    b.sphere((0.0, face_y - 0.016, CLOCK_CENTRE), 0.02, "metal", srgb(BRASS), frame=frame, segments=6)


def cast_iron_stove(b: Builder, frame: Matrix, **options) -> None:
    """Pot-bellied cast-iron stove on a square base with a glowing fire door and a stovepipe that turns into the wall
    (the pipe elbow sits at the back, so place it with its back to a wall)."""
    belly = [(0.2, 0.18), (0.29, 0.3), (0.33, 0.5), (0.3, 0.75), (0.21, 0.92), (0.12, 1.0)]

    b.box((-0.34, -0.34, 0.0), (0.34, 0.34, 0.07), "metal", srgb(IRON_WORN), frame=frame)

    for leg_x, leg_y in ((-0.28, -0.28), (0.28, -0.28), (-0.28, 0.28), (0.28, 0.28)):
        b.box((leg_x - 0.025, leg_y - 0.025, 0.07), (leg_x + 0.025, leg_y + 0.025, 0.2), "metal", srgb(CAST_IRON), frame=frame)

    lathe(b, belly, 14, "metal", CAST_IRON, frame)
    lathe(b, [(0.12, 1.0), (0.06, 1.04), (0.001, 1.05)], 14, "metal", CAST_IRON, frame)
    ring(b, (0.0, 0.0, 0.3), 0.3, 0.012, "metal", IRON_WORN, frame, sides=14, tube_sides=4)
    ring(b, (0.0, 0.0, 0.84), 0.26, 0.012, "metal", IRON_WORN, frame, sides=14, tube_sides=4)

    b.box((-0.11, -0.345, 0.38), (0.11, -0.3, 0.66), "metal", srgb(IRON_WORN), frame=frame)
    b.box((-0.06, -0.352, 0.45), (0.06, -0.346, 0.58), "glow_warm", srgb("FFFFFF"), frame=frame)
    b.box((0.07, -0.352, 0.5), (0.09, -0.345, 0.56), "metal", srgb(BRASS), frame=frame)
    b.box((-0.1, -0.33, 0.22), (0.1, -0.29, 0.3), "metal", srgb(IRON_WORN), frame=frame)

    b.cylinder((0.0, 0.0, 1.04), 0.048, STOVE_PIPE_TOP - 1.04, 10, "metal", srgb(CAST_IRON), frame=frame)
    b.cylinder((0.0, 0.0, 1.9), 0.062, 0.03, 10, "metal", srgb(IRON_WORN), frame=frame)
    b.sphere((0.0, 0.0, STOVE_PIPE_TOP), 0.052, "metal", srgb(CAST_IRON), frame=frame, segments=8)
    b.cylinder((0.0, 0.0, STOVE_PIPE_TOP), 0.048, 0.43, 10, "metal", srgb(CAST_IRON), frame=frame, axis="Y")
    b.cylinder((0.0, 0.3, STOVE_PIPE_TOP), 0.07, 0.03, 10, "metal", srgb(IRON_WORN), frame=frame, axis="Y")


def brass_bell(b: Builder, frame: Matrix, **options) -> None:
    """Brass hand bell with a turned walnut handle, standing mouth down on a table or shelf."""
    bell = [(0.082, 0.0), (0.078, 0.03), (0.06, 0.08), (0.045, 0.13), (0.03, 0.16), (0.014, 0.17), (0.001, 0.17)]

    lathe(b, bell, 14, "metal", BRASS, frame)
    ring(b, (0.0, 0.0, 0.012), 0.082, 0.006, "metal", BRASS, frame, sides=14, tube_sides=4)
    lathe(b, [(0.012, 0.17), (0.02, 0.19), (0.016, 0.24), (0.024, 0.27), (0.001, 0.29)], 10, "wood", WALNUT_DARK, frame, uv=WOOD_DARK_UV)


def side_table(b: Builder, frame: Matrix, **options) -> None:
    """Small round walnut table on a turned column with three splayed feet, a doily and a closed book on top."""
    top_z = 0.66

    lathe(b, [(0.001, top_z - 0.06), (0.27, top_z - 0.06), (0.28, top_z - 0.03), (0.28, top_z), (0.001, top_z)], 18, "wood", WALNUT, frame, uv=WOOD_LIGHT_UV)
    lathe(b, [(0.03, 0.12), (0.045, 0.2), (0.025, 0.3), (0.04, 0.38), (0.026, 0.5), (0.04, top_z - 0.06)], 10, "wood", WALNUT_DARK, frame, uv=WOOD_DARK_UV)

    for foot in range(3):
        angle = math.tau * foot / 3.0
        end = (0.24 * math.cos(angle), 0.24 * math.sin(angle), 0.0)

        b.beam((0.0, 0.0, 0.16), (end[0], end[1], 0.02), 0.04, 0.03, "wood", srgb(WALNUT_DARK), frame=frame, uv=WOOD_DARK_UV)

    b.cylinder((0.0, 0.0, top_z), 0.2, 0.004, 18, "paint", srgb(DIAL_CREAM), frame=frame)
    bevel_box(b, frame, (-0.07, -0.05, top_z + 0.004), (0.08, 0.06, top_z + 0.04), "6E333A", bevel=0.004, material="paint")


PROPS = {
    "wall_clock": {"build": wall_clock, "size": (0.62, 0.1, 2.65), "solid": False},
    "cast_iron_stove": {"build": cast_iron_stove, "size": (0.72, 0.72, 2.95), "solid": True, "clearance": 0.8},
    "brass_bell": {"build": brass_bell, "size": (0.17, 0.17, 0.29), "solid": False},
    "side_table": {"build": side_table, "size": (0.58, 0.58, 0.7), "solid": True},
}
