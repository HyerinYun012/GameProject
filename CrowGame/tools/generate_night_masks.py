"""Generate smooth alpha masks used by CrowGame's night-vision renderer."""

from __future__ import annotations

import math
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from CrowGame.main import (  # noqa: E402
    NIGHT_MASK_PATHS,
    NIGHT_MASK_SIZE,
    NIGHT_VISION_FEATHER,
    NIGHT_VISION_RADIUS,
    TORCH_VISION_RADIUS,
)
from CrowGame.tools.extract_character_sheet import write_rgba_png  # noqa: E402


MASK_RGB = (1, 5, 12)


def smootherstep(value: float) -> float:
    value = min(max(value, 0.0), 1.0)
    return value * value * value * (value * (value * 6.0 - 15.0) + 10.0)


def build_mask(radius: float) -> bytes:
    center = (NIGHT_MASK_SIZE - 1) / 2.0
    inner_squared = radius * radius
    outer = radius + NIGHT_VISION_FEATHER
    outer_squared = outer * outer
    alpha_pixels = [bytes((*MASK_RGB, alpha)) for alpha in range(256)]
    result = bytearray()

    for y in range(NIGHT_MASK_SIZE):
        dy_squared = (y - center) ** 2
        for x in range(NIGHT_MASK_SIZE):
            distance_squared = (x - center) ** 2 + dy_squared
            if distance_squared <= inner_squared:
                alpha = 0
            elif distance_squared >= outer_squared:
                alpha = 255
            else:
                distance = math.sqrt(distance_squared)
                blend = smootherstep(
                    (distance - radius) / NIGHT_VISION_FEATHER
                )
                alpha = round(255 * blend)
            result.extend(alpha_pixels[alpha])
    return bytes(result)


def main() -> None:
    masks = {
        False: NIGHT_VISION_RADIUS,
        True: TORCH_VISION_RADIUS,
    }
    for torch_held, radius in masks.items():
        destination = NIGHT_MASK_PATHS[torch_held]
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_rgba_png(
            destination,
            NIGHT_MASK_SIZE,
            NIGHT_MASK_SIZE,
            build_mask(radius),
        )
        print(destination)


if __name__ == "__main__":
    main()
