extends GutTest

const VOLUME_BUS_BY_SETTING: Dictionary[GameSettings.Setting, StringName] = {
	GameSettings.Setting.MASTER_VOLUME: &"Master",
	GameSettings.Setting.AMBIENT_VOLUME: &"Ambient",
	GameSettings.Setting.EFFECTS_VOLUME: &"Effects",
	GameSettings.Setting.MUSIC_VOLUME: &"Music",
}
const HALF_VOLUME: int = 50


func after_each() -> void:
	for setting in VOLUME_BUS_BY_SETTING:
		GameSettings.choose(setting, GameSettings.DEFAULT_OPTION[setting])


func test_every_volume_slider_moves_its_bus() -> void:
	for setting in VOLUME_BUS_BY_SETTING:
		var bus_index: int = AudioServer.get_bus_index(VOLUME_BUS_BY_SETTING[setting])

		GameSettings.choose(setting, HALF_VOLUME)

		assert_ne(bus_index, -1, "%s bus exists" % VOLUME_BUS_BY_SETTING[setting])
		assert_almost_eq(AudioServer.get_bus_volume_db(bus_index), linear_to_db(0.5), 0.01)


func test_volumes_are_sliders_from_zero_to_one_hundred() -> void:
	for setting in VOLUME_BUS_BY_SETTING:
		assert_true(GameSettings.is_slider(setting))
		assert_eq(GameSettings.option_range(setting), Vector2i(0, 100))
