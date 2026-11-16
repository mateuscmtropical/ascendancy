extends Node
## Roda o trailer sem janela e aponta, plano a plano, câmera dentro de coisa, ator fora do chão
## caminhável (atravessando sebe, banco, parede), ator fora do quadro, tampado ou pequeno demais,
## Mula, moradores e bichos da fazenda enfiados em colisão do mundo. Câmera baixa só é conferida
## contra a navmesh fora dos planos da Mula (o pasto além do muro não tem navmesh).
## Uso: tools/Godot_v4.7.2-stable_win64_console.exe --headless --path . --fixed-fps 30
##   res://tests/promo/trailer_check.tscn (ou full_check.tscn)

enum Problem {
	CAMERA_INSIDE_SOLID,
	CAMERA_IN_SCENERY,
	ACTOR_OFF_WALKWAY,
	ACTOR_OUT_OF_FRAME,
	ACTOR_HIDDEN,
	ACTOR_TOO_SMALL,
	ACTOR_TOUCHES_RESIDENT,
	MULA_IN_SOLID,
	RESIDENT_IN_SOLID,
	ANIMAL_IN_SOLID,
}

const PROBLEM_NAMES: Dictionary[Problem, String] = {
	Problem.CAMERA_INSIDE_SOLID: "câmera dentro de colisão",
	Problem.CAMERA_IN_SCENERY: "câmera baixa fora do chão caminhável (sebe/prop?)",
	Problem.ACTOR_OFF_WALKWAY: "ator fora da navmesh (atravessando algo)",
	Problem.ACTOR_OUT_OF_FRAME: "ator fora do quadro",
	Problem.ACTOR_HIDDEN: "ator tampado por colisão",
	Problem.ACTOR_TOO_SMALL: "ator pequeno demais no quadro",
	Problem.ACTOR_TOUCHES_RESIDENT: "ator encostando em morador",
	Problem.MULA_IN_SOLID: "Mula dentro de colisão (cerca, muro, feno?)",
	Problem.RESIDENT_IN_SOLID: "morador à vista dentro de colisão",
	Problem.ANIMAL_IN_SOLID: "bicho à vista dentro de colisão",
}
const WARMUP_FRAMES: int = 3
## Sem chão até aqui embaixo, o ponto está no alto (voo): conta como chão a esta distância.
const GROUND_SEARCH_DEPTH: float = 6.0
const WORLD_COLLISION_MASK: int = 1
const CAMERA_RADIUS: float = 0.25
const LOW_CAMERA_HEIGHT: float = 1.25
const CAMERA_WALKWAY_TOLERANCE: float = 0.6
const ACTOR_WALKWAY_TOLERANCE: float = 0.35
const ACTOR_HEAD_HEIGHT: float = 1.75
const ACTOR_CHEST_HEIGHT: float = 1.3
const ACTOR_MIN_SCREEN_FRACTION: float = 0.12
const RESIDENT_CLEARANCE: float = 0.65
const MULA_RADIUS: float = 0.5
const MULA_CENTER_HEIGHT: float = 1.0
const RESIDENT_RADIUS: float = 0.3
const RESIDENT_CENTER_HEIGHT: float = 1.0
const ANIMAL_RADIUS: float = 0.35
const ANIMAL_CENTER_HEIGHT: float = 0.8

@export var director: TrailerDirector

var _frame: int = 0
var _frames_by_shot: Dictionary[int, int] = {}
var _problem_frames: Dictionary[String, int] = {}
var _problem_details: Dictionary[String, String] = {}
var _camera_probe: PhysicsShapeQueryParameters3D = PhysicsShapeQueryParameters3D.new()
var _residents: Array[Node] = []
var _animals: Array[Node] = []
var _body_probe: PhysicsShapeQueryParameters3D = PhysicsShapeQueryParameters3D.new()


