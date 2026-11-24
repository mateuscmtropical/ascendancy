"""Plan of the tavern and inn (docs/research/shops.md, references in the private refs repo, lojas/tavern).

The owner's sketch (2026-11-24): one big, nearly square tavern hall entered at its front-right corner on the low
floor; an L-shaped terrace a chest-height up (TERRACE) runs along the back wall and the right wall, its inner corner
rounded, reached by a ramp that climbs along the right wall from the door (a ramp, not steps: the serving girls carry
trays); the bar along the left wall with its flap at the front end; round tables below and on the terrace, the
inglenook and the musicians' stage up on the back band. As in a coaching inn, the inn has its own door on the side
street: its hall with the reception and a dog-leg stair up to the guest floor (2026-11-24 plan): a gallery along the
side street, two corridors, two twin rooms on the street, three chambers at the back (two with a fireplace on the
kitchen and inglenook stacks), a washroom with the privy, the linen room and the guests' parlour between the corridors.
Behind the bar the kitchen (doors to the hall and to the reception), behind the kitchen the pantry, behind the hall the
store with the back door.

tavern_shell.py builds the walls, ceilings, the terrace and the ramp from ROOMS, TERRACE_* and FRONT_WINDOWS;
tavern_inn.py the stair and the guest floor from STAIR_* and UPPER_*; build_market_shops.py reads PLAN (keeper,
partitions, furnish). Coordinates as in shop_layouts.py: u across the
facade (u < 0 on the side street), d into the lot.
"""

HALL_WALL = -3.0  # axis of the wall between the hall and the inn / kitchen / pantry strip on the side street
INN_BACK = 6.8  # axis of the wall between the inn's hall and the kitchen
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
TERRACE_BAND = 3.6  # depth of each arm of the L: one row of tables or the hearth chairs, and a 1.2 m aisle by the rail
TERRACE_FILLET = 1.8  # radius of the rounded inner corner of the L
RAMP = dict(u_from=6.75, u_to=8.55, d_from=2.2, d_to=8.2)  # along the right wall, from the door landing up to the terrace
HALL = ROOMS["hall"]
BACK_EDGE = HALL[3] - TERRACE_BAND  # front edge of the back arm
SIDE_EDGE = HALL[1] - TERRACE_BAND  # inner edge of the right arm
TERRACE_PARTS = (  # (u from, u to, d from, d to) of the two arms; the right arm starts where the ramp arrives
    (HALL[0], HALL[1], BACK_EDGE, HALL[3]),
    (SIDE_EDGE, HALL[1], RAMP["d_to"], BACK_EDGE),
)

FRONT_WINDOWS = (-7.0, 0.6, 3.6)  # u of the leaded street windows: the inn's (clear of the stair), two to the hall (door at u 7.1)
WINDOW = (1.4, 0.95, 1.7)  # width, sill, height of the street windows (the sides take the same through SHOPS)
INN_DOOR = dict(d=2.6, width=1.2, height=2.4)  # the inn's own door on the side street
WAINSCOT, PLASTERED = "tavern_wainscot", "tavern_limewash"
INN_HALL_DOOR = 6.0  # d of the door from the reception to the tavern hall: past the foot of the stair, behind the bar
INN_KITCHEN_DOOR = -5.15  # u of the door from the reception to the kitchen, beside the reception desk

# The dog-leg stair in the reception's corner by the hall wall: the first flight climbs along that wall toward the
# street, the half landing turns it, the second flight climbs back and arrives on the guest floor by the gallery.
UPPER_FLOOR = 5.2  # slab of the guest floor (the tavern's ground storey)
STAIR_RISERS = 15  # per flight
STAIR_RISE = UPPER_FLOOR / (2 * STAIR_RISERS)
STAIR_TREAD = 0.28
LANDING = (-5.45, HALL_WALL - HALF_WALL, 0.3, 1.4)  # (u from, u to, d from, d to), the half landing against the street wall
STAIR_FOOT = LANDING[3] + (STAIR_RISERS - 1) * STAIR_TREAD  # d of the first riser of the first flight and the last of the second
FIRST_FLIGHT = (-4.3, HALL_WALL - HALF_WALL)  # u from, u to: from the reception floor up to the landing
SECOND_FLIGHT = (LANDING[0], -4.4)  # from the landing up to the guest floor
SPINE = (SECOND_FLIGHT[1], FIRST_FLIGHT[0])  # wall between the flights, up to the reception ceiling
STAIR_WELL = (LANDING[0], LANDING[1], LANDING[2], STAIR_FOOT)  # open through the reception ceiling and the guest floor

