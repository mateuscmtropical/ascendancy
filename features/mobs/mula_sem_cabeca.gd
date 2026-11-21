class_name MulaSemCabeca
extends Node3D
## Mula sem cabeça (folclore brasileiro): visual do mob, sem IA nem combate.
## O modelo vem de tools_src/build_mula_sem_cabeca.py. Aqui: toca a animação em laço, troca o
## material das veias pelo shader que pulsa e o das labaredas em fita (malha MulaFlames) pelo shader
## de chama, pendura brasas, fumaça e luz nos marcadores Fire* que o modelo traz presos aos ossos
## (cada um recebe a cópia do filho de FireTemplates do seu tipo), balança as pontas de corrente
## partida, faz as luzes do fogo tremerem e apaga o fogo quando a mula morre.
## Longe da câmera ou fora da tela ela perde detalhe: a animação avança em passos mais espaçados
## (esqueleto parado poupa o skinning e o arrasto das ~40 partículas presas aos ossos) e o fogo
## preso ao corpo some (partícula escondida não é processada); a luz dele já esmaeceu antes disso.

const IDLE_ANIMATION: StringName = &"Idle"
const WALK_ANIMATION: StringName = &"Walk"
const RUN_ANIMATION: StringName = &"Run"
const ATTACK_ANIMATION: StringName = &"Attack"
const DEATH_ANIMATION: StringName = &"Death"
const LOOPING_ANIMATIONS: Array[StringName] = [IDLE_ANIMATION, WALK_ANIMATION, RUN_ANIMATION]
const ANIMATION_BLEND_SECONDS: float = 0.25
const FIRE_MARKER_PATTERN: String = "Fire*"
const FIRE_MARKER_NUMBER_SEPARATOR: String = "_"
## Tipo do marcador (nome até o "_") -> filho de FireTemplates copiado para ele.
const FIRE_TEMPLATE_BY_MARKER_KIND: Dictionary[String, String] = {
	"FireStump": "StumpFire",
	"FireMane": "ManeFire",
	"FireTail": "TailFire",
	"FireHoof": "HoofFire",
}
## Ossos das pontas de corrente partida (quantos houver: o gerador decide).
const CHAIN_BONE_PREFIX: String = "Chain"
## O assento vai preso a este osso: sobe, desce e balança com o galope, e quem monta junto.
const SADDLE_BONE: StringName = &"Torso"
## Balanço das correntes (radianos) conforme o passo.
const CHAIN_SWAY_BY_ANIMATION: Dictionary[StringName, float] = {
	IDLE_ANIMATION: 0.07,
	WALK_ANIMATION: 0.16,
	RUN_ANIMATION: 0.34,
	ATTACK_ANIMATION: 0.4,
	DEATH_ANIMATION: 0.0,
}
const CHAIN_SWAY_SPEED: Vector2 = Vector2(2.3, 1.7)
const CHAIN_PHASE_STEP: float = 1.9
const LIGHT_FLICKER_SPEED: float = 9.0
const LIGHT_FLICKER_SHARE: float = 0.3
## As fitas de fogo abrem no shader para além da caixa da malha (metros).
const FLAME_CULL_MARGIN: float = 1.5
## Parâmetro de instância dos shaders de veia e de labareda: 1 acesa, 0 apagada.
const BURN_PARAMETER: StringName = &"burn"
const BURN_BY_ANIMATION: Dictionary[StringName, float] = {DEATH_ANIMATION: 0.0}
const BURN_FADE_SECONDS: float = 1.6
## Morta, a lava das veias ainda fica em brasa fraca.
const VEIN_BURN_WHEN_DEAD: float = 0.18
## Pegadas: o casco "pisa" quando o marcador desce abaixo de HOOF_CONTACT_HEIGHT (metros acima
## do chão da mula, no tamanho original; cresce junto com a escala do nó Model) e só pisa de novo
## depois de subir acima de HOOF_LIFT_HEIGHT.
const HOOF_MARKER_PATTERN: String = "FireHoof*"
const STUMP_MARKER_NAME: String = "FireStump"
const HOOF_CONTACT_HEIGHT: float = 0.1
const HOOF_LIFT_HEIGHT: float = 0.17
const FOOTPRINT_SIZE: float = 0.36
const FOOTPRINT_FLAME_SHARE: float = 0.2
const HORSESHOE: float = 1.0
const STAIN: float = 0.0
## Pingos de lava do toco: de tempos em tempos uma manchinha no chão embaixo dele.
const DRIP_STAIN_SIZE: float = 0.16
const DRIP_STAIN_SECONDS: float = 0.4
const DRIP_STAIN_SPREAD: float = 0.3
const MIN_BURN_TO_MARK: float = 0.5
## Detalhe pela distância à câmera: até a distância x (m) a animação avança a cada y segundos
## (0 = todo quadro); além da última, a cada FAR_ANIMATION_STEP_SECONDS.
const ANIMATION_STEP_BY_DISTANCE: Array[Vector2] = [
	Vector2(30.0, 0.0),
	Vector2(60.0, 1.0 / 30.0),
]
const FAR_ANIMATION_STEP_SECONDS: float = 1.0 / 15.0
## Daqui em diante o fogo preso ao corpo (labaredas, fumaça, faíscas, luzes) fica escondido.
const FIRE_DETAIL_DISTANCE: float = 90.0
## Caixa do aviso de tela: corpo, fogo e fumaça do toco (metros, no espaço da mula).
const SCREEN_CHECK_BOUNDS: AABB = AABB(Vector3(-3.0, -0.5, -3.5), Vector3(6.0, 7.0, 7.0))

