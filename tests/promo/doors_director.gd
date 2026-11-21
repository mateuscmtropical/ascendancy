class_name DoorsDirector
extends Node
## Vídeo "Every door opens somewhere": a heroína jogada de verdade, com o PlayerController e a
## PlayerCamera do jogo. O diretor só injeta o que o teclado e o mouse fariam (andar, correr,
## E, chamar a mula, socos, olhar em volta). Os clipes de DoorsRoute vão em sequência, cada um
## teleportando, acertando a hora do céu e seguindo seus pontos pelo tempo fixo "seconds"; a
## edição (tools_src/cut_doors_trailer.py) corta pelos mesmos tempos. Gravar com
## env RECORD_FPS=60 bash tools_src/record.sh tests/promo/doors.tscn <saida.avi> [--clips=a,b].
## Grava com os gráficos no máximo do menu (só nesta cena, nada é salvo nas configurações).

const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
const CLIPS_ARGUMENT: String = "--clips="
const HEROINE: CharacterSelect.Choice = CharacterSelect.Choice.FEMALE
const MOVE_ACTIONS: Array[StringName] = [&"move_left", &"move_right", &"move_forward", &"move_back"]
const STANCE_ACTIONS: Array[StringName] = [&"walk", &"sprint"]
const STANCE_ACTION_BY_NAME: Dictionary[String, StringName] = {"walk": &"walk", "sprint": &"sprint"}
const ARRIVE_DISTANCE: float = 0.45
## Abaixo disso ela está parada e a câmera para de seguir o rumo (passa a girar com "orbit").
const MOVING_SPEED: float = 0.8
const CAMERA_FOLLOW_RATE: float = 2.4
const PITCH_RATE: float = 1.6
const DEFAULT_PITCH: float = -0.18
const KEY_TAP_SECONDS: float = 0.1
const PROMPT_NODE_NAME: String = "Prompt"
const RECORDING_QUALITY: Dictionary[GameSettings.Setting, int] = {
	GameSettings.Setting.MSAA: 3,
	GameSettings.Setting.SCREEN_SPACE_AA: 2,
	GameSettings.Setting.SHADOWS: 3,
	GameSettings.Setting.AMBIENT_OCCLUSION: 1,
	GameSettings.Setting.INDIRECT_LIGHT: 1,
	GameSettings.Setting.GLOW: 1,
}

@export var hub: Hub

var _player: PlayerController
var _camera_yaw: PlayerCamera
var _camera_pitch: Node3D
var _clips: Array[Dictionary] = []
var _clip_index: int = -1
var _clip_elapsed: float = 0.0
var _waypoint: int = 0
var _route: Array[Vector3] = []
var _watched: Node3D
var _next_event: int = 0
var _held_keys: Dictionary[StringName, float] = {}
var _prompts: Array[Node] = []
## Rumo da câmera quando ela chegou: o olhar em volta ("sweep") balança em torno dele.
var _sweep_center: float = 0.0
var _sweep_started_at: float = -1.0


func _ready() -> void:
	var wanted: PackedStringArray = _read_wanted_clips()

	DisplayServer.window_set_position(OFFSCREEN_POSITION)
	hub.show_scenery()
	hub.preview_choice(HEROINE)

	_player = hub.get_node("Player") as PlayerController
	_camera_yaw = _player.get_node("CameraYaw") as PlayerCamera
	_camera_pitch = _camera_yaw.get_node("CameraPitch") as Node3D
	_prompts = hub.find_children(PROMPT_NODE_NAME, "Label3D", true, false)
	_player.is_input_enabled = true
	_player.make_camera_current()

	while NavigationServer3D.map_get_iteration_id(_player.get_world_3d().navigation_map) == 0:
		await get_tree().physics_frame

	for setting in RECORDING_QUALITY:
		GameSettings.choose(setting, RECORDING_QUALITY[setting])

	for clip in DoorsRoute.CLIPS:
		if wanted.is_empty() or clip["name"] in wanted:
			_clips.append(clip)

	_start_clip(0)


func _process(_delta: float) -> void:
	for prompt in _prompts:
		prompt.visible = false


func _physics_process(delta: float) -> void:
	var clip: Dictionary

	if _clip_index < 0 or _clip_index >= _clips.size():
		return

	clip = _clips[_clip_index]
	_clip_elapsed += delta

	if _clip_elapsed >= clip["seconds"]:
		_start_clip(_clip_index + 1)

		return

	_release_finished_keys(delta)
	_fire_due_events(clip)
	_steer(clip)
	_turn_camera(clip, delta)


