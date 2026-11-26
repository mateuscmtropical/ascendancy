class_name CharacterModel
extends Node3D
## Visual de um personagem: corpo montado (art/characters) + animações no mesmo esqueleto
## (bibliotecas UAL e os golpes de tools_src/build_combat_animations.py) + rosto animado.

const HAIR_MATERIAL_PREFIX: String = "MI_Hair"
# Cartões de cabelo têm dupla face; rugosidade baixa reflete o céu como mechas cinza-azuladas.
const HAIR_ROUGHNESS: float = 1.0
const SKELETON_PATH: NodePath = ^"Armature/Skeleton3D"
const BODY_NODE_NAME: StringName = &"Body"
const ANIMATION_BLEND_SECONDS: float = 0.2
## Tempo para o tronco e os braços voltarem à animação de baixo depois de um golpe em camada.
const UPPER_BODY_RELEASE_SECONDS: float = 0.18
## As poses UAL deixam a sola ~5 cm abaixo da origem; o corpo sobe para o pé pisar no chão.
const SOLE_LIFT: float = 0.05
## Detalhe pela distância à câmera (só moradores): até aqui o rosto anima.
const FACE_DETAIL_DISTANCE: float = 12.0
## Daqui em diante o corpo some (corte do próprio renderizador, com esmaecer) e a animação para.
const HIDE_DISTANCE: float = 80.0
const HIDE_FADE_MARGIN: float = 8.0
## Até a distância x (m) a animação avança a cada y segundos (0 = todo quadro). Esqueleto parado
## também poupa o skinning na GPU.
const ANIMATION_STEP_BY_DISTANCE: Array[Vector2] = [
	Vector2(15.0, 0.0),
	Vector2(35.0, 1.0 / 30.0),
	Vector2(HIDE_DISTANCE + HIDE_FADE_MARGIN, 1.0 / 15.0),
]

@export var body_scene: PackedScene
@export var hair_color: Color = Color("4a3426")
@export var start_animation: StringName = &"ual1/Idle"
@export var start_offset_seconds: float = 0.0
## Moradores: animação, rosto e corpo perdem detalhe com a distância. O jogador fica sempre cheio.
@export var uses_distance_detail: bool = false

var _current_animation: StringName
var _pending_animation_seconds: float = 0.0
var _body: Node3D
## Só existe em quem já deu golpe andando (o jogador); nasce no primeiro uso.
var _upper_body: UpperBodyOverlay

@onready var _animation_player: AnimationPlayer = $AnimationPlayer
@onready var _face: FaceAnimator = $FaceAnimator


func _ready() -> void:
	_current_animation = start_animation
	set_process(uses_distance_detail)

	if uses_distance_detail:
		_animation_player.callback_mode_process = (
			AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		)
		# Espalha os passos dos moradores por quadros diferentes.
		_pending_animation_seconds = randf() * ANIMATION_STEP_BY_DISTANCE[-1].y

	if body_scene:
		_build_body()


func _process(delta: float) -> void:
	var distance: float = _distance_to_camera()
	var step_seconds: float = animation_step_for(distance)

	_face.set_detailed(distance < FACE_DETAIL_DISTANCE)
	_pending_animation_seconds += delta

	if _pending_animation_seconds < step_seconds:
		return

	_animation_player.advance(_pending_animation_seconds)
	_pending_animation_seconds = 0.0


## Intervalo entre passos da animação a esta distância da câmera; INF = escondido, não anima.
static func animation_step_for(distance: float) -> float:
	for reach in ANIMATION_STEP_BY_DISTANCE:
		if distance < reach.x:
			return reach.y

	return INF


func set_body(new_body_scene: PackedScene, new_hair_color: Color) -> void:
	var old_body: Node = get_node_or_null(NodePath(BODY_NODE_NAME))

	body_scene = new_body_scene
	hair_color = new_hair_color

	# A camada do tronco mora no esqueleto antigo e vai embora com ele.
	_upper_body = null

	if old_body:
		remove_child(old_body)
		old_body.queue_free()

	_build_body()


## blend_seconds menor que o padrão serve para golpes, que não podem amolecer na entrada.
## from_seconds entra no meio do clipe (golpe que já vinha tocando só no tronco).
func play_animation(
	animation_name: StringName,
	speed: float = 1.0,
	blend_seconds: float = ANIMATION_BLEND_SECONDS,
	from_seconds: float = 0.0
) -> void:
	_current_animation = animation_name
	_animation_player.speed_scale = 1.0
	_animation_player.play(animation_name, blend_seconds, speed)

	if from_seconds > 0.0:
		_animation_player.seek(from_seconds)


