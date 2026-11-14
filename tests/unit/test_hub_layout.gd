extends GutTest

const HUB_SCENE: PackedScene = preload("res://features/hub/hub.tscn")
const FOUNTAIN_CLEARANCE: float = 5.9
const PLAZA_HALF_WIDTH: float = 30.0
const NAVMESH_TOLERANCE: float = 0.3

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


func test_patrol_routes_avoid_fountain_and_stay_in_plaza() -> void:
	for point in _patrol_route_points():
		assert_gt(
			Vector2(point.x, point.z).length(), FOUNTAIN_CLEARANCE, "%s clears fountain" % point
		)
		assert_lt(absf(point.x), PLAZA_HALF_WIDTH, "route point %s inside plaza" % point)


func test_patrol_route_points_lie_on_navmesh() -> void:
	var navigation_map: RID = _hub.get_world_3d().navigation_map
	var closest_point: Vector3

	# Mapa de navegação sincroniza em segundo plano (~4 frames).
	await wait_physics_frames(10)

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
