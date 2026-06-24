from pathlib import Path
import os

from ..core import elements


__all__ = [
    "Padding",
    "Font",
    "GlobalElement",
    "Camera",
    "Scrollable",
]

class Padding(elements.Component):
    def __init__(
        self,
        scale: float = 0,
        offset: int = 10
    ) -> None:
        super().__init__()
        self.scale = scale
        self.offset = offset

def _resolve_font_path(font_path: str | Path | None) -> str | None:
    if font_path is None:
        return None
    path = Path(font_path)
    if not path.is_absolute():
        candidate = os.curdir / path
        if candidate.exists():
            return str(candidate)
    if path.exists():
        return str(path)
    return None

class Font(elements.Component):
    def __init__(
        self,
        font_path: str | Path | None = None,
        font_size: int | None = None,
        bold: bool | None = None,
        italic: bool | None = None,
        antialias: bool | None = None,
    ):
        super().__init__()
        self._font_path = _resolve_font_path(font_path)
        self.font_size = font_size
        self.bold = bold
        self.italic = italic
        self.antialias = antialias

    @property
    def font_path(self):
        return self._font_path
    
    @font_path.setter
    def font_path(self, value: str | Path | None):
        self._font_path = _resolve_font_path(value)

class GlobalElement(elements.Component):
    def __init__(self):
        super().__init__()

class Camera(elements.Component):
    def __init__(self, x: float = 0, y: float = 0):
        super().__init__()
        self.x = x
        self.y = y

class Scrollable(Camera):
    def __init__(self, scroll_speed: int = 40, scroll_x: float = 0, scroll_y: float = 0):
        super().__init__(scroll_x, scroll_y)
        self.scroll_speed = scroll_speed

    def scroll_x(self, amt: int, min_scroll: int, max_scroll: int):
        self.x -= amt * self.scroll_speed
        self.x = max(min_scroll, min(max_scroll, self.x))

    def scroll_y(self, amt: int, min_scroll: int, max_scroll: int):
        self.y -= amt * self.scroll_speed
        self.y = max(min_scroll, min(max_scroll, self.y))