## Ritmo do ciclo que está tocando: a passada acompanha a velocidade real do corpo. Vale até a
## próxima troca de animação.
func pace_animation(pace: float) -> void:
	_animation_player.speed_scale = pace


## Toca um clipe só da cintura para cima, por cima da animação do corpo (soco andando).
func play_upper_body(animation_name: StringName, speed: float, blend_seconds: float) -> void:
	var clip: Animation = _animation_player.get_animation(animation_name)

	if _upper_body == null:
		_upper_body = UpperBodyOverlay.new()
		_body.get_node(SKELETON_PATH).add_child(_upper_body)

	_upper_body.play(clip, speed, blend_seconds)


func stop_upper_body() -> void:
	if _upper_body != null:
		_upper_body.stop(UPPER_BODY_RELEASE_SECONDS)


## Peso do corpo por cima da animação: lean inclina a partir dos pés (x = para a frente,
## y = para a esquerda, em rad) e stretch estica (>0) ou amassa (<0) a altura mantendo o volume.
func set_sway(lean: Vector2, stretch: float) -> void:
	var height: float = 1.0 + stretch
	var width: float = 1.0 / sqrt(height)
	var tilt: Basis = Basis.from_euler(Vector3(lean.x, 0.0, -lean.y))

	_body.basis = tilt * Basis.from_scale(Vector3(width, height, width))


## Expressão do rosto; com hold_seconds ela passa e o rosto volta à de descanso.
func show_expression(expression: FaceAnimator.Mood, hold_seconds: float = 0.0) -> void:
	_face.show_expression(expression, hold_seconds)


## Expressão para onde o rosto volta sozinho (neutra na cidade, concentrada em guarda).
func rest_expression(expression: FaceAnimator.Mood) -> void:
	_face.resting_expression = expression
	_face.show_expression(expression)


## Falando, o rosto mexe a boca em sílabas até mandar parar.
func set_talking(is_talking: bool) -> void:
	_face.is_talking = is_talking


## Onde a animação atual está no próprio ciclo, em segundos.
func animation_seconds() -> float:
	return _animation_player.current_animation_position


## Onde a animação atual está no próprio ciclo, de 0 a 1.
func animation_phase() -> float:
	var length: float = _animation_player.current_animation_length

	return _animation_player.current_animation_position / maxf(length, 0.001)


## Toca um trecho único (impulso, aterrissagem) e emenda no ciclo seguinte.
func play_animation_then(first_animation: StringName, next_animation: StringName) -> void:
	_current_animation = next_animation
	_animation_player.speed_scale = 1.0
	_animation_player.play(first_animation, ANIMATION_BLEND_SECONDS)
	_animation_player.queue(next_animation)


func _build_body() -> void:
	var body: Node3D = body_scene.instantiate()

	body.name = BODY_NODE_NAME
	body.position.y = SOLE_LIFT
	add_child(body)
	_body = body

	_tint_hair(body.get_node(SKELETON_PATH))

	if uses_distance_detail:
		_hide_from_afar(body)

	_face.bind(body.get_node(SKELETON_PATH))
	_animation_player.clear_caches()
	_animation_player.play(_current_animation)
	_animation_player.seek(start_offset_seconds, true)


func _tint_hair(skeleton: Skeleton3D) -> void:
	var hair_meshes: Array[MeshInstance3D] = []

	for child in skeleton.get_children():
		if child is MeshInstance3D and _is_hair_mesh(child):
			hair_meshes.append(child)

	for hair_mesh in hair_meshes:
		var tinted_material: StandardMaterial3D = hair_mesh.mesh.surface_get_material(0).duplicate()

		tinted_material.albedo_color = hair_color
		tinted_material.roughness = HAIR_ROUGHNESS
		hair_mesh.set_surface_override_material(0, tinted_material)


## Sem câmera (testes) conta como perto: detalhe cheio.
func _distance_to_camera() -> float:
	var camera: Camera3D = get_viewport().get_camera_3d()

	if camera == null:
		return 0.0

	return camera.global_position.distance_to(global_position)


func _hide_from_afar(body: Node) -> void:
	var meshes: Array[Node] = body.find_children("*", "GeometryInstance3D", true, false)

	for mesh in meshes:
		var geometry: GeometryInstance3D = mesh as GeometryInstance3D

		geometry.visibility_range_end = HIDE_DISTANCE
		geometry.visibility_range_end_margin = HIDE_FADE_MARGIN
		geometry.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF


func _is_hair_mesh(mesh_instance: MeshInstance3D) -> bool:
	var material: Material = mesh_instance.mesh.surface_get_material(0)

	return material.resource_name.begins_with(HAIR_MATERIAL_PREFIX)
