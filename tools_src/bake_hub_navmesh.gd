extends SceneTree
## Assa a navmesh da praça a partir das malhas e colisões do grupo "navigation_source" e salva em
## features/hub/hub_navmesh.tres. Rodar depois de build_hub_scene.py:
##   tools/Godot_v4.7.2-stable_win64_console.exe --headless --path . -s tools_src/bake_hub_navmesh.gd

const HUB_SCENE_PATH: String = "res://features/hub/hub.tscn"
const OUTPUT_PATH: String = "res://features/hub/hub_navmesh.tres"
const SOURCE_GROUP: StringName = &"navigation_source"
const PLAZA_BOUNDS: AABB = AABB(Vector3(-45.5, -1.0, -83.5), Vector3(91.0, 6.0, 129.0))


func _initialize() -> void:
	_bake_and_save.call_deferred()


func _bake_and_save() -> void:
	var hub: Node3D = load(HUB_SCENE_PATH).instantiate()
	var navigation_mesh: NavigationMesh = _make_navigation_mesh()
	var source_geometry: NavigationMeshSourceGeometryData3D = NavigationMeshSourceGeometryData3D.new()
	var save_error: Error

	root.add_child(hub)
	await process_frame

	NavigationServer3D.parse_source_geometry_data(navigation_mesh, source_geometry, hub)
	NavigationServer3D.bake_from_source_geometry_data(navigation_mesh, source_geometry)
	save_error = ResourceSaver.save(navigation_mesh, OUTPUT_PATH)

	print(
		"NAVMESH polygons=", navigation_mesh.get_polygon_count(),
		" vertices=", navigation_mesh.vertices.size(),
		" saved=", error_string(save_error)
	)
	quit()


func _make_navigation_mesh() -> NavigationMesh:
	var navigation_mesh: NavigationMesh = NavigationMesh.new()

	navigation_mesh.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_BOTH
	navigation_mesh.geometry_source_geometry_mode = (
		NavigationMesh.SOURCE_GEOMETRY_GROUPS_WITH_CHILDREN
	)
	navigation_mesh.geometry_source_group_name = SOURCE_GROUP
	navigation_mesh.filter_baking_aabb = PLAZA_BOUNDS
	navigation_mesh.cell_size = 0.25
	navigation_mesh.cell_height = 0.1
	navigation_mesh.agent_radius = 0.5
	navigation_mesh.agent_height = 1.8
	# Degrau da fonte (0.18 m) e mureta não viram caminho: NPC anda sem física vertical.
	navigation_mesh.agent_max_climb = 0.1

	return navigation_mesh
