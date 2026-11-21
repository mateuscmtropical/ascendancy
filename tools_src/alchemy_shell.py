"""Shell of the apothecary-alchemist: a stone-fronted burgher house of real rooms instead of the open shop hall.

Ground floor after alchemy_layout.ROOMS: the Offizin under a white barrel vault with transverse arches, the herb room
and the stamping room under flat plaster, the laboratory under a brick vault, the master's study; tiles, brick and
flags on the floors. Outside: rusticated ashlar on the ground storey, round-headed street windows with voussoirs and
show globes, a portal with pilasters and a gilt mortar over the door, and an oriel on carved corbels above it.

build_market_shops.py calls build_shell() for the "alchemy" entry of SHOPS (shell="alchemy_shell").
"""

import math

from mathutils import Matrix

import build_market_shops as shops
import build_town_houses as town
from alchemy_layout import BACK_WINDOW, BACK_WINDOWS, FLOORS, FRONT_WINDOWS, HERBAL, LABORATORY, OFFIZIN, PANELLED, ROOMS, VAULT_RISE, VAULT_SPRING, VAULTS, WINDOW
from build_town_houses import BRICK, STONE, WOOD_DARK_BAND, WOOD_LIGHT_BAND, Builder, Opening, srgb

shops.WALL_FINISHES.update({
    OFFIZIN: dict(dado="E9E1D0", trim="5A4636"),
    HERBAL: dict(dado="8FA593", trim="4F5E48"),
    LABORATORY: dict(dado="9A8F80", trim="3A3030"),
    PANELLED: dict(dado="8B5A3C", trim="4A2E1E", material="wood", uv=("band", *WOOD_LIGHT_BAND, 1.5)),
})
VAULT_FACETS = 12
VAULT_SHELL = 0.14
ARCH_DEPTH = 0.16  # how far a transverse arch hangs under the vault
ARCH_WIDTH = 0.42
VAULT_FINISH = {"offizin": ("plaster", "F4EFE6", "plaster", STONE["media"]), "lab": ("brick", "B98A6E", "plaster", STONE["media"])}
FLOOR_FINISH = {"tiles": ("stone", STONE["caiada"]), "brick": ("brick", BRICK["claro"]), "stone": ("stone", STONE["media"])}
CHEQUER = 0.5
CHEQUER_DARK = "B0603F"
CEILING_PLASTER = srgb("F2EBDD")
GLAZING = srgb("2F4A3F")
ASHLAR_ROW = 0.46
ASHLAR_LENGTHS = (0.95, 0.65)
ASHLAR_PROUD = 0.06
ASHLAR_JOINT = "9C8F7A"
VOUSSOIRS = 9
VOUSSOIR_DEPTH = 0.3
GLOBES = ((3.4, "red"), (6.6, "green"))  # show globes in the Offizin windows
ORIEL = dict(half=1.5, reach=0.85, bottom=4.9, top=7.1, cap=0.42)
GILT = srgb("E8B64A")
LIGHTS = ((3.0, 3.4, 2.8), (-5.85, 4.5, 3.4), (2.5, 11.0, 2.6), (-4.8, 11.4, 3.3), (-4.8, 16.6, 3.0))
LAMP_LIGHT = "FFD9A0"


# ---------- walls and openings ----------

def street_openings(room) -> dict:
    """Round-headed street door and windows; back windows under the vault springing (wall-local u)."""
    door_u, door_width, door_height, door_top = room.door
    width, sill, height = WINDOW
    back_width, back_sill, back_height = BACK_WINDOW
    front = [Opening(door_u + room.half, door_width, 0.0, door_height, door_top, kind="door")]
    front += [Opening(u + room.half, width, sill, height, "round", kind="vitrine") for u in FRONT_WINDOWS]
    back = [Opening(room.half - u, back_width, back_sill, back_height, "segment", kind="vitrine") for u in BACK_WINDOWS]

    return {"front": front, "back": back, "left": [], "right": []}


def glazing_bars(b: Builder, frame: Matrix, opening: Opening) -> None:
    """Painted wooden mullion and transoms over the glass of a window."""
    left = opening.u - opening.width / 2.0
    transoms = [opening.bottom + (opening.spring - opening.bottom) * share for share in (0.35, 0.7)]

    b.box((opening.u - 0.03, 0.1, opening.bottom), (opening.u + 0.03, 0.13, opening.apex - 0.02), "paint", GLAZING, frame=frame)

    for z in transoms + [opening.spring]:
        b.box((left, 0.1, z - 0.025), (left + opening.width, 0.13, z + 0.025), "paint", GLAZING, frame=frame)