func _ready() -> void:
	var probe_sphere: SphereShape3D = SphereShape3D.new()

	probe_sphere.radius = CAMERA_RADIUS
	_camera_probe.shape = probe_sphere
	_camera_probe.collision_mask = WORLD_COLLISION_MASK
	process_priority = 100
	_body_probe.shape = SphereShape3D.new()
	_body_probe.collision_mask = WORLD_COLLISION_MASK
	_residents = director.hub.find_children("*", "WalkingNpc", true, false)
	_animals = director.hub.find_children("*", "FarmAnimal", true, false)


func _process(_delta: float) -> void:
	var shot_index: int = director.shot_index

	_frame += 1

	if _frame <= WARMUP_FRAMES:
		return

	_frames_by_shot[shot_index] = _frames_by_shot.get(shot_index, 0) + 1

	if director.shots[shot_index]["camera"] == TrailerShots.CameraKind.SELECT:
		return

	_check_camera(shot_index)
	_check_bodies(shot_index)

	if director.actor.visible:
		_check_actor(shot_index)


func _exit_tree() -> void:
	var keys: Array[String] = _problem_frames.keys()

	keys.sort()
	print("TRAILER CHECK: %d problema(s)" % keys.size())

	for key in keys:
		var shot_index: int = int(key.get_slice(":", 0))
		var problem: Problem = int(key.get_slice(":", 1)) as Problem

		print(
			(
				"  plano %d: %s em %d de %d quadros %s"
				% [
					shot_index + 1,
					PROBLEM_NAMES[problem],
					_problem_frames[key],
					_frames_by_shot[shot_index],
					_problem_details[key],
				]
			)
		)


func _check_camera(shot_index: int) -> void:
	var camera: Camera3D = director.camera
	var space: PhysicsDirectSpaceState3D = camera.get_world_3d().direct_space_state
	var eye: Vector3 = camera.global_position
	var height_above_ground: float = eye.y - _ground_height_below(eye)
	var touching: Array[Dictionary]

	_camera_probe.transform = Transform3D(Basis(), eye)
	touching = space.intersect_shape(_camera_probe, 1)

	if not touching.is_empty():
		_report(shot_index, Problem.CAMERA_INSIDE_SOLID, touching[0]["collider"].get_parent().name)

	if (
		height_above_ground < LOW_CAMERA_HEIGHT
		and not director.shots[shot_index].has("mula")
		and _distance_to_walkway(eye) > CAMERA_WALKWAY_TOLERANCE
	):
		_report(shot_index, Problem.CAMERA_IN_SCENERY)


## Mula, moradores e bichos à vista não podem estar dentro de colisão do mundo (cerca, prop).
func _check_bodies(shot_index: int) -> void:
	if director.shots[shot_index].has("mula"):
		_report_if_inside_solid(
			shot_index,
			Problem.MULA_IN_SOLID,
			director.mula.global_position,
			MULA_RADIUS,
			MULA_CENTER_HEIGHT
		)

	for resident: Node3D in _residents:
		_report_if_seen_inside_solid(
			shot_index, Problem.RESIDENT_IN_SOLID, resident, RESIDENT_RADIUS, RESIDENT_CENTER_HEIGHT
		)

	for animal: Node3D in _animals:
		_report_if_seen_inside_solid(
			shot_index, Problem.ANIMAL_IN_SOLID, animal, ANIMAL_RADIUS, ANIMAL_CENTER_HEIGHT
		)


func _report_if_seen_inside_solid(
	shot_index: int, problem: Problem, body: Node3D, radius: float, center_height: float
) -> void:
	var center: Vector3 = body.global_position + Vector3.UP * center_height

	if not director.camera.is_position_in_frustum(center):
		return

	_report_if_inside_solid(shot_index, problem, body.global_position, radius, center_height)


func _report_if_inside_solid(
	shot_index: int, problem: Problem, feet: Vector3, radius: float, center_height: float
) -> void:
	var space: PhysicsDirectSpaceState3D = director.camera.get_world_3d().direct_space_state
	var touching: Array[Dictionary]

	(_body_probe.shape as SphereShape3D).radius = radius
	_body_probe.transform = Transform3D(Basis(), feet + Vector3.UP * center_height)
	touching = space.intersect_shape(_body_probe, 1)

	if not touching.is_empty():
		_report(
			shot_index,
			problem,
			(
				"em %s/%s %s"
				% [
					touching[0]["collider"].get_parent().name,
					touching[0]["collider"].name,
					_describe_collider(touching[0]["collider"], feet)
				]
			)
		)


