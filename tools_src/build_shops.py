"""Model the RPG shop dressings and export them to art/town/shops/.

Every trade gets a hanging sign that build_hub_scene.py fixes beside the shop doors:
  shop_<type>_sign.gltf   wrought-iron bracket with a round hanging board and a chunky emblem (origin: wall mount)

Blender coords: the house wall is the plane Y = 0 and the street is toward -Y. Everything is modelled from
primitives (no third-party meshes). Meshes named *-colonly become collision in Godot.

Usage (after build_cathedral.py):
  blender -b --factory-startup -P tools_src/build_shops.py -- [shop_type ...]
"""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Euler

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_cathedral import (  # noqa: E402
    OUTPUT_DIR,
    make_box,
    make_cylinder,
    make_plain_material,
    make_span,
    make_sphere,
    merge_meshes_by_material,
)

SHOP_DIR = OUTPUT_DIR / "shops"
SIGN_CENTER = (-0.72, 2.72)  # (y, z) of the hanging board
SIGN_THICKNESS = 0.14
CREAM = (0.93, 0.88, 0.76)


# ---------- helpers ----------

def build_shop_materials(shop_color: tuple) -> dict:
    return {
        "wood": make_painted_material("M_ShopWood", (0.3, 0.18, 0.1), 0.0, 0.75),
        "wood_light": make_painted_material("M_ShopWoodLight", (0.58, 0.42, 0.25), 0.0, 0.8),
        "iron": make_painted_material("M_ShopIron", (0.07, 0.07, 0.09), 0.8, 0.5),
        "steel": make_painted_material("M_ShopSteel", (0.62, 0.65, 0.7), 0.9, 0.35),
        "gold": make_painted_material("M_ShopGold", (0.95, 0.72, 0.28), 1.0, 0.3),
        "cloth": make_painted_material("M_ShopCloth", shop_color, 0.0, 0.85),
        "cream": make_painted_material("M_ShopCream", CREAM, 0.0, 0.85),
        "bread": make_painted_material("M_ShopBread", (0.78, 0.52, 0.24), 0.0, 0.8),
        "leather": make_painted_material("M_ShopLeather", (0.42, 0.24, 0.12), 0.0, 0.7),
        "green": make_painted_material("M_ShopGreen", (0.2, 0.5, 0.25), 0.0, 0.8),
        "red": make_painted_material("M_ShopRed", (0.7, 0.16, 0.14), 0.0, 0.7),
        "blue": make_painted_material("M_ShopBlue", (0.18, 0.3, 0.66), 0.0, 0.7),
        "crystal": make_glow_material("M_ShopCrystal", (0.3, 0.8, 1.0), 1.1),
        "violet": make_glow_material("M_ShopViolet", (0.66, 0.36, 1.0), 1.1),
        "potion_green": make_glow_material("M_ShopPotionGreen", (0.35, 1.0, 0.35), 0.8),
        "potion_blue": make_glow_material("M_ShopPotionBlue", (0.3, 0.5, 1.0), 0.8),
    }


def linear_color(srgb_color: tuple) -> tuple:
    """Colours in this file are picked in sRGB (what the eye sees); glTF factors are linear."""
    return tuple(channel ** 2.2 for channel in srgb_color)


def make_painted_material(name: str, srgb_color: tuple, metallic: float, roughness: float):
    return make_plain_material(name, linear_color(srgb_color), metallic, roughness)


def make_glow_material(name: str, color: tuple, strength: float):
    material = make_painted_material(name, color, 0.0, 0.3)
    shader = material.node_tree.nodes["Principled BSDF"]

    shader.inputs["Emission Color"].default_value = (*linear_color(color), 1.0)
    shader.inputs["Emission Strength"].default_value = strength

    return material


def turned(mesh_object, x_degrees: float = 0.0, y_degrees: float = 0.0, z_degrees: float = 0.0):
    mesh_object.rotation_euler = (math.radians(x_degrees), math.radians(y_degrees), math.radians(z_degrees))

    return mesh_object


