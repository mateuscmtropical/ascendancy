extends Node3D
## Vídeo de conferência da destruição no campo de ruínas: o jogador de verdade soca e chuta caixa,
## pedra, porta e cerca (pedidos de um roteiro, ações seguradas no InputMap, nada vai para a
## janela) e impactos de teste com energia crescente batem na ruína (a mesma chamada de
## Destruction que golpes e magias usam). `--reel=house`: a casa e o muro pré-fraturados.
## Gravar com tools_src/record.sh; fecha sozinha.

enum Cue { PLACE, ATTACK, MOVE, CAMERA, BLAST, CAPTION, QUIT }

const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
const PUNCH: UnarmedFighter.Attack = UnarmedFighter.Attack.PUNCH
const KICK: UnarmedFighter.Attack = UnarmedFighter.Attack.KICK
const RUN_ON: Array[StringName] = [&"move_forward"]
const STAND: Array[StringName] = []
const MOVE_ACTIONS: Array[StringName] = [&"move_forward", &"walk", &"sprint"]
const LEAD_IN_SECONDS: float = 1.0
## Lugar do jogador: nó de referência, ponto onde fica e ponto para onde olha (no espaço do nó).
const CRATE_SPOT: Array = ["RuinsField/Crates/Crate1", Vector3(0, 0, -0.85), Vector3(0, 0, 0)]
const STONE_SPOT: Array = ["RuinsField/Temple", Vector3(6.0, 0, 0.5), Vector3(4.8, 0, 0.5)]
const DOOR_NEAR_SPOT: Array = ["RuinsField/Gate", Vector3(0, 0, 1.15), Vector3(0, 0, 0)]
const DOOR_RUN_SPOT: Array = ["RuinsField/Gate", Vector3(0, 0, 5.0), Vector3(0, 0, 0)]
const FENCE_SPOT: Array = ["RuinsField/Fence", Vector3(3.0, 0, -0.75), Vector3(3.0, 0, 0)]
const ASIDE_SPOT: Array = ["RuinsField/Temple", Vector3(-9.0, 0, 7.0), Vector3(0, 0, 0)]
const HOUSE_DOOR_SPOT: Array = ["RuinsField/Cottage", Vector3(-1.0, 0, 2.8), Vector3(-1.0, 0, 0)]
const HOUSE_RUN_SPOT: Array = ["RuinsField/Cottage", Vector3(-1.0, 0, 6.9), Vector3(-1.0, 0, 0)]
const HOUSE_WALL_SPOT: Array = ["RuinsField/Cottage", Vector3(1.2, 0, 2.75), Vector3(1.2, 0, 0)]
const HOUSE_ASIDE_SPOT: Array = ["RuinsField/Cottage", Vector3(-7.0, 0, 9.0), Vector3(0, 0, 0)]
const REEL_ARGUMENT: String = "--reel="
## Impactos de teste: nó de referência, ponto (no espaço dele), energia e raio.
const FIELD_TIMELINE: Array[Dictionary] = [
	{"at": 0.0, "cue": Cue.CAMERA, "value": "CratesCam"},
	{"at": 0.0, "cue": Cue.PLACE, "value": CRATE_SPOT},
	{"at": 0.0, "cue": Cue.CAPTION, "value": "Soco e chute: madeira quebra"},
	{"at": 0.8, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 1.4, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 1.9, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 3.4, "cue": Cue.ATTACK, "value": KICK},
	{"at": 4.4, "cue": Cue.ATTACK, "value": KICK},
	{"at": 6.2, "cue": Cue.CAMERA, "value": "StoneCam"},
	{"at": 6.2, "cue": Cue.PLACE, "value": STONE_SPOT},
	{"at": 6.2, "cue": Cue.CAPTION, "value": "Pedra: soco e chute só soam"},
	{"at": 6.8, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 7.2, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 7.7, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 9.0, "cue": Cue.ATTACK, "value": KICK},
	{"at": 10.8, "cue": Cue.CAMERA, "value": "DoorCam"},
	{"at": 10.8, "cue": Cue.PLACE, "value": DOOR_NEAR_SPOT},
	{"at": 10.8, "cue": Cue.CAPTION, "value": "Porta de tábua grossa: chute parado não arromba"},
	{"at": 11.4, "cue": Cue.ATTACK, "value": KICK},
	{"at": 12.3, "cue": Cue.ATTACK, "value": KICK},
	{"at": 13.4, "cue": Cue.ATTACK, "value": KICK},
	{"at": 15.0, "cue": Cue.CAMERA, "value": "DoorInsideCam"},
	{"at": 15.0, "cue": Cue.PLACE, "value": DOOR_RUN_SPOT},
	{"at": 15.0, "cue": Cue.CAPTION, "value": "Chute voador arromba"},
	{"at": 15.4, "cue": Cue.MOVE, "value": RUN_ON},
	{"at": 16.05, "cue": Cue.ATTACK, "value": KICK},
	{"at": 16.25, "cue": Cue.MOVE, "value": STAND},
	{"at": 18.4, "cue": Cue.CAMERA, "value": "FenceCam"},
	{"at": 18.4, "cue": Cue.PLACE, "value": FENCE_SPOT},
	{"at": 18.4, "cue": Cue.CAPTION, "value": "Cerca"},
	{"at": 19.0, "cue": Cue.ATTACK, "value": KICK},
	{"at": 20.3, "cue": Cue.ATTACK, "value": KICK},
	{"at": 22.2, "cue": Cue.CAMERA, "value": "TempleCam"},
	{"at": 22.2, "cue": Cue.PLACE, "value": ASIDE_SPOT},
	{"at": 22.2, "cue": Cue.CAPTION, "value": "Impacto de teste: energia 300"},
	{
		"at": 22.8,
		"cue": Cue.BLAST,
		"value": ["RuinsField/Temple", Vector3(-3.0, 1.2, 4.6), 300.0, 2.0]
	},
	{"at": 25.0, "cue": Cue.CAPTION, "value": "Energia 900"},
	{
		"at": 25.6,
		"cue": Cue.BLAST,
		"value": ["RuinsField/Temple", Vector3(1.0, 1.6, 4.6), 900.0, 2.6]
	},
	{"at": 28.2, "cue": Cue.CAPTION, "value": "Energia 3000"},
	{
		"at": 28.8,
		"cue": Cue.BLAST,
		"value": ["RuinsField/Temple", Vector3(0.0, 1.4, -1.5), 3000.0, 4.5]
	},
	{"at": 34.0, "cue": Cue.QUIT, "value": null},
]
const HOUSE_TIMELINE: Array[Dictionary] = [
	{"at": 0.0, "cue": Cue.CAMERA, "value": "HouseNearCam"},
	{"at": 0.0, "cue": Cue.PLACE, "value": HOUSE_WALL_SPOT},
	{"at": 0.0, "cue": Cue.CAPTION, "value": "Parede de reboco: soco e chute não quebram"},
	{"at": 0.7, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 1.2, "cue": Cue.ATTACK, "value": PUNCH},
	{"at": 2.4, "cue": Cue.ATTACK, "value": KICK},
	{"at": 4.0, "cue": Cue.PLACE, "value": HOUSE_DOOR_SPOT},
	{"at": 4.0, "cue": Cue.CAPTION, "value": "Porta: chute parado não arromba"},
	{"at": 4.6, "cue": Cue.ATTACK, "value": KICK},
	{"at": 6.2, "cue": Cue.PLACE, "value": HOUSE_RUN_SPOT},
	{"at": 6.2, "cue": Cue.CAPTION, "value": "Chute voador arromba"},
	{"at": 6.6, "cue": Cue.MOVE, "value": RUN_ON},
	{"at": 7.25, "cue": Cue.ATTACK, "value": KICK},
	{"at": 7.45, "cue": Cue.MOVE, "value": STAND},
	{"at": 9.6, "cue": Cue.CAMERA, "value": "HouseCam"},
	{"at": 9.6, "cue": Cue.PLACE, "value": HOUSE_ASIDE_SPOT},
	{"at": 9.6, "cue": Cue.CAPTION, "value": "Impacto de teste: energia 400"},
	{
		"at": 10.2,
		"cue": Cue.BLAST,
		"value": ["RuinsField/Cottage", Vector3(1.6, 1.4, 2.4), 400.0, 1.6]
	},
	{"at": 12.4, "cue": Cue.CAPTION, "value": "Energia 1200"},
	{
		"at": 13.0,
		"cue": Cue.BLAST,
		"value": ["RuinsField/Cottage", Vector3(-0.6, 1.6, 2.6), 1200.0, 2.4]
	},
	{"at": 16.0, "cue": Cue.CAPTION, "value": "Energia 3000"},
	{
		"at": 16.6,
		"cue": Cue.BLAST,
		"value": ["RuinsField/Cottage", Vector3(0.0, 1.5, 0.0), 3000.0, 4.0]
	},
	{"at": 21.0, "cue": Cue.CAMERA, "value": "WallCam"},
	{"at": 21.0, "cue": Cue.CAPTION, "value": "Muro de pedra: energia 700"},
	{
		"at": 21.6,
		"cue": Cue.BLAST,
		"value": ["RuinsField/FieldWall", Vector3(1.5, 1.0, 0.8), 700.0, 1.8]
	},
	{"at": 25.0, "cue": Cue.QUIT, "value": null},
]
const TIMELINE_BY_REEL: Dictionary[String, Array] = {
	"field": FIELD_TIMELINE,
	"house": HOUSE_TIMELINE,
}
const CAMERA_TARGETS: Dictionary[String, String] = {
	"CratesCam": "RuinsField/Crates/Crate1",
	"StoneCam": "RuinsField/Temple",
	"DoorCam": "RuinsField/Gate",
	"DoorInsideCam": "RuinsField/Gate",
	"FenceCam": "RuinsField/Fence",
	"TempleCam": "RuinsField/Temple",
	"HouseNearCam": "RuinsField/Cottage",
	"HouseCam": "RuinsField/Cottage",
	"WallCam": "RuinsField/FieldWall",
}
## Onde cada câmera mira, no espaço do nó de referência dela.
const CAMERA_AIMS: Dictionary[String, Vector3] = {
	"CratesCam": Vector3(0, 0.9, -0.3),
	"StoneCam": Vector3(5.3, 1.1, 0.5),
	"DoorCam": Vector3(0, 1.0, 2.0),
	"DoorInsideCam": Vector3(0, 1.0, 1.5),
	"FenceCam": Vector3(3.0, 0.6, -0.3),
	"TempleCam": Vector3(0, 1.6, 1.0),
	"HouseNearCam": Vector3(0.2, 1.3, 2.4),
	"HouseCam": Vector3(0, 1.6, 0.5),
	"WallCam": Vector3(0, 1.0, 0),
}
## Câmeras postas pelo script, no espaço do nó de referência (as outras ficam onde a cena põe).
const CAMERA_PLACES: Dictionary[String, Vector3] = {
	"HouseNearCam": Vector3(4.2, 1.7, 6.6),
	"HouseCam": Vector3(5.5, 3.2, 11.0),
	"WallCam": Vector3(2.0, 2.0, 8.0),
}

