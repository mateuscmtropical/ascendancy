extends GutTest
## Olhando para baixo a câmera sobe atrás do jogador: num salão fechado ela tem de parar embaixo
## do teto que se vê (forro, vigas, rocha da catacumba), senão mostra o outro lado das paredes.

const PLAYER_SCENE: PackedScene = preload("res://features/player/player.tscn")
const CRYPT_SCENE: PackedScene = preload("res://art/town/cathedral_crypt.gltf")
const SMITH_SCENE: PackedScene = preload("res://art/town/shops/shop_smith.gltf")
const LOOK_DOWN: Vector2 = Vector2(0.0, 2000.0)
## Cripta na mesma posição da praça (hub.tscn); a galeria da catacumba tem 2,4 m de pé-direito.
const CRYPT_TRANSFORM: Transform3D = Transform3D(
	Basis(Vector3.UP, -PI / 2.0), Vector3(13.0, 0.0, 0.0)
)
const CATACOMB_SPOT: Vector3 = Vector3(-7.5, -4.6, -3.5)
const CATACOMB_CEILING: float = -2.35
## Ferreiro na origem: forro a 4,8 m e as vigas descendo 0,42 m.
const SMITH_SPOT: Vector3 = Vector3(0.0, 0.3, -9.0)
const SMITH_BEAM_UNDERSIDE: float = 4.38


func test_camera_stays_under_the_catacomb_ceiling() -> void:
	var camera: Camera3D = await _look_down_in(CRYPT_SCENE, CRYPT_TRANSFORM, CATACOMB_SPOT)

	assert_lt(camera.global_position.y, CATACOMB_CEILING, "camera under the rock ceiling")


func test_camera_stays_under_the_shop_beams() -> void:
	var camera: Camera3D = await _look_down_in(SMITH_SCENE, Transform3D.IDENTITY, SMITH_SPOT)

	assert_lt(camera.global_position.y, SMITH_BEAM_UNDERSIDE, "camera under the ceiling beams")


func _look_down_in(room_scene: PackedScene, room_transform: Transform3D, spot: Vector3) -> Camera3D:
	var room: Node3D = room_scene.instantiate()
	var player: PlayerController = PLAYER_SCENE.instantiate()
	var camera_yaw: PlayerCamera

	room.transform = room_transform
	add_child_autofree(room)
	add_child_autofree(player)
	player.global_position = spot
	player.make_camera_current()
	camera_yaw = player.get_node("CameraYaw")
	camera_yaw.rotate_by_mouse(LOOK_DOWN)
	await wait_physics_frames(10)

	return get_viewport().get_camera_3d()
