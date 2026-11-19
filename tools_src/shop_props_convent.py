"""Convent and orphanage furniture the orphanage library lacked: child beds and nursery cots, latrine stalls, nuns'
cell cubicles, the parlour grille, the fencing hall (piste, weapon rack, plastron, pell), the magic practice room
(target dummy, ward line), the laundry's mangle and ceiling airer, the washroom trough, the porter's desk and the
kitchen's chopping block.

After 19th-century convent and institution pieces: iron beds and cots in long rows, board latrine stalls, curtained
timber cells in the nuns' dormitory, the double iron grille with its turning drum (roda) between parlour and
enclosure, the salle d'armes with its marked strip, foil racks, wall plastrons and pell, the cast-iron mangle and the
pulley airer. These repeat many times: low triangle counts, few sides on round parts.

Runs inside Blender, imported by build_prop_sheet.py and layout builders. Contract of shop_props_common.py: X width
centred on 0, front faces -Y, back at +size[1] / 2, Z up from the floor (hang=True props grow down from the
ceiling at z = 0).
"""

import math
import sys
from pathlib import Path

from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_town_houses import Builder  # noqa: E402
from shop_props_common import wood_box  # noqa: E402
from shop_props_orphanage import (  # noqa: E402
    BLANKET_COLOURS,
    BRASS_AGED,
    CAST_IRON,
    HONEY_WOOD,
    LEATHER_BROWN,
    LINEN_CREAM,
    LINEN_RAW,
    PINE_SCRUB,
    STONE_LIGHT,
    WALNUT_DARK,
    WALNUT_MID,
    WROUGHT_IRON,
    _at,
    _beam,
    _book_open,
    _box,
    _cyl,
    _draped_towel,
    _pillow,
    _soft_block,
    _sphere,
    _wicker_basket,
    iron_bed,
)

CURTAIN_GREEN = "4E5E44"
PISTE_GREY = "8D8A80"
PISTE_LINE = "EDE6D6"
CANVAS = "D8CDB2"
STRAW = "C9A85C"
SCORCH = "3A2E26"
FOIL_STEEL = "B8BEC4"
MASK_MESH = "40444A"
CHILD_BED_SCALE = (0.9, 0.925, 0.95)


def child_bed(b: Builder, frame: Matrix, variant: str = None, **options) -> None:
    """The orphanage's iron bed cut down for children 7-14 (1.85 m), so four rows fit a dormitory band."""
    iron_bed(b, frame @ Matrix.Diagonal((*CHILD_BED_SCALE, 1.0)), variant=variant, **options)


def cot(b: Builder, frame: Matrix, variant: str = None, **options) -> None:
    """Little ones' iron cot (ages 3-6): high barred sides, mattress, small blanket, pillow, a rag doll."""
    blanket = BLANKET_COLOURS.get(variant or "ochre", BLANKET_COLOURS["ochre"])
    half_w, half_l, rail_z = 0.35, 0.7, 0.95
    corners = [(x, y) for x in (-half_w, half_w) for y in (-half_l, half_l)]

    for corner_x, corner_y in corners:
        _cyl(b, frame, (corner_x, corner_y, 0.0), 0.016, rail_z + 0.04, 6, "metal", WROUGHT_IRON)
        _sphere(b, frame, (corner_x, corner_y, rail_z + 0.06), 0.022, "metal", BRASS_AGED, segments=5)

    for side_x in (-half_w, half_w):
        _cyl(b, frame, (side_x, -half_l, 0.3), 0.01, 2.0 * half_l, 5, "metal", WROUGHT_IRON, axis="Y")
        _cyl(b, frame, (side_x, -half_l, rail_z), 0.01, 2.0 * half_l, 5, "metal", WROUGHT_IRON, axis="Y")

        for bar in range(10):
            _box(b, frame, (side_x - 0.005, -half_l + 0.14 * (bar + 0.5) - 0.005, 0.3), (side_x + 0.005, -half_l + 0.14 * (bar + 0.5) + 0.005, rail_z), "metal", WROUGHT_IRON)

    for end_y in (-half_l, half_l):
        _cyl(b, frame, (-half_w, end_y, 0.3), 0.01, 2.0 * half_w, 5, "metal", WROUGHT_IRON, axis="X")
        _cyl(b, frame, (-half_w, end_y, rail_z), 0.01, 2.0 * half_w, 5, "metal", WROUGHT_IRON, axis="X")

        for bar in range(5):
            _box(b, frame, (-half_w + 0.14 * (bar + 0.5) - 0.005, end_y - 0.005, 0.3), (-half_w + 0.14 * (bar + 0.5) + 0.005, end_y + 0.005, rail_z), "metal", WROUGHT_IRON)

    _soft_block(b, frame, (0.0, 0.0, 0.38), (half_w - 0.02, half_l - 0.03, 0.07), "E2D9C6")
    _soft_block(b, frame, (0.0, -0.16, 0.41), (half_w - 0.015, half_l - 0.2, 0.06), blanket)
    _pillow(b, frame, 0.0, half_l - 0.17, 0.48, 0.24, 0.13, 0.05)
    _soft_block(b, frame, (0.12, -0.42, 0.49), (0.05, 0.03, 0.08), "B5523E", bevel=0.015)
    _sphere(b, frame, (0.12, -0.42, 0.6), 0.04, "paint", "E9CDB0", segments=5)


