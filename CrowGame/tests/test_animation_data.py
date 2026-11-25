from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pico2d as p2


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CrowGame.main import (  # noqa: E402
    ACTION_BODY_FRAMES,
    ACTION_STATES,
    ATTACK_FRAMES,
    CUSTOM_SIDE_BODY_FRAMES,
    CUSTOM_SIDE_TOOL_PATHS,
    DEATH_FRAMES,
    DIRECTIONS,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    HELD_STONE_AXE_MOTION,
    HELD_TOOL_ICON_PATHS,
    HURT_FRAMES,
    IDLE_FRAMES,
    MOVE_FRAMES,
    Player,
    RUN_FRAMES,
    STATE_FPS,
    SIDE_ACTION_FRAMES,
    VERTICAL_TOOL_FRAMES,
)


class AnimationDataTests(unittest.TestCase):
    def test_stone_axe_has_a_dedicated_held_pixel_asset(self) -> None:
        self.assertEqual({"stone_axe"}, set(HELD_TOOL_ICON_PATHS))
        self.assertTrue(HELD_TOOL_ICON_PATHS["stone_axe"].exists())
        self.assertEqual({"idle", "walk", "run"}, set(HELD_STONE_AXE_MOTION))
        for state, motion in HELD_STONE_AXE_MOTION.items():
            self.assertEqual(4, len(motion), state)
            self.assertGreater(len(set(motion)), 1, state)

    def test_directional_animation_sets_exist(self) -> None:
        directions = set(DIRECTIONS)
        self.assertEqual(directions, set(MOVE_FRAMES))
        self.assertEqual(directions, set(RUN_FRAMES))
        self.assertEqual(directions, set(IDLE_FRAMES))
        self.assertEqual(directions, set(HURT_FRAMES))
        self.assertEqual(directions, set(DEATH_FRAMES))
        self.assertEqual(directions, set(ATTACK_FRAMES))
        for direction in directions:
            self.assertEqual(4, len(IDLE_FRAMES[direction]))
            self.assertEqual(4, len(MOVE_FRAMES[direction]))
            self.assertEqual(4, len(RUN_FRAMES[direction]))
            self.assertEqual(2, len(HURT_FRAMES[direction]))
            self.assertEqual(5, len(DEATH_FRAMES[direction]))
        self.assertGreater(STATE_FPS["run"], STATE_FPS["walk"])

    def test_side_idle_frames_face_the_last_horizontal_direction(self) -> None:
        self.assertEqual(1134, IDLE_FRAMES["right"][0].left)
        self.assertEqual(4, IDLE_FRAMES["right"][0].top)
        self.assertEqual(1134, IDLE_FRAMES["left"][0].left)
        self.assertEqual(76, IDLE_FRAMES["left"][0].top)

    def test_front_and_back_actions_share_consistent_body_frames(self) -> None:
        player = Player(sprite_sheet=None)
        expected_rows = {"down": 76, "up": 4}
        for direction, expected_row in expected_rows.items():
            for state in ("attack", "axe", "mine", "fish"):
                player.direction = direction
                player.state = state
                frames = player._frames_for_state()
                self.assertEqual(VERTICAL_TOOL_FRAMES[direction], frames)
                self.assertTrue(all(frame.top == expected_row for frame in frames))

    def test_horizontal_actions_use_custom_clean_side_bodies(self) -> None:
        player = Player(sprite_sheet=None)
        for state in ("attack", "axe", "mine", "fish"):
            for direction in ("left", "right"):
                player.state = state
                player.direction = direction
                self.assertEqual(
                    SIDE_ACTION_FRAMES[state][direction],
                    player._frames_for_state(),
                )
                self.assertEqual(
                    ACTION_BODY_FRAMES[state][direction],
                    player._frames_for_state(),
                )
                self.assertEqual(
                    CUSTOM_SIDE_BODY_FRAMES[direction],
                    player._frames_for_state(),
                )
                self.assertTrue(
                    all(
                        frame.top == (4 if direction == "right" else 76)
                        for frame in player._frames_for_state()
                    )
                )

    def test_tool_actions_reuse_the_replacement_character_idle_frames(self) -> None:
        for state in ("attack", "axe", "mine", "fish"):
            for direction in DIRECTIONS:
                self.assertEqual(
                    IDLE_FRAMES[direction],
                    SIDE_ACTION_FRAMES[state][direction],
                )

    def test_custom_side_action_has_four_authored_body_beats(self) -> None:
        player = Player(sprite_sheet=None)
        player.state = "axe"
        player.direction = "right"
        transforms = []
        for frame_index in range(4):
            player.frame_index = frame_index
            transforms.append(player._state_transform())
        self.assertEqual(4, len(set(transforms)))

    def test_fishing_keeps_one_body_frame_while_only_the_rod_animates(self) -> None:
        player = Player(sprite_sheet=None)
        player.state = "fish"
        for direction in DIRECTIONS:
            player.direction = direction
            visible_frames = []
            transforms = []
            for frame_index in range(4):
                player.frame_index = frame_index
                visible_frames.append(player._frame_for_draw())
                transforms.append(player._state_transform())
            self.assertEqual([IDLE_FRAMES[direction][0]] * 4, visible_frames)
            self.assertEqual([(0.0, 0.0, 0.0)] * 4, transforms)

    def test_each_custom_side_tool_has_four_authored_arc_positions(self) -> None:
        self.assertEqual(
            {"attack", "axe", "mine", "fish"}, set(CUSTOM_SIDE_TOOL_PATHS)
        )
        for path, size in CUSTOM_SIDE_TOOL_PATHS.values():
            self.assertEqual(4, len(path))
            self.assertEqual(4, len(set(path)))
            self.assertGreater(size, 0)

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

    def test_diagonal_move_uses_and_keeps_the_matching_direction(self) -> None:
        player = Player(sprite_sheet=None)
        player.update(0.05, {p2.SDLK_w, p2.SDLK_d})
        self.assertEqual("up_right", player.direction)
        self.assertEqual("walk", player.state)
        player.update(0.05, set())
        self.assertEqual("up_right", player.direction)
        self.assertEqual("idle", player.state)

    def test_every_requested_action_has_frames_inside_the_atlas(self) -> None:
        player = Player(sprite_sheet=None)  # Drawing is not used in this data-only test.
        all_frames = []
        for direction in DIRECTIONS:
            player.direction = direction
            for state in ("idle", "walk", "run", "hurt", "death", "attack", "axe", "mine", "fish"):
                player.state = state
                frames = player._frames_for_state()
                self.assertTrue(frames, (direction, state))
                all_frames.extend(frames)

        for frame in all_frames:
            self.assertGreaterEqual(frame.left, 0)
            self.assertGreaterEqual(frame.top, 0)
            self.assertLessEqual(frame.left + FRAME_WIDTH, 1944)
            self.assertLessEqual(frame.top + FRAME_HEIGHT, 809)

    def test_action_state_list_is_complete(self) -> None:
        self.assertEqual({"hurt", "death", "attack", "axe", "mine", "fish"}, set(ACTION_STATES))

    def test_hurt_and_death_use_native_sheet_motion_without_extra_rotation(self) -> None:
        player = Player(sprite_sheet=None)
        for state, frame_count in (("hurt", 2), ("death", 5)):
            player.state = state
            player.direction = "down_right"
            frames = player._frames_for_state()
            self.assertEqual(frame_count, len(frames))
            self.assertEqual(frame_count, len(set(frames)))
            for frame_index in range(frame_count):
                player.frame_index = frame_index
                self.assertEqual((0.0, 0.0, 0.0), player._state_transform())


if __name__ == "__main__":
    unittest.main()
