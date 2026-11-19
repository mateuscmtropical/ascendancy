"""Floor plans of the market shops: what stands where in each hall (docs/research/shops.md).

Each plan is a function of a Furnisher (build_market_shops.py): f.put(prop, u, d, degrees), f.on_wall(side, prop,
along), f.wall(side, [props]), f.grid(prop, u range, d range, columns, rows). Coordinates in metres: u across the
facade (0 = middle of the lot, the hall goes from f.left to f.right), d into the lot (f.front at the door wall,
f.back at the far wall). Props turn their front to the street at 0 degrees; the wall helpers turn their backs to
the wall. PLANS also says where the shopkeeper stands and, when the default grid does not fit, the posts and the
inner walls ("u" | "d", fixed coordinate, from, to). The back wall and the sides facing a street have windows
(f.windows, f.piers(side)): tall furniture goes on the piers between them (window_wall), the report flags any
prop that covers one.
"""

import orphanage_wing_library
import orphanage_wing_reading
import orphanage_wing_school
import orphanage_wing_seminary


def furnish_generic(f) -> None:
    """Stand-in plan: counter at the back, shelves on the walls, tables of goods and rugs down the hall."""
    keeper_u, keeper_d = f.keeper

    f.put("counter_till", keeper_u, keeper_d - 1.3)
    f.put("rug", f.door_u, f.front + 4.5)
    f.wall("back", ["wall_shelf"] * 5, gap=0.6)
    f.wall("left", ["wall_shelf", "crate_stack", "wall_shelf", "barrel_group", "wall_shelf"], start=f.front + 2.0, gap=0.8)
    f.wall("right", ["wall_shelf", "sack_pile", "wall_shelf", "crate_stack", "wall_shelf"], start=f.front + 2.0, gap=0.8)
    f.grid("display_table", (f.left + 4.5, f.right - 4.5), (f.front + 5.0, f.back - 6.5), 2, 2)
    f.grid("wheel_chandelier", (f.left + 5.0, f.right - 5.0), (f.front + 5.0, f.back - 5.0), 2, 2)


def furnish_guild(f) -> None:
    """Adventurers' guild (24 m, 7 m tall): the nave from the portal to the three-wicket counter under the world map,
    the registry crystal on a carpeted dais, a panelled hall with banners and trophies, a hearth lounge on the left
    cut off by timber screens, the quest board wall on the right, and the guild bank in the back right corner behind
    a stone partition with an arched doorway (teller counter, deposit boxes, vault door, coin table)."""
    f.put("guild_hearth_a", -10.9, 9.65, 90.0)
    f.put("wall_lantern", -6.2, 4.0)
    f.on_wall("right", "wall_lantern", 8.6)
    f.put("doorway_lintel_a", 6.2, 13.2, 90.0, width=2.0, height=4.6)

    for along in [1.4 + 2.0 * index for index in range(9)]:
        f.on_wall("left", "wainscot_a", along)
        f.on_wall("right", "wainscot_a", along)

    f.wall("back", ["wainscot_a"] * 12, start=f.left, gap=0.0)

    for along in (15.3, 17.3):  # o vão da porta em arco vai de 12.0 a 14.2: lambri só na parede
        f.put("wainscot_a", 6.03, along, -90.0)

    # nave
    f.put("rug", 0.0, 6.2, variant="red")
    f.put("rug", 0.0, 8.2, variant="red")
    f.put("dais_a", 0.0, 11.2, width=3.6, depth=2.4)
    f.put("registry_crystal", 0.0, 11.4, 0.0, z=0.35)
    f.put("dragon_skull_hanging", 0.0, 8.0)
    f.put("guild_counter", 0.0, 15.7)
    f.on_wall("back", "world_map_wall", 0.0)
    f.on_wall("back", "guild_banner", -3.4)
    f.on_wall("back", "guild_banner", 3.4)
    f.on_wall("back", "monster_trophy", -5.6, variant="horns")
    f.on_wall("back", "trophy_case", -8.0)
    f.on_wall("back", "rank_board", 5.4)
    f.on_wall("back", "plant_pot", -10.6, variant="bush")
    f.on_wall("front", "armor_stand_a", -3.4, variant="knight_gold")
    f.on_wall("front", "armor_stand_a", 3.4, variant="plate")
    f.on_wall("front", "plant_pot", -10.8, variant="bush")
    f.on_wall("front", "plant_pot", 10.8, variant="bush")
    f.put("group_table", -2.6, 5.2)
    f.put("group_table", 3.0, 5.2)

    # quest wall on the right
    f.on_wall("right", "notice_board", 3.6)
    f.on_wall("right", "quest_board", 6.6)
    f.on_wall("right", "wanted_posters", 9.6)
    f.put("bench_long", 9.2, 8.6, 90.0)
    f.put("bench_long", 9.2, 4.4, 90.0)
    f.put("group_table", 7.2, 8.4, 90.0)

    # bank
    f.put("teller_counter", 8.9, 15.3, -90.0)
    f.on_wall("back", "vault_door", 9.6)
    f.on_wall("right", "deposit_boxes", 14.6)
    f.put("money_sacks", 10.7, 13.2)
    f.put("coin_table", 10.4, 17.4, 90.0)
    f.put("chest_gold", 11.1, 16.2, 90.0)
    f.put("rug", 7.4, 15.0, 90.0, variant="gold")

    # hearth lounge on the left behind timber screens
    f.put("timber_screen_a", -6.2, 6.6, 90.0, variant="lattice")
    f.put("timber_screen_a", -6.2, 12.8, 90.0, variant="lattice")
    f.put("armchair", -8.2, 7.4, -60.0)
    f.put("armchair", -8.2, 11.8, -120.0)
    f.put("rug", -8.4, 9.65, 90.0, variant="gold")
    f.on_wall("left", "monster_trophy", 5.6, variant="claw")
    f.on_wall("left", "monster_trophy", 13.6, variant="skull")
    f.on_wall("left", "weapon_rental_rack", 16.6)
    f.put("group_table", -7.4, 15.4)
    f.put("crate_stack", -10.3, 3.6)
    f.put("barrel_group", -9.4, 17.8)
    f.grid("wheel_chandelier", (-7.2, 7.2), (4.5, 13.5), 2, 2)


