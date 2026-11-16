"""CrowGame four-map prototype with inventory, hotbar, and equipment UI."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pico2d as p2

try:  # Works both as ``python main.py`` and ``python -m CrowGame.main``.
    from .game_model import (
        CRAFTING_RECIPES,
        ITEMS,
        CraftingRecipe,
        InventoryModel,
        ItemStack,
        SlotRef,
    )
    from .map_system import (
        FIRST_MAP,
        GID_DIAGONAL_FLIP,
        GID_HORIZONTAL_FLIP,
        GID_VERTICAL_FLIP,
        MapData,
        TileSpriteDefinition,
        WorldEntityDefinition,
        WorldRect,
        load_map_data,
    )
except ImportError:  # pragma: no cover - exercised by the normal command file.
    from game_model import (
        CRAFTING_RECIPES,
        ITEMS,
        CraftingRecipe,
        InventoryModel,
        ItemStack,
        SlotRef,
    )
    from map_system import (
        FIRST_MAP,
        GID_DIAGONAL_FLIP,
        GID_HORIZONTAL_FLIP,
        GID_VERTICAL_FLIP,
        MapData,
        TileSpriteDefinition,
        WorldEntityDefinition,
        WorldRect,
        load_map_data,
    )


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FRAME_WIDTH = 32
FRAME_HEIGHT = 48
CHARACTER_WIDTH = 160
CHARACTER_HEIGHT = 240
MAX_HP = 100.0
MAX_SP = 100.0
SP_DRAIN_PER_SECOND = 25.0
SP_RECOVERY_PER_SECOND = 18.0
SP_RUN_RESTART_THRESHOLD = 20.0
CAMERA_ZOOM = 0.50
INTERACTION_SCREEN_DISTANCE = 125.0
AUTO_PICKUP_SCREEN_DISTANCE = 115.0
THROWN_DROP_REARM_MOVEMENT = 30.0
FRUIT_COOLDOWN_SECONDS = 30.0
THROWN_DROP_MIN_SCREEN_DISTANCE = 80.0
THROWN_DROP_MAX_SCREEN_DISTANCE = 130.0
THROWN_DROP_SCREEN_SIZE = 76.0
PROJECTILE_MAX_SCREEN_RANGE = 680.0
PROJECTILE_SCREEN_SPEED = 760.0
PROJECTILE_ARC_SCREEN_HEIGHT = 92.0
PROJECTILE_RELEASE_DELAY = 0.10
THROWABLE_ITEM_IDS = frozenset({"wooden_spear", "stone_spear", "stone"})
PROJECTILE_DAMAGE = {
    "wooden_spear": 35,
    "stone_spear": 50,
    "stone": 18,
}
MELEE_DAMAGE = {
    "wooden_sword": 25,
    "stone_sword": 35,
    "wooden_spear": 30,
    "stone_spear": 40,
}
PLACED_UTILITY_SCREEN_DISTANCE = 130.0
UTILITY_PLACEMENT_SCREEN_DISTANCE = 105.0
INSTALLABLE_ITEM_IDS = frozenset({"travel_bedding", "campfire"})
PLACED_UTILITY_WORLD_SIZES = {
    "travel_bedding": (240.0, 170.0),
    "campfire": (190.0, 190.0),
}
ASSET_DIR = Path(__file__).resolve().parent / "assets"
FRUIT_TREE_UNRIPE_SPRITE = ASSET_DIR / "fruit_tree_unripe.png"
ANIMAL_ASSET_ROOT = (
    Path(__file__).resolve().parent.parent / "Assets" / "Sprites" / "Animals"
)
GENERATED_ICON_DIR = Path(__file__).resolve().parent / "generated" / "icons"
CHARACTER_SHEET = (
    ASSET_DIR
    / "Character Creation 32P"
    / "Character Creation 32P"
    / "Animations Adventurer.png"
)

SIDE_MOVE_X = (0, 32, 64, 96, 128, 176, 208, 240, 272)
VERTICAL_MOVE_X = (0, 32, 64, 96, 128)
STATE_FPS = {
    "idle": 3.0,
    "walk": 9.0,
    "run": 15.0,
    "hurt": 11.0,
    "death": 4.5,
    "attack": 11.0,
    "axe": 10.0,
    "mine": 10.0,
    "fish": 6.0,
}
ACTION_STATES = frozenset({"hurt", "death", "attack", "axe", "mine", "fish"})

ANIMAL_ANIMATIONS: dict[str, dict[str, tuple[int, float, bool]]] = {
    "crow": {
        "idle": (4, 8.0, True),
        "walk": (6, 12.0, True),
        # The crow pack has no separate attack sheet; one brisk non-looping
        # flight cycle is used as a diving strike.
        "attack": (6, 12.0, False),
        "hurt": (3, 12.0, False),
        "death": (6, 10.0, False),
    },
    "wolf": {
        "idle": (4, 4.0, True),
        "walk": (6, 10.0, True),
        "attack": (6, 12.0, False),
        "hurt": (3, 12.0, False),
        "death": (6, 8.0, False),
    },
    "bear": {
        "idle": (4, 4.0, True),
        "walk": (6, 6.0, True),
        "attack": (6, 10.0, False),
        "hurt": (3, 12.0, False),
        "death": (6, 8.0, False),
    },
}
ANIMAL_STATS = {
    "crow": {
        "hp": 35, "size": 210.0, "speed": 100.0, "hit_radius": 68.0,
        "attack_range": 68.0, "attack_damage": 8.0,
    },
    "wolf": {
        "hp": 70, "size": 285.0, "speed": 125.0, "hit_radius": 88.0,
        "attack_range": 82.0, "attack_damage": 14.0,
    },
    "bear": {
        "hp": 120, "size": 375.0, "speed": 90.0, "hit_radius": 120.0,
        "attack_range": 105.0, "attack_damage": 20.0,
    },
}
MAP_AI_KINDS: dict[str, tuple[str, ...]] = {
    "crow_map.json": ("crow",),
    "wolf_map.json": ("wolf",),
    "bear_map.json": ("bear",),
}
MAP_SPECIES = {
    "crow_map.json": "crow",
    "wolf_map.json": "wolf",
    "bear_map.json": "bear",
}
SPECIES_LABELS = {"crow": "까마귀", "wolf": "늑대", "bear": "곰"}
AFFINITY_MAX = 100
AFFINITY_LOSS_PER_HIT = 5
AI_DETECTION_SCREEN_RANGES = {
    "hostile": 520.0,
    "wary": 230.0,
    "near_friendly": 88.0,
    "reconciled": 0.0,
}
AI_PROVOKED_SCREEN_RANGE = 620.0
AI_ATTACK_COOLDOWN = 1.35
AI_PROVOKED_SECONDS = 6.0
AFFINITY_COLORS = {
    "hostile": (205, 54, 65),
    "wary": (224, 145, 54),
    "near_friendly": (81, 154, 214),
    "reconciled": (79, 190, 105),
}


def affinity_relationship(value: int) -> str:
    if value >= 100:
        return "reconciled"
    if value >= 80:
        return "near_friendly"
    if value >= 40:
        return "wary"
    return "hostile"


@dataclass(frozen=True, slots=True)
class SpriteFrame:
    left: int
    top: int
    flip: str = ""


@dataclass(frozen=True, slots=True)
class Rect:
    cx: float
    cy: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.cx - self.width / 2

    @property
    def right(self) -> float:
        return self.cx + self.width / 2

    @property
    def bottom(self) -> float:
        return self.cy - self.height / 2

    @property
    def top(self) -> float:
        return self.cy + self.height / 2

    def contains(self, x: float, y: float) -> bool:
        return self.left <= x <= self.right and self.bottom <= y <= self.top


@dataclass(slots=True)
class DragState:
    source: SlotRef
    item_id: str
    x: float
    y: float


@dataclass(slots=True)
class WorldDrop:
    stack: ItemStack
    x: float
    y: float
    pickup_enabled: bool = True
    large_icon: bool = False
    pickup_origin_x: float | None = None
    pickup_origin_y: float | None = None


@dataclass(slots=True)
class PlacedUtility:
    item_id: str
    x: float
    y: float


@dataclass(slots=True)
class ThrownProjectile:
    item_id: str
    start_x: float
    start_y: float
    target_x: float
    target_y: float
    duration: float
    arc_height: float
    durability: int | None
    elapsed: float = -PROJECTILE_RELEASE_DELAY

    @property
    def progress(self) -> float:
        if self.duration <= 0:
            return 1.0
        return min(max(self.elapsed / self.duration, 0.0), 1.0)

    @property
    def position(self) -> tuple[float, float]:
        progress = self.progress
        return (
            self.start_x + (self.target_x - self.start_x) * progress,
            self.start_y
            + (self.target_y - self.start_y) * progress
            + math.sin(math.pi * progress) * self.arc_height,
        )

    @property
    def landed(self) -> bool:
        return self.elapsed >= self.duration

    def advance(self, dt: float) -> tuple[tuple[float, float], tuple[float, float]]:
        previous = self.position
        self.elapsed += dt
        return previous, self.position


@dataclass(slots=True)
class EnemyAI:
    animal: str
    x: float
    y: float
    home_x: float
    home_y: float
    hp: int
    max_hp: int
    state: str = "idle"
    direction_row: int = 0
    frame_index: int = 0
    frame_clock: float = 0.0
    patrol_clock: float = 0.0
    attack_cooldown: float = 0.0
    attack_pending: bool = False
    provoked_timer: float = 0.0

    @classmethod
    def create(cls, animal: str, x: float, y: float) -> "EnemyAI":
        max_hp = int(ANIMAL_STATS[animal]["hp"])
        return cls(animal, x, y, x, y, max_hp, max_hp)

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def display_size(self) -> float:
        return float(ANIMAL_STATS[self.animal]["size"])

    @property
    def hit_center(self) -> tuple[float, float]:
        return self.x, self.y + self.display_size * 0.42

    @property
    def hit_radius(self) -> float:
        return float(ANIMAL_STATS[self.animal]["hit_radius"])

    def _set_state(self, state: str) -> None:
        if self.state == state:
            return
        self.state = state
        self.frame_index = 0
        self.frame_clock = 0.0

    def take_damage(self, amount: int) -> int:
        if amount <= 0 or not self.alive:
            return 0
        previous = self.hp
        self.hp = max(0, self.hp - amount)
        self.provoked_timer = AI_PROVOKED_SECONDS
        self.attack_pending = False
        self._set_state("death" if self.hp == 0 else "hurt")
        return previous - self.hp

    def _face_vector(self, dx: float, dy: float) -> None:
        if math.hypot(dx, dy) <= 0.01:
            return
        angle = math.atan2(dy, dx)
        sector = round(angle / (math.pi / 4.0)) % 8
        self.direction_row = (sector + 2) % 8

    def _move_toward(
        self, target_x: float, target_y: float, dt: float, map_data: MapData
    ) -> None:
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)
        if distance <= 12.0:
            self._set_state("idle")
            return
        speed = float(ANIMAL_STATS[self.animal]["speed"])
        move_x = dx / distance * speed * dt
        move_y = dy / distance * speed * dt
        if self.animal == "crow":
            # Crows fly over ground props and collision tiles; resolving them
            # like walking animals makes the patrol visibly snag on scenery.
            next_x, next_y = self.x + move_x, self.y + move_y
        else:
            next_x, next_y = map_data.resolve_movement(
                self.x, self.y, move_x, move_y
            )
        moved_x = next_x - self.x
        moved_y = next_y - self.y
        self.x, self.y = next_x, next_y
        if math.hypot(moved_x, moved_y) > 0.01:
            self._face_vector(moved_x, moved_y)
            self._set_state("walk")
        else:
            self._set_state("idle")

    def update(
        self,
        dt: float,
        map_data: MapData,
        player: Player | None = None,
        affinity: int = AFFINITY_MAX,
        camera_zoom: float = 1.0,
    ) -> float:
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.provoked_timer = max(0.0, self.provoked_timer - dt)

        state_before = self.state
        if state_before in ("hurt", "death", "attack"):
            self._advance_animation(dt)
            if (
                state_before == "attack"
                and self.attack_pending
                and (self.frame_index >= 2 or self.state != "attack")
            ):
                self.attack_pending = False
                return float(ANIMAL_STATS[self.animal]["attack_damage"])
            return 0.0

        should_engage = False
        distance_screen = math.inf
        if player is not None and not player.dead:
            dx = player.x - self.x
            dy = player.y - self.y
            distance_screen = math.hypot(dx, dy) * camera_zoom
            relationship = affinity_relationship(affinity)
            detection_range = AI_DETECTION_SCREEN_RANGES[relationship]
            if self.provoked_timer > 0 and affinity < AFFINITY_MAX:
                detection_range = max(detection_range, AI_PROVOKED_SCREEN_RANGE)
            should_engage = detection_range > 0 and distance_screen <= detection_range

        if should_engage and player is not None:
            dx = player.x - self.x
            dy = player.y - self.y
            self._face_vector(dx, dy)
            attack_range = float(ANIMAL_STATS[self.animal]["attack_range"])
            if distance_screen <= attack_range:
                if self.attack_cooldown <= 0:
                    self._set_state("attack")
                    self.attack_pending = True
                    self.attack_cooldown = AI_ATTACK_COOLDOWN
                else:
                    self._set_state("idle")
            else:
                self._move_toward(player.x, player.y, dt, map_data)
        else:
            self.patrol_clock += dt
            radius = 150.0 if self.animal == "crow" else 105.0
            target_x = self.home_x + math.cos(self.patrol_clock * 0.65) * radius
            target_y = self.home_y + math.sin(self.patrol_clock * 0.47) * radius
            self._move_toward(target_x, target_y, dt, map_data)
        self._advance_animation(dt)
        return 0.0

    def _advance_animation(self, dt: float) -> None:
        frame_count, fps, loops = ANIMAL_ANIMATIONS[self.animal][self.state]
        self.frame_clock += dt
        frame_duration = 1.0 / fps
        while self.frame_clock >= frame_duration:
            self.frame_clock -= frame_duration
            if self.frame_index + 1 < frame_count:
                self.frame_index += 1
                continue
            if loops:
                self.frame_index = 0
            elif self.state in ("hurt", "attack"):
                self._set_state("idle")
            else:
                self.frame_index = frame_count - 1
                self.frame_clock = 0.0
            break


@dataclass(slots=True)
class WorldEntity:
    definition: WorldEntityDefinition
    hp: int
    visible: bool = True
    completed: bool = False
    cooldown_remaining: float = 0.0
    is_on: bool = False
    reward_claimed: bool = False

    @classmethod
    def create(cls, definition: WorldEntityDefinition) -> "WorldEntity":
        return cls(
            definition=definition,
            hp=max(1, int(definition.properties.get("hp", 1))),
            is_on=bool(definition.properties.get("is_on", False)),
        )

    @property
    def sprite_path(self) -> Path:
        if (
            self.definition.entity_type == "fruit_tree"
            and self.cooldown_remaining > 0
        ):
            return FRUIT_TREE_UNRIPE_SPRITE
        if self.definition.entity_type == "generator_switch":
            if not self.is_on and self.definition.alternate_sprite_path:
                return self.definition.alternate_sprite_path
        elif self.completed and self.definition.alternate_sprite_path:
            return self.definition.alternate_sprite_path
        return self.definition.sprite_path


def tiled_gid_transform(raw_gid: int) -> tuple[float, str]:
    """Convert Tiled's three flip bits to Pico2D rotation/flip values."""
    horizontal = bool(raw_gid & GID_HORIZONTAL_FLIP)
    vertical = bool(raw_gid & GID_VERTICAL_FLIP)
    diagonal = bool(raw_gid & GID_DIAGONAL_FLIP)
    if diagonal:
        if horizontal and vertical:
            return math.pi / 2, "h"
        if horizontal:
            return math.pi / 2, ""
        if vertical:
            return -math.pi / 2, ""
        return -math.pi / 2, "h"
    flip = ("h" if horizontal else "") + ("v" if vertical else "")
    return 0.0, flip


