class_name CleaveEffect
extends Node3D
## Visual da magia de corte em linha: clarão curto na saída, uma lâmina em meia-lua que voa de
## origin até origin + direction * length, o risco de luz que ela deixa e que some devagar, e
## poeira ao longo do caminho. Largura, brilho e duração crescem com a energia (a mesma escala
## logarítmica 300..3000 de ExplosionEffect). Só visual: a quebra é o Impact de quem chama.
## O nó precisa estar na árvore antes de play e se apaga sozinho no fim.

## Metros por segundo da lâmina: 25 m em 0,25 s.
const SLASH_SPEED: float = 100.0
## Largura da lâmina, em metros.
const WEAK_WIDTH: float = 4.0
const STRONG_WIDTH: float = 8.0
const WEAK_GLOW: float = 0.75
const STRONG_GLOW: float = 1.3
## Espessura do risco que fica e do fio da lâmina, em metros (halo incluído).
const WEAK_LINE_THICKNESS: float = 0.16
const STRONG_LINE_THICKNESS: float = 0.34
const EDGE_THICKNESS_SHARE: float = 3.0
## Quanto o risco demora para sumir depois que a lâmina passou.
const WEAK_LINGER_SECONDS: float = 1.2
const STRONG_LINGER_SECONDS: float = 1.8
## Parte final do voo em que a lâmina se desfaz.
const SLASH_FADE_SHARE: float = 0.3
const FLASH_SECONDS: float = 0.16
const FLASH_LIGHT_ENERGY: float = 8.0
const WEAK_DUST_RATIO: float = 0.5

var _has_played: bool = false

@onready var _flash: MeshInstance3D = $Flash
@onready var _light: OmniLight3D = $Light
@onready var _cut_line: MeshInstance3D = $CutLine
@onready var _slash: Node3D = $Slash
@onready var _crescent: MeshInstance3D = $Slash/Crescent
@onready var _edge: MeshInstance3D = $Slash/Edge
@onready var _dust: GPUParticles3D = $Slash/Dust


## Solta o corte de origin ao longo de direction (deitada, não vertical) por length metros.
func play(origin: Vector3, direction: Vector3, length: float, energy: float) -> void:
	var strength: float = ExplosionEffect.strength_of(energy)
	var travel_seconds: float = length / SLASH_SPEED
	var linger_seconds: float = lerpf(WEAK_LINGER_SECONDS, STRONG_LINGER_SECONDS, strength)
	var width: float = lerpf(WEAK_WIDTH, STRONG_WIDTH, strength)
	var glow: float = lerpf(WEAK_GLOW, STRONG_GLOW, strength)
	var thickness: float = lerpf(WEAK_LINE_THICKNESS, STRONG_LINE_THICKNESS, strength)
	var tween: Tween

	if _has_played:
		return

	_has_played = true
	look_at_from_position(origin, origin + direction)
	visible = true

	_slash.scale = Vector3(width, 1.0, width)
	_cut_line.scale.x = length
	_cut_line.position.z = -length / 2.0
	_cut_line.set_instance_shader_parameter(&"thickness", thickness)
	_edge.set_instance_shader_parameter(&"thickness", thickness * EDGE_THICKNESS_SHARE)
	_edge.set_instance_shader_parameter(&"reveal", 1.0)
	_set_glow(glow)
	_dust.amount_ratio = lerpf(WEAK_DUST_RATIO, 1.0, strength)
	_dust.emitting = true
	_light.light_energy = FLASH_LIGHT_ENERGY * glow

	tween = create_tween()
	tween.set_parallel(true)
	tween.tween_method(_set_parameter.bind(_flash, &"strength"), 1.0, 0.0, FLASH_SECONDS)
	tween.tween_property(_light, "light_energy", 0.0, FLASH_SECONDS * 2.0)
	tween.tween_property(_slash, "position:z", -length, travel_seconds)
	tween.tween_method(_set_parameter.bind(_cut_line, &"reveal"), 0.0, 1.0, travel_seconds)
	_set_parameter(1.0, _cut_line, &"fade")
	_set_slash_fade(1.0)
	tween.tween_method(_set_slash_fade, 1.0, 0.0, travel_seconds * SLASH_FADE_SHARE).set_delay(
		travel_seconds * (1.0 - SLASH_FADE_SHARE)
	)
	tween.tween_callback(_end_slash).set_delay(travel_seconds)
	(
		tween
		. tween_method(_set_parameter.bind(_cut_line, &"fade"), 1.0, 0.0, linger_seconds)
		. set_delay(travel_seconds)
		. set_trans(Tween.TRANS_QUAD)
		. set_ease(Tween.EASE_IN)
	)
	tween.chain().tween_callback(queue_free)


## A lâmina chegou ao fim: some, e a poeira para de nascer (a que já saiu termina sozinha).
func _end_slash() -> void:
	_crescent.visible = false
	_edge.visible = false
	_dust.emitting = false


func _set_glow(glow: float) -> void:
	_cut_line.set_instance_shader_parameter(&"glow", glow)
	_crescent.set_instance_shader_parameter(&"glow", glow)
	_edge.set_instance_shader_parameter(&"glow", glow)


func _set_slash_fade(fade: float) -> void:
	_crescent.set_instance_shader_parameter(&"fade", fade)
	_edge.set_instance_shader_parameter(&"fade", fade)


func _set_parameter(value: float, instance: GeometryInstance3D, parameter: StringName) -> void:
	instance.set_instance_shader_parameter(parameter, value)
