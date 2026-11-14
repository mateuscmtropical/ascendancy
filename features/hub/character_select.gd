class_name CharacterSelect
extends CanvasLayer
## Tela inicial: escolher aventureiro ou aventureira. Passar o mouse mostra, clicar confirma.

signal choice_previewed(choice: Choice)
signal choice_confirmed(choice: Choice)

enum Choice { MALE, FEMALE }

@onready var _male_button: Button = %MaleButton
@onready var _female_button: Button = %FemaleButton


func _ready() -> void:
	_male_button.mouse_entered.connect(choice_previewed.emit.bind(Choice.MALE))
	_female_button.mouse_entered.connect(choice_previewed.emit.bind(Choice.FEMALE))
	_male_button.pressed.connect(_confirm_choice.bind(Choice.MALE))
	_female_button.pressed.connect(_confirm_choice.bind(Choice.FEMALE))


func _confirm_choice(choice: Choice) -> void:
	hide()
	choice_confirmed.emit(choice)