def frames_at(row: int, xs: tuple[int, ...] | list[int], flip: str = "") -> tuple[SpriteFrame, ...]:
    return tuple(SpriteFrame(x, row, flip) for x in xs)


IDLE_FRAMES: dict[str, tuple[SpriteFrame, ...]] = {
    "down": frames_at(0, (0, 32, 64)),
    # The source atlas stores the right-facing idle set before the left-facing set.
    "right": frames_at(0, (96, 128, 176)),
    "left": frames_at(0, (208, 240, 272)),
    "up": (SpriteFrame(0, 192),),
}

MOVE_FRAMES: dict[str, tuple[SpriteFrame, ...]] = {
    "left": frames_at(48, SIDE_MOVE_X),
    "right": frames_at(96, SIDE_MOVE_X),
    "down": frames_at(144, VERTICAL_MOVE_X),
    "up": frames_at(192, VERTICAL_MOVE_X),
}

# Front/back actions share clean poses. Horizontal actions use the atlas's real
# side-facing bodies so the character looks toward the swing direction.
VERTICAL_TOOL_FRAMES: dict[str, tuple[SpriteFrame, ...]] = {
    "down": frames_at(192, (176, 208, 240, 272)),
    "up": frames_at(144, (176, 208, 240, 272)),
}
SIDE_ACTION_FRAMES: dict[str, dict[str, tuple[SpriteFrame, ...]]] = {
    "attack": {
        "right": frames_at(288, (0, 32, 32, 0)),
        "left": frames_at(288, (64, 96, 96, 64)),
    },
    "axe": {
        "right": frames_at(288, (176, 208, 240, 272)),
        "left": frames_at(288, (176, 208, 240, 272), "h"),
    },
    "mine": {
        "right": frames_at(240, (176, 208, 240, 272)),
        "left": frames_at(240, (176, 208, 240, 272), "h"),
    },
    "fish": {
        "right": frames_at(432, (176, 208, 208, 176)),
        "left": frames_at(432, (240, 272, 272, 240)),
    },
}

ACTION_BODY_FRAMES: dict[str, dict[str, tuple[SpriteFrame, ...]]] = {
    state: {
        "down": VERTICAL_TOOL_FRAMES["down"],
        "up": VERTICAL_TOOL_FRAMES["up"],
        **side_frames,
    }
    for state, side_frames in SIDE_ACTION_FRAMES.items()
}

# Kept as a public alias for older preview/test code; only front/back bodies are
# intentionally unified now.
UNIFIED_ACTION_FRAMES = VERTICAL_TOOL_FRAMES

HURT_FRAMES: dict[str, tuple[SpriteFrame, ...]] = {
    "down": frames_at(384, (0, 32, 64)),
    "up": frames_at(432, (0, 32, 64)),
    "right": frames_at(480, (0, 32, 64)),
    "left": frames_at(528, (0, 32, 64)),
}

# Backwards-compatible public name used by tests and preview tooling.
ATTACK_FRAMES = ACTION_BODY_FRAMES["attack"]


class Player:
    WALK_SPEED = 150.0
    RUN_SPEED = 255.0

    def __init__(self, sprite_sheet: p2.Image) -> None:
        self.sprite_sheet = sprite_sheet
        self.x = WINDOW_WIDTH / 2
        self.y = 275.0  # feet position
        self.direction = "down"
        self.state = "idle"
        self.frame_index = 0
        self.frame_clock = 0.0
        self.dead = False
        self.max_hp = MAX_HP
        self.hp = self.max_hp
        self.max_sp = MAX_SP
        self.sp = self.max_sp
        self.stamina_exhausted = False

    def _frames_for_state(self) -> tuple[SpriteFrame, ...]:
        if self.state == "idle":
            return IDLE_FRAMES[self.direction]
        if self.state in ("walk", "run"):
            return MOVE_FRAMES[self.direction]
        if self.state == "hurt":
            return HURT_FRAMES[self.direction]
        if self.state in ("attack", "axe", "mine", "fish"):
            return ACTION_BODY_FRAMES[self.state][self.direction]
        if self.state == "death":
            base = {
                "left": IDLE_FRAMES["left"][0],
                "right": IDLE_FRAMES["right"][0],
                "down": IDLE_FRAMES["down"][0],
                "up": IDLE_FRAMES["up"][0],
            }[self.direction]
            return (base, base, base, base)

        return IDLE_FRAMES[self.direction]

    def _set_state(self, state: str) -> None:
        if state == self.state:
            return
        self.state = state
        self.frame_index = 0
        self.frame_clock = 0.0

    def start_action(self, action: str) -> bool:
        if self.dead and action != "death":
            return False
        if action not in ACTION_STATES:
            return False
        self.dead = action == "death"
        self.state = action
        self.frame_index = 0
        self.frame_clock = 0.0
        return True

    def revive(self) -> None:
        self.dead = False
        self.hp = self.max_hp
        self._set_state("idle")

    def take_damage(self, amount: float) -> float:
        if amount <= 0 or self.dead:
            return 0.0
        previous_hp = self.hp
        self.hp = max(0.0, self.hp - amount)
        damage_taken = previous_hp - self.hp
        if self.hp <= 0:
            self.start_action("death")
        else:
            self.start_action("hurt")
        return damage_taken

    def restore_hp(self, amount: float) -> float:
        if amount <= 0 or self.dead:
            return 0.0
        previous_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - previous_hp

    def update(
        self,
        dt: float,
        pressed: set[int],
        movement_resolver: Callable[[float, float, float, float], tuple[float, float]] | None = None,
    ) -> None:
        running = False
        moved = False
        if self.sp <= 0:
            self.stamina_exhausted = True
        if self.state not in ACTION_STATES:
            dx = float(p2.SDLK_d in pressed) - float(p2.SDLK_a in pressed)
            dy = float(p2.SDLK_w in pressed) - float(p2.SDLK_s in pressed)
            moving = dx != 0.0 or dy != 0.0
            if moving:
                if dx and dy:
                    scale = 1.0 / math.sqrt(2.0)
                    dx *= scale
                    dy *= scale
                if abs(dx) > 0 and (not dy or self.direction in ("left", "right")):
                    self.direction = "right" if dx > 0 else "left"
                elif dy:
                    self.direction = "up" if dy > 0 else "down"

                run_requested = (
                    p2.SDLK_LSHIFT in pressed or p2.SDLK_RSHIFT in pressed
                )
                running = (
                    run_requested
                    and not self.stamina_exhausted
                    and self.sp > 0
                )
                speed = self.RUN_SPEED if running else self.WALK_SPEED
                move_x = dx * speed * dt
                move_y = dy * speed * dt
                previous_x, previous_y = self.x, self.y
                if movement_resolver is None:
                    self.x += move_x
                    self.y += move_y
                    self.x = max(CHARACTER_WIDTH / 2, min(WINDOW_WIDTH - CHARACTER_WIDTH / 2, self.x))
                    self.y = max(155.0, min(WINDOW_HEIGHT - CHARACTER_HEIGHT - 15.0, self.y))
                else:
                    self.x, self.y = movement_resolver(self.x, self.y, move_x, move_y)
                moved = not (
                    math.isclose(self.x, previous_x)
                    and math.isclose(self.y, previous_y)
                )
                self._set_state("run" if running else "walk")
            else:
                self._set_state("idle")

        if running and moved:
            self.sp = max(0.0, self.sp - SP_DRAIN_PER_SECOND * dt)
            if self.sp <= 0:
                self.stamina_exhausted = True
        elif self.state in ("idle", "walk"):
            self.sp = min(self.max_sp, self.sp + SP_RECOVERY_PER_SECOND * dt)
            if self.stamina_exhausted and self.sp >= SP_RUN_RESTART_THRESHOLD:
                self.stamina_exhausted = False

        self._advance_animation(dt)

    def _advance_animation(self, dt: float) -> None:
        frames = self._frames_for_state()
        if len(frames) <= 1:
            self.frame_index = 0
            return
        self.frame_clock += dt
        frame_duration = 1.0 / STATE_FPS[self.state]
        while self.frame_clock >= frame_duration:
            self.frame_clock -= frame_duration
            next_index = self.frame_index + 1
            if next_index < len(frames):
                self.frame_index = next_index
                continue
            if self.state == "death":
                self.frame_index = len(frames) - 1
                self.frame_clock = 0.0
                break
            if self.state in ACTION_STATES:
                self.state = "idle"
                self.frame_index = 0
                self.frame_clock = 0.0
                break
            self.frame_index = 0

    def draw(
        self,
        x: float | None = None,
        y: float | None = None,
        display_scale: float = 1.0,
    ) -> None:
        frames = self._frames_for_state()
        frame = frames[min(self.frame_index, len(frames) - 1)]
        source_bottom = self.sprite_sheet.h - frame.top - FRAME_HEIGHT
        offset_x, offset_y, rotation = self._state_transform()
        draw_x = self.x if x is None else x
        draw_y = self.y if y is None else y
        self.sprite_sheet.clip_composite_draw(
            frame.left,
            source_bottom,
            FRAME_WIDTH,
            FRAME_HEIGHT,
            rotation,
            frame.flip,
            draw_x + offset_x * display_scale,
            draw_y + (CHARACTER_HEIGHT / 2 + offset_y) * display_scale,
            CHARACTER_WIDTH * display_scale,
            CHARACTER_HEIGHT * display_scale,
        )

    def _state_transform(self) -> tuple[float, float, float]:
        """Add recoil and a full-body fall where the source atlas is static."""
        if self.state == "hurt":
            phase = min(self.frame_index, 2)
            recoil = (14.0, -8.0, 0.0)[phase]
            rotation = (-0.10, 0.06, 0.0)[phase]
            if self.direction == "right":
                return -recoil, 0.0, rotation
            if self.direction == "left":
                return recoil, 0.0, -rotation
            if self.direction == "up":
                return 0.0, -recoil, rotation
            return 0.0, recoil, -rotation
        if self.state == "death":
            phase = min(self.frame_index, 3)
            side = -1.0 if self.direction == "left" else 1.0
            x = (0.0, 14.0, 34.0, 55.0)[phase] * side
            y = (0.0, -12.0, -42.0, -88.0)[phase]
            angle = (0.0, 0.42, 0.95, math.pi / 2)[phase] * side
            return x, y, angle
        return 0.0, 0.0, 0.0


