class_name NightTakeDirector
extends Node
## Plano-sequência "Uma noite em Ascendancy", sem cortes: a heroína vai da praça no fim da
## tarde até a cripta e volta já de noite, e a câmera sobe para o céu no fim. A lente não é a
## câmera de jogo: cada perna diz de que lado dela filmar (NightTakeRoute) e a câmera gira em
## volta dela de uma perna à outra, sempre com o rosto ou o caminho no quadro.

const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
const CHARACTER_SCENE: PackedScene = preload("res://features/player/character_model.tscn")
const BODY_SCENE: PackedScene = preload("res://art/characters/adventurer_female.gltf")
const HAIR_COLOR: Color = Color(0.62, 0.36, 0.2)
const PASSAGE_NODE_NAME: String = "CryptMonument"
const PLAYER_LAYER: int = 2
const WORLD_COLLISION_MASK: int = 1
const GROUND_PROBE_UP: float = 1.2
const GROUND_PROBE_DOWN: float = 2.4
const ACTOR_AVOIDANCE_RADIUS: float = 0.5
const HEAD_HEIGHT: float = 1.55
const CAMERA_WALL_MARGIN: float = 0.3
const FRAMING_RATE: float = 1.1
const CAMERA_HEADING_RATE: float = 1.6
const CAMERA_SETTLE_RATE: float = 9.0
const ANCHOR_RATE: float = 2.2
const LOOK_AHEAD: float = 2.0
const LANTERN_BONE: StringName = &"hand_r"
const LANTERN_COLOR: Color = Color(1.0, 0.68, 0.36)
const LANTERN_ENERGY: float = 2.4
const LANTERN_RANGE: float = 7.5
const LANTERN_FADE_SECONDS: float = 1.2
## Morador a menos disso dela é empurrado de lado: o avoidance do jogo deixa passar colado.
const PERSONAL_SPACE: float = 1.1
const LENS_SPACE: float = 1.8
## Lados tentados em volta dela quando uma parede tapa a lente (graus somados ao "orbit").
const DODGE_ORBITS: Array[float] = [0.0, 35.0, -35.0, 70.0, -70.0, 110.0, -110.0]
const DODGE_RATE: float = 3.0
const CRANE_RISE: float = 2.5
const END_HOLD_SECONDS: float = 3.0

@export var hub: Hub
@export var camera: Camera3D

var actor: CharacterModel

var _legs: Array[Dictionary] = []
var _leg_starts: Array[float] = []
var _leg_index: int = -1
var _elapsed_seconds: float = 0.0
var _total_seconds: float = 0.0
var _ground_height: float = 0.0
var _heading: Vector3 = Vector3.LEFT
var _orbit: float = 0.0
var _camera_distance: float = 3.2
var _camera_height: float = 1.6
var _camera_heading: Vector3 = Vector3.LEFT
var _anchor_weight: float = 0.0
var _anchor: Vector3
var _lantern: OmniLight3D
var _lantern_lit_at: float = -1.0
var _dodge: float = 0.0
var _villagers: Array[Node] = []
var _crane_from: Transform3D
var _passage: SecretPassage
var _presence: AnimatableBody3D
var _obstacle: NavigationObstacle3D


func _ready() -> void:
	DisplayServer.window_set_position(OFFSCREEN_POSITION)
	hub.show_scenery()

	_legs.assign(NightTakeRoute.LEGS.duplicate(true))
	while NavigationServer3D.map_get_iteration_id(camera.get_world_3d().navigation_map) == 0:
		await get_tree().physics_frame

	_measure_legs()
	_passage = hub.find_child(PASSAGE_NODE_NAME, true, false) as SecretPassage

	actor = CHARACTER_SCENE.instantiate()
	add_child(actor)
	actor.set_body(BODY_SCENE, HAIR_COLOR)
	_add_presence()
	_add_lantern()
	_villagers = hub.find_children("*", "WalkingNpc", true, false)
	_heading = PathWalk.heading_along(_legs[0]["path"], 0.0).normalized()
	_camera_heading = _heading
	_update_actor(_legs[0])

	camera.make_current()
	_start_leg(0)
	_frame_toward(_legs[0], 1.0)
	camera.global_position = _orbit_position()
	camera.look_at(_look_target())


