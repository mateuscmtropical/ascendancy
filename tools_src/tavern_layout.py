"""Plan of the tavern and inn (docs/research/shops.md, references in the private refs repo, lojas/tavern).

The owner's sketch (2026-11-24): one big, nearly square tavern hall entered at its front-right corner on the low
floor; an L-shaped terrace a chest-height up (TERRACE) runs along the back wall and the right wall, its inner corner
rounded, reached by a ramp that climbs along the right wall from the door (a ramp, not steps: the serving girls carry
trays); the bar along the left wall with its flap at the front end; round tables below and on the terrace, the
inglenook and the musicians' stage up on the back band. As in a coaching inn, the inn has its own door on the side
street: a small hall with the reception and the boxed stair to the guest rooms upstairs. Behind the bar the kitchen,
behind the kitchen the pantry, behind the hall the store with the back door.

tavern_shell.py builds the walls, ceilings, the terrace and the ramp from ROOMS, TERRACE_* and FRONT_WINDOWS;
build_market_shops.py reads PLAN (keeper, partitions, furnish). Coordinates as in shop_layouts.py: u across the
facade (u < 0 on the side street), d into the lot.
"""

HALL_WALL = -3.0  # axis of the wall between the hall and the inn / kitchen / pantry strip on the side street
INN_BACK = 5.0  # axis of the wall between the inn's hall and the kitchen
HALL_BACK = 14.0  # axis of the wall behind the tavern hall (store) and behind the kitchen (pantry)
HALF_WALL = 0.15
BAR_MIDDLE = 5.4  # d of the middle of the bar run (it spans 6 m); the kitchen door opens on the floor just past it
KITCHEN_DOOR = 9.4
ROOMS = {  # name -> (u from, u to, d from, d to) inside the walls
    "hall": (HALL_WALL + HALF_WALL, 8.55, 0.3, HALL_BACK - HALF_WALL),
    "inn": (-8.55, HALL_WALL - HALF_WALL, 0.3, INN_BACK - HALF_WALL),
    "kitchen": (-8.55, HALL_WALL - HALF_WALL, INN_BACK + HALF_WALL, HALL_BACK - HALF_WALL),
    "pantry": (-8.55, HALL_WALL - HALF_WALL, HALL_BACK + HALF_WALL, 19.1),
    "store": (HALL_WALL + HALF_WALL, 8.55, HALL_BACK + HALF_WALL, 19.1),
}

TERRACE = 1.25  # rise of the terrace over the hall floor: chest height of a man standing below
TERRACE_BAND = 3.2  # depth of each arm of the L: one row of tables against the wall and an aisle
TERRACE_FILLET = 1.8  # radius of the rounded inner corner of the L
RAMP = dict(u_from=6.75, u_to=8.55, d_from=2.2, d_to=8.2)  # along the right wall, from the door landing up to the terrace
HALL = ROOMS["hall"]
BACK_EDGE = HALL[3] - TERRACE_BAND  # front edge of the back arm
SIDE_EDGE = HALL[1] - TERRACE_BAND  # inner edge of the right arm
TERRACE_PARTS = (  # (u from, u to, d from, d to) of the two arms; the right arm starts where the ramp arrives
    (HALL[0], HALL[1], BACK_EDGE, HALL[3]),
    (SIDE_EDGE, HALL[1], RAMP["d_to"], BACK_EDGE),
)

