class_name SettingsMenu
extends CanvasLayer
## Menu do Esc: abas de tela e gráficos montadas a partir do GameSettings, voltar ao jogo e sair.
## Esc abre e fecha; quem joga escuta visibility_changed para travar e soltar o personagem.

const ROW_FONT_SIZE: int = 20
const OPTION_MIN_WIDTH: float = 300.0

var _options_by_setting: Dictionary[GameSettings.Setting, OptionButton] = {}

@onready var _display_rows: GridContainer = %DisplayRows
@onready var _graphics_rows: GridContainer = %GraphicsRows
@onready var _resume_button: Button = %ResumeButton
@onready var _quit_button: Button = %QuitButton


func _ready() -> void:
	var rows_by_section: Dictionary[GameSettings.Section, GridContainer] = {
		GameSettings.Section.DISPLAY: _display_rows,
		GameSettings.Section.GRAPHICS: _graphics_rows,
	}

	hide()
	_resume_button.pressed.connect(hide)
	_quit_button.pressed.connect(get_tree().quit)

	for section in rows_by_section:
		_add_rows(rows_by_section[section], GameSettings.settings_in(section))


func _unhandled_input(event: InputEvent) -> void:
	if not event.is_action_pressed(&"toggle_menu"):
		return

	visible = not visible
	get_viewport().set_input_as_handled()

	if not visible:
		return

	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	_show_chosen_options()


## As opções salvas são carregadas depois que o menu é montado: o menu confere ao abrir.
func _show_chosen_options() -> void:
	for setting in _options_by_setting:
		var options: OptionButton = _options_by_setting[setting]

		options.select(GameSettings.chosen_option(setting))


func _add_rows(rows: GridContainer, settings: Array[GameSettings.Setting]) -> void:
	for setting in settings:
		var label: Label = Label.new()
		var options: OptionButton = OptionButton.new()

		rows.add_child(label)
		rows.add_child(options)
		label.text = GameSettings.LABEL_BY_SETTING[setting]
		label.add_theme_font_size_override(&"font_size", ROW_FONT_SIZE)
		options.custom_minimum_size.x = OPTION_MIN_WIDTH
		options.add_theme_font_size_override(&"font_size", ROW_FONT_SIZE)

		for option_label in GameSettings.option_labels_of(setting):
			options.add_item(option_label)

		options.item_selected.connect(
			func(option: int) -> void: GameSettings.choose(setting, option)
		)
		_options_by_setting[setting] = options
