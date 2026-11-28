class_name PlayerController
extends CharacterBody3D
## Personagem do jogador em terceira pessoa: anda relativo à câmera, corpo gira para a direção.
## Soco e chute seguem a sequência de UnarmedFighter sem parar o passo: andando, o soco sai só no
## tronco e o chute é voador; parado, o golpe toma o corpo todo e depois fica a guarda por um tempo.
## A passada acompanha a velocidade real e o corpo ganha peso por cima da animação (BodySway).
## Em build de debug, dois toques no pulo ligam o voo livre (atravessa paredes).

enum Stance { IDLE, WALK, RUN, SPRINT, AIRBORNE, HOVER, FLY, GUARD, ATTACK }

const SPEED_BY_STANCE: Dictionary[Stance, float] = {
	Stance.IDLE: 0.0,
	Stance.WALK: 1.6,
	Stance.RUN: 5.2,
	Stance.SPRINT: 8.2,
	Stance.HOVER: 0.0,
	Stance.FLY: 16.0,
	Stance.GUARD: 0.0,
	Stance.ATTACK: 0.0,
}
const ANIMATION_BY_STANCE: Dictionary[Stance, StringName] = {
	Stance.IDLE: &"ual1/Idle",
	Stance.WALK: &"ual1/Walk",
	Stance.RUN: &"combat/Run",
	Stance.SPRINT: &"ual1/Sprint",
	Stance.AIRBORNE: &"ual1/Jump",
	Stance.HOVER: &"ual1/Swim_Idle",
	Stance.FLY: &"ual1/Swim_Fwd",
	Stance.GUARD: &"combat/Fight_Idle",
}
## Ritmo do ciclo na velocidade cheia da postura, para o pé de apoio não escorregar: velocidade
## do corpo dividida pela do pé no clipe (medida: 1,03 m/s no passo, 4,19 na corrida, 9,58 no
## sprint).
const ANIMATION_SPEED_BY_STANCE: Dictionary[Stance, float] = {
	Stance.WALK: 1.55,
	Stance.RUN: 1.24,
	Stance.SPRINT: 0.86,
}
## Arrancando e freando, o ciclo segue a velocidade real dentro desta faixa do ritmo cheio.
const MIN_STRIDE_PACE: float = 0.6
const MAX_STRIDE_PACE: float = 1.15
const JUMP_START_ANIMATION: StringName = &"ual1/Jump_Start"
const JUMP_LAND_ANIMATION: StringName = &"ual1/Jump_Land"
const SWING_SOUND_BY_ATTACK: Dictionary[UnarmedFighter.Attack, AudioStream] = {
	UnarmedFighter.Attack.PUNCH: preload("res://art/audio/swing_punch.tres"),
	UnarmedFighter.Attack.KICK: preload("res://art/audio/swing_kick.tres"),
}
const ATTACK_BY_ACTION: Dictionary[StringName, UnarmedFighter.Attack] = {
	&"attack_punch": UnarmedFighter.Attack.PUNCH,
	&"attack_kick": UnarmedFighter.Attack.KICK,
}
const FACE_BY_STANCE: Dictionary[Stance, FaceAnimator.Mood] = {
	Stance.GUARD: FaceAnimator.Mood.FOCUSED,
	Stance.ATTACK: FaceAnimator.Mood.FOCUSED,
}
## Golpe entra seco: mistura curta com a pose anterior, senão o braço sai mole.
const ATTACK_BLEND_SECONDS: float = 0.08
## Saindo do descanso o corpo ainda tem de armar a guarda: mistura mais longa para não estalar.
const FIRST_ATTACK_BLEND_SECONDS: float = 0.16
## O esforço aparece no rosto no instante do acerto e some logo.
const STRIKE_FACE_SECONDS: float = 0.22
const GROUND_ACCELERATION: float = 22.0
const AIR_ACCELERATION: float = 6.0
const FLY_ACCELERATION: float = 40.0
const FLY_BOOST: float = 2.5
const TURN_SPEED: float = 12.0
## Pulo curto e firme: ~1,1 m de altura, ~0,6 s no ar; cai mais rápido do que sobe.
const JUMP_VELOCITY: float = 7.0
const RISE_GRAVITY: float = 22.0
const FALL_GRAVITY: float = 30.0
const DOUBLE_TAP_SECONDS: float = 0.3
## Câmera mais perto que isso do pivô esconde o corpo.
const HIDE_MODEL_DISTANCE: float = 0.7
## Antecipação do teste do degrau, para o corpo encostar na borda já levantando.
const STEP_PROBE_SECONDS: float = 0.08
## Fora do chão por menos que isso (subindo degrau ou meio-fio) ainda conta como no chão: o golpe
## não é cortado nem o corpo troca para a pose de queda.
const OFF_FLOOR_GRACE_SECONDS: float = 0.12

