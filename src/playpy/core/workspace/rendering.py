from __future__ import annotations
from typing import TYPE_CHECKING

from ..elements import Element
from ..state import SurfaceHandler
from .display import DisplayManager
from .scenes import SceneManager
from .element_hierarchy import ElementHierarchyManager

if TYPE_CHECKING:
    from .workspace import Workspace


class Renderer:
    _forwarded = {}


    def __init__(self, workspace: Workspace, display_manager: DisplayManager, scene_manager: SceneManager, element_hierarchy_manager: ElementHierarchyManager) -> None:
        self.workspace = workspace
        self._display_manager = display_manager
        self._scene_manager = scene_manager
        self._element_hierarchy_manager = element_hierarchy_manager

    
    def draw_element(self, element: Element, parent_handler: SurfaceHandler | None):
        if not element.visible: return
        drawn_handler = element.draw(self.workspace, parent_handler)

        current_handler = drawn_handler if drawn_handler is not None else parent_handler

        for child in element.children:
            child_handler = self.draw_element(child, current_handler)

            if current_handler is not None and child_handler is not None:
                current_handler.extend(
                    child_handler,
                    clip_within_self=not child.ignores_environment,
                )

        return current_handler if drawn_handler is not None else None
    
    def draw(self):
        scene = self._scene_manager.current_scene
        draw_order = None
        if scene is not None:
            draw_order = [scene] + list(self._element_hierarchy_manager._get_global_children())

        for child in draw_order or self.workspace.children:
            child_handler = self.draw_element(child, self._display_manager.draw_surface)
            if child_handler is not None:
                self._display_manager.draw_surface.extend(child_handler, clip_within_self=True)


__all__ = [
    "Renderer"
]