def furnish_smith(f) -> None:
    """Blacksmith (24 m): the sales hall on the left (panelled walls, a showpiece plinth on a rug by the lane, weapons
    on every wall, a barred stock alcove behind the counter) and the forge yard on the right behind a stone partition
    with an arched doorway: hearth on slate flags at the back wall, anvils, quench barrel, grindstone, a workbench with
    a vise and tool racks hanging from the beams; the yard is open to the street."""
    f.on_wall("back", "forge", 8.2)
    f.put("forge_floor_a", 7.4, 16.9)
    f.put("hanging_lantern", -5.0, 5.0)
    f.put("hanging_lantern", -5.0, 11.8)
    f.put("doorway_lintel_a", 3.1, 13.3, 90.0, width=2.0, height=f.ceiling)

    for along in [1.4 + 2.0 * index for index in range(9)]:
        f.on_wall("left", "wainscot_a", along)

    f.wall("back", ["wainscot_a"] * 7, start=f.left, gap=0.0)

    for along in (9.5, 15.3, 17.3):
        f.put("wainscot_a", 2.88, along, -90.0)

    # sales hall: counter, lane, showpiece
    f.put("counter_till", -5.0, 14.0)
    f.put("rug", -5.0, 11.4, variant="gold")
    f.put("rug", -2.4, 5.0, variant="red")
    f.put("masterwork_plinth_a", -2.4, 5.0)
    f.wall("back", ["shield_wall", ("sword_wall", {"seed": 2}), "helmet_shelf", "giant_sword"], start=-7.0, gap=0.4)
    window_wall(f, "left", [[("armor_stand_a", {"variant": "knight_gold"})], [("armor_stand_a", {"variant": "plate"}), ("armor_stand_a", {"variant": "mail"})], [("wall_shelf", {"variant": "helmets"})], ["spear_rack", ("armor_stand_a", {"variant": "leather"})]], ["boots_rack", "crate_stack", "gauntlet_basket", None], gap=0.5)
    f.put("floor_shelf", -8.4, 10.8, 90.0, variant="tools")
    f.put("floor_shelf", -1.6, 10.8, 90.0, variant="helmets")
    f.put("armor_stand_a", -8.9, 3.6, 20.0, variant="plate")
    f.put("axe_mace_rack", -8.9, 5.6, 90.0)
    f.put("ingot_crates", 0.8, 3.0)
    f.put("weapon_barrel", 2.2, 5.8)
    f.put("blade_shelf", 2.6, 10.6, -90.0)
    f.put("spear_rack", 2.7, 16.6, -90.0)
    f.put("plans_table", 1.3, 18.0, -90.0)
    f.grid("wheel_chandelier", (-8.4, -1.6), (5.0, 12.0), 2, 2)

    # stock alcove behind bars in the back left corner
    f.put("timber_screen_a", -10.5, 17.0, 0.0, variant="bars")
    f.put("timber_screen_a", -8.5, 17.0, 0.0, variant="bars")
    f.wall("back", [("wall_shelf", {"variant": "tools"}), ("wall_shelf", {"variant": "boxes"})], start=-11.4, gap=0.1)
    f.put("crate_stack", -10.3, 17.95, 0.0)
    f.put("barrel_group", -8.5, 17.95, 0.0)
    f.put("display_table", -9.8, 7.9, variant="daggers")
    f.put("display_table", -2.0, 1.8, 0.0, variant="ingots")

    # forge yard
    f.put("bellows", 6.0, 17.5, -20.0)
    f.put("anvil_block", 7.0, 15.2, 30.0)
    f.put("quench_barrel", 9.6, 15.2)
    f.put("grindstone", 5.2, 11.6, 90.0)
    f.on_wall("right", "workbench_vise_a", 11.9)
    f.on_wall("right", "coal_pile", 17.0)
    f.on_wall("right", "tool_wall_rack", 13.9)
    f.on_wall("right", "ingot_crates", 8.4)
    f.put("hanging_tool_rack_a", 7.4, 12.0)
    f.put("hanging_tool_rack_a", 8.8, 6.0)
    f.put("barrel_group", 10.4, 4.6)
    f.put("crate_stack", 10.6, 6.6)
    f.put("anvil_block", 7.8, 3.4, -20.0)
    f.put("weapon_barrel", 5.4, 3.2)
    f.put("ceiling_beam_hooks", 5.0, 8.0, 90.0)
    f.put("forge_floor_a", 8.0, 7.2)
    f.put("coal_pile", 5.6, 7.4, 90.0)
    f.put("plate_pile", 4.8, 4.6)
    f.put("grindstone", 9.8, 9.6, -90.0)


