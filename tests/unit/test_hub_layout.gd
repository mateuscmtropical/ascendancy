extends GutTest

const HUB_SCENE: PackedScene = preload("res://features/hub/hub.tscn")
const FOUNTAIN_CLEARANCE: float = 5.9
const PLAZA_HALF_WIDTH: float = 30.0

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
	var route_points: Array[Vector3] = []

	for walker in _townsfolk_by_activity(WalkingNpc.Activity.PATROL):
		route_points.append_array(Array(walker.route))

	for point in route_points:
		assert_gt(
			Vector2(point.x, point.z).length(),
			FOUNTAIN_CLEARANCE,
			"route point %s clears fountain" % point
		)
		assert_lt(absf(point.x), PLAZA_HALF_WIDTH, "route point %s inside plaza" % point)


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
