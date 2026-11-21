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

import orphanage_vestibule
import orphanage_wing_library
import orphanage_wing_reading
import orphanage_wing_school
import orphanage_wing_seminary
import alchemy_layout
import general_layout
import tavern_layout


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
    """Blacksmith after the stone smithies of the references (ascendancy-refs/lojas/smith): the shop room by the street
    door (counter, weapons on the walls, armour on stands), the workshop under the open roof with two brick forges on
    the back wall (bellows, an anvil on a stump before each, slack tubs, tongs on the wall), the long vice bench, the
    iron stock rack and the grindstone, the shoeing corner behind the open bay, and the store room for coal and iron."""
    # loja (u -11,7..-3,55, d 0,3..11,05)
    f.put("counter_till", -7.4, 8.2)
    f.put("rug", -7.4, 4.6, variant="red")
    f.put("masterwork_plinth_a", -9.9, 4.4)
    f.put("display_table", -5.3, 3.4, 0.0, variant="daggers")
    f.put("armor_stand_a", -10.9, 1.2, 30.0, variant="plate")
    f.put("armor_stand_a", -10.9, 9.9, 140.0, variant="mail")
    f.put("shield_wall", -9.6, 10.92)
    f.put("giant_sword", -5.0, 10.95)
    f.put("sword_wall", -3.75, 2.2, -90.0, seed=2)
    f.put("axe_mace_rack", -3.85, 8.4, -90.0)
    f.on_wall("left", "spear_rack", 5.7)
    f.on_wall("left", "boots_rack", 3.5)
    f.on_wall("left", "gauntlet_basket", 7.85)
    f.put("hanging_lantern", -7.4, 3.2)
    f.put("hanging_lantern", -7.4, 7.4)

    # depósito (u -11,7..-3,55, d 11,35..19,7): carvão, ferro, sucata
    f.on_wall("back", "coal_pile", -9.6)
    f.on_wall("back", "ingot_crates", -6.4)
    f.on_wall("left", "iron_stock_rack", 13.6)
    f.put("barrel_group", -5.0, 12.4)
    f.put("crate_stack", -10.6, 12.3)
    f.put("plate_pile", -7.2, 14.6)
    f.put("hanging_lantern", -7.6, 15.4)

    # oficina: as duas forjas no fundo, cada uma com fole, bigorna, tina e ferramentas
    for forge_u in (0.0, 6.2):
        f.on_wall("back", "forge", forge_u)
        f.put("bellows", forge_u - 1.6, 18.3, -70.0)
        f.put("anvil_block", forge_u + 0.2, 16.6, 15.0)
        f.put("quench_barrel", forge_u + 1.6, 17.4)
        f.put("hanging_tool_rack_a", forge_u, 15.2)

    f.on_wall("back", "tool_wall_rack", 3.1)
    f.on_wall("back", "tool_wall_rack", 9.4)
    f.put("anvil_block", 3.2, 12.6, -25.0)
    f.on_wall("right", "workbench_vise_a", 9.4)
    f.on_wall("right", "workbench_vise_a", 12.6)
    f.on_wall("right", "tool_wall_rack", 17.9)
    f.on_wall("right", "tool_wall_rack", 9.4, z=1.25)
    f.on_wall("right", "tool_wall_rack", 13.4, z=1.25)
    f.on_wall("right", "hanging_tool_rack_a", 4.6, z=1.6)
    f.put("tool_wall_rack", -3.15, 11.6, 90.0, z=1.25)
    f.put("tool_wall_rack", -3.15, 6.8, 90.0)
    f.put("tool_wall_rack", -3.15, 17.6, 90.0)
    f.on_wall("right", "wagon_wheel_lean", 6.6)
    f.put("iron_stock_rack", -2.85, 8.6, 90.0)
    f.put("grindstone", 2.6, 8.4, 90.0)
    f.put("weapon_barrel", -0.6, 11.8)
    f.put("workbench_vise_a", -2.8, 11.6, 90.0)
    f.put("tool_wall_rack", -3.15, 2.2, 90.0)
    f.put("plans_table", 0.4, 6.4, 0.0)
    f.put("ceiling_beam_hooks", 3.1, 13.6, 90.0)
    f.put("hanging_lantern", 3.1, 16.0)
    f.put("hanging_lantern", 3.1, 8.6)
    f.put("plate_pile", 4.7, 14.2)
    f.put("crate_stack", 10.8, 18.2)
    f.put("anvil_block", 1.4, 10.4, 40.0)
    f.put("quench_barrel", 0.2, 9.4)
    f.put("weapon_barrel", 5.6, 10.6)

    # canto de ferrar atrás do vão aberto
    f.on_wall("right", "horseshoe_board", 1.6)
    f.put("ingot_crates", 7.4, 4.2)
    f.put("coal_pile", 10.6, 4.9, 180.0)

    # debaixo do telheiro, na calçada: bigorna de ferrar e tina
    f.put("anvil_block", 7.6, -1.1, 20.0)
    f.put("quench_barrel", 10.8, -0.9)
    f.put("wagon_wheel_lean", 5.0, 0.0, 180.0)

