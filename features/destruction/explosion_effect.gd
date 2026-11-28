class_name ExplosionEffect
extends Node3D
## Visual da magia de explosão, posto no ponto do chão onde ela cai. play_charge mostra os
## círculos de runas crescendo e girando com faíscas convergindo; play_blast solta o clarão, a
## bola de fogo, a onda de choque, a poeira e a coluna de fumaça, com tamanho e duração pela
## energia (escala logarítmica de WEAK_ENERGY a STRONG_ENERGY). Só visual: cratera, fogo, som e
## quebra são de quem chama. O nó se apaga sozinho em qualquer caminho: carga sem explosão,
## explosão sem carga, explosão no meio da carga.

const WEAK_ENERGY: float = 300.0
const STRONG_ENERGY: float = 3000.0
## Raio da bola de fogo cheia, em metros.
const WEAK_RADIUS: float = 3.0
const STRONG_RADIUS: float = 9.0
## Quanto a explosão forte dura a mais.
const WEAK_PACE: float = 0.8
const STRONG_PACE: float = 1.3
## Carga que ninguém explodiu some este tanto depois de completa.
const CHARGE_GRACE_SECONDS: float = 0.6
const CHARGE_FADE_SECONDS: float = 0.3
const CHARGE_TURNS: float = 1.5
const CHARGE_GLOW_ENERGY: float = 4.0
const FLASH_SECONDS: float = 0.32
const FLASH_LIGHT_ENERGY: float = 24.0
const FIRE_LIGHT_ENERGY: float = 6.0
const FIRE_LIGHT_COLOR: Color = Color(1.0, 0.5, 0.15)
const FIREBALL_SECONDS: float = 1.5
const FIREBALL_RISE: float = 0.45
const SHOCKWAVE_SECONDS: float = 0.7
const SHOCKWAVE_REACH: float = 3.2
const LIGHT_REACH: float = 5.0
## Vida da partícula mais demorada (a fumaça), no ritmo 1.
const BLAST_SECONDS: float = 4.2

## Raio do círculo de runas do chão, em metros.
@export var charge_radius: float = 4.5

var _charge_tween: Tween
var _has_blasted: bool = false

@onready var _charge: Node3D = $Charge
@onready var _rune_ground: MeshInstance3D = $Charge/RuneGround
@onready var _rune_middle: MeshInstance3D = $Charge/RuneMiddle
@onready var _rune_top: MeshInstance3D = $Charge/RuneTop
@onready var _charge_sparks: GPUParticles3D = $Charge/Sparks
@onready var _charge_glow: OmniLight3D = $Charge/Glow
@onready var _blast: Node3D = $Blast
@onready var _fireball: MeshInstance3D = $Blast/Fireball
@onready var _shockwave: MeshInstance3D = $Blast/Shockwave
@onready var _flash: MeshInstance3D = $Blast/Flash
@onready var _blast_light: OmniLight3D = $Blast/Light
@onready var _bursts: Array[GPUParticles3D] = [
	$Blast/FireBurst, $Blast/SmokeColumn, $Blast/Dust, $Blast/Embers
]


## 0 a 1: onde a energia cai entre a explosão fraca e a cheia.
static func strength_of(energy: float) -> float:
	var span: float = log(STRONG_ENERGY / WEAK_ENERGY)

	return clampf(log(maxf(energy, 0.001) / WEAK_ENERGY) / span, 0.0, 1.0)


## Raio da bola de fogo dessa energia, em metros (medida para cratera e alcance do fogo).
static func blast_radius_of(energy: float) -> float:
	return lerpf(WEAK_RADIUS, STRONG_RADIUS, strength_of(energy))


## Círculos de runas crescendo e girando por seconds, com faíscas convergindo para o centro.
func play_charge(seconds: float) -> void:
	if _has_blasted:
		return

	_charge.visible = true
	_charge.scale = Vector3.ONE * charge_radius
	_charge_sparks.emitting = true
	_set_charge_fade(1.0)

	_charge_tween = create_tween()
	_charge_tween.set_parallel(true)
	_reveal_rune(_rune_ground, 0.0, seconds, CHARGE_TURNS)
	_reveal_rune(_rune_middle, 0.3, seconds, -CHARGE_TURNS * 1.4)
	_reveal_rune(_rune_top, 0.55, seconds, CHARGE_TURNS * 2.0)
	_charge_tween.tween_property(_charge_glow, "light_energy", CHARGE_GLOW_ENERGY, seconds)
	_charge_tween.chain().tween_interval(CHARGE_GRACE_SECONDS)
	_charge_tween.chain().tween_method(_set_charge_fade, 1.0, 0.0, CHARGE_FADE_SECONDS)
	_charge_tween.chain().tween_callback(queue_free)


