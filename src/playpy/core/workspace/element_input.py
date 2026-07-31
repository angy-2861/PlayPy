from __future__ import annotations

from collections.abc import Generator
import contextlib as ctl
import inspect
from typing import TYPE_CHECKING

from .input import InputManager
from .scenes import SceneManager
from .element_hierarchy import ElementHierarchyManager

if TYPE_CHECKING:
    from ..elements import Element
    from .workspace import Workspace

class ElementInputManager:
    _forwarded = {
        "is_mouse_over",
        "is_mouse_top",
        "just_hovered_inclusive",
        "just_hovered",
        "just_unhovered_inclusive",
        "just_unhovered",
    }

    def __init__(self, workspace: Workspace, input_manager: InputManager, scene_manager: SceneManager, element_hierarchy_manager: ElementHierarchyManager) -> None:
        self.workspace = workspace
        self._input_manager = input_manager
        self._scene_manager = scene_manager
        self._element_hierarchy_manager = element_hierarchy_manager

        self.hovered_set: "set[Element]" = set()
        self.hovered_top: "Element | None" = None
        self.last_hovered_set: "set[Element]" = set()
        self.last_hovered_top: "Element | None" = None

        self.coroutines: list[Generator[None, None, None]] = []
        
        self.order_dirty = True
        self.input_order: "list[Element]" = []

    def _update_hover_state(self, draw_order: "list[Element]") -> None:
        self.last_hovered_set = self.hovered_set
        self.last_hovered_top = self.hovered_top

        hovered: "list[Element]" = []
        for element in draw_order:
            if self._element_hierarchy_manager._is_element_hittable(element) and not element.ignores_environment:
                hovered.append(element)
        self.hovered_set = set(hovered)
        self.hovered_top = hovered[-1] if hovered else None


    def is_mouse_over(self, element: "Element") -> bool:
        return element in self.hovered_set

    def is_mouse_top(self, element: "Element") -> bool:
        return self.hovered_top is element

    def just_hovered_inclusive(self, element: "Element") -> bool:
        return element in self.hovered_set and element not in self.last_hovered_set

    def just_hovered(self, element: "Element") -> bool:
        return self.hovered_top is element and self.last_hovered_top is not element

    def just_unhovered_inclusive(self, element: "Element") -> bool:
        return element not in self.hovered_set and element in self.last_hovered_set

    def just_unhovered(self, element: "Element") -> bool:
        return self.hovered_top is not element and self.last_hovered_top is element


    def generate_processing_order(self, target: "Element | None" = None):
        order: "list[Element]" = []
        if target is None:
            targ = self.workspace
        else:
            targ = target
            order.append(targ)

        for child in targ.children:
            order.extend(self.generate_processing_order(child))
        return order
    
    def generate_global_processing_order(self) -> "list[Element]":
        # Generate processing order for elements that are in the workspace but not in the current scene, AND have the global component
        order: "list[Element]" = []
        for child in self._element_hierarchy_manager._get_global_children():
            if child is self._scene_manager.current_scene: continue
            order.extend(self.generate_processing_order(child))
        return order

    def _base_processing_order(self) -> "list[Element]":
        scene = self._scene_manager.current_scene
        if scene is not None:
            self.input_order = self.generate_global_processing_order() + self.generate_processing_order(scene)
        else:
            self.input_order = self.generate_processing_order()
        self.order_dirty = False
        return self.input_order


    def update_coroutines(self):
        alive_coroutines = []

        for coroutine in self.coroutines:
            with ctl.suppress(StopIteration):
                next(coroutine)
                alive_coroutines.append(coroutine)

        self.coroutines = alive_coroutines

    def process_input(self):
        base_order = self._base_processing_order() if self.order_dirty else self.input_order
        self._input_manager.update_input()

        self._update_hover_state(base_order)
        for inp_target in reversed(base_order):
            if not inp_target.enabled or (
                inp_target.block_input_when_occluded
                and self.is_mouse_over(inp_target)
                and not self.is_mouse_top(inp_target)
            ):
                continue

            result = inp_target.handle_input(self.workspace)

            if inspect.isgenerator(result):
                self.coroutines.append(result)


__all__ = [
    "ElementInputManager"
]