VAULT_CROWN = 4.55  # o fecho das abóbadas do armeiro (spec vaults): as lanternas penduram dele


def furnish_armor(f) -> None:
    """Armourer as a brick arsenal (references: armoury halls of royal and city arsenals, armourer's workshop
    engravings, Hanseatic merchant halls). Vaulted hall in front, three aisles on two rows of brick piers: in each
    side aisle a plinth of mannequins faces the centre with the wall behind it hung with breastplates (left) or
    racks of helmets (right); the gold knight on a dais in the middle aisle, the counter at its end under the
    shield wall, the fitting corner with mirror and screen at the back right. Behind the cross wall: the plate
    workshop (forge, bellows, stake blocks, anvil, polishing wheel, vice benches) and the store of finished suits."""
    # salão: corredor do meio
    f.put("armor_stand_a", -1.9, 1.4, 0.0, variant="plate")
    f.put("armor_stand_a", 1.9, 1.4, 0.0, variant="plate")
    f.put("rug", 0.0, 3.0, variant="red")
    f.put("dais_a", 0.0, 5.9, width=2.2, depth=2.2)
    f.put("armor_stand_a", 0.0, 6.0, 0.0, z=0.35, variant="knight_gold")
    f.put("rug", 0.0, 8.6, variant="red")
    f.put("counter_straight", 0.0, 9.9)
    f.put("shield_wall", 0.0, 11.33, 0.0)
    f.put("guild_banner", -2.1, 11.36, 0.0, tint="7A2F3A")
    f.put("guild_banner", 2.1, 11.36, 0.0, tint="7A2F3A")

    # nave esquerda: couraças entre as janelas, manequins no estrado virados para o meio
    for along in (1.45, 5.5, 9.65):
        f.on_wall("left", "cuirass_wall", along)

    f.put("armor_stand_row_a", -5.9, 2.0, 90.0)
    f.put("armor_stand_row_a", -5.9, 5.9, 90.0)
    f.put("chainmail_stand", -6.4, 8.2, 90.0)
    f.put("armor_stand_a", -6.4, 9.2, 90.0, variant="leather")
    f.put("boots_rack", -4.0, 9.4, 0.0)

    # nave direita: estantes de elmos, estrado e o canto da prova
    f.on_wall("right", "helmet_rack_tall", 2.0)
    f.on_wall("right", "helmet_rack_tall", 5.9)
    f.put("armor_stand_row_a", 5.9, 2.0, -90.0)
    f.put("gauntlet_basket", 4.6, 4.0)
    f.put("plate_pile", 5.9, 5.9, -90.0)
    f.put("gauntlet_basket", 4.6, 7.2)
    f.put("fitting_platform", 6.0, 9.0)
    f.on_wall("right", "standing_mirror", 9.0)
    f.put("timber_screen_a", 4.1, 9.0, 90.0, variant="lattice")

    for u, d in ((0.0, 3.0), (0.0, 8.6), (-5.9, 2.0), (-5.9, 5.9), (-5.9, 9.65), (5.9, 2.0), (5.9, 5.9), (5.9, 9.65)):
        f.put("hanging_lantern", u, d, z=VAULT_CROWN)

    # oficina do armeiro (fundo à esquerda)
    f.on_wall("back", "forge", -5.8)
    f.put("bellows", -7.5, 18.2, -70.0)
    f.put("armour_stake_stump", -5.6, 16.0)
    f.put("anvil_block", -4.0, 17.0, 20.0)
    f.put("quench_barrel", -3.7, 18.5)
    f.put("hanging_tool_rack_a", -5.8, 14.6, z=VAULT_CROWN)
    f.on_wall("back", "tool_wall_rack", -1.8)
    f.put("coal_pile", -1.8, 18.5, 0.0)
    f.put("grindstone", 0.3, 18.4, 0.0)
    f.put("armour_stake_stump", -1.0, 14.2, 30.0)
    f.on_wall("left", "workbench_vise_a", 13.3)
    f.on_wall("left", "tool_wall_rack", 13.3, z=1.25)

    for along in (13.4, 15.4):
        f.put("workbench_vise_a", 2.4, along, -90.0)
        f.put("tool_wall_rack", 2.75, along, -90.0, z=1.25)

    f.put("plate_pile", -7.6, 16.6, 90.0)
    f.put("plans_table", 0.4, 12.6, 0.0)
    f.put("armor_stand_a", -7.7, 14.8, 90.0, variant="plate")
    f.put("gauntlet_basket", -6.9, 13.9)
    f.put("helmet_shelf", -2.2, 12.1, 180.0)

    for u, d in ((-5.9, 13.5), (-0.6, 16.4)):
        f.put("hanging_lantern", u, d, z=VAULT_CROWN)

    # depósito das peças prontas (fundo à direita)
    for u, variant in ((4.6, "mail"), (5.8, "plate"), (7.0, "leather")):
        f.put("armor_stand_a", u, 18.7, 0.0, variant=variant)

    f.on_wall("right", "helmet_shelf", 14.0)
    f.put("ingot_crates", 4.4, 12.5, 0.0)
    f.put("plate_pile", 5.6, 15.6, 0.0)
    f.put("crate_stack", 7.7, 16.8, -90.0)
    f.put("hanging_lantern", 5.9, 15.0, z=VAULT_CROWN)


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


