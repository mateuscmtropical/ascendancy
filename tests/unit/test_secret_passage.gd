extends GutTest

const PASSAGE_SCENE: PackedScene = preload("res://features/hub/crypt_monument.tscn")


func test_prompt_shows_only_with_someone_near() -> void:
	var passage: SecretPassage = PASSAGE_SCENE.instantiate()
	var visitor: Node3D = Node3D.new()

	add_child_autofree(passage)
	autofree(visitor)
	assert_false(passage.is_prompt_shown())

	passage._on_body_entered(visitor)
	assert_true(passage.is_prompt_shown())

	passage._on_body_exited(visitor)
	assert_false(passage.is_prompt_shown())


func test_monument_slides_open_and_back() -> void:
	var passage: SecretPassage = PASSAGE_SCENE.instantiate()
	var mover: Node3D

	add_child_autofree(passage)
	mover = passage.get_node("Mover")
	passage.toggle()
	await wait_seconds(SecretPassage.SWING_SECONDS + 0.3)
	assert_true(passage.is_open)
	assert_almost_eq(mover.position.x, passage.open_offset.x, 0.01)

	passage.toggle()
	await wait_seconds(SecretPassage.SWING_SECONDS + 0.3)
	assert_false(passage.is_open)
	assert_almost_eq(mover.position.x, 0.0, 0.01)


func test_does_not_close_on_someone_standing_in_the_gap() -> void:
	var passage: SecretPassage = PASSAGE_SCENE.instantiate()
	var visitor: CharacterBody3D = _make_visitor()
	var mover: Node3D

	add_child_autofree(passage)
	mover = passage.get_node("Mover")
	passage.toggle()
	await wait_seconds(SecretPassage.SWING_SECONDS + 0.3)

	passage.add_child(visitor)
	visitor.position = Vector3(-0.7, 0.95, 0.0)
	await wait_physics_frames(4)
	assert_true(passage.is_path_blocked())

	passage.toggle()
	await wait_seconds(SecretPassage.SWING_SECONDS + 0.3)
	assert_true(passage.is_open)
	assert_almost_eq(mover.position.x, passage.open_offset.x, 0.01)

	visitor.queue_free()
	await wait_physics_frames(4)
	assert_false(passage.is_path_blocked())

	passage.toggle()
	await wait_seconds(SecretPassage.SWING_SECONDS + 0.3)
	assert_false(passage.is_open)
	assert_almost_eq(mover.position.x, 0.0, 0.01)


func test_reopens_when_someone_steps_in_while_closing() -> void:
	var passage: SecretPassage = PASSAGE_SCENE.instantiate()
	var visitor: Node3D = Node3D.new()
	var mover: Node3D

	add_child_autofree(passage)
	autofree(visitor)
	mover = passage.get_node("Mover")
	passage.toggle()
	await wait_seconds(SecretPassage.SWING_SECONDS + 0.3)

	passage.toggle()
	await wait_seconds(SecretPassage.SWING_SECONDS * 0.4)
	assert_true(passage.is_closing())

	passage._on_path_body_entered(visitor)
	assert_true(passage.is_open)
	await wait_seconds(SecretPassage.SWING_SECONDS + 0.3)
	assert_almost_eq(mover.position.x, passage.open_offset.x, 0.01)


func _make_visitor() -> CharacterBody3D:
	var visitor: CharacterBody3D = CharacterBody3D.new()
	var collision: CollisionShape3D = CollisionShape3D.new()
	var capsule: CapsuleShape3D = CapsuleShape3D.new()

	capsule.radius = 0.3
	capsule.height = 1.8
	collision.shape = capsule
	visitor.collision_layer = 2
	visitor.collision_mask = 1
	visitor.add_child(collision)

	return visitor
