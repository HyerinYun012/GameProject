"""Tiled JSON map loading, collision, spawn, and transition data for CrowGame."""

from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


MAP_DIRECTORY = Path(__file__).resolve().parent
MAP_SCALE = 4.0
TILE_CHUNK_SIZE = 512.0
FIRST_MAP = "ruined_town_demo.json"
GID_HORIZONTAL_FLIP = 0x80000000
GID_VERTICAL_FLIP = 0x40000000
GID_DIAGONAL_FLIP = 0x20000000
GID_MASK = 0x1FFFFFFF

RESOURCE_SPRITES = {
    "tree": "assets/Plants - 복사본.png",
    "rock": "assets/9035b6fb-45c2-49de-8d00-101109c7c749.png",
    "grass": "assets/c1949f5d-75ca-4fa8-b2c4-b4e44e9382d1.png",
    "flower": "assets/058d2338-325c-4151-b4db-016499c2936f.png",
    "fruit_tree": "assets/127ea630-ecab-4452-b747-d018dd001cf4.png",
}

EVENT_SPRITES = {
    "generator_switch": "assets/4c458576-ba44-470c-8700-ca5b20278099.png",
    "bird's nest": "assets/aa9b10f1-6fc4-427e-8c8b-da02f9633c12.png",
    "rescue a bird": "assets/c6cc274f-bb8f-4b18-b79a-02ff04ce5d35.png",
    "hunter_trap_remove": "assets/wolf_den_repaired (2).png",
    "wolf_pup_rescue": "assets/wolf_den_repaired (4).png",
    "wolf_den_repair": "assets/wolf_den_repaired (3).png",
    "bear_cub_heal": "assets/594f5cd7-0680-4a1c-a22c-ac33f228d1d2.png",
    "bear_rescue": "assets/46918e73-f77f-42c5-82c7-33d2c105ffa7.png",
    "bear_water_restore": "assets/921b57e3-c949-4bee-9e81-2d3ef3e7ef19 - 복사본.png",
}

EVENT_ALTERNATE_SPRITES = {
    "generator_switch": "assets/12e60a17-1de6-4d84-8cc9-05b2c4ed1915.png",
    "wolf_den_repair": "assets/wolf_den_repaired (1).png",
    "bear_water_restore": "assets/921b57e3-c949-4bee-9e81-2d3ef3e7ef19.png",
}

RUINED_TOWN_SOLID_PROPS = frozenset(
    {
        "barbed_wire",
        "barrier_concrete",
        "barrier_road",
        "bed",
        "box_cardboard",
        "box_stack",
        "brick_pile",
        "bush_dead",
        "campfire",
        "car_burnt",
        "car_wreck",
        "car_wreck_v",
        "chair",
        "couch",
        "crate",
        "crate_broken",
        "drum_toxic",
        "dumpster",
        "fence_chain",
        "fence_chain_broken",
        "fridge",
        "generator",
        "hydrant",
        "mailbox",
        "oil_drum",
        "planks_broken",
        "rubble_large",
        "rubble_small",
        "sandbags",
        "shelf",
        "sign_stop",
        "sign_warning",
        "street_lamp",
        "street_lamp_broken",
        "table",
        "tent",
        "tire",
        "tire_stack",
        "toilet",
        "traffic_cone",
        "trash_bag",
        "trash_can",
        "trash_pile",
        "tree_dead",
        "tv_broken",
    }
)


@dataclass(frozen=True, slots=True)
class MapDefinition:
    json_filename: str
    background_filename: str
    label: str


MAP_DEFINITIONS: dict[str, MapDefinition] = {
    "ruined_town_demo.json": MapDefinition(
        "ruined_town_demo.json", "ruined_town_demo.png", "폐허 마을"
    ),
    "crow_map.json": MapDefinition("crow_map.json", "map_background.png", "까마귀 숲"),
    "wolf_map.json": MapDefinition("wolf_map.json", "wolf_background.png", "늑대 숲"),
    "bear_map.json": MapDefinition("bear_map.json", "bear_background.png", "곰 숲"),
}