@export var start_animation: StringName = IDLE_ANIMATION
@export var vein_material: ShaderMaterial
@export var flame_ribbon_material: ShaderMaterial

## No ar (montada, voando) os cascos não marcam o chão.
var is_airborne: bool = false
## Montada: a câmera está colada nela, então anima a cada quadro e não confere distância nem tela.
var has_rider: bool = false

var _chain_sway: float = 0.0
var _burn: float = 1.0
var _burn_tween: Tween
var _fire_emitters: Array[GPUParticles3D] = []
var _seconds_alive: float = 0.0
var _chain_bone_indices: PackedInt32Array = PackedInt32Array()
var _chain_rest_rotations: Array[Quaternion] = []
var _fire_lights: Array[OmniLight3D] = []
var _fire_light_energies: PackedFloat32Array = PackedFloat32Array()
var _hoof_markers: Array[Node3D] = []
var _hoof_is_down: PackedByteArray = PackedByteArray()
var _stump_marker: Node3D
var _seconds_to_drip_stain: float = 0.0
var _body_scale: float = 1.0
var _pending_animation_seconds: float = 0.0
var _screen_check: VisibleOnScreenNotifier3D
var _fire_nodes: Array[Node3D] = []
var _is_fire_shown: bool = true

@onready var _model: Node3D = $Model
@onready var _skeleton: Skeleton3D = $Model.find_child("Skeleton3D") as Skeleton3D
@onready
var _animation_player: AnimationPlayer = $Model.find_child("AnimationPlayer") as AnimationPlayer
@onready var _veins: MeshInstance3D = $Model.find_child("MulaVeins") as MeshInstance3D
@onready var _flames: MeshInstance3D = $Model.find_child("MulaFlames") as MeshInstance3D
@onready var _fire_templates: Node3D = $FireTemplates
@onready var _lava_marks: LavaMarks = $LavaMarks
@onready var _saddle: Marker3D = $Saddle
@onready var _turbo_flames: GPUParticles3D = $TurboJet/Flames
@onready var _turbo_smoke: GPUParticles3D = $TurboJet/Smoke
@onready var _turbo_light: OmniLight3D = $TurboJet/Light


func _ready() -> void:
	_body_scale = _model.scale.x

	_veins.material_override = vein_material
	_flames.material_override = flame_ribbon_material
	_flames.extra_cull_margin = FLAME_CULL_MARGIN

	_loop_gait_animations()
	_hang_fire_on_markers()
	_collect_chain_bones()
	_attach_saddle_to_back()
	_collect_lava_sources()
	_watch_the_screen()
	play_animation(start_animation)


func _process(delta: float) -> void:
	var distance: float = _distance_to_camera()
	var is_on_screen: bool = _screen_check.is_on_screen()

	_seconds_alive += delta
	_pending_animation_seconds += delta

	_show_fire(should_show_fire(distance, is_on_screen))
	_step_animation(0.0 if has_rider else animation_step_for(distance, is_on_screen))
	_sway_chains()
	_flicker_lights()

	if _burn > MIN_BURN_TO_MARK and not is_airborne:
		_leave_footprints()
		_leave_drip_stains(delta)


