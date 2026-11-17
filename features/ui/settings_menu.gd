class_name SettingsMenu
extends CanvasLayer
## Menu do Esc: abas de tela, gráficos e áudio montadas a partir do GameSettings,
## voltar ao jogo e sair.
## Esc abre e fecha; quem joga escuta visibility_changed para travar e soltar o personagem.

const ROW_FONT_SIZE: int = 20
const OPTION_MIN_WIDTH: float = 300.0
const SLIDER_VALUE_WIDTH: float = 64.0
const PERCENT_FORMAT: String = "%d%%"
const OPEN_SOUND: AudioStream = preload("res://art/audio/ui_open.wav")
const CLOSE_SOUND: AudioStream = preload("res://art/audio/ui_close.wav")
const CLICK_SOUND: AudioStream = preload("res://art/audio/ui_click.wav")

var _options_by_setting: Dictionary[GameSettings.Setting, OptionButton] = {}
var _sliders_by_setting: Dictionary[GameSettings.Setting, HSlider] = {}

@onready var _display_rows: GridContainer = %DisplayRows
@onready var _graphics_rows: GridContainer = %GraphicsRows
@onready var _audio_rows: GridContainer = %AudioRows
@onready var _resume_button: Button = %ResumeButton
@onready var _quit_button: Button = %QuitButton
@onready var _interface_sound: AudioStreamPlayer = %InterfaceSound


func _ready() -> void:
	var rows_by_section: Dictionary[GameSettings.Section, GridContainer] = {
		GameSettings.Section.DISPLAY: _display_rows,
		GameSettings.Section.GRAPHICS: _graphics_rows,
		GameSettings.Section.AUDIO: _audio_rows,
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
	_play_interface_sound(OPEN_SOUND if visible else CLOSE_SOUND)

	if not visible:
		return

	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	_show_chosen_options()


## As opções salvas são carregadas depois que o menu é montado: o menu confere ao abrir.
func _show_chosen_options() -> void:
	for setting in _options_by_setting:
		var options: OptionButton = _options_by_setting[setting]

		options.select(GameSettings.chosen_option(setting))

	for setting in _sliders_by_setting:
		var slider: HSlider = _sliders_by_setting[setting]

		slider.set_value_no_signal(GameSettings.chosen_option(setting))
		_show_slider_value(slider)


func _add_rows(rows: GridContainer, settings: Array[GameSettings.Setting]) -> void:
	for setting in settings:
		var label: Label = Label.new()
		var control: Control = (
			_make_slider(setting) if GameSettings.is_slider(setting) else _make_options(setting)
		)

		rows.add_child(label)
		rows.add_child(control)
		label.text = GameSettings.LABEL_BY_SETTING[setting]
		label.add_theme_font_size_override(&"font_size", ROW_FONT_SIZE)
		control.custom_minimum_size.x = OPTION_MIN_WIDTH


func _make_options(setting: GameSettings.Setting) -> OptionButton:
	var options: OptionButton = OptionButton.new()

	options.add_theme_font_size_override(&"font_size", ROW_FONT_SIZE)

	for option_label in GameSettings.option_labels_of(setting):
		options.add_item(option_label)

	options.item_selected.connect(
		func(option: int) -> void:
			GameSettings.choose(setting, option)
			_play_interface_sound(CLICK_SOUND)
	)
	_options_by_setting[setting] = options

	return options


## Slider com o valor ao lado; aplica enquanto arrasta, o clique soa só ao soltar.
func _make_slider(setting: GameSettings.Setting) -> HBoxContainer:
	var row: HBoxContainer = HBoxContainer.new()
	var slider: HSlider = HSlider.new()
	var value_label: Label = Label.new()
	var valid_range: Vector2i = GameSettings.option_range(setting)

	slider.min_value = valid_range.x
	slider.max_value = valid_range.y
	slider.step = 1.0
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	value_label.custom_minimum_size.x = SLIDER_VALUE_WIDTH
	value_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	value_label.add_theme_font_size_override(&"font_size", ROW_FONT_SIZE)
	row.add_child(slider)
	row.add_child(value_label)

	slider.value_changed.connect(
		func(value: float) -> void:
			GameSettings.choose(setting, int(value))
			_show_slider_value(slider)
	)
	slider.drag_ended.connect(func(_changed: bool) -> void: _play_interface_sound(CLICK_SOUND))
	_sliders_by_setting[setting] = slider

	return row


func _show_slider_value(slider: HSlider) -> void:
	var value_label: Label = slider.get_parent().get_child(1) as Label

	value_label.text = PERCENT_FORMAT % int(slider.value)


func _play_interface_sound(sound: AudioStream) -> void:
	_interface_sound.stream = sound
	_interface_sound.play()
