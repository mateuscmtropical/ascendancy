extends Node
## Configurações de tela, gráficos e áudio do jogador: guarda em user://settings.cfg
## e aplica no motor.
## Só a cena principal usa o que o jogador salvou. Cenas de teste e de vídeo rodam com o padrão
## do projeto, para que prints e medições não dependam do que o jogador escolheu.

signal setting_changed(setting: Setting)

enum Section { DISPLAY, GRAPHICS, AUDIO }
## Ordem de aplicação: monitor antes do modo de janela, modo antes da resolução.
enum Setting {
	MONITOR,
	WINDOW_MODE,
	RESOLUTION,
	VSYNC,
	MAX_FPS,
	RENDER_SCALE,
	MSAA,
	FXAA,
	SHADOWS,
	AMBIENT_OCCLUSION,
	INDIRECT_LIGHT,
	GLOW,
	MASTER_VOLUME,
	AMBIENT_VOLUME,
	EFFECTS_VOLUME,
}

const SETTINGS_PATH: String = "user://settings.cfg"
const SETTINGS_SECTION: String = "settings"
const SECTION_BY_SETTING: Dictionary[Setting, Section] = {
	Setting.MONITOR: Section.DISPLAY,
	Setting.WINDOW_MODE: Section.DISPLAY,
	Setting.RESOLUTION: Section.DISPLAY,
	Setting.VSYNC: Section.DISPLAY,
	Setting.MAX_FPS: Section.DISPLAY,
	Setting.RENDER_SCALE: Section.DISPLAY,
	Setting.MSAA: Section.GRAPHICS,
	Setting.FXAA: Section.GRAPHICS,
	Setting.SHADOWS: Section.GRAPHICS,
	Setting.AMBIENT_OCCLUSION: Section.GRAPHICS,
	Setting.INDIRECT_LIGHT: Section.GRAPHICS,
	Setting.GLOW: Section.GRAPHICS,
	Setting.MASTER_VOLUME: Section.AUDIO,
	Setting.AMBIENT_VOLUME: Section.AUDIO,
	Setting.EFFECTS_VOLUME: Section.AUDIO,
}
const LABEL_BY_SETTING: Dictionary[Setting, String] = {
	Setting.MONITOR: "Monitor",
	Setting.WINDOW_MODE: "Window mode",
	Setting.RESOLUTION: "Window size",
	Setting.VSYNC: "V-Sync",
	Setting.MAX_FPS: "Frame rate limit",
	Setting.RENDER_SCALE: "Render scale",
	Setting.MSAA: "Anti-aliasing (MSAA)",
	Setting.FXAA: "Edge smoothing (FXAA)",
	Setting.SHADOWS: "Shadow quality",
	Setting.AMBIENT_OCCLUSION: "Ambient occlusion",
	Setting.INDIRECT_LIGHT: "Indirect light",
	Setting.GLOW: "Glow",
	Setting.MASTER_VOLUME: "Master volume",
	Setting.AMBIENT_VOLUME: "Ambience",
	Setting.EFFECTS_VOLUME: "Effects",
}
## Cada lista tem constante tipada própria: lista solta dentro do dicionário constante
## fica sem tipo e chega vazia ao OptionButton.
const OFF_ON: PackedStringArray = ["Off", "On"]
const WINDOW_MODE_LABELS: PackedStringArray = [
	"Windowed", "Borderless fullscreen", "Exclusive fullscreen"
]
const RESOLUTION_LABELS: PackedStringArray = [
	"1280 x 720", "1600 x 900", "1920 x 1080", "2560 x 1440", "3840 x 2160"
]
const VSYNC_LABELS: PackedStringArray = ["Off", "On", "Adaptive", "Mailbox"]
const MAX_FPS_LABELS: PackedStringArray = ["Unlimited", "30", "60", "120", "144", "165", "240"]
const RENDER_SCALE_LABELS: PackedStringArray = ["50%", "67%", "77%", "85%", "100%"]
const MSAA_LABELS: PackedStringArray = ["Off", "2x", "4x", "8x"]
const SHADOW_LABELS: PackedStringArray = ["Low", "Medium", "High", "Ultra"]
const VOLUME_LABELS: PackedStringArray = [
	"0%", "10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%", "100%"
]
const FIXED_OPTION_LABELS: Dictionary[Setting, PackedStringArray] = {
	Setting.WINDOW_MODE: WINDOW_MODE_LABELS,
	Setting.RESOLUTION: RESOLUTION_LABELS,
	Setting.VSYNC: VSYNC_LABELS,
	Setting.MAX_FPS: MAX_FPS_LABELS,
	Setting.RENDER_SCALE: RENDER_SCALE_LABELS,
	Setting.MSAA: MSAA_LABELS,
	Setting.FXAA: OFF_ON,
	Setting.SHADOWS: SHADOW_LABELS,
	Setting.AMBIENT_OCCLUSION: OFF_ON,
	Setting.INDIRECT_LIGHT: OFF_ON,
	Setting.GLOW: OFF_ON,
	Setting.MASTER_VOLUME: VOLUME_LABELS,
	Setting.AMBIENT_VOLUME: VOLUME_LABELS,
	Setting.EFFECTS_VOLUME: VOLUME_LABELS,
}
## Padrão = o que o projeto já usa (project.godot e o Environment da praça).
const DEFAULT_OPTION: Dictionary[Setting, int] = {
	Setting.MONITOR: 0,
	Setting.WINDOW_MODE: 0,
	Setting.RESOLUTION: 2,
	Setting.VSYNC: 0,
	Setting.MAX_FPS: 0,
	Setting.RENDER_SCALE: 4,
	Setting.MSAA: 2,
	Setting.FXAA: 1,
	Setting.SHADOWS: 2,
	Setting.AMBIENT_OCCLUSION: 1,
	Setting.INDIRECT_LIGHT: 1,
	Setting.GLOW: 1,
	Setting.MASTER_VOLUME: 8,
	Setting.AMBIENT_VOLUME: 10,
	Setting.EFFECTS_VOLUME: 10,
}
const WINDOW_MODES: Array[DisplayServer.WindowMode] = [
	DisplayServer.WINDOW_MODE_WINDOWED,
	DisplayServer.WINDOW_MODE_FULLSCREEN,
	DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN,
]
const RESOLUTIONS: Array[Vector2i] = [
	Vector2i(1280, 720),
	Vector2i(1600, 900),
	Vector2i(1920, 1080),
	Vector2i(2560, 1440),
	Vector2i(3840, 2160),
]
const VSYNC_MODES: Array[DisplayServer.VSyncMode] = [
	DisplayServer.VSYNC_DISABLED,
	DisplayServer.VSYNC_ENABLED,
	DisplayServer.VSYNC_ADAPTIVE,
	DisplayServer.VSYNC_MAILBOX,
]
const VOLUME_STEP: float = 0.1
const MAX_FPS_VALUES: Array[int] = [0, 30, 60, 120, 144, 165, 240]
const RENDER_SCALES: Array[float] = [0.5, 0.67, 0.77, 0.85, 1.0]
const MSAA_MODES: Array[Viewport.MSAA] = [
	Viewport.MSAA_DISABLED,
	Viewport.MSAA_2X,
	Viewport.MSAA_4X,
	Viewport.MSAA_8X,
]
const SHADOW_ATLAS_SIZES: Array[int] = [2048, 4096, 4096, 8192]
const SHADOW_FILTERS: Array[RenderingServer.ShadowQuality] = [
	RenderingServer.SHADOW_QUALITY_SOFT_LOW,
	RenderingServer.SHADOW_QUALITY_SOFT_LOW,
	RenderingServer.SHADOW_QUALITY_SOFT_MEDIUM,
	RenderingServer.SHADOW_QUALITY_SOFT_HIGH,
]