def furnish_armor(f) -> None:
    """Armourer (17 m): the showroom behind the shop windows with mannequins on both sides of a red lane, a fitting
    booth of timber screens with a mirror, the counter under a wall of shields, a raised dais with the masterwork
    suit in the back left corner and, behind an arched stone partition on the right, the plate workshop with its
    own forge, anvil and tool racks. Panelled walls, shields and racks hang from the beams."""
    f.on_wall("right", "forge", 16.6)
    f.put("forge_floor_a", 6.3, 16.6, 90.0)
    f.put("hanging_lantern", 0.0, 6.4)
    f.put("hanging_lantern", -5.8, 15.6)
    f.put("doorway_lintel_a", 3.5, 15.3, 90.0, width=2.0, height=f.ceiling)

    for along in [1.4 + 2.0 * index for index in range(9)]:
        f.on_wall("left", "wainscot_a", along)

    f.wall("back", ["wainscot_a"] * 8, start=f.left, gap=0.0)

    for along in range(0, 12, 2):
        f.on_wall("right", "wainscot_a", 1.4 + along)

    for along in (13.3, 17.3):
        f.put("wainscot_a", 3.28, along, -90.0)

    # showroom
    f.put("counter_straight", 0.0, 14.7)
    f.put("rug", 0.0, 5.6, variant="red")
    f.put("rug", 0.0, 9.2, variant="red")
    f.on_wall("back", "shield_wall", 0.0)
    f.on_wall("back", "helmet_shelf", -3.6)
    f.on_wall("back", "helmet_shelf", 2.2)
    window_wall(f, "left", [[], [("armor_stand_a", {"variant": "plate"}), ("armor_stand_a", {"variant": "knight_gold"})], [("armor_stand_a", {"variant": "mail"}), ("armor_stand_a", {"variant": "leather"})], ["chainmail_stand", ("armor_stand_a", {"variant": "plate"})]], ["boots_rack", "gauntlet_basket", "boots_rack", None], gap=0.5)
    f.wall("right", [("wall_shelf", {"variant": "helmets"}), ("armor_stand_a", {"variant": "leather"}), "shield_wall", "gauntlet_basket", ("armor_stand_a", {"variant": "plate"})], start=2.6, gap=0.6)
    f.put("armor_stand_a", -2.6, 3.6, -20.0, variant="knight_gold")
    f.put("armor_stand_a", 2.6, 3.6, 20.0, variant="plate")
    f.put("floor_shelf", 5.6, 8.0, 90.0, variant="shoes")
    f.put("floor_shelf", -5.6, 5.4, 90.0, variant="helmets")

    # fitting booth in the left middle
    f.put("fitting_platform", -4.4, 9.8)
    f.put("standing_mirror", -4.4, 11.6)
    f.put("timber_screen_a", -6.5, 9.8, 90.0, variant="lattice")
    f.put("timber_screen_a", -2.3, 9.8, 90.0, variant="lattice")
    f.put("timber_screen_a", -4.4, 12.5, 0.0, variant="panels")

    # dais with the masterwork suit
    f.put("dais_a", -5.8, 17.5, width=3.6, depth=2.4)
    f.put("armor_stand_a", -5.8, 17.9, 0.0, z=0.35, variant="knight_gold")
    f.on_wall("back", "guild_banner", -8.2, tint="7A2F3A")
    f.put("armor_stand_row_a", -2.2, 17.6, 0.0)

    # plate workshop behind the partition
    f.put("anvil_block", 5.6, 16.8, 20.0)
    f.put("quench_barrel", 7.9, 13.6)
    f.on_wall("back", "tool_wall_rack", 6.4)
    f.put("hanging_tool_rack_a", 5.8, 14.6)
    f.put("plate_pile", 4.7, 18.1)
    f.put("coal_pile", 7.8, 18.4)
    f.put("workbench_vise_a", 4.9, 13.2, 0.0)
    f.grid("wheel_chandelier", (0.0, 0.0), (5.0, 12.5), 1, 2)


SCREEN_SLOT_B = 2.0  # largura de um módulo de panel_screen / partition_doorway
SCREEN_HALF_B = 0.14  # meia espessura de uma divisória de painéis


def screen_run_b(f, axis: str, fixed: float, start: float, slots: int, door_slot: int = None, variant: str = "glazed", doorway: str = "timber") -> None:
    """Divisória de módulos de 2 m: axis "u" corre ao longo da fachada na profundidade `fixed`, "d" corre para o
    fundo no u `fixed`; o módulo door_slot vira passagem (partition_doorway)."""
    degrees = {"u": 0.0, "d": 90.0}[axis]

    for index in range(slots):
        centre = start + SCREEN_SLOT_B * (index + 0.5)
        u, d = {"u": (centre, fixed), "d": (fixed, centre)}[axis]
        name, options = ("partition_doorway", {"variant": doorway}) if index == door_slot else ("panel_screen", {"variant": variant})

        f.put(name, u, d, degrees, **options)


def back_room_b(f, u_from: float, slots_across: int, slots_deep: int, door_on: str = "front", door_slot: int = 1, variant: str = "glazed", doorway: str = "timber", has_left: bool = True, has_right: bool = True) -> dict:
    """Sala de divisórias encostada na parede do fundo. u_from: eixo da divisória esquerda (ou a parede, sem ela).
    Devolve os limites internos {u_from, u_to, d_from}. door_on: front, left ou right."""
    run_from = u_from + (SCREEN_HALF_B if has_left else 0.0)
    run_to = run_from + SCREEN_SLOT_B * slots_across
    front_d = f.back - SCREEN_SLOT_B * slots_deep - SCREEN_HALF_B
    side_start = front_d + SCREEN_HALF_B
    doors = {side: (door_slot if door_on == side else None) for side in ("front", "left", "right")}

    screen_run_b(f, "u", front_d, run_from, slots_across, doors["front"], variant, doorway)

    if has_left:
        screen_run_b(f, "d", u_from, side_start, slots_deep, doors["left"], variant, doorway)
        f.put("screen_post", u_from, front_d)

    if has_right:
        screen_run_b(f, "d", run_to + SCREEN_HALF_B, side_start, slots_deep, doors["right"], variant, doorway)
        f.put("screen_post", run_to + SCREEN_HALF_B, front_d)

    return {"u_from": run_from, "u_to": run_to, "d_from": front_d + SCREEN_HALF_B}