@export var is_input_enabled: bool = true

var is_flying: bool = false

var _stance: Stance = Stance.IDLE
## Um golpe acabou de começar e o corpo ainda não entrou no clipe dele.
var _is_blow_fresh: bool = false
var _sway: BodySway = BodySway.new()
var _takeoff_speed: float = 0.0
var _seconds_off_floor: float = 0.0
var _last_jump_press_seconds: float = -1.0
var _ground_collision_mask: int
var _rider: MountRider

@onready var _model: CharacterModel = $CharacterModel
@onready var _fighter: UnarmedFighter = $UnarmedFighter
@onready var _camera_yaw: PlayerCamera = $CameraYaw
@onready var _avoidance_obstacle: NavigationObstacle3D = $AvoidanceObstacle
@onready var _mount_collision: CollisionShape3D = $MountCollision
@onready var _footsteps: FootstepPlayer = $Footsteps
@onready var _swings: AudioStreamPlayer3D = $Swings


func _ready() -> void:
	_ground_collision_mask = collision_mask
	_camera_yaw.ignore_body(get_rid())
	_rider = MountRider.new(self, _model, _camera_yaw, _avoidance_obstacle)
	_fighter.move_started.connect(_on_move_started)
	_fighter.strike_reached.connect(_on_strike_reached)
	_fighter.swing_started.connect(_on_swing_started)
	_fighter.move_finished.connect(_model.stop_upper_body)
	_footsteps.follows_stride = true


func _unhandled_input(event: InputEvent) -> void:
	var is_mouse_captured: bool = Input.mouse_mode == Input.MOUSE_MODE_CAPTURED

	if not is_input_enabled:
		return

	if event is InputEventMouseButton and event.pressed and not is_mouse_captured:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

		return

	if event.is_action_pressed(&"jump") and not event.is_echo():
		_detect_double_jump_tap()

	if event.is_action_pressed(&"summon_mount") and not is_riding():
		_summon_mount()

	_request_attack_from(event)

	if event is InputEventMouseMotion and is_mouse_captured:
		_camera_yaw.rotate_by_mouse(event.relative)


func _process(_delta: float) -> void:
	# Câmera colada no pivô (parede atrás, olhar para cima): o corpo só taparia a tela por dentro.
	_model.visible = _camera_yaw.distance_to_pivot() > HIDE_MODEL_DISTANCE

	if is_riding():
		_rider.seat_rider()


func _physics_process(delta: float) -> void:
	var input_vector: Vector2 = _read_move_input()

	_fighter.is_on_the_move = not input_vector.is_zero_approx()
	_fighter.advance(delta)

	if is_riding():
		_rider.advance(input_vector, delta)

		return

	if is_flying:
		_fly(input_vector, delta)

		return

	_walk(input_vector, delta)


func make_camera_current() -> void:
	_camera_yaw.make_current()


func set_appearance(body_scene: PackedScene, hair_color: Color) -> void:
	_model.set_body(body_scene, hair_color)