def make_tilted_box(name: str, center: tuple, size: tuple, material, x_degrees: float = 0.0, y_degrees: float = 0.0, z_degrees: float = 0.0):
    box = make_box(name, (0, 0, 0), size, material)
    box.location = center

    return turned(box, x_degrees, y_degrees, z_degrees)


def make_lying_cylinder(name: str, center: tuple, radius: float, length: float, sides: int, material, axis: str = "X"):
    """Cylinder centred at center with its axis along X or Y."""
    cylinder = make_cylinder(name, (0, 0, -length / 2.0), radius, length, sides, material)
    cylinder.location = center

    return turned(cylinder, y_degrees=90.0) if axis == "X" else turned(cylinder, x_degrees=90.0)


def emblem_box(name: str, offset: tuple, size: tuple, material, degrees: float = 0.0, thickness: float = SIGN_THICKNESS) -> None:
    """Flat piece of an emblem: offset and size are (across, up) on the board; it shows on both faces."""
    make_tilted_box(name, (0.0, SIGN_CENTER[0] + offset[0], SIGN_CENTER[1] + offset[1]), (thickness, size[0], size[1]), material, x_degrees=degrees)


def emblem_disc(name: str, offset: tuple, radius: float, material, sides: int = 12, thickness: float = SIGN_THICKNESS):
    return make_lying_cylinder(name, (0.0, SIGN_CENTER[0] + offset[0], SIGN_CENTER[1] + offset[1]), radius, thickness, sides, material)


def emblem_anvil(materials: dict) -> None:
    emblem_box("AnvilFace", (0.0, 0.08), (0.46, 0.12), materials["steel"])
    emblem_box("AnvilHorn", (-0.26, 0.09), (0.16, 0.07), materials["steel"], degrees=-12.0)
    emblem_box("AnvilWaist", (0.0, -0.03), (0.2, 0.12), materials["steel"])
    emblem_box("AnvilFoot", (0.0, -0.13), (0.38, 0.09), materials["steel"])
    emblem_box("HammerHandle", (0.1, 0.22), (0.3, 0.04), materials["wood_light"], degrees=-30.0)
    emblem_box("HammerHead", (0.22, 0.29), (0.1, 0.16), materials["iron"], degrees=-30.0)


def emblem_shield(materials: dict) -> None:
    emblem_disc("ShieldBody", (0.0, 0.03), 0.27, materials["blue"], sides=6)
    emblem_box("ShieldPale", (0.0, 0.03), (0.07, 0.46), materials["gold"])
    emblem_box("ShieldFess", (0.0, 0.07), (0.44, 0.07), materials["gold"])
    emblem_disc("ShieldBoss", (0.0, 0.07), 0.07, materials["steel"], thickness=SIGN_THICKNESS + 0.06)


def emblem_star(materials: dict) -> None:
    for ray_index in range(4):
        emblem_box(f"StarRay{ray_index}", (0.0, 0.0), (0.52 if ray_index % 2 == 0 else 0.34, 0.07), materials["crystal"], degrees=ray_index * 45.0)

    emblem_disc("StarCore", (0.0, 0.0), 0.1, materials["violet"], thickness=SIGN_THICKNESS + 0.06)


def emblem_flask(materials: dict) -> None:
    emblem_disc("FlaskBody", (0.0, -0.07), 0.19, materials["potion_green"])
    emblem_box("FlaskNeck", (0.0, 0.14), (0.1, 0.2), materials["cream"])
    emblem_box("FlaskLip", (0.0, 0.25), (0.17, 0.04), materials["cream"])
    emblem_disc("FlaskBubble", (0.12, 0.3), 0.035, materials["potion_green"], sides=8)


