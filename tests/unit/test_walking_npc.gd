extends GutTest

const NPC_SCENE: PackedScene = preload("res://features/hub/walking_npc.tscn")
const BODY_SCENE: PackedScene = preload("res://art/characters/villager_female.gltf")
const FLOOR_HALF_SIZE: float = 20.0


func before_each() -> void:
	var region: NavigationRegion3D = NavigationRegion3D.new()
	var navigation_mesh: NavigationMesh = NavigationMesh.new()
	var corners: PackedVector3Array = PackedVector3Array(
		[
			Vector3(-FLOOR_HALF_SIZE, 0, -FLOOR_HALF_SIZE),
			Vector3(FLOOR_HALF_SIZE, 0, -FLOOR_HALF_SIZE),
			Vector3(FLOOR_HALF_SIZE, 0, FLOOR_HALF_SIZE),
			Vector3(-FLOOR_HALF_SIZE, 0, FLOOR_HALF_SIZE),
		]
	)

	navigation_mesh.vertices = corners
	navigation_mesh.add_polygon(PackedInt32Array([0, 1, 2, 3]))
	region.navigation_mesh = navigation_mesh
	add_child_autofree(region)

	# Mapa de navegação sincroniza em segundo plano (~4 frames).
	await wait_physics_frames(10)


func test_route_index_wraps_to_start() -> void:
	assert_eq(WalkingNpc.next_route_index(0, 3), 1)
	assert_eq(WalkingNpc.next_route_index(2, 3), 0)


func test_patrol_npc_walks_toward_next_point() -> void:
	var npc: WalkingNpc = _spawn_walker(PackedVector3Array([Vector3.ZERO, Vector3(10, 0, 0)]), 2.0)

	await wait_physics_frames(60)

	assert_between(npc.global_position.x, 1.0, 2.2, "about one second of walking at 2 m/s")
	assert_almost_eq(npc.global_position.z, 0.0, 0.05)


func test_patrol_npc_pauses_on_arrival_then_turns_back() -> void:
	var npc: WalkingNpc = _spawn_walker(PackedVector3Array([Vector3.ZERO, Vector3(2, 0, 0)]), 2.0)
	var paused_position: Vector3

	npc.pause_seconds = 1.0
	await wait_physics_frames(60)
	paused_position = npc.global_position
	await wait_physics_frames(20)

	assert_almost_eq(
		npc.global_position.distance_to(paused_position), 0.0, 0.01, "still while paused"
	)

	await wait_physics_frames(60)

	assert_lt(npc.global_position.x, paused_position.x - 0.3, "walks back toward the first point")


func test_walkers_on_collision_course_keep_apart() -> void:
	var east_walker: WalkingNpc = _spawn_walker(
		PackedVector3Array([Vector3(-4, 0, 0), Vector3(4, 0, 0)]), 1.3
	)
	var west_walker: WalkingNpc = _spawn_walker(
		PackedVector3Array([Vector3(4, 0, 0), Vector3(-4, 0, 0)]), 1.3
	)
	var closest_distance: float = INF

	for frame in 240:
		await wait_physics_frames(1)
		closest_distance = minf(
			closest_distance, east_walker.global_position.distance_to(west_walker.global_position)
		)

	assert_gt(closest_distance, 0.55, "capsules (r=0.3) never overlap")
	assert_gt(east_walker.global_position.x, 2.0, "east walker got past")


func test_standing_npc_does_not_move() -> void:
	var npc: WalkingNpc = NPC_SCENE.instantiate()

	npc.body_scene = BODY_SCENE
	npc.activity = WalkingNpc.Activity.STAND
	npc.position = Vector3(3, 0, 4)
	add_child_autofree(npc)
	await wait_physics_frames(10)

	assert_false(npc.is_physics_processing())
	assert_eq(npc.global_position, Vector3(3, 0, 4))


func test_chatting_npc_smiles_now_and_then() -> void:
	var npc: WalkingNpc = NPC_SCENE.instantiate()
	var face: FaceAnimator

	npc.body_scene = BODY_SCENE
	npc.activity = WalkingNpc.Activity.STAND
	npc.smile_every_seconds = 0.2
	add_child_autofree(npc)
	face = npc.find_child("FaceAnimator", true, false) as FaceAnimator
	await wait_seconds(0.3)
	face.advance(0.5)

	assert_gt(face.weight_of(&"smile"), 0.5, "smiling after the first beat")


func test_animation_steps_grow_with_distance() -> void:
	assert_eq(CharacterModel.animation_step_for(5.0), 0.0, "near: every frame")
	assert_almost_eq(CharacterModel.animation_step_for(25.0), 1.0 / 30.0, 0.0001)
	assert_almost_eq(CharacterModel.animation_step_for(60.0), 1.0 / 15.0, 0.0001)
	assert_eq(CharacterModel.animation_step_for(200.0), INF, "hidden: no animation")


func test_townsfolk_body_is_cut_from_afar() -> void:
	var npc: WalkingNpc = _spawn_walker(PackedVector3Array([Vector3.ZERO, Vector3(2, 0, 0)]), 1.0)
	var meshes: Array[Node] = npc.find_children("*", "GeometryInstance3D", true, false)

	await wait_physics_frames(2)

	assert_gt(meshes.size(), 0)

	for mesh in meshes:
		assert_eq((mesh as GeometryInstance3D).visibility_range_end, CharacterModel.HIDE_DISTANCE)


func _spawn_walker(route: PackedVector3Array, speed: float) -> WalkingNpc:
	var npc: WalkingNpc = NPC_SCENE.instantiate()

	npc.body_scene = BODY_SCENE
	npc.route = route
	npc.walk_speed = speed
	npc.pause_seconds = 5.0
	add_child_autofree(npc)

	return npc
