class_name MulaMount
extends Area3D
## Montaria da Mula: com o jogador perto, E monta (ele passa a guiar a mula pelo chão e, com o
## pulo, pelo ar) e E de novo apeia. Montado, o aviso some: a mula vai junto e a área também.

const PROMPT_TEXT: String = "E: montar na mula"

var _player_near: PlayerController
var _rider: PlayerController

@onready var _mula: MulaSemCabeca = get_parent() as MulaSemCabeca
@onready var _prompt: Label3D = $Prompt


func _ready() -> void:
	_prompt.text = PROMPT_TEXT
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)
	_refresh_prompt()


func _unhandled_input(event: InputEvent) -> void:
	var player: PlayerController = _rider if _rider != null else _player_near

	if player == null or not event.is_action_pressed(&"interact"):
		return

	get_viewport().set_input_as_handled()
	toggle_ride(player)


## Monta o jogador na mula ou, se ele já está montado, apeia.
func toggle_ride(player: PlayerController) -> void:
	if _rider != null:
		_rider.dismount()
		_rider = null
		_refresh_prompt()

		return

	_rider = player
	player.ride(_mula)
	_refresh_prompt()


func is_ridden() -> bool:
	return _rider != null


func _on_body_entered(body: Node3D) -> void:
	if body is PlayerController:
		_player_near = body as PlayerController
		_refresh_prompt()


func _on_body_exited(body: Node3D) -> void:
	if body == _player_near:
		_player_near = null
		_refresh_prompt()


func _refresh_prompt() -> void:
	_prompt.visible = _player_near != null and _rider == null