def latrine_stall(b: Builder, frame: Matrix, **options) -> None:
    """One latrine stall, back to the wall: board partitions, a half door hung open, the scrubbed wooden bench with
    its hole and lid, a peg and a water jug. Rows are stalls placed side by side."""
    width, depth, height = 1.0, 1.3, 2.05
    back = depth / 2.0

    for side in (-1.0, 1.0):
        post = side * (width / 2.0 - 0.03)
        wood_box(b, frame, (post - 0.02, -back, 0.12), (post + 0.02, back, height), WALNUT_MID)
        _box(b, frame, (post - 0.03, -back, 0.0), (post + 0.03, -back + 0.06, height + 0.05), "wood", WALNUT_DARK)

    wood_box(b, frame, (-width / 2.0 + 0.02, back - 0.6, 0.0), (width / 2.0 - 0.02, back, 0.46), PINE_SCRUB, light=True)
    _cyl(b, frame, (0.0, back - 0.32, 0.461), 0.13, 0.004, 10, "paint", "2A2420")
    wood_box(b, frame, (-0.2, back - 0.2, 0.47), (0.2, back - 0.02, 0.5), HONEY_WOOD, light=True)
    door = _at(frame, (-width / 2.0 + 0.07, -back + 0.03, 0.25), 35.0)  # entreaberta para dentro
    wood_box(b, door, (0.0, -0.02, 0.0), (width - 0.16, 0.02, 1.35), WALNUT_MID)
    _box(b, door, (width - 0.28, -0.04, 0.68), (width - 0.24, -0.02, 0.76), "metal", CAST_IRON)
    _cyl(b, frame, (0.3, back - 0.05, 1.5), 0.012, 0.1, 5, "wood", WALNUT_DARK, axis="Y")
    _cyl(b, frame, (-0.32, back - 0.12, 0.0), 0.08, 0.28, 8, "paint", "C98A5A", top_radius=0.06)


