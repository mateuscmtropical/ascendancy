class_name FarmAnimal
extends AnimatableBody3D
## Bicho da fazenda (vaca, porco): pasta parado e de vez em quando caminha devagar até outro
## ponto do cercado. Sem navmesh: anda em linha reta dentro do retângulo `pen` (x, z), que fica
## afastado da cerca. O sorteio usa a semente própria, então cada bicho repete o mesmo passeio.
## Antes de sair vira no lugar para o alvo; acelera e freia devagar, e o passo da animação acompanha
## a velocidade (sem patinar). Modelo sem animação de andar fica pastando no lugar. Troncos de
## árvore no cercado (`obstacles`) ficam fora do caminho: o bicho só escolhe alvo com linha livre.

enum Mood { GRAZING, TURNING, WALKING }

const IDLE_ANIMATION: StringName = &"Idle"
const WALK_ANIMATION: StringName = &"Walk"
const SLOW_WALK_ANIMATION: StringName = &"WalkSlow"
const ANIMATION_BLEND_SECONDS: float = 0.35
const TURN_SPEED: float = 1.6
const WALKING_TURN_SPEED: float = 2.0
## Vira no lugar até o alvo ficar a menos disso da frente (radianos), aí começa a andar.
const START_WALK_ANGLE: float = 0.35
const ACCELERATION: float = 0.8
const SLOWDOWN_DISTANCE: float = 1.5
const MIN_SPEED_SHARE: float = 0.3
const ARRIVAL_DISTANCE: float = 0.15
const GRAZE_SECONDS: Vector2 = Vector2(4.0, 11.0)
## Passo mínimo até o próximo ponto: menos que isso o bicho só se vira no lugar.
const MIN_WANDER_DISTANCE: float = 2.0
const WANDER_ATTEMPTS: int = 8
const MIN_ANIMATION_SPEED: float = 0.4

@export var model_scene: PackedScene
@export var pen: Rect2 = Rect2(0.0, 0.0, 4.0, 4.0)
@export var walk_speed: float = 0.5
## Velocidade (m/s) em que a animação de andar tocada em 1x não patina.
@export var stride_speed: float = 0.6
@export var wander_seed: int = 1
## Caixa de colisão (largura, altura, comprimento) que o jogador não atravessa.
@export var body_size: Vector3 = Vector3(0.8, 1.3, 2.0)
## Troncos no cercado: (x, z, raio) de cada um.
@export var obstacles: PackedVector3Array = PackedVector3Array()

var _generator: RandomNumberGenerator = RandomNumberGenerator.new()
var _mood: Mood = Mood.GRAZING
var _graze_left: float = 0.0
var _target: Vector2 = Vector2.ZERO
var _speed: float = 0.0
var _animation_player: AnimationPlayer
var _walk_animation: StringName = WALK_ANIMATION
var _can_walk: bool = true
var _mood_steps: Dictionary[Mood, Callable] = {
	Mood.GRAZING: _graze,
	Mood.TURNING: _turn_to_target,
	Mood.WALKING: _walk_to_target,
}


func _ready() -> void:
	var model: Node3D = model_scene.instantiate() if model_scene else null

	_generator.seed = wander_seed
	_graze_left = _generator.randf_range(0.0, GRAZE_SECONDS.y)
	_add_body_collision()

	if model == null:
		return

	add_child(model)
	_animation_player = model.find_child("AnimationPlayer", true, false) as AnimationPlayer
	_pick_walk_animation()
	_loop_animations()
	_play(IDLE_ANIMATION)


func _physics_process(delta: float) -> void:
	var mood_step: Callable = _mood_steps[_mood]

	mood_step.call(delta)


## Próximo ponto do passeio: dentro do cercado, longe o bastante de onde o bicho está e com a linha
## reta até ele livre dos obstáculos (folga `clearance` além do raio). Sem nenhum, fica onde está.
static func pick_wander_target(
	area: Rect2,
	from: Vector2,
	generator: RandomNumberGenerator,
	blockers: PackedVector3Array = PackedVector3Array(),
	clearance: float = 0.0
) -> Vector2:
	var candidate: Vector2 = from

	for attempt in WANDER_ATTEMPTS:
		candidate = Vector2(
			generator.randf_range(area.position.x, area.end.x),
			generator.randf_range(area.position.y, area.end.y)
		)

		if candidate.distance_to(from) < MIN_WANDER_DISTANCE:
			continue

		if is_path_clear(from, candidate, blockers, clearance):
			return candidate

	return from


