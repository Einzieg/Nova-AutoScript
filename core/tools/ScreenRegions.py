from enum import Enum
from typing import Sequence, Tuple, Union

import numpy as np


SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
TILE_WIDTH = SCREEN_WIDTH // 3
TILE_HEIGHT = SCREEN_HEIGHT // 3

# A small overlap keeps text that straddles a tile boundary inside the OCR crop.
OVERLAP_X = round(TILE_WIDTH * 0.08)
OVERLAP_Y = round(TILE_HEIGHT * 0.08)


class ScreenTile(Enum):
    TOP_LEFT = (0, 0)
    TOP_CENTER = (1, 0)
    TOP_RIGHT = (2, 0)
    MIDDLE_LEFT = (0, 1)
    CENTER = (1, 1)
    MIDDLE_RIGHT = (2, 1)
    BOTTOM_LEFT = (0, 2)
    BOTTOM_CENTER = (1, 2)
    BOTTOM_RIGHT = (2, 2)


ScreenRegion = Union[ScreenTile, Sequence[ScreenTile]]
Bounds = Tuple[int, int, int, int]

CENTER_RIGHT = (ScreenTile.CENTER, ScreenTile.MIDDLE_RIGHT)
RIGHT_MIDDLE_BOTTOM = (ScreenTile.MIDDLE_RIGHT, ScreenTile.BOTTOM_RIGHT)
CENTER_BOTTOM = (ScreenTile.CENTER, ScreenTile.BOTTOM_CENTER)
LOWER_RIGHT = (
    ScreenTile.CENTER,
    ScreenTile.MIDDLE_RIGHT,
    ScreenTile.BOTTOM_CENTER,
    ScreenTile.BOTTOM_RIGHT,
)


def region_bounds(region: ScreenRegion) -> Bounds:
    """Return an overlapped bounding rectangle for one or more adjacent tiles."""
    tiles = (region,) if isinstance(region, ScreenTile) else tuple(region)
    if not tiles:
        raise ValueError("OCR region must contain at least one screen tile")

    columns = [tile.value[0] for tile in tiles]
    rows = [tile.value[1] for tile in tiles]
    left = max(0, min(columns) * TILE_WIDTH - OVERLAP_X)
    top = max(0, min(rows) * TILE_HEIGHT - OVERLAP_Y)
    right = min(SCREEN_WIDTH, (max(columns) + 1) * TILE_WIDTH + OVERLAP_X)
    bottom = min(SCREEN_HEIGHT, (max(rows) + 1) * TILE_HEIGHT + OVERLAP_Y)
    return left, top, right, bottom


def crop_region(image: np.ndarray, region: ScreenRegion) -> Tuple[np.ndarray, Tuple[int, int]]:
    """Crop a 1920x1080 screenshot and return the crop plus its screen origin."""
    if image is None or image.shape[:2] != (SCREEN_HEIGHT, SCREEN_WIDTH):
        shape = None if image is None else image.shape[:2]
        raise ValueError(
            f"Regional OCR requires a {SCREEN_WIDTH}x{SCREEN_HEIGHT} screenshot; got {shape}"
        )

    left, top, right, bottom = region_bounds(region)
    return image[top:bottom, left:right], (left, top)