def cell_walls(b: Builder, frame: Matrix, width: float) -> None:
    """Nun's cell cubicle: timber partitions 2.4 m high left and right (back open to the room wall, top open), a
    framed front with a linen curtain on a rail, half drawn. The furniture comes from the layout."""
    depth, height = 3.6, 2.4
    front, back = -depth / 2.0, depth / 2.0
    door_from, door_to = -width / 2.0 + 0.1, -width / 2.0 + 1.0

    for side in (-1.0, 1.0):
        wood_box(b, frame, (side * width / 2.0 - 0.04 * (side > 0), front, 0.0), (side * width / 2.0 + 0.04 * (side < 0), back, height), WALNUT_MID)

    wood_box(b, frame, (door_to, front, 0.0), (width / 2.0 - 0.04, front + 0.05, height), WALNUT_MID)
    _box(b, frame, (-width / 2.0, front, height - 0.1), (width / 2.0, front + 0.1, height), "wood", WALNUT_DARK)
    _cyl(b, frame, (door_from, front + 0.12, 2.1), 0.012, door_to - door_from, 5, "metal", BRASS_AGED, axis="X")

    for fold in range(4):
        fold_x = door_from + fold * 0.12
        _box(b, frame, (fold_x, front + 0.1 + 0.02 * (fold % 2), 0.08), (fold_x + 0.12, front + 0.12 + 0.02 * (fold % 2), 2.08), "paint", LINEN_RAW)

    _box(b, frame, (0.4, front - 0.005, 1.7), (0.52, front, 1.86), "paint", "2A2420")  # plaquinha com o nome da irmã

    for side in (-1.0, 1.0):  # paredes finas que barram o passo; a cela fica livre por dentro para os móveis
        b.collider((side * width / 2.0 - 0.05, front, 0.0), (side * width / 2.0 + 0.05, back, height), frame)

    b.collider((door_to, front, 0.0), (width / 2.0, front + 0.05, height), frame)


def nun_cell(b: Builder, frame: Matrix, **options) -> None:
    cell_walls(b, frame, 3.0)


def nun_cell_narrow(b: Builder, frame: Matrix, **options) -> None:
    cell_walls(b, frame, 2.4)


def parlour_grille(b: Builder, frame: Matrix, variant: str = None, **options) -> None:
    """Grille filling the wall opening between parlour and enclosure, from the 0.9 m sill up: wooden ledge, thick
    frame, two dense iron lattices a hand apart, a dark curtain behind (+Y). "turn" adds the revolving drum (roda)
    in the middle of the ledge for passing things without being seen."""
    width, sill, top = 3.0, 0.9, 2.6

    wood_box(b, frame, (-width / 2.0, -0.15, sill - 0.06), (width / 2.0, 0.15, sill), HONEY_WOOD, light=True)
    wood_box(b, frame, (-width / 2.0, -0.1, top - 0.18), (width / 2.0, 0.1, top), WALNUT_DARK)
    wood_box(b, frame, (-width / 2.0, -0.1, sill), (-width / 2.0 + 0.14, 0.1, top - 0.18), WALNUT_DARK)
    wood_box(b, frame, (width / 2.0 - 0.14, -0.1, sill), (width / 2.0, 0.1, top - 0.18), WALNUT_DARK)

    for grille_y in (-0.05, 0.05):
        for bar in range(15):
            bar_x = -width / 2.0 + 0.24 + bar * (width - 0.48) / 14.0
            _box(b, frame, (bar_x - 0.01, grille_y - 0.01, sill), (bar_x + 0.01, grille_y + 0.01, top - 0.18), "metal", WROUGHT_IRON)

        for rail in range(5):
            rail_z = sill + 0.14 + rail * 0.3
            _box(b, frame, (-width / 2.0 + 0.14, grille_y - 0.01, rail_z - 0.01), (width / 2.0 - 0.14, grille_y + 0.01, rail_z + 0.01), "metal", WROUGHT_IRON)

    for fold in range(8):
        fold_x = -width / 2.0 + 0.14 + fold * (width - 0.28) / 8.0
        _box(b, frame, (fold_x, 0.1 + 0.02 * (fold % 2), sill), (fold_x + (width - 0.28) / 8.0, 0.12 + 0.02 * (fold % 2), top - 0.18), "paint", CURTAIN_GREEN)

    if variant == "turn":  # a roda atravessa a espessura da parede, um palmo para cada lado da grade
        _cyl(b, frame, (0.0, 0.0, sill), 0.28, 0.55, 10, "wood", HONEY_WOOD)
        _box(b, frame, (-0.18, -0.29, sill + 0.08), (0.18, -0.24, sill + 0.45), "paint", "1E1814")


