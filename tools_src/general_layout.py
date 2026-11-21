"""Plan of the general store and bakery (references in the private refs repo, lojas/general).

After grocers' shops and bakeries kept in museums: two shops behind one painted wooden shopfront. The grocer's on
the left, long and deep, its blind party wall lined from floor to ceiling with shelves over a bank of spice and
coffee drawers behind the long counter, hardware, crockery and barrels on the other side and the iron stove with
chairs in the middle; the storeroom behind it with the back door. The baker's shop on the right with its own street
door, the counter and the slanted bread shelves, tiled walls; the bakehouse behind it with the brick oven, the
kneading trough, the moulding table and proving racks.

general_shell.py builds the walls, floors, ceilings and the shopfront; build_market_shops.py reads PLAN (keeper,
partitions, furnish). Coordinates as in shop_layouts.py: u across the facade, d into the lot.
"""

SHOP_WALL = 1.2  # axis of the wall between the grocer's and the bakery, front to back
STORE_BACK = 12.6  # axis of the wall between the grocer's shop and its storeroom
BAKERY_BACK = 7.2  # axis of the wall between the baker's shop and the bakehouse
HALF_WALL = 0.15
ROOMS = {  # name -> (u from, u to, d from, d to) inside the walls
    "store": (-8.55, SHOP_WALL - HALF_WALL, 0.3, STORE_BACK - HALF_WALL),
    "storeroom": (-8.55, SHOP_WALL - HALF_WALL, STORE_BACK + HALF_WALL, 19.1),
    "bakery": (SHOP_WALL + HALF_WALL, 8.55, 0.3, BAKERY_BACK - HALF_WALL),
    "bakehouse": (SHOP_WALL + HALF_WALL, 8.55, BAKERY_BACK + HALF_WALL, 19.1),
}
BAKERY_DOOR = (4.95, 1.3, 2.7)  # u, width, height of the baker's own street door (the grocer's is SHOPS["general"]["door"])
FRONT_WINDOWS = ((-6.6, 2.6), (-0.8, 2.6), (2.9, 2.0), (7.3, 1.8))  # (u, width) of the shop windows
WINDOW_SILL, WINDOW_TOP = 0.55, 3.1
SIDE_WINDOWS = (3.6, 10.6, 15.6)  # d of the windows on the side street (bakery shop, bakehouse)
SIDE_WINDOW = (1.4, 1.0, 1.7)  # width, sill, height
BACK_WINDOWS = (-4.0, 2.2, 7.9)  # u of the back windows (storeroom, bakehouse)
BACK_WINDOW = (1.2, 1.4, 1.4)
GROCER, STOREROOM, BAKERY, BAKEHOUSE = "grocer_panel", "storeroom_lime", "bakery_tiles", "bakehouse_lime"
PARTITIONS = (
    ("u", SHOP_WALL, 0.3, BAKERY_BACK, dict(faces=(GROCER, BAKERY))),
    ("u", SHOP_WALL, BAKERY_BACK, STORE_BACK, dict(faces=(GROCER, BAKEHOUSE))),
    ("u", SHOP_WALL, STORE_BACK, 19.1, dict(doors=[dict(at=15.6, width=1.1, height=2.2, leaf=("low", 1))], faces=(STOREROOM, BAKEHOUSE))),
    ("d", STORE_BACK, -8.55, SHOP_WALL - HALF_WALL, dict(doors=[dict(at=-4.6, width=1.4, height=2.4, leaf=("high", 1))], faces=(GROCER, STOREROOM))),
    ("d", BAKERY_BACK, SHOP_WALL + HALF_WALL, 8.55, dict(doors=[dict(at=7.2, width=1.1, height=2.3)], faces=(BAKERY, BAKEHOUSE))),
)
GROCER_BAY = 1.56


