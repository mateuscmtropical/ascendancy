class_name SkyEclipse
extends RefCounted
## Um eclipse do dia: solar (de dia, a lua cobre o sol e aparece a coroa) ou lunar (de noite, a
## lua fica avermelhada). `start_offset` conta a partir do nascer do sol daquele dia.

enum Kind { SOLAR, LUNAR }

## Fração da duração gasta entrando e saindo da totalidade.
const RAMP_SHARE: float = 0.25

var kind: Kind = Kind.SOLAR
var start_offset: float = 0.0
var duration: float = 90.0


func _init(eclipse_kind: Kind, offset_seconds: float, seconds: float) -> void:
	kind = eclipse_kind
	start_offset = offset_seconds
	duration = seconds


## Quanto do disco está coberto (0 a 1) a `seconds_into_day` segundos do nascer do sol.
func coverage_at(seconds_into_day: float) -> float:
	var progress: float = (seconds_into_day - start_offset) / duration

	if progress <= 0.0 or progress >= 1.0:
		return 0.0

	return (
		smoothstep(0.0, RAMP_SHARE, progress) * (1.0 - smoothstep(1.0 - RAMP_SHARE, 1.0, progress))
	)
