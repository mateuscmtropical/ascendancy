extends Node
## Mede fps de cada câmera da praça: janela fora da tela, espera o aquecimento, tira a média do
## intervalo e imprime tempo de CPU/GPU e contagem de draw calls (cena principal e sombras).
## Argumentos (depois de --): [--cameras=A,B,C] [--warmup=5] [--measure=5] [--time-of-day=0.8]
## [--disable=ssao,ssil,glow,fog,shadows,sky,lights,aa] para achar o gargalo desligando um custo,
## [--hide=Trees,Buildings,...] esconde filhos diretos da praça,
## [--scene=res://...tscn] mede outra cena de câmeras (os salões ficam em shop_shots.tscn),
## [--stop=WalkingNpc,AnimationPlayer,...] desliga o processamento dos nós dessa classe (nativa ou
## class_name) para medir quanto custam por quadro,
## [--no-shadow=LeafCards,...] tira a sombra das malhas com esse nome.

const DEFAULT_SCENE_PATH: String = "res://tests/shots/hub_shots.tscn"
const OFFSCREEN_POSITION: Vector2i = Vector2i(-20000, -20000)
const CAMERAS_ARGUMENT: String = "--cameras="
const WARMUP_ARGUMENT: String = "--warmup="
const MEASURE_ARGUMENT: String = "--measure="
const DISABLE_ARGUMENT: String = "--disable="
const HIDE_ARGUMENT: String = "--hide="
const SCENE_ARGUMENT: String = "--scene="
const STOP_ARGUMENT: String = "--stop="
const NO_SHADOW_ARGUMENT: String = "--no-shadow="
const DEFAULT_CAMERAS: PackedStringArray = [
	"SpawnEye", "LawnEye", "StreetEye", "FarmEye", "CityOverview", "CathedralEye"
]
const MILLISECONDS_PER_SECOND: float = 1000.0
const MICROSECONDS_PER_MILLISECOND: float = 1000.0
const MILLION: float = 1000000.0

var _camera_names: PackedStringArray = DEFAULT_CAMERAS
var _warmup_seconds: float = 5.0
var _measure_seconds: float = 5.0
var _disabled_features: PackedStringArray = []
var _hidden_nodes: PackedStringArray = []
var _stopped_classes: PackedStringArray = []
var _shadowless_meshes: PackedStringArray = []
var _scene_path: String = DEFAULT_SCENE_PATH
var _hub_shots: Node
var _environment_disablers: Dictionary[String, Callable] = {
	"ssao": func(environment: Environment) -> void: environment.ssao_enabled = false,
	"ssil": func(environment: Environment) -> void: environment.ssil_enabled = false,
	"glow": func(environment: Environment) -> void: environment.glow_enabled = false,
	"fog": func(environment: Environment) -> void: environment.fog_enabled = false,
	"sky": _use_plain_sky,
}


func _ready() -> void:
	DisplayServer.window_set_position(OFFSCREEN_POSITION)
	_read_arguments()
	_run_benchmark()


func _read_arguments() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with(CAMERAS_ARGUMENT):
			_camera_names = argument.trim_prefix(CAMERAS_ARGUMENT).split(",")

		if argument.begins_with(WARMUP_ARGUMENT):
			_warmup_seconds = argument.trim_prefix(WARMUP_ARGUMENT).to_float()

		if argument.begins_with(MEASURE_ARGUMENT):
			_measure_seconds = argument.trim_prefix(MEASURE_ARGUMENT).to_float()

		if argument.begins_with(DISABLE_ARGUMENT):
			_disabled_features = argument.trim_prefix(DISABLE_ARGUMENT).split(",")

		if argument.begins_with(HIDE_ARGUMENT):
			_hidden_nodes = argument.trim_prefix(HIDE_ARGUMENT).split(",")

		if argument.begins_with(NO_SHADOW_ARGUMENT):
			_shadowless_meshes = argument.trim_prefix(NO_SHADOW_ARGUMENT).split(",")

		if argument.begins_with(STOP_ARGUMENT):
			_stopped_classes = argument.trim_prefix(STOP_ARGUMENT).split(",")

		if argument.begins_with(SCENE_ARGUMENT):
			_scene_path = argument.trim_prefix(SCENE_ARGUMENT)