func play_animation(animation_name: StringName) -> void:
	if _animation_player.current_animation == animation_name:
		return

	_chain_sway = CHAIN_SWAY_BY_ANIMATION.get(animation_name, 0.0)
	_animation_player.play(animation_name, ANIMATION_BLEND_SECONDS)
	_pending_animation_seconds = 0.0
	_fade_fire_to(BURN_BY_ANIMATION.get(animation_name, 1.0))


## Intervalo entre passos da animação a esta distância da câmera; INF = fora da tela, parada.
static func animation_step_for(distance: float, is_on_screen: bool) -> float:
	if not is_on_screen:
		return INF

	for reach in ANIMATION_STEP_BY_DISTANCE:
		if distance < reach.x:
			return reach.y

	return FAR_ANIMATION_STEP_SECONDS


static func should_show_fire(distance: float, is_on_screen: bool) -> bool:
	return is_on_screen and distance < FIRE_DETAIL_DISTANCE


## Turbo da montaria: jato de fogo pela traseira, como um foguete.
func set_turbo(is_on: bool) -> void:
	_turbo_flames.emitting = is_on
	_turbo_smoke.emitting = is_on
	_turbo_light.visible = is_on


func is_turbo_on() -> bool:
	return _turbo_light.visible


## Onde senta quem monta: posição e inclinação globais do lombo, que acompanham o passo.
func get_saddle_transform() -> Transform3D:
	return _saddle.global_transform


## Quanto do fogo está aceso: 1 viva, 0 morta e apagada.
func get_burn() -> float:
	return _burn


func _loop_gait_animations() -> void:
	for animation_name in LOOPING_ANIMATIONS:
		var animation: Animation = _animation_player.get_animation(animation_name)

		animation.loop_mode = Animation.LOOP_LINEAR


## O esqueleto vem na escala do pacote (o modelo é reduzido pelo nó raiz); o fogo é desenhado
## em metros do tamanho original e cresce só com a escala do nó Model, então cada cópia desfaz
## o resto da escala do marcador.
func _attach_saddle_to_back() -> void:
	var back: BoneAttachment3D = BoneAttachment3D.new()

	back.name = "SaddleBone"
	back.bone_name = SADDLE_BONE
	_skeleton.add_child(back)
	_saddle.reparent(back)


func _hang_fire_on_markers() -> void:
	var markers: Array[Node] = _skeleton.find_children(FIRE_MARKER_PATTERN, "Node3D", true, false)

	for marker in markers:
		_fire_nodes.append(_hang_fire_on_marker(marker as Node3D))

	_fire_templates.queue_free()

	for light in _skeleton.find_children("*", "OmniLight3D", true, false):
		_fire_lights.append(light as OmniLight3D)
		_fire_light_energies.append((light as OmniLight3D).light_energy)

	for emitter in _skeleton.find_children("*", "GPUParticles3D", true, false):
		_fire_emitters.append(emitter as GPUParticles3D)


## A animação avança à mão (AnimationPlayer em modo manual), no passo que a distância pede.
func _step_animation(step_seconds: float) -> void:
	if _pending_animation_seconds < step_seconds:
		return

	_animation_player.advance(_pending_animation_seconds)
	_pending_animation_seconds = 0.0


func _show_fire(is_shown: bool) -> void:
	if is_shown == _is_fire_shown:
		return

	_is_fire_shown = is_shown

	for fire in _fire_nodes:
		fire.visible = is_shown


func _watch_the_screen() -> void:
	_animation_player.callback_mode_process = (
		AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	)
	_screen_check = VisibleOnScreenNotifier3D.new()
	_screen_check.aabb = SCREEN_CHECK_BOUNDS
	add_child(_screen_check)


func _distance_to_camera() -> float:
	var camera: Camera3D = get_viewport().get_camera_3d()

	if camera == null:
		return 0.0

	return camera.global_position.distance_to(global_position)


func _fade_fire_to(target_burn: float) -> void:
	var is_burning: bool = target_burn > 0.0

	for emitter in _fire_emitters:
		emitter.emitting = is_burning

	if _burn_tween != null:
		_burn_tween.kill()

	_burn_tween = create_tween()
	_burn_tween.tween_method(_set_burn, _burn, target_burn, BURN_FADE_SECONDS)


func _set_burn(burn: float) -> void:
	var vein_burn: float = lerpf(VEIN_BURN_WHEN_DEAD, 1.0, burn)

	_burn = burn
	_flames.set_instance_shader_parameter(BURN_PARAMETER, burn)
	_veins.set_instance_shader_parameter(BURN_PARAMETER, vein_burn)