FRONT_WINDOWS = (-5.9, 0.6, 3.6)  # u of the leaded street windows: the inn's, two to the hall (its door is at u 7.1)
WINDOW = (1.4, 0.95, 1.7)  # width, sill, height of the street windows (the sides take the same through SHOPS)
INN_DOOR = dict(d=2.6, width=1.2, height=2.4)  # the inn's own door on the side street
WAINSCOT, PLASTERED = "tavern_wainscot", "tavern_limewash"
PARTITIONS = (
    ("u", HALL_WALL, 0.3, INN_BACK, dict(doors=[dict(at=1.5, width=1.2, height=2.4)], faces=(WAINSCOT, WAINSCOT))),
    ("u", HALL_WALL, INN_BACK, HALL_BACK, dict(doors=[dict(at=KITCHEN_DOOR, width=1.0, height=2.2, leaf=("high", 1))], faces=(PLASTERED, WAINSCOT))),
    ("u", HALL_WALL, HALL_BACK, 19.1, dict(doors=[dict(at=16.6, width=1.0, height=2.2, leaf=("high", -1))], faces=(PLASTERED, PLASTERED))),
    ("d", INN_BACK, -8.55, HALL_WALL - HALF_WALL, dict(faces=(WAINSCOT, PLASTERED))),
    ("d", HALL_BACK, -8.55, HALL_WALL - HALF_WALL, dict(doors=[dict(at=-4.3, width=1.0, height=2.2, leaf=("high", 1))], faces=(PLASTERED, PLASTERED))),
    ("d", HALL_BACK, HALL_WALL + HALF_WALL, 8.55, dict(faces=(WAINSCOT, PLASTERED))),
)
STONE_FLOORS = tuple(ROOMS[name] for name in ("inn", "kitchen", "pantry", "store"))
TERRACE_TOP = 0.05 + TERRACE  # build_market_shops.FLOOR_TOP + TERRACE


def furnish_hall(f) -> None:
    """The U bar on the left wall (casks and bottles behind it, the flap at the front end), stools along it, six round
    tables on the low floor; shields and banners on the tall wall over the ramp."""
    f.on_face("u", HALL[0], 1, "tavern_bar", BAR_MIDDLE)
    f.on_face("u", HALL[0], 1, "keg_rack", BAR_MIDDLE - 1.3)
    f.on_face("u", HALL[0], 1, "bottle_shelf", BAR_MIDDLE + 0.9)
    f.grid("bar_stool", (-0.2, -0.2), (BAR_MIDDLE - 2.4, BAR_MIDDLE + 2.4), 1, 6)
    f.put("ceiling_beam_hooks", -1.9, BAR_MIDDLE, variant="sausages")

    for u, d in ((1.7, 2.3), (4.5, 2.3), (1.7, 5.1), (4.5, 5.1), (1.7, 7.9), (4.2, 7.9)):
        f.put("round_table_set", u, d)

    f.on_face("d", HALL[2], 1, "menu_board", -1.5)
    f.on_face("d", HALL[2], 1, "wall_banner", 5.15, z=1.4)
    f.put("wheel_chandelier", 3.1, 5.1)
    f.on_wall("right", "shield_wall", 5.2, z=1.7)
    f.on_wall("right", "wall_banner", 3.0, z=1.6)
    f.on_wall("right", "wall_banner", 7.4, z=1.6)


def furnish_terrace(f) -> None:
    """Inglenook with two armchairs and the musicians' stage on the back arm, tables at the corner of the L, a standing
    barrel table in the corner, the dart board and a stag's head over the right arm, banners on the walls."""
    f.on_face("d", HALL[3], -1, "inglenook", 1.8, z=TERRACE_TOP)
    f.put("mounted_head", 1.8, 12.4, 0.0, z=TERRACE_TOP + 0.35, variant="boar")
    f.put("rug_ornate", 1.8, 11.7, 0.0, z=TERRACE_TOP, variant="red")
    f.put("armchair", 0.9, 11.5, 160.0, z=TERRACE_TOP)
    f.put("armchair", 2.7, 11.5, -160.0, z=TERRACE_TOP)
    f.put("stage", -1.35, 12.85, z=TERRACE_TOP)
    f.put("bunting", -1.35, 12.2)
    f.put("round_table_set", 4.8, 12.8, z=TERRACE_TOP)
    f.put("round_table_set", 7.5, 11.0, z=TERRACE_TOP)
    f.put("barrel_table", 7.9, 13.3, z=TERRACE_TOP)
    f.on_wall("right", "dart_board", 9.4, z=TERRACE_TOP)
    f.on_wall("right", "mounted_head", 12.4, z=TERRACE_TOP + 0.4, variant="stag")
    f.on_face("u", HALL[0], 1, "wall_banner", 12.3, z=TERRACE_TOP + 0.3)
    f.on_face("d", HALL[3], -1, "wall_banner", 4.6, z=TERRACE_TOP + 0.3)
    f.on_face("d", HALL[3], -1, "wall_banner", 6.4, z=TERRACE_TOP + 0.3)
    f.put("hanging_lantern", 4.8, 12.8, lit=False)
    f.put("hanging_lantern", 7.5, 11.0, lit=False)


