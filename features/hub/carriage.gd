class_name Carriage
extends AnimatableBody3D
## Carroça puxada a cavalo rodando devagar em laço por uma rota fixa nas ruas rebaixadas.
## O corpo empurra o jogador e o NavigationObstacle3D filho faz os moradores desviarem.
## A posição vem só da distância percorrida (início + velocidade x tempo): duas máquinas com o
## mesmo relógio veem a carroça no mesmo lugar. Um condutor vai sentado no banco da frente.

const CHARACTER_MODEL_SCENE: PackedScene = preload("res://features/player/character_model.tscn")
const WALK_ANIMATION: StringName = &"Walk"
const DRIVER_ANIMATION: StringName = &"ual1/Sitting_Idle"
## O cavalo e a carroça viram olhando um pouco à frente: a curva sai suave mesmo na quina da rota.
const LOOK_AHEAD_DISTANCE: float = 2.5
## A traseira da carroça fica 1,4 m atrás do eixo; a caixa começa ali.
const WAGON_REAR: float = 1.4

@export var wagon_scene: PackedScene
@export var horse_scene: PackedScene
## Do eixo da carroça até as patas do cavalo, para a frente (+Z do modelo).
@export var horse_offset: float = 3.9
## Corpo do condutor (sem corpo, a carroça anda sozinha) e onde ele senta, na origem da carroça.
@export var driver_body: PackedScene
@export var driver_hair_color: Color = Color("4a3426")
@export var driver_seat: Vector3 = Vector3(0.0, 1.2, 1.6)
@export var route: PackedVector3Array = PackedVector3Array()
@export var speed: float = 1.4
@export var start_distance: float = 0.0
## Caixa que cobre carroça e cavalo (largura, altura, comprimento até o focinho).
@export var body_size: Vector3 = Vector3(2.0, 2.3, 7.6)

var _travelled: float = 0.0


func _ready() -> void:
	var wagon: Node3D = wagon_scene.instantiate() if wagon_scene else null
	var horse: Node3D = horse_scene.instantiate() if horse_scene else null

	_travelled = start_distance
	_add_body_collision()
	_add_navigation_obstacle()
	_seat_driver()

	if wagon:
		add_child(wagon)

	if horse:
		horse.position = Vector3(0.0, 0.0, horse_offset)
		add_child(horse)
		_walk_in_place(horse)

	set_physics_process(route.size() > 1)

	if route.size() < 2:
		return

	_follow_route()


func _physics_process(delta: float) -> void:
	_travelled += speed * delta
	_follow_route()


## Comprimento total do laço (o último ponto volta ao primeiro).
static func route_length(points: PackedVector3Array) -> float:
	var length: float = 0.0

	for index in points.size():
		length += points[index].distance_to(points[(index + 1) % points.size()])

	return length


## Ponto da rota a `distance` metros do primeiro ponto, dando quantas voltas for preciso.
static func point_along(points: PackedVector3Array, distance: float) -> Vector3:
	var remaining: float = fposmod(distance, maxf(route_length(points), 0.001))

	for index in points.size():
		var start: Vector3 = points[index]
		var end: Vector3 = points[(index + 1) % points.size()]
		var segment_length: float = start.distance_to(end)

		if remaining <= segment_length:
			return start.lerp(end, remaining / maxf(segment_length, 0.001))

		remaining -= segment_length

	return points[0]


func _follow_route() -> void:
	var here: Vector3 = point_along(route, _travelled)
	var ahead: Vector3 = point_along(route, _travelled + LOOK_AHEAD_DISTANCE)
	var heading: Vector3 = ahead - here

	global_position = here
	rotation.y = atan2(heading.x, heading.z)


func _add_body_collision() -> void:
	var collision: CollisionShape3D = CollisionShape3D.new()
	var box: BoxShape3D = BoxShape3D.new()

	box.size = body_size
	collision.shape = box
	collision.position = Vector3(0.0, body_size.y / 2.0, body_size.z / 2.0 - WAGON_REAR)
	add_child(collision)


## Moradores com avoidance contornam a carroça em vez de bater nela.
func _add_navigation_obstacle() -> void:
	var obstacle: NavigationObstacle3D = NavigationObstacle3D.new()

	obstacle.radius = body_size.z / 2.0
	obstacle.position.z = body_size.z / 2.0 - WAGON_REAR
	obstacle.avoidance_enabled = true
	add_child(obstacle)


func _seat_driver() -> void:
	var driver: CharacterModel

	if driver_body == null:
		return

	driver = CHARACTER_MODEL_SCENE.instantiate()
	driver.body_scene = driver_body
	driver.hair_color = driver_hair_color
	driver.start_animation = DRIVER_ANIMATION
	driver.position = driver_seat
	add_child(driver)


func _walk_in_place(horse: Node3D) -> void:
	var animation_player: AnimationPlayer = (
		horse.find_child("AnimationPlayer", true, false) as AnimationPlayer
	)

	if animation_player == null or not animation_player.has_animation(WALK_ANIMATION):
		return

	animation_player.get_animation(WALK_ANIMATION).loop_mode = Animation.LOOP_LINEAR
	animation_player.play(WALK_ANIMATION)
