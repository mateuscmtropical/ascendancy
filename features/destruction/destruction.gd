class_name Destruction
extends RefCounted
## Regras da destruição: quanto cada material aguenta, o que um impacto quebra e o som que faz.
## Um impacto (Impact) acha os pedaços quebráveis (BreakablePiece) no alcance, solta quem recebe
## mais energia do que aguenta e, com eles, os que estavam apoiados por cima. A mesma energia
## decide o impulso dos pedaços e o volume e o grave do som.
## Rede: a quebra é só o impacto (ponto, direção, raio, energia); outro cliente refaz o mesmo
## impacto e simula o entulho por conta própria, que é só visual.

enum Substance { WOOD, PLASTER, STONE, EARTH }

const WORLD_LAYER: int = 1
const PLAYER_LAYER: int = 1 << 1
const DEBRIS_LAYER: int = 1 << 4
const BREAKABLE_LAYER: int = 1 << 5
## Energia que um pedaço comum de cada material aguenta. Soco e chute quebram madeira; pedra só
## com magia.
const RESISTANCE_BY_SUBSTANCE: Dictionary[Substance, float] = {
	Substance.WOOD: 16.0,
	Substance.PLASTER: 120.0,
	Substance.STONE: 200.0,
	Substance.EARTH: 150.0,
}
const HIT_WOOD: AudioStream = preload("res://art/audio/hit_wood.tres")
const HIT_STONE: AudioStream = preload("res://art/audio/hit_stone.tres")
const BREAK_WOOD: AudioStream = preload("res://art/audio/break_wood.tres")
const BREAK_STONE: AudioStream = preload("res://art/audio/break_stone.tres")
const KNOCK_WOOD: AudioStream = preload("res://art/audio/debris_wood.tres")
const KNOCK_STONE: AudioStream = preload("res://art/audio/debris_stone.tres")
## Golpe que não quebra, quebra e entulho batendo no chão; reboco e terra soam como pedra.
const HIT_SOUND_BY_SUBSTANCE: Dictionary[Substance, AudioStream] = {
	Substance.WOOD: HIT_WOOD,
	Substance.PLASTER: HIT_STONE,
	Substance.STONE: HIT_STONE,
	Substance.EARTH: HIT_STONE,
}
const BREAK_SOUND_BY_SUBSTANCE: Dictionary[Substance, AudioStream] = {
	Substance.WOOD: BREAK_WOOD,
	Substance.PLASTER: BREAK_STONE,
	Substance.STONE: BREAK_STONE,
	Substance.EARTH: BREAK_STONE,
}
const KNOCK_SOUND_BY_SUBSTANCE: Dictionary[Substance, AudioStream] = {
	Substance.WOOD: KNOCK_WOOD,
	Substance.PLASTER: KNOCK_STONE,
	Substance.STONE: KNOCK_STONE,
	Substance.EARTH: KNOCK_STONE,
}
## Faixa de energia que o som cobre: de um soco fraco a uma magia cheia.
const QUIET_ENERGY: float = 20.0
const LOUD_ENERGY: float = 3000.0
const QUIET_VOLUME_DB: float = -16.0
const LOUD_VOLUME_DB: float = -2.0
## Quanto mais forte, mais grave.
const QUIET_PITCH: float = 1.15
const LOUD_PITCH: float = 0.6
## Golpe forte se ouve de longe.
const QUIET_UNIT_SIZE: float = 4.0
const LOUD_UNIT_SIZE: float = 40.0
const SOUND_BUS: StringName = &"Effects"
## Sons de entulho batendo ao mesmo tempo; passou disso, o pedaço cai calado.
const MAX_KNOCK_VOICES: int = 6
## Pedaços soltos na cena; passou disso, os mais velhos somem primeiro.
const MAX_LOOSE_PIECES: int = 260
const MAX_QUERY_RESULTS: int = 512

static var _knock_voices: int = 0
static var _loose_pieces: Array[BreakablePiece] = []


## Aplica o impacto ao cenário em volta e toca o som dele. Devolve quantos pedaços soltou.
## Chamar no passo de física (consulta o espaço físico).
static func strike(impact: Impact, context: Node3D) -> int:
	var pieces: Array[BreakablePiece] = find_pieces_in_reach(impact, context.get_world_3d())
	var broken: Array[BreakablePiece] = []
	var loudest_hit: BreakablePiece = null
	var loudest_energy: float = 0.0

	for piece in pieces:
		var energy: float = piece.energy_from(impact)

		# Entulho solto empurrado já soa ao bater no chão; o som do golpe é de quem estava preso.
		if not piece.is_loose and energy > loudest_energy:
			loudest_hit = piece
			loudest_energy = energy

		if piece.take_impact(impact):
			broken.append(piece)

	_release_supported(broken, context.get_world_3d())
	_play_strike_sound(impact, loudest_hit, broken, context)

	return broken.size()


