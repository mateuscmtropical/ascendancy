class_name FarmAnimal
extends AnimatableBody3D
## Bicho da fazenda (vaca, porco): pasta parado e de vez em quando caminha devagar até outro
## ponto do cercado. Sem navmesh: anda em linha reta dentro do retângulo `pen` (x, z), que fica
## afastado da cerca. O sorteio usa a semente própria, então cada bicho repete o mesmo passeio.

enum Mood { GRAZING, WALKING }

const IDLE_ANIMATION: StringName = &"Idle"
const WALK_ANIMATION: StringName = &"Walk"
const TURN_SPEED: float = 2.5
const ARRIVAL_DISTANCE: float = 0.15
const GRAZE_SECONDS: Vector2 = Vector2(4.0, 11.0)
## Passo mínimo até o próximo ponto: menos que isso o bicho só se vira no lugar.
const MIN_WANDER_DISTANCE: float = 2.0
const WANDER_ATTEMPTS: int = 8

@export var model_scene: PackedScene
@export var pen: Rect2 = Rect2(0.0, 0.0, 4.0, 4.0)
@export var walk_speed: float = 0.5
@export var wander_seed: int = 1
## Caixa de colisão (largura, altura, comprimento) que o jogador não atravessa.
@export var body_size: Vector3 = Vector3(0.8, 1.3, 2.0)

var _generator: RandomNumberGenerator = RandomNumberGenerator.new()
var _mood: Mood = Mood.GRAZING
var _graze_left: float = 0.0
var _target: Vector2 = Vector2.ZERO
var _animation_player: AnimationPlayer
var _mood_steps: Dictionary[Mood, Callable] = {
	Mood.GRAZING: _graze,
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
	_loop_animations()
	_play(IDLE_ANIMATION)


func _physics_process(delta: float) -> void:
	var mood_step: Callable = _mood_steps[_mood]

	mood_step.call(delta)


## Próximo ponto do passeio: dentro do cercado e longe o bastante de onde o bicho está.
static func pick_wander_target(
	area: Rect2, from: Vector2, generator: RandomNumberGenerator
) -> Vector2:
	var candidate: Vector2 = from

	for attempt in WANDER_ATTEMPTS:
		candidate = Vector2(
			generator.randf_range(area.position.x, area.end.x),
			generator.randf_range(area.position.y, area.end.y)
		)

		if candidate.distance_to(from) >= MIN_WANDER_DISTANCE:
			return candidate

	return candidate


## Um passo em linha reta, sem passar do alvo.
static func step_toward(from: Vector2, target: Vector2, distance: float) -> Vector2:
	return from.move_toward(target, distance)


func _graze(delta: float) -> void:
	var ground_position: Vector2 = Vector2(global_position.x, global_position.z)

	_graze_left -= delta

	if _graze_left > 0.0:
		return

	_target = pick_wander_target(pen, ground_position, _generator)
	_mood = Mood.WALKING
	_play(WALK_ANIMATION)


func _walk_to_target(delta: float) -> void:
	var ground_position: Vector2 = Vector2(global_position.x, global_position.z)
	var heading: Vector2 = _target - ground_position
	var next_position: Vector2 = step_toward(ground_position, _target, walk_speed * delta)

	if heading.length() <= ARRIVAL_DISTANCE:
		_start_grazing()

		return

	global_position = Vector3(next_position.x, global_position.y, next_position.y)
	rotation.y = lerp_angle(rotation.y, atan2(heading.x, heading.y), TURN_SPEED * delta)


func _start_grazing() -> void:
	_mood = Mood.GRAZING
	_graze_left = _generator.randf_range(GRAZE_SECONDS.x, GRAZE_SECONDS.y)
	_play(IDLE_ANIMATION)


func _add_body_collision() -> void:
	var collision: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()

	box.size = body_size
	collision.shape = box
	collision.position.y = body_size.y / 2.0
	add_child(collision)


## O glTF convertido não marca as animações como laço; pastar e andar repetem sem parar.
func _loop_animations() -> void:
	if _animation_player == null:
		return

	for animation_name in [IDLE_ANIMATION, WALK_ANIMATION]:
		if not _animation_player.has_animation(animation_name):
			continue

		_animation_player.get_animation(animation_name).loop_mode = Animation.LOOP_LINEAR


func _play(animation_name: StringName) -> void:
	if _animation_player == null or not _animation_player.has_animation(animation_name):
		return

	_animation_player.play(animation_name)