def fencing_piste(b: Builder, frame: Matrix, **options) -> None:
    """Marked fencing strip on the hall floor, 14 m along X: grey linoleum, white side lines, centre line, en-garde
    lines at 2 m, the last 2 m before each end line shaded as the warning zone."""
    half_l, half_w = 7.0, 0.9

    _box(b, frame, (-half_l, -half_w, 0.0), (half_l, half_w, 0.012), "paint", PISTE_GREY)

    for end in (-1.0, 1.0):
        _box(b, frame, *sorted_box((end * (half_l - 2.0), -half_w, 0.012), (end * half_l, half_w, 0.014)), "paint", "6F6A60")

    for line_x in (0.0, -2.0, 2.0, -5.0, 5.0, -half_l + 0.025, half_l - 0.025):
        _box(b, frame, (line_x - 0.025, -half_w, 0.014), (line_x + 0.025, half_w, 0.018), "paint", PISTE_LINE)

    for side in (-1.0, 1.0):
        _box(b, frame, (-half_l, side * half_w - 0.025, 0.014), (half_l, side * half_w + 0.025, 0.018), "paint", PISTE_LINE)


def sorted_box(low: tuple, high: tuple) -> tuple:
    """(low, high) corners with each axis in order, for boxes mirrored by sign."""
    return tuple(min(pair) for pair in zip(low, high)), tuple(max(pair) for pair in zip(low, high))


def fencing_rack(b: Builder, frame: Matrix, **options) -> None:
    """Wall rack of the salle d'armes: foils and sabres upright in a slotted shelf, six wire masks on pegs above,
    padded plastrons hung at the top."""
    width, depth = 1.6, 0.3
    back = depth / 2.0

    wood_box(b, frame, (-width / 2.0, back - 0.04, 0.0), (width / 2.0, back, 2.0), WALNUT_DARK)
    wood_box(b, frame, (-width / 2.0, -back, 0.0), (width / 2.0, back, 0.1), WALNUT_MID)
    wood_box(b, frame, (-width / 2.0, -back + 0.05, 0.85), (width / 2.0, back, 0.89), WALNUT_MID)

    for blade in range(10):
        blade_x = -0.65 + blade * 0.145
        lean = 0.04 if blade % 2 else 0.0
        guard_material, guard_tint = ("metal", BRASS_AGED) if blade % 3 else ("paint", LEATHER_BROWN)
        _beam(b, frame, (blade_x, 0.0, 0.1), (blade_x, 0.04 + lean, 0.95), 0.006, 0.006, "metal", FOIL_STEEL)
        _cyl(b, frame, (blade_x, 0.05 + lean, 0.95), 0.012, 0.15, 5, guard_material, guard_tint)
        _cyl(b, frame, (blade_x, 0.05 + lean, 0.95), 0.035, 0.008, 6, "metal", FOIL_STEEL)

    for mask in range(6):
        mask_x = -0.62 + mask * 0.248
        _cyl(b, frame, (mask_x, back - 0.04, 1.42), 0.01, 0.08, 5, "wood", WALNUT_DARK, axis="Y")
        _sphere(b, frame, (mask_x, back - 0.15, 1.4), 0.1, "metal", MASK_MESH, scale=(0.9, 0.8, 1.15), segments=6)
        _box(b, frame, (mask_x - 0.09, back - 0.16, 1.24), (mask_x + 0.09, back - 0.1, 1.29), "paint", PISTE_LINE)

    for jacket in range(3):
        _soft_block(b, frame, (-0.5 + jacket * 0.5, back - 0.08, 1.78), (0.18, 0.03, 0.17), PISTE_LINE, bevel=0.02)


