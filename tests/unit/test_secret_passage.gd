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
