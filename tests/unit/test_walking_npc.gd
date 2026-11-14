extends GutTest

const NPC_SCENE: PackedScene = preload("res://features/hub/walking_npc.tscn")
const BODY_SCENE: PackedScene = preload("res://art/characters/villager_female.gltf")


func test_route_index_wraps_to_start() -> void:
	assert_eq(WalkingNpc.next_route_index(0, 3), 1)
	assert_eq(WalkingNpc.next_route_index(2, 3), 0)


func test_patrol_npc_walks_toward_next_point() -> void:
	var npc: WalkingNpc = NPC_SCENE.instantiate()
	var start: Vector3 = Vector3(0, 0, 0)
	var target: Vector3 = Vector3(10, 0, 0)

	npc.body_scene = BODY_SCENE
	npc.route = PackedVector3Array([start, target])
	npc.walk_speed = 2.0
	add_child_autofree(npc)

	npc._process(1.0)

	assert_almost_eq(npc.global_position.x, 2.0, 0.01)
	assert_almost_eq(npc.global_position.z, 0.0, 0.01)


func test_patrol_npc_pauses_on_arrival_then_turns_back() -> void:
	var npc: WalkingNpc = NPC_SCENE.instantiate()

	npc.body_scene = BODY_SCENE
	npc.route = PackedVector3Array([Vector3.ZERO, Vector3(1, 0, 0)])
	npc.walk_speed = 5.0
	npc.pause_seconds = 1.0
	add_child_autofree(npc)

	npc._process(1.0)
	npc._process(0.1)
	var paused_position: Vector3 = npc.global_position
	npc._process(0.5)

	assert_eq(npc.global_position, paused_position, "stays still while paused")

	npc._process(0.6)
	npc._process(0.1)

	assert_lt(npc.global_position.x, paused_position.x, "walks back toward the first point")


func test_standing_npc_does_not_move() -> void:
	var npc: WalkingNpc = NPC_SCENE.instantiate()

	npc.body_scene = BODY_SCENE
	npc.activity = WalkingNpc.Activity.STAND
	npc.position = Vector3(3, 0, 4)
	add_child_autofree(npc)

	assert_false(npc.is_processing())
	assert_eq(npc.global_position, Vector3(3, 0, 4))