def plastron_target(b: Builder, frame: Matrix, **options) -> None:
    """Wall plastron for lunging practice: a board on the wall with a padded leather torso, the middle worn pale
    by thousands of touches, painted rings."""
    back = 0.125

    wood_box(b, frame, (-0.45, back - 0.05, 0.3), (0.45, back, 1.9), WALNUT_MID)
    _soft_block(b, frame, (0.0, back - 0.12, 1.25), (0.28, 0.07, 0.4), LEATHER_BROWN, bevel=0.05)
    _cyl(b, frame, (0.0, back - 0.195, 1.3), 0.17, 0.01, 12, "paint", "A57A55", axis="Y")
    _cyl(b, frame, (0.0, back - 0.205, 1.3), 0.08, 0.01, 10, "paint", "D2B48C", axis="Y")
    _sphere(b, frame, (0.0, back - 0.11, 1.78), 0.11, "paint", LEATHER_BROWN, scale=(1.0, 0.6, 1.1), segments=6)


def pell_post(b: Builder, frame: Matrix, **options) -> None:
    """Wooden pell in a cross base, its upper half nicked and scarred by blade work."""
    for angle in (0.0, 90.0):
        wood_box(b, _at(frame, (0.0, 0.0, 0.0), angle), (-0.25, -0.05, 0.0), (0.25, 0.05, 0.1), WALNUT_DARK)

    _box(b, frame, (-0.08, -0.08, 0.1), (0.08, 0.08, 1.8), "wood", HONEY_WOOD)

    for nick in range(7):
        nick_z = 0.9 + nick * 0.12
        nick_frame = _at(frame, (0.0, -0.081, nick_z), 18.0 * (1 if nick % 2 else -1), "Y")
        _box(b, nick_frame, (-0.06, -0.004, -0.006), (0.06, 0.0, 0.006), "paint", "5A3E28")


def practice_dummy(b: Builder, frame: Matrix, **options) -> None:
    """Magic practice target: a straw dummy bound with rope on a post, a runed disc on its chest, scorch marks."""
    for angle in (0.0, 90.0):
        wood_box(b, _at(frame, (0.0, 0.0, 0.0), angle), (-0.24, -0.05, 0.0), (0.24, 0.05, 0.1), WALNUT_DARK)

    _cyl(b, frame, (0.0, 0.0, 0.1), 0.05, 1.45, 6, "wood", WALNUT_MID)
    _soft_block(b, frame, (0.0, 0.0, 1.2), (0.2, 0.15, 0.32), STRAW, bevel=0.07)
    _sphere(b, frame, (0.0, 0.0, 1.7), 0.13, "paint", STRAW, scale=(1.0, 0.95, 1.15), segments=6)
    _cyl(b, frame, (-0.34, 0.0, 1.4), 0.03, 0.68, 5, "wood", WALNUT_MID, axis="X")

    for rope_z in (0.95, 1.45, 1.58):
        half_x, half_y = (0.21, 0.16) if rope_z < 1.5 else (0.13, 0.13)
        _box(b, frame, (-half_x, -half_y, rope_z), (half_x, half_y, rope_z + 0.03), "paint", "8C7350")

    _cyl(b, frame, (0.0, -0.16, 1.25), 0.13, 0.015, 12, "metal", BRASS_AGED, axis="Y")
    _cyl(b, frame, (0.0, -0.176, 1.25), 0.09, 0.004, 10, "glow_cyan", "8FD8FF", axis="Y")
    _soft_block(b, frame, (0.13, -0.16, 1.0), (0.06, 0.005, 0.08), SCORCH, bevel=0.0)
    _soft_block(b, frame, (-0.1, -0.16, 1.44), (0.05, 0.005, 0.05), SCORCH, bevel=0.0)


def ward_line(b: Builder, frame: Matrix, **options) -> None:
    """Glowing runic strip on the floor of the magic room, marking where the casters stand."""
    _box(b, frame, (-3.0, -0.15, 0.0), (3.0, 0.15, 0.006), "paint", "3A3550")

    for rune in range(20):
        rune_x = -2.85 + rune * 0.3
        tilt = 30.0 if rune % 3 == 0 else (-30.0 if rune % 3 == 1 else 90.0)
        _box(b, _at(frame, (rune_x, 0.0, 0.006), tilt), (-0.09, -0.012, 0.0), (0.09, 0.012, 0.012), "glow_cyan", "8FD8FF")

    for side in (-1.0, 1.0):
        _box(b, frame, (-3.0, side * 0.13 - 0.01, 0.006), (3.0, side * 0.13 + 0.01, 0.01), "glow_cyan", "8FD8FF")