func _process(delta: float) -> void:
	var leg: Dictionary

	if _leg_index < 0:
		return

	_elapsed_seconds += delta

	if _elapsed_seconds >= _total_seconds + END_HOLD_SECONDS:
		get_tree().quit()

		return

	while _leg_index < _legs.size() - 1 and _elapsed_seconds >= _leg_starts[_leg_index + 1]:
		_start_leg(_leg_index + 1)

	leg = _legs[_leg_index]
	hub.set_time_of_day(_time_of_day_at(_elapsed_seconds))
	_update_actor(leg)
	_update_camera(leg, delta)
	_update_lantern()
	_hide_prompt()
	_keep_villagers_apart()


## Duração de cada perna: caminho / velocidade, ou "seconds" nas paradas e no guindaste.
func _measure_legs() -> void:
	var start: float = 0.0

	for leg in _legs:
		_leg_starts.append(start)
		start += _leg_length(leg)

	_total_seconds = start
	print("NIGHT_TAKE legs=", _leg_starts, " total=", _total_seconds)


func _leg_length(leg: Dictionary) -> float:
	var path: Array = leg.get("path", [])
	var speed: float = PlayerController.SPEED_BY_STANCE[leg.get(
		"stance", PlayerController.Stance.IDLE
	)]

	if path.size() < 2 or is_zero_approx(speed):
		return leg.get("seconds", 0.0)

	return PathWalk.path_length(path) / speed


func _start_leg(index: int) -> void:
	var leg: Dictionary = _legs[index]
	var stance: PlayerController.Stance = leg.get("stance", PlayerController.Stance.IDLE)
	var action: StringName = leg.get("action", &"")

	_leg_index = index

	if leg.get("crane", false):
		_crane_from = camera.global_transform

	if leg.get("open_passage", false) and not _passage.is_open:
		_passage.toggle()

	if leg.get("lantern", false) and _lantern_lit_at < 0.0:
		_lantern_lit_at = _elapsed_seconds

	if action.is_empty():
		actor.play_animation(
			PlayerController.ANIMATION_BY_STANCE[stance],
			PlayerController.ANIMATION_SPEED_BY_STANCE.get(stance, 1.0)
		)

		return

	actor.play_animation(action)


func _leg_progress() -> float:
	var length: float = maxf(_leg_length(_legs[_leg_index]), 0.001)

	return clampf((_elapsed_seconds - _leg_starts[_leg_index]) / length, 0.0, 1.0)


func _update_actor(leg: Dictionary) -> void:
	var path: Array = leg.get("path", [])
	var point: Vector3

	if path.size() < 2:
		if leg.has("face"):
			_turn_towards(_flat(leg["face"] - actor.global_position), 0.08)
			actor.global_rotation.y = atan2(_heading.x, _heading.z)

		return

	point = PathWalk.point_along(path, _leg_progress() * PathWalk.path_length(path))
	_turn_towards(PathWalk.heading_along(path, _leg_progress() * PathWalk.path_length(path)), 0.15)
	_ground_height = _probe_ground(point)
	actor.global_position = Vector3(point.x, _ground_height, point.z)
	actor.global_rotation.y = atan2(_heading.x, _heading.z)
	_obstacle.velocity = _heading * PlayerController.SPEED_BY_STANCE[leg["stance"]]


## O caminho já traz a altura aproximada; o raio só assenta o pé no piso de verdade.
func _probe_ground(point: Vector3) -> float:
	var space: PhysicsDirectSpaceState3D = camera.get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		point + Vector3.UP * GROUND_PROBE_UP,
		point + Vector3.DOWN * GROUND_PROBE_DOWN,
		WORLD_COLLISION_MASK
	)
	var hit: Dictionary

	query.exclude = [_presence.get_rid()]
	hit = space.intersect_ray(query)

	return hit["position"].y if hit else point.y


