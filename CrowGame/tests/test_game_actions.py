from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CrowGame.game_model import InventoryModel, ItemStack, SlotRef  # noqa: E402
from CrowGame.main import DragState, Game, Player  # noqa: E402


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
    game.drag = None
    game.toast = ""
    game.toast_error = False
    game.toast_timer = 0.0
    return game


class GameActionTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
