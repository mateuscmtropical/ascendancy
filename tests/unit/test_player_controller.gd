extends GutTest

const PLAYER_SCENE: PackedScene = preload("res://features/player/player.tscn")

var _player: PlayerController


func before_each() -> void:
	var floor_body: StaticBody3D = StaticBody3D.new()
	var floor_shape: CollisionShape3D = CollisionShape3D.new()

	floor_shape.shape = WorldBoundaryShape3D.new()
	floor_body.add_child(floor_shape)
	add_child_autofree(floor_body)

	_player = PLAYER_SCENE.instantiate()
	add_child_autofree(_player)


func after_each() -> void:
	Input.action_release(&"move_forward")
	Input.action_release(&"sprint")
	Input.action_release(&"jump")


func test_player_jogs_forward_away_from_camera() -> void:
	var start: Vector3 = _player.global_position

	Input.action_press(&"move_forward")
	await wait_physics_frames(60)

	assert_lt(_player.global_position.z, start.z - 1.5, "moved toward -Z (camera forward)")
	assert_almost_eq(_player.global_position.x, start.x, 0.05)


func test_sprint_covers_more_ground_than_jog() -> void:
	var start: Vector3 = _player.global_position
	var jog_distance: float
	var sprint_distance: float

	Input.action_press(&"move_forward")
	await wait_physics_frames(60)
	jog_distance = start.distance_to(_player.global_position)

	Input.action_press(&"sprint")
	start = _player.global_position
	await wait_physics_frames(60)
	sprint_distance = start.distance_to(_player.global_position)

	assert_gt(sprint_distance, jog_distance * 1.3)


func test_disabled_input_keeps_player_still() -> void:
	var start: Vector3

	await wait_physics_frames(10)
	start = _player.global_position
	_player.is_input_enabled = false
	Input.action_press(&"move_forward")
	await wait_physics_frames(30)

	assert_almost_eq(_player.global_position.distance_to(start), 0.0, 0.01)


func test_jump_is_short_and_snappy() -> void:
	var peak_height: float = 0.0

	await wait_physics_frames(10)
	Input.action_press(&"jump")
	await wait_physics_frames(2)
	Input.action_release(&"jump")

	for frame in 40:
		await wait_physics_frames(1)
		peak_height = maxf(peak_height, _player.global_position.y)

	assert_between(peak_height, 0.9, 1.4, "jump reaches about head-bump height")
	assert_true(_player.is_on_floor(), "back on the ground within ~0.7 s")


func test_flying_holds_altitude_without_gravity() -> void:
	var start_height: float

	_player.global_position.y = 5.0
	_player.set_flying(true)
	await wait_physics_frames(30)
	start_height = _player.global_position.y

	assert_almost_eq(start_height, 5.0, 0.05, "no gravity while flying")