var _option_labels: Dictionary[Setting, PackedStringArray] = {}
var _chosen_options: Dictionary[Setting, int] = {}
var _is_saving_enabled: bool = false
var _appliers: Dictionary[Setting, Callable] = {
	Setting.MONITOR: _apply_monitor,
	Setting.WINDOW_MODE: _apply_window_mode,
	Setting.RESOLUTION: _apply_resolution,
	Setting.VSYNC: _apply_vsync,
	Setting.MAX_FPS: _apply_max_fps,
	Setting.RENDER_SCALE: _apply_render_scale,
	Setting.MSAA: _apply_msaa,
	Setting.FXAA: _apply_fxaa,
	Setting.SHADOWS: _apply_shadows,
	Setting.AMBIENT_OCCLUSION: _apply_ambient_occlusion,
	Setting.INDIRECT_LIGHT: _apply_indirect_light,
	Setting.GLOW: _apply_glow,
	Setting.MASTER_VOLUME: _apply_volume.bind(&"Master"),
	Setting.AMBIENT_VOLUME: _apply_volume.bind(&"Ambient"),
	Setting.EFFECTS_VOLUME: _apply_volume.bind(&"Effects"),
}


## Dados prontos na construção: o menu da cena pode ficar pronto antes do _ready deste autoload.
func _init() -> void:
	_option_labels = FIXED_OPTION_LABELS.duplicate(true)
	_option_labels[Setting.MONITOR] = _monitor_labels()
	_chosen_options = DEFAULT_OPTION.duplicate()


func _ready() -> void:
	_use_saved_settings_in_main_scene.call_deferred()


func settings_in(section: Section) -> Array[Setting]:
	var settings: Array[Setting] = []

	settings.assign(
		SECTION_BY_SETTING.keys().filter(
			func(setting: Setting) -> bool: return SECTION_BY_SETTING[setting] == section
		)
	)

	return settings


func option_labels_of(setting: Setting) -> PackedStringArray:
	return _option_labels[setting]


func chosen_option(setting: Setting) -> int:
	return _chosen_options[setting]