MAGIC_CROWN = 5.55  # fecho da abóbada azul da loja de magia (spec vaults): lustres e o crocodilo penduram dele


def furnish_magic(f) -> None:
    """Magic shop as a cabinet of curiosities (references: Museum Wormianum and Kunstkammer engravings and
    reconstructions, monastery library halls, globe and instrument galleries). Under a blue star vault with gilded
    ribs the side walls are lined bay by bay with floor-to-vault curiosity shelving and bookcases, a stuffed
    crocodile and a planet mobile hang from the vault, the great armillary sphere stands in the middle on a rug
    between four glass table cases and two celestial globes, and the glass counter closes the hall under the star
    tapestry. Behind the cross wall: the enchanter's sanctum (summoning dais, rune pillars, enchanting table) on
    the left and the library (bookcases on the back wall, reading table, orrery, ladder, scroll racks) on the right."""
    # paredes do salão: um móvel por vão entre as cintas da abóbada
    for along, name in ((1.8, "curiosity_cabinet"), (5.0, "curiosity_cabinet"), (8.13, "tall_bookcase"), (11.25, "curiosity_cabinet")):
        f.on_wall("left", name, along, seed=int(along * 10))

    for along, name in ((1.8, "curiosity_cabinet"), (5.0, "tall_bookcase"), (8.13, "curiosity_cabinet"), (11.25, "curiosity_cabinet")):
        f.on_wall("right", name, along, seed=int(along * 10) + 1)

    # meio do salão
    f.put("rug_ornate", 0.0, 6.5, 90.0, variant="blue")
    f.put("armillary_sphere", 0.0, 6.5)

    for u, d in ((-3.4, 3.6), (3.4, 3.6), (-3.4, 9.4), (3.4, 9.4)):
        f.put("vitrine_case", u, d, 90.0, seed=int(10 * (u + d)))

    f.put("celestial_globe", -5.6, 6.5)
    f.put("skeleton_stand", -7.4, 9.7, 70.0)
    f.put("monster_trophy", -6.2, 12.6, 0.0, variant="horns")
    f.put("monster_trophy", 6.2, 12.6, 0.0, variant="skull")
    f.put("celestial_globe", 5.6, 6.5, tint="4A2E7A")
    f.put("counter_glass", 0.0, 11.1)
    f.put("world_map_wall", 0.0, 12.58, 0.0, z=2.3)
    f.put("wand_case", -1.8, 12.35, 0.0)
    f.put("mage_hat_stand", 2.4, 12.2, 0.0)

    f.put("staff_rack", -5.8, 3.4, 90.0)
    f.put("scroll_rack", 5.8, 3.4, -90.0)
    f.put("mana_crystal_crate", -5.8, 9.6)
    f.put("wand_case", 5.8, 9.6, -90.0)

    # vitrine da rua, sob as janelas
    for u, name in ((-5.1, "crystal_ball_pedestal"), (5.1, "crystal_ball_pedestal"), (-2.0, "giant_hourglass"), (2.0, "astrolabe")):
        f.put(name, u, 0.8)

    # o que pende da abóbada
    f.put("hanging_crocodile", 0.0, 3.4, z=MAGIC_CROWN)
    f.put("planet_mobile", 0.0, 9.0, z=MAGIC_CROWN)

    for u, d in ((-4.6, 3.4), (4.6, 3.4), (-4.6, 9.6), (4.6, 9.6)):
        f.put("floating_candles", u, d, z=MAGIC_CROWN - 0.6)

    # santuário do encantador (fundo à esquerda)
    f.put("summoning_dais", -4.0, 16.4)
    f.put("floating_books", -4.0, 16.4, z=MAGIC_CROWN - 0.4)
    f.put("rune_pillar", -7.6, 14.0)
    f.put("rune_pillar", -7.6, 18.5)
    f.put("rune_pillar", -0.4, 18.5)
    f.put("enchant_table", -0.9, 14.4, -90.0)
    f.on_wall("back", "star_tapestry", -4.0)
    f.put("lectern", -7.4, 16.3, 90.0)
    f.put("candle_stand", -2.4, 18.6)
    f.put("candle_stand", -5.6, 18.6)
    f.put("scroll_rack", 0.25, 16.6, -90.0)
    f.put("glowing_jar", -7.9, 15.0, variant="cyan")
    f.on_wall("left", "star_tapestry", 16.3)

    # biblioteca (fundo à direita)
    for along in (1.9, 7.2):
        f.on_wall("back", "tall_bookcase", along, seed=int(along * 10))

    f.put("reading_table", 4.4, 15.4, 0.0)
    f.put("study_chair", 3.8, 14.6, 180.0)
    f.put("study_chair", 5.0, 16.2, 0.0)
    f.put("orrery", 7.0, 14.3)
    f.put("tall_bookcase_slim", 0.95, 16.9, 90.0)
    f.put("book_cart", 2.4, 17.6, 0.0)
    f.put("globe_stand", 2.2, 14.0)
    f.put("rolling_ladder", 7.8, 18.1, -90.0)
    f.on_wall("right", "scroll_rack", 14.0)
    f.on_wall("right", "card_catalog", 16.2)
    f.put("floating_candles", 4.4, 15.4, z=MAGIC_CROWN - 0.6)