var _seconds: float = -LEAD_IN_SECONDS
var _timeline: Array = FIELD_TIMELINE
var _next_cue: int = 0
var _cue_players: Dictionary[Cue, Callable] = {
	Cue.PLACE: _place_player,
	Cue.ATTACK: _request_attack,
	Cue.MOVE: _hold_move_actions,
	Cue.CAMERA: _cut_to_camera,
	Cue.BLAST: _blast,
	Cue.CAPTION: _show_caption,
	Cue.QUIT: _quit,
}

@onready var _player: PlayerController = $Player
@onready var _fighter: UnarmedFighter = $Player/UnarmedFighter
@onready var _model: CharacterModel = $Player/CharacterModel
@onready var _camera_yaw: Node3D = $Player/CameraYaw
@onready var _caption: Label = $Interface/Caption


func _ready() -> void:
	DisplayServer.window_set_position(OFFSCREEN_POSITION)

	for argument in OS.get_cmdline_user_args():
		if argument.begins_with(REEL_ARGUMENT):
			_timeline = TIMELINE_BY_REEL[argument.trim_prefix(REEL_ARGUMENT)]

	for camera_name in CAMERA_TARGETS:
		var camera: Camera3D = get_node(camera_name) as Camera3D
		var reference: Node3D = get_node(CAMERA_TARGETS[camera_name]) as Node3D

		if camera_name in CAMERA_PLACES:
			camera.global_position = reference.global_transform * CAMERA_PLACES[camera_name]

		camera.look_at(reference.global_transform * CAMERA_AIMS[camera_name])


