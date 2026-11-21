"""Plan of the tavern and inn (docs/research/shops.md, references in the private refs repo, lojas/tavern).

After a real 19th-century inn plan: the entrance hall runs from the street door to the back with the inn's reception,
the taproom on one side (inglenook on the outer wall, the bar against the kitchen wall with a serving hatch) and the
Stube on the other (panelled, a tiled stove fed from the hall, wall benches round square tables); behind them the
kitchen, the store with the back door, and the music room with its stage. The guest rooms are upstairs, reached by
the boxed stair behind a door at the end of the hall.

tavern_shell.py builds the walls, ceilings and finishes from ROOMS and FRONT_WINDOWS; build_market_shops.py reads
PLAN (keeper, partitions, furnish). Coordinates as in shop_layouts.py: u across the facade, d into the lot.
"""

TAPROOM_WALL = -2.4  # axis of the wall between the hall and the taproom / kitchen
STUBE_WALL = 2.4  # axis of the wall between the hall and the Stube / music room
BACK_ROW = 12.6  # axis of the wall in front of the kitchen, the store and the back of the music room
STUBE_BACK = 8.4  # axis of the wall between the Stube and the music room
HALF_WALL = 0.15
ROOMS = {  # name -> (u from, u to, d from, d to) inside the walls
    "taproom": (-8.55, TAPROOM_WALL - HALF_WALL, 0.3, BACK_ROW - HALF_WALL),
    "kitchen": (-8.55, TAPROOM_WALL - HALF_WALL, BACK_ROW + HALF_WALL, 19.1),
    "hall": (TAPROOM_WALL + HALF_WALL, STUBE_WALL - HALF_WALL, 0.3, BACK_ROW - HALF_WALL),
    "store": (TAPROOM_WALL + HALF_WALL, STUBE_WALL - HALF_WALL, BACK_ROW + HALF_WALL, 19.1),
    "stube": (STUBE_WALL + HALF_WALL, 8.55, 0.3, STUBE_BACK - HALF_WALL),
    "music": (STUBE_WALL + HALF_WALL, 8.55, STUBE_BACK + HALF_WALL, 19.1),
}
FRONT_WINDOWS = (-7.0, -4.2, 4.2, 7.0)  # u of the leaded windows of the ground floor, two to a room
WINDOW = (1.4, 0.95, 1.7)  # width, sill, height of the street windows (the sides take the same through SHOPS)
WAINSCOT, PLASTERED, PANELLED = "tavern_wainscot", "tavern_limewash", "stube_panel"
PARTITIONS = (
    ("u", TAPROOM_WALL, 0.3, BACK_ROW, dict(doors=[dict(at=10.0, width=2.0, height=2.6)], faces=(WAINSCOT, WAINSCOT))),
    ("u", TAPROOM_WALL, BACK_ROW, 19.1, dict(doors=[dict(at=16.0, width=1.0, height=2.2, leaf=("high", 1))], faces=(PLASTERED, PLASTERED))),
    ("u", STUBE_WALL, 0.3, STUBE_BACK, dict(doors=[dict(at=6.0, width=1.2, height=2.3, leaf=("high", -1))], faces=(WAINSCOT, PANELLED))),
    ("u", STUBE_WALL, STUBE_BACK, BACK_ROW, dict(doors=[dict(at=10.4, width=2.0, height=2.6)], faces=(WAINSCOT, WAINSCOT))),
    ("u", STUBE_WALL, BACK_ROW, 19.1, dict(faces=(PLASTERED, WAINSCOT))),
    ("d", BACK_ROW, -8.55, TAPROOM_WALL - HALF_WALL, dict(doors=[dict(at=-7.4, width=1.2, height=2.1, sill=1.05)], faces=(WAINSCOT, PLASTERED))),
    ("d", BACK_ROW, TAPROOM_WALL + HALF_WALL, STUBE_WALL - HALF_WALL, dict(doors=[dict(at=0.0, width=1.4, height=2.3, leaf=("high", 1))], faces=(WAINSCOT, PLASTERED))),
    ("d", STUBE_BACK, STUBE_WALL + HALF_WALL, 8.55, dict(faces=(PANELLED, WAINSCOT))),
)
STONE_FLOORS = tuple(ROOMS[name] for name in ("hall", "kitchen", "store"))


