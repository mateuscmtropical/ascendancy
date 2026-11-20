extends GutTest

const PLAYER_SCENE: PackedScene = preload("res://features/player/player.tscn")
const MULA_SCENE: PackedScene = preload("res://features/mobs/mula_sem_cabeca.tscn")

var _player: PlayerController
var _mula: MulaSemCabeca
var _mount: MulaMount


func before_each() -> void:
	var floor_body: StaticBody3D = StaticBody3D.new()
	var floor_shape: CollisionShape3D = CollisionShape3D.new()

	floor_shape.shape = WorldBoundaryShape3D.new()
	floor_body.add_child(floor_shape)
	add_child_autofree(floor_body)

	_mula = MULA_SCENE.instantiate()
	add_child_autofree(_mula)
	_mula.position = Vector3(0.0, 0.0, -1.5)
	_mount = _mula.get_node("MountReach") as MulaMount

	_player = PLAYER_SCENE.instantiate()
	add_child_autofree(_player)
	await wait_physics_frames(5)


func after_each() -> void:
	Input.action_release(&"move_forward")
	Input.action_release(&"jump")
	Input.action_release(&"sprint")


func test_prompt_shows_when_the_player_is_near() -> void:
	assert_true(_mount.get_node("Prompt").visible)


func test_riding_carries_the_mula_along() -> void:
	var start: Vector3

	_mount.toggle_ride(_player)
	await wait_physics_frames(2)
	start = _mula.global_position
	Input.action_press(&"move_forward")
	await wait_physics_frames(60)

	assert_true(_player.is_riding())
	assert_gt(start.distance_to(_mula.global_position), 3.0, "mula galloped with the rider")
	assert_almost_eq(_mula.global_position.x, _player.global_position.x, 0.01)
	assert_false(_mount.get_node("Prompt").visible, "no prompt while riding")


func test_one_jump_tap_hops_and_lands() -> void:
	_mount.toggle_ride(_player)
	await wait_physics_frames(2)
	await _tap(&"jump")
	await wait_physics_frames(90)

	assert_almost_eq(_mula.global_position.y, 0.0, 0.1, "back on the ground")
	assert_false(_mula.is_airborne)


func test_two_jump_taps_take_the_mula_into_the_air() -> void:
	_mount.toggle_ride(_player)
	await wait_physics_frames(2)
	await _tap(&"jump")
	Input.action_press(&"jump")
	await wait_physics_frames(60)

	assert_gt(_mula.global_position.y, 2.0, "mula flies up")
	assert_true(_mula.is_airborne)


func test_two_sprint_taps_fire_the_turbo() -> void:
	var start: Vector3

	_mount.toggle_ride(_player)
	await wait_physics_frames(2)
	await _tap(&"sprint")
	Input.action_press(&"sprint")
	await wait_physics_frames(2)

	assert_true(_mula.is_turbo_on(), "fire jet on")

	start = _mula.global_position
	await wait_physics_frames(60)

	assert_gt(start.distance_to(_mula.global_position), 30.0, "rocket speed")


func test_mula_walks_over_a_bench_high_step() -> void:
	var step_body: StaticBody3D = StaticBody3D.new()
	var step_shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()

	box.size = Vector3(6.0, 0.55, 1.0)
	step_shape.shape = box
	step_body.add_child(step_shape)
	step_body.position = Vector3(0.0, 0.275, -6.0)
	add_child_autofree(step_body)
	_mount.toggle_ride(_player)
	await wait_physics_frames(2)
	Input.action_press(&"move_forward")
	await wait_physics_frames(60)

	assert_lt(_mula.global_position.z, -7.0, "crossed the bench line")


func test_summoned_mula_flies_to_the_caller() -> void:
	var caller: Node3D = Node3D.new()

	add_child_autofree(caller)
	caller.global_position = Vector3(40.0, 0.0, 30.0)
	_mount.summon_to(caller)
	await wait_physics_frames(10)

	assert_true(_mula.is_airborne, "flying over")

	await wait_physics_frames(150)

	assert_lt(_mula.global_position.distance_to(caller.global_position), 3.0, "landed beside")
	assert_false(_mount.is_flying_to_caller())


func test_dismount_leaves_the_mula_and_frees_the_player() -> void:
	_mount.toggle_ride(_player)
	await wait_physics_frames(5)
	_mount.toggle_ride(_player)
	await wait_physics_frames(5)

	assert_false(_player.is_riding())
	assert_false(_mount.is_ridden())
	assert_gt(_player.global_position.distance_to(_mula.global_position), 1.0, "stepped off")


func _tap(action: StringName) -> void:
	Input.action_press(action)
	await wait_physics_frames(2)
	Input.action_release(action)
	await wait_physics_frames(2)