func _run_benchmark() -> void:
	var viewport_rid: RID = get_viewport().get_viewport_rid()

	_load_scene()
	RenderingServer.viewport_set_measure_render_time(viewport_rid, true)
	await get_tree().process_frame

	_apply_disabled_features()

	for camera_name in _camera_names:
		await _measure_camera(camera_name, viewport_rid)

	get_tree().quit()


## O jogador só existe depois de escolher o personagem; o bench quer o custo dele na cena.
func _load_scene() -> void:
	var packed: PackedScene = load(_scene_path)
	var hub: Hub

	_hub_shots = packed.instantiate()
	_hub_shots.get_node("ShotCapture").free()
	add_child(_hub_shots)

	hub = _hub_shots.get_node("Hub") as Hub
	hub.start_playing(CharacterSelect.Choice.MALE)
	hub.show_scenery()


func _apply_disabled_features() -> void:
	var hub: Node = _hub_shots.get_node("Hub")
	var environment: Environment = hub.get_node("WorldEnvironment").environment
	var sun: DirectionalLight3D = hub.get_node("Sun")

	for node_name in _hidden_nodes:
		(hub.get_node(node_name) as Node3D).hide()

	for feature in _disabled_features:
		if _environment_disablers.has(feature):
			_environment_disablers[feature].call(environment)

	if "daynight" in _disabled_features:
		hub.get_node("DayNight").set_process(false)

	if "shadows" in _disabled_features:
		sun.shadow_enabled = false

	if "lights" in _disabled_features:
		_hide_local_lights(hub)

	_stop_classes(hub)
	_remove_shadows(hub)

	if "aa" in _disabled_features:
		get_viewport().msaa_3d = Viewport.MSAA_DISABLED
		get_viewport().screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED


func _remove_shadows(hub: Node) -> void:
	var meshes: Array[Node] = hub.find_children("*", "GeometryInstance3D", true, false)

	if _shadowless_meshes.is_empty():
		return

	for mesh in meshes:
		if String(mesh.name).rstrip("0123456789") in _shadowless_meshes:
			(mesh as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func _stop_classes(hub: Node) -> void:
	var nodes: Array[Node] = hub.find_children("*", "", true, false)

	if _stopped_classes.is_empty():
		return

	for node in nodes:
		if _is_stopped_class(node):
			node.process_mode = Node.PROCESS_MODE_DISABLED


func _is_stopped_class(node: Node) -> bool:
	var script: Script = node.get_script()
	var script_class: String = script.get_global_name() if script else ""

	return node.get_class() in _stopped_classes or script_class in _stopped_classes


func _hide_local_lights(hub: Node) -> void:
	var lights: Array[Node] = hub.find_children("*", "Light3D", true, false)

	for light in lights:
		if light is DirectionalLight3D:
			continue

		(light as Light3D).visible = false


func _measure_camera(camera_name: String, viewport_rid: RID) -> void:
	var camera: Camera3D = _hub_shots.find_child(camera_name, true, false) as Camera3D
	var frames: int = 0
	var cpu_total: float = 0.0
	var gpu_samples: PackedFloat64Array = []
	var frame_samples: PackedFloat64Array = []
	var process_total: float = 0.0
	var physics_total: float = 0.0
	var navigation_total: float = 0.0
	var last_usec: int
	var started_msec: int
	var elapsed_seconds: float

	camera.make_current()
	await get_tree().create_timer(_warmup_seconds).timeout

	started_msec = Time.get_ticks_msec()
	last_usec = Time.get_ticks_usec()

	while (Time.get_ticks_msec() - started_msec) < _measure_seconds * MILLISECONDS_PER_SECOND:
		await RenderingServer.frame_post_draw
		frames += 1
		cpu_total += RenderingServer.viewport_get_measured_render_time_cpu(viewport_rid)
		gpu_samples.append(RenderingServer.viewport_get_measured_render_time_gpu(viewport_rid))
		frame_samples.append((Time.get_ticks_usec() - last_usec) / MICROSECONDS_PER_MILLISECOND)
		process_total += Performance.get_monitor(Performance.TIME_PROCESS)
		physics_total += Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS)
		navigation_total += Performance.get_monitor(Performance.TIME_NAVIGATION_PROCESS)
		last_usec = Time.get_ticks_usec()

	elapsed_seconds = (Time.get_ticks_msec() - started_msec) / MILLISECONDS_PER_SECOND
	_print_row(
		camera_name,
		viewport_rid,
		{
			"fps": frames / elapsed_seconds,
			"fps_median": MILLISECONDS_PER_SECOND / _median(frame_samples),
			"cpu_ms": cpu_total / frames,
			"gpu_median_ms": _median(gpu_samples),
			"process_ms": process_total / frames * MILLISECONDS_PER_SECOND,
			"physics_ms": physics_total / frames * MILLISECONDS_PER_SECOND,
			"navigation_ms": navigation_total / frames * MILLISECONDS_PER_SECOND,
		}
	)