@dataclass(frozen=True, slots=True)
class WorldRect:
    left: float
    bottom: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def top(self) -> float:
        return self.bottom + self.height

    def contains(self, x: float, y: float) -> bool:
        return self.left <= x <= self.right and self.bottom <= y <= self.top

    def intersects(self, other: "WorldRect") -> bool:
        return not (
            self.right <= other.left
            or self.left >= other.right
            or self.top <= other.bottom
            or self.bottom >= other.top
        )


@dataclass(frozen=True, slots=True)
class MapTransition:
    name: str
    rect: WorldRect
    target_map: str | None = None
    target_spawn: str = "player_start"
    ends_game: bool = False


@dataclass(frozen=True, slots=True)
class WorldEntityDefinition:
    object_id: int
    name: str
    kind: str
    entity_type: str
    rect: WorldRect
    collision_rect: WorldRect | None
    properties: dict[str, object]
    sprite_path: Path
    alternate_sprite_path: Path | None = None


@dataclass(frozen=True, slots=True)
class TileSpriteDefinition:
    image_path: Path
    clip_left: int
    clip_bottom: int
    clip_width: int
    clip_height: int
    image_width: int
    image_height: int


@dataclass(frozen=True, slots=True)
class MapTileDefinition:
    raw_gid: int
    rect: WorldRect
    sprite: TileSpriteDefinition
    opacity: float = 1.0
    draw_order: int = 0


@dataclass(frozen=True, slots=True)
class MapObjectTileDefinition:
    object_id: int
    name: str
    raw_gid: int
    rect: WorldRect
    sprite: TileSpriteDefinition
    rotation: float = 0.0
    opacity: float = 1.0


@dataclass(frozen=True, slots=True)
class MapData:
    name: str
    label: str
    background_path: Path
    width: float
    height: float
    spawns: dict[str, tuple[float, float]]
    collisions: tuple[WorldRect, ...]
    transitions: tuple[MapTransition, ...]
    entities: tuple[WorldEntityDefinition, ...]
    tiles: tuple[MapTileDefinition, ...]
    object_tiles: tuple[MapObjectTileDefinition, ...]
    source_path: Path
    source_mtime_ns: int
    tile_chunks: dict[tuple[int, int], tuple[MapTileDefinition, ...]]
    tile_margin: float

    def spawn(self, name: str = "player_start") -> tuple[float, float]:
        try:
            return self.spawns[name]
        except KeyError as exc:
            raise KeyError(f"Map {self.name!r} has no spawn named {name!r}") from exc

    def transition_at(self, x: float, y: float) -> MapTransition | None:
        for transition in self.transitions:
            if transition.rect.contains(x, y):
                return transition
        return None

    def tiles_in_view(
        self, left: float, bottom: float, right: float, top: float
    ) -> tuple[MapTileDefinition, ...]:
        if not self.tile_chunks:
            return ()
        start_x = math.floor((left - self.tile_margin) / TILE_CHUNK_SIZE)
        end_x = math.floor((right + self.tile_margin) / TILE_CHUNK_SIZE)
        start_y = math.floor((bottom - self.tile_margin) / TILE_CHUNK_SIZE)
        end_y = math.floor((top + self.tile_margin) / TILE_CHUNK_SIZE)
        candidates = [
            tile
            for chunk_y in range(start_y, end_y + 1)
            for chunk_x in range(start_x, end_x + 1)
            for tile in self.tile_chunks.get((chunk_x, chunk_y), ())
        ]
        candidates.sort(key=lambda tile: tile.draw_order)
        return tuple(candidates)

    def resolve_movement(
        self,
        x: float,
        y: float,
        dx: float,
        dy: float,
        extra_collisions: tuple[WorldRect, ...] = (),
    ) -> tuple[float, float]:
        """Move a small feet hitbox with axis-separated collision sliding."""
        min_x, max_x = 12.0, max(12.0, self.width - 12.0)
        min_y, max_y = 8.0, max(8.0, self.height - 8.0)
        next_x = min(max(x + dx, min_x), max_x)
        if self._blocked(next_x, y, extra_collisions):
            next_x = x
        next_y = min(max(y + dy, min_y), max_y)
        if self._blocked(next_x, next_y, extra_collisions):
            next_y = y
        return next_x, next_y

    def _blocked(
        self, x: float, y: float, extra_collisions: tuple[WorldRect, ...] = ()
    ) -> bool:
        feet = WorldRect(x - 18.0, y - 5.0, 36.0, 22.0)
        return any(feet.intersects(obstacle) for obstacle in (*self.collisions, *extra_collisions))


