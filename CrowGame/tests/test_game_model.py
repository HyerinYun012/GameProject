from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from game_model import (  # noqa: E402
    ARMOR_ITEM_IDS,
    CRAFTING_RECIPES,
    HOTBAR_SIZE,
    INVENTORY_SIZE,
    ITEMS,
    TOOL_ITEM_IDS,
    InventoryModel,
    ItemStack,
    SlotRef,
)


class InventoryModelTests(unittest.TestCase):
    def test_harvested_fruit_uses_the_apple_asset(self) -> None:
        self.assertEqual("사과", ITEMS["fruit"].label)
        self.assertEqual("apple.png", ITEMS["fruit"].icon_filename)
        self.assertEqual(5, ITEMS["fruit"].heal_amount)
        self.assertTrue((PROJECT_DIR / "assets" / "apple.png").exists())

    def test_gathered_materials_are_limited_to_ten_per_slot(self) -> None:
        for item_id in ("fruit", "wood", "stone", "fiber"):
            self.assertEqual(10, ITEMS[item_id].max_stack)

    def test_definition_and_demo_sizes(self) -> None:
        self.assertEqual(17, len(ITEMS))
        self.assertEqual(10, len(TOOL_ITEM_IDS))
        self.assertEqual({"light_armor"}, ARMOR_ITEM_IDS)
        model = InventoryModel.demo()
        self.assertEqual(INVENTORY_SIZE, len(model.slots))
        occupied = [stack for stack in model.slots if stack is not None]
        self.assertEqual(len(TOOL_ITEM_IDS), len(occupied))
        self.assertTrue(all(stack.definition.category == "tool" for stack in occupied))
        self.assertEqual(INVENTORY_SIZE - len(TOOL_ITEM_IDS), model.slots.count(None))

    def test_all_requested_crafting_recipes_are_registered(self) -> None:
        recipes = {
            recipe.output_item_id: dict(recipe.ingredients)
            for recipe in CRAFTING_RECIPES
        }
        self.assertEqual(13, len(recipes))
        self.assertEqual({"wood": 2, "stone": 2, "fiber": 1}, recipes["stone_axe"])
        self.assertEqual({"wood": 1, "stone": 2, "fiber": 1}, recipes["stone_pickaxe"])
        self.assertEqual({"wood": 2, "fiber": 1}, recipes["wooden_spear"])
        self.assertEqual({"wood": 2, "fiber": 3}, recipes["light_armor"])
        self.assertEqual({"wood": 2, "stone": 3}, recipes["campfire"])
        self.assertEqual({"fiber": 4, "wood": 1}, recipes["travel_bedding"])
        self.assertEqual({"wood": 2, "fiber": 2}, recipes["fishing_rod"])

    def test_requested_max_durability_values_are_registered(self) -> None:
        expected = {
            "wooden_sword": 40,
            "stone_sword": 80,
            "wooden_pickaxe": 24,
            "stone_pickaxe": 60,
            "fishing_rod": 30,
            "wooden_spear": 12,
            "stone_spear": 21,
            "stone_axe": 60,
            "wooden_axe": 24,
            "light_armor": 20,
        }
        self.assertEqual(
            expected,
            {item_id: ITEMS[item_id].max_durability for item_id in expected},
        )

    def test_durable_stack_starts_full_and_preserves_wear_on_pickup(self) -> None:
        stack = ItemStack("stone_sword")
        self.assertEqual(80, stack.durability)
        self.assertFalse(stack.lose_durability(4))
        self.assertEqual(76, stack.durability)

        model = InventoryModel()
        self.assertEqual(0, model.add_stack(stack))
        self.assertEqual(76, model.slots[0].durability)

    def test_crafted_tool_starts_at_full_durability(self) -> None:
        model = InventoryModel()
        model.add_item("wood", 1)
        model.add_item("fiber", 1)
        recipe = next(
            recipe for recipe in CRAFTING_RECIPES
            if recipe.output_item_id == "wooden_axe"
        )
        self.assertTrue(model.craft(recipe))
        crafted = next(
            stack for stack in model.slots
            if stack is not None and stack.item_id == "wooden_axe"
        )
        self.assertEqual(24, crafted.durability)

    def test_crafting_atomically_consumes_materials_and_adds_output(self) -> None:
        model = InventoryModel()
        model.add_item("wood", 2)
        model.add_item("stone", 2)
        model.add_item("fiber", 1)
        recipe = next(
            recipe for recipe in CRAFTING_RECIPES
            if recipe.output_item_id == "stone_axe"
        )

        self.assertTrue(model.craft(recipe))
        self.assertEqual(0, model.item_count("wood"))
        self.assertEqual(0, model.item_count("stone"))
        self.assertEqual(0, model.item_count("fiber"))
        self.assertEqual(1, model.item_count("stone_axe"))

    def test_crafting_failure_never_consumes_materials(self) -> None:
        model = InventoryModel()
        model.slots[0] = ItemStack("wood", 3)
        model.slots[1] = ItemStack("fiber", 2)
        for index in range(2, INVENTORY_SIZE):
            model.slots[index] = ItemStack("wooden_sword")
        recipe = next(
            recipe for recipe in CRAFTING_RECIPES
            if recipe.output_item_id == "wooden_axe"
        )

        self.assertFalse(model.craft(recipe))
        self.assertEqual(3, model.item_count("wood"))
        self.assertEqual(2, model.item_count("fiber"))
        self.assertEqual(0, model.item_count("wooden_axe"))

    def test_hotbar_is_the_first_five_inventory_slots(self) -> None:
        model = InventoryModel.demo()
        self.assertEqual(HOTBAR_SIZE, len(model.hotbar))
        for index in range(HOTBAR_SIZE):
            self.assertIs(model.slots[index], model.get(SlotRef.hotbar(index)))
        first = model.slots[0]
        self.assertTrue(model.try_move(SlotRef.hotbar(0), SlotRef.tool()))
        self.assertIsNone(model.slots[0])
        self.assertIsNone(model.hotbar[0])
        self.assertIs(first, model.tool_slot)

    def test_add_item_stacks_then_uses_first_empty_slot(self) -> None:
        model = InventoryModel()
        self.assertEqual(0, model.add_item("wood", 11))
        self.assertEqual(ItemStack("wood", 10), model.slots[0])
        self.assertEqual(ItemStack("wood", 1), model.slots[1])
        self.assertEqual(0, model.add_item("wood", 5))
        self.assertEqual(6, model.slots[1].count)

    def test_add_item_returns_remainder_when_full(self) -> None:
        model = InventoryModel()
        model.slots = [ItemStack("wood", ITEMS["wood"].max_stack) for _ in model.slots]
        self.assertEqual(7, model.add_item("wood", 7))

    def test_take_removes_a_stack_for_world_drop(self) -> None:
        model = InventoryModel()
        model.slots[0] = ItemStack("stone", 7)
        dropped = model.take(SlotRef.hotbar(0))
        self.assertEqual(ItemStack("stone", 7), dropped)
        self.assertIsNone(model.slots[0])

    def test_take_partial_stack_and_remove_item(self) -> None:
        model = InventoryModel()
        model.slots[0] = ItemStack("fiber", 8)
        taken = model.take(SlotRef.inventory(0), 3)
        self.assertEqual(ItemStack("fiber", 3), taken)
        self.assertEqual(5, model.slots[0].count)
        self.assertEqual(4, model.remove_item("fiber", 4))
        self.assertEqual(1, model.slots[0].count)

    def test_tool_slot_accepts_every_item_category(self) -> None:
        model = InventoryModel()
        for item_id in ("wood", "light_armor", "campfire", "fruit"):
            model.slots[0] = ItemStack(item_id)
            self.assertTrue(model.try_move(SlotRef.inventory(0), SlotRef.tool()))
            self.assertEqual(item_id, model.tool_slot.item_id)
            self.assertTrue(model.try_move(SlotRef.tool(), SlotRef.inventory(0)))

    def test_armor_slot_preserves_base_defense_and_rejects_tools(self) -> None:
        model = InventoryModel(base_defense=2)
        model.slots[0] = ItemStack("light_armor")
        model.slots[1] = ItemStack("stone_sword")
        self.assertTrue(model.try_move(SlotRef.inventory(0), SlotRef.armor()))
        self.assertEqual(2, model.defense)
        self.assertFalse(model.try_move(SlotRef.inventory(1), SlotRef.armor()))
        self.assertEqual("light_armor", model.armor_slot.item_id)
        self.assertEqual("stone_sword", model.slots[1].item_id)

    def test_tool_slot_swaps_all_items_while_armor_stays_restricted(self) -> None:
        model = InventoryModel()
        model.tool_slot = ItemStack("wooden_axe")
        model.slots[0] = ItemStack("stone_sword")
        self.assertTrue(model.try_move(SlotRef.inventory(0), SlotRef.tool()))
        self.assertEqual("stone_sword", model.tool_slot.item_id)
        self.assertEqual("wooden_axe", model.slots[0].item_id)

        model.slots[1] = ItemStack("fiber", 2)
        before_tool = model.tool_slot
        before_inventory = model.slots[1]
        self.assertTrue(model.try_move(SlotRef.tool(), SlotRef.inventory(1)))
        self.assertIs(before_inventory, model.tool_slot)
        self.assertIs(before_tool, model.slots[1])

    def test_merge_never_loses_overflow(self) -> None:
        model = InventoryModel()
        model.slots[0] = ItemStack("stone", 9)
        model.slots[1] = ItemStack("stone", 4)
        self.assertTrue(model.try_move(SlotRef.inventory(1), SlotRef.inventory(0)))
        self.assertEqual(10, model.slots[0].count)
        self.assertEqual(3, model.slots[1].count)
        self.assertEqual(13, model.slots[0].count + model.slots[1].count)

    def test_invalid_indices_are_rejected(self) -> None:
        model = InventoryModel()
        with self.assertRaises(IndexError):
            model.get(SlotRef.inventory(INVENTORY_SIZE))
        with self.assertRaises(IndexError):
            model.get(SlotRef.hotbar(HOTBAR_SIZE))


if __name__ == "__main__":
    unittest.main()
