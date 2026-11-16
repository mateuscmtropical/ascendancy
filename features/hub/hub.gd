class_name Hub
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

var _shader_sun_direction: Vector3 = Vector3.ZERO
var _is_playing: bool = false

@onready var _player: PlayerController = $Player
@onready var _character_select: CharacterSelect = $CharacterSelect
@onready var _select_camera: Camera3D = $SelectCamera
@onready var _cinematic_tour: CinematicTour = $CinematicTour
@onready var _fps_counter: FpsCounter = $FpsCounter
@onready var _sun: DirectionalLight3D = $Sun
@onready var _settings_menu: SettingsMenu = $SettingsMenu
@onready var _day_night: DayNightCycle = $DayNight


func _ready() -> void:
	var arguments: PackedStringArray = OS.get_cmdline_user_args()
	var character_name: String = _read_character_name(arguments)

	_character_select.choice_previewed.connect(preview_choice)
	_character_select.choice_confirmed.connect(start_playing)
	_settings_menu.visibility_changed.connect(_follow_settings_menu)

	if CINEMATIC_ARGUMENT in arguments:
		show_scenery()
		_cinematic_tour.start_tour()

		return

	if CHOICE_BY_NAME.has(character_name):
		start_playing(CHOICE_BY_NAME[character_name])

		return

	open_character_select()


## Feixes dos vitrais (art/shaders/light_shaft.gdshader) seguem o sol: o shader lê a direção dele.
func _process(_delta: float) -> void:
	var sun_direction: Vector3 = -_sun.global_basis.z

	if sun_direction.is_equal_approx(_shader_sun_direction):
		return

	_shader_sun_direction = sun_direction
	RenderingServer.global_shader_parameter_set(&"sun_direction", sun_direction)


func open_character_select() -> void:
	_player.is_input_enabled = false
	_select_camera.make_current()
	_character_select.show()


func preview_choice(choice: CharacterSelect.Choice) -> void:
	_player.set_appearance(BODY_BY_CHOICE[choice], HAIR_BY_CHOICE[choice])


func start_playing(choice: CharacterSelect.Choice) -> void:
	_character_select.hide()
	preview_choice(choice)
	_player.is_input_enabled = true
	_player.make_camera_current()
	_is_playing = true


## Esconde a interface e trava o jogador; a câmera fica com quem chamou (tour, vídeo).
func show_scenery() -> void:
	_character_select.hide()
	_fps_counter.hide()
	_player.is_input_enabled = false


## Pula o céu para uma hora do dia (vídeo, tour); o relógio continua andando dali.
func set_time_of_day(day_time: float) -> void:
	_day_night.set_time_of_day(day_time)


func start_meteor_shower() -> void:
	_day_night.start_meteor_shower()


## Menu aberto trava o personagem; ao fechar, quem estava jogando volta com o mouse preso.
func _follow_settings_menu() -> void:
	var is_menu_open: bool = _settings_menu.visible

	_player.is_input_enabled = _is_playing and not is_menu_open

	if is_menu_open or not _is_playing:
		return

	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func _read_character_name(arguments: PackedStringArray) -> String:
	for argument in arguments:
		if argument.begins_with(CHARACTER_ARGUMENT):
			return argument.trim_prefix(CHARACTER_ARGUMENT)

	return ""
