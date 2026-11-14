"""Map-free CrowGame character, inventory, hotbar, and equipment prototype."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import pico2d as p2

try:  # Works both as ``python main.py`` and ``python -m CrowGame.main``.
    from .game_model import ITEMS, InventoryModel, ItemStack, SlotRef
except ImportError:  # pragma: no cover - exercised by the normal command file.
    from game_model import ITEMS, InventoryModel, ItemStack, SlotRef


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FRAME_WIDTH = 32
FRAME_HEIGHT = 48
CHARACTER_WIDTH = 160
CHARACTER_HEIGHT = 240
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

    def update(self, dt: float, pressed: set[int]) -> None:
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
                self.x += dx * speed * dt
                self.y += dy * speed * dt
                self.x = max(CHARACTER_WIDTH / 2, min(WINDOW_WIDTH - CHARACTER_WIDTH / 2, self.x))
                self.y = max(155.0, min(WINDOW_HEIGHT - CHARACTER_HEIGHT - 15.0, self.y))
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

    def draw(self) -> None:
        frames = self._frames_for_state()
        frame = frames[min(self.frame_index, len(frames) - 1)]
        source_bottom = self.sprite_sheet.h - frame.top - FRAME_HEIGHT
        offset_x, offset_y, rotation = self._state_transform()
        self.sprite_sheet.clip_composite_draw(
            frame.left,
            source_bottom,
            FRAME_WIDTH,
            FRAME_HEIGHT,
            rotation,
            frame.flip,
            self.x + offset_x,
            self.y + CHARACTER_HEIGHT / 2 + offset_y,
            CHARACTER_WIDTH,
            CHARACTER_HEIGHT,
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

    def draw_equipped_world_tool(self, player: Player, *, behind: bool) -> None:
        """Draw equipped tools at rest and animate vertical tool-use arcs."""
        stack = self.model.tool_slot
        if stack is None:
            return

        image = self.item_images[stack.item_id]
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
                player.x + offset_x,
                player.y + offset_y,
                48,
                48,
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
            player.x + offset_x,
            player.y + offset_y,
            size,
            size,
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
        self.running = True
        self.inventory_open = False
        self.pressed: set[int] = set()
        self.drag: DragState | None = None
        self.toast = "Tab: 인벤토리  |  WASD: 이동  |  E/Space: 장착 도구 사용"
        self.toast_error = False
        self.toast_timer = 5.0
        self.collect_index = 0

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
        elif key in (p2.SDLK_SPACE, p2.SDLK_e):
            self._use_tool()
        elif key == p2.SDLK_h:
            if self.player.start_action("hurt"):
                self.show_toast("피격 애니메이션")
        elif key == p2.SDLK_k:
            if self.player.start_action("death"):
                self.show_toast("쓰러졌습니다. R 키로 일어나기")
        elif key == p2.SDLK_r:
            self.player.revive()
            self.show_toast("다시 일어났습니다")
        elif key == p2.SDLK_c:
            self._collect_test_item()

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

    def _collect_test_item(self) -> None:
        item_id = ("wood", "stone", "fiber")[self.collect_index % 3]
        self.collect_index += 1
        remainder = self.model.add_item(item_id, 1)
        if remainder:
            self.show_toast("인벤토리가 가득 찼습니다", error=True)
        else:
            self.show_toast(f"{ITEMS[item_id].label} 1개 자동 수집")

    def _finish_drag(self, x: float, y: float) -> None:
        if not self.drag:
            return
        target = self.ui.slot_at(x, y, self.inventory_open)
        if target is None:
            self.show_toast("이동이 취소되었습니다", error=True, seconds=1.2)
        elif self.model.try_move(self.drag.source, target):
            self.show_toast("슬롯이 동기화되었습니다", seconds=1.2)
        else:
            target_name = "도구" if target.area == "tool" else "방어구" if target.area == "armor" else "해당"
            self.show_toast(f"{target_name} 슬롯에 넣을 수 없는 아이템입니다", error=True)
        self.drag = None

    def update(self, dt: float) -> None:
        self.player.update(dt, self.pressed)
        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0:
                self.toast = ""

    def draw(self, *, present: bool = True) -> None:
        p2.clear_canvas()
        p2.draw_rectangle(0, 0, WINDOW_WIDTH - 1, WINDOW_HEIGHT - 1, 25, 37, 43, 255, True)
        p2.draw_rectangle(0, 145, WINDOW_WIDTH - 1, 148, 54, 70, 73, 255, True)
        self.ui.draw_equipped_world_tool(self.player, behind=True)
        self.player.draw()
        self.ui.draw_equipped_world_tool(self.player, behind=False)
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