def furnish_tavern(f) -> None:
    """Tavern and inn (18 m): inn reception and coat pegs by the door on the left, an inglenook (hearth with a
    hooded breast, settles, spit and rug) on the left wall, a partitioned kitchen behind the bar with its own door,
    an L bar with kegs and bottles in the back right, wall booths and a stage with bunting on the right wall, long
    tables and round tables down the middle, the stair to the rooms in the back left."""
    f.on_wall("left", "fireplace_tall", 9.65)
    f.on_wall("left", "mounted_head", 9.65, z=0.7)
    f.grid("wheel_chandelier", (-4.6, 4.6), (5.0, 11.6), 2, 2)

    f.put("bar_counter_l", 4.6, 15.9)
    f.on_wall("back", "bottle_shelf", 5.4)
    f.on_wall("back", "keg_rack", 1.6)
    f.grid("bar_stool", (2.4, 6.6), (14.2, 14.2), 4, 1)
    f.put("mug_rail", 4.6, 15.9)
    f.put("ceiling_beam_hooks", 4.6, 14.1, variant="sausages")

    back_room_b(f, -6.69, 3, 2, door_on="right", door_slot=0, variant="lattice")
    f.on_wall("back", "stone_oven", -5.0)
    f.on_wall("back", "kitchen_stove", -2.4)
    f.put("dough_table", -3.6, 16.6)
    f.put("flour_sacks", -1.3, 17.4)
    f.put("barrel_group", -5.7, 16.3, 90.0)
    f.put("hanging_pots", -3.6, 17.6)
    f.put("garlic_strings", -5.6, 17.8)
    f.put("ceiling_beam_hooks", -3.6, 15.7, variant="herbs")

    f.on_wall("left", "coat_rack_wall", 1.5)
    f.on_wall("left", "luggage_pile", 3.4)
    f.on_wall("left", "reception_desk", 5.5)
    f.put("stairs_straight", -7.75, 15.6)

    f.put("rug_ornate", -6.1, 9.7, 90.0, variant="red")
    f.put("spit_roast", -6.6, 9.7, 90.0)
    f.put("settle_bench", -6.1, 7.9, 180.0)
    f.put("settle_bench", -6.1, 11.5, 0.0)
    f.put("armchair", -4.2, 9.7, -90.0)
    f.put("plant_pot", -4.2, 7.6, variant="fern")

    f.on_wall("right", "menu_board", 1.4)
    f.on_wall("right", "wainscot", 1.35)
    f.on_wall("right", "tavern_booth", 3.6)
    f.on_wall("right", "tavern_booth", 6.0)
    f.put("stage", 6.9, 9.7, -90.0)
    f.on_wall("right", "wall_banner", 8.0)
    f.on_wall("right", "wall_banner", 11.4)
    f.on_wall("right", "tavern_booth", 12.55)
    f.on_wall("right", "dart_board", 14.3)
    f.put("bunting", 6.9, 9.7, 90.0)
    f.grid("hanging_lantern", (7.4, 7.4), (3.6, 12.55), 1, 3)

    f.put("rug_runner", 0.0, 7.6, variant="red")
    f.put("tavern_table_set", 0.0, 5.6)
    f.put("tavern_table_set", 0.0, 9.6)
    f.put("tavern_table_set", 4.6, 6.2, 90.0)
    f.put("round_table_set", -4.6, 4.0)
    f.put("round_table_set", 4.6, 11.4)
    f.put("round_table_set", -4.4, 13.2)
    f.put("barrel_table", 0.4, 13.2)
    f.put("barrel_table", -1.4, 14.0)
    f.put("plant_pot", 1.7, 3.6, variant="fern")


def side_wall(f, side: str, tall: list, low: list, start: float = None, gap: float = 0.35) -> None:
    """Tall furniture against a blind side wall, low goods under the windows of an exposed one."""
    items = low if side in f.room.exposed else tall

    f.wall(side, items, start=start, gap=gap)


def window_wall(f, side: str, pier_rows: list, sill_items: list, gap: float = 0.3) -> None:
    """A wall with windows: each row of tall props centred on the next pier between windows (an empty row skips
    that pier), each low prop centred under the next window (None skips that window)."""
    for (pier_from, pier_to), row in zip(f.piers(side), pier_rows):
        f.wall(side, row, start=(pier_from + pier_to - f.row_length(row, gap)) / 2.0, gap=gap)

    for (window_from, window_to, _), item in zip(f.windows[side], sill_items):
        if item is None:
            continue

        name, options = (item, {}) if isinstance(item, str) else item
        f.on_wall(side, name, (window_from + window_to) / 2.0, **options)


SHELF_PAIR_OFFSET = 0.25  # half the depth of a floor_shelf: two of them stand back to back


def shelf_island(f, u: float, d: float, variants: tuple) -> None:
    """Two floor shelves back to back across the aisle, one facing each side."""
    f.put("floor_shelf", u - SHELF_PAIR_OFFSET, d, -90.0, variant=variants[0])
    f.put("floor_shelf", u + SHELF_PAIR_OFFSET, d, 90.0, variant=variants[1])


def furnish_magic(f) -> None:
    """Magic shop: a three-step dais with a summoning circle under floating books in the middle of the nave, a
    wizards' library on the left (two-tier gallery with a spiral stair, an orrery and floating candles), staff racks,
    wand cases and bookcases on the right, wands and crystal balls in the windows, a glass counter, and the
    enchanter's sanctum (partitioned off, arched doorway, enchanting table between rune pillars) at the back right."""
    f.put("summoning_dais", 0.0, 9.7)
    f.put("floating_books", 0.0, 9.7)
    f.grid("wheel_chandelier", (-5.7, 5.7), (5.0, 12.4), 2, 2)
    f.put("rug_ornate", 0.0, 4.6, variant="blue")
    f.put("crystal_ball_pedestal", 0.0, 5.4)
    f.put("counter_glass", 0.0, 14.2)
    f.put("price_board", 1.9, 14.2)
    f.put("stool_round", 0.9, 16.0)

    f.put("gallery_stair", f.left + 1.2, 1.5, -70.0)
    f.on_wall("left", "book_gallery", 4.8, open_end=-1)
    f.on_wall("left", "book_gallery", 8.96)
    f.on_wall("left", "tall_bookcase", 12.2)
    f.on_wall("left", "staff_rack", 14.4)
    f.put("orrery", -4.9, 8.2)
    f.put("floating_candles", -4.9, 4.6)
    f.put("floating_candles", -4.9, 12.6)
    f.put("celestial_globe", -5.6, 5.6)
    f.put("giant_hourglass", -5.7, 12.0)

    f.on_wall("back", "tall_bookcase", -7.0)
    f.on_wall("back", "wand_case", -2.4)
    f.on_wall("back", "star_tapestry", 0.0)
    f.on_wall("back", "mage_hat_stand", 1.2)
    f.put("lectern", -5.2, 16.6)
    f.put("chest_gold", -3.2, 17.6)
    f.put("rug_ornate", -5.2, 16.2, 90.0, variant="plum")

    back_room_b(f, f.right - 6.0 - SCREEN_HALF_B, 3, 2, door_on="front", door_slot=1, variant="glazed", doorway="arch", has_right=False)
    f.put("rug_ornate", 5.55, 17.2, variant="blue")
    f.put("enchant_table", 5.55, 17.2)
    f.put("rune_pillar", 3.5, 18.2)
    f.put("rune_pillar", 7.6, 16.0)
    f.put("giant_hourglass", 7.5, 18.3)
    f.on_wall("back", "tall_bookcase", 7.4)
    f.on_wall("back", "staff_rack", 3.7)

    f.wall("right", ["wand_case", "staff_rack", "tall_bookcase", "mage_hat_stand", "wand_case", "scroll_rack", ("wall_shelf", {"variant": "potions"})], start=f.front + 1.6, gap=0.3)
    f.put("astrolabe", 5.9, 4.4)
    f.put("mana_crystal_crate", 5.9, 6.4)
    f.put("crystal_ball_pedestal", 5.9, 8.2)

    f.wall("front", ["wand_case", ("glowing_jar", {"variant": "green"}), "crystal_ball_pedestal"], start=f.left + 3.4)
    f.wall("front", [("glowing_jar", {"variant": "pink"}), "wand_case", "crystal_ball_pedestal", ("glowing_jar", {"variant": "cyan"}), "wand_case"], start=f.door_u + 2.0)
    f.grid("hanging_lantern", (-1.8, 1.8), (2.0, 2.0), 2, 1)


