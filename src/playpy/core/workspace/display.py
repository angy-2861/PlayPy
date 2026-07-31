from __future__ import annotations

from typing import TYPE_CHECKING

from pathlib import Path
import pygame as pg

from ..resources import _make_surface, DEFAULT_ICON_PATH
from ..state import SurfaceHandler, ColorValue, CoordinateValue

if TYPE_CHECKING:
    from .workspace import Workspace


class DisplayManager:
    _forwarded = {
        'size': {},
        'windowed_size': {
            "readonly": False
        },
        'color': {
            "readonly": False
        },
        'name': {},
        "icon": {},
        "mouse_visible": {},
        "fullscreen": {},
        "maximized": {},
        "resizable": {},
        "resized": {},
        "maxed": {},
        "restored": {},
        "toggle_mouse_visible": {},
    }

    windowed_size: CoordinateValue
    size: CoordinateValue
    color: ColorValue

    def __init__(
        self,
        workspace: Workspace,
        windowed_size: CoordinateValue,
        color: ColorValue,
        name: str | None,
        icon: str | Path | None
    ):
        self.workspace = workspace
        self.color = color

        self.windowed_size = windowed_size
        info = pg.display.Info()
        self.fullscreen_size = (info.current_w, info.current_h)

        self.size = self.windowed_size

        self._name = name
        if self._name:
            pg.display.set_caption(self._name)
        else:
            pg.display.set_caption("PlayPy Window")

        self._icon = Path(icon) if icon is not None else DEFAULT_ICON_PATH
        if self._icon and self._icon.exists():
            try:
                pg.display.set_icon(pg.image.load(self._icon))
            except Exception:
                pass
    
        self.screen = pg.display.set_mode(self.size)

        self._draw_surface: SurfaceHandler = SurfaceHandler(_make_surface(self.size), (0, 0))
        self._draw_surface_dirty: bool = True

        self._mouse_visible: bool = True

        # screen size change tracking
        self._fullscreen = False  # whether or not the window is currently in fullscreen mode
        self._maximized = False  # whether or not the window is currently maximized (only relevant if not in fullscreen)
        self._resizable = False  # whether or not the window is currently resizable (window must be resizable to be fullscreen or maximized)

        self._resized = False  # whether or not the window was resized this frame
        self._maxed = False  # whether or not the window was maximized this frame
        self._restored = False  # whether or not the window was restored this frame


    @property
    def name(self) -> str | None:
        return self._name
    
    @name.setter
    def name(self, value: str | None):
        self._name = value
        if self._name:
            pg.display.set_caption(self._name)
        else:
            pg.display.set_caption("PlayPy Window")

    @property
    def icon(self) -> str | Path | None:
        return self._icon
    
    @icon.setter
    def icon(self, value: str | Path | None):
        self._icon = Path(value) if value is not None else DEFAULT_ICON_PATH
        if self._icon and self._icon.exists():
            try:
                pg.display.set_icon(pg.image.load(self._icon))
            except Exception:
                pass


    @property
    def mouse_visible(self) -> bool:
        return self._mouse_visible

    @mouse_visible.setter
    def mouse_visible(self, value: bool):
        self._mouse_visible = value
        pg.mouse.set_visible(value)


    @property
    def fullscreen(self) -> bool:
        return self._fullscreen and self._resizable and not self._maximized
    
    @fullscreen.setter
    def fullscreen(self, value: bool):
        if self._fullscreen != value:
            self._fullscreen = value
            if value:
                self._maximized = False
                self._resizable = True
            self._set_display_mode()

    @property
    def maximized(self) -> bool:
        return self._maximized and self._resizable and not self._fullscreen
    
    @maximized.setter
    def maximized(self, value: bool):
        if self._maximized != value:
            self._maximized = value
            if value:
                self._fullscreen = False
                self._resizable = True
            self._set_display_mode()

    @property
    def resizable(self) -> bool:
        return self._resizable
    
    @resizable.setter
    def resizable(self, value: bool):
        if self._resizable != value:
            self._resizable = value
            if not value:
                self._fullscreen = False
                self._maximized = False
            self._set_display_mode()

    @property
    def resized(self) -> bool:
        return self._resized
    
    @property
    def maxed(self) -> bool:
        return self._maxed
    
    @property
    def restored(self) -> bool:
        return self._restored
    

    @property
    def draw_surface(self) -> SurfaceHandler:
        return self._draw_surface


    def _set_display_mode(self) -> None:
        flags = 0
        if self._fullscreen:
            flags |= pg.FULLSCREEN
            self.size = self.fullscreen_size
        else:
            if self._resizable:
                flags |= pg.RESIZABLE
            if self._maximized:
                flags |= pg.WINDOWMAXIMIZED
            self.size = self.windowed_size

        self.screen = pg.display.set_mode(self.size, flags)
        self._rebuild_draw_surface()

    
    def toggle_mouse_visible(self, visible: bool | None = None):
        if visible is None:
            visible = not self._mouse_visible
        self._mouse_visible = visible
        pg.mouse.set_visible(self._mouse_visible)


    def _rebuild_draw_surface(self) -> None:
        self._draw_surface = SurfaceHandler(
            _make_surface(self.size),
            (0, 0)
        )


    def fill(self):
        self.screen.fill(self.color)
        self.draw_surface.surface.fill((0, 0, 0, 0))

    def flip(self):
        self.screen.blit(self.draw_surface.surface, (0, 0))
        pg.display.flip()


__all__ = [
    "DisplayManager"
]