def furnish_tailor(f) -> None:
    """Draper, tailor and jeweller behind a street portico (references: draper's and haberdasher's shops of old
    engravings and museums, tailors' workrooms with long cutting tables and pressing stoves, milliners' shelves,
    cheval mirrors). The shop: a long counter down each side with stools for the customers, the wall behind
    the left one shelved with bolts of cloth, behind the right one the haberdasher's glass drawers, sale tables of
    folded cloth in the middle and dress forms in the arched windows. Behind the cross wall: the workroom (two
    cutting tables, pressing stove, forms, rails, spinning wheel) on the left and, on the right, the fitting
    rooms with the cheval mirror beside the jeweller's cases."""
    # loja de fazendas: balcão e estantes de peças à esquerda
    f.wall("left", ["fabric_shelf"] * 4, start=0.9, gap=0.3)
    f.on_wall("left", "hat_shelf", 10.6)

    for along in (3.0, 7.4):
        f.put("counter_straight", -6.1, along, 90.0)
        f.put("stool_round", -4.9, along - 0.8)
        f.put("stool_round", -4.9, along + 0.8)

    # armarinho à direita
    for along in (1.45, 5.45, 9.65):
        f.on_wall("right", "haberdashery_drawers", along, seed=int(along * 10))

    f.put("counter_straight", 6.1, 4.2, -90.0)
    f.put("stool_round", 4.9, 3.4)
    f.put("stool_round", 4.9, 5.0)

    # meio: mesas de fazenda e manequins nas janelas
    f.put("cloth_bolt_table", -2.2, 5.0, 90.0, seed=1)
    f.put("cloth_bolt_table", 2.2, 5.0, 90.0, seed=2)
    f.put("cloth_bolt_table", 0.0, 8.6, 0.0, seed=3)

    for u, variant in ((-6.88, "gown"), (-3.44, "dress"), (3.44, "cloak"), (6.88, "dress")):
        f.put("dress_form_a", u, 0.85, 180.0, variant=variant)

    f.put("hanging_fabrics_a", -2.2, 5.0, 90.0)
    f.put("hanging_fabrics_a", 2.2, 5.0, 90.0)
    f.put("hanging_fabrics_a", -7.2, 3.0, 90.0)
    f.put("hanging_fabrics_a", -7.2, 7.4, 90.0)
    f.put("bunting_a", 0.0, 1.6)
    f.put("rug", 0.0, 2.6, variant="gold")
    f.put("dress_form_a", -1.3, 10.4, 0.0, variant="gown")
    f.put("dress_form_a", 1.3, 10.4, 0.0, variant="cloak")
    f.put("crate_open", -4.4, 9.8, variant="cloth")
    f.put("clothes_rail", -2.8, 9.9, 0.0)
    f.put("clothes_rail", 2.8, 9.9, 0.0)
    f.put("yarn_basket", 4.4, 6.8)
    f.put("yarn_basket", -4.6, 1.2)
    f.put("bench_long", 4.4, 8.6, -90.0)
    f.put("plant_pot", -1.6, 0.9, variant="flower")
    f.put("plant_pot", 1.6, 0.9, variant="flower")

    for u, d in ((0.0, 2.6), (0.0, 7.0), (-6.1, 5.2), (6.1, 7.8)):
        f.put("hanging_lantern", u, d)

    # oficina de corte (fundo à esquerda)
    f.put("cutting_table", -5.4, 14.0, 0.0, tint="2B3C6E")
    f.put("cutting_table", -5.4, 17.2, 0.0, tint="8E2F45")
    f.on_wall("back", "pressing_stove", -1.0)
    f.put("dress_form_a", -1.2, 13.4, 200.0, variant="cloak")
    f.put("dress_form_a", 0.4, 13.6, 160.0, variant="gown")
    f.on_wall("left", "clothes_rail", 13.2)
    f.on_wall("left", "fabric_shelf", 17.2)
    f.put("spinning_wheel", 1.6, 17.6, -90.0)
    f.put("cutting_table", -1.4, 15.8, 90.0, tint="3F8A50")
    f.put("crate_open", -7.6, 15.6, 90.0, variant="cloth")
    f.put("yarn_basket", -2.6, 18.6)
    f.put("chair", -5.4, 15.4, 180.0)
    f.put("chair", -5.4, 18.5, 180.0)

    for u, d in ((-5.4, 14.0), (-5.4, 17.2), (-0.6, 15.6)):
        f.put("hanging_lantern", u, d)

    # provadores e joalheiro (fundo à direita)
    f.put("fitting_booth", 6.36, 18.3, 0.0)
    f.on_wall("right", "fitting_booth", 18.0)
    f.put("standing_mirror", 3.1, 17.8, 90.0)
    f.put("rug", 6.4, 15.4, variant="gold")
    f.on_wall("right", "jewel_case", 13.85)
    f.put("necklace_busts", 3.4, 12.4, 0.0)
    f.put("goldsmith_bench", 4.8, 16.2, 0.0)
    f.put("hanging_lantern", 5.6, 15.4)


