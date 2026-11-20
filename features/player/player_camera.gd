class_name PlayerCamera
extends Node3D
## Câmera de terceira pessoa do jogador (nó CameraYaw): o mouse gira o yaw e o pitch; o braço do
## ombro e o braço de trás são esferas que encostam nas paredes. Olhando para cima o braço encurta
## e o pivô sobe até a cabeça, senão a câmera desceria para baixo do chão atrás do personagem;
## perto da vertical ela chega à cabeça e o céu fica livre para ver as estrelas.

const MOUSE_SENSITIVITY: float = 0.0025
const PITCH_MIN: float = -1.1
const PITCH_MAX: float = 1.4
const ARM_LENGTH: float = 4.2
## Altura mínima da câmera acima dos pés quando olha para cima (o braço encurta para caber).
const LOOK_UP_CAMERA_HEIGHT: float = 0.5
const STARGAZE_CAMERA_HEIGHT: float = 1.45
const STARGAZE_PITCH: Vector2 = Vector2(0.9, 1.35)
const PIVOT_HEIGHT: float = 1.55
const LOOK_UP_PIVOT_HEIGHT: float = 1.75

## Altura somada ao pivô (montado na mula a câmera sobe junto com o cavaleiro).
var lift: float = 0.0:
	set(value):
		lift = value
		_follow_pitch()

var _collision_mask: int

@onready var _pitch: Node3D = $CameraPitch
@onready var _shoulder_arm: SpringArm3D = $CameraPitch/ShoulderArm
@onready var _spring_arm: SpringArm3D = $CameraPitch/ShoulderArm/SpringArm3D
@onready var _camera: Camera3D = $CameraPitch/ShoulderArm/SpringArm3D/Camera3D


func _ready() -> void:
	_collision_mask = _spring_arm.collision_mask
	_follow_pitch()


## Altura do pivô acima dos pés: sobe até a cabeça conforme o olhar vai para cima.
static func pivot_height_for(pitch: float) -> float:
	return lerpf(PIVOT_HEIGHT, LOOK_UP_PIVOT_HEIGHT, smoothstep(0.0, PITCH_MAX, pitch))


## Comprimento do braço para a câmera nunca descer abaixo de LOOK_UP_CAMERA_HEIGHT (pitch > 0
## põe a câmera abaixo do pivô); perto da vertical o piso sobe até STARGAZE_CAMERA_HEIGHT.
static func arm_length_for(pitch: float) -> float:
	var stargaze: float = smoothstep(STARGAZE_PITCH.x, STARGAZE_PITCH.y, pitch)
	var lowest_camera: float = lerpf(LOOK_UP_CAMERA_HEIGHT, STARGAZE_CAMERA_HEIGHT, stargaze)
	var drop_room: float = pivot_height_for(pitch) - lowest_camera

	if pitch <= 0.0:
		return ARM_LENGTH

	return minf(ARM_LENGTH, drop_room / sin(pitch))


func rotate_by_mouse(mouse_delta: Vector2) -> void:
	var pitch: float = _pitch.rotation.x - mouse_delta.y * MOUSE_SENSITIVITY

	rotation.y -= mouse_delta.x * MOUSE_SENSITIVITY
	_pitch.rotation.x = clampf(pitch, PITCH_MIN, PITCH_MAX)
	_follow_pitch()


## Os braços não batem no próprio corpo do jogador.
func ignore_body(body_rid: RID) -> void:
	_shoulder_arm.add_excluded_object(body_rid)
	_spring_arm.add_excluded_object(body_rid)


## No voo livre de debug a câmera atravessa paredes junto com o corpo.
func set_collides(should_collide: bool) -> void:
	_spring_arm.collision_mask = _collision_mask if should_collide else 0
	_shoulder_arm.collision_mask = _spring_arm.collision_mask


func make_current() -> void:
	_camera.make_current()


## Base do olhar (com pitch): o voo vai para onde a câmera aponta.
func get_look_basis() -> Basis:
	return _pitch.global_basis


func distance_to_pivot() -> float:
	return _camera.global_position.distance_to(global_position)


func _follow_pitch() -> void:
	var pitch: float = _pitch.rotation.x

	if not is_node_ready():
		return

	_spring_arm.spring_length = arm_length_for(pitch)
	position.y = pivot_height_for(pitch) + lift
