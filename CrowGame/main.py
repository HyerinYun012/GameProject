"""CrowGame four-map prototype with inventory, hotbar, and equipment UI."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pico2d as p2

try:  # Works both as ``python main.py`` and ``python -m CrowGame.main``.
    from .game_model import ITEMS, InventoryModel, ItemStack, SlotRef
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
    from game_model import ITEMS, InventoryModel, ItemStack, SlotRef
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
CAMERA_ZOOM = 0.50
INTERACTION_SCREEN_DISTANCE = 125.0
AUTO_PICKUP_SCREEN_DISTANCE = 115.0
MANUAL_PICKUP_SCREEN_DISTANCE = 145.0
THROWN_DROP_REARM_MOVEMENT = 30.0
FRUIT_COOLDOWN_SECONDS = 30.0
THROWN_DROP_MIN_SCREEN_DISTANCE = 80.0
THROWN_DROP_MAX_SCREEN_DISTANCE = 130.0
THROWN_DROP_SCREEN_SIZE = 76.0
ASSET_DIR = Path(__file__).resolve().parent / "assets"
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
class WorldEntity:
    definition: WorldEntityDefinition
    hp: int
    visible: bool = True
    completed: bool = False
    cooldown_remaining: float = 0.0
    is_on: bool = False

    @classmethod
    def create(cls, definition: WorldEntityDefinition) -> "WorldEntity":
        return cls(
            definition=definition,
            hp=max(1, int(definition.properties.get("hp", 1))),
            is_on=bool(definition.properties.get("is_on", False)),
        )

    @property
    def sprite_path(self) -> Path:
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

# The atlas has clean front/back body frames but only side-on tool swings.  For
# vertical tool use, these four body poses are combined with a direction-aware
# world-tool arc in GameUI.  This avoids showing a sideways body while facing up
# or down and preserves the original side animations where they exist.
VERTICAL_TOOL_FRAMES: dict[str, tuple[SpriteFrame, ...]] = {
    "down": frames_at(192, (176, 208, 240, 272)),
    "up": frames_at(144, (176, 208, 240, 272)),
}

HURT_FRAMES: dict[str, tuple[SpriteFrame, ...]] = {
    "down": frames_at(384, (0, 32, 64)),
    "up": frames_at(432, (0, 32, 64)),
    "right": frames_at(480, (0, 32, 64)),
    "left": frames_at(528, (0, 32, 64)),
}

ATTACK_FRAMES: dict[str, tuple[SpriteFrame, ...]] = {
    "right": frames_at(288, (0, 32, 32, 0)),
    "left": frames_at(288, (64, 96, 96, 64)),
    "up": frames_at(336, (0, 32, 32, 0)),
    "down": frames_at(336, (64, 96, 96, 64)),
}


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

    def _frames_for_state(self) -> tuple[SpriteFrame, ...]:
        if self.state == "idle":
            return IDLE_FRAMES[self.direction]
        if self.state in ("walk", "run"):
            return MOVE_FRAMES[self.direction]
        if self.state == "hurt":
            return HURT_FRAMES[self.direction]
        if self.state == "attack":
            return ATTACK_FRAMES[self.direction]
        if self.state == "death":
            base = {
                "left": IDLE_FRAMES["left"][0],
                "right": IDLE_FRAMES["right"][0],
                "down": IDLE_FRAMES["down"][0],
                "up": IDLE_FRAMES["up"][0],
            }[self.direction]
            return (base, base, base, base)

        flip = "h" if self.direction == "left" else ""
        if self.state == "axe":
            if self.direction in VERTICAL_TOOL_FRAMES:
                return VERTICAL_TOOL_FRAMES[self.direction]
            return frames_at(288, (176, 208, 240, 272), flip)
        if self.state == "mine":
            if self.direction in VERTICAL_TOOL_FRAMES:
                return VERTICAL_TOOL_FRAMES[self.direction]
            return frames_at(240, (176, 208, 240, 272), flip)
        if self.state == "fish":
            if self.direction in VERTICAL_TOOL_FRAMES:
                return VERTICAL_TOOL_FRAMES[self.direction]
            if self.direction == "left":
                return frames_at(432, (240, 272, 272, 240))
            return frames_at(432, (176, 208, 208, 176))
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
        self._set_state("idle")

    def update(
        self,
        dt: float,
        pressed: set[int],
        movement_resolver: Callable[[float, float, float, float], tuple[float, float]] | None = None,
    ) -> None:
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

                running = p2.SDLK_LSHIFT in pressed or p2.SDLK_RSHIFT in pressed
                speed = self.RUN_SPEED if running else self.WALK_SPEED
                move_x = dx * speed * dt
                move_y = dy * speed * dt
                if movement_resolver is None:
                    self.x += move_x
                    self.y += move_y
                    self.x = max(CHARACTER_WIDTH / 2, min(WINDOW_WIDTH - CHARACTER_WIDTH / 2, self.x))
                    self.y = max(155.0, min(WINDOW_HEIGHT - CHARACTER_HEIGHT - 15.0, self.y))
                else:
                    self.x, self.y = movement_resolver(self.x, self.y, move_x, move_y)
                self._set_state("run" if running else "walk")
            else:
                self._set_state("idle")

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
        drag: DragState | None,
        toast: str,
        toast_error: bool,
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

        self.font.draw(1017, 146, "TOOL", (255, 225, 165))
        self.font.draw(1161, 146, "ARMOR", (255, 225, 165))
        self.font.draw(1151, 17, f"DEF {self.model.defense}", (235, 242, 255))

        if drag:
            self.item_images[drag.item_id].draw(drag.x, drag.y, 70, 70)
        if toast:
            color = (255, 125, 115) if toast_error else (255, 237, 176)
            p2.draw_rectangle(376, 655, 904, 700, 28, 24, 22, 220, True)
            self.font.draw(405, 677, toast, color)

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

    def draw_equipped_world_tool(
        self,
        player: Player,
        *,
        behind: bool,
        x: float | None = None,
        y: float | None = None,
        display_scale: float = 1.0,
    ) -> None:
        """Draw equipped tools at rest and animate vertical tool-use arcs."""
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
            player.direction not in ("up", "down")
            or player.state not in ("axe", "mine", "fish")
            or definition.action != player.state
        ):
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
        }
        path, size = (back_paths if is_behind else front_paths)[player.state]
        offset_x, offset_y, rotation = path[phase]
        image.composite_draw(
            rotation,
            "h" if is_behind else "",
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
        self.world_drops: dict[str, list[WorldDrop]] = {}
        self.world_entities: dict[str, list[WorldEntity]] = {}
        self.map_data: MapData
        self.map_background: p2.Image | None
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.camera_zoom = CAMERA_ZOOM
        self.transition_armed = False
        self.ending_timer = 0.0
        self.running = True
        self.inventory_open = False
        self.pressed: set[int] = set()
        self.drag: DragState | None = None
        self.toast = "E: 채집·이벤트 상호작용  |  Space: 도구 사용  |  Tab: 인벤토리"
        self.toast_error = False
        self.toast_timer = 5.0
        self._load_map(FIRST_MAP, "player_start")

    def show_toast(self, message: str, *, error: bool = False, seconds: float = 2.2) -> None:
        self.toast = message
        self.toast_error = error
        self.toast_timer = seconds

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
                source = self.ui.slot_at(x, y, self.inventory_open)
                if source:
                    stack = self.model.get(source)
                    if stack:
                        self.drag = DragState(source, stack.item_id, x, y)
            elif event.type == p2.SDL_MOUSEMOTION and self.drag:
                self.drag.x = event.x
                self.drag.y = WINDOW_HEIGHT - 1 - event.y
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
            self.drag = None
        elif key == p2.SDLK_SPACE:
            self._use_tool()
        elif key == p2.SDLK_e:
            if not self._interact_world():
                self._use_tool()
        elif key == p2.SDLK_f:
            self._pickup_nearby_item()
        elif key == p2.SDLK_h:
            if self.player.start_action("hurt"):
                self.show_toast("피격 애니메이션")
        elif key == p2.SDLK_k:
            if self.player.start_action("death"):
                self.show_toast("쓰러졌습니다. R 키로 일어나기")
        elif key == p2.SDLK_r:
            self.player.revive()
            self.show_toast("다시 일어났습니다")

    def _use_tool(self) -> None:
        tool = self.model.equipped_tool_definition
        if tool is None:
            self.show_toast("tool 슬롯에 도구를 먼저 넣으세요", error=True)
            return
        if tool.action == "torch":
            self.show_toast("횃불을 밝혔습니다")
            return
        if tool.action and self.player.start_action(tool.action):
            labels = {"attack": "공격", "axe": "도끼질", "mine": "채광", "fish": "낚시"}
            self.show_toast(f"{tool.label}: {labels.get(tool.action, tool.action)}")

    def _current_entities(self) -> list[WorldEntity]:
        return self.world_entities.setdefault(self.map_data.name, [])

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
                f"{label} 채집은 tool 슬롯에 {required_label}를 장착해야 합니다",
                error=True,
            )
            return
        if required_action and not self.player.start_action(required_action):
            return

        entity.hp -= 1
        if entity.hp > 0:
            self.show_toast(f"{label}: {entity.hp}번 더 채집해야 합니다")
            return

        entity.visible = False
        item_id = str(entity.definition.properties.get("drop_item", "fiber"))
        count = int(entity.definition.properties.get("drop_count", 1))
        collected, remainder = self._give_loot(
            item_id, count, rect.left + rect.width / 2, rect.bottom
        )
        suffix = f" · {remainder}개는 바닥에 떨어졌습니다" if remainder else ""
        self.show_toast(f"{label}을(를) 수확해 {ITEMS[item_id].label} {collected}개 획득{suffix}")

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
            self.show_toast(f"발전기 {state_label} · 보상 {reward}")
            return

        entity.completed = True
        if entity.definition.alternate_sprite_path is None:
            entity.visible = False
        self.show_toast(f"{label} 완료 · 보상 {reward}")

    def _update_entity_timers(self, dt: float) -> None:
        for entities in self.world_entities.values():
            for entity in entities:
                if entity.cooldown_remaining <= 0:
                    continue
                entity.cooldown_remaining = max(0.0, entity.cooldown_remaining - dt)
                if entity.cooldown_remaining == 0:
                    entity.completed = False

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
            target_name = "도구" if target.area == "tool" else "방어구" if target.area == "armor" else "해당"
            self.show_toast(f"{target_name} 슬롯에 넣을 수 없는 아이템입니다", error=True)
        self.drag = None

    def _pickup_nearby_item(self) -> None:
        drops = self.world_drops.setdefault(self.map_data.name, [])
        if not drops:
            self.show_toast("근처에 주울 아이템이 없습니다", error=True, seconds=1.2)
            return
        nearby = min(
            drops,
            key=lambda drop: (drop.x - self.player.x) ** 2 + (drop.y - self.player.y) ** 2,
        )
        distance_squared = (nearby.x - self.player.x) ** 2 + (nearby.y - self.player.y) ** 2
        pickup_radius = MANUAL_PICKUP_SCREEN_DISTANCE / self.camera_zoom
        if distance_squared > pickup_radius ** 2:
            self.show_toast("아이템에 더 가까이 가세요", error=True, seconds=1.2)
            return
        original_count = nearby.stack.count
        remainder = self.model.add_item(nearby.stack.item_id, original_count)
        collected = original_count - remainder
        if collected == 0:
            self.show_toast("인벤토리가 가득 찼습니다", error=True)
            return
        if remainder:
            nearby.stack.count = remainder
        else:
            drops.remove(nearby)
        self.show_toast(f"{nearby.stack.definition.label} {collected}개를 주웠습니다")

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
            remainder = self.model.add_item(drop.stack.item_id, original_count)
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
        if reloaded or map_name not in self.world_entities:
            self.world_entities[map_name] = [
                WorldEntity.create(definition) for definition in map_data.entities
            ]
        self.camera_zoom = CAMERA_ZOOM
        self.transition_armed = False
        self._update_camera()

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

    def _update_transition(self) -> None:
        transition = self.map_data.transition_at(self.player.x, self.player.y)
        if transition is None:
            self.transition_armed = True
            return
        if not self.transition_armed:
            return
        if transition.ends_game:
            self.ending_timer = 1.25
            self.pressed.clear()
            self.player._set_state("idle")
            self.show_toast("엔딩 통로에 도착했습니다. 게임을 종료합니다.", seconds=1.25)
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
                if (
                    entity.definition.entity_type == "fruit_tree"
                    and entity.cooldown_remaining > 0
                ):
                    marker_y = entity_y + draw_height * 0.1
                    p2.draw_rectangle(
                        entity_x - 34,
                        marker_y - 13,
                        entity_x + 34,
                        marker_y + 13,
                        20,
                        55,
                        25,
                        225,
                        True,
                    )
                    self.ui.font_small.draw(
                        entity_x - 25,
                        marker_y - 6,
                        f"OK {math.ceil(entity.cooldown_remaining)}s",
                        (188, 255, 166),
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
        player_x, player_y = self.world_to_screen(self.player.x, self.player.y)
        self.ui.draw_equipped_world_tool(
            self.player,
            behind=True,
            x=player_x,
            y=player_y,
            display_scale=self.camera_zoom,
        )
        self.player.draw(player_x, player_y, display_scale=self.camera_zoom)
        self.ui.draw_equipped_world_tool(
            self.player,
            behind=False,
            x=player_x,
            y=player_y,
            display_scale=self.camera_zoom,
        )
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
        self.ui.draw(self.inventory_open, self.drag, self.toast, self.toast_error)
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