def furnish_inn(f) -> None:
    """The inn's reception desk, the door of the boxed stair, notices and a bench by the side door."""
    f.on_face("d", INN_BACK - HALF_WALL, -1, "reception_desk", -7.1)
    f.on_face("d", INN_BACK - HALF_WALL, -1, "plank_door", -4.4)
    f.on_face("u", HALL_WALL - HALF_WALL, -1, "key_board", 4.1)
    f.on_face("u", HALL_WALL - HALF_WALL, -1, "notice_board", 3.0)
    f.on_face("d", 0.3, 1, "luggage_pile", -7.6)
    f.on_face("d", 0.3, 1, "bench_long", -5.7)
    f.put("rug_runner", -6.0, 2.6, 90.0, variant="red")
    f.put("hanging_lantern", -5.8, 2.6, lit=False)


def furnish_kitchen(f) -> None:
    """Range on the back wall, dresser and sink on the bar wall, firewood on the street wall, work table in the middle."""
    f.on_face("d", HALL_BACK - HALF_WALL, -1, "masonry_range", -6.8)
    f.on_face("u", HALL_WALL - HALF_WALL, -1, "crockery_dresser", 6.8)
    f.on_face("u", HALL_WALL - HALF_WALL, -1, "stone_sink", 11.7)
    f.on_face("d", INN_BACK + HALF_WALL, 1, "pot_shelf", -5.0)
    f.on_wall("left", "firewood_stack", 11.8)
    f.put("kitchen_worktable", -5.8, 9.0)
    f.put("hanging_pan_rack", -5.8, 9.0)
    f.put("garlic_strings", -7.6, 6.2)
    f.put("ceiling_beam_hooks", -4.4, 12.4, variant="herbs")
    f.put("chopping_block", -4.4, 12.2)
    f.put("flour_sacks", -7.7, 6.0)


def furnish_pantry(f) -> None:
    """Barrels, sacks and the kegs waiting for the bar."""
    f.put("barrel_group", -7.6, 18.4)
    f.put("barrel_group", -5.4, 18.4)
    f.on_face("u", HALL_WALL - HALF_WALL, -1, "keg_rack", 18.2)
    f.put("sack_pile", -6.0, 15.2)


def furnish_store(f) -> None:
    """Kegs, barrels, crates and sacks round the back door to the yard; an upturned barrel to tap the next keg on."""
    f.on_wall("back", "plank_door", 3.0)
    f.put("barrel_group", 0.4, 18.45)
    f.put("barrel_group", 5.6, 18.45)
    f.on_wall("right", "wall_shelf", 16.6, variant="boxes")
    f.on_wall("back", "keg_rack", -1.6)
    f.put("crate_stack", 7.7, 18.5)
    f.put("crate_stack", 7.9, 14.9, 90.0)
    f.put("crate_open", 6.6, 18.6)
    f.put("barrel_table", 1.6, 16.2)
    f.put("sack_pile", -1.6, 15.2)
    f.put("flour_sacks", 4.8, 15.0)


def furnish_tavern(f) -> None:
    """Room by room; the lit props come first (only the first few get a real light)."""
    furnish_terrace(f)
    furnish_hall(f)
    furnish_inn(f)
    furnish_kitchen(f)
    furnish_pantry(f)
    furnish_store(f)


BLIND_WALLS = {"left": ((INN_DOOR["d"] - 1.5, INN_DOOR["d"] + 1.5),)}  # no side window crowding the inn's door
PLAN = dict(keeper=(HALL[0] + 1.03, BAR_MIDDLE + 0.9), posts=(), partitions=PARTITIONS, stone_floors=STONE_FLOORS, blind_walls=BLIND_WALLS, furnish=furnish_tavern)