class GameUI:
    INVENTORY_RECT = Rect(WINDOW_WIDTH / 2, 405, 630, 420)
    CRAFTING_RECT = Rect(WINDOW_WIDTH / 2, 370, 1140, 590)
    HOTBAR_RECT = Rect(WINDOW_WIDTH / 2, 87, 520, 173)
    TOOL_PANEL_RECT = Rect(1068, 76, 132, 131)
    ARMOR_PANEL_RECT = Rect(1207, 76, 132, 127)

    INVENTORY_SOURCE_CENTERS = (
        (294, 313), (534, 313), (774, 313), (1014, 313), (1255, 313),
        (294, 546), (534, 546), (774, 546), (1014, 546), (1255, 546),
        (294, 782), (534, 782), (774, 782), (1014, 782), (1255, 782),
    )
    HOTBAR_SOURCE_X = (420, 755, 1089, 1423, 1760)

    def __init__(self, model: InventoryModel) -> None:
        self.model = model
        self.inventory_image = p2.load_image(str(ASSET_DIR / "inventory.png"))
        self.hotbar_image = p2.load_image(str(ASSET_DIR / "hotbar.png"))
        self.tool_image = p2.load_image(str(ASSET_DIR / "tool.png"))
        self.armor_image = p2.load_image(str(ASSET_DIR / "armor.png"))
        self.item_images: dict[str, p2.Image] = {}
        for item_id, definition in ITEMS.items():
            thumbnail = GENERATED_ICON_DIR / definition.icon_filename
            source = thumbnail if thumbnail.exists() else ASSET_DIR / definition.icon_filename
            self.item_images[item_id] = p2.load_image(str(source))

        font_regular = Path("C:/Windows/Fonts/malgun.ttf")
        font_bold = Path("C:/Windows/Fonts/malgunbd.ttf")
        self.font_small = p2.load_font(str(font_regular), 15)
        self.font = p2.load_font(str(font_bold), 18)
        self.font_title = p2.load_font(str(font_bold), 23)

    @staticmethod
    def _source_to_screen(panel: Rect, source_w: float, source_h: float, sx: float, sy: float) -> tuple[float, float]:
        x = panel.left + panel.width * (sx / source_w)
        y = panel.top - panel.height * (sy / source_h)
        return x, y

    def inventory_slots(self) -> list[tuple[SlotRef, Rect]]:
        result: list[tuple[SlotRef, Rect]] = []
        for index, (sx, sy) in enumerate(self.INVENTORY_SOURCE_CENTERS):
            x, y = self._source_to_screen(self.INVENTORY_RECT, 1536, 1024, sx, sy)
            result.append((SlotRef.inventory(index), Rect(x, y, 78, 78)))
        return result

    def hotbar_slots(self) -> list[tuple[SlotRef, Rect]]:
        result: list[tuple[SlotRef, Rect]] = []
        for index, sx in enumerate(self.HOTBAR_SOURCE_X):
            x, y = self._source_to_screen(self.HOTBAR_RECT, 2172, 724, sx, 376)
            result.append((SlotRef.hotbar(index), Rect(x, y, 62, 62)))
        return result

    def equipment_slots(self) -> list[tuple[SlotRef, Rect]]:
        return [
            (SlotRef.tool(), Rect(self.TOOL_PANEL_RECT.cx, 70, 78, 78)),
            (SlotRef.armor(), Rect(self.ARMOR_PANEL_RECT.cx, 70, 78, 78)),
        ]

    def crafting_cards(self) -> list[tuple[CraftingRecipe, Rect]]:
        cards: list[tuple[CraftingRecipe, Rect]] = []
        card_width = 532.0
        card_height = 69.0
        for index, recipe in enumerate(CRAFTING_RECIPES):
            column = index % 2
            row = index // 2
            left = self.CRAFTING_RECT.left + 16 + column * 560
            top = self.CRAFTING_RECT.top - 61 - row * 73
            cards.append(
                (
                    recipe,
                    Rect(
                        left + card_width / 2,
                        top - card_height / 2,
                        card_width,
                        card_height,
                    ),
                )
            )
        return cards

    def crafting_recipe_at(self, x: float, y: float) -> CraftingRecipe | None:
        for recipe, rect in self.crafting_cards():
            if rect.contains(x, y):
                return recipe
        return None

    def slot_at(self, x: float, y: float, inventory_open: bool) -> SlotRef | None:
        groups: list[list[tuple[SlotRef, Rect]]] = []
        if inventory_open:
            groups.append(self.inventory_slots())
        groups.extend((self.hotbar_slots(), self.equipment_slots()))
        for group in groups:
            for ref, rect in group:
                if rect.contains(x, y):
                    return ref
        return None

    def draw(
        self,
        inventory_open: bool,
        crafting_open: bool,
        drag: DragState | None,
        toast: str,
        toast_error: bool,
        hovered_slot: SlotRef | None,
        mouse_x: float,
        mouse_y: float,
    ) -> None:
        self.hotbar_image.draw(
            self.HOTBAR_RECT.cx,
            self.HOTBAR_RECT.cy,
            self.HOTBAR_RECT.width,
            self.HOTBAR_RECT.height,
        )
        self.tool_image.draw(
            self.TOOL_PANEL_RECT.cx,
            self.TOOL_PANEL_RECT.cy,
            self.TOOL_PANEL_RECT.width,
            self.TOOL_PANEL_RECT.height,
        )
        self.armor_image.draw(
            self.ARMOR_PANEL_RECT.cx,
            self.ARMOR_PANEL_RECT.cy,
            self.ARMOR_PANEL_RECT.width,
            self.ARMOR_PANEL_RECT.height,
        )

        skip = self.model.canonical_ref(drag.source) if drag else None
        for ref, rect in self.hotbar_slots():
            self._draw_stack(ref, rect, skip)
        for ref, rect in self.equipment_slots():
            self._draw_stack(ref, rect, skip)

        if inventory_open:
            self.inventory_image.draw(
                self.INVENTORY_RECT.cx,
                self.INVENTORY_RECT.cy,
                self.INVENTORY_RECT.width,
                self.INVENTORY_RECT.height,
            )
            self.font_title.draw(self.INVENTORY_RECT.left + 74, self.INVENTORY_RECT.top - 28, "INVENTORY", (255, 226, 166))
            for ref, rect in self.inventory_slots():
                self._draw_stack(ref, rect, skip)

        if crafting_open:
            self._draw_crafting()

        self.font.draw(1000, 146, "TOOL BAR", (255, 225, 165))
        self.font.draw(1161, 146, "ARMOR", (255, 225, 165))
        armor = self.model.armor_slot
        if armor is not None and armor.durability is not None:
            armor_status = f"내구 {armor.durability}/{armor.definition.max_durability}"
        else:
            armor_status = "방어구 없음"
        self.font_small.draw(1144, 17, armor_status, (235, 242, 255))

        if drag:
            self.item_images[drag.item_id].draw(drag.x, drag.y, 70, 70)
        if toast:
            color = (255, 125, 115) if toast_error else (255, 237, 176)
            p2.draw_rectangle(376, 655, 904, 700, 28, 24, 22, 220, True)
            self.font.draw(405, 677, toast, color)
        if hovered_slot is not None:
            self._draw_durability_tooltip(hovered_slot, mouse_x, mouse_y)

    def _draw_crafting(self) -> None:
        panel = self.CRAFTING_RECT
        p2.draw_rectangle(
            panel.left - 5,
            panel.bottom - 5,
            panel.right + 5,
            panel.top + 5,
            113,
            76,
            39,
            248,
            True,
        )
        p2.draw_rectangle(
            panel.left,
            panel.bottom,
            panel.right,
            panel.top,
            43,
            29,
            23,
            246,
            True,
        )
        self.font_title.draw(panel.left + 22, panel.top - 37, "CRAFTING", (255, 226, 166))
        self.font_small.draw(
            panel.right - 225,
            panel.top - 34,
            "C 닫기 · 카드 클릭 제작",
            (226, 207, 166),
        )

        for recipe, card in self.crafting_cards():
            ready = self.model.has_recipe_ingredients(recipe)
            border = (89, 157, 83) if ready else (126, 84, 50)
            p2.draw_rectangle(
                card.left,
                card.bottom,
                card.right,
                card.top,
                *border,
                255,
                True,
            )
            p2.draw_rectangle(
                card.left + 2,
                card.bottom + 2,
                card.right - 2,
                card.top - 2,
                68,
                43,
                29,
                248,
                True,
            )
            self.item_images[recipe.output_item_id].draw(
                card.left + 38, card.cy, 54, 54
            )
            self.font.draw(
                card.left + 76,
                card.top - 25,
                recipe.output.label,
                (255, 228, 174),
            )
            status = "제작 가능" if ready else "재료 부족"
            status_color = (116, 232, 112) if ready else (255, 104, 96)
            self.font_small.draw(card.right - 82, card.top - 23, status, status_color)
            for ingredient_index, (item_id, needed) in enumerate(recipe.ingredients):
                owned = self.model.item_count(item_id)
                enough = owned >= needed
                text_color = (117, 235, 112) if enough else (255, 105, 98)
                self.font_small.draw(
                    card.left + 76 + ingredient_index * 135,
                    card.bottom + 12,
                    f"{ITEMS[item_id].label} {needed}/{owned}",
                    text_color,
                )

    def draw_status_bars(self, player: Player) -> None:
        def draw_bar(
            label: str,
            bottom: float,
            ratio: float,
            fill_color: tuple[int, int, int],
        ) -> None:
            bar_left = 51.0
            bar_right = 216.0
            bar_top = bottom + 18.0
            p2.draw_rectangle(
                12, bottom - 4, 216, bar_top + 4, 18, 23, 22, 215, True
            )
            p2.draw_rectangle(
                bar_left, bottom, bar_right, bar_top, 40, 42, 40, 255, True
            )
            fill_right = bar_left + (bar_right - bar_left) * min(max(ratio, 0.0), 1.0)
            if fill_right > bar_left:
                p2.draw_rectangle(
                    bar_left,
                    bottom,
                    fill_right,
                    bar_top,
                    *fill_color,
                    255,
                    True,
                )
            p2.draw_rectangle(
                bar_left,
                bottom,
                bar_right,
                bar_top,
                235,
                224,
                194,
                255,
                False,
            )
            self.font_small.draw(19, bottom + 2, label, (255, 238, 205))

        draw_bar("HP", 649, player.hp / player.max_hp, (205, 54, 65))
        draw_bar("SP", 617, player.sp / player.max_sp, (224, 171, 54))

    def _draw_stack(self, ref: SlotRef, rect: Rect, skip: SlotRef | None) -> None:
        canonical = self.model.canonical_ref(ref)
        if skip is not None and canonical == skip:
            return
        stack = self.model.get(canonical)
        if stack is None:
            return
        size = min(rect.width, rect.height) * 0.78
        self.item_images[stack.item_id].draw(rect.cx, rect.cy, size, size)
        if stack.count > 1:
            self.font_small.draw(rect.right - 24, rect.bottom + 12, str(stack.count), (255, 255, 255))
        ratio = stack.durability_ratio
        if ratio is not None:
            bar_left = rect.left + 5
            bar_right = rect.right - 5
            bar_bottom = rect.bottom + 3
            bar_top = bar_bottom + 6
            if ratio > 0.5:
                color = (80, 201, 104)
            elif ratio > 0.25:
                color = (232, 167, 62)
            else:
                color = (218, 67, 72)
            p2.draw_rectangle(
                bar_left - 1,
                bar_bottom - 1,
                bar_right + 1,
                bar_top + 1,
                20,
                23,
                22,
                235,
                True,
            )
            if ratio > 0:
                p2.draw_rectangle(
                    bar_left,
                    bar_bottom,
                    bar_left + (bar_right - bar_left) * ratio,
                    bar_top,
                    *color,
                    255,
                    True,
                )

    def _draw_durability_tooltip(
        self, ref: SlotRef, mouse_x: float, mouse_y: float
    ) -> None:
        stack = self.model.get(ref)
        if stack is None or stack.durability is None:
            return
        maximum = stack.definition.max_durability
        text = f"{stack.definition.label} · 내구도 {stack.durability}/{maximum}"
        width = max(178.0, 16.0 + len(text) * 9.0)
        left = min(max(mouse_x + 14.0, 8.0), WINDOW_WIDTH - width - 8.0)
        bottom = mouse_y + 16.0
        if bottom + 34.0 > WINDOW_HEIGHT:
            bottom = mouse_y - 42.0
        p2.draw_rectangle(
            left,
            bottom,
            left + width,
            bottom + 32.0,
            24,
            27,
            25,
            242,
            True,
        )
        p2.draw_rectangle(
            left,
            bottom,
            left + width,
            bottom + 32.0,
            220,
            203,
            160,
            255,
            False,
        )
        self.font_small.draw(left + 9.0, bottom + 9.0, text, (255, 241, 204))

    def draw_equipped_world_tool(
        self,
        player: Player,
        *,
        behind: bool,
        x: float | None = None,
        y: float | None = None,
        display_scale: float = 1.0,
    ) -> None:
        """Draw held items and front/back action arcs."""
        stack = self.model.tool_slot
        if stack is None:
            return

        image = self.item_images[stack.item_id]
        draw_x = player.x if x is None else x
        draw_y = player.y if y is None else y
        if player.state in ("idle", "walk", "run"):
            is_behind = player.direction == "up"
            if behind != is_behind:
                return
            offsets = {
                "right": (43.0, 82.0),
                "left": (-43.0, 82.0),
                "down": (38.0, 76.0),
                "up": (-34.0, 82.0),
            }
            rotations = {"right": 0.0, "left": 0.0, "down": -0.18, "up": 0.18}
            offset_x, offset_y = offsets[player.direction]
            image.composite_draw(
                rotations[player.direction],
                "h" if player.direction == "left" else "",
                draw_x + offset_x * display_scale,
                draw_y + offset_y * display_scale,
                48 * display_scale,
                48 * display_scale,
            )
            return

        definition = ITEMS[stack.item_id]
        if (
            player.state not in ("attack", "axe", "mine", "fish")
            or definition.action != player.state
        ):
            return

        # Side-facing action frames already contain their matching swung tool.
        # Drawing the inventory icon again would create a doubled weapon.
        if player.direction in ("left", "right"):
            return

        is_behind = player.direction == "up"
        if behind != is_behind:
            return
        phase = min(player.frame_index, 3)
        front_paths = {
            "axe": (
                ((34.0, 105.0, 0.72), (22.0, 91.0, 0.25), (-4.0, 65.0, -0.68), (27.0, 87.0, 0.15)),
                62,
            ),
            "mine": (
                ((-31.0, 105.0, -0.58), (-17.0, 90.0, -0.18), (8.0, 60.0, 0.62), (-22.0, 85.0, -0.08)),
                62,
            ),
            "fish": (
                ((28.0, 100.0, -0.34), (38.0, 89.0, 0.02), (45.0, 78.0, 0.38), (32.0, 92.0, 0.04)),
                68,
            ),
            "attack": (
                ((39.0, 101.0, 0.72), (24.0, 88.0, 0.24), (-8.0, 62.0, -0.70), (29.0, 86.0, 0.12)),
                66,
            ),
        }
        back_paths = {
            "axe": (
                ((-43.0, 105.0, -0.72), (-35.0, 91.0, -0.25), (39.0, 65.0, 0.68), (-34.0, 87.0, -0.15)),
                62,
            ),
            "mine": (
                ((43.0, 105.0, 0.58), (35.0, 90.0, 0.18), (-39.0, 60.0, -0.62), (35.0, 85.0, 0.08)),
                62,
            ),
            "fish": (
                ((-35.0, 100.0, 0.34), (-42.0, 89.0, -0.02), (-47.0, 78.0, -0.38), (-36.0, 92.0, -0.04)),
                68,
            ),
            "attack": (
                ((-45.0, 101.0, -0.72), (-34.0, 88.0, -0.24), (42.0, 62.0, 0.70), (-35.0, 86.0, -0.12)),
                66,
            ),
        }
        path, size = (back_paths if is_behind else front_paths)[player.state]
        offset_x, offset_y, rotation = path[phase]
        flip = "h" if is_behind else ""
        if player.direction == "left":
            offset_x = -offset_x
            rotation = -rotation
            flip = "h"
        image.composite_draw(
            rotation,
            flip,
            draw_x + offset_x * display_scale,
            draw_y + offset_y * display_scale,
            size * display_scale,
            size * display_scale,
        )