def furnish_taproom(f) -> None:
    """Inglenook with its settles on the outer wall, long tables by the windows, the bar against the kitchen wall."""
    f.on_wall("left", "inglenook", 5.5)
    f.put("mounted_head", -7.1, 5.5, 90.0, z=0.35, variant="boar")
    f.put("settle_bench", -6.6, 3.6, 180.0)
    f.put("settle_bench", -6.6, 7.4, 0.0)
    f.put("rug_ornate", -5.9, 5.5, 90.0, variant="red")
    f.put("armchair", -5.2, 5.5, -90.0)

    f.put("counter_straight", -5.2, 10.7)
    f.on_face("d", BACK_ROW - HALF_WALL, -1, "keg_rack", -5.8)
    f.on_face("d", BACK_ROW - HALF_WALL, -1, "bottle_shelf", -3.85)
    f.grid("bar_stool", (-6.3, -4.2), (9.95, 9.95), 4, 1)
    f.put("ceiling_beam_hooks", -5.2, 11.6, variant="sausages")

    f.put("tavern_table_set", -6.4, 1.6, 90.0)
    f.put("tavern_table_set", -3.9, 2.4)
    f.put("tavern_table_set", -3.9, 5.6)
    f.put("barrel_table", -3.9, 8.3)
    f.on_face("u", TAPROOM_WALL - HALF_WALL, -1, "menu_board", 7.6)
    f.on_face("u", TAPROOM_WALL - HALF_WALL, -1, "wall_lantern", 4.0, z=1.9, lit=False)
    f.on_wall("left", "wall_lantern", 9.6, z=1.9, lit=False)


def furnish_hall(f) -> None:
    """The inn's reception desk and key board, coats and luggage, the notice board, the door of the boxed stair."""
    f.put("reception_desk", -1.45, 5.0, 90.0)
    f.on_face("u", TAPROOM_WALL + HALF_WALL, 1, "key_board", 7.0)
    f.on_face("u", TAPROOM_WALL + HALF_WALL, 1, "notice_board", 8.2)
    f.on_face("u", STUBE_WALL - HALF_WALL, -1, "coat_rack_wall", 1.6)
    f.on_face("u", STUBE_WALL - HALF_WALL, -1, "luggage_pile", 3.6)
    f.on_face("u", STUBE_WALL - HALF_WALL, -1, "bench_long", 8.0)
    f.on_face("d", BACK_ROW - HALF_WALL, -1, "plank_door", -1.5)
    f.put("rug_runner", 0.0, 6.8, variant="red")
    f.put("hanging_lantern", 0.0, 4.0, lit=False)
    f.put("hanging_lantern", 0.0, 9.6, lit=False)
    f.on_face("u", STUBE_WALL - HALF_WALL, -1, "long_case_clock", 12.05)
    f.hang_picture("u", TAPROOM_WALL + HALF_WALL, 1, 2.2, "landscape")
    f.on_face("u", TAPROOM_WALL + HALF_WALL, 1, "wall_lantern", 9.2, z=1.9, lit=False)
    f.on_face("u", STUBE_WALL - HALF_WALL, -1, "wall_lantern", 4.6, z=1.9, lit=False)