## Onde está o corpo e a caixa do colisor (para achar o que ele é na cena).
func _describe_collider(collider: CollisionObject3D, feet: Vector3) -> String:
	var shape_node: CollisionShape3D = collider.find_child("*", false, false) as CollisionShape3D
	var box: AABB = shape_node.shape.get_debug_mesh().get_aabb() if shape_node else AABB()

	return (
		"(corpo em %s, colisor em %s tamanho %s)"
		% [feet.snappedf(0.1), collider.global_position.snappedf(0.1), box.size.snappedf(0.1)]
	)


func _check_actor(shot_index: int) -> void:
	var camera: Camera3D = director.camera
	var feet: Vector3 = director.actor.global_position
	var head: Vector3 = feet + Vector3.UP * ACTOR_HEAD_HEIGHT
	var chest: Vector3 = feet + Vector3.UP * ACTOR_CHEST_HEIGHT
	var screen_height: float = director.get_viewport().get_visible_rect().size.y
	var head_on_screen: Vector2
	var feet_on_screen: Vector2

	if _distance_to_walkway(feet) > ACTOR_WALKWAY_TOLERANCE:
		_report(shot_index, Problem.ACTOR_OFF_WALKWAY)

	if _closest_resident_distance(feet) < RESIDENT_CLEARANCE:
		_report(shot_index, Problem.ACTOR_TOUCHES_RESIDENT)

	if not camera.is_position_in_frustum(chest):
		_report(shot_index, Problem.ACTOR_OUT_OF_FRAME)

		return

	if _is_blocked(camera.global_position, chest):
		_report(shot_index, Problem.ACTOR_HIDDEN)

	head_on_screen = camera.unproject_position(head)
	feet_on_screen = camera.unproject_position(feet)

	if absf(feet_on_screen.y - head_on_screen.y) < ACTOR_MIN_SCREEN_FRACTION * screen_height:
		_report(shot_index, Problem.ACTOR_TOO_SMALL)


func _closest_resident_distance(feet: Vector3) -> float:
	var closest: float = INF

	for resident: Node3D in _residents:
		var offset: Vector3 = resident.global_position - feet

		closest = minf(closest, Vector2(offset.x, offset.z).length())

	return closest


func _distance_to_walkway(point: Vector3) -> float:
	var navigation_map: RID = director.camera.get_world_3d().navigation_map
	var ground: Vector3 = Vector3(point.x, _ground_height_below(point), point.z)
	var closest: Vector3 = NavigationServer3D.map_get_closest_point(navigation_map, ground)

	return Vector2(closest.x - ground.x, closest.z - ground.z).length()


func _ground_height_below(point: Vector3) -> float:
	var space: PhysicsDirectSpaceState3D = director.camera.get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		point + Vector3.UP * 0.5, point + Vector3.DOWN * GROUND_SEARCH_DEPTH, WORLD_COLLISION_MASK
	)
	var hit: Dictionary = space.intersect_ray(query)

	return hit["position"].y if hit else point.y - GROUND_SEARCH_DEPTH


func _is_blocked(from: Vector3, to: Vector3) -> bool:
	var space: PhysicsDirectSpaceState3D = director.camera.get_world_3d().direct_space_state
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		from, to, WORLD_COLLISION_MASK
	)

	return not space.intersect_ray(query).is_empty()


func _report(shot_index: int, problem: Problem, detail: String = "") -> void:
	var key: String = "%02d:%d" % [shot_index, problem]
	var camera_position: Vector3 = director.camera.global_position

	_problem_frames[key] = _problem_frames.get(key, 0) + 1

	if _problem_details.has(key):
		return

	_problem_details[key] = (
		"(primeiro com câmera em %s %s)" % [camera_position.snappedf(0.1), detail]
	)
