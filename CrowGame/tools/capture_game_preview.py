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
    world_resources_preview = generated / "game_preview_world_resources.png"
    world_event_preview = generated / "game_preview_world_event.png"
    fruit_cooldown_preview = generated / "game_preview_fruit_cooldown.png"
    projectile_flight_preview = generated / "game_preview_projectile_flight.png"
    projectile_aim_preview = generated / "game_preview_projectile_aim.png"
    ai_hurt_preview = generated / "game_preview_ai_hurt.png"
    ai_attack_preview = generated / "game_preview_ai_attack.png"
    crow_flight_preview = generated / "game_preview_crow_flight.png"
    alert_network_preview = generated / "game_preview_alert_network.png"
    action_previews = {
        "attack": generated / "game_preview_attack.png",
        "axe": generated / "game_preview_axe.png",
        "mine": generated / "game_preview_mine.png",
        "death": generated / "game_preview_death.png",
    }
    direction_previews = {
        (action, direction): generated / f"game_preview_{action}_{direction}.png"
        for action in ("attack", "axe", "mine", "fish")
        for direction in ("down", "up", "right", "left")
    }
    p2.open_canvas(WINDOW_WIDTH, WINDOW_HEIGHT)
    try:
        game = Game()
        game.inventory_open = True
        game.model.try_move(SlotRef.inventory(0), SlotRef.tool())
        game.model.armor_slot = ItemStack("light_armor", durability=12)
        game.model.slots[1].lose_durability(8)
        hovered_rect = game.ui.inventory_slots()[1][1]
        game.mouse_screen_x = hovered_rect.cx
        game.mouse_screen_y = hovered_rect.cy
        game.toast = "내구도 게이지 · 슬롯에 마우스를 올리면 현재/최대 표시"
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
            if state == "attack":
                game.model.tool_slot = ItemStack("wooden_sword")
            elif state == "axe":
                game.model.tool_slot = ItemStack("wooden_axe")
            elif state == "mine":
                game.model.tool_slot = ItemStack("wooden_pickaxe")
            game.player.state = state
            game.player.dead = state == "death"
            game.player.direction = "right"
            game.player.frame_index = 3 if state == "death" else 2
            game.toast = {
                "attack": "통일된 검 공격",
                "axe": "도끼질",
                "mine": "채광질",
                "death": "쓰러지기",
            }[state]
            game.draw(present=False)
            capture(destination)
            p2.update_canvas()

        action_tools = {
            "attack": "wooden_sword",
            "axe": "wooden_axe",
            "mine": "wooden_pickaxe",
            "fish": "fishing_rod",
        }
        action_labels = {
            "attack": "검 공격",
            "axe": "도끼질",
            "mine": "채광질",
            "fish": "낚시",
        }
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

        game._load_map("crow_map.json", "player_start")
        crow = game.enemies["crow_map.json"][0]
        game.player.x = crow.x - 290
        game.player.y = crow.y
        game.player.state = "idle"
        game.player.direction = "right"
        crow._set_state("walk")
        crow.awareness = "suspicious"
        crow.direction_row = 2
        crow.frame_index = 2
        crow.flight_clock = 0.18
        game._update_camera()
        game.toast = "까마귀 비행 · 연속 부유 · 14fps 날갯짓"
        game.draw(present=False)
        capture(crow_flight_preview)
        p2.update_canvas()

        tree = next(
            entity
            for entity in game.world_entities["crow_map.json"]
            if entity.definition.entity_type == "tree"
        )
        tree_rect = tree.definition.rect
        game.player.x = tree_rect.left + tree_rect.width / 2
        game.player.y = tree_rect.bottom - 70
        game.player.state = "idle"
        game.player.direction = "up"
        game._update_camera()
        game.toast = "JSON Resources / Events · E 상호작용"
        game.draw(present=False)
        capture(world_resources_preview)
        p2.update_canvas()

        generator = next(
            entity
            for entity in game.world_entities["crow_map.json"]
            if entity.definition.entity_type == "generator_switch"
        )
        generator_rect = generator.definition.rect
        game.player.x = generator_rect.left + generator_rect.width / 2
        game.player.y = generator_rect.bottom - 70
        game._activate_event(generator)
        game._update_camera()
        game.draw(present=False)
        capture(world_event_preview)
        p2.update_canvas()

        game._load_map("bear_map.json", "player_start")
        fruit_tree = next(
            entity
            for entity in game.world_entities["bear_map.json"]
            if entity.definition.entity_type == "fruit_tree"
        )
        fruit_rect = fruit_tree.definition.rect
        game.player.x = fruit_rect.left + fruit_rect.width / 2
        game.player.y = fruit_rect.bottom - 70
        game._harvest_resource(fruit_tree)
        game._update_camera()
        game.draw(present=False)
        capture(fruit_cooldown_preview)
        p2.update_canvas()

        alert_animals = game.enemies["bear_map.json"]
        alert_offsets = {
            "bear": (260.0, 40.0),
            "crow": (-230.0, 150.0),
            "wolf": (30.0, -30.0),
        }
        for animal in alert_animals:
            offset_x, offset_y = alert_offsets[animal.animal]
            animal.x = game.player.x + offset_x
            animal.y = game.player.y + offset_y
            animal.receive_alert(game.player.x, game.player.y)
        game.toast = "까마귀 경보 → 늑대·곰 마지막 위치 공유 · ! 추적"
        game.draw(present=False)
        capture(alert_network_preview)
        p2.update_canvas()

        game._load_map("wolf_map.json", "player_start")
        game.species_affinity.update({"crow": 25, "wolf": 60, "bear": 90})
        wolf = game.enemies["wolf_map.json"][0]
        game.player.x = wolf.x - 520
        game.player.y = wolf.y
        game.player.state = "idle"
        game.player.dead = False
        game.model.tool_slot = ItemStack("stone_spear")
        game._update_camera()
        target_screen = game.world_to_screen(*wolf.hit_center)
        game._aim_at_screen(*target_screen)
        game.toast = "마우스 이동: 조준 · 좌클릭: 창/돌 던지기"
        game.draw(present=False)
        capture(projectile_aim_preview)
        p2.update_canvas()
        game._throw_equipped_at_screen(*target_screen)
        game._update_projectiles(0.20)
        game.draw(present=False)
        capture(projectile_flight_preview)
        p2.update_canvas()

        for _ in range(8):
            game._update_projectiles(0.05)
            if not game.projectiles["wolf_map.json"]:
                break
        wolf.update(
            0.10,
            game.map_data,
            game.player,
            game.species_affinity[wolf.animal],
            game.camera_zoom,
        )
        game.draw(present=False)
        capture(ai_hurt_preview)
        p2.update_canvas()

        game.player.state = "idle"
        wolf._set_state("attack")
        wolf.frame_index = 2
        game.toast = "경계 관계 · 늑대 근거리 공격"
        game.draw(present=False)
        capture(ai_attack_preview)
        p2.update_canvas()
    finally:
        p2.close_canvas()
    print(inventory_preview)
    print(character_preview)
    print(world_resources_preview)
    print(world_event_preview)
    print(fruit_cooldown_preview)
    print(projectile_flight_preview)
    print(projectile_aim_preview)
    print(ai_hurt_preview)
    print(ai_attack_preview)
    print(crow_flight_preview)
    print(alert_network_preview)
    for destination in action_previews.values():
        print(destination)
    for destination in direction_previews.values():
        print(destination)


if __name__ == "__main__":
    main()
