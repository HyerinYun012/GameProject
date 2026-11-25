"""CrowGame four-map prototype with inventory, hotbar, and equipment UI."""

from __future__ import annotations

import ctypes
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pico2d as p2
import pico2d.pico2d as pico_core

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
        MAP_SCALE,
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
        MAP_SCALE,
        MapData,
        TileSpriteDefinition,
        WorldEntityDefinition,
        WorldRect,
        load_map_data,
    )


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FRAME_WIDTH = 80
FRAME_HEIGHT = 72
CHARACTER_WIDTH = 240
CHARACTER_HEIGHT = 216
MAX_HP = 100.0
MAX_SP = 100.0
SP_DRAIN_PER_SECOND = 25.0
SP_RECOVERY_PER_SECOND = 18.0
NIGHT_SP_RECOVERY_MULTIPLIER = 0.70
SP_RUN_RESTART_THRESHOLD = 20.0
CAMERA_ZOOM = 0.50
GAME_MINUTES_PER_REAL_SECOND = 2.0
GAME_DAY_MINUTES = 24.0 * 60.0
GAME_START_MINUTES = 8.0 * 60.0
DAWN_START_MINUTES = 5.0 * 60.0
DAY_START_MINUTES = 7.0 * 60.0
DUSK_START_MINUTES = 17.0 * 60.0
NIGHT_START_MINUTES = 20.0 * 60.0
SLEEP_ALLOWED_START_MINUTES = 17.0 * 60.0
SLEEP_WAKE_MINUTES = 8.0 * 60.0
SLEEP_FAST_FORWARD_MINUTES_PER_REAL_SECOND = 240.0
NIGHT_AMBIENT_ALPHA = 82
NIGHT_EXTERIOR_ALPHA = 245
NIGHT_VISION_RADIUS = 100.0
TORCH_VISION_RADIUS = 260.0
NIGHT_VISION_FEATHER = 96.0
NIGHT_MASK_SIZE = 768
INTERACTION_SCREEN_DISTANCE = 125.0
AUTO_PICKUP_SCREEN_DISTANCE = 115.0
THROWN_DROP_REARM_MOVEMENT = 30.0
FRUIT_COOLDOWN_SECONDS = 30.0
THROWN_DROP_MIN_SCREEN_DISTANCE = 80.0
THROWN_DROP_MAX_SCREEN_DISTANCE = 130.0
THROWN_DROP_SCREEN_SIZE = 76.0
WORLD_TILE_SIZE = 32.0 * MAP_SCALE
PROJECTILE_MAX_TILES = 5.0
PROJECTILE_SCREEN_SPEED = 760.0
PROJECTILE_ARC_SCREEN_HEIGHT = 92.0
PROJECTILE_RELEASE_DELAY = 0.10
THROWABLE_ITEM_IDS = frozenset({"wooden_spear", "stone_spear", "stone"})
PROJECTILE_DAMAGE = {
    "wooden_spear": 15,
    "stone_spear": 30,
    "stone": 18,
}
MELEE_DAMAGE = {
    "wooden_sword": 10,
    "stone_sword": 20,
}
MELEE_RANGE_TILES = {"wooden_sword": 1.2, "stone_sword": 1.2}
UNARMED_DAMAGE = 5
UNARMED_RANGE_TILES = 1.0
PLACED_UTILITY_SCREEN_DISTANCE = 130.0
UTILITY_PLACEMENT_SCREEN_DISTANCE = 105.0
INSTALLABLE_ITEM_IDS = frozenset({"travel_bedding", "campfire"})
FISHING_BITE_MIN_SECONDS = 1.5
FISHING_BITE_MAX_SECONDS = 4.0
FISHING_REACTION_SECONDS = 1.0
FISHING_TENSION_RISE_PER_SECOND = 58.0
FISHING_TENSION_FALL_PER_SECOND = 46.0
FISHING_SAFE_TENSION_MIN = 42.0
FISHING_SAFE_TENSION_MAX = 62.0
FISHING_DANGER_TENSION_MIN = 8.0
FISHING_DANGER_TENSION_MAX = 90.0
FISHING_DANGER_HOLD_SECONDS = 0.60
FISHING_CAPTURE_PER_SECOND = 18.0
FISHING_CAPTURE_LOSS_PER_SECOND = 14.0
GAME_TITLE = "The Last Wile Human"
CUTSCENE_FADE_SECONDS = 0.65
CUTSCENE_HOLD_SECONDS = 3.60
CUTSCENE_FAST_FORWARD_RATE = 2.0
CUTSCENE_CONTROLS_HEIGHT = 60
LOBBY_FADE_SECONDS = 0.65
PLACED_UTILITY_WORLD_SIZES = {
    "travel_bedding": (240.0, 170.0),
    "campfire": (190.0, 190.0),
}
ASSET_DIR = Path(__file__).resolve().parent / "assets"
LOBBY_BACKGROUND_PATH = ASSET_DIR / "ui" / "lobby_background.png"
LOBBY_BUTTON_PATH = ASSET_DIR / "ui" / "lobby_button.png"
CUTSCENE_DIR = Path(__file__).resolve().parent.parent / "ENDING"
INTRO_CUTSCENE_PATHS = tuple(
    CUTSCENE_DIR / f"story{index}.png" for index in range(1, 5)
)
CONFLICT_ENDING_CUTSCENE_PATHS = tuple(
    CUTSCENE_DIR / f"ending1-{index}.png" for index in range(1, 6)
)
RECONCILIATION_ENDING_CUTSCENE_PATHS = tuple(
    CUTSCENE_DIR / f"ending2-{index}.png" for index in range(1, 7)
)
NIGHT_MASK_PATHS = {
    False: ASSET_DIR / "ui" / "night_mask.png",
    True: ASSET_DIR / "ui" / "night_mask_torch.png",
}
FRUIT_TREE_UNRIPE_SPRITE = ASSET_DIR / "fruit_tree_unripe.png"
AWARENESS_ICON_PATHS = {
    "suspicious": ASSET_DIR / "ui" / "suspicion_question.png",
    "searching": ASSET_DIR / "ui" / "suspicion_question.png",
    "alerted": ASSET_DIR / "ui" / "alert_exclamation.png",
}
AWARENESS_ICON_SCREEN_SIZE = 58.0
AWARENESS_ICON_CENTER_OFFSET = 52.0
ANIMAL_ASSET_ROOT = (
    Path(__file__).resolve().parent.parent / "Assets" / "Sprites" / "Animals"
)
GENERATED_ICON_DIR = Path(__file__).resolve().parent / "generated" / "icons"
HELD_TOOL_ICON_PATHS = {
    "stone_axe": ASSET_DIR / "stone-axe-held-pixel-v1.png",
}
HELD_STONE_AXE_MOTION = {
    "idle": (
        (0.0, 0.0, 0.00),
        (0.0, 2.0, 0.03),
        (0.0, 0.0, 0.00),
        (0.0, -2.0, -0.03),
    ),
    "walk": (
        (-3.0, -3.0, -0.07),
        (3.0, 3.0, 0.05),
        (3.0, -3.0, 0.07),
        (-3.0, 3.0, -0.05),
    ),
    "run": (
        (-6.0, -5.0, -0.12),
        (6.0, 5.0, 0.09),
        (6.0, -5.0, 0.12),
        (-6.0, 5.0, -0.09),
    ),
}
CHARACTER_SHEET = (
    Path(__file__).resolve().parent
    / "sprite-preview"
    / "dist"
    / "assets"
    / "adventurer-8dir-idle-walk-run-hurt-death-unified-v26.png"
)

DIRECTIONS = (
    "up",
    "up_right",
    "right",
    "down_right",
    "down",
    "down_left",
    "left",
    "up_left",
)
DIRECTION_VECTORS = {
    "up": (0.0, 1.0),
    "up_right": (math.sqrt(0.5), math.sqrt(0.5)),
    "right": (1.0, 0.0),
    "down_right": (math.sqrt(0.5), -math.sqrt(0.5)),
    "down": (0.0, -1.0),
    "down_left": (-math.sqrt(0.5), -math.sqrt(0.5)),
    "left": (-1.0, 0.0),
    "up_left": (-math.sqrt(0.5), math.sqrt(0.5)),
}
NORTH_FACING_DIRECTIONS = frozenset({"up_left", "up", "up_right"})
WEST_FACING_DIRECTIONS = frozenset({"up_left", "left", "down_left"})


def direction_from_vector(dx: float, dy: float, fallback: str = "down") -> str:
    """Quantize a vector to the nearest of the character sheet's 8 directions."""
    if math.isclose(dx, 0.0) and math.isclose(dy, 0.0):
        return fallback
    octant = round(math.atan2(dy, dx) / (math.pi / 4.0)) % 8
    return (
        "right",
        "up_right",
        "up",
        "up_left",
        "left",
        "down_left",
        "down",
        "down_right",
    )[octant]


def format_game_time(game_minutes: float) -> str:
    """Return a wrapping 12-hour clock label for the current game time."""
    minute = int(game_minutes % GAME_DAY_MINUTES)
    hour = minute // 60
    display_hour = hour % 12 or 12
    return f"{display_hour:02d}:{minute % 60:02d}"


def game_time_period(game_minutes: float) -> str:
    """Return the Korean AM/PM label displayed beside the clock."""
    minute = game_minutes % GAME_DAY_MINUTES
    return "오전" if minute < 12 * 60 else "오후"


def night_darkness_progress(game_minutes: float) -> float:
    """Return 0 in daylight and a smooth 0..1 dusk/night/dawn amount."""
    minute = game_minutes % GAME_DAY_MINUTES
    if DUSK_START_MINUTES <= minute < NIGHT_START_MINUTES:
        return (minute - DUSK_START_MINUTES) / (
            NIGHT_START_MINUTES - DUSK_START_MINUTES
        )
    if minute >= NIGHT_START_MINUTES or minute < DAWN_START_MINUTES:
        return 1.0
    if DAWN_START_MINUTES <= minute < DAY_START_MINUTES:
        return 1.0 - (minute - DAWN_START_MINUTES) / (
            DAY_START_MINUTES - DAWN_START_MINUTES
        )
    return 0.0


def stamina_recovery_multiplier(game_minutes: float) -> float:
    """Return the daytime rate or the 30%-slower full-night rate."""
    minute = game_minutes % GAME_DAY_MINUTES
    if minute >= NIGHT_START_MINUTES or minute < DAWN_START_MINUTES:
        return NIGHT_SP_RECOVERY_MULTIPLIER
    return 1.0


STATE_FPS = {
    "idle": 4.0,
    "walk": 7.0,
    "run": 10.0,
    "hurt": 6.0,
    "death": 6.0,
    "attack": 11.0,
    "axe": 10.0,
    "mine": 10.0,
    "fish": 6.0,
}
ACTION_STATES = frozenset({"hurt", "death", "attack", "axe", "mine", "fish"})

ANIMAL_ANIMATIONS: dict[str, dict[str, tuple[int, float, bool]]] = {
    "crow": {
        "idle": (4, 8.0, True),
        "walk": (6, 14.0, True),
        # The crow pack has no separate attack sheet; one brisk non-looping
        # flight cycle is used as a diving strike.
        "attack": (6, 14.0, False),
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
        "hp": 35, "size": 210.0, "speed": 250.0, "hit_radius": 68.0,
        "attack_range": 68.0, "attack_damage": 20.0, "attack_cooldown": 3.5,
    },
    "wolf": {
        "hp": 70, "size": 285.0, "speed": 200.0, "hit_radius": 88.0,
        "attack_range": 82.0, "attack_damage": 40.0, "attack_cooldown": 1.35,
    },
    "bear": {
        "hp": 120, "size": 375.0, "speed": 160.0, "hit_radius": 120.0,
        "attack_range": 105.0, "attack_damage": 55.0, "attack_cooldown": 1.8,
    },
}
MAP_NATIVE_AI_KINDS: dict[str, tuple[str, ...]] = {
    "crow_map.json": ("crow",),
    "wolf_map.json": ("wolf",),
    "bear_map.json": ("bear",),
}
# Backwards-compatible name for code that only needs each map's native species.
MAP_AI_KINDS = MAP_NATIVE_AI_KINDS
MAP_SPECIES = {
    "crow_map.json": "crow",
    "wolf_map.json": "wolf",
    "bear_map.json": "bear",
}
SPECIES_LABELS = {"crow": "까마귀", "wolf": "늑대", "bear": "곰"}
AFFINITY_MAX = 100
AFFINITY_LOSS_PER_HIT = 5
AI_SENSES: dict[str, dict[str, float]] = {
    "crow": {
        "vision_tiles": 7.0,
        "vision_angle": 110.0,
        "alert_tiles": 10.0,
        "search_tiles": 2.0,
        "confirm_seconds": 0.8,
        "max_chase_tiles": 12.0,
        "search_seconds": 6.0,
    },
    "wolf": {
        "vision_tiles": 6.0,
        "vision_angle": 120.0,
        "alert_tiles": 8.0,
        "search_tiles": 3.0,
        "confirm_seconds": 0.5,
        "max_chase_tiles": 14.0,
        "search_seconds": 8.0,
    },
    "bear": {
        "vision_tiles": 3.0,
        "vision_angle": 120.0,
        "alert_tiles": 0.0,
        "search_tiles": 2.0,
        "confirm_seconds": 0.25,
        "max_chase_tiles": 6.0,
        "search_seconds": 6.0,
    },
}
AI_ATTACK_COOLDOWN = 1.35
AI_PROVOKED_SECONDS = 6.0
AI_ALERT_REFRESH_SECONDS = 1.25
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