def emblem_mug(materials: dict) -> None:
    emblem_box("MugBody", (-0.04, -0.03), (0.28, 0.34), materials["wood_light"])
    emblem_box("MugHoopTop", (-0.04, 0.08), (0.3, 0.04), materials["iron"])
    emblem_box("MugHoopLow", (-0.04, -0.14), (0.3, 0.04), materials["iron"])
    emblem_box("MugHandleOut", (0.19, -0.03), (0.05, 0.22), materials["wood_light"])
    emblem_box("MugHandleTop", (0.15, 0.07), (0.1, 0.05), materials["wood_light"])
    emblem_box("MugHandleLow", (0.15, -0.13), (0.1, 0.05), materials["wood_light"])
    emblem_disc("MugFoamA", (-0.11, 0.17), 0.08, materials["cream"], sides=8)
    emblem_disc("MugFoamB", (0.02, 0.19), 0.09, materials["cream"], sides=8)


def emblem_bed(materials: dict) -> None:
    emblem_box("BedFrame", (0.0, -0.1), (0.5, 0.07), materials["wood_light"])
    emblem_box("BedHead", (-0.23, 0.0), (0.06, 0.3), materials["wood_light"])
    emblem_box("BedFoot", (0.23, -0.08), (0.06, 0.16), materials["wood_light"])
    emblem_box("BedBlanket", (0.04, -0.03), (0.34, 0.09), materials["red"])
    emblem_box("BedPillow", (-0.15, -0.01), (0.1, 0.09), materials["cream"])
    emblem_disc("BedMoon", (0.12, 0.2), 0.08, materials["gold"], sides=10)


def emblem_swords(materials: dict) -> None:
    for sword_index, degrees in enumerate((45.0, -45.0)):
        side = 1.0 if sword_index == 0 else -1.0
        emblem_box(f"SwordBlade{sword_index}", (-side * 0.03, 0.03), (0.06, 0.5), materials["steel"], degrees=degrees)
        emblem_box(f"SwordGuard{sword_index}", (side * 0.12, -0.12), (0.2, 0.04), materials["gold"], degrees=degrees)
        emblem_box(f"SwordGrip{sword_index}", (side * 0.17, -0.17), (0.045, 0.12), materials["leather"], degrees=degrees)


def emblem_loaf(materials: dict) -> None:
    emblem_disc("LoafMiddle", (0.0, 0.0), 0.17, materials["bread"], sides=10)
    emblem_disc("LoafLeft", (-0.14, -0.01), 0.14, materials["bread"], sides=10)
    emblem_disc("LoafRight", (0.14, -0.01), 0.14, materials["bread"], sides=10)

    for slash_index in range(3):
        emblem_box(f"LoafSlash{slash_index}", (-0.12 + 0.12 * slash_index, 0.03), (0.03, 0.16), materials["cream"], degrees=-25.0)


def emblem_spool(materials: dict) -> None:
    emblem_box("SpoolThread", (0.0, 0.0), (0.26, 0.26), materials["red"])
    emblem_box("SpoolTop", (0.0, 0.16), (0.36, 0.06), materials["wood_light"])
    emblem_box("SpoolBottom", (0.0, -0.16), (0.36, 0.06), materials["wood_light"])
    emblem_box("Needle", (0.0, 0.0), (0.03, 0.56), materials["steel"], degrees=-50.0)


def emblem_gem(materials: dict) -> None:
    emblem_disc("GemCrown", (0.0, 0.02), 0.23, materials["crystal"], sides=6)
    emblem_disc("GemTable", (0.0, 0.02), 0.12, materials["cream"], sides=6, thickness=SIGN_THICKNESS + 0.05)
    emblem_box("GemRing", (0.0, -0.24), (0.2, 0.05), materials["gold"])