func _update_camera(leg: Dictionary, delta: float) -> void:
	var head: Vector3 = actor.global_position + Vector3.UP * HEAD_HEIGHT
	var rate: float = leg.get("rate", 1.0)
	var wanted: Vector3

	if leg.get("crane", false):
		_update_crane(leg, head)

		return

	_frame_toward(leg, minf(1.0, delta * FRAMING_RATE * rate))
	_camera_heading = _turned(
		_camera_heading, _heading, minf(1.0, delta * CAMERA_HEADING_RATE * rate)
	)
	_anchor = leg.get("camera_at", _anchor)
	_anchor_weight = move_toward(
		_anchor_weight, 1.0 if leg.has("camera_at") else 0.0, delta * ANCHOR_RATE
	)
	_dodge = rad_to_deg(
		lerp_angle(
			deg_to_rad(_dodge), deg_to_rad(_clear_dodge(head)), minf(1.0, delta * DODGE_RATE)
		)
	)
	wanted = _keep_off_walls(head, _orbit_position(_dodge))
	wanted = wanted.lerp(_anchor, smoothstep(0.0, 1.0, _anchor_weight))
	camera.global_position = camera.global_position.lerp(
		wanted, minf(1.0, delta * CAMERA_SETTLE_RATE)
	)
	camera.look_at(_look_target().lerp(head, _anchor_weight))


## Lente em volta da heroína: "orbit" graus a partir das costas, na distância e altura da perna.
func _orbit_position(dodge: float = 0.0) -> Vector3:
	var around: Vector3 = (-_camera_heading).rotated(Vector3.UP, deg_to_rad(_orbit + dodge))

	return actor.global_position + around * _camera_distance + Vector3.UP * _camera_height


## Desvio de órbita com a lente mais longe da parede: em corredor a câmera contorna a heroína
## em vez de encostar na cabeça dela.
func _clear_dodge(head: Vector3) -> float:
	var best: float = _dodge
	var best_reach: float = -1.0

	for dodge in DODGE_ORBITS:
		var spot: Vector3 = _keep_off_walls(head, _orbit_position(dodge))
		var reach: float = spot.distance_to(head)

		if reach >= _camera_distance * 0.9:
			return dodge

		if reach > best_reach:
			best = dodge
			best_reach = reach

	return best


## De costas a lente olha à frente dela; de frente, para o rosto.
func _look_target() -> Vector3:
	var head: Vector3 = actor.global_position + Vector3.UP * HEAD_HEIGHT
	var ahead: float = LOOK_AHEAD * maxf(0.0, cos(deg_to_rad(_orbit)))

	return head + _camera_heading * ahead


func _frame_toward(leg: Dictionary, weight: float) -> void:
	var orbit: float = lerp_angle(deg_to_rad(_orbit), deg_to_rad(leg.get("orbit", _orbit)), weight)

	_orbit = rad_to_deg(orbit)
	_camera_distance = lerpf(_camera_distance, leg.get("distance", _camera_distance), weight)
	_camera_height = lerpf(_camera_height, leg.get("height", _camera_height), weight)


## No fim a câmera sobe por trás da heroína e inclina até "look_up", no céu.
func _update_crane(leg: Dictionary, head: Vector3) -> void:
	var eased: float = smoothstep(0.0, 1.0, _leg_progress())
	var risen: Vector3 = _crane_from.origin + Vector3.UP * CRANE_RISE * eased
	var target: Transform3D = Transform3D(_crane_from.basis, risen).looking_at(leg["look_up"])
	var start: Transform3D = Transform3D(_crane_from.basis, risen).looking_at(head)

	camera.global_transform = start.interpolate_with(target, eased)


## Parede ou coluna entre a cabeça e a câmera: puxa a câmera para o ponto livre.
func _keep_off_walls(head: Vector3, wanted: Vector3) -> Vector3:
	var space: PhysicsDirectSpaceState3D = camera.get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		head, wanted, WORLD_COLLISION_MASK
	)
	var hit: Dictionary

	query.exclude = [_presence.get_rid()]
	hit = space.intersect_ray(query)

	if not hit:
		return wanted

	return hit["position"] + (head - wanted).normalized() * CAMERA_WALL_MARGIN


func _time_of_day_at(seconds: float) -> float:
	var keys: Array = NightTakeRoute.TIME_KEYS

	for index in keys.size() - 1:
		if seconds <= keys[index + 1].x:
			return lerpf(
				keys[index].y,
				keys[index + 1].y,
				inverse_lerp(keys[index].x, keys[index + 1].x, seconds)
			)

	return keys[-1].y