UPPER_HEIGHT = 3.0  # the second storey of the tavern spec
UPPER_CEILING = 2.6  # over the guest floor's slab
UPPER_FRONT = -0.1  # inner face of the jettied street wall upstairs
UPPER_ROOMS = {  # name -> (u from, u to, d from, d to) inside the walls of the guest floor
    "gallery": (-8.55, -5.6, UPPER_FRONT, 13.25),
    "corridor": (-5.6, 8.55, 5.6, 7.4),
    "back_corridor": (-5.6, 8.55, 11.0, 13.25),
    "street_twin": (-2.85, 2.8, UPPER_FRONT, 5.3),
    "corner_twin": (3.1, 8.55, UPPER_FRONT, 5.3),
    "washroom": (-5.3, -3.15, 7.7, 10.7),
    "linen": (-2.85, 1.5, 7.7, 10.7),
    "parlour": (1.8, 8.55, 7.7, 10.7),
    "side_chamber": (-8.55, -3.05, 13.55, 19.1),
    "middle_chamber": (-2.75, 3.175, 13.55, 19.1),
    "corner_chamber": (3.475, 8.55, 13.55, 19.1),
}
ROOM_DOOR = dict(width=0.9, height=2.1)
UPPER_PARTITIONS = (
    ("u", HALL_WALL, UPPER_FRONT, 5.45, dict(faces=(None, PLASTERED))),
    ("d", 5.45, HALL_WALL - HALF_WALL, 8.55, dict(doors=[dict(at=-2.0, **ROOM_DOOR, leaf=("low", 1)), dict(at=4.0, **ROOM_DOOR, leaf=("low", 1))], faces=(WAINSCOT, PLASTERED))),
    ("u", 2.95, UPPER_FRONT, 5.3, dict(faces=(WAINSCOT, WAINSCOT))),
    ("d", 7.55, -5.6, 8.55, dict(doors=[dict(at=-4.7, **ROOM_DOOR, leaf=("high", 1)), dict(at=-0.6, **ROOM_DOOR, leaf=("high", 1)), dict(at=5.2, width=1.4, height=2.2)], faces=(PLASTERED, PLASTERED))),
    ("d", 10.85, -5.6, 8.55, dict(doors=[dict(at=5.2, width=1.4, height=2.2)], faces=(PLASTERED, PLASTERED))),
    ("u", -5.45, 7.4, 11.0, dict(faces=(PLASTERED, PLASTERED))),
    ("u", HALL_WALL, 7.7, 10.7, dict(faces=(PLASTERED, PLASTERED))),
    ("u", 1.65, 7.7, 10.7, dict(faces=(PLASTERED, WAINSCOT))),
    ("d", 13.4, -8.55, 8.55, dict(doors=[dict(at=-4.5, **ROOM_DOOR, leaf=("high", 1)), dict(at=-1.6, **ROOM_DOOR, leaf=("high", 1)), dict(at=5.0, **ROOM_DOOR, leaf=("high", 1))], faces=(PLASTERED, WAINSCOT))),
    ("u", -2.9, 13.55, 19.1, dict(faces=(WAINSCOT, WAINSCOT))),
    ("u", 3.325, 13.55, 19.1, dict(faces=(WAINSCOT, WAINSCOT))),
)
UPPER_WINDOWS = {  # side -> (along, width) of the casements upstairs: u on the street and back walls, d on the side street
    "front": ((-7.0, 1.2), (0.0, 1.2), (5.9, 1.2)),
    "left": ((2.6, 1.2), (6.5, 1.2), (10.0, 1.2), (16.3, 1.2)),
    "back": ((-5.8, 1.2), (0.2, 1.2), (6.0, 1.2)),
}
UPPER_WINDOW = (0.85, 1.35)  # sill, height over the guest floor
CHIMNEY_BREASTS = (-6.8, 1.8)  # u of the kitchen and inglenook stacks, each a fireplace in a back chamber
UPPER_LIGHTS = ((-7.0, 3.0), (-7.0, 10.0), (1.0, 6.5), (1.0, 12.1), (0.0, 2.6), (5.8, 2.6), (5.2, 9.2), (-5.8, 16.3), (0.2, 16.3), (6.0, 16.3))
PARTITIONS = (
    ("u", HALL_WALL, 0.3, INN_BACK, dict(doors=[dict(at=INN_HALL_DOOR, width=0.9, height=2.2)], faces=(WAINSCOT, WAINSCOT))),
    ("u", HALL_WALL, INN_BACK, HALL_BACK, dict(doors=[dict(at=KITCHEN_DOOR, width=1.0, height=2.2, leaf=("high", 1))], faces=(PLASTERED, WAINSCOT))),
    ("u", HALL_WALL, HALL_BACK, 19.1, dict(doors=[dict(at=16.6, width=1.0, height=2.2, leaf=("high", -1))], faces=(PLASTERED, PLASTERED))),
    ("d", INN_BACK, -8.55, HALL_WALL - HALF_WALL, dict(doors=[dict(at=INN_KITCHEN_DOOR, width=0.9, height=2.2, leaf=("high", 1))], faces=(WAINSCOT, PLASTERED))),
    ("d", HALL_BACK, -8.55, HALL_WALL - HALF_WALL, dict(doors=[dict(at=-4.3, width=1.0, height=2.2, leaf=("high", 1))], faces=(PLASTERED, PLASTERED))),
    ("d", HALL_BACK, HALL_WALL + HALF_WALL, 8.55, dict(faces=(WAINSCOT, PLASTERED))),
)
STONE_FLOORS = tuple(ROOMS[name] for name in ("inn", "kitchen", "pantry", "store"))
TERRACE_TOP = 0.05 + TERRACE  # build_market_shops.FLOOR_TOP + TERRACE
# Round table sets (2.05 m) on the low floor, 1.2 m aisles along the stools, along the street wall, between the columns
# and the rows; the door's lane keeps a standing barrel table instead of a fifth set.
LOW_TABLES = ((2.23, 2.53), (2.23, 5.78), (5.48, 5.78), (2.23, 9.03))