def furnish_alchemy(f) -> None:
    """Alchemist: a big bubbling cauldron on a stone hearth in the middle with copper pipes over the back-right
    distillery, a glass-walled greenhouse corner in the back left, potion walls and an alembic bench at the back,
    mortar and glowing jars on the right, and the herb wing down the left (drying racks, seed drawers, planters
    under hanging plants, baskets of herbs and mushrooms)."""
    f.put("hearth_ring", 0.0, 9.7)
    f.put("big_cauldron", 0.0, 9.7)
    f.grid("wheel_chandelier", (-1.6, 1.6), (6.4, 12.6), 2, 2)
    f.put("rug_ornate", 0.0, 4.8, variant="green")
    f.put("counter_glass", 0.0, 14.2)
    f.put("price_board", 1.9, 14.2)
    f.put("stool_round", 0.9, 16.0)
    f.on_wall("back", "potion_wall", 0.0)

    back_room_b(f, -8.55 - 0.0, 3, 2, door_on="front", door_slot=1, variant="glazed", doorway="timber", has_left=False, has_right=True)
    f.grid("planter_box", (-7.4, -7.4), (16.0, 18.4), 1, 2, 90.0)
    f.put("flower_steps", -5.3, 18.3)
    f.put("watering_cans", -3.3, 16.2)
    f.put("hanging_plants", -5.6, 17.0)
    f.put("hanging_plants", -3.4, 17.6)
    f.put("plant_pot", -3.2, 18.6, variant="flower")

    back_room_b(f, f.right - 6.0 - SCREEN_HALF_B, 3, 2, door_on="front", door_slot=1, variant="glazed", doorway="timber", has_right=False)
    f.on_wall("back", "athanor_furnace", 7.3)
    f.on_wall("back", "alembic_table", 4.7)
    f.put("mortar_table", 3.8, 16.6)
    f.put("copper_pipes", 5.55, 16.9)
    f.put("glowing_jar", 6.9, 16.4, variant="green")
    f.put("glowing_jar", 7.7, 16.6, variant="pink")
    f.put("slime_jar", 6.2, 17.7)

    side_wall(f, "left", ["drying_rack_herbs", ("wicker_basket", {"variant": "herbs"}), "drying_rack_herbs", ("wicker_basket", {"variant": "mushrooms"}), "seed_drawers", "drying_rack_herbs", ("plant_pot", {"variant": "fern"})], ["planter_box", ("wicker_basket", {"variant": "herbs"}), "planter_box", ("wicker_basket", {"variant": "mushrooms"}), "planter_box", ("plant_pot", {"variant": "flower"})], start=0.8, gap=0.5)
    f.grid("planter_box", (-5.7, -5.7), (4.6, 11.8), 1, 3, 90.0)
    f.grid("hanging_plants", (-5.7, -5.7), (4.6, 11.8), 1, 3)
    f.put("herb_bundles", -5.7, 14.0)
    f.put("ceiling_beam_hooks", -3.0, 6.0, variant="herbs")
    f.put("ceiling_beam_hooks", 3.0, 6.0, variant="herbs")

    side_wall(f, "right", [("wall_shelf", {"variant": "potions"}), "potion_wall", ("wall_shelf", {"variant": "jars"}), "recipe_board", ("wall_shelf", {"variant": "bottles"}), "skeleton_stand"], [("crate_open", {"variant": "bottles"}), ("glowing_jar", {"variant": "green"}), ("crate_open", {"variant": "roots"}), "barrel_group", ("wicker_basket", {"variant": "mushrooms"})], start=0.8, gap=0.4)
    f.put("mortar_table", 5.7, 4.6, -90.0)
    f.put("alembic_table", 5.7, 8.6, -90.0)
    f.put("glowing_jar", 4.9, 11.6, variant="green")
    f.put("glowing_jar", 5.7, 11.9, variant="cyan")
    f.put("glowing_jar", 6.5, 11.6, variant="pink")
    f.put("slime_jar", 5.7, 12.7)

    f.wall("front", ["flower_steps", ("wicker_basket", {"variant": "herbs"}), "watering_cans", ("plant_pot", {"variant": "flower"})], start=f.left + 1.2)
    f.wall("front", ["slime_jar", ("glowing_jar", {"variant": "pink"}), ("crate_open", {"variant": "bottles"}), ("glowing_jar", {"variant": "cyan"})], start=f.door_u + 2.0)
    f.put("hanging_lantern", 5.7, 6.6)


