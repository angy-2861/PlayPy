from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, overload

import pygame as pg

from ..resources import require_init, log, quit, Severity, MissingAttribute
from ..state import ColorValue, CoordinateValue, InputProfile, InputState, Tween, TweenedValue
from .display import DisplayManager
from .element_input import ElementInputManager
from .element_hierarchy import ElementHierarchyManager
from .input import InputManager
from .rendering import Renderer
from .scenes import SceneManager, SceneHandle
from .tween import TweenManager


def generate_forwards(cls: object, manager_attr: str, manager_cls: type):
    if not hasattr(manager_cls, "_forwarded"):
        log(Severity.WARNING, MissingAttribute, f"{manager_cls.__name__} has no forwarded iterable.", frames_back=1)
        return cls
    type_hints = manager_cls.__annotations__
    if not isinstance(manager_cls._forwarded, dict):
        manager_cls._forwarded = {forward: {} for forward in manager_cls._forwarded}
    for name in manager_cls._forwarded:
        rename = manager_cls._forwarded[name].get("rename", name)
        try:
            target = getattr(manager_cls, name)
            is_mutable = isinstance(target, property) and target.fset is not None
        except AttributeError:
            if name not in type_hints:
                log(Severity.CRITICAL, MissingAttribute, f"{manager_cls.__name__}.{name} is forwarded but is not present in class.", frames_back=1)
                continue
            is_mutable = not manager_cls._forwarded[name].get("readonly", True)
        def getter(self, name=name):
            return getattr(getattr(self, manager_attr), name)
        if is_mutable:
            def setter(self, value, name=name):
                setattr(getattr(self, manager_attr), name, value)
            setattr(cls, rename, property(getter, setter))
        else:
            setattr(cls, rename, property(getter))

    return cls

if TYPE_CHECKING:
    from ..elements import Element, Scene

    class Workspace:
        def __init__(
            self,
            windowed_size: CoordinateValue = (800, 600),
            color: ColorValue = (255, 255, 255),
            fps: int = 60,
            name: str | None = None,
            icon: str | Path | None = None,
        ):
            self._display: DisplayManager
            self._tween_manager: TweenManager
            self._input_manager: InputManager
            self._scene_manager: SceneManager
            self._element_input_manager: ElementInputManager
            self._element_hierarchy_manager: ElementHierarchyManager
            self._renderer: Renderer

            self.fps: int
            self.clock: pg.time.Clock
            self.running: bool
            self._stepping: bool
        
        @property
        def size(self) -> CoordinateValue: ...

        @property
        def windowed_size(self) -> CoordinateValue: ...
        @windowed_size.setter
        def windowed_size(self, value: CoordinateValue): ...

        @property
        def color(self) -> ColorValue: ...
        @color.setter
        def color(self, value: ColorValue): ...

        @property
        def name(self) -> str | None: ...
        @name.setter
        def name(self, value: str | None): ...

        @property
        def icon(self) -> str | Path | None: ...
        @icon.setter
        def icon(self, value: str | Path | None): ...

        @property
        def mouse_visible(self) -> bool: ...
        @mouse_visible.setter
        def mouse_visible(self, value: bool): ...

        @property
        def fullscreen(self) -> bool: ...
        @fullscreen.setter
        def fullscreen(self, value: bool): ...

        @property
        def maximized(self) -> bool: ...
        @maximized.setter
        def maximized(self, value: bool): ...

        @property
        def resizable(self) -> bool: ...
        @resizable.setter
        def resizable(self, value: bool): ...

        @property
        def resized(self) -> bool: ...
        @property
        def maxed(self) -> bool: ...
        @property
        def restored(self) -> bool: ...

        def toggle_mouse_visible(self, visible: bool | None = None): ...


        @property
        def input_state(self) -> InputState: ...
        @property
        def controller_profiles(self) -> set[InputProfile]: ...
        @property
        def profile_changes(self) -> list[tuple[InputProfile, bool]]: ...
        @property
        def profiles_added(self) -> set[InputProfile]: ...
        @property
        def profiles_removed(self) -> set[InputProfile]: ...
        @property
        def bad_joystick_indices(self) -> set[int]: ...

        def get_controller_name(self, profile: InputProfile) -> str | None: ...
        def rumble_controller(self, profile: InputProfile, strength: float, duration_ms: int) -> None: ...
        def stop_rumble_controller(self, profile: InputProfile) -> None: ...


        @property
        def current_scene(self) -> "Scene | None": ...
        @property
        def scene_stack(self) -> "list[Scene]": ...
        @property
        def scene_changed(self) -> bool: ...
        @property
        def previous_scene(self) -> "Scene | None": ...
        @property
        def last_scene_change_time(self) -> float: ...

        def queue_scene_change(self, scene: "Scene | None") -> None: ...
        def queue_scene_push(self, scene: "Scene") -> None: ...
        def queue_scene_pop(self, scene: "Scene | None" = None) -> None: ...

        @contextmanager
        def scene_scope(self, scene: "Scene") -> "Iterator[tuple[Scene, SceneHandle]]": ...


        @property
        def children(self) -> "list[Element]": ...

        def add_child(self, child: "Element", z: int | None = None) -> None: ...
        def remove_child(self, child: "Element") -> None: ...
        def is_ancestor_of(self, descendant: "Element") -> bool: ...
        def is_parent_of(self, child: "Element") -> bool: ...
        def get_element_rect(self, element: "Element") -> pg.Rect: ...


        def is_mouse_over(self, element: "Element") -> bool: ...
        def is_mouse_top(self, element: "Element") -> bool: ...
        def just_hovered_inclusive(self, element: "Element") -> bool: ...
        def just_hovered(self, element: "Element") -> bool: ...
        def just_unhovered_inclusive(self, element: "Element") -> bool: ...
        def just_unhovered(self, element: "Element") -> bool: ...


        @property
        def active_tweens(self) -> list[Tween]: ...

        def add_tween(self, tween: Tween, /) -> int: ...

        @overload
        def remove_tween(self, tween_index: int, /) -> Tween: ...
        @overload
        def remove_tween(self, tween: Tween, /) -> Tween: ...
        def remove_tween(self, *args) -> Tween: ...

        def get_tween(self, tween_index: int) -> Tween: ...

        def clear_tweens(self) -> list[Tween]: ...


        def step(self): ...
        def run(self): ...
        def wait(self, seconds: float) -> float: ...
        def quit(self): ...
        def _finish_frame(self): ...
        def _tick(self) -> float: ...

