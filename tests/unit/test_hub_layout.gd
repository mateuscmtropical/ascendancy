extends GutTest

const HUB_SCENE: PackedScene = preload("res://features/hub/hub.tscn")
const FOUNTAIN_CLEARANCE: float = 5.9
const FOUNTAIN_CENTERS: Array[Vector2] = [Vector2(-34, 0), Vector2(0, -57)]
const CITY_BOUNDS: Rect2 = Rect2(-102, -96, 204, 184)
const NAVMESH_TOLERANCE: float = 0.3
const CATHEDRAL_FORECOURT: Vector3 = Vector3(8, 0, 4)
const CATHEDRAL_NAVE: Vector3 = Vector3(40, 1.05, 0)
const SHOP_TYPES: Array[String] = [
	"smith",
	"armor",
	"magic",
	"tailor",
	"tavern",
	"alchemy",
	"general",
	"guild",
	"library",
	"school",
	"seminary",
]
## Todo prédio da praça comercial tem casca e salão mobiliado (placa não: o seminário não tem).
const SHOP_PIECES: Array[String] = ["Building", "Interior"]
const STREET_POINT: Vector2 = Vector2(-68, 0)
const LAWN_POINT: Vector2 = Vector2(-20, -30)
## Na rua a oeste da praça oeste, entre dois postes da borda da praça.
const STREET_START: Vector3 = Vector3(-68, 0, 9)
const CURB_DISTANCE: float = 4.0
## Na frente da escadaria da catedral, de frente para a porta (+X).
const CATHEDRAL_STAIRS_START: Vector3 = Vector3(6, 0.1, -1.5)
const NAVE_FLOOR_HEIGHT: float = 1.05
const NAVE_ENTRANCE_X: float = 16.0
## Pé da escada do coreto; a escada sobe para -X.
const CORETO_STAIRS_START: Vector3 = Vector3(-37.5, 0.1, -13.0)
const CORETO_FLOOR_HEIGHT: float = 1.2
const CORETO_FLOOR_X: float = -43.0

var _hub: Node3D


func before_all() -> void:
	_hub = HUB_SCENE.instantiate()
	add_child(_hub)


func after_all() -> void:
	_hub.free()


func test_hub_has_townsfolk_walking_and_standing() -> void:
	var walkers: Array[WalkingNpc] = _townsfolk_by_activity(WalkingNpc.Activity.PATROL)
	var standers: Array[WalkingNpc] = _townsfolk_by_activity(WalkingNpc.Activity.STAND)

	assert_gte(walkers.size(), 6)
	assert_gte(standers.size(), 4)


func test_farm_animals_start_with_the_whole_body_clear_of_pen_props() -> void:
	var animals: Array[Node] = _hub.find_child("FarmAnimals", false, false).get_children()

	assert_gt(animals.size(), 0)

	for animal in animals:
		var farm_animal: FarmAnimal = animal as FarmAnimal

		assert_gt(farm_animal.obstacles.size(), 0, "%s knows the props of its pen" % animal.name)
		assert_gte(
			_room_around(farm_animal),
			FarmAnimal.swing_radius(farm_animal.body_size),
			"%s can turn in place without touching a prop" % animal.name
		)


func test_patrol_routes_avoid_fountains_and_stay_in_city() -> void:
	for point in _patrol_route_points():
		var ground_point: Vector2 = Vector2(point.x, point.z)

		assert_true(CITY_BOUNDS.has_point(ground_point), "route point %s inside city" % point)

		for fountain_center in FOUNTAIN_CENTERS:
			assert_gt(
				ground_point.distance_to(fountain_center),
				FOUNTAIN_CLEARANCE,
				"%s clears fountain" % point
			)


func test_cathedral_interior_is_reachable_on_foot() -> void:
	var navigation_map: RID = _hub.get_world_3d().navigation_map
	var path: PackedVector3Array

	await _wait_for_navigation_map(navigation_map)
	path = NavigationServer3D.map_get_path(
		navigation_map, CATHEDRAL_FORECOURT, CATHEDRAL_NAVE, true
	)

	assert_gt(path.size(), 1, "forecourt connects to the nave")
	assert_lt(path[-1].distance_to(CATHEDRAL_NAVE), 0.5, "path ends inside the nave, not outside")


func test_patrol_route_points_lie_on_navmesh() -> void:
	var navigation_map: RID = _hub.get_world_3d().navigation_map
	var closest_point: Vector3

	await _wait_for_navigation_map(navigation_map)

	for point in _patrol_route_points():
		closest_point = NavigationServer3D.map_get_closest_point(navigation_map, point)

		assert_lt(
			Vector2(closest_point.x - point.x, closest_point.z - point.z).length(),
			NAVMESH_TOLERANCE,
			"route point %s is walkable, not inside a prop" % point
		)


func test_character_select_opens_without_preset_character() -> void:
	var character_select: CharacterSelect = _hub.get_node("CharacterSelect")
	var player: PlayerController = _hub.get_node("Player")

	assert_true(character_select.visible)
	assert_false(player.is_input_enabled)


