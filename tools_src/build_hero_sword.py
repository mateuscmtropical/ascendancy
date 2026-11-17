"""Model the adventurer's longsword (art/props/hero_sword.gltf): the shop sword of shop_props_arms.py at hero size,
with a cyan glowing jewel in the guard. Origin at the middle of the grip, blade along +Z (glTF: +Y), flat side
facing -Y; the promo director hangs it on the right hand bone.

Usage:
  blender -b --factory-startup -P tools_src/build_hero_sword.py
"""

import sys
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_town_houses as town  # noqa: E402
from shop_props_arms import sword  # noqa: E402

LENGTH = 1.05
WIDTH = 0.055
GRIP_MIDDLE = WIDTH * 0.42 * 1.6 + LENGTH * 0.16 / 2.0  # sword(): pommel * 1.6 + metade do cabo
OUTPUT = town.PROJECT_DIR / "art" / "props" / "hero_sword.gltf"


if __name__ == "__main__":
    builder = town.Builder("hero_sword")
    sword(builder, Matrix.Translation((0.0, 0.0, -GRIP_MIDDLE)), LENGTH, width=WIDTH, jewel="glow_cyan")
    sidecar = builder.finish(OUTPUT, {"length": LENGTH})
    print(f"BUILT hero_sword: aabb {sidecar['aabb_min']} .. {sidecar['aabb_max']}")
