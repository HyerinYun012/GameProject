from __future__ import annotations

import sys
import math
import unittest
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CrowGame.game_model import (  # noqa: E402
    CRAFTING_RECIPES,
    InventoryModel,
    ItemStack,
    SlotRef,
)
from CrowGame.main import (  # noqa: E402
    MAX_HP,
    MAX_SP,
    DragState,
    Game,
    GameUI,
    Player,
    WorldDrop,
    WorldEntity,
)
from CrowGame.map_system import FIRST_MAP, load_map_data  # noqa: E402


class FixedTargetUI:
    def __init__(self, target: SlotRef | None) -> None:
        self.target = target

    def slot_at(self, _x: float, _y: float, _inventory_open: bool) -> SlotRef | None:
        return self.target


def make_game() -> Game:
    game = Game.__new__(Game)
    game.model = InventoryModel()
    game.player = Player(sprite_sheet=None)
    game.inventory_open = True
    game.crafting_open = False
    game.drag = None
    game.toast = ""
    game.toast_error = False
    game.toast_timer = 0.0
    game.camera_zoom = 1.0
    game.map_data = load_map_data(FIRST_MAP)
    game.world_entities = {FIRST_MAP: []}
    game.world_drops = {FIRST_MAP: []}
    return game


def place_near_entity(game: Game, map_name: str, entity_type: str) -> WorldEntity:
    game.map_data = load_map_data(map_name)
    entities = [WorldEntity.create(definition) for definition in game.map_data.entities]
    game.world_entities = {map_name: entities}
    game.world_drops = {map_name: []}
    entity = next(item for item in entities if item.definition.entity_type == entity_type)
    rect = entity.definition.rect
    game.player.x = rect.left + rect.width / 2
    game.player.y = rect.bottom
    return entity