def furnish_kitchen(f) -> None:
    """Range on the back wall, dresser and firewood on the outer wall, sink by the door, work table in the middle."""
    f.on_wall("back", "masonry_range", -7.1)
    f.on_face("d", BACK_ROW + HALF_WALL, 1, "crockery_dresser", -4.3)
    f.on_wall("left", "firewood_stack", 14.4)
    f.on_face("u", TAPROOM_WALL - HALF_WALL, -1, "stone_sink", 14.2)
    f.on_face("u", TAPROOM_WALL - HALF_WALL, -1, "pot_shelf", 17.9)
    f.put("kitchen_worktable", -5.6, 15.7)
    f.put("hanging_pan_rack", -5.6, 15.7)
    f.put("garlic_strings", -7.6, 17.2)
    f.put("ceiling_beam_hooks", -4.0, 17.6, variant="herbs")
    f.put("flour_sacks", -4.6, 18.5)
    f.put("barrel_group", -7.8, 17.0)
    f.put("chopping_block", -6.4, 14.2)


def furnish_store(f) -> None:
    """Kegs, barrels, crates and sacks round the back door to the yard."""
    f.on_wall("back", "plank_door", 0.0)
    f.put("barrel_group", -1.55, 18.45)
    f.put("barrel_group", 1.55, 18.45)
    f.on_face("u", TAPROOM_WALL + HALF_WALL, 1, "keg_rack", 13.7)
    f.on_face("u", STUBE_WALL - HALF_WALL, -1, "wall_shelf", 14.2, variant="boxes")
    f.put("sack_pile", 1.5, 16.4)


def furnish_stube(f) -> None:
    """Tiled stove backing onto the hall, wall benches under the windows and along the blind wall, three tables."""
    f.put("tiled_stove", 3.3, 7.5, 90.0)
    f.on_wall("front", "wall_bench", 7.3)
    f.on_wall("front", "wall_bench", 4.3)
    f.on_wall("right", "wall_bench", 2.1)
    f.on_wall("right", "wall_bench", 5.6)

    for u, d in ((7.3, 1.6), (4.3, 1.6), (7.3, 5.6)):
        f.put("stube_table", u, d)

    for u, d, degrees in ((6.25, 1.6, 90.0), (7.3, 2.65, 0.0), (4.3, 2.65, 0.0), (3.2, 1.6, 90.0), (6.25, 5.6, 90.0), (7.3, 6.65, 0.0)):
        f.put("stube_chair", u, d, degrees)

    f.put("wheel_chandelier", 5.6, 3.9)

    for along in (4.2, 7.0):
        f.on_wall("front", "curtain_pair", along, variant="cream")

    for along in (1.5, 3.7, 5.9):
        f.on_wall("right", "plate_shelf", along, z=2.26)

    for along in (4.6, 7.0):
        f.on_face("d", STUBE_BACK - HALF_WALL, -1, "plate_shelf", along, z=2.26)

    f.on_face("d", STUBE_BACK - HALF_WALL, -1, "wall_clock", 6.0)
    f.on_wall("right", "mounted_head", 7.6, z=0.4, variant="stag")


def furnish_music(f) -> None:
    """Stage in the back corner under bunting, round tables, a booth on the blind wall, darts and banners."""
    f.put("stage", 7.0, 17.95)
    f.put("bunting", 7.0, 16.9)
    f.put("round_table_set", 5.2, 10.6)
    f.put("round_table_set", 7.3, 13.4)
    f.put("round_table_set", 4.4, 15.2)
    f.on_wall("right", "tavern_booth", 10.0)
    f.on_wall("right", "dart_board", 15.6)
    f.on_face("u", STUBE_WALL + HALF_WALL, 1, "wall_banner", 14.0)
    f.on_face("u", STUBE_WALL + HALF_WALL, 1, "wall_banner", 16.6)
    f.put("barrel_table", 3.4, 18.4)
    f.put("hanging_lantern", 5.5, 12.5, lit=False)
    f.put("hanging_lantern", 5.5, 16.0, lit=False)


def furnish_tavern(f) -> None:
    """Room by room; the lit props come first (only the first few get a real light)."""
    furnish_taproom(f)
    furnish_stube(f)
    furnish_hall(f)
    furnish_kitchen(f)
    furnish_store(f)
    furnish_music(f)


PLAN = dict(keeper=(-4.6, 11.6), posts=(), partitions=PARTITIONS, stone_floors=STONE_FLOORS, furnish=furnish_tavern)
