from __future__ import annotations

import sys
import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CrowGame.map_system import (  # noqa: E402
    FIRST_MAP,
    MAP_DEFINITIONS,
    load_map_data,
    validate_map_network,
)


class MapSystemTests(unittest.TestCase):
    def test_first_map_and_all_backgrounds_exist(self) -> None:
        self.assertEqual("ruined_town_demo.json", FIRST_MAP)
        self.assertEqual(4, len(MAP_DEFINITIONS))
        for map_name in MAP_DEFINITIONS:
            map_data = load_map_data(map_name)
            self.assertTrue(map_data.background_path.exists())
            self.assertGreater(map_data.width, 0)
            self.assertGreater(map_data.height, 0)

    def test_every_transition_target_and_spawn_is_valid(self) -> None:
        self.assertEqual([], validate_map_network())

    def test_four_maps_are_bidirectionally_connected(self) -> None:
        expected_edges = {
            ("ruined_town_demo.json", "crow_map.json"),
            ("crow_map.json", "ruined_town_demo.json"),
            ("crow_map.json", "wolf_map.json"),
            ("wolf_map.json", "crow_map.json"),
            ("wolf_map.json", "bear_map.json"),
            ("bear_map.json", "wolf_map.json"),
        }
        actual_edges = {
            (map_name, transition.target_map)
            for map_name in MAP_DEFINITIONS
            for transition in load_map_data(map_name).transitions
            if transition.target_map is not None
        }
        self.assertTrue(expected_edges.issubset(actual_edges))

    def test_bear_map_has_game_ending_transition(self) -> None:
        bear_map = load_map_data("bear_map.json")
        self.assertTrue(any(transition.ends_game for transition in bear_map.transitions))

    def test_tiled_y_axis_is_converted_to_world_coordinates(self) -> None:
        town = load_map_data(FIRST_MAP)
        start_x, start_y = town.spawn("player_start")
        self.assertEqual(856.0, start_x)
        self.assertEqual(486.0, start_y)

    def test_crow_tile_layers_are_loaded_from_the_current_json(self) -> None:
        crow = load_map_data("crow_map.json")
        raw = json.loads(crow.source_path.read_text(encoding="utf-8"))
        expected = sum(
            value != 0
            for layer in raw["layers"]
            if layer["type"] == "tilelayer" and layer.get("visible", True)
            for value in layer["data"]
        )
        self.assertEqual(expected, len(crow.tiles))
        self.assertTrue(all(tile.sprite.image_path.exists() for tile in crow.tiles))

    def test_ruined_town_tiles_and_prop_objects_are_loaded(self) -> None:
        town = load_map_data("ruined_town_demo.json")
        self.assertEqual(381, len(town.tiles))
        self.assertEqual(68, len(town.object_tiles))
        self.assertTrue(
            all(tile.sprite.image_path.exists() for tile in town.object_tiles)
        )
        self.assertTrue(
            all("Downloads" not in str(tile.sprite.image_path) for tile in town.tiles)
        )

    def test_ruined_town_walls_and_solid_props_block_movement(self) -> None:
        town = load_map_data("ruined_town_demo.json")
        self.assertGreaterEqual(len(town.collisions), 70)

        start_x, start_y = town.spawn("player_start")
        self.assertEqual(
            (start_x, start_y),
            town.resolve_movement(start_x, start_y, 0.0, 60.0),
        )
        self.assertTrue(town._blocked(160.0, 320.0))  # car_wreck
        self.assertFalse(town._blocked(640.0, 400.0))  # open road

    def test_resources_and_events_are_loaded_from_json_with_images(self) -> None:
        expected_counts = {
            "crow_map.json": (86, 17),
            "wolf_map.json": (80, 20),
            "bear_map.json": (192, 13),
        }
        for map_name, (resource_count, event_count) in expected_counts.items():
            entities = load_map_data(map_name).entities
            self.assertEqual(resource_count, sum(entity.kind == "resource" for entity in entities))
            self.assertEqual(event_count, sum(entity.kind == "event" for entity in entities))
            self.assertTrue(all(entity.sprite_path.exists() for entity in entities))
            self.assertTrue(
                all(
                    entity.alternate_sprite_path is None
                    or entity.alternate_sprite_path.exists()
                    for entity in entities
                )
            )

    def test_resource_types_include_requested_harvestables(self) -> None:
        resource_types = {
            entity.entity_type
            for map_name in ("crow_map.json", "wolf_map.json", "bear_map.json")
            for entity in load_map_data(map_name).entities
            if entity.kind == "resource"
        }
        self.assertTrue({"tree", "rock", "grass", "fruit_tree"}.issubset(resource_types))


if __name__ == "__main__":
    unittest.main()