def furnish_hall(f) -> None:
    """The U bar on the left wall (casks and bottles behind it, the flap at the front end), stools along it, four round
    tables and a standing barrel table on the low floor between 1.2 m aisles; shields and banners on the tall wall over
    the ramp."""
    f.on_face("u", HALL[0], 1, "tavern_bar", BAR_MIDDLE)
    f.on_face("u", HALL[0], 1, "bottle_shelf", BAR_MIDDLE - 1.65)  # the reception's door opens behind the bar, between the two
    f.on_face("u", HALL[0], 1, "keg_rack", BAR_MIDDLE + 2.3)
    f.grid("bar_stool", (-0.2, -0.2), (BAR_MIDDLE - 2.4, BAR_MIDDLE + 2.4), 1, 6)
    f.put("ceiling_beam_hooks", -1.9, BAR_MIDDLE, variant="sausages")

    for u, d in LOW_TABLES:
        f.put("round_table_set", u, d)

    f.put("barrel_table", 5.2, 2.5)

    f.on_face("d", HALL[2], 1, "menu_board", -1.5)
    f.on_face("d", HALL[2], 1, "wall_banner", 5.15, z=1.4)
    f.put("wheel_chandelier", 3.85, 4.15)
    f.on_wall("right", "shield_wall", 5.2, z=1.7)
    f.on_wall("right", "wall_banner", 3.0, z=1.6)
    f.on_wall("right", "wall_banner", 7.4, z=1.6)


def furnish_terrace(f) -> None:
    """Inglenook with a plank bench and two stools at the fire, the musicians' stage on the back arm, tables at the
    corner of the L, casks stored in the corner, the dart board and a stag's head over the right arm, banners."""
    f.on_face("d", HALL[3], -1, "inglenook", 1.8, z=TERRACE_TOP)
    f.put("mounted_head", 1.8, 12.4, 0.0, z=TERRACE_TOP + 0.35, variant="boar")
    f.put("bench_long", 1.8, 11.95, 180.0, z=TERRACE_TOP)
    f.put("stool_round", 0.6, 12.35, z=TERRACE_TOP)
    f.put("stool_round", 3.0, 12.35, z=TERRACE_TOP)
    f.put("stage", -1.35, 12.85, z=TERRACE_TOP)
    f.put("bunting", -1.35, 12.2)
    f.put("round_table_set", 4.8, 12.8, z=TERRACE_TOP)
    f.put("round_table_set", 7.5, 11.0, z=TERRACE_TOP)
    f.put("barrel_group", 7.8, 13.3, z=TERRACE_TOP)
    f.on_wall("right", "dart_board", 9.4, z=TERRACE_TOP)
    f.on_wall("right", "mounted_head", 12.4, z=TERRACE_TOP + 0.4, variant="stag")
    f.on_face("u", HALL[0], 1, "wall_banner", 12.3, z=TERRACE_TOP + 0.3)
    f.on_face("d", HALL[3], -1, "wall_banner", 4.6, z=TERRACE_TOP + 0.3)
    f.on_face("d", HALL[3], -1, "wall_banner", 6.4, z=TERRACE_TOP + 0.3)
    f.put("hanging_lantern", 4.8, 12.8, lit=False)
    f.put("hanging_lantern", 7.5, 11.0, lit=False)


