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


func test_jump_takes_the_mula_into_the_air() -> void:
	_mount.toggle_ride(_player)
	await wait_physics_frames(2)
	Input.action_press(&"jump")
	await wait_physics_frames(60)

	assert_gt(_mula.global_position.y, 2.0, "mula flies up")
	assert_true(_mula.is_airborne)


func test_dismount_leaves_the_mula_and_frees_the_player() -> void:
	_mount.toggle_ride(_player)
	await wait_physics_frames(5)
	_mount.toggle_ride(_player)
	await wait_physics_frames(5)

	assert_false(_player.is_riding())
	assert_false(_mount.is_ridden())
	assert_gt(_player.global_position.distance_to(_mula.global_position), 1.0, "stepped off")