def furnish_tailor(f) -> None:
    """Tailor and jeweler (17 m): the cloth hall with a ring of dress forms on a rug, fabric walls, rails and hat
    shelves, the counter in the middle, a fitting dais with a mirror and panelled screen by the right windows, the
    cutting table and spinning wheel at the back, and the jeweler's parlour in the back left corner behind a
    partition with an arched doorway (glass cases, necklace busts, the goldsmith's bench and a safe)."""
    f.put("hanging_lantern", -6.2, 15.3)
    f.put("hanging_lantern", 5.7, 15.0)
    f.put("hanging_lantern", 0.0, 5.0)
    f.put("hanging_fabrics_a", -4.6, 6.0, 90.0)
    f.put("hanging_fabrics_a", 4.6, 10.4, 90.0)
    f.put("bunting_a", 0.0, 3.4)
    f.put("doorway_lintel_a", -3.6, 15.3, 90.0, width=2.0, height=3.7)

    for along in [1.4 + 2.0 * index for index in range(9)]:
        f.on_wall("left", "wainscot_a", along, tint="E6C9A4")
        f.on_wall("right", "wainscot_a", along, tint="E6C9A4")

    f.wall("back", ["wainscot_a"] * 8, start=f.left, gap=0.0)

    for along in (13.3, 17.3):
        f.put("wainscot_a", -3.38, along, 90.0)
        f.put("wainscot_a", -3.82, along, -90.0)

    # cloth hall
    f.put("rug", 0.0, 9.7, variant="red")
    f.put("rug", 0.0, 6.2, variant="gold")
    f.put("dress_form_a", -1.3, 8.6, variant="dress")
    f.put("dress_form_a", 1.3, 8.6, variant="gown")
    f.put("dress_form_a", -1.3, 10.8, variant="cloak")
    f.put("dress_form_a", 1.3, 10.8, variant="dress")
    f.put("counter_straight", 0.0, 14.2)
    f.put("stool_round", 0.9, 16.0)
    f.put("cutting_table", 1.4, 17.7, 0.0)
    f.put("chair", -0.4, 17.9, 180.0)
    window_wall(f, "back", [[], ["fabric_shelf", 0.4, "wall_banner", 0.4, "fabric_shelf"], []], [None, "hat_shelf"])
    f.on_wall("back", "spinning_wheel", 7.4)
    side_wall(f, "left", ["fabric_shelf", "clothes_rail", ("wall_shelf", {"variant": "shoes"}), "clothes_rail", "hat_shelf"], ["yarn_basket", ("crate_open", {"variant": "cloth"}), ("dress_form_a", {"variant": "gown"}), "yarn_basket", ("crate_open", {"variant": "cloth"})], start=1.6)
    window_wall(f, "right", [[("crate_open", {"variant": "cloth"}), ("dress_form_a", {"variant": "dress"})], [("dress_form_a", {"variant": "cloak"}), ("plant_pot", {"variant": "flower"})], ["clothes_rail"]], ["yarn_basket", "spinning_wheel", ("crate_open", {"variant": "cloth"}), None])
    f.wall("front", [("dress_form_a", {"variant": "gown"}), ("crate_open", {"variant": "cloth"}), ("dress_form_a", {"variant": "dress"}), "yarn_basket"], start=f.door_u + 2.0, gap=0.5)
    f.wall("front", ["necklace_busts", ("plant_pot", {"variant": "flower"}), "necklace_busts"], start=f.left + 1.2)
    f.put("display_table", -5.7, 8.2, variant="cloth")
    f.put("display_table", -4.4, 4.4, variant="cloth")
    f.put("display_table", 4.4, 4.4, variant="cloth")
    f.put("rug", -4.4, 4.4, variant="gold")
    f.put("rug", 4.4, 4.4, variant="gold")
    f.put("bench_long", -2.7, 3.0, 0.0)
    f.put("plant_pot", 2.5, 3.0, variant="flower")
    f.put("yarn_basket", -5.7, 10.0)
    shelf_island(f, 5.7, 5.0, ("cloth", "shoes"))
    shelf_island(f, 5.7, 9.2, ("cloth", "cloth"))
    f.grid("wheel_chandelier", (-5.7, 5.7), (5.0, 12.0), 2, 2)

    # fitting dais
    f.put("dais_a", 5.6, 13.4, 90.0, width=3.0, depth=2.0)
    f.put("dress_form_a", 5.7, 13.5, 0.0, z=0.35, variant="gown")
    f.put("standing_mirror", 7.6, 13.4, -90.0)
    f.put("timber_screen_a", 5.7, 14.9, 0.0, variant="panels")

    # jeweler's parlour
    f.on_wall("left", "iron_safe", 18.4)
    f.on_wall("left", "goldsmith_bench", 16.4)
    f.on_wall("left", "iron_safe", 13.0)
    f.put("jewel_case", -5.9, 18.5, 0.0)
    f.put("jewel_case", -4.9, 17.1, 90.0)
    f.put("jewel_case", -5.9, 12.8, 0.0)
    f.put("necklace_busts", -7.6, 14.3, 90.0)
    f.put("rug", -6.1, 15.4, 90.0, variant="gold")


