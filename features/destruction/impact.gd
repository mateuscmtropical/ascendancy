class_name Impact
extends RefCounted
## Um golpe ou uma magia chegando no cenário: de onde, para onde, até que distância e com quanta
## energia. Golpe redondo (soco, explosão) com length 0; corte em linha com length > 0, de origin
## até origin + direction * length. Só conta: quem quebra é Destruction.

## Quanto o pedaço voa para fora do golpe em vez de seguir a direção dele.
const OUTWARD_SHARE: float = 0.6
## Um pouco para cima: entulho que sai rente ao chão parece arrastado, não arremessado.
const LIFT: float = 0.35

var origin: Vector3
var direction: Vector3
var radius: float
var energy: float
var length: float


func _init(
	impact_origin: Vector3,
	impact_direction: Vector3,
	impact_radius: float,
	impact_energy: float,
	reach_length: float = 0.0
) -> void:
	origin = impact_origin
	direction = impact_direction.normalized()
	radius = impact_radius
	energy = impact_energy
	length = reach_length


## Ponto da linha do golpe mais perto de point (o próprio origin num golpe redondo).
func nearest_point_to(point: Vector3) -> Vector3:
	var along: float = clampf((point - origin).dot(direction), 0.0, length)

	return origin + direction * along


## Energia que chega a point: quase cheia perto da linha do golpe, zero na borda do raio.
func energy_at(point: Vector3) -> float:
	var distance: float = nearest_point_to(point).distance_to(point)
	var share: float = 1.0 - pow(distance / radius, 2.0)

	return energy * maxf(share, 0.0)


## Para onde um pedaço em point voa: para fora do golpe, puxado na direção dele e um pouco
## para cima.
func push_direction_at(point: Vector3) -> Vector3:
	var outward: Vector3 = point - nearest_point_to(point)
	var push: Vector3

	if outward.length_squared() < 0.0001:
		outward = direction

	push = outward.normalized() * OUTWARD_SHARE + direction * (1.0 - OUTWARD_SHARE)

	return (push + Vector3.UP * LIFT).normalized()
