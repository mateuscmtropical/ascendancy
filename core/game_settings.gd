extends Node
## Configurações de tela, gráficos e áudio do jogador: guarda em user://settings.cfg
## e aplica no motor.
## Gráficos salvos com uma versão de padrões mais velha voltam ao padrão atual (o padrão mudou por
## desempenho: MSAA 4x e luz indireta custavam metade do quadro).
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
	SCREEN_SPACE_AA,
	SHADOWS,
	AMBIENT_OCCLUSION,
	INDIRECT_LIGHT,
	GLOW,
	MASTER_VOLUME,
	AMBIENT_VOLUME,
	EFFECTS_VOLUME,
	MUSIC_VOLUME,
}

const SETTINGS_PATH: String = "user://settings.cfg"
const SETTINGS_SECTION: String = "settings"
## Sobe quando o padrão dos gráficos muda; gráficos salvos com versão menor são descartados.
const GRAPHICS_DEFAULTS_VERSION: int = 2
const GRAPHICS_VERSION_KEY: String = "GRAPHICS_DEFAULTS_VERSION"
const SECTION_BY_SETTING: Dictionary[Setting, Section] = {
	Setting.MONITOR: Section.DISPLAY,
	Setting.WINDOW_MODE: Section.DISPLAY,
	Setting.RESOLUTION: Section.DISPLAY,
	Setting.VSYNC: Section.DISPLAY,
	Setting.MAX_FPS: Section.DISPLAY,
	Setting.RENDER_SCALE: Section.DISPLAY,
	Setting.MSAA: Section.GRAPHICS,
	Setting.SCREEN_SPACE_AA: Section.GRAPHICS,
	Setting.SHADOWS: Section.GRAPHICS,
	Setting.AMBIENT_OCCLUSION: Section.GRAPHICS,
	Setting.INDIRECT_LIGHT: Section.GRAPHICS,
	Setting.GLOW: Section.GRAPHICS,
	Setting.MASTER_VOLUME: Section.AUDIO,
	Setting.AMBIENT_VOLUME: Section.AUDIO,
	Setting.EFFECTS_VOLUME: Section.AUDIO,
	Setting.MUSIC_VOLUME: Section.AUDIO,
}
const LABEL_BY_SETTING: Dictionary[Setting, String] = {
	Setting.MONITOR: "Monitor",
	Setting.WINDOW_MODE: "Modo de janela",
	Setting.RESOLUTION: "Tamanho da janela",
	Setting.VSYNC: "V-Sync",
	Setting.MAX_FPS: "Limite de FPS",
	Setting.RENDER_SCALE: "Escala de renderização",
	Setting.MSAA: "Antisserrilhado (MSAA)",
	Setting.SCREEN_SPACE_AA: "Suavizar bordas",
	Setting.SHADOWS: "Qualidade das sombras",
	Setting.AMBIENT_OCCLUSION: "Oclusão de ambiente",
	Setting.INDIRECT_LIGHT: "Luz indireta",
	Setting.GLOW: "Brilho",
	Setting.MASTER_VOLUME: "Volume geral",
	Setting.AMBIENT_VOLUME: "Ambiente",
	Setting.EFFECTS_VOLUME: "Efeitos",
	Setting.MUSIC_VOLUME: "Música",
}
## Cada lista tem constante tipada própria: lista solta dentro do dicionário constante
## fica sem tipo e chega vazia ao OptionButton.
const OFF_ON: PackedStringArray = ["Desligado", "Ligado"]
const WINDOW_MODE_LABELS: PackedStringArray = [
	"Janela", "Tela cheia sem borda", "Tela cheia exclusiva"
]
const RESOLUTION_LABELS: PackedStringArray = [
	"1280 x 720", "1600 x 900", "1920 x 1080", "2560 x 1440", "3840 x 2160"
]
const VSYNC_LABELS: PackedStringArray = ["Desligado", "Ligado", "Adaptativo", "Mailbox"]
const MAX_FPS_LABELS: PackedStringArray = ["Sem limite", "30", "60", "120", "144", "165", "240"]
const MSAA_LABELS: PackedStringArray = ["Desligado", "2x", "4x", "8x"]
const SCREEN_SPACE_AA_LABELS: PackedStringArray = ["Desligado", "FXAA", "SMAA"]
const SHADOW_LABELS: PackedStringArray = ["Baixa", "Média", "Alta", "Ultra"]
## Ajustes contínuos viram slider em porcentagem: a opção escolhida é o próprio valor.
const SLIDER_RANGE: Dictionary[Setting, Vector2i] = {
	Setting.RENDER_SCALE: Vector2i(50, 100),
	Setting.MASTER_VOLUME: Vector2i(0, 100),
	Setting.AMBIENT_VOLUME: Vector2i(0, 100),
	Setting.EFFECTS_VOLUME: Vector2i(0, 100),
	Setting.MUSIC_VOLUME: Vector2i(0, 100),
}
## Sliders gravam com outra chave: a versão em passos guardava o índice da opção.
const SLIDER_KEY_SUFFIX: String = "_PERCENT"
const FIXED_OPTION_LABELS: Dictionary[Setting, PackedStringArray] = {
	Setting.WINDOW_MODE: WINDOW_MODE_LABELS,
	Setting.RESOLUTION: RESOLUTION_LABELS,
	Setting.VSYNC: VSYNC_LABELS,
	Setting.MAX_FPS: MAX_FPS_LABELS,
	Setting.MSAA: MSAA_LABELS,
	Setting.SCREEN_SPACE_AA: SCREEN_SPACE_AA_LABELS,
	Setting.SHADOWS: SHADOW_LABELS,
	Setting.AMBIENT_OCCLUSION: OFF_ON,
	Setting.INDIRECT_LIGHT: OFF_ON,
	Setting.GLOW: OFF_ON,
}
## Padrão = o que o projeto já usa (project.godot e o Environment da praça).
const DEFAULT_OPTION: Dictionary[Setting, int] = {
	Setting.MONITOR: 0,
	Setting.WINDOW_MODE: 0,
	Setting.RESOLUTION: 2,
	Setting.VSYNC: 0,
	Setting.MAX_FPS: 0,
	Setting.RENDER_SCALE: 100,
	Setting.MSAA: 0,
	Setting.SCREEN_SPACE_AA: 2,
	Setting.SHADOWS: 2,
	Setting.AMBIENT_OCCLUSION: 1,
	Setting.INDIRECT_LIGHT: 0,
	Setting.GLOW: 1,
	Setting.MASTER_VOLUME: 80,
	Setting.AMBIENT_VOLUME: 100,
	Setting.EFFECTS_VOLUME: 100,
	Setting.MUSIC_VOLUME: 60,
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
const PERCENT: float = 0.01
const MAX_FPS_VALUES: Array[int] = [0, 30, 60, 120, 144, 165, 240]
const SCREEN_SPACE_AA_MODES: Array[Viewport.ScreenSpaceAA] = [
	Viewport.SCREEN_SPACE_AA_DISABLED,
	Viewport.SCREEN_SPACE_AA_FXAA,
	Viewport.SCREEN_SPACE_AA_SMAA,
]
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
	Setting.SCREEN_SPACE_AA: _apply_screen_space_aa,
	Setting.SHADOWS: _apply_shadows,
	Setting.AMBIENT_OCCLUSION: _apply_ambient_occlusion,
	Setting.INDIRECT_LIGHT: _apply_indirect_light,
	Setting.GLOW: _apply_glow,
	Setting.MASTER_VOLUME: _apply_volume.bind(&"Master"),
	Setting.AMBIENT_VOLUME: _apply_volume.bind(&"Ambient"),
	Setting.EFFECTS_VOLUME: _apply_volume.bind(&"Effects"),
	Setting.MUSIC_VOLUME: _apply_volume.bind(&"Music"),
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
	return _option_labels.get(setting, PackedStringArray())


func is_slider(setting: Setting) -> bool:
	return SLIDER_RANGE.has(setting)


## Menor e maior opção válida: índice da lista ou faixa do slider.
func option_range(setting: Setting) -> Vector2i:
	if is_slider(setting):
		return SLIDER_RANGE[setting]

	return Vector2i(0, _option_labels[setting].size() - 1)


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

	for setting in _saved_settings_in(config):
		var saved_option: int = config.get_value(
			SETTINGS_SECTION, _key_of(setting), _chosen_options[setting]
		)
		var valid_range: Vector2i = option_range(setting)

		_chosen_options[setting] = clampi(saved_option, valid_range.x, valid_range.y)


func _save() -> void:
	var config: ConfigFile = ConfigFile.new()

	for setting in _chosen_options:
		config.set_value(SETTINGS_SECTION, _key_of(setting), _chosen_options[setting])

	config.set_value(SETTINGS_SECTION, GRAPHICS_VERSION_KEY, GRAPHICS_DEFAULTS_VERSION)
	config.save(SETTINGS_PATH)


## Configurações cujo valor salvo vale: os gráficos só se foram salvos com os padrões atuais.
func _saved_settings_in(config: ConfigFile) -> Array[Setting]:
	var saved_version: int = config.get_value(SETTINGS_SECTION, GRAPHICS_VERSION_KEY, 0)
	var is_graphics_current: bool = saved_version >= GRAPHICS_DEFAULTS_VERSION
	var settings: Array[Setting] = []

	for setting in _chosen_options:
		if is_graphics_current or SECTION_BY_SETTING[setting] != Section.GRAPHICS:
			settings.append(setting)

	return settings


func _key_of(setting: Setting) -> String:
	var key: String = Setting.find_key(setting)

	return key + SLIDER_KEY_SUFFIX if is_slider(setting) else key


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
	var scale: float = option * PERCENT
	var is_upscaled: bool = scale < 1.0

	get_viewport().scaling_3d_mode = (
		Viewport.SCALING_3D_MODE_FSR if is_upscaled else Viewport.SCALING_3D_MODE_BILINEAR
	)
	get_viewport().scaling_3d_scale = scale


func _apply_msaa(option: int) -> void:
	get_viewport().msaa_3d = MSAA_MODES[option]


func _apply_screen_space_aa(option: int) -> void:
	get_viewport().screen_space_aa = SCREEN_SPACE_AA_MODES[option]


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


## Volume em porcentagem; zero silencia o canal de vez.
func _apply_volume(option: int, bus_name: StringName) -> void:
	var bus_index: int = AudioServer.get_bus_index(bus_name)
	var volume: float = option * PERCENT

	AudioServer.set_bus_mute(bus_index, option == 0)
	AudioServer.set_bus_volume_db(bus_index, linear_to_db(volume))