## Corpo na camada do jogador: a passagem secreta vê a heroína chegar e mostra o "E" como no jogo.
func _add_presence() -> void:
	var shape: CollisionShape3D = CollisionShape3D.new()
	var capsule: CapsuleShape3D = CapsuleShape3D.new()

	capsule.radius = 0.35
	capsule.height = 1.7
	shape.shape = capsule
	shape.position.y = 0.85

	_presence = AnimatableBody3D.new()
	_presence.collision_layer = PLAYER_LAYER
	_presence.collision_mask = 0
	_presence.sync_to_physics = false
	_presence.add_child(shape)
	actor.add_child(_presence)

	_obstacle = NavigationObstacle3D.new()
	_obstacle.radius = ACTOR_AVOIDANCE_RADIUS
	_obstacle.avoidance_enabled = true
	actor.add_child(_obstacle)


func _turn_towards(direction: Vector3, weight: float) -> void:
	_heading = _turned(_heading, direction, weight)


## Gira pelo ângulo no plano: slerp de vetores quase opostos dá eixo torto na curva.
func _turned(from: Vector3, direction: Vector3, weight: float) -> Vector3:
	var yaw: float = lerp_angle(atan2(from.x, from.z), atan2(direction.x, direction.z), weight)

	return Vector3(sin(yaw), 0.0, cos(yaw))


## Lanterna na mão direita: acesa na boca da escada, ilumina a cripta por onde ela passa.
func _add_lantern() -> void:
	var skeleton: Skeleton3D = actor.find_child("Skeleton3D", true, false)
	var hand: BoneAttachment3D = BoneAttachment3D.new()
	var body: MeshInstance3D = MeshInstance3D.new()
	var glass: CylinderMesh = CylinderMesh.new()
	var material: StandardMaterial3D = StandardMaterial3D.new()

	hand.bone_name = LANTERN_BONE
	skeleton.add_child(hand)
	glass.top_radius = 0.06
	glass.bottom_radius = 0.075
	glass.height = 0.18
	material.albedo_color = Color(0.25, 0.2, 0.15)
	material.emission_enabled = true
	material.emission = LANTERN_COLOR
	material.emission_energy_multiplier = 0.0
	glass.material = material
	body.mesh = glass
	body.position = Vector3(0.0, -0.16, 0.0)
	hand.add_child(body)

	_lantern = OmniLight3D.new()
	_lantern.light_color = LANTERN_COLOR
	_lantern.light_energy = 0.0
	_lantern.omni_range = LANTERN_RANGE
	_lantern.shadow_enabled = true
	_lantern.position = Vector3(0.0, -0.1, 0.0)
	body.add_child(_lantern)


func _update_lantern() -> void:
	var lit: float = 0.0
	var glass: CylinderMesh = (_lantern.get_parent() as MeshInstance3D).mesh

	if _lantern_lit_at >= 0.0:
		lit = smoothstep(0.0, LANTERN_FADE_SECONDS, _elapsed_seconds - _lantern_lit_at)

	_lantern.light_energy = LANTERN_ENERGY * lit
	(glass.material as StandardMaterial3D).emission_energy_multiplier = 3.0 * lit


## Moradores fora do espaço dela e da frente da lente: ninguém tapa o quadro.
func _keep_villagers_apart() -> void:
	for villager in _villagers:
		_push_away(villager as Node3D, actor.global_position, PERSONAL_SPACE)
		_push_away(villager as Node3D, camera.global_position, LENS_SPACE)


func _push_away(villager: Node3D, center: Vector3, space: float) -> void:
	var apart: Vector3 = _flat(villager.global_position - center)
	var gap: float = apart.length()

	if gap < space and gap > 0.01:
		villager.global_position += apart / gap * (space - gap)


## O aviso "E: empurrar" é do jogo; no vídeo a tela fica limpa.
func _hide_prompt() -> void:
	var prompt: Label3D = _passage.get_node_or_null("Prompt")

	if prompt:
		prompt.visible = false


func _flat(vector: Vector3) -> Vector3:
	return Vector3(vector.x, 0.0, vector.z)