func _hang_fire_on_marker(marker: Node3D) -> Node3D:
	var marker_kind: String = marker.name.get_slice(FIRE_MARKER_NUMBER_SEPARATOR, 0)
	var template_name: String = FIRE_TEMPLATE_BY_MARKER_KIND[marker_kind]
	var template: Node3D = _fire_templates.get_node(template_name) as Node3D
	var fire: Node3D = template.duplicate() as Node3D
	var marker_scale: Vector3 = marker.global_basis.get_scale() / _model.global_basis.get_scale()

	fire.scale = Vector3.ONE / marker_scale
	marker.add_child(fire)

	return fire


func _collect_chain_bones() -> void:
	for bone_index in _skeleton.get_bone_count():
		if _skeleton.get_bone_name(bone_index).begins_with(CHAIN_BONE_PREFIX):
			_chain_bone_indices.append(bone_index)
			_chain_rest_rotations.append(
				_skeleton.get_bone_rest(bone_index).basis.get_rotation_quaternion()
			)


func _sway_chains() -> void:
	for chain_index in _chain_bone_indices.size():
		var phase: float = chain_index * CHAIN_PHASE_STEP
		var sideways_angle: float = sin(_seconds_alive * CHAIN_SWAY_SPEED.x + phase) * _chain_sway
		var lengthwise_angle: float = (
			sin(_seconds_alive * CHAIN_SWAY_SPEED.y + phase * 1.3) * _chain_sway
		)
		var sway: Quaternion = (
			Quaternion(Vector3.RIGHT, sideways_angle) * Quaternion(Vector3.BACK, lengthwise_angle)
		)

		_skeleton.set_bone_pose_rotation(
			_chain_bone_indices[chain_index], _chain_rest_rotations[chain_index] * sway
		)


func _flicker_lights() -> void:
	for light_index in _fire_lights.size():
		var fast_wave: float = sin(_seconds_alive * LIGHT_FLICKER_SPEED + light_index * 2.1)
		var slow_wave: float = sin(_seconds_alive * LIGHT_FLICKER_SPEED * 0.37 + light_index)
		var flicker: float = 1.0 + fast_wave * slow_wave * LIGHT_FLICKER_SHARE

		_fire_lights[light_index].light_energy = (
			_fire_light_energies[light_index] * flicker * _burn
		)


## Marcadores dos cascos e do toco, para as marcas de lava no chão.
func _collect_lava_sources() -> void:
	for marker in _skeleton.find_children(HOOF_MARKER_PATTERN, "Node3D", true, false):
		_hoof_markers.append(marker as Node3D)
		_hoof_is_down.append(1)

	_stump_marker = _skeleton.find_child(STUMP_MARKER_NAME, true, false) as Node3D


func _leave_footprints() -> void:
	for hoof_index in _hoof_markers.size():
		var hoof_position: Vector3 = _hoof_markers[hoof_index].global_position
		var height: float = hoof_position.y - global_position.y
		var was_down: bool = _hoof_is_down[hoof_index] == 1
		var has_landed: bool = not was_down and height < HOOF_CONTACT_HEIGHT * _body_scale

		if was_down and height > HOOF_LIFT_HEIGHT * _body_scale:
			_hoof_is_down[hoof_index] = 0

		if has_landed:
			_hoof_is_down[hoof_index] = 1
			_lava_marks.stamp(
				_ground_under(hoof_position),
				FOOTPRINT_SIZE * _body_scale,
				global_rotation.y,
				FOOTPRINT_FLAME_SHARE,
				HORSESHOE
			)


func _leave_drip_stains(delta: float) -> void:
	var scatter: Vector3 = (
		Vector3(randf() - 0.5, 0.0, randf() - 0.5) * 2.0 * DRIP_STAIN_SPREAD * _body_scale
	)

	_seconds_to_drip_stain -= delta

	if _seconds_to_drip_stain > 0.0:
		return

	_seconds_to_drip_stain = DRIP_STAIN_SECONDS
	_lava_marks.stamp(
		_ground_under(_stump_marker.global_position + scatter),
		DRIP_STAIN_SIZE * _body_scale,
		randf() * TAU,
		0.0,
		STAIN
	)


func _ground_under(source_position: Vector3) -> Vector3:
	return Vector3(source_position.x, global_position.y, source_position.z)