## Sobe na mula: daí em diante quem anda é o MountRider.
func ride(mount: MulaSemCabeca) -> void:
	set_flying(false)
	_stand_straight()
	_footsteps.follows_stride = false
	_mount_collision.disabled = false
	_rider.start(mount)


## Desce da mula, que fica parada onde está.
func dismount() -> void:
	if not is_riding():
		return

	_rider.stop()
	_footsteps.follows_stride = true
	_mount_collision.disabled = true
	_stance = Stance.AIRBORNE


## Chama a montaria: ela vem voando de onde estiver e pousa ao lado.
func _summon_mount() -> void:
	var mount: MulaMount = get_tree().get_first_node_in_group(MulaMount.GROUP) as MulaMount

	if mount != null:
		mount.summon_to(self)


func is_riding() -> bool:
	return _rider.mount != null


func set_flying(should_fly: bool) -> void:
	is_flying = should_fly
	_fighter.cancel()
	collision_mask = 0 if should_fly else _ground_collision_mask
	_camera_yaw.set_collides(not should_fly)
	velocity = Vector3.ZERO
	_stand_straight()


func _walk(input_vector: Vector2, delta: float) -> void:
	var move_direction: Vector3 = (
		_camera_yaw.global_basis * Vector3(input_vector.x, 0.0, input_vector.y)
	)
	var travel_stance: Stance = _choose_travel_stance(input_vector)
	var stance: Stance = _choose_ground_stance(travel_stance)
	var is_grounded: bool = is_on_floor()
	var ground_speed: float = 0.0 if _fighter.holds_feet() else SPEED_BY_STANCE[travel_stance]
	var speed: float = ground_speed if is_grounded else _takeoff_speed
	var target_velocity: Vector3 = move_direction.normalized() * speed
	var acceleration: float = GROUND_ACCELERATION if is_grounded else AIR_ACCELERATION
	var gravity: float = RISE_GRAVITY if velocity.y > 0.0 else FALL_GRAVITY
	var start_velocity: Vector3 = velocity

	velocity.x = move_toward(velocity.x, target_velocity.x, acceleration * delta)
	velocity.z = move_toward(velocity.z, target_velocity.z, acceleration * delta)
	velocity.y -= gravity * delta

	if is_grounded:
		_takeoff_speed = maxf(SPEED_BY_STANCE[travel_stance], SPEED_BY_STANCE[Stance.RUN])

	if is_grounded and is_input_enabled and Input.is_action_just_pressed(&"jump"):
		velocity.y = JUMP_VELOCITY
		stance = Stance.AIRBORNE
		_sway.push_off()

	if stance == Stance.AIRBORNE:
		_fighter.cancel()

	if is_grounded:
		climb_step(Vector3(velocity.x, 0.0, velocity.z) * STEP_PROBE_SECONDS)

	move_and_slide()

	_seconds_off_floor = 0.0 if is_on_floor() else _seconds_off_floor + delta
	# NPCs desviam do jogador prevendo para onde ele vai.
	_avoidance_obstacle.velocity = Vector3(velocity.x, 0.0, velocity.z)
	_turn_model_toward(move_direction, delta)
	_apply_stance(stance)
	_pace_stride(stance)
	_sway_body(start_velocity, is_grounded, delta)


## Sobe o corpo até o topo do degrau à frente, se o deslocamento horizontal motion bate numa
## parede baixa (até STEP_HEIGHT) com chão firme em cima. Devolve se subiu.
func climb_step(motion: Vector3, step_height: float = StepClimber.STEP_HEIGHT) -> bool:
	var step_top: float = StepClimber.step_top_ahead(self, motion, step_height)

	if step_top <= safe_margin:
		return false

	global_position.y += step_top

	return true


