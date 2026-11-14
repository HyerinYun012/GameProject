"""Render one deterministic CrowGame frame and save it for visual QA."""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path

import pico2d as p2
import pico2d.pico2d as pico_core

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CrowGame.game_model import ItemStack, SlotRef
from CrowGame.main import Game, WINDOW_HEIGHT, WINDOW_WIDTH
from CrowGame.tools.extract_character_sheet import write_rgba_png


def capture(path: Path) -> None:
    pixels = (ctypes.c_ubyte * (WINDOW_WIDTH * WINDOW_HEIGHT * 4))()
    result = pico_core.SDL_RenderReadPixels(
        pico_core.renderer,
        None,
        pico_core.SDL_PIXELFORMAT_RGBA32,
        pixels,
        WINDOW_WIDTH * 4,
    )
    if result != 0:
        raise RuntimeError("SDL_RenderReadPixels failed")
    write_rgba_png(path, WINDOW_WIDTH, WINDOW_HEIGHT, bytes(pixels))


def main() -> None:
    generated = Path(__file__).resolve().parents[1] / "generated"
    inventory_preview = generated / "game_preview_inventory.png"
    character_preview = generated / "game_preview_character.png"
    action_previews = {
        "axe": generated / "game_preview_axe.png",
        "mine": generated / "game_preview_mine.png",
        "death": generated / "game_preview_death.png",
    }
    direction_previews = {
        (action, direction): generated / f"game_preview_{action}_{direction}.png"
        for action in ("axe", "mine", "fish")
        for direction in ("down", "up", "right", "left")
    }
    p2.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    try:
        game = Game()
        game.inventory_open = True
        game.model.try_move(SlotRef.inventory(0), SlotRef.tool())
        game.model.try_move(SlotRef.inventory(10), SlotRef.armor())
        game.toast = "인벤토리·핫바 동기화 / 도구·방어구 장착"
        game.toast_timer = 99
        game.draw(present=False)
        capture(inventory_preview)
        p2.update_canvas()

        game.inventory_open = False
        game.player.state = "run"
        game.player.direction = "right"
        game.player.frame_index = 4
        game.toast = "WASD 걷기 / Shift 달리기 / E·Space 장착 도구 사용 / Tab 인벤토리"
        game.draw(present=False)
        capture(character_preview)
        p2.update_canvas()

        for state, destination in action_previews.items():
            if state == "axe":
                game.model.tool_slot = ItemStack("wooden_axe")
            elif state == "mine":
                game.model.tool_slot = ItemStack("wooden_pickaxe")
            game.player.state = state
            game.player.dead = state == "death"
            game.player.direction = "right"
            game.player.frame_index = 3 if state == "death" else 2
            game.toast = {"axe": "도끼질", "mine": "채광질", "death": "쓰러지기"}[state]
            game.draw(present=False)
            capture(destination)
            p2.update_canvas()

        action_tools = {"axe": "wooden_axe", "mine": "wooden_pickaxe", "fish": "fishing_rod"}
        action_labels = {"axe": "도끼질", "mine": "채광질", "fish": "낚시"}
        direction_labels = {"down": "앞", "up": "뒤", "right": "오른쪽", "left": "왼쪽"}
        for (state, direction), destination in direction_previews.items():
            game.model.tool_slot = ItemStack(action_tools[state])
            game.player.state = state
            game.player.dead = False
            game.player.direction = direction
            game.player.frame_index = 2
            game.toast = f"{action_labels[state]} · {direction_labels[direction]} 방향"
            game.draw(present=False)
            capture(destination)
            p2.update_canvas()
    finally:
        p2.close_canvas()
    print(inventory_preview)
    print(character_preview)
    for destination in action_previews.values():
        print(destination)
    for destination in direction_previews.values():
        print(destination)


if __name__ == "__main__":
    main()
