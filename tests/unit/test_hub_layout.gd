extends GutTest

const HUB_SCENE: PackedScene = preload("res://features/hub/hub.tscn")
const FOUNTAIN_CLEARANCE: float = 5.9
const FOUNTAIN_CENTERS: Array[Vector2] = [Vector2(-34, 0), Vector2(0, -57)]
const CITY_BOUNDS: Rect2 = Rect2(-102, -96, 204, 184)
const NAVMESH_TOLERANCE: float = 0.3
const CATHEDRAL_FORECOURT: Vector3 = Vector3(8, 0, 4)
const CATHEDRAL_NAVE: Vector3 = Vector3(40, 1.05, 0)

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


func _townsfolk_by_activity(activity: WalkingNpc.Activity) -> Array[WalkingNpc]:
	var matches: Array[WalkingNpc] = []

	for child in _hub.get_node("Townsfolk").get_children():
		if child is WalkingNpc and child.activity == activity:
			matches.append(child)

	return matches


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