def build_walls(b: Builder, room) -> dict:
    openings = street_openings(room)
    frames = shops.wall_frames(room)
    windows = [(side, opening) for side, found in openings.items() for opening in found if opening.kind == "vitrine"]

    shops.build_walls(b, room, openings)

    for side, opening in windows:
        glazing_bars(b, frames[side], opening)

    return openings


# ---------- floors ----------

def build_floors(b: Builder, room) -> None:
    """Plank floor (the study keeps it), a tiled, a brick and two flagged rooms laid over it."""
    board_count = round((room.right - room.left) / shops.BOARD_WIDTH)
    top = shops.FLOOR_TOP + shops.STONE_PATCH_LIFT

    shops.build_plank_floor(b, room, board_count, (room.right - room.left) / board_count)
    b.collider((room.left, room.front, 0.0), (room.right, room.back, shops.FLOOR_TOP), name="WoodFloor")

    for name, finish in FLOORS.items():
        u_from, u_to, d_from, d_to = ROOMS[name]
        material, tint = FLOOR_FINISH[finish]
        b.box((u_from, d_from, shops.FLOOR_TOP), (u_to, d_to, top), material, srgb(tint), uv=("world", 1.0))
        b.collider((u_from, d_from, shops.FLOOR_TOP), (u_to, d_to, top), name="StoneFloor")

    chequer(b, ROOMS["offizin"], top)