RECEPTION_DESK = -7.35  # u of the reception desk on the kitchen wall; the innkeeper stands behind it
INNKEEPER = (RECEPTION_DESK, INN_BACK - HALF_WALL - 0.45)


def furnish_inn(f) -> None:
    """The reception desk (guest book, bell and the key board behind the innkeeper) facing the side door, notices on
    the stair's spine wall, a bench under the street window, luggage under the landing, a runner to the desk."""
    f.on_face("d", INN_BACK - HALF_WALL, -1, "reception_desk", RECEPTION_DESK)
    f.on_face("u", SPINE[0], -1, "notice_board", 3.3)  # on the stair's spine wall, facing the side door
    f.on_face("u", SPINE[0], -1, "wall_lantern", 4.6)
    f.on_wall("left", "wall_lantern", 4.4)
    f.on_face("d", 0.3, 1, "bench_long", FRONT_WINDOWS[0])
    f.on_face("d", 0.3, 1, "luggage_pile", -4.9)
    f.put("rug_runner", -7.2, 3.0, variant="red")
    f.put("hanging_lantern", -7.0, 3.0, lit=False)
    f.block("escada", (FIRST_FLIGHT[0], FIRST_FLIGHT[1], LANDING[3], STAIR_FOOT))


def furnish_kitchen(f) -> None:
    """Range on the back wall, dresser on the reception wall, sink on the bar wall, firewood on the street
    wall, work table and chopping block in the middle."""
    f.on_face("d", HALL_BACK - HALF_WALL, -1, "masonry_range", -6.8)
    f.on_face("d", INN_BACK + HALF_WALL, 1, "crockery_dresser", -6.75)
    f.on_face("u", HALL_WALL - HALF_WALL, -1, "stone_sink", 11.7)
    f.on_wall("left", "firewood_stack", 11.8)
    f.put("kitchen_worktable", -5.6, 9.3)
    f.put("hanging_pan_rack", -5.6, 9.3)
    f.put("garlic_strings", -5.6, 11.6)
    f.put("ceiling_beam_hooks", -4.4, 12.4, variant="herbs")
    f.put("chopping_block", -7.6, 10.3)


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


def guest_floor(f):
    """Furnisher of the guest floor: its own street wall (jettied) and ceiling."""
    upper = f.upstairs(UPPER_FLOOR)
    upper.front, upper.ceiling = UPPER_FRONT, UPPER_FLOOR + UPPER_CEILING
    upper.windows, upper.window_list = {}, []  # the hall's windows are not this floor's (its casements stand clear of the furniture)

    return upper


def furnish_twin_rooms(upper) -> None:
    """Two beds a room with their heads to the street wall either side of the casement, a trunk at each foot."""
    washstands = {"street_twin": ("u", UPPER_ROOMS["street_twin"][0], 1), "corner_twin": ("u", UPPER_ROOMS["corner_twin"][1], -1)}

    for room_name, washstand_face in washstands.items():
        u_from, u_to, _, _ = UPPER_ROOMS[room_name]
        middle = (u_from + u_to) / 2.0

        for side_sign in (-1, 1):
            upper.on_wall("front", "bed_single", middle + side_sign * 1.55)
            upper.put("bed_trunk", middle + side_sign * 1.55, 2.35)

        upper.on_face(*washstand_face, "washstand", 3.4)
        upper.put("rug", middle, 3.0)
        upper.put("hanging_lantern", middle, 2.6, lit=False)

    upper.on_face("u", UPPER_ROOMS["corner_twin"][0], 1, "wardrobe", 3.4)
    upper.on_face("u", UPPER_ROOMS["street_twin"][1], -1, "study_chair", 3.6)


