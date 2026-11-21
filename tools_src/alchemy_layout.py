"""Plan of the apothecary-alchemist (references in the private refs repo, lojas/alchemy).

After old apothecaries and their museum reconstructions: the Offizin on the street under a white barrel vault, its
walls lined with the Repositorium (drawer banks under shelves of faience jars, gilt crowns) and the dispensing counter
in the middle facing the door, show globes in the arched windows; the herb room beside it (drawer cabinets, bundles
drying on poles under the ceiling); behind them the laboratory under a brick vault (hearth bench under its smoke hood,
copper still, the alchemist's cauldron), the stamping room with the big bronze mortar on its spring pole, and the
master's study with the locked poison cabinet.

alchemy_shell.py builds the walls, vaults, floors and finishes from ROOMS; build_market_shops.py reads PLAN (keeper,
partitions, furnish). Coordinates as in shop_layouts.py: u across the facade, d into the lot.
"""

HERB_WALL = -3.0  # axis of the wall between the herb room and the Offizin
LAB_WALL = -1.0  # axis of the wall between the stamping room / study and the laboratory
FRONT_ROW = 8.85  # axis of the wall behind the Offizin and the herb room
STUDY_WALL = 14.0  # axis of the wall between the stamping room and the study
HALF_WALL = 0.15
ROOMS = {  # name -> (u from, u to, d from, d to) inside the walls
    "offizin": (HERB_WALL + HALF_WALL, 8.55, 0.3, FRONT_ROW - HALF_WALL),
    "herbs": (-8.55, HERB_WALL - HALF_WALL, 0.3, FRONT_ROW - HALF_WALL),
    "lab": (LAB_WALL + HALF_WALL, 8.55, FRONT_ROW + HALF_WALL, 19.1),
    "mortar": (-8.55, LAB_WALL - HALF_WALL, FRONT_ROW + HALF_WALL, STUDY_WALL - HALF_WALL),
    "study": (-8.55, LAB_WALL - HALF_WALL, STUDY_WALL + HALF_WALL, 19.1),
}
VAULT_SPRING = 2.9  # springing of the vaults over the Offizin and the laboratory
VAULT_RISE = 1.25  # crown at 4.15, under the 4.2 m ceiling of the 4.6 m storey
VAULTS = {  # room -> (axis the vault spans, transverse arches along the other axis)
    "offizin": ("d", (1.6, 5.0)),
    "lab": ("u", (12.4, 15.8)),
}
FRONT_WINDOWS = (-5.85, 3.4, 6.6)  # u of the arched street windows (herb room, two in the Offizin)
WINDOW = (1.5, 0.6, 2.1)  # width, sill, height to the apex of the round-headed street windows
BACK_WINDOWS = (-4.8, 2.2, 5.6)  # u of the back windows (study, two in the laboratory), under the vault springing
BACK_WINDOW = (1.3, 1.2, 1.5)
OFFIZIN, HERBAL, LABORATORY, PANELLED = "offizin_plain", "herb_limewash", "lab_soot", "study_panel"
PARTITIONS = (
    ("u", HERB_WALL, 0.3, FRONT_ROW, dict(doors=[dict(at=4.5, width=1.6, height=2.5)], faces=(HERBAL, OFFIZIN))),
    ("u", LAB_WALL, FRONT_ROW, STUDY_WALL, dict(doors=[dict(at=11.4, width=1.1, height=2.2, leaf=("low", 1))], faces=(HERBAL, LABORATORY))),
    ("u", LAB_WALL, STUDY_WALL, 19.1, dict(faces=(PANELLED, LABORATORY))),
    ("d", FRONT_ROW, -8.55, HERB_WALL - HALF_WALL, dict(doors=[dict(at=-6.4, width=1.0, height=2.2, leaf=("high", 1))], faces=(HERBAL, HERBAL))),
    ("d", FRONT_ROW, HERB_WALL + HALF_WALL, LAB_WALL - HALF_WALL, dict(faces=(OFFIZIN, HERBAL))),
    ("d", FRONT_ROW, LAB_WALL + HALF_WALL, 8.55, dict(doors=[dict(at=6.6, width=1.3, height=2.4, leaf=("high", 1))], faces=(OFFIZIN, LABORATORY))),
    ("d", STUDY_WALL, -8.55, LAB_WALL - HALF_WALL, dict(doors=[dict(at=-4.0, width=1.0, height=2.2, leaf=("high", -1))], faces=(HERBAL, PANELLED))),
)
FLOORS = {"offizin": "tiles", "herbs": "brick", "lab": "stone", "mortar": "stone"}  # the study keeps the plank floor
REPOSITORIUM_BAY = 1.6