def desired_map_species(
    map_name: str, species_affinity: dict[str, int]
) -> tuple[str, ...]:
    """Return native animals plus unresolved species that follow downstream."""
    desired = list(MAP_NATIVE_AI_KINDS.get(map_name, ()))
    if map_name in ("wolf_map.json", "bear_map.json"):
        if species_affinity.get("crow", 0) < AFFINITY_MAX:
            desired.append("crow")
    if map_name == "bear_map.json":
        if species_affinity.get("wolf", 0) < AFFINITY_MAX:
            desired.append("wolf")
    return tuple(desired)


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
    awareness: str = "unaware"
    suspicion_timer: float = 0.0
    last_seen_x: float | None = None
    last_seen_y: float | None = None
    search_clock: float = 0.0
    search_timer: float = 0.0
    alert_refresh: float = 0.0
    just_alerted: bool = False
    flight_clock: float = 0.0

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

    def _forward_vector(self) -> tuple[float, float]:
        directions = (
            (0.0, -1.0),
            (math.sqrt(0.5), -math.sqrt(0.5)),
            (1.0, 0.0),
            (math.sqrt(0.5), math.sqrt(0.5)),
            (0.0, 1.0),
            (-math.sqrt(0.5), math.sqrt(0.5)),
            (-1.0, 0.0),
            (-math.sqrt(0.5), -math.sqrt(0.5)),
        )
        return directions[self.direction_row % 8]

    def _can_see_player(self, player: Player, affinity: int) -> bool:
        if affinity >= AFFINITY_MAX or player.dead or not self.alive:
            return False
        senses = AI_SENSES[self.animal]
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.hypot(dx, dy)
        max_chase = senses["max_chase_tiles"] * WORLD_TILE_SIZE
        if self.provoked_timer > 0:
            return distance <= max_chase
        if distance > senses["vision_tiles"] * WORLD_TILE_SIZE:
            return False
        if distance <= 0.01:
            return True
        forward_x, forward_y = self._forward_vector()
        alignment = (dx * forward_x + dy * forward_y) / distance
        half_angle = math.radians(senses["vision_angle"] / 2.0)
        return alignment >= math.cos(half_angle)

    def receive_alert(self, x: float, y: float) -> None:
        if not self.alive:
            return
        self.last_seen_x = x
        self.last_seen_y = y
        self.awareness = "alerted"
        self.suspicion_timer = AI_SENSES[self.animal]["confirm_seconds"]
        self.search_timer = AI_SENSES[self.animal]["search_seconds"]
        self.search_clock = 0.0

    def _chase_target(self, target_x: float, target_y: float) -> tuple[float, float]:
        max_distance = AI_SENSES[self.animal]["max_chase_tiles"] * WORLD_TILE_SIZE
        dx = target_x - self.home_x
        dy = target_y - self.home_y
        distance = math.hypot(dx, dy)
        if distance <= max_distance or distance <= 0.01:
            return target_x, target_y
        return (
            self.home_x + dx / distance * max_distance,
            self.home_y + dy / distance * max_distance,
        )

    def _move_toward(
        self, target_x: float, target_y: float, dt: float, map_data: MapData
    ) -> None:
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)
        stop_distance = 2.0 if self.animal == "crow" else 12.0
        if distance <= stop_distance:
            if self.animal == "crow":
                # The patrol target itself moves a small amount every frame.
                # Switching to idle whenever the crow catches that point makes
                # the renderer alternate between two different sprite sheets,
                # which looks like a rapid blink. Snap the final tiny distance
                # and keep the continuous flight cycle instead.
                if distance > 0.01:
                    self.x = target_x
                    self.y = target_y
                    self._face_vector(dx, dy)
                self._set_state("walk")
            else:
                self._set_state("idle")
            return
        speed = float(ANIMAL_STATS[self.animal]["speed"])
        travel_distance = min(speed * dt, distance)
        move_x = dx / distance * travel_distance
        move_y = dy / distance * travel_distance
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
        del camera_zoom  # Perception is defined in world tiles, not zoomed pixels.
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.provoked_timer = max(0.0, self.provoked_timer - dt)
        self.alert_refresh = max(0.0, self.alert_refresh - dt)
        self.just_alerted = False
        if self.animal == "crow" and self.alive:
            self.flight_clock += dt

        state_before = self.state
        if state_before in ("hurt", "death", "attack"):
            if (
                state_before == "attack"
                and affinity >= 80
                and self.provoked_timer <= 0
            ):
                self.attack_pending = False
                self._set_state("idle")
                return 0.0
            self._advance_animation(dt)
            if (
                state_before == "attack"
                and self.attack_pending
                and (self.frame_index >= 2 or self.state != "attack")
            ):
                self.attack_pending = False
                return float(ANIMAL_STATS[self.animal]["attack_damage"])
            return 0.0

        sees_player = player is not None and self._can_see_player(player, affinity)
        senses = AI_SENSES[self.animal]
        if affinity >= AFFINITY_MAX:
            self.awareness = "unaware"
            self.suspicion_timer = 0.0
            self.last_seen_x = None
            self.last_seen_y = None
        elif sees_player and player is not None:
            self.last_seen_x = player.x
            self.last_seen_y = player.y
            self.search_timer = senses["search_seconds"]
            if self.awareness in ("unaware", "searching"):
                self.awareness = "suspicious"
                self.suspicion_timer = 0.0
            if self.awareness == "suspicious":
                self.suspicion_timer += dt
                if self.suspicion_timer >= senses["confirm_seconds"]:
                    self.awareness = "alerted"
                    self.just_alerted = True
                    self.alert_refresh = AI_ALERT_REFRESH_SECONDS
            elif self.awareness == "alerted" and self.alert_refresh <= 0:
                self.just_alerted = True
                self.alert_refresh = AI_ALERT_REFRESH_SECONDS
        elif self.awareness == "suspicious":
            self.suspicion_timer = max(0.0, self.suspicion_timer - dt * 2.0)
            if self.suspicion_timer <= 0:
                self.awareness = "unaware"

        if self.awareness == "suspicious" and player is not None:
            self._face_vector(player.x - self.x, player.y - self.y)
            self._set_state("idle")
        elif self.awareness == "alerted" and self.last_seen_x is not None and self.last_seen_y is not None:
            target_x, target_y = self._chase_target(self.last_seen_x, self.last_seen_y)
            distance_to_target = math.hypot(target_x - self.x, target_y - self.y)
            if sees_player and player is not None:
                self._face_vector(player.x - self.x, player.y - self.y)
                attack_range = float(ANIMAL_STATS[self.animal]["attack_range"])
                if math.hypot(player.x - self.x, player.y - self.y) <= attack_range:
                    can_attack_first = affinity < 80
                    may_retaliate = self.provoked_timer > 0
                    if self.attack_cooldown <= 0 and (
                        can_attack_first or may_retaliate
                    ):
                        self._set_state("attack")
                        self.attack_pending = True
                        self.attack_cooldown = float(
                            ANIMAL_STATS[self.animal]["attack_cooldown"]
                        )
                    else:
                        self._set_state("idle")
                else:
                    self._move_toward(target_x, target_y, dt, map_data)
            elif distance_to_target > 24.0:
                self._move_toward(target_x, target_y, dt, map_data)
            else:
                self.awareness = "searching"
                self.search_clock = 0.0
                self._set_state("idle")
        elif self.awareness == "searching" and self.last_seen_x is not None and self.last_seen_y is not None:
            self.search_timer = max(0.0, self.search_timer - dt)
            self.search_clock += dt
            if self.search_timer <= 0:
                self.awareness = "unaware"
                self.last_seen_x = None
                self.last_seen_y = None
            else:
                radius = senses["search_tiles"] * WORLD_TILE_SIZE
                target_x = self.last_seen_x + math.cos(self.search_clock * 1.4) * radius
                target_y = self.last_seen_y + math.sin(self.search_clock * 1.4) * radius
                target_x, target_y = self._chase_target(target_x, target_y)
                self._move_toward(target_x, target_y, dt, map_data)
        elif self.animal == "bear":
            if math.hypot(self.home_x - self.x, self.home_y - self.y) > 16.0:
                self._move_toward(self.home_x, self.home_y, dt, map_data)
            else:
                self._set_state("idle")
        else:
            self.patrol_clock += dt
            if self.animal == "crow":
                # Chase a point ahead on one smooth ellipse instead of catching
                # and stopping on a slowly drifting target every few frames.
                patrol_angle = self.patrol_clock * 0.46 + 0.85
                target_x = self.home_x + math.cos(patrol_angle) * 190.0
                target_y = self.home_y + math.sin(patrol_angle) * 125.0
            else:
                radius = 105.0
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


# Coordinates are shared with sprite-preview/dist/app.js. Each stored x value is
# the visual centre of an 80x72 crop in the v26 sheet.
DIRECTION_SHEET_META = {
    "up": (0, 0),
    "down": (0, 1),
    "up_right": (1, 0),
    "down_left": (1, 1),
    "right": (2, 0),
    "left": (2, 1),
    "down_right": (3, 0),
    "up_left": (3, 1),
}
STANDARD_FRAME_CENTERS = (
    (260, 342, 425, 508),
    (717, 800, 884, 971),
    (1174, 1258, 1343, 1425),
    (1628, 1712, 1798, 1884),
)
HURT_FRAME_CENTERS = (
    (336, 436),
    (794, 889),
    (1250, 1346),
    (1709, 1805),
)
DEATH_FRAME_CENTERS = (
    (239, 312, 386, 462, 537),
    (703, 773, 845, 918, 993),
    (1158, 1227, 1300, 1376, 1452),
    (1612, 1680, 1746, 1827, 1900),
)


