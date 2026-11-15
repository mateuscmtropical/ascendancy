"""Model the RPG shop dressings and export them to art/town/shops/.

Every shop type gets three small models that build_hub_scene.py hangs on a row house facing the squares:
  shop_<type>_sign.gltf   wrought-iron bracket with a round hanging board and a chunky emblem (origin: wall mount)
  shop_<type>_stall.gltf  striped awning in the shop colours over a counter with its goods (origin: bay centre at the wall)
  shop_<type>_yard.gltf   the big props of the trade standing by the wall (origin: bay centre at the wall)

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
    make_cone,
    make_cylinder,
    make_plain_material,
    make_span,
    make_sphere,
    merge_meshes_by_material,
)
from build_plaza_props import make_frustum  # noqa: E402

SHOP_DIR = OUTPUT_DIR / "shops"
SIGN_CENTER = (-0.72, 2.72)  # (y, z) of the hanging board
SIGN_THICKNESS = 0.14
STALL_WIDTH = 1.8
STALL_DEPTH = 0.9
COUNTER_HEIGHT = 0.9
CREAM = (0.93, 0.88, 0.76)


# ---------- helpers ----------

def build_shop_materials(shop_color: tuple) -> dict:
    return {
        "wood": make_painted_material("M_ShopWood", (0.3, 0.18, 0.1), 0.0, 0.75),
        "wood_light": make_painted_material("M_ShopWoodLight", (0.58, 0.42, 0.25), 0.0, 0.8),
        "iron": make_painted_material("M_ShopIron", (0.07, 0.07, 0.09), 0.8, 0.5),
        "steel": make_painted_material("M_ShopSteel", (0.62, 0.65, 0.7), 0.9, 0.35),
        "gold": make_painted_material("M_ShopGold", (0.95, 0.72, 0.28), 1.0, 0.3),
        "stone": make_painted_material("M_ShopStone", (0.55, 0.52, 0.5), 0.0, 0.9),
        "brick": make_painted_material("M_ShopBrick", (0.52, 0.25, 0.18), 0.0, 0.9),
        "cloth": make_painted_material("M_ShopCloth", shop_color, 0.0, 0.85),
        "cream": make_painted_material("M_ShopCream", CREAM, 0.0, 0.85),
        "bread": make_painted_material("M_ShopBread", (0.78, 0.52, 0.24), 0.0, 0.8),
        "leather": make_painted_material("M_ShopLeather", (0.42, 0.24, 0.12), 0.0, 0.7),
        "green": make_painted_material("M_ShopGreen", (0.2, 0.5, 0.25), 0.0, 0.8),
        "red": make_painted_material("M_ShopRed", (0.7, 0.16, 0.14), 0.0, 0.7),
        "blue": make_painted_material("M_ShopBlue", (0.18, 0.3, 0.66), 0.0, 0.7),
        "ember": make_glow_material("M_ShopEmber", (1.0, 0.38, 0.08), 1.8),
        "crystal": make_glow_material("M_ShopCrystal", (0.3, 0.8, 1.0), 1.1),
        "violet": make_glow_material("M_ShopViolet", (0.66, 0.36, 1.0), 1.1),
        "potion_red": make_glow_material("M_ShopPotionRed", (1.0, 0.2, 0.25), 0.8),
        "potion_green": make_glow_material("M_ShopPotionGreen", (0.35, 1.0, 0.35), 0.8),
        "potion_blue": make_glow_material("M_ShopPotionBlue", (0.3, 0.5, 1.0), 0.8),
        "lamp": make_glow_material("M_ShopLamp", (1.0, 0.85, 0.55), 1.4),
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


def make_barrel(name: str, base: tuple, radius: float, height: float, materials: dict) -> None:
    make_frustum(f"{name}Lower", base[2], radius * 0.84, radius, height / 2.0, 12, materials["wood_light"]).location[:2] = base[:2]
    make_frustum(f"{name}Upper", base[2] + height / 2.0, radius, radius * 0.84, height / 2.0, 12, materials["wood_light"]).location[:2] = base[:2]

    for hoop_index, hoop_height in enumerate((0.14, 0.5, 0.86)):
        hoop_radius = radius * (0.9 if hoop_index != 1 else 1.02)
        make_cylinder(f"{name}Hoop{hoop_index}", (base[0], base[1], base[2] + height * hoop_height - 0.02), hoop_radius, 0.04, 12, materials["iron"])


def make_bottle(name: str, base: tuple, radius: float, material, materials: dict) -> None:
    make_sphere(f"{name}Body", (base[0], base[1], base[2] + radius * 0.9), radius, material)
    make_cylinder(f"{name}Neck", (base[0], base[1], base[2] + radius * 1.6), radius * 0.3, radius * 0.9, 8, materials["cream"])
    make_cylinder(f"{name}Cork", (base[0], base[1], base[2] + radius * 2.5), radius * 0.34, radius * 0.3, 8, materials["leather"])


# ---------- sign ----------

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


# ---------- stall ----------

def build_stall(shop: dict, materials: dict) -> None:
    half = STALL_WIDTH / 2.0
    stripe_count = 6
    stripe_width = STALL_WIDTH / stripe_count
    awning_tilt = math.degrees(math.atan2(0.4, 1.15))

    make_span("CounterTop", (-half, -STALL_DEPTH, COUNTER_HEIGHT - 0.06), (half, -0.12, COUNTER_HEIGHT), materials["wood_light"])
    make_span("CounterFront", (-half + 0.05, -STALL_DEPTH + 0.06, 0.1), (half - 0.05, -STALL_DEPTH + 0.1, COUNTER_HEIGHT - 0.06), materials["wood"])
    make_span("CounterSkirt", (-half + 0.05, -STALL_DEPTH + 0.04, COUNTER_HEIGHT - 0.3), (half - 0.05, -STALL_DEPTH + 0.06, COUNTER_HEIGHT - 0.06), materials["cloth"])
    make_span("Stall-colonly", (-half, -STALL_DEPTH, 0.0), (half, 0.0, 1.2), None)

    for side_sign in (-1, 1):
        make_span(f"CounterLeg{side_sign:+d}", (side_sign * half - 0.05, -STALL_DEPTH, 0.0), (side_sign * half + 0.05, -STALL_DEPTH + 0.1, 2.12), materials["wood"])
        make_span(f"CounterSide{side_sign:+d}", (side_sign * (half - 0.03) - 0.02, -STALL_DEPTH + 0.1, 0.1), (side_sign * (half - 0.03) + 0.02, -0.12, COUNTER_HEIGHT - 0.06), materials["wood"])

    make_span("AwningBeam", (-half - 0.05, -STALL_DEPTH - 0.02, 2.1), (half + 0.05, -STALL_DEPTH + 0.06, 2.16), materials["wood"])

    for stripe_index in range(stripe_count):
        stripe_x = -half + stripe_width * (stripe_index + 0.5)
        stripe_material = materials["cloth"] if stripe_index % 2 == 0 else materials["cream"]
        make_tilted_box(f"AwningStripe{stripe_index}", (stripe_x, -0.55, 2.38), (stripe_width, 1.22, 0.03), stripe_material, x_degrees=awning_tilt)
        make_span(f"AwningValance{stripe_index}", (stripe_x - stripe_width / 2.0, -1.14, 2.0 + 0.04 * (stripe_index % 2)), (stripe_x + stripe_width / 2.0, -1.11, 2.19), stripe_material)

    shop["goods"](materials)


def goods_smith(materials: dict) -> None:
    for ingot_index in range(4):
        make_box(f"Ingot{ingot_index}", (-0.6 + 0.16 * (ingot_index % 2) + 0.08 * (ingot_index // 2), -0.5, COUNTER_HEIGHT + 0.03 + 0.06 * (ingot_index // 2)), (0.14, 0.3, 0.06), materials["steel"])

    make_tilted_box("HammerHandle", (0.1, -0.5, COUNTER_HEIGHT + 0.03), (0.42, 0.04, 0.04), materials["wood"], z_degrees=20.0)
    make_tilted_box("HammerHead", (0.3, -0.43, COUNTER_HEIGHT + 0.05), (0.1, 0.2, 0.1), materials["iron"], z_degrees=20.0)

    for shoe_index in range(3):
        make_cylinder(f"Horseshoe{shoe_index}", (0.62, -0.62 + 0.2 * shoe_index, COUNTER_HEIGHT), 0.08, 0.025, 8, materials["iron"])


def goods_armor(materials: dict) -> None:
    for helmet_index, helmet_x in enumerate((-0.55, 0.0, 0.55)):
        make_cylinder(f"HelmetStand{helmet_index}", (helmet_x, -0.5, COUNTER_HEIGHT), 0.06, 0.12, 8, materials["wood"])
        make_sphere(f"Helmet{helmet_index}", (helmet_x, -0.5, COUNTER_HEIGHT + 0.26), 0.17, materials["steel"])
        make_box(f"HelmetCrest{helmet_index}", (helmet_x, -0.5, COUNTER_HEIGHT + 0.42), (0.04, 0.3, 0.08), materials["red" if helmet_index == 1 else "gold"])
        make_box(f"HelmetVisor{helmet_index}", (helmet_x, -0.66, COUNTER_HEIGHT + 0.25), (0.2, 0.03, 0.05), materials["iron"])


def goods_magic(materials: dict) -> None:
    make_cylinder("OrbStand", (0.0, -0.5, COUNTER_HEIGHT), 0.11, 0.1, 10, materials["gold"])
    make_sphere("Orb", (0.0, -0.5, COUNTER_HEIGHT + 0.26), 0.17, materials["violet"])

    for crystal_index, (crystal_x, crystal_y, height) in enumerate([(-0.62, -0.5, 0.34), (-0.5, -0.62, 0.22), (-0.72, -0.64, 0.18), (0.55, -0.45, 0.3), (0.68, -0.6, 0.2)]):
        make_cone(f"Crystal{crystal_index}", (crystal_x, crystal_y, COUNTER_HEIGHT), 0.06, height, 6, materials["crystal"], top_radius=0.015)

    make_tilted_box("SpellBook", (0.42, -0.72, COUNTER_HEIGHT + 0.035), (0.24, 0.18, 0.07), materials["blue"], z_degrees=18.0)


def goods_alchemy(materials: dict) -> None:
    colors = ["potion_red", "potion_green", "potion_blue"]

    make_span("PotionShelf", (-0.8, -0.3, COUNTER_HEIGHT + 0.3), (0.8, -0.14, COUNTER_HEIGHT + 0.34), materials["wood"])

    for bottle_index in range(6):
        make_bottle(f"Potion{bottle_index}", (-0.66 + 0.26 * bottle_index, -0.62 + 0.08 * (bottle_index % 2), COUNTER_HEIGHT), 0.08, materials[colors[bottle_index % 3]], materials)

    for bottle_index in range(5):
        make_bottle(f"ShelfPotion{bottle_index}", (-0.6 + 0.3 * bottle_index, -0.22, COUNTER_HEIGHT + 0.34), 0.06, materials[colors[(bottle_index + 1) % 3]], materials)


def goods_tavern(materials: dict) -> None:
    for mug_index, mug_x in enumerate((-0.6, -0.36, 0.5)):
        make_cylinder(f"Mug{mug_index}", (mug_x, -0.58, COUNTER_HEIGHT), 0.07, 0.16, 10, materials["wood_light"])
        make_cylinder(f"MugFoam{mug_index}", (mug_x, -0.58, COUNTER_HEIGHT + 0.16), 0.065, 0.03, 10, materials["cream"])
        make_box(f"MugHandle{mug_index}", (mug_x + 0.09, -0.58, COUNTER_HEIGHT + 0.08), (0.04, 0.03, 0.1), materials["wood_light"])

    make_lying_cylinder("Keg", (0.05, -0.4, COUNTER_HEIGHT + 0.2), 0.18, 0.42, 12, materials["wood_light"])
    make_lying_cylinder("KegHoopA", (-0.1, -0.4, COUNTER_HEIGHT + 0.2), 0.19, 0.03, 12, materials["iron"])
    make_lying_cylinder("KegHoopB", (0.2, -0.4, COUNTER_HEIGHT + 0.2), 0.19, 0.03, 12, materials["iron"])
    make_span("KegCradle", (-0.18, -0.55, COUNTER_HEIGHT), (0.28, -0.25, COUNTER_HEIGHT + 0.05), materials["wood"])
    make_bottle("Wine", (0.72, -0.4, COUNTER_HEIGHT), 0.07, materials["green"], materials)


def goods_inn(materials: dict) -> None:
    make_span("KeyBoard", (-0.7, -0.2, COUNTER_HEIGHT + 0.25), (0.1, -0.16, COUNTER_HEIGHT + 0.75), materials["wood"])

    for key_index in range(6):
        key_x = -0.6 + 0.24 * (key_index % 3)
        key_z = COUNTER_HEIGHT + 0.62 - 0.22 * (key_index // 3)
        make_box(f"Key{key_index}", (key_x, -0.22, key_z), (0.03, 0.02, 0.12), materials["gold"])
        make_lying_cylinder(f"KeyBow{key_index}", (key_x, -0.22, key_z + 0.08), 0.035, 0.02, 8, materials["gold"], axis="Y")

    make_span("Ledger", (-0.2, -0.75, COUNTER_HEIGHT), (0.2, -0.45, COUNTER_HEIGHT + 0.05), materials["leather"])
    make_span("LedgerPages", (-0.18, -0.73, COUNTER_HEIGHT + 0.05), (0.18, -0.47, COUNTER_HEIGHT + 0.065), materials["cream"])
    make_cylinder("CandleDish", (0.6, -0.55, COUNTER_HEIGHT), 0.09, 0.02, 10, materials["gold"])
    make_cylinder("Candle", (0.6, -0.55, COUNTER_HEIGHT + 0.02), 0.03, 0.16, 8, materials["cream"])
    make_cone("CandleFlame", (0.6, -0.55, COUNTER_HEIGHT + 0.18), 0.022, 0.07, 6, materials["lamp"])


def goods_guild(materials: dict) -> None:
    for scroll_index in range(5):
        make_lying_cylinder(f"Scroll{scroll_index}", (-0.5 + 0.03 * (scroll_index % 2), -0.7 + 0.11 * scroll_index, COUNTER_HEIGHT + 0.04), 0.04, 0.4, 8, materials["cream"])

    make_span("QuestSheetA", (0.05, -0.75, COUNTER_HEIGHT), (0.35, -0.38, COUNTER_HEIGHT + 0.01), materials["cream"])
    make_tilted_box("QuestSheetB", (0.5, -0.5, COUNTER_HEIGHT + 0.012), (0.3, 0.38, 0.01), materials["cream"], z_degrees=20.0)
    make_sphere("WaxSeal", (0.2, -0.45, COUNTER_HEIGHT + 0.01), 0.035, materials["red"])
    make_cylinder("InkWell", (0.75, -0.7, COUNTER_HEIGHT), 0.045, 0.07, 8, materials["iron"])
    make_tilted_box("Quill", (0.75, -0.68, COUNTER_HEIGHT + 0.18), (0.015, 0.05, 0.3), materials["cream"], x_degrees=18.0)
    make_span("CoinStackA", (-0.1, -0.3, COUNTER_HEIGHT), (-0.02, -0.22, COUNTER_HEIGHT + 0.07), materials["gold"])
    make_span("CoinStackB", (0.0, -0.3, COUNTER_HEIGHT), (0.08, -0.22, COUNTER_HEIGHT + 0.04), materials["gold"])


def goods_bakery(materials: dict) -> None:
    make_span("BreadTray", (-0.8, -0.8, COUNTER_HEIGHT), (0.1, -0.3, COUNTER_HEIGHT + 0.03), materials["wood"])

    for loaf_index in range(6):
        loaf = make_sphere(f"Loaf{loaf_index}", (-0.65 + 0.28 * (loaf_index % 3), -0.66 + 0.24 * (loaf_index // 3), COUNTER_HEIGHT + 0.09), 0.1, materials["bread"])
        loaf.scale = (1.25, 0.85, 0.7)

    for baguette_index in range(4):
        make_tilted_box(f"Baguette{baguette_index}", (0.45 + 0.09 * baguette_index, -0.45, COUNTER_HEIGHT + 0.3), (0.07, 0.07, 0.62), materials["bread"], x_degrees=12.0, y_degrees=4.0 * baguette_index - 6.0)

    make_frustum("BaguetteBasket", COUNTER_HEIGHT, 0.2, 0.26, 0.26, 10, materials["leather"]).location[:2] = (0.58, -0.5)


def goods_tailor(materials: dict) -> None:
    bolt_colors = ["red", "blue", "green", "cream", "cloth", "leather"]

    for bolt_index, color_key in enumerate(bolt_colors):
        layer = bolt_index // 3
        make_lying_cylinder(f"ClothBolt{bolt_index}", (-0.25, -0.68 + 0.2 * (bolt_index % 3) + 0.1 * layer, COUNTER_HEIGHT + 0.09 + 0.16 * layer), 0.09, 0.9, 10, materials[color_key])

    make_cylinder("ThreadSpoolA", (0.55, -0.6, COUNTER_HEIGHT), 0.06, 0.12, 8, materials["red"])
    make_cylinder("ThreadSpoolB", (0.7, -0.45, COUNTER_HEIGHT), 0.06, 0.12, 8, materials["blue"])
    make_tilted_box("Shears", (0.5, -0.3, COUNTER_HEIGHT + 0.01), (0.3, 0.05, 0.02), materials["steel"], z_degrees=30.0)


def goods_jeweler(materials: dict) -> None:
    gem_colors = ["crystal", "potion_red", "potion_green", "violet", "potion_blue", "lamp"]

    make_span("VelvetTray", (-0.75, -0.78, COUNTER_HEIGHT), (0.75, -0.3, COUNTER_HEIGHT + 0.05), materials["cloth"])
    make_span("TrayFrameFront", (-0.78, -0.81, COUNTER_HEIGHT), (0.78, -0.78, COUNTER_HEIGHT + 0.08), materials["gold"])
    make_span("TrayFrameBack", (-0.78, -0.3, COUNTER_HEIGHT), (0.78, -0.27, COUNTER_HEIGHT + 0.08), materials["gold"])

    for gem_index, color_key in enumerate(gem_colors):
        gem_x = -0.6 + 0.24 * gem_index
        make_cone(f"GemCrown{gem_index}", (gem_x, -0.62, COUNTER_HEIGHT + 0.09), 0.055, 0.05, 6, materials[color_key], top_radius=0.03)
        make_cone(f"GemPavilion{gem_index}", (gem_x, -0.62, COUNTER_HEIGHT + 0.05), 0.012, 0.04, 6, materials[color_key], top_radius=0.055)
        make_cylinder(f"Ring{gem_index}", (gem_x, -0.42, COUNTER_HEIGHT + 0.05), 0.04, 0.02, 10, materials["gold"])


# ---------- yard ----------

def yard_smith(materials: dict) -> None:
    make_span("ForgeBody", (-0.85, -0.85, 0.0), (0.15, -0.05, 0.95), materials["brick"])
    make_span("ForgeLip", (-0.9, -0.9, 0.95), (0.2, 0.0, 1.05), materials["stone"])
    make_span("ForgeCoals", (-0.7, -0.75, 1.05), (0.0, -0.2, 1.1), materials["ember"])
    make_span("ForgeMouth", (-0.6, -0.87, 0.3), (-0.1, -0.84, 0.7), materials["ember"])
    make_frustum("ForgeHood", 1.9, 0.62, 0.3, 0.7, 4, materials["brick"]).location[:2] = (-0.35, -0.4)
    make_span("ForgeChimney", (-0.58, -0.62, 2.6), (-0.12, -0.18, 5.2), materials["brick"])
    make_span("ForgeChimneyCap", (-0.64, -0.68, 5.2), (-0.06, -0.12, 5.32), materials["stone"])
    make_span("ForgePostA", (-0.82, -0.82, 1.05), (-0.74, -0.74, 1.95), materials["iron"])
    make_span("ForgePostB", (0.04, -0.82, 1.05), (0.12, -0.74, 1.95), materials["iron"])
    make_cylinder("AnvilStump", (0.6, -0.55, 0.0), 0.24, 0.5, 10, materials["wood"])
    make_span("AnvilFoot", (0.42, -0.67, 0.5), (0.78, -0.43, 0.58), materials["iron"])
    make_span("AnvilWaist", (0.5, -0.63, 0.58), (0.7, -0.47, 0.7), materials["iron"])
    make_span("AnvilFace", (0.36, -0.67, 0.7), (0.84, -0.43, 0.82), materials["steel"])
    make_cone("AnvilHorn", (0.0, 0.0, 0.0), 0.1, 0.26, 8, materials["steel"]).rotation_euler.y = math.radians(-90.0)
    bpy.data.objects["AnvilHorn"].location = (0.36, -0.55, 0.76)
    make_span("Yard-colonly", (-0.9, -0.9, 0.0), (0.9, 0.0, 1.6), None)


def yard_armor(materials: dict) -> None:
    make_cylinder("MannequinFoot", (-0.45, -0.5, 0.0), 0.24, 0.06, 10, materials["wood"])
    make_cylinder("MannequinPole", (-0.45, -0.5, 0.0), 0.04, 1.75, 8, materials["wood"])
    make_frustum("Cuirass", 0.95, 0.2, 0.3, 0.5, 10, materials["steel"]).location[:2] = (-0.45, -0.5)
    make_frustum("Fauld", 0.72, 0.3, 0.21, 0.24, 10, materials["steel"]).location[:2] = (-0.45, -0.5)
    make_span("CuirassTrim", (-0.47, -0.81, 0.98), (-0.43, -0.78, 1.42), materials["gold"])
    make_span("CrossArm", (-0.95, -0.53, 1.38), (0.05, -0.47, 1.44), materials["wood"])

    for side_sign in (-1, 1):
        make_sphere(f"Pauldron{side_sign:+d}", (-0.45 + side_sign * 0.34, -0.5, 1.44), 0.15, materials["steel"])

    make_sphere("Helm", (-0.45, -0.5, 1.72), 0.16, materials["steel"])
    make_box("HelmCrest", (-0.45, -0.5, 1.88), (0.04, 0.3, 0.1), materials["red"])
    make_box("HelmSlit", (-0.45, -0.65, 1.72), (0.18, 0.03, 0.04), materials["iron"])

    for shield_index, (color_key, shield_x) in enumerate((("blue", 0.3), ("red", 0.7))):
        shield = make_lying_cylinder(f"Shield{shield_index}", (shield_x, -0.2 - 0.12 * shield_index, 0.42), 0.4, 0.05, 14, materials[color_key], axis="Y")
        shield.rotation_euler.x = math.radians(90.0 - 14.0)
        make_sphere(f"ShieldBoss{shield_index}", (shield_x, -0.26 - 0.12 * shield_index, 0.43), 0.09, materials["steel"])

    make_span("Yard-colonly", (-0.9, -0.85, 0.0), (0.95, 0.0, 1.9), None)


def yard_magic(materials: dict) -> None:
    make_frustum("CrystalPot", 0.0, 0.3, 0.38, 0.35, 8, materials["stone"]).location[:2] = (-0.4, -0.5)

    for crystal_index, (offset_x, offset_y, height, lean) in enumerate([(0.0, 0.0, 1.1, 0.0), (-0.16, 0.06, 0.7, -14.0), (0.17, -0.05, 0.8, 16.0), (0.02, 0.17, 0.55, 8.0)]):
        crystal = make_cone(f"BigCrystal{crystal_index}", (0, 0, 0), 0.11, height, 6, materials["crystal" if crystal_index % 2 == 0 else "violet"], top_radius=0.02)
        crystal.location = (-0.4 + offset_x, -0.5 + offset_y, 0.3)
        crystal.rotation_euler.y = math.radians(lean)

    make_span("RuneStone", (0.3, -0.62, 0.0), (0.8, -0.38, 1.5), materials["stone"])
    make_span("RuneStoneCap", (0.36, -0.6, 1.5), (0.74, -0.4, 1.62), materials["stone"])

    for rune_index, (rune_z, rune_width) in enumerate(((1.25, 0.26), (1.0, 0.14), (0.75, 0.3), (0.5, 0.18))):
        make_box(f"Rune{rune_index}", (0.55, -0.63, rune_z), (rune_width, 0.03, 0.06), materials["crystal"])

    make_box("RuneSpine", (0.55, -0.63, 0.88), (0.05, 0.03, 0.85), materials["crystal"])
    make_span("Yard-colonly", (-0.85, -0.85, 0.0), (0.85, 0.0, 1.6), None)


def yard_alchemy(materials: dict) -> None:
    for leg_index in range(3):
        angle = math.radians(90.0 + 120.0 * leg_index)
        make_tilted_box(f"TripodLeg{leg_index}", (-0.35 + 0.3 * math.cos(angle), -0.5 + 0.3 * math.sin(angle), 0.55), (0.04, 0.04, 1.2), materials["iron"], x_degrees=-14.0 * math.sin(angle), y_degrees=14.0 * math.cos(angle))

    make_frustum("CauldronBowl", 0.25, 0.22, 0.4, 0.38, 12, materials["iron"]).location[:2] = (-0.35, -0.5)
    make_cylinder("CauldronRim", (-0.35, -0.5, 0.63), 0.43, 0.05, 12, materials["iron"])
    make_cylinder("CauldronBrew", (-0.35, -0.5, 0.6), 0.38, 0.06, 12, materials["potion_green"])
    make_sphere("BrewBubbleA", (-0.45, -0.45, 0.68), 0.06, materials["potion_green"])
    make_sphere("BrewBubbleB", (-0.25, -0.6, 0.67), 0.04, materials["potion_green"])
    make_span("CauldronEmbers", (-0.55, -0.7, 0.0), (-0.15, -0.3, 0.08), materials["ember"])
    make_span("HerbCrate", (0.3, -0.75, 0.0), (0.85, -0.3, 0.4), materials["wood_light"])

    for herb_index in range(5):
        make_cone(f"Herb{herb_index}", (0.4 + 0.1 * herb_index, -0.62 + 0.09 * (herb_index % 3), 0.38), 0.08, 0.3 + 0.05 * (herb_index % 2), 5, materials["green"])

    make_span("Yard-colonly", (-0.85, -0.9, 0.0), (0.9, 0.0, 1.2), None)


def yard_tavern(materials: dict) -> None:
    make_barrel("BarrelA", (-0.5, -0.45, 0.0), 0.34, 0.9, materials)
    make_barrel("BarrelB", (0.22, -0.4, 0.0), 0.34, 0.9, materials)
    make_barrel("BarrelTop", (-0.14, -0.42, 0.9), 0.3, 0.8, materials)
    make_cylinder("TableTop", (0.72, -0.62, 0.72), 0.3, 0.05, 10, materials["wood"])
    make_cylinder("TableLeg", (0.72, -0.62, 0.0), 0.06, 0.72, 8, materials["wood"])
    make_cylinder("TableMug", (0.66, -0.66, 0.77), 0.06, 0.14, 8, materials["wood_light"])
    make_cylinder("TableMugFoam", (0.66, -0.66, 0.91), 0.055, 0.03, 8, materials["cream"])
    make_span("Yard-colonly", (-0.9, -0.95, 0.0), (1.05, 0.0, 1.7), None)


def yard_inn(materials: dict) -> None:
    make_span("TrunkBody", (-0.85, -0.7, 0.0), (-0.05, -0.2, 0.42), materials["leather"])
    make_lying_cylinder("TrunkLid", (-0.45, -0.45, 0.42), 0.25, 0.8, 10, materials["leather"])
    make_span("TrunkBandA", (-0.7, -0.72, 0.0), (-0.64, -0.18, 0.44), materials["gold"])
    make_span("TrunkBandB", (-0.26, -0.72, 0.0), (-0.2, -0.18, 0.44), materials["gold"])
    make_span("TrunkLock", (-0.5, -0.74, 0.3), (-0.4, -0.7, 0.42), materials["gold"])
    make_cylinder("LanternPost", (0.55, -0.6, 0.0), 0.05, 2.3, 8, materials["wood"])
    make_span("LanternArm", (0.55, -0.63, 2.2), (0.95, -0.57, 2.26), materials["wood"])
    make_span("LanternCage", (0.83, -0.68, 1.82), (0.99, -0.52, 2.1), materials["lamp"])
    make_cone("LanternRoof", (0.91, -0.6, 2.1), 0.14, 0.12, 4, materials["iron"], rotation=math.pi / 4.0)
    make_span("LanternFloor", (0.81, -0.7, 1.79), (1.01, -0.5, 1.82), materials["iron"])
    make_span("WelcomeMat", (-0.1, -0.95, 0.0), (0.45, -0.55, 0.02), materials["cloth"])
    make_span("Yard-colonly", (-0.9, -0.75, 0.0), (0.7, 0.0, 1.2), None)


def yard_guild(materials: dict) -> None:
    make_span("BoardPostA", (-0.85, -0.42, 0.0), (-0.75, -0.32, 2.2), materials["wood"])
    make_span("BoardPostB", (0.35, -0.42, 0.0), (0.45, -0.32, 2.2), materials["wood"])
    make_span("BoardPanel", (-0.8, -0.4, 0.9), (0.4, -0.34, 2.0), materials["wood_light"])
    make_tilted_box("BoardRoofA", (-0.5, -0.4, 2.3), (0.82, 0.3, 0.05), materials["wood"], y_degrees=-22.0)
    make_tilted_box("BoardRoofB", (0.1, -0.4, 2.3), (0.82, 0.3, 0.05), materials["wood"], y_degrees=22.0)

    for sheet_index, (sheet_x, sheet_z, degrees) in enumerate([(-0.6, 1.7, 4.0), (-0.25, 1.75, -5.0), (0.15, 1.68, 3.0), (-0.5, 1.25, -3.0), (-0.1, 1.2, 6.0), (0.2, 1.3, -4.0)]):
        make_tilted_box(f"Notice{sheet_index}", (sheet_x, -0.41, sheet_z), (0.26, 0.012, 0.34), materials["cream"], y_degrees=degrees)
        make_sphere(f"NoticePin{sheet_index}", (sheet_x, -0.42, sheet_z + 0.13), 0.02, materials["red"])

    make_cylinder("FlagPole", (0.78, -0.5, 0.0), 0.04, 3.4, 8, materials["wood"])
    make_sphere("FlagPoleTip", (0.78, -0.5, 3.44), 0.07, materials["gold"])
    make_span("Flag", (0.8, -0.51, 2.5), (0.83, -0.49, 3.3), materials["cloth"])
    make_span("FlagBody", (0.3, -0.51, 2.6), (0.8, -0.49, 3.3), materials["cloth"])
    make_span("FlagStripe", (0.3, -0.515, 2.9), (0.8, -0.485, 3.0), materials["gold"])
    make_span("Yard-colonly", (-0.9, -0.6, 0.0), (0.9, 0.0, 2.2), None)


def yard_bakery(materials: dict) -> None:
    for sack_index, (sack_x, sack_y, sack_z) in enumerate([(-0.55, -0.4, 0.0), (-0.1, -0.45, 0.0), (-0.32, -0.42, 0.36)]):
        sack = make_sphere(f"FlourSack{sack_index}", (sack_x, sack_y, sack_z + 0.22), 0.3, materials["cream"])
        sack.scale = (1.0, 0.8, 0.75)
        make_cone(f"FlourSackTie{sack_index}", (sack_x, sack_y, sack_z + 0.4), 0.07, 0.12, 6, materials["leather"], top_radius=0.1)

    make_frustum("BreadBasket", 0.0, 0.3, 0.4, 0.4, 10, materials["leather"]).location[:2] = (0.55, -0.5)

    for loaf_index in range(4):
        loaf = make_sphere(f"BasketLoaf{loaf_index}", (0.45 + 0.2 * (loaf_index % 2), -0.58 + 0.18 * (loaf_index // 2), 0.44), 0.14, materials["bread"])
        loaf.scale = (1.2, 0.85, 0.7)

    make_span("Yard-colonly", (-0.9, -0.9, 0.0), (0.95, 0.0, 1.0), None)


def yard_tailor(materials: dict) -> None:
    for form_index, (form_x, color_key) in enumerate(((-0.45, "cloth"), (0.45, "blue"))):
        make_cylinder(f"FormFoot{form_index}", (form_x, -0.5, 0.0), 0.22, 0.05, 10, materials["wood"])
        make_cylinder(f"FormPole{form_index}", (form_x, -0.5, 0.0), 0.035, 1.6, 8, materials["wood"])
        make_frustum(f"FormSkirt{form_index}", 0.3, 0.42, 0.17, 0.75, 12, materials[color_key]).location[:2] = (form_x, -0.5)
        make_frustum(f"FormBodice{form_index}", 1.05, 0.17, 0.24, 0.4, 12, materials[color_key]).location[:2] = (form_x, -0.5)
        make_cylinder(f"FormBelt{form_index}", (form_x, -0.5, 1.02), 0.185, 0.06, 12, materials["gold"])
        make_sphere(f"FormKnob{form_index}", (form_x, -0.5, 1.63), 0.06, materials["wood_light"])

    make_span("Yard-colonly", (-0.9, -0.95, 0.0), (0.9, 0.0, 1.6), None)


def yard_jeweler(materials: dict) -> None:
    make_span("StrongboxBody", (-0.75, -0.7, 0.0), (0.05, -0.2, 0.5), materials["iron"])
    make_span("StrongboxLid", (-0.78, -0.73, 0.5), (0.08, -0.17, 0.58), materials["iron"])
    make_span("StrongboxBandA", (-0.6, -0.72, 0.0), (-0.54, -0.18, 0.6), materials["gold"])
    make_span("StrongboxBandB", (-0.16, -0.72, 0.0), (-0.1, -0.18, 0.6), materials["gold"])
    make_span("StrongboxLock", (-0.4, -0.75, 0.28), (-0.3, -0.7, 0.42), materials["gold"])
    make_cylinder("DisplayPillar", (0.55, -0.5, 0.0), 0.2, 1.05, 8, materials["stone"])
    make_cylinder("DisplayPillarCap", (0.55, -0.5, 1.05), 0.26, 0.06, 8, materials["gold"])
    make_sphere("DisplayCushion", (0.55, -0.5, 1.13), 0.17, materials["cloth"]).scale = (1.0, 1.0, 0.45)
    make_cone("GreatGemCrown", (0.55, -0.5, 1.3), 0.12, 0.1, 6, materials["crystal"], top_radius=0.06)
    make_cone("GreatGemPavilion", (0.55, -0.5, 1.2), 0.02, 0.1, 6, materials["crystal"], top_radius=0.12)
    make_span("Yard-colonly", (-0.85, -0.8, 0.0), (0.85, 0.0, 1.3), None)


# ---------- catalogue and export ----------

SHOPS = {  # type -> awning/sign colour and the three builders
    "smith": {"color": (0.5, 0.14, 0.1), "emblem": emblem_anvil, "goods": goods_smith, "yard": yard_smith},
    "armor": {"color": (0.16, 0.26, 0.52), "emblem": emblem_shield, "goods": goods_armor, "yard": yard_armor},
    "magic": {"color": (0.36, 0.2, 0.58), "emblem": emblem_star, "goods": goods_magic, "yard": yard_magic},
    "alchemy": {"color": (0.16, 0.44, 0.3), "emblem": emblem_flask, "goods": goods_alchemy, "yard": yard_alchemy},
    "tavern": {"color": (0.66, 0.4, 0.12), "emblem": emblem_mug, "goods": goods_tavern, "yard": yard_tavern},
    "inn": {"color": (0.12, 0.38, 0.46), "emblem": emblem_bed, "goods": goods_inn, "yard": yard_inn},
    "guild": {"color": (0.62, 0.12, 0.2), "emblem": emblem_swords, "goods": goods_guild, "yard": yard_guild},
    "bakery": {"color": (0.8, 0.56, 0.2), "emblem": emblem_loaf, "goods": goods_bakery, "yard": yard_bakery},
    "tailor": {"color": (0.7, 0.3, 0.5), "emblem": emblem_spool, "goods": goods_tailor, "yard": yard_tailor},
    "jeweler": {"color": (0.1, 0.4, 0.4), "emblem": emblem_gem, "goods": goods_jeweler, "yard": yard_jeweler},
    # sign-only types: no stall or yard builder yet, so only the sign is built for them
    "general": {"color": (0.5, 0.4, 0.22), "emblem": emblem_sack_flask},
    "bank": {"color": (0.2, 0.32, 0.18), "emblem": emblem_coin},
    "bookshop": {"color": (0.38, 0.16, 0.3), "emblem": emblem_book},
    "herbalist": {"color": (0.45, 0.58, 0.18), "emblem": emblem_leaf},
}
PIECES = {"sign": build_sign, "stall": build_stall, "yard": lambda shop, materials: shop["yard"](materials)}
PIECE_NEEDS = {"sign": "emblem", "stall": "goods", "yard": "yard"}  # builder key a shop must define for each piece


def build_shop_piece(shop_type: str, piece: str) -> Path:
    output_path = SHOP_DIR / f"shop_{shop_type}_{piece}.gltf"
    shop = SHOPS[shop_type]

    bpy.ops.wm.read_factory_settings(use_empty=True)

    materials = build_shop_materials(shop["color"])
    PIECES[piece](shop, materials)
    bpy.context.view_layer.update()
    merge_meshes_by_material(f"Shop{shop_type.title()}{piece.title()}")

    SHOP_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(output_path), export_format="GLTF_SEPARATE", export_yup=True)

    return output_path


if __name__ == "__main__":
    script_arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    for requested_shop in script_arguments or list(SHOPS):
        for piece_name in (piece for piece in PIECES if PIECE_NEEDS[piece] in SHOPS[requested_shop]):
            print(f"BUILT {requested_shop} {piece_name} -> {build_shop_piece(requested_shop, piece_name)}")