WING_MODULES = (orphanage_vestibule, orphanage_wing_library, orphanage_wing_reading, orphanage_wing_school, orphanage_wing_seminary)  # orphanage wings: PLAN, NEW_WALL_FINISHES, furnish_<hall>
PLANS = {
    "vestibule": orphanage_vestibule.PLAN,
    "reading": orphanage_wing_reading.PLAN,
    "school": orphanage_wing_school.PLAN,
    "seminary": orphanage_wing_seminary.PLAN,
    "guild": dict(keeper=(0.0, 17.3), partitions=(("d", 12.0, 6.2, 11.55), ("u", 6.2, 14.2, 19.1)), furnish=furnish_guild),
    "smith": dict(
        keeper=(-7.4, 9.4), posts=(),
        partitions=(("u", -3.4, 0.3, 19.1, dict(doors=[dict(at=4.6, width=1.6, height=2.6), dict(at=15.2, width=1.8, height=2.6)])), ("d", 11.2, -11.55, -3.55)),
        wood_floors=((-11.55, -3.55, 0.3, 11.05),), stone_floors=((-3.25, 11.55, 13.2, 19.1), (6.1, 11.55, 0.3, 5.4)),
        furnish=furnish_smith,
    ),
    "armor": dict(
        keeper=(0.0, 10.8), posts=(),
        partitions=(("d", 11.58, -8.55, 8.55, dict(doors=[dict(at=-5.8, width=1.8, height=2.5), dict(at=7.4, width=1.2, height=2.4)])), ("u", 3.0, 11.73, 19.1, dict(doors=[dict(at=17.4, width=1.4, height=2.4)]))),
        furnish=furnish_armor,
    ),
    "tavern": tavern_layout.PLAN,
    "magic": dict(
        keeper=(0.0, 11.9), posts=(),
        partitions=(("d", 12.83, -8.55, 8.55, dict(doors=[dict(at=-4.0, width=1.8, height=2.8), dict(at=4.6, width=1.6, height=2.6)])), ("u", 0.6, 12.98, 19.1)),
        furnish=furnish_magic,
    ),
    "alchemy": alchemy_layout.PLAN,
    "tailor": dict(
        keeper=(7.3, 5.6), posts=(), girder_pitch=2.4,
        partitions=(("d", 11.4, -8.55, 8.55, dict(doors=[dict(at=-4.3, width=1.8, height=2.6), dict(at=5.2, width=1.4, height=2.5)])), ("u", 2.6, 11.55, 19.1, dict(doors=[dict(at=15.4, width=1.2, height=2.4)]))),
        furnish=furnish_tailor,
    ),
    "general": general_layout.PLAN,
    "library": orphanage_wing_library.PLAN,
}
FILL = {  # prédio -> ilhas soltas que enchem o chão livre dos dois lados do corredor da porta (fill_floor)
    "smith": [],
    "armor": [],
    "tailor": [],
    "general": [],
}
