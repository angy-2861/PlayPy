from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pygame as pg

from .. import resources
from .rect import CoordinateValue, RectValue, Rect
from .input import _KeyBase


ColorValue = tuple[int, int, int] | tuple[int, int, int, int]

class BlendMode(_KeyBase):
    RGB_ADD = pg.BLEND_RGB_ADD
    "Adds the base colors to black (`(0, 0, 0)`)."
    RGB_SUBTRACT = pg.BLEND_RGB_SUB
    "Subtracts the base colors from white (`(255, 255, 255)`)."
    RGB_MULTIPLY = pg.BLEND_RGB_MULT
    "Converts the base colors to decimals between 0 and 1 (e.g. `(128, 0, 255) -> (0.5, 0, 1)`), and multiplies them."
    RGB_ALPHA_ADD = pg.BLEND_RGBA_ADD
    "Adds the base colors and transparancies to transparent black (`(0, 0, 0, 0)`)."
    RGB_ALPHA_SUBTRACT = pg.BLEND_RGBA_SUB
    "Subtracts the base colors and transparancies from opaque white (`(255, 255, 255, 255)`)."
    RGB_ALPHA_MULTIPLY = pg.BLEND_RGBA_MULT
    "Converts the base colors and transparancies to decimals between 0 and 1 (e.g. `(128, 0, 255, 102) -> (0.5, 0, 1, 0.4)`), and multiplies them."


class Sprite:
    _cache: dict[Path, pg.Surface] = {}

    def __init__(
            self,
            source: Path | str,
            rect: RectValue | None = None
        ):
        self.source = Path(source)
        self.rect = rect

        self._surface: pg.Surface | None = None

    def load(self) -> pg.Surface:
        if self._surface is None:
            if self.source not in Sprite._cache:
                Sprite._cache[self.source] = pg.image.load(str(self.source)).convert_alpha()
            image = Sprite._cache[self.source]

            if self.rect is not None:
                image = image.subsurface(pg.Rect(
                    self.rect.tuple() if isinstance(self.rect, Rect) else self.rect
                )).copy()

            self._surface = image
        return self._surface
    
class Animation:
    def __init__(
        self,
        frames: Sequence[Path | str | Sprite],
        fps: int = 12,
        loop: bool = True,
    ):
        self.frames = [
            frame if isinstance(frame, Sprite) else Sprite(frame)
            for frame in frames
        ]

        if not self.frames:
            resources.log(resources.Severity.ERROR, resources.InvalidValue, "Animation needs at least one frame", frames_back=1)

        self.fps = fps
        self.loop = loop
        self.time = 0.0

    @property
    def current_frame(self) -> Sprite:
        index = int(self.time * self.fps)

        if self.loop:
            index %= len(self.frames)
        else:
            index = min(index, len(self.frames) - 1)

        return self.frames[index]
    
    @property
    def duration(self) -> float:
        return len(self.frames) / self.fps

    def update(self, dt: float):
        self.time += dt

        if self.loop:
            self.time %= self.duration

    def load(self) -> list[pg.Surface]:
        full: list[pg.Surface] = []
        for frame in self.frames:
            full.append(frame.load())
        return full

    @classmethod
    def from_folder(cls, folder: Path, /, *, prefix: str = "frame_"):
        paths = sorted(folder.glob(f"{prefix}*.png"))
        return cls(paths)
    
    @classmethod
    def from_spritesheet(
        cls,
        image_path: Path | str,
        frame_rects: list[RectValue],
        fps: int = 12,
    ):
        frames = [
            Sprite(image_path, rect)
            for rect in frame_rects
        ]

        return cls(frames, fps)
    
class SurfaceHandler:
    def __init__(
        self,
        surface: pg.Surface,
        pos: CoordinateValue,
        special_flags: int = 0
    ) -> None:
        self.surface = surface
        self.pos = pos
        self.special_flags = special_flags
        self._rect: pg.Rect = pg.Rect(self.pos, self.surface.get_size())

    @property
    def rect(self) -> pg.Rect:
        return self._rect
    
    @rect.setter
    def rect(self, new: pg.Rect):
        if new.size != self._rect.size:
            resources.log(resources.Severity.ERROR, resources.InvalidValue, "Cannot change size of SurfaceHandler rect", frames_back=1)
        self._rect = new
        self.pos = new.topleft

    def paste(self, base: pg.Surface, /):
        base.blit(self.surface, self.pos, special_flags=self.special_flags)

    def extend(self, other: "SurfaceHandler", /, *, clip_within_self: bool = False):
        if clip_within_self:
            offset = (
                other.pos[0] - self.pos[0],
                other.pos[1] - self.pos[1],
            )

            self.surface.blit(
                other.surface,
                offset,
                special_flags=other.special_flags,
            )
            return
        
        if self.rect.contains(other.rect):
            offset = (
                other.pos[0] - self.pos[0],
                other.pos[1] - self.pos[1],
            )
            self.surface.blit(other.surface, offset, special_flags=other.special_flags)
            return

        union = self.rect.union(other.rect)

        new_surface = pg.Surface(union.size, pg.SRCALPHA)

        self_offset = (
            self.rect.x - union.x,
            self.rect.y - union.y,
        )

        other_offset = (
            other.rect.x - union.x,
            other.rect.y - union.y,
        )

        new_surface.blit(self.surface, self_offset)
        new_surface.blit(
            other.surface,
            other_offset,
            special_flags=other.special_flags,
        )

        self.surface = new_surface
        self.pos = union.topleft
        self._rect = pg.Rect(self.pos, self.surface.get_size())

class Sound:
    _cache: dict[Path, pg.mixer.Sound] = {}

    def __init__(self, source: Path | str):
        self.source = Path(source)
        self._sound: pg.mixer.Sound | None = None

    def load(self) -> pg.mixer.Sound:
        if self._sound is None:
            path = self.source.resolve()
            if path not in Sound._cache:
                Sound._cache[path] = pg.mixer.Sound(str(path))
            self._sound = Sound._cache[path]
        return self._sound

    def play(self, loop_amt: int = 0, *, maxtime: int = 0, fade_ms: int = 0) -> pg.mixer.Channel:
        return self.load().play(loop_amt, maxtime, fade_ms)

    def stop(self):
        self.load().stop()

    def set_volume(self, volume: float):
        self.load().set_volume(volume)

    def get_volume(self) -> float:
        return self.load().get_volume()


__all__ = [
    "ColorValue",
    "BlendMode",
    "Sprite",
    "Animation",
    "SurfaceHandler",
    "Sound",
]
