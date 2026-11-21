extends GutTest
## Ao ar livre a câmera olhando para baixo sobe ~3,7 m acima do pivô: tem de parar embaixo do que
## avança sobre a calçada ou cobre o jogador (toldo, marquise, forro do coreto, lance de escada
## da torre). Esses colisores (CameraStop*) ficam numa camada que só o braço da câmera enxerga.

const PLAYER_SCENE: PackedScene = preload("res://features/player/player.tscn")
const SMITH_SCENE: PackedScene = preload("res://art/town/shops/shop_smith.gltf")
const CORETO_SCENE: PackedScene = preload("res://art/town/coreto.gltf")
const MARQUEE_HOUSE_SCENE: PackedScene = preload("res://art/town/houses/artdeco_w10_0.gltf")
const TOWERS_SCENE: PackedScene = preload("res://art/town/cathedral_towers.gltf")
const TAVERN_SCENE: PackedScene = preload("res://art/town/shops/shop_tavern.gltf")
const ALCHEMY_SCENE: PackedScene = preload("res://art/town/shops/shop_alchemy.gltf")
const GENERAL_SCENE: PackedScene = preload("res://art/town/shops/shop_general.gltf")
const IMPORT_SCRIPT: GDScript = preload("res://features/audio/tag_ground_surfaces.gd")
const LOOK_DOWN: Vector2 = Vector2(0.0, 2000.0)
const CAMERA_STOP_PREFIX: String = "CameraStop"
## Ferreiro na origem: o telheiro de ferrar cobre x 6,2..11,6 até 2,3 m da fachada e sobe até 3,9 m junto dela.
const LEAN_TO_SPOT: Vector3 = Vector3(9.6, 0.0, 1.2)
const LEAN_TO_TOP: float = 3.9
## Coreto na origem: piso a 1,2 m e o frechal (viga em volta do forro) com a face de baixo a 3,93 m.
const CORETO_SPOT: Vector3 = Vector3(0.0, 1.2, 1.5)
const CORETO_BEAM_UNDERSIDE: float = 3.93
## Casa art déco na origem: marquise de 1,1 m sobre a calçada, face de baixo a 3 m.
const MARQUEE_SPOT: Vector3 = Vector3(-3.0, 0.0, 0.6)
const MARQUEE_UNDERSIDE: float = 3.0
## Torres na posição da praça (hub.tscn): subindo um lance da torre sul, a câmera atrás do ombro não
## atravessa o pilar de canto do vão (face a x 16,23).
const TOWERS_TRANSFORM: Transform3D = Transform3D(
	Basis(Vector3.UP, -PI / 2.0), Vector3(13.0, 0.0, 0.0)
)
const TOWER_SPOT: Vector3 = Vector3(16.0, 10.7, -5.17)
const TOWER_NEWEL_FACE: float = 16.23
const NAVE_FLOOR: float = 1.0


func test_camera_stays_under_the_smith_lean_to() -> void:
	var camera: Camera3D = await _look_down_in(
		SMITH_SCENE, Transform3D.IDENTITY, LEAN_TO_SPOT, PI / 2.0, 0.0
	)

	assert_lt(camera.global_position.y, LEAN_TO_TOP, "camera under the lean-to")


func test_camera_stays_under_the_coreto_ceiling() -> void:
	var camera: Camera3D = await _look_down_in(
		CORETO_SCENE, Transform3D.IDENTITY, CORETO_SPOT, 0.0, 0.0
	)

	assert_lt(camera.global_position.y, CORETO_BEAM_UNDERSIDE, "camera under the ring beam")


func test_camera_stays_under_the_house_marquee() -> void:
	var camera: Camera3D = await _look_down_in(
		MARQUEE_HOUSE_SCENE, Transform3D.IDENTITY, MARQUEE_SPOT, PI / 2.0, 0.0
	)

	assert_lt(camera.global_position.y, MARQUEE_UNDERSIDE, "camera under the marquee")


func test_camera_stays_on_this_side_of_the_tower_newel() -> void:
	var camera: Camera3D = await _look_down_in(
		TOWERS_SCENE, TOWERS_TRANSFORM, TOWER_SPOT, PI / 2.0, NAVE_FLOOR
	)

	assert_lt(camera.global_position.x, TOWER_NEWEL_FACE, "camera before the newel post")


func test_camera_stops_sit_on_a_layer_only_the_camera_arm_sees() -> void:
	var player: PlayerController = PLAYER_SCENE.instantiate()
	var spring_arm: SpringArm3D = player.get_node("CameraYaw/CameraPitch/ShoulderArm/SpringArm3D")
	var camera_stops: Array[Node] = _camera_stops_of(
		[
			SMITH_SCENE,
			CORETO_SCENE,
			MARQUEE_HOUSE_SCENE,
			TOWERS_SCENE,
			TAVERN_SCENE,
			ALCHEMY_SCENE,
			GENERAL_SCENE
		]
	)

	add_child_autofree(player)

	assert_gt(camera_stops.size(), 0, "models carry camera stops")
	assert_eq(spring_arm.collision_mask & IMPORT_SCRIPT.CAMERA_LAYER, IMPORT_SCRIPT.CAMERA_LAYER)
	assert_eq(player.collision_mask & IMPORT_SCRIPT.CAMERA_LAYER, 0, "player walks through them")

	for camera_stop in camera_stops:
		assert_eq((camera_stop as CollisionObject3D).collision_layer, IMPORT_SCRIPT.CAMERA_LAYER)


func _camera_stops_of(scenes: Array[PackedScene]) -> Array[Node]:
	var camera_stops: Array[Node] = []

	for scene in scenes:
		var model: Node3D = scene.instantiate()
		var bodies: Array[Node] = model.find_children(CAMERA_STOP_PREFIX + "*", "StaticBody3D")

		add_child_autofree(model)
		camera_stops.append_array(bodies)

	return camera_stops


func _look_down_in(
	model_scene: PackedScene,
	model_transform: Transform3D,
	spot: Vector3,
	camera_yaw_angle: float,
	floor_height: float
) -> Camera3D:
	var model: Node3D = model_scene.instantiate()
	var ground: StaticBody3D = StaticBody3D.new()
	var ground_shape: CollisionShape3D = CollisionShape3D.new()
	var player: PlayerController = PLAYER_SCENE.instantiate()
	var camera_yaw: PlayerCamera

	model.transform = model_transform
	ground_shape.shape = WorldBoundaryShape3D.new()
	ground.position.y = floor_height
	ground.add_child(ground_shape)
	add_child_autofree(model)
	add_child_autofree(ground)
	add_child_autofree(player)
	player.global_position = spot
	player.make_camera_current()
	camera_yaw = player.get_node("CameraYaw")
	camera_yaw.rotation.y = camera_yaw_angle
	camera_yaw.rotate_by_mouse(LOOK_DOWN)
	await wait_physics_frames(10)

	return get_viewport().get_camera_3d()