func test_every_shop_type_has_a_dressed_front() -> void:
	for shop_type in SHOP_TYPES:
		var shops: Array[Node] = get_tree().get_nodes_in_group("shop_" + shop_type)

		assert_gt(shops.size(), 0, "%s shop exists" % shop_type)

		for piece in SHOP_PIECES:
			assert_not_null(
				shops[0].get_node_or_null(piece), "%s shop has its %s" % [shop_type, piece]
			)


func test_streets_sit_below_pavement_and_lawns_above() -> void:
	var street_height: float = await _ground_height_at(STREET_POINT)
	var lawn_height: float = await _ground_height_at(LAWN_POINT)

	assert_lt(street_height, -0.05, "street is lower than the pavement")
	assert_gt(lawn_height, 0.1, "lawn bed is raised above the pavement")


func test_player_walks_up_the_curb_from_the_street() -> void:
	var player: PlayerController = _hub.get_node("Player")
	var travelled: float

	player.global_position = STREET_START
	player.velocity = Vector3.ZERO
	player.is_input_enabled = true
	Input.action_press(&"move_forward")
	await wait_physics_frames(110)
	Input.action_release(&"move_forward")
	player.is_input_enabled = false
	travelled = absf(player.global_position.x - STREET_START.x)

	assert_gt(travelled, CURB_DISTANCE + 1.0, "player crossed the curb instead of stopping at it")
	assert_almost_eq(player.global_position.y, 0.0, 0.06, "player stands on the pavement")


func test_player_climbs_the_cathedral_stairs_into_the_nave() -> void:
	var player: PlayerController = _hub.get_node("Player")

	player.global_position = CATHEDRAL_STAIRS_START
	player.velocity = Vector3.ZERO
	player.is_input_enabled = true
	Input.action_press(&"move_forward")
	await wait_physics_frames(150)
	Input.action_release(&"move_forward")
	player.is_input_enabled = false

	assert_gt(player.global_position.x, NAVE_ENTRANCE_X, "player walked through the portal")
	assert_almost_eq(
		player.global_position.y, NAVE_FLOOR_HEIGHT, 0.05, "player stands on the nave floor"
	)


func test_player_climbs_the_coreto_stairs() -> void:
	var player: PlayerController = _hub.get_node("Player")

	player.global_position = CORETO_STAIRS_START
	player.velocity = Vector3.ZERO
	player.is_input_enabled = true
	Input.action_press(&"move_back")
	await wait_physics_frames(110)
	Input.action_release(&"move_back")
	player.is_input_enabled = false

	assert_lt(player.global_position.x, CORETO_FLOOR_X, "player reached the bandstand floor")
	assert_almost_eq(
		player.global_position.y, CORETO_FLOOR_HEIGHT, 0.05, "player stands on the floor"
	)


func _ground_height_at(ground_point: Vector2) -> float:
	var space_state: PhysicsDirectSpaceState3D = _hub.get_world_3d().direct_space_state
	var ray_top: Vector3 = Vector3(ground_point.x, 5.0, ground_point.y)
	var ray_bottom: Vector3 = Vector3(ground_point.x, -5.0, ground_point.y)
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(ray_top, ray_bottom)
	var hit: Dictionary

	await wait_physics_frames(2)
	hit = space_state.intersect_ray(query)

	return hit.get("position", Vector3.ZERO).y


func _townsfolk_by_activity(activity: WalkingNpc.Activity) -> Array[WalkingNpc]:
	var matches: Array[WalkingNpc] = []

	for child in _hub.get_node("Townsfolk").get_children():
		if child is WalkingNpc and child.activity == activity:
			matches.append(child)

	return matches


## Menor distância do bicho até a borda de um círculo de obstáculo do cercado dele.
func _room_around(animal: FarmAnimal) -> float:
	var ground_position: Vector2 = Vector2(animal.position.x, animal.position.z)
	var room: float = INF

	for obstacle in animal.obstacles:
		var center: Vector2 = Vector2(obstacle.x, obstacle.y)

		room = minf(room, ground_position.distance_to(center) - obstacle.z)

	return room


func _patrol_route_points() -> Array[Vector3]:
	var route_points: Array[Vector3] = []

	for walker in _townsfolk_by_activity(WalkingNpc.Activity.PATROL):
		route_points.append_array(Array(walker.route))

	return route_points


## Mapa de navegação sincroniza em segundo plano; a navmesh da cidade leva alguns frames.
func _wait_for_navigation_map(navigation_map: RID) -> void:
	var closest_point: Vector3

	for frame in 600:
		await wait_physics_frames(1)

		if NavigationServer3D.map_get_iteration_id(navigation_map) == 0:
			continue

		closest_point = NavigationServer3D.map_get_closest_point(
			navigation_map, CATHEDRAL_FORECOURT
		)

		if closest_point.distance_to(CATHEDRAL_FORECOURT) < 1.0:
			return