## Aplica a opção na hora e grava (na cena principal).
func choose(setting: Setting, option: int) -> void:
	var applier: Callable = _appliers[setting]

	_chosen_options[setting] = option
	applier.call(option)
	setting_changed.emit(setting)

	if _is_saving_enabled:
		_save()


func _use_saved_settings_in_main_scene() -> void:
	var main_scene_path: String = ProjectSettings.get_setting("application/run/main_scene")
	var current_scene: Node = get_tree().current_scene

	if current_scene == null or current_scene.scene_file_path != main_scene_path:
		return

	_is_saving_enabled = true
	_load()
	_apply_all()


func _load() -> void:
	var config: ConfigFile = ConfigFile.new()

	if not FileAccess.file_exists(SETTINGS_PATH):
		return

	if config.load(SETTINGS_PATH) != OK:
		return

	for setting in _chosen_options:
		var key: String = Setting.find_key(setting)
		var saved_option: int = config.get_value(SETTINGS_SECTION, key, _chosen_options[setting])

		_chosen_options[setting] = clampi(saved_option, 0, _option_labels[setting].size() - 1)


func _save() -> void:
	var config: ConfigFile = ConfigFile.new()

	for setting in _chosen_options:
		config.set_value(SETTINGS_SECTION, Setting.find_key(setting), _chosen_options[setting])

	config.save(SETTINGS_PATH)


func _apply_all() -> void:
	for setting in _chosen_options:
		var applier: Callable = _appliers[setting]

		applier.call(_chosen_options[setting])


func _monitor_labels() -> PackedStringArray:
	var labels: PackedStringArray = []
	var screen_count: int = maxi(DisplayServer.get_screen_count(), 1)

	for screen in screen_count:
		labels.append("Monitor %d" % (screen + 1))

	return labels


func _environment() -> Environment:
	return get_viewport().find_world_3d().environment


func _apply_monitor(option: int) -> void:
	DisplayServer.window_set_current_screen(option)
	_apply_resolution(_chosen_options[Setting.RESOLUTION])


func _apply_window_mode(option: int) -> void:
	DisplayServer.window_set_mode(WINDOW_MODES[option])
	_apply_resolution(_chosen_options[Setting.RESOLUTION])


## Tamanho só vale em janela; em tela cheia quem manda é a escala de render.
func _apply_resolution(option: int) -> void:
	var screen: int = DisplayServer.window_get_current_screen()
	var screen_rect: Rect2i = DisplayServer.screen_get_usable_rect(screen)
	var window_size: Vector2i = RESOLUTIONS[option].min(screen_rect.size)

	if DisplayServer.window_get_mode() != DisplayServer.WINDOW_MODE_WINDOWED:
		return

	DisplayServer.window_set_size(window_size)
	DisplayServer.window_set_position(screen_rect.position + (screen_rect.size - window_size) / 2)


func _apply_vsync(option: int) -> void:
	DisplayServer.window_set_vsync_mode(VSYNC_MODES[option])


func _apply_max_fps(option: int) -> void:
	Engine.max_fps = MAX_FPS_VALUES[option]


func _apply_render_scale(option: int) -> void:
	var scale: float = RENDER_SCALES[option]
	var is_upscaled: bool = scale < 1.0

	get_viewport().scaling_3d_mode = (
		Viewport.SCALING_3D_MODE_FSR if is_upscaled else Viewport.SCALING_3D_MODE_BILINEAR
	)
	get_viewport().scaling_3d_scale = scale


func _apply_msaa(option: int) -> void:
	get_viewport().msaa_3d = MSAA_MODES[option]


func _apply_fxaa(option: int) -> void:
	get_viewport().screen_space_aa = (
		Viewport.SCREEN_SPACE_AA_FXAA if option == 1 else Viewport.SCREEN_SPACE_AA_DISABLED
	)


func _apply_shadows(option: int) -> void:
	RenderingServer.directional_shadow_atlas_set_size(SHADOW_ATLAS_SIZES[option], true)
	RenderingServer.directional_soft_shadow_filter_set_quality(SHADOW_FILTERS[option])


func _apply_ambient_occlusion(option: int) -> void:
	var environment: Environment = _environment()

	if environment == null:
		return

	environment.ssao_enabled = option == 1


func _apply_indirect_light(option: int) -> void:
	var environment: Environment = _environment()

	if environment == null:
		return

	environment.ssil_enabled = option == 1


func _apply_glow(option: int) -> void:
	var environment: Environment = _environment()

	if environment == null:
		return

	environment.glow_enabled = option == 1


## Volume em passos de 10%; zero silencia o canal de vez.
func _apply_volume(option: int, bus_name: StringName) -> void:
	var bus_index: int = AudioServer.get_bus_index(bus_name)
	var volume: float = option * VOLUME_STEP

	AudioServer.set_bus_mute(bus_index, option == 0)
	AudioServer.set_bus_volume_db(bus_index, linear_to_db(volume))