func _fly(input_vector: Vector2, delta: float) -> void:
	var look_direction: Vector3 = (
		_camera_yaw.get_look_basis() * Vector3(input_vector.x, 0.0, input_vector.y)
	)
	var climb: float = read_climb_input()
	var stance: Stance = Stance.FLY if input_vector.length() > 0.0 or climb != 0.0 else Stance.HOVER
	var boost: float = FLY_BOOST if Input.is_action_pressed(&"sprint") else 1.0
	var target_velocity: Vector3 = (
		(look_direction + Vector3.UP * climb).limit_length(1.0)
		* SPEED_BY_STANCE[Stance.FLY]
		* boost
	)

	velocity = velocity.move_toward(target_velocity, FLY_ACCELERATION * boost * delta)
	move_and_slide()

	_avoidance_obstacle.velocity = Vector3.ZERO
	_turn_model_toward(Vector3(look_direction.x, 0.0, look_direction.z), delta)
	_apply_stance(stance)


func _read_move_input() -> Vector2:
	if not is_input_enabled:
		return Vector2.ZERO

	return Input.get_vector(&"move_left", &"move_right", &"move_forward", &"move_back")


## Subir (pulo) menos descer (Ctrl), para o voo.
func read_climb_input() -> float:
	var climb_up: float = 1.0 if Input.is_action_pressed(&"jump") else 0.0
	var climb_down: float = 1.0 if Input.is_action_pressed(&"walk") else 0.0

	if not is_input_enabled:
		return 0.0

	return climb_up - climb_down


func _detect_double_jump_tap() -> void:
	var now_seconds: float = Time.get_ticks_msec() / 1000.0
	var is_double_tap: bool = now_seconds - _last_jump_press_seconds < DOUBLE_TAP_SECONDS

	_last_jump_press_seconds = now_seconds

	if not OS.is_debug_build() or not is_double_tap or is_riding():
		return

	_last_jump_press_seconds = -1.0
	set_flying(not is_flying)


func _request_attack_from(event: InputEvent) -> void:
	var can_attack: bool = is_on_floor() and not is_flying and not is_riding()

	if not can_attack or event.is_echo():
		return

	for action in ATTACK_BY_ACTION:
		if event.is_action_pressed(action):
			_fighter.request_attack(ATTACK_BY_ACTION[action])


## O corpo entra no clipe do golpe em _apply_stance; o soco já arma o tronco aqui, por cima do
## que as pernas estiverem fazendo.
func _on_move_started(move: UnarmedFighter.Move) -> void:
	var animation: StringName = _fighter.animation_of(move)
	var animation_speed: float = _fighter.animation_speed_of(move)

	_is_blow_fresh = true

	if _fighter.is_committed():
		_model.stop_upper_body()

		return

	_model.play_upper_body(animation, animation_speed, ATTACK_BLEND_SECONDS)


func _on_swing_started(attack: UnarmedFighter.Attack) -> void:
	var sound: AudioStream = SWING_SOUND_BY_ATTACK[attack]

	# Trocar o stream corta o som que está tocando: só troca quando muda.
	if _swings.stream != sound:
		_swings.stream = sound

	_swings.play()


## No instante do acerto o golpe chega no que estiver à frente: madeira quebra, pedra só soa.
func _on_strike_reached(move: UnarmedFighter.Move) -> void:
	var impact: Impact = _fighter.impact_of(move, global_position, _model.global_basis.z)

	_model.show_expression(FaceAnimator.Mood.EFFORT, STRIKE_FACE_SECONDS)
	Destruction.strike(impact, self)


## O que o corpo mostra: o golpe só toma o corpo todo com o jogador parado ou num chute.
func _choose_ground_stance(travel_stance: Stance) -> Stance:
	var is_still: bool = travel_stance == Stance.IDLE

	if not is_on_floor() and _seconds_off_floor >= OFF_FLOOR_GRACE_SECONDS:
		return Stance.AIRBORNE

	if _fighter.is_attacking() and (is_still or _fighter.is_committed()):
		return Stance.ATTACK

	if is_still and _fighter.is_on_guard():
		return Stance.GUARD

	return travel_stance