def furnish_general(f) -> None:
    """General store and bakery (17 m): the produce market by the door, the till counter with the pastry case under
    shelves of jars and bottles, grocery and hardware shelves down the blind left wall and floor-shelf aisles in
    the middle, a cafe nook on a raised dais behind a timber screen by the right windows and, behind an arched
    stone partition in the back right corner, the bakery with its stone oven, dough table, bread racks and flour."""
    f.on_wall("back", "stone_oven", 5.9)
    f.put("hanging_lantern", 6.0, 15.0)
    f.put("hanging_lantern", -1.0, 5.0)
    f.put("bunting_a", 0.0, 7.6)
    f.put("bunting_a", 0.0, 12.0)
    f.put("doorway_lintel_a", 3.5, 15.3, 90.0, width=2.0, height=f.ceiling)

    for along in [1.4 + 2.0 * index for index in range(9)]:
        f.on_wall("left", "wainscot_a", along, tint="EBD9B8")
        f.on_wall("right", "wainscot_a", along, tint="EBD9B8")

    f.wall("back", ["wainscot_a"] * 8, start=f.left, gap=0.0)

    for along in (13.3, 17.3):
        f.put("wainscot_a", 3.28, along, -90.0)

    # market hall and counter
    f.put("rug", 0.0, 5.2, variant="gold")
    f.put("display_table", 0.0, 5.6, variant="fruit")
    f.put("display_table", 0.0, 9.7, variant="pottery")
    f.put("display_table", -3.6, 3.6, variant="pottery")
    f.put("display_table", 3.6, 3.6, variant="bread")
    f.put("rug", -3.6, 3.6, variant="gold")
    f.put("rug", 3.6, 3.6, variant="red")
    f.put("rug", 0.0, 9.7, variant="red")
    f.put("counter_till", -1.0, 14.2)
    f.put("pastry_case", 1.5, 14.2)
    f.put("cake_stand", 2.4, 15.6)
    f.put("stool_round", -0.2, 16.0)
    f.put("ceiling_beam_hooks", -1.0, 15.6, variant="sausages")
    window_wall(f, "back", [[("wall_shelf", {"variant": "jars"})], [("wall_shelf", {"variant": "bottles"}), ("wall_shelf", {"variant": "boxes"})]], [("crate_open", {"variant": "apples"})])
    f.put("chest_gold", -5.6, 16.8)
    f.put("blanket_pile", -3.9, 17.6)
    side_wall(f, "left", [("wall_shelf", {"variant": "jars"}), "sack_pile", "tool_rack", "crate_stack", "backpack_wall", "barrel_group", ("wall_shelf", {"variant": "boxes"}), "step_ladder"], ["sack_pile", ("crate_open", {"variant": "apples"}), "crate_stack", ("wicker_basket", {"variant": "fruit"}), "barrel_group", ("crate_open", {"variant": "roots"}), ("plant_pot", {"variant": "bush"})], start=0.8)
    window_wall(f, "right", [[("wall_shelf", {"variant": "bottles"})], [("wall_shelf", {"variant": "books"})], []], [("crate_open", {"variant": "ingots"}), "barrel_group", ("wicker_basket", {"variant": "wool"}), None])
    f.wall("front", [("crate_open", {"variant": "apples"}), ("wicker_basket", {"variant": "fruit"}), ("crate_open", {"variant": "roots"}), ("wicker_basket", {"variant": "bread"}), ("plant_pot", {"variant": "bush"})], start=f.left + 1.2)
    f.wall("front", [("plant_pot", {"variant": "bush"}), "barrel_group", ("crate_open", {"variant": "cloth"}), ("wicker_basket", {"variant": "wool"})], start=f.door_u + 2.0)
    shelf_island(f, -5.7, 5.0, ("jars", "bottles"))
    shelf_island(f, -5.7, 9.7, ("tools", "boxes"))
    f.put("barrel_group", -5.7, 12.6)
    f.put("cat_sleeping", 1.0, 12.4)
    f.grid("wheel_chandelier", (-5.7, 5.7), (5.0, 11.4), 3, 2)
    f.grid("hanging_goods", (-5.7, 5.7), (7.35, 7.35), 2, 1)

    # cafe nook on a dais behind a screen
    f.put("dais_a", 5.5, 8.4, width=3.0, depth=2.4)
    f.put("cafe_table_set", 5.5, 8.5, 0.0, z=0.35)
    f.put("timber_screen_a", 3.8, 8.4, 90.0, variant="lattice")
    f.put("plant_pot", 7.3, 6.4, variant="fern")
    shelf_island(f, 5.7, 4.6, ("bread", "jars"))

    # bakery behind the partition
    f.put("dough_table", 6.4, 14.0)
    f.on_wall("back", "bread_rack", 7.7)
    f.put("flour_sacks", 4.3, 16.9)
    f.on_wall("right", "jam_shelf", 13.4)
    f.put("barrel_group", 7.8, 16.6)


VESTIBULE_WELL = (-4.8, 4.8, 11.2, 19.1)  # vão da escadaria (u de, u até, d de, d até)
VESTIBULE_COLUMNS = (-9.7, 9.7)  # u das colunas do térreo fora do vão, em d = 11.2
FACADE_PIERS = (5.14, 8.17, 11.21)  # |u| dos panos de parede entre as janelas da fachada de um salão


def vestibule_walls(f, scenes: tuple) -> None:
    """Both side walls of a storey of the vestibule past the doorways: console under a pier glass, a bench under a
    painting and wall lanterns."""
    for side, scene in zip(("left", "right"), scenes):
        f.on_wall(side, "console_table", 6.6, seed=len(scene))
        f.on_wall(side, "wall_mirror", 6.6)
        f.on_wall(side, "wall_lantern", 5.2)
        f.on_wall(side, "wall_lantern", 8.0)
        f.on_wall(side, "bench_long", 9.9)
        f.on_wall(side, "painting", 9.9, variant=scene)