def furnish_store(f) -> None:
    """Grocer's wall and the long counter on the party wall, goods on the other side, the stove in the middle."""
    bays = [2.0 + GROCER_BAY * index for index in range(6)]

    for along in bays:
        f.on_wall("left", "grocer_wall", along)

    f.put("shop_counter", -6.25, 4.4, 90.0)
    f.put("shop_counter", -6.25, 7.6, 90.0, seed=4)
    f.put("coffee_mill", -6.25, 10.0, 90.0)
    f.put("step_ladder", -7.7, 10.9, 90.0)
    f.on_face("u", SHOP_WALL - HALF_WALL, -1, "wall_shelf", 2.4, variant="boxes")
    f.on_face("u", SHOP_WALL - HALF_WALL, -1, "wall_shelf", 4.6, variant="bottles")
    f.on_face("u", SHOP_WALL - HALF_WALL, -1, "wall_shelf", 6.8, variant="tools")
    f.on_face("u", SHOP_WALL - HALF_WALL, -1, "barrel_group", 9.0)
    f.on_face("u", SHOP_WALL - HALF_WALL, -1, "sack_pile", 11.2)
    f.put("display_table", -1.4, 3.2, variant="fruit")
    f.put("display_table", -1.4, 5.6, variant="pottery")
    f.put("cast_iron_stove", -3.0, 8.6)
    f.put("bentwood_chair", -4.1, 8.6, 90.0)
    f.put("bentwood_chair", -1.9, 8.6, -90.0)
    f.put("barrel_table", -3.0, 10.4)
    f.put("hanging_oil_lamp", -4.6, 4.0, lit=False)
    f.put("hanging_oil_lamp", -4.6, 9.4, lit=False)
    f.on_face("d", STORE_BACK - HALF_WALL, -1, "wall_clock", -1.6)


def furnish_storeroom(f) -> None:
    """Sacks, barrels and crates round the walls, flour by the bakehouse door, the back door to the yard."""
    f.on_wall("back", "plank_door", -7.0)
    f.on_wall("left", "sack_pile", 14.2)
    f.on_wall("left", "sack_pile", 16.6)
    f.put("barrel_group", -0.3, 18.2)
    f.put("barrel_group", -2.5, 18.3)
    f.on_face("d", STORE_BACK + HALF_WALL, 1, "crate_stack", -1.0)
    f.on_face("u", SHOP_WALL - HALF_WALL, -1, "wall_shelf", 17.9, variant="jars")
    f.put("flour_sacks", -5.0, 15.8)
    f.put("hanging_oil_lamp", -4.0, 15.9, lit=False)


def furnish_bakery(f) -> None:
    """The baker's counter facing the street, the slanted bread shelves behind, the pastry case."""
    f.put("shop_counter", 3.9, 4.2, variant="bakery")
    f.put("pastry_case", 6.6, 4.2)
    f.on_face("d", BAKERY_BACK - HALF_WALL, -1, "bread_wall", 2.9)
    f.on_face("d", BAKERY_BACK - HALF_WALL, -1, "bread_wall", 5.0, seed=8)
    f.on_face("u", SHOP_WALL + HALF_WALL, 1, "wall_clock", 5.6)
    f.put("hanging_oil_lamp", 4.9, 2.4, lit=False)


def furnish_bakehouse(f) -> None:
    """Oven on the back wall, peels and firewood beside it, kneading trough, moulding table, proving racks."""
    f.on_wall("back", "bakehouse_oven", 5.0)
    f.on_wall("right", "peel_rack", 18.3)
    f.on_wall("right", "firewood_stack", 13.0)
    f.on_face("u", SHOP_WALL + HALF_WALL, 1, "kneading_trough", 10.0)
    f.on_face("u", SHOP_WALL + HALF_WALL, 1, "bread_rack", 12.6)
    f.on_face("u", SHOP_WALL + HALF_WALL, 1, "bread_rack", 14.0)
    f.put("dough_table", 4.9, 12.0)
    f.put("flour_sacks", 2.4, 17.4)
    f.put("hanging_oil_lamp", 4.9, 10.0, lit=False)


def furnish_general(f) -> None:
    furnish_store(f)
    furnish_storeroom(f)
    furnish_bakery(f)
    furnish_bakehouse(f)


PLAN = dict(keeper=(-7.25, 6.0), posts=(), partitions=PARTITIONS, furnish=furnish_general)
