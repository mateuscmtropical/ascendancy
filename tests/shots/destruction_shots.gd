extends Node3D
## Prints do campo de ruínas: câmeras miradas no _ready e, se pedido, um impacto roteirizado antes
## do print (a mesma chamada de Destruction que o jogo usa).
## Argumentos (depois de --): [--blast=x,y,z,energia,raio[,comprimento,dx,dz]] [--blast-delay=s]

const BLAST_ARGUMENT: String = "--blast="
const DELAY_ARGUMENT: String = "--blast-delay="
const CAMERA_TARGETS: Dictionary[String, Vector3] = {
	"FieldOverview": Vector3(0, 1.2, -2),
	"TempleClose": Vector3(0, 1.6, -8),
	"TempleSide": Vector3(0, 1.4, -7),
	"CratesClose": Vector3(7.6, 0.7, 5.5),
	"GateClose": Vector3(-12, 1.3, 5),
	"FenceClose": Vector3(0, 0.7, 12),
	"CottageClose": Vector3(13, 1.8, -6),
	"WallClose": Vector3(-13, 1.0, -5),
}

var _blasts: Array[PackedFloat64Array] = []
var _delay_seconds: float = 0.4


func _ready() -> void:
	for camera_name in CAMERA_TARGETS:
		var camera: Camera3D = get_node(camera_name) as Camera3D

		camera.look_at(CAMERA_TARGETS[camera_name])

	_read_arguments()

	if not _blasts.is_empty():
		_strike_after_delay()


func _read_arguments() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with(BLAST_ARGUMENT):
			_blasts.append(argument.trim_prefix(BLAST_ARGUMENT).split_floats(","))

		if argument.begins_with(DELAY_ARGUMENT):
			_delay_seconds = argument.trim_prefix(DELAY_ARGUMENT).to_float()


func _strike_after_delay() -> void:
	await get_tree().create_timer(_delay_seconds).timeout
	await get_tree().physics_frame

	for blast in _blasts:
		var direction: Vector3 = (
			Vector3(blast[6], 0.0, blast[7]) if blast.size() > 7 else Vector3.FORWARD
		)
		var length: float = blast[5] if blast.size() > 5 else 0.0
		var impact: Impact = Impact.new(
			Vector3(blast[0], blast[1], blast[2]), direction, blast[4], blast[3], length
		)

		print("BLAST broke ", Destruction.strike(impact, self))
