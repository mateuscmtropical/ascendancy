extends GutTest
## O jogador sobe degrau baixo andando e para em degrau alto ou parede.

const PLAYER_SCENE: PackedScene = preload("res://features/player/player.tscn")
const STEP_EDGE_X: float = 0.6


func test_climbs_low_step() -> void:
	var player: PlayerController = _player_before_step(0.13)
	var has_climbed: bool = player.climb_step(Vector3(0.5, 0.0, 0.0))

	assert_true(has_climbed)
	assert_almost_eq(player.global_position.y, 0.13, 0.02)


func test_stops_at_tall_step() -> void:
	var player: PlayerController = _player_before_step(0.6)
	var has_climbed: bool = player.climb_step(Vector3(0.5, 0.0, 0.0))

	assert_false(has_climbed)
	assert_almost_eq(player.global_position.y, 0.0, 0.001)


func test_ignores_open_ground() -> void:
	var player: PlayerController = _player_before_step(0.13)
	var has_climbed: bool = player.climb_step(Vector3(0.0, 0.0, 0.5))

	assert_false(has_climbed)


func _player_before_step(step_height: float) -> PlayerController:
	var player: PlayerController = PLAYER_SCENE.instantiate()

	add_child_autofree(_box(Vector3(20.0, 1.0, 20.0), Vector3(0.0, -0.5, 0.0)))
	add_child_autofree(
		_box(Vector3(4.0, step_height, 4.0), Vector3(STEP_EDGE_X + 2.0, step_height / 2.0, 0.0))
	)
	add_child_autofree(player)
	player.is_input_enabled = false
	player.global_position = Vector3(STEP_EDGE_X - 0.34, 0.0, 0.0)

	return player


func _box(size: Vector3, center: Vector3) -> StaticBody3D:
	var body: StaticBody3D = StaticBody3D.new()
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()

	box.size = size
	shape.shape = box
	body.add_child(shape)
	body.position = center

	return body
