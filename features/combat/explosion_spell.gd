class_name ExplosionSpell
extends Node3D
## Magia de explosão do jogador. Segurar `cast_explosion` carrega: o zumbido sobe e o círculo de
## runas cresce no alvo, à frente do corpo. Soltar dispara: o zumbido corta, um instante de quase
## silêncio, o estrondo grave e um Impact grande no alvo. Energia, raio, volume e grave crescem com
## a carga. O chão de cratera (grupo `blast_ground`) afunda e queima, e o fogo (grupo `fire_grid`)
## pega onde houver um.

signal blasted(impact: Impact)

const CAST_ACTION: StringName = &"cast_explosion"
const MIN_ENERGY: float = 300.0
const MAX_ENERGY: float = 3000.0
const FULL_CHARGE_SECONDS: float = 2.5
## Soltar antes disso apaga a magia sem disparar.
const MIN_CHARGE_SECONDS: float = 0.35
## O alvo fica no chão, a esta distância à frente do corpo.
const CAST_DISTANCE: float = 11.0
const AIM_PROBE_HEIGHT: float = 30.0
## O instante de quase silêncio entre soltar e o estrondo.
const HUSH_SECONDS: float = 0.28
const BASE_RADIUS: float = 1.6
const RADIUS_PER_ROOT_ENERGY: float = 0.06
## Altura do centro da explosão acima do chão.
const BLAST_HEIGHT: float = 0.6
## Cratera, queimado e fogo medidos pelo tamanho da bola de fogo (ExplosionEffect.blast_radius_of).
const CRATER_SHARE: float = 0.75
const CRATER_DEPTH_SHARE: float = 0.28
const SCORCH_SHARE: float = 1.1
const FIRE_SHARE: float = 1.25
## O zumbido da carga é escrito com 3 s; o tom sobe com o próprio som, o volume com a carga.
const CHARGE_QUIET_DB: float = -14.0
const CHARGE_LOUD_DB: float = 0.0
const BOOM_SOUND: AudioStream = preload("res://art/audio/explosion_boom.tres")
const CHARGE_SOUND: AudioStream = preload("res://art/audio/explosion_charge.wav")
const FIRE_SOUND: AudioStream = preload("res://art/audio/fire_loop.wav")
const FIRE_SOUND_UNIT_SIZE: float = 6.0
const EFFECT_SCENE: PackedScene = preload("res://features/destruction/explosion_effect.tscn")

## De onde sai o "para frente" do alvo (o modelo do personagem).
@export var aim_from: Node3D

var is_charging: bool = false
var charge_seconds: float = 0.0

var _charge_player: AudioStreamPlayer3D = AudioStreamPlayer3D.new()
var _effect: ExplosionEffect


func _ready() -> void:
	_charge_player.stream = CHARGE_SOUND
	_charge_player.bus = &"Effects"
	_charge_player.unit_size = 8.0
	add_child(_charge_player)


func _physics_process(delta: float) -> void:
	if is_charging:
		charge_seconds += delta
		_charge_player.volume_db = lerpf(CHARGE_QUIET_DB, CHARGE_LOUD_DB, charge_ratio())
		_effect.global_position = aim_point()


## Energia da magia depois de carregar seconds (cresce até a carga cheia).
static func energy_for(seconds: float) -> float:
	var ratio: float = clampf(seconds / FULL_CHARGE_SECONDS, 0.0, 1.0)

	return lerpf(MIN_ENERGY, MAX_ENERGY, ratio * ratio)


## Raio do estrago: a energia se espalha numa área, então o raio cresce com a raiz dela.
static func radius_for(energy: float) -> float:
	return BASE_RADIUS + sqrt(energy) * RADIUS_PER_ROOT_ENERGY


func charge_ratio() -> float:
	return clampf(charge_seconds / FULL_CHARGE_SECONDS, 0.0, 1.0)


func begin_charge() -> void:
	if is_charging:
		return

	is_charging = true
	charge_seconds = 0.0
	_effect = EFFECT_SCENE.instantiate()
	get_tree().root.add_child(_effect)
	_effect.global_position = aim_point()
	_effect.play_charge(FULL_CHARGE_SECONDS)
	_charge_player.volume_db = CHARGE_QUIET_DB
	_charge_player.play()


## Solta a carga: curta demais apaga; senão dispara no alvo depois do instante de silêncio.
func release() -> void:
	var target: Vector3 = aim_point()
	var energy: float = energy_for(charge_seconds)
	var effect: ExplosionEffect = _effect

	if not is_charging:
		return

	is_charging = false
	_effect = null
	_charge_player.stop()

	if charge_seconds < MIN_CHARGE_SECONDS:
		effect.queue_free()

		return

	await get_tree().create_timer(HUSH_SECONDS, false).timeout
	_blast(target, energy, effect)


## Ponto no chão à frente do corpo, onde a magia cai.
func aim_point() -> Vector3:
	var forward: Vector3 = aim_from.global_basis.z
	var flat: Vector3 = Vector3(forward.x, 0.0, forward.z).normalized()
	var spot: Vector3 = global_position + flat * CAST_DISTANCE
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		spot + Vector3.UP * AIM_PROBE_HEIGHT,
		spot + Vector3.DOWN * AIM_PROBE_HEIGHT,
		Destruction.WORLD_LAYER
	)
	var hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(query)

	return hit.get("position", spot)


func _blast(target: Vector3, energy: float, effect: ExplosionEffect) -> void:
	var radius: float = radius_for(energy)
	var fireball: float = ExplosionEffect.blast_radius_of(energy)
	var impact: Impact = Impact.new(
		target + Vector3.UP * BLAST_HEIGHT, Vector3.DOWN, radius, energy
	)

	effect.global_position = target
	effect.play_blast(energy)
	Destruction.play_sound_at(BOOM_SOUND, target, energy, self)
	Destruction.strike(impact, self)

	for ground in get_tree().get_nodes_in_group(&"blast_ground"):
		ground.dig_crater(target, fireball * CRATER_SHARE, fireball * CRATER_DEPTH_SHARE)
		ground.scorch(target, fireball * SCORCH_SHARE, 1.0)

	for fire in get_tree().get_nodes_in_group(&"fire_grid"):
		fire.ignite(target, fireball * FIRE_SHARE)
		_play_fire_sound(target, fire)

	blasted.emit(impact)


## Estalo do fogo no lugar da explosão, até a grade inteira apagar.
func _play_fire_sound(target: Vector3, fire: FireGrid) -> void:
	var player: AudioStreamPlayer3D = AudioStreamPlayer3D.new()

	player.stream = FIRE_SOUND
	player.bus = &"Effects"
	player.unit_size = FIRE_SOUND_UNIT_SIZE
	get_tree().root.add_child(player)
	player.global_position = target
	player.play()
	fire.fire_died.connect(player.queue_free, CONNECT_ONE_SHOT)
