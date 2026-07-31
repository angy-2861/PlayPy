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
        self._scale = scale
        self._offset = offset

    @property
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self, value: float):
        self._scale = value
        if self._parent is not None:
            self._parent._propagate_layout_change(updates_children=True)

    @property
    def offset(self):
        return self._offset
    
    @offset.setter
    def offset(self, value: int):
        self._offset = value
        if self._parent is not None:
            self._parent._propagate_layout_change(updates_children=True)

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
        bold: bool = False,
        italic: bool = False,
        antialias: bool = True,
    ):
        super().__init__()
        self._font_path = _resolve_font_path(font_path)
        self._font_size = font_size
        self._bold = bold
        self._italic = italic
        self._antialias = antialias

    @property
    def font_path(self):
        return self._font_path
    
    @font_path.setter
    def font_path(self, value: str | Path | None):
        self._font_path = _resolve_font_path(value)
        if self._parent is not None:
            self._parent._propagate_layout_change()

    @property
    def font_size(self):
        return self._font_size
    
    @font_size.setter
    def font_size(self, value: int):
        self._font_size = value
        if self._parent is not None:
            self._parent._propagate_layout_change(updates_children=True)

    @property
    def bold(self):
        return self._bold
    
    @bold.setter
    def bold(self, value: bool):
        self._bold = value
        if self._parent is not None:
            self._parent._propagate_layout_change(updates_children=True)

    @property
    def italic(self):
        return self._italic
    
    @italic.setter
    def italic(self, value: bool):
        self._italic = value
        if self._parent is not None:
            self._parent._propagate_layout_change(updates_children=True)

    @property
    def antialias(self):
        return self._antialias
    
    @antialias.setter
    def antialias(self, value: bool):
        self._antialias = value
        if self._parent is not None:
            self._parent._propagate_layout_change(updates_children=True)


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
