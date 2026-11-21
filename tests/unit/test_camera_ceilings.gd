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
## Ferreiro na origem: a oficina tem o telhado à vista; o tirante das tesouras tem a face de
## baixo a 4,03 m.
const SMITH_SPOT: Vector3 = Vector3(0.0, 0.3, -9.0)
const SMITH_BEAM_UNDERSIDE: float = 4.03
const TAVERN_SCENE: PackedScene = preload("res://art/town/shops/shop_tavern.gltf")
## Taverna na origem, no salão diante do balcão: forro baixo a 3,6 m, viga-mestra descendo 0,32 m.
const TAVERN_SPOT: Vector3 = Vector3(-5.5, 0.3, -9.0)
const TAVERN_BEAM_UNDERSIDE: float = 3.28
const ALCHEMY_SCENE: PackedScene = preload("res://art/town/shops/shop_alchemy.gltf")
## Botica na origem, na Offizin junto da fachada: a abóbada nasce a 2,9 m e ali, a 1,3 m da
## parede, ainda está abaixo de 3,7 m (o forro plano e o colisor dele ficam acima, a 4,15 m).
const ALCHEMY_SPOT: Vector3 = Vector3(1.0, 0.3, -1.6)
const ALCHEMY_VAULT_UNDERSIDE: float = 3.7


func test_camera_stays_under_the_catacomb_ceiling() -> void:
	var camera: Camera3D = await _look_down_in(CRYPT_SCENE, CRYPT_TRANSFORM, CATACOMB_SPOT)

	assert_lt(camera.global_position.y, CATACOMB_CEILING, "camera under the rock ceiling")


func test_camera_stays_under_the_shop_beams() -> void:
	var camera: Camera3D = await _look_down_in(SMITH_SCENE, Transform3D.IDENTITY, SMITH_SPOT)

	assert_lt(camera.global_position.y, SMITH_BEAM_UNDERSIDE, "camera under the ceiling beams")


func test_camera_stays_under_the_tavern_beams() -> void:
	var camera: Camera3D = await _look_down_in(TAVERN_SCENE, Transform3D.IDENTITY, TAVERN_SPOT)

	assert_lt(camera.global_position.y, TAVERN_BEAM_UNDERSIDE, "camera under the taproom beams")


func test_camera_follows_the_offizin_vault() -> void:
	var camera: Camera3D = await _look_down_in(ALCHEMY_SCENE, Transform3D.IDENTITY, ALCHEMY_SPOT)

	assert_lt(camera.global_position.y, ALCHEMY_VAULT_UNDERSIDE, "camera under the Offizin vault")


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