func _print_row(camera_name: String, viewport_rid: RID, timing: Dictionary) -> void:
	var visible_calls: int = _render_info(
		viewport_rid, false, RenderingServer.VIEWPORT_RENDER_INFO_DRAW_CALLS_IN_FRAME
	)
	var shadow_calls: int = _render_info(
		viewport_rid, true, RenderingServer.VIEWPORT_RENDER_INFO_DRAW_CALLS_IN_FRAME
	)
	var visible_objects: int = _render_info(
		viewport_rid, false, RenderingServer.VIEWPORT_RENDER_INFO_OBJECTS_IN_FRAME
	)
	var visible_primitives: int = _render_info(
		viewport_rid, false, RenderingServer.VIEWPORT_RENDER_INFO_PRIMITIVES_IN_FRAME
	)
	var shadow_primitives: int = _render_info(
		viewport_rid, true, RenderingServer.VIEWPORT_RENDER_INFO_PRIMITIVES_IN_FRAME
	)

	print(
		(
			(
				"BENCH %s fps=%.1f fps_med=%.1f cpu_ms=%.2f gpu_med_ms=%.2f calls=%d"
				+ " shadow_calls=%d objects=%d tris_m=%.2f shadow_tris_m=%.2f"
				+ " process_ms=%.2f physics_ms=%.2f navigation_ms=%.2f"
			)
			% [
				camera_name,
				timing["fps"],
				timing["fps_median"],
				timing["cpu_ms"],
				timing["gpu_median_ms"],
				visible_calls,
				shadow_calls,
				visible_objects,
				visible_primitives / MILLION,
				shadow_primitives / MILLION,
				timing["process_ms"],
				timing["physics_ms"],
				timing["navigation_ms"],
			]
		)
	)


func _median(samples: PackedFloat64Array) -> float:
	var sorted: PackedFloat64Array = samples.duplicate()

	sorted.sort()

	return sorted[sorted.size() / 2]


func _render_info(
	viewport_rid: RID, is_shadow: bool, info: RenderingServer.ViewportRenderInfo
) -> int:
	var info_type: RenderingServer.ViewportRenderInfoType = (
		RenderingServer.VIEWPORT_RENDER_INFO_TYPE_SHADOW
		if is_shadow
		else RenderingServer.VIEWPORT_RENDER_INFO_TYPE_VISIBLE
	)

	return RenderingServer.viewport_get_render_info(viewport_rid, info_type, info)


## Céu simples no lugar do shader procedural, para medir quanto o céu custa.
static func _use_plain_sky(environment: Environment) -> void:
	environment.sky.sky_material = ProceduralSkyMaterial.new()