func _physics_process(delta: float) -> void:
	var cue: Dictionary = _timeline[_next_cue]

	_seconds += delta

	while _seconds >= cue.at and _next_cue < _timeline.size():
		_cue_players[cue.cue].call(cue.value)
		_next_cue += 1

		if _next_cue < _timeline.size():
			cue = _timeline[_next_cue]


## Põe o jogador no lugar, virado para o alvo; o "para frente" das teclas aponta para lá também.
func _place_player(spot: Array) -> void:
	var reference: Node3D = get_node(spot[0]) as Node3D
	var stand: Vector3 = reference.global_transform * (spot[1] as Vector3)
	var target: Vector3 = reference.global_transform * (spot[2] as Vector3)
	var facing: Vector3 = Vector3(target.x - stand.x, 0.0, target.z - stand.z)

	_player.global_position = Vector3(stand.x, 0.0, stand.z)
	_player.velocity = Vector3.ZERO
	_model.global_rotation.y = atan2(facing.x, facing.z)
	_camera_yaw.global_rotation.y = atan2(-facing.x, -facing.z)


func _request_attack(attack: UnarmedFighter.Attack) -> void:
	_fighter.request_attack(attack)


func _hold_move_actions(held_actions: Array[StringName]) -> void:
	for action in MOVE_ACTIONS:
		Input.action_release(action)

	for action in held_actions:
		Input.action_press(action)


func _cut_to_camera(camera_name: String) -> void:
	(get_node(camera_name) as Camera3D).make_current()


func _blast(blast: Array) -> void:
	var reference: Node3D = get_node(blast[0] as String) as Node3D
	var origin: Vector3 = reference.global_transform * (blast[1] as Vector3)
	var impact: Impact = Impact.new(origin, Vector3.FORWARD, blast[3], blast[2])

	Destruction.strike(impact, self)


func _show_caption(text: String) -> void:
	_caption.text = text


func _quit(_value: Variant) -> void:
	get_tree().quit()
