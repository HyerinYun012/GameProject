from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pico2d as p2


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CrowGame.main import (  # noqa: E402
    ACTION_STATES,
    ATTACK_FRAMES,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    HURT_FRAMES,
    IDLE_FRAMES,
    MOVE_FRAMES,
    Player,
    STATE_FPS,
    VERTICAL_TOOL_FRAMES,
)


class AnimationDataTests(unittest.TestCase):
    def test_directional_animation_sets_exist(self) -> None:
        directions = {"left", "right", "up", "down"}
        self.assertEqual(directions, set(MOVE_FRAMES))
        self.assertEqual(directions, set(IDLE_FRAMES))
        self.assertEqual(directions, set(HURT_FRAMES))
        self.assertEqual(directions, set(ATTACK_FRAMES))
        self.assertEqual(9, len(MOVE_FRAMES["left"]))
        self.assertEqual(9, len(MOVE_FRAMES["right"]))
        self.assertEqual(5, len(MOVE_FRAMES["up"]))
        self.assertEqual(5, len(MOVE_FRAMES["down"]))
        self.assertGreater(STATE_FPS["run"], STATE_FPS["walk"])

    def test_side_idle_frames_face_the_last_horizontal_direction(self) -> None:
        self.assertEqual(96, IDLE_FRAMES["right"][0].left)
        self.assertEqual(208, IDLE_FRAMES["left"][0].left)

    def test_vertical_tool_actions_use_front_and_back_body_frames(self) -> None:
        player = Player(sprite_sheet=None)
        expected_rows = {"down": 192, "up": 144}
        for direction, expected_row in expected_rows.items():
            for state in ("axe", "mine", "fish"):
                player.direction = direction
                player.state = state
                frames = player._frames_for_state()
                self.assertEqual(VERTICAL_TOOL_FRAMES[direction], frames)
                self.assertTrue(all(frame.top == expected_row for frame in frames))

    def test_releasing_horizontal_move_keeps_last_facing_direction(self) -> None:
        cases = (("right", p2.SDLK_d), ("left", p2.SDLK_a))
        for expected_direction, key in cases:
            player = Player(sprite_sheet=None)
            player.update(0.05, {key})
            self.assertEqual(expected_direction, player.direction)
            self.assertEqual("walk", player.state)
            player.update(0.05, set())
            self.assertEqual(expected_direction, player.direction)
            self.assertEqual("idle", player.state)

    def test_every_requested_action_has_frames_inside_the_atlas(self) -> None:
        player = Player(sprite_sheet=None)  # Drawing is not used in this data-only test.
        all_frames = []
        for direction in ("left", "right", "up", "down"):
            player.direction = direction
            for state in ("idle", "walk", "run", "hurt", "death", "attack", "axe", "mine", "fish"):
                player.state = state
                frames = player._frames_for_state()
                self.assertTrue(frames, (direction, state))
                all_frames.extend(frames)

        for frame in all_frames:
            self.assertGreaterEqual(frame.left, 0)
            self.assertGreaterEqual(frame.top, 0)
            self.assertLessEqual(frame.left + FRAME_WIDTH, 304)
            self.assertLessEqual(frame.top + FRAME_HEIGHT, 592)

    def test_action_state_list_is_complete(self) -> None:
        self.assertEqual({"hurt", "death", "attack", "axe", "mine", "fish"}, set(ACTION_STATES))

    def test_static_hurt_cells_get_three_visible_recoil_beats(self) -> None:
        player = Player(sprite_sheet=None)
        player.state = "hurt"
        player.direction = "right"
        transforms = []
        for frame_index in range(3):
            player.frame_index = frame_index
            transforms.append(player._state_transform())
        self.assertEqual(3, len(set(transforms)))

    def test_death_has_four_falling_transforms_and_finishes_horizontal(self) -> None:
        player = Player(sprite_sheet=None)
        player.state = "death"
        player.direction = "right"
        transforms = []
        for frame_index in range(4):
            player.frame_index = frame_index
            transforms.append(player._state_transform())
        self.assertEqual(4, len(set(transforms)))
        self.assertAlmostEqual(1.57079632679, transforms[-1][2], places=5)


if __name__ == "__main__":
    unittest.main()