def emblem_sack_flask(materials: dict) -> None:
    emblem_disc("SackBody", (-0.1, -0.08), 0.21, materials["wood_light"], sides=10)
    emblem_box("SackNeck", (-0.1, 0.12), (0.13, 0.12), materials["wood_light"])
    emblem_box("SackTie", (-0.1, 0.1), (0.19, 0.035), materials["leather"], thickness=SIGN_THICKNESS + 0.04)
    emblem_box("SackTuftLeft", (-0.15, 0.2), (0.07, 0.1), materials["wood_light"], degrees=-22.0)
    emblem_box("SackTuftRight", (-0.05, 0.2), (0.07, 0.1), materials["wood_light"], degrees=22.0)
    emblem_disc("FlaskBody", (0.19, -0.11), 0.12, materials["potion_blue"], thickness=SIGN_THICKNESS + 0.06)
    emblem_box("FlaskNeck", (0.19, 0.03), (0.06, 0.12), materials["cream"], thickness=SIGN_THICKNESS + 0.06)
    emblem_box("FlaskLip", (0.19, 0.1), (0.11, 0.03), materials["cream"], thickness=SIGN_THICKNESS + 0.06)


def emblem_coin(materials: dict) -> None:
    emblem_disc("CoinEdge", (0.0, 0.0), 0.28, materials["leather"], sides=16)
    emblem_disc("CoinFace", (0.0, 0.0), 0.22, materials["gold"], sides=16, thickness=SIGN_THICKNESS + 0.04)
    emblem_box("CoinBar", (0.0, 0.0), (0.06, 0.3), materials["leather"], thickness=SIGN_THICKNESS + 0.08)
    emblem_box("CoinBarTop", (0.0, 0.09), (0.2, 0.05), materials["leather"], thickness=SIGN_THICKNESS + 0.08)
    emblem_box("CoinBarLow", (0.0, -0.09), (0.2, 0.05), materials["leather"], thickness=SIGN_THICKNESS + 0.08)


def emblem_book(materials: dict) -> None:
    for side_name, side in (("Left", -1.0), ("Right", 1.0)):
        emblem_box(f"BookCover{side_name}", (side * 0.15, -0.01), (0.3, 0.4), materials["leather"], degrees=-side * 8.0)
        emblem_box(f"BookPage{side_name}", (side * 0.14, 0.0), (0.25, 0.34), materials["cream"], degrees=-side * 8.0, thickness=SIGN_THICKNESS + 0.04)

        for line_index in range(4):
            emblem_box(f"BookLine{side_name}{line_index}", (side * 0.14, 0.11 - 0.07 * line_index), (0.17, 0.015), materials["wood"], degrees=-side * 8.0, thickness=SIGN_THICKNESS + 0.07)

    emblem_box("BookSpine", (0.0, -0.01), (0.04, 0.4), materials["leather"], thickness=SIGN_THICKNESS + 0.06)
    emblem_box("BookRibbon", (0.0, -0.25), (0.045, 0.14), materials["red"])


def emblem_leaf(materials: dict) -> None:
    tilt = -35.0
    center = (0.02, 0.04)
    turn = math.radians(tilt)

    def on_leaf(local: tuple) -> tuple:
        """Leaf-local (across, along) position -> board offset."""
        return (
            center[0] + local[0] * math.cos(turn) - local[1] * math.sin(turn),
            center[1] + local[0] * math.sin(turn) + local[1] * math.cos(turn),
        )

    body = emblem_disc("LeafBody", center, 0.17, materials["green"], sides=16)
    body.scale = (1.75, 1.0, 1.0)
    body.rotation_euler = (Euler((turn, 0.0, 0.0)).to_matrix() @ Euler((0.0, math.radians(90.0), 0.0)).to_matrix()).to_euler()

    emblem_box("LeafStem", on_leaf((0.0, -0.33)), (0.04, 0.16), materials["wood_light"], degrees=tilt)
    emblem_box("LeafRib", on_leaf((0.0, 0.0)), (0.03, 0.52), materials["cream"], degrees=tilt, thickness=SIGN_THICKNESS + 0.04)

    for vein_index, vein_along in enumerate((-0.14, -0.02, 0.1)):
        for side_name, side in (("Left", -1.0), ("Right", 1.0)):
            emblem_box(f"LeafVein{side_name}{vein_index}", on_leaf((side * 0.06, vein_along + 0.04)), (0.02, 0.15), materials["cream"], degrees=tilt - side * 55.0, thickness=SIGN_THICKNESS + 0.04)