else:
    class Workspace:
        def __init__(
            self,
            windowed_size: CoordinateValue = (800, 600),
            color: ColorValue = (255, 255, 255),
            fps: int = 60,
            name: str | None = None,
            icon: str | Path | None = None,
        ):
            require_init()

            self._display = DisplayManager(self, windowed_size, color, name, icon)
            self._tween_manager = TweenManager(self)
            self._input_manager = InputManager(self)
            self._scene_manager = SceneManager(self, self._input_manager)
            self._element_hierarchy_manager = ElementHierarchyManager(self, self._display, self._input_manager)
            self._element_input_manager = ElementInputManager(self, self._input_manager, self._scene_manager, self._element_hierarchy_manager)
            self._renderer = Renderer(self, self._display, self._scene_manager, self._element_hierarchy_manager)

            self.fps = fps
            self.clock = pg.time.Clock()
            self.running = False
            self._stepping = False

        def step(self):
            self._stepping = True
            self._display.fill()

            try:
                self._scene_manager._resolve_queued_scene_change()
                self._scene_manager._resolve_queued_scene_push()
                self._element_input_manager.update_coroutines()
                self._element_input_manager.process_input()
                self._renderer.draw()
                self._finish_frame()
            finally:
                self._stepping = False

        def run(self):
            self.running = True
            while self.running:
                self.step()
            quit()

        def wait(self, seconds: float) -> float:
            if self._stepping or not self.running:
                elapsed = pg.time.wait(round(seconds * 1000))
                return elapsed / 1000

            start_time = pg.time.get_ticks()
            end_time = start_time + round(seconds * 1000)
            while self.running and pg.time.get_ticks() < end_time:
                self.step()
            return (pg.time.get_ticks() - start_time) / 1000

        def quit(self):
            if not self.running:
                quit()
            else:
                self.running = False

        def _finish_frame(self):
            self._display.flip()
            dt = self._tick()
            self._input_manager.next_frame(dt)
            self._tween_manager.next_frame(dt)
            self._scene_manager.scene_changed = False

        def _tick(self) -> float:
            return self.clock.tick(self.fps) / 1000

    generate_forwards(Workspace, "_display", DisplayManager)
    generate_forwards(Workspace, "_tween_manager", TweenManager)
    generate_forwards(Workspace, "_input_manager", InputManager)
    generate_forwards(Workspace, "_scene_manager", SceneManager)
    generate_forwards(Workspace, "_element_hierarchy_manager", ElementHierarchyManager)
    generate_forwards(Workspace, "_element_input_manager", ElementInputManager)
    generate_forwards(Workspace, "_renderer", Renderer)


__all__ = [
    "Workspace",
    "SceneHandle",
]