def furnish_vestibule(f) -> None:
    """Vestibule of the casarão, two storeys round the grand stair. Ground floor: the porter's desk on the right of
    the marble walk, urns and plants on the piers of the facade, consoles under pier glasses on the side walls, a
    hearth lounge in the back right and a waiting room with the long-case clock in the back left. Upper floor
    (the gallery): a salon between the stair and the balcony doors, a music room with the piano in the back right
    and a tea corner in the back left. The gilt chandelier hangs in the stair well."""
    gallery = f.upstairs(f.room.spec["storeys"][0])
    well_left, well_right, well_front, well_back = VESTIBULE_WELL

    f.block("escada", (well_left, well_right, well_front - 0.4, well_back))
    gallery.block("vão", VESTIBULE_WELL)
    gallery.block("chegada", (well_left, well_right, well_front - 1.6, well_front))

    for column_u in VESTIBULE_COLUMNS:
        f.block("coluna", (column_u - 0.35, column_u + 0.35, 10.85, 11.55))

    gallery.put("grand_chandelier", 0.0, (well_front + well_back) / 2.0, drop=2.4)

    # ground floor
    f.put("teacher_desk", 6.4, 6.3)
    f.put("rug_ornate", 6.4, 6.9, variant="blue")
    f.grid("grand_chandelier", (-8.2, 8.2), (5.6, 5.6), 2, 1, drop=0.5)
    vestibule_walls(f, ("seascape", "landscape"))

    for pier_u in (-FACADE_PIERS[0], FACADE_PIERS[0], -FACADE_PIERS[2], FACADE_PIERS[2]):
        f.put("pedestal_urn", pier_u, f.front + 0.36)

    for pier_u in (-FACADE_PIERS[1], FACADE_PIERS[1]):
        f.put("plant_pot", pier_u, f.front + 0.4, variant="bush")

    for well_u in (well_left - 0.33, well_right + 0.33):
        f.put("pedestal_urn", well_u, well_front + 0.5)

    f.grid("pedestal_urn", (-2.4, 2.4), (4.4, 9.0), 2, 2)

    f.on_wall("right", "fireplace", 15.4)
    f.put("rug_ornate", 11.6, 15.4, 90.0, variant="red")
    f.put("sofa", 10.2, 15.4, 90.0)
    f.put("armchair", 12.2, 13.2, 160.0)
    f.put("armchair", 12.2, 17.6, 20.0)
    f.on_wall("back", "painting", 9.83, variant="portrait")
    f.on_wall("back", "pedestal_urn", 6.0)
    f.put("plant_pot", f.right - 0.6, 12.4, variant="fern")

    f.on_wall("left", "long_case_clock", 15.4)
    f.on_wall("left", "bench_long", 13.2)
    f.on_wall("left", "bench_long", 17.6)
    f.put("rug_ornate", -10.4, 15.4, 90.0, variant="green")
    f.put("sofa", -6.2, 15.4, 90.0)
    f.on_wall("back", "painting", -9.83, variant="lady")
    f.on_wall("back", "console_table", -9.83, seed=7)
    f.put("plant_pot", -5.6, 18.5, variant="fern")

    # gallery
    gallery.grid("grand_chandelier", (-8.2, 8.2), (5.6, 5.6), 2, 1, drop=0.5)
    vestibule_walls(gallery, ("portrait", "lady"))
    gallery.put("rug_ornate", 0.0, 6.2, variant="red")

    for salon_u in (-3.4, 3.4):
        gallery.put("pedestal_urn", salon_u, 8.4)

    gallery.put("sofa", -4.6, 6.2, 90.0)
    gallery.put("sofa", 4.6, 6.2, -90.0)

    for pier_u in (-FACADE_PIERS[1], FACADE_PIERS[1], -FACADE_PIERS[2], FACADE_PIERS[2]):
        gallery.put("pedestal_urn", pier_u, f.front + 0.36)

    gallery.on_wall("back", "piano", 9.83)
    gallery.grid("chair", (8.6, 11.0), (14.4, 15.6), 3, 2, 180.0)
    gallery.put("rug_ornate", 9.8, 15.0, variant="plum")
    gallery.on_wall("right", "painting", 15.2, variant="landscape")
    gallery.on_wall("right", "sofa", 15.2)
    gallery.on_wall("back", "long_case_clock", 13.6)
    gallery.put("plant_pot", 5.5, 18.5, variant="fern")

    gallery.put("rug_ornate", -9.8, 15.2, 90.0, variant="blue")
    gallery.put("cafe_table_set", -9.8, 15.2)
    gallery.on_wall("left", "sofa", 15.2)
    gallery.on_wall("left", "painting", 15.2, variant="seascape")
    gallery.on_wall("back", "console_table", -9.83, seed=3)
    gallery.on_wall("back", "wall_mirror", -9.83)
    gallery.on_wall("back", "pedestal_urn", -6.0)
    gallery.put("plant_pot", -13.9, 12.2, variant="flower")


WING_MODULES = (orphanage_wing_library, orphanage_wing_reading, orphanage_wing_school, orphanage_wing_seminary)  # orphanage wings: PLAN, NEW_WALL_FINISHES, furnish_<hall>
PLANS = {
    "vestibule": dict(keeper=(6.4, 7.4), posts=(), furnish=furnish_vestibule),
    "reading": orphanage_wing_reading.PLAN,
    "school": orphanage_wing_school.PLAN,
    "seminary": orphanage_wing_seminary.PLAN,
    "guild": dict(keeper=(0.0, 17.3), partitions=(("d", 12.0, 6.2, 11.55), ("u", 6.2, 14.2, 19.1)), furnish=furnish_guild),
    "smith": dict(keeper=(-5.0, 15.6), posts=((-8.4, 7.0), (-1.6, 7.0), (-8.4, 13.4), (-1.6, 13.4)), partitions=(("u", 3.1, 8.5, 12.3), ("u", 3.1, 14.3, 19.1)), furnish=furnish_smith),
    "armor": dict(keeper=(0.0, 16.2), partitions=(("u", 3.5, 12.3, 14.3), ("u", 3.5, 16.3, 19.1)), furnish=furnish_armor),
    "tavern": dict(keeper=(5.0, 17.6), furnish=furnish_tavern),
    "magic": dict(keeper=(0.0, 15.6), furnish=furnish_magic),
    "alchemy": dict(keeper=(0.0, 15.6), furnish=furnish_alchemy),
    "tailor": dict(keeper=(0.0, 15.6), partitions=(("u", -3.6, 12.3, 14.3), ("u", -3.6, 16.3, 19.1)), furnish=furnish_tailor),
    "general": dict(keeper=(-1.0, 15.6), partitions=(("u", 3.5, 12.3, 14.3), ("u", 3.5, 16.3, 19.1)), furnish=furnish_general),
    "library": orphanage_wing_library.PLAN,
}
FILL = {  # prédio -> ilhas soltas que enchem o chão livre dos dois lados do corredor da porta (fill_floor)
    "smith": [],
    "armor": [],
    "tailor": [],
    "general": [],
}