## Pedaços quebráveis (presos ou soltos) que o alcance do impacto toca.
static func find_pieces_in_reach(impact: Impact, world: World3D) -> Array[BreakablePiece]:
	var query: PhysicsShapeQueryParameters3D = PhysicsShapeQueryParameters3D.new()
	var found: Array[BreakablePiece] = []
	var hits: Array[Dictionary]

	query.shape = _reach_shape(impact)
	query.transform = _reach_transform(impact)
	query.collision_mask = BREAKABLE_LAYER
	hits = world.direct_space_state.intersect_shape(query, MAX_QUERY_RESULTS)

	for hit in hits:
		var piece: BreakablePiece = hit.collider as BreakablePiece

		if piece != null:
			found.append(piece)

	return found


## 0 a 1: onde a energia cai entre um soco fraco e uma magia cheia (escala de ouvido, logarítmica).
static func loudness_of(energy: float) -> float:
	var span: float = log(LOUD_ENERGY / QUIET_ENERGY)

	return clampf(log(maxf(energy, 0.001) / QUIET_ENERGY) / span, 0.0, 1.0)


## Toca um som solto no mundo, no volume e no grave da energia; o nó some quando o som acaba.
static func play_sound_at(
	stream: AudioStream, position: Vector3, energy: float, context: Node
) -> AudioStreamPlayer3D:
	var player: AudioStreamPlayer3D = AudioStreamPlayer3D.new()
	var loudness: float = loudness_of(energy)

	player.stream = stream
	player.bus = SOUND_BUS
	player.volume_db = lerpf(QUIET_VOLUME_DB, LOUD_VOLUME_DB, loudness)
	player.pitch_scale = lerpf(QUIET_PITCH, LOUD_PITCH, loudness)
	player.unit_size = lerpf(QUIET_UNIT_SIZE, LOUD_UNIT_SIZE, loudness)
	player.finished.connect(player.queue_free)
	context.get_tree().root.add_child(player)
	player.global_position = position
	player.play()

	return player


## Batida de entulho no chão, se ainda houver voz livre.
static func play_knock(
	substance: Substance, position: Vector3, energy: float, context: Node
) -> void:
	var player: AudioStreamPlayer3D

	if _knock_voices >= MAX_KNOCK_VOICES:
		return

	_knock_voices += 1
	player = play_sound_at(KNOCK_SOUND_BY_SUBSTANCE[substance], position, energy, context)
	player.tree_exited.connect(_free_knock_voice)


## Conta um pedaço que acabou de se soltar; os mais velhos somem se passar do limite.
static func register_loose(piece: BreakablePiece) -> void:
	_loose_pieces.append(piece)

	while _loose_pieces.size() > MAX_LOOSE_PIECES:
		var oldest: BreakablePiece = _loose_pieces.pop_front()

		if is_instance_valid(oldest):
			oldest.fade_out()


static func forget_loose(piece: BreakablePiece) -> void:
	_loose_pieces.erase(piece)


static func loose_piece_count() -> int:
	return _loose_pieces.size()


static func _free_knock_voice() -> void:
	_knock_voices = maxi(_knock_voices - 1, 0)


## Solta, de baixo para cima, o que perdeu o apoio: cada pedaço solto larga os presos que estavam
## sentados nele, e a física decide quem cai e quem fica equilibrado.
static func _release_supported(released: Array[BreakablePiece], world: World3D) -> void:
	var queue: Array[BreakablePiece] = released.duplicate()

	while not queue.is_empty():
		var piece: BreakablePiece = queue.pop_back()

		queue.append_array(piece.release_pieces_on_top(world))


static func _play_strike_sound(
	impact: Impact, loudest_hit: BreakablePiece, broken: Array[BreakablePiece], context: Node3D
) -> void:
	var sound_by_substance: Dictionary[Substance, AudioStream] = BREAK_SOUND_BY_SUBSTANCE
	var substance: Substance

	if loudest_hit == null:
		return

	if broken.is_empty():
		sound_by_substance = HIT_SOUND_BY_SUBSTANCE

	substance = loudest_hit.substance
	play_sound_at(sound_by_substance[substance], impact.origin, impact.energy, context)


static func _reach_shape(impact: Impact) -> Shape3D:
	var capsule: CapsuleShape3D = CapsuleShape3D.new()
	var sphere: SphereShape3D = SphereShape3D.new()

	if impact.length <= 0.0:
		sphere.radius = impact.radius

		return sphere

	capsule.radius = impact.radius
	capsule.height = impact.length + impact.radius * 2.0

	return capsule


## A cápsula do Godot fica em pé (eixo Y): deita no comprimento do corte, centrada nele.
static func _reach_transform(impact: Impact) -> Transform3D:
	var center: Vector3 = impact.origin + impact.direction * impact.length / 2.0
	var side: Vector3 = impact.direction.cross(Vector3.UP)
	var basis: Basis

	if impact.length <= 0.0:
		return Transform3D(Basis.IDENTITY, impact.origin)

	if side.length_squared() < 0.0001:
		side = Vector3.RIGHT

	basis = Basis(side.normalized(), impact.direction, side.cross(impact.direction).normalized())

	return Transform3D(basis.orthonormalized(), center)
