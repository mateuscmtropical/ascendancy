class_name MountRider
extends RefCounted
## Guia a montaria (Mula sem cabeça) com o corpo do jogador: o CharacterBody3D do jogador é quem
## anda e colide; a mula vai junto e o cavaleiro senta no lombo dela. Números em RideTuning.

var mount: MulaSemCabeca
var is_flying: bool = false
var stance: PlayerController.Stance = PlayerController.Stance.IDLE

var _turbo_seconds_left: float = 0.0
var _last_tap_seconds: Dictionary[StringName, float] = {}
var _body: PlayerController
var _model: CharacterModel
var _camera: PlayerCamera
var _obstacle: NavigationObstacle3D


func _init(
	body: PlayerController,
	model: CharacterModel,
	camera: PlayerCamera,
	obstacle: NavigationObstacle3D
) -> void:
	_body = body
	_model = model
	_camera = camera
	_obstacle = obstacle


## Sobe na mula: o corpo vai para o lugar dela e daí em diante guia a mula (ver advance).
func start(new_mount: MulaSemCabeca) -> void:
	mount = new_mount
	is_flying = false
	stance = PlayerController.Stance.AIRBORNE
	_camera.lift = RideTuning.CAMERA_LIFT
	_body.global_position = new_mount.global_position
	_model.global_rotation.y = new_mount.global_rotation.y


## Desce pela esquerda da mula, que fica parada onde está.
func stop() -> void:
	var side_step: Vector3 = _model.global_basis.x * RideTuning.DISMOUNT_SIDE_OFFSET

	mount.is_airborne = false
	mount.set_turbo(false)
	mount.play_animation(MulaSemCabeca.IDLE_ANIMATION)
	mount = null
	is_flying = false
	_turbo_seconds_left = 0.0
	_camera.lift = 0.0
	_model.position = Vector3.ZERO
	_body.move_and_collide(side_step)


## Guia a mula: no chão anda como a pé (bem mais rápido, gira devagar, passa por cima de banco
## e canteiro); um toque no pulo salta, dois levantam voo. No ar vai para onde a câmera olha,
## pulo sobe e Ctrl desce; encostando no chão sem subir, pousa. Dois toques no correr: turbo.
func advance(input_vector: Vector2, delta: float) -> void:
	var climb: float = _body.read_climb_input() if is_flying else 0.0
	var steer_basis: Basis = _camera.get_look_basis() if is_flying else _camera.global_basis
	var move_direction: Vector3 = steer_basis * Vector3(input_vector.x, 0.0, input_vector.y)
	var new_stance: PlayerController.Stance
	var speed: float

	_read_ride_taps()
	_burn_turbo(delta)

	if _turbo_seconds_left > 0.0 and move_direction.is_zero_approx():
		move_direction = _model.global_basis.z

	new_stance = _choose_ride_stance(move_direction, climb)
	speed = RideTuning.SPEED_BY_STANCE[new_stance]

	if _turbo_seconds_left > 0.0:
		speed = (
			maxf(speed, RideTuning.SPEED_BY_STANCE[PlayerController.Stance.SPRINT])
			* RideTuning.TURBO_SPEED_SCALE
		)

	_move_mount(move_direction, climb, speed, delta)

	if is_flying and _body.is_on_floor() and climb <= 0.0:
		is_flying = false

	_turn_model_toward(Vector3(move_direction.x, 0.0, move_direction.z), delta)
	_carry_mount()
	_apply_ride_stance(new_stance)


func _read_ride_taps() -> void:
	var jumped: bool = _body.is_input_enabled and Input.is_action_just_pressed(&"jump")
	var sprinted: bool = _body.is_input_enabled and Input.is_action_just_pressed(&"sprint")

	if jumped and _is_double_tap(&"jump"):
		is_flying = true
	elif jumped and _body.is_on_floor() and not is_flying:
		_body.velocity.y = RideTuning.JUMP_VELOCITY

	if sprinted and _is_double_tap(&"sprint"):
		_turbo_seconds_left = RideTuning.TURBO_SECONDS
		mount.set_turbo(true)