def sheet_frames(
    direction: str,
    centers: tuple[tuple[int, ...], ...],
    row_tops: tuple[int, int],
) -> tuple[SpriteFrame, ...]:
    group, row = DIRECTION_SHEET_META[direction]
    return frames_at(
        row_tops[row],
        tuple(center - FRAME_WIDTH // 2 for center in centers[group]),
    )


IDLE_FRAMES: dict[str, tuple[SpriteFrame, ...]] = {
    direction: sheet_frames(direction, STANDARD_FRAME_CENTERS, (4, 76))
    for direction in DIRECTIONS
}
WALK_FRAMES: dict[str, tuple[SpriteFrame, ...]] = {
    direction: sheet_frames(direction, STANDARD_FRAME_CENTERS, (164, 236))
    for direction in DIRECTIONS
}
# Backwards-compatible name used by existing tests and preview tooling.
MOVE_FRAMES = WALK_FRAMES
RUN_FRAMES: dict[str, tuple[SpriteFrame, ...]] = {
    direction: sheet_frames(direction, STANDARD_FRAME_CENTERS, (321, 393))
    for direction in DIRECTIONS
}
HURT_FRAMES: dict[str, tuple[SpriteFrame, ...]] = {
    direction: sheet_frames(direction, HURT_FRAME_CENTERS, (477, 546))
    for direction in DIRECTIONS
}
DEATH_FRAMES: dict[str, tuple[SpriteFrame, ...]] = {
    direction: sheet_frames(direction, DEATH_FRAME_CENTERS, (626, 715))
    for direction in DIRECTIONS
}

# The replacement sheet intentionally has no tool-specific body rows. Tool
# actions therefore reuse its matching 8-direction idle cycle while the actual
# equipped icon supplies the four-phase swing/interaction arc.
ACTION_BODY_FRAMES: dict[str, dict[str, tuple[SpriteFrame, ...]]] = {
    state: {direction: IDLE_FRAMES[direction] for direction in DIRECTIONS}
    for state in ("attack", "axe", "mine", "fish")
}
VERTICAL_TOOL_FRAMES: dict[str, tuple[SpriteFrame, ...]] = {
    direction: ACTION_BODY_FRAMES["attack"][direction]
    for direction in ("down", "up")
}
CUSTOM_SIDE_BODY_FRAMES: dict[str, tuple[SpriteFrame, ...]] = {
    direction: ACTION_BODY_FRAMES["attack"][direction]
    for direction in ("right", "left")
}
SIDE_ACTION_FRAMES: dict[str, dict[str, tuple[SpriteFrame, ...]]] = {
    state: ACTION_BODY_FRAMES[state]
    for state in ("attack", "axe", "mine", "fish")
}

# Per-phase (x, y, rotation) paths for the actual equipped item icon. Left is
# produced by mirroring these authored right-facing paths.
CUSTOM_SIDE_TOOL_PATHS = {
    "axe": (
        (
            (16.0, 105.0, 0.95),
            (37.0, 96.0, 0.40),
            (60.0, 69.0, -0.72),
            (43.0, 85.0, -0.05),
        ),
        62,
    ),
    "mine": (
        (
            (14.0, 106.0, 0.82),
            (36.0, 95.0, 0.30),
            (59.0, 68.0, -0.64),
            (42.0, 84.0, -0.03),
        ),
        62,
    ),
    "fish": (
        (
            (18.0, 96.0, -0.48),
            (40.0, 92.0, -0.08),
            (66.0, 80.0, 0.48),
            (44.0, 88.0, 0.04),
        ),
        68,
    ),
    "attack": (
        (
            (17.0, 103.0, 0.94),
            (42.0, 92.0, 0.28),
            (69.0, 73.0, -0.58),
            (45.0, 86.0, 0.02),
        ),
        66,
    ),
}

# Kept as a public alias for older preview/test code.
UNIFIED_ACTION_FRAMES = VERTICAL_TOOL_FRAMES

# Backwards-compatible public name used by tests and preview tooling.
ATTACK_FRAMES = ACTION_BODY_FRAMES["attack"]


class Player:
    WALK_SPEED = 150.0
    RUN_SPEED = 225.0

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
        if self.state == "walk":
            return WALK_FRAMES[self.direction]
        if self.state == "run":
            return RUN_FRAMES[self.direction]
        if self.state == "hurt":
            return HURT_FRAMES[self.direction]
        if self.state in ("attack", "axe", "mine", "fish"):
            return ACTION_BODY_FRAMES[self.state][self.direction]
        if self.state == "death":
            return DEATH_FRAMES[self.direction]

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
        sp_recovery_multiplier: float = 1.0,
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
                self.direction = direction_from_vector(dx, dy, self.direction)

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
            recovery = (
                SP_RECOVERY_PER_SECOND
                * max(sp_recovery_multiplier, 0.0)
                * dt
            )
            self.sp = min(self.max_sp, self.sp + recovery)
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
        frame = self._frame_for_draw()
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

    def draw_sleeping(self, bedding: Rect) -> None:
        # Use the head and shoulder of a lying frame so the blanket covers the body.
        frame = DEATH_FRAMES["right"][-1]
        crop_width, crop_height = 26, 31
        head_width = bedding.width * 0.25
        self.sprite_sheet.clip_composite_draw(
            frame.left + 44,
            self.sprite_sheet.h - frame.top - 40 - crop_height,
            crop_width,
            crop_height,
            math.radians(23),
            frame.flip,
            bedding.cx + bedding.width * 0.19,
            bedding.cy + bedding.height * 0.20,
            head_width,
            head_width * crop_height / crop_width,
        )

    def _frame_for_draw(self) -> SpriteFrame:
        if self.state == "fish":
            # Fishing phases animate the equipped rod only. Reusing one idle
            # body frame prevents the character from leaning or stepping while
            # the rod follows its four authored arc positions.
            return IDLE_FRAMES[self.direction][0]
        frames = self._frames_for_state()
        return frames[min(self.frame_index, len(frames) - 1)]

    def _state_transform(self) -> tuple[float, float, float]:
        """Author side-action recoil; hurt/death motion lives in the v26 sheet."""
        if (
            self.state in ("attack", "axe", "mine")
            and self.direction in ("left", "right")
        ):
            phase = min(self.frame_index, 3)
            side = 1.0 if self.direction == "right" else -1.0
            offset_x = (-5.0, 1.0, 10.0, 2.0)[phase] * side
            offset_y = (0.0, 3.0, -4.0, 0.0)[phase]
            rotation = (-0.08, 0.04, 0.13, 0.0)[phase] * side
            return offset_x, offset_y, rotation
        return 0.0, 0.0, 0.0


class GameUI:
    HUD_COLUMN_LEFT = 12
    HUD_COLUMN_RIGHT = 216
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

    HEART_POTION_ICON = (
        "....CCCC....",
        "...CccccC...",
        "...CCCCCC...",
        "....IwwI....",
        "...Iw..wI...",
        "..IwwrrrwI..",
        ".IwrhhrhhrI.",
        ".IwrhhhhhrI.",
        ".IrrrhhhrrI.",
        ".IdrrrhrrdI.",
        "..IdrrrrdI..",
        "...IIIIII...",
    )
    RUNNER_ICON = (
        "........yy..",
        ".......yYYy.",
        "........yy..",
        "......yy..y.",
        ".....yYy.yy.",
        ".ss.yyYYyy..",
        "...yy.yy....",
        "......yyy...",
        ".s...yy.yy..",
        "....yy...y..",
        "..yyy....y..",
        ".........yy.",
    )
    FAST_FORWARD_ICON = (
        "YY...YY....",
        ".YY...YY...",
        "..YY...YY..",
        "...YY...YY.",
        "....YY...YY",
        "...YY...YY.",
        "..YY...YY..",
        ".YY...YY...",
        "YY...YY....",
    )
    PAUSE_ICON = ("YY..YY",) * 8
    PLAY_ICON = (
        "Y.....",
        "YYY...",
        "YYYYY.",
        "YYYYYY",
        "YYYYYY",
        "YYYYY.",
        "YYY...",
        "Y.....",
    )
    HUD_ICON_COLORS = {
        "C": (155, 95, 50),
        "c": (239, 184, 112),
        "I": (191, 135, 134),
        "w": (251, 204, 189),
        "r": (207, 57, 76),
        "h": (255, 230, 222),
        "d": (147, 36, 55),
        "y": (241, 181, 75),
        "Y": (255, 232, 158),
        "s": (144, 109, 64),
    }

    def __init__(self, model: InventoryModel) -> None:
        self.model = model
        self.inventory_image = p2.load_image(str(ASSET_DIR / "inventory.png"))
        self.hotbar_image = p2.load_image(str(ASSET_DIR / "hotbar.png"))
        self.tool_image = p2.load_image(str(ASSET_DIR / "tool.png"))
        self.armor_image = p2.load_image(str(ASSET_DIR / "armor.png"))
        self.item_images: dict[str, p2.Image] = {}
        self.held_item_images: dict[str, p2.Image] = {}
        for item_id, definition in ITEMS.items():
            thumbnail = GENERATED_ICON_DIR / definition.icon_filename
            source = thumbnail if thumbnail.exists() else ASSET_DIR / definition.icon_filename
            self.item_images[item_id] = p2.load_image(str(source))
            held_source = HELD_TOOL_ICON_PATHS.get(item_id, source)
            self.held_item_images[item_id] = p2.load_image(str(held_source))

        font_regular = Path("C:/Windows/Fonts/malgun.ttf")
        font_bold = Path("C:/Windows/Fonts/malgunbd.ttf")
        self.font_small = p2.load_font(str(font_regular), 15)
        self.font = p2.load_font(str(font_bold), 18)
        self.font_title = p2.load_font(str(font_bold), 23)
        self.font_lobby_title = p2.load_font(str(font_bold), 60)
        self.font_lobby_button = p2.load_font(str(font_bold), 30)

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

        armor = self.model.armor_slot
        if armor is not None and armor.durability is not None:
            armor_status = f"내구 {armor.durability}/{armor.definition.max_durability}"
            self.font_small.draw(1144, 17, armor_status, (235, 242, 255))

        if drag:
            self.item_images[drag.item_id].draw(drag.x, drag.y, 70, 70)
        if hovered_slot is not None:
            self._draw_durability_tooltip(hovered_slot, mouse_x, mouse_y)
        if toast:
            self._draw_toast(toast, toast_error)

    @staticmethod
    def measure_text_width(font: p2.Font, text: str) -> int:
        width = ctypes.c_int()
        p2.TTF_SizeUTF8(font.font, text.encode("utf-8"), ctypes.byref(width), None)
        return width.value

    def _draw_toast(self, text: str, error: bool) -> None:
        padding = 24
        line_height = 26
        max_text_width = WINDOW_WIDTH - 4 * padding
        text_width = self.measure_text_width(self.font, text)
        lines = [(text, text_width)]
        if text_width > max_text_width:
            lines = []
            line, line_width = "", 0
            for word in text.split():
                candidate = f"{line} {word}" if line else word
                candidate_width = self.measure_text_width(self.font, candidate)
                if line and candidate_width > max_text_width:
                    lines.append((line, line_width))
                    line, line_width = word, self.measure_text_width(self.font, word)
                else:
                    line, line_width = candidate, candidate_width
            lines.append((line, line_width))

        panel = Rect(
            WINDOW_WIDTH / 2,
            WINDOW_HEIGHT / 2,
            max(width for _, width in lines) + 2 * padding,
            len(lines) * line_height + 18,
        )
        self.draw_hud_panel(panel.left, panel.bottom, panel.right, panel.top)
        color = (255, 125, 115) if error else (255, 237, 176)
        first_line_y = panel.cy + (len(lines) - 1) * line_height / 2 + 1
        for index, (line, width) in enumerate(lines):
            self.font.draw(
                panel.cx - width / 2, first_line_y - index * line_height, line, color
            )

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

    @staticmethod
    def draw_hud_panel(left: float, bottom: float, right: float, top: float) -> None:
        rim = (112, 85, 52)
        inset = (21, 27, 24)
        p2.draw_rectangle(left + 2, bottom, right - 2, top, *rim, 255, True)
        p2.draw_rectangle(left, bottom + 2, right, top - 2, *rim, 255, True)
        p2.draw_rectangle(left + 2, bottom + 2, right - 2, top - 2, *inset, 255, True)
        for start, end in ((left + 2, left + 9), (right - 9, right - 2)):
            p2.draw_rectangle(start, top, end, top, 193, 152, 89, 255, True)
            p2.draw_rectangle(start, bottom, end, bottom, 154, 117, 68, 255, True)

    @classmethod
    def draw_hud_icon(cls, icon: tuple[str, ...], cx: float, cy: float) -> None:
        pixel_size = 2
        left = cx - len(icon[0]) * pixel_size / 2
        top = cy + len(icon) * pixel_size / 2 - 1
        for row_index, row in enumerate(icon):
            y = top - row_index * pixel_size
            for column_index, shade in enumerate(row):
                if shade == ".":
                    continue
                x = left + column_index * pixel_size
                p2.draw_rectangle(
                    x,
                    y - pixel_size + 1,
                    x + pixel_size - 1,
                    y,
                    *cls.HUD_ICON_COLORS[shade],
                    255,
                    True,
                )

    def draw_status_bars(self, player: Player) -> None:
        def draw_bar(
            icon: tuple[str, ...],
            bottom: float,
            ratio: float,
            fill_color: tuple[int, int, int],
        ) -> None:
            bar_left = self.HUD_COLUMN_LEFT + 39
            bar_right = self.HUD_COLUMN_RIGHT - 6
            bar_top = bottom + 18.0
            self.draw_hud_panel(
                self.HUD_COLUMN_LEFT, bottom - 4, self.HUD_COLUMN_RIGHT, bar_top + 4
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
            icon_x = (self.HUD_COLUMN_LEFT + bar_left) / 2
            self.draw_hud_icon(icon, icon_x, (bottom + bar_top) / 2)

        draw_bar(self.HEART_POTION_ICON, 649, player.hp / player.max_hp, (205, 54, 65))
        draw_bar(self.RUNNER_ICON, 617, player.sp / player.max_sp, (224, 171, 54))

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

    def _draw_stone_axe_grip(
        self,
        player: Player,
        draw_x: float,
        draw_y: float,
        display_scale: float,
    ) -> None:
        grip_offsets = {
            "up": (36.0, 87.0),
            "up_right": (39.0, 87.0),
            "right": (42.0, 81.0),
            "down_right": (42.0, 78.0),
            "down": (42.0, 78.0),
            "down_left": (-42.0, 78.0),
            "left": (-42.0, 81.0),
            "up_left": (-39.0, 87.0),
        }
        motion_x, motion_y, _rotation = HELD_STONE_AXE_MOTION[player.state][
            player.frame_index % len(HELD_STONE_AXE_MOTION[player.state])
        ]
        if player.direction in WEST_FACING_DIRECTIONS:
            motion_x = -motion_x
        grip_x, grip_y = grip_offsets[player.direction]
        center_x = draw_x + (grip_x + motion_x) * display_scale
        center_y = draw_y + (grip_y + motion_y) * display_scale
        side = -1.0 if player.direction in WEST_FACING_DIRECTIONS else 1.0
        connector_left = center_x - (18.0 if side > 0 else 0.0) * display_scale
        connector_right = center_x + (0.0 if side > 0 else 18.0) * display_scale
        p2.draw_rectangle(
            connector_left,
            center_y - 4.0 * display_scale,
            connector_right,
            center_y + 4.0 * display_scale,
            59,
            33,
            26,
            255,
            True,
        )
        p2.draw_rectangle(
            center_x - (14.0 if side > 0 else 0.0) * display_scale,
            center_y - 1.0 * display_scale,
            center_x + (0.0 if side > 0 else 14.0) * display_scale,
            center_y + 2.0 * display_scale,
            130,
            67,
            38,
            255,
            True,
        )

        # A stepped 5x5-pixel fist matches the source sprite's rounded hand.
        fist_unit = 3.0 * display_scale
        p2.draw_rectangle(
            center_x - 2.0 * fist_unit,
            center_y - fist_unit,
            center_x + 3.0 * fist_unit,
            center_y + 2.0 * fist_unit,
            59,
            33,
            26,
            255,
            True,
        )
        p2.draw_rectangle(
            center_x - fist_unit,
            center_y - 2.0 * fist_unit,
            center_x + 2.0 * fist_unit,
            center_y + 3.0 * fist_unit,
            59,
            33,
            26,
            255,
            True,
        )
        p2.draw_rectangle(
            center_x - fist_unit,
            center_y - fist_unit,
            center_x + 2.0 * fist_unit,
            center_y + 2.0 * fist_unit,
            238,
            157,
            105,
            255,
            True,
        )
        p2.draw_rectangle(
            center_x - fist_unit,
            center_y - fist_unit,
            center_x + fist_unit,
            center_y,
            255,
            208,
            162,
            255,
            True,
        )
        p2.draw_rectangle(
            center_x,
            center_y + fist_unit,
            center_x + 2.0 * fist_unit,
            center_y + 2.0 * fist_unit,
            139,
            74,
            45,
            255,
            True,
        )

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

        image = self.held_item_images[stack.item_id]
        draw_x = player.x if x is None else x
        draw_y = player.y if y is None else y
        if player.state in ("idle", "walk", "run"):
            is_stone_axe = stack.item_id == "stone_axe"
            if is_stone_axe and not behind:
                self._draw_stone_axe_grip(
                    player, draw_x, draw_y, display_scale
                )
                return
            # The stone axe shaft is always behind the authored body so the
            # existing hand pixels wrap over it instead of the axe covering
            # the face/torso like a pasted-on icon.
            is_behind = (
                True
                if is_stone_axe
                else player.direction in NORTH_FACING_DIRECTIONS
            )
            if behind != is_behind:
                return
            offsets = {
                "up": (-34.0, 82.0),
                "up_right": (37.0, 84.0),
                "right": (48.0, 80.0),
                "down_right": (43.0, 76.0),
                "down": (38.0, 74.0),
                "down_left": (-43.0, 76.0),
                "left": (-48.0, 80.0),
                "up_left": (-37.0, 84.0),
            }
            if is_stone_axe:
                offsets = {
                    "up": (39.0, 102.0),
                    "up_right": (42.0, 99.0),
                    "right": (45.0, 96.0),
                    "down_right": (45.0, 90.0),
                    "down": (42.0, 87.0),
                    "down_left": (-45.0, 90.0),
                    "left": (-45.0, 96.0),
                    "up_left": (-42.0, 99.0),
                }
            rotations = {
                "up": 0.42 if is_stone_axe else 0.18,
                "up_right": 0.30 if is_stone_axe else 0.10,
                "right": 0.16 if is_stone_axe else 0.0,
                "down_right": 0.0 if is_stone_axe else -0.10,
                "down": -0.11 if is_stone_axe else -0.18,
                "down_left": 0.0 if is_stone_axe else 0.10,
                "left": -0.16 if is_stone_axe else 0.0,
                "up_left": -0.30 if is_stone_axe else -0.10,
            }
            offset_x, offset_y = offsets[player.direction]
            rotation = rotations[player.direction]
            if is_stone_axe:
                motion = HELD_STONE_AXE_MOTION[player.state][
                    player.frame_index % len(HELD_STONE_AXE_MOTION[player.state])
                ]
                motion_x, motion_y, motion_rotation = motion
                if player.direction in WEST_FACING_DIRECTIONS:
                    motion_x = -motion_x
                    motion_rotation = -motion_rotation
                offset_x += motion_x
                offset_y += motion_y
                rotation += motion_rotation
            image.composite_draw(
                rotation,
                "h" if player.direction in WEST_FACING_DIRECTIONS else "",
                draw_x + offset_x * display_scale,
                draw_y + offset_y * display_scale,
                (84 if is_stone_axe else 48) * display_scale,
                (84 if is_stone_axe else 48) * display_scale,
            )
            return

        definition = ITEMS[stack.item_id]
        if (
            player.state not in ("attack", "axe", "mine", "fish")
            or definition.action != player.state
        ):
            return

        phase = min(player.frame_index, 3)
        is_side = player.direction in ("left", "right")
        # On side swings the wind-up passes behind the body, then the tool
        # crosses in front. Front/back retain their established depth order.
        is_behind = (
            player.direction in NORTH_FACING_DIRECTIONS
            or (is_side and phase == 0)
        )
        if behind != is_behind:
            return
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
        if is_side:
            path, size = CUSTOM_SIDE_TOOL_PATHS[player.state]
        else:
            path, size = (back_paths if is_behind else front_paths)[player.state]
        offset_x, offset_y, rotation = path[phase]
        flip = "h" if player.direction in WEST_FACING_DIRECTIONS else ""
        if player.direction in WEST_FACING_DIRECTIONS:
            offset_x = -offset_x
            rotation = -rotation
        image.composite_draw(
            rotation,
            flip,
            draw_x + offset_x * display_scale,
            draw_y + offset_y * display_scale,
            size * display_scale,
            size * display_scale,
        )


class Game:
    DIALOG_PANEL = Rect(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2, 430, 174)
    _DIALOG_LEFT_BUTTON = Rect(WINDOW_WIDTH / 2 - 100, WINDOW_HEIGHT / 2 - 32, 168, 48)
    _DIALOG_RIGHT_BUTTON = Rect(WINDOW_WIDTH / 2 + 100, WINDOW_HEIGHT / 2 - 32, 180, 48)
    RETRY_BUTTON = _DIALOG_LEFT_BUTTON
    RETURN_TO_LOBBY_BUTTON = _DIALOG_RIGHT_BUTTON
    PAUSE_QUIT_BUTTON = _DIALOG_LEFT_BUTTON
    PAUSE_RESUME_BUTTON = _DIALOG_RIGHT_BUTTON
    LOBBY_START_BUTTON = Rect(WINDOW_WIDTH / 2, 340, 390, 72)
    LOBBY_QUIT_BUTTON = Rect(WINDOW_WIDTH / 2, 240, 390, 72)
    CUTSCENE_PAUSE_BUTTON = Rect(
        WINDOW_WIDTH - 262, CUTSCENE_CONTROLS_HEIGHT / 2, 76, 36
    )
    CUTSCENE_FAST_FORWARD_BUTTON = Rect(
        WINDOW_WIDTH - 176, CUTSCENE_CONTROLS_HEIGHT / 2, 76, 36
    )
    CUTSCENE_SKIP_BUTTON = Rect(WINDOW_WIDTH - 76, CUTSCENE_CONTROLS_HEIGHT / 2, 104, 36)

    def __init__(self) -> None:
        if not CHARACTER_SHEET.exists():
            raise FileNotFoundError(
                f"Missing v26 eight-direction character sheet: {CHARACTER_SHEET}"
            )
        self._player_sprite_sheet = p2.load_image(str(CHARACTER_SHEET))
        self._map_cache: dict[str, MapData] = {}
        self._background_cache: dict[str, p2.Image] = {}
        self._world_image_cache: dict[Path, p2.Image] = {}
        self._animal_image_cache: dict[tuple[str, str], p2.Image] = {}
        self._cutscene_image_cache: dict[Path, p2.Image] = {}
        self.lobby_background = p2.load_image(str(LOBBY_BACKGROUND_PATH))
        self.lobby_button_image = p2.load_image(str(LOBBY_BUTTON_PATH))
        self._night_mask_images = {
            torch_held: p2.load_image(str(path))
            for torch_held, path in NIGHT_MASK_PATHS.items()
        }
        self._reset_game_state()
        self._start_cutscene(INTRO_CUTSCENE_PATHS, "intro")

    def _reset_game_state(self) -> None:
        """Restore every mutable play-session value to a brand-new game."""
        self.model = InventoryModel.demo()
        self.player = Player(self._player_sprite_sheet)
        if hasattr(self, "ui"):
            self.ui.model = self.model
        else:
            self.ui = GameUI(self.model)
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
        self.game_minutes = GAME_START_MINUTES
        self.sleep_bedding: PlacedUtility | None = None
        self.sleep_minutes_remaining = 0.0
        self.fishing_state = "idle"
        self.fishing_bite_timer = 0.0
        self.fishing_reaction_timer = 0.0
        self.fishing_tension = 0.0
        self.fishing_capture = 0.0
        self.fishing_danger_timer = 0.0
        self.fishing_reeling = False
        self.active_fishing_spot: WorldRect | None = None
        self.fishing_direction: str | None = None
        self.fishing_origin: tuple[float, float] | None = None
        self.transition_armed = False
        self.ending_timer = 0.0
        self.ending_variant = ""
        self.cutscene_sequence: tuple[Path, ...] = ()
        self.cutscene_kind = ""
        self.cutscene_index = 0
        self.cutscene_elapsed = 0.0
        self.cutscene_fast_forward = False
        self.cutscene_paused = False
        self.world_fade_remaining = 0.0
        self.lobby_active = False
        self.lobby_transition = ""
        self.lobby_transition_elapsed = 0.0
        self.running = True
        self.game_over = False
        self.game_paused = False
        self.inventory_open = False
        self.crafting_open = False
        self.pressed: set[int] = set()
        self.drag: DragState | None = None
        self.mouse_screen_x = WINDOW_WIDTH * 0.72
        self.mouse_screen_y = WINDOW_HEIGHT * 0.55
        self.toast = "좌클릭: 공격/투척 | E: 상호작용·도구 공격 | Tab: 인벤토리"
        self.toast_error = False
        self.toast_timer = 5.0
        self._load_map(FIRST_MAP, "player_start")

    def restart_game(self) -> None:
        self._reset_game_state()
        self.world_fade_remaining = LOBBY_FADE_SECONDS

    @property
    def sleeping(self) -> bool:
        return self.sleep_bedding is not None

    @property
    def cutscene_active(self) -> bool:
        return bool(self.cutscene_sequence)

    @staticmethod
    def _cutscene_scene_seconds() -> float:
        return CUTSCENE_FADE_SECONDS * 2.0 + CUTSCENE_HOLD_SECONDS

    def _cutscene_image(self, path: Path) -> p2.Image:
        image = self._cutscene_image_cache.get(path)
        if image is None:
            image = p2.load_image(str(path))
            self._cutscene_image_cache[path] = image
        return image

    def _start_cutscene(self, sequence: tuple[Path, ...], kind: str) -> None:
        if not sequence:
            return
        missing = [path for path in sequence if not path.exists()]
        if missing:
            raise FileNotFoundError(missing[0])
        self.cutscene_sequence = tuple(sequence)
        self.cutscene_kind = kind
        self.cutscene_index = 0
        self.cutscene_elapsed = 0.0
        self.cutscene_fast_forward = False
        self.cutscene_paused = False
        self.world_fade_remaining = 0.0
        self.pressed.clear()
        self.inventory_open = False
        self.crafting_open = False
        self.drag = None
        # Preloading the active sequence avoids a disk-load hitch between
        # consecutive narrative panels. Data-only tests use Game.__new__ and
        # intentionally do not own a render cache.
        if hasattr(self, "_cutscene_image_cache"):
            for path in sequence:
                self._cutscene_image(path)

    def _return_to_lobby(self) -> None:
        self.cutscene_sequence = ()
        self.cutscene_kind = ""
        self.cutscene_index = 0
        self.cutscene_elapsed = 0.0
        self.cutscene_fast_forward = False
        self.cutscene_paused = False
        self.game_paused = False
        self.lobby_active = True
        self.lobby_transition = ""
        self.lobby_transition_elapsed = 0.0
        self.world_fade_remaining = LOBBY_FADE_SECONDS
        self.pressed.clear()
        self.drag = None

    def _activate_lobby_button(self, x: float, y: float) -> bool:
        if not self.lobby_active or self.lobby_transition:
            return False
        if self.LOBBY_START_BUTTON.contains(x, y):
            self.lobby_transition = "start"
        elif self.LOBBY_QUIT_BUTTON.contains(x, y):
            self.lobby_transition = "quit"
        else:
            return False
        self.lobby_transition_elapsed = 0.0
        self.pressed.clear()
        return True

    def _handle_lobby_event(self, event: object) -> None:
        if self.lobby_transition:
            return
        if event.type == p2.SDL_KEYDOWN and event.key == p2.SDLK_RETURN:
            self.lobby_transition = "start"
            self.lobby_transition_elapsed = 0.0
        elif event.type == p2.SDL_MOUSEMOTION:
            self.mouse_screen_x = event.x
            self.mouse_screen_y = WINDOW_HEIGHT - 1 - event.y
        elif (
            event.type == p2.SDL_MOUSEBUTTONDOWN
            and event.button == p2.SDL_BUTTON_LEFT
        ):
            x, y = event.x, WINDOW_HEIGHT - 1 - event.y
            self.mouse_screen_x = x
            self.mouse_screen_y = y
            self._activate_lobby_button(x, y)

    def _update_lobby(self, dt: float) -> None:
        if not self.lobby_transition:
            return
        self.lobby_transition_elapsed = min(
            LOBBY_FADE_SECONDS,
            self.lobby_transition_elapsed + dt,
        )
        if self.lobby_transition_elapsed < LOBBY_FADE_SECONDS:
            return
        if self.lobby_transition == "quit":
            # The loop draws one last fully black lobby frame before closing.
            self.running = False
            return
        self.restart_game()

    def _update_cutscene(self, dt: float) -> None:
        if not self.cutscene_active or self.cutscene_paused:
            return
        playback_rate = CUTSCENE_FAST_FORWARD_RATE if self.cutscene_fast_forward else 1.0
        self.cutscene_elapsed += dt * playback_rate
        scene_seconds = self._cutscene_scene_seconds()
        while self.cutscene_elapsed >= scene_seconds:
            self.cutscene_elapsed -= scene_seconds
            self.cutscene_index += 1
            if self.cutscene_index >= len(self.cutscene_sequence):
                self._return_to_lobby()
                return

    def _request_cutscene_advance(self) -> None:
        if not self.cutscene_active or self.cutscene_paused:
            return
        fade_out_start = CUTSCENE_FADE_SECONDS + CUTSCENE_HOLD_SECONDS
        if self.cutscene_elapsed < fade_out_start:
            self.cutscene_elapsed = fade_out_start

    def _handle_cutscene_event(self, event: object) -> None:
        if event.type == p2.SDL_KEYDOWN:
            if event.key in (p2.SDLK_SPACE, p2.SDLK_RETURN):
                self._request_cutscene_advance()
        elif event.type == p2.SDL_MOUSEMOTION:
            self.mouse_screen_x = event.x
            self.mouse_screen_y = WINDOW_HEIGHT - 1 - event.y
        elif (
            event.type == p2.SDL_MOUSEBUTTONDOWN
            and event.button == p2.SDL_BUTTON_LEFT
        ):
            x, y = event.x, WINDOW_HEIGHT - 1 - event.y
            self.mouse_screen_x, self.mouse_screen_y = x, y
            if self.CUTSCENE_SKIP_BUTTON.contains(x, y):
                self._return_to_lobby()
            elif self.CUTSCENE_PAUSE_BUTTON.contains(x, y):
                self.cutscene_paused = not self.cutscene_paused
            elif self.CUTSCENE_FAST_FORWARD_BUTTON.contains(x, y):
                self.cutscene_fast_forward = not self.cutscene_fast_forward
            else:
                self._request_cutscene_advance()

    def _toggle_game_pause(self) -> None:
        self.game_paused = not self.game_paused
        if self.game_paused:
            self.pressed.clear()
            self.drag = None
            self.fishing_reeling = False

    def _handle_pause_event(self, event: object) -> None:
        if event.type == p2.SDL_MOUSEMOTION:
            self.mouse_screen_x = event.x
            self.mouse_screen_y = WINDOW_HEIGHT - 1 - event.y
        elif event.type == p2.SDL_MOUSEBUTTONDOWN and event.button == p2.SDL_BUTTON_LEFT:
            x, y = event.x, WINDOW_HEIGHT - 1 - event.y
            self.mouse_screen_x, self.mouse_screen_y = x, y
            if self.PAUSE_QUIT_BUTTON.contains(x, y):
                self._return_to_lobby()
            elif self.PAUSE_RESUME_BUTTON.contains(x, y):
                self.game_paused = False

    def _enter_game_over(self) -> None:
        if getattr(self, "game_over", False):
            return
        self.game_over = True
        self.pressed.clear()
        self.inventory_open = False
        self.crafting_open = False
        self.drag = None

    def _activate_game_over_button(self, x: float, y: float) -> bool:
        if self.RETRY_BUTTON.contains(x, y):
            self.restart_game()
            return True
        if self.RETURN_TO_LOBBY_BUTTON.contains(x, y):
            self._return_to_lobby()
            return True
        return False

    def show_toast(self, message: str, *, error: bool = False, seconds: float = 2.2) -> None:
        self.toast = message
        self.toast_error = error
        self.toast_timer = seconds

    def _advance_game_clock(self, dt: float) -> None:
        self.game_minutes = (
            self.game_minutes + dt * GAME_MINUTES_PER_REAL_SECOND
        ) % GAME_DAY_MINUTES

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
            self._enter_game_over()
            self.show_toast("HP가 모두 소진되어 쓰러졌습니다", error=True)
        else:
            self.show_toast("공격을 받아 HP가 감소했습니다", error=True)
        return damage_taken

    def handle_events(self) -> None:
        for event in p2.get_events():
            if event.type == p2.SDL_QUIT:
                self.running = False
                return
            elif event.type == p2.SDL_KEYDOWN and event.key == p2.SDLK_ESCAPE:
                if self.lobby_active or getattr(event, "repeat", 0):
                    continue
                if self.cutscene_active or self.game_over:
                    self._return_to_lobby()
                else:
                    self._toggle_game_pause()
            elif self.cutscene_active:
                self._handle_cutscene_event(event)
            elif self.game_paused:
                self._handle_pause_event(event)
            elif self.world_fade_remaining > 0.0:
                continue
            elif self.lobby_active:
                self._handle_lobby_event(event)
            elif self.game_over:
                if event.type == p2.SDL_MOUSEMOTION:
                    self.mouse_screen_x = event.x
                    self.mouse_screen_y = WINDOW_HEIGHT - 1 - event.y
                elif (
                    event.type == p2.SDL_MOUSEBUTTONDOWN
                    and event.button == p2.SDL_BUTTON_LEFT
                ):
                    x, y = event.x, WINDOW_HEIGHT - 1 - event.y
                    self.mouse_screen_x = x
                    self.mouse_screen_y = y
                    self._activate_game_over_button(x, y)
            elif self.sleeping:
                continue
            elif self.fishing_state != "idle":
                self._handle_fishing_event(event)
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
                    if self._try_sleep_at_screen(x, y):
                        continue
                    if not self._throw_equipped_at_screen(x, y):
                        self._use_primary_attack()
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
        if getattr(self, "game_over", False):
            return
        if key in (p2.SDLK_w, p2.SDLK_a, p2.SDLK_s, p2.SDLK_d, p2.SDLK_LSHIFT, p2.SDLK_RSHIFT):
            self.pressed.add(key)
            return
        if repeated:
            return
        if key == p2.SDLK_TAB:
            self.inventory_open = not self.inventory_open
            if self.inventory_open:
                self.crafting_open = False
            self.drag = None
        elif key == p2.SDLK_c:
            self.crafting_open = not self.crafting_open
            if self.crafting_open:
                self.inventory_open = False
            self.drag = None
        elif key == p2.SDLK_e:
            if not self._interact_world():
                self._use_equipped_with_e()
        elif key == p2.SDLK_h:
            self.damage_player(10.0)
        elif key == p2.SDLK_k:
            if self.player.take_damage(self.player.hp) > 0:
                self._enter_game_over()
                self.show_toast("HP가 모두 소진되어 쓰러졌습니다", error=True)

    def _handle_fishing_event(self, event: object) -> None:
        if event.type == p2.SDL_KEYDOWN:
            if event.key != p2.SDLK_SPACE:
                return
            if self.fishing_state == "bite":
                self._begin_fishing_minigame()
            elif self.fishing_state == "minigame":
                self.fishing_reeling = True
        elif event.type == p2.SDL_KEYUP and event.key == p2.SDLK_SPACE:
            self.fishing_reeling = False

    def _use_tool(self) -> None:
        tool = self.model.equipped_tool_definition
        if tool is None:
            if not self.player.start_action("attack"):
                return
            enemy = self._nearest_melee_enemy(UNARMED_RANGE_TILES)
            if enemy is None:
                self.show_toast("맨손 공격")
                return
            damage = enemy.take_damage(UNARMED_DAMAGE)
            enemy.receive_alert(self.player.x, self.player.y)
            affinity = self._adjust_species_affinity(
                enemy.animal, -AFFINITY_LOSS_PER_HIT
            )
            self.show_toast(
                f"{self._enemy_label(enemy)} 맨손 명중 · {damage} 피해 · "
                f"호감도 -{AFFINITY_LOSS_PER_HIT} ({affinity}/100)",
                seconds=1.7,
            )
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
        if tool.item_id == "fishing_rod":
            self.show_toast("낚시 스팟 가까이에서 E 키를 누르세요", error=True)
            return
        if tool.action and self.player.start_action(tool.action):
            labels = {"attack": "공격", "axe": "도끼질", "mine": "채광", "fish": "낚시"}
            if tool.action == "attack" and tool.item_id in MELEE_DAMAGE:
                enemy = self._nearest_melee_enemy(
                    MELEE_RANGE_TILES[tool.item_id]
                )
                if enemy is not None:
                    damage = enemy.take_damage(MELEE_DAMAGE[tool.item_id])
                    enemy.receive_alert(self.player.x, self.player.y)
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

    def _use_primary_attack(self) -> bool:
        stack = self.model.tool_slot
        if stack is not None and stack.item_id not in MELEE_DAMAGE:
            return False
        self._use_tool()
        return True

    def _use_equipped_with_e(self) -> None:
        stack = self.model.tool_slot
        if stack is None:
            self.show_toast("가까운 상호작용 대상이 없습니다", error=True)
            return
        if stack.definition.heal_amount > 0:
            self._consume_equipped_food()
            return
        if stack.item_id in INSTALLABLE_ITEM_IDS:
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

    def _nearest_melee_enemy(self, range_tiles: float) -> EnemyAI | None:
        facing_x, facing_y = DIRECTION_VECTORS[self.player.direction]
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
                distance <= range_tiles * WORLD_TILE_SIZE
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
        self.player.direction = direction_from_vector(dx, dy, self.player.direction)

    def _throw_target_world(self, screen_x: float, screen_y: float) -> tuple[float, float]:
        target_x, target_y = self.screen_to_world(screen_x, screen_y)
        start_x = self.player.x
        start_y = self.player.y + CHARACTER_HEIGHT * 0.34
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.hypot(dx, dy)
        maximum = PROJECTILE_MAX_TILES * WORLD_TILE_SIZE
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

    def _nearest_placed_utility(
        self, item_id: str | None = None
    ) -> PlacedUtility | None:
        maximum_distance = PLACED_UTILITY_SCREEN_DISTANCE / self.camera_zoom
        nearest: PlacedUtility | None = None
        nearest_distance = math.inf
        for utility in self._current_placed_utilities():
            if item_id is not None and utility.item_id != item_id:
                continue
            distance = math.hypot(
                utility.x - self.player.x, utility.y - self.player.y
            )
            if distance <= maximum_distance and distance < nearest_distance:
                nearest = utility
                nearest_distance = distance
        return nearest

    def _nearest_fishing_spot(self) -> WorldRect | None:
        maximum_distance = INTERACTION_SCREEN_DISTANCE / self.camera_zoom
        nearest: WorldRect | None = None
        nearest_distance = math.inf
        for spot in self.map_data.fishing_spots:
            closest_x = min(max(self.player.x, spot.left), spot.right)
            closest_y = min(max(self.player.y, spot.bottom), spot.top)
            distance = math.hypot(
                self.player.x - closest_x, self.player.y - closest_y
            )
            if distance <= maximum_distance and distance < nearest_distance:
                nearest = spot
                nearest_distance = distance
        return nearest

    def _start_fishing(self, spot: WorldRect) -> None:
        held = self.model.tool_slot
        if held is None or held.item_id != "fishing_rod":
            self.show_toast("낚싯대를 툴바에 장착해야 합니다", error=True)
            return
        self.fishing_state = "waiting"
        self.fishing_bite_timer = random.uniform(
            FISHING_BITE_MIN_SECONDS, FISHING_BITE_MAX_SECONDS
        )
        self.fishing_reaction_timer = 0.0
        self.fishing_tension = 0.0
        self.fishing_capture = 0.0
        self.fishing_danger_timer = 0.0
        self.fishing_reeling = False
        self.active_fishing_spot = spot
        self.fishing_direction = self.player.direction
        self.fishing_origin = (self.player.x, self.player.y)
        self.inventory_open = False
        self.crafting_open = False
        self.drag = None
        self.pressed.clear()
        self.player.start_action("fish")
        self.show_toast("낚시 시작 · 입질 신호를 기다리세요")

    def _begin_fishing_minigame(self) -> None:
        held = self.model.tool_slot
        if held is None or held.item_id != "fishing_rod":
            self._finish_fishing(False, "낚싯대가 없어 낚시를 중단했습니다")
            return
        broke, remaining, label = self._wear_equipped_item(SlotRef.tool(), 2)
        if broke:
            self._finish_fishing(False, f"{label}이(가) 부러져 물고기를 놓쳤습니다")
            return
        self.fishing_state = "minigame"
        self.fishing_reeling = True
        self.fishing_tension = 0.0
        self.fishing_capture = 0.0
        self.fishing_danger_timer = 0.0
        self.show_toast(
            f"Space 누르기/놓기로 장력 조절 · 낚싯대 {remaining}/30",
            seconds=2.4,
        )

    def _finish_fishing(self, success: bool, message: str) -> None:
        if success:
            collected, remainder = self._give_loot(
                "fish", 1, self.player.x, self.player.y
            )
            if collected:
                message = "생선을 낚았습니다 · 인벤토리에 생선 1개 추가"
            elif remainder:
                message = "생선을 낚았지만 인벤토리가 가득 차 바닥에 떨어졌습니다"
        self.fishing_state = "idle"
        self.fishing_bite_timer = 0.0
        self.fishing_reaction_timer = 0.0
        self.fishing_reeling = False
        self.fishing_danger_timer = 0.0
        self.active_fishing_spot = None
        self.player._set_state("idle")
        self.fishing_direction = None
        self.fishing_origin = None
        self.show_toast(message, error=not success, seconds=2.5)

    def _update_fishing(self, dt: float) -> None:
        if self.fishing_origin is not None:
            self.player.x, self.player.y = self.fishing_origin
        if self.fishing_direction is not None:
            self.player.direction = self.fishing_direction
        if self.player.state != "fish":
            self.player.start_action("fish")
        else:
            self.player._advance_animation(dt)

        if self.fishing_state == "waiting":
            self.fishing_bite_timer -= dt
            if self.fishing_bite_timer <= 0.0:
                self.fishing_state = "bite"
                self.fishing_reaction_timer = FISHING_REACTION_SECONDS
                self.show_toast("입질! 제한 시간 안에 Spacebar를 누르세요!", seconds=1.3)
            return
        if self.fishing_state == "bite":
            self.fishing_reaction_timer -= dt
            if self.fishing_reaction_timer <= 0.0:
                self._finish_fishing(False, "입질에 늦게 반응해 물고기가 도망갔습니다")
            return
        if self.fishing_state != "minigame":
            return

        tension_delta = (
            FISHING_TENSION_RISE_PER_SECOND
            if self.fishing_reeling
            else -FISHING_TENSION_FALL_PER_SECOND
        )
        self.fishing_tension = min(
            max(self.fishing_tension + tension_delta * dt, 0.0), 100.0
        )
        in_safe_range = (
            FISHING_SAFE_TENSION_MIN
            <= self.fishing_tension
            <= FISHING_SAFE_TENSION_MAX
        )
        if in_safe_range:
            self.fishing_capture = min(
                100.0,
                self.fishing_capture + FISHING_CAPTURE_PER_SECOND * dt,
            )
        else:
            self.fishing_capture = max(
                0.0,
                self.fishing_capture - FISHING_CAPTURE_LOSS_PER_SECOND * dt,
            )

        in_danger = (
            self.fishing_tension <= FISHING_DANGER_TENSION_MIN
            or self.fishing_tension >= FISHING_DANGER_TENSION_MAX
        )
        if in_danger:
            self.fishing_danger_timer += dt
        else:
            self.fishing_danger_timer = max(
                0.0, self.fishing_danger_timer - dt * 2.0
            )
        if self.fishing_danger_timer >= FISHING_DANGER_HOLD_SECONDS:
            self._finish_fishing(False, "위험 장력이 오래 유지되어 물고기를 놓쳤습니다")
        elif self.fishing_capture >= 100.0:
            self._finish_fishing(True, "")

    def _placed_bedding_at_screen(
        self, screen_x: float, screen_y: float
    ) -> PlacedUtility | None:
        width, height = PLACED_UTILITY_WORLD_SIZES["travel_bedding"]
        for utility in reversed(self._current_placed_utilities()):
            if utility.item_id != "travel_bedding":
                continue
            center_x, center_y = self.world_to_screen(utility.x, utility.y)
            rect = Rect(
                center_x,
                center_y,
                width * self.camera_zoom,
                height * self.camera_zoom,
            )
            if rect.contains(screen_x, screen_y):
                return utility
        return None

    def _sleep_is_available(self) -> bool:
        minute = self.game_minutes % GAME_DAY_MINUTES
        return minute >= SLEEP_ALLOWED_START_MINUTES or minute < SLEEP_WAKE_MINUTES

    def _try_sleep_at_screen(self, screen_x: float, screen_y: float) -> bool:
        bedding = self._placed_bedding_at_screen(screen_x, screen_y)
        if bedding is None:
            return False

        maximum_distance = PLACED_UTILITY_SCREEN_DISTANCE / self.camera_zoom
        distance = math.hypot(
            bedding.x - self.player.x, bedding.y - self.player.y
        )
        if distance > maximum_distance:
            self.show_toast("간이 침구 가까이에서 잠을 잘 수 있습니다", error=True)
            return True
        if not self._sleep_is_available():
            self.show_toast("간이 침구는 오후 05:00부터 사용할 수 있습니다", error=True)
            return True

        self.sleep_bedding = bedding
        self.sleep_minutes_remaining = (
            SLEEP_WAKE_MINUTES - self.game_minutes
        ) % GAME_DAY_MINUTES
        self.pressed.clear()
        self.inventory_open = False
        self.crafting_open = False
        self.drag = None
        self.player._set_state("idle")
        self.show_toast("", seconds=0.0)
        return True

    def _update_sleep(self, dt: float) -> None:
        advance = min(
            self.sleep_minutes_remaining,
            dt * SLEEP_FAST_FORWARD_MINUTES_PER_REAL_SECOND,
        )
        self.game_minutes = (self.game_minutes + advance) % GAME_DAY_MINUTES
        self.sleep_minutes_remaining -= advance
        if self.sleep_minutes_remaining <= 1e-6:
            self.game_minutes = SLEEP_WAKE_MINUTES
            self.sleep_minutes_remaining = 0.0
            self.sleep_bedding = None
            self.show_toast("푹 자고 일어났습니다 · 오전 08:00")

    def _utility_placement_position(
        self, item_id: str
    ) -> tuple[float, float] | None:
        forward_x, forward_y = DIRECTION_VECTORS[self.player.direction]
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

    def _cook_equipped_fish(self) -> None:
        stack = self.model.tool_slot
        if stack is None or stack.item_id != "fish":
            return
        count = stack.count
        self.model.tool_slot = ItemStack("cooked_fish", count)
        self.show_toast(f"모닥불에서 생선 {count}개를 익혔습니다")

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
        held = self.model.tool_slot
        if held is not None and held.item_id == "fish":
            campfire = self._nearest_placed_utility("campfire")
            if campfire is not None:
                self._cook_equipped_fish()
                return True
            return False
        if held is not None and held.item_id == "cooked_fish":
            return False

        utility = self._nearest_placed_utility()
        if utility is not None:
            self._pickup_placed_utility(utility)
            return True
        if held is not None and held.item_id in INSTALLABLE_ITEM_IDS:
            self._place_utility(held.item_id)
            return True
        if held is not None and held.item_id == "fishing_rod":
            fishing_spot = self._nearest_fishing_spot()
            if fishing_spot is not None:
                self._start_fishing(fishing_spot)
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
                hit_enemy.receive_alert(self.player.x, self.player.y)
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
        enemies = self._current_enemies()
        alerts: list[EnemyAI] = []
        for enemy in enemies:
            damage = enemy.update(
                dt,
                self.map_data,
                self.player,
                self.species_affinity[enemy.animal],
                self.camera_zoom,
            )
            if damage > 0:
                self.damage_player(damage)
            if (
                enemy.just_alerted
                and enemy.last_seen_x is not None
                and enemy.last_seen_y is not None
            ):
                alerts.append(enemy)

        for source in alerts:
            alert_distance = (
                AI_SENSES[source.animal]["alert_tiles"] * WORLD_TILE_SIZE
            )
            if alert_distance <= 0:
                continue
            for target in enemies:
                if target is source or not target.alive:
                    continue
                if self.species_affinity[target.animal] >= AFFINITY_MAX:
                    continue
                if source.animal == "crow" and target.animal not in ("wolf", "bear"):
                    continue
                if source.animal == "wolf" and target.animal != "bear":
                    continue
                if math.hypot(target.x - source.x, target.y - source.y) > alert_distance:
                    continue
                target.receive_alert(source.last_seen_x, source.last_seen_y)

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
        desired_species = desired_map_species(map_name, self.species_affinity)
        if reloaded or map_name not in self.enemies:
            self.enemies[map_name] = self._spawn_map_enemies(
                map_data, desired_species
            )
        else:
            self._sync_map_enemies(map_data, desired_species)
        self.camera_zoom = CAMERA_ZOOM
        self.transition_armed = False
        self._update_camera()

    @staticmethod
    def _spawn_map_enemies(
        map_data: MapData, kinds: tuple[str, ...] | None = None
    ) -> list[EnemyAI]:
        if kinds is None:
            kinds = MAP_NATIVE_AI_KINDS.get(map_data.name, ())
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

    def _sync_map_enemies(
        self, map_data: MapData, desired_species: tuple[str, ...]
    ) -> None:
        existing = self.enemies.setdefault(map_data.name, [])
        spawned = self._spawn_map_enemies(map_data, desired_species)
        synchronized: list[EnemyAI] = []
        used: set[int] = set()
        for template in spawned:
            match_index = next(
                (
                    index
                    for index, enemy in enumerate(existing)
                    if index not in used and enemy.animal == template.animal
                ),
                None,
            )
            if match_index is None:
                synchronized.append(template)
            else:
                used.add(match_index)
                synchronized.append(existing[match_index])
        self.enemies[map_data.name] = synchronized

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
        return "대립 엔딩"

    def _begin_ending_cutscene(self) -> None:
        self.ending_variant = self._affinity_ending()
        sequence = (
            RECONCILIATION_ENDING_CUTSCENE_PATHS
            if self.ending_variant == "완전한 화해 엔딩"
            else CONFLICT_ENDING_CUTSCENE_PATHS
        )
        self.ending_timer = 0.0
        self.player._set_state("idle")
        self._start_cutscene(sequence, "ending")

    def _update_transition(self) -> None:
        transition = self.map_data.transition_at(self.player.x, self.player.y)
        if transition is None:
            self.transition_armed = True
            return
        if not self.transition_armed:
            return
        if transition.ends_game:
            self._begin_ending_cutscene()
            self.transition_armed = False
            return
        if transition.target_map is None:
            return
        self._load_map(transition.target_map, transition.target_spawn)
        self.show_toast(f"{self.map_data.label}(으)로 이동했습니다")

    def update(self, dt: float) -> None:
        if self.game_paused:
            return
        if self.cutscene_active:
            self._update_cutscene(dt)
            return
        if self.world_fade_remaining > 0.0:
            self.world_fade_remaining = max(
                0.0, self.world_fade_remaining - dt
            )
            return
        if self.lobby_active:
            self._update_lobby(dt)
            return
        if self.player.dead and not self.game_over:
            self._enter_game_over()
        if self.game_over:
            # Let the fall animation finish beneath the modal, while every
            # other mutable world system remains frozen.
            self.player.update(dt, set())
            return
        if self.sleeping:
            self._update_sleep(dt)
            return
        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0:
                self.toast = ""
        if self.fishing_state != "idle":
            self._advance_game_clock(dt)
            self._update_fishing(dt)
            return
        self._advance_game_clock(dt)
        self._update_entity_timers(dt)
        self.player.update(
            dt,
            self.pressed,
            self._resolve_player_movement,
            stamina_recovery_multiplier(self.game_minutes),
        )
        self._update_enemies(dt)
        if not self.game_over:
            self._update_projectiles(dt)
            self._update_camera()
            self._auto_pickup_world_items()
            self._update_transition()

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
        dive_offset = 0.0
        if enemy.animal == "crow" and enemy.alive:
            frame_count, fps, _loops = ANIMAL_ANIMATIONS["crow"][enemy.state]
            flight_bob = math.sin(enemy.flight_clock * math.tau * 1.15) * 5.0
            if enemy.state == "attack":
                visual_frame = min(
                    enemy.frame_index + enemy.frame_clock * fps,
                    frame_count - 1,
                )
                attack_progress = visual_frame / max(1, frame_count - 1)
                dive = math.sin(math.pi * attack_progress)
                dive_offset = -enemy.display_size * 0.42 * dive
                size *= 1.0 - 0.28 * dive
        screen_x, screen_y = self.world_to_screen(
            enemy.x,
            enemy.y + enemy.display_size * 0.42 + flight_bob + dive_offset,
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
        if enemy.alive:
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
            indicator_path = AWARENESS_ICON_PATHS.get(enemy.awareness)
            if indicator_path is not None:
                self._world_image(indicator_path).draw(
                    screen_x,
                    bar_bottom + AWARENESS_ICON_CENTER_OFFSET,
                    AWARENESS_ICON_SCREEN_SIZE,
                    AWARENESS_ICON_SCREEN_SIZE,
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
        self.ui.draw_hud_panel(
            self.ui.HUD_COLUMN_LEFT, 483, self.ui.HUD_COLUMN_RIGHT, 607
        )
        self.ui.font_small.draw(19, 589, "종 호감도", (255, 238, 205))
        rows = (("crow", 558.0), ("wolf", 530.0), ("bear", 502.0))
        for species, bottom in rows:
            bar_left = 101.0
            bar_right = self.ui.HUD_COLUMN_RIGHT - 6
            bar_top = bottom + 16.0
            row_center_y = (bottom + bar_top) / 2
            label_y = row_center_y + 2
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
                row_center_y,
                28,
                28,
            )
            self.ui.font_small.draw(
                43, label_y, SPECIES_LABELS[species], (245, 231, 198)
            )
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
            self._draw_centered_text(
                self.ui.font_small,
                label_y,
                f"{value}/100",
                (255, 255, 255),
                center_x=(bar_left + bar_right) / 2,
            )

    def _night_vision_radius(self) -> float:
        held = self.model.tool_slot
        if held is not None and held.item_id == "torch":
            return TORCH_VISION_RADIUS
        return NIGHT_VISION_RADIUS

    def _draw_night_overlay(self, center_x: float, center_y: float) -> None:
        """Darken the world and leave a feathered player-centered sight circle."""
        progress = night_darkness_progress(self.game_minutes)
        if progress <= 0.0:
            return

        pico_core.SDL_SetRenderDrawBlendMode(
            pico_core.renderer, pico_core.SDL_BLENDMODE_BLEND
        )
        ambient_alpha = round(NIGHT_AMBIENT_ALPHA * progress)
        p2.draw_rectangle(
            0,
            0,
            WINDOW_WIDTH,
            WINDOW_HEIGHT,
            4,
            15,
            29,
            ambient_alpha,
            True,
        )

        exterior_alpha = round(NIGHT_EXTERIOR_ALPHA * progress ** 1.35)
        if exterior_alpha <= 0:
            pico_core.SDL_SetRenderDrawBlendMode(
                pico_core.renderer, pico_core.SDL_BLENDMODE_NONE
            )
            return

        half_mask = NIGHT_MASK_SIZE / 2.0
        mask_left = center_x - half_mask
        mask_right = center_x + half_mask
        mask_bottom = center_y - half_mask
        mask_top = center_y + half_mask

        def draw_exterior(left: float, bottom: float, right: float, top: float) -> None:
            left = max(0.0, left)
            bottom = max(0.0, bottom)
            right = min(float(WINDOW_WIDTH), right)
            top = min(float(WINDOW_HEIGHT), top)
            if right <= left or top <= bottom:
                return
            p2.draw_rectangle(
                left,
                bottom,
                right,
                top,
                1,
                5,
                12,
                exterior_alpha,
                True,
            )

        draw_exterior(0, mask_top, WINDOW_WIDTH, WINDOW_HEIGHT)
        draw_exterior(0, 0, WINDOW_WIDTH, mask_bottom)
        draw_exterior(0, mask_bottom, mask_left, mask_top)
        draw_exterior(mask_right, mask_bottom, WINDOW_WIDTH, mask_top)
        pico_core.SDL_SetRenderDrawBlendMode(
            pico_core.renderer, pico_core.SDL_BLENDMODE_NONE
        )

        held = self.model.tool_slot
        mask = self._night_mask_images[
            held is not None and held.item_id == "torch"
        ]
        mask.opacify(exterior_alpha / 255.0)
        mask.draw(center_x, center_y, NIGHT_MASK_SIZE, NIGHT_MASK_SIZE)
        mask.opacify(1.0)

    def _draw_game_clock(self) -> None:
        period = game_time_period(self.game_minutes)
        label = f"{period} {format_game_time(self.game_minutes)}"
        self._draw_hud_label(label, 1116, 1268)

    def _draw_hud_label(self, label: str, left: float, right: float) -> None:
        self.ui.draw_hud_panel(left, 678, right, 710)
        self._draw_centered_text(
            self.ui.font, 694, label, (255, 236, 183), center_x=(left + right) / 2
        )

    @staticmethod
    def _draw_black_overlay(alpha: int) -> None:
        alpha = min(max(int(alpha), 0), 255)
        if alpha <= 0:
            return
        pico_core.SDL_SetRenderDrawBlendMode(
            pico_core.renderer, pico_core.SDL_BLENDMODE_BLEND
        )
        p2.draw_rectangle(
            0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0, 0, 0, alpha, True
        )
        pico_core.SDL_SetRenderDrawBlendMode(
            pico_core.renderer, pico_core.SDL_BLENDMODE_NONE
        )

    def _draw_cutscene(self) -> None:
        p2.draw_rectangle(
            0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 0, 0, 0, 255, True
        )
        path = self.cutscene_sequence[
            min(self.cutscene_index, len(self.cutscene_sequence) - 1)
        ]
        image = self._cutscene_image(path)
        scene_height = WINDOW_HEIGHT - CUTSCENE_CONTROLS_HEIGHT
        scale = min(WINDOW_WIDTH / image.w, scene_height / image.h)
        image.draw(
            WINDOW_WIDTH / 2,
            CUTSCENE_CONTROLS_HEIGHT + scene_height / 2,
            image.w * scale,
            image.h * scale,
        )

        fade_out_start = CUTSCENE_FADE_SECONDS + CUTSCENE_HOLD_SECONDS
        if self.cutscene_elapsed < CUTSCENE_FADE_SECONDS:
            progress = self.cutscene_elapsed / CUTSCENE_FADE_SECONDS
            blackout_alpha = round(255 * (1.0 - progress))
        elif self.cutscene_elapsed < fade_out_start:
            blackout_alpha = 0
        else:
            progress = (
                self.cutscene_elapsed - fade_out_start
            ) / CUTSCENE_FADE_SECONDS
            blackout_alpha = round(255 * min(max(progress, 0.0), 1.0))
        self._draw_black_overlay(blackout_alpha)
        self._draw_cutscene_controls()

    def _draw_cutscene_controls(self) -> None:
        pause = self.CUTSCENE_PAUSE_BUTTON
        fast_forward = self.CUTSCENE_FAST_FORWARD_BUTTON
        skip = self.CUTSCENE_SKIP_BUTTON
        self._draw_hud_button(pause, active=self.cutscene_paused)
        self._draw_hud_button(fast_forward, active=self.cutscene_fast_forward)
        self._draw_hud_button(skip)
        pause_icon = self.ui.PLAY_ICON if self.cutscene_paused else self.ui.PAUSE_ICON
        self.ui.draw_hud_icon(pause_icon, pause.cx, pause.cy)
        self.ui.draw_hud_icon(self.ui.FAST_FORWARD_ICON, fast_forward.cx, fast_forward.cy)
        self._draw_centered_text(
            self.ui.font, skip.cy + 1, "SKIP", (255, 230, 174), center_x=skip.cx
        )

    def _draw_hud_button(self, rect: Rect, *, active: bool = False) -> None:
        self.ui.draw_hud_panel(rect.left, rect.bottom, rect.right, rect.top)
        hovered = rect.contains(self.mouse_screen_x, self.mouse_screen_y)
        if active or hovered:
            fill_color = (98, 72, 37) if active else (64, 48, 31)
            p2.draw_rectangle(
                rect.left + 2,
                rect.bottom + 2,
                rect.right - 2,
                rect.top - 2,
                *fill_color,
                255,
                True,
            )

    def _draw_world_fade(self) -> None:
        if self.world_fade_remaining <= 0.0:
            return
        alpha = round(
            255 * self.world_fade_remaining / LOBBY_FADE_SECONDS
        )
        self._draw_black_overlay(alpha)

    def _draw_lobby(self) -> None:
        self.lobby_background.draw(
            WINDOW_WIDTH / 2,
            WINDOW_HEIGHT / 2,
            WINDOW_WIDTH,
            WINDOW_HEIGHT,
        )

        # A soft shadow keeps the title readable without hiding the artwork.
        self._draw_centered_text(
            self.ui.font_lobby_title,
            548,
            GAME_TITLE,
            (25, 18, 26),
            offset_x=4,
            offset_y=-5,
        )
        self._draw_centered_text(
            self.ui.font_lobby_title,
            548,
            GAME_TITLE,
            (255, 224, 157),
        )
        for rect, label in (
            (self.LOBBY_START_BUTTON, "게임 시작"),
            (self.LOBBY_QUIT_BUTTON, "게임 종료"),
        ):
            hovered = (
                not self.lobby_transition
                and rect.contains(self.mouse_screen_x, self.mouse_screen_y)
            )
            draw_width = 432 if hovered else 420
            draw_height = 144 if hovered else 140
            self.lobby_button_image.opacify(1.0 if hovered else 0.92)
            self.lobby_button_image.draw(
                rect.cx,
                rect.cy,
                draw_width,
                draw_height,
            )
            self.lobby_button_image.opacify(1.0)
            text_color = (255, 239, 194) if hovered else (232, 216, 184)
            self._draw_centered_text(
                self.ui.font_lobby_button,
                rect.cy,
                label,
                text_color,
            )

        if self.lobby_transition:
            progress = min(
                self.lobby_transition_elapsed / LOBBY_FADE_SECONDS,
                1.0,
            )
            self._draw_black_overlay(round(255 * progress))

    @staticmethod
    def _draw_centered_text(
        font: p2.Font,
        center_y: float,
        text: str,
        color: tuple[int, int, int],
        *,
        center_x: float = WINDOW_WIDTH / 2,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> None:
        width = GameUI.measure_text_width(font, text)
        font.draw(
            center_x - width / 2 + offset_x,
            center_y + offset_y,
            text,
            color,
        )

    def _draw_sleep_overlay(self) -> None:
        if not self.sleeping:
            return
        pico_core.SDL_SetRenderDrawBlendMode(
            pico_core.renderer, pico_core.SDL_BLENDMODE_BLEND
        )
        p2.draw_rectangle(
            0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, 2, 6, 14, 95, True
        )
        pico_core.SDL_SetRenderDrawBlendMode(
            pico_core.renderer, pico_core.SDL_BLENDMODE_NONE
        )

    def _draw_fishing_ui(self, player_x: float, player_y: float) -> None:
        if self.fishing_state == "idle":
            return

        panel_width = 278.0
        panel_height = 100.0
        panel_left = min(
            max(player_x - panel_width / 2.0, 12.0),
            WINDOW_WIDTH - panel_width - 12.0,
        )
        panel_bottom = min(
            player_y + CHARACTER_HEIGHT * self.camera_zoom + 20.0,
            WINDOW_HEIGHT - panel_height - 48.0,
        )
        panel_right = panel_left + panel_width
        panel_top = panel_bottom + panel_height
        p2.draw_rectangle(
            panel_left,
            panel_bottom,
            panel_right,
            panel_top,
            16,
            21,
            25,
            225,
            True,
        )
        p2.draw_rectangle(
            panel_left,
            panel_bottom,
            panel_right,
            panel_top,
            235,
            224,
            194,
            220,
            False,
        )

        if self.fishing_state == "waiting":
            status = "입질을 기다리는 중..."
            status_color = (255, 236, 183)
        elif self.fishing_state == "bite":
            status = "! 입질!  SPACEBAR !"
            status_color = (255, 184, 92)
        else:
            status = "SPACE 누르기: 감기  ·  놓기: 풀기"
            status_color = (220, 232, 240)
        self.ui.font_small.draw(
            panel_left + 12.0,
            panel_top - 22.0,
            status,
            status_color,
        )

        bar_left = panel_left + 61.0
        bar_right = panel_right - 12.0
        capture_bottom = panel_bottom + 45.0
        tension_bottom = panel_bottom + 14.0
        bar_height = 17.0
        self.ui.font_small.draw(
            panel_left + 11.0,
            capture_bottom + 1.0,
            "포획",
            (222, 238, 245),
        )
        self.ui.font_small.draw(
            panel_left + 11.0,
            tension_bottom + 1.0,
            "장력",
            (222, 238, 245),
        )

        for bottom in (capture_bottom, tension_bottom):
            p2.draw_rectangle(
                bar_left,
                bottom,
                bar_right,
                bottom + bar_height,
                5,
                8,
                12,
                245,
                True,
            )

        capture_right = bar_left + (
            (bar_right - bar_left) * self.fishing_capture / 100.0
        )
        if capture_right > bar_left:
            p2.draw_rectangle(
                bar_left,
                capture_bottom,
                capture_right,
                capture_bottom + bar_height,
                71,
                181,
                223,
                255,
                True,
            )

        safe_left = bar_left + (
            (bar_right - bar_left) * FISHING_SAFE_TENSION_MIN / 100.0
        )
        safe_right = bar_left + (
            (bar_right - bar_left) * FISHING_SAFE_TENSION_MAX / 100.0
        )
        tension_right = bar_left + (
            (bar_right - bar_left) * self.fishing_tension / 100.0
        )
        if (
            self.fishing_tension <= FISHING_DANGER_TENSION_MIN
            or self.fishing_tension >= FISHING_DANGER_TENSION_MAX
        ):
            tension_color = (235, 75, 68)
        elif FISHING_SAFE_TENSION_MIN <= self.fishing_tension <= FISHING_SAFE_TENSION_MAX:
            tension_color = (91, 205, 111)
        else:
            tension_color = (239, 182, 72)
        if tension_right > bar_left:
            p2.draw_rectangle(
                bar_left,
                tension_bottom,
                tension_right,
                tension_bottom + bar_height,
                *tension_color,
                235,
                True,
            )
        p2.draw_rectangle(
            safe_left,
            tension_bottom,
            safe_right,
            tension_bottom + bar_height,
            176,
            241,
            154,
            220,
            False,
        )
        self.ui.font_small.draw(
            bar_right - 37.0,
            capture_bottom + 1.0,
            f"{int(self.fishing_capture)}%",
            (245, 249, 252),
        )
        self.ui.font_small.draw(
            bar_right - 37.0,
            tension_bottom + 1.0,
            f"{int(self.fishing_tension)}%",
            (245, 249, 252),
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

    def _draw_pause_menu(self) -> None:
        self._draw_game_dialog(
            "게임을 그만두시겠습니까?",
            (
                (self.PAUSE_QUIT_BUTTON, "게임 종료"),
                (self.PAUSE_RESUME_BUTTON, "게임으로 돌아가기"),
            ),
        )

    def _draw_game_over(self) -> None:
        self._draw_game_dialog(
            "게임 오버",
            (
                (self.RETRY_BUTTON, "다시 하기"),
                (self.RETURN_TO_LOBBY_BUTTON, "로비로"),
            ),
            description="HP가 모두 소진되어 쓰러졌습니다",
        )

    def _draw_game_dialog(
        self,
        title: str,
        buttons: tuple[tuple[Rect, str], ...],
        *,
        description: str = "",
    ) -> None:
        self._draw_black_overlay(135)
        panel = self.DIALOG_PANEL
        self.ui.draw_hud_panel(panel.left, panel.bottom, panel.right, panel.top)
        text_color = (255, 230, 174)
        self._draw_centered_text(
            self.ui.font_title,
            panel.top - (32 if description else 44),
            title,
            text_color,
            center_x=panel.cx,
        )
        if description:
            self._draw_centered_text(
                self.ui.font,
                panel.top - 62,
                description,
                (232, 216, 184),
                center_x=panel.cx,
            )
        for rect, label in buttons:
            self._draw_hud_button(rect)
            self._draw_centered_text(
                self.ui.font, rect.cy + 1, label, text_color, center_x=rect.cx
            )

    def draw(self, *, present: bool = True) -> None:
        p2.clear_canvas()
        if self.cutscene_active:
            self._draw_cutscene()
            if present:
                p2.update_canvas()
            return
        if self.lobby_active:
            self._draw_lobby()
            self._draw_world_fade()
            if present:
                p2.update_canvas()
            return
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
                if utility is self.sleep_bedding:
                    self.player.draw_sleeping(
                        Rect(utility_x, utility_y, draw_width, draw_height)
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
        bedding = self.sleep_bedding
        if bedding is None:
            self._draw_awake_player(player_x, player_y)
            sight_x = player_x
            sight_y = player_y + CHARACTER_HEIGHT * self.camera_zoom / 2.0
        else:
            sight_x, sight_y = self.world_to_screen(bedding.x, bedding.y)
        self._draw_night_overlay(sight_x, sight_y)
        self._draw_sleep_overlay()
        self._draw_fishing_ui(player_x, player_y)
        self._draw_hud_label(
            self.map_data.label, self.ui.HUD_COLUMN_LEFT, self.ui.HUD_COLUMN_RIGHT
        )
        self._draw_game_clock()
        self.ui.draw_status_bars(self.player)
        self._draw_species_affinity()
        hovered_slot = None
        if not (self.crafting_open or self.game_paused or self.game_over):
            hovered_slot = self.ui.slot_at(
                self.mouse_screen_x, self.mouse_screen_y, self.inventory_open
            )
        self.ui.draw(
            self.inventory_open,
            self.crafting_open,
            self.drag,
            "" if self.game_over else self.toast,
            self.toast_error,
            hovered_slot,
            self.mouse_screen_x,
            self.mouse_screen_y,
        )
        if self.game_over:
            self._draw_game_over()
        self._draw_world_fade()
        if self.game_paused:
            self._draw_pause_menu()
        if present:
            p2.update_canvas()

    def _draw_awake_player(self, player_x: float, player_y: float) -> None:
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
        held = self.model.tool_slot
        if self.fishing_state != "idle":
            nearby_utility = None
        elif held is not None and held.item_id == "fish":
            nearby_utility = self._nearest_placed_utility("campfire")
        elif held is not None and held.item_id == "cooked_fish":
            nearby_utility = None
        else:
            nearby_utility = self._nearest_placed_utility()
        nearby: WorldEntity | None = None
        if nearby_utility is not None:
            prompt_x, prompt_y = self.world_to_screen(
                nearby_utility.x, nearby_utility.y
            )
            label = ITEMS[nearby_utility.item_id].label
            if (
                nearby_utility.item_id == "campfire"
                and held is not None
                and held.item_id == "fish"
            ):
                prompt = "E · 생선 굽기"
                prompt_offset = 49
            elif (
                nearby_utility.item_id == "campfire"
                and held is not None
                and held.item_id == "cooked_fish"
            ):
                prompt = "E · 익힌 생선 먹기"
                prompt_offset = 65
            elif nearby_utility.item_id == "travel_bedding":
                prompt = "E · 회수 / 좌클릭 · 잠자기"
                prompt_offset = 89
            else:
                prompt = f"E · {label} 회수"
                prompt_offset = 45
            self.ui.font_small.draw(
                prompt_x - prompt_offset,
                prompt_y + 55,
                prompt,
                (255, 245, 176),
            )
        elif self.fishing_state == "idle":
            if held is not None and held.item_id in ("fish", "cooked_fish"):
                label = ITEMS[held.item_id].label
                self.ui.font_small.draw(
                    player_x - 42,
                    player_y + 55,
                    f"E · {label} 먹기",
                    (255, 245, 176),
                )
            else:
                fishing_spot = (
                    self._nearest_fishing_spot()
                    if held is not None and held.item_id == "fishing_rod"
                    else None
                )
            if (
                held is not None
                and held.item_id not in ("fish", "cooked_fish")
                and fishing_spot is not None
            ):
                prompt_x, prompt_y = self.world_to_screen(
                    fishing_spot.left + fishing_spot.width / 2.0,
                    fishing_spot.bottom + fishing_spot.height / 2.0,
                )
                self.ui.font_small.draw(
                    prompt_x - 42,
                    prompt_y + 16,
                    "E · 낚시 시작",
                    (255, 245, 176),
                )
            elif held is None or held.item_id not in ("fish", "cooked_fish"):
                nearby = self._nearest_interactable()
        if nearby is not None:
            rect = nearby.definition.rect
            prompt_x, prompt_y = self.world_to_screen(
                rect.left + rect.width / 2, rect.top
            )
            label = self._entity_label(nearby.definition.entity_type)
            self.ui.font_small.draw(prompt_x - 42, prompt_y + 10, f"E · {label}", (255, 245, 176))


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
            if not game.running:
                break
            game.update(dt)
            game.draw()
            p2.delay(0.001)
    finally:
        p2.close_canvas()


if __name__ == "__main__":
    main()