def build_sign(shop: dict, materials: dict) -> None:
    board_y, board_z = SIGN_CENTER

    make_span("BracketArm", (-0.025, -1.25, 3.3), (0.025, 0.0, 3.35), materials["iron"])
    make_tilted_box("BracketBrace", (0.0, -0.36, 3.0), (0.035, 0.035, 0.95), materials["iron"], x_degrees=-48.0)
    make_span("BracketPlate", (-0.08, -0.03, 2.55), (0.08, 0.0, 3.45), materials["iron"])
    make_sphere("BracketTip", (0.0, -1.27, 3.325), 0.06, materials["iron"])
    make_lying_cylinder("BracketScroll", (0.0, -1.05, 3.2), 0.1, 0.03, 10, materials["iron"])

    for chain_y in (board_y - 0.24, board_y + 0.24):
        make_span(f"Chain{chain_y:.2f}", (-0.012, chain_y - 0.012, board_z + 0.4), (0.012, chain_y + 0.012, 3.3), materials["iron"])

    make_lying_cylinder("BoardRim", (0.0, board_y, board_z), 0.5, 0.05, 16, materials["iron"])
    make_lying_cylinder("BoardFace", (0.0, board_y, board_z), 0.45, 0.08, 16, materials["cream"])
    make_lying_cylinder("BoardBand", (0.0, board_y, board_z), 0.47, 0.065, 16, materials["cloth"])
    shop["emblem"](materials)


# ---------- catalogue and export ----------

SHOPS = {  # type -> sign colour and emblem builder
    "smith": {"color": (0.5, 0.14, 0.1), "emblem": emblem_anvil},
    "armor": {"color": (0.16, 0.26, 0.52), "emblem": emblem_shield},
    "magic": {"color": (0.36, 0.2, 0.58), "emblem": emblem_star},
    "alchemy": {"color": (0.16, 0.44, 0.3), "emblem": emblem_flask},
    "tavern": {"color": (0.66, 0.4, 0.12), "emblem": emblem_mug},
    "inn": {"color": (0.12, 0.38, 0.46), "emblem": emblem_bed},
    "guild": {"color": (0.62, 0.12, 0.2), "emblem": emblem_swords},
    "bakery": {"color": (0.8, 0.56, 0.2), "emblem": emblem_loaf},
    "tailor": {"color": (0.7, 0.3, 0.5), "emblem": emblem_spool},
    "jeweler": {"color": (0.1, 0.4, 0.4), "emblem": emblem_gem},
    "general": {"color": (0.5, 0.4, 0.22), "emblem": emblem_sack_flask},
    "bank": {"color": (0.2, 0.32, 0.18), "emblem": emblem_coin},
    "bookshop": {"color": (0.38, 0.16, 0.3), "emblem": emblem_book},
    "herbalist": {"color": (0.45, 0.58, 0.18), "emblem": emblem_leaf},
}
def build_shop_sign(shop_type: str) -> Path:
    output_path = SHOP_DIR / f"shop_{shop_type}_sign.gltf"
    shop = SHOPS[shop_type]

    bpy.ops.wm.read_factory_settings(use_empty=True)

    materials = build_shop_materials(shop["color"])
    build_sign(shop, materials)
    bpy.context.view_layer.update()
    merge_meshes_by_material(f"Shop{shop_type.title()}Sign")

    SHOP_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_yup=True)

    return output_path


if __name__ == "__main__":
    script_arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    for requested_shop in script_arguments or list(SHOPS):
        print(f"BUILT {requested_shop} sign -> {build_shop_sign(requested_shop)}")
