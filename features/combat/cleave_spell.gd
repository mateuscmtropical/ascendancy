class_name CleaveSpell
extends Node3D
## Magia de corte em linha do jogador. Segurar `cast_cleave` carrega: o zunido afina e sobe.
## Soltar corta: uma lâmina de ar sai do corpo e corre reta para a frente na altura do peito,
## partindo o que cruzar (paredes, encostas fatiadas). O golpe chega em trechos, junto com a
## lâmina. Energia, alcance, volume e grave crescem com a carga.

signal cut(impact: Impact)

const CAST_ACTION: StringName = &"cast_cleave"
const MIN_ENERGY: float = 300.0
const MAX_ENERGY: float = 3000.0
const FULL_CHARGE_SECONDS: float = 1.5
## Soltar antes disso apaga a magia sem cortar.
const MIN_CHARGE_SECONDS: float = 0.2
## Altura do corte acima dos pés.
const CUT_HEIGHT: float = 1.4
## A lâmina é fina: só o que ela cruza recebe o golpe.
const CUT_RADIUS: float = 0.7
const BASE_LENGTH: float = 12.0
const LENGTH_PER_ROOT_ENERGY: float = 0.25
## A lâmina sai um pouco à frente do corpo, para não cortar o próprio jogador.
const START_AHEAD: float = 0.8
## Em quantos trechos o golpe chega, cada um quando a lâmina (CleaveEffect.SLASH_SPEED) passa.
const SEGMENTS: int = 5
const CHARGE_QUIET_DB: float = -16.0
const CHARGE_LOUD_DB: float = -2.0
const SLASH_SOUND: AudioStream = preload("res://art/audio/cleave_slash.tres")
const CHARGE_SOUND: AudioStream = preload("res://art/audio/cleave_charge.wav")
const EFFECT_SCENE: PackedScene = preload("res://features/destruction/cleave_effect.tscn")

## De onde sai o "para frente" do corte (o modelo do personagem).
@export var aim_from: Node3D

var is_charging: bool = false
var charge_seconds: float = 0.0

var _charge_player: AudioStreamPlayer3D = AudioStreamPlayer3D.new()


func _ready() -> void:
	_charge_player.stream = CHARGE_SOUND
	_charge_player.bus = &"Effects"
	_charge_player.unit_size = 8.0
	add_child(_charge_player)


func _physics_process(delta: float) -> void:
	if is_charging:
		charge_seconds += delta
		_charge_player.volume_db = lerpf(CHARGE_QUIET_DB, CHARGE_LOUD_DB, charge_ratio())


## Energia do corte depois de carregar seconds (cresce até a carga cheia).
static func energy_for(seconds: float) -> float:
	var ratio: float = clampf(seconds / FULL_CHARGE_SECONDS, 0.0, 1.0)

	return lerpf(MIN_ENERGY, MAX_ENERGY, ratio * ratio)


## Alcance do corte: mais energia, mais longe a lâmina vai.
static func length_for(energy: float) -> float:
	return BASE_LENGTH + sqrt(energy) * LENGTH_PER_ROOT_ENERGY


func charge_ratio() -> float:
	return clampf(charge_seconds / FULL_CHARGE_SECONDS, 0.0, 1.0)


func begin_charge() -> void:
	if is_charging:
		return

	is_charging = true
	charge_seconds = 0.0
	_charge_player.volume_db = CHARGE_QUIET_DB
	_charge_player.play()


## Solta a carga: curta demais apaga; senão a lâmina sai e o golpe acompanha.
func release() -> void:
	var energy: float = energy_for(charge_seconds)

	if not is_charging:
		return

	is_charging = false
	_charge_player.stop()

	if charge_seconds < MIN_CHARGE_SECONDS:
		return

	_slash(energy)


## Começo da linha do corte e direção dela (reta, rente ao chão, para onde o corpo olha).
func cut_line() -> Array[Vector3]:
	var forward: Vector3 = aim_from.global_basis.z
	var flat: Vector3 = Vector3(forward.x, 0.0, forward.z).normalized()
	var start: Vector3 = global_position + Vector3.UP * CUT_HEIGHT + flat * START_AHEAD

	return [start, flat]


func _slash(energy: float) -> void:
	var line: Array[Vector3] = cut_line()
	var start: Vector3 = line[0]
	var direction: Vector3 = line[1]
	var length: float = length_for(energy)
	var segment_length: float = length / SEGMENTS
	var segment_seconds: float = segment_length / CleaveEffect.SLASH_SPEED
	var effect: CleaveEffect = EFFECT_SCENE.instantiate()

	get_tree().root.add_child(effect)
	effect.play(start, direction, length, energy)
	Destruction.play_sound_at(SLASH_SOUND, global_position, energy, self)

	for segment in SEGMENTS:
		var impact: Impact = Impact.new(
			start + direction * segment_length * segment,
			direction,
			CUT_RADIUS,
			energy,
			segment_length
		)

		await get_tree().create_timer(segment_seconds, false, true).timeout
		Destruction.strike(impact, self)
		cut.emit(impact)