def _properties(obj: dict[str, object]) -> dict[str, object]:
    return {
        str(prop["name"]): prop.get("value")
        for prop in obj.get("properties", [])  # type: ignore[union-attr]
    }


def _world_rect(
    obj: dict[str, object],
    source_height: float,
    scale: float,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
) -> WorldRect:
    x = float(obj.get("x", 0.0)) + offset_x
    y = float(obj.get("y", 0.0)) + offset_y
    width = float(obj.get("width", 0.0))
    height = float(obj.get("height", 0.0))
    # Tiled tile objects use a bottom-left origin; ordinary rectangles use a
    # top-left origin.  Resource/event objects can contain either form.
    bottom = source_height - y if obj.get("gid") else source_height - y - height
    return WorldRect(x * scale, bottom * scale, width * scale, height * scale)


def _entity_collision(
    rect: WorldRect, properties: dict[str, object], scale: float
) -> WorldRect | None:
    if not properties.get("solid"):
        return None
    width = float(properties.get("collision_w", 0.0)) * scale
    height = float(properties.get("collision_h", 0.0)) * scale
    if width <= 0 or height <= 0:
        return None
    return WorldRect(rect.left + (rect.width - width) / 2, rect.bottom, width, height)


def _tile_collision_runs(
    data: list[object],
    layer_width: int,
    layer_height: int,
    source_height: float,
    tile_width: float,
    tile_height: float,
    scale: float,
    offset_x: float,
    offset_y: float,
) -> list[WorldRect]:
    """Merge adjacent solid tiles into one horizontal collision rectangle."""
    rectangles: list[WorldRect] = []
    for row in range(layer_height):
        column = 0
        while column < layer_width:
            if int(data[row * layer_width + column]) == 0:
                column += 1
                continue
            start = column
            while (
                column < layer_width
                and int(data[row * layer_width + column]) != 0
            ):
                column += 1
            rectangles.append(
                WorldRect(
                    (start * tile_width + offset_x) * scale,
                    (source_height - offset_y - (row + 1) * tile_height) * scale,
                    (column - start) * tile_width * scale,
                    tile_height * scale,
                )
            )
    return rectangles


def _prop_collision(rect: WorldRect, scale: float) -> WorldRect:
    """Use the lower footprint of a top-down prop instead of its full artwork."""
    inset = min(rect.width * 0.15, 4.0 * scale)
    return WorldRect(
        rect.left + inset,
        rect.bottom,
        max(1.0, rect.width - inset * 2),
        min(rect.height, 10.0 * scale),
    )


def _asset_path(filename: str) -> Path:
    normalized = filename.replace("\\", "/")
    if not normalized.startswith("assets/"):
        normalized = f"assets/{Path(normalized).name}"
    return MAP_DIRECTORY / normalized


def _resolve_reference(reference: str, base_directory: Path) -> Path:
    """Resolve a Tiled reference without depending on the map author's PC."""
    normalized = reference.replace("\\", "/")
    candidate = (base_directory / normalized).resolve()
    if candidate.exists():
        return candidate
    fallbacks = (
        MAP_DIRECTORY / normalized,
        MAP_DIRECTORY / "assets" / Path(normalized).name,
        MAP_DIRECTORY / "assets" / "ruined_town" / "tilesets" / Path(normalized).name,
    )
    for fallback in fallbacks:
        if fallback.exists():
            return fallback.resolve()
    raise FileNotFoundError(
        f"Unable to resolve Tiled reference {reference!r} from {base_directory}"
    )