def chequer(b: Builder, bounds: tuple, top: float) -> None:
    """Terracotta squares on every other cell of the cream tiling of the Offizin."""
    u_from, u_to, d_from, d_to = bounds
    columns, rows = int((u_to - u_from) / CHEQUER), int((d_to - d_from) / CHEQUER)
    dark_cells = [index for index in range(columns * rows) if (index % columns + index // columns) % 2]
    tint = srgb(CHEQUER_DARK)

    for index in dark_cells:
        u, d = u_from + (index % columns) * CHEQUER, d_from + (index // columns) * CHEQUER
        b.box((u, d, top), (u + CHEQUER, d + CHEQUER, top + 0.004), "stone", tint, uv=("world", 1.0))


# ---------- ceilings and vaults ----------

def build_ceiling(b: Builder, room) -> None:
    """Flat plaster over the herb room, the stamping room and the study; vaults over the Offizin and the laboratory.
    The ceiling collider comes down to the vault crowns and every vault facet is a camera stop."""
    crown = VAULT_SPRING + VAULT_RISE

    b.box((room.left, room.front, room.ceiling), (room.right, room.back, room.storey), "plaster", CEILING_PLASTER)
    b.collider((room.left, room.front, crown), (room.right, room.back, room.storey))

    for name, (spans, arches) in VAULTS.items():
        build_vault(b, name, spans, arches)


def arc_points(span_from: float, span_to: float, inset: float) -> list:
    """(across, z) of a segmental arc from span_from to span_to springing at VAULT_SPRING, grown inward by inset."""
    chord = span_to - span_from
    radius = (chord * chord / 4.0 + VAULT_RISE * VAULT_RISE) / (2.0 * VAULT_RISE)
    centre = ((span_from + span_to) / 2.0, VAULT_SPRING + VAULT_RISE - radius)
    half_angle = math.asin(chord / 2.0 / radius)
    angles = [-half_angle + 2.0 * half_angle * index / VAULT_FACETS for index in range(VAULT_FACETS + 1)]

    return [(centre[0] + (radius - inset) * math.sin(angle), centre[1] + (radius - inset) * math.cos(angle)) for angle in angles]


def arc_facets(span_from: float, span_to: float, inner: float, outer: float) -> list:
    """Quads (as convex profiles) between two concentric arcs: inner inset below the vault surface, outer above."""
    low, high = arc_points(span_from, span_to, inner), arc_points(span_from, span_to, outer)

    return [[low[index], low[index + 1], high[index + 1], high[index]] for index in range(VAULT_FACETS)]


def build_vault(b: Builder, name: str, spans: str, arches: tuple) -> None:
    """Segmental barrel vault over a room spanning u or d, transverse arches on corbels across it."""
    u_from, u_to, d_from, d_to = ROOMS[name]
    material, tint, arch_material, arch_tint = VAULT_FINISH[name]
    across = (d_from, d_to) if spans == "d" else (u_from, u_to)
    along = (u_from, u_to) if spans == "d" else (d_from, d_to)
    extrude = b.side_prism if spans == "d" else b.prism
    shell = arc_facets(*across, 0.0, -VAULT_SHELL)
    ribs = [(facet, at) for at in arches for facet in arc_facets(*across, ARCH_DEPTH, 0.0)]

    for facet in shell:
        b.camera_stop(extrude(facet, *along, material, srgb(tint), uv=("world", 1.0)))

    for facet, at in ribs:
        extrude(facet, at - ARCH_WIDTH / 2.0, at + ARCH_WIDTH / 2.0, arch_material, srgb(arch_tint))

    for at in arches:
        vault_corbels(b, spans, across, at, arch_material, srgb(arch_tint))


def vault_corbels(b: Builder, spans: str, across: tuple, at: float, material: str, tint: tuple) -> None:
    """Stepped corbel under each foot of a transverse arch."""
    feet = ((across[0], 1), (across[1], -1))

    for face, inward in feet:
        near, far = sorted((face, face + inward * 0.28))
        low = (at - ARCH_WIDTH / 2.0, near, VAULT_SPRING - 0.35) if spans == "d" else (near, at - ARCH_WIDTH / 2.0, VAULT_SPRING - 0.35)
        high = (at + ARCH_WIDTH / 2.0, far, VAULT_SPRING + 0.05) if spans == "d" else (far, at + ARCH_WIDTH / 2.0, VAULT_SPRING + 0.05)
        b.box(low, high, material, tint)


# ---------- finishes ----------

def outer_faces(room) -> list:
    """(axis, face, normal, span, finish, cuts) of each room's stretch of the outer walls."""
    door_half = room.door[1] / 2.0 + town.FRAME_DEPTH + 0.18
    front_cuts = [(u - WINDOW[0] / 2.0 - 0.1, u + WINDOW[0] / 2.0 + 0.1) for u in FRONT_WINDOWS if WINDOW[1] < shops.DADO_HEIGHT] + [(room.door[0] - door_half, room.door[0] + door_half)]
    walls = {"front": ("d", room.front, 1, front_cuts), "back": ("d", room.back, -1, []), "left": ("u", room.left, 1, []), "right": ("u", room.right, -1, [])}
    stretches = (
        ("offizin", "front", OFFIZIN), ("offizin", "right", OFFIZIN), ("herbs", "front", HERBAL), ("herbs", "left", HERBAL), ("mortar", "left", HERBAL),
        ("lab", "right", LABORATORY), ("lab", "back", LABORATORY), ("study", "left", PANELLED), ("study", "back", PANELLED),
    )
    along = lambda name, side: ROOMS[name][:2] if side in ("front", "back") else ROOMS[name][2:]

    return [(walls[side][0], walls[side][1], walls[side][2], along(name, side), finish, walls[side][3], name) for name, side, finish in stretches]


def build_finishes(b: Builder, room) -> None:
    """Dado and skirting room by room; the flat-ceiled rooms also get the picture rail and cornice of the shops."""
    for axis, face_at, normal, span, finish, cuts, name in outer_faces(room):
        if name in VAULTS:
            dado_only(b, axis, face_at, normal, span, finish, cuts)
            continue

        shops.dress_wall_face(b, room, axis, face_at, normal, span, finish, cuts, cuts)


def dado_only(b: Builder, axis: str, face_at: float, normal: int, span: tuple, finish_name: str, cuts: list) -> None:
    finish = shops.WALL_FINISHES[finish_name]
    wood_uv = ("band", *WOOD_DARK_BAND, 1.5)

    for piece in shops.free_spans(span[0], span[1], cuts):
        b.box(*shops.wall_slab(axis, face_at, normal, piece, 0.0, shops.DADO_DEPTH, (shops.SKIRTING_HEIGHT, shops.DADO_HEIGHT)), finish.get("material", "plaster"), srgb(finish["dado"]), uv=finish.get("uv"))
        b.box(*shops.wall_slab(axis, face_at, normal, piece, 0.0, shops.SKIRTING_DEPTH, (0.0, shops.SKIRTING_HEIGHT)), "wood", srgb(finish["trim"]), uv=wood_uv)


# ---------- outside ----------

def ashlar_cuts(room, openings: list, z_from: float, z_to: float, margin: float) -> list:
    """Stretches of a course taken by openings grown by margin (their jambs and voussoirs), facade u."""
    hit = [opening for opening in openings if opening.bottom < z_to and opening.apex + margin > z_from]

    return [(opening.u - room.half - opening.width / 2.0 - margin, opening.u - room.half + opening.width / 2.0 + margin) for opening in hit]


def ashlar_course(room, openings: list, row: int) -> list:
    """(u from, u to, z from, z to) of the blocks of one course, joints staggered from course to course."""
    z_from = row * ASHLAR_ROW
    z_to = min(z_from + ASHLAR_ROW, room.storey - 0.3) - 0.03
    spans = shops.free_spans(-room.house.half, room.house.half, ashlar_cuts(room, openings, z_from, z_to, VOUSSOIR_DEPTH + 0.05))
    blocks = []

    for span_from, span_to in spans:
        joints = [span_from]

        while joints[-1] < span_to - 0.2:
            joints.append(min(span_to, joints[-1] + ASHLAR_LENGTHS[(len(joints) + row) % 2]))

        blocks += [(start, end - 0.03, z_from, z_to) for start, end in zip(joints, joints[1:])]

    return blocks


def build_ashlar(b: Builder, room, openings: list) -> None:
    """Rusticated stone over the ground storey of the street front."""
    rows = int((room.storey - 0.3) / ASHLAR_ROW) + 1
    blocks = [block for row in range(rows) for block in ashlar_course(room, openings, row)]
    stone = srgb(STONE["clara"])

    for row in range(rows):
        backing_course(b, room, openings, row)

    for u_from, u_to, z_from, z_to in blocks:
        b.box((u_from, -ASHLAR_PROUD, z_from), (u_to, -0.015, z_to), "plaster", stone)

    b.box((-room.house.half, -ASHLAR_PROUD - 0.06, room.storey - 0.3), (room.house.half, 0.0, room.storey - 0.1), "stone", srgb(STONE["media"]))


def backing_course(b: Builder, room, openings: list, row: int) -> None:
    """Darker mortar behind one course: it shows in the joints and round the arches, never across an opening."""
    z_from = row * ASHLAR_ROW
    z_to = min(z_from + ASHLAR_ROW, room.storey - 0.3)
    spans = shops.free_spans(-room.house.half, room.house.half, ashlar_cuts(room, openings, z_from, z_to, 0.0))
    joint = srgb(ASHLAR_JOINT)

    for span_from, span_to in spans:
        b.box((span_from, -0.015, z_from), (span_to, 0.0, z_to), "paint", joint)


def build_jambs(b: Builder, room, opening: Opening) -> None:
    """Stone jambs from the sill (or the ground) up to the springing of the arch."""
    u, half = opening.u - room.half, opening.width / 2.0
    stone = srgb(STONE["clara"])

    for side_sign in (-1, 1):
        inner = u + side_sign * (half + 0.02)
        outer = u + side_sign * (half + 0.02 + VOUSSOIR_DEPTH)
        b.box((min(inner, outer), -0.07, opening.bottom), (max(inner, outer), 0.0, opening.spring), "plaster", stone)


def build_voussoirs(b: Builder, room, opening: Opening) -> None:
    """Wedge stones round a round-headed opening, a raised keystone at the top."""
    u, radius = opening.u - room.half, opening.width / 2.0 + 0.02
    angles = [math.pi * index / VOUSSOIRS for index in range(VOUSSOIRS + 1)]
    stone = srgb(STONE["clara"])

    for index in range(VOUSSOIRS):
        first, second = angles[index] + 0.01, angles[index + 1] - 0.01
        inner = [(u + radius * math.cos(angle), opening.spring + radius * math.sin(angle)) for angle in (first, second)]
        outer = [(u + (radius + VOUSSOIR_DEPTH) * math.cos(angle), opening.spring + (radius + VOUSSOIR_DEPTH) * math.sin(angle)) for angle in (second, first)]
        proud = 0.12 if index == VOUSSOIRS // 2 else 0.07
        b.prism(inner + outer, -proud, 0.0, "plaster", stone)


def build_portal(b: Builder, room) -> None:
    """Pilasters and an entablature round the street door, a gilt mortar and pestle on the cornice."""
    door_u, door_width, door_height, _ = room.door
    half = door_width / 2.0 + VOUSSOIR_DEPTH + 0.1
    stone = srgb(STONE["clara"])
    top = door_height + VOUSSOIR_DEPTH + 0.12

    for side_sign in (-1, 1):
        u = door_u + side_sign * (half + 0.18)
        b.box((u - 0.2, -0.16, 0.0), (u + 0.2, 0.0, top), "plaster", stone)
        b.box((u - 0.24, -0.2, 0.0), (u + 0.24, 0.0, 0.3), "plaster", srgb(STONE["media"]))

    b.box((door_u - half - 0.45, -0.24, top), (door_u + half + 0.45, 0.0, top + 0.22), "plaster", stone)
    b.box((door_u - half - 0.55, -0.32, top + 0.22), (door_u + half + 0.55, 0.0, top + 0.32), "plaster", srgb(STONE["media"]))
    b.cylinder((door_u, -0.2, top + 0.32), 0.16, 0.22, 10, "metal", GILT, top_radius=0.2)
    b.beam((door_u + 0.02, -0.2, top + 0.4), (door_u + 0.2, -0.2, top + 0.78), 0.06, 0.06, "metal", GILT)


def build_oriel(b: Builder, room) -> None:
    """Oriel of the upper floor over the door: corbels, a plastered bay with three windows and a slate cap. The
    camera stops under it."""
    house = room.house
    half, reach, bottom, top, cap = ORIEL["half"], ORIEL["reach"], ORIEL["bottom"], ORIEL["top"], ORIEL["cap"]
    stone = srgb(STONE["clara"])
    corbels = [(half - 0.15 * step, reach - 0.22 * step, bottom - 0.18 * (step + 1)) for step in range(3)]

    for corbel_half, corbel_reach, corbel_bottom in corbels:
        b.camera_stop(b.box((-corbel_half, -corbel_reach, corbel_bottom), (corbel_half, 0.0, corbel_bottom + 0.18), "stone", stone))

    b.camera_stop(b.box((-half, -reach, bottom), (half, 0.0, top), house.wall_material, house.wall_tint))
    oriel_windows(b, half, reach, bottom, top)
    b.box((-half - 0.06, -reach - 0.06, top), (half + 0.06, 0.0, top + 0.12), "stone", stone)
    cap_points = [(-half - 0.1, -reach - 0.1, top + 0.12), (half + 0.1, -reach - 0.1, top + 0.12), (-half - 0.1, 0.0, top + 0.12), (half + 0.1, 0.0, top + 0.12), (-half + 0.3, 0.0, top + 0.12 + cap), (half - 0.3, 0.0, top + 0.12 + cap)]
    b.camera_stop(b.hull(cap_points, house.roof_material, house.roof_tint))


def oriel_windows(b: Builder, half: float, reach: float, bottom: float, top: float) -> None:
    """Glass and green frames on the front and the two cheeks of the oriel."""
    sill, head = bottom + 0.85, top - 0.35
    glass = srgb("3A4E66")
    front_panes = [(-half + 0.25, -0.1), (0.1, half - 0.25)]

    for u_from, u_to in front_panes:
        b.box((u_from, -reach - 0.02, sill), (u_to, -reach + 0.01, head), "glass", glass)
        b.box((u_from - 0.06, -reach - 0.05, sill - 0.06), (u_to + 0.06, -reach - 0.02, sill), "paint", GLAZING)
        b.box(((u_from + u_to) / 2.0 - 0.03, -reach - 0.05, sill), ((u_from + u_to) / 2.0 + 0.03, -reach - 0.02, head), "paint", GLAZING)
        b.box((u_from - 0.06, -reach - 0.05, head), (u_to + 0.06, -reach - 0.02, head + 0.06), "paint", GLAZING)

    for side_sign in (-1, 1):
        u = side_sign * half
        b.box((u - 0.02, -reach + 0.2, sill), (u + 0.02, -0.2, head), "glass", glass)
        b.box((u - 0.05, -reach + 0.14, head), (u + 0.05, -0.14, head + 0.06), "paint", GLAZING)


def build_show_globes(b: Builder) -> None:
    """Show globes standing in the Offizin windows, behind the glass."""
    for u, variant in GLOBES:
        frame = Matrix.Translation((u, 0.62, shops.FLOOR_TOP))
        shops.PROPS["show_globe"]["build"](b, frame, variant=variant)
        b.collider((-0.28, -0.28, 0.0), (0.28, 0.28, 1.74), frame)


def build_street_front(b: Builder, room, openings: dict) -> None:
    front = openings["front"]
    arched = [opening for opening in front if opening.top == "round"]

    build_ashlar(b, room, front)

    for opening in arched:
        build_voussoirs(b, room, opening)
        build_jambs(b, room, opening)

    build_portal(b, room)
    build_oriel(b, room)
    build_show_globes(b)


# ---------- assembly ----------

def build_shell(room) -> dict:
    b = Builder(f"shop_{room.shop_type}")
    openings = build_walls(b, room)

    build_floors(b, room)
    build_ceiling(b, room)

    for partition in room.partitions:
        shops.build_partition(b, room, partition)

    build_finishes(b, room)
    shops.build_roof(b, room)
    build_street_front(b, room, openings)

    for u, d, z in LIGHTS:
        b.light((u, d, z), LAMP_LIGHT, 1.3, 7.0)

    b.marker("shopkeeper", (*room.keeper, 0.0))

    return b.finish(town.SHOP_DIR / f"shop_{room.shop_type}.gltf", shops.shell_sidecar(room))