def laundry_mangle(b: Builder, frame: Matrix, **options) -> None:
    """Cast-iron mangle: frame on splayed legs, two wooden rollers under a screw press, a spoked crank wheel at the
    side, folded sheets on the board and a wicker basket underneath."""
    half_w, wheel_x, wheel_radius = 0.3, 0.38, 0.32

    for side in (-1.0, 1.0):
        _beam(b, frame, (side * half_w, -0.3, 0.0), (side * half_w, -0.03, 1.2), 0.05, 0.05, "metal", CAST_IRON)
        _beam(b, frame, (side * half_w, 0.3, 0.0), (side * half_w, 0.03, 1.2), 0.05, 0.05, "metal", CAST_IRON)
        _box(b, frame, (side * half_w - 0.035, -0.06, 1.15), (side * half_w + 0.035, 0.06, 1.36), "metal", CAST_IRON)

    _box(b, frame, (-half_w, -0.05, 1.33), (half_w, 0.05, 1.38), "metal", CAST_IRON)
    _cyl(b, frame, (0.0, 0.0, 1.38), 0.015, 0.02, 6, "metal", CAST_IRON)

    for roller_z in (1.03, 1.19):
        _cyl(b, frame, (-half_w, 0.0, roller_z), 0.07, 2.0 * half_w, 10, "wood", PINE_SCRUB, axis="X")

    wood_box(b, frame, (-half_w + 0.03, -0.34, 0.8), (half_w - 0.03, -0.05, 0.83), HONEY_WOOD, light=True)
    wheel = _at(frame, (wheel_x, 0.0, 1.03), 90.0, "Y")

    for spoke in range(5):
        angle = 2.0 * math.pi * spoke / 5.0
        _beam(b, wheel, (0.0, 0.0, 0.0), (wheel_radius * math.cos(angle), wheel_radius * math.sin(angle), 0.0), 0.022, 0.022, "metal", CAST_IRON)

    for step in range(12):
        start, end = 2.0 * math.pi * step / 12.0, 2.0 * math.pi * (step + 1) / 12.0
        _beam(b, wheel, (wheel_radius * math.cos(start), wheel_radius * math.sin(start), 0.0), (wheel_radius * math.cos(end), wheel_radius * math.sin(end), 0.0), 0.03, 0.03, "metal", CAST_IRON)

    _cyl(b, frame, (wheel_x, 0.27, 1.25), 0.02, 0.1, 5, "wood", WALNUT_DARK, axis="X")

    for sheet in range(3):
        _soft_block(b, frame, (0.0, -0.2, 0.845 + sheet * 0.03), (0.22, 0.12, 0.014), LINEN_CREAM if sheet % 2 else LINEN_RAW, bevel=0.006)

    _wicker_basket(b, frame, 0.0, 0.05, 0.0, r_bot=0.16, r_top=0.21, height=0.24)