## O passo que as teclas pedem, sem olhar para golpe nem para o chão.
func _choose_travel_stance(input_vector: Vector2) -> Stance:
	if input_vector.is_zero_approx():
		return Stance.IDLE

	if Input.is_action_pressed(&"sprint"):
		return Stance.SPRINT

	if Input.is_action_pressed(&"walk"):
		return Stance.WALK

	return Stance.RUN


func _apply_stance(stance: Stance) -> void:
	var was_airborne: bool = _stance == Stance.AIRBORNE
	var was_guard_up: bool = _stance == Stance.GUARD or _stance == Stance.ATTACK
	var is_new_blow: bool = stance == Stance.ATTACK and _is_blow_fresh

	_is_blow_fresh = false

	if stance == _stance and not is_new_blow:
		return

	if stance != _stance:
		_model.rest_expression(FACE_BY_STANCE.get(stance, FaceAnimator.Mood.NEUTRAL))

	_stance = stance

	if stance == Stance.ATTACK:
		_play_blow_on_body(was_guard_up)

		return

	if stance == Stance.AIRBORNE and velocity.y > 0.0:
		_model.play_animation_then(JUMP_START_ANIMATION, ANIMATION_BY_STANCE[stance])

		return

	if was_airborne and stance == Stance.IDLE:
		_model.play_animation_then(JUMP_LAND_ANIMATION, ANIMATION_BY_STANCE[stance])

		return

	_model.play_animation(ANIMATION_BY_STANCE[stance])


## Põe o corpo todo no clipe do golpe, do ponto em que o golpe já está (o jogador pode ter parado
## no meio de um soco que vinha só no tronco).
func _play_blow_on_body(was_guard_up: bool) -> void:
	var move: UnarmedFighter.Move = _fighter.current_move()
	var animation: StringName = _fighter.animation_of(move)
	var animation_speed: float = _fighter.animation_speed_of(move)
	var blend_seconds: float = ATTACK_BLEND_SECONDS if was_guard_up else FIRST_ATTACK_BLEND_SECONDS

	_model.play_animation(animation, animation_speed, blend_seconds, _fighter.move_seconds())


## A passada do ciclo de andar segue a velocidade do corpo (sem pé patinando na arrancada) e
## avisa o som dos passos de onde o ciclo está, para o passo soar quando o pé pisa.
func _pace_stride(stance: Stance) -> void:
	var full_pace: float = ANIMATION_SPEED_BY_STANCE.get(stance, 0.0)
	var ground_speed: float = Vector2(velocity.x, velocity.z).length()
	var speed_share: float = ground_speed / maxf(SPEED_BY_STANCE.get(stance, 0.0), 0.01)

	if full_pace == 0.0:
		_footsteps.stride_phase = FootstepPlayer.NO_STRIDE

		return

	_model.pace_animation(full_pace * clampf(speed_share, MIN_STRIDE_PACE, MAX_STRIDE_PACE))
	_footsteps.stride_phase = _model.animation_phase()


## Inclina o corpo para onde ele acelerou neste passo e amassa no pouso.
func _sway_body(start_velocity: Vector3, was_grounded: bool, delta: float) -> void:
	var gained: Vector3 = (velocity - start_velocity) / (GROUND_ACCELERATION * delta)
	var local_gain: Vector3 = _model.global_basis.inverse() * Vector3(gained.x, 0.0, gained.z)

	if is_on_floor() and not was_grounded:
		_sway.land(-start_velocity.y)

	_sway.advance(Vector2(local_gain.x, local_gain.z), delta)
	_model.set_sway(_sway.lean, _sway.stretch)


## Voando ou montado o corpo não leva a inclinação do passo.
func _stand_straight() -> void:
	_sway.reset()
	_model.set_sway(_sway.lean, _sway.stretch)


func _turn_model_toward(direction: Vector3, delta: float, turn_speed: float = TURN_SPEED) -> void:
	var target_yaw: float

	if direction.length_squared() < 0.01:
		return

	target_yaw = atan2(direction.x, direction.z)
	_model.global_rotation.y = lerp_angle(_model.global_rotation.y, target_yaw, turn_speed * delta)
