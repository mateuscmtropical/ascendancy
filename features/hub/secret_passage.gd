class_name SecretPassage
extends Node3D
## Passagem escondida: com o jogador perto, E empurra a peça móvel (o pedestal do santo que tampa a
## escada da cripta) pelo deslocamento de abertura e E de novo a traz de volta. A peça é um
## AnimatableBody3D, então empurra quem estiver no caminho em vez de atravessá-lo.

const SWING_SECONDS: float = 2.4
const PROMPT_BY_STATE: Dictionary[bool, String] = {
	false: "E: empurrar o pedestal",
	true: "E: fechar a passagem",
}

## Deslocamento da peça móvel, no espaço deste nó, quando a passagem está aberta.
@export var open_offset: Vector3 = Vector3(-1.55, 0.0, 0.0)

var is_open: bool = false
var _bodies_near: int = 0
var _slide: Tween

@onready var _mover: AnimatableBody3D = $Mover
@onready var _reach: Area3D = $Reach
@onready var _prompt: Label3D = $Prompt


func _ready() -> void:
	_reach.body_entered.connect(_on_body_entered)
	_reach.body_exited.connect(_on_body_exited)
	_refresh_prompt()


func _unhandled_input(event: InputEvent) -> void:
	if _bodies_near == 0 or not event.is_action_pressed("interact"):
		return

	toggle()
	get_viewport().set_input_as_handled()


## Abre se está fechada, fecha se está aberta; a pedra arrasta devagar, pesada.
func toggle() -> void:
	var target: Vector3

	is_open = not is_open
	target = open_offset if is_open else Vector3.ZERO

	if _slide:
		_slide.kill()

	_slide = create_tween()
	_slide.set_process_mode(Tween.TWEEN_PROCESS_PHYSICS)
	(
		_slide
		. tween_property(_mover, "position", target, SWING_SECONDS)
		. set_trans(Tween.TRANS_QUAD)
		. set_ease(Tween.EASE_IN_OUT)
	)
	_refresh_prompt()


func is_prompt_shown() -> bool:
	return _prompt.visible


func _on_body_entered(_body: Node3D) -> void:
	_bodies_near += 1
	_refresh_prompt()


func _on_body_exited(_body: Node3D) -> void:
	_bodies_near = maxi(_bodies_near - 1, 0)
	_refresh_prompt()


func _refresh_prompt() -> void:
	_prompt.text = PROMPT_BY_STATE[is_open]
	_prompt.visible = _bodies_near > 0
