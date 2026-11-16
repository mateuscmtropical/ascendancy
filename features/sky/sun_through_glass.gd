class_name SunThroughGlass
extends SpotLight3D
## Sol atravessando um vitral: a spot fica no vitral e aponta para onde a luz do sol viaja, então a
## mancha colorida (projetor = desenho do vitral) anda pelo piso com a hora do dia. Acende só com o
## sol acima do horizonte e do lado de fora do vitral; de noite e no eclipse apaga.

## Quanto a luz precisa entrar de frente no vitral (cosseno): de rasante a franca.
const FACING_FADE: Vector2 = Vector2(0.05, 0.35)
const MIN_VISIBLE_ENERGY: float = 0.01
const NEAR_VERTICAL: float = 0.99

@export var day_night: DayNightCycle
## Normal do vitral apontando para dentro da igreja (mundo).
@export var inward_normal: Vector3 = Vector3.FORWARD
@export var base_energy: float = 2.0


func _ready() -> void:
	set_process(day_night != null)
	visible = false


func _process(_delta: float) -> void:
	var light_travel: Vector3 = -day_night.sun_direction_now
	var strength: float = day_night.sunlight * entry_strength(light_travel, inward_normal)
	var up: Vector3 = Vector3.FORWARD if absf(light_travel.y) > NEAR_VERTICAL else Vector3.UP

	visible = strength > MIN_VISIBLE_ENERGY

	if not visible:
		return

	light_energy = base_energy * strength
	look_at(global_position + light_travel, up)


## Quanto da luz entra pelo vitral: zero com o sol do lado de dentro ou rasante na parede.
static func entry_strength(light_travel: Vector3, inward: Vector3) -> float:
	var facing: float = light_travel.normalized().dot(inward.normalized())

	return smoothstep(FACING_FADE.x, FACING_FADE.y, facing)