## Verdadeiro se o segmento `from`-`target` passa a mais de raio + `clearance` de cada obstáculo.
static func is_path_clear(
	from: Vector2, target: Vector2, blockers: PackedVector3Array, clearance: float
) -> bool:
	for blocker in blockers:
		var center: Vector2 = Vector2(blocker.x, blocker.y)
		var closest: Vector2 = Geometry2D.get_closest_point_to_segment(center, from, target)

		if closest.distance_to(center) < blocker.z + clearance:
			return false

	return true


## Um passo em linha reta, sem passar do alvo.
static func step_toward(from: Vector2, target: Vector2, distance: float) -> Vector2:
	return from.move_toward(target, distance)


## Velocidade desejada a `distance` do alvo: cheia longe, diminuindo na chegada.
static func cruise_speed(top_speed: float, distance: float) -> float:
	var share: float = clampf(distance / SLOWDOWN_DISTANCE, MIN_SPEED_SHARE, 1.0)

	return top_speed * share


## Ângulo (rotation.y) de quem olha de `from` para `target` no chão.
static func heading_angle(from: Vector2, target: Vector2) -> float:
	var heading: Vector2 = target - from

	return atan2(heading.x, heading.y)


func _graze(delta: float) -> void:
	var ground_position: Vector2 = Vector2(global_position.x, global_position.z)

	_graze_left -= delta

	if _graze_left > 0.0:
		return

	if not _can_walk:
		_start_grazing()

		return

	_target = pick_wander_target(pen, ground_position, _generator, obstacles, body_size.z / 2.0)

	if _target == ground_position:
		_start_grazing()

		return

	_mood = Mood.TURNING
	_play(_walk_animation, MIN_ANIMATION_SPEED)


func _turn_to_target(delta: float) -> void:
	var ground_position: Vector2 = Vector2(global_position.x, global_position.z)
	var wanted: float = heading_angle(ground_position, _target)

	rotation.y = rotate_toward(rotation.y, wanted, TURN_SPEED * delta)

	if absf(angle_difference(rotation.y, wanted)) > START_WALK_ANGLE:
		return

	_mood = Mood.WALKING


func _walk_to_target(delta: float) -> void:
	var ground_position: Vector2 = Vector2(global_position.x, global_position.z)
	var distance_left: float = ground_position.distance_to(_target)
	var wanted_speed: float = cruise_speed(walk_speed, distance_left)
	var next_position: Vector2

	if distance_left <= ARRIVAL_DISTANCE:
		_start_grazing()

		return

	_speed = move_toward(_speed, wanted_speed, ACCELERATION * delta)
	next_position = step_toward(ground_position, _target, _speed * delta)
	global_position = Vector3(next_position.x, global_position.y, next_position.y)
	rotation.y = lerp_angle(
		rotation.y, heading_angle(ground_position, _target), WALKING_TURN_SPEED * delta
	)
	_match_stride()


func _start_grazing() -> void:
	_mood = Mood.GRAZING
	_speed = 0.0
	_graze_left = _generator.randf_range(GRAZE_SECONDS.x, GRAZE_SECONDS.y)
	_play(IDLE_ANIMATION)


func _add_body_collision() -> void:
	var collision: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()

	box.size = body_size
	collision.shape = box
	collision.position.y = body_size.y / 2.0
	add_child(collision)


## Passo lento quando o pacote tem; sem nenhuma animação de andar o bicho não passeia.
func _pick_walk_animation() -> void:
	var has_slow_walk: bool = (
		_animation_player != null and _animation_player.has_animation(SLOW_WALK_ANIMATION)
	)
	var has_walk: bool = (
		_animation_player != null and _animation_player.has_animation(WALK_ANIMATION)
	)

	_walk_animation = SLOW_WALK_ANIMATION if has_slow_walk else WALK_ANIMATION
	_can_walk = has_slow_walk or has_walk


## O glTF convertido não marca as animações como laço; pastar e andar repetem sem parar.
func _loop_animations() -> void:
	if _animation_player == null:
		return

	for animation_name in [IDLE_ANIMATION, WALK_ANIMATION, SLOW_WALK_ANIMATION]:
		if not _animation_player.has_animation(animation_name):
			continue

		_animation_player.get_animation(animation_name).loop_mode = Animation.LOOP_LINEAR


func _match_stride() -> void:
	if _animation_player == null:
		return

	_animation_player.speed_scale = maxf(_speed / stride_speed, MIN_ANIMATION_SPEED)


func _play(animation_name: StringName, speed_scale: float = 1.0) -> void:
	if _animation_player == null or not _animation_player.has_animation(animation_name):
		return

	_animation_player.speed_scale = speed_scale
	_animation_player.play(animation_name, ANIMATION_BLEND_SECONDS)