func _burn_turbo(delta: float) -> void:
	if _turbo_seconds_left <= 0.0:
		return

	_turbo_seconds_left -= delta

	if _turbo_seconds_left <= 0.0:
		mount.set_turbo(false)


## Segundo toque da mesma ação dentro de PlayerController.DOUBLE_TAP_SECONDS.
func _is_double_tap(action: StringName) -> bool:
	var now_seconds: float = Time.get_ticks_msec() / 1000.0
	var is_double: bool = (
		now_seconds - _last_tap_seconds.get(action, -1.0) < PlayerController.DOUBLE_TAP_SECONDS
	)

	_last_tap_seconds[action] = -1.0 if is_double else now_seconds

	return is_double


func _choose_ride_stance(move_direction: Vector3, climb: float) -> PlayerController.Stance:
	var is_moving: bool = not move_direction.is_zero_approx()

	if is_flying:
		return (
			PlayerController.Stance.FLY
			if is_moving or climb != 0.0
			else PlayerController.Stance.HOVER
		)

	if not _body.is_on_floor():
		return PlayerController.Stance.AIRBORNE

	if not is_moving:
		return PlayerController.Stance.IDLE

	if Input.is_action_pressed(&"sprint") or _turbo_seconds_left > 0.0:
		return PlayerController.Stance.SPRINT

	if Input.is_action_pressed(&"walk"):
		return PlayerController.Stance.WALK

	return PlayerController.Stance.RUN


func _move_mount(move_direction: Vector3, climb: float, speed: float, delta: float) -> void:
	var target_velocity: Vector3 = move_direction.normalized() * speed
	var acceleration: float = (
		RideTuning.TURBO_ACCELERATION if _turbo_seconds_left > 0.0 else RideTuning.ACCELERATION
	)
	var gravity: float = (
		PlayerController.RISE_GRAVITY if _body.velocity.y > 0.0 else PlayerController.FALL_GRAVITY
	)

	if is_flying:
		target_velocity += Vector3.UP * climb * RideTuning.CLIMB_SPEED
		_body.velocity = _body.velocity.move_toward(target_velocity, acceleration * delta)
		_body.move_and_slide()

		return

	_body.velocity.x = move_toward(_body.velocity.x, target_velocity.x, acceleration * delta)
	_body.velocity.z = move_toward(_body.velocity.z, target_velocity.z, acceleration * delta)
	_body.velocity.y -= gravity * delta

	if _body.is_on_floor():
		_body.climb_step(
			Vector3(_body.velocity.x, 0.0, _body.velocity.z) * PlayerController.STEP_PROBE_SECONDS,
			RideTuning.STEP_HEIGHT
		)

	_body.move_and_slide()


## A mula vai junto com o corpo e o cavaleiro senta no lombo dela.
func _carry_mount() -> void:
	var seat_drop: Vector3 = Vector3.DOWN * RideTuning.RIDER_SEAT_HEIGHT

	mount.global_position = _body.global_position
	mount.global_rotation.y = _model.global_rotation.y
	mount.is_airborne = is_flying or not _body.is_on_floor()
	_model.global_position = mount.get_saddle_position() + seat_drop
	_obstacle.velocity = Vector3(_body.velocity.x, 0.0, _body.velocity.z)


func _apply_ride_stance(next_stance: PlayerController.Stance) -> void:
	var rider_animation: StringName = RideTuning.RIDER_ANIMATION_BY_STANCE.get(
		next_stance, RideTuning.GALLOP_ANIMATION
	)

	if next_stance == stance:
		return

	stance = next_stance
	mount.play_animation(RideTuning.MULA_ANIMATION_BY_STANCE[next_stance])
	_model.play_animation(rider_animation)


func _turn_model_toward(direction: Vector3, delta: float) -> void:
	var target_yaw: float

	if direction.length_squared() < 0.01:
		return

	target_yaw = atan2(direction.x, direction.z)
	_model.global_rotation.y = lerp_angle(
		_model.global_rotation.y, target_yaw, RideTuning.TURN_SPEED * delta
	)
