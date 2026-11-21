"""Props of the adventurers' guild and its bank (guild_layout.py): the standing writing desk of the banking hall.

Prop contract of shop_props_common: origin at the middle of the footprint on the floor, front toward -Y, back toward
+Y, z up. Runs inside Blender, imported by build_market_shops.py.
"""

import sys
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import Builder  # noqa: E402
from shop_props_arcane import BRASS, PARCHMENT, box, cyl, rod  # noqa: E402
from shop_props_food import WALNUT  # noqa: E402

MARBLE = "E6E0D4"
INK = "1E2333"
DESK_LEGS = ((-0.7, -0.25), (0.7, -0.25), (-0.7, 0.25), (0.7, 0.25))
SLIP_XS = (-0.45, 0.05, 0.5)


def check_desk(b: Builder, frame: Matrix, **options) -> None:
    """Standing desk in the middle of a banking hall: turned legs, a marble top, a brass rail with the slip rack,
    inkwells and pens, deposit slips laid out."""
    for x, y in DESK_LEGS:
        cyl(b, frame, (x, y, 0.0), 0.05, 1.02, "wood", WALNUT, sides=6)

    box(b, frame, (-0.78, -0.33, 0.25), (0.78, 0.33, 0.3), "wood", WALNUT)
    box(b, frame, (-0.8, -0.35, 1.02), (0.8, 0.35, 1.08), "paint", MARBLE)
    rod(b, frame, (-0.78, 0.0, 1.08), (-0.78, 0.0, 1.32), 0.02, "metal", BRASS)
    rod(b, frame, (0.78, 0.0, 1.08), (0.78, 0.0, 1.32), 0.02, "metal", BRASS)
    rod(b, frame, (-0.78, 0.0, 1.32), (0.78, 0.0, 1.32), 0.02, "metal", BRASS)
    box(b, frame, (-0.7, -0.02, 1.08), (0.7, 0.06, 1.24), "wood", WALNUT)

    for x in SLIP_XS:
        box(b, frame, (x - 0.13, -0.3, 1.08), (x + 0.13, -0.12, 1.083), "paint", PARCHMENT)
        cyl(b, frame, (x + 0.2, -0.16, 1.08), 0.03, 0.05, "paint", INK, sides=6)
        rod(b, frame, (x + 0.2, -0.16, 1.12), (x + 0.24, -0.1, 1.24), 0.006, "paint", INK)


PROPS = {
    "check_desk": {"build": check_desk, "size": (1.6, 0.7, 1.32), "solid": True, "clearance": 0.9},
}