func _start_clip(index: int) -> void:
	var clip: Dictionary

	_clip_index = index
	_release_all_keys()

	if index >= _clips.size():
		get_tree().quit()

		return

	clip = _clips[index]
	_watched = (
		hub.find_child(clip.get("watch", ""), true, false) as Node3D if clip.has("watch") else null
	)

	if clip.has("near") and _watched != null:
		clip = _meet(clip, _watched.global_position)

	_route = _plan_route(clip)
	_clip_elapsed = 0.0
	_waypoint = 0
	_next_event = 0
	_sweep_started_at = -1.0
	print("CLIP %s %.2f s" % [clip["name"], clip["seconds"]])

	hub.set_time_of_day(clip["time"])
	_player.global_position = clip["start"]
	_player.velocity = Vector3.ZERO

	if STANCE_ACTION_BY_NAME.has(clip.get("stance", "")):
		Input.action_press(STANCE_ACTION_BY_NAME[clip["stance"]])

	var first_target: Vector3 = (
		_route[0] if not _route.is_empty() else clip["start"] + Vector3.FORWARD
	)
	var heading: Vector3 = first_target - clip["start"]
	var yaw: float = atan2(-heading.x, -heading.z) + deg_to_rad(clip.get("side", 0.0))

	_camera_yaw.rotate_by_mouse(
		(
			Vector2(
				-angle_difference(_camera_yaw.rotation.y, yaw),
				_camera_pitch.rotation.x - clip.get("pitch", DEFAULT_PITCH)
			)
			/ PlayerCamera.MOUSE_SENSITIVITY
		)
	)


## Clipe com "near" encontra quem está sendo olhado onde ele estiver agora (o Saci anda o
## tempo todo): começa a "near" dele e anda dois terços do caminho até ele.
func _meet(clip: Dictionary, watched_position: Vector3) -> Dictionary:
	var met: Dictionary = clip.duplicate()
	var start: Vector3 = watched_position + clip["near"]
	var ground: Vector3 = Vector3(watched_position.x, 0.0, watched_position.z)

	met["start"] = Vector3(start.x, 0.0, start.z)
	met["path"] = [met["start"].lerp(ground, 0.65)]

	return met


## Pontos que ela segue: os do roteiro ligados pela navmesh do jogo (desvia de canteiro, meio-fio
## e banco como quem joga) e, do fim dela, reto até o ponto (dentro das lojas a navmesh acaba
## na porta; "snap" para no ponto da navmesh mais perto, fora de canteiros); "direct" segue os
## pontos como estão ("waits" conta esses pontos).
func _plan_route(clip: Dictionary) -> Array[Vector3]:
	var route: Array[Vector3] = []
	var navigation_map: RID = _player.get_world_3d().navigation_map
	var from: Vector3 = clip["start"]

	if clip.get("direct", false):
		route.assign(clip.get("path", []))

		return route

	for point in clip.get("path", []):
		route.append_array(NavigationServer3D.map_get_path(navigation_map, from, point, true))
		route.append(
			(
				NavigationServer3D.map_get_closest_point(navigation_map, point)
				if clip.get("snap", false)
				else point
			)
		)
		from = point

	return route


## Aperta as direções que levam ao próximo ponto, vistas da câmera, como faria o teclado.
func _steer(clip: Dictionary) -> void:
	var input_vector: Vector2 = Vector2.ZERO
	var waits: Dictionary = clip.get("waits", {})
	var is_waiting: bool = _clip_elapsed < waits.get(_waypoint, 0.0)

	if _waypoint < _route.size() and not is_waiting:
		var offset: Vector3 = _route[_waypoint] - _player.global_position

		offset.y = 0.0

		if offset.length() < ARRIVE_DISTANCE:
			_waypoint += 1

		var local: Vector3 = _camera_yaw.global_basis.inverse() * offset.normalized()

		input_vector = Vector2(local.x, local.z).normalized()

	_press_move(input_vector)


func _press_move(input_vector: Vector2) -> void:
	var strengths: Array[float] = [
		maxf(-input_vector.x, 0.0),
		maxf(input_vector.x, 0.0),
		maxf(-input_vector.y, 0.0),
		maxf(input_vector.y, 0.0),
	]

	for index in MOVE_ACTIONS.size():
		if strengths[index] > 0.001:
			Input.action_press(MOVE_ACTIONS[index], strengths[index])
		else:
			Input.action_release(MOVE_ACTIONS[index])


