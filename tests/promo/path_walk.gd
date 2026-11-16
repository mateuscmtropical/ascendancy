class_name PathWalk
extends RefCounted
## Andar por um caminho de pontos (lista de Vector3): comprimento, ponto e direção a uma distância.


static func path_length(path: Array) -> float:
	var length: float = 0.0

	for index in path.size() - 1:
		length += path[index].distance_to(path[index + 1])

	return length


static func point_along(path: Array, travel: float) -> Vector3:
	var remaining: float = travel

	for index in path.size() - 1:
		var segment: Vector3 = path[index + 1] - path[index]

		if remaining <= segment.length():
			return path[index] + segment.normalized() * remaining

		remaining -= segment.length()

	return path[-1]


static func heading_along(path: Array, travel: float) -> Vector3:
	var remaining: float = travel

	if path.size() < 2:
		return Vector3.BACK

	for index in path.size() - 1:
		var segment: Vector3 = path[index + 1] - path[index]

		if remaining <= segment.length() or index == path.size() - 2:
			return Vector3(segment.x, 0.0, segment.z)

		remaining -= segment.length()

	return Vector3.BACK
