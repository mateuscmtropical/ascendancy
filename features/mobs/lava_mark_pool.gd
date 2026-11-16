class_name LavaMarkPool
extends RefCounted
## Fila circular das marcas de lava no chão (pegadas e pingos): número fixo de vagas, a marca
## nova toma a vaga da mais velha. Guarda só quando cada marca nasceu; o calor sai da idade.

const NEVER: float = -1.0e6

var _capacity: int = 0
var _next_slot: int = 0
var _birth_seconds: PackedFloat32Array = PackedFloat32Array()


func _init(capacity: int) -> void:
	_capacity = capacity
	_birth_seconds.resize(capacity)
	_birth_seconds.fill(NEVER)


func get_capacity() -> int:
	return _capacity


## Vaga da marca nova (a mais antiga é reaproveitada quando todas estão em uso).
func claim_slot(now_seconds: float) -> int:
	var slot: int = _next_slot

	_birth_seconds[slot] = now_seconds
	_next_slot = (slot + 1) % _capacity

	return slot


## 1 recém-pisada, 0 fria (some): cai em linha reta ao longo de `cooling_seconds`.
func get_heat(slot: int, now_seconds: float, cooling_seconds: float) -> float:
	var age: float = now_seconds - _birth_seconds[slot]

	return clampf(1.0 - age / cooling_seconds, 0.0, 1.0)


func count_hot_marks(now_seconds: float, cooling_seconds: float) -> int:
	var hot_marks: int = 0

	for slot in _capacity:
		hot_marks += int(get_heat(slot, now_seconds, cooling_seconds) > 0.0)

	return hot_marks
