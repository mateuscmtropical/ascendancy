extends Node3D
## Praça inicial: escolha de personagem, jogo em terceira pessoa ou tour de câmera (--cinematic).
## Argumentos (depois de --): --character=male|female pula a escolha; --cinematic roda o tour.

const CHARACTER_ARGUMENT: String = "--character="
const CINEMATIC_ARGUMENT: String = "--cinematic"
const CHOICE_BY_NAME: Dictionary[String, CharacterSelect.Choice] = {
	"male": CharacterSelect.Choice.MALE,
	"female": CharacterSelect.Choice.FEMALE,
}
const BODY_BY_CHOICE: Dictionary[CharacterSelect.Choice, PackedScene] = {
	CharacterSelect.Choice.MALE: preload("res://art/characters/adventurer_male.gltf"),
	CharacterSelect.Choice.FEMALE: preload("res://art/characters/adventurer_female.gltf"),
}
const HAIR_BY_CHOICE: Dictionary[CharacterSelect.Choice, Color] = {
	CharacterSelect.Choice.MALE: Color(0.29, 0.2, 0.15),
	CharacterSelect.Choice.FEMALE: Color(0.62, 0.36, 0.2),
}

@onready var _player: PlayerController = $Player
@onready var _character_select: CharacterSelect = $CharacterSelect
@onready var _select_camera: Camera3D = $SelectCamera
@onready var _cinematic_tour: CinematicTour = $CinematicTour


func _ready() -> void:
	var arguments: PackedStringArray = OS.get_cmdline_user_args()
	var character_name: String = _read_character_name(arguments)

	_character_select.choice_previewed.connect(_preview_choice)
	_character_select.choice_confirmed.connect(_start_playing)

	if CINEMATIC_ARGUMENT in arguments:
		_start_cinematic()

		return

	if CHOICE_BY_NAME.has(character_name):
		_start_playing(CHOICE_BY_NAME[character_name])

		return

	_open_character_select()


func _read_character_name(arguments: PackedStringArray) -> String:
	for argument in arguments:
		if argument.begins_with(CHARACTER_ARGUMENT):
			return argument.trim_prefix(CHARACTER_ARGUMENT)

	return ""


func _open_character_select() -> void:
	_player.is_input_enabled = false
	_select_camera.make_current()
	_character_select.show()


func _preview_choice(choice: CharacterSelect.Choice) -> void:
	_player.set_appearance(BODY_BY_CHOICE[choice], HAIR_BY_CHOICE[choice])


func _start_playing(choice: CharacterSelect.Choice) -> void:
	_character_select.hide()
	_preview_choice(choice)
	_player.is_input_enabled = true
	_player.make_camera_current()


func _start_cinematic() -> void:
	_character_select.hide()
	_player.is_input_enabled = false
	_cinematic_tour.start_tour()