class Game:
    def __init__(self) -> None:
        if not CHARACTER_SHEET.exists():
            raise FileNotFoundError(
                f"Missing coloured character sheet: {CHARACTER_SHEET}\n"
                "Run: python CrowGame/tools/extract_character_sheet.py, then "
                "powershell -ExecutionPolicy Bypass -File CrowGame/tools/style_character_sheet.ps1"
            )
        self.model = InventoryModel.demo()
        self.player = Player(p2.load_image(str(CHARACTER_SHEET)))
        self.ui = GameUI(self.model)
        self._map_cache: dict[str, MapData] = {}
        self._background_cache: dict[str, p2.Image] = {}
        self._world_image_cache: dict[Path, p2.Image] = {}
        self._animal_image_cache: dict[tuple[str, str], p2.Image] = {}
        self.world_drops: dict[str, list[WorldDrop]] = {}
        self.placed_utilities: dict[str, list[PlacedUtility]] = {}
        self.world_entities: dict[str, list[WorldEntity]] = {}
        self.enemies: dict[str, list[EnemyAI]] = {}
        self.projectiles: dict[str, list[ThrownProjectile]] = {}
        self.species_affinity = {species: 0 for species in SPECIES_LABELS}
        self.map_data: MapData
        self.map_background: p2.Image | None
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.camera_zoom = CAMERA_ZOOM
        self.transition_armed = False
        self.ending_timer = 0.0
        self.ending_variant = ""
        self.running = True
        self.inventory_open = False
        self.crafting_open = False
        self.pressed: set[int] = set()
        self.drag: DragState | None = None
        self.mouse_screen_x = WINDOW_WIDTH * 0.72
        self.mouse_screen_y = WINDOW_HEIGHT * 0.55
        self.toast = "마우스: 조준/투척 | E: 상호작용 | Space: 도구 | Tab: 인벤토리"
        self.toast_error = False
        self.toast_timer = 5.0
        self._load_map(FIRST_MAP, "player_start")

    def show_toast(self, message: str, *, error: bool = False, seconds: float = 2.2) -> None:
        self.toast = message
        self.toast_error = error
        self.toast_timer = seconds

    def _adjust_species_affinity(self, species: str, amount: int) -> int:
        current = self.species_affinity[species]
        updated = min(max(current + amount, 0), AFFINITY_MAX)
        self.species_affinity[species] = updated
        return updated

    def _wear_equipped_item(
        self, ref: SlotRef, amount: int
    ) -> tuple[bool, int | None, str]:
        stack = self.model.get(ref)
        if stack is None or stack.durability is None:
            return False, None, ""
        label = stack.definition.label
        broke = stack.lose_durability(amount)
        remaining = stack.durability
        if broke:
            self.model.take(ref)
        return broke, remaining, label

    def damage_player(self, amount: float) -> float:
        armor = self.model.armor_slot
        if armor is not None and armor.durability is not None:
            maximum = armor.definition.max_durability
            broke, remaining, label = self._wear_equipped_item(
                SlotRef.armor(), 2
            )
            if broke:
                self.show_toast(
                    f"{label}이(가) 공격을 막고 파괴되었습니다 · HP 피해 없음",
                    error=True,
                )
            else:
                self.show_toast(
                    f"{label}이(가) 공격을 막았습니다 · 내구도 {remaining}/{maximum}",
                    error=True,
                )
            return 0.0
        mitigated = max(1.0, amount - self.model.defense)
        damage_taken = self.player.take_damage(mitigated)
        if damage_taken <= 0:
            return 0.0
        if self.player.dead:
            self.show_toast("HP가 모두 소진되어 쓰러졌습니다", error=True)
        else:
            self.show_toast("공격을 받아 HP가 감소했습니다", error=True)
        return damage_taken

    def handle_events(self) -> None:
        for event in p2.get_events():
            if event.type == p2.SDL_QUIT:
                self.running = False
            elif event.type == p2.SDL_KEYDOWN:
                self._key_down(event)
            elif event.type == p2.SDL_KEYUP:
                self.pressed.discard(event.key)
            elif event.type == p2.SDL_MOUSEBUTTONDOWN and event.button == p2.SDL_BUTTON_LEFT:
                x, y = event.x, WINDOW_HEIGHT - 1 - event.y
                self._aim_at_screen(x, y)
                if self.crafting_open:
                    recipe = self.ui.crafting_recipe_at(x, y)
                    if recipe is not None:
                        self._craft_recipe(recipe)
                    continue
                source = self.ui.slot_at(x, y, self.inventory_open)
                if source is not None:
                    stack = self.model.get(source)
                    if stack:
                        self.drag = DragState(source, stack.item_id, x, y)
                    continue
                if not self.inventory_open:
                    self._throw_equipped_at_screen(x, y)
            elif event.type == p2.SDL_MOUSEMOTION:
                x, y = event.x, WINDOW_HEIGHT - 1 - event.y
                self._aim_at_screen(x, y)
                if self.drag:
                    self.drag.x = x
                    self.drag.y = y
            elif event.type == p2.SDL_MOUSEBUTTONUP and event.button == p2.SDL_BUTTON_LEFT:
                self._finish_drag(event.x, WINDOW_HEIGHT - 1 - event.y)

    def _key_down(self, event: object) -> None:
        key = event.key
        repeated = bool(getattr(event, "repeat", 0))
        if key in (p2.SDLK_w, p2.SDLK_a, p2.SDLK_s, p2.SDLK_d, p2.SDLK_LSHIFT, p2.SDLK_RSHIFT):
            self.pressed.add(key)
            return
        if repeated:
            return
        if key == p2.SDLK_ESCAPE:
            self.running = False
        elif key == p2.SDLK_TAB:
            self.inventory_open = not self.inventory_open
            if self.inventory_open:
                self.crafting_open = False
            self.drag = None
        elif key == p2.SDLK_c:
            self.crafting_open = not self.crafting_open
            if self.crafting_open:
                self.inventory_open = False
            self.drag = None
        elif key == p2.SDLK_SPACE:
            self._use_tool()
        elif key == p2.SDLK_e:
            if not self._interact_world():
                self._use_equipped_with_e()
        elif key == p2.SDLK_h:
            self.damage_player(10.0)
        elif key == p2.SDLK_k:
            if self.player.take_damage(self.player.hp) > 0:
                self.show_toast("쓰러졌습니다. R 키로 일어나기")
        elif key == p2.SDLK_r:
            self.player.revive()
            self.show_toast("다시 일어났습니다")

    def _use_tool(self) -> None:
        tool = self.model.equipped_tool_definition
        if tool is None:
            self.show_toast("툴바에 아이템을 먼저 넣으세요", error=True)
            return
        if tool.item_id in INSTALLABLE_ITEM_IDS:
            self.show_toast(f"{tool.label}: E 키로 설치할 수 있습니다")
            return
        if tool.heal_amount > 0:
            self.show_toast(f"{tool.label}: E 키로 먹을 수 있습니다")
            return
        if tool.item_id == "stone":
            self.show_toast(f"{tool.label}: 마우스로 조준하고 좌클릭해 던집니다")
            return
        if tool.action == "torch":
            self.show_toast("횃불을 밝혔습니다")
            return
        if tool.action and self.player.start_action(tool.action):
            labels = {"attack": "공격", "axe": "도끼질", "mine": "채광", "fish": "낚시"}
            if tool.action == "attack" and tool.item_id in MELEE_DAMAGE:
                enemy = self._nearest_melee_enemy()
                if enemy is not None:
                    damage = enemy.take_damage(MELEE_DAMAGE[tool.item_id])
                    durability_text = ""
                    if tool.item_id in ("wooden_sword", "stone_sword"):
                        broke, remaining, label = self._wear_equipped_item(
                            SlotRef.tool(), 4
                        )
                        durability_text = (
                            f" · {label} 파괴"
                            if broke
                            else f" · 내구도 {remaining}/{tool.max_durability}"
                        )
                    affinity = self._adjust_species_affinity(
                        enemy.animal, -AFFINITY_LOSS_PER_HIT
                    )
                    self.show_toast(
                        f"{self._enemy_label(enemy)} 근접 명중 · {damage} 피해 · "
                        f"호감도 -{AFFINITY_LOSS_PER_HIT} ({affinity}/100)"
                        f"{durability_text}",
                        seconds=1.7,
                    )
                    return
            self.show_toast(f"{tool.label}: {labels.get(tool.action, tool.action)}")

    def _use_equipped_with_e(self) -> None:
        stack = self.model.tool_slot
        if stack is not None and stack.definition.heal_amount > 0:
            self._consume_equipped_food()
            return
        if stack is not None and stack.item_id in INSTALLABLE_ITEM_IDS:
            self._place_utility(stack.item_id)
            return
        self._use_tool()

    def _consume_equipped_food(self) -> None:
        stack = self.model.tool_slot
        if stack is None or stack.definition.heal_amount <= 0:
            return
        if self.player.dead:
            self.show_toast("쓰러진 상태에서는 먹을 수 없습니다", error=True)
            return
        label = stack.definition.label
        heal_amount = stack.definition.heal_amount
        consumed = self.model.take(SlotRef.tool(), 1)
        if consumed is None:
            return
        restored = self.player.restore_hp(heal_amount)
        if restored > 0:
            self.show_toast(
                f"{label} 1개 섭취 · HP +{int(restored)} "
                f"({int(self.player.hp)}/{int(self.player.max_hp)})"
            )
        else:
            self.show_toast(f"{label} 1개 섭취 · HP가 이미 가득 찼습니다")

    def _craft_recipe(self, recipe: CraftingRecipe) -> None:
        if not self.model.has_recipe_ingredients(recipe):
            self.show_toast(
                f"{recipe.output.label}: 재료가 부족합니다", error=True
            )
            return
        if not self.model.craft(recipe):
            self.show_toast("인벤토리에 완성품을 넣을 공간이 없습니다", error=True)
            return
        self.show_toast(f"{recipe.output.label} 제작 완료")

    def _current_entities(self) -> list[WorldEntity]:
        return self.world_entities.setdefault(self.map_data.name, [])

    def _current_enemies(self) -> list[EnemyAI]:
        return self.enemies.setdefault(self.map_data.name, [])

    def _current_projectiles(self) -> list[ThrownProjectile]:
        return self.projectiles.setdefault(self.map_data.name, [])

    def _nearest_melee_enemy(self) -> EnemyAI | None:
        direction_vectors = {
            "up": (0.0, 1.0),
            "down": (0.0, -1.0),
            "left": (-1.0, 0.0),
            "right": (1.0, 0.0),
        }
        facing_x, facing_y = direction_vectors[self.player.direction]
        nearest: EnemyAI | None = None
        nearest_distance = math.inf
        for enemy in self._current_enemies():
            if not enemy.alive:
                continue
            dx = enemy.x - self.player.x
            dy = enemy.y - self.player.y
            distance = math.hypot(dx, dy)
            if distance <= 0:
                alignment = 1.0
            else:
                alignment = (dx * facing_x + dy * facing_y) / distance
            if (
                distance * self.camera_zoom <= 145.0
                and alignment >= 0.15
                and distance < nearest_distance
            ):
                nearest = enemy
                nearest_distance = distance
        return nearest

    def _equipped_throwable_id(self) -> str | None:
        stack = self.model.tool_slot
        if stack is None or stack.item_id not in THROWABLE_ITEM_IDS:
            return None
        return stack.item_id

    def _aim_at_screen(self, x: float, y: float) -> None:
        self.mouse_screen_x = x
        self.mouse_screen_y = y
        if self._equipped_throwable_id() is None or self.player.dead:
            return
        target_x, target_y = self.screen_to_world(x, y)
        dx = target_x - self.player.x
        dy = target_y - (self.player.y + CHARACTER_HEIGHT * 0.22)
        if abs(dx) >= abs(dy):
            self.player.direction = "right" if dx >= 0 else "left"
        else:
            self.player.direction = "up" if dy >= 0 else "down"

    def _throw_target_world(self, screen_x: float, screen_y: float) -> tuple[float, float]:
        target_x, target_y = self.screen_to_world(screen_x, screen_y)
        start_x = self.player.x
        start_y = self.player.y + CHARACTER_HEIGHT * 0.34
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.hypot(dx, dy)
        maximum = PROJECTILE_MAX_SCREEN_RANGE / self.camera_zoom
        if distance > maximum and distance > 0:
            target_x = start_x + dx / distance * maximum
            target_y = start_y + dy / distance * maximum
        return (
            min(max(target_x, 8.0), self.map_data.width - 8.0),
            min(max(target_y, 8.0), self.map_data.height - 8.0),
        )

    def _throw_equipped_at_screen(self, screen_x: float, screen_y: float) -> bool:
        item_id = self._equipped_throwable_id()
        if item_id is None:
            return False
        if self.player.dead or self.player.state in ACTION_STATES:
            self.show_toast("현재 동작이 끝난 뒤 던질 수 있습니다", error=True)
            return False
        self._aim_at_screen(screen_x, screen_y)
        target_x, target_y = self._throw_target_world(screen_x, screen_y)
        start_x = self.player.x
        start_y = self.player.y + CHARACTER_HEIGHT * 0.34
        distance = math.hypot(target_x - start_x, target_y - start_y)
        if distance < 30.0 / self.camera_zoom:
            self.show_toast("조금 더 먼 곳을 조준하세요", error=True)
            return False
        if not self.player.start_action("attack"):
            return False
        thrown_stack = self.model.take(SlotRef.tool(), 1)
        if thrown_stack is None:
            return False
        world_speed = PROJECTILE_SCREEN_SPEED / self.camera_zoom
        self._current_projectiles().append(
            ThrownProjectile(
                item_id,
                start_x,
                start_y,
                target_x,
                target_y,
                max(0.18, distance / world_speed),
                PROJECTILE_ARC_SCREEN_HEIGHT / self.camera_zoom,
                thrown_stack.durability,
            )
        )
        self.show_toast(f"{ITEMS[item_id].label}을(를) 던졌습니다", seconds=1.3)
        return True

    def _current_placed_utilities(self) -> list[PlacedUtility]:
        return self.placed_utilities.setdefault(self.map_data.name, [])

    def _nearest_placed_utility(self) -> PlacedUtility | None:
        maximum_distance = PLACED_UTILITY_SCREEN_DISTANCE / self.camera_zoom
        nearest: PlacedUtility | None = None
        nearest_distance = math.inf
        for utility in self._current_placed_utilities():
            distance = math.hypot(
                utility.x - self.player.x, utility.y - self.player.y
            )
            if distance <= maximum_distance and distance < nearest_distance:
                nearest = utility
                nearest_distance = distance
        return nearest

    def _utility_placement_position(
        self, item_id: str
    ) -> tuple[float, float] | None:
        direction_vectors = {
            "up": (0.0, 1.0),
            "down": (0.0, -1.0),
            "left": (-1.0, 0.0),
            "right": (1.0, 0.0),
        }
        forward_x, forward_y = direction_vectors[self.player.direction]
        side_x, side_y = -forward_y, forward_x
        base_distance = UTILITY_PLACEMENT_SCREEN_DISTANCE / self.camera_zoom
        width, height = PLACED_UTILITY_WORLD_SIZES[item_id]
        obstacles = (*self.map_data.collisions, *self._dynamic_collisions())
        for distance_scale in (1.0, 1.25, 0.8, 1.5, 1.75):
            distance = base_distance * distance_scale
            for side_offset in (0.0, -0.35, 0.35, -0.7, 0.7, -1.0, 1.0):
                candidate_x = (
                    self.player.x
                    + forward_x * distance
                    + side_x * distance * side_offset
                )
                candidate_y = (
                    self.player.y
                    + forward_y * distance
                    + side_y * distance * side_offset
                )
                candidate_x = min(
                    max(candidate_x, width / 2), self.map_data.width - width / 2
                )
                candidate_y = min(
                    max(candidate_y, height / 2), self.map_data.height - height / 2
                )
                footprint = WorldRect(
                    candidate_x - width * 0.34,
                    candidate_y - height * 0.20,
                    width * 0.68,
                    height * 0.40,
                )
                if any(footprint.intersects(obstacle) for obstacle in obstacles):
                    continue
                overlaps_utility = False
                for utility in self._current_placed_utilities():
                    placed_width, placed_height = PLACED_UTILITY_WORLD_SIZES[
                        utility.item_id
                    ]
                    placed_footprint = WorldRect(
                        utility.x - placed_width * 0.34,
                        utility.y - placed_height * 0.20,
                        placed_width * 0.68,
                        placed_height * 0.40,
                    )
                    if footprint.intersects(placed_footprint):
                        overlaps_utility = True
                        break
                if not overlaps_utility:
                    return candidate_x, candidate_y
        return None

    def _place_utility(self, item_id: str) -> None:
        position = self._utility_placement_position(item_id)
        if position is None:
            self.show_toast("앞쪽에 설치할 공간이 없습니다", error=True)
            return
        stack = self.model.take(SlotRef.tool())
        if stack is None or stack.item_id != item_id:
            return
        self._current_placed_utilities().append(
            PlacedUtility(item_id, position[0], position[1])
        )
        self.show_toast(f"{ITEMS[item_id].label}을(를) 설치했습니다")

    def _pickup_placed_utility(self, utility: PlacedUtility) -> None:
        if self.model.add_item(utility.item_id, 1) != 0:
            self.show_toast("인벤토리에 회수할 공간이 없습니다", error=True)
            return
        self._current_placed_utilities().remove(utility)
        self.show_toast(f"{ITEMS[utility.item_id].label}을(를) 회수했습니다")

    @staticmethod
    def _entity_label(entity_type: str) -> str:
        return {
            "tree": "나무",
            "rock": "돌",
            "grass": "풀",
            "flower": "꽃",
            "fruit_tree": "과일나무",
            "generator_switch": "발전기",
            "bird's nest": "새 둥지",
            "rescue a bird": "새 구조",
            "hunter_trap_remove": "사냥꾼 덫",
            "wolf_pup_rescue": "새끼 늑대 구조",
            "wolf_den_repair": "늑대 굴 복구",
            "bear_cub_heal": "새끼 곰 치료",
            "bear_rescue": "곰 구조",
            "bear_water_restore": "물길 복원",
        }.get(entity_type, entity_type)

    def _nearest_interactable(self) -> WorldEntity | None:
        nearest: WorldEntity | None = None
        nearest_distance = math.inf
        maximum_distance = INTERACTION_SCREEN_DISTANCE / self.camera_zoom
        for entity in self._current_entities():
            if not entity.visible:
                continue
            rect = entity.definition.rect
            closest_x = min(max(self.player.x, rect.left), rect.right)
            closest_y = min(max(self.player.y, rect.bottom), rect.top)
            distance = math.hypot(self.player.x - closest_x, self.player.y - closest_y)
            if distance <= maximum_distance and distance < nearest_distance:
                nearest = entity
                nearest_distance = distance
        return nearest

    def _interact_world(self) -> bool:
        utility = self._nearest_placed_utility()
        if utility is not None:
            self._pickup_placed_utility(utility)
            return True
        held = self.model.tool_slot
        if held is not None and held.item_id in INSTALLABLE_ITEM_IDS:
            self._place_utility(held.item_id)
            return True
        entity = self._nearest_interactable()
        if entity is None:
            return False
        if entity.definition.kind == "resource":
            self._harvest_resource(entity)
        else:
            self._activate_event(entity)
        return True

    def _equipped_action_is(self, action: str) -> bool:
        tool = self.model.equipped_tool_definition
        return tool is not None and tool.action == action

    def _give_loot(self, item_id: str, count: int, x: float, y: float) -> tuple[int, int]:
        remainder = self.model.add_item(item_id, count)
        collected = count - remainder
        if remainder:
            self.world_drops.setdefault(self.map_data.name, []).append(
                WorldDrop(ItemStack(item_id, remainder), x, y)
            )
        return collected, remainder

    def _harvest_resource(self, entity: WorldEntity) -> None:
        resource_type = entity.definition.entity_type
        label = self._entity_label(resource_type)
        rect = entity.definition.rect

        if resource_type == "fruit_tree":
            if entity.cooldown_remaining > 0:
                self.show_toast(
                    f"사과가 다시 열리려면 {math.ceil(entity.cooldown_remaining)}초 남았습니다",
                    error=True,
                )
                return
            count = int(entity.definition.properties.get("fruit_count", 3))
            collected, remainder = self._give_loot(
                "fruit", count, rect.left + rect.width / 2, rect.bottom
            )
            entity.cooldown_remaining = FRUIT_COOLDOWN_SECONDS
            entity.completed = True
            suffix = f" · {remainder}개는 바닥에 떨어졌습니다" if remainder else ""
            self.show_toast(f"사과 {collected}개를 수확했습니다{suffix}")
            return

        required_action = {"tree": "axe", "rock": "mine"}.get(resource_type)
        if required_action and not self._equipped_action_is(required_action):
            required_label = "도끼" if required_action == "axe" else "곡괭이"
            self.show_toast(
                f"{label} 채집은 툴바에 {required_label}를 넣어야 합니다",
                error=True,
            )
            return
        if required_action and not self.player.start_action(required_action):
            return

        tool_broke = False
        broken_label = ""
        remaining_durability: int | None = None
        if required_action:
            tool_broke, remaining_durability, broken_label = (
                self._wear_equipped_item(SlotRef.tool(), 4)
            )

        entity.hp -= 1
        if entity.hp > 0:
            durability_text = (
                f" · {broken_label} 파괴"
                if tool_broke
                else f" · 내구도 {remaining_durability}"
            )
            self.show_toast(
                f"{label}: {entity.hp}번 더 채집해야 합니다{durability_text}"
            )
            return

        entity.visible = False
        item_id = str(entity.definition.properties.get("drop_item", "fiber"))
        count = int(entity.definition.properties.get("drop_count", 1))
        collected, remainder = self._give_loot(
            item_id, count, rect.left + rect.width / 2, rect.bottom
        )
        suffix = f" · {remainder}개는 바닥에 떨어졌습니다" if remainder else ""
        durability_text = f" · {broken_label} 파괴" if tool_broke else ""
        self.show_toast(
            f"{label}을(를) 수확해 {ITEMS[item_id].label} {collected}개 획득"
            f"{suffix}{durability_text}"
        )

    def _claim_event_reward(self, entity: WorldEntity, reward: int) -> str:
        species = MAP_SPECIES.get(self.map_data.name)
        if species is None or reward <= 0 or entity.reward_claimed:
            return ""
        entity.reward_claimed = True
        previous = self.species_affinity[species]
        updated = self._adjust_species_affinity(species, reward)
        gained = updated - previous
        return (
            f" · {SPECIES_LABELS[species]} 호감도 +{gained} "
            f"({updated}/{AFFINITY_MAX})"
        )

    def _activate_event(self, entity: WorldEntity) -> None:
        event_type = entity.definition.entity_type
        label = self._entity_label(event_type)
        if event_type != "generator_switch" and entity.completed:
            self.show_toast(f"{label} 이벤트는 이미 완료했습니다")
            return

        required_tool = str(entity.definition.properties.get("required_tool", ""))
        if required_tool:
            required_action = "mine" if required_tool == "pickaxe" else required_tool
            if not self._equipped_action_is(required_action):
                self.show_toast(f"{label}: 곡괭이를 장착해야 합니다", error=True)
                return
            if not self.player.start_action(required_action):
                return

        reward = int(entity.definition.properties.get("reward", 0))
        if event_type == "generator_switch":
            entity.is_on = not entity.is_on
            state_label = "켜짐" if entity.is_on else "꺼짐"
            reward_text = self._claim_event_reward(entity, reward)
            self.show_toast(f"발전기 {state_label}{reward_text}")
            return

        entity.completed = True
        if entity.definition.alternate_sprite_path is None:
            entity.visible = False
        reward_text = self._claim_event_reward(entity, reward)
        self.show_toast(f"{label} 완료{reward_text}")

    def _update_entity_timers(self, dt: float) -> None:
        for entities in self.world_entities.values():
            for entity in entities:
                if entity.cooldown_remaining <= 0:
                    continue
                entity.cooldown_remaining = max(0.0, entity.cooldown_remaining - dt)
                if entity.cooldown_remaining == 0:
                    entity.completed = False

    @staticmethod
    def _distance_to_segment(
        point_x: float,
        point_y: float,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
    ) -> float:
        segment_x = end_x - start_x
        segment_y = end_y - start_y
        length_squared = segment_x * segment_x + segment_y * segment_y
        if length_squared <= 0.0001:
            return math.hypot(point_x - start_x, point_y - start_y)
        projection = (
            (point_x - start_x) * segment_x
            + (point_y - start_y) * segment_y
        ) / length_squared
        projection = min(max(projection, 0.0), 1.0)
        closest_x = start_x + segment_x * projection
        closest_y = start_y + segment_y * projection
        return math.hypot(point_x - closest_x, point_y - closest_y)

    @staticmethod
    def _enemy_label(enemy: EnemyAI) -> str:
        return SPECIES_LABELS[enemy.animal]

    def _land_projectile(
        self, projectile: ThrownProjectile, x: float, y: float
    ) -> bool:
        durability = projectile.durability
        if projectile.item_id in ("wooden_spear", "stone_spear"):
            assert durability is not None
            durability = max(0, durability - 3)
            if durability == 0:
                return True
        self.world_drops.setdefault(self.map_data.name, []).append(
            WorldDrop(
                ItemStack(projectile.item_id, 1, durability),
                x,
                y,
                pickup_enabled=False,
                pickup_origin_x=projectile.start_x,
                pickup_origin_y=(
                    projectile.start_y - CHARACTER_HEIGHT * 0.34
                ),
            )
        )
        return False

    def _update_projectiles(self, dt: float) -> None:
        projectiles = self._current_projectiles()
        for projectile in tuple(projectiles):
            previous, current = projectile.advance(dt)
            if projectile.elapsed < 0:
                continue
            hit_enemy: EnemyAI | None = None
            for enemy in self._current_enemies():
                if not enemy.alive:
                    continue
                center_x, center_y = enemy.hit_center
                if self._distance_to_segment(
                    center_x,
                    center_y,
                    previous[0],
                    previous[1],
                    current[0],
                    current[1],
                ) <= enemy.hit_radius:
                    hit_enemy = enemy
                    break
            if hit_enemy is not None:
                damage = hit_enemy.take_damage(PROJECTILE_DAMAGE[projectile.item_id])
                affinity = self._adjust_species_affinity(
                    hit_enemy.animal, -AFFINITY_LOSS_PER_HIT
                )
                projectiles.remove(projectile)
                spear_broke = self._land_projectile(
                    projectile, hit_enemy.x, hit_enemy.y
                )
                durability_text = (
                    " · 창 파괴"
                    if spear_broke
                    else (
                        f" · 창 내구도 {projectile.durability - 3}"
                        if projectile.item_id in ("wooden_spear", "stone_spear")
                        else ""
                    )
                )
                label = self._enemy_label(hit_enemy)
                if hit_enemy.alive:
                    self.show_toast(
                        f"{label} 명중 · {damage} 피해 · HP {hit_enemy.hp}/{hit_enemy.max_hp} · "
                        f"호감도 -{AFFINITY_LOSS_PER_HIT} ({affinity}/100)"
                        f"{durability_text}",
                        seconds=1.7,
                    )
                else:
                    self.show_toast(
                        f"{label} 명중 · {damage} 피해 · 처치 · "
                        f"호감도 -{AFFINITY_LOSS_PER_HIT} ({affinity}/100)"
                        f"{durability_text}",
                        seconds=1.7,
                    )
                continue
            if projectile.landed:
                projectiles.remove(projectile)
                spear_broke = self._land_projectile(
                    projectile, projectile.target_x, projectile.target_y
                )
                if spear_broke:
                    self.show_toast("창이 착탄 충격으로 파괴되었습니다", error=True)

    def _update_enemies(self, dt: float) -> None:
        for enemy in self._current_enemies():
            damage = enemy.update(
                dt,
                self.map_data,
                self.player,
                self.species_affinity[enemy.animal],
                self.camera_zoom,
            )
            if damage > 0:
                self.damage_player(damage)

    def _dynamic_collisions(self) -> tuple[WorldRect, ...]:
        return tuple(
            entity.definition.collision_rect
            for entity in self._current_entities()
            if entity.visible and entity.definition.collision_rect is not None
        )

    def _resolve_player_movement(
        self, x: float, y: float, dx: float, dy: float
    ) -> tuple[float, float]:
        return self.map_data.resolve_movement(
            x,
            y,
            dx / self.camera_zoom,
            dy / self.camera_zoom,
            self._dynamic_collisions(),
        )

    def _random_drop_position(self) -> tuple[float, float]:
        minimum = THROWN_DROP_MIN_SCREEN_DISTANCE / self.camera_zoom
        maximum = THROWN_DROP_MAX_SCREEN_DISTANCE / self.camera_zoom
        extra_collisions = self._dynamic_collisions()
        for _ in range(32):
            angle = random.uniform(0.0, math.tau)
            distance = random.uniform(minimum, maximum)
            world_x = min(
                max(self.player.x + math.cos(angle) * distance, 12.0),
                self.map_data.width - 12.0,
            )
            world_y = min(
                max(self.player.y + math.sin(angle) * distance, 8.0),
                self.map_data.height - 8.0,
            )
            actual_distance = math.hypot(
                world_x - self.player.x, world_y - self.player.y
            )
            if actual_distance < minimum * 0.75:
                continue
            if not self.map_data._blocked(world_x, world_y, extra_collisions):
                return world_x, world_y
        return (
            min(max(self.player.x + minimum, 12.0), self.map_data.width - 12.0),
            min(max(self.player.y, 8.0), self.map_data.height - 8.0),
        )

    def _finish_drag(self, x: float, y: float) -> None:
        if not self.drag:
            return
        target = self.ui.slot_at(x, y, self.inventory_open)
        if target is None:
            stack = self.model.take(self.drag.source)
            if stack is not None:
                world_x, world_y = self._random_drop_position()
                self.world_drops.setdefault(self.map_data.name, []).append(
                    WorldDrop(
                        stack,
                        world_x,
                        world_y,
                        pickup_enabled=False,
                        large_icon=True,
                        pickup_origin_x=self.player.x,
                        pickup_origin_y=self.player.y,
                    )
                )
                self.show_toast(
                    f"{stack.definition.label}을(를) 캐릭터 주변에 던졌습니다",
                    seconds=1.5,
                )
        elif self.model.try_move(self.drag.source, target):
            self.show_toast("슬롯이 동기화되었습니다", seconds=1.2)
        else:
            target_name = "툴바" if target.area == "tool" else "방어구" if target.area == "armor" else "해당"
            self.show_toast(f"{target_name} 슬롯에 넣을 수 없는 아이템입니다", error=True)
        self.drag = None

    def _auto_pickup_world_items(self) -> None:
        drops = self.world_drops.setdefault(self.map_data.name, [])
        pickup_radius = AUTO_PICKUP_SCREEN_DISTANCE / self.camera_zoom
        legacy_rearm_radius = pickup_radius * 1.05
        collected_labels: list[str] = []
        for drop in tuple(drops):
            distance = math.hypot(drop.x - self.player.x, drop.y - self.player.y)
            if not drop.pickup_enabled:
                if (
                    drop.pickup_origin_x is not None
                    and drop.pickup_origin_y is not None
                ):
                    movement = math.hypot(
                        self.player.x - drop.pickup_origin_x,
                        self.player.y - drop.pickup_origin_y,
                    )
                    if movement * self.camera_zoom >= THROWN_DROP_REARM_MOVEMENT:
                        drop.pickup_enabled = True
                elif distance > legacy_rearm_radius:
                    drop.pickup_enabled = True
                if not drop.pickup_enabled:
                    continue
            if distance > pickup_radius:
                continue
            original_count = drop.stack.count
            remainder = self.model.add_stack(drop.stack)
            collected = original_count - remainder
            if collected == 0:
                continue
            collected_labels.append(f"{drop.stack.definition.label} {collected}개")
            if remainder:
                drop.stack.count = remainder
            else:
                drops.remove(drop)
        if collected_labels:
            self.show_toast(f"자동 획득: {', '.join(collected_labels)}", seconds=1.5)

    def _load_map(self, map_name: str, spawn_name: str) -> None:
        map_data = self._map_cache.get(map_name)
        reloaded = (
            map_data is None
            or not map_data.source_path.exists()
            or map_data.source_path.stat().st_mtime_ns != map_data.source_mtime_ns
        )
        if reloaded:
            map_data = load_map_data(map_name)
            self._map_cache[map_name] = map_data
        background = None
        if not map_data.tiles:
            background = self._background_cache.get(map_name)
            if background is None:
                background = p2.load_image(str(map_data.background_path))
                self._background_cache[map_name] = background
        self.map_data = map_data
        self.map_background = background
        self.player.x, self.player.y = map_data.spawn(spawn_name)
        self.player._set_state("idle")
        self.world_drops.setdefault(map_name, [])
        self.placed_utilities.setdefault(map_name, [])
        self.projectiles.setdefault(map_name, [])
        if reloaded or map_name not in self.world_entities:
            self.world_entities[map_name] = [
                WorldEntity.create(definition) for definition in map_data.entities
            ]
        if reloaded or map_name not in self.enemies:
            self.enemies[map_name] = self._spawn_map_enemies(map_data)
        self.camera_zoom = CAMERA_ZOOM
        self.transition_armed = False
        self._update_camera()

    @staticmethod
    def _spawn_map_enemies(map_data: MapData) -> list[EnemyAI]:
        kinds = MAP_AI_KINDS.get(map_data.name, ())
        if not kinds:
            return []
        anchor_x, anchor_y = map_data.spawn("player_start")
        result: list[EnemyAI] = []
        search_radii = (450.0, 600.0, 800.0, 1000.0)
        search_angles = (60.0, 90.0, 120.0, 30.0, 150.0, 0.0, 180.0)
        for index, animal in enumerate(kinds):
            spawn_x, spawn_y = anchor_x, anchor_y
            found = False
            for radius in search_radii:
                for angle_degrees in search_angles[index:] + search_angles[:index]:
                    angle = math.radians(angle_degrees)
                    candidate_x = anchor_x + math.cos(angle) * radius
                    candidate_y = anchor_y + math.sin(angle) * radius
                    if not (
                        50.0 <= candidate_x <= map_data.width - 50.0
                        and 50.0 <= candidate_y <= map_data.height - 50.0
                    ):
                        continue
                    if map_data._blocked(candidate_x, candidate_y):
                        continue
                    spawn_x, spawn_y = candidate_x, candidate_y
                    found = True
                    break
                if found:
                    break
            result.append(EnemyAI.create(animal, spawn_x, spawn_y))
        return result

    def _update_camera(self) -> None:
        viewport_width = WINDOW_WIDTH / self.camera_zoom
        viewport_height = WINDOW_HEIGHT / self.camera_zoom
        if self.map_data.width <= viewport_width:
            self.camera_x = self.map_data.width / 2
        else:
            self.camera_x = min(
                max(self.player.x, viewport_width / 2),
                self.map_data.width - viewport_width / 2,
            )
        if self.map_data.height <= viewport_height:
            self.camera_y = self.map_data.height / 2
        else:
            self.camera_y = min(
                max(self.player.y, viewport_height / 2),
                self.map_data.height - viewport_height / 2,
            )

    def world_to_screen(self, x: float, y: float) -> tuple[float, float]:
        return (
            (x - self.camera_x) * self.camera_zoom + WINDOW_WIDTH / 2,
            (y - self.camera_y) * self.camera_zoom + WINDOW_HEIGHT / 2,
        )

    def screen_to_world(self, x: float, y: float) -> tuple[float, float]:
        return (
            (x - WINDOW_WIDTH / 2) / self.camera_zoom + self.camera_x,
            (y - WINDOW_HEIGHT / 2) / self.camera_zoom + self.camera_y,
        )

    def _affinity_ending(self) -> str:
        values = tuple(self.species_affinity.values())
        if all(value == AFFINITY_MAX for value in values):
            return "완전한 화해 엔딩"
        if all(value >= 80 for value in values):
            return "공존 엔딩"
        if any(value < 40 for value in values):
            return "대립 엔딩"
        return "불안한 휴전 엔딩"

    def _update_transition(self) -> None:
        transition = self.map_data.transition_at(self.player.x, self.player.y)
        if transition is None:
            self.transition_armed = True
            return
        if not self.transition_armed:
            return
        if transition.ends_game:
            self.ending_variant = self._affinity_ending()
            self.ending_timer = 1.75
            self.pressed.clear()
            self.player._set_state("idle")
            values = self.species_affinity
            self.show_toast(
                f"{self.ending_variant} · 까마귀 {values['crow']} · "
                f"늑대 {values['wolf']} · 곰 {values['bear']}",
                seconds=1.75,
            )
            self.transition_armed = False
            return
        if transition.target_map is None:
            return
        self._load_map(transition.target_map, transition.target_spawn)
        self.show_toast(f"{self.map_data.label}(으)로 이동했습니다")

    def update(self, dt: float) -> None:
        self._update_entity_timers(dt)
        if self.ending_timer > 0:
            self.ending_timer -= dt
            if self.ending_timer <= 0:
                self.running = False
        else:
            self.player.update(dt, self.pressed, self._resolve_player_movement)
            self._update_enemies(dt)
            self._update_projectiles(dt)
            self._update_camera()
            self._auto_pickup_world_items()
            self._update_transition()
        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0:
                self.toast = ""

    def _world_image(self, path: Path) -> p2.Image:
        image = self._world_image_cache.get(path)
        if image is None:
            image = p2.load_image(str(path))
            self._world_image_cache[path] = image
        return image

    def _animal_image(self, animal: str, state: str) -> p2.Image:
        key = (animal, state)
        image = self._animal_image_cache.get(key)
        if image is None:
            asset_state = "walk" if animal == "crow" and state == "attack" else state
            filename = f"{animal}_{asset_state}.png"
            path = ANIMAL_ASSET_ROOT / animal.capitalize() / filename
            image = p2.load_image(str(path))
            self._animal_image_cache[key] = image
        return image

    def _draw_enemy(self, enemy: EnemyAI) -> None:
        size = enemy.display_size * self.camera_zoom
        flight_bob = 0.0
        if enemy.animal == "crow" and enemy.alive:
            frame_count, _fps, _loops = ANIMAL_ANIMATIONS["crow"][enemy.state]
            phase = (enemy.frame_index % frame_count) / frame_count
            flight_bob = math.sin(phase * math.tau) * 7.0
        screen_x, screen_y = self.world_to_screen(
            enemy.x,
            enemy.y + enemy.display_size * 0.42 + flight_bob,
        )
        if (
            screen_x + size / 2 < -40
            or screen_x - size / 2 > WINDOW_WIDTH + 40
            or screen_y + size / 2 < -40
            or screen_y - size / 2 > WINDOW_HEIGHT + 40
        ):
            return
        image = self._animal_image(enemy.animal, enemy.state)
        source_bottom = image.h - (enemy.direction_row + 1) * 256
        image.clip_draw(
            enemy.frame_index * 256,
            source_bottom,
            256,
            256,
            screen_x,
            screen_y,
            size,
            size,
        )
        if enemy.alive and enemy.hp < enemy.max_hp:
            bar_width = max(54.0, size * 0.55)
            bar_bottom = screen_y + size * 0.42
            p2.draw_rectangle(
                screen_x - bar_width / 2 - 2,
                bar_bottom - 2,
                screen_x + bar_width / 2 + 2,
                bar_bottom + 8,
                22,
                24,
                22,
                225,
                True,
            )
            p2.draw_rectangle(
                screen_x - bar_width / 2,
                bar_bottom,
                screen_x - bar_width / 2 + bar_width * enemy.hp / enemy.max_hp,
                bar_bottom + 6,
                205,
                54,
                65,
                255,
                True,
            )

    def _draw_projectile(self, projectile: ThrownProjectile) -> None:
        if projectile.elapsed < 0:
            return
        world_x, world_y = projectile.position
        screen_x, screen_y = self.world_to_screen(world_x, world_y)
        angle = math.atan2(
            projectile.target_y
            - projectile.start_y
            + math.pi
            * projectile.arc_height
            * math.cos(math.pi * projectile.progress),
            projectile.target_x - projectile.start_x,
        )
        if projectile.item_id == "stone":
            rotation = projectile.progress * math.tau * 1.5
            size = 42.0
        else:
            rotation = angle - math.pi / 4.0
            size = 90.0
        self.ui.item_images[projectile.item_id].composite_draw(
            rotation, "", screen_x, screen_y, size, size
        )

    def _draw_species_affinity(self) -> None:
        panel_left = 12.0
        panel_right = 216.0
        panel_bottom = 483.0
        panel_top = 607.0
        p2.draw_rectangle(
            panel_left,
            panel_bottom,
            panel_right,
            panel_top,
            18,
            23,
            22,
            218,
            True,
        )
        self.ui.font_small.draw(19, 589, "종 호감도", (255, 238, 205))
        rows = (("crow", 558.0), ("wolf", 530.0), ("bear", 502.0))
        for species, bottom in rows:
            value = self.species_affinity[species]
            relationship = affinity_relationship(value)
            color = AFFINITY_COLORS[relationship]
            image = self._animal_image(species, "idle")
            source_bottom = image.h - 256
            image.clip_draw(
                0,
                source_bottom,
                256,
                256,
                29,
                bottom + 9,
                28,
                28,
            )
            self.ui.font_small.draw(
                43, bottom + 3, SPECIES_LABELS[species], (245, 231, 198)
            )
            bar_left = 101.0
            bar_right = 210.0
            bar_top = bottom + 16.0
            p2.draw_rectangle(
                bar_left, bottom, bar_right, bar_top, 40, 42, 40, 255, True
            )
            fill_right = bar_left + (bar_right - bar_left) * value / AFFINITY_MAX
            if fill_right > bar_left:
                p2.draw_rectangle(
                    bar_left, bottom, fill_right, bar_top, *color, 255, True
                )
            p2.draw_rectangle(
                bar_left,
                bottom,
                bar_right,
                bar_top,
                235,
                224,
                194,
                255,
                False,
            )
            self.ui.font_small.draw(
                166, bottom + 2, f"{value}/100", (255, 255, 255)
            )

    def _draw_aim_indicator(self) -> None:
        if (
            self._equipped_throwable_id() is None
            or self.inventory_open
            or self.crafting_open
            or self.player.dead
        ):
            return
        target_x, target_y = self._throw_target_world(
            self.mouse_screen_x, self.mouse_screen_y
        )
        start_x, start_y = self.world_to_screen(
            self.player.x, self.player.y + CHARACTER_HEIGHT * 0.34
        )
        end_x, end_y = self.world_to_screen(target_x, target_y)
        for index in range(1, 8):
            progress = index / 8.0
            x = start_x + (end_x - start_x) * progress
            y = start_y + (end_y - start_y) * progress
            p2.draw_rectangle(x - 2, y - 2, x + 2, y + 2, 246, 222, 132, 180, True)
        p2.draw_rectangle(
            end_x - 12, end_y - 1, end_x + 12, end_y + 1,
            176, 241, 154, 235, True,
        )
        p2.draw_rectangle(
            end_x - 1, end_y - 12, end_x + 1, end_y + 12,
            176, 241, 154, 235, True,
        )

    def _draw_tiled_sprite(
        self,
        sprite: TileSpriteDefinition,
        raw_gid: int,
        rect: WorldRect,
        rotation_degrees: float = 0.0,
    ) -> None:
        center_x, center_y = self.world_to_screen(
            rect.left + rect.width / 2, rect.bottom + rect.height / 2
        )
        draw_width = rect.width * self.camera_zoom
        draw_height = rect.height * self.camera_zoom
        if (
            center_x + draw_width / 2 < 0
            or center_x - draw_width / 2 > WINDOW_WIDTH
            or center_y + draw_height / 2 < 0
            or center_y - draw_height / 2 > WINDOW_HEIGHT
        ):
            return
        rotation, flip = tiled_gid_transform(raw_gid)
        rotation += math.radians(rotation_degrees)
        self._world_image(sprite.image_path).clip_composite_draw(
            sprite.clip_left,
            sprite.clip_bottom,
            sprite.clip_width,
            sprite.clip_height,
            rotation,
            flip,
            center_x,
            center_y,
            draw_width,
            draw_height,
        )

    def draw(self, *, present: bool = True) -> None:
        p2.clear_canvas()
        p2.draw_rectangle(0, 0, WINDOW_WIDTH - 1, WINDOW_HEIGHT - 1, 12, 18, 21, 255, True)
        if self.map_background is not None:
            background_x, background_y = self.world_to_screen(
                self.map_data.width / 2, self.map_data.height / 2
            )
            self.map_background.draw(
                background_x,
                background_y,
                self.map_data.width * self.camera_zoom,
                self.map_data.height * self.camera_zoom,
            )
        else:
            view_left, view_bottom = self.screen_to_world(0, 0)
            view_right, view_top = self.screen_to_world(WINDOW_WIDTH, WINDOW_HEIGHT)
            for tile in self.map_data.tiles_in_view(
                view_left, view_bottom, view_right, view_top
            ):
                self._draw_tiled_sprite(tile.sprite, tile.raw_gid, tile.rect)
            for obj in self.map_data.object_tiles:
                self._draw_tiled_sprite(
                    obj.sprite, obj.raw_gid, obj.rect, obj.rotation
                )
        for entity in self._current_entities():
            if not entity.visible:
                continue
            rect = entity.definition.rect
            entity_x, entity_y = self.world_to_screen(
                rect.left + rect.width / 2, rect.bottom + rect.height / 2
            )
            draw_width = rect.width * self.camera_zoom
            draw_height = rect.height * self.camera_zoom
            if not (
                entity_x + draw_width / 2 < -40
                or entity_x - draw_width / 2 > WINDOW_WIDTH + 40
                or entity_y + draw_height / 2 < -40
                or entity_y - draw_height / 2 > WINDOW_HEIGHT + 40
            ):
                self._world_image(entity.sprite_path).draw(
                    entity_x, entity_y, draw_width, draw_height
                )
        for enemy in self._current_enemies():
            self._draw_enemy(enemy)
        for utility in self._current_placed_utilities():
            utility_x, utility_y = self.world_to_screen(utility.x, utility.y)
            width, height = PLACED_UTILITY_WORLD_SIZES[utility.item_id]
            draw_width = width * self.camera_zoom
            draw_height = height * self.camera_zoom
            if (
                utility_x + draw_width / 2 >= -40
                and utility_x - draw_width / 2 <= WINDOW_WIDTH + 40
                and utility_y + draw_height / 2 >= -40
                and utility_y - draw_height / 2 <= WINDOW_HEIGHT + 40
            ):
                self.ui.item_images[utility.item_id].draw(
                    utility_x,
                    utility_y,
                    draw_width,
                    draw_height,
                )
        for drop in self.world_drops[self.map_data.name]:
            drop_x, drop_y = self.world_to_screen(drop.x, drop.y)
            if -50 <= drop_x <= WINDOW_WIDTH + 50 and -50 <= drop_y <= WINDOW_HEIGHT + 50:
                drop_size = (
                    THROWN_DROP_SCREEN_SIZE
                    if drop.large_icon
                    else 54 * self.camera_zoom
                )
                self.ui.item_images[drop.stack.item_id].draw(
                    drop_x, drop_y + drop_size * 0.2, drop_size, drop_size
                )
                if drop.stack.count > 1:
                    self.ui.font_small.draw(
                        drop_x + drop_size * 0.25,
                        drop_y,
                        str(drop.stack.count),
                        (255, 255, 255),
                    )
        for projectile in self._current_projectiles():
            self._draw_projectile(projectile)
        player_x, player_y = self.world_to_screen(self.player.x, self.player.y)
        self.ui.draw_equipped_world_tool(
            self.player,
            behind=True,
            x=player_x,
            y=player_y,
            display_scale=self.camera_zoom,
        )
        self._draw_aim_indicator()
        self.player.draw(player_x, player_y, display_scale=self.camera_zoom)
        self.ui.draw_equipped_world_tool(
            self.player,
            behind=False,
            x=player_x,
            y=player_y,
            display_scale=self.camera_zoom,
        )
        nearby_utility = self._nearest_placed_utility()
        nearby: WorldEntity | None = None
        if nearby_utility is not None:
            prompt_x, prompt_y = self.world_to_screen(
                nearby_utility.x, nearby_utility.y
            )
            label = ITEMS[nearby_utility.item_id].label
            self.ui.font_small.draw(
                prompt_x - 45,
                prompt_y + 55,
                f"E · {label} 회수",
                (255, 245, 176),
            )
        else:
            nearby = self._nearest_interactable()
        if nearby is not None:
            rect = nearby.definition.rect
            prompt_x, prompt_y = self.world_to_screen(
                rect.left + rect.width / 2, rect.top
            )
            label = self._entity_label(nearby.definition.entity_type)
            self.ui.font_small.draw(prompt_x - 42, prompt_y + 10, f"E · {label}", (255, 245, 176))
        p2.draw_rectangle(12, 678, 216, 710, 20, 25, 23, 205, True)
        self.ui.font.draw(24, 690, self.map_data.label, (255, 236, 183))
        self.ui.draw_status_bars(self.player)
        self._draw_species_affinity()
        hovered_slot = None
        if not self.crafting_open:
            hovered_slot = self.ui.slot_at(
                self.mouse_screen_x, self.mouse_screen_y, self.inventory_open
            )
        self.ui.draw(
            self.inventory_open,
            self.crafting_open,
            self.drag,
            self.toast,
            self.toast_error,
            hovered_slot,
            self.mouse_screen_x,
            self.mouse_screen_y,
        )
        if present:
            p2.update_canvas()


def main() -> None:
    p2.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    try:
        game = Game()
        previous = p2.get_time()
        while game.running:
            now = p2.get_time()
            dt = min(max(now - previous, 0.0), 0.05)
            previous = now
            game.handle_events()
            game.update(dt)
            game.draw()
            p2.delay(0.001)
    finally:
        p2.close_canvas()


if __name__ == "__main__":
    main()
