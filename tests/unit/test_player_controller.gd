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


func test_kick_on_the_run_survives_stepping_onto_a_curb() -> void:
	var curb: StaticBody3D = StaticBody3D.new()
	var curb_shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()
	var fighter: UnarmedFighter = _player.get_node("UnarmedFighter")
	var struck: Array[UnarmedFighter.Move] = []

	box.size = Vector3(4.0, 0.15, 4.0)
	curb_shape.shape = box
	curb.add_child(curb_shape)
	curb.position = Vector3(0.0, 0.075, -2.6)
	add_child_autofree(curb)
	fighter.strike_reached.connect(func(move: UnarmedFighter.Move) -> void: struck.append(move))
	Input.action_press(&"move_forward")
	await wait_physics_frames(6)
	fighter.request_attack(UnarmedFighter.Attack.KICK)
	await wait_physics_frames(45)

	assert_gt(_player.global_position.y, 0.1, "went up the curb during the kick")
	assert_eq(struck.size(), 1, "the kick still landed")


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


func test_stride_follows_the_ground_speed() -> void:
	var animation_player: AnimationPlayer = _player.get_node("CharacterModel/AnimationPlayer")
	var jog_pace: float = PlayerController.ANIMATION_SPEED_BY_STANCE[PlayerController.Stance.RUN]
	var starting_pace: float

	await wait_physics_frames(10)
	Input.action_press(&"move_forward")
	await wait_physics_frames(3)
	starting_pace = animation_player.speed_scale
	await wait_physics_frames(40)

	assert_eq(String(animation_player.current_animation), "combat/Run")
	assert_lt(starting_pace, jog_pace * 0.8, "slow strides while the body is still speeding up")
	assert_almost_eq(animation_player.speed_scale, jog_pace, 0.01, "full stride at full speed")

	Input.action_release(&"move_forward")
	await wait_physics_frames(30)

	assert_eq(animation_player.speed_scale, 1.0, "standing still plays at its own pace")


func test_steps_sound_with_the_stride_not_with_a_clock() -> void:
	var footsteps: FootstepPlayer = _player.get_node("Footsteps")

	await wait_physics_frames(10)
	watch_signals(footsteps)
	await wait_physics_frames(30)

	assert_signal_emit_count(footsteps, "stepped", 0, "silent while standing")

	Input.action_press(&"move_forward")
	await wait_physics_frames(120)

	# Corrida: ciclo de 0,93 s tocado a 1,24 = um passo a cada 0,38 s.
	assert_between(get_signal_emit_count(footsteps, "stepped"), 4, 6, "two footfalls per cycle")


func test_no_two_steps_sound_on_top_of_each_other() -> void:
	var footsteps: FootstepPlayer = _player.get_node("Footsteps")
	var step_frames: Array[int] = []
	var closest_frames: int = 1000

	footsteps.stepped.connect(func() -> void: step_frames.append(Engine.get_physics_frames()))
	Input.action_press(&"move_forward")
	await wait_physics_frames(40)
	Input.action_press(&"jump")
	await wait_physics_frames(2)
	Input.action_release(&"jump")
	await wait_physics_frames(70)
	Input.action_press(&"sprint")
	await wait_physics_frames(50)
	Input.action_release(&"sprint")
	await wait_physics_frames(40)

	for index in range(1, step_frames.size()):
		closest_frames = mini(closest_frames, step_frames[index] - step_frames[index - 1])

	assert_gt(step_frames.size(), 5, "kept stepping through the jump and the gait changes")
	assert_gt(closest_frames, 8, "landing or changing gait never doubles a step (0.15 s apart)")


func test_body_leans_into_the_start_and_stands_up_again() -> void:
	var body: Node3D = _player.get_node("CharacterModel/Body")
	var forward: Vector3
	var start_lean: float

	await wait_physics_frames(10)
	Input.action_press(&"move_forward")
	await wait_physics_frames(10)
	forward = Vector3(_player.velocity.x, 0.0, _player.velocity.z).normalized()
	start_lean = body.global_basis.y.dot(forward)
	await wait_physics_frames(90)

	assert_gt(start_lean, 0.03, "head ahead of the feet while speeding up")
	assert_almost_eq(body.global_basis.y.dot(forward), 0.0, 0.01, "upright at steady speed")


func test_landing_squashes_the_body_for_a_moment() -> void:
	var body: Node3D = _player.get_node("CharacterModel/Body")
	var shortest: float = 1.0

	await wait_physics_frames(10)
	Input.action_press(&"jump")
	await wait_physics_frames(2)
	Input.action_release(&"jump")

	for frame in 70:
		await wait_physics_frames(1)
		shortest = minf(shortest, body.global_basis.get_scale().y)

	assert_lt(shortest, 0.96, "squash on landing")
	assert_almost_eq(body.global_basis.get_scale().y, 1.0, 0.01, "full height again")


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


func test_camera_never_drops_under_the_floor_when_looking_up() -> void:
	var pitch_steps: int = 28

	for step in pitch_steps + 1:
		var pitch: float = lerpf(0.0, PlayerCamera.PITCH_MAX, float(step) / pitch_steps)
		var camera_height: float = (
			PlayerCamera.pivot_height_for(pitch) - PlayerCamera.arm_length_for(pitch) * sin(pitch)
		)

		assert_gte(camera_height, PlayerCamera.LOOK_UP_CAMERA_HEIGHT - 0.001)


func test_camera_stays_inside_when_a_wall_is_beside_the_player() -> void:
	# Encostado na parede: o ombro da câmera (0,35 m) passaria do lado de fora dela.
	var wall_x: float = 0.34
	var camera: Camera3D

	_add_wall(Vector3(wall_x + 0.5, 1.5, 0.0), Vector3(1.0, 3.0, 12.0))
	await wait_physics_frames(3)
	camera = get_viewport().get_camera_3d()

	assert_lt(camera.global_position.x, wall_x, "camera on the player's side of the wall")


func test_camera_stays_inside_when_a_wall_is_behind_the_player() -> void:
	var wall_z: float = 1.0
	var camera: Camera3D

	_add_wall(Vector3(0.0, 1.5, wall_z + 0.5), Vector3(12.0, 3.0, 1.0))
	await wait_physics_frames(3)
	camera = get_viewport().get_camera_3d()

	assert_lt(camera.global_position.z, wall_z, "camera in front of the wall")


func _add_wall(center: Vector3, size: Vector3) -> void:
	var wall_body: StaticBody3D = StaticBody3D.new()
	var wall_shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()

	box.size = size
	wall_shape.shape = box
	wall_body.add_child(wall_shape)
	wall_body.position = center
	add_child_autofree(wall_body)
	_player.make_camera_current()
