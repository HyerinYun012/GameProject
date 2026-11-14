"""Inventory and equipment data model for the CrowGame prototype.

The module intentionally has no Pico2D dependency, so the game state can be
unit-tested without opening a window.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ItemCategory = Literal["tool", "armor", "material", "utility"]
SlotArea = Literal["inventory", "hotbar", "tool", "armor"]

INVENTORY_SIZE = 15
HOTBAR_SIZE = 5


@dataclass(frozen=True, slots=True)
class ItemDefinition:
    item_id: str
    label: str
    icon_filename: str
    category: ItemCategory
    max_stack: int = 1
    defense: int = 0
    action: str | None = None


ITEMS: dict[str, ItemDefinition] = {
    "wooden_sword": ItemDefinition("wooden_sword", "나무 검", "wooden sword.png", "tool", action="attack"),
    "stone_sword": ItemDefinition("stone_sword", "돌 검", "Stone Sword.png", "tool", action="attack"),
    "fishing_rod": ItemDefinition("fishing_rod", "낚싯대", "fishing rod.png", "tool", action="fish"),
    "torch": ItemDefinition("torch", "횃불", "torchlight.png", "tool", action="torch"),
    "wooden_pickaxe": ItemDefinition("wooden_pickaxe", "나무 곡괭이", "Wooden Pickaxe.png", "tool", action="mine"),
    "stone_pickaxe": ItemDefinition("stone_pickaxe", "돌 곡괭이", "stone pickaxe.png", "tool", action="mine"),
    "wooden_axe": ItemDefinition("wooden_axe", "나무 도끼", "wooden ax.png", "tool", action="axe"),
    "stone_axe": ItemDefinition("stone_axe", "돌 도끼", "stone ax.png", "tool", action="axe"),
    "wooden_spear": ItemDefinition("wooden_spear", "나무 창", "Wooden Spear.png", "tool", action="attack"),
    "stone_spear": ItemDefinition("stone_spear", "돌 창", "Stone Spear.png", "tool", action="attack"),
    "light_armor": ItemDefinition("light_armor", "간이 갑옷", "Light armor.png", "armor", defense=4),
    "wood": ItemDefinition("wood", "나무", "wood.png", "material", max_stack=99),
    "stone": ItemDefinition("stone", "돌", "stone.png", "material", max_stack=99),
    "fiber": ItemDefinition("fiber", "섬유", "fiber.png", "material", max_stack=99),
    "travel_bedding": ItemDefinition("travel_bedding", "여행 침구", "travel bedding set.png", "utility"),
}

TOOL_ITEM_IDS = frozenset(item_id for item_id, item in ITEMS.items() if item.category == "tool")
ARMOR_ITEM_IDS = frozenset(item_id for item_id, item in ITEMS.items() if item.category == "armor")


@dataclass(slots=True)
class ItemStack:
    item_id: str
    count: int = 1

    def __post_init__(self) -> None:
        if self.item_id not in ITEMS:
            raise KeyError(f"Unknown item: {self.item_id}")
        if self.count <= 0:
            raise ValueError("Item stack count must be positive")
        if self.count > ITEMS[self.item_id].max_stack:
            raise ValueError("Item stack exceeds its maximum size")

    @property
    def definition(self) -> ItemDefinition:
        return ITEMS[self.item_id]


@dataclass(frozen=True, slots=True)
class SlotRef:
    area: SlotArea
    index: int | None = None

    @classmethod
    def inventory(cls, index: int) -> "SlotRef":
        return cls("inventory", index)

    @classmethod
    def hotbar(cls, index: int) -> "SlotRef":
        return cls("hotbar", index)

    @classmethod
    def tool(cls) -> "SlotRef":
        return cls("tool")

    @classmethod
    def armor(cls) -> "SlotRef":
        return cls("armor")


DEMO_LOADOUT: tuple[tuple[str, int], ...] = (
    ("wooden_axe", 1),
    ("wooden_pickaxe", 1),
    ("fishing_rod", 1),
    ("wooden_sword", 1),
    ("torch", 1),
    ("stone_axe", 1),
    ("stone_pickaxe", 1),
    ("stone_sword", 1),
    ("wooden_spear", 1),
    ("stone_spear", 1),
    ("light_armor", 1),
    ("wood", 12),
    ("stone", 10),
    ("fiber", 8),
    ("travel_bedding", 1),
)


class InventoryModel:
    """Single-source-of-truth storage for inventory, hotbar, and equipment."""

    def __init__(self, *, base_defense: int = 0) -> None:
        self.slots: list[ItemStack | None] = [None] * INVENTORY_SIZE
        self.tool_slot: ItemStack | None = None
        self.armor_slot: ItemStack | None = None
        self.base_defense = base_defense

    @classmethod
    def demo(cls) -> "InventoryModel":
        model = cls()
        model.seed_demo_inventory()
        return model

    @property
    def hotbar(self) -> tuple[ItemStack | None, ...]:
        """A live view of inventory slots 0..4, never separate storage."""
        return tuple(self.slots[:HOTBAR_SIZE])

    @property
    def defense(self) -> int:
        bonus = self.armor_slot.definition.defense if self.armor_slot else 0
        return self.base_defense + bonus

    @property
    def equipped_tool_definition(self) -> ItemDefinition | None:
        return self.tool_slot.definition if self.tool_slot else None

    def seed_demo_inventory(self) -> None:
        if len(DEMO_LOADOUT) != INVENTORY_SIZE:
            raise RuntimeError("Demo loadout must fill exactly 15 slots")
        self.slots = [ItemStack(item_id, count) for item_id, count in DEMO_LOADOUT]
        self.tool_slot = None
        self.armor_slot = None

    def canonical_ref(self, ref: SlotRef) -> SlotRef:
        if ref.area == "hotbar":
            if ref.index is None or not 0 <= ref.index < HOTBAR_SIZE:
                raise IndexError("Hotbar index out of range")
            return SlotRef.inventory(ref.index)
        if ref.area == "inventory":
            if ref.index is None or not 0 <= ref.index < INVENTORY_SIZE:
                raise IndexError("Inventory index out of range")
            return ref
        if ref.area in ("tool", "armor"):
            if ref.index is not None:
                raise ValueError("Equipment slots do not use an index")
            return ref
        raise ValueError(f"Unknown slot area: {ref.area}")

    def get(self, ref: SlotRef) -> ItemStack | None:
        ref = self.canonical_ref(ref)
        if ref.area == "inventory":
            assert ref.index is not None
            return self.slots[ref.index]
        return self.tool_slot if ref.area == "tool" else self.armor_slot

    def _set(self, ref: SlotRef, stack: ItemStack | None) -> None:
        ref = self.canonical_ref(ref)
        if ref.area == "inventory":
            assert ref.index is not None
            self.slots[ref.index] = stack
        elif ref.area == "tool":
            self.tool_slot = stack
        else:
            self.armor_slot = stack

    def slot_accepts(self, ref: SlotRef, stack: ItemStack | None) -> bool:
        if stack is None:
            return True
        ref = self.canonical_ref(ref)
        if ref.area == "inventory":
            return True
        if ref.area == "tool":
            return stack.definition.category == "tool"
        return stack.definition.category == "armor"

    def add_item(self, item_id: str, count: int = 1) -> int:
        """Collect an item automatically; return the quantity that did not fit."""
        if item_id not in ITEMS:
            raise KeyError(f"Unknown item: {item_id}")
        if count < 0:
            raise ValueError("Cannot add a negative item count")
        if count == 0:
            return 0

        definition = ITEMS[item_id]
        remaining = count
        for stack in self.slots:
            if stack is None or stack.item_id != item_id:
                continue
            moved = min(definition.max_stack - stack.count, remaining)
            stack.count += moved
            remaining -= moved
            if remaining == 0:
                return 0

        for index, stack in enumerate(self.slots):
            if stack is not None:
                continue
            moved = min(definition.max_stack, remaining)
            self.slots[index] = ItemStack(item_id, moved)
            remaining -= moved
            if remaining == 0:
                return 0
        return remaining

    def try_move(self, source: SlotRef, target: SlotRef) -> bool:
        """Move, merge, or swap two slots without ever losing an item."""
        source = self.canonical_ref(source)
        target = self.canonical_ref(target)
        source_stack = self.get(source)
        if source_stack is None:
            return False
        if source == target:
            return True

        target_stack = self.get(target)
        if not self.slot_accepts(target, source_stack):
            return False

        if target_stack and target_stack.item_id == source_stack.item_id:
            room = source_stack.definition.max_stack - target_stack.count
            if room <= 0:
                return False
            moved = min(room, source_stack.count)
            target_stack.count += moved
            source_stack.count -= moved
            if source_stack.count == 0:
                self._set(source, None)
            return True

        if target_stack is not None and not self.slot_accepts(source, target_stack):
            return False
        self._set(source, target_stack)
        self._set(target, source_stack)
        return True


__all__ = [
    "ARMOR_ITEM_IDS", "DEMO_LOADOUT", "HOTBAR_SIZE", "INVENTORY_SIZE", "ITEMS",
    "TOOL_ITEM_IDS", "InventoryModel", "ItemDefinition", "ItemStack", "SlotRef",
]