## Mouse de quem joga: andando, a câmera vai para trás dela (mais "side" graus), vendo o que ela
## vê; quando chega, "sweep" (graus para cada lado, segundos de um lado ao outro) passeia o olhar
## pelo lugar como quem contempla, ou "orbit" gira em volta dela em graus por segundo; o olhar
## sobe ou desce até "pitch" (ou "pitch_hold" depois que ela chega).
func _turn_camera(clip: Dictionary, delta: float) -> void:
	var flat_velocity: Vector3 = Vector3(_player.velocity.x, 0.0, _player.velocity.z)
	var is_moving: bool = flat_velocity.length() > MOVING_SPEED
	var has_arrived: bool = _waypoint >= _route.size()
	var yaw_now: float = _camera_yaw.rotation.y
	var yaw_step: float = deg_to_rad(clip.get("orbit", 0.0)) * delta
	var target_pitch: float = clip.get(
		"pitch_hold" if has_arrived else "pitch", clip.get("pitch", DEFAULT_PITCH)
	)
	var pitch_rate: float = clip.get("pitch_rate", PITCH_RATE)
	var pitch_step: float = (
		(target_pitch - _camera_pitch.rotation.x) * minf(1.0, pitch_rate * delta)
	)

	if has_arrived and clip.has("sweep"):
		yaw_step = _sweep_step(clip["sweep"], yaw_now, delta)
	elif (has_arrived or not is_moving and _clip_elapsed > 1.5) and clip.has("hold_yaw"):
		var hold_yaw: float = deg_to_rad(clip["hold_yaw"])

		yaw_step = angle_difference(yaw_now, hold_yaw) * minf(1.0, CAMERA_FOLLOW_RATE * delta)
	elif _watched != null:
		var to_watched: Vector3 = _watched.global_position - _camera_yaw.global_position
		var watch_yaw: float = (
			atan2(-to_watched.x, -to_watched.z) + deg_to_rad(clip.get("side", 0.0))
		)

		yaw_step = angle_difference(yaw_now, watch_yaw) * minf(1.0, CAMERA_FOLLOW_RATE * delta)
	elif is_moving:
		var heading_yaw: float = (
			atan2(-flat_velocity.x, -flat_velocity.z) + deg_to_rad(clip.get("side", 0.0))
		)

		yaw_step = angle_difference(yaw_now, heading_yaw) * minf(1.0, CAMERA_FOLLOW_RATE * delta)

	_camera_yaw.rotate_by_mouse(Vector2(-yaw_step, -pitch_step) / PlayerCamera.MOUSE_SENSITIVITY)


func _sweep_step(sweep: Vector2, yaw_now: float, delta: float) -> float:
	var phase: float
	var target_yaw: float

	if _sweep_started_at < 0.0:
		_sweep_started_at = _clip_elapsed
		_sweep_center = yaw_now

	phase = (_clip_elapsed - _sweep_started_at) / sweep.y * PI
	target_yaw = _sweep_center + deg_to_rad(sweep.x) * sin(phase)

	return angle_difference(yaw_now, target_yaw) * minf(1.0, CAMERA_FOLLOW_RATE * delta)


## Teclas do roteiro ("events": {"at", "press", "hold"}) entram como eventos de verdade, então
## passam pelo _unhandled_input do jogo (E da passagem e da mula, socos, chamar a mula).
func _fire_due_events(clip: Dictionary) -> void:
	var events: Array = clip.get("events", [])

	while _next_event < events.size() and _clip_elapsed >= events[_next_event]["at"]:
		var event: Dictionary = events[_next_event]

		_send_action(event["press"], true)
		_held_keys[event["press"]] = event.get("hold", KEY_TAP_SECONDS)
		_next_event += 1


func _release_finished_keys(delta: float) -> void:
	for action in _held_keys.keys():
		_held_keys[action] -= delta

		if _held_keys[action] <= 0.0:
			_send_action(action, false)
			_held_keys.erase(action)


func _release_all_keys() -> void:
	for action in MOVE_ACTIONS + STANCE_ACTIONS:
		Input.action_release(action)

	for action in _held_keys.keys():
		_send_action(action, false)

	_held_keys.clear()


func _send_action(action: StringName, is_pressed: bool) -> void:
	var event: InputEventAction = InputEventAction.new()

	event.action = action
	event.pressed = is_pressed
	Input.parse_input_event(event)


func _read_wanted_clips() -> PackedStringArray:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with(CLIPS_ARGUMENT):
			return argument.trim_prefix(CLIPS_ARGUMENT).split(",")

	return PackedStringArray()
