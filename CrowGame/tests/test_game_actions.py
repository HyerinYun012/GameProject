from __future__ import annotations

import sys
import math
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


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
    AWARENESS_ICON_PATHS,
    AWARENESS_ICON_SCREEN_SIZE,
    AI_SENSES,
    ANIMAL_ANIMATIONS,
    ANIMAL_STATS,
    CONFLICT_ENDING_CUTSCENE_PATHS,
    CUTSCENE_FADE_SECONDS,
    CUTSCENE_HOLD_SECONDS,
    FISHING_CAPTURE_LOSS_PER_SECOND,
    FISHING_CAPTURE_PER_SECOND,
    FISHING_DANGER_HOLD_SECONDS,
    FISHING_DANGER_TENSION_MAX,
    FISHING_DANGER_TENSION_MIN,
    FISHING_REACTION_SECONDS,
    FISHING_SAFE_TENSION_MAX,
    FISHING_SAFE_TENSION_MIN,
    FISHING_TENSION_FALL_PER_SECOND,
    FISHING_TENSION_RISE_PER_SECOND,
    GAME_START_MINUTES,
    GAME_TITLE,
    INTRO_CUTSCENE_PATHS,
    LOBBY_BACKGROUND_PATH,
    LOBBY_BUTTON_PATH,
    LOBBY_FADE_SECONDS,
    MAX_HP,
    MAX_SP,
    NIGHT_SP_RECOVERY_MULTIPLIER,
    NIGHT_MASK_PATHS,
    NIGHT_MASK_SIZE,
    NIGHT_VISION_RADIUS,
    PROJECTILE_DAMAGE,
    RECONCILIATION_ENDING_CUTSCENE_PATHS,
    TORCH_VISION_RADIUS,
    WINDOW_HEIGHT,
    WORLD_TILE_SIZE,
    DragState,
    EnemyAI,
    Game,
    GameUI,
    Player,
    PlacedUtility,
    Rect,
    WorldDrop,
    WorldEntity,
    affinity_relationship,
    desired_map_species,
    format_game_time,
    game_time_period,
    night_darkness_progress,
    stamina_recovery_multiplier,
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
    game.running = True
    game.game_over = False
    game.game_paused = False
    game.pressed = set()
    game.ending_timer = 0.0
    game.cutscene_sequence = ()
    game.cutscene_kind = ""
    game.cutscene_index = 0
    game.cutscene_elapsed = 0.0
    game.cutscene_fast_forward = False
    game.cutscene_paused = False
    game.world_fade_remaining = 0.0
    game.lobby_active = False
    game.lobby_transition = ""
    game.lobby_transition_elapsed = 0.0
    game.game_minutes = GAME_START_MINUTES
    game.sleep_bedding = None
    game.sleep_minutes_remaining = 0.0
    game.fishing_state = "idle"
    game.fishing_bite_timer = 0.0
    game.fishing_reaction_timer = 0.0
    game.fishing_tension = 0.0
    game.fishing_capture = 0.0
    game.fishing_danger_timer = 0.0
    game.fishing_reeling = False
    game.active_fishing_spot = None
    game.fishing_direction = None
    game.fishing_origin = None
    game.camera_zoom = 1.0
    game.map_data = load_map_data(FIRST_MAP)
    game.camera_x = game.player.x
    game.camera_y = game.player.y
    game.mouse_screen_x = 640.0
    game.mouse_screen_y = 360.0
    game.world_entities = {FIRST_MAP: []}
    game.world_drops = {FIRST_MAP: []}
    game.placed_utilities = {FIRST_MAP: []}
    game.enemies = {FIRST_MAP: []}
    game.projectiles = {FIRST_MAP: []}
    game.species_affinity = {"crow": 0, "wolf": 0, "bear": 0}
    game.ending_variant = ""
    return game


def place_near_entity(game: Game, map_name: str, entity_type: str) -> WorldEntity:
    game.map_data = load_map_data(map_name)
    entities = [WorldEntity.create(definition) for definition in game.map_data.entities]
    game.world_entities = {map_name: entities}
    game.world_drops = {map_name: []}
    game.placed_utilities = {map_name: []}
    entity = next(item for item in entities if item.definition.entity_type == entity_type)
    rect = entity.definition.rect
    game.player.x = rect.left + rect.width / 2
    game.player.y = rect.bottom
    return entity


def prepare_fishing_game() -> Game:
    game = make_game()
    map_name = "crow_map.json"
    game.map_data = load_map_data(map_name)
    game.world_entities.setdefault(map_name, [])
    game.world_drops.setdefault(map_name, [])
    game.placed_utilities.setdefault(map_name, [])
    game.enemies.setdefault(map_name, [])
    game.projectiles.setdefault(map_name, [])
    spot = game.map_data.fishing_spots[0]
    game.player.x = spot.left + spot.width / 2.0
    game.player.y = spot.bottom + spot.height / 2.0
    game.camera_x = game.player.x
    game.camera_y = game.player.y
    game.model.tool_slot = ItemStack("fishing_rod")
    return game