class GameActionTests(unittest.TestCase):
    def test_crafting_ui_has_thirteen_clickable_cards(self) -> None:
        ui = GameUI.__new__(GameUI)
        cards = ui.crafting_cards()
        self.assertEqual(13, len(cards))
        self.assertEqual(
            [recipe for recipe, _rect in cards],
            [ui.crafting_recipe_at(rect.cx, rect.cy) for _recipe, rect in cards],
        )

    def test_c_key_toggles_crafting_and_closes_inventory(self) -> None:
        import pico2d as p2

        game = make_game()
        game._key_down(SimpleNamespace(key=p2.SDLK_c, repeat=0))
        self.assertTrue(game.crafting_open)
        self.assertFalse(game.inventory_open)
        game._key_down(SimpleNamespace(key=p2.SDLK_c, repeat=0))
        self.assertFalse(game.crafting_open)

    def test_crafting_recipe_adds_item_to_inventory(self) -> None:
        game = make_game()
        game.model.add_item("wood", 1)
        game.model.add_item("fiber", 1)
        recipe = next(
            recipe for recipe in CRAFTING_RECIPES
            if recipe.output_item_id == "torch"
        )

        game._craft_recipe(recipe)

        self.assertEqual(1, game.model.item_count("torch"))
        self.assertEqual(0, game.model.item_count("wood"))
        self.assertEqual(0, game.model.item_count("fiber"))
        self.assertIn("제작 완료", game.toast)

    def test_player_starts_with_full_hp_and_sp(self) -> None:
        player = Player(sprite_sheet=None)
        self.assertEqual(MAX_HP, player.hp)
        self.assertEqual(MAX_SP, player.sp)

    def test_running_drains_sp_and_exhaustion_forces_walking(self) -> None:
        import pico2d as p2

        player = Player(sprite_sheet=None)
        resolver = lambda x, y, dx, dy: (x + dx, y + dy)
        run_keys = {p2.SDLK_d, p2.SDLK_LSHIFT}

        player.update(1.0, run_keys, resolver)
        self.assertEqual("run", player.state)
        self.assertEqual(75.0, player.sp)

        player.sp = 0.0
        player.stamina_exhausted = True
        player.update(0.5, run_keys, resolver)
        self.assertEqual("walk", player.state)
        self.assertEqual(9.0, player.sp)

        player.update(1.0, run_keys, resolver)
        self.assertEqual("walk", player.state)
        self.assertFalse(player.stamina_exhausted)
        player.update(0.1, run_keys, resolver)
        self.assertEqual("run", player.state)

    def test_idle_and_walking_recover_sp(self) -> None:
        player = Player(sprite_sheet=None)
        player.sp = 50.0
        player.update(1.0, set())
        self.assertEqual(68.0, player.sp)

    def test_enemy_damage_reduces_hp_and_zero_hp_causes_death(self) -> None:
        player = Player(sprite_sheet=None)
        self.assertEqual(25.0, player.take_damage(25.0))
        self.assertEqual(75.0, player.hp)
        self.assertEqual("hurt", player.state)

        player.take_damage(75.0)
        self.assertEqual(0.0, player.hp)
        self.assertTrue(player.dead)
        self.assertEqual("death", player.state)

        player.revive()
        self.assertEqual(MAX_HP, player.hp)
        self.assertFalse(player.dead)

    def test_each_tool_dispatches_to_the_expected_action(self) -> None:
        cases = {
            "wooden_axe": "axe",
            "stone_axe": "axe",
            "wooden_pickaxe": "mine",
            "stone_pickaxe": "mine",
            "fishing_rod": "fish",
            "wooden_sword": "attack",
            "stone_sword": "attack",
            "wooden_spear": "attack",
            "stone_spear": "attack",
        }
        game = make_game()
        for item_id, expected_state in cases.items():
            game.player.revive()
            game.model.tool_slot = ItemStack(item_id)
            game._use_tool()
            self.assertEqual(expected_state, game.player.state, item_id)

    def test_torch_is_selectable_without_starting_a_missing_animation(self) -> None:
        game = make_game()
        game.model.tool_slot = ItemStack("torch")
        game._use_tool()
        self.assertEqual("idle", game.player.state)
        self.assertIn("횃불", game.toast)

    def test_e_key_uses_the_equipped_tool(self) -> None:
        import pico2d as p2

        game = make_game()
        game.model.tool_slot = ItemStack("wooden_axe")
        game._key_down(SimpleNamespace(key=p2.SDLK_e, repeat=0))
        self.assertEqual("axe", game.player.state)
        self.assertIn("도끼질", game.toast)

    def test_mouse_drag_from_hotbar_moves_the_same_inventory_slot(self) -> None:
        game = make_game()
        game.model.slots[0] = ItemStack("wooden_axe")
        game.ui = FixedTargetUI(SlotRef.tool())
        game.drag = DragState(SlotRef.hotbar(0), "wooden_axe", 0, 0)
        game._finish_drag(10, 10)
        self.assertIsNone(game.model.slots[0])
        self.assertIsNone(game.model.hotbar[0])
        self.assertEqual("wooden_axe", game.model.tool_slot.item_id)

    def test_invalid_drag_to_tool_is_rejected_without_data_loss(self) -> None:
        game = make_game()
        stack = ItemStack("wood", 5)
        game.model.slots[0] = stack
        game.ui = FixedTargetUI(SlotRef.tool())
        game.drag = DragState(SlotRef.inventory(0), "wood", 0, 0)
        game._finish_drag(10, 10)
        self.assertIs(stack, game.model.slots[0])
        self.assertIsNone(game.model.tool_slot)
        self.assertTrue(game.toast_error)

    def test_dragging_outside_slots_creates_a_visible_world_drop(self) -> None:
        game = make_game()
        game.model.slots[0] = ItemStack("wooden_axe")
        game.ui = FixedTargetUI(None)
        game.map_data = load_map_data(FIRST_MAP)
        game.camera_x = game.map_data.width / 2
        game.camera_y = game.map_data.height / 2
        game.world_drops = {FIRST_MAP: []}
        game.drag = DragState(SlotRef.inventory(0), "wooden_axe", 0, 0)
        game._finish_drag(640, 360)
        self.assertIsNone(game.model.slots[0])
        self.assertEqual(1, len(game.world_drops[FIRST_MAP]))
        drop = game.world_drops[FIRST_MAP][0]
        self.assertEqual("wooden_axe", drop.stack.item_id)
        self.assertFalse(drop.pickup_enabled)
        self.assertTrue(drop.large_icon)
        self.assertEqual(game.player.x, drop.pickup_origin_x)
        self.assertEqual(game.player.y, drop.pickup_origin_y)
        distance = math.hypot(
            drop.x - game.player.x,
            drop.y - game.player.y,
        )
        self.assertGreaterEqual(distance, 80.0)
        self.assertLessEqual(distance, 130.0)

    def test_dropped_item_auto_collects_after_leaving_and_reapproaching(self) -> None:
        game = make_game()
        game.player.x = 300
        game.player.y = 300
        drop = WorldDrop(ItemStack("wood", 2), 300, 300, pickup_enabled=False)
        game.world_drops[FIRST_MAP] = [drop]

        game._auto_pickup_world_items()
        self.assertIsNone(game.model.slots[0])
        self.assertFalse(drop.pickup_enabled)

        game.player.x = 600
        game._auto_pickup_world_items()
        self.assertTrue(drop.pickup_enabled)
        self.assertEqual([drop], game.world_drops[FIRST_MAP])

        game.player.x = 300
        game._auto_pickup_world_items()
        self.assertEqual("wood", game.model.slots[0].item_id)
        self.assertEqual(2, game.model.slots[0].count)
        self.assertEqual([], game.world_drops[FIRST_MAP])

    def test_thrown_item_collects_when_player_walks_toward_it(self) -> None:
        game = make_game()
        game.player.x = 300
        game.player.y = 300
        drop = WorldDrop(
            ItemStack("wood", 1),
            430,
            300,
            pickup_enabled=False,
            large_icon=True,
            pickup_origin_x=300,
            pickup_origin_y=300,
        )
        game.world_drops[FIRST_MAP] = [drop]

        game.player.x = 330
        game._auto_pickup_world_items()

        self.assertEqual("wood", game.model.slots[0].item_id)
        self.assertEqual([], game.world_drops[FIRST_MAP])

    def test_resource_overflow_drop_auto_collects_on_approach(self) -> None:
        game = make_game()
        game.player.x = 250
        game.player.y = 250
        drop = WorldDrop(ItemStack("stone", 2), 250, 250)
        game.world_drops[FIRST_MAP] = [drop]
        game._auto_pickup_world_items()
        self.assertEqual("stone", game.model.slots[0].item_id)
        self.assertEqual([], game.world_drops[FIRST_MAP])

    def test_f_key_has_no_item_pickup_action(self) -> None:
        import pico2d as p2

        game = make_game()
        game.player.x = 250
        game.player.y = 250
        drop = WorldDrop(ItemStack("stone", 1), 250, 250)
        game.world_drops[FIRST_MAP] = [drop]

        game._key_down(SimpleNamespace(key=p2.SDLK_f, repeat=0))

        self.assertIsNone(game.model.slots[0])
        self.assertEqual([drop], game.world_drops[FIRST_MAP])

    def test_tree_requires_equipped_axe_and_disappears_after_three_hits(self) -> None:
        game = make_game()
        tree = place_near_entity(game, "crow_map.json", "tree")
        game._harvest_resource(tree)
        self.assertEqual(3, tree.hp)
        self.assertTrue(tree.visible)

        game.model.tool_slot = ItemStack("wooden_axe")
        for _ in range(3):
            game._harvest_resource(tree)
        self.assertFalse(tree.visible)
        self.assertEqual("wood", game.model.slots[0].item_id)
        self.assertEqual(2, game.model.slots[0].count)

    def test_rock_requires_pickaxe_not_axe(self) -> None:
        game = make_game()
        rock = place_near_entity(game, "wolf_map.json", "rock")
        game.model.tool_slot = ItemStack("stone_axe")
        game._harvest_resource(rock)
        self.assertEqual(3, rock.hp)
        game.model.tool_slot = ItemStack("wooden_pickaxe")
        for _ in range(3):
            game._harvest_resource(rock)
        self.assertFalse(rock.visible)
        self.assertEqual("stone", game.model.slots[0].item_id)

    def test_grass_harvests_with_e_without_a_tool(self) -> None:
        game = make_game()
        grass = place_near_entity(game, "crow_map.json", "grass")
        game._harvest_resource(grass)
        self.assertFalse(grass.visible)
        self.assertEqual("fiber", game.model.slots[0].item_id)

    def test_fruit_tree_stays_visible_and_uses_thirty_second_cooldown(self) -> None:
        game = make_game()
        fruit_tree = place_near_entity(game, "bear_map.json", "fruit_tree")
        game._harvest_resource(fruit_tree)
        self.assertTrue(fruit_tree.visible)
        self.assertTrue(fruit_tree.completed)
        self.assertEqual(30.0, fruit_tree.cooldown_remaining)
        self.assertEqual("fruit", game.model.slots[0].item_id)
        self.assertEqual("apple.png", game.model.slots[0].definition.icon_filename)
        self.assertEqual("사과", game.model.slots[0].definition.label)
        self.assertEqual(3, game.model.slots[0].count)
        game._harvest_resource(fruit_tree)
        self.assertEqual(3, game.model.slots[0].count)

    def test_event_with_after_sprite_changes_instead_of_disappearing(self) -> None:
        game = make_game()
        wolf_den = place_near_entity(game, "wolf_map.json", "wolf_den_repair")
        game._activate_event(wolf_den)
        self.assertFalse(wolf_den.completed)
        game.model.tool_slot = ItemStack("stone_pickaxe")
        game._activate_event(wolf_den)
        self.assertTrue(wolf_den.completed)
        self.assertTrue(wolf_den.visible)
        self.assertEqual(wolf_den.definition.alternate_sprite_path, wolf_den.sprite_path)

    def test_one_shot_event_without_after_sprite_disappears(self) -> None:
        game = make_game()
        trap = place_near_entity(game, "wolf_map.json", "hunter_trap_remove")
        game._activate_event(trap)
        self.assertTrue(trap.completed)
        self.assertFalse(trap.visible)


if __name__ == "__main__":
    unittest.main()