def laundry_airer(b: Builder, frame: Matrix, **options) -> None:
    """Pulley airer hung from the ceiling: cast-iron end brackets on ropes, five laths, sheets and shirts drying."""
    length, drop = 2.4, 0.75

    for side in (-1.0, 1.0):
        bracket = side * (length / 2.0 - 0.15)
        _box(b, frame, (bracket - 0.02, -0.38, -drop - 0.04), (bracket + 0.02, 0.38, -drop + 0.03), "metal", CAST_IRON)
        _beam(b, frame, (bracket, -0.34, -drop), (bracket, 0.0, -0.05), 0.012, 0.012, "paint", LINEN_RAW)
        _beam(b, frame, (bracket, 0.34, -drop), (bracket, 0.0, -0.05), 0.012, 0.012, "paint", LINEN_RAW)
        _cyl(b, frame, (bracket, 0.0, -0.06), 0.05, 0.06, 8, "metal", CAST_IRON)

    for lath in range(5):
        lath_y = -0.32 + lath * 0.16
        _box(b, frame, (-length / 2.0, lath_y - 0.02, -drop - 0.01), (length / 2.0, lath_y + 0.02, -drop + 0.02), "wood", PINE_SCRUB)

    _draped_towel(b, frame, -0.4, -0.16, -drop + 0.02, 1.2, 0.24, LINEN_CREAM, stripe=LINEN_CREAM)
    _draped_towel(b, frame, 0.6, 0.16, -drop + 0.02, 0.5, 0.2, "C9D2DA", stripe="C9D2DA")
    _draped_towel(b, frame, 0.65, -0.32, -drop + 0.02, 0.4, 0.2, LINEN_RAW, stripe="3B5A7A")


def washroom_trough(b: Builder, frame: Matrix, **options) -> None:
    """Long stone trough on piers with four brass taps on a back pipe, a soap ledge, a strip of mirror above."""
    width, depth = 3.0, 0.6
    back = depth / 2.0

    for pier_x in (-1.35, 0.0, 1.35):
        _box(b, frame, (pier_x - 0.1, -0.15, 0.0), (pier_x + 0.1, back - 0.02, 0.62), "stone", STONE_LIGHT)

    _box(b, frame, (-width / 2.0, -back + 0.02, 0.62), (width / 2.0, back - 0.02, 0.66), "stone", STONE_LIGHT)
    _box(b, frame, (-width / 2.0, -back + 0.02, 0.66), (width / 2.0, -back + 0.08, 0.84), "stone", STONE_LIGHT)
    _box(b, frame, (-width / 2.0, back - 0.08, 0.66), (width / 2.0, back - 0.02, 0.88), "stone", STONE_LIGHT)

    for end in (-1.0, 1.0):
        _box(b, frame, *sorted_box((end * width / 2.0, -back + 0.02, 0.66), (end * (width / 2.0 - 0.06), back - 0.02, 0.84)), "stone", STONE_LIGHT)

    _box(b, frame, (-width / 2.0 + 0.06, -back + 0.08, 0.66), (width / 2.0 - 0.06, back - 0.08, 0.7), "water", "6C8EA0")
    _cyl(b, frame, (-width / 2.0, back - 0.04, 0.98), 0.02, width, 6, "metal", BRASS_AGED, axis="X")

    for tap in range(4):
        tap_x = -1.125 + tap * 0.75
        _beam(b, frame, (tap_x, back - 0.04, 0.98), (tap_x, back - 0.16, 0.94), 0.025, 0.025, "metal", BRASS_AGED)
        _cyl(b, frame, (tap_x, back - 0.04, 1.0), 0.03, 0.02, 6, "metal", BRASS_AGED)
        _box(b, frame, (tap_x + 0.18, back - 0.07, 0.885), (tap_x + 0.26, back - 0.02, 0.91), "paint", "E8DCC0")

    _box(b, frame, (-width / 2.0 + 0.1, back - 0.015, 1.03), (width / 2.0 - 0.1, back, 1.1), "glass", "FFFFFF")
    _box(b, frame, (-width / 2.0 + 0.08, back - 0.02, 1.02), (width / 2.0 - 0.08, back - 0.01, 1.03), "wood", WALNUT_DARK)