def furnish_service_rooms(upper) -> None:
    """Washroom with the privy, the linen room, the guests' parlour; a settle and a table along the gallery, runners
    and lanterns down the corridors."""
    washroom, linen, parlour, gallery = (UPPER_ROOMS[name] for name in ("washroom", "linen", "parlour", "gallery"))

    upper.on_face("d", washroom[3], -1, "latrine_stall", -3.7)
    upper.on_face("u", washroom[0], 1, "washstand", 9.6)
    upper.on_face("u", washroom[1], -1, "towel_rack", 8.6)
    upper.on_face("d", linen[3], -1, "linen_press", -1.5)
    upper.on_face("u", linen[0], 1, "wall_shelf", 9.0, variant="boxes")
    upper.on_face("u", linen[1], -1, "laundry_tubs", 9.0)
    upper.on_face("u", parlour[0], 1, "settle_bench", 9.2)
    upper.on_wall("right", "console_table", 9.2)
    upper.put("armchair", 7.0, 8.5, 135.0)
    upper.put("armchair", 7.0, 9.9, 45.0)
    upper.put("rug", 7.0, 9.2, 90.0)
    upper.put("candle_stand", 3.3, 10.2)
    upper.on_wall("left", "settle_bench", 4.5)
    upper.on_wall("left", "console_table", 8.3)
    upper.put("rug_runner", (gallery[0] + gallery[1]) / 2.0, 8.6, variant="red")

    for corridor in (UPPER_ROOMS["corridor"], UPPER_ROOMS["back_corridor"]):
        middle = (corridor[2] + corridor[3]) / 2.0
        upper.put("rug_runner", 2.0, middle, 90.0, variant="red")
        upper.put("hanging_lantern", 1.0, middle, lit=False)


def furnish_chambers(upper) -> None:
    """The back chambers: a canopy bed against a side wall, a fireplace on the kitchen and inglenook stacks with an
    armchair before it, wardrobe, washstand and a trunk at the foot of the bed."""
    side, middle, corner = (UPPER_ROOMS[name] for name in ("side_chamber", "middle_chamber", "corner_chamber"))

    for u in CHIMNEY_BREASTS:
        upper.on_face("d", side[2], 1, "fireplace", u)
        upper.put("armchair", u, 15.4)
        upper.put("rug", u, 15.6)

    upper.on_face("u", side[1], -1, "bed_canopy", 17.0)
    upper.on_wall("back", "wardrobe", -7.8)
    upper.on_wall("left", "washstand", 15.0)
    upper.put("bed_trunk", -5.6, 17.0, 90.0)
    upper.on_face("u", middle[0], 1, "bed_canopy", 17.0)
    upper.on_wall("back", "wardrobe", 2.2)
    upper.on_face("u", middle[1], -1, "washstand", 17.8)
    upper.put("bed_trunk", -0.25, 17.0, -90.0)
    upper.on_wall("right", "bed_canopy", 17.0)
    upper.on_face("d", corner[2], 1, "wardrobe", 7.7)
    upper.on_face("u", corner[0], 1, "washstand", 16.5)
    upper.put("study_chair", 4.2, 18.3, 180.0)
    upper.put("bed_trunk", 5.95, 17.0, 90.0)

    for room in (side, middle, corner):
        upper.put("hanging_lantern", (room[0] + room[1]) / 2.0, 16.6, lit=False)


def furnish_tavern(f) -> None:
    """Room by room; the lit props come first (only the first few get a real light)."""
    furnish_terrace(f)
    furnish_hall(f)
    furnish_inn(f)
    furnish_kitchen(f)
    furnish_pantry(f)
    furnish_store(f)

    upper = guest_floor(f)
    upper.block("vão da escada", STAIR_WELL)
    furnish_twin_rooms(upper)
    furnish_service_rooms(upper)
    furnish_chambers(upper)


BLIND_WALLS = {"left": ((INN_DOOR["d"] - 1.5, INN_DOOR["d"] + 1.5),)}  # no side window crowding the inn's door
PLAN = dict(keeper=(HALL[0] + 1.03, BAR_MIDDLE - 0.6), posts=(), partitions=PARTITIONS, stone_floors=STONE_FLOORS, blind_walls=BLIND_WALLS, furnish=furnish_tavern)