class GameActionTests(unittest.TestCase):
    def test_clock_formats_wraps_and_advances_at_the_design_rate(self) -> None:
        game = make_game()

        self.assertEqual("08:00", format_game_time(game.game_minutes))
        game._advance_game_clock(30.0)
        self.assertEqual("09:00", format_game_time(game.game_minutes))

        game.game_minutes = 23 * 60 + 59
        game._advance_game_clock(0.5)
        self.assertEqual("12:00", format_game_time(game.game_minutes))

    def test_dusk_night_and_dawn_darkness_are_continuous(self) -> None:
        self.assertEqual("오전", game_time_period(8 * 60))
        self.assertEqual("오후", game_time_period(18 * 60))
        self.assertEqual("12:00", format_game_time(12 * 60))
        self.assertEqual("09:00", format_game_time(21 * 60))
        self.assertEqual(0.0, night_darkness_progress(17 * 60))
        self.assertAlmostEqual(0.5, night_darkness_progress(18.5 * 60))
        self.assertEqual(1.0, night_darkness_progress(20 * 60))
        self.assertAlmostEqual(0.5, night_darkness_progress(6 * 60))
        self.assertEqual(0.0, night_darkness_progress(7 * 60))

    def test_holding_torch_automatically_expands_night_vision(self) -> None:
        game = make_game()

        self.assertEqual(NIGHT_VISION_RADIUS, game._night_vision_radius())
        game.model.tool_slot = ItemStack("torch")
        self.assertEqual(TORCH_VISION_RADIUS, game._night_vision_radius())

    def test_night_masks_are_smooth_full_size_rgba_assets(self) -> None:
        for path in NIGHT_MASK_PATHS.values():
            data = path.read_bytes()
            self.assertEqual(b"\x89PNG\r\n\x1a\n", data[:8])
            self.assertEqual(NIGHT_MASK_SIZE, int.from_bytes(data[16:20], "big"))
            self.assertEqual(NIGHT_MASK_SIZE, int.from_bytes(data[20:24], "big"))
            self.assertEqual(6, data[25])  # PNG RGBA colour type.

    def test_campfire_and_bedding_install_and_return_to_inventory(self) -> None:
        for item_id in ("campfire", "travel_bedding"):
            game = make_game()
            game.model.tool_slot = ItemStack(item_id)
            game._utility_placement_position = lambda _item_id: (500.0, 400.0)

            self.assertTrue(game._interact_world())

            self.assertIsNone(game.model.tool_slot)
            self.assertEqual(
                [PlacedUtility(item_id, 500.0, 400.0)],
                game.placed_utilities[FIRST_MAP],
            )

            game.player.x = 500.0
            game.player.y = 400.0
            self.assertTrue(game._interact_world())
            self.assertEqual(1, game.model.item_count(item_id))
            self.assertEqual([], game.placed_utilities[FIRST_MAP])

    def test_bedding_click_sleeps_from_five_pm_until_eight_am(self) -> None:
        game = make_game()
        origin = (game.player.x, game.player.y)
        other_bedding = PlacedUtility(
            "travel_bedding", game.player.x - 50.0, game.player.y
        )
        bedding = PlacedUtility(
            "travel_bedding", game.player.x + 80.0, game.player.y
        )
        game.placed_utilities[FIRST_MAP] = [bedding, other_bedding]
        click_x, click_y = game.world_to_screen(bedding.x, bedding.y)
        game.game_minutes = 17 * 60
        game.show_toast("이전 알림")

        self.assertTrue(game._try_sleep_at_screen(click_x, click_y))
        self.assertTrue(game.sleeping)
        self.assertIs(bedding, game.sleep_bedding)
        self.assertEqual("", game.toast)
        self.assertEqual(15 * 60, game.sleep_minutes_remaining)

        game._update_sleep(3.75)

        self.assertFalse(game.sleeping)
        self.assertEqual([bedding, other_bedding], game.placed_utilities[FIRST_MAP])
        self.assertEqual(origin, (game.player.x, game.player.y))
        self.assertEqual(8 * 60, game.game_minutes)
        self.assertEqual("푹 자고 일어났습니다 · 오전 08:00", game.toast)

    def test_bedding_click_before_five_pm_does_not_start_sleep(self) -> None:
        game = make_game()
        bedding = PlacedUtility(
            "travel_bedding", game.player.x + 80.0, game.player.y
        )
        game.placed_utilities[FIRST_MAP] = [bedding]
        click_x, click_y = game.world_to_screen(bedding.x, bedding.y)
        game.game_minutes = 16 * 60 + 59

        self.assertTrue(game._try_sleep_at_screen(click_x, click_y))
        self.assertFalse(game.sleeping)
        self.assertTrue(game.toast_error)

    def test_clicking_campfire_does_not_consume_primary_attack(self) -> None:
        game = make_game()
        campfire = PlacedUtility("campfire", game.player.x + 80.0, game.player.y)
        game.placed_utilities[FIRST_MAP] = [campfire]
        click_x, click_y = game.world_to_screen(campfire.x, campfire.y)

        self.assertFalse(game._try_sleep_at_screen(click_x, click_y))

    def test_installables_find_open_space_near_the_town_spawn(self) -> None:
        game = make_game()
        game.camera_zoom = 0.5
        game.player.x, game.player.y = game.map_data.spawn("player_start")
        game.player.direction = "down"

        for item_id in ("campfire", "travel_bedding"):
            self.assertIsNotNone(game._utility_placement_position(item_id))

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

    def test_night_stamina_recovery_is_thirty_percent_slower(self) -> None:
        self.assertEqual(1.0, stamina_recovery_multiplier(19 * 60 + 59))
        self.assertEqual(
            NIGHT_SP_RECOVERY_MULTIPLIER,
            stamina_recovery_multiplier(20 * 60),
        )
        self.assertEqual(
            NIGHT_SP_RECOVERY_MULTIPLIER,
            stamina_recovery_multiplier(4 * 60 + 59),
        )
        self.assertEqual(1.0, stamina_recovery_multiplier(5 * 60))

        player = Player(sprite_sheet=None)
        player.sp = 50.0
        player.update(1.0, set(), None, NIGHT_SP_RECOVERY_MULTIPLIER)
        self.assertAlmostEqual(62.6, player.sp)

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

    def test_fatal_damage_enters_game_over_and_clears_active_input(self) -> None:
        import pico2d as p2

        game = make_game()
        game.inventory_open = True
        game.crafting_open = True
        game.pressed = {p2.SDLK_w, p2.SDLK_LSHIFT}

        self.assertEqual(MAX_HP, game.damage_player(MAX_HP))

        self.assertTrue(game.game_over)
        self.assertTrue(game.player.dead)
        self.assertEqual(set(), game.pressed)
        self.assertFalse(game.inventory_open)
        self.assertFalse(game.crafting_open)

    def test_restart_restores_every_mutable_gameplay_collection(self) -> None:
        game = make_game()
        game._player_sprite_sheet = None
        game._map_cache = {}
        game._background_cache = {}
        game.ui = SimpleNamespace(model=game.model)
        initial_fruit = InventoryModel.demo().item_count("fruit")

        game.model.add_item("fruit", 7)
        game.player.take_damage(game.player.hp)
        game.world_drops["old_map.json"] = [
            WorldDrop(ItemStack("stone"), 10.0, 20.0)
        ]
        game.placed_utilities["old_map.json"] = [
            PlacedUtility("campfire", 30.0, 40.0)
        ]
        game.enemies["old_map.json"] = [EnemyAI.create("bear", 50.0, 60.0)]
        game.projectiles["old_map.json"] = []
        game.species_affinity = {"crow": 100, "wolf": 80, "bear": 40}
        game.ending_variant = "대립 엔딩"
        game.game_over = True
        game.sleep_bedding = PlacedUtility("travel_bedding", 30.0, 40.0)
        game.sleep_minutes_remaining = 123.0
        game.fishing_state = "minigame"
        game.fishing_capture = 72.0
        game.fishing_tension = 55.0
        game.fishing_direction = "left"
        game.fishing_origin = (100.0, 200.0)

        game.restart_game()

        self.assertIs(game.ui.model, game.model)
        self.assertEqual(initial_fruit, game.model.item_count("fruit"))
        self.assertEqual(MAX_HP, game.player.hp)
        self.assertEqual(MAX_SP, game.player.sp)
        self.assertFalse(game.player.dead)
        self.assertFalse(game.game_over)
        self.assertEqual(FIRST_MAP, game.map_data.name)
        self.assertNotIn("old_map.json", game.world_drops)
        self.assertNotIn("old_map.json", game.placed_utilities)
        self.assertNotIn("old_map.json", game.enemies)
        self.assertNotIn("old_map.json", game.projectiles)
        self.assertEqual({"crow": 0, "wolf": 0, "bear": 0}, game.species_affinity)
        self.assertEqual("", game.ending_variant)
        self.assertEqual(GAME_START_MINUTES, game.game_minutes)
        self.assertFalse(game.sleeping)
        self.assertEqual(0.0, game.sleep_minutes_remaining)
        self.assertEqual("idle", game.fishing_state)
        self.assertEqual(0.0, game.fishing_capture)
        self.assertEqual(0.0, game.fishing_tension)
        self.assertIsNone(game.fishing_direction)
        self.assertIsNone(game.fishing_origin)
        self.assertFalse(game.cutscene_active)
        self.assertFalse(game.lobby_active)
        self.assertEqual(LOBBY_FADE_SECONDS, game.world_fade_remaining)

    def test_game_over_buttons_retry_or_return_to_lobby(self) -> None:
        game = make_game()
        restarted: list[bool] = []
        game.restart_game = lambda: restarted.append(True)

        self.assertTrue(
            game._activate_game_over_button(
                game.RETRY_BUTTON.cx, game.RETRY_BUTTON.cy
            )
        )
        self.assertEqual([True], restarted)

        self.assertTrue(
            game._activate_game_over_button(
                game.RETURN_TO_LOBBY_BUTTON.cx, game.RETURN_TO_LOBBY_BUTTON.cy
            )
        )
        self.assertTrue(game.running)
        self.assertTrue(game.lobby_active)

    def test_player_healing_is_capped_at_max_hp(self) -> None:
        player = Player(sprite_sheet=None)
        player.hp = 97.0
        self.assertEqual(3.0, player.restore_hp(5.0))
        self.assertEqual(MAX_HP, player.hp)

    def test_equipped_apple_consumes_one_and_heals_five(self) -> None:
        game = make_game()
        game.player.hp = 90.0
        game.model.tool_slot = ItemStack("fruit", 2)

        game._use_equipped_with_e()

        self.assertEqual(95.0, game.player.hp)
        self.assertEqual(1, game.model.tool_slot.count)
        self.assertIn("HP +5", game.toast)

        game._use_equipped_with_e()
        self.assertEqual(100.0, game.player.hp)
        self.assertIsNone(game.model.tool_slot)

    def test_dead_player_does_not_consume_equipped_apple(self) -> None:
        game = make_game()
        game.player.take_damage(game.player.hp)
        game.model.tool_slot = ItemStack("fruit", 2)

        game._use_equipped_with_e()

        self.assertEqual(0.0, game.player.hp)
        self.assertEqual(2, game.model.tool_slot.count)
        self.assertIn("먹을 수 없습니다", game.toast)

    def test_crow_animation_uses_asset_flight_timing(self) -> None:
        self.assertEqual((4, 8.0, True), ANIMAL_ANIMATIONS["crow"]["idle"])
        self.assertEqual((6, 14.0, True), ANIMAL_ANIMATIONS["crow"]["walk"])
        self.assertEqual((6, 10.0, False), ANIMAL_ANIMATIONS["crow"]["death"])

    def test_awareness_states_use_large_dedicated_icon_assets(self) -> None:
        self.assertEqual(
            AWARENESS_ICON_PATHS["suspicious"],
            AWARENESS_ICON_PATHS["searching"],
        )
        self.assertNotEqual(
            AWARENESS_ICON_PATHS["suspicious"],
            AWARENESS_ICON_PATHS["alerted"],
        )
        self.assertGreaterEqual(AWARENESS_ICON_SCREEN_SIZE, 56.0)
        for path in set(AWARENESS_ICON_PATHS.values()):
            self.assertTrue(path.exists(), path)

        crow = EnemyAI.create("crow", 0.0, 0.0)
        crow._set_state("walk")
        crow._advance_animation(1.0 / 14.0)
        self.assertEqual(1, crow.frame_index)

    def test_crow_patrol_and_flight_clock_advance_without_stop_start_jitter(self) -> None:
        open_map = SimpleNamespace(
            resolve_movement=lambda x, y, dx, dy: (x + dx, y + dy)
        )
        player = Player(sprite_sheet=None)
        player.x = 5000.0
        player.y = 5000.0
        crow = EnemyAI.create("crow", 500.0, 500.0)
        positions = []
        states = []

        for _ in range(360):
            crow.update(1.0 / 60.0, open_map, player, 100, 1.0)
            positions.append((crow.x, crow.y))
            states.append(crow.state)

        self.assertEqual(360, len(set(positions)))
        self.assertEqual({"walk"}, set(states))
        self.assertAlmostEqual(6.0, crow.flight_clock, places=5)

    def test_flying_crow_does_not_get_stuck_on_ground_collisions(self) -> None:
        blocked_map = SimpleNamespace(
            resolve_movement=lambda x, y, _dx, _dy: (x, y)
        )
        crow = EnemyAI.create("crow", 0.0, 0.0)
        wolf = EnemyAI.create("wolf", 0.0, 0.0)

        crow._move_toward(100.0, 0.0, 0.1, blocked_map)
        wolf._move_toward(100.0, 0.0, 0.1, blocked_map)

        self.assertGreater(crow.x, 0.0)
        self.assertEqual("walk", crow.state)
        self.assertEqual(0.0, wolf.x)
        self.assertEqual("idle", wolf.state)

    def test_each_tool_dispatches_to_the_expected_action(self) -> None:
        cases = {
            "wooden_axe": "axe",
            "stone_axe": "axe",
            "wooden_pickaxe": "mine",
            "stone_pickaxe": "mine",
            "fishing_rod": "idle",
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

    def test_e_key_eats_one_equipped_apple(self) -> None:
        import pico2d as p2

        game = make_game()
        game.player.hp = 80.0
        game.model.tool_slot = ItemStack("fruit", 3)

        game._key_down(SimpleNamespace(key=p2.SDLK_e, repeat=0))

        self.assertEqual(85.0, game.player.hp)
        self.assertEqual(2, game.model.tool_slot.count)

    def test_e_key_does_not_trigger_unarmed_attack_with_empty_tool_bar(self) -> None:
        import pico2d as p2

        game = make_game()
        enemy = EnemyAI.create("wolf", game.player.x + 50.0, game.player.y)
        game.enemies[FIRST_MAP] = [enemy]

        game._key_down(SimpleNamespace(key=p2.SDLK_e, repeat=0))

        self.assertEqual(enemy.max_hp, enemy.hp)
        self.assertEqual("idle", game.player.state)

    def test_space_key_has_no_gameplay_action(self) -> None:
        import pico2d as p2

        game = make_game()
        enemy = EnemyAI.create("wolf", game.player.x + 50.0, game.player.y)
        game.enemies[FIRST_MAP] = [enemy]
        game.model.tool_slot = ItemStack("wooden_sword")

        game._key_down(SimpleNamespace(key=p2.SDLK_SPACE, repeat=0))

        self.assertEqual(enemy.max_hp, enemy.hp)
        self.assertEqual("idle", game.player.state)

    def test_e_key_still_performs_equipped_sword_attack(self) -> None:
        import pico2d as p2

        game = make_game()
        game.player.direction = "right"
        enemy = EnemyAI.create("wolf", game.player.x + 50.0, game.player.y)
        game.enemies[FIRST_MAP] = [enemy]
        game.model.tool_slot = ItemStack("wooden_sword")

        game._key_down(SimpleNamespace(key=p2.SDLK_e, repeat=0))

        self.assertEqual(enemy.max_hp - 10, enemy.hp)
        self.assertEqual("attack", game.player.state)
        self.assertIn("근접 명중", game.toast)

    def test_mouse_drag_from_hotbar_moves_the_same_inventory_slot(self) -> None:
        game = make_game()
        game.model.slots[0] = ItemStack("wooden_axe")
        game.ui = FixedTargetUI(SlotRef.tool())
        game.drag = DragState(SlotRef.hotbar(0), "wooden_axe", 0, 0)
        game._finish_drag(10, 10)
        self.assertIsNone(game.model.slots[0])
        self.assertIsNone(game.model.hotbar[0])
        self.assertEqual("wooden_axe", game.model.tool_slot.item_id)

    def test_material_drag_to_tool_slot_is_accepted(self) -> None:
        game = make_game()
        stack = ItemStack("wood", 5)
        game.model.slots[0] = stack
        game.ui = FixedTargetUI(SlotRef.tool())
        game.drag = DragState(SlotRef.inventory(0), "wood", 0, 0)
        game._finish_drag(10, 10)
        self.assertIsNone(game.model.slots[0])
        self.assertIs(stack, game.model.tool_slot)
        self.assertFalse(game.toast_error)

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
        game._harvest_resource(tree)
        self.assertEqual(20, game.model.tool_slot.durability)
        for _ in range(2):
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
        game._harvest_resource(rock)
        self.assertEqual(20, game.model.tool_slot.durability)
        for _ in range(2):
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
        self.assertEqual("fruit_tree_unripe.png", fruit_tree.sprite_path.name)
        self.assertTrue(fruit_tree.sprite_path.exists())
        game._harvest_resource(fruit_tree)
        self.assertEqual(3, game.model.slots[0].count)

        game._update_entity_timers(30.0)

        self.assertEqual(0.0, fruit_tree.cooldown_remaining)
        self.assertFalse(fruit_tree.completed)
        self.assertEqual(
            fruit_tree.definition.sprite_path,
            fruit_tree.sprite_path,
        )

    def test_mouse_aim_sets_throw_direction(self) -> None:
        game = make_game()
        game.model.tool_slot = ItemStack("stone", 2)

        game._aim_at_screen(1000.0, 360.0)
        self.assertEqual("right", game.player.direction)
        game._aim_at_screen(640.0, 650.0)
        self.assertEqual("up", game.player.direction)

    def test_thrown_spear_flies_into_ai_and_causes_hurt(self) -> None:
        game = make_game()
        game.species_affinity["wolf"] = 60
        game.player.x = 300.0
        game.player.y = 300.0
        game.camera_x = game.player.x
        game.camera_y = game.player.y
        enemy = EnemyAI.create("wolf", 560.0, 300.0)
        game.enemies[FIRST_MAP] = [enemy]
        game.model.tool_slot = ItemStack("wooden_spear")
        target_screen = game.world_to_screen(*enemy.hit_center)

        self.assertTrue(game._throw_equipped_at_screen(*target_screen))
        self.assertIsNone(game.model.tool_slot)
        self.assertEqual("attack", game.player.state)
        self.assertEqual(1, len(game.projectiles[FIRST_MAP]))

        for _ in range(12):
            game._update_projectiles(0.05)
            if not game.projectiles[FIRST_MAP]:
                break

        self.assertEqual(55, enemy.hp)
        self.assertEqual("hurt", enemy.state)
        self.assertEqual([], game.projectiles[FIRST_MAP])
        self.assertEqual("wooden_spear", game.world_drops[FIRST_MAP][0].stack.item_id)
        self.assertEqual(9, game.world_drops[FIRST_MAP][0].stack.durability)
        self.assertFalse(game.world_drops[FIRST_MAP][0].pickup_enabled)
        self.assertEqual(55, game.species_affinity["wolf"])

    def test_throwing_one_stone_keeps_the_rest_equipped(self) -> None:
        game = make_game()
        game.model.tool_slot = ItemStack("stone", 3)

        self.assertTrue(game._throw_equipped_at_screen(1000.0, 360.0))

        self.assertEqual(2, game.model.tool_slot.count)
        self.assertEqual("stone", game.projectiles[FIRST_MAP][0].item_id)

    def test_projectile_that_misses_ai_does_not_deal_damage(self) -> None:
        game = make_game()
        enemy = EnemyAI.create("wolf", 560.0, 600.0)
        game.enemies[FIRST_MAP] = [enemy]
        game.model.tool_slot = ItemStack("wooden_spear")

        self.assertTrue(game._throw_equipped_at_screen(1000.0, 360.0))
        for _ in range(20):
            game._update_projectiles(0.05)
            if not game.projectiles[FIRST_MAP]:
                break

        self.assertEqual(enemy.max_hp, enemy.hp)
        self.assertEqual("idle", enemy.state)
        self.assertEqual(9, game.world_drops[FIRST_MAP][0].stack.durability)

    def test_event_with_after_sprite_changes_instead_of_disappearing(self) -> None:
        game = make_game()
        game.species_affinity["wolf"] = 95
        wolf_den = place_near_entity(game, "wolf_map.json", "wolf_den_repair")
        game._activate_event(wolf_den)
        self.assertFalse(wolf_den.completed)
        game.model.tool_slot = ItemStack("stone_pickaxe")
        game._activate_event(wolf_den)
        self.assertTrue(wolf_den.completed)
        self.assertTrue(wolf_den.visible)
        self.assertEqual(wolf_den.definition.alternate_sprite_path, wolf_den.sprite_path)
        self.assertTrue(wolf_den.reward_claimed)
        self.assertEqual(100, game.species_affinity["wolf"])

    def test_one_shot_event_without_after_sprite_disappears(self) -> None:
        game = make_game()
        trap = place_near_entity(game, "wolf_map.json", "hunter_trap_remove")
        game._activate_event(trap)
        self.assertTrue(trap.completed)
        self.assertFalse(trap.visible)
        self.assertEqual(5, game.species_affinity["wolf"])
        game._activate_event(trap)
        self.assertEqual(5, game.species_affinity["wolf"])

    def test_generator_reward_is_claimed_only_once(self) -> None:
        game = make_game()
        generator = place_near_entity(game, "crow_map.json", "generator_switch")

        game._activate_event(generator)
        self.assertEqual(10, game.species_affinity["crow"])
        self.assertTrue(generator.reward_claimed)
        game._activate_event(generator)
        self.assertEqual(10, game.species_affinity["crow"])

    def test_affinity_relationship_thresholds(self) -> None:
        self.assertEqual("hostile", affinity_relationship(0))
        self.assertEqual("hostile", affinity_relationship(39))
        self.assertEqual("wary", affinity_relationship(40))
        self.assertEqual("wary", affinity_relationship(79))
        self.assertEqual("near_friendly", affinity_relationship(80))
        self.assertEqual("near_friendly", affinity_relationship(99))
        self.assertEqual("reconciled", affinity_relationship(100))

    def test_unreconciled_species_follow_into_later_maps(self) -> None:
        affinity = {"crow": 0, "wolf": 0, "bear": 0}
        self.assertEqual(
            ("crow",), desired_map_species("crow_map.json", affinity)
        )
        self.assertEqual(
            ("wolf", "crow"), desired_map_species("wolf_map.json", affinity)
        )
        self.assertEqual(
            ("bear", "crow", "wolf"),
            desired_map_species("bear_map.json", affinity),
        )

        affinity["crow"] = 100
        self.assertEqual(
            ("wolf",), desired_map_species("wolf_map.json", affinity)
        )
        self.assertEqual(
            ("bear", "wolf"), desired_map_species("bear_map.json", affinity)
        )

        affinity["wolf"] = 100
        self.assertEqual(
            ("bear",), desired_map_species("bear_map.json", affinity)
        )

    def test_map_enemy_sync_adds_and_removes_following_species(self) -> None:
        game = make_game()
        wolf_map = load_map_data("wolf_map.json")
        native_wolf = EnemyAI.create("wolf", 500.0, 500.0)
        following_crow = EnemyAI.create("crow", 600.0, 500.0)
        game.enemies[wolf_map.name] = [native_wolf, following_crow]

        game._sync_map_enemies(wolf_map, ("wolf",))
        self.assertEqual(["wolf"], [enemy.animal for enemy in game.enemies[wolf_map.name]])
        self.assertIs(native_wolf, game.enemies[wolf_map.name][0])

        game._sync_map_enemies(wolf_map, ("wolf", "crow"))
        self.assertEqual(
            ["wolf", "crow"],
            [enemy.animal for enemy in game.enemies[wolf_map.name]],
        )

    def test_affinity_80_to_99_detects_but_never_attacks_first(self) -> None:
        game = make_game()
        game.player.x = 500.0
        game.player.y = 500.0
        passive_enemy = EnemyAI.create("crow", 535.0, 500.0)
        hostile_enemy = EnemyAI.create("crow", 535.0, 500.0)
        reconciled_enemy = EnemyAI.create("crow", 535.0, 500.0)
        passive_enemy.direction_row = 6
        hostile_enemy.direction_row = 6
        reconciled_enemy.direction_row = 6

        passive_damage = 0.0
        hostile_damage = 0.0
        for _ in range(30):
            passive_damage += passive_enemy.update(
                0.1, game.map_data, game.player, 99, game.camera_zoom
            )
            hostile_damage += hostile_enemy.update(
                0.1, game.map_data, game.player, 79, game.camera_zoom
            )
        reconciled_damage = sum(
            reconciled_enemy.update(
                0.1, game.map_data, game.player, 100, game.camera_zoom
            )
            for _ in range(20)
        )

        self.assertEqual("alerted", passive_enemy.awareness)
        self.assertEqual(0.0, passive_damage)
        self.assertGreater(hostile_damage, 0.0)
        self.assertEqual(0.0, reconciled_damage)

    def test_affinity_80_to_99_can_retaliate_after_player_attacks(self) -> None:
        game = make_game()
        game.player.x = 500.0
        game.player.y = 500.0
        crow = EnemyAI.create("crow", 535.0, 500.0)
        crow.take_damage(1)
        crow.receive_alert(game.player.x, game.player.y)

        damage = 0.0
        for _ in range(40):
            damage += crow.update(
                0.1, game.map_data, game.player, 94, game.camera_zoom
            )

        self.assertGreater(damage, 0.0)

    def test_detection_uses_distance_angle_and_confirmation_time(self) -> None:
        game = make_game()
        game.player.x = 500.0 + 5.0 * WORLD_TILE_SIZE
        game.player.y = 500.0
        wolf = EnemyAI.create("wolf", 500.0, 500.0)
        wolf.direction_row = 2

        wolf.update(0.3, game.map_data, game.player, 20, 1.0)
        self.assertEqual("suspicious", wolf.awareness)
        wolf.update(0.21, game.map_data, game.player, 20, 1.0)
        self.assertEqual("alerted", wolf.awareness)

        behind = EnemyAI.create("wolf", 500.0, 500.0)
        behind.direction_row = 6
        behind.update(1.0, game.map_data, game.player, 20, 1.0)
        self.assertNotEqual("alerted", behind.awareness)

    def test_leaving_view_before_confirmation_cancels_suspicion(self) -> None:
        game = make_game()
        crow = EnemyAI.create("crow", 500.0, 500.0)
        crow.direction_row = 2
        game.player.x = 700.0
        game.player.y = 500.0

        crow.update(0.4, game.map_data, game.player, 20, 1.0)
        self.assertEqual("suspicious", crow.awareness)
        game.player.x = -1000.0
        crow.update(0.21, game.map_data, game.player, 20, 1.0)
        self.assertEqual("unaware", crow.awareness)

    def test_lost_target_searches_around_last_known_position(self) -> None:
        open_map = SimpleNamespace(
            resolve_movement=lambda x, y, dx, dy: (x + dx, y + dy)
        )
        game = make_game()
        game.player.x = 3000.0
        game.player.y = 3000.0
        wolf = EnemyAI.create("wolf", 500.0, 500.0)
        wolf.receive_alert(500.0, 500.0)

        wolf.update(0.1, open_map, game.player, 20, 1.0)
        self.assertEqual("searching", wolf.awareness)
        wolf.update(0.1, open_map, game.player, 20, 1.0)

        self.assertEqual("searching", wolf.awareness)
        self.assertGreater(math.hypot(wolf.x - 500.0, wolf.y - 500.0), 0.0)
        self.assertEqual(3.0, AI_SENSES["wolf"]["search_tiles"])

    def test_crow_alert_shares_last_position_only_inside_ten_tiles(self) -> None:
        game = make_game()
        game.map_data = SimpleNamespace(
            name=FIRST_MAP,
            resolve_movement=lambda x, y, dx, dy: (x + dx, y + dy),
        )
        game.player.x = 600.0
        game.player.y = 500.0
        crow = EnemyAI.create("crow", 500.0, 500.0)
        nearby_wolf = EnemyAI.create("wolf", 500.0, 900.0)
        distant_wolf = EnemyAI.create(
            "wolf", 500.0 + 12.0 * WORLD_TILE_SIZE, 500.0
        )
        crow.direction_row = 2
        nearby_wolf.direction_row = 4
        distant_wolf.direction_row = 2
        game.enemies[game.map_data.name] = [crow, nearby_wolf, distant_wolf]

        game._update_enemies(0.4)
        game._update_enemies(0.41)

        self.assertEqual("alerted", crow.awareness)
        self.assertEqual("alerted", nearby_wolf.awareness)
        self.assertEqual(600.0, nearby_wolf.last_seen_x)
        self.assertNotEqual("alerted", distant_wolf.awareness)

    def test_reconciled_species_ignores_crow_alert(self) -> None:
        game = make_game()
        game.map_data = SimpleNamespace(
            name=FIRST_MAP,
            resolve_movement=lambda x, y, dx, dy: (x + dx, y + dy),
        )
        game.species_affinity["wolf"] = 100
        game.player.x = 600.0
        game.player.y = 500.0
        crow = EnemyAI.create("crow", 500.0, 500.0)
        wolf = EnemyAI.create("wolf", 500.0, 800.0)
        crow.direction_row = 2
        wolf.direction_row = 4
        game.enemies[FIRST_MAP] = [crow, wolf]

        game._update_enemies(0.4)
        game._update_enemies(0.41)

        self.assertEqual("alerted", crow.awareness)
        self.assertEqual("unaware", wolf.awareness)

    def test_bear_stays_at_habitat_until_detection_or_alert(self) -> None:
        game = make_game()
        game.player.x = 3000.0
        game.player.y = 3000.0
        bear = EnemyAI.create("bear", 500.0, 500.0)

        bear.update(2.0, game.map_data, game.player, 0, 1.0)

        self.assertEqual((500.0, 500.0), (bear.x, bear.y))
        self.assertEqual("idle", bear.state)

    def test_species_attack_power_and_speed_match_design(self) -> None:
        self.assertEqual(35, ANIMAL_STATS["crow"]["hp"])
        self.assertEqual(70, ANIMAL_STATS["wolf"]["hp"])
        self.assertEqual(120, ANIMAL_STATS["bear"]["hp"])
        self.assertEqual(20.0, ANIMAL_STATS["crow"]["attack_damage"])
        self.assertEqual(40.0, ANIMAL_STATS["wolf"]["attack_damage"])
        self.assertEqual(55.0, ANIMAL_STATS["bear"]["attack_damage"])
        self.assertEqual(250.0, ANIMAL_STATS["crow"]["speed"])
        self.assertEqual(200.0, ANIMAL_STATS["wolf"]["speed"])
        self.assertEqual(160.0, ANIMAL_STATS["bear"]["speed"])
        self.assertLess(Player.WALK_SPEED, ANIMAL_STATS["wolf"]["speed"])
        self.assertLess(ANIMAL_STATS["wolf"]["speed"], Player.RUN_SPEED)
        self.assertEqual(7.0, AI_SENSES["crow"]["vision_tiles"])
        self.assertEqual(6.0, AI_SENSES["wolf"]["vision_tiles"])

    def test_melee_hit_damages_ai_and_reduces_species_affinity(self) -> None:
        game = make_game()
        game.player.x = 300.0
        game.player.y = 300.0
        game.player.direction = "right"
        enemy = EnemyAI.create("wolf", 400.0, 300.0)
        game.enemies[FIRST_MAP] = [enemy]
        game.species_affinity["wolf"] = 50
        game.model.tool_slot = ItemStack("wooden_sword")

        game._use_primary_attack()

        self.assertEqual(60, enemy.hp)
        self.assertEqual("hurt", enemy.state)
        self.assertEqual(45, game.species_affinity["wolf"])
        self.assertEqual(36, game.model.tool_slot.durability)

    def test_empty_tool_bar_uses_five_damage_unarmed_attack(self) -> None:
        game = make_game()
        game.player.x = 300.0
        game.player.y = 300.0
        game.player.direction = "right"
        enemy = EnemyAI.create("wolf", 400.0, 300.0)
        game.enemies[FIRST_MAP] = [enemy]
        game.species_affinity["wolf"] = 50

        game._use_primary_attack()

        self.assertEqual(65, enemy.hp)
        self.assertEqual("hurt", enemy.state)
        self.assertIn("맨손 명중", game.toast)

    def test_spear_damage_and_throw_range_match_design(self) -> None:
        self.assertEqual(15, PROJECTILE_DAMAGE["wooden_spear"])
        self.assertEqual(30, PROJECTILE_DAMAGE["stone_spear"])
        game = make_game()
        game.player.x = 1000.0
        game.player.y = 1000.0
        game.camera_x = game.player.x
        game.camera_y = game.player.y
        target_x, target_y = game._throw_target_world(100000.0, 360.0)
        distance = math.hypot(
            target_x - game.player.x,
            target_y - (game.player.y + 240.0 * 0.34),
        )
        self.assertLessEqual(distance, 5.0 * WORLD_TILE_SIZE + 0.001)

    def test_sword_durability_does_not_drop_when_attack_misses(self) -> None:
        game = make_game()
        game.model.tool_slot = ItemStack("wooden_sword")

        game._use_primary_attack()

        self.assertEqual(40, game.model.tool_slot.durability)

    def test_spear_breaks_after_landing_at_zero_durability(self) -> None:
        game = make_game()
        game.model.tool_slot = ItemStack("wooden_spear", durability=3)

        self.assertTrue(game._throw_equipped_at_screen(1000.0, 360.0))
        for _ in range(30):
            game._update_projectiles(0.05)
            if not game.projectiles[FIRST_MAP]:
                break

        self.assertEqual([], game.world_drops[FIRST_MAP])
        self.assertIn("파괴", game.toast)

    def test_fishing_rod_waits_for_future_bite_before_losing_durability(self) -> None:
        game = make_game()
        game.model.tool_slot = ItemStack("fishing_rod")

        game._use_tool()

        self.assertEqual(30, game.model.tool_slot.durability)

    def test_fishing_uses_the_harder_tension_window(self) -> None:
        self.assertEqual(1.0, FISHING_REACTION_SECONDS)
        self.assertEqual((58.0, 46.0), (
            FISHING_TENSION_RISE_PER_SECOND,
            FISHING_TENSION_FALL_PER_SECOND,
        ))
        self.assertEqual((42.0, 62.0), (
            FISHING_SAFE_TENSION_MIN,
            FISHING_SAFE_TENSION_MAX,
        ))
        self.assertEqual((8.0, 90.0, 0.60), (
            FISHING_DANGER_TENSION_MIN,
            FISHING_DANGER_TENSION_MAX,
            FISHING_DANGER_HOLD_SECONDS,
        ))
        self.assertEqual((18.0, 14.0), (
            FISHING_CAPTURE_PER_SECOND,
            FISHING_CAPTURE_LOSS_PER_SECOND,
        ))

    def test_fishing_spot_starts_bite_and_spacebar_minigame(self) -> None:
        game = prepare_fishing_game()
        game.player.direction = "down_left"
        origin = (game.player.x, game.player.y)

        self.assertTrue(game._interact_world())
        self.assertEqual("waiting", game.fishing_state)
        self.assertEqual(30, game.model.tool_slot.durability)
        self.assertEqual("down_left", game.player.direction)
        self.assertEqual(0.0, game.fishing_tension)

        game.player.x += 80.0
        game.player.y -= 40.0
        game.player.direction = "up_right"
        game._update_fishing(0.01)
        self.assertEqual(origin, (game.player.x, game.player.y))
        self.assertEqual("down_left", game.player.direction)

        game.fishing_bite_timer = 0.01
        game._update_fishing(0.02)
        self.assertEqual("bite", game.fishing_state)

        game._begin_fishing_minigame()
        self.assertEqual("minigame", game.fishing_state)
        self.assertEqual(28, game.model.tool_slot.durability)
        self.assertTrue(game.fishing_reeling)
        self.assertEqual(0.0, game.fishing_tension)

    def test_fishing_safe_tension_fills_capture_and_awards_raw_fish(self) -> None:
        game = prepare_fishing_game()
        game._start_fishing(game.map_data.fishing_spots[0])
        game._begin_fishing_minigame()
        game.fishing_tension = 50.0
        game.fishing_capture = 99.0
        game.fishing_reeling = False

        game._update_fishing(0.1)

        self.assertEqual("idle", game.fishing_state)
        self.assertEqual(1, game.model.item_count("fish"))
        self.assertIn("생선을 낚았습니다", game.toast)

    def test_fishing_fails_on_missed_bite_or_sustained_danger_tension(self) -> None:
        game = prepare_fishing_game()
        game._start_fishing(game.map_data.fishing_spots[0])
        game.fishing_state = "bite"
        game.fishing_reaction_timer = 0.01

        game._update_fishing(0.02)

        self.assertEqual("idle", game.fishing_state)
        self.assertEqual(0, game.model.item_count("fish"))

        game._start_fishing(game.map_data.fishing_spots[0])
        game._begin_fishing_minigame()
        game.fishing_tension = 100.0
        game.fishing_danger_timer = 0.84
        game.fishing_reeling = True

        game._update_fishing(0.02)

        self.assertEqual("idle", game.fishing_state)
        self.assertEqual(0, game.model.item_count("fish"))
        self.assertIn("물고기를 놓쳤습니다", game.toast)

    def test_raw_and_cooked_fish_heal_and_campfire_cooks_entire_stack(self) -> None:
        import pico2d as p2

        game = make_game()
        game.player.hp = 80.0
        game.model.tool_slot = ItemStack("fish", 2)

        game._use_equipped_with_e()

        self.assertEqual(85.0, game.player.hp)
        self.assertEqual(1, game.model.tool_slot.count)

        bedding = PlacedUtility("travel_bedding", game.player.x, game.player.y)
        game.placed_utilities[FIRST_MAP] = [bedding]
        game._key_down(SimpleNamespace(key=p2.SDLK_e, repeat=0))
        self.assertEqual(90.0, game.player.hp)
        self.assertIsNone(game.model.tool_slot)
        self.assertEqual([bedding], game.placed_utilities[FIRST_MAP])

        campfire = PlacedUtility("campfire", game.player.x, game.player.y)
        game.placed_utilities[FIRST_MAP].append(campfire)
        game.model.tool_slot = ItemStack("fish")
        self.assertTrue(game._interact_world())
        self.assertEqual("cooked_fish", game.model.tool_slot.item_id)
        self.assertEqual(1, game.model.tool_slot.count)
        self.assertEqual([bedding, campfire], game.placed_utilities[FIRST_MAP])

        game._use_equipped_with_e()

        self.assertEqual(100.0, game.player.hp)
        self.assertIsNone(game.model.tool_slot)

    def test_armor_absorbs_hits_until_it_breaks_before_hp_is_damaged(self) -> None:
        game = make_game()
        game.model.armor_slot = ItemStack("light_armor", durability=4)

        self.assertEqual(0.0, game.damage_player(50.0))
        self.assertEqual(100.0, game.player.hp)
        self.assertEqual(2, game.model.armor_slot.durability)

        self.assertEqual(0.0, game.damage_player(50.0))
        self.assertEqual(100.0, game.player.hp)
        self.assertIsNone(game.model.armor_slot)

        self.assertEqual(50.0, game.damage_player(50.0))
        self.assertEqual(50.0, game.player.hp)

    def test_ending_changes_with_final_species_affinity(self) -> None:
        game = make_game()
        cases = (
            ({"crow": 100, "wolf": 100, "bear": 100}, "완전한 화해 엔딩"),
            ({"crow": 100, "wolf": 100, "bear": 99}, "대립 엔딩"),
            ({"crow": 80, "wolf": 90, "bear": 99}, "대립 엔딩"),
            ({"crow": 40, "wolf": 70, "bear": 79}, "대립 엔딩"),
            ({"crow": 100, "wolf": 39, "bear": 100}, "대립 엔딩"),
        )
        for affinity, expected in cases:
            game.species_affinity = affinity
            self.assertEqual(expected, game._affinity_ending())

    def test_cutscene_assets_are_complete_and_ordered(self) -> None:
        self.assertEqual(
            [f"story{index}.png" for index in range(1, 5)],
            [path.name for path in INTRO_CUTSCENE_PATHS],
        )
        self.assertEqual(
            [f"ending1-{index}.png" for index in range(1, 6)],
            [path.name for path in CONFLICT_ENDING_CUTSCENE_PATHS],
        )
        self.assertEqual(
            [f"ending2-{index}.png" for index in range(1, 7)],
            [path.name for path in RECONCILIATION_ENDING_CUTSCENE_PATHS],
        )
        for path in (
            INTRO_CUTSCENE_PATHS
            + CONFLICT_ENDING_CUTSCENE_PATHS
            + RECONCILIATION_ENDING_CUTSCENE_PATHS
        ):
            self.assertTrue(path.exists(), path)

    def test_intro_cutscene_advances_then_fades_into_lobby(self) -> None:
        game = make_game()
        game._start_cutscene(INTRO_CUTSCENE_PATHS, "intro")
        scene_seconds = CUTSCENE_FADE_SECONDS * 2.0 + CUTSCENE_HOLD_SECONDS

        for expected_index in range(1, 4):
            game._update_cutscene(scene_seconds)
            self.assertEqual(expected_index, game.cutscene_index)
            self.assertTrue(game.cutscene_active)

        game._update_cutscene(scene_seconds)

        self.assertFalse(game.cutscene_active)
        self.assertTrue(game.lobby_active)
        self.assertEqual(LOBBY_FADE_SECONDS, game.world_fade_remaining)
        self.assertTrue(game.running)

    def test_lobby_assets_and_start_quit_transitions(self) -> None:
        self.assertEqual("The Last Wile Human", GAME_TITLE)
        self.assertTrue(LOBBY_BACKGROUND_PATH.exists())
        self.assertTrue(LOBBY_BUTTON_PATH.exists())
        self.assertEqual(b"\x89PNG\r\n\x1a\n", LOBBY_BACKGROUND_PATH.read_bytes()[:8])
        self.assertEqual(b"\x89PNG\r\n\x1a\n", LOBBY_BUTTON_PATH.read_bytes()[:8])
        self.assertEqual(6, LOBBY_BUTTON_PATH.read_bytes()[25])

        game = make_game()
        game.lobby_active = True
        game._player_sprite_sheet = None
        game._map_cache = {FIRST_MAP: game.map_data}
        game._background_cache = {}
        game.ui = SimpleNamespace(model=game.model)
        game.game_minutes = 23 * 60
        game.species_affinity["crow"] = 80
        game.ending_variant = "대립 엔딩"
        start = game.LOBBY_START_BUTTON
        self.assertGreater(start.cy, WINDOW_HEIGHT / 2 - 40)
        self.assertGreater(start.cy, game.LOBBY_QUIT_BUTTON.cy)

        self.assertTrue(game._activate_lobby_button(start.cx, start.cy))
        self.assertEqual("start", game.lobby_transition)
        game._update_lobby(LOBBY_FADE_SECONDS)

        self.assertFalse(game.lobby_active)
        self.assertFalse(game.cutscene_active)
        self.assertEqual(LOBBY_FADE_SECONDS, game.world_fade_remaining)
        self.assertTrue(game.running)
        self.assertEqual(GAME_START_MINUTES, game.game_minutes)
        self.assertEqual(0, game.species_affinity["crow"])
        self.assertEqual("", game.ending_variant)

        game = make_game()
        game.lobby_active = True
        quit_button = game.LOBBY_QUIT_BUTTON

        self.assertTrue(
            game._activate_lobby_button(quit_button.cx, quit_button.cy)
        )
        game._update_lobby(LOBBY_FADE_SECONDS)

        self.assertFalse(game.running)
        self.assertTrue(game.lobby_active)
        self.assertEqual("quit", game.lobby_transition)

    def test_ending_cutscene_branch_matches_final_affinity(self) -> None:
        game = make_game()
        game.species_affinity = {"crow": 100, "wolf": 100, "bear": 99}

        game._begin_ending_cutscene()

        self.assertEqual("대립 엔딩", game.ending_variant)
        self.assertEqual(CONFLICT_ENDING_CUTSCENE_PATHS, game.cutscene_sequence)

        game.species_affinity = {"crow": 100, "wolf": 100, "bear": 100}
        game._begin_ending_cutscene()

        self.assertEqual("완전한 화해 엔딩", game.ending_variant)
        self.assertEqual(
            RECONCILIATION_ENDING_CUTSCENE_PATHS,
            game.cutscene_sequence,
        )

        game._update_cutscene(
            game._cutscene_scene_seconds()
            * len(RECONCILIATION_ENDING_CUTSCENE_PATHS)
        )

        self.assertTrue(game.running)
        self.assertFalse(game.cutscene_active)
        self.assertTrue(game.lobby_active)
        self.assertEqual(LOBBY_FADE_SECONDS, game.world_fade_remaining)

    def test_cutscene_buttons_pause_resume_toggle_speed_and_skip(self) -> None:
        import pico2d as p2

        def click(game: Game, rect: Rect) -> None:
            event = SimpleNamespace(
                type=p2.SDL_MOUSEBUTTONDOWN,
                button=p2.SDL_BUTTON_LEFT,
                x=int(rect.cx),
                y=WINDOW_HEIGHT - 1 - int(rect.cy),
            )
            with patch.object(p2, "get_events", return_value=[event]):
                game.handle_events()

        for sequence, kind in (
            (INTRO_CUTSCENE_PATHS, "intro"),
            (CONFLICT_ENDING_CUTSCENE_PATHS, "ending"),
        ):
            with self.subTest(kind=kind):
                game = make_game()
                game._start_cutscene(sequence, kind)
                click(game, game.CUTSCENE_FAST_FORWARD_BUTTON)
                self.assertTrue(game.cutscene_fast_forward)
                game.update(1.0)
                self.assertEqual(2.0, game.cutscene_elapsed)

                click(game, game.CUTSCENE_PAUSE_BUTTON)
                self.assertTrue(game.cutscene_paused)
                click(game, Rect(640, 360, 1, 1))
                advance = SimpleNamespace(type=p2.SDL_KEYDOWN, key=p2.SDLK_RETURN)
                with patch.object(p2, "get_events", return_value=[advance]):
                    game.handle_events()
                game.update(10.0)
                self.assertEqual(0, game.cutscene_index)
                self.assertEqual(2.0, game.cutscene_elapsed)

                click(game, game.CUTSCENE_PAUSE_BUTTON)
                self.assertFalse(game.cutscene_paused)
                game.update(0.25)
                self.assertEqual(2.5, game.cutscene_elapsed)
                click(game, game.CUTSCENE_FAST_FORWARD_BUTTON)
                self.assertFalse(game.cutscene_fast_forward)
                game.update(0.5)
                self.assertEqual(3.0, game.cutscene_elapsed)

                click(game, game.CUTSCENE_FAST_FORWARD_BUTTON)
                click(game, game.CUTSCENE_PAUSE_BUTTON)
                click(game, game.CUTSCENE_SKIP_BUTTON)
                self.assertTrue(game.running)
                self.assertTrue(game.lobby_active)
                self.assertFalse(game.cutscene_active)
                self.assertFalse(game.cutscene_fast_forward)
                self.assertFalse(game.cutscene_paused)

    def test_gameplay_escape_pauses_until_resume_or_return_to_lobby(self) -> None:
        import pico2d as p2

        game = make_game()
        game.pressed.add(p2.SDLK_w)
        start_time = game.game_minutes
        start_position = (game.player.x, game.player.y)
        escape = SimpleNamespace(type=p2.SDL_KEYDOWN, key=p2.SDLK_ESCAPE, repeat=0)
        repeated_escape = SimpleNamespace(type=p2.SDL_KEYDOWN, key=p2.SDLK_ESCAPE, repeat=1)
        damage = SimpleNamespace(type=p2.SDL_KEYDOWN, key=p2.SDLK_h, repeat=0)

        def dispatch(*events: object) -> None:
            with patch.object(p2, "get_events", return_value=events):
                game.handle_events()

        def click(rect: Rect) -> None:
            dispatch(SimpleNamespace(
                type=p2.SDL_MOUSEBUTTONDOWN,
                button=p2.SDL_BUTTON_LEFT,
                x=int(rect.cx),
                y=WINDOW_HEIGHT - 1 - int(rect.cy),
            ))

        dispatch(escape, repeated_escape, damage)
        self.assertTrue(game.game_paused)
        self.assertFalse(game.lobby_active)
        self.assertFalse(game.pressed)
        game.update(1.0)
        self.assertEqual(MAX_HP, game.player.hp)
        self.assertEqual(start_time, game.game_minutes)
        self.assertEqual(start_position, (game.player.x, game.player.y))

        click(game.PAUSE_RESUME_BUTTON)
        self.assertFalse(game.game_paused)
        game.update(0.5)
        self.assertGreater(game.game_minutes, start_time)

        dispatch(escape, escape)
        self.assertFalse(game.game_paused)
        dispatch(escape)
        click(game.PAUSE_QUIT_BUTTON)
        self.assertFalse(game.game_paused)
        self.assertTrue(game.lobby_active)
        self.assertTrue(game.running)

    def test_cutscene_escape_leaves_game_running_in_lobby(self) -> None:
        import pico2d as p2

        escape = SimpleNamespace(type=p2.SDL_KEYDOWN, key=p2.SDLK_ESCAPE, repeat=0)
        game = make_game()
        game._start_cutscene(INTRO_CUTSCENE_PATHS, "intro")
        with patch.object(p2, "get_events", return_value=[escape, escape]):
            game.handle_events()
        game.update(LOBBY_FADE_SECONDS)
        self.assertTrue(game.running)
        self.assertTrue(game.lobby_active)
        self.assertFalse(game.cutscene_active)
        self.assertEqual("", game.lobby_transition)

    def test_window_close_stops_game_in_any_screen(self) -> None:
        import pico2d as p2

        window_close = SimpleNamespace(type=p2.SDL_QUIT)
        for screen in ("world", "pause", "lobby", "cutscene", "game_over"):
            with self.subTest(screen=screen):
                game = make_game()
                game.game_paused = screen == "pause"
                game.lobby_active = screen == "lobby"
                game.game_over = screen == "game_over"
                if screen == "cutscene":
                    game._start_cutscene(INTRO_CUTSCENE_PATHS, "intro")
                with patch.object(p2, "get_events", return_value=[window_close]):
                    game.handle_events()
                self.assertFalse(game.running)
                self.assertEqual(screen == "lobby", game.lobby_active)
                self.assertEqual("", game.lobby_transition)
                self.assertEqual(0.0, game.world_fade_remaining)


if __name__ == "__main__":
    unittest.main()