def furnish_offizin(f) -> None:
    """Repositorium bays round the walls, the dispensing counter facing the door, brass lamps under the vault."""
    right_bays = [1.1 + REPOSITORIUM_BAY * index for index in range(5)]
    back_bays = [-2.05 + REPOSITORIUM_BAY * index for index in range(5)]

    for along in right_bays:
        f.on_wall("right", "repositorium", along)

    for along in back_bays:
        f.on_face("d", FRONT_ROW - HALF_WALL, -1, "repositorium", along)

    f.on_face("u", HERB_WALL + HALF_WALL, 1, "repositorium", 1.3)
    f.on_face("u", HERB_WALL + HALF_WALL, 1, "repositorium", 7.0)
    f.put("rezeptur", 3.0, 5.5)
    f.put("stool_round", 1.6, 6.6)
    f.put("hanging_oil_lamp", 1.4, 3.6, lit=False)
    f.put("hanging_oil_lamp", 5.6, 3.6, lit=False)


def furnish_herbs(f) -> None:
    """Drawer cabinets on the party wall, herbs drying on poles, the sorting table, sacks and baskets."""
    f.on_wall("left", "herb_cabinet", 2.0)
    f.on_wall("left", "herb_cabinet", 4.3)
    f.on_wall("left", "seed_drawers", 6.6)
    f.on_face("u", HERB_WALL - HALF_WALL, -1, "drying_rack_herbs", 1.6)
    f.on_face("u", HERB_WALL - HALF_WALL, -1, "sack_pile", 7.4)
    f.on_face("d", FRONT_ROW - HALF_WALL, -1, "wicker_basket", -4.2, variant="herbs")
    f.on_face("d", FRONT_ROW - HALF_WALL, -1, "wicker_basket", -7.8, variant="mushrooms")
    f.put("mortar_table", -5.6, 4.6, 90.0)
    f.put("herb_poles", -5.6, 2.8, 90.0)
    f.put("herb_poles", -5.6, 6.2, 90.0)


def furnish_lab(f) -> None:
    """Hearth bench and still on the party wall, the athanor at the back, the cauldron, a glass bench in the middle,
    potion shelves on the inner wall."""
    f.on_wall("right", "lab_hearth", 13.6)
    f.on_wall("right", "copper_still", 17.5)
    f.on_wall("back", "athanor_furnace", 0.3)
    f.put("big_cauldron", 4.0, 16.9)
    f.put("alembic_table", 3.0, 12.3)
    f.put("mortar_table", 3.0, 14.2, 180.0)
    f.on_face("u", LAB_WALL + HALF_WALL, 1, "potion_wall", 16.6)
    f.on_face("u", LAB_WALL + HALF_WALL, 1, "wall_shelf", 13.9, variant="potions")
    f.on_face("d", FRONT_ROW + HALF_WALL, 1, "wall_shelf", 2.0, variant="jars")
    f.put("glowing_jar", 7.0, 18.5, variant="green")
    f.put("glowing_jar", 6.3, 18.6, variant="amber")
    f.put("slime_jar", 1.0, 10.0)
    f.put("skeleton_stand", 0.0, 13.7, 90.0)


def furnish_mortar(f) -> None:
    """The bronze mortar on its spring pole, a drying rack, a work table, sacks, crates of roots."""
    f.put("stamp_mortar", -5.4, 11.4)
    f.on_wall("left", "drying_rack_herbs", 10.0)
    f.on_wall("left", "sack_pile", 12.3)
    f.put("mortar_table", -2.4, 12.7, -90.0)
    f.on_face("d", STUDY_WALL - HALF_WALL, -1, "medicine_cabinet", -7.4)
    f.on_face("d", FRONT_ROW + HALF_WALL, 1, "crate_open", -3.0, variant="roots")


def furnish_study(f) -> None:
    """The master's study: bookcase, reading table under the window, lectern, globe and astrolabe, poison cabinet."""
    f.on_wall("left", "tall_bookcase", 16.6)
    f.put("reading_table", -4.8, 17.4)
    f.put("bentwood_chair", -4.8, 16.5, 180.0)
    f.on_face("u", LAB_WALL - HALF_WALL, -1, "poison_cabinet", 16.4)
    f.on_face("d", STUDY_WALL + HALF_WALL, 1, "scroll_rack", -7.2)
    f.put("celestial_globe", -2.2, 18.3)
    f.put("lectern", -2.4, 15.2, -90.0)
    f.put("hanging_oil_lamp", -4.8, 16.6, lit=False)


def furnish_alchemy(f) -> None:
    furnish_offizin(f)
    furnish_herbs(f)
    furnish_lab(f)
    furnish_mortar(f)
    furnish_study(f)


PLAN = dict(keeper=(3.0, 6.6), posts=(), partitions=PARTITIONS, furnish=furnish_alchemy)
