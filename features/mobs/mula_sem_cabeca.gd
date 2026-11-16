class_name MulaSemCabeca
extends Node3D
## Mula sem cabeça (folclore brasileiro): visual do mob, sem IA nem combate.
## O modelo vem de tools_src/build_mula_sem_cabeca.py. Aqui: toca a animação em laço, troca o
## material das veias pelo shader que pulsa e o das labaredas em fita (malha MulaFlames) pelo shader
## de chama, pendura brasas, fumaça e luz nos marcadores Fire* que o modelo traz presos aos ossos
## (cada um recebe a cópia do filho de FireTemplates do seu tipo), balança as pontas de corrente
## partida, faz as luzes do fogo tremerem e apaga o fogo quando a mula morre.

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
## do chão da mula) e só pisa de novo depois de subir acima de HOOF_LIFT_HEIGHT.
const HOOF_MARKER_PATTERN: String = "FireHoof*"
const STUMP_MARKER_NAME: String = "FireStump"
const HOOF_CONTACT_HEIGHT: float = 0.1
const HOOF_LIFT_HEIGHT: float = 0.17
const FOOTPRINT_SIZE: float = 0.36
const FOOTPRINT_FLAME_SHARE: float = 0.4
const HORSESHOE: float = 1.0
const STAIN: float = 0.0
## Pingos de lava do toco: de tempos em tempos uma manchinha no chão embaixo dele.
const DRIP_STAIN_SIZE: float = 0.16
const DRIP_STAIN_SECONDS: float = 0.4
const DRIP_STAIN_SPREAD: float = 0.3
const MIN_BURN_TO_MARK: float = 0.5

@export var start_animation: StringName = IDLE_ANIMATION
@export var vein_material: ShaderMaterial
@export var flame_ribbon_material: ShaderMaterial

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

@onready var _skeleton: Skeleton3D = $Model.find_child("Skeleton3D") as Skeleton3D
@onready
var _animation_player: AnimationPlayer = $Model.find_child("AnimationPlayer") as AnimationPlayer
@onready var _veins: MeshInstance3D = $Model.find_child("MulaVeins") as MeshInstance3D
@onready var _flames: MeshInstance3D = $Model.find_child("MulaFlames") as MeshInstance3D
@onready var _fire_templates: Node3D = $FireTemplates
@onready var _lava_marks: LavaMarks = $LavaMarks


func _ready() -> void:
	_veins.material_override = vein_material
	_flames.material_override = flame_ribbon_material
	_flames.extra_cull_margin = FLAME_CULL_MARGIN

	_loop_gait_animations()
	_hang_fire_on_markers()
	_collect_chain_bones()
	_collect_lava_sources()
	play_animation(start_animation)


func _process(delta: float) -> void:
	_seconds_alive += delta

	_sway_chains()
	_flicker_lights()

	if _burn > MIN_BURN_TO_MARK:
		_leave_footprints()
		_leave_drip_stains(delta)


func play_animation(animation_name: StringName) -> void:
	_chain_sway = CHAIN_SWAY_BY_ANIMATION.get(animation_name, 0.0)
	_animation_player.play(animation_name, ANIMATION_BLEND_SECONDS)
	_fade_fire_to(BURN_BY_ANIMATION.get(animation_name, 1.0))


## Quanto do fogo está aceso: 1 viva, 0 morta e apagada.
func get_burn() -> float:
	return _burn


func _loop_gait_animations() -> void:
	for animation_name in LOOPING_ANIMATIONS:
		var animation: Animation = _animation_player.get_animation(animation_name)

		animation.loop_mode = Animation.LOOP_LINEAR


## O esqueleto vem na escala do pacote (o modelo é reduzido pelo nó raiz); o fogo é desenhado
## em metros, então cada cópia desfaz a escala do marcador.
func _hang_fire_on_markers() -> void:
	var markers: Array[Node] = _skeleton.find_children(FIRE_MARKER_PATTERN, "Node3D", true, false)

	for marker in markers:
		_hang_fire_on_marker(marker as Node3D)

	_fire_templates.queue_free()

	for light in _skeleton.find_children("*", "OmniLight3D", true, false):
		_fire_lights.append(light as OmniLight3D)
		_fire_light_energies.append((light as OmniLight3D).light_energy)

	for emitter in _skeleton.find_children("*", "GPUParticles3D", true, false):
		_fire_emitters.append(emitter as GPUParticles3D)


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


func _hang_fire_on_marker(marker: Node3D) -> void:
	var marker_kind: String = marker.name.get_slice(FIRE_MARKER_NUMBER_SEPARATOR, 0)
	var template_name: String = FIRE_TEMPLATE_BY_MARKER_KIND[marker_kind]
	var template: Node3D = _fire_templates.get_node(template_name) as Node3D
	var fire: Node3D = template.duplicate() as Node3D
	var marker_scale: Vector3 = marker.global_basis.get_scale() / global_basis.get_scale()

	fire.scale = Vector3.ONE / marker_scale
	marker.add_child(fire)


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
		var has_landed: bool = not was_down and height < HOOF_CONTACT_HEIGHT

		if was_down and height > HOOF_LIFT_HEIGHT:
			_hoof_is_down[hoof_index] = 0

		if has_landed:
			_hoof_is_down[hoof_index] = 1
			_lava_marks.stamp(
				_ground_under(hoof_position),
				FOOTPRINT_SIZE,
				global_rotation.y,
				FOOTPRINT_FLAME_SHARE,
				HORSESHOE
			)


func _leave_drip_stains(delta: float) -> void:
	var scatter: Vector3 = Vector3(randf() - 0.5, 0.0, randf() - 0.5) * 2.0 * DRIP_STAIN_SPREAD

	_seconds_to_drip_stain -= delta

	if _seconds_to_drip_stain > 0.0:
		return

	_seconds_to_drip_stain = DRIP_STAIN_SECONDS
	_lava_marks.stamp(
		_ground_under(_stump_marker.global_position + scatter),
		DRIP_STAIN_SIZE,
		randf() * TAU,
		0.0,
		STAIN
	)


func _ground_under(source_position: Vector3) -> Vector3:
	return Vector3(source_position.x, global_position.y, source_position.z)
