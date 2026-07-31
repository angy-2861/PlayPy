from __future__ import annotations

from typing import TYPE_CHECKING
from contextlib import contextmanager

from .input import InputManager
from .display import DisplayManager
from ..resources import InvalidValue, Severity, log

if TYPE_CHECKING:
    from ..elements import Scene
    from .workspace import Workspace


class SceneManager:
    _forwarded = {
        "current_scene",
        "scene_stack",
        "scene_changed",
        "previous_scene",
        "last_scene_change_time",
        "queue_scene_change",
        "queue_scene_push",
        "queue_scene_pop",
        "scene_scope",
    }

    scene_stack: "list[Scene]"
    scene_changed: bool
    previous_scene: "Scene | None"
    last_scene_change_time: float

    def __init__(self, workspace: Workspace, input_manager: InputManager, display_manager: DisplayManager) -> None:
        self.workspace = workspace
        self._input_manager = input_manager
        self._display_manager = display_manager

        self.scene_stack: "list[Scene]" = []
        self.scene_changed = False
        self.previous_scene: "Scene | None" = None
        self.last_scene_change_time = 0.0
        self.scene_change_queue: "list[Scene | None]" = []
        self.scene_push_queue: "list[tuple[Scene, bool]]" = [] # (scene, is_push)


    @property
    def current_scene(self) -> "Scene | None":
        if not self.scene_stack:
            return None
        return self.scene_stack[-1]
    

    def _record_scene_change(self, old_scene: "Scene | None", new_scene: "Scene | None") -> None:
        if old_scene is not new_scene:
            self.previous_scene = old_scene
            self.scene_changed = True
            self.last_scene_change_time = self._input_manager.state.runtime

    def _resolve_queued_scene_change(self):
        if not self.scene_change_queue: return
        self._display_manager._draw_surface_dirty = True
        old_scene = self.current_scene
        while self.scene_stack:
            old = self.scene_stack.pop()
            try:
                old.on_exit(self.workspace)
            finally:
                old.parent = None

        final_scene: "Scene | None" = None
        while self.scene_change_queue:
            scene = self.scene_change_queue.pop(0)
            if final_scene is not None:
                try:
                    final_scene.on_exit(self.workspace)
                finally:
                    final_scene.parent = None
                final_scene = None

            if scene is None:
                final_scene = None
                continue

            self.scene_stack.append(scene)
            scene.parent = self.workspace
            scene.on_enter(self.workspace)
            final_scene = scene

        self._record_scene_change(old_scene, final_scene)

    def _resolve_queued_scene_push(self):
        if not self.scene_push_queue: return
        self._display_manager._draw_surface_dirty = True
        while self.scene_push_queue:
            scene, is_push = self.scene_push_queue.pop(0)
            if not is_push:
                if not self.scene_stack:
                    continue
                popped = self.scene_stack.pop()
                try:
                    popped.on_exit(self.workspace)
                finally:
                    popped.parent = None
                current = self.current_scene
                if current is not None:
                    current.on_resume(self.workspace)
                self._record_scene_change(popped, current)
            else:
                current = self.current_scene
                if current is not None:
                    current.on_pause(self.workspace)
                self.scene_stack.append(scene)
                scene.parent = self.workspace
                scene.on_enter(self.workspace)
                self._record_scene_change(current, scene)

    def queue_scene_change(self, scene: "Scene | None") -> None:
        self.scene_change_queue.append(scene)

    def queue_scene_push(self, scene: "Scene") -> None:
        self.scene_push_queue.append((scene, True))

    def queue_scene_pop(self, scene: "Scene | None" = None) -> None:
        if scene is not None and scene not in self.scene_stack:
            log(Severity.ERROR, InvalidValue, "Cannot remove scene from stack as scene isn't in stack.", frames_back=1)
        if not self.scene_stack:
            log(Severity.ERROR, InvalidValue, "Cannot remove scene from stack as stack is empty.", frames_back=1)
        scene = scene or self.scene_stack[-1]
        self.scene_push_queue.append((scene, False))

    @contextmanager
    def scene_scope(self, scene: "Scene"):
        handle = SceneHandle(self, scene)
        self.queue_scene_push(scene)

        try:
            yield scene, handle
        finally:
            handle.disconnect()


class SceneHandle:
    def __init__(self, manager: SceneManager, scene: "Scene"):
        self.manager = manager
        self.scene = scene
        self._disconnected = False

    @property
    def disconnected(self):
        return self._disconnected

    def disconnect(self):
        if not self._disconnected:
            self._disconnected = True
            self.manager.queue_scene_pop(self.scene)


__all__ = [
    "SceneManager",
]