def porter_desk(b: Builder, frame: Matrix, **options) -> None:
    """Porter's lodge desk: a high sloped writing desk with the visitors' register open, an inkstand and quill, a
    brass hand bell."""
    width = 1.6

    wood_box(b, frame, (-width / 2.0, -0.33, 0.0), (width / 2.0, 0.33, 0.95), WALNUT_MID)
    _box(b, frame, (-width / 2.0 - 0.02, -0.35, 0.0), (width / 2.0 + 0.02, -0.32, 0.1), "wood", WALNUT_DARK)
    _beam(b, frame, (-width / 2.0, -0.02, 0.98), (width / 2.0, -0.02, 0.98), 0.03, 0.68, "wood", WALNUT_DARK)
    wood_box(b, frame, (-width / 2.0, 0.25, 0.95), (width / 2.0, 0.35, 1.1), WALNUT_DARK)
    _book_open(b, frame, -0.25, -0.05, 1.0, 0.5, 0.34, "6E2D38")
    _cyl(b, frame, (0.4, 0.15, 1.0), 0.03, 0.05, 6, "paint", "1E1E24")
    _beam(b, frame, (0.4, 0.15, 1.05), (0.46, 0.21, 1.09), 0.006, 0.006, "paint", PISTE_LINE)
    _cyl(b, frame, (0.6, -0.1, 0.99), 0.045, 0.05, 8, "metal", BRASS_AGED, top_radius=0.02)


def chopping_block(b: Builder, frame: Matrix, **options) -> None:
    """Butcher's block: a thick end-grain slab on four stout legs, a cleaver stuck in the top."""
    for corner_x, corner_y in ((-0.22, -0.22), (-0.22, 0.22), (0.22, -0.22), (0.22, 0.22)):
        _box(b, frame, (corner_x - 0.05, corner_y - 0.05, 0.0), (corner_x + 0.05, corner_y + 0.05, 0.5), "wood", WALNUT_DARK)

    _cyl(b, frame, (0.0, 0.0, 0.5), 0.3, 0.35, 10, "wood", HONEY_WOOD)
    _cyl(b, frame, (0.0, 0.0, 0.849), 0.27, 0.003, 10, "paint", "A57A55")
    blade = _at(frame, (0.05, -0.02, 0.85), 25.0)
    _box(b, blade, (-0.1, -0.004, -0.04), (0.06, 0.004, 0.06), "metal", FOIL_STEEL)
    _box(b, blade, (0.06, -0.012, 0.03), (0.2, 0.012, 0.055), "wood", WALNUT_DARK)


PROPS = {
    "child_bed": {"build": child_bed, "size": (0.86, 1.85, 1.09), "solid": True, "variants": ["grey_blue", "ochre", "dull_red", "green"]},
    "cot": {"build": cot, "size": (0.75, 1.45, 1.05), "solid": True, "variants": list(BLANKET_COLOURS)},
    "latrine_stall": {"build": latrine_stall, "size": (1.0, 1.3, 2.1), "solid": True},
    "nun_cell": {"build": nun_cell, "size": (3.0, 3.6, 2.4), "solid": False},
    "nun_cell_narrow": {"build": nun_cell_narrow, "size": (2.4, 3.6, 2.4), "solid": False},
    "parlour_grille": {"build": parlour_grille, "size": (3.0, 0.3, 2.6), "solid": True, "variants": ["plain", "turn"]},
    "fencing_piste": {"build": fencing_piste, "size": (14.0, 1.8, 0.02), "solid": False},
    "fencing_rack": {"build": fencing_rack, "size": (1.6, 0.3, 2.0), "solid": True},
    "plastron_target": {"build": plastron_target, "size": (0.9, 0.25, 1.9), "solid": False},
    "pell_post": {"build": pell_post, "size": (0.5, 0.5, 1.8), "solid": True},
    "practice_dummy": {"build": practice_dummy, "size": (0.7, 0.5, 1.9), "solid": True},
    "ward_line": {"build": ward_line, "size": (6.0, 0.3, 0.02), "solid": False},
    "laundry_mangle": {"build": laundry_mangle, "size": (1.0, 0.7, 1.4), "solid": True},
    "laundry_airer": {"build": laundry_airer, "size": (2.4, 0.8, 1.0), "solid": False, "hang": True},
    "washroom_trough": {"build": washroom_trough, "size": (3.0, 0.6, 1.1), "solid": True},
    "porter_desk": {"build": porter_desk, "size": (1.6, 0.7, 1.1), "solid": True},
    "chopping_block": {"build": chopping_block, "size": (0.6, 0.6, 0.85), "solid": True},
}