def _tileset_sprites(
    raw: dict[str, object], map_path: Path
) -> dict[int, TileSpriteDefinition]:
    sprites: dict[int, TileSpriteDefinition] = {}
    for entry in raw.get("tilesets", []):  # type: ignore[union-attr]
        first_gid = int(entry["firstgid"])
        source = entry.get("source")
        if not source:
            raise ValueError(f"Embedded tilesets are not supported in {map_path.name}")
        tileset_path = _resolve_reference(str(source), map_path.parent)
        root = ET.parse(tileset_path).getroot()
        tile_width = int(root.attrib["tilewidth"])
        tile_height = int(root.attrib["tileheight"])

        atlas = root.find("image")
        if atlas is not None:
            image_path = _resolve_reference(atlas.attrib["source"], tileset_path.parent)
            image_width = int(atlas.attrib["width"])
            image_height = int(atlas.attrib["height"])
            columns = int(root.attrib.get("columns", "0"))
            tile_count = int(root.attrib.get("tilecount", "0"))
            margin = int(root.attrib.get("margin", "0"))
            spacing = int(root.attrib.get("spacing", "0"))
            if columns <= 0:
                columns = max(1, (image_width - margin * 2 + spacing) // (tile_width + spacing))
            for local_id in range(tile_count):
                column = local_id % columns
                row = local_id // columns
                clip_left = margin + column * (tile_width + spacing)
                clip_top = margin + row * (tile_height + spacing)
                sprites[first_gid + local_id] = TileSpriteDefinition(
                    image_path=image_path,
                    clip_left=clip_left,
                    clip_bottom=image_height - clip_top - tile_height,
                    clip_width=tile_width,
                    clip_height=tile_height,
                    image_width=image_width,
                    image_height=image_height,
                )

        for tile in root.findall("tile"):
            image = tile.find("image")
            if image is None:
                continue
            local_id = int(tile.attrib["id"])
            image_path = _resolve_reference(image.attrib["source"], tileset_path.parent)
            image_width = int(image.attrib.get("width", tile_width))
            image_height = int(image.attrib.get("height", tile_height))
            sprites[first_gid + local_id] = TileSpriteDefinition(
                image_path=image_path,
                clip_left=0,
                clip_bottom=0,
                clip_width=image_width,
                clip_height=image_height,
                image_width=image_width,
                image_height=image_height,
            )
    return sprites


def _base_gid(raw_gid: int) -> int:
    return raw_gid & GID_MASK


def _build_tile_chunks(
    tiles: list[MapTileDefinition],
) -> dict[tuple[int, int], tuple[MapTileDefinition, ...]]:
    chunks: dict[tuple[int, int], list[MapTileDefinition]] = {}
    for tile in tiles:
        center_x = tile.rect.left + tile.rect.width / 2
        center_y = tile.rect.bottom + tile.rect.height / 2
        key = (
            math.floor(center_x / TILE_CHUNK_SIZE),
            math.floor(center_y / TILE_CHUNK_SIZE),
        )
        chunks.setdefault(key, []).append(tile)
    return {key: tuple(value) for key, value in chunks.items()}


def _entity_sprite_path(
    obj: dict[str, object],
    tile_sprites: dict[int, TileSpriteDefinition],
    fallback: str,
) -> Path:
    raw_gid = int(obj.get("gid", 0))
    sprite = tile_sprites.get(_base_gid(raw_gid))
    # Resource/event objects use image-collection tiles.  Using the object's GID
    # means changing that image in Tiled changes the game without another table edit.
    if sprite is not None and (
        sprite.clip_width == sprite.image_width
        and sprite.clip_height == sprite.image_height
    ):
        return sprite.image_path
    return _asset_path(fallback)


def load_map_data(map_name: str, *, scale: float = MAP_SCALE) -> MapData:
    """Load one of the four approved maps and convert Tiled coordinates."""
    safe_name = Path(map_name).name
    if safe_name != map_name or safe_name not in MAP_DEFINITIONS:
        raise ValueError(f"Unknown CrowGame map: {map_name}")
    definition = MAP_DEFINITIONS[safe_name]
    map_path = MAP_DIRECTORY / definition.json_filename
    background_path = MAP_DIRECTORY / definition.background_filename
    if not map_path.exists():
        raise FileNotFoundError(map_path)
    if not background_path.exists():
        raise FileNotFoundError(background_path)

    raw = json.loads(map_path.read_text(encoding="utf-8"))
    source_width = float(raw["width"] * raw["tilewidth"])
    source_height = float(raw["height"] * raw["tileheight"])
    map_tile_width = float(raw["tilewidth"])
    map_tile_height = float(raw["tileheight"])
    tile_sprites = _tileset_sprites(raw, map_path)
    spawns: dict[str, tuple[float, float]] = {}
    collisions: list[WorldRect] = []
    transitions: list[MapTransition] = []
    entities: list[WorldEntityDefinition] = []
    tiles: list[MapTileDefinition] = []
    object_tiles: list[MapObjectTileDefinition] = []

    for layer in raw.get("layers", []):
        if not layer.get("visible", True):
            continue
        layer_type = layer.get("type")
        offset_x = float(layer.get("offsetx", 0.0)) + float(layer.get("x", 0.0)) * map_tile_width
        offset_y = float(layer.get("offsety", 0.0)) + float(layer.get("y", 0.0)) * map_tile_height
        if layer_type == "tilelayer":
            layer_width = int(layer.get("width", raw["width"]))
            layer_height = int(layer.get("height", raw["height"]))
            opacity = float(layer.get("opacity", 1.0))
            layer_data = list(layer.get("data", []))
            if safe_name == "ruined_town_demo.json" and str(
                layer.get("name", "")
            ).strip().lower() == "walls":
                collisions.extend(
                    _tile_collision_runs(
                        layer_data,
                        layer_width,
                        layer_height,
                        source_height,
                        map_tile_width,
                        map_tile_height,
                        scale,
                        offset_x,
                        offset_y,
                    )
                )
            for index, value in enumerate(layer_data):
                raw_gid = int(value)
                if raw_gid == 0:
                    continue
                sprite = tile_sprites.get(_base_gid(raw_gid))
                if sprite is None:
                    raise ValueError(
                        f"{safe_name}:{layer.get('name')} uses unknown tile GID "
                        f"{_base_gid(raw_gid)}"
                    )
                column = index % layer_width
                row = index // layer_width
                tiles.append(
                    MapTileDefinition(
                        raw_gid=raw_gid,
                        rect=WorldRect(
                            (column * map_tile_width + offset_x) * scale,
                            (source_height - offset_y - (row + 1) * map_tile_height) * scale,
                            map_tile_width * scale,
                            map_tile_height * scale,
                        ),
                        sprite=sprite,
                        opacity=opacity,
                        draw_order=len(tiles),
                    )
                )
            continue
        if layer_type != "objectgroup":
            continue
        layer_name = str(layer.get("name", "")).lower()
        for obj in layer.get("objects", []):
            if not obj.get("visible", True):
                continue
            props = _properties(obj)
            if obj.get("point") and obj.get("name"):
                spawns[str(obj["name"])] = (
                    (float(obj.get("x", 0.0)) + offset_x) * scale,
                    (source_height - float(obj.get("y", 0.0)) - offset_y) * scale,
                )
            if layer_name == "collision" and not props.get("target_map"):
                collisions.append(
                    _world_rect(obj, source_height, scale, offset_x, offset_y)
                )
            if layer_name == "transitions" and (
                props.get("target_map") or props.get("end_game")
            ):
                target_map = props.get("target_map")
                transitions.append(
                    MapTransition(
                        name=str(obj.get("name", "map_exit")),
                        rect=_world_rect(
                            obj, source_height, scale, offset_x, offset_y
                        ),
                        target_map=str(target_map) if target_map else None,
                        target_spawn=str(props.get("target_spawn", "player_start")),
                        ends_game=bool(props.get("end_game", False)),
                    )
                )
            if "resource" in layer_name and props.get("resource_type"):
                entity_type = str(props["resource_type"]).strip().lower()
                sprite_filename = RESOURCE_SPRITES.get(entity_type)
                if sprite_filename:
                    rect = _world_rect(
                        obj, source_height, scale, offset_x, offset_y
                    )
                    entities.append(
                        WorldEntityDefinition(
                            object_id=int(obj.get("id", 0)),
                            name=str(obj.get("name", entity_type)).strip(),
                            kind="resource",
                            entity_type=entity_type,
                            rect=rect,
                            collision_rect=_entity_collision(rect, props, scale),
                            properties=props,
                            sprite_path=_entity_sprite_path(
                                obj, tile_sprites, sprite_filename
                            ),
                        )
                    )
            if "event" in layer_name and props.get("event_type"):
                event_type = str(props["event_type"]).strip().lower()
                sprite_filename = EVENT_SPRITES.get(event_type)
                if sprite_filename:
                    alternate = props.get("after_sprite") or EVENT_ALTERNATE_SPRITES.get(event_type)
                    entities.append(
                        WorldEntityDefinition(
                            object_id=int(obj.get("id", 0)),
                            name=str(obj.get("name", event_type)).strip(),
                            kind="event",
                            entity_type=event_type,
                            rect=_world_rect(
                                obj, source_height, scale, offset_x, offset_y
                            ),
                            collision_rect=None,
                            properties=props,
                            sprite_path=_entity_sprite_path(
                                obj, tile_sprites, sprite_filename
                            ),
                            alternate_sprite_path=_asset_path(str(alternate)) if alternate else None,
                        )
                    )
            object_name = str(obj.get("name", "")).strip().lower()
            if (
                safe_name == "ruined_town_demo.json"
                and layer_name == "props"
                and object_name in RUINED_TOWN_SOLID_PROPS
            ):
                collisions.append(
                    _prop_collision(
                        _world_rect(
                            obj, source_height, scale, offset_x, offset_y
                        ),
                        scale,
                    )
                )
            if (
                obj.get("gid")
                and "resource" not in layer_name
                and "event" not in layer_name
                and layer_name not in {"collision", "transitions", "spawn"}
            ):
                raw_gid = int(obj["gid"])
                sprite = tile_sprites.get(_base_gid(raw_gid))
                if sprite is None:
                    raise ValueError(
                        f"{safe_name}:{layer.get('name')} uses unknown object GID "
                        f"{_base_gid(raw_gid)}"
                    )
                rect = _world_rect(
                    obj, source_height, scale, offset_x, offset_y
                )
                width = rect.width or sprite.clip_width * scale
                height = rect.height or sprite.clip_height * scale
                object_tiles.append(
                    MapObjectTileDefinition(
                        object_id=int(obj.get("id", 0)),
                        name=str(obj.get("name", "")).strip(),
                        raw_gid=raw_gid,
                        rect=WorldRect(rect.left, rect.bottom, width, height),
                        sprite=sprite,
                        rotation=float(obj.get("rotation", 0.0)),
                        opacity=float(obj.get("opacity", 1.0))
                        * float(layer.get("opacity", 1.0)),
                    )
                )

    if "player_start" not in spawns:
        raise ValueError(f"Map {safe_name!r} does not define player_start")
    return MapData(
        name=safe_name,
        label=definition.label,
        background_path=background_path,
        width=source_width * scale,
        height=source_height * scale,
        spawns=spawns,
        collisions=tuple(collisions),
        transitions=tuple(transitions),
        entities=tuple(entities),
        tiles=tuple(tiles),
        object_tiles=tuple(
            sorted(object_tiles, key=lambda item: item.rect.bottom, reverse=True)
        ),
        source_path=map_path,
        source_mtime_ns=map_path.stat().st_mtime_ns,
        tile_chunks=_build_tile_chunks(tiles),
        tile_margin=max(map_tile_width, map_tile_height) * scale,
    )


def validate_map_network() -> list[str]:
    """Return human-readable topology errors for all four configured maps."""
    maps = {name: load_map_data(name) for name in MAP_DEFINITIONS}
    errors: list[str] = []
    for source_name, map_data in maps.items():
        for transition in map_data.transitions:
            if transition.ends_game:
                continue
            if transition.target_map not in maps:
                errors.append(f"{source_name}:{transition.name} has an unknown target map")
                continue
            target = maps[transition.target_map]
            if transition.target_spawn not in target.spawns:
                errors.append(
                    f"{source_name}:{transition.name} targets missing spawn "
                    f"{transition.target_map}:{transition.target_spawn}"
                )
    return errors


__all__ = [
    "EVENT_ALTERNATE_SPRITES", "EVENT_SPRITES", "FIRST_MAP", "GID_DIAGONAL_FLIP",
    "GID_HORIZONTAL_FLIP", "GID_MASK", "GID_VERTICAL_FLIP", "MAP_DEFINITIONS",
    "MAP_SCALE", "RESOURCE_SPRITES", "MapData", "MapDefinition",
    "MapObjectTileDefinition", "MapTileDefinition", "MapTransition",
    "TileSpriteDefinition", "WorldEntityDefinition", "WorldRect", "load_map_data",
    "validate_map_network",
]