## Clarão, bola de fogo, onda de choque, poeira e fumaça; o nó some quando a fumaça acaba.
func play_blast(energy: float) -> void:
	var strength: float = strength_of(energy)
	var radius: float = blast_radius_of(energy)
	var pace: float = lerpf(WEAK_PACE, STRONG_PACE, strength)
	var tween: Tween

	if _has_blasted:
		return

	_has_blasted = true
	_end_charge()
	_blast.visible = true
	_blast.scale = Vector3.ONE * radius
	_blast_light.omni_range = radius * LIGHT_REACH

	for burst in _bursts:
		_size_burst(burst, radius)
		burst.speed_scale = 1.0 / pace
		burst.restart()

	tween = create_tween()
	tween.set_parallel(true)
	_flash_white(tween, pace)
	_swell_fireball(tween, pace)
	_spread_shockwave(tween, pace)
	tween.chain().tween_interval(maxf(BLAST_SECONDS - FIREBALL_SECONDS, 0.0) * pace)
	tween.chain().tween_callback(queue_free)


## Um círculo aparece do centro para fora a partir de start_share da carga, girando cada vez mais
## rápido até o fim dela.
func _reveal_rune(rune: MeshInstance3D, start_share: float, seconds: float, turns: float) -> void:
	var delay: float = seconds * start_share

	rune.set_instance_shader_parameter(&"progress", 0.0)
	(
		_charge_tween
		. tween_method(_set_instance_parameter.bind(rune, &"progress"), 0.0, 1.0, seconds - delay)
		. set_delay(delay)
	)
	(
		_charge_tween
		. tween_property(rune, "rotation:y", TAU * turns, seconds)
		. set_trans(Tween.TRANS_QUAD)
		. set_ease(Tween.EASE_IN)
	)


func _end_charge() -> void:
	if _charge_tween != null:
		_charge_tween.kill()

	_charge.visible = false
	_charge_sparks.emitting = false


## A escala do nó move o ponto de emissão mas não aumenta a partícula: cada explosão leva a sua
## cópia do processo, com o tamanho (feito para a explosão fraca) crescendo junto com o raio.
func _size_burst(burst: GPUParticles3D, radius: float) -> void:
	var process: ParticleProcessMaterial = burst.process_material.duplicate()
	var growth: float = radius / WEAK_RADIUS

	process.scale_min *= growth
	process.scale_max *= growth
	burst.process_material = process


func _flash_white(tween: Tween, pace: float) -> void:
	var seconds: float = FLASH_SECONDS * pace

	(
		tween
		. tween_method(_set_instance_parameter.bind(_flash, &"strength"), 1.0, 0.0, seconds)
		. set_trans(Tween.TRANS_QUAD)
		. set_ease(Tween.EASE_OUT)
	)
	_blast_light.light_color = Color.WHITE
	_blast_light.light_energy = FLASH_LIGHT_ENERGY
	tween.tween_property(_blast_light, "light_color", FIRE_LIGHT_COLOR, seconds)
	tween.tween_property(_blast_light, "light_energy", FIRE_LIGHT_ENERGY, seconds)
	tween.tween_property(_blast_light, "light_energy", 0.0, FIREBALL_SECONDS * pace).set_delay(
		seconds
	)


## A bola incha depressa, sobe devagar e vai sendo roída até virar fumaça.
func _swell_fireball(tween: Tween, pace: float) -> void:
	var seconds: float = FIREBALL_SECONDS * pace

	_fireball.scale = Vector3.ONE * 0.15
	(
		tween
		. tween_property(_fireball, "scale", Vector3.ONE, seconds * 0.22)
		. set_trans(Tween.TRANS_CUBIC)
		. set_ease(Tween.EASE_OUT)
	)
	tween.tween_property(_fireball, "scale", Vector3.ONE * 1.25, seconds * 0.78).set_delay(
		seconds * 0.22
	)
	tween.tween_property(_fireball, "position:y", FIREBALL_RISE, seconds)
	tween.tween_method(_set_instance_parameter.bind(_fireball, &"life"), 0.0, 1.0, seconds)
	tween.tween_callback(_fireball.hide).set_delay(seconds)


func _spread_shockwave(tween: Tween, pace: float) -> void:
	var seconds: float = SHOCKWAVE_SECONDS * pace

	_shockwave.scale = Vector3.ONE * 0.3
	(
		tween
		. tween_property(_shockwave, "scale", Vector3.ONE * SHOCKWAVE_REACH, seconds)
		. set_trans(Tween.TRANS_QUAD)
		. set_ease(Tween.EASE_OUT)
	)
	tween.tween_method(_set_instance_parameter.bind(_shockwave, &"fade"), 1.0, 0.0, seconds)


func _set_charge_fade(fade: float) -> void:
	_rune_ground.set_instance_shader_parameter(&"fade", fade)
	_rune_middle.set_instance_shader_parameter(&"fade", fade)
	_rune_top.set_instance_shader_parameter(&"fade", fade)
	_charge_glow.light_energy = minf(_charge_glow.light_energy, CHARGE_GLOW_ENERGY * fade)


func _set_instance_parameter(
	value: float, instance: GeometryInstance3D, parameter: StringName
) -> void:
	instance.set_instance_shader_parameter(parameter, value)
